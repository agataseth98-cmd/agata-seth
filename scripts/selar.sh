#!/usr/bin/env bash
# Rodar da RAIZ do repo. Uso: bash scripts/selar.sh <arquivo> | --check
set -euo pipefail
SELOS="SELOS.txt"
if [ "${1:-}" = "--check" ]; then
    [ -f "$SELOS" ] || { echo "sem selos registrados ($SELOS ausente)"; exit 1; }
    falha=0
    while read -r hash arquivo data; do
        [ -z "$hash" ] && continue
        atual=$(sha256sum "$arquivo" 2>/dev/null | cut -d' ' -f1 || echo "ARQUIVO_AUSENTE")
        if [ "$atual" = "$hash" ]; then echo "OK      $arquivo (selado em $data)"
        else echo "VIOLADO $arquivo — selo $hash != atual $atual"; falha=1; fi
    done < "$SELOS"
    exit $falha
fi
[ -n "${1:-}" ] || { echo "uso: selar.sh <arquivo> | --check"; exit 1; }
[ -f "$1" ] || { echo "arquivo não existe: $1"; exit 1; }
hash=$(sha256sum "$1" | cut -d' ' -f1); data=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "$hash $1 $data" >> "$SELOS"
echo "selado: $1"; echo "sha256: $hash"
echo "registrado em $SELOS — commite e tag: git tag ${1%.md}-final"
