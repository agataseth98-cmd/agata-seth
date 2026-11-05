"""Orçamento por turno (lote 5, pacote D3): rodadas de ferramenta, chamadas e prazo. Mecânico, sem modelo.

Quando o orçamento do turno acaba, a resposta não é apresentada como completa: o `posterior` a marca
`parcial` com o motivo. Os limites vêm do orçamento da nova versão (redesign/nova_versao/orcamento.py) e do
teto de rodadas de ferramenta do gateway (6).
"""
from __future__ import annotations

import time

MAX_RODADAS_FERRAMENTA = 6


def estado(*, rodadas: int, chamadas: int, inicio_monotonic: float, max_chamadas: int, prazo_s: float,
           max_rodadas: int = MAX_RODADAS_FERRAMENTA) -> dict:
    motivos = []
    if rodadas >= max_rodadas:
        motivos.append(f"rodadas de ferramenta esgotadas ({rodadas}/{max_rodadas})")
    if chamadas >= max_chamadas:
        motivos.append(f"chamadas esgotadas ({chamadas}/{max_chamadas})")
    if time.monotonic() - inicio_monotonic > prazo_s:
        motivos.append("prazo do turno esgotado")
    return {"esgotado": bool(motivos), "motivos": motivos,
            "restantes": {"rodadas": max(max_rodadas - rodadas, 0), "chamadas": max(max_chamadas - chamadas, 0)}}
