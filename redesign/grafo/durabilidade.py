#!/usr/bin/env python3
"""
Camada de durabilidade do loop da Fase 4 -- padrao decidido pelo spike P4-00
(ver redesign/grafo/DURABILIDADE.md, veredito OPCAO A).

- WAL append-only proprio: <dir>/eventos.ndjson, um registro "intent" ANTES de cada
  efeito externo e "done" DEPOIS, os.fsync em cada linha.
- idempotency key por (thread_id, node, passo): efeito so acontece 1x mesmo em re-run.
- replay(): reconstroi a DECISAO ("quais efeitos aconteceram") aplicando idempotencia --
  o WAL acumula "done" repetido no crash+resume e isso e' append-only correto.

O checkpointer do LangGraph (SqliteSaver) roda POR CIMA disto; a ordem obrigatoria em
todo no com efeito colateral e':
    wal(intent) -> checar idem key -> efeito -> wal(done) -> return   (ai o LangGraph checa-pointa)
"""
import hashlib
import json
import os
import time
from pathlib import Path


def idem_key(thread_id: str, node: str, passo) -> str:
    return hashlib.sha1(f"{thread_id}|{node}|{passo}".encode()).hexdigest()[:16]


def _fsync_append(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(line if line.endswith("\n") else line + "\n")
        f.flush()
        os.fsync(f.fileno())


class WAL:
    """Write-ahead log de eventos do loop. Um por diretorio de estado (por thread ou global)."""

    def __init__(self, dir_estado: str | os.PathLike):
        self.path = Path(dir_estado) / "eventos.ndjson"

    def registrar(self, thread_id: str, node: str, passo, fase: str, chave: str, **extra) -> None:
        rec = {"ts": round(time.time(), 3), "thread": thread_id, "node": node,
               "passo": passo, "fase": fase, "chave": chave}
        rec.update(extra)
        _fsync_append(self.path, json.dumps(rec, ensure_ascii=False))

    def intent(self, thread_id, node, passo, chave, **e):
        self.registrar(thread_id, node, passo, "intent", chave, **e)

    def done(self, thread_id, node, passo, chave, **e):
        self.registrar(thread_id, node, passo, "done", chave, **e)

    def replay(self, thread_id: str) -> dict:
        """Reconstroi a decisao so do WAL. Retorna raw (com repeticao) e dedup (a decisao)."""
        raw, decisao = [], []
        if not self.path.exists():
            return {"wal_done_raw": [], "decisao": [], "ultimo": None}
        for ln in self.path.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            e = json.loads(ln)
            if e.get("thread") == thread_id and e.get("fase") == "done":
                raw.append(e["chave"])
                if e["chave"] not in decisao:
                    decisao.append(e["chave"])
        return {"wal_done_raw": raw, "decisao": decisao,
                "ultimo": decisao[-1] if decisao else None}


def efeito_idempotente(wal: WAL, thread_id: str, node: str, passo, ja_feito, aplicar):
    """
    Executa `aplicar()` no maximo 1x para a chave (thread,node,passo).
    `ja_feito(chave) -> bool` diz se o efeito ja consta no mundo real (log/git/disco).
    Retorna (chave, "novo" | "pulado").
    """
    chave = idem_key(thread_id, node, passo)
    wal.intent(thread_id, node, passo, chave)
    if ja_feito(chave):
        estado = "pulado"
    else:
        aplicar(chave)
        estado = "novo"
    wal.done(thread_id, node, passo, chave)
    return chave, estado
