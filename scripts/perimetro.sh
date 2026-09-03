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

# Âncora de append-only pelo topo, usada por P-5 (MEMÓRIAS (271)).
_P5_MARCADOR="<!-- ENTRADAS-NOVAS:AQUI"

# Mesmo padrão de propostas/APROVADO-<nome> (P-8): arquivo que o Humano
# cria pra autorizar, uso único, procurado em propostas/ e
# propostas/aplicadas/. Ecoa o caminho achado (não só 0/1) pro chamador
# poder citar qual marca disparou o ramo de permutação no aviso.
_p5_migracao_pendente() {
  local diretorio arq
  for diretorio in propostas propostas/aplicadas; do
    [ -d "$diretorio" ] || continue
    for arq in "$diretorio"/MIGRACAO-P5-*; do
      if [ -e "$arq" ]; then
        echo "$arq"
        return 0
      fi
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
# controle mais forte do sistema. Compara o MEMÓRIAS.md staged (o que vai
# virar o próximo commit) contra o MEMÓRIAS.md do commit anterior (HEAD)
# -- não contra memória do executor.
#
# Desde MEMÓRIAS (271), 26/08/2026: MEMÓRIAS.md cresce pelo TOPO do corpo
# (logo após o marcador ENTRADAS-NOVAS), não mais pelo fim físico --
# decisão do Humano, mudança estrutural documentada naquela entrada,
# portão das três perguntas cumprido. A checagem tem três ramos, nesta
# ordem de prioridade:
#   1. Marca de migração presente (propostas*/MIGRACAO-P5-<nome>) --
#      checagem de PERMUTAÇÃO via scripts/verificar_migracao_memorias.py:
#      mesmo conjunto de blocos byte-idênticos, só reordenados. Único uso
#      esperado: a própria migração de (271). Marca é de uso único, mesmo
#      padrão de risco aceito de P-8 (Humano cria o arquivo -- ameaça é
#      desatenção, não contorno deliberado).
#   2. HEAD já tem o marcador ENTRADAS-NOVAS -- formato novo em vigor:
#      corpo após o marcador tem que ser SUFIXO não-encolhido do novo.
#      Mesma força de garantia do sufixo original, direção invertida.
#   3. HEAD sem marcador e sem marca de migração -- formato antigo ainda
#      em vigor: checagem original, prefixo byte-exato (crescimento pelo
#      fim). É o ramo que roda em todo commit até a migração acontecer.
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
  local tmp_antigo tmp_novo codigo marca_migracao
  tmp_antigo="$(mktemp)"
  tmp_novo="$(mktemp)"
  if ! git show HEAD:MEMÓRIAS.md > "$tmp_antigo" 2>/dev/null; then
    rm -f "$tmp_antigo" "$tmp_novo"
    return 0
  fi
  if ! git show :MEMÓRIAS.md > "$tmp_novo" 2>/dev/null; then
    cat MEMÓRIAS.md > "$tmp_novo" 2>/dev/null
  fi

  marca_migracao="$(_p5_migracao_pendente)" || true
  if [ -n "$marca_migracao" ]; then
    echo "P-5: marca de migração '$marca_migracao' presente -- checagem de PERMUTAÇÃO (verificar_migracao_memorias.py), não de sufixo. Uso único, MEMÓRIAS (271)."
    if python3 "$_PERIMETRO_DIR/verificar_migracao_memorias.py" "$tmp_antigo" "$tmp_novo"; then
      codigo=0
    else
      codigo=1
    fi
    rm -f "$tmp_antigo" "$tmp_novo"
    return "$codigo"
  fi

  if grep -qF "$_P5_MARCADOR" "$tmp_antigo"; then
    python3 - "$tmp_antigo" "$tmp_novo" <<'PYEOF'
import sys
MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI".encode("utf-8")
with open(sys.argv[1], 'rb') as f:
    antigo = f.read()
with open(sys.argv[2], 'rb') as f:
    novo = f.read()
i_antigo = antigo.find(MARCADOR)
i_novo = novo.find(MARCADOR)
if i_antigo == -1:
    print("SUSPEITO (P-5): marcador ENTRADAS-NOVAS não achado no commit anterior apesar do grep externo achar -- inconsistência, restaure antes de comitar.")
    sys.exit(1)
if i_novo == -1:
    print("SUSPEITO (P-5, nunca se apaga história): marcador ENTRADAS-NOVAS existia no commit anterior e sumiu no staged -- não se apaga a âncora de append-only.")
    sys.exit(1)
fim_linha_antigo = antigo.find(b'\n', i_antigo) + 1
fim_linha_novo = novo.find(b'\n', i_novo) + 1
corpo_antigo = antigo[fim_linha_antigo:]
corpo_novo = novo[fim_linha_novo:]
if len(corpo_novo) < len(corpo_antigo):
    print(f"SUSPEITO (P-5, nunca se apaga história): corpo de MEMÓRIAS.md ENCOLHEU -- {len(corpo_antigo)} bytes no commit anterior, {len(corpo_novo)} agora. Alguma entrada foi removida. Restaure o arquivo antes de comitar.")
    sys.exit(1)
if not corpo_novo.endswith(corpo_antigo):
    print("SUSPEITO (P-5, nunca se apaga história): o conteúdo antigo não é mais um SUFIXO do novo -- uma entrada já registrada foi alterada, ou a entrada nova não entrou logo após o marcador. Restaure o arquivo antes de comitar.")
    sys.exit(1)
sys.exit(0)
PYEOF
    codigo=$?
  else
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
  fi
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
P12_REPO="${AGATA_RESTIC_REPO:-/run/media/$USER/AgataBkup01/restic-agata-local}"
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
  if _p5_migracao_pendente >/dev/null; then
    echo "P-7: marca de migração presente -- pulado (P-5 já provou, por permutação, que nenhum byte de entrada é novo nesta commit; nada a citar que já não estivesse no canon)."
    PERIMETRO_ESTADO="SKIP"
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
#   ONDE_ESTAMOS.md, INDICE_MEMORIAS.md, .hidrata.md (gerado)
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
    REGRAS.md|PROJETO.md|scripts/*|.githooks/*|config/*) return 0 ;;
    *) return 1 ;;
  esac
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
  local tmp resultado_blob diff_abs repo_raiz

  staged_blob="$(git rev-parse ":$f" 2>/dev/null)" || return 1
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
        resultado_blob="$(git hash-object "$tmp/$f" 2>/dev/null)"
        if [ "$resultado_blob" = "$staged_blob" ]; then
          rm -rf "$tmp"
          return 0
        fi
      fi
      rm -rf "$tmp"
    done
  done
  return 1
}

p8_quarentena() {
  local staged f ruim=0
  staged="$(git diff --cached --name-only)"
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
# podem conter bloco MOD sensível -- nonce TES-002 de 3.3 -- num
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

p11_silos_nao_versionados() {
  local staged f ruim=0
  staged="$(git diff --cached --name-only)"
  [ -z "$staged" ] && return 0
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if _p11_eh_silo "$f"; then
      echo "SUSPEITO (P-11): '$f' é um silo por modelo e está staged. Por que importa: silo pode conter bloco MOD sensível (nonce TES-002) e o repositório é público -- só '.hidrata.md' (o comum, sem MOD com modelo-alvo) entra no canon. O que fazer: 'git restore --staged $f' -- o hook gerar-hidratacao.sh regenera o silo na árvore da Máquina quando preciso; se veio de 'git add -f', não force silo pro commit."
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
P9_UNIDADES_USUARIO=("agata-consolidacao.timer" "omniroute.service" "omniroute-sanitizer.service" "openvino-whisper.service" "openvino-embeddings.service" "obsidian-ro-proxy.service")
P9_CONTAINERS_DOCKER=("open-webui" "kokoro-tts")

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

  local tmp sha data hreal hesp
  tmp="$(mktemp -d)" || { echo "P-10: mktemp falhou -- pulado."; PERIMETRO_ESTADO="SKIP"; return 0; }
  sha="$(git rev-parse HEAD)"
  data="$(git log -1 --format=%cI)"
  if ! git archive HEAD | tar -x -C "$tmp" 2>/dev/null; then
    rm -rf "$tmp"
    echo "SUSPEITO (P-10): git archive HEAD falhou -- não dá pra conferir o vault."
    return 1
  fi
  if ! ( cd "$tmp" && AGATA_CANON_SHA="$sha" AGATA_CANON_DATA="$data" \
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

  echo "=== RESULTADO GERAL: $([ "$FALHOU" -eq 0 ] && echo OK || echo FALHOU) -- ${CONT_OK} OK · ${CONT_SKIP} SKIP · ${CONT_PARCIAL} PARCIAL · ${CONT_FALHA} FALHA ==="
  return "$FALHOU"
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  main
  exit $?
fi
