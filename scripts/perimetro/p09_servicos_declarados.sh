#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica. Acrescimo posterior: _p9_ollama_na_gpu
# (03/10/2026), abaixo.

p9_servicos_declarados() {
  local avisos=0 u estado habilitada rodando
  for u in "${P9_UNIDADES_SISTEMA[@]}"; do
    estado="$(systemctl is-active "$u" 2>/dev/null)"
    if [ "$estado" = "failed" ] || [ "$estado" = "inactive" ]; then
      echo "AVISO (P-9): unidade de sistema '$u', declarada em PROJETO.md, está '$estado' -- o que fazer: 'systemctl status $u' e reinicie se preciso."
      avisos=1
    fi
    habilitada="$(systemctl is-enabled "$u" 2>/dev/null)"
    if [ "$habilitada" = "disabled" ] || [ "$habilitada" = "masked" ]; then
      echo "AVISO (P-9): unidade de sistema '$u' está '$habilitada' -- o que fazer: não volta sozinha num boot, decida se isso é intencional."
      avisos=1
    fi
  done
  for u in "${P9_UNIDADES_USUARIO[@]}"; do
    estado="$(systemctl --user is-active "$u" 2>/dev/null)"
    if [ "$estado" = "failed" ]; then
      echo "AVISO (P-9): unidade de usuário '$u', declarada em PROJETO.md, está 'failed' -- o que fazer: 'systemctl --user status $u' antes de confiar que ela roda."
      avisos=1
    fi
    habilitada="$(systemctl --user is-enabled "$u" 2>/dev/null)"
    if [ "$habilitada" = "disabled" ] || [ "$habilitada" = "masked" ]; then
      echo "AVISO (P-9): unidade de usuário '$u' está '$habilitada' -- o que fazer: não volta sozinha na próxima sessão, decida se isso é intencional."
      avisos=1
    fi
  done
  if command -v docker >/dev/null 2>&1; then
    for u in "${P9_CONTAINERS_DOCKER[@]}"; do
      rodando="$(docker ps --filter "name=^${u}\$" --format '{{.Names}}' 2>/dev/null)"
      if [ -z "$rodando" ]; then
        echo "AVISO (P-9): container '$u', declarado em PROJETO.md, não aparece rodando em 'docker ps' -- o que fazer: 'docker ps -a | grep $u' pra ver se caiu ou nunca subiu."
        avisos=1
      fi
    done
  fi
  _p9_ollama_na_gpu
  return 0
}

# Ollama com parte do modelo na CPU (03/10/2026, MEMÓRIAS (648)/(649)): um
# llama-cpp que voltou sozinho depois de OOM tomou a VRAM, o Ollama subiu o
# modelo dividido e a Seth caiu de ~43 para 6,3 tok/s -- com TODAS as unidades
# "active". Nenhuma checagem de estado de unidade vê isso; o /api/ps vê:
# `size_vram < size` = parte do modelo fora da GPU. Mesma doutrina do resto do
# P-9: AVISA, nunca falha. Ollama fora do ar ou sem modelo carregado -> silêncio
# (o primeiro já é coberto por ollama.service acima; o segundo é o repouso
# normal). Só localhost, timeout curto: o perímetro roda a cada commit.
# P9_OLLAMA_PS_URL existe só para o teste isolado apontar um servidor falso.
_p9_ollama_na_gpu() {
  local url="${P9_OLLAMA_PS_URL:-http://127.0.0.1:11434/api/ps}" saida
  saida="$(python3 - "$url" <<'PYEOF' 2>/dev/null
import json, sys, urllib.request
sem_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # localhost nunca via proxy
try:
    with sem_proxy.open(sys.argv[1], timeout=2) as r:
        modelos = json.load(r).get("models") or []
except Exception:
    sys.exit(0)
for m in modelos:
    if not isinstance(m, dict):
        continue
    try:
        total, vram = int(m.get("size") or 0), int(m.get("size_vram") or 0)
    except (TypeError, ValueError):
        continue
    if total > 0 and vram < total:
        print(f"{m.get('name') or m.get('model') or '?'}\t{100 * vram // total}")
PYEOF
)"
  [ -z "$saida" ] && return 0
  local nome pct quem=""
  if command -v nvidia-smi >/dev/null 2>&1; then
    quem="$(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>/dev/null | tr '\n' ';' | sed 's/;$//')"
  fi
  while IFS=$'\t' read -r nome pct; do
    echo "AVISO (P-9): Ollama com '$nome' só ${pct}% na GPU (o resto na CPU, várias vezes mais lento) -- o que fazer: 'nvidia-smi' para ver quem tomou a VRAM${quem:+ (agora: $quem)}; pare o intruso (ex.: 'systemctl --user stop llamacpp@<modelo>') e recarregue o modelo do Ollama."
  done <<< "$saida"
  return 0
}

