"""Uma única definição de "entrada CORREÇÃO" para a Alexandria (lote 5, pacote C1).

Antes havia duas (acervo.py e curadoria.py), com regras diferentes. Agora:
`correcao_de(texto)` devolve (nova, velha): `nova` é o número da própria CORREÇÃO e `velha` é a
primeira entrada citada no cabeçalho, que é a que ela corrige. Se não for CORREÇÃO, devolve None.
Regra 4 do canon: a antiga permanece; a correção é entrada nova.
"""
from __future__ import annotations

import re

RE_CABECALHO = re.compile(r"^\((\d{1,4})\)\s+CORRE[CÇ][AÃ]O\b", re.I)
RE_CITA = re.compile(r"(?<![\w(])\((\d{1,4})\)")


def correcao_de(texto: str) -> tuple[int, int | None] | None:
    m = RE_CABECALHO.match(texto or "")
    if not m:
        return None
    nova = int(m.group(1))
    cabecalho = (texto or "").split("\n", 1)[0]
    citadas = [int(c) for c in RE_CITA.findall(cabecalho[m.end():]) if int(c) != nova]
    return nova, (citadas[0] if citadas else None)
