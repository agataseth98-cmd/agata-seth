#!/usr/bin/env python3
"""HTTP local, com limite -- item 5 do plano de ação da auditoria de Marcos
(MEMÓRIAS (500)/(502)/(503)): nenhum dos servidores HTTP crus deste sistema
(`seth_gateway`, `proxy` sanitizador, `whisper_server`, `embeddings_server`,
`seth_escriba`, `seth_verificador`, `tts_piper`, `ro_proxy`) limitava o
tamanho do corpo (`Content-Length` mentiroso ou gigante -> tenta alocar
tudo em memória antes de validar nada) nem o número de conexões simultâneas
(`ThreadingHTTPServer` sobe uma thread por conexão, sem teto -- uma rajada
de conexões lentas/paradas esgota threads/memória). Todos escutam só em
127.0.0.1 (contenção de rede já existe, PROJETO.md "Segurança") -- isto é
defesa em profundidade pra quando o processo que fala com eles for outro
processo local comprometido/quebrado, não um desconhecido de fora.

Uso, em cada servidor:
    from http_seguro import ler_corpo_limitado, ServidorConcorrenciaLimitada

    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            corpo = ler_corpo_limitado(self)   # None + 413 já enviado se estourou
            if corpo is None:
                return
            ...

    srv = ServidorConcorrenciaLimitada((host, port), _Handler)  # limite default 32
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_CORPO_PADRAO = 25 * 1024 * 1024  # 25 MiB -- generoso pra JSON/texto, recusa payload absurdo
MAX_CONEXOES_PADRAO = 32


def ler_corpo_limitado(handler: BaseHTTPRequestHandler, limite: int = MAX_CORPO_PADRAO) -> bytes | None:
    """Lê o corpo do request, recusando ANTES de ler se `Content-Length`
    declarado passar do limite -- nunca chama `rfile.read(n)` com um `n`
    gigante primeiro pra só then verificar (isso já aloca/bloqueia). Em
    caso de recusa, já manda 413 e devolve None; quem chama só precisa
    checar `is None` e sair sem processar mais nada."""
    try:
        n = int(handler.headers.get("content-length", 0))
    except ValueError:
        n = 0
    if n < 0:
        n = 0
    if n > limite:
        corpo_erro = json.dumps({"error": "payload_grande_demais",
                                  "limite_bytes": limite, "recebido_bytes": n}).encode()
        handler.send_response(413)
        handler.send_header("content-type", "application/json")
        handler.send_header("content-length", str(len(corpo_erro)))
        handler.end_headers()
        handler.wfile.write(corpo_erro)
        return None
    return handler.rfile.read(n) if n else b""


class ServidorConcorrenciaLimitada(ThreadingHTTPServer):
    """`ThreadingHTTPServer` com teto de conexões processadas ao mesmo tempo.
    `ThreadingMixIn.process_request` sobe uma thread e retorna na hora (não
    bloqueia o loop principal) -- o teto tem que travar DENTRO da thread
    nova, não no aceite da conexão, senão o aceite em si já enfileira sem
    limite no kernel. Conexão além do teto espera (bloqueia) até uma vaga
    abrir -- não recusa, só põe fila (mesmo padrão de um pool de workers)."""

    max_conexoes = MAX_CONEXOES_PADRAO

    def __init__(self, *a, max_conexoes: int = MAX_CONEXOES_PADRAO, **kw):
        self.max_conexoes = max_conexoes
        self._semaforo = threading.Semaphore(max_conexoes)
        super().__init__(*a, **kw)

    def process_request_thread(self, request, client_address):
        with self._semaforo:
            super().process_request_thread(request, client_address)


def _selftest() -> int:
    import http.client
    import socket
    import time

    ok = True

    # --- 1. corpo além do limite: recusado com 413, sem travar. ---
    class _EcoLimitado(BaseHTTPRequestHandler):
        def do_POST(self):
            corpo = ler_corpo_limitado(self, limite=1024)
            if corpo is None:
                return
            self.send_response(200)
            self.send_header("content-length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def log_message(self, *a):
            pass

    def _porta_livre() -> int:
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        p = s.getsockname()[1]
        s.close()
        return p

    porta1 = _porta_livre()
    srv1 = ThreadingHTTPServer(("127.0.0.1", porta1), _EcoLimitado)
    threading.Thread(target=srv1.serve_forever, daemon=True).start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", porta1, timeout=5)
        conn.request("POST", "/", body=b"x" * 2000)
        resp = conn.getresponse()
        cond1 = resp.status == 413
        resp.read()
        conn.close()
        print(f"{'PASS' if cond1 else 'FALHA'}  corpo acima do limite -- 413 (status={resp.status})")
        ok = ok and cond1

        conn = http.client.HTTPConnection("127.0.0.1", porta1, timeout=5)
        conn.request("POST", "/", body=b"x" * 100)
        resp = conn.getresponse()
        corpo_ok = resp.read()
        cond1b = resp.status == 200 and corpo_ok == b"x" * 100
        print(f"{'PASS' if cond1b else 'FALHA'}  corpo dentro do limite -- 200, eco correto")
        ok = ok and cond1b
        conn.close()
    finally:
        srv1.shutdown()

    # --- 2. concorrência: teto real, requests além dele esperam, nenhuma se perde. ---
    _em_voo = {"n": 0, "pico": 0}
    _lock = threading.Lock()

    class _Lento(BaseHTTPRequestHandler):
        def do_GET(self):
            with _lock:
                _em_voo["n"] += 1
                _em_voo["pico"] = max(_em_voo["pico"], _em_voo["n"])
            time.sleep(0.3)
            with _lock:
                _em_voo["n"] -= 1
            self.send_response(200)
            self.send_header("content-length", "2")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *a):
            pass

    porta2 = _porta_livre()
    srv2 = ServidorConcorrenciaLimitada(("127.0.0.1", porta2), _Lento, max_conexoes=2)
    threading.Thread(target=srv2.serve_forever, daemon=True).start()
    try:
        resultados = []

        def _cliente():
            c = http.client.HTTPConnection("127.0.0.1", porta2, timeout=5)
            c.request("GET", "/")
            r = c.getresponse()
            resultados.append(r.status)
            r.read()
            c.close()

        threads = [threading.Thread(target=_cliente) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        cond2a = all(s == 200 for s in resultados) and len(resultados) == 6
        print(f"{'PASS' if cond2a else 'FALHA'}  todos os 6 requests completaram apesar do teto "
              f"(status={resultados})")
        ok = ok and cond2a

        cond2b = _em_voo["pico"] <= 2
        print(f"{'PASS' if cond2b else 'FALHA'}  pico de conexões simultâneas em voo <= teto "
              f"(pico={_em_voo['pico']}, teto=2)")
        ok = ok and cond2b
    finally:
        srv2.shutdown()

    print("\nSELFTEST OK" if ok else "\nSELFTEST FALHOU")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
