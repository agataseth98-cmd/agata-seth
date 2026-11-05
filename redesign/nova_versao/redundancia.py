"""Redundância por capacidade (lote 5, pacote D2): escolher rota alternativa e ensaiar a falha.

`escolher_rota` usa só rotas que PASSARAM no teste funcional (testar_rotas), nunca as instaladas.
`ensaio_retorno` injeta a falha da rota principal (sem parar serviço nenhum) e confere que a alternativa
responde. O histórico de rota vai ao ledger como evento por rota, com chave idempotente.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import eventos  # noqa: E402
import papeis  # noqa: E402


def escolher_rota(capacidade: str, rotas: list[dict], aprovadas: dict[str, list[str]], excluir: set[str] | None = None):
    if capacidade not in papeis.PROVAS:
        raise ValueError("capacidade fora das provas")
    excluir = excluir or set()
    for r in sorted(rotas, key=lambda x: x["rota"]):
        if r["rota"] in excluir:
            continue
        if r["rota"] in aprovadas.get(capacidade, []):
            return r
    return None


def ensaio_retorno(capacidade: str, rotas: list[dict], aprovadas: dict[str, list[str]], chamar) -> dict:
    """Falha a primeira rota de propósito (chamar levanta) e confere a alternativa. Só injeção, nunca serviço real."""
    principal = escolher_rota(capacidade, rotas, aprovadas)
    if principal is None:
        return {"capacidade": capacidade, "estado": "sem_rota", "principal": None, "alternativa": None}
    def falha(rota, prompt):
        if rota["rota"] == principal["rota"]:
            raise ConnectionError("falha injetada para o ensaio")
        return chamar(rota, prompt)
    try:
        falha(principal, "teste")
        estado, usada = "principal_ok", principal["rota"]
    except ConnectionError:
        alt = escolher_rota(capacidade, rotas, aprovadas, excluir={principal["rota"]})
        if alt is None:
            estado, usada = "sem_alternativa", None
        else:
            r = falha(alt, "teste")
            estado, usada = ("retorno_ok" if r.get("ok") else "retorno_falhou"), alt["rota"]
    eventos.registrar("verification", estado, f"rota:{principal['rota']}", componente="redundancia",
                      classification="project", chave=f"rota:{principal['rota']}:ensaio:{capacidade}:{time.monotonic_ns()}",
                      capacidade=capacidade, usada=usada)
    return {"capacidade": capacidade, "estado": estado, "principal": principal["rota"], "alternativa": usada}
