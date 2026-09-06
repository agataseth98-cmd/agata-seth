#!/usr/bin/env bash
# P-13, autorizado pelo Humano ("Autorizado, vai.") como item 2 do backlog
# "Ponto Cego" reordenado em MEMÓRIAS (355). Cobre REGRAS.md, Regra 4,
# item 4: "Sem discordância real em 4 semanas -> provocar uma `sintética`,
# marcada como tal."
#
# Detecção puramente MECÂNICA -- acha a data, não decide se falta
# discordância de verdade nem como provocar uma. Isso é julgamento
# editorial, fora de escopo aqui por ordem do Humano (item explicitamente
# excluído ao autorizar este script).
#
# Fonte de sinal: entradas rotuladas CONSELHO cujo corpo contém a raiz
# "discord" (discordância/discordâncias/discorda/discordou/discordante --
# a raiz não colide com "concordância"/"concorda", que não contêm
# "discord"). Não basta existir uma entrada CONSELHO qualquer -- a
# definição em MEMÓRIAS.md ("Como ler este arquivo") diz que CONSELHO
# cobre entrada, saída OU discordância de modelo; convergência pura
# (ex.: (276)) não conta pro relógio da Regra 4.
#
# AVISA, nunca falha -- mesma doutrina de P-6/P-9: um relógio de atrito
# saudável não é motivo pra travar a escrita do canon.
set -uo pipefail

# checar_discordancia [MEMÓRIAS.md]
checar_discordancia() {
  local memorias="${1:-MEMÓRIAS.md}"
  [ -f "$memorias" ] || return 0
  python3 - "$memorias" <<'PYEOF'
import re, sys
from datetime import date

memorias_path = sys.argv[1]
with open(memorias_path, encoding='utf-8') as f:
    memorias = f.read()

padrao_entrada = re.compile(
    r'^\((\d+)\) CONSELHO — (\d{2})/(\d{2})/(\d{4})\b.*$', re.MULTILINE
)
posicoes = [(m.start(), m) for m in padrao_entrada.finditer(memorias)]

candidatas = []
for i, (pos, m) in enumerate(posicoes):
    fim = posicoes[i + 1][0] if i + 1 < len(posicoes) else len(memorias)
    corpo = memorias[pos:fim]
    if re.search(r'discord', corpo, re.IGNORECASE):
        n = int(m.group(1))
        dia, mes, ano = int(m.group(2)), int(m.group(3)), int(m.group(4))
        candidatas.append((n, dia, mes, ano))

if not candidatas:
    # Bootstrap: nenhuma discordância real jamais registrada -- não dá pra
    # medir um relógio sem primeiro dado. Silencioso de propósito, mesma
    # lógica do bootstrap de P-10.
    sys.exit(0)

n, dia, mes, ano = max(candidatas, key=lambda t: t[0])
try:
    data_entrada = date(ano, mes, dia)
except ValueError:
    # Data malformada na própria entrada -- não é o que este controle audita.
    sys.exit(0)

dias = (date.today() - data_entrada).days
if dias >= 28:
    print(
        f"AVISO (P-13): última discordância real registrada em CONSELHO foi "
        f"({n}), {dia:02d}/{mes:02d}/{ano} -- {dias} dias atrás, >= 28 "
        f"(REGRAS.md, Regra 4, item 4). Por que importa: sem atrito real "
        f"por 4 semanas o canon corre o risco de virar eco entre modelos, "
        f"sem ninguém contestando nada de verdade. O que fazer: provocar "
        f"uma discordância SINTÉTICA e registrar como entrada CONSELHO "
        f"marcada como tal (ver convenção estrutural em REGRAS.md) -- "
        f"nunca disfarçada de discordância real."
    )
    sys.exit(1)
sys.exit(0)
PYEOF
}

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  checar_discordancia "${1:-MEMÓRIAS.md}"
  exit $?
fi
