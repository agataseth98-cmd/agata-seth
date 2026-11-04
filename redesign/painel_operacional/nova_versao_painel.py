#!/usr/bin/env python3
"""Nova versão do Agata no painel: Alexandria, skills, metacognição, corpo, orçamento e eventos.

Leitura em `estado()`; execução por lista fechada em `executar()`, uma por vez (lock).
A consulta vem do Humano pelo painel, limitada a 300 caracteres, e só vira pacote de
evidência (nunca comando). O orçamento só aceita os campos e limites de
`redesign/nova_versao/orcamento.py`; cada mudança vira evento no ledger.
Nada aqui escreve no repositório: os dados ficam em ~/.local/share/agata/nova-versao.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in ("nova_versao", "alexandria", "corpo", "metacognicao"):
    sys.path.insert(0, str(ROOT / "redesign" / _p))

ACOES = ("iniciar", "indexar", "consultar", "skills", "fotografar", "salvar_orcamento", "classificar")
_LOCK = threading.Lock()


def estado() -> dict:
    import nv  # noqa: E402
    return nv.estado()


def executar(acao, dados: dict | None = None) -> dict:
    if acao not in ACOES:
        raise ValueError("ação fora da lista")
    dados = dados if isinstance(dados, dict) else {}
    texto = dados.get("consulta")
    if acao in ("consultar", "skills", "classificar"):
        if not isinstance(texto, str) or not texto.strip() or len(texto) > 300:
            raise ValueError("consulta vazia ou longa demais")
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError("ocupado")
    try:
        if acao == "iniciar":
            import nv  # noqa: E402
            return {"acao": acao, "resultado": nv.iniciar()}
        if acao == "indexar":
            import acervo  # noqa: E402
            return {"acao": acao, "resultado": acervo.indexar(acervo.snapshot("HEAD", ROOT))}
        if acao == "consultar":
            import acervo  # noqa: E402
            sem = dados.get("semantica") if dados.get("semantica") in ("nunca", "auto", "sempre") else "auto"
            return {"acao": acao, "resultado": acervo.consultar(texto, semantica=sem, salvar=True)}
        if acao == "skills":
            import skills  # noqa: E402
            return {"acao": acao, "resultado": skills.selecionar(texto, n=5)}
        if acao == "classificar":
            import previo  # noqa: E402
            return {"acao": acao, "resultado": previo.classificar({"messages": [{"role": "user", "content": texto}]})}
        if acao == "fotografar":
            import fotografar  # noqa: E402
            import saude  # noqa: E402
            f = fotografar.fotografar()
            return {"acao": acao, "resultado": {"quando": f["quando"], **saude.classificar(f)}}
        import orcamento  # noqa: E402
        return {"acao": acao, "resultado": orcamento.salvar(dados.get("orcamento") or {})}
    finally:
        _LOCK.release()
