#!/usr/bin/env bash
# rodar_par.sh -- um par do paralelo P8-02 (Hermes vs. grafo+OmniRoute).
# Roda o pedido pelo grafo num clone fresco, guarda a saída inteira, RECUSA no
# portão (nada commita no clone), e acrescenta 1 linha em redesign/grafo/paralelo.md.
# O resultado do Hermes o Humano cola na coluna à mão.
#
# Uso:  redesign/grafo/rodar_par.sh <trabalho|conselho|verificacao> "<pedido>"
set -u
REPO="$HOME/agata"
CLONE="$HOME/.cache/agata/paralelo-clone"
PY="$REPO/redesign/grafo/.venv/bin/python"
PARALELO="$REPO/redesign/grafo/paralelo.md"
RUNS="$REPO/redesign/grafo/paralelo-runs"

[ "$#" -eq 2 ] || { echo "uso: $0 <trabalho|conselho|verificacao> \"<pedido>\"" >&2; exit 2; }
tipo="$1"; pedido="$2"
case "$tipo" in trabalho|conselho|verificacao) ;; *) echo "tipo inválido: $tipo" >&2; exit 2 ;; esac

n="$(date +%y%m%d-%H%M%S)"
mkdir -p "$RUNS"
rm -rf "$CLONE"
git clone --local --no-hardlinks --quiet "$REPO" "$CLONE"
git -C "$CLONE" switch --quiet redesign 2>/dev/null || git -C "$CLONE" switch --quiet -c redesign origin/redesign

run_file="$RUNS/par-$n.txt"
"$PY" "$REPO/redesign/grafo/grafo.py" run "$pedido" --repo "$CLONE" --thread "par-$n" --tipo "$tipo" > "$run_file" 2>&1
"$PY" "$REPO/redesign/grafo/grafo.py" resume --thread "par-$n" --repo "$CLONE" --recusar >> "$run_file" 2>&1

# leitura rápida direto do arquivo de run (sem depender do schema JSON)
rota="$(grep -oE 'rotear:[a-z]+' "$run_file" | head -1 | cut -d: -f2)"
modelo="$(grep -oE 'trabalhar:[^"]*(minimax|gemini|gpt-oss|glm|llamacpp-local|ollama-local)[^"[:space:]]*' "$run_file" | head -1)"
per="$(grep -oE 'RESULTADO GERAL: [A-Z]+' "$run_file" | head -1 | awk '{print $3}')"
fab="$(grep -oiE '[0-9]+ cita[cç][aã]o' "$run_file" | head -1)"
portao="$(grep -q '"pausado_no_portao": true' "$run_file" && echo pausou || echo '?')"
commit_clone="$(git -C "$CLONE" rev-parse --short HEAD)"

linha="| par-$n | $(date +%F) | ${pedido:0:48} | $tipo | _(Hermes: preencher)_ | rota=${rota:-?} · ${modelo:-trabalhar:?} · perímetro=${per:-?} · fab=${fab:-0} · portão=${portao} | clone @ $commit_clone · run: paralelo-runs/par-$n.txt |"
printf '%s\n' "$linha" >> "$PARALELO"
echo "acrescentado a paralelo.md:"
echo "  $linha"
echo
echo "saída completa: $run_file"
echo "-> rode o MESMO pedido no Hermes e edite a coluna 'Hermes' dessa linha."
