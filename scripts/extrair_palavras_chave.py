#!/usr/bin/env python3
"""Extrai palavras-chave de cada linha de título de INDICE_MEMORIAS.md.

Puramente mecânico: tokeniza, tira stopword e palavra curta, deduplica,
preserva ordem de primeira aparição. NUNCA embedding, NUNCA modelo de
linguagem julgando relevância — decisão (115): grep vence embedding em
precisão, custo e auditabilidade, pra este corpus. As palavras-chave
existem pra `grep -i` achar entrada por assunto sem reler o índice
inteiro, não pra "entender" nada.

Uso: uma linha de título por vez no stdin, devolve a mesma linha
seguida de uma linha "  palavras-chave: a, b, c" (2 espaços de indent,
igual ao padrão de nota que INDICE_MEMORIAS.md já usa).
"""
from __future__ import annotations

import re
import sys

STOPWORDS = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "ou",
    "em", "no", "na", "nos", "nas", "um", "uma", "uns", "umas", "por",
    "para", "com", "sem", "que", "se", "não", "já", "só", "mais",
    "menos", "muito", "pouco", "ao", "aos", "à", "às", "é", "foi",
    "ser", "está", "são", "seu", "sua", "seus", "suas", "este", "esta",
    "esse", "essa", "isso", "isto", "num", "numa", "entre", "sobre",
    "até", "quando", "onde", "como", "mas", "também", "vez", "vezes",
    "ver", "ainda", "depois", "antes", "cada", "todo", "toda", "todos",
    "todas", "outro", "outra", "outros", "outras", "diário", "conselho",
    "nenhum", "nenhuma", "nesta", "neste", "nessa", "nesse", "naquela",
    "naquele", "duas", "dois", "via", "algum", "alguma", "alguns",
    "algumas", "qualquer", "quaisquer", "pelo", "pela", "pelos", "pelas",
}


def extrair(titulo: str, minimo_letras: int = 3) -> list[str]:
    # Remove o prefixo de data/número/rótulo (ex: "21/08/2026 (234) DIÁRIO — ")
    # antes de tokenizar -- não é palavra-chave, é metadado que já está em
    # campo próprio no índice.
    sem_prefixo = re.sub(
        r"^\d{4}-\d{2}-\d{2}\s*\(\d+\)\s*|^\(\d+\)\s*",
        "",
        titulo,
    )
    sem_prefixo = re.sub(r"^(DIÁRIO|CONSELHO|MOD[^—]*|CORREÇÃO)\s*—\s*", "", sem_prefixo)
    sem_prefixo = re.sub(r"^\d{2}/\d{2}/\d{4}\s*·\s*", "", sem_prefixo)

    palavras = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", sem_prefixo.lower())
    vistas: dict[str, None] = {}
    for p in palavras:
        if len(p) < minimo_letras:
            continue
        if p in STOPWORDS:
            continue
        vistas.setdefault(p, None)
    return list(vistas.keys())


def main() -> int:
    for linha in sys.stdin:
        linha = linha.rstrip("\n")
        if not linha.strip():
            continue
        print(linha)
        chaves = extrair(linha)
        if chaves:
            print("  palavras-chave: " + ", ".join(chaves))
    return 0


if __name__ == "__main__":
    sys.exit(main())
