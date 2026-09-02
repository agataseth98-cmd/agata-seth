#!/usr/bin/env python3
"""
openvino-whisper — STT na iGPU Intel via OpenVINO GenAI (Agata, Fase 2 / P2-02).

Serve POST /transcribe em 127.0.0.1:20130 (stdlib http.server, sem framework).
Modelo: distil-whisper IR int8 exportado por optimum-cli (ver P2-02 passo 2).
Long-form (>30 s): o WhisperPipeline do openvino-genai chunka internamente.

Uso:
  whisper_server.py                          # sobe o serviço (device do env OVW_DEVICE, default GPU)
  whisper_server.py --selftest a.wav         # transcreve, imprime {text, rtf}, sai
  whisper_server.py --selftest a.wav --device CPU   # p/ comparar RTF iGPU vs CPU
  whisper_server.py --model DIR              # sobrescreve o diretorio do modelo

Env:
  OVW_MODEL_DIR   diretorio do IR (default ~/.cache/agata/openvino/whisper/distil-small.en-int8)
  OVW_DEVICE      GPU (default) | CPU | GPU.0 ...
  OVW_BIND        host:porta (default 127.0.0.1:20130)
"""
import io
import json
import os
import sys
import time
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

HOME = os.path.expanduser("~")
# IR OpenVINO pre-convertido (OpenVINO/whisper-base-int8-ov) -- multilingue (o canon e' PT-BR),
# int8, RTF ~0.08 na iGPU. distil-small.en foi descartado: English-only e o optimum-cli export
# esta quebrado (bug do optimum 2.3.0). whisper-small-int8-ov e' o upgrade drop-in (RTF ~0.21).
DEFAULT_MODEL = os.path.join(HOME, ".cache/agata/openvino/whisper/whisper-base-int8-ov")
MODEL_DIR = os.environ.get("OVW_MODEL_DIR", DEFAULT_MODEL)
# OpenVINO enumera a iGPU Intel como GPU.0 e a dGPU NVIDIA como GPU.1 nesta maquina;
# fixamos GPU.0 para nunca cair na 4060 (o objetivo da Fase 2 e' tirar carga dela).
DEVICE = os.environ.get("OVW_DEVICE", "GPU.0")
BIND = os.environ.get("OVW_BIND", "127.0.0.1:20130")

_PIPE = None
_PIPE_DEVICE = None


def _load_pipe(device):
    """Carrega (uma vez) o WhisperPipeline no device pedido."""
    global _PIPE, _PIPE_DEVICE
    if _PIPE is not None and _PIPE_DEVICE == device:
        return _PIPE
    import openvino_genai  # import tardio: erro claro se o venv estiver incompleto
    t0 = time.time()
    _PIPE = openvino_genai.WhisperPipeline(MODEL_DIR, device=device)
    _PIPE_DEVICE = device
    sys.stderr.write(f"[whisper] modelo carregado em {device} em {time.time()-t0:.1f}s ({MODEL_DIR})\n")
    sys.stderr.flush()
    return _PIPE


def _read_audio_16k_mono(raw_bytes):
    """WAV bytes -> (float32 mono 16 kHz, duracao_s). Reamostra se preciso."""
    with wave.open(io.BytesIO(raw_bytes), "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        pcm = w.readframes(n)
    if sw != 2:
        # caminho raro: delega ao soundfile
        import soundfile as sf
        data, sr = sf.read(io.BytesIO(raw_bytes), dtype="float32", always_2d=True)
        audio = data.mean(axis=1)
    else:
        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        if ch > 1:
            audio = audio.reshape(-1, ch).mean(axis=1)
    if sr != 16000:
        import librosa
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
        sr = 16000
    return np.ascontiguousarray(audio, dtype=np.float32), len(audio) / 16000.0


def transcribe(raw_bytes, device=None):
    device = device or DEVICE
    audio, audio_s = _read_audio_16k_mono(raw_bytes)
    pipe = _load_pipe(device)
    t0 = time.time()
    res = pipe.generate(audio, return_timestamps=True)
    proc_s = time.time() - t0
    chunks = []
    for c in (getattr(res, "chunks", None) or []):
        chunks.append({"text": c.text, "start": round(c.start_ts, 2), "end": round(c.end_ts, 2)})
    return {
        "text": str(res).strip(),
        "chunks": chunks,
        "audio_s": round(audio_s, 2),
        "proc_s": round(proc_s, 2),
        "rtf": round(proc_s / audio_s, 3) if audio_s else None,
        "device": device,
        "model": MODEL_DIR,
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "device": _PIPE_DEVICE or DEVICE, "model": MODEL_DIR})
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/transcribe":
            self._send(404, {"error": "not_found"})
            return
        n = int(self.headers.get("content-length", 0))
        raw = self.rfile.read(n)
        ctype = self.headers.get("content-type", "")
        try:
            if ctype.startswith("application/json"):
                req = json.loads(raw)
                path = req.get("path")
                if not path:
                    self._send(400, {"error": "json body needs 'path' (or POST raw wav bytes)"})
                    return
                with open(os.path.expanduser(path), "rb") as f:
                    raw = f.read()
            self._send(200, transcribe(raw))
        except FileNotFoundError as e:
            self._send(400, {"error": "file_not_found", "detail": str(e)})
        except Exception as e:  # noqa: BLE001 — devolve o erro, nao derruba o serviço
            self._send(500, {"error": type(e).__name__, "detail": str(e)})

    def log_message(self, *a):  # silencia o log por request no stderr
        pass


def _selftest(path, device):
    with open(os.path.expanduser(path), "rb") as f:
        raw = f.read()
    out = transcribe(raw, device=device)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\nRTF={out['rtf']}  ({out['proc_s']}s de processo / {out['audio_s']}s de audio) em {out['device']}")
    return 0 if (out["rtf"] is not None and out["rtf"] < 1.0) else 1


def main():
    args = sys.argv[1:]
    device = DEVICE
    if "--device" in args:
        i = args.index("--device")
        device = args[i + 1]
        del args[i:i + 2]
    if "--model" in args:
        i = args.index("--model")
        global MODEL_DIR
        MODEL_DIR = os.path.expanduser(args[i + 1])
        del args[i:i + 2]
    if args and args[0] == "--selftest":
        sys.exit(_selftest(args[1], device))
    host, port = BIND.split(":")
    _load_pipe(device)  # carrega antes de aceitar request (falha cedo)
    srv = ThreadingHTTPServer((host, int(port)), Handler)
    sys.stderr.write(f"[whisper] ouvindo em http://{host}:{port}  device={device}\n")
    sys.stderr.flush()
    srv.serve_forever()


if __name__ == "__main__":
    main()
