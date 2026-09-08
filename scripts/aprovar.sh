#!/usr/bin/env bash
# scripts/aprovar.sh <nome> ["motivo em uma frase"]
#
# Cria propostas/APROVADO-<nome> -- o ato deliberado do Humano que P-8 exige
# (PROJETO.md, "Quarentena estrutural"). Substitui, como CAMINHO PRÁTICO, o
# "abrir editor e criar o arquivo à mão": o Humano cola esta linha no terminal
# depois de ler o propostas/<nome>.diff. Criar o arquivo à mão continua valendo.
#
# LINHA VERMELHA: o EXECUTOR (modelo) NUNCA roda este script. Mesma regra de
# "o executor não se autoaprova" -- quem cola o comando é o Humano, e é o ato
# de colar que conta como aprovação. O script não enfraquece P-8: a ameaça que
# P-8 cobre é desatenção/automação agindo sem ninguém ver, não um executor que
# decida burlar de propósito (esse risco segue aceito e escrito no PROJETO).
set -euo pipefail

nome="${1:?uso: bash scripts/aprovar.sh <nome> [\"motivo em uma frase\"]  (sem .diff, sem APROVADO-)}"
motivo="${2:-}"

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
diff_pend="$raiz/propostas/$nome.diff"
diff_aplic="$raiz/propostas/aplicadas/$nome.diff"
alvo="$raiz/propostas/APROVADO-$nome"

if [ ! -f "$diff_pend" ] && [ ! -f "$diff_aplic" ]; then
  echo "ERRO: não achei propostas/$nome.diff (nem em aplicadas/)." >&2
  echo "      confira o <nome> -- é o basename do .diff, sem extensão." >&2
  exit 1
fi
if [ -e "$alvo" ]; then
  echo "ERRO: propostas/APROVADO-$nome já existe -- nada a fazer." >&2
  exit 1
fi

{
  echo "Aprovado pelo Humano em $(date '+%Y-%m-%d %H:%M %z')."
  echo "Via: comando colado no terminal (scripts/aprovar.sh) -- ato deliberado do Humano."
  [ -n "$motivo" ] && echo "Motivo: $motivo"
  echo "Cobre: propostas/$nome.diff"
} > "$alvo"

echo "criado: propostas/APROVADO-$nome"
echo "próximo: o executor aplica o .diff, move o par para propostas/aplicadas/ e comita."
