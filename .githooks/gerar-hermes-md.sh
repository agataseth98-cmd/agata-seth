#!/usr/bin/env bash
# Regenera ~/agata/.hermes.md e ~/agata/INDICE_MEMORIAS.md a partir de
# REGRAS.md + PROJETO.md + uma janela de MEMÓRIAS.md.
# Chamado pelo hook pre-commit. Pode ser rodado manualmente também.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=".hermes.md"
INDICE="INDICE_MEMORIAS.md"
# Índice paralelo com palavras-chave por entrada (grep, nunca embedding --
# decisão (115)). Fica DE FORA de $OUT de propósito: medido rodando os dois
# lados antes de propor isto -- o índice com palavras-chave inteiro pesa 73%
# a mais que o índice puro (24K -> 41,5K chars nesta base). Embutir isso em
# .hermes.md pioraria exatamente o problema que este projeto já brigou pra
# resolver (MEMÓRIAS 103-105, 220: carregador cortando contexto em
# silêncio) -- então este arquivo fica só em disco, pra `grep` sob demanda
# de qualquer sessão com Máquina, nunca auto-injetado.
INDICE_CHAVES="INDICE_MEMORIAS_PALAVRAS-CHAVE.md"

# Janela de MEMÓRIAS: por ENTRADA INTEIRA, não por linha crua (linha corta
# no meio da frase). Acumula entradas completas de trás pra frente até um
# orçamento de caracteres; nunca corta uma entrada ao meio — se a última
# entrada sozinha já estourar o orçamento, ela entra inteira mesmo assim.
# Uniforme hoje (um .hermes.md só, sem silo por modelo — Fase 2 ainda não
# construída); calibração por modelo de verdade depende dessa fase existir.
JANELA_ORCAMENTO_CHARS=25000
INDICE_RECENTES_COMPLETAS=30
INDICE_TETO_ANTIGAS=80

# Âncora de MEMÓRIAS (271): quando presente no arquivo, o corpo (49)+ vem
# logo depois dela, mais recente primeiro; o bloco "Migrado de DIÁRIO.md"
# (mais antigo) fica no fim físico. Ausente = formato antigo (mais recente
# no fim físico) ainda em vigor -- funções abaixo checam os dois estados,
# nunca presumem qual está em vigor.
MARCADOR_ENTRADAS_NOVAS="<!-- ENTRADAS-NOVAS:AQUI"

