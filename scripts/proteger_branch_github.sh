#!/usr/bin/env bash
# Fase 3 (F3.2): proteção de branch no GitHub pra um repositório recém-nascido
# (genese.sh não cria o repo no GitHub nem mexe em configuração remota --
# fora do escopo dele de propósito, "não usa sudo, rede além do git nem rm").
# Script SEPARADO, chamado à parte, não embutido no fluxo de gênese --
# decisão do Humano, 27/09/2026: evita acoplar o script central a um token
# de admin do GitHub disponível no momento do nascimento.
#
# Reproduz exatamente a proteção real de agata-seth/main (lida via
# `gh api repos/.../branches/main/protection`, 27/09/2026):
#   - PR obrigatório antes de qualquer merge (sem exigir aprovação de
#     revisor -- 0 aprovações necessárias, mesmo padrão usado nesta sessão
#     inteira: humano sozinho aprova a própria PR);
#   - o check `suite-adversarial` (CI) precisa passar, na branch atualizada
#     (strict=true);
#   - até admin não pode passar por cima (enforce_admins=true);
#   - sem force-push, sem deleção da branch.
#
# Padrão: simulação. Só age com --aplicar. Idempotente: reaplicar a mesma
# configuração não muda nada (a API do GitHub é PUT -- substitui, não
# acumula).
set -euo pipefail

uso() {
  cat >&2 <<'EOF'
uso: proteger_branch_github.sh --repo DONO/NOME [--branch main] [--check suite-adversarial] [--aplicar]
  --repo     "dono/nome" do repositório no GitHub (obrigatório)
  --branch   branch a proteger (padrão: main)
  --check    nome do status check obrigatório (padrão: suite-adversarial --
             o workflow da Fase 8 desta Máquina; ajuste se o clone usar outro nome)
  --aplicar  sem isto, só mostra o plano
EOF
  exit 2
}

REPO="" BRANCH="main" CHECK="suite-adversarial" APLICAR=0
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="${2:-}"; shift 2 ;;
    --branch) BRANCH="${2:-}"; shift 2 ;;
    --check) CHECK="${2:-}"; shift 2 ;;
    --aplicar) APLICAR=1; shift ;;
    *) uso ;;
  esac
done
[ -n "$REPO" ] || uso

passo() { printf '%-8s %s\n' "$1" "$2"; }
falha() { passo "FALHOU" "$1"; exit 1; }

command -v gh >/dev/null 2>&1 || falha "gh (GitHub CLI) não encontrado"
gh auth status >/dev/null 2>&1 || falha "gh não autenticado -- rode 'gh auth login' primeiro"
gh repo view "$REPO" >/dev/null 2>&1 || falha "repositório não encontrado ou sem acesso: $REPO"
gh api "repos/$REPO/branches/$BRANCH" >/dev/null 2>&1 || falha "branch não encontrada: $REPO#$BRANCH (precisa existir pelo menos 1 commit)"

BODY=$(cat <<JSON
{
  "required_status_checks": {"strict": true, "contexts": ["$CHECK"]},
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
)

passo "PLANO" "proteger $REPO#$BRANCH: PR obrigatório (0 aprovações), check '$CHECK' obrigatório, sem force-push, sem deleção, até admin sem passar por cima"
if [ "$APLICAR" -ne 1 ]; then
  passo "PULADO" "simulação (use --aplicar para agir)"
  exit 0
fi

if echo "$BODY" | gh api -X PUT "repos/$REPO/branches/$BRANCH/protection" --input - >/dev/null; then
  passo "FEITO" "proteção aplicada em $REPO#$BRANCH"
else
  falha "a API do GitHub recusou -- confira permissão de admin no repo"
fi

# --- Conferência pós-aplicação: relê a proteção e confirma os 4 pontos ---
ATUAL="$(gh api "repos/$REPO/branches/$BRANCH/protection" 2>/dev/null)"
# set -e mata o script se o python saisse != 0 ANTES do `if` conseguir checar
# -- achado revisando antes de testar (não em produção). `if comando; then`
# suspende o -e só pra esse comando, exit code some no $? normal.
if python3 - "$ATUAL" "$CHECK" <<'PY'
import json, sys
d = json.loads(sys.argv[1])
check = sys.argv[2]
ok = (
    d.get("required_status_checks", {}).get("strict") is True
    and check in d.get("required_status_checks", {}).get("contexts", [])
    and d.get("enforce_admins", {}).get("enabled") is True
    and d.get("allow_force_pushes", {}).get("enabled") is False
    and d.get("allow_deletions", {}).get("enabled") is False
)
sys.exit(0 if ok else 1)
PY
then
  passo "OK" "confirmado relendo a API -- os 4 pontos batem"
else
  falha "aplicado, mas a releitura não bate com o esperado -- confira à mão"
fi
