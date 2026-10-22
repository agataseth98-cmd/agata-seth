#!/usr/bin/env bash
# Prepara a assinatura de uma proposta: confere os checks do PR, mescla o PR,
# atualiza o main e verifica o .diff. NÃO assina: a assinatura é do Humano,
# com `bash scripts/aprovar.sh <nome>`. Uso: bash scripts/preparar_assinatura.sh <nome>
set -euo pipefail

NOME="${1:?uso: preparar_assinatura.sh <nome-da-proposta>}"
cd "$(git rev-parse --show-toplevel)"

if [ "$(git branch --show-current)" != "main" ]; then
  echo "ERRO: rode no checkout principal, em main (branch atual: $(git branch --show-current))" >&2
  exit 1
fi

git fetch -q origin
git pull -q --ff-only origin main

PR="$(gh pr list --head "proposta/$NOME" --state open --json number --jq '.[0].number // empty' 2>/dev/null || true)"

if [ -z "$PR" ]; then
  if [ -f "propostas/$NOME.diff" ]; then
    echo "OK: nenhum PR aberto para proposta/$NOME, e o diff já está no main."
  else
    echo "ERRO: sem PR aberto para proposta/$NOME e sem propostas/$NOME.diff no main." >&2
    exit 1
  fi
else
  CHECKS="$(gh pr checks "$PR" 2>&1 || true)"
  if echo "$CHECKS" | grep -Eq '[[:space:]](fail|pending)[[:space:]]|no checks'; then
    echo "ERRO: PR #$PR ainda não está verde. Checks:" >&2
    echo "$CHECKS" | awk '{print "  " $1, $2}' >&2
    echo "Rode de novo quando os checks passarem." >&2
    exit 1
  fi
  gh pr merge "$PR" --merge
  git pull -q --ff-only origin main
  echo "OK: PR #$PR mesclado e main atualizado."
fi

if [ ! -f "propostas/$NOME.diff" ]; then
  echo "ERRO: propostas/$NOME.diff não está no main após o merge." >&2
  exit 1
fi

bash scripts/p8_verificar.sh "$NOME" 2>&1 | tail -1 || true
echo
echo "Próximo passo (só você, no seu terminal, depois de ler o .diff):"
echo "  bash scripts/aprovar.sh $NOME \"<motivo>\""
