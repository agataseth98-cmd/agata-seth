#!/usr/bin/env bash
# hash_ir.sh -- hash de conteudo REPRODUZIVEL de um diretorio de IR OpenVINO.
#
# Contexto: o models/manifest.json tem um campo `ir_sha256_xmlbin` por recurso
# OpenVINO, mas a FORMULA de calculo nunca foi registrada (o chat 3 calculou e
# nao anotou; nenhum recorte obvio -- `cat xml bin`, `cat bin xml`, hash de
# hashes -- reproduz os valores gravados). O TESTE DE RESTORE do P7-03 (restic
# restore num scratch + `diff -rq` contra a arvore viva) e' a garantia real de
# fidelidade; este hash e' so um rotulo estavel.
#
# Formula (fixada 2026-09-03, chat 6): sha256 da concatenacao de TODOS os
# arquivos do diretorio (menos model_cache/, que e' cache de GPU gerado em
# runtime), na ordem de `LC_ALL=C sort`.
#
# Uso:  hash_ir.sh <dir-do-IR>
#   ex: hash_ir.sh ~/.cache/agata/openvino/embeddings/multilingual-e5-small-int8
set -eu
d="${1:?uso: hash_ir.sh <dir>}"
[ -d "$d" ] || { echo "nao e' diretorio: $d" >&2; exit 2; }
( cd "$d" && find . -type f ! -path './model_cache/*' | LC_ALL=C sort | xargs sha256sum | sha256sum | cut -d' ' -f1 )
