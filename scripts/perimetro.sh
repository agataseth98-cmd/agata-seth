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

# Item 10 do plano de mitigacao da auditoria do Marcos (MEMORIAS (437)):
# cada controle abaixo morava inline neste arquivo -- extraido por
# corte-e-cola pra scripts/perimetro/, corpo identico, sem mudar contrato
# de saida nem logica. perimetro.sh vira runner: source + orquestracao.
source "$_PERIMETRO_DIR/perimetro/p03_publicacao.sh"
source "$_PERIMETRO_DIR/perimetro/p04_bind.sh"
source "$_PERIMETRO_DIR/perimetro/p05_append_only.sh"
source "$_PERIMETRO_DIR/perimetro/p06_backup_pendente.sh"
source "$_PERIMETRO_DIR/perimetro/p07_citacao.sh"
source "$_PERIMETRO_DIR/perimetro/p08_quarentena.sh"
source "$_PERIMETRO_DIR/perimetro/p09_servicos_declarados.sh"
source "$_PERIMETRO_DIR/perimetro/p10_vault_derivado.sh"
source "$_PERIMETRO_DIR/perimetro/p11_silos.sh"
source "$_PERIMETRO_DIR/perimetro/p12_backup_verificavel.sh"
source "$_PERIMETRO_DIR/perimetro/p14_frio_imutavel.sh"
source "$_PERIMETRO_DIR/perimetro/p15_roster_remoto.sh"
source "$_PERIMETRO_DIR/perimetro/p16_testes_dos_controles.sh"
source "$_PERIMETRO_DIR/perimetro/p17_skip_cronico.sh"
source "$_PERIMETRO_DIR/perimetro/p18_ancora_falha.sh"
source "$_PERIMETRO_DIR/perimetro/p19_citacao_arquivo.sh"

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


# --- P-6 -----------------------------------------------------------------
# "Cópia da história fora desta máquina" (PROJETO, Riscos conhecidos).
# AVISA, nunca falha -- o incidente real de hoje foi o marcador acumulando
# em silêncio por um dia inteiro de trabalho intenso, sem ninguém notar
# até alguém perguntar. Limiar escolhido nesta sessão, documentado aqui
# por não haver um número já declarado no canon: mais de 3 commits OU
# mais de 2 horas desde que o marcador apareceu, o que vier primeiro.
P6_MAX_COMMITS=3
P6_MAX_HORAS=2

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
P9_UNIDADES_USUARIO=("agata-consolidacao.timer" "agata-pesquisa-modelos.timer" "omniroute.service" "omniroute-sanitizer.service" "openvino-whisper.service" "openvino-embeddings.service" "obsidian-ro-proxy.service" "seth-gateway.service" "seth-escriba.service" "seth-verificador.service" "piper-tts.service")
P9_CONTAINERS_DOCKER=("librechat" "librechat-mongodb" "librechat-meilisearch" "kokoro-tts")




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
  cd "$(git rev-parse --show-toplevel)" || { echo "perimetro.sh: não consegui entrar na raiz do repo -- abortando (não rodar os 14 controles no diretório errado)." >&2; exit 1; }
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

  cabecalho "P-18" "Âncora de SHA não fica fail-soft esquecida" "MEMÓRIAS (277) -- fail-soft da âncora, detector textual não mecanizado até agora"
  p18_ancora_falha
  echo "veredito: AVISO SÓ (nunca falha)"
  CONT_OK=$((CONT_OK + 1))
  echo

  cabecalho "P-19" "Citação de arquivo:linha em entrada nova de MEMÓRIAS confere contra a fonte real" "REGRAS, Catálogo de falhas conhecidas -- família (59)-(250)/(251), 8/20 do catálogo"
  p19_citacao_arquivo
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
  _resultado_modular=$?

  # Modo sombra (item 10 do plano de mitigacao da auditoria do Marcos,
  # MEMORIAS (437) -- desenho pedido numa segunda opiniao formal antes desta
  # extracao, MEMORIAS (450)). A versao MODULAR decide (e' o exit code real
  # do hook, abaixo); a versao de referencia -- congelada, o monolito de
  # ANTES da extracao -- roda em paralelo so' pra registrar divergencia,
  # nunca pra decidir. Ativo so' enquanto o arquivo de referencia existir --
  # apagar ele desliga o modo sombra sem tocar em mais nada. Desligado
  # dentro da propria suite de testes (AGATA_TESTE_PERIMETRO) pra nao
  # dobrar o tempo de cada um dos 31 casos nem rodar contra um clone que
  # nao tem o arquivo de referencia.
  _ref_sombra="$_PERIMETRO_DIR/perimetro-sombra-referencia.sh"
  if [ -f "$_ref_sombra" ] && [ -z "${AGATA_TESTE_PERIMETRO:-}" ]; then
    _saida_sombra="$(bash "$_ref_sombra" 2>&1)"
    _resultado_sombra=$?
    _log_sombra="$HOME/.cache/agata/perimetro-sombra.log"
    mkdir -p "$(dirname "$_log_sombra")" 2>/dev/null
    if [ "$_resultado_sombra" != "$_resultado_modular" ]; then
      {
        echo "=== DIVERGENCIA $(date -Is 2>/dev/null) commit-em-curso=$(git rev-parse HEAD 2>/dev/null) ==="
        echo "modular:   exit=$_resultado_modular"
        echo "referencia (pre-extracao, congelada): exit=$_resultado_sombra"
        echo "ultimas linhas da referencia:"
        echo "$_saida_sombra" | tail -8
        echo
      } >> "$_log_sombra" 2>/dev/null
    fi
  fi

  exit "$_resultado_modular"
fi
