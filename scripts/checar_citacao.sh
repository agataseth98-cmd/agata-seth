#!/usr/bin/env bash
# P-7, HABILITADO desde MEMÓRIAS (204) -- checagem de citação. Decisão do
# Humano: NÃO trocar a arquitetura de hidratação; fechar só a falha
# específica que a expedição RLM achou -- a única fabricação confirmada em
# 240 respostas foi uma CITAÇÃO ERRADA (atribuiu a (143) um erro que
# estava na (157)). Checar só se a entrada existe não pega isso: as duas
# existem de verdade. Desde (162) toda citação carrega uma síntese junto
# do número -- `(n - síntese)` -- e é essa síntese que dá o que checar.
#
# Implementado e testado em (203) (isolado + contra os ~197 entradas
# reais, taxa medida). Duas correções em (204), ordem do Humano, antes de
# habilitar:
#   1. Citação dentro de crases é EXEMPLO de formato, pulada sem alarme
#      (ver REGRAS.md, "Citação de MEMÓRIAS -- primeira referência").
#   2. Síntese composta com mais de um número no mesmo parêntese
#      (`(194 - ...; 196 - ...)`) agora valida CADA número, não só o
#      primeiro.
#
# Generosa de propósito: síntese é paráfrase legítima, não citação
# literal. Só marca SUSPEITO quando NENHUMA palavra significativa da
# síntese aparece no corpo real da entrada -- overlap parcial já basta
# pra passar. Se isto reprovar o próprio canon, a checagem está errada,
# não o canon (ordem do Humano, doutrina de defesa proporcional). O
# limite conhecido (palavra genérica compartilhada deixa passar citação
# de assunto errado, achado em (203)) fica como está, por decisão do
# Humano: trancar commit honesto é pior que deixar passar uma citação
# rara.
set -uo pipefail

