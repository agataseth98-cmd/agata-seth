#!/usr/bin/env python3
"""seth_gateway.py — reidrata a Seth antes do OmniRoute.

Fica entre o frontend (Open WebUI, Goose, curl) e o proxy de sanitização.
Escuta em 127.0.0.1:20126. Em cada POST /v1/chat/completions, se ainda não
houver uma mensagem de sistema hidratada, **antepõe** o conteúdo de
`.hidrata-seth.md` (REGRAS + PROJETO + janela de MEMÓRIAS, silo seth) como
mensagem `system` e repassa para :20127 (que sanitiza segredo) -> OmniRoute.

Assim qualquer frontend que apontar para :20126 fala com a Seth hidratada,
sem o Hermes. GET (/v1/models, /health) e streaming passam direto.

Só stdlib. Não instala nada, não lê chave nenhuma.

Uso:
    python3 redesign/router/seth_gateway.py
        # frontend aponta para http://127.0.0.1:20126

    python3 redesign/router/seth_gateway.py --selftest
        # sobe upstream dummy + gateway; manda 1 pedido sem system e confere
        # que o corpo repassado ganhou a mensagem system hidratada. exit 0 = OK.

Env:
    SETH_UPSTREAM        default http://127.0.0.1:20127   (o proxy sanitizador)
    SETH_BIND            default 127.0.0.1:20126
    SETH_HIDRATA         default ~/agata/.hidrata-seth.md
    SETH_HIDRATA_MODO    compacto (default) | full
        compacto -> cabeçalho curto + estado atual (estado_para_eco.sh) + ponteiro
                    p/ query_canon. Rápido, sem estourar o deadline do OmniRoute.
        full     -> injeta o .hidrata-seth.md inteiro (~45k tokens). Só com um
                    modelo de janela grande E o deadline do OmniRoute folgado.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

UPSTREAM = os.environ.get("SETH_UPSTREAM", "http://127.0.0.1:20127").rstrip("/")
_bind = os.environ.get("SETH_BIND", "127.0.0.1:20126")
BIND_HOST, BIND_PORT = _bind.split(":")[0], int(_bind.split(":")[1])
HIDRATA_PATH = Path(os.environ.get(
    "SETH_HIDRATA", str(Path.home() / "agata" / ".hidrata-seth.md")))
MODO = os.environ.get("SETH_HIDRATA_MODO", "compacto").lower()
REPO = Path(os.environ.get("SETH_REPO", str(Path.home() / "agata")))

# --- marcador amarrado a hash (achado 04/09/2026, Camada C) ----------------
# A versão anterior usava uma string fixa: qualquer system message que o
# CLIENTE mandasse contendo essa string era aceito como "já hidratado", sem
# nada ligando o marcador à injeção real deste gateway. Um cliente direto em
# :20126 (fora do LibreChat, ex.: um Goose mal configurado ou um teste solto)
# podia mandar só a linha do marcador e pular a hidratação inteira, olhando
# hidratado pro resto do pipeline sem estar. Agora o marcador carrega um hash
# do texto-fonte deste módulo (a doutrina fixa, não o bloco "Estado agora"
# que varia a cada chamada -- hashear isso forçaria reinjeção every turn,
# acumulando system messages). Não é defesa contra quem lê este arquivo (não
# há segredo aqui, é loopback) -- é o mesmo tipo de trava que P-8 documenta
# pra si mesmo: fecha o descuido/bug, não o contorno deliberado por quem já
# tem acesso ao código-fonte. Efeito colateral bom: também pega REDEPLOY —
# se este módulo mudar a doutrina, o hash muda, e uma conversa em andamento
# com o marcador velho volta a ser reidratada em vez de ficar presa à versão
# antiga pro resto da sessão.
_DOUTRINA_FIXA = (
    "Você é a **Seth**, o modelo do sistema **Agata** — governança pessoal "
    "canônica em git (REGRAS, PROJETO, MEMÓRIAS, append-only). Papéis: o "
    "**Humano decide**, você **propõe**, a Máquina arbitra fatos (rodando o "
    "comando, não afirmando de memória). Nada muda o canon sem passar pelo "
    "**portão** (as 3 perguntas). Não bajule, não simule emoção, não afirme "
    "sem fonte, não diga ter feito o que não fez.\n\n"
    "**Regra 1 — abra toda resposta com:** modelo que você é · turno (conte no "
    "contexto) · última entrada de MEMÓRIAS que leu (nº + título) · o que está "
    "quebrado (ou `pronto.`).\n\n"
    "O canon inteiro está no repositório; **não assuma o conteúdo** — peça o "
    "trecho com a tool `query_canon` (ou peça ao Humano). Este cabeçalho é a "
    "hidratação mínima; o resto é sob demanda.\n\n"
)
_HASH_DOUTRINA = hashlib.sha256(_DOUTRINA_FIXA.encode("utf-8")).hexdigest()[:8]
MARCADOR = f"<!-- SETH:HIDRATADO:{_HASH_DOUTRINA} -->"

_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}

_CACHE: dict = {"mtime": None, "texto": ""}


def _estado() -> str:
    """Saída curta de scripts/estado_para_eco.sh (HEAD, topo de MEMÓRIAS, sync).
    Best-effort — se falhar, devolve string vazia."""
    import subprocess
    try:
        r = subprocess.run(["bash", "scripts/estado_para_eco.sh"], cwd=REPO,
                           capture_output=True, text=True, timeout=15)
        linhas = [l for l in r.stdout.splitlines()
                  if l.startswith(("HEAD:", "TOPO-MEMÓRIAS:", "sync:", "HASH-ESTADO:"))]
        return "\n".join(linhas)
    except Exception:
        return ""


def _hidratacao() -> str:
    """Modo compacto (default): cabeçalho + estado atual. Modo full: o arquivo inteiro."""
    if MODO == "compacto":
        est = _estado()
        # Regra 1.1: campo medível não pode sumir em silêncio quando a
        # medição falha -- antes, `est` vazio só omitia o bloco inteiro sem
        # dizer que algo quebrou (achado 04/09/2026, Camada C).
        bloco_estado = (
            f"**Estado agora (fatos da Máquina):**\n{est}\n" if est
            else "**Estado agora:** `lacuna: estado_para_eco.sh falhou ou não rodou "
                 "(sem shell/Máquina daqui?) — não afirme HEAD/sync sem medir.`\n"
        )
        return f"{MARCADOR}\n{_DOUTRINA_FIXA}{bloco_estado}"
    try:
        st = HIDRATA_PATH.stat()
        if _CACHE["mtime"] != st.st_mtime:
            _CACHE["texto"] = HIDRATA_PATH.read_text(encoding="utf-8")
            _CACHE["mtime"] = st.st_mtime
    except OSError:
        return f"{MARCADOR}\n(hidratação indisponível: {HIDRATA_PATH} não pôde ser lido)"
    return f"{MARCADOR}\n" + _CACHE["texto"]


def _injeta(payload: dict) -> dict:
    msgs = payload.get("messages")
    if not isinstance(msgs, list):
        return payload
    # já hidratado nesta conversa? não repete.
    for m in msgs:
        if isinstance(m, dict) and m.get("role") == "system" \
           and isinstance(m.get("content"), str) and MARCADOR in m["content"]:
            return payload
    sys_msg = {"role": "system", "content": _hidratacao()}
    # se o frontend já mandou um system próprio, o nosso entra ANTES dele
    payload["messages"] = [sys_msg] + msgs
    return payload


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        self._passar(b"", "GET")

    def do_HEAD(self):
        self._passar(b"", "HEAD")

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        corpo = self.rfile.read(n) if n else b""
        ctype = (self.headers.get("Content-Type") or "").lower()
        if "application/json" in ctype and corpo and "/chat/completions" in self.path:
            try:
                payload = json.loads(corpo)
            except ValueError:
                return self._erro(400, "corpo marcado como JSON mas não parseia")
            if isinstance(payload, dict):
                corpo = json.dumps(_injeta(payload), ensure_ascii=False).encode("utf-8")
        self._passar(corpo, "POST")

    def _passar(self, corpo: bytes, metodo: str):
        url = UPSTREAM + self.path
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in _HOP_BY_HOP}
        req = urllib.request.Request(url, data=corpo or None, method=metodo, headers=headers)
        try:
            up = urllib.request.urlopen(req, timeout=300)
        except urllib.error.HTTPError as e:
            up = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            return self._erro(502, f"upstream ({UPSTREAM}) inacessível: {e}. "
                                   "Suba o sanitizador: systemctl --user start omniroute-sanitizer omniroute")
        self.send_response(up.status)
        for k, v in up.headers.items():
            if k.lower() not in _HOP_BY_HOP:
                self.send_header(k, v)
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

    def _erro(self, code: int, msg: str):
        corpo = json.dumps({"error": {"type": "seth_gateway_error", "message": msg}},
                           ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def servir(host: str = BIND_HOST, port: int = BIND_PORT):
    srv = ThreadingHTTPServer((host, port), _Handler)
    print(f"seth_gateway em http://{host}:{port}  ->  {UPSTREAM}  "
          f"(hidratação: {MODO}, {HIDRATA_PATH.name})")
    srv.serve_forever()


# --------------------------------------------------------------------------- #
def _porta_livre() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class _Dummy(BaseHTTPRequestHandler):
    ultimo_corpo = b""

    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        type(self).ultimo_corpo = self.rfile.read(n)
        corpo = json.dumps({"choices": [{"message": {"role": "assistant", "content": "ok"}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


def _selftest() -> int:
    global UPSTREAM
    up_port, gw_port = _porta_livre(), _porta_livre()
    UPSTREAM = f"http://127.0.0.1:{up_port}"
    up = ThreadingHTTPServer(("127.0.0.1", up_port), _Dummy)
    gw = ThreadingHTTPServer(("127.0.0.1", gw_port), _Handler)
    threading.Thread(target=up.serve_forever, daemon=True).start()
    threading.Thread(target=gw.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{gw_port}/v1/chat/completions"
    falhas = 0

    # 1. pedido sem system -> o corpo repassado ao upstream ganha 1 system hidratado
    body = json.dumps({"model": "seth", "messages": [{"role": "user", "content": "oi"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body, headers={"Content-Type": "application/json"}), timeout=10).read()
    repassado = json.loads(_Dummy.ultimo_corpo)
    m = repassado["messages"]
    ok = (m[0]["role"] == "system" and MARCADOR in m[0]["content"]
          and m[1]["role"] == "user" and len(m) == 2)
    print(f"{'PASS' if ok else 'FALHA'}  sem system -> injetou 1 system hidratado antes do user "
          f"({len(m[0]['content'])} chars)")
    falhas += 0 if ok else 1

    # 2. pedido JÁ hidratado -> não repete
    body2 = json.dumps({"model": "seth", "messages": [
        {"role": "system", "content": f"{MARCADOR}\nx"},
        {"role": "user", "content": "oi"}]}).encode()
    urllib.request.urlopen(urllib.request.Request(
        base, data=body2, headers={"Content-Type": "application/json"}), timeout=10).read()
    m2 = json.loads(_Dummy.ultimo_corpo)["messages"]
    ok2 = len(m2) == 2 and m2[0]["content"] == f"{MARCADOR}\nx"
    print(f"{'PASS' if ok2 else 'FALHA'}  já hidratado -> não repetiu (messages={len(m2)})")
    falhas += 0 if ok2 else 1

    up.shutdown()
    gw.shutdown()
    print(f"\n{'SELFTEST OK' if not falhas else f'SELFTEST FALHOU ({falhas})'}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        raise SystemExit(_selftest())
    servir()
