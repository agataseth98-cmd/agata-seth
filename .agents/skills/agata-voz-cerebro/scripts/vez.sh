#!/bin/bash
# Uma vez da conversa por voz com o modelo da CLI como cérebro:
# para o som de espera, fala o arquivo $1 pela voz do sistema, ouve UMA fala do Humano, liga o som de espera
# (toca enquanto o modelo pensa) e imprime a transcrição. Uso: vez.sh ARQUIVO_FALAVEL [limite_s]
# Encerrar: vez.sh --parar   (só para o som de espera)
AQUI="$(cd "$(dirname "$0")" && pwd)"
RAIZ="$(cd "$AQUI/../../../.." && pwd)"
RT="${XDG_RUNTIME_DIR:-/tmp}/agata-voz-cerebro"; mkdir -p "$RT"; chmod 700 "$RT"
SOM="$RT/espera.wav"; MARCA="$RT/espera_loop"
parar() { pkill -f "$MARCA" 2>/dev/null; pkill -f "pw-play $SOM" 2>/dev/null; }
parar
[ "$1" = "--parar" ] && exit 0
[ -s "$SOM" ] || ffmpeg -loglevel error -y -f lavfi \
  -i "sine=f=330:d=1.2,volume=0.06,afade=t=in:d=0.4,afade=t=out:st=0.8:d=0.4,apad=pad_dur=0.8" "$SOM"
if [ -n "$1" ]; then
  (cd "$RAIZ" && python3 scripts/agata_falar.py --arquivo "$1" >/dev/null 2>&1) || echo "[voz falhou: não falei]"
fi
timeout 120 python3 "$AQUI/escutar.py" "${2:-90}" 2>/dev/null | tail -1
setsid bash -c "exec -a $MARCA bash -c 'for i in \$(seq 60); do pw-play $SOM; done'" >/dev/null 2>&1 < /dev/null &
