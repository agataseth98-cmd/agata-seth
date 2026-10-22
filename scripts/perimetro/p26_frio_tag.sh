#!/usr/bin/env bash
# P-26 (proposta 21/10/2026, v8): todo chunk frio selado tem tag de git.
# Estado atual: 11 chunks sem tag própria -> PARCIAL (aviso) com a lista. Criar tags = backfill aprovado.
p26_frio_tag() {
  [ -f SELOS.txt ] || return 0
  local faltam="" arq base tag
  while read -r _hash arq _data; do
    [ -z "$arq" ] && continue
    case "$arq" in memoria/frio/*|MEMORIAS-FRIO-*) ;; *) continue ;; esac
    base="${arq%.md}"; base="${base##*/}"; tag="${base}-final"
    git rev-parse -q --verify "refs/tags/$tag" >/dev/null 2>&1 || faltam="$faltam $tag"
  done < SELOS.txt
  if [ -n "$faltam" ]; then
    PERIMETRO_ESTADO="PARCIAL"
    echo "AVISO (P-26): chunks frios sem tag:$faltam (backfill pendente, aprovado pelo Humano)."
  else
    echo "OK (P-26): todo chunk frio selado tem tag."
  fi
  return 0
}
