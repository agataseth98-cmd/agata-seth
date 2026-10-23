#!/usr/bin/env bash
# Cria um clone descartável com os HOOKS do repositório ativos (core.hooksPath),
# para testar um commit sem tocar o repositório real. Sem isso, o clone não passa
# pelo pre-commit e o teste não vale nada (aprendido em 23/10/2026).
# Uso: scripts/clone_teste.sh <destino-novo> [ref]
set -euo pipefail
destino="${1:?uso: clone_teste.sh <destino-novo> [ref]}"
ref="${2:-HEAD}"
origem="$(git rev-parse --show-toplevel)"
[ -e "$destino" ] && { echo "destino já existe: $destino" >&2; exit 1; }
git clone -q --no-hardlinks "$origem" "$destino"
cd "$destino"
git checkout -q "$ref"
git config core.hooksPath .githooks
git config user.name "$(git -C "$origem" config user.name)"
git config user.email "$(git -C "$origem" config user.email)"
echo "clone pronto: $destino (hooks ativos: $(git config core.hooksPath))"
