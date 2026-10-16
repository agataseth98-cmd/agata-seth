#!/usr/bin/env bash
# scripts/agata_busca.sh -- busca por SENTIDO na memória da Agata, para o Humano
# (o "Smart Lookup" / "Smart Context" do Obsidian, com o embedding local da
# Máquina, sem plugin e sem nuvem). MEMÓRIAS (670).
#
#   bash scripts/agata_busca.sh "frase"              # 10 entradas e trechos mais próximos
#   bash scripts/agata_busca.sh "frase" --abrir 1    # abre o 1º resultado no Obsidian
#   bash scripts/agata_busca.sh --contexto "tema"    # pacote .md na Área de trabalho, p/ colar noutra IA
#
# Consulta usa o índice disponível sem atualizá-lo; avisa se faltar cobertura.
# --abrir atua no Obsidian e --contexto grava arquivo: exigem autorização aplicável.
# Atualização é manutenção via post-commit ou --atualizar na Máquina.
# O pacote de contexto é recorte -- a fonte da verdade é o canon.
set -euo pipefail
raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bs="$raiz/scripts/busca_semantica.py"

if [ "${1:-}" = "--contexto" ]; then
  tema="${2:?uso: agata_busca.sh --contexto \"tema\"}"
  mesa="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME")"
  slug="$(printf '%s' "$tema" | tr -cs '[:alnum:]' '-' | tr '[:upper:]' '[:lower:]' | cut -c1-40)"
  python3 "$bs" "$tema" -n 12 --contexto "$mesa/contexto-agata-${slug%-}.md"
  exit 0
fi

frase="${1:?uso: agata_busca.sh \"frase\" [--abrir N] | --contexto \"tema\"}"
if [ "${2:-}" = "--abrir" ]; then
  n="${3:-1}"
  case "$n" in ''|*[!0-9]*) echo "ERRO: --abrir N, com N número" >&2; exit 1 ;; esac
  num="$(python3 "$bs" "$frase" -n "$n" --json | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r[int(sys.argv[1])-1]["num"] if len(r)>=int(sys.argv[1]) else "")' "$n")"
  [ -n "$num" ] || { echo "ERRO: não há resultado $n" >&2; exit 1; }
  nota="memoria/obsidian/entradas/$(printf '%04d' "$num")"
  echo "abrindo ($num) no Obsidian: $nota.md"
  xdg-open "obsidian://open?vault=agata&file=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "$nota")" >/dev/null 2>&1 &
  exit 0
fi
python3 "$bs" "$frase" -n 10
echo
echo "abrir no Obsidian: bash scripts/agata_busca.sh \"$frase\" --abrir N"
