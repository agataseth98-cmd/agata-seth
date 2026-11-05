#!/usr/bin/env python3
"""Recuperação sem modelo (protocolo §4): precisão@k, recall@k e MRR por método, mesmo conjunto.

Métodos: `busca_texto` (o caminho atual), `alexandria` (léxico + relações) e
`alexandria+semantica` (busca por sentido sempre ligada). Usa as tarefas que têm `consulta` e
`relevantes` (números de entrada revisados). Paráfrase e termo exato saem separados pelo campo
`forma` da tarefa (`exata` | `parafrase`). Complementa `scripts/medir_recuperacao.py`, que mede o caso
fácil (palavras raras da própria nota) e continua valendo no seu alcance.

Grava no registro comum (`registro.py`). Uso: recuperacao.py [--split dev] [--k 5]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
for _p in (AQUI, REPO / "redesign" / "nova_versao", REPO / "redesign" / "alexandria", REPO / "scripts"):
    sys.path.insert(0, str(_p))
import conjunto  # noqa: E402
import registro  # noqa: E402

METODOS = ("busca_texto", "alexandria", "alexandria+semantica")
RE_ENTRADA = re.compile(r"^\((\d{1,4})\)\s")


def _entrada_de(raiz: Path, rel: str, linha: int, cache: dict) -> str | None:
    if rel not in cache:
        try:
            cache[rel] = (raiz / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            cache[rel] = []
    ls = cache[rel]
    for i in range(min(linha, len(ls)) - 1, -1, -1):
        m = RE_ENTRADA.match(ls[i])
        if m:
            return m.group(1)
    return None


def recuperar(metodo: str, consulta: str, k: int, *, raiz: Path = REPO, buscar=None, consultar=None) -> list[str]:
    """Lista ordenada de entradas (sem repetição) devolvidas pelo método."""
    out: list[str] = []
    if metodo == "busca_texto":
        if buscar is None:
            import busca_texto
            buscar = busca_texto.buscar
        cache: dict = {}
        for _n, rel, ln, _t in buscar(consulta)[0]:
            e = _entrada_de(raiz, rel, ln, cache)
            if e and e not in out:
                out.append(e)
    else:
        if consultar is None:
            import acervo
            consultar = acervo.consultar
        pac = consultar(consulta, n=k * 2, semantica="sempre" if metodo.endswith("semantica") else "nunca")
        for r in pac["resultados"]:
            e = str(r["entrada"]) if r.get("entrada") is not None else None
            if e and e not in out:
                out.append(e)
    return out[:k]


def medidas(achados: list[str], relevantes: set[str], k: int) -> dict:
    topo = achados[:k]
    acertos = [x for x in topo if x in relevantes]
    rr = next((1 / i for i, x in enumerate(topo, 1) if x in relevantes), 0.0)
    return {"p_at_k": round(len(acertos) / k, 4) if k else None,
            "recall_at_k": round(len(set(acertos)) / len(relevantes), 4) if relevantes else None, "rr": round(rr, 4)}


def rodar(split: str = "dev", k: int = 5, **kw) -> dict:
    ts = [t for t in conjunto.carregar(split) if t.get("consulta") and t.get("relevantes")]
    if not ts:
        raise ValueError("nenhuma tarefa com consulta e relevantes neste split")
    run = registro.abrir("recuperacao", split, registro.hash_conjunto(ts), extra={"k": k, "metodos": list(METODOS)})
    por = {}
    for m in METODOS:
        linhas_ = []
        for t in ts:
            try:
                ach = recuperar(m, t["consulta"], k, **kw)
                md = medidas(ach, set(t["relevantes"]), k)
                ln = registro.linha(run, task_id=t["task_id"], condition=m, model_id=None, outcome="passou" if md["rr"] else "falhou",
                                    evidence=ach, forma=t.get("forma", "exata"), **md)
            except Exception as e:  # noqa: BLE001 — endpoint de sentido fora entra como etapa, não como erro de recuperação
                ln = registro.linha(run, task_id=t["task_id"], condition=m, model_id=None, outcome="nao_rodou",
                                    failure_stage="indisponivel", forma=t.get("forma", "exata"), erro=e.__class__.__name__)
            linhas_.append(ln)
        por[m] = {}
        for forma in ("exata", "parafrase"):
            ls = [x for x in linhas_ if x["forma"] == forma and x["outcome"] != "nao_rodou"]
            por[m][forma] = {"n": len(ls),
                             "p_at_k": round(sum(x["p_at_k"] for x in ls) / len(ls), 4) if ls else None,
                             "recall_at_k": round(sum(x["recall_at_k"] for x in ls) / len(ls), 4) if ls else None,
                             "mrr": round(sum(x["rr"] for x in ls) / len(ls), 4) if ls else None}
        por[m]["nao_rodou"] = sum(x["outcome"] == "nao_rodou" for x in linhas_)
    return registro.fechar(run, {"k": k, "por_metodo": por,
                                 "nota": "relevância revisada só nas tarefas do conjunto; n pequeno não generaliza"})


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="dev", choices=conjunto.SPLITS)
    ap.add_argument("--k", type=int, default=5)
    a = ap.parse_args()
    r = rodar(a.split, a.k)
    print(json.dumps({"run_id": r["run_id"], **r["resumo"]}, ensure_ascii=False, indent=1))


def rodar_skills(tarefas: list[dict], selecionar=None, n: int = 3) -> dict:
    """Seleção de skill medida (protocolo §4; lote 5, B3): omissão, falso positivo e sucesso final, sem modelo.
    Cada tarefa tem `consulta` e `skill: {esperadas: [...], proibidas: [...]}`. Denominador zero dá None."""
    if selecionar is None:
        import skills  # noqa: E402
        selecionar = lambda q: skills.selecionar(q, n=n)  # noqa: E731
    casos = [t for t in tarefas if t.get("skill") and t.get("consulta")]
    if not casos:
        raise ValueError("nenhuma tarefa de seleção de skill")
    om = fp = ok = esperadas_total = proibidas_total = 0
    detalhe = []
    for t in casos:
        escolhidas = {c["nome"] for c in selecionar(t["consulta"])["candidatos"]}
        esp, pro = set(t["skill"].get("esperadas", [])), set(t["skill"].get("proibidas", []))
        omitidas, falsas = sorted(esp - escolhidas), sorted(pro & escolhidas)
        om += len(omitidas); fp += len(falsas); esperadas_total += len(esp); proibidas_total += len(pro)
        sucesso = not omitidas and not falsas
        ok += sucesso
        detalhe.append({"task_id": t.get("task_id"), "omitidas": omitidas, "falsas": falsas, "sucesso": sucesso})
    return {"n": len(casos),
            "omissao": round(om / esperadas_total, 4) if esperadas_total else None,
            "falso_positivo": round(fp / proibidas_total, 4) if proibidas_total else None,
            "sucesso": round(ok / len(casos), 4), "detalhe": detalhe}
