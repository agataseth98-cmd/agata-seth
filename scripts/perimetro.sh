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
source "$_PERIMETRO_DIR/checar_discordancia.sh"

cabecalho() {
  # PERIMETRO_CTRL: qual controle está correndo agora. Existe para o P-17
  # (vigia de SKIP) saber a QUEM atribuir um SKIP -- antes, o veredito era
  # anônimo e um controle podia ficar em SKIP para sempre sem nome nem conta.
  PERIMETRO_CTRL="$1"
  echo "=== $1 ==="
  echo "controle: $2"
  echo "fonte: $3"
}

# Âncora de append-only pelo topo, usada por P-5 (MEMÓRIAS (271)).
_P5_MARCADOR="<!-- ENTRADAS-NOVAS:AQUI"

# Mesmo padrão de propostas/APROVADO-<nome> (P-8): arquivo que o Humano
# cria pra autorizar, uso único, procurado em propostas/ e
# propostas/aplicadas/. Ecoa o caminho achado (não só 0/1) pro chamador
# poder citar qual marca disparou o ramo de permutação no aviso.
_p5_migracao_pendente() {
  local diretorio arq
  # PERIODO (Fase 4, MEMÓRIAS (357)): mecanismo RECORRENTE, ao contrário do
  # de (271) (uso único histórico) -- por isso pode continuar sendo achado
  # em propostas/aplicadas/ pra sempre sem risco: quem chama esta função
  # pra decidir o ramo PERIODO (`p5_append_only`) só olha pra marca DEPOIS
  # de o crescimento ordinário já ter falhado de verdade (quente/morno
  # encolheram), e mesmo assim quem prova que a migração é legítima é
  # `verificar_migracao_periodo.py` (byte a byte), não a marca sozinha.
  # Achado real, corrigido: uma versão anterior restringia a marca PERIODO
  # a só contar em propostas/ (pendente) -- resolvia o "nunca expira", mas
  # quebrava o padrão de sempre (marca commitada em aplicadas/ junto com o
  # resto) para o SEGUNDO corte de período. A ordem de decisão em
  # `p5_append_only` (ordinário primeiro) já resolve o "nunca expira" sem
  # precisar desta restrição.
  for diretorio in propostas propostas/aplicadas; do
    [ -d "$diretorio" ] || continue
    for arq in "$diretorio"/MIGRACAO-P5-*; do
      [ -e "$arq" ] && { echo "$arq"; return 0; }
    done
  done
  return 1
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
# controle mais forte do sistema. Compara os arquivos de camada quente/morna
# staged (o que vai virar o próximo commit) contra a versão do commit
# anterior (HEAD) -- não contra memória do executor.
#
# Desde MEMÓRIAS (271), 26/08/2026: MEMÓRIAS.md cresce pelo TOPO do corpo
# (logo após o marcador ENTRADAS-NOVAS). Desde "MEMÓRIAS por período"
# (Fase 4, MEMÓRIAS (357)): MEMORIAS-MORNO.md existe como segunda camada,
# mesma disciplina de crescimento por topo, e um chunk MEMORIAS-FRIO-*.md
# uma vez selado não é mais protegido por P-5 -- vira P-14
# (imutabilidade total, nunca mais escrita nenhuma, nem por sufixo).
#
# Ramos, nesta ordem de prioridade:
#   0. Marca de migração de PERÍODO presente (propostas*/MIGRACAO-P5-PERIODO-<nome>)
#      -- checagem de PERMUTAÇÃO entre CAMADAS via
#      scripts/verificar_migracao_periodo.py: união de quente+morno (HEAD)
#      == união de quente+morno+frio-novo (staged), byte-idêntico, só
#      realocado. Cada corte de período usa esta marca -- não é uso único
#      como o item 1 abaixo, é o mecanismo recorrente da Fase 4.
#   1. Marca de migração ANTIGA presente (MIGRACAO-P5-<nome>, sem
#      "PERIODO") -- checagem de PERMUTAÇÃO só de MEMÓRIAS.md via
#      scripts/verificar_migracao_memorias.py. Único uso esperado: a
#      migração de (271). Preservado por compatibilidade histórica.
#   2. Sem marca: roda o sufixo/prefixo normal (_p5_checar_sufixo, abaixo)
#      pra MEMÓRIAS.md E, se já existir no HEAD, pra MEMORIAS-MORNO.md --
#      as duas independentemente, as duas têm que passar.
_p5_checar_sufixo() {
  local caminho="$1" rotulo="$2"
  local tmp_antigo tmp_novo codigo
  tmp_antigo="$(mktemp)"
  tmp_novo="$(mktemp)"
  if ! git show "HEAD:$caminho" > "$tmp_antigo" 2>/dev/null; then
    # Arquivo não existia no HEAD (ex.: MEMORIAS-MORNO.md antes da
    # primeira migração de período) -- nada a proteger ainda, ele nasce
    # com o primeiro commit que o cria, fora do escopo deste controle.
    rm -f "$tmp_antigo" "$tmp_novo"
    return 0
  fi
  if ! git show ":$caminho" > "$tmp_novo" 2>/dev/null; then
    cat "$caminho" > "$tmp_novo" 2>/dev/null
  fi
  if grep -qF "$_P5_MARCADOR" "$tmp_antigo"; then
    python3 - "$tmp_antigo" "$tmp_novo" "$rotulo" <<'PYEOF'
import sys
MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI".encode("utf-8")
rotulo = sys.argv[3]
with open(sys.argv[1], 'rb') as f:
    antigo = f.read()
with open(sys.argv[2], 'rb') as f:
    novo = f.read()
i_antigo = antigo.find(MARCADOR)
i_novo = novo.find(MARCADOR)
if i_antigo == -1:
    print(f"SUSPEITO (P-5): marcador ENTRADAS-NOVAS não achado no commit anterior de {rotulo} apesar do grep externo achar -- inconsistência, restaure antes de comitar.")
    sys.exit(1)
if i_novo == -1:
    print(f"SUSPEITO (P-5, nunca se apaga história): marcador ENTRADAS-NOVAS existia no commit anterior de {rotulo} e sumiu no staged -- não se apaga a âncora de append-only.")
    sys.exit(1)
fim_linha_antigo = antigo.find(b'\n', i_antigo) + 1
fim_linha_novo = novo.find(b'\n', i_novo) + 1
corpo_antigo = antigo[fim_linha_antigo:]
corpo_novo = novo[fim_linha_novo:]
if len(corpo_novo) < len(corpo_antigo):
    print(f"SUSPEITO (P-5, nunca se apaga história): corpo de {rotulo} ENCOLHEU -- {len(corpo_antigo)} bytes no commit anterior, {len(corpo_novo)} agora. Alguma entrada foi removida (ou precisa da marca de migração de período). Restaure antes de comitar.")
    sys.exit(1)
if not corpo_novo.endswith(corpo_antigo):
    print(f"SUSPEITO (P-5, nunca se apaga história): o conteúdo antigo de {rotulo} não é mais um SUFIXO do novo -- uma entrada já registrada foi alterada, ou a entrada nova não entrou logo após o marcador. Restaure antes de comitar.")
    sys.exit(1)
sys.exit(0)
PYEOF
    codigo=$?
  else
    python3 - "$tmp_antigo" "$tmp_novo" "$rotulo" <<'PYEOF'
import sys
rotulo = sys.argv[3]
with open(sys.argv[1], 'rb') as f:
    antigo = f.read()
with open(sys.argv[2], 'rb') as f:
    novo = f.read()
if len(novo) < len(antigo):
    print(f"SUSPEITO (P-5, nunca se apaga história): {rotulo} ENCOLHEU -- {len(antigo)} bytes no commit anterior, {len(novo)} agora. Alguma linha foi removida. Restaure antes de comitar.")
    sys.exit(1)
if novo[:len(antigo)] != antigo:
    for i, (a, b) in enumerate(zip(antigo, novo)):
        if a != b:
            print(f"SUSPEITO (P-5, nunca se apaga história): byte mudou no offset {i} de {rotulo} -- não é mais append-only. Um trecho antigo foi alterado. Restaure antes de comitar.")
            print(f"  antigo: ...{antigo[max(0,i-40):i+40]!r}...")
            print(f"  novo:   ...{novo[max(0,i-40):i+40]!r}...")
            break
    sys.exit(1)
sys.exit(0)
PYEOF
    codigo=$?
  fi
  rm -f "$tmp_antigo" "$tmp_novo"
  return "$codigo"
}

# Checagem de PERMUTAÇÃO entre camadas pra migração de período: união de
# {MEMÓRIAS.md, MEMORIAS-MORNO.md} no HEAD (as que existirem) tem que
# bater, byte a byte, com a união de {MEMÓRIAS.md, MEMORIAS-MORNO.md,
# todo MEMORIAS-FRIO-*.md ADICIONADO nesta commit} no staged. Chunk frio
# já existente no HEAD nunca entra aqui -- depois de selado é P-14, não
# P-5 (nunca deveria mudar de novo).
_p5_periodo_verificar() {
  local -a antes=() depois=()
  local f tmp staged_frio
  for f in "MEMÓRIAS.md" "MEMORIAS-MORNO.md"; do
    if git show "HEAD:$f" >/dev/null 2>&1; then
      tmp="$(mktemp)"; git show "HEAD:$f" > "$tmp"; antes+=("$tmp")
    fi
    if git show ":$f" >/dev/null 2>&1; then
      tmp="$(mktemp)"; git show ":$f" > "$tmp"; depois+=("$tmp")
    fi
  done
  staged_frio="$(git diff --cached --name-only --diff-filter=A -- 'MEMORIAS-FRIO-*.md' 2>/dev/null)"
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    tmp="$(mktemp)"; git show ":$f" > "$tmp"; depois+=("$tmp")
  done <<< "$staged_frio"

  if [ "${#antes[@]}" -eq 0 ]; then
    echo "SUSPEITO (P-5, período): marca de migração presente mas nenhum arquivo de quente/morno achado no HEAD -- nada a comparar, restaure antes de comitar."
    rm -f "${depois[@]}"
    return 1
  fi
  python3 "$_PERIMETRO_DIR/verificar_migracao_periodo.py" --antes "${antes[@]}" --depois "${depois[@]}"
  local codigo=$?
  rm -f "${antes[@]}" "${depois[@]}"
  return "$codigo"
}

# Qual ramo o P-5 realmente tomou nesta corrida: "ordinario" (crescimento
# normal, entrada nova -- há bytes novos a citar) ou "permutacao" (migração
# entre camadas, byte a byte, nada de conteúdo novo). O P-7 lê isto pra
# decidir se pode pular. Antes ele lia a MARCA de migração direto, e a marca
# mora em propostas/aplicadas/, que NUNCA é limpo (é registro histórico, por
# desenho) -- resultado: a marca de 06/09/2026 desligou o P-7 em todo commit
# desde então, alegando "P-5 já provou por permutação" quando o P-5 tinha
# passado pelo ramo ordinário. Mesmo bug que o próprio P-5 já corrigiu pra si
# (comentário longo abaixo, "uma marca antiga esquecida"); a correção nunca
# tinha chegado ao P-7.
P5_RAMO="ordinario"
# Houve entrada NOVA nesta corrida, mesmo tendo ido pelo ramo de permutação?
# O verificador de permutação distingue "entrada realocada byte-idêntica" de
# "entrada nova genuína" e ANUNCIA a contagem. Sem ler essa contagem, o P-7
# pulava um commit que trazia entrada nova só porque o P-5 tinha ido pela
# permutação -- foi assim que a suíte de regressão dos controles pegou, em
# 09/09/2026, um furo introduzido pelo conserto do dia anterior ((419)).
P5_ENTRADAS_NOVAS=0

p5_append_only() {
  P5_RAMO="ordinario"
  P5_ENTRADAS_NOVAS=0
  if ! git rev-parse HEAD >/dev/null 2>&1; then
    return 0
  fi
  # Achado real ao testar (15/08/2026): `trap ... RETURN` dentro de uma
  # função não fica limitada a ela -- o bash não escopa isso por chamada.
  # Corrigido: limpeza explícita em cada saída, sem trap (vale pros
  # helpers acima também).
  #
  # (271), sem PERIODO no nome: branch histórico, prioridade sobre o resto,
  # comportamento intocado desde sempre -- reordenação de MEMÓRIAS.md não é
  # suficiente-crescimento, tem que ir direto pra permutação.
  local marca_migracao
  marca_migracao="$(_p5_migracao_pendente)" || true
  if [ -n "$marca_migracao" ] && [[ "$marca_migracao" != *PERIODO* ]]; then
    P5_RAMO="permutacao"
    echo "P-5: marca de migração '$marca_migracao' presente -- checagem de PERMUTAÇÃO (verificar_migracao_memorias.py), não de sufixo. Uso único, MEMÓRIAS (271)."
    local tmp_antigo tmp_novo codigo
    tmp_antigo="$(mktemp)"; tmp_novo="$(mktemp)"
    if ! git show HEAD:MEMÓRIAS.md > "$tmp_antigo" 2>/dev/null; then
      rm -f "$tmp_antigo" "$tmp_novo"; return 0
    fi
    if ! git show :MEMÓRIAS.md > "$tmp_novo" 2>/dev/null; then
      cat MEMÓRIAS.md > "$tmp_novo" 2>/dev/null
    fi
    if python3 "$_PERIMETRO_DIR/verificar_migracao_memorias.py" "$tmp_antigo" "$tmp_novo"; then
      codigo=0
    else
      codigo=1
    fi
    rm -f "$tmp_antigo" "$tmp_novo"
    return "$codigo"
  fi

  # PERIODO (Fase 4): ao contrário de (271), tenta o crescimento ORDINÁRIO
  # primeiro -- quente/morno crescendo normalmente (entrada nova) não
  # precisa de marca nenhuma, igual a todo commit de sempre. Só cai pra
  # permutação entre camadas se o crescimento ordinário genuinamente
  # falhar (encolheu de verdade -- migração real aconteceu). Achado
  # preparando o segundo corte de período: a versão anterior dava
  # prioridade à marca ANTES de tentar o ordinário, e uma marca antiga
  # esquecida em propostas/aplicadas/ forçava todo commit seguinte (mesmo
  # um sem migração nenhuma, só entrada nova) pela checagem de permutação
  # estrita, reprovando por "conteúdo novo". Nesta ordem, uma marca velha
  # nunca atrapalha um commit ordinário -- e quando a permutação É
  # necessária, o verificador (byte a byte) continua sendo a rede de
  # segurança real, não a marca.
  # Tentativa silenciosa primeiro -- saída só é impressa se for mesmo o
  # veredito final (senão, "ENCOLHEU" apareceria no log de um commit que
  # vai passar de qualquer jeito pela permutação, achado mais confuso que
  # útil de propósito).
  local saida_quente saida_morno cod_quente cod_morno
  saida_quente="$(_p5_checar_sufixo "MEMÓRIAS.md" "MEMÓRIAS.md (quente)" 2>&1)"; cod_quente=$?
  saida_morno="$(_p5_checar_sufixo "MEMORIAS-MORNO.md" "MEMORIAS-MORNO.md (morno)" 2>&1)"; cod_morno=$?
  if [ "$cod_quente" -eq 0 ] && [ "$cod_morno" -eq 0 ]; then
    return 0
  fi
  if [ -n "$marca_migracao" ]; then
    P5_RAMO="permutacao"
    echo "P-5: crescimento ordinário falhou (quente/morno encolheram) e marca '$marca_migracao' está presente -- checagem de PERMUTAÇÃO entre camadas (verificar_migracao_periodo.py), quente+morno+frio. MEMÓRIAS por período (Fase 4)."
    local saida_perm codigo_perm
    saida_perm="$(_p5_periodo_verificar 2>&1)"; codigo_perm=$?
    [ -n "$saida_perm" ] && echo "$saida_perm"
    # O verificador separa "entrada realocada byte-idêntica" de "entrada NOVA
    # genuína" e imprime a contagem das novas. Se veio entrada nova, este
    # commit TEM conteúdo inédito -- e o P-7 não pode pular alegando que não
    # há nada a citar. Medido em 09/09/2026: uma entrada gravada no lugar
    # errado (fim do arquivo, em vez do topo abaixo do marcador) derruba o
    # crescimento ordinário, cai aqui, passa como permutação legítima com
    # "+1 entrada nova genuína" -- e o P-7 pulava justo o commit que trazia
    # a citação nova. Achado pela suíte scripts/testar_perimetro.sh no
    # primeiro dia dela, contra um furo que o conserto do dia anterior
    # ((419)) tinha acabado de criar.
    if echo "$saida_perm" | grep -qE '[1-9][0-9]* entrada\(s\) nova\(s\) genuína\(s\)'; then
      P5_ENTRADAS_NOVAS=1
    fi
    return "$codigo_perm"
  fi
  [ -n "$saida_quente" ] && echo "$saida_quente"
  [ -n "$saida_morno" ] && echo "$saida_morno"
  local ruim=0
  [ "$cod_quente" -eq 0 ] || ruim=1
  [ "$cod_morno" -eq 0 ] || ruim=1
  return "$ruim"
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

# --- P-12 ---------------------------------------------------------------
# "Todo recurso com backup verificavel" (ROADMAP, Fase 7). Um recurso do
# models/manifest.json cujo CONTEUDO ATUAL (sha256) nao tem snapshot
# restic == trabalho que some num disco morto. P-6 avisa "conecte o HD";
# P-12 e' POR RECURSO e e' FALHA-class (mesma severidade de P-8) para os
# recursos irrecuperaveis.
#
# REGUA -- decisao do Humano (redesign/fase7-hd/REGUA-P12.md). Reafinar =
# mudar SO estas tres linhas; o resto do controle nao muda:
P12_N_DIAS=14
P12_FALHA_SEM_BACKUP="rlm-qwen3-8b-teste:latest multilingual-e5-small-int8"
P12_AVISO_SEM_BACKUP="whisper-base-int8-ov whisper-small-int8-ov"
# Recurso do manifesto fora das duas listas == ISENTO (reconstruivel:
# 'ollama pull' / HF publico com hash fixado -- models/RECONSTRUCAO.md).
# A isencao e' deliberada: P-12 sempre-vermelho vira P-12 ignorado.
#
# HD AUSENTE: P-12 nunca FALHA um commit (disco no trabalho nao trava o
# hook). Le o cache de cobertura que a passada de backup deixa quando o
# HD ESTA presente, e reporta PARCIAL com a data mais velha. FALHA so
# quando o HD esta montado E um recurso da lista-FALHA nao tem snapshot
# para o sha256 atual < N dias.
# ${USER:-...}: achado 04/09/2026 (Camada C) -- sob `set -u`, $USER indefinido
# (containers/cron/systemd sem login shell) derrubava o script inteiro com
# "USER: unbound variable" ANTES de rodar qualquer controle -- o guardião de
# commits falhando por detalhe de ambiente, não por violação real. `id -un`
# é a mesma informação, sem depender de env var.
P12_REPO="${AGATA_RESTIC_REPO:-/run/media/${USER:-$(id -un)}/AgataBkup01/restic-agata-local}"
P12_PASS="$HOME/.config/agata/restic.pass"
P12_CACHE="$HOME/.agata-backup-staging/p12-cobertura.json"
p12_backup_verificavel() {
  local manifesto="models/manifest.json"
  if [ ! -f "$manifesto" ]; then
    echo "P-12: $manifesto ausente -- pulado."
    PERIMETRO_ESTADO="SKIP"; return 0
  fi
  if ! command -v restic >/dev/null 2>&1; then
    echo "PARCIAL (P-12): restic nao instalado -- nao da pra conferir backup por recurso."
    PERIMETRO_ESTADO="PARCIAL"; return 0
  fi

  local hd_ok=0
  if [ -d "$P12_REPO" ] && [ -f "$P12_PASS" ] && \
     RESTIC_PASSWORD_FILE="$P12_PASS" restic -r "$P12_REPO" cat config >/dev/null 2>&1; then
    hd_ok=1
  fi

  # nome<TAB>sha256 de cada recurso (blob_sha256 ou ir_sha256_xmlbin).
  local linhas
  linhas="$(python3 - "$manifesto" <<'PY'
import json, sys
m = json.load(open(sys.argv[1], encoding="utf-8"))
for x in m["modelos"]:
    h = x.get("blob_sha256") or x.get("ir_sha256_xmlbin") or ""
    print(x["name"] + "\t" + h)
PY
)"

  local falhou_p12=0 nome hash em_falha em_aviso fresco
  local TAB
  TAB="$(printf '\t')"
  while IFS="$TAB" read -r nome hash; do
    [ -z "$nome" ] && continue
    case " $P12_FALHA_SEM_BACKUP " in *" $nome "*) em_falha=1 ;; *) em_falha=0 ;; esac
    case " $P12_AVISO_SEM_BACKUP " in *" $nome "*) em_aviso=1 ;; *) em_aviso=0 ;; esac
    [ "$em_falha" = 0 ] && [ "$em_aviso" = 0 ] && continue

    if [ "$hd_ok" = 1 ]; then
      fresco="$(RESTIC_PASSWORD_FILE="$P12_PASS" P12_REPO="$P12_REPO" \
        python3 - "$nome" "$hash" "$P12_N_DIAS" <<'PY'
