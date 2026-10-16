#!/usr/bin/env bash
# Instala a voz treinada da Agata (modelo `last`) em voices/, conferindo o sha256 de cada arquivo
# contra agata-last.sha256. Idempotente, nunca baixa nada e nunca sobrescreve com arquivo de hash
# divergente. Artefatos (voices/) são gitignorados; só este script e o manifesto vão ao git.
# Desfazer: apagar voices/pt_BR-agata-last.onnx (o tts_piper.py volta à voz genérica sozinho).
#
# Origem: AGATA_VOZ_ORIGEM (default ~/.local/share/agata-voz/resultado). Este modelo vem de
# CML-TTS pt, leitora 12710 (CC BY 4.0, LibriVox): atribuição obrigatória SE a voz for distribuída.
set -euo pipefail
cd "$(dirname "$0")"
ORIGEM="${AGATA_VOZ_ORIGEM:-$HOME/.local/share/agata-voz/resultado}"
MANIFESTO="${AGATA_VOZ_MANIFESTO:-agata-last.sha256}"
mkdir -p voices
n=0
while read -r esperado arquivo; do
  case "${esperado:-}" in ''|\#*) continue ;; esac
  [ -f "$ORIGEM/$arquivo" ] || { echo "ERRO: $ORIGEM/$arquivo não existe." >&2; exit 1; }
  real="$(sha256sum "$ORIGEM/$arquivo" | cut -d' ' -f1)"
  [ "$real" = "$esperado" ] || { echo "ERRO: sha256 de $arquivo diverge do manifesto (esperado ${esperado:0:12}…, obtido ${real:0:12}…). Nada foi instalado." >&2; exit 1; }
  if [ -f "voices/$arquivo" ] && [ "$(sha256sum "voices/$arquivo" | cut -d' ' -f1)" = "$esperado" ]; then
    echo "já instalado: $arquivo"
  else
    cp "$ORIGEM/$arquivo" "voices/$arquivo.novo.$$" && mv -f "voices/$arquivo.novo.$$" "voices/$arquivo"
    echo "instalado: $arquivo"
  fi
  n=$((n+1))
done < "$MANIFESTO"
[ "$n" -gt 0 ] || { echo "ERRO: manifesto vazio." >&2; exit 1; }
echo "OK: $n arquivo(s) conferidos. Reinicie o serviço para usar:  systemctl --user restart piper-tts"
