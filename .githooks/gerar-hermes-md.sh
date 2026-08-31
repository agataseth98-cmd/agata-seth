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

# --- Fase 2 / Bloco 3.1: silos por modelo ------------------------------
# Modelos-alvo que ganham um .hermes-<modelo>.md PRÓPRIO: a janela de
# MEMÓRIAS e as linhas de índice desse arquivo não trazem bloco MOD de
# OUTRO modelo-alvo. Todo modelo fora desta lista usa o .hermes.md COMUM,
# que não traz NENHUM bloco MOD que declare `modelo-alvo:`.
# Hoje só `claude` tem bloco MOD no canon ((51)); `seth`/`gemini`/`glm`
# são alvos previsíveis de Fase 3 -- listados para o arquivo já existir
# com a fronteira certa antes do primeiro MOD sensível ser escrito.
# Efeito de tamanho hoje ≈ nulo (dossiê S1, Achado 4); o valor é a
# fronteira de confidencialidade, não economia de token.
# Os .hermes-<modelo>.md NÃO são versionados (ver .gitignore) nem
# adicionados pelo pre-commit -- vivem só na árvore da Máquina, o único
# lugar onde MOD sensível pode aparecer. O .hermes.md comum continua
# versionado e é o único artefato de hidratação público.
ALVOS_SILO=(claude seth gemini glm)

# Orçamento de janela por modelo (Regra 8, 3 passadas qwen local 31/08/2026:
# convergência em "calibrar por janela de contexto do modelo", não valor
# fixo). Sem entrada aqui -> usa JANELA_ORCAMENTO_CHARS. Hoje todos os
# alvos têm >= 64k de contexto e 25000 cabe em todos; o mapa existe pra
# calibrar sem novo patch quando um alvo de janela menor entrar.
declare -A JANELA_POR_MODELO=()

