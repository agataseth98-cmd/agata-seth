#!/usr/bin/env bash
# Regenera ~/agata/.hermes.md a partir de REGRAS.md + PROJETO.md + fim do DIÁRIO.md.
# Chamado pelo hook pre-commit. Pode ser rodado manualmente também.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=".hermes.md"
DIARIO_LINHAS=30

{
  echo "<!--"
  echo "ARQUIVO GERADO AUTOMATICAMENTE — NÃO EDITE DIRETAMENTE."
  echo "Gerado por .githooks/gerar-hermes-md.sh a partir de REGRAS.md + PROJETO.md + fim do DIÁRIO.md."
  echo "Para mudar o conteúdo, edite REGRAS.md, PROJETO.md ou DIÁRIO.md e faça commit —"
  echo "o hook pre-commit regenera este arquivo sozinho."
  echo ""
  echo "Motivo de existir: o Hermes só auto-injeta um de"
  echo ".hermes.md / AGENTS.md / CLAUDE.md / .cursorrules no prompt de sistema"
  echo "(nunca REGRAS.md/PROJETO.md/DIÁRIO.md diretamente). Embutir aqui evita depender"
  echo "de tool-call (e do modelo acertar offset/wc -l) no início da sessão."
  echo "-->"
  echo ""
  echo "# REGRAS.md"
  echo ""
  cat REGRAS.md
  echo ""
  echo "# PROJETO.md"
  echo ""
  cat PROJETO.md
  echo ""
  echo "# DIÁRIO.md (últimas $DIARIO_LINHAS linhas)"
  echo ""
  echo "## DIÁRIO (últimas 30 linhas)"
  echo ""
  tail -n "$DIARIO_LINHAS" DIÁRIO.md
} > "$OUT"

echo "gerado: $OUT ($(wc -c < "$OUT") bytes)"
