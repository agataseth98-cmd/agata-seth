#!/usr/bin/env python3
"""Ouvido do Agata (projeto 5 sentidos, nova versão, lote 4 item 1): fala → texto, tudo local.

Motor principal: `lfm3-audio:2b` (Liquid AI) pelo Ollama local. Reserva: o Whisper da iGPU
(`redesign/igpu/whisper_server.py`, porta 20130), só se o serviço já estiver no ar. Este módulo não liga
serviço nenhum (decisão de 29/10: tudo sob demanda).

Medido em 05/11/2026 (20 frases da voz do sistema, `medir_ouvido.py`): lfm3-audio teve WER de 3,4%
(limpo) e 4,0% (com ruído), com 0,14 s por frase; o Whisper base teve 18% e 0,6 s.
A instrução de transcrever vai como mensagem de SISTEMA, como no card oficial. Na mensagem do usuário
o modelo entra em laço e o Ollama aborta com "token repeat limit". O áudio vai em base64 no campo
`images` da mensagem (o campo `audio` dá 500 no Ollama 0.40.14).

Só ouve: a voz do sistema continua o piper `pt_BR-agata-last` (`scripts/agata_falar.py`); este módulo
nunca gera fala. O áudio não sai da Máquina; nada é gravado além do arquivo temporário convertido.

Uso: ouvido.py ARQUIVO [--motor auto|lfm3|whisper] [--idioma Portuguese]     |     --selftest
Saída: JSON {text, motor, proc_s, audio_s, falha_etapa, erro}. Exit 0 = transcreveu; 3 = nenhum motor.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA = os.environ.get("AGATA_OLLAMA", "http://127.0.0.1:11434")
MODELO = os.environ.get("AGATA_OUVIDO_MODELO", "lfm3-audio:2b")
WHISPER = os.environ.get("AGATA_WHISPER", "http://127.0.0.1:20130")
PASTA_WHISPER = Path(os.path.realpath(os.path.expanduser(
    os.environ.get("OVW_PASTA_ENTRADA", "~/.cache/agata/whisper-entrada"))))
MOTORES = ("auto", "lfm3", "whisper")
MAX_BYTES = 50 * 1024 * 1024


def _post(url: str, corpo: dict, timeout: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def para_16k(origem: Path, destino: Path) -> float | None:
    """Converte para wav mono 16 kHz (o que os dois motores esperam). Devolve a duração em segundos."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg ausente")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(origem), "-ar", "16000", "-ac", "1", str(destino)],
                   check=True, timeout=60, stdin=subprocess.DEVNULL)
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(destino)],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        return round(float(out), 2)
    except (ValueError, OSError, subprocess.SubprocessError):
        return None


def lfm3(wav16: Path, idioma: str = "Portuguese", *, post=None, timeout: int = 120) -> str:
    post = post or _post
    b = base64.b64encode(wav16.read_bytes()).decode()
    d = post(f"{OLLAMA}/api/chat", {"model": MODELO, "stream": False, "keep_alive": "10m",
                                    "messages": [{"role": "system", "content": f"Perform ASR in {idioma}."},
                                                 {"role": "user", "content": "", "images": [b]}]}, timeout)
    return ((d.get("message") or {}).get("content") or "").strip()


def whisper_no_ar(get=None) -> bool:
    try:
        (get or urllib.request.urlopen)(f"{WHISPER}/", timeout=2)
        return True
    except urllib.error.HTTPError:
        return True          # respondeu (404 na raiz): está no ar
    except Exception:  # noqa: BLE001
        return False


def whisper(wav16: Path, *, post=None, timeout: int = 120) -> str:
    """Usa o servidor existente pelo caminho permitido (OVW_PASTA_ENTRADA), sem mexer nele."""
    post = post or _post
    PASTA_WHISPER.mkdir(parents=True, exist_ok=True)
    fd, nome = tempfile.mkstemp(suffix=".wav", dir=PASTA_WHISPER)
    os.close(fd)
    try:
        shutil.copyfile(wav16, nome)
        return (post(f"{WHISPER}/transcribe", {"path": nome}, timeout).get("text") or "").strip()
    finally:
        os.remove(nome)


