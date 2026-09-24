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
    # Texto corrigido na varredura tripla (MEMORIAS (527)): o log so recebe
    # SUCESSO do conselho_remoto.py -- nao registra tentativa. "0 familias"
    # tanto pode ser roster quebrado quanto ninguem ter chamado o Conselho em
    # 24h. Em 23/09/2026 o aviso dizia "degradada" enquanto 4 de 5 membros
    # respondiam a chamada direta. O aviso agora diz o que mediu, nao o que supoe.
    echo "AVISO (P-15): so ${fams:-0} familia(s) do roster remoto com SUCESSO registrado nas ultimas 24h. Este controle so enxerga sucessos do scripts/conselho_remoto.py -- 0 pode ser so falta de uso, nao prova degradacao. Pra medir de verdade: python3 scripts/pesquisar_modelos_gratuitos.py (sonda o roster). Nao falha o commit."
  else
    echo "roster remoto OK -- $fams familias com sucesso nas ultimas 24h"
  fi
  return 0
}

