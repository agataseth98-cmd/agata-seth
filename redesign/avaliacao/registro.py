#!/usr/bin/env python3
"""Registro por execução, comum a todo medidor da nova versão (Experimento GPT, protocolo §5).

Um `run_id` agrupa as linhas de uma rodada; cada linha é um item (tarefa × condição × rota ×
repetição) com o esquema do protocolo: split, condition, model_id, corpus_snapshot, context_id,
seed, budget, usage, latency_ms, outcome, failure_stage, critical_failure, evidence, reviewer,
rubric_version. Contagem que o provedor não deu fica `null`; nada é estimado em silêncio.

Arquivos: `<dados>/avaliacao/execucoes/<run_id>.jsonl` (linhas) e `<run_id>.resumo.json`
(métricas). O ledger recebe só o evento da rodada, com hashes, nunca o texto.
Usado por `avaliar.py` e `recuperacao.py`; outro medidor (teste_portugues, seth_autodev)
adota o mesmo formato chamando `abrir()`/`linha()`/`fechar()`.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
sys.path.insert(0, str(REPO / "redesign" / "nova_versao"))
import eventos  # noqa: E402

SCHEMA = 1
SPLITS = ("dev", "calibracao", "teste", "teste2")
OUTCOMES = ("pending", "passou", "falhou", "absteve", "nao_rodou")
RE_RUN = re.compile(r"r-\d{8}-\d{6}-[0-9a-f]{6}")
FAILURE_STAGES = (None, "transporte", "indisponivel", "orcamento", "privacidade", "custo", "configuracao",
                  "autorizacao", "cancelada", "prazo", "recuperacao", "raciocinio", "execucao")


def pasta() -> Path:
    p = eventos.dados() / "avaliacao" / "execucoes"
    p.mkdir(parents=True, exist_ok=True)
    return p


def commit(repo: Path = REPO) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=10, check=True).stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def hash_conjunto(tarefas: list[dict]) -> str:
    canon = json.dumps(sorted(tarefas, key=lambda t: t["task_id"]), ensure_ascii=False, sort_keys=True)
    return "sha256:" + hashlib.sha256(canon.encode()).hexdigest()


def abrir(medidor: str, split: str, conjunto_hash: str, *, extra: dict | None = None) -> dict:
    if split not in SPLITS:
        raise ValueError("split fora da lista")
    run_id = "r-" + time.strftime("%Y%m%d-%H%M%S") + "-" + os.urandom(3).hex()
    run = {"schema_version": SCHEMA, "run_id": run_id, "medidor": medidor, "split": split, "commit": commit(),
           "conjunto_hash": conjunto_hash, "inicio": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **(extra or {})}
    (pasta() / f"{run_id}.jsonl").touch()
    return run


def linha(run: dict, *, task_id: str, condition: str, model_id: str | None, outcome: str, failure_stage=None,
          critical_failure: bool = False, seed=None, usage: dict | None = None, latency_ms=None, context_id=None,
          corpus_snapshot=None, skill_versions=None, tools=None, evidence=None, budget=None, rubric_version=None,
          reviewer=None, **campos) -> dict:
    if outcome not in OUTCOMES:
        raise ValueError("outcome fora da lista")
    if failure_stage not in FAILURE_STAGES:
        failure_stage = "execucao"
    u = usage or {}
    reg = {"schema_version": SCHEMA, "run_id": run["run_id"], "task_id": task_id, "split": run["split"],
           "condition": condition, "model_id": model_id, "model_version": None,
           "corpus_snapshot": corpus_snapshot or run.get("commit"), "context_id": context_id,
           "skill_versions": skill_versions or [], "seed": seed,
           "budget": budget or {"max_calls": None, "max_tokens": None, "timeout_seconds": None},
           "usage": {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
                     "reasoning_tokens": u.get("reasoning_tokens"), "cache_tokens": u.get("cache_tokens")},
           "latency_ms": latency_ms, "tools": tools or [], "outcome": outcome, "failure_stage": failure_stage,
           "critical_failure": bool(critical_failure), "evidence": evidence or [], "reviewer": reviewer,
           "rubric_version": rubric_version, "correction_event": None, **campos}
    with open(pasta() / f"{run['run_id']}.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(reg, ensure_ascii=False) + "\n")
    return reg


def fechar(run: dict, resumo: dict, *, estado: str = "concluida") -> dict:
    run = dict(run, fim=time.strftime("%Y-%m-%dT%H:%M:%S%z"), estado=estado, resumo=resumo)
    destino = pasta() / f"{run['run_id']}.resumo.json"
    tmp = destino.with_suffix(".tmp")
    tmp.write_text(json.dumps(run, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, destino)
    eventos.registrar("verification", estado, f"avaliacao:{run['run_id']}", componente="avaliacao",
                      chave=f"avaliacao:{run['run_id']}", medidor=run["medidor"], split=run["split"],
                      conjunto_hash=run["conjunto_hash"], commit=run.get("commit"))
    return run


def linhas(run_id: str) -> list[dict]:
    if not isinstance(run_id, str) or not RE_RUN.fullmatch(run_id):
        raise ValueError("run_id inválido")
    base = os.path.realpath(pasta())
    alvo = os.path.normpath(os.path.join(base, run_id + ".jsonl"))
    if not alvo.startswith(base + os.sep):
        raise ValueError("caminho fora das execuções")
    p = Path(alvo)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def listar(n: int = 10) -> list[dict]:
    arqs = sorted(pasta().glob("r-*.resumo.json"), reverse=True)[:n]
    return [json.loads(a.read_text(encoding="utf-8")) for a in arqs]
