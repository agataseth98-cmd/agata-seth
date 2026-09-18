#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

# --- P-15 --------------------------------------------------------------------
# Saúde do roster do Conselho Remoto (MEMÓRIAS (374)). scripts/conselho_remoto.py
# escreve `memoria/missoes/conselho-remoto/sucessos.log`: uma linha
# `<epoch>\t<modelo>\t<familia>` por chamada bem-sucedida. AVISO (nunca FALHA)
# se menos de 2 FAMILIAS distintas responderam nas ultimas 24h -- sinal de que a
# camada externa esta degradada e o sistema pode estar andando com fallback
# local. Nunca falha o commit (a camada local basta pra operar).
p15_roster_remoto() {
  local log="$_PERIMETRO_DIR/../memoria/missoes/conselho-remoto/sucessos.log"
  if [ ! -f "$log" ]; then
    echo "sem historico de sucesso do Conselho Remoto ainda -- nada a avaliar (nao e problema)"
    return 0
  fi
  local corte fams
  corte=$(( $(date +%s) - 86400 ))
  fams=$(awk -F'\t' -v c="$corte" 'NF>=3 && ($1 + 0) >= c {print $3}' "$log" | sort -u | grep -c .)
  if [ "${fams:-0}" -lt 2 ]; then
    echo "AVISO (P-15): so ${fams:-0} familia(s) do roster remoto teve(tiveram) sucesso nas ultimas 24h. A segunda opiniao externa pode estar degradada -- o sistema pode estar andando com fallback local. Nao falha o commit; olhe scripts/conselho_remoto.py e o OmniRoute."
  else
    echo "roster remoto OK -- $fams familias com sucesso nas ultimas 24h"
  fi
  return 0
}

