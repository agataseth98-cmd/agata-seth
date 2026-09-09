#!/usr/bin/env python3
"""seth_local_shim.py — endpoint OpenAI-compat de UM modelo local, pro OmniRoute.

Motivo (H4, MEMÓRIAS (402)): o combo `seth-livre` da Seth cascateia por 4
provedores grátis EXTERNOS (zai -> gemini -> huggingface -> mistral) e não tem
fundo local. Se os 4 caírem no mesmo minuto — cenário de (390), já aconteceu
1× — a Seth fica muda. O OmniRoute até tem provider connection pro Ollama
(`ollama-local`, :11434), mas a descoberta de modelos dele só pegou os de
EMBEDDING; nenhum modelo local de chat aparece em `/v1/models`, então não dá
pra pôr no combo.

Este shim é a opção (B), escolhida pelo Humano: em vez de brigar com a
descoberta do OmniRoute, um endpoint mínimo que expõe EXATAMENTE UM modelo
local de chat, que o OmniRoute registra como provider custom sem ambiguidade.

Fala só o dialeto OpenAI que o OmniRoute usa:
  GET  /health                 -> {"status":"ok"}  (não toca o Ollama — barato)
  GET  /v1/models              -> lista com 1 modelo só (SETH_LOCAL_MODEL_ID)
  POST /v1/chat/completions    -> força `model` = SETH_LOCAL_MODEL, repassa pro
                                  Ollama (:11434/v1), faz streaming passar.

Qualquer outra rota -> 404 JSON.

Por que forçar o `model`: o OmniRoute manda o id que ele conhece
(`<provider>/<SETH_LOCAL_MODEL_ID>`); o Ollama precisa da tag real
(`qwen3.5-9b-64k:latest`). O shim traduz. Também garante que só o modelo
auditado (`-64k`, com `PARAMETER num_ctx 65536` no Modelfile — PROJETO.md
"Cérebro") seja usado, nunca a tag `qwen3.5:9b` crua que reproduz o bug de
(121)/#16814.

Só stdlib. Não lê segredo nenhum. Loopback só.

Cold start: se o modelo não estiver carregado, a 1ª chamada pode passar de
30-45s (load do Ollama) e o OmniRoute desiste no `maxWaitMs` (45s desde
(363)); a 2ª responde. `agata-warmup.service` pré-aquece. Este é o ÚLTIMO
tier — se a requisição chegou aqui, os 4 externos já falharam e esperar é
melhor que mudo. Por isso o timeout do upstream é largo (300s).

Env:
  SETH_LOCAL_SHIM_BIND   default 127.0.0.1:20133
  SETH_LOCAL_UPSTREAM    default http://127.0.0.1:11434   (Ollama)
  SETH_LOCAL_MODEL       default qwen3.5-9b-64k:latest    (tag real no Ollama)
  SETH_LOCAL_MODEL_ID    default qwen3.5-9b-64k           (id anunciado ao OmniRoute)

Uso:
  python3 redesign/router/seth_local_shim.py
  python3 redesign/router/seth_local_shim.py --selftest
"""
from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_bind = os.environ.get("SETH_LOCAL_SHIM_BIND", "127.0.0.1:20133")
BIND_HOST, BIND_PORT = _bind.split(":")[0], int(_bind.split(":")[1])
UPSTREAM = os.environ.get("SETH_LOCAL_UPSTREAM", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.environ.get("SETH_LOCAL_MODEL", "qwen3.5-9b-64k:latest")
MODEL_ID = os.environ.get("SETH_LOCAL_MODEL_ID", "qwen3.5-9b-64k")
UPSTREAM_TIMEOUT = int(os.environ.get("SETH_LOCAL_TIMEOUT", "300"))

_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}


