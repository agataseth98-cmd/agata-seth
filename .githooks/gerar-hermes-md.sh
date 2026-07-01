#!/usr/bin/env bash
# Regenera ~/agata/.hermes.md a partir de REGRAS.md + PROJETO.md.
# Chamado pelo hook pre-commit. Pode ser rodado manualmente também.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=".hermes.md"

{
  echo "<!--"
  echo "ARQUIVO GERADO AUTOMATICAMENTE — NÃO EDITE DIRETAMENTE."
  echo "Gerado por .githooks/gerar-hermes-md.sh a partir de REGRAS.md + PROJETO.md."
  echo "Para mudar o conteúdo, edite REGRAS.md ou PROJETO.md e faça commit —"
  echo "o hook pre-commit regenera este arquivo sozinho."
  echo ""
  echo "Motivo de existir: o Hermes só auto-injeta um de"
  echo ".hermes.md / AGENTS.md / CLAUDE.md / .cursorrules no prompt de sistema"
  echo "(nunca REGRAS.md/PROJETO.md diretamente). Embutir aqui evita depender"
  echo "de tool-call manual no início da sessão para carregar as regras."
  echo "-->"
  echo ""
  echo "# REGRAS.md"
  echo ""
  cat REGRAS.md
  echo ""
  echo "# PROJETO.md"
  echo ""
  cat PROJETO.md
} > "$OUT"

echo "gerado: $OUT ($(wc -c < "$OUT") bytes)"
