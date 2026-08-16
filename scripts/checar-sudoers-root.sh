#!/usr/bin/env bash
# Agata -- verificação root-side de /etc/sudoers.d (MEMÓRIAS (194)).
# SÓ LÊ E REPORTA. Nunca edita sudoers, em nenhuma circunstância, sob
# hipótese alguma.
#
# Disparado como root por /etc/pacman.d/hooks/agata-sudoers.hook
# (Operation Install/Upgrade/Remove sobre etc/sudoers.d/*), ou rodado
# manualmente com sudo depois de qualquer `visudo` -- que não dispara
# pacman, cobertura que o hook não tem (ver PROJETO.md, "Sudo e
# interação humana").
#
# AUTOCONTIDO DE PROPÓSITO: não faz `source` de nada em ~/agata. Um
# script que roda como root não pode depender de arquivo gravável por
# orusoua -- seria recriar a classe fechada em MEMÓRIAS (192). A lógica
# de inspeção abaixo é cópia pequena (~15 linhas) da mesma de
# `checar_sudoers` em scripts/varredura_segredo.sh -- duplicação
# deliberada pela fronteira de segurança, não descuido.
#
# Instalado pelo Humano, com sudo, em:
#   /usr/local/lib/agata/checar-sudoers-root.sh  (root:root, 0755)
# Este arquivo em scripts/ é só o material de origem, versionado pra
# revisão e diff -- não é o que roda como root.
set -uo pipefail

STATUS_FILE="${AGATA_P2_STATUS_FILE:-/var/lib/agata/p2-status.json}"

# $1, se passado, substitui a saída real do `sudo -l` -- só pra teste
# isolado (mesmo padrão de p4_bind em scripts/perimetro.sh).
saida="${1:-}"
if [ -z "$saida" ]; then
  saida="$(sudo -n -l -U orusoua 2>/dev/null || sudo -l -U orusoua 2>/dev/null || true)"
fi

bloco="$(printf '%s\n' "$saida" | sed -n '/pode executar os seguintes comandos/,$p')"
ruim=0
achado=""
inspecionados=""
while IFS= read -r caminho; do
  [ -z "$caminho" ] && continue
  inspecionados="${inspecionados}${caminho}"$'\n'
  if [ ! -e "$caminho" ]; then
    achado="regra aponta pra caminho INEXISTENTE: $caminho"
    ruim=1
  elif [ -w "$caminho" ] && [ "$(stat -c '%U' "$caminho" 2>/dev/null)" != "root" ]; then
    achado="regra aponta pra caminho gravável por não-root: $caminho"
    ruim=1
  fi
done < <(printf '%s\n' "$bloco" | grep -oE '/[^[:space:]]+')

veredito="OK"
[ "$ruim" -eq 1 ] && veredito="FALHOU"
timestamp="$(date -Iseconds)"

esc() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }
inspecionado_json="$(printf '%s' "$inspecionados" | sed '/^$/d' | while IFS= read -r p; do printf '"%s",' "$(esc "$p")"; done | sed 's/,$//')"

tmp="$(mktemp)"
{
  printf '{\n'
  printf '  "timestamp": "%s",\n' "$(esc "$timestamp")"
  printf '  "veredito": "%s",\n' "$(esc "$veredito")"
  printf '  "detalhe": "%s",\n' "$(esc "$achado")"
  printf '  "inspecionado": [%s]\n' "$inspecionado_json"
  printf '}\n'
} > "$tmp"

mkdir -p "$(dirname "$STATUS_FILE")" 2>/dev/null || true
chmod 0644 "$tmp"
mv "$tmp" "$STATUS_FILE"
[ "$(id -u)" -eq 0 ] && chown root:root "$STATUS_FILE" 2>/dev/null

echo "checar-sudoers-root: veredito $veredito -- status em $STATUS_FILE" >&2
exit "$ruim"
