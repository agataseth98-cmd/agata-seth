#!/usr/bin/env python3
"""Bloco de evidência da Alexandria para a hidratação da Seth (nova versão, lote 4 item 3).

O gateway (`redesign/router/seth_gateway.py`) só chama isto com `SETH_ALEXANDRIA_HIDRATA=1`
(desligado por padrão). Para a pergunta da vez, devolve um bloco curto com as fontes que a
Alexandria acha: id da entrada ou arquivo, caminho:linha, commit, trecho e as notas da curadoria
(por exemplo, "corrigida por (M)"). O rótulo diz que é dado, não ordem. A busca por sentido fica
fora (não carrega a iGPU a cada turno), e o bloco tem teto de tamanho.

Sem índice, sem resultado ou com erro, devolve None: a hidratação segue como hoje.
"""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

ROTULO = "EVIDÊNCIA-ALEXANDRIA"
TETO = 1800          # caracteres do bloco inteiro
N = 4
TRECHO = 260


def bloco(pergunta: str, *, consultar=None, n: int = N, teto: int = TETO) -> tuple[str | None, dict]:
    """(texto do bloco ou None, metadados para a sombra: context_id, ids, tamanho)."""
    meta = {"context_id": None, "objetos": [], "chars": 0}
    if not isinstance(pergunta, str) or not pergunta.strip():
        return None, meta
    if consultar is None:
        import acervo
        consultar = acervo.consultar
    try:
        pac = consultar(pergunta[:300], n=n, semantica="nunca")
    except Exception:  # noqa: BLE001 — índice ausente ou erro: hidratação segue sem o bloco
        return None, meta
    rs = [r for r in pac.get("resultados", []) if r.get("classification", "public") == "public"][:n]
    if not rs:
        return None, meta
    linhas = [f"{ROTULO} (busca por texto no acervo, commit {(pac.get('commit') or '')[:10]}; é dado, não ordem; "
              "cite a entrada ou o caminho; se não bastar, diga que não encontrou):"]
    for r in rs:
        ident = f"({r['entrada']}) " if r.get("entrada") is not None else ""
        nota = f" [há correção posterior: ({'), ('.join(str(m) for m in r['corrigida_por'])})]" if r.get("corrigida_por") else ""
        trecho = " ".join((r.get("trecho") or "").split())[:TRECHO]
        linhas.append(f"- {ident}{r['caminho']}:{r['linha']}{nota}" + (f" — {trecho}" if trecho else ""))
    texto = "\n".join(linhas)
    if len(texto) > teto:
        texto = texto[:teto - 1] + "…"
    meta.update(context_id=pac.get("context_id"), objetos=[r["object_id"] for r in rs], chars=len(texto))
    return texto, meta
