#!/usr/bin/env bash
# Passo 5 (ordem de saneamento, 15/08/2026 19:09): perímetro de controles.
# Escopo fechado de propósito -- NÃO é hardening geral, não é revisão de
# grupos, não é auditoria de pacotes. Cada checagem defende um controle
# que o canon já declarou, e cita a fonte. Controle não declarado não
# entra aqui -- propõe-se ao Humano, não se acrescenta por conta.
#
# P-1 a P-5 falham (exit != 0, e o script inteiro sai != 0 se qualquer
# um falhar). P-6 avisa, nunca falha -- aviso que trava fluxo vira aviso
# ignorado.
#
# Nada de correção automática: o script ACHA E PARA. Quem corrige o
# controle é o Humano, por decisão.
#
# Sourceável sem executar (BASH_SOURCE guard no fim) -- pra testar cada
# função isolada, mesmo método usado em varredura_segredo.sh.
set -uo pipefail

_PERIMETRO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$_PERIMETRO_DIR/varredura_segredo.sh"

cabecalho() {
  echo "=== $1 ==="
  echo "controle: $2"
  echo "fonte: $3"
}

# --- P-3 -----------------------------------------------------------------
# "Publicação é decisão deliberada; consentimento por trecho, com data"
# (REGRAS, Conselho; PROJETO, Estado de publicação). Escritores automáticos
# conhecidos, enumerados aqui -- cada um com o padrão gitignored que a
# publicação deliberada exige que NUNCA apareça rastreado:
#   - memória nativa do Hermes (USER.md/MEMORY.md e qualquer futuro arquivo
#     da mesma classe) -- achado em (181)/(189), protegido por `memoria/*.md`
#   - backup automático (bundles de git) -- achado em (97)/(98), protegido
#     por `*.bundle`
# Se .gitignore falhou ou foi forçado (`git add -f`), `git ls-files` ainda
# mostra o arquivo rastreado -- é isso que a checagem mede, não a presença
# da regra no .gitignore (regra existir não prova que foi respeitada).
p3_publicacao() {
  local escritores=("memoria/*.md" "*.bundle")
  local ruim=0
  local padrao achados
  for padrao in "${escritores[@]}"; do
    achados="$(git ls-files -- "$padrao")"
    if [ -n "$achados" ]; then
      echo "SUSPEITO (P-3): escritor automático '$padrao' tem arquivo RASTREADO, deveria estar fora do índice:"
      echo "$achados" | sed 's/^/  /'
      ruim=1
    fi
  done
  return "$ruim"
}

# --- P-4 -----------------------------------------------------------------
# "O api_server executa terminal: nunca expor sem contenção" e "Ollama
# restrito a 127.0.0.1" (PROJETO, Segurança). Transforma a auditoria
# pontual de S-2 (181) em checagem recorrente -- escopo fechado aos
# serviços do Agata (hermes*, ollama), não hardening de toda superfície
# de rede da máquina (isso já foi olhado uma vez em S-2 e ficou fora
# deste perímetro por decisão de escopo).
p4_bind() {
  local saida="${1:-}"
  [ -z "$saida" ] && saida="$(ss -tulpn 2>/dev/null)"
  local ruim=0
  local linha
  while IFS= read -r linha; do
    [ -z "$linha" ] && continue
    if echo "$linha" | grep -qiE "hermes|ollama"; then
      local endereco
      endereco="$(echo "$linha" | awk '{print $5}')"
      if echo "$endereco" | grep -qE '^(0\.0\.0\.0|\*|\[::\]|:::)'; then
        echo "SUSPEITO (P-4): serviço do Agata bindado fora de loopback: $linha"
        ruim=1
      fi
    fi
  done <<< "$saida"
  return "$ruim"
}

