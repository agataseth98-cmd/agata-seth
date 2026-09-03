#!/usr/bin/env bash
# S-1 (auditoria de segurança, 15/08/2026), testado contra os últimos 20
# commits reais em 3.1 -- zero falso positivo. Reorganizado em 15/08/2026
# (Passo 5, perímetro de controles) em funções reusáveis -- este arquivo
# continua funcionando sozinho (`bash scripts/varredura_segredo.sh`), e
# `scripts/perimetro.sh` importa as mesmas funções como P-1/P-2, sem
# duplicar a lógica já testada.
set -uo pipefail

# Estado extra que uma checagem pode declarar além do exit code (0/1), pra
# quem chama (perimetro.sh) não confundir "rodou e não achou nada" com
# "não rodou de verdade". Setado por checar_sudoers quando pula por falta
# de sudo não-interativo -- achado em MEMÓRIAS (192)/(193): sem isso, um
# SKIP estrutural (nunca vai deixar de acontecer, é o controle do PROJETO
# funcionando) entrava no canon como "OK" indistinguível de verificação
# real. Vazio = sem ressalva (OK de verdade se o exit code for 0).
PERIMETRO_ESTADO=""

PADROES_SEGREDO=(
  'AKIA[0-9A-Z]{16}'                          # AWS access key id
  'AIza[0-9A-Za-z_-]{35}'                     # Google API key
  'gh[pousr]_[0-9A-Za-z]{36,}'                # GitHub token (ghp_/gho_/ghu_/ghs_/ghr_)
  'sk-[A-Za-z0-9]{20,}'                       # OpenAI-style secret key
  'xox[baprs]-[0-9A-Za-z-]{10,}'              # Slack token
  '-----BEGIN[A-Z ]*PRIVATE KEY-----'         # PEM private key
  '[A-Za-z0-9_]*(KEY|TOKEN|SECRET|PASSWORD)[A-Za-z0-9_]*[[:space:]]*[:=][[:space:]]*["'"'"']?[A-Za-z0-9/+_-]{16,}["'"'"']?'
)

# P-1 -- "Segredos só em ~/.config/agata/.env, fora do repo" (PROJETO, Segurança).
# Olha só o que está staged (git diff --cached), que é o que um pre-commit
# real veria. Padrões de chave conhecidos + heurística genérica. Heurística
# tem falso positivo/negativo -- rede de segurança adicional, não substitui
# revisão humana do diff.
checar_segredo() {
  local achou=0

  # Arquivo .env staged é o próprio incidente, não um caso pra escanear por
  # padrão -- se .gitignore falhou ou foi forçado (`git add -f`), avisa
  # sempre, sujo ou limpo por dentro. Achado real ao testar (15/08/2026):
  # uma versão anterior deste script EXCLUÍA .env do diff escaneado -- o
  # oposto do que devia, isso escondia exatamente o caso mais grave.
  local env_staged
  env_staged="$(git diff --cached --name-only -- '.env' '.env.*' '*/.env' '*/.env.*')"
  if [ -n "$env_staged" ]; then
    achou=1
    echo "SUSPEITO: arquivo .env staged (deveria estar em .gitignore sempre):"
    echo "$env_staged" | sed 's/^/  /'
  fi

  # Por arquivo, não pelo diff inteiro concatenado -- MEMÓRIAS (202): com
  # mais de um arquivo staged, o alarme antigo não dizia qual deles tinha
  # o achado (achado na prova de legibilidade, MEMÓRIAS (196)/(197)).
  local arquivo diff_arquivo p linhas
  while IFS= read -r arquivo; do
    [ -z "$arquivo" ] && continue
    diff_arquivo="$(git diff --cached -U0 -- "$arquivo")"
    for p in "${PADROES_SEGREDO[@]}"; do
      linhas="$(echo "$diff_arquivo" | grep -nE '^\+' | grep -vE '^\+\+\+' | grep -E -- "$p")"
      if [ -n "$linhas" ]; then
        achou=1
        echo "SUSPEITO (padrão: $p) em $arquivo:"
        echo "$linhas" | sed 's/^/  /'
      fi
    done
  done < <(git diff --cached --name-only)

  return "$achou"
}

# P-2 -- "O executor pausa e pede sudo ao Humano" (PROJETO, Sudo e
# interação humana). MEMÓRIAS (194): deixou de chamar `sudo -n -l`
# diretamente -- isso era SKIP estrutural sempre, porque o executor nunca
# tem sudo não-interativo (é o controle funcionando, não uma falha).
# Passou a LER o status escrito por um mecanismo root separado
# (scripts/checar-sudoers-root.sh, disparado por
# /etc/pacman.d/hooks/agata-sudoers.hook ou manualmente após `visudo`).
# Três estados, não dois:
#   - status ausente (mecanismo root nunca rodou) -> SKIP, não FALHOU.
#     Bloquear todo commit até o Humano instalar o hook seria o mesmo
#     erro que motivou o desenho original de SKIP.
#   - status presente, veredito negativo -> FALHOU, sempre, com o
#     conteúdo literal do achado.
#   - status presente, veredito positivo -> OK, com a data da última
#     verificação. IDADE não é alarme (ordem do Humano, MEMÓRIAS (194)):
#     se nada tocou sudoers.d desde a última checagem, o resultado
#     continua válido -- não implementar alerta por idade aqui.
checar_sudoers() {
  local status_file="${AGATA_P2_STATUS_FILE:-/var/lib/agata/p2-status.json}"
  if [ ! -e "$status_file" ]; then
    echo "checar_sudoers: $status_file ausente -- mecanismo root (checar-sudoers-root.sh) nunca rodou, sem verificação real ainda." >&2
    PERIMETRO_ESTADO="SKIP"
    return 0
  fi
  local veredito timestamp detalhe
  veredito="$(python3 -c "import json,sys
try:
    print(json.load(open(sys.argv[1])).get('veredito',''))
except Exception:
    pass" "$status_file" 2>/dev/null)"
  timestamp="$(python3 -c "import json,sys
try:
    print(json.load(open(sys.argv[1])).get('timestamp',''))
except Exception:
    pass" "$status_file" 2>/dev/null)"
  detalhe="$(python3 -c "import json,sys
try:
    print(json.load(open(sys.argv[1])).get('detalhe',''))
except Exception:
    pass" "$status_file" 2>/dev/null)"
  if [ -z "$veredito" ]; then
    echo "checar_sudoers: $status_file existe mas não deu pra ler o campo 'veredito' -- tratando como SKIP, não FALHOU (pode estar sendo escrito agora)." >&2
    PERIMETRO_ESTADO="SKIP"
    return 0
  fi
  echo "checar_sudoers: última verificação root em $timestamp -- veredito $veredito"
  if [ "$veredito" != "OK" ]; then
    echo "SUSPEITO (sudoers, verificação root): $detalhe"
    return 1
  fi
  return 0
}

# Só executa como script principal quando chamado direto -- sourced (por
# perimetro.sh) só expõe as funções, não roda nem sai sozinho.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  achou=0
  checar_segredo || achou=1
  checar_sudoers || achou=1
  if [ "$achou" -eq 1 ]; then
    echo
    echo "varredura_segredo.sh: possível segredo no staged diff ou regra de sudoers suspeita. Revise antes de comitar." >&2
    exit 1
  fi
  exit 0
fi