gerar_indice() {
  {
    echo "<!-- GERADO AUTOMATICAMENTE por .githooks/gerar-hermes-md.sh a partir de MEMÓRIAS.md — não edite direto. -->"
    echo "# Índice de MEMÓRIAS.md"
    echo
    if grep -qF "$MARCADOR_ENTRADAS_NOVAS" MEMÓRIAS.md; then
      echo "Uma linha por entrada, da mais recente pra mais antiga (MEMÓRIAS (271)). Números antes de (49) não são únicos globalmente — a história migrada reinicia numeração por origem; desambigue pela data junto ao número."
    else
      echo "Uma linha por entrada, na ordem em que aparecem no arquivo. Números antes de (49) não são únicos globalmente — a história migrada reinicia numeração por origem; desambigue pela data junto ao número."
    fi
    echo
    # Sem -o: o `grep` real do sistema (/usr/sbin/grep, build "3.12-modified"
    # da distro) trunca matches de -oE com [^\n]* em conteúdo UTF-8
    # multibyte — bug achado rodando o hook de verdade (fora do wrapper de
    # ferramenta), não presença teórica. -o nunca foi necessário aqui: os
    # padrões ancoram em ^ e a linha inteira é o que se quer mesmo.
    #
    # Rótulos reconhecidos: DIÁRIO, CONSELHO, MOD<qualquer coisa>, CORREÇÃO.
    # Achado real (rodada de otimização de hidratação, 14/08/2026): CORREÇÃO
    # não estava nesta lista -- a entrada (134) CORREÇÃO existia em
    # MEMÓRIAS.md e nunca chegou ao índice nem à hidratação. Adicionar rótulo
    # novo aqui exige o mesmo cuidado: listar explicitamente, não usar
    # curinga genérico que engoliria parênteses maiúsculos não intencionais.
    # Grafia sem acento ("DIARIO") e separador "-" (hífen) tolerados desde
    # MEMÓRIAS (271): sessões sem UTF-8 correto (Qwen, entradas (260)-(270))
    # escreveram assim -- achado testando a migração contra o arquivo
    # inteiro, um regex só-acentuado engolia essas entradas inteiras dentro
    # da anterior que batia o padrão.
    #
    # Ordem dos dois `grep`: desde MEMÓRIAS (271) o corpo (49)+ vem primeiro
    # no arquivo físico (mais recente primeiro) e o bloco migrado (mais
    # antigo) por último -- a concatenação abaixo espelha isso, condicional
    # ao marcador existir. Antes da migração, ordem original preservada.
    if grep -qF "$MARCADOR_ENTRADAS_NOVAS" MEMÓRIAS.md; then
      {
        grep -E '^\([0-9]+\) (DI[AÁ]RIO|CONSELHO|MOD[^—-]*|CORRE[CÇ][AÃ]O) [—-] [0-9]{2}/[0-9]{2}/[0-9]{4}' MEMÓRIAS.md
        grep -E '^### [0-9]{4}-[0-9]{2}-[0-9]{2} \([0-9]+\)' MEMÓRIAS.md | sed -E 's/^### //'
      } | python3 scripts/compactar_indice.py "$INDICE_RECENTES_COMPLETAS" "$INDICE_TETO_ANTIGAS"
    else
      {
        grep -E '^### [0-9]{4}-[0-9]{2}-[0-9]{2} \([0-9]+\)' MEMÓRIAS.md | sed -E 's/^### //'
        grep -E '^\([0-9]+\) (DI[AÁ]RIO|CONSELHO|MOD[^—-]*|CORRE[CÇ][AÃ]O) [—-] [0-9]{2}/[0-9]{2}/[0-9]{4}' MEMÓRIAS.md
      } | python3 scripts/compactar_indice.py "$INDICE_RECENTES_COMPLETAS" "$INDICE_TETO_ANTIGAS"
    fi
  } > "$INDICE"
}

janela_memorias() {
  if grep -qF "$MARCADOR_ENTRADAS_NOVAS" MEMÓRIAS.md; then
    # Formato novo (MEMÓRIAS (271)+): mais recente logo após o marcador.
    # Acumula entradas completas de CIMA pra baixo até o orçamento; nunca
    # corta uma entrada ao meio -- se a primeira sozinha já estourar o
    # orçamento, entra inteira mesmo assim. O bloco migrado (mais antigo,
    # heading "## Migrado de DIÁRIO.md", fim físico do arquivo) nunca entra
    # na janela por orçamento -- limita o fim do corpo a ele, não a `total`,
    # senão a última entrada "engoliria" o bloco inteiro na medição.
    awk -v budget="$JANELA_ORCAMENTO_CHARS" '
      /^## Migrado de DIÁRIO\.md/ { migrado=NR }
      /^\([0-9]+\) (DI[AÁ]RIO|CONSELHO|MOD|CORRE[CÇ][AÃ]O)/ { hdr[++n]=NR }
      { line[NR]=$0 }
      END {
        total=NR
        fim_corpo = (migrado > 0 ? migrado - 1 : total)
        if (n == 0) {
          for (j=1; j<=total; j++) print line[j]
        } else {
          # seglen acumula do TOPO fixo (hdr[1]) até o candidato `prox` --
          # espelha o original (que acumulava do candidato até o FIM fixo,
          # caminhando pra trás). Bug real, achado depois de commitar:
          # somar só o tamanho de CADA entrada isolada (sem acumular)
          # nunca estoura o orçamento por entradas pequenas sozinhas --
          # .hermes.md saiu com o arquivo quase inteiro (868KB em vez de
          # ~25KB) na primeira rodada real.
          fim=hdr[1]-1
          for (i=1; i<=n; i++) {
            prox = (i < n) ? hdr[i+1]-1 : fim_corpo
            seglen = 0
            for (j=hdr[1]; j<=prox; j++) seglen += length(line[j]) + 1
            if (seglen > budget && i != 1) break
            fim = prox
          }
          for (j=hdr[1]; j<=fim; j++) print line[j]
        }
      }
    ' MEMÓRIAS.md
  else
    # Formato antigo: mais recente no fim físico. Acumula de trás pra
    # frente até o orçamento -- comportamento original, MEMÓRIAS (191)/(192).
    awk -v budget="$JANELA_ORCAMENTO_CHARS" '
      /^\([0-9]+\) (DI[AÁ]RIO|CONSELHO|MOD|CORRE[CÇ][AÃ]O)/ { hdr[++n]=NR }
      { line[NR]=$0 }
      END {
        total=NR
        if (n == 0) {
          for (j=1; j<=total; j++) print line[j]
        } else {
          start=hdr[n]
          for (i=n; i>=1; i--) {
            seglen = 0
            for (j=hdr[i]; j<=total; j++) seglen += length(line[j]) + 1
            if (seglen > budget && i != n) break
            start = hdr[i]
          }
          for (j=start; j<=total; j++) print line[j]
        }
      }
    ' MEMÓRIAS.md
  fi
}

