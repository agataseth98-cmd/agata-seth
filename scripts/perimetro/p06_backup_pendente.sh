#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

p6_backup_pendente() {
  local glob="${1:-$HOME/.agata-backup-staging/PENDENTE-HD-DESCONECTADO*}"
  local marcador
  for marcador in $glob; do
    [ -e "$marcador" ] || continue
    local commit_hash timestamp_str
    commit_hash="$(grep -oE '[0-9a-f]{7,40}' "$marcador" | head -1)"
    timestamp_str="$(grep -oE '[0-9]{8}-[0-9]{6}' "$marcador" | head -1)"
    [ -z "$commit_hash" ] && continue
    local agora_epoch marca_epoch horas_passadas commits_desde
    marca_epoch="$(date -d "${timestamp_str:0:4}-${timestamp_str:4:2}-${timestamp_str:6:2} ${timestamp_str:9:2}:${timestamp_str:11:2}:${timestamp_str:13:2}" +%s 2>/dev/null)"
    agora_epoch="$(date +%s)"
    if [ -n "$marca_epoch" ]; then
      horas_passadas=$(( (agora_epoch - marca_epoch) / 3600 ))
    else
      horas_passadas=0
    fi
    commits_desde="$(git rev-list --count "${commit_hash}..HEAD" 2>/dev/null || echo 0)"
    if [ "$commits_desde" -gt "$P6_MAX_COMMITS" ] || [ "$horas_passadas" -gt "$P6_MAX_HORAS" ]; then
      echo "AVISO (P-6): $marcador pendente há $commits_desde commits / $horas_passadas h (limiar: $P6_MAX_COMMITS commits ou ${P6_MAX_HORAS}h) -- conecte o HD."
    fi
  done
  return 0
}

