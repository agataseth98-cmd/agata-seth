#!/usr/bin/env bash
# P-22 -- derivados de hidratação rastreados não podem divergir do HEAD sem a
# fonte ter mudado. MEMÓRIAS (333): `.hidrata.md` e os dois índices voltaram a
# um conteúdo velho na árvore de trabalho, com MEMÓRIAS.md intacto; causa raiz
# segue `lacuna` (349). Fecha a classe, não o caso: qualquer repetição aparece
# na próxima corrida do perímetro, em vez de ser achada por acaso.
# AVISA, nunca falha -- o remédio é regenerar, e o pre-commit já regenera.
#
# Fonte mexida (index ou árvore) = regeneração legítima em andamento: silêncio.

P22_DERIVADOS=(".hidrata.md" "INDICE_MEMORIAS.md" "INDICE_MEMORIAS_PALAVRAS-CHAVE.md")
P22_FONTES=("MEMÓRIAS.md" "MEMORIAS-MORNO.md" "memoria/frio" "PROJETO.md" "REGRAS.md"
            "PROTOCOLOS.md" "FALHAS.md" "PROMPT_CARREGAMENTO.md" ".githooks/gerar-hidratacao.sh")

p22_derivados_drift() {
  if ! git diff --quiet HEAD -- "${P22_FONTES[@]}" 2>/dev/null; then
    echo "P-22: fonte do canon modificada -- derivados podem divergir legitimamente, nada a checar."
    return 0
  fi
  local d sujos=()
  for d in "${P22_DERIVADOS[@]}"; do
    git ls-files --error-unmatch -- "$d" >/dev/null 2>&1 || continue
    git diff --quiet HEAD -- "$d" 2>/dev/null || sujos+=("$d")
  done
  [ "${#sujos[@]}" -eq 0 ] && return 0
  echo "AVISO (P-22): derivado(s) diferente(s) do HEAD sem nenhuma fonte ter mudado: ${sujos[*]}. Por que importa: foi o drift de (333) -- quem lê o derivado lê história velha ou truncada. O que fazer: \`bash .githooks/gerar-hidratacao.sh\` e conferir que \`git status\` volta limpo; se repetir, anotar hora e o que estava aberto (causa raiz ainda é lacuna, (349))."
  return 0
}
