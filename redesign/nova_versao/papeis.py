"""Papéis da nova versão (lote 5, pacote D1): escolher a rota certa para cada papel, sem serviço por papel.

Um papel é uma descrição (config/papeis.json). `resolver` cruza essa descrição com as rotas que o orçamento
permite e com as que PASSARAM no teste funcional de `testar_rotas` (capacidade provada, não instalada).
Revisor e suporte precisam ser de família diferente do sintetizador (independência, protocolo §10 do contrato).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
CONFIG = RAIZ / "config" / "papeis.json"
PROVAS = ("conversa", "formato", "codigo")
CATEGORIAS = ("local", "gratuito", "assinatura", "pago")
NIVEIS = ("leve", "intermediario", "forte", "revisor")


def carregar(caminho: Path = CONFIG) -> dict:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    for nome, p in dados["papeis"].items():
        if p["nivel"] not in NIVEIS:
            raise ValueError(f"nível inválido em {nome}")
        if not set(p["capacidades"]) <= set(PROVAS):
            raise ValueError(f"capacidade sem prova em {nome}")
        if not set(p["categorias"]) <= set(CATEGORIAS):
            raise ValueError(f"categoria inválida em {nome}")
        if p.get("independente_de") and p["independente_de"] not in dados["papeis"]:
            raise ValueError(f"independente_de desconhecido em {nome}")
    return dados["papeis"]


def familia(rota: dict) -> str:
    fam = (rota.get("independencia") or {}).get("familia")
    if fam:
        return str(fam).lower()
    return re.split(r"[/:]", rota.get("rota", "?"))[-1].split("-")[0].lower()


def resolver(papel: str, rotas: list[dict], aprovadas: dict[str, list[str]], *, escolhidas: dict[str, dict] | None = None,
             papeis: dict | None = None) -> dict | None:
    """Rota para o papel: permitida pelo orçamento, com as capacidades provadas, e de família diferente do
    papel de quem ela deve ser independente. `aprovadas` = rotas_que_passaram de testar_rotas (por prova)."""
    papeis = papeis or carregar()
    if papel not in papeis:
        raise ValueError("papel desconhecido")
    p = papeis[papel]
    exigidas = p["capacidades"] or []
    candidatas = []
    for r in sorted(rotas, key=lambda x: x["rota"]):
        if r.get("categoria") not in p["categorias"]:
            continue
        if any(r["rota"] not in aprovadas.get(cap, []) for cap in exigidas):
            continue
        candidatas.append(r)
    if p.get("independente_de") and escolhidas and p["independente_de"] in escolhidas:
        fam_base = familia(escolhidas[p["independente_de"]])
        candidatas = [r for r in candidatas if familia(r) != fam_base]
    return candidatas[0] if candidatas else None
