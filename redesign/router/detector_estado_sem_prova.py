"""Detector determinístico de afirmação de estado sem prova (M1, M2, M3 de 21/10/2026).

Sem modelo: regex sobre o texto da resposta. Achado = afirmação de estado
("endereçado", "fechado", "confirmado", "medido agora") sem PR, commit,
caminho de arquivo ou saída de comando no mesmo parágrafo; percentual de
confiança (M2); componente removido citado no presente sem marcação (M3).
"""
from __future__ import annotations

import re

_ESTADO = re.compile(r"(?i)\b(endere[cç]ad\w*|fechad\w*|confirmad\w*|medido agora|resolvid\w*)\b")
_PROVA = re.compile(r"(?i)(#\d+|pull/\d+|\b[0-9a-f]{7,40}\b|\b[\w./-]+\.(py|sh|md|json|yaml|yml|mjs|service)\b|\$ |`[^`]+`|saída|exit=|HTTP \d{3})")
_CONFIANCA = re.compile(r"(?i)confian[çc]a\W{0,12}\d{1,3}\s?%")
_REMOVIDOS = re.compile(r"\b(Hermes|kokoro|agata\.service)\b")
_MARCA_REMOCAO = re.compile(r"(?i)removid\w*|\(\s*31[12]\s*\)|\(\s*59[34]\s*\)")


def achados(texto: str) -> list[str]:
    out: list[str] = []
    for paragrafo in re.split(r"\n\s*\n", texto):
        if _ESTADO.search(paragrafo) and not _PROVA.search(paragrafo):
            out.append("estado afirmado sem prova no mesmo parágrafo: " + paragrafo.strip()[:100])
    for m in _CONFIANCA.finditer(texto):
        out.append("percentual de confiança sem base: " + m.group(0))
    for paragrafo in re.split(r"\n\s*\n", texto):
        if _REMOVIDOS.search(paragrafo) and not _MARCA_REMOCAO.search(paragrafo):
            out.append("componente removido citado sem marcação de remoção: " + paragrafo.strip()[:100])
    return out
