#!/usr/bin/env bash
# Início de sessão da dupla (skill agata-fluxo §0): uma leitura, saída curta.
# Uso: bash scripts/dupla/inicio.sh <claude|codex>
# Sem nada novo, não imprime texto (economia de tokens).
set -euo pipefail
agente="${1:?uso: inicio.sh <claude|codex>}"
raiz="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$raiz"
timeout 60 python3 scripts/dupla/dupla.py presente --agente "$agente" >/dev/null 2>&1 || true
novo="$(timeout 60 python3 scripts/dupla/dupla.py ler --agente "$agente" 2>/dev/null || true)"
case "$novo" in
  ""|*"nada novo no canal"*) exit 0 ;;
  *) printf '%s\n' "$novo" ;;
esac
