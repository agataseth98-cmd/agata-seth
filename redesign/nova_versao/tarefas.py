#!/usr/bin/env python3
"""Coordenação da nova versão — tarefas com versão de contexto, orçamento, cancelamento e
fila de GPU (Experimento GPT, conclusões (048), (054)–(055), (071); Alexandria §10).

- Cada tarefa tem `task_id`, `contexto_versao` (commit do repo ao criar), prazo e teto
  de chamadas. Estados: criada → em_execucao → concluida, com saídas falhou, cancelada e
  em_revisao (quando o contexto mudou durante a execução: o resultado é marcado obsoleto e
  volta à verificação, nunca é consolidado em silêncio).
- Itens independentes podem rodar em paralelo (threads); itens marcados como `gpu`
  passam por UMA trava de arquivo (duas tags na mesma GPU não são dois recursos).
- Cancelar (`cancelar(task_id)`) impede que novos itens comecem; o que já rodou fica
  registrado.
- Escritor único: só a thread principal grava o arquivo da tarefa (troca atômica) e os
  eventos no ledger; os trabalhadores só devolvem resultado. Chave idempotente por item.
- Papéis (hidratador, recuperador, revisor, vigia...) são funções passadas aqui, não
  serviços: nada de uma LLM por papel ((039)–(040)).

Reaproveita o padrão de `redesign/grafo/durabilidade.py` (intenção antes do efeito,
registro depois) e o `evidence_ledger` (via `eventos.py`).
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import eventos  # noqa: E402

ESTADOS = ("criada", "em_execucao", "em_revisao", "concluida", "falhou", "cancelada", "aguardando_humano")


def _pasta() -> Path:
    return eventos.dados() / "coordenacao" / "tarefas"


def _gpu_lock() -> Path:
    return Path(os.environ.get("AGATA_NV_CACHE", Path.home() / ".cache" / "agata" / "nova-versao")) / "gpu.lock"


def versao_contexto(repo: Path = REPO) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=10).stdout.strip() or "sem-git"
    except (OSError, subprocess.TimeoutExpired):
        return "sem-git"


def _gravar(t: dict) -> None:
    p = _pasta() / f"{t['task_id']}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(t, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def criar(tipo: str, itens: list[dict], *, max_chamadas: int, prazo_s: int, repo: Path = REPO) -> dict:
    tid = "t-" + time.strftime("%Y%m%d-%H%M%S") + "-" + hashlib.sha256(os.urandom(8)).hexdigest()[:6]
    t = {"task_id": tid, "tipo": tipo, "estado": "criada", "contexto_versao": versao_contexto(repo),
         "criada_em": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "prazo_s": prazo_s, "max_chamadas": max_chamadas,
         "itens": itens, "resultados": {}, "chamadas": 0, "obsoleto": False}
    _gravar(t)
    eventos.registrar("execution", "criada", f"tarefa:{tid}", componente="coordenacao", tipo=tipo, n_itens=len(itens))
    return t


def cancelar(task_id: str) -> None:
    (_pasta() / f"{task_id}.cancelar").parent.mkdir(parents=True, exist_ok=True)
    (_pasta() / f"{task_id}.cancelar").write_text(time.strftime("%Y-%m-%dT%H:%M:%S%z"), encoding="utf-8")


def ler(task_id: str) -> dict | None:
    try:
        return json.loads((_pasta() / f"{task_id}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def listar(n: int = 10) -> list[dict]:
    arqs = sorted(_pasta().glob("t-*.json"))[-n:] if _pasta().exists() else []
    out = []
    for a in arqs:
        t = json.loads(a.read_text(encoding="utf-8"))
        out.append({k: t[k] for k in ("task_id", "tipo", "estado", "criada_em", "chamadas", "obsoleto")})
    return out


def executar(t: dict, funcao, *, paralelo: bool = True, max_workers: int = 3, repo: Path = REPO) -> dict:
    """`funcao(item) -> dict`. Item com `"recurso": "gpu"` passa pela trava da GPU."""
    t = dict(t, estado="em_execucao", inicio=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    _gravar(t)
    fim = time.monotonic() + t["prazo_s"]
    flag = _pasta() / f"{t['task_id']}.cancelar"
    lock = _gpu_lock()
    lock.parent.mkdir(parents=True, exist_ok=True)
    pendentes = [i for i in t["itens"] if i["chave"] not in t["resultados"]]

    def rodar(item):
        if flag.exists():
            return item["chave"], {"ok": False, "falha_etapa": "cancelada", "erro": "tarefa cancelada antes de começar"}
        if time.monotonic() > fim:
            return item["chave"], {"ok": False, "falha_etapa": "prazo", "erro": "prazo da tarefa esgotado"}
        try:
            if item.get("recurso") == "gpu":
                with open(lock, "w") as fh:
                    fcntl.flock(fh, fcntl.LOCK_EX)
                    try:
                        return item["chave"], funcao(item)
                    finally:
                        fcntl.flock(fh, fcntl.LOCK_UN)
            return item["chave"], funcao(item)
        except Exception as e:  # noqa: BLE001 — falha de um item não derruba a tarefa
            return item["chave"], {"ok": False, "falha_etapa": "execucao", "erro": f"{e.__class__.__name__}: {str(e)[:160]}"}

    # teto de chamadas: só entram itens até o teto; os demais ficam registrados como não rodados
    cabem = max(t["max_chamadas"] - t["chamadas"], 0)
    agora, fora = pendentes[:cabem], pendentes[cabem:]
    remotos = [i for i in agora if i.get("recurso") != "gpu"]
    locais = [i for i in agora if i.get("recurso") == "gpu"]
    resultados = []
    if paralelo and remotos:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futuros = [ex.submit(rodar, i) for i in remotos]
            resultados += [rodar(i) for i in locais]   # GPU em série, na thread principal
            resultados += [f.result() for f in futuros]
    else:
        resultados += [rodar(i) for i in remotos + locais]
    for chave, r in resultados:                         # escritor único
        t["resultados"][chave] = r
        if r.get("falha_etapa") not in ("cancelada", "prazo", "orcamento", "privacidade", "configuracao", "custo", "autorizacao"):
            t["chamadas"] += 1
    for i in fora:
        t["resultados"][i["chave"]] = {"ok": False, "falha_etapa": "orcamento", "erro": "teto de chamadas da tarefa"}
    t["fim"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    if versao_contexto(repo) != t["contexto_versao"]:
        t["obsoleto"] = True
        t["estado"] = "em_revisao"
    elif flag.exists():
        t["estado"] = "cancelada"
    else:
        t["estado"] = "concluida"
    _gravar(t)
    eventos.registrar("execution", t["estado"], f"tarefa:{t['task_id']}", componente="coordenacao",
                      chamadas=t["chamadas"], obsoleto=t["obsoleto"], chave=f"fim:{t['task_id']}")
    return t
