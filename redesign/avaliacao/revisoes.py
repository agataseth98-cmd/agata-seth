"""Revisão humana da rubrica semântica, às cegas (protocolo §2; lote 5, B3).

`cegas(run_id)` mostra pedido, documentos e resposta, com um rótulo que não revela condição nem rota.
`registrar(run_id, rotulo, veredito, revisor)` guarda o veredito humano em `avaliacao/revisoes/<run_id>.jsonl`.
`resumo(run_id)` conta, sem revelar. Só depois de tudo revisado, `revelar` mostra a condição e a rota de cada rótulo.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
for _p in (AQUI, AQUI.parents[1] / "nova_versao"):
    sys.path.insert(0, str(_p))
import caminhos  # noqa: E402
import conjunto  # noqa: E402
import eventos  # noqa: E402
import registro  # noqa: E402

VEREDITOS = ("ok", "parcial", "falhou", "nao_aplica")


def _pasta() -> Path:
    p = eventos.dados() / "avaliacao" / "revisoes"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _arquivo(run_id: str) -> Path:
    caminhos.id_seguro(run_id, caminhos.RE_RUN)
    return caminhos.dentro(_pasta(), run_id + ".jsonl")


def _rotulo(run_id: str, linha: dict) -> str:
    return "R" + hashlib.sha256(f"{run_id}|{linha['task_id']}|{linha['condition']}|{linha['rota']}".encode()).hexdigest()[:8]


def _linhas_avaliaveis(run_id: str) -> list[dict]:
    return [x for x in registro.linhas(run_id) if x.get("condition") != "mecanico" and x.get("outcome") != "nao_rodou"]


def cegas(run_id: str) -> list[dict]:
    split = next((r["split"] for r in registro.listar(50) if r.get("run_id") == run_id), None)
    tarefas = {t["task_id"]: t for t in conjunto.carregar(split)} if split else {}
    out = []
    for x in _linhas_avaliaveis(run_id):
        t = tarefas.get(x["task_id"], {})
        out.append({"rotulo": _rotulo(run_id, x), "pedido": t.get("pedido"), "documentos": t.get("documentos", []),
                    "resposta": x.get("resposta")})
    return out


def registrar(run_id: str, rotulo: str, veredito: str, revisor: str) -> dict:
    if veredito not in VEREDITOS:
        raise ValueError("veredito fora da lista")
    if not (revisor or "").strip():
        raise ValueError("revisor obrigatório")
    alvo = {_rotulo(run_id, x): x for x in _linhas_avaliaveis(run_id)}
    if rotulo not in alvo:
        raise ValueError("rótulo desconhecido para este run")
    reg = {"rotulo": rotulo, "veredito": veredito, "revisor": revisor.strip()[:60],
           "em": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "rubric_version": conjunto.RUBRICA}
    with open(_arquivo(run_id), "a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    return reg


def resumo(run_id: str) -> dict:
    total = len(_linhas_avaliaveis(run_id))
    feitos = {}
    arq = _arquivo(run_id)
    if arq.exists():
        for l in arq.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            feitos[r["rotulo"]] = r["veredito"]            # o último veredito de cada rótulo vale
    ok = sum(v == "ok" for v in feitos.values())
    aplicaveis = sum(v != "nao_aplica" for v in feitos.values())
    return {"run_id": run_id, "total": total, "revisados": len(feitos), "pendentes": total - len(feitos),
            "taxa_ok": round(ok / aplicaveis, 4) if aplicaveis else None}


def revelar(run_id: str) -> dict:
    """Mostra condição e rota de cada rótulo, e só quando tudo foi revisado."""
    r = resumo(run_id)
    if r["pendentes"]:
        raise PermissionError(f"ainda faltam {r['pendentes']} revisões")
    return {_rotulo(run_id, x): {"task_id": x["task_id"], "condicao": x["condition"], "rota": x["rota"]}
            for x in _linhas_avaliaveis(run_id)}
