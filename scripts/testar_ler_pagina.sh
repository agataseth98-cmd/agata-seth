#!/usr/bin/env bash
# Regressão PERMANENTE de scripts/ler_pagina.sh -- conserto autorizado pelo
# Humano em 21/08/2026 (MEMÓRIAS (232)). Roda de novo sempre que o script
# mudar, não é teste avulso.
#
# CONTROLE POSITIVO (razionshefa.com.br/pt): espera conteúdo real extraído
# (CASO 1 ou SUSPEITA do antigo CASO 3).
# TESTE NEGATIVO (angular.realworld.io): antes do conserto, o script
# devolvia mensagens internas de erro do Angular como se fossem conteúdo
# do site ("StaticProvider does not have...", "Cannot mix multi
# providers..."). Depois do conserto, não pode rotular essas frases como
# conteúdo válido -- tem que virar SUSPEITA + reportar a API real do
# pacote (https://conduit.productionready.io/api, confirmada por grep
# direto no pacote JS).
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
SCRIPT="scripts/ler_pagina.sh"
FALHAS=0

echo "=== CONTROLE POSITIVO: https://razionshefa.com.br/pt ==="
OUT_POS=$(bash "$SCRIPT" "https://razionshefa.com.br/pt" 2>&1)
RC_POS=$?
echo "$OUT_POS"
echo "(exit $RC_POS)"
if [ $RC_POS -ne 0 ]; then
  echo "FALHA: esperava exit 0 (conteúdo achado), saiu $RC_POS"
  FALHAS=$((FALHAS+1))
fi
if ! echo "$OUT_POS" | grep -qE '^(CASO 1|SUSPEITA)'; then
  echo "FALHA: esperava rótulo CASO 1 ou SUSPEITA na saída"
  FALHAS=$((FALHAS+1))
fi

echo
echo "=== TESTE NEGATIVO: https://angular.realworld.io/ ==="
OUT_NEG=$(bash "$SCRIPT" "https://angular.realworld.io/" 2>&1)
RC_NEG=$?
echo "$OUT_NEG"
echo "(exit $RC_NEG)"
if echo "$OUT_NEG" | grep -qE '^CASO 3'; then
  echo "FALHA: rótulo CASO 3 (conclusão) voltou a aparecer -- deveria ser SUSPEITA"
  FALHAS=$((FALHAS+1))
fi
if ! echo "$OUT_NEG" | grep -q "SUSPEITA"; then
  echo "FALHA: esperava rótulo SUSPEITA (ruído de framework provável) na saída"
  FALHAS=$((FALHAS+1))
fi
if ! echo "$OUT_NEG" | grep -qF "https://conduit.productionready.io/api"; then
  echo "FALHA: esperava a URL de API real do pacote (conduit.productionready.io/api) reportada"
  FALHAS=$((FALHAS+1))
fi

echo
if [ $FALHAS -eq 0 ]; then
  echo "REGRESSÃO OK -- 0 falhas."
else
  echo "REGRESSÃO FALHOU -- $FALHAS falha(s)."
fi
exit $FALHAS
