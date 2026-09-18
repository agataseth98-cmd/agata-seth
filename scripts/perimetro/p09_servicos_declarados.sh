#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

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
  return 0
}

