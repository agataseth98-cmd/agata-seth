#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

# --- P-3 -----------------------------------------------------------------
# "Publicação é decisão deliberada; consentimento por trecho, com data"
# (REGRAS, Conselho; PROJETO, Estado de publicação). Escritores automáticos
# conhecidos, enumerados aqui -- cada um com o padrão gitignored que a
# publicação deliberada exige que NUNCA apareça rastreado:
#   - memória nativa do Hermes (USER.md/MEMORY.md e qualquer futuro arquivo
#     da mesma classe) -- achado em (181)/(189), protegido por `memoria/*.md`
#   - backup automático (bundles de git) -- achado em (97)/(98), protegido
#     por `*.bundle`
# Se .gitignore falhou ou foi forçado (`git add -f`), `git ls-files` ainda
# mostra o arquivo rastreado -- é isso que a checagem mede, não a presença
# da regra no .gitignore (regra existir não prova que foi respeitada).
#
# `memoria/frio/` é exceção deliberada desde 25/09/2026 (risco assumido por
# escrito pelo Humano): os chunks selados MORAM lá de propósito, rastreados
# e versionados -- não são escritor automático não-intencional, são o
# canon (P-14 garante a imutabilidade deles depois de selados). O pathspec
# de exclusão ':!memoria/frio/*' tira só essa pasta; um USER.md/MEMORY.md
# batendo direto em memoria/ (a classe real que este controle existe pra
# pegar) continua caindo no SUSPEITO — medido antes de aplicar.
p3_publicacao() {
  local escritores=("memoria/*.md" "*.bundle")
  local ruim=0
  local padrao achados
  for padrao in "${escritores[@]}"; do
    if [ "$padrao" = "memoria/*.md" ]; then
      achados="$(git ls-files -- "$padrao" ":!memoria/frio/*")"
    else
      achados="$(git ls-files -- "$padrao")"
    fi
    if [ -n "$achados" ]; then
      echo "SUSPEITO (P-3): escritor automático '$padrao' tem arquivo RASTREADO, deveria estar fora do índice:"
      echo "$achados" | sed 's/^/  /'
      ruim=1
    fi
  done
  return "$ruim"
}