# Checagem de reconciliação (heurística, não semântica): entre as últimas
# entradas de MEMÓRIAS, quais números NÃO aparecem citados em PROJETO.md.
# Não é prova de contradição — é sinal barato de deriva possível. Não
# bloqueia o commit; só avisa no output do hook, pra alguém decidir olhar.
checar_reconciliacao() {
  local n_checar=10
  local avisos=0
  local corte_cmd="tail"
  # Mais recente no TOPO da lista de números (formato novo) -> "as últimas
  # entradas" são as N PRIMEIRAS da lista, não as N últimas.
  grep -qF "$MARCADOR_ENTRADAS_NOVAS" MEMÓRIAS.md && corte_cmd="head"
  while read -r num; do
    [ -z "$num" ] && continue
    if ! grep -q "($num)" PROJETO.md; then
      echo "aviso reconciliação: entrada ($num) de MEMÓRIAS não é citada em PROJETO.md" >&2
      avisos=$((avisos + 1))
    fi
  done < <(grep -E '^\([0-9]+\) (DI[AÁ]RIO|CONSELHO|MOD|CORRE[CÇ][AÃ]O)' MEMÓRIAS.md | grep -oE '^\([0-9]+\)' | tr -d '()' | "$corte_cmd" -n "$n_checar")
  if [ "$avisos" -gt 0 ]; then
    echo "checagem de reconciliação: $avisos aviso(s) — heurística por citação, não prova de contradição" >&2
  fi
}

gerar_indice_palavras_chave() {
  {
    echo "<!-- GERADO AUTOMATICAMENTE por .githooks/gerar-hermes-md.sh a partir de MEMÓRIAS.md -- não edite direto. -->"
    echo "# Índice de MEMÓRIAS.md, com palavras-chave por entrada"
    echo
    echo "Mesmas entradas de INDICE_MEMORIAS.md, uma linha \"  palavras-chave: ...\" logo"
    echo "abaixo de cada título. Extração puramente mecânica (tokeniza, tira stopword,"
    echo "deduplica) -- scripts/extrair_palavras_chave.py, NUNCA embedding, decisão (115)."
    echo "Pensado pra \`grep -i <termo>\` achar entrada por assunto sem reler o índice"
    echo "inteiro. NÃO entra em .hermes.md -- ver comentário em INDICE_CHAVES acima."
    echo
    if grep -qF "$MARCADOR_ENTRADAS_NOVAS" MEMÓRIAS.md; then
      {
        grep -E '^\([0-9]+\) (DI[AÁ]RIO|CONSELHO|MOD[^—-]*|CORRE[CÇ][AÃ]O) [—-] [0-9]{2}/[0-9]{2}/[0-9]{4}' MEMÓRIAS.md
        grep -E '^### [0-9]{4}-[0-9]{2}-[0-9]{2} \([0-9]+\)' MEMÓRIAS.md | sed -E 's/^### //'
      } | python3 scripts/compactar_indice.py "$INDICE_RECENTES_COMPLETAS" "$INDICE_TETO_ANTIGAS" \
        | python3 scripts/extrair_palavras_chave.py
    else
      {
        grep -E '^### [0-9]{4}-[0-9]{2}-[0-9]{2} \([0-9]+\)' MEMÓRIAS.md | sed -E 's/^### //'
        grep -E '^\([0-9]+\) (DI[AÁ]RIO|CONSELHO|MOD[^—-]*|CORRE[CÇ][AÃ]O) [—-] [0-9]{2}/[0-9]{2}/[0-9]{4}' MEMÓRIAS.md
      } | python3 scripts/compactar_indice.py "$INDICE_RECENTES_COMPLETAS" "$INDICE_TETO_ANTIGAS" \
        | python3 scripts/extrair_palavras_chave.py
    fi
  } > "$INDICE_CHAVES"
}

