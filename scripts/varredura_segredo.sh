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
  # Acrescentados 09/09/2026. Motivo medido, não teórico: os padrões acima
  # não pegavam NENHUMA das chaves que ESTE sistema realmente usa em forma
  # nua. `sk-[A-Za-z0-9]{20,}` quebra no primeiro hífen -- `sk-ant-` tem só
  # 3 alfanuméricos depois de `sk-`, `sk-or-v1-` tem 2. Medido com controles
  # válidos (openai/google/aws casam, provando o arranjo): anthropic,
  # openrouter, groq, huggingface, github fine-grained PAT e zhipu TODOS
  # passavam limpos. Segundo CHAVES.md, três dessas (GROQ, OPENROUTER,
  # ZHIPU) são chaves vivas nesta máquina. Só a heurística #7 as pegava, e
  # só na forma de atribuição (`GROQ_API_KEY=gsk_...`) -- a chave colada em
  # prosa, que é o caso realista de vazamento, saía inteira.
  # Esta régua serve DOIS controles: P-1 (o que entra no repo público) e
  # sanitizar.py (o que sai pra provedor externo). Falsos positivos medidos
  # antes de acrescentar: ZERO arquivos rastreados para os cinco.
  'sk-(ant|or|proj)-[A-Za-z0-9_-]{20,}'       # Anthropic / OpenRouter / OpenAI project
  'gsk_[A-Za-z0-9]{40,}'                      # Groq
  'hf_[A-Za-z0-9]{30,}'                       # Hugging Face
  'github_pat_[A-Za-z0-9_]{50,}'              # GitHub fine-grained PAT
  '[0-9a-f]{32}\.[A-Za-z0-9]{16}'             # Zhipu/GLM (<32hex>.<16>)
)

# P-1 -- "Segredos só em ~/.config/agata/.env, fora do repo" (PROJETO, Segurança).
# Olha só o que está staged (git diff --cached), que é o que um pre-commit
# real veria. Padrões de chave conhecidos + heurística genérica. Heurística
# tem falso positivo/negativo -- rede de segurança adicional, não substitui
# revisão humana do diff.
# --- AUTOPROVA DOS PADRÕES (MEMÓRIAS (422)) -------------------------------
# O varredor prova que ENXERGA antes de dizer que não viu nada.
#
# Buraco medido em 09/09/2026, não teórico: um padrão MALFORMADO (ex.: um
# parêntese sem fechar) faz `grep -E` sair 2 e devolver VAZIO. No laço do
# checar_segredo, vazio == "não achei" == limpo. Ou seja: quebrar um padrão
# -- por edição desatenta, por merge, por um `sed` largo -- desliga aquela
# régua EM SILÊNCIO, e o segredo que ela guardava passa. O controle não
# distingue "procurei e não achei" de "não consegui procurar".
#
# Origem do achado: o modelo desta sessão declarou um commit "limpo" depois
# de uma varredura ad-hoc em que um dos 12 padrões (o PEM, que começa com
# `-----`) foi lido como OPÇÃO do grep e nunca chegou a rodar. O controle
# real não tinha esse defeito (usa `grep -E --`), mas o episódio expôs a
# pergunta certa: como alguém SABE que todos os padrões rodaram? Não sabia.
# Agora sabe. É a falha catalogada em REGRAS ("Grep negativo usado como
# prova de ausência sem validar o padrão contra um positivo conhecido
# primeiro", (250)-(251)) transformada em mecanismo em vez de advertência.
#
# Fixtures montadas em PEDAÇOS, nunca escritas inteiras: literal completo
# faria o próprio P-1 acusar este arquivo. Mesma convenção de
# redesign/router/sanitizar.py (_fx) e de scripts/testar_perimetro.sh (_k).
_vs_k() { local IFS=""; printf '%s' "$*"; }
_vs_rep() { printf "%${2}s" "" | tr ' ' "$1"; }

_autoprova_padroes() {
  local provas=(
    "$(_vs_k "AK" "IA" "$(_vs_rep A 16)")"
    "$(_vs_k "AI" "za" "$(_vs_rep b 35)")"
    "$(_vs_k "gh" "p" "_" "$(_vs_rep c 36)")"
    "$(_vs_k "sk" "-" "$(_vs_rep d 20)")"
    "$(_vs_k "xo" "xb" "-" "1234567890")"
    "$(_vs_k "---" "--BEGIN " "RSA " "PRIVATE " "KEY" "---" "--")"
    "$(_vs_k "API" "_KEY" "=" "$(_vs_rep e 16)")"
    "$(_vs_k "sk" "-" "ant" "-" "$(_vs_rep f 20)")"
    "$(_vs_k "gs" "k" "_" "$(_vs_rep g 40)")"
    "$(_vs_k "h" "f" "_" "$(_vs_rep h 30)")"
    "$(_vs_k "git" "hub" "_pat_" "$(_vs_rep i 50)")"
    "$(_vs_k "$(_vs_rep 0 32)" "." "$(_vs_rep j 16)")"
  )
  # O pareamento por POSIÇÃO é frágil por natureza -- foi exatamente assim
  # que _ROTULOS quebrou nesta mesma sessão quando padrões novos entraram
  # sem rótulo novo. Então o descasamento de tamanho é FALHA declarada, não
  # silêncio: quem acrescentar padrão sem acrescentar prova, descobre aqui.
  if [ "${#provas[@]}" -ne "${#PADROES_SEGREDO[@]}" ]; then
    echo "FALHA (P-1): ${#PADROES_SEGREDO[@]} padrões e ${#provas[@]} provas -- alguém acrescentou padrão sem a fixture correspondente. Enquanto não parear, o varredor NÃO pode declarar nada limpo."
    return 1
  fi
  local i ruim=0
  for i in "${!PADROES_SEGREDO[@]}"; do
    if ! printf '%s\n' "${provas[$i]}" | grep -qE -- "${PADROES_SEGREDO[$i]}" 2>/dev/null; then
      echo "FALHA (P-1): o padrão '${PADROES_SEGREDO[$i]}' NÃO casa a própria fixture -- está malformado ou foi quebrado numa edição. Esta régua está CEGA, e um segredo que ela cobria passaria como limpo. Conserte o padrão antes de comitar qualquer coisa."
      ruim=1
    fi
  done
  return "$ruim"
}

checar_segredo() {
  local achou=0

  # Antes de qualquer veredito: as réguas enxergam? Se alguma estiver cega,
  # "limpo" seria mentira -- e mentira de controle de segredo num repo
  # público. Falha fechada, como manda o princípio: controle que enxerga
  # menos do que devia é falha do controle, não licença.
  if ! _autoprova_padroes; then
    achou=1
  fi

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