# --- P-5 -----------------------------------------------------------------
# "Registre e nunca apague" (REGRAS, Regra 4 -- linha vermelha). O
# controle mais forte do sistema, o único sem verificação mecânica até
# hoje. Compara o MEMÓRIAS.md staged (o que vai virar o próximo commit)
# contra o MEMÓRIAS.md do commit anterior (HEAD) -- não contra memória
# do executor. Append-only de verdade: o conteúdo antigo tem que ser
# prefixo byte-exato do novo. Encolher OU mudar qualquer byte anterior
# ao ponto de append é falha.
p5_append_only() {
  if ! git rev-parse HEAD >/dev/null 2>&1; then
    return 0
  fi
  # Achado real ao testar (15/08/2026): a primeira versão passava o
  # conteúdo inteiro do MEMÓRIAS.md (500 KB+) como argumento de linha de
  # comando pro python3 -- estourou ARG_MAX ("Lista de argumentos muito
  # longa"). Corrigido: escreve em arquivo temporário, python lê do
  # arquivo, só o caminho (curto) vira argv.
  # Achado real ao testar (15/08/2026): `trap ... RETURN` dentro desta
  # função não fica limitada a ela -- o bash não escopa isso por chamada,
  # e o trap disparava de novo no retorno da PRÓXIMA função (cabecalho,
  # p6_backup_pendente...), quando $tmp_antigo/$tmp_novo já tinham saído
  # de escopo, estourando "variável não associada" sob `set -u`.
  # Corrigido: limpeza explícita em cada saída, sem trap.
  local tmp_antigo tmp_novo codigo
  tmp_antigo="$(mktemp)"
  tmp_novo="$(mktemp)"
  if ! git show HEAD:MEMÓRIAS.md > "$tmp_antigo" 2>/dev/null; then
    rm -f "$tmp_antigo" "$tmp_novo"
    return 0
  fi
  if ! git show :MEMÓRIAS.md > "$tmp_novo" 2>/dev/null; then
    cat MEMÓRIAS.md > "$tmp_novo" 2>/dev/null
  fi
  python3 - "$tmp_antigo" "$tmp_novo" <<'PYEOF'
import sys
with open(sys.argv[1], 'rb') as f:
    antigo = f.read()
with open(sys.argv[2], 'rb') as f:
    novo = f.read()
if len(novo) < len(antigo):
    print(f"SUSPEITO (P-5): MEMÓRIAS.md ENCOLHEU -- {len(antigo)} bytes no commit anterior, {len(novo)} agora.")
    sys.exit(1)
if novo[:len(antigo)] != antigo:
    for i, (a, b) in enumerate(zip(antigo, novo)):
        if a != b:
            print(f"SUSPEITO (P-5): byte mudou no offset {i} -- MEMÓRIAS.md não é mais append-only.")
            print(f"  antigo: ...{antigo[max(0,i-40):i+40]!r}...")
            print(f"  novo:   ...{novo[max(0,i-40):i+40]!r}...")
            break
    sys.exit(1)
sys.exit(0)
PYEOF
  codigo=$?
  rm -f "$tmp_antigo" "$tmp_novo"
  return "$codigo"
}

# --- P-6 -----------------------------------------------------------------
# "Cópia da história fora desta máquina" (PROJETO, Riscos conhecidos).
# AVISA, nunca falha -- o incidente real de hoje foi o marcador acumulando
# em silêncio por um dia inteiro de trabalho intenso, sem ninguém notar
# até alguém perguntar. Limiar escolhido nesta sessão, documentado aqui
# por não haver um número já declarado no canon: mais de 3 commits OU
# mais de 2 horas desde que o marcador apareceu, o que vier primeiro.
P6_MAX_COMMITS=3
P6_MAX_HORAS=2
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

main() {
  cd "$(git rev-parse --show-toplevel)"
  local FALHOU=0

  cabecalho "P-1" "Segredos só em ~/.hermes/.env, fora do repo" "PROJETO, Segurança"
  if checar_segredo; then echo "veredito: OK"; else echo "veredito: FALHOU"; FALHOU=1; fi
  echo

  cabecalho "P-2" "O executor pausa e pede sudo ao Humano" "PROJETO, Sudo e interação humana"
  if checar_sudoers; then echo "veredito: OK"; else echo "veredito: FALHOU"; FALHOU=1; fi
  echo

  cabecalho "P-3" "Publicação é decisão deliberada; consentimento por trecho, com data" "REGRAS, Conselho · PROJETO, Estado de publicação"
  if p3_publicacao; then echo "veredito: OK"; else echo "veredito: FALHOU"; FALHOU=1; fi
  echo

  cabecalho "P-4" "api_server executa terminal, nunca expor sem contenção · Ollama restrito a 127.0.0.1" "PROJETO, Segurança"
  if p4_bind; then echo "veredito: OK"; else echo "veredito: FALHOU"; FALHOU=1; fi
  echo

  cabecalho "P-5" "Registre e nunca apague" "REGRAS, Regra 4 (linha vermelha)"
  if p5_append_only; then echo "veredito: OK"; else echo "veredito: FALHOU"; FALHOU=1; fi
  echo

  cabecalho "P-6" "Cópia da história fora desta máquina" "PROJETO, Riscos conhecidos"
  p6_backup_pendente
  echo "veredito: AVISO SÓ (nunca falha)"
  echo

  echo "=== RESULTADO GERAL: $([ "$FALHOU" -eq 0 ] && echo OK || echo FALHOU) ==="
  return "$FALHOU"
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  main
  exit $?
fi
