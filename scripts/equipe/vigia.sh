#!/usr/bin/env bash
# vigia.sh <membro> [intervalo_s=20]  -- SEM modelo: só shell. Imprime UMA linha quando algo muda; silêncio = nada mudou.
# Sinais: mensagem nova de OUTRO membro da Equipe no canal, novo/removido APROVADO- em propostas/, novo HEAD de origin/main.
# Uso (quem tem Monitor/stdout em segundo plano): rode em background e reaja só às linhas. Pare com: touch ~/.cache/agata/sincronia/vigia.parar
set -u
eu="${1:?uso: vigia.sh <membro> [intervalo_s] [--uma [max_s]]}"; iv="${2:-20}"; uma=0; max=600; [ "${3:-}" = "--uma" ] && { uma=1; max="${4:-600}"; }; ini=$SECONDS
C="${EQUIPE_CANAL:-${DUPLA_CANAL:-$HOME/.cache/agata/sincronia/conversa.md}}"; R="${EQUIPE_REPO:-${DUPLA_REPO:-$HOME/agata}}"; P="${EQUIPE_PARAR:-${DUPLA_PARAR:-$HOME/.cache/agata/sincronia/vigia.parar}}"; rm -f "$P"
# Blocos de outros membros = todos os blocos menos os meus. `grep -c` imprime 0 e sai com 1 quando não acha: o `|| true` não pode somar um segundo "0".
outros() { local t m; t=$(grep -c '^## ' "$C" 2>/dev/null) || true; m=$(grep -c "^## $eu-" "$C" 2>/dev/null) || true; echo $(( ${t:-0} - ${m:-0} )); }
n0=$(outros)
a0=$(ls "$R"/propostas/APROVADO-* 2>/dev/null | sort | md5sum | cut -c1-8)
par0=""
h0=$(git -C "$R" ls-remote -q origin refs/heads/main 2>/dev/null | cut -c1-8)
while [ ! -e "$P" ]; do
  sleep "$iv"
  achou=0
  n=$(outros)
  a=$(ls "$R"/propostas/APROVADO-* 2>/dev/null | sort | md5sum | cut -c1-8)
  h=$(git -C "$R" ls-remote -q origin refs/heads/main 2>/dev/null | cut -c1-8)
  [ "$n" != "$n0" ] && { echo "$(TZ=America/Sao_Paulo date +%H:%M) MENSAGEM de outro membro: $((n-n0)) nova(s)"; n0=$n; achou=1; }
  [ "$a" != "$a0" ] && { echo "$(TZ=America/Sao_Paulo date +%H:%M) ASSINATURAS mudaram: $(ls "$R"/propostas/APROVADO-* 2>/dev/null | xargs -n1 basename 2>/dev/null | tr '\n' ' ')"; a0=$a; achou=1; }
  par=$(python3 -I "$(dirname "$0")/vigia_par.py" "$eu" "$C" 2>/dev/null); [ -n "$par" ] && [ "$par" != "$par0" ] && { echo "$(TZ=America/Sao_Paulo date +%H:%M) $par"; par0="$par"; achou=1; }
  [ -n "$h" ] && [ "$h" != "$h0" ] && { echo "$(TZ=America/Sao_Paulo date +%H:%M) MAIN andou: $h"; h0=$h; achou=1; }
  [ "$uma" = 1 ] && [ "$achou" = 1 ] && exit 0
  [ "$uma" = 1 ] && [ $((SECONDS-ini)) -ge "$max" ] && { echo "$(TZ=America/Sao_Paulo date +%H:%M) SEM EVENTO em ${max}s"; exit 0; }
done