import json, os, subprocess, sys, datetime
nome, alvo, ndias = sys.argv[1], sys.argv[2], int(sys.argv[3])
try:
    out = subprocess.run(
        ["restic", "-r", os.environ["P12_REPO"], "snapshots", "--json", "--tag", nome],
        check=True, capture_output=True, text=True, timeout=60,
    ).stdout
    snaps = json.loads(out or "[]")
except Exception:
    snaps = []
agora = datetime.datetime.now(datetime.timezone.utc)
ok = False
for s in snaps:
    tags = s.get("tags") or []
    if alvo and alvo not in tags:
        continue
    t = (s.get("time") or "")[:19]
    try:
        dt = datetime.datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
    except Exception:
        continue
    if (agora - dt).days <= ndias:
        ok = True
print("1" if ok else "0")
PY
)"
      if [ "$fresco" != 1 ]; then
        if [ "$em_falha" = 1 ]; then
          echo "SUSPEITO (P-12): recurso '$nome' (sha256 ${hash:0:12}...) sem snapshot restic do conteudo atual < ${P12_N_DIAS}d. Por que importa: build local irrecuperavel -- disco morto = trabalho perdido. O que fazer: com o HD montado, redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md -- 'restic backup --tag $nome --tag $hash <path>' + 'restic check'."
          falhou_p12=1
        else
          echo "AVISO (P-12): recurso '$nome' sem snapshot restic < ${P12_N_DIAS}d (reconstruivel do HF/registry, mas o re-download e' lento -- vale um snapshot). Ver redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md."
        fi
      fi
    fi
  done <<EOF
