#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

# --- P-11 ----------------------------------------------------------------
# Silos por modelo (.hidrata-<modelo>.md) nunca entram no canon. Vêm do
# hook gerar-hidratacao.sh, um por modelo-alvo, e
# podem conter bloco MOD sensível (MOD de outra família, dado privado) num
# repositório PÚBLICO. A defesa de primeira linha é o `.gitignore`
# (`.hidrata-*.md`) + o `git add` de nomes literais no pre-commit; P-11 é
# o backstop pro caso que nenhum dos dois cobre: `git add -f` manual.
# Achado da cadeia de auditoria de 3.1 (Camada C, 31/08/2026): `.gitignore`
# sozinho não é garantia -- `-f` fura, é comportamento padrão do git.
# Só `.hidrata.md` (o comum, sem bloco MOD que declare `modelo-alvo:`) é
# artefato público. FALHA o commit -- mesma severidade de P-8.
# Fonte: REGRAS.md, "Princípios" (Segurança) · REGRAS.md, "O Conselho"
# item 3 · PROJETO.md, "Memória e hidratação" (silos Fase 2).
_p11_eh_silo() {
  # `.hidrata-<algo>.md` casa; `.hidrata.md` (o comum, versionado) NÃO --
  # não há `-` depois de `.hidrata`.
  case "$1" in
    .hidrata-*.md) return 0 ;;
    *) return 1 ;;
  esac
}


_p11_conteudo_de_silo() {
  # Segunda camada, por CONTEÚDO. _p11_eh_silo olha só o NOME, e nome se
  # troca: `cp .hidrata-seth.md notas.md && git add notas.md` nunca teve
  # nome de silo, então nem a regra de nome nem o `--no-renames` abaixo o
  # pegam -- não houve rename, houve cópia. MEDIDO 09/09/2026: passava
  # limpo, com `modelo-alvo:` e MOD no corpo, pro repositório PÚBLICO.
  # Marca de MOD: o cabeçalho `modelo-alvo:` no início da linha,
  # obrigatório em bloco MOD (REGRAS, "O Conselho" item 3).
  # Falsos positivos medidos no repo inteiro: 1 -- o chunk frio
  # MEMORIAS-FRIO-2026-09-06-com-migrado.md, que REGISTRA o formato em vez
  # de carregar MOD vivo. Por isso a lista de exclusão: história e canon,
  # onde citar o cabeçalho é o trabalho normal do arquivo. Silo de verdade
  # nunca tem nome dessa lista -- se tiver, P-5/P-14 já brigam por outro
  # motivo. Esta camada é o que salvou P-14 do mesmo furo (selar.sh
  # --check pegou o que a listagem staged não viu).
  case "$1" in
    MEMÓRIAS.md|MEMORIAS-MORNO.md|MEMORIAS-FRIO-*.md|REGRAS.md|PROJETO.md|.hidrata.md|INDICE_MEMORIAS*.md) return 1 ;;
  esac
  git show ":$1" 2>/dev/null | grep -qaE '^modelo-alvo:[[:space:]]*[A-Za-z]'
}


p11_silos_nao_versionados() {
  local staged f ruim=0
  # `--no-renames` pelo mesmo motivo de p8_quarentena: sem ele, `git mv`
  # de um silo staged pra um nome inocente apaga o path de silo da
  # listagem e P-11 dá OK. MEDIDO 09/09/2026 (vermelho/verde): silo com
  # nome de silo -> SUSPEITO; o MESMO arquivo renomeado -> "veredito: OK",
  # com `modelo-alvo:` e MOD privado indo pro repositório PÚBLICO.
  staged="$(git -c core.quotepath=false diff --cached --no-renames --name-only)"
  [ -z "$staged" ] && return 0
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if _p11_eh_silo "$f"; then
      echo "SUSPEITO (P-11): '$f' é um silo por modelo e está staged. Por que importa: silo pode conter bloco MOD sensível (MOD de outra família) e o repositório é público -- só '.hidrata.md' (o comum, sem MOD com modelo-alvo) entra no canon. O que fazer: 'git restore --staged $f' -- o hook gerar-hidratacao.sh regenera o silo na árvore da Máquina quando preciso; se veio de 'git add -f', não force silo pro commit."
      ruim=1
    elif _p11_conteudo_de_silo "$f"; then
      echo "SUSPEITO (P-11): '$f' não tem nome de silo, mas o conteúdo staged tem cabeçalho 'modelo-alvo:' -- é bloco MOD. Por que importa: MOD é privado por padrão (REGRAS, 'O Conselho' item 2/3) e este repositório é público; renomear ou copiar um silo não o torna publicável. O que fazer: 'git restore --staged $f'. Se for texto sobre o formato (não MOD vivo), o lugar é MEMÓRIAS/REGRAS, que estão fora desta checagem."
      ruim=1
    fi
  done <<< "$staged"
  return "$ruim"
}

