#!/usr/bin/env bash
# Regenera ~/agata/.hermes.md e ~/agata/INDICE_MEMORIAS.md a partir de
# REGRAS.md + PROJETO.md + uma janela de MEMÓRIAS.md.
# Chamado pelo hook pre-commit. Pode ser rodado manualmente também.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=".hermes.md"
INDICE="INDICE_MEMORIAS.md"

# Janela de MEMÓRIAS: por ENTRADA INTEIRA, não por linha crua (linha corta
# no meio da frase). Acumula entradas completas de trás pra frente até um
# orçamento de caracteres; nunca corta uma entrada ao meio — se a última
# entrada sozinha já estourar o orçamento, ela entra inteira mesmo assim.
# Uniforme hoje (um .hermes.md só, sem silo por modelo — Fase 2 ainda não
# construída); calibração por modelo de verdade depende dessa fase existir.
JANELA_ORCAMENTO_CHARS=25000

gerar_indice() {
  {
    echo "<!-- GERADO AUTOMATICAMENTE por .githooks/gerar-hermes-md.sh a partir de MEMÓRIAS.md — não edite direto. -->"
    echo "# Índice de MEMÓRIAS.md"
    echo
    echo "Uma linha por entrada, na ordem em que aparecem no arquivo. Números antes de (49) não são únicos globalmente — a história migrada reinicia numeração por origem; desambigue pela data junto ao número."
    echo
    # Sem -o: o `grep` real do sistema (/usr/sbin/grep, build "3.12-modified"
    # da distro) trunca matches de -oE com [^\n]* em conteúdo UTF-8
    # multibyte — bug achado rodando o hook de verdade (fora do wrapper de
    # ferramenta), não presença teórica. -o nunca foi necessário aqui: os
    # padrões ancoram em ^ e a linha inteira é o que se quer mesmo.
    grep -E '^### [0-9]{4}-[0-9]{2}-[0-9]{2} \([0-9]+\)' MEMÓRIAS.md | sed -E 's/^### //'
    # Rótulos reconhecidos: DIÁRIO, CONSELHO, MOD<qualquer coisa>, CORREÇÃO.
    # Achado real (rodada de otimização de hidratação, 14/08/2026): CORREÇÃO
    # não estava nesta lista -- a entrada (134) CORREÇÃO existia em
    # MEMÓRIAS.md e nunca chegou ao índice nem à hidratação. Adicionar rótulo
    # novo aqui exige o mesmo cuidado: listar explicitamente, não usar
    # curinga genérico que engoliria parênteses maiúsculos não intencionais.
    grep -E '^\([0-9]+\) (DIÁRIO|CONSELHO|MOD[^—]*|CORREÇÃO) — [0-9]{2}/[0-9]{2}/[0-9]{4}' MEMÓRIAS.md
  } > "$INDICE"
}

janela_memorias() {
  awk -v budget="$JANELA_ORCAMENTO_CHARS" '
    /^\([0-9]+\) (DIÁRIO|CONSELHO|MOD|CORREÇÃO)/ { hdr[++n]=NR }
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
}

# Checagem de reconciliação (heurística, não semântica): entre as últimas
# entradas de MEMÓRIAS, quais números NÃO aparecem citados em PROJETO.md.
# Não é prova de contradição — é sinal barato de deriva possível. Não
# bloqueia o commit; só avisa no output do hook, pra alguém decidir olhar.
checar_reconciliacao() {
  local n_checar=10
  local avisos=0
  while read -r num; do
    [ -z "$num" ] && continue
    if ! grep -q "($num)" PROJETO.md; then
      echo "aviso reconciliação: entrada ($num) de MEMÓRIAS não é citada em PROJETO.md" >&2
      avisos=$((avisos + 1))
    fi
  done < <(grep -E '^\([0-9]+\) (DIÁRIO|CONSELHO|MOD|CORREÇÃO)' MEMÓRIAS.md | grep -oE '^\([0-9]+\)' | tr -d '()' | tail -n "$n_checar")
  if [ "$avisos" -gt 0 ]; then
    echo "checagem de reconciliação: $avisos aviso(s) — heurística por citação, não prova de contradição" >&2
  fi
}

gerar_indice

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

echo "gerado: $OUT ($(wc -c < "$OUT") bytes), $INDICE ($(wc -c < "$INDICE") bytes)"
