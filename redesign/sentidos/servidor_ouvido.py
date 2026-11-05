#!/usr/bin/env python3
"""Servidor do ouvido (5 sentidos): transcrição compatível com OpenAI para o LibreChat falar por voz.

POST /v1/audio/transcriptions (multipart/form-data, campo de arquivo `file`, opcional `language`)
→ {"text": "..."}. GET /health → {"ok": true, "motor": ...}. Usa `ouvido.transcrever` (lfm3-audio pelo
Ollama, Whisper da iGPU de reserva se já estiver no ar). Escuta só em 127.0.0.1:20137; o LibreChat
chega pelo relé `librechat-ponte-host` em 172.29.7.1:20137 (config/portas-agata.txt).

Não exige chave (loopback e bridge local, como o piper em :8890). Limite de 25 MB por áudio. O áudio
vai para um temporário e é apagado; o texto não é registrado em log. A voz do sistema não muda: a
fala continua no piper `agata-last` (:8890).

Uso: servidor_ouvido.py            (sobe o serviço; porta em AGATA_OUVIDO_PORTA, padrão 20137)
     servidor_ouvido.py --selftest
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from email.parser import BytesParser
from email.policy import HTTP
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import ouvido  # noqa: E402

HOST = "127.0.0.1"
PORTA = int(os.environ.get("AGATA_OUVIDO_PORTA", "20137"))
LIMITE = 25 * 1024 * 1024
IDIOMAS = {"pt": "Portuguese", "pt-br": "Portuguese", "portuguese": "Portuguese", "portuguese (brazil)": "Portuguese",
           "en": "English", "en-us": "English", "english": "English", "es": "Spanish", "spanish": "Spanish"}


def ler_multipart(ctype: str, corpo: bytes) -> tuple[bytes | None, dict]:
    """Devolve (bytes do arquivo, campos de texto). Só multipart/form-data."""
    if not ctype.lower().startswith("multipart/form-data"):
        raise ValueError("esperado multipart/form-data")
    msg = BytesParser(policy=HTTP).parsebytes(b"Content-Type: " + ctype.encode() + b"\r\n\r\n" + corpo)
    arquivo, campos = None, {}
    for parte in msg.iter_parts():
        nome = parte.get_param("name", header="content-disposition")
        if parte.get_filename() is not None or nome == "file":
            if arquivo is None:
                arquivo = parte.get_payload(decode=True)
        elif nome:
            campos[nome] = (parte.get_payload(decode=True) or b"").decode(errors="replace").strip()[:100]
    return arquivo, campos


def idioma(campos: dict) -> str:
    return IDIOMAS.get((campos.get("language") or "pt").lower(), "Portuguese")


def ler_corpo(rfile, headers) -> bytes:
    """Corpo da requisição: Content-Length, ou Transfer-Encoding: chunked (o Node/LibreChat envia assim,
    sem Content-Length; sem isto a voz do LibreChat dava 411). Levanta ValueError com a razão."""
    if "chunked" in (headers.get("Transfer-Encoding") or "").lower():
        out = bytearray()
        while True:
            linha = rfile.readline(64)
            if not linha:
                raise ValueError("corpo chunked truncado")
            try:
                tam = int(linha.split(b";")[0].strip(), 16)
            except ValueError:
                raise ValueError("chunk inválido")
            if tam == 0:
                while rfile.readline(1024) not in (b"\r\n", b"\n", b""):
                    pass
                return bytes(out)
            if len(out) + tam > LIMITE:
                raise ValueError("corpo grande demais")
            falta = tam
            while falta:
                bloco = rfile.read(falta)
                if not bloco:
                    raise ValueError("corpo chunked truncado")
                out += bloco
                falta -= len(bloco)
            rfile.readline(2)
    try:
        n = int(headers.get("Content-Length") or 0)
    except ValueError:
        raise ValueError("Content-Length inválido")
    if n <= 0:
        raise ValueError("tamanho inválido")
    if n > LIMITE:
        raise ValueError("corpo grande demais")
    return rfile.read(n)


class Handler(BaseHTTPRequestHandler):
    transcrever = staticmethod(ouvido.transcrever)

    def _send(self, code: int, obj: dict) -> None:
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True, "motor": ouvido.MODELO, "reserva": "whisper (iGPU, se no ar)"})
        return self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self.path.split("?")[0] != "/v1/audio/transcriptions":
            return self._send(404, {"error": "not_found"})
        try:
            corpo = ler_corpo(self.rfile, self.headers)
        except ValueError as e:
            return self._send(413 if "grande" in str(e) else 411, {"error": str(e)})
        try:
            dados, campos = ler_multipart(self.headers.get("Content-Type", ""), corpo)
        except ValueError as e:
            return self._send(400, {"error": str(e)})
        if not dados:
            return self._send(400, {"error": "sem arquivo de áudio (campo file)"})
        with tempfile.TemporaryDirectory(prefix="ouvido-srv-") as tmp:
            arq = Path(tmp) / "entrada"
            arq.write_bytes(dados)
            try:
                r = self.transcrever(arq, idioma=idioma(campos))
            except Exception as e:  # noqa: BLE001 — erro de conversão (áudio inválido) não derruba o serviço
                return self._send(422, {"error": f"áudio não processado: {e.__class__.__name__}"})
        if not r.get("text"):
            return self._send(503, {"error": r.get("erro") or "nenhum motor transcreveu"})
        return self._send(200, {"text": r["text"]})

    def log_message(self, *a):  # sem log por pedido: o texto da fala não vai para o journal
        pass


def _selftest() -> int:
    import threading
    import urllib.request
    import uuid

    class Falso(Handler):
        transcrever = staticmethod(lambda arq, idioma="Portuguese": {"text": f"ok:{idioma}:{arq.stat().st_size}"})
    srv = ThreadingHTTPServer((HOST, 0), Falso)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    porta = srv.server_address[1]
    b = uuid.uuid4().hex
    corpo = (f"--{b}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\nlfm3-audio\r\n"
             f"--{b}\r\nContent-Disposition: form-data; name=\"language\"\r\n\r\nen\r\n"
             f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.webm\"\r\n"
             f"Content-Type: audio/webm\r\n\r\n").encode() + b"\x01\x02\x03" + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(f"http://{HOST}:{porta}/v1/audio/transcriptions", data=corpo,
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    r = json.loads(urllib.request.urlopen(req, timeout=5).read())
    ok = r == {"text": "ok:English:3"}
    print("PASS" if ok else f"FALHA {r}", "multipart OpenAI → texto")
    import http.client  # chunked, como o Node/LibreChat envia (sem Content-Length)
    conn = http.client.HTTPConnection(HOST, porta, timeout=5)
    conn.request("POST", "/v1/audio/transcriptions", body=iter([corpo[:40], corpo[40:]]),
                 headers={"Content-Type": f"multipart/form-data; boundary={b}"}, encode_chunked=True)
    r2 = json.loads(conn.getresponse().read())
    ok2 = r2 == {"text": "ok:English:3"}
    print("PASS" if ok2 else f"FALHA chunked {r2}", "chunked sem Content-Length → texto")
    ok = ok and ok2
    srv.shutdown()
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    srv = ThreadingHTTPServer((HOST, PORTA), Handler)
    print(f"[ouvido] ouvindo em http://{HOST}:{PORTA}  motor={ouvido.MODELO}", flush=True)
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