# Emite MEMÓRIAS.md sem os blocos MOD que não pertencem a $1.
#   $1 vazio -> arquivo comum: remove TODO bloco MOD que declara `modelo-alvo:`.
#   $1 = X   -> silo de X: remove bloco MOD cujo `modelo-alvo:` (primeiro
#              token, ignorando parênteses/comentário) seja != X.
# Bloco MOD SEM linha `modelo-alvo:` é MAL-FORMADO -- REGRAS.md, "O Conselho"
# item 3: "Cabeçalho `modelo-alvo:` obrigatório". NÃO entra em nenhum
# artefato de hidratação (nem comum, nem silo). O hook emite um AVISO em
# stderr nomeando a entrada, uma vez, na passada do arquivo comum. A entrada
# segue intacta em MEMÓRIAS.md (Regra 4: nada se apaga) -- só não é injetada.
# Emenda da Camada B ao rascunho v1, autorizada pelo Humano 31/08/2026: a v1
# mantinha esse bloco "em todos por ser indistinguível de coletivo" e foi
# rejeitada -- vazava um MOD mal-formado para todo silo.
# DIÁRIO / CONSELHO / CORREÇÃO nunca são tocados: comuns a todos por
# definição. O bloco migrado ("## Migrado de DIÁRIO.md" até o fim físico)
# passa verbatim.
filtrar_mod_por_alvo() {
  local alvo="${1:-}"
  awk -v alvo="$alvo" '
    function flush(   k) {
      # MOD sem `modelo-alvo:` valido -> mal-formado -> fora de todo artefato.
      # Aviso uma vez so (passada do comum, alvo vazio); entrada fica em MEMORIAS.md.
      if (n > 0 && em_mod && !tem_alvo) {
        pular = 1
        if (alvo == "")
          printf "AVISO: bloco MOD sem linha \"modelo-alvo:\" -- fora de TODOS os artefatos de hidratacao (comum e silos); entrada intacta em MEMORIAS.md: %s\n", buf[1] > "/dev/stderr"
      }
      if (n > 0 && !pular) for (k = 1; k <= n; k++) print buf[k]
      n = 0; pular = 0; em_mod = 0; tem_alvo = 0
    }
    migrado { print; next }
    /^## Migrado de DIÁRIO\.md/ { flush(); print; migrado = 1; next }
    /^\([0-9]+\) (DI[AÁ]RIO|CONSELHO|MOD|CORRE[CÇ][AÃ]O)/ {
      flush()
      em_mod = ($0 ~ /^\([0-9]+\) MOD([ (]|$)/)
      buf[++n] = $0
      next
    }
    {
      buf[++n] = $0
      if (em_mod && $0 ~ /^modelo-alvo:[ \t]*[^ \t]/) {
        tem_alvo = 1
        ab = $0
        sub(/^modelo-alvo:[ \t]*/, "", ab)
        sub(/[ \t(].*$/, "", ab)
        if (alvo == "" || ab != alvo) pular = 1
      }
    }
    END { flush() }
  ' MEMÓRIAS.md
}

# Filtra as linhas de índice (título só, sem corpo) por modelo-alvo,
# lendo o token do próprio cabeçalho "(n) MOD <modelo>". $1 vazio =
# arquivo comum (nenhuma linha MOD com modelo nomeado). Roda só na
# montagem do .hermes*, o INDICE_MEMORIAS*.md em disco fica completo.
filtrar_indice_por_alvo() {
  local alvo="${1:-}"
  awk -v alvo="$alvo" '
    /^\([0-9]+\) MOD / { if (alvo == "" || $3 != alvo) next }
    { print }
  '
}

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
  local modelo="${1:-}"
  local budget="$JANELA_ORCAMENTO_CHARS"
  # `${arr[$k]}` com $k vazio é "subscrito incorreto" sob `set -u` -- só
  # consulta o mapa quando há modelo.
  [ -n "$modelo" ] && budget="${JANELA_POR_MODELO[$modelo]:-$JANELA_ORCAMENTO_CHARS}"
  local mem
  mem="$(filtrar_mod_por_alvo "$modelo")"
  # O marcador vive no preâmbulo, nunca dentro de um bloco MOD -- o filtro
  # nunca o remove. Checa direto no arquivo: pipar o stream de ~1 MB de
  # $mem em `grep -q` fecha o pipe cedo e, sob `pipefail`, faz a condição
  # inteira "falhar" (SIGPIPE no printf de cima) -- caía no ramo errado.
  if grep -qF "$MARCADOR_ENTRADAS_NOVAS" MEMÓRIAS.md; then
    # Formato novo (MEMÓRIAS (271)+): mais recente logo após o marcador.
    # Acumula entradas completas de CIMA pra baixo até o orçamento; nunca
    # corta uma entrada ao meio -- se a primeira sozinha já estourar o
    # orçamento, entra inteira mesmo assim. O bloco migrado (mais antigo,
    # heading "## Migrado de DIÁRIO.md", fim físico do arquivo) nunca entra
    # na janela por orçamento -- limita o fim do corpo a ele, não a `total`,
    # senão a última entrada "engoliria" o bloco inteiro na medição.
    printf '%s\n' "$mem" | awk -v budget="$budget" '
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
    '
  else
    # Formato antigo: mais recente no fim físico. Acumula de trás pra
    # frente até o orçamento -- comportamento original, MEMÓRIAS (191)/(192).
    printf '%s\n' "$mem" | awk -v budget="$budget" '
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
    '
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

# Monta um arquivo de hidratação. $1 = modelo-alvo (vazio = arquivo comum),
# $2 = caminho de saída. REGRAS/PROJETO são idênticos em todos; só a janela
# de MEMÓRIAS e as linhas de índice MOD mudam por silo.
montar_hermes() {
  local modelo="${1:-}" out="$2"
  local _budget="$JANELA_ORCAMENTO_CHARS"
  [ -n "$modelo" ] && _budget="${JANELA_POR_MODELO[$modelo]:-$JANELA_ORCAMENTO_CHARS}"
  {
    echo "<!--"
    echo "ARQUIVO GERADO AUTOMATICAMENTE — NÃO EDITE DIRETAMENTE."
    echo "Gerado por .githooks/gerar-hermes-md.sh a partir de REGRAS.md + PROJETO.md + janela de MEMÓRIAS.md + INDICE_MEMORIAS.md."
    echo "Para mudar o conteúdo, edite REGRAS.md, PROJETO.md ou MEMÓRIAS.md e faça commit —"
    echo "o hook pre-commit regenera este arquivo sozinho."
    if [ -n "$modelo" ]; then
      echo ""
      echo "SILO: $modelo. Esta variante NÃO traz bloco MOD de outro modelo-alvo."
      echo "Não é versionada (.gitignore) nem adicionada pelo pre-commit -- só existe"
      echo "na árvore da Máquina. A seleção de qual arquivo o Hermes injeta por sessão"
      echo "NÃO está construída neste .diff (ver seção 'lacuna' da proposta)."
    else
      echo ""
      echo "ARQUIVO COMUM: nenhum bloco MOD que declare 'modelo-alvo:'. É o fallback"
      echo "para todo modelo sem silo próprio, e o único artefato de hidratação público."
    fi
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
    filtrar_indice_por_alvo "$modelo" < "$INDICE"
    echo ""
    echo "# MEMÓRIAS.md (janela por entrada inteira, orçamento ${_budget} chars${modelo:+, silo: $modelo})"
    echo ""
    janela_memorias "$modelo"
  } > "$out"
}

montar_hermes "" "$OUT"
SILO_FILES=()
for _m in "${ALVOS_SILO[@]}"; do
  montar_hermes "$_m" ".hermes-${_m}.md"
  SILO_FILES+=(".hermes-${_m}.md")
done

checar_reconciliacao || true

_silos_txt=""
for _f in "${SILO_FILES[@]}"; do
  _silos_txt="${_silos_txt}, ${_f} ($(wc -c < "$_f") bytes)"
done
if [ -f "$INDICE_CHAVES" ]; then
  echo "gerado: $OUT ($(wc -c < "$OUT") bytes), $INDICE ($(wc -c < "$INDICE") bytes), $INDICE_CHAVES ($(wc -c < "$INDICE_CHAVES") bytes, fora de .hermes.md)${_silos_txt}"
else
  echo "gerado: $OUT ($(wc -c < "$OUT") bytes), $INDICE ($(wc -c < "$INDICE") bytes), $INDICE_CHAVES: FALHOU nesta rodada, ver aviso acima${_silos_txt}"
fi
