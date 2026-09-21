#!/usr/bin/env python3
"""proxy.py — proxy fino de sanitização antes do OmniRoute (P1-02, opção B).

Fica entre o caller e o OmniRoute. Escuta em 127.0.0.1:20127, roda
`sanitizar.sanitizar_payload` no corpo JSON de cada POST, e SÓ ENTÃO repassa
para o OmniRoute (127.0.0.1:20128). Casou um padrão de segredo ⇒ responde 4xx
com erro estruturado (qual padrão, qual campo) e **não repassa nada** — o
upstream nunca vê o corpo. Falha fechada.

Só stdlib (http.server + urllib) — não instala nada. Streaming (SSE) passa
direto: o corpo da resposta do upstream é copiado byte a byte para o caller.

Uso:
    python3 redesign/router/proxy.py
        # sobe o proxy: caller aponta para http://127.0.0.1:20127 em vez de :20128

    python3 redesign/router/proxy.py --selftest
        # teste offline ponta a ponta: sobe um upstream dummy + o proxy, manda
        # 1 pedido limpo (espera 200 passthrough) e 1 com segredo plantado
        # (espera 4xx do proxy, upstream NÃO tocado). exit 0 = OK.

Env:
    OMNIROUTE_UPSTREAM   default http://127.0.0.1:20128
    SANITIZER_BIND       default 127.0.0.1:20127
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sanitizar  # noqa: E402  (redesign/router/sanitizar.py)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from http_seguro import ler_corpo_limitado, ServidorConcorrenciaLimitada  # noqa: E402

UPSTREAM = os.environ.get("OMNIROUTE_UPSTREAM", "http://127.0.0.1:20128").rstrip("/")
_bind = os.environ.get("SANITIZER_BIND", "127.0.0.1:20127")
BIND_HOST, BIND_PORT = _bind.split(":")[0], int(_bind.split(":")[1])

_ENV_PATH = os.path.expanduser("~/.config/agata/.env")


def _token_interno() -> str:
    """Lê AGATA_INTERNAL_TOKEN de ~/.config/agata/.env. Nunca loga o valor.

    Item 3 do plano de mitigação da auditoria do Marcos (MEMÓRIAS (437)):
    a fronteira localhost não é fronteira de segurança por si só -- qualquer
    processo no mesmo host podia bater direto neste proxy (ou pior, direto
    no OmniRoute em :20128) sem passar pelo seth_gateway. Este token não
    fecha a porta do OmniRoute (produto de terceiro, sem controle de código
    aqui -- residual registrado, não escondido), mas fecha a deste proxy:
    só quem tem o segredo (hoje, só o seth_gateway) passa."""
    try:
        with open(_ENV_PATH, encoding="utf-8") as f:
            for linha in f:
                if linha.startswith("AGATA_INTERNAL_TOKEN="):
                    return linha.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""

_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # silencia o log ruidoso do http.server
        pass

    def _token_ok(self) -> bool:
        """Falha FECHADA (mesma doutrina do resto deste arquivo): sem token
        configurado em .env, NADA passa -- não é modo aberto de
        compatibilidade, é o mesmo padrão de 'sem a régua de segredo, o
        serviço não responde' que P1-02 já usa."""
        esperado = _token_interno()
        if not esperado:
            return False
        recebido = self.headers.get("X-Agata-Token", "")
        return recebido == esperado

    def _recusar_sem_token(self):
        self._json(403, {"error": {
            "type": "internal_token_required",
            "message": "faltou ou errou X-Agata-Token -- este proxy só aceita chamadas do seth_gateway",
        }})

    # -- GET/HEAD: repassa sem tocar (ex.: /v1/models, /health) -------------- #
    def do_GET(self):
        if not self._token_ok():
            return self._recusar_sem_token()
        self._passar(b"", "GET")

    def do_HEAD(self):
        if not self._token_ok():
            return self._recusar_sem_token()
        self._passar(b"", "HEAD")

    # -- POST: sanitiza o corpo antes de repassar --------------------------- #
    def do_POST(self):
        if not self._token_ok():
            return self._recusar_sem_token()
        corpo = ler_corpo_limitado(self)
        if corpo is None:
            return

        # Falha FECHADA (docstring do módulo, P1-02): corpo vazio passa (nada
        # a varrer); todo corpo COM bytes tem que parsear como JSON e ser
        # varrido -- não-JSON não segue mais "como está" (achado 04/09/2026,
        # Camada C: a versão anterior deixava passar ileso qualquer corpo que
        # não fosse `application/json`, contradizendo a própria promessa de
        # "SÓ ENTÃO repassa" no topo do arquivo).
        if corpo:
            try:
                payload = json.loads(corpo)
            except ValueError:
                return self._erro(415, "corpo não é JSON -- este proxy só entende OpenAI-compat; nada foi repassado")
            if isinstance(payload, dict):
                try:
                    sanitizar.sanitizar_payload(payload)
                except sanitizar.SegredoNoPayload as e:
                    return self._bloqueado(e)
            else:
                # JSON válido mas não-objeto (lista, string, número) caía aqui
                # e seguia direto pro _passar SEM VARREDURA NENHUMA -- o mesmo
                # "passa ileso" que o conserto de 04/09 fechou um degrau
                # abaixo (não-JSON), deixado aberto um degrau acima.
                # Medido em 09/09/2026 com upstream de teste: corpo `dict` com
                # segredo -> 422 e upstream intocado; a MESMA chave dentro de
                # uma LISTA de topo -> 200 e o upstream RECEBEU o segredo.
                # Falha fechada, como o topo deste arquivo promete: corpo
                # OpenAI-compat é sempre objeto, então não-objeto é recusa.
                return self._erro(
                    415,
                    "corpo JSON não é objeto -- este proxy só entende OpenAI-compat "
                    "(objeto no topo); nada foi repassado",
                )
        self._passar(corpo, "POST")

    # --------------------------------------------------------------------- #
    def _passar(self, corpo: bytes, metodo: str):
        url = UPSTREAM + self.path
        headers = {
            k: v for k, v in self.headers.items()
            if k.lower() not in _HOP_BY_HOP
        }
        req = urllib.request.Request(url, data=corpo or None, method=metodo, headers=headers)
        try:
            up = urllib.request.urlopen(req, timeout=180)
        except urllib.error.HTTPError as e:  # repassa o erro do upstream tal qual
            up = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            return self._erro(502, f"upstream OmniRoute inacessível em {UPSTREAM}: {e}")

        self.send_response(up.status)
        for k, v in up.headers.items():
            if k.lower() not in _HOP_BY_HOP:
                self.send_header(k, v)
        # streaming/SSE passa direto
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        try:
            while True:
                pedaco = up.read(8192)
                if not pedaco:
                    break
                self.wfile.write(f"{len(pedaco):X}\r\n".encode())
                self.wfile.write(pedaco)
                self.wfile.write(b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
        finally:
            up.close()

    def _bloqueado(self, e: "sanitizar.SegredoNoPayload"):
        detalhe = [
            {"campo": a.get("campo"), "padrao": a["padrao_rotulo"], "trecho": a["trecho_redigido"]}
            for a in e.achados
        ]
        self._json(422, {
            "error": {
                "type": "secret_blocked_before_egress",
                "message": "payload bloqueado pela sanitização (P1-02) — não foi enviado ao provedor",
                "achados": detalhe,
            }
        })

    def _erro(self, code: int, msg: str):
        self._json(code, {"error": {"type": "proxy_error", "message": msg}})

    def _json(self, code: int, obj: dict):
        corpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def servir(host: str = BIND_HOST, port: int = BIND_PORT):
    srv = ServidorConcorrenciaLimitada((host, port), _Handler)
    print(f"proxy de sanitização em http://{host}:{port}  ->  {UPSTREAM}")
    srv.serve_forever()


# --------------------------------------------------------------------------- #
# selftest offline: upstream dummy + proxy, 1 pedido limpo + 1 com segredo     #
# --------------------------------------------------------------------------- #
def _porta_livre() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class _DummyUpstream(BaseHTTPRequestHandler):
    tocado = False

    def log_message(self, *a):
        pass

    def do_POST(self):
        type(self).tocado = True
        n = int(self.headers.get("Content-Length") or 0)
        _ = self.rfile.read(n)
        corpo = json.dumps({"choices": [{"message": {"role": "assistant", "content": "ok-dummy"}}],
                            "usage": {"total_tokens": 3}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def _selftest() -> int:
    global UPSTREAM
    up_port = _porta_livre()
    px_port = _porta_livre()
    UPSTREAM = f"http://127.0.0.1:{up_port}"

    # Token isolado do .env real -- o selftest não depende de o Humano já
    # ter configurado AGATA_INTERNAL_TOKEN, e não usa o valor de produção.
    # globals() (não reimport) porque este arquivo pode rodar como
    # __main__ -- um `import proxy` separado criaria um SEGUNDO objeto de
    # módulo, e o monkeypatch cairia no lugar errado (achado testando).
    token_teste = "selftest-token-nao-e-segredo-de-verdade"
    globals()["_token_interno"] = lambda: token_teste

    up_srv = ThreadingHTTPServer(("127.0.0.1", up_port), _DummyUpstream)
    px_srv = ThreadingHTTPServer(("127.0.0.1", px_port), _Handler)
    threading.Thread(target=up_srv.serve_forever, daemon=True).start()
    threading.Thread(target=px_srv.serve_forever, daemon=True).start()

    base = f"http://127.0.0.1:{px_port}/v1/chat/completions"
    falhas = 0
    com_token = {"Content-Type": "application/json", "X-Agata-Token": token_teste}

    # 0a. sem token nenhum -> 403, upstream NAO tocado (item 3 do plano de
    # mitigacao da auditoria do Marcos, MEMORIAS (437))
    limpo = json.dumps({"model": "x", "messages": [{"role": "user", "content": "oi"}]}).encode()
    try:
        urllib.request.urlopen(
            urllib.request.Request(base, data=limpo, headers={"Content-Type": "application/json"}), timeout=10)
        print("FALHA  pedido sem token passou (esperava 403)")
        falhas += 1
    except urllib.error.HTTPError as e:
        ok = e.code == 403 and not _DummyUpstream.tocado
        print(f"{'PASS' if ok else 'FALHA'}  sem token -> {e.code}, upstream {'NAO tocado' if not _DummyUpstream.tocado else 'TOCADO (falha!)'}")
        falhas += 0 if ok else 1

    # 0b. token errado -> 403, upstream NAO tocado
    try:
        urllib.request.urlopen(urllib.request.Request(
            base, data=limpo, headers={"Content-Type": "application/json", "X-Agata-Token": "errado"}), timeout=10)
        print("FALHA  pedido com token errado passou (esperava 403)")
        falhas += 1
    except urllib.error.HTTPError as e:
        ok = e.code == 403 and not _DummyUpstream.tocado
        print(f"{'PASS' if ok else 'FALHA'}  token errado -> {e.code}, upstream {'NAO tocado' if not _DummyUpstream.tocado else 'TOCADO (falha!)'}")
        falhas += 0 if ok else 1

    # 1. pedido limpo, token certo -> 200, passthrough do dummy
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(base, data=limpo, headers=com_token), timeout=10)
        body = json.loads(r.read())
        ok = r.status == 200 and body.get("choices", [{}])[0].get("message", {}).get("content") == "ok-dummy"
        print(f"{'PASS' if ok else 'FALHA'}  pedido limpo, token certo -> {r.status}, upstream {'tocado' if _DummyUpstream.tocado else 'NAO tocado'}")
        falhas += 0 if ok else 1
    except Exception as e:  # noqa: BLE001
        print(f"FALHA  pedido limpo levantou {type(e).__name__}: {e}")
        falhas += 1

    # 2. pedido com segredo plantado (gerado na hora), token certo -> 4xx do proxy, upstream NAO tocado
    _DummyUpstream.tocado = False
    fake = sanitizar._fx("sk", "-", "Z" * 24)  # casa sk-[A-Za-z0-9]{20,}
    sujo = json.dumps({"model": "x", "messages": [{"role": "user", "content": f"minha chave e {fake}"}]}).encode()
    try:
        urllib.request.urlopen(
            urllib.request.Request(base, data=sujo, headers=com_token), timeout=10)
        print("FALHA  pedido com segredo passou (esperava 4xx)")
        falhas += 1
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        ok = e.code == 422 and not _DummyUpstream.tocado and body["error"]["type"] == "secret_blocked_before_egress"
        red = body["error"]["achados"][0]["trecho"] if ok else "?"
        print(f"{'PASS' if ok else 'FALHA'}  pedido sujo -> {e.code}, upstream {'NAO tocado' if not _DummyUpstream.tocado else 'TOCADO (falha!)'}, trecho redigido {red!r}")
        falhas += 0 if ok else 1
    except Exception as e:  # noqa: BLE001
        print(f"FALHA  pedido sujo levantou {type(e).__name__}: {e}")
        falhas += 1

    up_srv.shutdown()
    px_srv.shutdown()
    print(f"\n{'SELFTEST OK' if not falhas else f'SELFTEST FALHOU ({falhas})'}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        raise SystemExit(_selftest())
    servir()