$linhas
EOF

  [ "$falhou_p12" = 1 ] && return 1

  if [ "$hd_ok" = 0 ]; then
    local visto="nunca"
    if [ -f "$P12_CACHE" ]; then
      visto="$(python3 - "$P12_CACHE" <<'PY'
import json, sys
try:
    c = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception:
    c = {}
ds = [v.get("verificado_em", "") for v in c.values() if isinstance(v, dict) and v.get("verificado_em")]
print(min(ds) if ds else "nunca")
PY
)"
    fi
    echo "PARCIAL (P-12): HD ($P12_REPO) ausente -- cobertura de backup nao re-conferida. Cache de cobertura mais velho: $visto. O que fazer: no proximo acesso ao HD, rodar redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md (snapshots + restic check + reescreve o cache)."
    PERIMETRO_ESTADO="PARCIAL"; return 0
  fi
  return 0
}

# --- P-14 -----------------------------------------------------------------
# "Depois de selado, imutável" (MEMÓRIAS por período, Fase 4, MEMÓRIAS
# (357)). Um chunk MEMORIAS-FRIO-*.md listado em SELOS.txt nunca mais
# recebe escrita nenhuma -- nem sequer voltar a aparecer staged. Diferente
# de P-5 (que permite crescer): aqui a garantia é imutabilidade TOTAL.
# FALHA-class, mesma severidade de P-8 -- violar um selo é o mesmo tipo de
# "história editada" que Regra 4 existe pra impedir, só que na camada fria.
p14_frio_imutavel() {
  [ -f SELOS.txt ] || return 0
  local ruim=0 arquivo staged tmp_saida selos_lista
  # A lista de selos vem de HEAD:SELOS.txt, não do disco. Se viesse do
  # disco, apagar a linha de um chunk e reescrever o chunk no MESMO commit
  # tiraria os dois do radar: o loop abaixo nunca veria o nome, e o
  # selar.sh --check (a outra perna) também não -- o chunk sumiria do
  # relatório em vez de aparecer como VIOLADO. Medido em 09/09/2026 numa
  # cópia em sandbox. Lendo de HEAD, remover a linha não desprotege
  # retroativamente o que já estava selado. (O outro lado do conserto:
  # SELOS.txt entrou na quarentena P-8, então mexer nele exige aprovação
  # assinada.) Sem HEAD ainda (primeiro commit) cai pro disco -- bootstrap,
  # mesma lógica de _p8_assinatura_ok.
  selos_lista="$(git show HEAD:SELOS.txt 2>/dev/null)" || selos_lista=""
  [ -z "$selos_lista" ] && selos_lista="$(cat SELOS.txt 2>/dev/null)"
  # Só é violação re-tocar um chunk que JÁ existia selado num commit
  # ANTERIOR -- na própria commit que cria e sela o chunk pela primeira vez
  # ele necessariamente aparece staged, e isso é normal (mesmo bootstrap de
  # P-8: aprovar e criar acontecem juntos).
  # Antes esse caso era excluído por `--diff-filter=M` (só MODIFICADO, nunca
  # ADICIONADO). O filtro saiu, e o caso continua excluído por um motivo
  # melhor: a lista agora vem de HEAD:SELOS.txt, e no commit que cria o
  # chunk o selo dele ainda NÃO está em HEAD -- o nome nem entra no loop.
  # Trocar o filtro pela origem-em-HEAD amplia a cobertura de graça: agora
  # DELEÇÃO e RENOMEAÇÃO de um chunk já selado também são pegas, e o
  # `--diff-filter=M` deixava as duas passarem.
  # --no-renames pelo mesmo motivo de P-8/P-11 (furo medido nesta data):
  # sem ele o lado antigo de um rename some da listagem. Aqui o
  # selar.sh --check ainda pegaria pelo hash, mas os três controles devem
  # enxergar o mesmo conjunto de paths -- controle que enxerga menos do que
  # devia é falha do controle (REGRAS, Princípios: Segurança).
  staged="$(git -c core.quotepath=false diff --cached --no-renames --name-only)"
  while read -r _ arquivo _; do
    [ -z "$arquivo" ] && continue
    if echo "$staged" | grep -qxF "$arquivo"; then
      echo "SUSPEITO (P-14): '$arquivo' está selado (SELOS.txt), já existia num commit anterior, e aparece staged neste commit -- chunk frio nunca recebe escrita depois de selado. O que fazer: 'git restore --staged $arquivo'; se o conteúdo mudou de verdade, o arquivo foi violado -- restaure também o conteúdo."
      ruim=1
    fi
  done <<< "$selos_lista"
  tmp_saida="$(mktemp)"
  if ! bash "$_PERIMETRO_DIR/selar.sh" --check > "$tmp_saida" 2>&1; then
    echo "SUSPEITO (P-14): 'scripts/selar.sh --check' reprovou -- ao menos um chunk frio foi alterado depois de selado:"
    sed 's/^/  /' "$tmp_saida"
    ruim=1
  fi
  rm -f "$tmp_saida"
  return "$ruim"
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
  # Marca de migração presente (P-5 já rodou a checagem de permutação e
  # confirmou: nenhum byte de entrada mudou, só a posição física) -- um
  # commit de reordenação faz `git diff` enxergar praticamente o arquivo
  # inteiro como "+" (a posição mudou, o texto não), e P-7 rescanearia
  # citações antigas já grandfathered como se fossem novas (foi assim que
  # a citação de (162) a "(101 - ...)", já tratada como não-issue no
  # comentário acima, voltou a disparar SUSPEITO testando MEMÓRIAS (271)).
  # Pular aqui não abre brecha: a garantia real é a permutação byte-exata
  # do P-5, mais forte que P-7 -- se nenhum byte é novo, não há citação
  # nova pra checar.
  # Pula só quando o P-5 REALMENTE tomou o ramo de permutação nesta corrida
  # (P5_RAMO, setado por p5_append_only, que roda antes de P-7 no main).
  # A versão anterior perguntava por _p5_migracao_pendente -- a MARCA no
  # disco, não o ramo tomado. Como a marca vive em propostas/aplicadas/ e
  # esse diretório nunca é limpo por desenho, a marca de 06/09/2026 deixou
  # o P-7 em SKIP permanente: medido em 09/09/2026, "veredito: SKIP" com o
  # P-5 tendo passado pelo ramo ORDINÁRIO (havia bytes novos, e a mensagem
  # impressa afirmava o contrário). Toda citação nova entrou sem checagem
  # nesse intervalo. O controle em si estava íntegro -- testado contra
  # positivo e negativo conhecidos: citação real -> passa, citação
  # fabricada -> pega. Era só o portão de entrada que estava travado aberto.
  # Duas condições, não uma: o P-5 foi pela permutação E a permutação não
  # trouxe entrada nova. A segunda metade veio depois (mesma data), quando a
  # suíte mostrou que permutação com entrada nova existe e é comum -- ver o
  # comentário em p5_append_only.
  if [ "${P5_RAMO:-ordinario}" = "permutacao" ] && [ "${P5_ENTRADAS_NOVAS:-0}" -eq 0 ]; then
    echo "P-7: P-5 tomou o ramo de PERMUTAÇÃO e nenhuma entrada nova veio junto -- pulado (nada a citar que já não estivesse no canon)."
    PERIMETRO_ESTADO="SKIP"
    return 0
  fi
  local tmp_novo tmp_diff tmp_combinado codigo f
  tmp_novo="$(mktemp)"
  tmp_diff="$(mktemp)"
  tmp_combinado="$(mktemp)"
  if ! git show :MEMÓRIAS.md > "$tmp_novo" 2>/dev/null; then
    cat MEMÓRIAS.md > "$tmp_novo" 2>/dev/null
  fi
  # Desde a "MEMÓRIAS por período" (Fase 4): quente (MEMÓRIAS.md) só tem
  # as entradas recentes -- uma citação nova pode apontar pra uma entrada
  # que já migrou pra morno ou foi congelada em frio. Sem isto, P-7
  # reprovaria como "não existe" toda citação a história relocada -- falso
  # positivo, não achado real. O universo de busca junta as três camadas;
  # o DIFF checado continua sendo só o que entrou em quente (só lá se
  # escreve entrada nova).
  cat "$tmp_novo" > "$tmp_combinado"
  if git show :MEMORIAS-MORNO.md > /dev/null 2>&1; then
    git show :MEMORIAS-MORNO.md >> "$tmp_combinado"
  elif [ -f MEMORIAS-MORNO.md ]; then
    cat MEMORIAS-MORNO.md >> "$tmp_combinado"
  fi
  for f in MEMORIAS-FRIO-*.md; do
    [ -e "$f" ] || continue
    cat "$f" >> "$tmp_combinado"
  done
  git diff --cached -U0 -- MEMÓRIAS.md 2>/dev/null | grep -E '^\+' | grep -vE '^\+\+\+' | sed 's/^\+//' > "$tmp_diff"
  checar_citacao "$tmp_diff" "$tmp_combinado"
  codigo=$?
  rm -f "$tmp_novo" "$tmp_diff" "$tmp_combinado"
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
#   ONDE_ESTAMOS.md, INDICE_MEMORIAS.md, .hidrata.md (gerado)
# Motivo da linha: registro errado se corrige com entrada nova -- é pra
# isso que append-only existe. Comportamento errado, não.
#
# ACHADO 04/09/2026 (Camada C, auditoria dos pareceres gpt-5.6-terra +
# Qwen): testado AO VIVO -- sujar redesign/router/seth_escriba.py, `git add`,
# rodar este script, P-8 respondia "OK", sem SUSPEITO nem FALHA. O padrão
# abaixo nunca cobriu redesign/router/*.py (gateway, sanitizador, o único
# caminho de escrita da Seth), redesign/mcp/*.py, redesign/librechat/*.mjs
# nem redesign/systemd/* -- exatamente o código que faz a sanitização de
# segredo, o portão de hidratação e a trava de append-only. Uma sessão
# comprometida (ou um bug) podia reescrever qualquer um deles e commitar sem
# proposta nem APROVADO-. Ampliado abaixo; teste de regressão fica em
# propostas/aplicadas/ (o par .diff/APROVADO- que aplicou esta mudança).
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
    REGRAS.md|PROJETO.md|scripts/*|.githooks/*|config/*) return 0 ;;
    # A raiz de confiança da aprovação assinada (MEMÓRIAS (366)): trocá-la
    # é mudança de comportamento tanto quanto trocar um script. A
    # verificação em _p8_assinatura_ok usa a versão de HEAD, nunca a
    # working-tree -- uma troca staged não autoaprova a própria troca.
    propostas/.allowed_signers) return 0 ;;
    redesign/router/*|redesign/mcp/*|redesign/librechat/*.mjs|redesign/librechat/*.yaml|redesign/systemd/*) return 0 ;;
    # Lacuna achada em (340)/(341), fechada 06/09/2026: redesign/grafo/* (nó real
    # do loop de governança) e redesign/librechat/*.yml (docker-compose, só .yaml
    # estava coberto) mudavam comportamento sem quarentena. *.py/*.sh cobre
    # subpasta também (case casa "/"); *.md/*.gbnf ficam de fora de propósito --
    # varredura real mostrou 17 arquivos afetados, nenhum com aprovação prévia,
    # nenhum trava retroativo. Autorização do Humano, texto explícito.
    redesign/grafo/*.py|redesign/grafo/*.sh|redesign/librechat/*.yml) return 0 ;;
    # Buracos medidos em 09/09/2026, mesma classe do achado de 04/09 que
    # trouxe redesign/router/* pra cá -- código de controle que ficou de fora:
    #   redesign/obsidian/*.py  ro_proxy.py É o serviço que força read-only
    #                           sobre o vault (do_PUT/do_PATCH/do_DELETE ->
    #                           403) e injeta o bearer do Obsidian. Trocá-lo
    #                           abre escrita no vault sem aprovação nenhuma.
    #   SELOS.txt               raiz de confiança do P-14. Sem isto, apagar
    #                           uma linha do SELOS + reescrever o chunk frio
    #                           correspondente, no MESMO commit, passa: as
    #                           duas pernas do P-14 iteram o arquivo mutilado
    #                           e o chunk simplesmente some do relatório.
    #                           (O outro lado deste conserto está no próprio
    #                           p14_frio_imutavel, que agora lê HEAD:SELOS.txt.)
    #   .gitignore              é a PRIMEIRA linha de defesa que o P-11 cita
    #                           no próprio comentário -- editá-la para
    #                           destravar um silo não exigia aprovação.
    #   models/manifest.json    lista de recursos que o P-12 usa como régua de
    #                           backup; mexer nela muda o que "estar coberto"
    #                           significa.
    redesign/obsidian/*.py|SELOS.txt|.gitignore|models/manifest.json) return 0 ;;
    *) return 1 ;;
  esac
}

_p8_assinatura_ok() {
  # Assinatura ssh de propostas/APROVADO-<nome> sobre o .diff (desde
  # MEMÓRIAS (366)). Sem propostas/.allowed_signers no repo: assinatura
  # NÃO exigida -- modo compat da janela em que o par de chaves ainda
  # não foi gerado. Com .allowed_signers presente: exige bloco
  # `BEGIN SSH SIGNATURE` válido, principal `agata-humano`, namespace
  # `agata-aprovacao-p8`, mensagem = "<sha256 do .diff>  <nome>".
  # A mensagem carrega o hash do .diff -> editar o .diff depois de
  # assinado quebra a verificação. Verificar não precisa da passphrase;
  # só assinar (scripts/aprovar.sh, mão do Humano) precisa.
  local aprovado="$1" diff_abs="$2" nome="$3"
  local signers signers_tmp="" sig="" rc=1

  # Raiz de confiança = a versão JÁ COMMITADA de propostas/.allowed_signers
  # (HEAD:), nunca a working-tree -- senão uma troca de .allowed_signers
  # staged no mesmo commit poderia autoaprovar a própria troca. Rotação de
  # chave: assina-se o .diff da rotação com a chave ATUAL (a de HEAD), que
  # é o que esta verificação usa. Primeiro commit que introduziu
  # .allowed_signers não tinha HEAD: -> caía no working-tree (bootstrap).
  if git cat-file -e HEAD:propostas/.allowed_signers 2>/dev/null; then
    signers_tmp="$(mktemp)"
    git show HEAD:propostas/.allowed_signers > "$signers_tmp" 2>/dev/null
    signers="$signers_tmp"
  elif [ -f "$(pwd)/propostas/.allowed_signers" ]; then
    signers="$(pwd)/propostas/.allowed_signers"
  else
    return 0   # nem HEAD: nem working-tree -> modo compat (par de chaves ainda não existe)
  fi

  local dsha msg
  dsha="$(sha256sum "$diff_abs" | awk '{print $1}')"
  msg="$(printf '%s  %s' "$dsha" "$nome")"

  if ! command -v ssh-keygen >/dev/null 2>&1; then
    echo "P-8: ssh-keygen ausente -- não dá pra verificar a assinatura de $aprovado"
  elif ! grep -qxE "diff-sha256: $dsha" "$aprovado" 2>/dev/null; then
    echo "P-8: $aprovado -- linha 'diff-sha256:' ausente ou diferente do .diff atual (diff editado depois de assinado?)"
  else
    sig="$(mktemp)"
    awk '/-----BEGIN SSH SIGNATURE-----/,/-----END SSH SIGNATURE-----/' "$aprovado" > "$sig"
    if ! [ -s "$sig" ]; then
      echo "P-8: $aprovado sem bloco de assinatura ssh -- gere com scripts/aprovar.sh (PROJETO.md, \"Quarentena estrutural\")"
    elif printf '%s' "$msg" | ssh-keygen -Y verify -f "$signers" -I agata-humano \
           -n agata-aprovacao-p8 -s "$sig" >/dev/null 2>&1; then
      rc=0
    else
      echo "P-8: assinatura inválida em $aprovado (chave não confere com a raiz de confiança em HEAD:propostas/.allowed_signers, ou mensagem adulterada)"
    fi
  fi

  [ -n "$sig" ] && rm -f "$sig"
  [ -n "$signers_tmp" ] && rm -f "$signers_tmp"
  return "$rc"
}

_p8_arquivo_aprovado() {
  # Conserto de 22/08/2026 (achado testando `ab1-projeto.diff`, ver
  # MEMÓRIAS -- "aprovado" deixava de expirar: qualquer arquivo já
  # citado no cabeçalho de QUALQUER .diff aprovado, alguma vez na
  # história, ficava isento de P-8 pra sempre, porque `propostas/
  # aplicadas/` nunca é limpo (é o registro histórico, por desenho) e a
  # checagem antiga só olhava PATH, nunca CONTEÚDO. Confirmado com uma
  # edição trivial e sem relação nenhuma passando pela quarentena.
  #
  # Novo critério: "aprovado" só conta se aplicar o .diff candidato à
  # versão HEAD (pai) deste arquivo reproduz, byte a byte (hash do
  # blob), o que está staged agora. Path não decide mais nada sozinho
  # -- só entra na lista de candidatos a testar. Um .diff antigo, já
  # consumido, só vai bater essa checagem se o arquivo staged agora for
  # EXATAMENTE o resultado daquela mudança antiga -- o que não acontece
  # numa edição nova e diferente, mesmo no mesmo caminho.
  local f="$1" staged_blob diretorio aprovado nome diff_path
  local tmp resultado_blob diff_abs repo_raiz eh_delecao=0

  # --verify --quiet: exige UM objeto válido e sai != 0 SEM ecoar o argumento
  # quando não há (git rev-parse "cru" ecoa o arg no stdout e sai 128 -- isso
  # enchia $staged_blob com lixo e pulava o ramo de deleção).
  if ! staged_blob="$(git rev-parse --verify --quiet ":$f" 2>/dev/null)" \
     || [ -z "$staged_blob" ]; then
    # Sem blob staged. Ou o arquivo saiu do commit (P-8 não o checa), ou
    # está staged como DELEÇÃO -- e P-8 tem que poder aprovar deleção de
    # arquivo de comportamento igual aprova modificação: por um .diff
    # ASSINADO cujo hunk pra este path seja uma deleção total. Antes,
    # `|| return 1` aqui bloqueava TODA deleção sem caminho de aprovação
    # (achado em MEMÓRIAS (403); conserto autorizado em (407) com 2a
    # opinião do Conselho Remoto). Renomear = git vê delete(path velho) +
    # add(path novo) -- mas isso só é verdade com `--no-renames`. Sem ele, a
    # detecção de rename do git (LIGADA por padrão) colapsa os dois lados
    # num único R e mostra APENAS o path novo: o lado "delete" simplesmente
    # não aparece, e este ramo nunca dispara.
    # MEDIDO 09/09/2026 (vermelho/verde, clone descartável): editar
    # redesign/router/sanitizar.py no lugar -> SUSPEITO (P-8), correto;
    # `git mv redesign/router/sanitizar.py extras/` -> P-8 SILENCIOSO, e o
    # sanitizador (único ponto que tira segredo do payload antes de sair pra
    # provedor externo) saía do caminho vivo sem nenhum APROVADO-. Qualquer
    # arquivo de comportamento podia deixar a quarentena por renomeação.
    # Por isso `--no-renames` aqui E em p8_quarentena -- os dois têm que
    # enxergar o mesmo conjunto de paths, senão o furo volta por um lado só.
    if git -c core.quotepath=false diff --cached --no-renames --name-only --diff-filter=D 2>/dev/null | grep -qxF -- "$f"; then
      eh_delecao=1
    else
      return 1
    fi
  fi
  repo_raiz="$(pwd)"

  for diretorio in propostas propostas/aplicadas; do
    [ -d "$diretorio" ] || continue
    for aprovado in "$diretorio"/APROVADO-*; do
      [ -e "$aprovado" ] || continue
      nome="$(basename "$aprovado")"
      nome="${nome#APROVADO-}"
      diff_path="$diretorio/${nome}.diff"
      [ -f "$diff_path" ] || continue
      # Filtro barato antes do caro: só tenta aplicar diffs que sequer
      # mencionam este caminho no cabeçalho.
      grep -qE "^(\+\+\+ b/|--- a/)$(printf '%s' "$f" | sed 's/[.[\*^$/]/\\&/g')\$" "$diff_path" 2>/dev/null || continue

      diff_abs="$repo_raiz/$diff_path"
      tmp="$(mktemp -d)" || continue
      mkdir -p "$tmp/$(dirname "$f")"
      # Conserto de 23/08/2026 (achado testando `harness-a1-trace.diff`,
      # arquivo NOVO): criar um placeholder vazio aqui fazia `git apply`
      # recusar diffs de "novo arquivo" (`--- /dev/null`) com "already
      # exists in working directory" -- esse tipo de diff exige que o
      # caminho NÃO exista pra aplicar. Não criar nada quando o arquivo
      # não existe em HEAD deixa o próprio `git apply` criar o arquivo,
      # igual faria num `git apply` real contra o repositório.
      if git cat-file -e "HEAD:$f" 2>/dev/null; then
        git show "HEAD:$f" > "$tmp/$f" 2>/dev/null
      fi

      if (cd "$tmp" && git apply --include="$f" "$diff_abs") >/dev/null 2>&1; then
        if [ "$eh_delecao" -eq 1 ]; then
          # Aplicar o .diff a HEAD:$f fez o arquivo SUMIR == a deleção
          # staged. `git apply` já validou o CONTEÚDO do hunk (as linhas
          # `-` da deleção têm que bater com HEAD:$f, senão recusa) --
          # não basta o cabeçalho citar o path.
          if [ ! -e "$tmp/$f" ] && _p8_assinatura_ok "$aprovado" "$diff_abs" "$nome"; then
            rm -rf "$tmp"
            return 0
          fi
        else
          resultado_blob="$(git hash-object "$tmp/$f" 2>/dev/null)"
          if [ "$resultado_blob" = "$staged_blob" ] && _p8_assinatura_ok "$aprovado" "$diff_abs" "$nome"; then
            rm -rf "$tmp"
            return 0
          fi
        fi
      fi
      rm -rf "$tmp"
    done
  done
  return 1
}

p8_quarentena() {
  local staged f ruim=0
  # `--no-renames` é load-bearing, não cosmético: sem ele um rename aparece
  # só com o path NOVO, e mover um arquivo de comportamento pra fora dos
  # padrões de _p8_eh_comportamento tira ele da quarentena sem APROVADO-
  # nenhum (bypass medido em 09/09/2026 -- ver o comentário longo em
  # _p8_arquivo_aprovado). Com ele, os dois lados do rename entram na
  # checagem, e os dois hunks precisam estar no MESMO .diff assinado.
  staged="$(git -c core.quotepath=false diff --cached --no-renames --name-only)"
  [ -z "$staged" ] && return 0
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if _p8_eh_comportamento "$f"; then
      if ! _p8_arquivo_aprovado "$f"; then
        echo "SUSPEITO (P-8): '$f' muda comportamento e está staged sem propostas/APROVADO-<nome> correspondente cujo diff, aplicado ao HEAD deste arquivo, reproduza exatamente o conteúdo staged (o .diff em propostas/ precisa citar este caminho nos cabeçalhos E bater byte a byte). Crie a proposta, peça aprovação do Humano (propostas/README.md), ou tire este arquivo do commit."
        ruim=1
      fi
    fi
  done <<< "$staged"
  return "$ruim"
}

# --- P-11 ----------------------------------------------------------------
# Silos por modelo (.hidrata-<modelo>.md) nunca entram no canon. Vêm do
# hook gerar-hidratacao.sh, um por modelo-alvo, e
# podem conter bloco MOD sensível (MOD de outra família, dado privado) num
# repositório PÚBLICO. A defesa de primeira linha é o `.gitignore`
# (`.hidrata-*.md`) + o `git add` de nomes literais no pre-commit; P-11 é
# o backstop pro caso que nenhum dos dois cobre: `git add -f` manual.
# Achado da cadeia de auditoria de 3.1 (Camada C, 31/08/2026): `.gitignore`
# sozinho não é garantia -- `-f` fura, é comportamento padrão do git.
# Só `.hidrata.md` (o comum, sem bloco MOD que declare `modelo-alvo:`) é
# artefato público. FALHA o commit -- mesma severidade de P-8.
# Fonte: REGRAS.md, "Princípios" (Segurança) · REGRAS.md, "O Conselho"
# item 3 · PROJETO.md, "Memória e hidratação" (silos Fase 2).
_p11_eh_silo() {
  # `.hidrata-<algo>.md` casa; `.hidrata.md` (o comum, versionado) NÃO --
  # não há `-` depois de `.hidrata`.
  case "$1" in
    .hidrata-*.md) return 0 ;;
    *) return 1 ;;
  esac
}

_p11_conteudo_de_silo() {
  # Segunda camada, por CONTEÚDO. _p11_eh_silo olha só o NOME, e nome se
  # troca: `cp .hidrata-seth.md notas.md && git add notas.md` nunca teve
  # nome de silo, então nem a regra de nome nem o `--no-renames` abaixo o
  # pegam -- não houve rename, houve cópia. MEDIDO 09/09/2026: passava
  # limpo, com `modelo-alvo:` e MOD no corpo, pro repositório PÚBLICO.
  # Marca de MOD: o cabeçalho `modelo-alvo:` no início da linha,
  # obrigatório em bloco MOD (REGRAS, "O Conselho" item 3).
  # Falsos positivos medidos no repo inteiro: 1 -- o chunk frio
  # MEMORIAS-FRIO-2026-09-06-com-migrado.md, que REGISTRA o formato em vez
  # de carregar MOD vivo. Por isso a lista de exclusão: história e canon,
  # onde citar o cabeçalho é o trabalho normal do arquivo. Silo de verdade
  # nunca tem nome dessa lista -- se tiver, P-5/P-14 já brigam por outro
  # motivo. Esta camada é o que salvou P-14 do mesmo furo (selar.sh
  # --check pegou o que a listagem staged não viu).
  case "$1" in
    MEMÓRIAS.md|MEMORIAS-MORNO.md|MEMORIAS-FRIO-*.md|REGRAS.md|PROJETO.md|.hidrata.md|INDICE_MEMORIAS*.md) return 1 ;;
  esac
  git show ":$1" 2>/dev/null | grep -qaE '^modelo-alvo:[[:space:]]*[A-Za-z]'
}

p11_silos_nao_versionados() {
  local staged f ruim=0
  # `--no-renames` pelo mesmo motivo de p8_quarentena: sem ele, `git mv`
  # de um silo staged pra um nome inocente apaga o path de silo da
  # listagem e P-11 dá OK. MEDIDO 09/09/2026 (vermelho/verde): silo com
  # nome de silo -> SUSPEITO; o MESMO arquivo renomeado -> "veredito: OK",
  # com `modelo-alvo:` e MOD privado indo pro repositório PÚBLICO.
  staged="$(git -c core.quotepath=false diff --cached --no-renames --name-only)"
  [ -z "$staged" ] && return 0
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if _p11_eh_silo "$f"; then
      echo "SUSPEITO (P-11): '$f' é um silo por modelo e está staged. Por que importa: silo pode conter bloco MOD sensível (MOD de outra família) e o repositório é público -- só '.hidrata.md' (o comum, sem MOD com modelo-alvo) entra no canon. O que fazer: 'git restore --staged $f' -- o hook gerar-hidratacao.sh regenera o silo na árvore da Máquina quando preciso; se veio de 'git add -f', não force silo pro commit."
      ruim=1
    elif _p11_conteudo_de_silo "$f"; then
      echo "SUSPEITO (P-11): '$f' não tem nome de silo, mas o conteúdo staged tem cabeçalho 'modelo-alvo:' -- é bloco MOD. Por que importa: MOD é privado por padrão (REGRAS, 'O Conselho' item 2/3) e este repositório é público; renomear ou copiar um silo não o torna publicável. O que fazer: 'git restore --staged $f'. Se for texto sobre o formato (não MOD vivo), o lugar é MEMÓRIAS/REGRAS, que estão fora desta checagem."
      ruim=1
    fi
  done <<< "$staged"
  return "$ruim"
}

# --- P-9 -----------------------------------------------------------------
# Serviço declarado no PROJETO que morreu em silêncio (item 5, documento
# do Humano 20/08/2026, MEMÓRIAS (221)). agata-consolidacao.service
# ficou falhando desde data desconhecida (`hermes: comando não
# encontrado`) e nenhuma das oito checagens anteriores percebeu --
# PROJETO.md listava a unidade como se funcionasse. Controle que não
# avisa quando falha é pior que controle nenhum.
#
# Escopo fechado, mesma doutrina de P-3/P-4: unidades e containers
# citados em PROJETO.md, "Serviços (boot)", enumerados à mão -- atualizar
# esta lista quando aquela linha do PROJETO mudar. AVISA, nunca falha --
# serviço caído não é motivo pra travar a escrita do canon (mesma lógica
# de P-6).
#
# `agata-consolidacao.service` (o oneshot em si, não o timer) fica de
# propósito FORA da lista: seu estado de repouso normal depois de rodar
# com sucesso é "inactive", não "failed" -- checar isso soaria falso
# alarme a cada execução normal. O que importa pra "vai rodar de novo" é
# o TIMER que dispara ele, não o resultado da última corrida.
P9_UNIDADES_SISTEMA=("ollama.service")
# Fase 8 (redesenho): hermes-gateway saiu do loop (P8-05). O executor agora e' o
# grafo + OmniRoute -- os membros do agata.target sao os servicos criticos.
# seth-gateway/seth-escriba adicionados 04/09/2026 (Camada C): rodam agora
# (LibreChat/Seth em uso desde (313)), mas não estavam na lista -- P-9 nunca
# apitaria se caíssem, embora sejam a hidratação e o único caminho de escrita
# dela. Achado, não teórico: confirmado com `ss -ltnp` que os dois escutam.
P9_UNIDADES_USUARIO=("agata-consolidacao.timer" "agata-pesquisa-modelos.timer" "omniroute.service" "omniroute-sanitizer.service" "openvino-whisper.service" "openvino-embeddings.service" "obsidian-ro-proxy.service" "seth-gateway.service" "seth-escriba.service" "piper-tts.service")
P9_CONTAINERS_DOCKER=("librechat" "librechat-mongodb" "librechat-meilisearch" "kokoro-tts")

# --- P-15 --------------------------------------------------------------------
# Saúde do roster do Conselho Remoto (MEMÓRIAS (374)). scripts/conselho_remoto.py
# escreve `memoria/missoes/conselho-remoto/sucessos.log`: uma linha
# `<epoch>\t<modelo>\t<familia>` por chamada bem-sucedida. AVISO (nunca FALHA)
# se menos de 2 FAMILIAS distintas responderam nas ultimas 24h -- sinal de que a
# camada externa esta degradada e o sistema pode estar andando com fallback
# local. Nunca falha o commit (a camada local basta pra operar).
p15_roster_remoto() {
  local log="$_PERIMETRO_DIR/../memoria/missoes/conselho-remoto/sucessos.log"
  if [ ! -f "$log" ]; then
    echo "sem historico de sucesso do Conselho Remoto ainda -- nada a avaliar (nao e problema)"
    return 0
  fi
  local corte fams
  corte=$(( $(date +%s) - 86400 ))
  fams=$(awk -F'\t' -v c="$corte" 'NF>=3 && ($1 + 0) >= c {print $3}' "$log" | sort -u | grep -c .)
  if [ "${fams:-0}" -lt 2 ]; then
    echo "AVISO (P-15): so ${fams:-0} familia(s) do roster remoto teve(tiveram) sucesso nas ultimas 24h. A segunda opiniao externa pode estar degradada -- o sistema pode estar andando com fallback local. Nao falha o commit; olhe scripts/conselho_remoto.py e o OmniRoute."
  else
    echo "roster remoto OK -- $fams familias com sucesso nas ultimas 24h"
  fi
  return 0
}

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

p10_vault_derivado() {
  # P-10 (MEMÓRIAS (293)): memoria/obsidian/ é o único derivado gerado FORA do
  # commit (post-commit, gitignorado) -- .hidrata.md e os índices entram no
  # commit pelo pre-commit e não têm como divergir. Aqui: regenera o vault a
  # partir do conteúdo de HEAD num sandbox e confere byte a byte contra o disco.
  # HEAD dos DOIS lados -- comparar contra o disco staged reprovaria todo commit
  # que toca canon (o vault no disco foi gerado do commit anterior).
  local vault="memoria/obsidian"

  # Bootstrap: se o próprio gerador muda neste commit, HEAD tem a versão antiga
  # -- a conferência não faz sentido, adia pro próximo commit.
  if ! git diff --cached --quiet -- scripts/gerar_obsidian.py 2>/dev/null; then
    echo "P-10: scripts/gerar_obsidian.py muda neste commit -- conferência adiada pro próximo."
    PERIMETRO_ESTADO="SKIP"; return 0
  fi
  if [ ! -d "$vault" ]; then
    echo "P-10: $vault/ ainda não existe (clone fresco?) -- o post-commit cria no 1º commit."
    PERIMETRO_ESTADO="SKIP"; return 0
  fi

  local tmp sha data hreal hesp missoes_md
  tmp="$(mktemp -d)" || { echo "P-10: mktemp falhou -- pulado."; PERIMETRO_ESTADO="SKIP"; return 0; }
  sha="$(git rev-parse HEAD)"
  data="$(git log -1 --format=%cI)"
  # memoria/missoes/ é gitignorado do repo principal -- `git archive HEAD`
  # nunca o inclui, então a sandbox abaixo não o vê. Calculado aqui, no repo
  # real (que o tem), e repassado por env -- mesmo padrão de AGATA_CANON_SHA.
  if [ -d memoria/missoes ]; then
    missoes_md="$(git -c core.quotepath=false -C memoria/missoes ls-files '*.md' 2>/dev/null)"
  else
    missoes_md=""
  fi
  if ! git archive HEAD | tar -x -C "$tmp" 2>/dev/null; then
    rm -rf "$tmp"
    echo "SUSPEITO (P-10): git archive HEAD falhou -- não dá pra conferir o vault."
    return 1
  fi
  if ! ( cd "$tmp" && AGATA_CANON_SHA="$sha" AGATA_CANON_DATA="$data" \
         AGATA_MISSOES_MD="$missoes_md" \
         python3 scripts/gerar_obsidian.py >/dev/null 2>&1 ); then
    rm -rf "$tmp"
    echo "SUSPEITO (P-10): gerar_obsidian.py falhou ao rodar sobre HEAD -- gerador quebrado."
    return 1
  fi
  hreal="$( cd "$vault" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum )"
  hesp="$(  cd "$tmp/$vault" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum )"
  rm -rf "$tmp"
  if [ "$hreal" != "$hesp" ]; then
    echo "SUSPEITO (P-10): $vault/ não bate com o que gerar_obsidian.py produz de HEAD."
    echo "  o que fazer: rode 'python3 scripts/gerar_obsidian.py' -- e se você editou uma nota à mão, desfaça: correção é entrada nova em MEMÓRIAS, não edição do vault."
    echo "  fonte: MEMÓRIAS (293)"
    return 1
  fi
  return 0
}

# Imprime o veredito de uma checagem e soma no placar -- único ponto que
# decide OK vs SKIP vs PARCIAL vs FALHOU, pra nenhuma chamada em main()
# arriscar imprimir "OK" por engano quando a checagem só pulou (MEMÓRIAS
# (193)). $1 = exit code da checagem; usa PERIMETRO_ESTADO, que a própria
# checagem deixa setado quando não é um OK de verdade.
# --- P-16 ----------------------------------------------------------------
# "Quem muda um controle roda os testes daquele controle." (MEMÓRIAS (421))
#
# Motivo, medido e não teórico: até 09/09/2026 NADA testava os controles. O
# P-7 ficou morto 79 commits; P-8 e P-11 eram cegos a renomeação desde
# sempre. Os quatro furos da (419) foram achados porque alguém sentou pra
# procurar -- não porque o sistema avisou. A (419) consertou os furos; sem
# este controle, o próximo furo esperaria a próxima auditoria manual.
#
# Escopo estreito de propósito: só dispara quando um arquivo de CONTROLE está
# staged. Commit que não toca controle não paga nada. Quando dispara, custa
# ~1-2 min (a suíte roda o perímetro inteiro uma vez por caso, num clone).
# Esse é o commit em que vale esperar.
#
# FALHA-class: mesma severidade de P-8. Mudar o controle sem que os testes
# dele passem é a definição de regressão silenciosa.
#
# Prova de que não é decorativo: na primeira corrida, a suíte reprovou o
# próprio conserto que a (419) tinha acabado de fazer -- o P-7 pulava commits
# de permutação que traziam entrada nova. Consertado antes de entrar no canon.
P16_ARQUIVOS_DE_CONTROLE='^(scripts/(perimetro|varredura_segredo|checar_citacao|checar_discordancia|selar|testar_perimetro|verificar_cabecalho|verificar_migracao_[a-z]+)\.(sh|py)|\.githooks/.*)$'

p16_testes_dos_controles() {
  # Guarda de recursão: a suíte roda o perímetro dentro do clone dela.
  if [ -n "${AGATA_TESTE_PERIMETRO:-}" ]; then
    echo "P-16: rodando DENTRO da suíte -- pulado (senão recursa infinitamente)."
    PERIMETRO_ESTADO="SKIP"; return 0
  fi
  local staged tocados
  staged="$(git -c core.quotepath=false diff --cached --no-renames --name-only 2>/dev/null)"
  tocados="$(echo "$staged" | grep -E "$P16_ARQUIVOS_DE_CONTROLE" || true)"
  if [ -z "$tocados" ]; then
    echo "P-16: nenhum arquivo de controle staged -- suíte não precisa rodar."
    PERIMETRO_ESTADO="SKIP"; return 0
  fi
  if [ ! -f "$_PERIMETRO_DIR/testar_perimetro.sh" ]; then
    echo "SUSPEITO (P-16): arquivo de controle staged ($(echo "$tocados" | tr '\n' ' ')) mas scripts/testar_perimetro.sh não existe -- o controle mudou sem que exista teste dele."
    return 1
  fi
  # Cobertura ANTES de rodar: todo controle do main() precisa ter caso na
  # suíte OU motivo escrito na tabela SEM_TESTE dela. Acrescentado em (422)
  # porque a suíte nasceu cobrindo 5 de 16 e os outros 11 não estavam
  # isentos -- estavam esquecidos, e ninguém sabia dizer quais. É a mesma
  # doutrina do resto: a diferença entre "não dá pra testar" e "ninguém
  # testou" tem de estar escrita, senão vira o P-7 outra vez.
  local declarados testados descobertos
  declarados="$(grep -oE 'cabecalho "P-[0-9]+"' "$_PERIMETRO_DIR/perimetro.sh" | grep -oE 'P-[0-9]+' | sort -u)"
  testados="$( { grep -oE '_caso P-[0-9]+' "$_PERIMETRO_DIR/testar_perimetro.sh" | grep -oE 'P-[0-9]+'
                 grep -oE '^\s*\[P-[0-9]+\]=' "$_PERIMETRO_DIR/testar_perimetro.sh" | grep -oE 'P-[0-9]+'; } | sort -u)"
  descobertos="$(comm -23 <(echo "$declarados") <(echo "$testados") | tr '\n' ' ')"
  if [ -n "${descobertos// /}" ]; then
    echo "SUSPEITO (P-16): controle(s) sem caso na suíte E sem motivo escrito: $descobertos"
    echo "  O que fazer: ou escreva um caso em scripts/testar_perimetro.sh, ou declare o motivo na tabela SEM_TESTE de lá. Controle sem teste e sem justificativa é como o P-7 antes de (419) -- ninguém sabe se está dispensado ou esquecido."
    return 1
  fi
  echo "P-16: controle staged ($(echo "$tocados" | tr '\n' ' ')) -- rodando a suíte de regressão (pode levar 1-2 min)..."
  local saida codigo
  saida="$(AGATA_TESTE_PERIMETRO=1 bash "$_PERIMETRO_DIR/testar_perimetro.sh" 2>&1)"; codigo=$?
  if [ "$codigo" -eq 0 ]; then
    echo "$saida" | tail -1
    return 0
  fi
  echo "SUSPEITO (P-16): a suíte de regressão dos controles REPROVOU com um arquivo de controle staged. O que fazer: rode 'bash scripts/testar_perimetro.sh' e conserte antes de comitar -- um controle que perdeu cobertura não deve entrar no canon."
  echo "$saida" | sed 's/^/  /'
  return 1
}

# --- P-17 ----------------------------------------------------------------
# "Controle que pula sempre está desligado, não é dispensado." (MEMÓRIAS (422))
#
# A falha que este controle contém, medida: o P-7 ficou em SKIP por 79
# commits. Não quebrou, não deu erro, não avisou -- pulava educadamente,
# escrevendo na tela que não havia nada a conferir. Ninguém percebeu porque
# um SKIP é indistinguível de outro: normal na terça, normal na quarta,
# normal por três meses. O olho humano perde a série; o disco não.
#
# Mecanismo: cada corrida grava quem pulou. Um controle que pula N corridas
# SEGUIDAS deixa de ser rotina e vira AVISO com o número na cara -- "P-7:
# 79 corridas seguidas sem conferir nada" é impossível de ler como normal.
# Sucesso (qualquer veredito que não seja SKIP) zera a série daquele
# controle, então SKIP legítimo e ocasional nunca alarma.
#
# AVISA, nunca falha: pular pode ser correto (P-16 fora de commit de
# controle, P-7 numa migração real). O que não pode é pular em silêncio
# para sempre. Mesma doutrina de P-6/P-9 -- barulho, não bloqueio.
#
# Estado FORA do repositório (~/.cache/agata/): é telemetria de execução,
# não canon, e não deve sujar `git status` nem exigir entrada no .gitignore.
P17_SKIPS=""
P17_LIMITE=10
P17_ESTADO="${XDG_CACHE_HOME:-$HOME/.cache}/agata/perimetro-skip.tsv"

p17_skip_cronico() {
  [ -n "${AGATA_TESTE_PERIMETRO:-}" ] && { echo "P-17: dentro da suíte -- não contabiliza."; PERIMETRO_ESTADO="SKIP"; return 0; }
  mkdir -p "$(dirname "$P17_ESTADO")" 2>/dev/null || { echo "P-17: sem cache gravável -- série não acompanhada."; PERIMETRO_ESTADO="PARCIAL"; return 0; }
  touch "$P17_ESTADO" 2>/dev/null

  local todos ctrl serie novo="" alarmes=""
  todos="$(grep -oE 'cabecalho "P-[0-9]+"' "$_PERIMETRO_DIR/perimetro.sh" 2>/dev/null | grep -oE 'P-[0-9]+' | sort -u)"
  while IFS= read -r ctrl; do
    [ -z "$ctrl" ] && continue
    serie="$(awk -v c="$ctrl" '$1==c{print $2}' "$P17_ESTADO" 2>/dev/null | tail -1)"
    [ -z "$serie" ] && serie=0
    if printf '%s' " $P17_SKIPS" | grep -q " $ctrl "; then
      serie=$((serie + 1))
      [ "$serie" -ge "$P17_LIMITE" ] && alarmes="${alarmes}${ctrl}=${serie} "
    else
      serie=0
    fi
    novo="${novo}${ctrl}	${serie}
"
  done <<< "$todos"
  printf '%s' "$novo" > "$P17_ESTADO" 2>/dev/null

  if [ -n "$alarmes" ]; then
    echo "AVISO (P-17): controle(s) em SKIP por $P17_LIMITE ou mais corridas SEGUIDAS: $alarmes"
    echo "  Por que importa: foi exatamente assim que o P-7 ficou desligado por 79 commits -- pulando em silêncio, um SKIP igual ao anterior. Confira se o motivo do SKIP ainda é verdade; se for, o controle talvez precise mudar de forma, não continuar pulando."
    return 0
  fi
  if [ -n "$P17_SKIPS" ]; then
    echo "P-17: pularam nesta corrida ($P17_SKIPS) -- séries abaixo do limite de $P17_LIMITE."
  else
    echo "P-17: nenhum controle pulou nesta corrida."
  fi
  return 0
}

_perimetro_veredito() {
  local codigo="$1"
  if [ "$codigo" -ne 0 ]; then
    echo "veredito: FALHOU"
    FALHOU=1
    CONT_FALHA=$((CONT_FALHA + 1))
  elif [ "$PERIMETRO_ESTADO" = "SKIP" ]; then
    echo "veredito: SKIP"
    CONT_SKIP=$((CONT_SKIP + 1))
    P17_SKIPS="${P17_SKIPS}${PERIMETRO_CTRL:-?} "
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

  cabecalho "P-1" "Segredos só em ~/.config/agata/.env, fora do repo" "PROJETO, Segurança"
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

  cabecalho "P-11" "Silo por modelo (.hidrata-<modelo>.md) nunca entra no canon -- backstop do git add -f" "REGRAS, Princípios (Segurança) · REGRAS, O Conselho item 3 · PROJETO, Memória e hidratação"
  PERIMETRO_ESTADO=""
  p11_silos_nao_versionados; _perimetro_veredito "$?"
  echo

  cabecalho "P-10" "Vault derivado (memoria/obsidian/) confere com a fonte em HEAD" "MEMÓRIAS (293)"
  PERIMETRO_ESTADO=""
  p10_vault_derivado; _perimetro_veredito "$?"
  echo

  cabecalho "P-9" "Serviço declarado em PROJETO.md não pode morrer em silêncio" "PROJETO, Serviços (boot)"
  p9_servicos_declarados
  echo "veredito: AVISO SÓ (nunca falha)"
  CONT_OK=$((CONT_OK + 1))
  echo

  cabecalho "P-6" "Cópia da história fora desta máquina" "PROJETO, Riscos conhecidos"
  p6_backup_pendente
  echo "veredito: AVISO SÓ (nunca falha)"
  CONT_OK=$((CONT_OK + 1))
  echo

  cabecalho "P-12" "Todo recurso do manifesto com backup restic verificavel < N dias" "ROADMAP, Fase 7 -- redesign/fase7-hd/REGUA-P12.md"
  PERIMETRO_ESTADO=""
  p12_backup_verificavel; _perimetro_veredito "$?"
  echo

  cabecalho "P-13" "Sem discordância real entre modelos em 4 semanas -> provocar sintética, marcada como tal" "REGRAS, Regra 4, item 4"
  checar_discordancia
  echo "veredito: AVISO SÓ (nunca falha)"
  CONT_OK=$((CONT_OK + 1))
  echo

  cabecalho "P-14" "Chunk frio (MEMORIAS-FRIO-*.md), depois de selado, imutável" "MEMÓRIAS por período (Fase 4), MEMÓRIAS (357)"
  PERIMETRO_ESTADO=""
  p14_frio_imutavel; _perimetro_veredito "$?"
  echo

  cabecalho "P-15" "Saúde do roster do Conselho Remoto -- < 2 famílias com sucesso em 24h vira AVISO" "MEMÓRIAS (374); scripts/conselho_remoto.py"
  p15_roster_remoto
  echo "veredito: AVISO SÓ (nunca falha)"
  CONT_OK=$((CONT_OK + 1))
  echo

  cabecalho "P-16" "Quem muda um controle roda os testes daquele controle" "MEMÓRIAS (421); scripts/testar_perimetro.sh"
  PERIMETRO_ESTADO=""
  p16_testes_dos_controles; _perimetro_veredito "$?"
  echo

  cabecalho "P-17" "Controle que pula sempre está desligado, não é dispensado" "MEMÓRIAS (422); a morte silenciosa do P-7 em (419)"
  PERIMETRO_ESTADO=""
  p17_skip_cronico; _perimetro_veredito "$?"
  echo

  echo "=== RESULTADO GERAL: $([ "$FALHOU" -eq 0 ] && echo OK || echo FALHOU) -- ${CONT_OK} OK · ${CONT_SKIP} SKIP · ${CONT_PARCIAL} PARCIAL · ${CONT_FALHA} FALHA ==="
  return "$FALHOU"
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  main
  exit $?
fi
