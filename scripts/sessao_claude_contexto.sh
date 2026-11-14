#!/usr/bin/env bash
# (28/10/2026; sincronia-12-11) Contexto de início de sessão do Claude Code no ~/agata. O conteúdo é de
# scripts/sessao_contexto.py (estado da Máquina, memória comum do Conselho, lotes abertos, regras ativas e
# sessão conjunta): o mesmo para Claude Code, Gemini CLI e Codex. Entregue pelo hook SessionStart de
# .claude/settings.json. Só leitura. Saída: JSON com hookSpecificOutput.additionalContext.
set -u
cd "$(dirname "$0")/.." || exit 0
if [ "${1:-}" = "--selftest" ]; then
  exec python3 -I scripts/sessao_contexto.py --selftest
fi
exec python3 scripts/sessao_contexto.py --json
