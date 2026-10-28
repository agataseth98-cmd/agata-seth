#!/usr/bin/env bash
# Início de sessão na Equipe (skill agata-fluxo §0): uma leitura, saída curta. Qualquer membro do Conselho.
# Uso: bash scripts/equipe/inicio.sh <membro>   (claude, codex, gemini, goose...)
# Sem nada novo, não imprime texto (economia de tokens).
set -euo pipefail
agente="${1:?uso: inicio.sh <membro>}"
raiz="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$raiz"
timeout 60 python3 scripts/equipe/equipe.py presente --agente "$agente" >/dev/null 2>&1 || true
novo="$(timeout 60 python3 scripts/equipe/equipe.py ler --agente "$agente" 2>/dev/null || true)"
case "$novo" in
  ""|*"nada novo no canal"*) exit 0 ;;
  *) printf '%s\n' "$novo" ;;
esac
