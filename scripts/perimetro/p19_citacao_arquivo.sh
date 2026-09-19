#!/usr/bin/env bash
# P-19 -- citação de arquivo:linha em entrada NOVA de MEMÓRIAS.md confere
# contra a fonte real. Mecaniza a falha mais recorrente do catálogo
# (REGRAS.md, "Catálogo de falhas conhecidas"): 8 das 20 falhas catalogadas
# -- (59) até (250)/(251) -- são desta família: citar arquivo+linha+trecho
# sem checar contra a fonte antes de escrever. Duas ocorrências frescas
# motivaram esta proposta: uma minuta externa (Conselho Remoto, GLM) com
# dois erros reais de linha só achados testando contra o repositório de
# verdade, e uma citação MINHA que dei por fabricada num `grep` que falhou
# por engano -- a citação era 100% correta; a checagem manual é que falhou.
#
# Nome "P-19" reclamado FORMALMENTE aqui pela primeira vez. Numa conversa
# recente este número foi usado informalmente para outro mecanismo -- a
# guarda de integridade da âncora dentro de `.githooks/pre-commit` (a que
# aborta o commit se a atualização da âncora de SHA varre conteúdo fora
# dela) -- mas aquela guarda NUNCA foi registrada aqui via `cabecalho
# "P-19"` (confirmado com `grep -oE 'cabecalho "P-[0-9]+"' scripts/perimetro.sh`
# antes desta proposta: só P-1..P-18 existiam). Este controle é o primeiro a
# ocupar o número de verdade; a guarda da âncora segue sem número, chamada
# só pelo nome descritivo daqui em diante.
#
# Doutrina P-6/P-9/P-18: AVISO SÓ, nunca falha o commit. Motivo, testado e
# não teórico: o próprio verificador (scripts/verificar_citacao_arquivo.py)
# tem falso-positivo conhecido -- citação sem trecho entre aspas pra
# conferir, ou prosa com mais de um trecho entre crases perto da citação
# (ex.: um hash curto de commit entre a referência de linha e o trecho de
# verdade), pode marcar FALHA numa citação correta. Achado rodando contra o
# documento real da minuta GLM v2, não em caso sintético -- documentado no
# docstring do próprio script. "Nenhuma checagem entra bloqueando antes de
# passar verde um tempo de verdade" é a régua já usada para promover P-18 a
# FALHA-class no futuro, se for o caso; a mesma régua vale aqui.
#
# Escopo igual ao P-7: só a entrada NOVA que este commit ACRESCENTA a
# MEMÓRIAS.md, nunca o arquivo inteiro -- reaudita a história toda a cada
# commit seria caro e ruidoso, e citação já commitada no passado já teve a
# chance de virar entrada nova de correção (REGRAS, Regra 4 -- corrigir é
# entrada nova, nunca edição). Mesmo guarda de permutação do P-7: sem ele,
# uma migração de camada (quente -> morno/frio) aparece pro `git diff` como
# bloco "+" gigante, e este controle rescanearia citações antigas como se
# fossem novas -- o mesmo bug que já pegou o P-7 de verdade (comentário em
# p07_citacao.sh, e o mesmo teste de regressão se aplica aqui).

p19_citacao_arquivo() {
  if ! git rev-parse HEAD >/dev/null 2>&1; then
    return 0
  fi
  if [ "${P5_RAMO:-ordinario}" = "permutacao" ] && [ "${P5_ENTRADAS_NOVAS:-0}" -eq 0 ]; then
    echo "P-19: P-5 tomou o ramo de PERMUTAÇÃO e nenhuma entrada nova veio junto -- pulado (nada de novo pra citar)."
    return 0
  fi

  local raiz verificador tmp_diff saida
  raiz="$(git rev-parse --show-toplevel 2>/dev/null)" || return 0
  verificador="$raiz/scripts/verificar_citacao_arquivo.py"
  [ -f "$verificador" ] || return 0
  if ! command -v python3 >/dev/null 2>&1; then
    echo "AVISO (P-19): python3 não encontrado -- checagem pulada."
    return 0
  fi

  tmp_diff="$(mktemp)"
  git diff --cached -U0 -- MEMÓRIAS.md 2>/dev/null | grep -E '^\+' | grep -vE '^\+\+\+' | sed 's/^\+//' > "$tmp_diff"

  if [ ! -s "$tmp_diff" ]; then
    rm -f "$tmp_diff"
    return 0
  fi

  saida="$(python3 "$verificador" --raiz "$raiz" < "$tmp_diff" 2>&1)"
  rm -f "$tmp_diff"

  if echo "$saida" | grep -q '^FALHA'; then
    echo "AVISO (P-19): citação de arquivo:linha na entrada nova de MEMÓRIAS.md não bate com a fonte -- confira antes de assinar/aplicar (verificador tem falso-positivo conhecido, ver docstring)."
    echo "$saida" | grep -E '^(OK|FALHA)'
  fi
  return 0
}
