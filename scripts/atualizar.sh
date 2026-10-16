#!/usr/bin/env bash
# Reconcilia os canônicos locais (REGRAS/PROJETO/DIÁRIO) com o GitHub, que é a
# fonte da verdade. Nunca sobrescreve história local não commitada: se houver
# mudança local pendente ou conflito de merge, para e reporta em vez de forçar.
set -euo pipefail

REPO_DIR="$HOME/agata"
ALVO="${1:-TUDO}"

case "$ALVO" in
  MEMORIA|PROJETO|REGRAS|TUDO) ;;
  *)
    echo "Uso: atualizar.sh [MEMORIA|PROJETO|REGRAS|TUDO]" >&2
    exit 1
    ;;
esac

cd "$REPO_DIR"

# I5 (candidato 16/10/2026, lição do bootc: depois de um rollback o sistema atualiza de novo sozinho se
# ninguém pausar). Uma verificação de saúde que falhou deixa este marcador e a próxima atualização RECUSA
# até o Humano olhar e remover o arquivo (ou exportar AGATA_ATUALIZAR_RETOMAR=1 por uma vez).
PAUSA="${AGATA_PAUSA_ATUALIZACAO:-$HOME/.cache/agata/atualizacao-pausada}"
if [ -e "$PAUSA" ] && [ "${AGATA_ATUALIZAR_RETOMAR:-0}" != "1" ]; then
  echo "ERRO: atualização PAUSADA por uma verificação de saúde que falhou antes:" >&2
  sed 's/^/  /' "$PAUSA" >&2
  echo "Olhe o que falhou, e só então: rm \"$PAUSA\"  (ou rode uma vez com AGATA_ATUALIZAR_RETOMAR=1)." >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "ERRO: há mudanças locais não commitadas em $REPO_DIR." >&2
  echo "Faça commit ou stash antes de atualizar — não vou sobrescrever história local." >&2
  git status --short
  exit 1
fi

ANTES=$(git rev-parse HEAD)

if ! git pull --no-edit origin main; then
  echo "ERRO: git pull falhou (provável conflito de merge)." >&2
  echo "PARANDO sem forçar nada — resolva manualmente e rode de novo." >&2
  git status --short
  exit 1
fi

DEPOIS=$(git rev-parse HEAD)

echo "atualizar.sh: alvo=$ALVO"
if [ "$ANTES" = "$DEPOIS" ]; then
  echo "  já estava em dia (HEAD=$DEPOIS)."
else
  echo "  atualizado: $ANTES -> $DEPOIS"
  git diff --stat "$ANTES" "$DEPOIS"
fi

bash .githooks/gerar-hidratacao.sh

case "$ALVO" in
  MEMORIA) echo "  MEMÓRIAS.md reconciliado; topo reinjetado em .hidrata.md." ;;
  PROJETO) echo "  PROJETO.md reconciliado; reinjetado em .hidrata.md." ;;
  REGRAS)  echo "  REGRAS.md (+ PROTOCOLOS.md, FALHAS.md) reconciliados; reinjetados em .hidrata.md." ;;
  TUDO)    echo "  REGRAS.md + PROTOCOLOS.md + FALHAS.md + PROJETO.md + MEMÓRIAS.md reconciliados; reinjetados em .hidrata.md." ;;
esac

# I6 (candidato 16/10/2026): verificação de saúde depois de atualizar, no modelo "obrigatória e opcional" do
# Greenboot. Obrigatória: o perímetro (P-1 a P-23). Opcional, só aviso: deriva dos componentes externos.
# NUNCA reverte sozinho (história não se apaga, Regra 4): em falha, pausa e diz como voltar (`git revert`).
if [ "$ANTES" != "$DEPOIS" ]; then
  echo "atualizar.sh: verificação de saúde (obrigatória: perímetro)"
  SAUDE_LOG="$(mktemp)"
  if bash scripts/perimetro.sh >"$SAUDE_LOG" 2>&1; then
    grep -E "RESULTADO GERAL" "$SAUDE_LOG" | tail -1 | sed 's/^/  /'
    rm -f "$PAUSA"
  else
    echo "ERRO: o perímetro FALHOU depois da atualização ($ANTES -> $DEPOIS)." >&2
    tail -n 25 "$SAUDE_LOG" | sed 's/^/  | /' >&2
    mkdir -p "$(dirname "$PAUSA")"
    {
      echo "pausada em $(date '+%Y-%m-%d %H:%M %z'): perímetro falhou depois de $ANTES -> $DEPOIS"
      echo "voltar sem apagar história: git revert <commit>   (nunca git reset --hard)"
    } > "$PAUSA"
    echo "PAUSEI as próximas atualizações ($PAUSA). Nada foi revertido. Para voltar: git revert; a decisão é do Humano." >&2
    rm -f "$SAUDE_LOG"
    exit 1
  fi
  rm -f "$SAUDE_LOG"
  if [ -f scripts/inventario_componentes.py ]; then
    echo "atualizar.sh: componentes externos (opcional, só aviso)"
    python3 scripts/inventario_componentes.py --verificar 2>&1 | sed 's/^/  /' || true
  fi
fi

echo "atualizar.sh: concluído."
