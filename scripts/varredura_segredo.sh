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

# P-1 -- "Segredos só em ~/.hermes/.env, fora do repo" (PROJETO, Segurança).
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

  local diff
  diff="$(git diff --cached -U0)"

  local p linhas
  for p in "${PADROES_SEGREDO[@]}"; do
    linhas="$(echo "$diff" | grep -nE '^\+' | grep -vE '^\+\+\+' | grep -E -- "$p")"
    if [ -n "$linhas" ]; then
      achou=1
      echo "SUSPEITO (padrão: $p):"
      echo "$linhas" | sed 's/^/  /'
    fi
  done

  return "$achou"
}

# P-2 -- "O executor pausa e pede sudo ao Humano" (PROJETO, Sudo e
# interação humana). Falha quando existe regra sudoers apontando pra
# caminho inexistente OU gravável por não-root. Checagem só: nunca
# escreve em /etc/sudoers.d/. Roda `sudo -n -l` (não-interativo); se
# pedir senha, pula com aviso, não bloqueia o commit por falta de acesso
# -- bloquear todo commit por não poder checar seria pior que o risco
# que a checagem previne.
checar_sudoers() {
  local saida
  saida="$(sudo -n -l 2>/dev/null)" || {
    echo "checar_sudoers: sudo -n -l sem acesso não-interativo agora -- checagem pulada, não é falha." >&2
    PERIMETRO_ESTADO="SKIP"
    return 0
  }
  # Achado real ao testar (15/08/2026): uma primeira versão varria a saída
  # inteira e o "secure_path=/usr/local/sbin:/usr/local/bin:/usr/bin" (uma
  # linha "Defaults", PATH de busca, não regra de comando) virava falso
  # positivo de "caminho inexistente" porque o regex ganancioso engolia os
  # `:` escapados como se fosse um caminho só. Corrigido: só olha linhas
  # depois do cabeçalho "pode executar", que é onde ficam as regras reais.
  local bloco
  bloco="$(echo "$saida" | sed -n '/pode executar os seguintes comandos/,$p')"
  local ruim=0
  local caminho
  while IFS= read -r caminho; do
    [ -z "$caminho" ] && continue
    if [ ! -e "$caminho" ]; then
      echo "SUSPEITO (sudoers): regra aponta pra caminho INEXISTENTE: $caminho"
      ruim=1
    elif [ -w "$caminho" ] && [ "$(stat -c '%U' "$caminho" 2>/dev/null)" != "root" ]; then
      echo "SUSPEITO (sudoers): regra aponta pra caminho gravável por não-root: $caminho"
      ruim=1
    fi
  done < <(echo "$bloco" | grep -oE '/[^[:space:]]+')
  return "$ruim"
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
