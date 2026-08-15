#!/usr/bin/env bash
# S-1 (auditoria de segurança, 15/08/2026): varredura de segredo sobre o
# diff staged, ANTES do commit. Escrito e testado nesta sessão -- NÃO
# habilitado em .githooks/pre-commit. Habilitar é decisão do Humano.
#
# Não é scanner geral de todo o repo: olha só o que está staged agora
# (git diff --cached), que é o que um pre-commit real veria. Padrões
# cobrem formatos de chave conhecidos (AWS, Google, GitHub, OpenAI/sk-,
# Slack) + heurística genérica (VAR_KEY/_TOKEN/_SECRET/_PASSWORD = string
# longa). Heurística tem falso positivo/negativo -- é rede de segurança
# adicional, não substitui revisão humana do diff.
set -uo pipefail

PADROES=(
  'AKIA[0-9A-Z]{16}'                          # AWS access key id
  'AIza[0-9A-Za-z_-]{35}'                     # Google API key
  'gh[pousr]_[0-9A-Za-z]{36,}'                # GitHub token (ghp_/gho_/ghu_/ghs_/ghr_)
  'sk-[A-Za-z0-9]{20,}'                       # OpenAI-style secret key
  'xox[baprs]-[0-9A-Za-z-]{10,}'              # Slack token
  '-----BEGIN[A-Z ]*PRIVATE KEY-----'         # PEM private key
  '[A-Za-z0-9_]*(KEY|TOKEN|SECRET|PASSWORD)[A-Za-z0-9_]*[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9/+_-]{16,}["'"'"']?'
)

achou=0

# Arquivo .env staged é o próprio incidente, não um caso pra escanear por
# padrão -- se .gitignore falhou ou foi forçado (`git add -f`), avisa
# sempre, sujo ou limpo por dentro. Achado real ao testar (15/08/2026):
# uma versão anterior deste script EXCLUÍA .env do diff escaneado -- o
# oposto do que devia, isso escondia exatamente o caso mais grave.
env_staged="$(git diff --cached --name-only -- '.env' '.env.*' '*/.env' '*/.env.*')"
if [ -n "$env_staged" ]; then
  achou=1
  echo "SUSPEITO: arquivo .env staged (deveria estar em .gitignore sempre):"
  echo "$env_staged" | sed 's/^/  /'
fi

DIFF="$(git diff --cached -U0)"

for p in "${PADROES[@]}"; do
  linhas="$(echo "$DIFF" | grep -nE '^\+' | grep -vE '^\+\+\+' | grep -E -- "$p")"
  if [ -n "$linhas" ]; then
    achou=1
    echo "SUSPEITO (padrão: $p):"
    echo "$linhas" | sed 's/^/  /'
  fi
done

if [ "$achou" -eq 1 ]; then
  echo
  echo "varredura_segredo.sh: possível segredo no staged diff. Revise antes de comitar." >&2
  exit 1
fi
exit 0
