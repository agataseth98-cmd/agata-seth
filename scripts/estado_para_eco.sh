#!/usr/bin/env bash
# scripts/estado_para_eco.sh — Fase 2 / Bloco 3.2: mecaniza o eco pós-carregar.
#
# POR QUÊ: hidratação falha (história atrasada ou incompleta) não se vê lendo
# a própria cópia — quem carregou 12 dias atrás lê um estado coerente e errado
# (MEMÓRIAS (248)-(252)). A Máquina tem os fatos; este script os imprime para
# o modelo FUNDAMENTAR o eco e o Humano ter um cartão de conferência.
#
# O QUE É E O QUE NÃO É: imprime fatos de estado, nada mais. NÃO escreve o eco,
# NÃO valida o texto do eco, NÃO decide se a hidratação passou — conferir o eco
# contra estes fatos é do Humano (Regra 8, 3 passadas qwen local 31/08/2026:
# Q1 convergiu em "só imprimir"; Q3 convergiu em "obrigatório quando há shell";
# Q2 decidida pelo Humano — "hash + frase", as duas).
#
# Escrita única, fora do repo: o cache do ls-remote em ~/.cache/agata/ (ver
# "cache" abaixo). No repo, READ-ONLY.
# READ-ONLY: só lê arquivos e consulta o remoto (git ls-remote). Nunca
# git add/commit/push, nunca escreve no repo. Uma rede indisponível vira
# `sync: não verificado`, não erro.
#
# A linha `sync:` sai na forma canônica de REGRAS.md ("Carregar e formatos",
# três formas, nunca uma quarta): `sync: PASS · REGRAS=<hash8> · MEMÓRIAS=<hash8>
# · HEAD=<commit7>` / `sync: FALHA · <o que diverge>` / `sync: não verificado ·
# lacuna: <motivo>`. É pra poder ser colada no bloco de prontidão sem virar
# uma quarta grafia.
#
# HASH-ESTADO é derivado e PÚBLICO — serve só para o eco citar um token que
# prova leitura sem "teatro" narrativo. (Não há mais nonce: TES-002 aposentado
# em 09/09/2026, MEMÓRIAS (417).)

set -euo pipefail

# Locale fixo: `cut -c` conta caractere sob UTF-8 e byte sob LC_ALL=C — sem
# isto, linha com travessão/acentos sai como mojibake num ambiente despido de
# locale (cron/CI). Achado 3 da Camada B, 31/08/2026.
export LC_ALL="${LC_ALL_ECO:-C.UTF-8}"

cd "$(git rev-parse --show-toplevel)"

MARCADOR="ENTRADAS-NOVAS"
CANONICOS=(REGRAS.md MEMÓRIAS.md PROJETO.md)
# Código de saída: 0 = estado utilizável (sync PASS ou não verificado);
# 1 = sync FALHA — a cópia local não é o canon: HEAD diverge do remoto, OU a
#     árvore de trabalho tem edição não commitada num dos canônicos (o eco NÃO
#     pode afirmar o topo do canon; ver REGRAS "Última entrada sob sync não
#     verificado");
# 2 = defeito estrutural (marcador ENTRADAS-NOVAS sumiu — leitura do topo não
#     é confiável). 2 tem precedência sobre 1.
SAIDA=0

# --- HEAD ---
head_full=$(git rev-parse HEAD)
head7=$(git rev-parse --short=7 HEAD)
head_subject=$(git log -1 --format=%s)

