#!/usr/bin/env bash
# (28/10/2026) Contexto automático para sessões do Claude Code no ~/agata: estado da Máquina,
# memória comum do Conselho e estado da Equipe. Entregue pelo hook SessionStart de .claude/settings.json.
# Só leitura. Saída: JSON com hookSpecificOutput.additionalContext. Não escreve em lugar nenhum.
set -u
cd "$(dirname "$0")/.." || exit 0
ctx() {
  echo "=== Estado da Máquina (estado_para_eco.sh) ==="
  timeout 30 bash scripts/estado_para_eco.sh 2>/dev/null | head -8 || echo "(indisponível)"
  echo "=== Memória comum do Conselho (últimas 10) ==="
  timeout 30 python3 redesign/router/cache_conselho.py ler --n 10 2>/dev/null | head -40 || echo "(indisponível)"
  echo "=== Sessão conjunta (equipe.py status) ==="
  timeout 30 python3 scripts/equipe/equipe.py status 2>/dev/null | head -3 || echo "(indisponível)"
  echo "=== Regras desta sessão ==="
  echo "Cabeçalho na abertura de cada resposta. Fato do sistema: busque no vault antes de afirmar. Antes de entregar texto com afirmação verificável: python3 redesign/router/auditoria_turno.py --verificar < arquivo. Ao fechar trabalho relevante: cache_conselho.py anotar."
}
if [ "${1:-}" = "--selftest" ]; then
  out="$(ctx)"
  printf '%s' "$out" | grep -q "Estado da Máquina" && printf '%s' "$out" | grep -q "Memória comum" && printf '%s' "$out" | grep -q "Sessão conjunta" && echo "sessao_claude_contexto: OK" || { echo "sessao_claude_contexto: FALHOU"; exit 1; }
  exit 0
fi
python3 - "$(ctx)" <<'PY'
import json, sys
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": sys.argv[1]}}, ensure_ascii=False))
PY
