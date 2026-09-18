#!/usr/bin/env bash
# P-18 -- avisa quando a geração da âncora de SHA (PROMPT_CARREGAMENTO.md,
# REGRAS.md, PROJETO.md, MEMÓRIAS.md) falhou fail-soft num commit anterior
# e ainda não foi corrigida. Doutrina P-6/P-9: barulho, nunca bloqueio --
# a âncora sempre foi "conveniência pra sessões só-HTTP" (.githooks/pre-commit),
# não controle de segurança, e continua não sendo um aqui.
#
# Fonte do marcador: .githooks/pre-commit escreve uma linha em
# "$(git rev-parse --git-dir)/AGATA_ANCORA_AVISOS.log" (fora do repo
# versionado, local a esta cópia) toda vez que atualizar_ancora_prompt.py
# falha pra algum dos 4 arquivos. Mecaniza o detector que MEMÓRIAS (277)
# já registrava como existente só no texto ("campo 'Escrito em:' comparado
# com a hora medida na abertura da sessão") -- aqui vira checagem automática
# do próprio perímetro, em vez de depender de alguém lembrar de comparar.

p18_ancora_falha() {
  local log="${1:-$(git rev-parse --git-dir 2>/dev/null)/AGATA_ANCORA_AVISOS.log}"
  [ -f "$log" ] || return 0

  local linha arquivo commit_falho commits_desde
  while IFS= read -r linha; do
    [ -z "$linha" ] && continue
    arquivo="$(echo "$linha" | awk '{print $2}')"
    commit_falho="$(echo "$linha" | awk '{print $3}')"
    [ -z "$commit_falho" ] && continue
    commits_desde="$(git rev-list --count "${commit_falho}..HEAD" 2>/dev/null || echo 0)"
    if [ "$commits_desde" -gt "${P18_MAX_COMMITS:-1}" ]; then
      echo "AVISO (P-18): âncora de SHA em $arquivo não atualiza há $commits_desde commits (desde $commit_falho) -- reveja .githooks/pre-commit ou rode scripts/atualizar_ancora_prompt.py à mão."
    fi
  done < "$log"
  return 0
}
