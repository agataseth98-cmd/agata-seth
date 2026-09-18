#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

p17_skip_cronico() {
  [ -n "${AGATA_TESTE_PERIMETRO:-}" ] && { echo "P-17: dentro da suíte -- não contabiliza."; PERIMETRO_ESTADO="SKIP"; return 0; }
  mkdir -p "$(dirname "$P17_ESTADO")" 2>/dev/null || { echo "P-17: sem cache gravável -- série não acompanhada."; PERIMETRO_ESTADO="PARCIAL"; return 0; }
  touch "$P17_ESTADO" 2>/dev/null

  local todos ctrl serie novo="" alarmes=""
  todos="$(grep -oE 'cabecalho "P-[0-9]+"' "$_PERIMETRO_DIR/perimetro.sh" 2>/dev/null | grep -oE 'P-[0-9]+' | sort -u)"
  while IFS= read -r ctrl; do
    [ -z "$ctrl" ] && continue
    serie="$(awk -v c="$ctrl" '$1==c{print $2}' "$P17_ESTADO" 2>/dev/null | tail -1)"
    [ -z "$serie" ] && serie=0
    if printf '%s' " $P17_SKIPS" | grep -q " $ctrl "; then
      serie=$((serie + 1))
      [ "$serie" -ge "$P17_LIMITE" ] && alarmes="${alarmes}${ctrl}=${serie} "
    else
      serie=0
    fi
    novo="${novo}${ctrl}	${serie}
"
  done <<< "$todos"
  printf '%s' "$novo" > "$P17_ESTADO" 2>/dev/null

  if [ -n "$alarmes" ]; then
    echo "AVISO (P-17): controle(s) em SKIP por $P17_LIMITE ou mais corridas SEGUIDAS: $alarmes"
    echo "  Por que importa: foi exatamente assim que o P-7 ficou desligado por 79 commits -- pulando em silêncio, um SKIP igual ao anterior. Confira se o motivo do SKIP ainda é verdade; se for, o controle talvez precise mudar de forma, não continuar pulando."
    return 0
  fi
  if [ -n "$P17_SKIPS" ]; then
    echo "P-17: pularam nesta corrida ($P17_SKIPS) -- séries abaixo do limite de $P17_LIMITE."
  else
    echo "P-17: nenhum controle pulou nesta corrida."
  fi
  return 0
}

