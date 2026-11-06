#!/usr/bin/env python3
"""MVP de autoaprimoramento governado (P2): pedido -> evidências -> proposta com digest -> revisão -> decisão humana.

Não aplica mudança nenhuma. A decisão só vale se o Humano informar o digest exato da proposta que leu.
Ferramenta de registro: grava arquivos em uma pasta de trabalho escolhida por quem chama.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DECISOES = ("aceita", "recusada")


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def criar_pedido(objetivo: str, arquivos: list[str]) -> dict:
    if not objetivo.strip():
        raise ValueError("pedido sem objetivo")
    if not arquivos:
        raise ValueError("pedido sem arquivos de escopo")
    for rel in arquivos:
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            raise ValueError(f"caminho fora do escopo: {rel!r}")
    pedido = {"objetivo": objetivo.strip(), "arquivos": sorted(arquivos)}
    pedido["id"] = _digest(pedido)[:16]
    return pedido


def coletar_evidencias(pedido: dict, raiz: Path = RAIZ) -> list[dict]:
    """Hash e tamanho de cada arquivo de escopo, na árvore dada. Arquivo ausente é registrado, não ignorado."""
    evid = []
    for rel in pedido["arquivos"]:
        p = raiz / rel
        if p.is_file():
            evid.append({"caminho": rel, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size})
        else:
            evid.append({"caminho": rel, "sha256": None, "bytes": 0, "ausente": True})
    return evid


def head_git(raiz: Path = RAIZ) -> str:
    try:
        return subprocess.run(["git", "-C", str(raiz), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True, timeout=10).stdout.strip()
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return "não medido"


def criar_proposta(pedido: dict, evidencias: list[dict], diff_texto: str, commit: str) -> dict:
    if not evidencias:
        raise ValueError("proposta sem evidência")
    if not diff_texto.strip():
        raise ValueError("proposta sem diff")
    corpo = {"pedido": pedido, "evidencias": evidencias, "diff": diff_texto, "commit_base": commit}
    return {**corpo, "digest": _digest(corpo)}


def salvar(proposta: dict, pasta: Path) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"proposta-{proposta['digest'][:16]}.json"
    tmp = destino.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(proposta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, destino)  # gravação atômica: nunca deixa arquivo pela metade no destino
    return destino


def registrar_decisao(proposta: dict, decisao: str, humano: str, digest_lido: str) -> dict:
    """Decisão humana. Recusa se o digest lido não for o da proposta, se o autor não for pessoa, ou se a decisão for inválida."""
    if decisao not in DECISOES:
        raise ValueError(f"decisão inválida: {decisao!r}")
    if not humano.strip() or humano.strip().lower() in ("modelo", "claude", "codex", "seth", "agente"):
        raise ValueError("decisão precisa de um humano identificado")
    if digest_lido != proposta["digest"]:
        raise ValueError("digest lido não bate com a proposta: decisão recusada")
    return {"digest": proposta["digest"], "decisao": decisao, "humano": humano.strip(), "aplicado": False}


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return 0 if _selftest() else 1
    print(__doc__)
    return 2


def _selftest() -> bool:
    p = criar_pedido("teste", ["README.md"])
    e = coletar_evidencias(p, RAIZ)
    pr = criar_proposta(p, e, "--- a\n+++ b\n", "abc")
    try:
        registrar_decisao(pr, "aceita", "humano", "0" * 64)
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
