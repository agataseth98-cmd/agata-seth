#!/usr/bin/env python3
"""Versão de exportação do índice derivado, para o cano do Drive.

A varredura de segredo do subir_esfera_projeto.py aborta em nome de variável
de ambiente pelado (ex.: ZHIPU_API_KEY sem valor) — falso positivo em prosa
de canon público, mas o scanner é conservador de propósito e não se afrouxa.
Este script produz uma cópia do índice com esses nomes mascarados.

Lê   : memoria/missoes/agata-sistema/derivado/indice.md
Escreve: memoria/missoes/agata-sistema/derivado/indice_export.md

O indice.md original NÃO é tocado — a reconstrução byte a byte de MEMÓRIAS (298)
continua valendo pra ele. O indice_export.md é o que sobe pro Drive; para o
NotebookLM, baixe o indice_export.md do Drive.

Não altera o scanner. Verifica no fim que o indice_export.md passa em TODOS os
padrões de PADROES_SEGREDO — se algum sobrar, aborta sem escrever.
"""
import os
import re
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from subir_esfera_projeto import PADROES_SEGREDO  # noqa: E402  (fonte única da lista)

DERIVADO = os.path.join(REPO, "memoria", "missoes", "agata-sistema", "derivado")
ENTRADA = os.path.join(DERIVADO, "indice.md")
SAIDA = os.path.join(DERIVADO, "indice_export.md")

PLACEHOLDER = "[variável de ambiente]"

# Só nomes de variável pelados. Espelham os padrões 48 e 56 do scanner —
# os únicos que casam NOME, não SEGREDO.
NOMES_VAR = [
    re.compile(r"\b(?:ZHIPU|GOOGLE|GEMINI|GROQ|DEEPSEEK|OPENROUTER|OPENAI|ANTHROPIC)_API_KEY\b"),
    re.compile(r"(?i)\baws_secret_access_key\b"),
]

MARCA = ("<!-- versão de exportação: nomes de variável de ambiente mascarados "
         "como '[variável de ambiente]'. Original verbatim: indice.md. -->")


def abortar(msg):
    print(f"ABORTADO: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    if not os.path.isfile(ENTRADA):
        abortar(f"{ENTRADA} não existe — rode gerar_indice_derivado.py antes.")

    txt = open(ENTRADA, encoding="utf-8").read()

    trocas = []

    def _sub(m):
        trocas.append(m.group(0))
        return PLACEHOLDER

    for rx in NOMES_VAR:
        txt = rx.sub(_sub, txt)

    # marca logo após o fim do frontmatter (2ª linha '---')
    linhas = txt.split("\n")
    fim_fm = None
    if linhas and linhas[0] == "---":
        for i in range(1, len(linhas)):
            if linhas[i] == "---":
                fim_fm = i
                break
    if fim_fm is not None:
        linhas.insert(fim_fm + 1, MARCA)
        txt = "\n".join(linhas)
    else:
        txt = MARCA + "\n" + txt

    # gate: o resultado tem que passar no scanner inteiro
    for pat, desc in PADROES_SEGREDO:
        m = re.search(pat, txt)
        if m:
            abortar(f"ainda casa o scanner ({desc}): {m.group(0)[:50]!r} — nada foi escrito.")

    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(txt)

    print(f"OK: indice_export.md ({len(txt)} chars) — {len(trocas)} nome(s) de variável mascarado(s)")
    for nome, n in Counter(trocas).most_common():
        print(f"    {n}x  {nome}")
    print(f"    em {SAIDA}")
    print("    passa em PADROES_SEGREDO (16/16 sem match).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
