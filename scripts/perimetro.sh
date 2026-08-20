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
# SKIP e PARCIAL (MEMÓRIAS (193)): terceiro e quarto estado, nunca somados
# a OK no placar -- "verde que ninguém questiona é pior que checagem
# ausente" (ordem do Humano). SKIP = a checagem não rodou de verdade (ex.
# P-2 sem sudo não-interativo). PARCIAL = rodou, mas com visibilidade
# estruturalmente incompleta sem root (ex. P-4: `ss -tulpn` sem root só
# atribui processo a sockets do próprio UID -- ollama roda como usuário de
# sistema `ollama`, diferente de `orusoua`, e sai invisível pro grep sem
# nenhum erro). Nenhum dos dois falha o hook -- exigir root pra todo
# commit seria pior que a lacuna que eles sinalizam.
#
# Sourceável sem executar (BASH_SOURCE guard no fim) -- pra testar cada
# função isolada, mesmo método usado em varredura_segredo.sh.
#
# Todo alarme (SUSPEITO/PARCIAL/AVISO) diz três coisas, nesta ordem:
# o que aconteceu, por que importa, o que fazer. Ordem do Humano,
# MEMÓRIAS (202) -- a prova de legibilidade de (196)/(197) achou alarmes
# que só diziam as duas primeiras.
set -uo pipefail

_PERIMETRO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$_PERIMETRO_DIR/varredura_segredo.sh"
source "$_PERIMETRO_DIR/checar_citacao.sh"

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
  # Achado real ao testar (16/08/2026, MEMÓRIAS (193)): sem root, `ss -p`
  # só atribui processo a sockets do PRÓPRIO uid -- confirmado rodando de
  # verdade: a linha do ollama (uid `ollama`, systemd system service)
  # aparece com endereço e porta, mas ZERO texto de processo, enquanto a
  # do hermes-gateway (uid `orusoua`, mesmo uid do check) aparece completa.
  # O grep "hermes|ollama" contra a linha inteira nunca acha a de ollama
  # nesse caso -- não é falha, é ausência silenciosa. Marca PARCIAL sempre
  # que não-root, incondicional: não dá pra provar que nenhuma linha
  # oculta era hermes/ollama sem o privilégio pra ver.
  if [ "$(id -u)" -ne 0 ]; then
    PERIMETRO_ESTADO="PARCIAL"
    # MEMÓRIAS (202): PARCIAL sozinho não dizia por quê nem o que fazer --
    # os outros vereditos explicam antes do veredito, este não explicava.
    echo "PARCIAL: rodando sem privilégio de administrador, não enxergo todos os processos -- não é falha, é o controle enxergando menos do que deveria. Para ver completo: rode de novo com sudo."
  fi
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
    print(f"SUSPEITO (P-5, nunca se apaga história): MEMÓRIAS.md ENCOLHEU -- {len(antigo)} bytes no commit anterior, {len(novo)} agora. Alguma linha foi removida. Restaure o arquivo antes de comitar.")
    sys.exit(1)
if novo[:len(antigo)] != antigo:
    for i, (a, b) in enumerate(zip(antigo, novo)):
        if a != b:
            print(f"SUSPEITO (P-5, nunca se apaga história): byte mudou no offset {i} -- MEMÓRIAS.md não é mais append-only. Um trecho antigo foi alterado. Restaure o arquivo antes de comitar.")
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

# --- P-7 -----------------------------------------------------------------
# Citação de MEMÓRIAS aponta pra entrada real, não fabricada (REGRAS,
# "Citação de MEMÓRIAS -- primeira referência"). Checa só o que esta
# staged ACRESCENTOU a MEMÓRIAS.md, nunca o arquivo inteiro -- P-7 valida
# entrada NOVA a cada commit, não reaudita a história toda toda vez.
# Consequência direta: uma citação-exemplo já commitada no passado (ex.:
# (162), que cita "(101 - ...)" como transcrição literal de uma ordem,
# sem crases) nunca é rescaneada por este mecanismo -- só citações que
# entram DAQUI PRA FRENTE. checar_citacao.sh, função própria: MEMÓRIAS
# (203)/(204).
p7_citacao() {
  if ! git rev-parse HEAD >/dev/null 2>&1; then
    return 0
  fi
  local tmp_novo tmp_diff codigo
  tmp_novo="$(mktemp)"
  tmp_diff="$(mktemp)"
  if ! git show :MEMÓRIAS.md > "$tmp_novo" 2>/dev/null; then
    cat MEMÓRIAS.md > "$tmp_novo" 2>/dev/null
  fi
  git diff --cached -U0 -- MEMÓRIAS.md 2>/dev/null | grep -E '^\+' | grep -vE '^\+\+\+' | sed 's/^\+//' > "$tmp_diff"
  checar_citacao "$tmp_diff" "$tmp_novo"
  codigo=$?
  rm -f "$tmp_novo" "$tmp_diff"
  return "$codigo"
}

