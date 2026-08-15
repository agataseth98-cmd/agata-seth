#!/usr/bin/env bash
# Passo 3.1 (ordem 15/08/2026, 18:57): testa varredura_segredo.sh contra os
# últimos 20 commits REAIS antes de habilitar no pre-commit. Reaproveita a
# mesma lógica de padrões do script real, aplicada ao diff que cada commit
# introduziu (git show), não ao staged atual.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

PADROES=(
  'AKIA[0-9A-Z]{16}'
  'AIza[0-9A-Za-z_-]{35}'
  'gh[pousr]_[0-9A-Za-z]{36,}'
  'sk-[A-Za-z0-9]{20,}'
  'xox[baprs]-[0-9A-Za-z-]{10,}'
  '-----BEGIN[A-Z ]*PRIVATE KEY-----'
  '[A-Za-z0-9_]*(KEY|TOKEN|SECRET|PASSWORD)[A-Za-z0-9_]*[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9/+_-]{16,}["'"'"']?'
)

total_achados=0
for commit in $(git log --format='%H' -20); do
  env_tocado="$(git show --name-only --format='' "$commit" -- '.env' '.env.*' '*/.env' '*/.env.*')"
  if [ -n "$env_tocado" ]; then
    echo "COMMIT $commit -- .env tocado: $env_tocado"
    total_achados=$((total_achados+1))
  fi

  diff="$(git show -U0 --format='' "$commit")"
  for p in "${PADROES[@]}"; do
    linhas="$(echo "$diff" | grep -nE '^\+' | grep -vE '^\+\+\+' | grep -E -- "$p")"
    if [ -n "$linhas" ]; then
      total_achados=$((total_achados+1))
      echo "COMMIT $commit -- padrão [$p]:"
      echo "$linhas" | sed 's/^/  /'
    fi
  done
done

echo
echo "TOTAL DE ACHADOS NOS ÚLTIMOS 20 COMMITS: $total_achados"
