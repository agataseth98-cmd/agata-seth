#!/usr/bin/env python3
"""Orçamento de inferência da nova versão, editado pelo painel.

Decisão do Humano (04/11/2026): "tudo que estiver disponível, configurável pelo painel".
Este arquivo guarda QUAIS provedores podem ser usados e com QUAL teto. O padrão de
fábrica é só local, porque nenhum provedor remoto foi escolhido ainda. Quem muda é o
Humano, pelo painel. Cada mudança vira evento no ledger, com o valor anterior e o novo.

No lote 1 ninguém consome inferência: o orçamento é lido e mostrado. `permite()` é a
porta que os lotes 2 e 3 vão consultar antes de chamar qualquer modelo.

Arquivo: `<dados>/config/orcamento.json` (fora do repo; sem segredo, só política).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import eventos  # noqa: E402

PROVEDORES = ("local", "gratuito", "assinatura", "pago")  # assinatura = CLI do plano do usuário (cota, não R$)
PADRAO = {"schema_version": 1, "provedores": {"local": True, "gratuito": False, "assinatura": False, "pago": False},
          "max_chamadas": 200, "max_tokens": 2_000_000, "timeout_s": 120, "teto_reais": 0.0}
LIMITES = {"max_chamadas": (0, 100000), "max_tokens": (0, 50_000_000), "timeout_s": (1, 3600), "teto_reais": (0.0, 10000.0)}


def caminho() -> Path:
    return eventos.dados() / "config" / "orcamento.json"


def ler() -> dict:
    try:
        d = json.loads(caminho().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return json.loads(json.dumps(PADRAO))
    return validar(d)


def validar(d: dict) -> dict:
    if not isinstance(d, dict):
        raise ValueError("orçamento inválido")
    prov = d.get("provedores") or {}
    if not isinstance(prov, dict) or set(prov) - set(PROVEDORES):
        raise ValueError("provedor fora da lista")
    out = {"schema_version": 1, "provedores": {p: bool(prov.get(p, PADRAO["provedores"][p])) for p in PROVEDORES}}
    for campo, (lo, hi) in LIMITES.items():
        v = d.get(campo, PADRAO[campo])
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError(f"{campo} não é número")
        if not lo <= v <= hi:
            raise ValueError(f"{campo} fora do limite [{lo}, {hi}]")
        out[campo] = float(v) if campo == "teto_reais" else int(v)
    return out


def salvar(novo: dict, actor: str = "humano-painel") -> dict:
    """Grava atômico e registra o evento (antes -> depois)."""
    novo = validar(novo)
    antes = ler()
    if novo == antes:
        return {**novo, "mudou": False}
    p = caminho()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".orcamento.")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(novo, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)
    eventos.registrar("decision", "aplicada", "orcamento", actor=actor, componente="orcamento", antes=antes, depois=novo)
    return {**novo, "mudou": True}


def permite(provedor: str, chamadas_ja: int = 0) -> tuple[bool, str]:
    """Porta para os lotes 2 e 3: pode chamar este provedor agora?"""
    o = ler()
    if provedor not in PROVEDORES:
        return False, "provedor fora da lista"
    if not o["provedores"][provedor]:
        return False, f"provedor '{provedor}' desligado no painel"
    if chamadas_ja >= o["max_chamadas"]:
        return False, "teto de chamadas atingido"
    if provedor == "pago" and o["teto_reais"] <= 0:
        return False, "pago ligado sem teto em R$: nada é gasto"
    return True, "permitido"


if __name__ == "__main__":
    print(json.dumps(ler(), ensure_ascii=False, indent=1))
