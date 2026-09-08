#!/usr/bin/env python3
"""Shim OpenAI-compat pra Piper TTS -- voz pt-BR local, rápida, sem GPU.

Motivo (MEMÓRIAS (387)): as vozes pt-BR do Kokoro (`pf_dora` etc.) não têm
nota de qualidade no model card oficial e pronunciam português errado
("transcreve errado", relato do Humano no teste da Seth). Kokoro seguia em
CPU numa máquina com RTX 4060 -> também lento. Piper `pt_BR-faber-medium`
(corpus CML-TTS, treino real de pt-BR) resolve os dois: RTF ~0,13 em CPU,
zero VRAM, então não briga com o cérebro local da Seth (`qwen3.5-9b-64k`,
que ocupa ~90% da 4060 quando gera).

Fala só o dialeto OpenAI que o LibreChat usa:
  POST /v1/audio/speech  {input, voice?, response_format?, speed?}
  GET  /health
  GET  /v1/models

Zero dependência além do que já está no venv do Piper + ffmpeg (conversão de
formato). Um processo `piper` por requisição (curto -- o modelo carrega em
~0,2s). NÃO faz streaming: devolve o buffer inteiro. Loopback só.

Env:
  PIPER_TTS_PORT   porta (default 8890)
  PIPER_TTS_HOST   host  (default 127.0.0.1 -- não expor)
  PIPER_MODEL      caminho do .onnx (default: voices/pt_BR-faber-medium.onnx ao lado deste arquivo)
  PIPER_PYTHON     python do venv do Piper (default: tts-piper/.venv/bin/python ao lado deste arquivo)
"""
import json
import os
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

AQUI = os.path.dirname(os.path.abspath(__file__))
HOST = os.environ.get("PIPER_TTS_HOST", "127.0.0.1")
PORT = int(os.environ.get("PIPER_TTS_PORT", "8890"))
MODEL = os.environ.get("PIPER_MODEL", os.path.join(AQUI, "tts-piper", "voices", "pt_BR-faber-medium.onnx"))
PYTHON = os.environ.get("PIPER_PYTHON", os.path.join(AQUI, "tts-piper", ".venv", "bin", "python"))
FFMPEG = shutil.which("ffmpeg")

# sample_rate vem do .json ao lado do modelo (Piper grava isso lá).
try:
    with open(MODEL + ".json", encoding="utf-8") as f:
        SAMPLE_RATE = int(json.load(f)["audio"]["sample_rate"])
except Exception:  # noqa: BLE001 -- default do medium
    SAMPLE_RATE = 22050

# response_format -> (args de saída do ffmpeg, mime). "wav" não passa por ffmpeg.
FORMATOS = {
    "mp3": (["-f", "mp3", "-b:a", "128k"], "audio/mpeg"),
    "opus": (["-f", "opus"], "audio/opus"),
    "aac": (["-f", "adts"], "audio/aac"),
    "flac": (["-f", "flac"], "audio/flac"),
    "wav": (None, "audio/wav"),
    "pcm": (None, "audio/L16"),
}


def sintetizar(texto, speed=1.0):
    """texto -> PCM s16le mono cru (bytes). speed 1.0 = natural; >1 acelera."""
    length_scale = 1.0 / speed if speed and speed > 0 else 1.0
    proc = subprocess.run(
        [PYTHON, "-m", "piper", "-m", MODEL, "--output-raw",
         "--length-scale", f"{length_scale:.4f}"],
        input=texto.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace")[:500])
    return proc.stdout


def para_formato(pcm, fmt):
    """PCM cru -> bytes no formato pedido. wav/pcm sem ffmpeg; resto via ffmpeg."""
    if fmt == "pcm":
        return pcm
    if fmt == "wav" or not FFMPEG:
        # embrulha o PCM num header WAV mínimo (44 bytes), sem ffmpeg
        import struct
        n = len(pcm)
        hdr = b"RIFF" + struct.pack("<I", 36 + n) + b"WAVEfmt " + struct.pack(
            "<IHHIIHH", 16, 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16
        ) + b"data" + struct.pack("<I", n)
        return hdr + pcm
    args, _ = FORMATOS[fmt]
    out = subprocess.run(
        [FFMPEG, "-hide_banner", "-loglevel", "error",
         "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-i", "-",
         *args, "-"],
        input=pcm, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
    )
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace")[:500])
    return out.stdout


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _json(self, code, obj):
        corpo = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *a):  # silencia o log por request
        pass

    def do_GET(self):
        if self.path.rstrip("/") == "/health":
            return self._json(200, {"status": "ok", "engine": "piper",
                                    "model": os.path.basename(MODEL),
                                    "sample_rate": SAMPLE_RATE, "ffmpeg": bool(FFMPEG)})
        if self.path.rstrip("/") == "/v1/models":
            return self._json(200, {"object": "list", "data": [
                {"id": "tts-1", "object": "model", "owned_by": "piper"},
                {"id": "tts-1-hd", "object": "model", "owned_by": "piper"},
                {"id": "piper", "object": "model", "owned_by": "piper"},
            ]})
        return self._json(404, {"error": {"message": "not found", "type": "not_found"}})

    def do_POST(self):
        if self.path.rstrip("/") not in ("/v1/audio/speech", "/audio/speech"):
            return self._json(404, {"error": {"message": "not found", "type": "not_found"}})
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception:  # noqa: BLE001
            return self._json(400, {"error": {"message": "corpo não é JSON", "type": "invalid_request_error"}})

        texto = (req.get("input") or "").strip()
        if not texto:
            return self._json(400, {"error": {"message": "campo 'input' vazio", "type": "invalid_request_error"}})
        fmt = (req.get("response_format") or "mp3").lower()
        if fmt not in FORMATOS:
            fmt = "mp3"
        try:
            speed = float(req.get("speed", 1.0))
        except (TypeError, ValueError):
            speed = 1.0

        # `voice` é ignorado de propósito: o modelo pt_BR-faber-medium tem 1
        # locutor. Fica no shape só pra não quebrar o cliente. Multi-voz =
        # trocar o modelo por um multi-speaker e mapear aqui.
        try:
            pcm = sintetizar(texto, speed)
            audio = para_formato(pcm, fmt)
        except Exception as e:  # noqa: BLE001
            return self._json(500, {"error": {"message": f"piper falhou: {e}", "type": "server_error"}})

        _, mime = FORMATOS[fmt]
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(audio)))
        self.end_headers()
        self.wfile.write(audio)


def main():
    if not os.path.exists(MODEL):
        print(f"ABORTADO: modelo não encontrado em {MODEL}. Rode tts-piper/instalar.sh.", file=sys.stderr)
        return 1
    if not os.path.exists(PYTHON):
        print(f"ABORTADO: python do venv não encontrado em {PYTHON}. Rode tts-piper/instalar.sh.", file=sys.stderr)
        return 1
    srv = ThreadingHTTPServer((HOST, PORT), H)
    print(f"piper-tts: {HOST}:{PORT} · modelo {os.path.basename(MODEL)} · {SAMPLE_RATE}Hz · ffmpeg={'sim' if FFMPEG else 'não'}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