def _models_payload() -> bytes:
    return json.dumps({
        "object": "list",
        "data": [{"id": MODEL_ID, "object": "model", "owned_by": "agata-local"}],
    }).encode("utf-8")


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path.rstrip("/") in ("/health", "/healthz"):
            return self._json(200, {"status": "ok", "model": MODEL_ID})
        if self.path.rstrip("/") in ("/v1/models", "/models"):
            return self._raw(200, "application/json", _models_payload())
        return self._json(404, {"error": {"message": f"rota não suportada: {self.path}"}})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        corpo = self.rfile.read(n) if n else b""
        if "/chat/completions" not in self.path:
            return self._json(404, {"error": {"message": f"rota não suportada: {self.path}"}})
        try:
            payload = json.loads(corpo) if corpo else {}
        except ValueError:
            return self._json(400, {"error": {"message": "corpo não é JSON válido"}})
        if not isinstance(payload, dict):
            return self._json(400, {"error": {"message": "corpo JSON não é um objeto"}})
        # força a tag real do Ollama, seja qual for o id que o OmniRoute mandou.
        payload["model"] = MODEL
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._passar(corpo)

    def _passar(self, corpo: bytes):
        url = UPSTREAM + "/v1/chat/completions"
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in _HOP_BY_HOP}
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=corpo, method="POST", headers=headers)
        try:
            up = urllib.request.urlopen(req, timeout=UPSTREAM_TIMEOUT)
        except urllib.error.HTTPError as e:
            up = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            return self._json(502, {"error": {
                "message": f"Ollama ({UPSTREAM}) inacessível: {e}. "
                           "systemctl --user start ollama (ou verifique :11434)."}})
        try:
            self.send_response(up.status)
            for k, v in up.headers.items():
                if k.lower() not in _HOP_BY_HOP:
                    self.send_header(k, v)
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            while True:
                pedaco = up.read(8192)
                if not pedaco:
                    break
                self.wfile.write(f"{len(pedaco):X}\r\n".encode())
                self.wfile.write(pedaco)
                self.wfile.write(b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
        except (BrokenPipeError, ConnectionResetError):
            # cliente (OmniRoute) desconectou no meio -- abandona ESTA req em
            # silêncio, não derruba o servidor. Mesmo bug de (393) no seth_gateway.
            self.close_connection = True
        finally:
            up.close()

    def _json(self, code: int, obj: dict):
        self._raw(code, "application/json", json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _raw(self, code: int, ctype: str, corpo: bytes):
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True


def servir(host: str = BIND_HOST, port: int = BIND_PORT):
    srv = ThreadingHTTPServer((host, port), _Handler)
    print(f"seth_local_shim em http://{host}:{port}  ->  {UPSTREAM}/v1  "
          f"(modelo: {MODEL_ID} -> {MODEL})")
    srv.serve_forever()


# --------------------------------------------------------------------------- #
class _DummyOllama(BaseHTTPRequestHandler):
    ultimo_corpo = b""

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        type(self).ultimo_corpo = self.rfile.read(n)
        corpo = json.dumps({
            "model": "qwen3.5-9b-64k:latest",
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def _porta_livre() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _selftest() -> int:
    import threading
    import time

    global UPSTREAM
    porta_ollama = _porta_livre()
    UPSTREAM = f"http://127.0.0.1:{porta_ollama}"
    dummy = ThreadingHTTPServer(("127.0.0.1", porta_ollama), _DummyOllama)
    threading.Thread(target=dummy.serve_forever, daemon=True).start()

    porta_shim = _porta_livre()
    shim = ThreadingHTTPServer(("127.0.0.1", porta_shim), _Handler)
    threading.Thread(target=shim.serve_forever, daemon=True).start()
    time.sleep(0.2)

    falhas = []

    # /v1/models expõe 1 modelo só
    r = urllib.request.urlopen(f"http://127.0.0.1:{porta_shim}/v1/models", timeout=5)
    d = json.loads(r.read())
    if [m["id"] for m in d["data"]] != [MODEL_ID]:
        falhas.append(f"/v1/models devia listar só [{MODEL_ID}], listou {d['data']}")

    # /health não toca o upstream
    r = urllib.request.urlopen(f"http://127.0.0.1:{porta_shim}/health", timeout=5)
    if json.loads(r.read()).get("status") != "ok":
        falhas.append("/health não devolveu status ok")

    # POST força o model e repassa
    body = json.dumps({"model": "qualquer/coisa", "messages": [{"role": "user", "content": "oi"}]}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{porta_shim}/v1/chat/completions",
                                 data=body, headers={"Content-Type": "application/json"}, method="POST")
    r = urllib.request.urlopen(req, timeout=5)
    resp = r.read().decode()
    if '"content": "ok"' not in resp and '"content":"ok"' not in resp:
        falhas.append(f"POST não repassou a resposta do upstream: {resp[:200]}")
    enviado = json.loads(_DummyOllama.ultimo_corpo)
    if enviado.get("model") != MODEL:
        falhas.append(f"model devia ter sido forçado pra {MODEL!r}, foi {enviado.get('model')!r}")

    # rota desconhecida -> 404
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{porta_shim}/v1/embeddings", timeout=5)
        falhas.append("/v1/embeddings devia dar 404")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            falhas.append(f"/v1/embeddings devia dar 404, deu {e.code}")

    dummy.shutdown()
    shim.shutdown()
    if falhas:
        print("SELFTEST FALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    servir()
