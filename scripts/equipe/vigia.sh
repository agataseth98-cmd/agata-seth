#!/usr/bin/env bash
# vigia.sh <membro> [intervalo_s=20] [--uma [max_s]]  -- SEM modelo: só shell.
# Anota, em UMA linha, cada evento do sistema Agata. Silêncio = nada mudou.
# Eventos vigiados:
#   1. mensagem nova de outro membro no canal da Equipe;
#   2. pendência entre membros (vigia_par.py);
#   3. assinatura nova ou removida em propostas/APROVADO-*;
#   4. novo commit no origin/main (checado a cada 60 s);
#   5. serviço da Seth/Agata que subiu, caiu ou mudou de estado (checado a cada intervalo);
#   6. quantos provedores do Conselho estão detectados no navegador (a cada 60 s, pelo painel);
#   7. LibreChat saudável ou não (a cada 60 s).
# Cada evento sai na tela (quem tem Monitor lê) e vai para o diário ~/.cache/agata/sincronia/eventos.log.
# A Seth lê o diário pelo painel: GET /api/eventos (só leitura).
# Parar: systemctl --user stop agata-vigia@<membro> (o seth-parar faz isso).
set -u
eu="${1:?uso: vigia.sh <membro> [intervalo_s] [--uma [max_s]]}"; iv="${2:-20}"; uma=0; max=600; [ "${3:-}" = "--uma" ] && { uma=1; max="${4:-600}"; }; ini=$SECONDS
C="${EQUIPE_CANAL:-${DUPLA_CANAL:-$HOME/.cache/agata/sincronia/conversa.md}}"; R="${EQUIPE_REPO:-${DUPLA_REPO:-$HOME/agata}}"; P="${EQUIPE_PARAR:-${DUPLA_PARAR:-$HOME/.cache/agata/sincronia/vigia.parar}}"
D="${VIGIA_DIARIO:-$HOME/.cache/agata/sincronia/eventos.log}"; rm -f "$P"; mkdir -p "$(dirname "$D")" 2>/dev/null || true
# Uma linha por evento: vai para a tela e para o diário (o diário é o que a Seth lê).
ev() { local l; l="$(TZ=America/Sao_Paulo date +%H:%M) $*"; echo "$l"; echo "$l" >> "$D" 2>/dev/null || true; }
# Serviços da espinha da Seth (os que sobem com `seth` e caem com `seth-parar`).
ESPINHA="seth-gateway seth-escriba seth-verificador painel-operacional omniroute omniroute-sanitizer openvino-whisper openvino-embeddings obsidian-ro-proxy obsidian-app piper-tts discord-mcp navegador-mcp"
declare -A st
for s in $ESPINHA; do st[$s]=$(systemctl --user is-active "$s.service" 2>/dev/null); done
# Blocos de outros membros = todos os blocos menos os meus. `grep -c` imprime 0 e sai com 1 quando não acha: o `|| true` não pode somar um segundo "0".
outros() { local t m; t=$(grep -c '^## ' "$C" 2>/dev/null) || true; m=$(grep -c "^## $eu-" "$C" 2>/dev/null) || true; echo $(( ${t:-0} - ${m:-0} )); }
# Provedores do Conselho detectados (o painel conta as abas com a extensão). "?" = painel fora do ar.
prov() { curl -s -m 3 http://127.0.0.1:20146/api/relay-council/state 2>/dev/null | python3 -c 'import sys,json
try: print(len(json.load(sys.stdin).get("providers", [])))
except Exception: print("?")' 2>/dev/null || echo "?"; }
lc() { docker inspect -f '{{.State.Health.Status}}' librechat 2>/dev/null || echo "fora"; }
n0=$(outros)
a0=$(ls "$R"/propostas/APROVADO-* 2>/dev/null | sort | md5sum | cut -c1-8)
par0=""
h0=$(git -C "$R" ls-remote -q origin refs/heads/main 2>/dev/null | cut -c1-8)
pv0=$(prov); lc0=$(lc)
t=0
while [ ! -e "$P" ]; do
  sleep "$iv"; t=$((t+1))
  achou=0
  n=$(outros)
  a=$(ls "$R"/propostas/APROVADO-* 2>/dev/null | sort | md5sum | cut -c1-8)
  [ "$n" != "$n0" ] && { ev "MENSAGEM de outro membro: $((n-n0)) nova(s)"; n0=$n; achou=1; }
  [ "$a" != "$a0" ] && { ev "ASSINATURAS mudaram: $(ls "$R"/propostas/APROVADO-* 2>/dev/null | xargs -n1 basename 2>/dev/null | tr '\n' ' ')"; a0=$a; achou=1; }
  par=$(python3 -I "$(dirname "$0")/vigia_par.py" "$eu" "$C" 2>/dev/null); [ -n "$par" ] && [ "$par" != "$par0" ] && { ev "$par"; par0="$par"; achou=1; }
  for s in $ESPINHA; do
    x=$(systemctl --user is-active "$s.service" 2>/dev/null)
    [ "$x" != "${st[$s]}" ] && { ev "SERVIÇO $s: ${st[$s]:-?} -> $x"; st[$s]=$x; achou=1; }
  done
  if [ $((t % 3)) -eq 0 ]; then
    h=$(git -C "$R" ls-remote -q origin refs/heads/main 2>/dev/null | cut -c1-8)
    [ -n "$h" ] && [ "$h" != "$h0" ] && { ev "MAIN andou: $h"; h0=$h; achou=1; }
    pv=$(prov)
    [ "$pv" != "$pv0" ] && { ev "CONSELHO provedores detectados: $pv0 -> $pv"; pv0=$pv; achou=1; }
    lx=$(lc)
    [ "$lx" != "$lc0" ] && { ev "LIBRECHAT: $lc0 -> $lx"; lc0=$lx; achou=1; }
  fi
  [ "$uma" = 1 ] && [ "$achou" = 1 ] && exit 0
  [ "$uma" = 1 ] && [ $((SECONDS-ini)) -ge "$max" ] && { ev "SEM EVENTO em ${max}s"; exit 0; }
done
