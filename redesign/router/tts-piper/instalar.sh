#!/usr/bin/env bash
# Cria o venv do Piper e baixa a voz pt-BR. Idempotente. Artefatos (.venv,
# voices/) são gitignorados -- só este script, o shim tts_piper.py e a unit
# systemd vão pro git. MEMÓRIAS (387).
set -euo pipefail
cd "$(dirname "$0")"

VOZ="${PIPER_VOZ:-pt_BR-faber-medium}"

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q piper-tts

mkdir -p voices
if [ ! -f "voices/${VOZ}.onnx" ]; then
  ./.venv/bin/python -m piper.download_voices "$VOZ" --data-dir voices
fi

echo "OK: .venv + voices/${VOZ}.onnx ($(du -h "voices/${VOZ}.onnx" | cut -f1))"
echo "Teste: echo 'bom dia' | ./.venv/bin/python -m piper -m voices/${VOZ}.onnx -f /tmp/t.wav && echo gerou /tmp/t.wav"
