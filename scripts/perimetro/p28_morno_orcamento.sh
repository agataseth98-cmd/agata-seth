#!/usr/bin/env bash
# P-28 (26/11/2026, proposta memoria-manutencao-26-11): morno (MEMORIAS-MORNO.md) acima do limite
# de congelamento. Pedido do Gemini via Humano (cache 965); MORNO em 1,17 MB desde 23/10/2026 sem
# ciclo novo de migrar_periodo.py + selar.sh. Estado: AVISO PARCIAL (nunca FALHA) — lembra o
# Humano de disparar o próximo ciclo de camada fria; escalada para FALHA fica para fase seguinte,
# como em P-24.
p28_morno_orcamento() {
  local orc=1024000 tam  # 1.000 KB; cada frio sela ~90-110 KB, então acima disto já cabem ~10 blocos.
  [ -f MEMORIAS-MORNO.md ] || return 0
  tam=$(wc -c < MEMORIAS-MORNO.md 2>/dev/null | tr -d '[:space:]')
  [ -z "$tam" ] && return 0
  if [ "$tam" -gt "$orc" ]; then
    PERIMETRO_ESTADO="PARCIAL"
    echo "AVISO (P-28): MEMORIAS-MORNO.md tem $tam bytes; limite para novo congelamento é $orc."
    echo "  O que fazer: rode 'python3 scripts/migrar_periodo.py' para gerar um novo bloco frio e, em seguida, 'bash scripts/selar.sh <arquivo-novo>'."
    echo "  Por que importa: MORNO cresce sem teto quando o ciclo frio não roda; busca e hidratação derivada ficam mais caras a cada commit."
  fi
  return 0
}
