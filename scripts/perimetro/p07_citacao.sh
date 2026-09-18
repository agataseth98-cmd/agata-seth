#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

# --- P-7 -----------------------------------------------------------------
# Citação de MEMÓRIAS aponta pra entrada real, não fabricada (REGRAS,
# "Citação de MEMÓRIAS -- primeira referência"). Checa só o que esta
# staged ACRESCENTOU a MEMÓRIAS.md, nunca o arquivo inteiro -- P-7 valida
# entrada NOVA a cada commit, não reaudita a história toda toda vez.
# Consequência direta: uma citação-exemplo já commitada no passado (ex.:
# (162), que cita "(101 - ...)" como transcrição literal de uma ordem,
# sem crases) nunca é rescaneada por este mecanismo -- só citações que
# entram DAQUI PRA FRENTE. checar_citacao.sh, função própria: MEMÓRIAS
# (203)/(204).
p7_citacao() {
  if ! git rev-parse HEAD >/dev/null 2>&1; then
    return 0
  fi
  # Marca de migração presente (P-5 já rodou a checagem de permutação e
  # confirmou: nenhum byte de entrada mudou, só a posição física) -- um
  # commit de reordenação faz `git diff` enxergar praticamente o arquivo
  # inteiro como "+" (a posição mudou, o texto não), e P-7 rescanearia
  # citações antigas já grandfathered como se fossem novas (foi assim que
  # a citação de (162) a "(101 - ...)", já tratada como não-issue no
  # comentário acima, voltou a disparar SUSPEITO testando MEMÓRIAS (271)).
  # Pular aqui não abre brecha: a garantia real é a permutação byte-exata
  # do P-5, mais forte que P-7 -- se nenhum byte é novo, não há citação
  # nova pra checar.
  # Pula só quando o P-5 REALMENTE tomou o ramo de permutação nesta corrida
  # (P5_RAMO, setado por p5_append_only, que roda antes de P-7 no main).
  # A versão anterior perguntava por _p5_migracao_pendente -- a MARCA no
  # disco, não o ramo tomado. Como a marca vive em propostas/aplicadas/ e
  # esse diretório nunca é limpo por desenho, a marca de 06/09/2026 deixou
  # o P-7 em SKIP permanente: medido em 09/09/2026, "veredito: SKIP" com o
  # P-5 tendo passado pelo ramo ORDINÁRIO (havia bytes novos, e a mensagem
  # impressa afirmava o contrário). Toda citação nova entrou sem checagem
  # nesse intervalo. O controle em si estava íntegro -- testado contra
  # positivo e negativo conhecidos: citação real -> passa, citação
  # fabricada -> pega. Era só o portão de entrada que estava travado aberto.
  # Duas condições, não uma: o P-5 foi pela permutação E a permutação não
  # trouxe entrada nova. A segunda metade veio depois (mesma data), quando a
  # suíte mostrou que permutação com entrada nova existe e é comum -- ver o
  # comentário em p5_append_only.
  if [ "${P5_RAMO:-ordinario}" = "permutacao" ] && [ "${P5_ENTRADAS_NOVAS:-0}" -eq 0 ]; then
    echo "P-7: P-5 tomou o ramo de PERMUTAÇÃO e nenhuma entrada nova veio junto -- pulado (nada a citar que já não estivesse no canon)."
    PERIMETRO_ESTADO="SKIP"
    return 0
  fi
  local tmp_novo tmp_diff tmp_combinado codigo f
  tmp_novo="$(mktemp)"
  tmp_diff="$(mktemp)"
  tmp_combinado="$(mktemp)"
  if ! git show :MEMÓRIAS.md > "$tmp_novo" 2>/dev/null; then
    cat MEMÓRIAS.md > "$tmp_novo" 2>/dev/null
  fi
  # Desde a "MEMÓRIAS por período" (Fase 4): quente (MEMÓRIAS.md) só tem
  # as entradas recentes -- uma citação nova pode apontar pra uma entrada
  # que já migrou pra morno ou foi congelada em frio. Sem isto, P-7
  # reprovaria como "não existe" toda citação a história relocada -- falso
  # positivo, não achado real. O universo de busca junta as três camadas;
  # o DIFF checado continua sendo só o que entrou em quente (só lá se
  # escreve entrada nova).
  cat "$tmp_novo" > "$tmp_combinado"
  if git show :MEMORIAS-MORNO.md > /dev/null 2>&1; then
    git show :MEMORIAS-MORNO.md >> "$tmp_combinado"
  elif [ -f MEMORIAS-MORNO.md ]; then
    cat MEMORIAS-MORNO.md >> "$tmp_combinado"
  fi
  for f in MEMORIAS-FRIO-*.md; do
    [ -e "$f" ] || continue
    cat "$f" >> "$tmp_combinado"
  done
  git diff --cached -U0 -- MEMÓRIAS.md 2>/dev/null | grep -E '^\+' | grep -vE '^\+\+\+' | sed 's/^\+//' > "$tmp_diff"
  checar_citacao "$tmp_diff" "$tmp_combinado"
  codigo=$?
  rm -f "$tmp_novo" "$tmp_diff" "$tmp_combinado"
  return "$codigo"
}

