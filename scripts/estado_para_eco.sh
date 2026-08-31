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
# HASH-ESTADO é derivado e PÚBLICO — não tem relação com o nonce secreto do
# TES-002 (esse é gerado por openssl, nunca versionado, entregue à mão). Serve
# só para o eco citar um token que prova leitura sem "teatro" narrativo.

set -euo pipefail

# Locale fixo: `cut -c` conta caractere sob UTF-8 e byte sob LC_ALL=C — sem
# isto, a linha TES-002 (travessão, acentos) sai como mojibake num ambiente
# despido de locale (cron/CI). Achado 3 da Camada B, 31/08/2026.
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

# --- sync: local × remoto (forma canônica de REGRAS) ---
remoto=$(git ls-remote origin main 2>/dev/null | awk '{print $1}' | head -c 40 || true)
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

# --- TES-002 (só o status da 1ª frase; NÃO ecoar o nonce aposentado da linha) ---
# Achado 4 da Camada B: a linha do PROJETO cita `e1d1a` ("não deve ser ecoado
# por ninguém"). Cortar na 1ª frase deixa o status e larga o nonce.
tes002_raw=$(grep -m1 -E '^[[:space:]]*-[[:space:]]+\*\*TES-002:\*\*' PROJETO.md \
  | sed -E 's/^[[:space:]]*-[[:space:]]+//; s/\*\*//g' \
  | sed -E 's/^(TES-002:[^.]*\.).*/\1/' \
  | cut -c1-160 || true)
if [ -n "$tes002_raw" ] && ! printf '%s' "$tes002_raw" | grep -q '`'; then
  tes002="$tes002_raw …(ver PROJETO.md \"Estado dos bugs\")"
else
  tes002="TES-002: (status não extraído da forma esperada — ver PROJETO.md \"Estado dos bugs\")"
fi

# --- HASH-ESTADO: derivado, determinístico, público ---
hash_estado=$(printf '%s\n%s\n%s\n%s\n%s\n' \
  "$head_full" "$topo_linha" "$h_regras" "$h_memorias" "$h_projeto" \
  | sha256sum | cut -c1-12)

cat <<FIM
--- ESTADO PARA O ECO (fatos da Máquina; não é o eco) ---
HEAD: $head7 $head_subject
TOPO-MEMÓRIAS: $topo_linha
$sync_linha
PROPOSTAS-ABERTAS: $abertas (.diff sem APROVADO-)
$tes002
HASH-ESTADO: $hash_estado
--- fim dos fatos. O modelo escreve o eco (<=5 linhas), cita o HASH-ESTADO e
--- diz em 1 linha por que o estado está coerente. O Humano confere e confirma.
FIM

exit $SAIDA