gerar_indice
# Fail-soft de propósito: índice de palavras-chave é um extra "nível 0",
# best-effort -- se quebrar (script ausente, bug, MEMÓRIAS.md sem entrada
# nenhuma), NÃO pode derrubar a geração de .hermes.md/INDICE_MEMORIAS.md,
# que são o caminho crítico de hidratação. Achado testando de propósito
# antes de propor: sem o `|| ...` abaixo, um `scripts/extrair_palavras_chave.py`
# ausente ou quebrado travava o hook inteiro (nenhum commit passaria).
if ! gerar_indice_palavras_chave; then
  echo "AVISO: geração de $INDICE_CHAVES falhou -- .hermes.md/$INDICE seguem normais, só o índice de palavras-chave (extra, não crítico) ficou de fora desta rodada." >&2
  rm -f "$INDICE_CHAVES"
fi

{
  echo "<!--"
  echo "ARQUIVO GERADO AUTOMATICAMENTE — NÃO EDITE DIRETAMENTE."
  echo "Gerado por .githooks/gerar-hermes-md.sh a partir de REGRAS.md + PROJETO.md + janela de MEMÓRIAS.md + INDICE_MEMORIAS.md."
  echo "Para mudar o conteúdo, edite REGRAS.md, PROJETO.md ou MEMÓRIAS.md e faça commit —"
  echo "o hook pre-commit regenera este arquivo sozinho."
  echo ""
  echo "Motivo de existir: o Hermes só auto-injeta um de"
  echo ".hermes.md / AGENTS.md / CLAUDE.md / .cursorrules no prompt de sistema"
  echo "(nunca REGRAS.md/PROJETO.md/MEMÓRIAS.md diretamente). Embutir aqui evita depender"
  echo "de tool-call (e do modelo acertar offset/wc -l) no início da sessão."
  echo "-->"
  echo ""
  echo "# REGRAS.md"
  echo ""
  cat REGRAS.md
  echo ""
  echo "# PROJETO.md"
  echo ""
  cat PROJETO.md
  echo ""
  cat "$INDICE"
  echo ""
  echo "# MEMÓRIAS.md (janela por entrada inteira, orçamento ${JANELA_ORCAMENTO_CHARS} chars)"
  echo ""
  janela_memorias
} > "$OUT"

checar_reconciliacao || true

if [ -f "$INDICE_CHAVES" ]; then
  echo "gerado: $OUT ($(wc -c < "$OUT") bytes), $INDICE ($(wc -c < "$INDICE") bytes), $INDICE_CHAVES ($(wc -c < "$INDICE_CHAVES") bytes, fora de .hermes.md)"
else
  echo "gerado: $OUT ($(wc -c < "$OUT") bytes), $INDICE ($(wc -c < "$INDICE") bytes), $INDICE_CHAVES: FALHOU nesta rodada, ver aviso acima"
fi
