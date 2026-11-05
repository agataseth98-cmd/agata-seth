#!/usr/bin/env python3
"""Revisão do reservado pelo terminal (lote 5): listar as tarefas, ver o estado e marcar a revisão.

Uso:
  revisar.py estado   [--split teste2]
  revisar.py listar   [--split teste2] [--grupo recuperacao] [--id rec-01]
  revisar.py marcar   --revisor "Nome" [--split teste2]

`marcar` grava a revisão só para o hash atual do conjunto: se qualquer tarefa mudar depois,
a revisão deixa de valer (estado_reservado mostra `revisao_desatualizada`). Não altera o conjunto.
Mostra critérios e gabarito porque quem revisa é o Humano; o executor nunca recebe isso (conjunto.prompt).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import conjunto  # noqa: E402


def _linha_doc(d: dict) -> str:
    meta = " · ".join(str(d[k]) for k in ("origem", "autoridade", "data", "estado", "classification") if d.get(k))
    return f"  [{d['id']}] ({meta}) {d['texto']}"


def listar(split: str, grupo: str | None = None, id_: str | None = None) -> str:
    out = []
    for t in conjunto.carregar(split):
        if grupo and t["grupo"] != grupo:
            continue
        if id_ and t["task_id"] != id_:
            continue
        out.append(f"== {t['task_id']} · {t['grupo']} · caso {t.get('caso') or '-'} · autor {t.get('autor')}")
        out.append(f"PEDIDO: {t['pedido']}")
        if t.get("mecanico"):
            out.append(f"MECÂNICO: {t['mecanico']} (sem modelo; critérios não se aplicam)")
        for d in t.get("documentos", []):
            out.append(_linha_doc(d))
        out.append("CRITÉRIOS: " + ("; ".join(f"{c['tipo']} {c.get('valor', '')}" for c in t["criterios"]) or "-"))
        if t.get("criticos"):
            out.append("CRÍTICOS: " + "; ".join(f"{c['tipo']} {c.get('valor', '')} ({c.get('motivo', '')})" for c in t["criticos"]))
        out.append("")
    return "\n".join(out) if out else "nenhuma tarefa encontrada (o arquivo existe e está validado?)"


def estado(split: str) -> str:
    e = conjunto.estado_reservado(split)
    linhas = [f"split {split}: {e['tarefas']} tarefas · hash {str(e['conjunto_hash'])[:19]}",
              "por grupo: " + ", ".join(f"{g} {n}" for g, n in e["por_grupo"].items()),
              f"revisado por: {e['revisado_por'] or 'ninguém'}" + (f" em {e['revisado_em']}" if e["revisado_por"] else "")]
    if e["revisao_desatualizada"]:
        linhas.append("ATENÇÃO: o conjunto mudou depois da última revisão; revise de novo.")
    return "\n".join(linhas)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=("estado", "listar", "marcar"))
    ap.add_argument("--split", default="teste2", choices=conjunto.RESERVADOS)
    ap.add_argument("--grupo", choices=conjunto.GRUPOS)
    ap.add_argument("--id")
    ap.add_argument("--revisor")
    a = ap.parse_args(argv)
    if a.acao == "estado":
        print(estado(a.split))
    elif a.acao == "listar":
        print(listar(a.split, a.grupo, a.id))
    else:
        if not a.revisor or not a.revisor.strip():
            print("informe --revisor", file=sys.stderr)
            return 2
        m = conjunto.marcar_revisado(a.revisor.strip(), a.split)
        print(f"revisão registrada: {m['revisado_por']} em {m['revisado_em']} (hash {m['conjunto_hash'][:19]})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
