#!/usr/bin/env bash
# reativar-provider.sh <nome-omniroute>
#
# Depois que um provedor dá 401/402, o OmniRoute DESABILITA a chave dele
# (`omniroute keys list` mostra "○ disabled") e para de tentar. Isso é de
# propósito: 401/402 = credencial ruim ou conta sem saldo, retentar não ajuda.
# (Só 429/5xx o OmniRoute recupera sozinho, via circuit breaker.) Quando VOCÊ
# conserta a conta/chave, precisa dizer ao OmniRoute "tenta de novo" — é o que
# este script faz.
#
# Lê a chave de ~/.hermes/.env pela convenção <PROV>_API_KEY (nome em MAIÚSCULAS;
# mapa especial: zai->ZHIPU_API_KEY, gemini->GOOGLE_API_KEY). O valor NUNCA é impresso.
#
# Uso:  bash redesign/router/reativar-provider.sh cerebras
set -uo pipefail

PROV="${1:-}"
[ -z "$PROV" ] && { echo "uso: $0 <nome-omniroute>  (ex.: cerebras groq gemini zai openrouter deepseek)"; exit 2; }

ENV_FILE="$HOME/.hermes/.env"
BIN="${OMNIROUTE_BIN:-$HOME/.npm-global/bin/omniroute}"
orun() { timeout 45 "$BIN" "$@" 2>&1 | grep -viE 'loaded env|unsettled top-level await|parseAsync|^\s*\^\s*$'; }

case "$PROV" in
  zai)    VAR="ZHIPU_API_KEY" ;;
  gemini) VAR="GOOGLE_API_KEY" ;;
  *)      VAR="$(printf '%s' "$PROV" | tr '[:lower:]-' '[:upper:]_')_API_KEY" ;;
esac

KEY="$(while IFS='=' read -r k v; do
  [ "$k" = "$VAR" ] || continue
  v="${v%\"}"; v="${v#\"}"; v="${v%\'}"; v="${v#\'}"; printf '%s' "$v"; break
done < "$ENV_FILE")"
[ -z "$KEY" ] && { echo "não achei $VAR em $ENV_FILE — cadastre a chave lá primeiro."; exit 1; }
echo "$VAR encontrada (${#KEY} chars). Reativando '$PROV' no OmniRoute..."

printf '%s' "$KEY" | timeout 45 "$BIN" keys add "$PROV" --stdin 2>&1 | grep -viE 'loaded env' || true
orun resilience reset --provider "$PROV" --yes >/dev/null || true

echo "--- status ---"
orun keys list        | grep -E "^\s*$PROV\b" || true
orun providers list   | grep -E "\b$PROV\b"   || true
echo "--- confirme com um pedido de verdade:  $BIN test $PROV  (ou um curl no combo que usa esse provedor) ---"
