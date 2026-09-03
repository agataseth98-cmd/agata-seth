#!/usr/bin/env bash
# Reconcilia os canônicos locais (REGRAS/PROJETO/DIÁRIO) com o GitHub, que é a
# fonte da verdade. Nunca sobrescreve história local não commitada: se houver
# mudança local pendente ou conflito de merge, para e reporta em vez de forçar.
set -euo pipefail

REPO_DIR="$HOME/agata"
ALVO="${1:-TUDO}"

case "$ALVO" in
  MEMORIA|PROJETO|REGRAS|TUDO) ;;
  *)
    echo "Uso: atualizar.sh [MEMORIA|PROJETO|REGRAS|TUDO]" >&2
    exit 1
    ;;
esac

cd "$REPO_DIR"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERRO: há mudanças locais não commitadas em $REPO_DIR." >&2
  echo "Faça commit ou stash antes de atualizar — não vou sobrescrever história local." >&2
  git status --short
  exit 1
fi

ANTES=$(git rev-parse HEAD)

if ! git pull --no-edit origin main; then
  echo "ERRO: git pull falhou (provável conflito de merge)." >&2
  echo "PARANDO sem forçar nada — resolva manualmente e rode de novo." >&2
  git status --short
  exit 1
fi

DEPOIS=$(git rev-parse HEAD)

echo "atualizar.sh: alvo=$ALVO"
if [ "$ANTES" = "$DEPOIS" ]; then
  echo "  já estava em dia (HEAD=$DEPOIS)."
else
  echo "  atualizado: $ANTES -> $DEPOIS"
  git diff --stat "$ANTES" "$DEPOIS"
fi

bash .githooks/gerar-hermes-md.sh

case "$ALVO" in
  MEMORIA) echo "  MEMÓRIAS.md reconciliado; topo reinjetado em .hidrata.md." ;;
  PROJETO) echo "  PROJETO.md reconciliado; reinjetado em .hidrata.md." ;;
  REGRAS)  echo "  REGRAS.md reconciliado; reinjetado em .hidrata.md." ;;
  TUDO)    echo "  REGRAS.md + PROJETO.md + MEMÓRIAS.md reconciliados; reinjetados em .hidrata.md." ;;
esac

echo "atualizar.sh: concluído."
