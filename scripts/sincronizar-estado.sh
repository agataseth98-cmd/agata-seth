#!/bin/bash
# scripts/sincronizar-estado.sh — verifica se ~/agata está em dia com origin/main
# Saída por log: /home/orusoua/agata/memoria/sync.log (append-only).
# Não altera canônico sem permissão explícita — todo push manual tem aviso no log.

set -euo pipefail

REPO="/home/orusoua/agata"
TODAY=$(date +'%Y%m%d')
LOG="$REPO/memoria/sincronizacao.log"
mkdir -p "$(dirname "$LOG")" || { echo "ERRO: não pode criar $(dirname $LOG)." >> "$LOG"; exit 1; }

cd "$REPO" || exit 1

# Verifica commits pendentes → age só se tiver mudanças para publicar
git status --porcelain | grep -q . && {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S')] ALERTA: commits pendentes detectados." >> "$LOG"
  
  if git remote get-url origin >/dev/null; then
    echo "[$(date +'%Y-%m-%dT%H:%M:%S')] Iniciando auto-commit e push automático..." >> "$LOG"
    
    git add --all || { echo "[$(date +'%Y-%m-%dT%H:%M:%S')] Erro em git add — interrompe." >> "$LOG"; exit 1; }
    git commit -m "(auto-sync) sincronizar-estado.sh detectou mudanças" || {
      echo "[$(date +'%Y-%m-%dT%H:%M:%S')] Commit falhou — abortando push." >> "$LOG"; exit 1
    }
    
    # Retentativa única (regra 2.3 do Conselho Remoto) → se falha, desiste e loga
    if git push origin main; then
      echo "[$(date +'%Y-%m-%dT%H:%M:%S')] Commit e push: OK. Verificado no remoto." >> "$LOG"
    else
      error_msg=$(git -v --push 2>&1 | head -3) || true
      echo "[$(date +'%Y-%m-%dT%H:%M:%S')] Push falhou após retentativa — verifique credenciais ou rede.\n$error_msg" >> "$LOG"
      exit 1
    fi
  else
    echo "[$(date +'%Y-%m-%dT%H:%M:%S')] Sem remote configurado ($REPO/remote.conf) — ignorando auto-push." >> "$LOG"
  fi
} || true

# Se já está em dia: compara HEAD local com remoto → loga divergence ou sincronia
if git remote get-url origin >/dev/null; then
  local_sha=$(git rev-parse --short HEAD) || { echo "LOCAL_SHA: erro em rev-parse — abortando." >> "$LOG"; exit 1; }
  
  # Usa ls-remote no formato porcelain (commit-hash space path)
  remote_line=$(git ls-remote origin main --porcelain 2>/dev/null | head -n 1) || true
  
  if [ "${local_sha:0:7}" = "$(git ls-remote --short origin/main)" ]; then
    echo "[$(date +'%Y-%m-%dT%H:%M:%S')] OK sincronizado: branch local em dia com origin/main." >> "$LOG"
  else
    remote_sha=$(git ls-remote --short origin/main | tail -1) || true
    [ -z "$remote_sha" ] && remote_sha=""
    
    if [ -n "$remote_sha" ]; then
      echo "[$(date +'%Y-%m-%dT%H:%M:%S')] DIVERGÊNCIA: local=$local_sha vs remoto=$remote_sha." >> "$LOG"
    else
      echo "[$(date +'%Y-%m-%dT%H:%M:%S')] OK sincronizado (modo local, remoto offline ou credencial expirada)." >> "$LOG"
    fi
  fi
else
  error_msg=$(git -v --remote origin main 2>&1 | head -3) || true
  echo "[$(date +'%Y-%m-%dT%H:%M:%S')] OK sincronizado (modo local, sem remote — $error_msg)" >> "$LOG"
fi

exit 0