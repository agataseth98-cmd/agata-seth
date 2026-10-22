#!/usr/bin/env bash
# P-24 (proposta 21/10/2026, v8): quente (MEMÓRIAS.md) acima do orçamento de hidratação.
# Estado atual: AVISO (PARCIAL) com o excesso medido. Escalada para FALHA: fase seguinte.
p24_quente_orcamento() {
  local orc=25000 tam
  [ -f MEMÓRIAS.md ] || return 0
  tam=$(python3 -c "import sys;print(len(open('MEMÓRIAS.md',encoding='utf-8').read()))")
  if [ "$tam" -gt "$orc" ]; then
    PERIMETRO_ESTADO="PARCIAL"
    echo "AVISO (P-24): MEMÓRIAS.md tem $tam caracteres; orçamento de hidratação é $orc. Escalada para FALHA ainda não implementada."
  fi
  return 0
}