def transcrever(arquivo: str | Path, *, motor: str = "auto", idioma: str = "Portuguese",
                chamar_lfm3=None, chamar_whisper=None, whisper_ativo=None) -> dict:
    if motor not in MOTORES:
        raise ValueError("motor fora da lista")
    origem = Path(arquivo)
    if not origem.is_file() or origem.stat().st_size > MAX_BYTES:
        raise ValueError("arquivo ausente ou grande demais")
    chamar_lfm3 = chamar_lfm3 or lfm3
    chamar_whisper = chamar_whisper or whisper
    ativo = whisper_ativo or whisper_no_ar
    with tempfile.TemporaryDirectory(prefix="ouvido-") as tmp:
        wav = Path(tmp) / "16k.wav"
        audio_s = para_16k(origem, wav)
        tentativas = []
        ordem = {"auto": ("lfm3", "whisper"), "lfm3": ("lfm3",), "whisper": ("whisper",)}[motor]
        for m in ordem:
            if m == "whisper" and not ativo():
                tentativas.append({"motor": m, "falha_etapa": "indisponivel", "erro": "whisper fora do ar (sob demanda)"})
                continue
            t0 = time.monotonic()
            try:
                texto = chamar_lfm3(wav, idioma) if m == "lfm3" else chamar_whisper(wav)
            except urllib.error.HTTPError as e:
                corpo = e.read()[:200].decode(errors="replace") if hasattr(e, "read") else ""
                tentativas.append({"motor": m, "falha_etapa": "execucao", "erro": f"HTTP {e.code}: {corpo}"})
                continue
            except Exception as e:  # noqa: BLE001 — próximo motor
                tentativas.append({"motor": m, "falha_etapa": "transporte", "erro": f"{e.__class__.__name__}: {str(e)[:160]}"})
                continue
            if not texto:
                tentativas.append({"motor": m, "falha_etapa": "execucao", "erro": "transcrição vazia"})
                continue
            return {"text": texto, "motor": m if m == "whisper" else MODELO, "proc_s": round(time.monotonic() - t0, 3),
                    "audio_s": audio_s, "falha_etapa": None, "erro": None, "tentativas": tentativas}
    return {"text": None, "motor": None, "proc_s": None, "audio_s": audio_s, "falha_etapa": "indisponivel",
            "erro": "nenhum motor transcreveu", "tentativas": tentativas}


def _selftest() -> int:
    ok = True
    if not shutil.which("ffmpeg"):
        print("SKIP sem ffmpeg")
        return 0
    with tempfile.TemporaryDirectory() as t:
        a = Path(t) / "x.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=440:d=1", str(a)], check=True)
        r = transcrever(a, chamar_lfm3=lambda w, i: "olá", whisper_ativo=lambda: False)
        ok &= r["text"] == "olá" and r["motor"] == MODELO
        print(("PASS" if ok else "FALHA"), "motor principal")

        def cai(w, i):
            raise ConnectionError("fora")
        r = transcrever(a, chamar_lfm3=cai, chamar_whisper=lambda w: "reserva", whisper_ativo=lambda: True)
        ok &= r["motor"] == "whisper" and r["tentativas"][0]["falha_etapa"] == "transporte"
        print(("PASS" if ok else "FALHA"), "reserva quando o principal cai")
        r = transcrever(a, chamar_lfm3=cai, whisper_ativo=lambda: False)
        ok &= r["text"] is None and r["falha_etapa"] == "indisponivel"
        print(("PASS" if ok else "FALHA"), "sem motor: indisponível, sem ligar serviço")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    if not argv or argv[0].startswith("-"):
        print(__doc__, file=sys.stderr)
        return 2
    motor = argv[argv.index("--motor") + 1] if "--motor" in argv else "auto"
    idioma = argv[argv.index("--idioma") + 1] if "--idioma" in argv else "Portuguese"
    r = transcrever(argv[0], motor=motor, idioma=idioma)
    print(json.dumps(r, ensure_ascii=False))
    return 0 if r["text"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