# --- Topo de MEMÓRIAS (primeira entrada após o marcador ENTRADAS-NOVAS) ---
topo_linha=$(awk -v m="$MARCADOR" '
  achou && /^\([0-9]+\)/ { print; exit }
  $0 ~ m { achou = 1 }
' MEMÓRIAS.md)
[ -z "$topo_linha" ] && { topo_linha="(desconhecido — marcador $MARCADOR não encontrado)"; SAIDA=2; }

# --- Hashes canônicos (ao vivo, nunca de memória) ---
h_regras=$(sha256sum REGRAS.md   | cut -c1-8)
h_memorias=$(sha256sum MEMÓRIAS.md | cut -c1-8)
h_projeto=$(sha256sum PROJETO.md  | cut -c1-8)

# --- Árvore de trabalho suja num canônico? (staged ou não) ---
# git ls-remote só compara o SHA do commit; um canônico editado e não commitado
# passaria como PASS e o HASH-ESTADO sairia sobre bytes que não são o canon.
# `git diff HEAD` já cobre staged + não-staged. Achado 1 da Camada B, 31/08/2026.
sujos=$(git -c core.quotepath=false diff --name-only HEAD -- "${CANONICOS[@]}" 2>/dev/null | paste -sd' ' - || true)

# --- ALERTA-HISTORIA: MEMÓRIAS.md perdeu linhas sem commit? ---
# "Árvore suja" acima não distingue uma entrada nova esperando commit (normal)
# de história APAGADA (Regra 4, linha vermelha). Em MEMÓRIAS.md, entre dois
# commits, só se acrescenta -- linha removida em relação ao HEAD nunca é
# legítima. Achado real, MEMÓRIAS (516)/(517): a ferramenta `write` do Goose
# reescreveu o arquivo inteiro (2457 -> 14 linhas) e ficou assim a manhã toda
# com `sync: FALHA` genérico, sem ninguém reagir. Linha própria, com número,
# pra ninguém confundir com "tem entrada pendente".
removidas=$(git diff --numstat HEAD -- MEMÓRIAS.md 2>/dev/null | awk '{print $2}' | head -1 || true)
alerta_historia=""
if [ -n "$removidas" ] && [ "$removidas" != "-" ] && [ "$removidas" -gt 0 ] 2>/dev/null; then
  alerta_historia="ALERTA-HISTORIA: MEMÓRIAS.md perdeu $removidas linha(s) em relação ao HEAD, sem commit -- história apagada na cópia local (Regra 4). Não escreva em MEMÓRIAS nem commite; avise o Humano. O canon no GitHub não é afetado."
  SAIDA=$(( SAIDA < 1 ? 1 : SAIDA ))
fi

# --- sync: local × remoto (forma canônica de REGRAS) ---
# Timeout PRÓPRIO pro `ls-remote`, menor que o timeout externo do chamador
# (seth_gateway.py usa 25s pro script inteiro) -- achado real, MEMÓRIAS (492):
# sem isto, um pico de rede no `ls-remote` consumia o orçamento inteiro do
# subprocess e o script INTEIRO morria por timeout, sem chegar nem a imprimir
# HEAD/hashes/topo-de-MEMÓRIAS -- que não dependem de rede nenhuma. Com
# timeout próprio e mais curto, o pico de rede vira só `sync: não verificado`
# (linha abaixo), e o resto do estado sai normal. `LS_REMOTE_TIMEOUT_ECO`
# como saída de emergência, mesmo padrão de `LC_ALL_ECO` acima.
# Cache de ${ECO_LSREMOTE_CACHE_S:-60}s (decisão do Humano, MEMÓRIAS (532)): o seth_gateway
# roda este script em TODO turno da Seth, e com o GitHub instável o ls-remote
# custava até 8s por resposta (medido em (527): 458/8032/464 ms). Só se guarda
# medição BEM-SUCEDIDA; falha nunca é cacheada (não vira PASS velho). A idade da
# medição vai numa linha própria, SYNC-REMOTO-IDADE -- a linha `sync:` mantém
# as três formas canônicas de REGRAS, nunca uma quarta. `ECO_LSREMOTE_CACHE_S=0`
# desliga o cache. `maquina_verificar git_sync` continua medindo ao vivo, sempre.
_cache_ls="$HOME/.cache/agata/ls-remote-main"
_agora=$(date +%s); remoto=""; idade_remoto=""
if [ "${ECO_LSREMOTE_CACHE_S:-60}" -gt 0 ] 2>/dev/null && [ -f "$_cache_ls" ]; then
  read -r _t _sha < "$_cache_ls" || true
  if [ -n "${_t:-}" ] && [ "${#_sha}" = 40 ] && [ $(( _agora - _t )) -ge 0 ] \
     && [ $(( _agora - _t )) -lt "${ECO_LSREMOTE_CACHE_S:-60}" ]; then
    remoto="$_sha"; idade_remoto="$(( _agora - _t ))s (cache)"
  fi
fi
if [ -z "$remoto" ]; then
  remoto=$(timeout "${LS_REMOTE_TIMEOUT_ECO:-8}" git ls-remote origin main 2>/dev/null | awk '{print $1}' | head -c 40 || true)
  if [ "${#remoto}" = 40 ]; then
    idade_remoto="0s (medido agora)"
    mkdir -p "$(dirname "$_cache_ls")" 2>/dev/null && printf '%s %s\n' "$_agora" "$remoto" > "$_cache_ls" 2>/dev/null || true
  fi
fi
if [ -z "$remoto" ]; then
  sync_linha="sync: não verificado · lacuna: remoto inacessível (rede ou credencial)"
elif [ "$remoto" != "$head_full" ]; then
  atras_a_frente=$(git rev-list --left-right --count "$head_full...$remoto" 2>/dev/null | tr '\t' '/' || echo "?/?")
  extra=""; [ -n "$sujos" ] && extra=" + árvore suja: $sujos"
  sync_linha="sync: FALHA · HEAD local=$head7 diverge do remoto=$(printf %s "$remoto" | cut -c1-7) (atrás/à-frente: ${atras_a_frente:-?/?})$extra"
  SAIDA=$(( SAIDA < 1 ? 1 : SAIDA ))
elif [ -n "$sujos" ]; then
  sync_linha="sync: FALHA · árvore de trabalho com edição não commitada em: $sujos (a cópia local não é o canon publicado)"
  SAIDA=$(( SAIDA < 1 ? 1 : SAIDA ))
else
  sync_linha="sync: PASS · REGRAS=$h_regras · MEMÓRIAS=$h_memorias · HEAD=$head7"
fi

# --- Propostas estruturais abertas (.diff sem APROVADO- correspondente) ---
abertas=0
shopt -s nullglob
for d in propostas/*.diff; do
  nome=$(basename "$d" .diff)
  [ -e "propostas/APROVADO-$nome" ] || abertas=$((abertas + 1))
done
shopt -u nullglob

# --- TOPO-PROPOSTA-JA-APLICADA: a entrada do topo cita uma proposta que já
# saiu de propostas/ pra propostas/aplicadas/? (achado auditando um
# carregamento real da Seth, MEMÓRIAS (464)/(465)). Aplicar uma proposta
# assinada não ganha entrada própria em MEMÓRIAS (Regra 4: correção é entrada
# nova, nunca edição do texto existente) -- então o topo pode dizer
# "aguardando assinatura" bem depois de já ter sido assinada e aplicada, sem
# nenhum sinal disso pra quem só lê o topo (a Seth, ou qualquer modelo sem
# `git log`). Heurística, não prova: procura nomes entre crases no topo que
# batam com um `.diff` em propostas/aplicadas/. Nome coincidente por acaso é
# o único falso-positivo esperado -- por isso isto é só um aviso, nunca falha.
topo_proposta_aplicada=""
for _nome_topo in $(grep -oE '`[a-zA-Z0-9_-]+`' <<<"$topo_linha" | tr -d '`'); do
  if [ -f "propostas/aplicadas/${_nome_topo}.diff" ]; then
    topo_proposta_aplicada="$_nome_topo"
    break
  fi
done

# TES-002 aposentado em 09/09/2026 (MEMÓRIAS (417)) — não há mais linha de
# status de nonce no eco. A checagem de hidratação velha agora é `sync:` +
# HASH-ESTADO + IDADE-HIDRATACAO abaixo.

# --- HASH-ESTADO: derivado, determinístico, público ---
hash_estado=$(printf '%s\n%s\n%s\n%s\n%s\n' \
  "$head_full" "$topo_linha" "$h_regras" "$h_memorias" "$h_projeto" \
  | sha256sum | cut -c1-12)

# --- IDADE-HIDRATACAO: há quanto tempo .hidrata.md foi gerado (item C1.1,
# pedido do Humano 05/09/2026 -- distingue "sync PASS" (HEAD bate com o
# remoto) de "hidratação recente" (o arquivo que o modelo de fato recebeu
# reflete esse HEAD). As duas coisas podem divergir: sync PASS não prova
# que .hidrata.md foi regenerado depois do último commit -- só o pre-commit
# faz isso, e um clone fresco ou uma falha silenciosa do hook deixaria o
# arquivo velho com HEAD novo. `lacuna` se o arquivo não existir.
if [ -f .hidrata.md ]; then
  hidrata_mtime=$(date -r .hidrata.md +%s)
  agora=$(date +%s)
  idade_s=$(( agora - hidrata_mtime ))
  if [ "$idade_s" -lt 0 ]; then
    idade_hidratacao="lacuna: mtime de .hidrata.md no futuro (relógio da Máquina?) — não confie na idade"
  elif [ "$idade_s" -lt 3600 ]; then
    idade_hidratacao="$(( idade_s / 60 ))min atrás"
  elif [ "$idade_s" -lt 86400 ]; then
    idade_hidratacao="$(( idade_s / 3600 ))h atrás"
  else
    idade_hidratacao="$(( idade_s / 86400 ))d atrás"
  fi
else
  idade_hidratacao="lacuna: .hidrata.md não existe neste checkout"
fi

# --- HORA-MAQUINA (H2, MEMÓRIAS (390)): a Seth (modelo em nuvem, sem shell)
# não tem como medir hora nenhuma -- só pode ecoar o que a Máquina mede e
# repassa aqui. Mesmo critério de selo da Regra 1.1 pros modelos locais
# (que TÊM shell): NTP sincronizado -> (relógio da Máquina); senão -> (relógio
# do sistema, não sincronizado). Sem isto, a doutrina só proibia inventar sem
# dar nada real pra copiar -- um glm já inventou `12:34:05 +00:00` num teste.
if command -v timedatectl >/dev/null 2>&1 \
   && timedatectl status 2>/dev/null | grep -qi "synchronized: yes"; then
  hora_maquina="$(TZ=America/Sao_Paulo date '+%Y-%m-%d %H:%M %z') (relógio da Máquina)"
else
  hora_maquina="$(TZ=America/Sao_Paulo date '+%Y-%m-%d %H:%M %z') (relógio do sistema, não sincronizado)"
fi

cat <<FIM
--- ESTADO PARA O ECO (fatos da Máquina; não é o eco) ---
HEAD: $head7 $head_subject
TOPO-MEMÓRIAS: $topo_linha
$sync_linha
${idade_remoto:+SYNC-REMOTO-IDADE: $idade_remoto
}${alerta_historia:+$alerta_historia
}IDADE-HIDRATACAO: $idade_hidratacao
PROPOSTAS-ABERTAS: $abertas (.diff sem APROVADO-)
${topo_proposta_aplicada:+TOPO-PROPOSTA-JA-APLICADA: '$topo_proposta_aplicada' citada no topo já está em propostas/aplicadas/ -- o texto da entrada pode estar desatualizado, confira "git log" ou ONDE_ESTAMOS.md antes de afirmar que ainda está pendente.
}HORA-MAQUINA: $hora_maquina
HASH-ESTADO: $hash_estado
--- fim dos fatos. O modelo escreve o eco (<=5 linhas), cita o HASH-ESTADO e
--- diz em 1 linha por que o estado está coerente. O Humano confere e confirma.
FIM

exit $SAIDA