# --- P-8 -----------------------------------------------------------------
# Quarentena de mudança estrutural (item 6, documento do Humano
# 20/08/2026, proposta do Marcos, MEMÓRIAS (218)). O BURACO que isto
# fecha: até aqui, o executor escreve em canon, comita e empurra -- o
# Humano fica sabendo DEPOIS. Nenhuma checagem P-1 a P-7 cobria isso;
# mesma classe do incidente de MEMÓRIAS (214) (sincronizar-estado.sh
# publicando sozinho apesar do próprio cabeçalho dizer que não).
#
# Escopo, proporcional de propósito (ordem do Humano):
#   QUARENTENA OBRIGATÓRIA -- muda COMPORTAMENTO: REGRAS.md, PROJETO.md,
#   scripts/*, .githooks/*
#   SEM quarentena -- só REGISTRA o que já aconteceu: MEMÓRIAS.md,
#   ONDE_ESTAMOS.md, INDICE_MEMORIAS.md, .hermes.md (gerado)
# Motivo da linha: registro errado se corrige com entrada nova -- é pra
# isso que append-only existe. Comportamento errado, não.
#
# Mecanismo: propostas/<nome>.diff (a mudança, cabeçalhos `--- a/` /
# `+++ b/` de verdade) + propostas/APROVADO-<nome> (criado pelo Humano
# == aprovação). Sem o par cobrindo o caminho staged, o commit FALHA.
# Ver propostas/README.md pro mecanismo completo, incluindo o risco
# residual registrado sem suavizar: o marcador é um arquivo que o
# próprio executor tem permissão técnica de criar -- P-8 impede
# automação agindo sem ninguém perceber, não impede contorno deliberado.
_p8_eh_comportamento() {
  case "$1" in
    REGRAS.md|PROJETO.md|scripts/*|.githooks/*) return 0 ;;
    *) return 1 ;;
  esac
}

_p8_caminhos_aprovados() {
  # Acha o par diff/APROVADO em propostas/ (pendente) OU em
  # propostas/aplicadas/ (já consumido). Precisa cobrir os dois: a
  # aprovação consumida no MESMO commit que aplica a mudança já não está
  # mais em propostas/ quando este check roda -- foi movida pra
  # aplicadas/ como parte do próprio commit staged (achado testando
  # antes de comitar de verdade: sem isso, todo commit que consome uma
  # aprovação reprovaria a própria aprovação que o autoriza).
  local diretorio aprovado nome diff_path
  for diretorio in propostas propostas/aplicadas; do
    [ -d "$diretorio" ] || continue
    for aprovado in "$diretorio"/APROVADO-*; do
      [ -e "$aprovado" ] || continue
      nome="$(basename "$aprovado")"
      nome="${nome#APROVADO-}"
      diff_path="$diretorio/${nome}.diff"
      [ -f "$diff_path" ] || continue
      grep -E '^(\+\+\+ b/|--- a/)' "$diff_path" 2>/dev/null | sed -E 's#^(\+\+\+ b/|--- a/)##' | grep -v '^/dev/null$'
    done
  done
}

p8_quarentena() {
  local staged f ruim=0 aprovados
  staged="$(git diff --cached --name-only)"
  [ -z "$staged" ] && return 0
  aprovados="$(_p8_caminhos_aprovados)"
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if _p8_eh_comportamento "$f"; then
      if ! printf '%s\n' "$aprovados" | grep -qxF "$f"; then
        echo "SUSPEITO (P-8): '$f' muda comportamento e está staged sem propostas/APROVADO-<nome> correspondente (o .diff em propostas/ precisa citar este caminho nos cabeçalhos). Crie a proposta, peça aprovação do Humano (propostas/README.md), ou tire este arquivo do commit."
        ruim=1
      fi
    fi
  done <<< "$staged"
  return "$ruim"
}

# Imprime o veredito de uma checagem e soma no placar -- único ponto que
# decide OK vs SKIP vs PARCIAL vs FALHOU, pra nenhuma chamada em main()
# arriscar imprimir "OK" por engano quando a checagem só pulou (MEMÓRIAS
# (193)). $1 = exit code da checagem; usa PERIMETRO_ESTADO, que a própria
# checagem deixa setado quando não é um OK de verdade.
_perimetro_veredito() {
  local codigo="$1"
  if [ "$codigo" -ne 0 ]; then
    echo "veredito: FALHOU"
    FALHOU=1
    CONT_FALHA=$((CONT_FALHA + 1))
  elif [ "$PERIMETRO_ESTADO" = "SKIP" ]; then
    echo "veredito: SKIP"
    CONT_SKIP=$((CONT_SKIP + 1))
  elif [ "$PERIMETRO_ESTADO" = "PARCIAL" ]; then
    echo "veredito: PARCIAL"
    CONT_PARCIAL=$((CONT_PARCIAL + 1))
  else
    echo "veredito: OK"
    CONT_OK=$((CONT_OK + 1))
  fi
}

main() {
  cd "$(git rev-parse --show-toplevel)"
  FALHOU=0
  CONT_OK=0
  CONT_SKIP=0
  CONT_PARCIAL=0
  CONT_FALHA=0

  cabecalho "P-1" "Segredos só em ~/.hermes/.env, fora do repo" "PROJETO, Segurança"
  PERIMETRO_ESTADO=""
  checar_segredo; _perimetro_veredito "$?"
  echo

  cabecalho "P-2" "O executor pausa e pede sudo ao Humano" "PROJETO, Sudo e interação humana"
  PERIMETRO_ESTADO=""
  checar_sudoers; _perimetro_veredito "$?"
  echo

  cabecalho "P-3" "Publicação é decisão deliberada; consentimento por trecho, com data" "REGRAS, Conselho · PROJETO, Estado de publicação"
  PERIMETRO_ESTADO=""
  p3_publicacao; _perimetro_veredito "$?"
  echo

  cabecalho "P-4" "api_server executa terminal, nunca expor sem contenção · Ollama restrito a 127.0.0.1" "PROJETO, Segurança"
  PERIMETRO_ESTADO=""
  p4_bind; _perimetro_veredito "$?"
  echo

  cabecalho "P-5" "Registre e nunca apague" "REGRAS, Regra 4 (linha vermelha)"
  PERIMETRO_ESTADO=""
  p5_append_only; _perimetro_veredito "$?"
  echo

  cabecalho "P-7" "Citação de MEMÓRIAS aponta pra entrada real, não fabricada" "REGRAS, Citação de MEMÓRIAS — primeira referência"
  PERIMETRO_ESTADO=""
  p7_citacao; _perimetro_veredito "$?"
  echo

  cabecalho "P-8" "Quarentena: mudança de comportamento exige propostas/APROVADO-<nome> antes de entrar no canon" "PROJETO, Quarentena estrutural (item 6, 20/08/2026) · propostas/README.md"
  PERIMETRO_ESTADO=""
  p8_quarentena; _perimetro_veredito "$?"
  echo

  cabecalho "P-6" "Cópia da história fora desta máquina" "PROJETO, Riscos conhecidos"
  p6_backup_pendente
  echo "veredito: AVISO SÓ (nunca falha)"
  CONT_OK=$((CONT_OK + 1))
  echo

  echo "=== RESULTADO GERAL: $([ "$FALHOU" -eq 0 ] && echo OK || echo FALHOU) -- ${CONT_OK} OK · ${CONT_SKIP} SKIP · ${CONT_PARCIAL} PARCIAL · ${CONT_FALHA} FALHA ==="
  return "$FALHOU"
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  main
  exit $?
fi