# checar_citacao <arquivo-com-texto-a-checar> [MEMÓRIAS.md]
# Extrai toda citação `(n - síntese)` do arquivo de texto e confere cada
# uma contra o corpo real da entrada n em MEMÓRIAS.md (a fonte de
# verdade). Não confere `(n)` sozinho -- isso é outra regra (primeira
# referência), fora do escopo do P-7.
checar_citacao() {
  local texto="$1"
  local memorias="${2:-MEMÓRIAS.md}"
  python3 - "$texto" "$memorias" <<'PYEOF'
import re, sys, unicodedata

texto_path, memorias_path = sys.argv[1], sys.argv[2]
with open(texto_path, encoding='utf-8') as f:
    texto = f.read()
with open(memorias_path, encoding='utf-8') as f:
    memorias = f.read()

STOPWORDS = {
    'para', 'sobre', 'entre', 'nunca', 'sempre', 'ainda', 'quando', 'onde',
    'isso', 'esta', 'este', 'essa', 'esse', 'pela', 'pelo', 'muito', 'mais',
    'menos', 'sem', 'com', 'nao', 'que', 'uma', 'um', 'dos', 'das', 'como',
    'depois', 'antes', 'todo', 'toda', 'todos', 'todas', 'pode', 'podem',
    'deve', 'devem', 'pois', 'mesmo', 'mesma', 'pra', 'tem', 'tem', 'foi',
    'sao', 'ser', 'estar', 'estava', 'estavam', 'fazer', 'feito', 'feita',
    'ainda', 'algo', 'alguma', 'algum', 'outra', 'outro', 'outros', 'outras',
    'ficou', 'fica', 'ficar', 'aqui', 'nesta', 'neste', 'nessa', 'nesse',
}

def normalizar(s):
    s = unicodedata.normalize('NFKD', s.lower())
    return ''.join(c for c in s if not unicodedata.combining(c))

# Índice das entradas: título começa em início de linha, formato "(n) LABEL"
# -- só existe sem ambiguidade a partir de (49) (história antes disso usa
# "### ", formato migrado, fora do escopo -- ver MEMÓRIAS "Como ler este
# arquivo").
padrao_entrada = re.compile(r'^\((\d+)\) (?:DIÁRIO|CONSELHO|CORREÇÃO|MOD)\b.*$', re.MULTILINE)
posicoes = [(m.start(), int(m.group(1)), m.group(0)) for m in padrao_entrada.finditer(memorias)]
entradas = {}
for i, (pos, n, titulo) in enumerate(posicoes):
    fim = posicoes[i + 1][0] if i + 1 < len(posicoes) else len(memorias)
    corpo = memorias[pos:fim]
    entradas.setdefault(n, []).append({'titulo': titulo, 'corpo_norm': normalizar(corpo)})

# Espaço dos dois lados do hífen é obrigatório -- é o que distingue uma
# citação real ("(101 - síntese)") de uma data ("(2026-07-02)") ou faixa
# numérica ("(45-97%)"), achado ao rodar contra o corpus real (MEMÓRIAS
# (203)): sem essa exigência, datas e faixas eram maioria dos falsos
# positivos.
padrao_citacao = re.compile(r'\((\d+) - ([^()]+)\)')

# Crases marcam EXEMPLO de formato, não citação real (REGRAS, "Citação de
# MEMÓRIAS -- primeira referência"; MEMÓRIAS (204)). Uma citação cujo
# span inteiro cai dentro de um trecho entre crases é pulada, sem alarme.
spans_crase = [(m.start(), m.end()) for m in re.finditer(r'`[^`]*`', texto)]

def dentro_de_crase(inicio, fim):
    return any(a <= inicio and fim <= b for a, b in spans_crase)

total = 0
suspeitos = 0
pulados_exemplo = 0
for m in padrao_citacao.finditer(texto):
    if dentro_de_crase(m.start(), m.end()):
        pulados_exemplo += 1
        continue
    n_primeiro_str, conteudo = m.group(1), m.group(2)
    # Síntese composta cita mais de um número no mesmo parêntese --
    # "(194 - Parte A: ...; 196 - Fase 1 ...)" (achado em (203), lacuna
    # de então). Divide só quando "; " é seguido de outro "N - ", nunca
    # em ponto-e-vírgula de prosa comum.
    segmentos = re.split(r'; (?=\d+ - )', conteudo)
    pares = [(int(n_primeiro_str), segmentos[0])]
    for seg in segmentos[1:]:
        m2 = re.match(r'(\d+) - (.+)', seg, re.DOTALL)
        if m2:
            pares.append((int(m2.group(1)), m2.group(2)))

    for n, sintese in pares:
        total += 1
        sintese = sintese.strip()
        if n not in entradas:
            print(f"SUSPEITO (P-7): ({n} - {sintese}) cita uma entrada que não existe em MEMÓRIAS.md. O número pode estar errado. Confira ({n}) antes de comitar.")
            suspeitos += 1
            continue
        palavras = [w for w in re.findall(r'[a-zA-ZÀ-ÿ]{4,}', sintese) if normalizar(w) not in STOPWORDS]
        if not palavras:
            continue  # síntese sem palavra significativa (ex.: só números/símbolos) -- generoso, não marca
        achou = False
        for cand in entradas[n]:
            corpo_norm = cand['corpo_norm']
            for w in palavras:
                wn = normalizar(w)
                chave = wn[:5] if len(wn) > 5 else wn
                if chave in corpo_norm:
                    achou = True
                    break
            if achou:
                break
        if not achou:
            titulo_real = entradas[n][-1]['titulo']
            print(f"SUSPEITO (P-7): citação ({n} - {sintese}) não bate com o conteúdo real de ({n}). Título real: \"{titulo_real}\". A síntese pode estar errada, ou é a entrada errada. Confira ({n}) antes de comitar.")
            suspeitos += 1

print(f"__RESUMO_P7__ total_citacoes={total} suspeitos={suspeitos} pulados_exemplo={pulados_exemplo}")
sys.exit(1 if suspeitos else 0)
PYEOF
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  if [ "$#" -lt 1 ]; then
    echo "uso: $0 <arquivo-com-texto-a-checar> [MEMÓRIAS.md]" >&2
    exit 2
  fi
  checar_citacao "$@"
  exit $?
fi
