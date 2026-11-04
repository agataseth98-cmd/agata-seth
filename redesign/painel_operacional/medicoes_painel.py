#!/usr/bin/env python3
"""Medições pesadas no painel: recuperação da busca e comprimento efetivo de contexto.

Só roda os dois scripts de medição, de lista fechada; o modelo vem da lista de tags do Ollama local (nunca
do texto da requisição), um trabalho por vez, em segundo plano. Resultados ficam em AGATA_MEDICOES_DIR
(padrão ~/.cache/agata/painel/medicoes), fora do repositório. Nada aqui escreve no repositório.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLLAMA_TAGS = "http://127.0.0.1:11434/api/tags"
ACOES = ("recuperacao", "recuperacao_semantica", "contexto")
TAREFAS = ("agulha", "varias", "rastreio", "agregacao")
RACIOCINIO = ("desligado", "ligado")
TIMEOUT_S = {"recuperacao": 300, "recuperacao_semantica": 300, "contexto": 3600}
_LOCK = threading.Lock()
_JOB: dict = {"estado": "ocioso"}


def pasta() -> Path:
    return Path(os.environ.get("AGATA_MEDICOES_DIR", Path.home() / ".cache" / "agata" / "painel" / "medicoes"))


def modelos_locais() -> list[str]:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS, timeout=3) as r:
            tags = [m["name"] for m in json.loads(r.read()).get("models", [])]
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return []
    return sorted(t for t in tags if isinstance(t, str) and "embed" not in t.lower())


def _ler(arq: Path) -> dict | None:
    try:
        return json.loads(arq.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def resultados() -> dict:
    p = pasta()
    return {"recuperacao": _ler(p / "recuperacao.json"), "recuperacao_semantica": _ler(p / "recuperacao-semantica.json"),
            "contexto": [d for d in (_ler(a) for a in sorted(p.glob("contexto-*.json"))) if d]}


def estado() -> dict:
    with _LOCK:
        job = dict(_JOB)
    return {"schema_version": 1, "job": job, "modelos": modelos_locais(), **resultados()}


def _rodar(acao: str, argv: list[str]) -> None:
    inicio = time.time()
    try:
        r = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT_S[acao],
                           env={**os.environ, "AGATA_MEDICOES_DIR": str(pasta())})
        texto = "" if r.returncode == 0 else (r.stderr or r.stdout).strip()
        novo = {"estado": "ok" if r.returncode == 0 else "falhou", "codigo": r.returncode,
                "detalhe": texto.splitlines()[-1][:200] if texto else ""}
    except subprocess.TimeoutExpired:
        novo = {"estado": "falhou", "codigo": 124, "detalhe": f"tempo esgotado ({TIMEOUT_S[acao]} s)"}
    except OSError as exc:
        novo = {"estado": "falhou", "codigo": 127, "detalhe": str(exc)[:200]}
    with _LOCK:
        _JOB.update(novo, fim=time.time(), segundos=round(time.time() - inicio, 1))


def executar(acao: str, modelo: str | None = None, sincrono: bool = False, tarefa: str | None = None, raciocinio: str | None = None) -> dict:
    if acao not in ACOES:
        raise ValueError("ação fora da lista")
    escolhido, tarefa_ok, raciocinio_ok = None, None, RACIOCINIO[0]
    if acao == "contexto":
        if tarefa not in (None, *TAREFAS):
            raise ValueError("tarefa fora da lista")
        tarefa_ok = TAREFAS[TAREFAS.index(tarefa or "agulha")]
        if raciocinio not in (None, *RACIOCINIO):
            raise ValueError("raciocínio fora da lista")
        raciocinio_ok = RACIOCINIO[RACIOCINIO.index(raciocinio or "desligado")]
        permitidos = {m: m for m in modelos_locais()}
        if not isinstance(modelo, str) or modelo not in permitidos:
            raise ValueError("modelo fora da lista do Ollama local")
        escolhido = permitidos[modelo]  # só valor vindo do Ollama segue adiante
    acao = ACOES[ACOES.index(acao)]
    with _LOCK:
        if _JOB.get("estado") == "rodando":
            raise RuntimeError("ocupado")
        _JOB.clear(); _JOB.update(estado="rodando", acao=acao, modelo=escolhido, tarefa=tarefa_ok, raciocinio=raciocinio_ok if escolhido else None, inicio=time.time())
    argv = [sys.executable, str(ROOT / "scripts" / ("medir_contexto_efetivo.py" if acao == "contexto" else "medir_recuperacao.py")), "--salvar"]
    if acao == "recuperacao_semantica":
        argv.append("--semantico")
    if escolhido:
        argv += ["--modelo", escolhido, "--tarefa", tarefa_ok]
        if raciocinio_ok == "ligado":
            argv.append("--raciocinio")
    if sincrono:
        _rodar(acao, argv)
    else:
        threading.Thread(target=_rodar, args=(acao, argv), daemon=True).start()
    return estado()
