#!/usr/bin/env python3
"""
P6-01 -- proxy READ-ONLY na frente do obsidian-local-rest-api.

O plugin `obsidian-local-rest-api` 5.1.0 NAO tem toggle global de read-only (confirmado no
`main.js`: so anotacoes `readOnlyHint` por tool MCP). Este proxy e' a trava:

  cliente -> 127.0.0.1:27125 (este proxy, SO leitura) -> 127.0.0.1:27124 (o plugin)

- `GET`/`HEAD`/`OPTIONS`  -> repassa.
- `POST /mcp/`            -> repassa SO se o JSON-RPC for metodo de leitura, ou
                            `tools/call` cujo `params.name` NAO cair no denylist de escrita.
- `PUT`/`PATCH`/`DELETE`  -> 403.
- `/commands/` (executa comando do Obsidian) -> 403 (qualquer metodo).
- Injeta o Bearer do `:27124` (lido de ~/.config/agata/obsidian.token) -- o cliente do
  proxy NAO precisa do segredo. O proxy so aceita loopback.

Streaming/SSE do `/mcp/` copiado byte a byte.

Uso:
  ro_proxy.py                # sobe em 127.0.0.1:27125
  ro_proxy.py --selftest     # sobe, bate GET (200) e PUT (403), imprime, sai
Env: OBS_UPSTREAM (default https://127.0.0.1:27124), OBS_BIND (default 127.0.0.1:27125),
     OBS_TOKEN_FILE (default ~/.config/agata/obsidian.token)
"""
import http.server
import json
import os
import ssl
import sys
import threading
import urllib.request

UPSTREAM = os.environ.get("OBS_UPSTREAM", "https://127.0.0.1:27124").rstrip("/")
BIND = os.environ.get("OBS_BIND", "127.0.0.1:27125")
TOKEN_FILE = os.environ.get("OBS_TOKEN_FILE", os.path.expanduser("~/.config/agata/obsidian.token"))

MCP_LEITURA = {
    "initialize", "notifications/initialized", "ping",
    "tools/list", "resources/list", "resources/read", "resources/templates/list",
    "prompts/list", "prompts/get", "completion/complete", "logging/setLevel",
}
DENY_TOOL_SUBSTR = ("put", "patch", "append", "delete", "post", "create", "write",
                    "execute", "command", "move", "rename", "trash", "insert", "replace")

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE  # cert self-signed do plugin, loopback


def _token():
    try:
        return open(TOKEN_FILE).read().strip()
    except OSError:
        return ""


def _bloqueia_mcp(body: bytes) -> str | None:
    """Retorna None se pode passar; senao a razao do 403."""
    try:
        req = json.loads(body or b"{}")
    except ValueError:
        return "corpo /mcp/ nao e' JSON"
    reqs = req if isinstance(req, list) else [req]
    for r in reqs:
        m = r.get("method", "")
        if m in MCP_LEITURA:
            continue
        if m == "tools/call":
            nome = (r.get("params", {}) or {}).get("name", "").lower()
            if any(s in nome for s in DENY_TOOL_SUBSTR):
                return f"tool de escrita bloqueada: {nome}"
            continue
        return f"metodo MCP nao-leitura bloqueado: {m or '(vazio)'}"
    return None


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _403(self, motivo):
        b = json.dumps({"error": "read_only_proxy", "motivo": motivo}).encode()
        self.send_response(403)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _repassa(self, metodo, corpo=None):
        url = UPSTREAM + self.path
        h = {k: v for k, v in self.headers.items()
             if k.lower() not in ("host", "authorization", "content-length", "connection")}
        h["Authorization"] = f"Bearer {_token()}"
        if corpo is not None:
            h["Content-Length"] = str(len(corpo))
        req = urllib.request.Request(url, data=corpo, method=metodo, headers=h)
        try:
            resp = urllib.request.urlopen(req, context=_CTX, timeout=120)
        except urllib.error.HTTPError as e:
            resp = e
        except Exception as e:  # noqa: BLE001
            self._403(f"upstream inacessivel: {e}")
            return
        self.send_response(resp.status)
        for k, v in resp.headers.items():
            if k.lower() not in ("transfer-encoding", "connection", "content-length"):
                self.send_header(k, v)
        data = resp.read()
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/commands"):
            return self._403("/commands/ nao e' leitura")
        self._repassa("GET")

    do_HEAD = do_GET

    def do_OPTIONS(self):
        self._repassa("OPTIONS")

    # POST permitido so em /mcp/ (filtrado) e nos endpoints de BUSCA (leitura pura)
    _POST_BUSCA = ("/search", "/search/", "/search/simple", "/search/simple/",
                   "/search/gui", "/search/gui/")

    def do_POST(self):
        n = int(self.headers.get("content-length", 0))
        corpo = self.rfile.read(n) if n else b""
        if self.path.rstrip("/") == "/mcp":
            motivo = _bloqueia_mcp(corpo)
            if motivo:
                return self._403(motivo)
            return self._repassa("POST", corpo)
        if self.path.split("?", 1)[0] in self._POST_BUSCA:
            return self._repassa("POST", corpo)
        return self._403(f"POST {self.path} nao permitido (so /mcp/ e /search/ de leitura)")

    def do_PUT(self):
        self._403("PUT bloqueado (proxy read-only)")

    do_PATCH = do_PUT
    do_DELETE = do_PUT

    def log_message(self, *a):
        pass


def _serve():
    host, port = BIND.split(":")
    srv = http.server.ThreadingHTTPServer((host, int(port)), Handler)
    srv.serve_forever()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = threading.Thread(target=_serve, daemon=True)
        t.start()
        import time
        time.sleep(0.6)
        base = f"http://{BIND}"
        def _c(m, p, d=None):
            r = urllib.request.Request(base + p, data=d, method=m)
            try:
                x = urllib.request.urlopen(r, timeout=15)
                return x.status, x.read()[:120]
            except urllib.error.HTTPError as e:
                return e.status, e.read()[:120]
        s1, b1 = _c("GET", "/")
        s2, b2 = _c("PUT", "/vault/x.md", b"x")
        s3, b3 = _c("POST", "/mcp/", b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"obsidian_put_content"}}')
        print(f"GET /            -> {s1}  {b1!r}")
        print(f"PUT /vault/x.md  -> {s2}  {b2!r}   (esperado 403)")
        print(f"POST /mcp/ (put) -> {s3}  {b3!r}   (esperado 403)")
        ok = s1 == 200 and s2 == 403 and s3 == 403
        print("SELFTEST", "OK" if ok else "FALHA")
        sys.exit(0 if ok else 1)
    _serve()
