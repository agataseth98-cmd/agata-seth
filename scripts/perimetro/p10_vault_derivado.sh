#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

p10_vault_derivado() {
  # P-10 (MEMÓRIAS (293)): memoria/obsidian/ é o único derivado gerado FORA do
  # commit (post-commit, gitignorado) -- .hidrata.md e os índices entram no
  # commit pelo pre-commit e não têm como divergir. Aqui: regenera o vault a
  # partir do conteúdo de HEAD num sandbox e confere byte a byte contra o disco.
  # HEAD dos DOIS lados -- comparar contra o disco staged reprovaria todo commit
  # que toca canon (o vault no disco foi gerado do commit anterior).
  local vault="memoria/obsidian"

  # Bootstrap: se o próprio gerador muda neste commit, HEAD tem a versão antiga
  # -- a conferência não faz sentido, adia pro próximo commit.
  if ! git diff --cached --quiet -- scripts/gerar_obsidian.py 2>/dev/null; then
    echo "P-10: scripts/gerar_obsidian.py muda neste commit -- conferência adiada pro próximo."
    PERIMETRO_ESTADO="SKIP"; return 0
  fi
  if [ ! -d "$vault" ]; then
    echo "P-10: $vault/ ainda não existe (clone fresco?) -- o post-commit cria no 1º commit."
    PERIMETRO_ESTADO="SKIP"; return 0
  fi

  local tmp sha data hreal hesp missoes_md_file
  tmp="$(mktemp -d)" || { echo "P-10: mktemp falhou -- pulado."; PERIMETRO_ESTADO="SKIP"; return 0; }
  sha="$(git rev-parse HEAD)"
  data="$(git log -1 --format=%cI)"
  # memoria/missoes/ é gitignorado do repo principal -- `git archive HEAD`
  # nunca o inclui, então a sandbox abaixo não o vê. Calculado aqui, no repo
  # real (que o tem), e repassado por ARQUIVO temporário (não env var: uma
  # missão com milhares de .md rastreados estourou MAX_ARG_STRLEN do kernel,
  # 131072 bytes por variável de ambiente -- achado 15/09/2026, MEMÓRIAS
  # (429). Arquivo não tem esse teto).
  missoes_md_file="$(mktemp)" || { rm -rf "$tmp"; echo "P-10: mktemp (lista) falhou -- pulado."; PERIMETRO_ESTADO="SKIP"; return 0; }
  if [ -d memoria/missoes ]; then
    git -c core.quotepath=false -C memoria/missoes ls-files '*.md' > "$missoes_md_file" 2>/dev/null
  fi
  if ! git archive HEAD | tar -x -C "$tmp" 2>/dev/null; then
    rm -rf "$tmp"; rm -f "$missoes_md_file"
    echo "SUSPEITO (P-10): git archive HEAD falhou -- não dá pra conferir o vault."
    return 1
  fi
  if ! ( cd "$tmp" && AGATA_CANON_SHA="$sha" AGATA_CANON_DATA="$data" \
         AGATA_MISSOES_MD_FILE="$missoes_md_file" \
         python3 scripts/gerar_obsidian.py >/dev/null 2>&1 ); then
    rm -rf "$tmp"; rm -f "$missoes_md_file"
    echo "SUSPEITO (P-10): gerar_obsidian.py falhou ao rodar sobre HEAD -- gerador quebrado."
    return 1
  fi
  hreal="$( cd "$vault" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum )"
  hesp="$(  cd "$tmp/$vault" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum )"
  rm -rf "$tmp"; rm -f "$missoes_md_file"
  if [ "$hreal" != "$hesp" ]; then
    echo "SUSPEITO (P-10): $vault/ não bate com o que gerar_obsidian.py produz de HEAD."
    echo "  o que fazer: rode 'python3 scripts/gerar_obsidian.py' -- e se você editou uma nota à mão, desfaça: correção é entrada nova em MEMÓRIAS, não edição do vault."
    echo "  fonte: MEMÓRIAS (293)"
    return 1
  fi
  return 0
}

