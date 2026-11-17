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
# Trava COMUM das medições de recuperação da busca (17/11/2026, D8): este painel e a nova versão
# (nova_versao_painel, medir_recuperacao) não rodam ao mesmo tempo. Quem chega com ela ocupada recebe o motivo.
TRAVA_RECUPERACAO = threading.Lock()
MOTIVO_OCUPADO = "ocupado"
MOTIVO_RECUPERACAO_OCUPADA = "medição de recuperação da busca já em curso (painel de medições ou conjunto da nova versão)"
MOTIVOS_OCUPADO = (MOTIVO_OCUPADO, MOTIVO_RECUPERACAO_OCUPADA)
ACOES_RECUPERACAO = ("recuperacao", "recuperacao_semantica")


def motivo_ocupado(exc: BaseException) -> str:
    """Só devolve motivo fixo conhecido; qualquer outro texto de erro vira 'ocupado' (não ecoa detalhe interno)."""
    texto = str(exc)
    return texto if texto in MOTIVOS_OCUPADO else MOTIVO_OCUPADO


def pasta() -> Path:
    return Path(os.environ.get("AGATA_MEDICOES_DIR", Path.home() / ".cache" / "agata" / "painel" / "medicoes"))


MOTIVO_MODELOS_SEM_LEITURA = "servidor de modelos locais parado ou sem resposta; a lista não foi lida"


def modelos_locais(leitura: dict | None = None) -> list[str]:
    """Modelos do Ollama local. Se a consulta falhar, devolve [] e, quando `leitura` é dado, marca nele `erro`."""
    try:
        with urllib.request.urlopen(OLLAMA_TAGS, timeout=3) as r:
            tags = [m["name"] for m in json.loads(r.read()).get("models", [])]
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError):
        if leitura is not None:
            leitura["erro"] = MOTIVO_MODELOS_SEM_LEITURA
        return []
    if leitura is not None:
        leitura["erro"] = None
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
    leitura: dict = {}
    modelos = modelos_locais(leitura)
    falhou = bool(leitura.get("erro"))
    return {"schema_version": 1, "job": job, "modelos": modelos,
            "modelos_estado": "sem_leitura" if falhou else "ok",
            "modelos_motivo": leitura.get("erro") if falhou else None,
            **resultados()}


def _rodar(acao: str, argv: list[str], com_trava: bool = False) -> None:
    """Roda o script de medição. Com `com_trava`, libera a trava comum de recuperação ao terminar, mesmo com erro."""
    inicio = time.time()
    novo = {"estado": "falhou", "codigo": 1, "detalhe": "medição interrompida"}
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
    finally:
        with _LOCK:
            _JOB.update(novo, fim=time.time(), segundos=round(time.time() - inicio, 1))
        if com_trava:
            TRAVA_RECUPERACAO.release()


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
    recuperacao = acao in ACOES_RECUPERACAO
    if recuperacao and not TRAVA_RECUPERACAO.acquire(blocking=False):
        raise RuntimeError(MOTIVO_RECUPERACAO_OCUPADA)
    try:
        with _LOCK:
            if _JOB.get("estado") == "rodando":
                raise RuntimeError(MOTIVO_OCUPADO)
            _JOB.clear(); _JOB.update(estado="rodando", acao=acao, modelo=escolhido, tarefa=tarefa_ok, raciocinio=raciocinio_ok if escolhido else None, inicio=time.time())
    except BaseException:
        if recuperacao:
            TRAVA_RECUPERACAO.release()
        raise
    argv = [sys.executable, str(ROOT / "scripts" / ("medir_contexto_efetivo.py" if acao == "contexto" else "medir_recuperacao.py")), "--salvar"]
    if acao == "recuperacao_semantica":
        argv.append("--semantico")
    if escolhido:
        argv += ["--modelo", escolhido, "--tarefa", tarefa_ok]
        if raciocinio_ok == "ligado":
            argv.append("--raciocinio")
    if sincrono:
        _rodar(acao, argv, recuperacao)  # libera a trava ao terminar, mesmo com erro
    else:
        try:
            threading.Thread(target=_rodar, args=(acao, argv, recuperacao), daemon=True).start()
        except BaseException:
            if recuperacao:
                TRAVA_RECUPERACAO.release()
            raise
    return estado()
