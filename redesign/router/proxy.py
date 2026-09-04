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

UPSTREAM = os.environ.get("OMNIROUTE_UPSTREAM", "http://127.0.0.1:20128").rstrip("/")
_bind = os.environ.get("SANITIZER_BIND", "127.0.0.1:20127")
BIND_HOST, BIND_PORT = _bind.split(":")[0], int(_bind.split(":")[1])

_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # silencia o log ruidoso do http.server
        pass

    # -- GET/HEAD: repassa sem tocar (ex.: /v1/models, /health) -------------- #
    def do_GET(self):
        self._passar(b"", "GET")

    def do_HEAD(self):
        self._passar(b"", "HEAD")

    # -- POST: sanitiza o corpo antes de repassar --------------------------- #
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        corpo = self.rfile.read(n) if n else b""

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
    srv = ThreadingHTTPServer((host, port), _Handler)
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

    up_srv = ThreadingHTTPServer(("127.0.0.1", up_port), _DummyUpstream)
    px_srv = ThreadingHTTPServer(("127.0.0.1", px_port), _Handler)
    threading.Thread(target=up_srv.serve_forever, daemon=True).start()
    threading.Thread(target=px_srv.serve_forever, daemon=True).start()

    base = f"http://127.0.0.1:{px_port}/v1/chat/completions"
    falhas = 0

    # 1. pedido limpo -> 200, passthrough do dummy
    limpo = json.dumps({"model": "x", "messages": [{"role": "user", "content": "responda so: ok"}]}).encode()
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(base, data=limpo, headers={"Content-Type": "application/json"}), timeout=10)
        body = json.loads(r.read())
        ok = r.status == 200 and body.get("choices", [{}])[0].get("message", {}).get("content") == "ok-dummy"
        print(f"{'PASS' if ok else 'FALHA'}  pedido limpo -> {r.status}, upstream {'tocado' if _DummyUpstream.tocado else 'NAO tocado'}")
        falhas += 0 if ok else 1
    except Exception as e:  # noqa: BLE001
        print(f"FALHA  pedido limpo levantou {type(e).__name__}: {e}")
        falhas += 1

    # 2. pedido com segredo plantado (gerado na hora) -> 4xx do proxy, upstream NAO tocado
    _DummyUpstream.tocado = False
    fake = sanitizar._fx("sk", "-", "Z" * 24)  # casa sk-[A-Za-z0-9]{20,}
    sujo = json.dumps({"model": "x", "messages": [{"role": "user", "content": f"minha chave e {fake}"}]}).encode()
    try:
        urllib.request.urlopen(
            urllib.request.Request(base, data=sujo, headers={"Content-Type": "application/json"}), timeout=10)
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
