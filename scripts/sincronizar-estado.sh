#!/bin/bash
# scripts/sincronizar-estado.sh — verifica se ~/agata está em dia com origin/main
# Saída por log: /home/orusoua/agata/memoria/sincronizacao.log (append-only).
#
# NUNCA publica sozinho. Este script só LÊ o estado e AVISA no log —
# git add/commit/push em canônico é decisão do Humano (REGRAS, Regra 3;
# Cadeia de auditoria em camadas). Versão anterior fazia `git add --all`
# + commit + push automáticos apesar de dizer o contrário no próprio
# cabeçalho — commit 564a50d entrou em origin/main sem entrada em
# MEMÓRIAS nem revisão. Ver o incidente em MEMÓRIAS antes de reintroduzir
# qualquer publicação automática aqui.

set -euo pipefail

REPO="/home/orusoua/agata"
LOG="$REPO/memoria/sincronizacao.log"
mkdir -p "$(dirname "$LOG")" || { echo "ERRO: não pode criar $(dirname "$LOG")." >> "$LOG"; exit 1; }

cd "$REPO" || exit 1

if git status --porcelain | grep -q .; then
  echo "[$(date +'%Y-%m-%dT%H:%M:%S')] ALERTA: mudanças pendentes no working tree (git status --porcelain não vazio). Este script não comita nem publica — revise e decida manualmente." >> "$LOG"
fi

if git remote get-url origin >/dev/null 2>&1; then
  local_sha=$(git rev-parse --short HEAD) || { echo "[$(date +'%Y-%m-%dT%H:%M:%S')] ERRO: git rev-parse HEAD falhou." >> "$LOG"; exit 1; }

  # Forma correta: <repositório> e <ref> são argumentos separados.
  # "origin/main" junto é um nome de ref local (remote-tracking branch),
  # não um repositório válido para ls-remote -- versão anterior usava essa
  # forma inválida, silenciosamente sem match, e sempre caía no ramo
  # "sincronizado (modo local)" mesmo com remoto acessível.
  # `--short` também não existe em `git ls-remote` (confirmado rodando de
  # verdade: `git ls-remote --short` dá "error: unknown option `short'",
  # git 2.55.0) -- não é flag válida para este subcomando em nenhuma
  # versão testada. O SHA curto vem do `cut`, não de uma flag inexistente.
  remote_sha=$(git ls-remote origin main 2>/dev/null | awk '{print $1}' | cut -c1-7) || true

  if [ -z "$remote_sha" ]; then
    echo "[$(date +'%Y-%m-%dT%H:%M:%S')] OK sincronizado (modo local — remoto inacessível: rede ou credencial)." >> "$LOG"
  elif [ "$local_sha" = "$remote_sha" ]; then
    echo "[$(date +'%Y-%m-%dT%H:%M:%S')] OK sincronizado: branch local em dia com origin/main ($local_sha)." >> "$LOG"
  else
    echo "[$(date +'%Y-%m-%dT%H:%M:%S')] DIVERGÊNCIA: local=$local_sha vs remoto=$remote_sha." >> "$LOG"
  fi
else
  echo "[$(date +'%Y-%m-%dT%H:%M:%S')] OK sincronizado (modo local, sem remote configurado)." >> "$LOG"
fi

exit 0
