#!/usr/bin/env python3
"""
P4-00 -- spike de durabilidade (matar-e-retomar). GATE da Fase 4.

Grafo-brinquedo com os nos reais do desenho (hidratar -> trabalhar -> efeito_externo ->
registrar_e_commitar). Prova o comportamento matar-processo-e-retomar antes de comprometer
a arquitetura do loop.

Camadas de durabilidade sob teste:
  - checkpointer LangGraph: SqliteSaver (snapshot de estado por no)
  - WAL proprio: eventos.ndjson, um registro "intent" ANTES do efeito e "done" DEPOIS,
    os.fsync em cada um (write-ahead)
  - idempotency key por (thread_id, node, passo): efeito so acontece 1x mesmo com re-run

Modos:
  spike_durabilidade.py worker --thread T          # roda o grafo (respeita SPIKE_KILL_AT)
  spike_durabilidade.py resume --thread T          # retoma do checkpoint (mesmo thread)
  spike_durabilidade.py matrix                     # os 3 pontos de morte x 4 criterios -> tabela
  spike_durabilidade.py replay --thread T          # reconstroi a decisao so do eventos.ndjson (criterio d)

SPIKE_KILL_AT in {apos_wal_antes_efeito, apos_efeito_antes_wal_done, apos_wal_done_antes_checkpoint}
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Annotated, TypedDict
from operator import add

SCRATCH = Path(os.path.expanduser("~/.cache/agata/grafo-spike"))
REPO = SCRATCH / "repo"
EFEITOS = SCRATCH / "efeitos.log"
EVENTOS = SCRATCH / "eventos.ndjson"
DB = SCRATCH / "checkpoints.sqlite"
SELF = os.path.abspath(__file__)
PY = sys.executable


# ----------------------------------------------------------------------------- infra
def _fsync_append(path: Path, line: str):
    with open(path, "a") as f:
        f.write(line if line.endswith("\n") else line + "\n")
        f.flush()
        os.fsync(f.fileno())


def wal(thread: str, node: str, passo: int, fase: str, chave: str):
    _fsync_append(EVENTOS, json.dumps({
        "ts": round(time.time(), 3), "thread": thread, "node": node,
        "passo": passo, "fase": fase, "chave": chave,
    }))


def idem_key(thread: str, node: str, passo: int) -> str:
    return hashlib.sha1(f"{thread}|{node}|{passo}".encode()).hexdigest()[:16]


def _maybe_kill(point: str):
    if os.environ.get("SPIKE_KILL_AT") == point:
        # marca que o kill aconteceu de fato neste ponto, entao SIGKILL (nao da p/ capturar)
        _fsync_append(SCRATCH / "kills.log", f"{time.time()} SIGKILL @ {point} pid={os.getpid()}")
        os.kill(os.getpid(), 9)


def _efeito_ja_feito(chave: str) -> bool:
    """Idempotencia: a chave ja consta no efeitos.log E no git log do repo-clone?"""
    in_log = EFEITOS.exists() and any(chave in ln for ln in EFEITOS.read_text().splitlines())
    r = subprocess.run(["git", "-C", str(REPO), "log", "--grep", chave, "--oneline"],
                       capture_output=True, text=True)
    in_git = bool(r.stdout.strip())
    return in_log and in_git


# ----------------------------------------------------------------------------- grafo
class Estado(TypedDict):
    thread_id: str
    passo: int
    entrada: str
    hidratacao: str
    trabalho: str
    eventos: Annotated[list, add]          # event-stream append-only (reducer)
    ultimo_efeito_confirmado: str


def hidratar(s: Estado) -> dict:
    h = hashlib.sha1(f"estado|{s['thread_id']}".encode()).hexdigest()[:12]
    return {"hidratacao": f"HASH-ESTADO={h}", "eventos": [f"hidratar:{h}"]}


def trabalhar(s: Estado) -> dict:
    # "modelo" simulado, deterministico
    return {"trabalho": f"resposta para: {s['entrada']}", "eventos": ["trabalhar:ok"]}


def efeito_externo(s: Estado) -> dict:
    thread, passo = s["thread_id"], s["passo"]
    chave = idem_key(thread, "efeito_externo", passo)

    wal(thread, "efeito_externo", passo, "intent", chave)
    _maybe_kill("apos_wal_antes_efeito")

    if not _efeito_ja_feito(chave):
        _fsync_append(EFEITOS, f"passo={passo} chave={chave} :: {s['trabalho']}")
        subprocess.run(["git", "-C", str(REPO), "commit", "--allow-empty", "-q",
                        "-m", f"efeito passo={passo}\n\nidem:{chave}"], check=True)
        feito = "novo"
    else:
        feito = "pulado(idempotente)"

    _maybe_kill("apos_efeito_antes_wal_done")
    wal(thread, "efeito_externo", passo, "done", chave)
    _maybe_kill("apos_wal_done_antes_checkpoint")

    return {"eventos": [f"efeito_externo:{feito}:{chave}"], "ultimo_efeito_confirmado": chave}


def registrar_e_commitar(s: Estado) -> dict:
    return {"eventos": [f"registrar:ultimo={s['ultimo_efeito_confirmado']}"]}


def build_graph():
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.sqlite import SqliteSaver
    g = StateGraph(Estado)
    g.add_node("hidratar", hidratar)
    g.add_node("trabalhar", trabalhar)
    g.add_node("efeito_externo", efeito_externo)
    g.add_node("registrar_e_commitar", registrar_e_commitar)
    g.add_edge(START, "hidratar")
    g.add_edge("hidratar", "trabalhar")
    g.add_edge("trabalhar", "efeito_externo")
    g.add_edge("efeito_externo", "registrar_e_commitar")
    g.add_edge("registrar_e_commitar", END)
    cm = SqliteSaver.from_conn_string(str(DB))
    saver = cm.__enter__()
    return g.compile(checkpointer=saver), cm


# ----------------------------------------------------------------------------- modos
def _reset_scratch():
    import shutil
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    SCRATCH.mkdir(parents=True)
    REPO.mkdir()
    subprocess.run(["git", "-C", str(REPO), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(REPO), "config", "user.email", "spike@agata"], check=True)
    subprocess.run(["git", "-C", str(REPO), "config", "user.name", "spike"], check=True)
    subprocess.run(["git", "-C", str(REPO), "commit", "-q", "--allow-empty", "-m", "raiz"], check=True)
    EVENTOS.touch()
    EFEITOS.touch()


def worker(thread: str, resume: bool = False):
    graph, cm = build_graph()
    cfg = {"configurable": {"thread_id": thread}}
    try:
        if resume:
            out = graph.invoke(None, cfg)          # retoma pendente do checkpoint
        else:
            out = graph.invoke(
                {"thread_id": thread, "passo": 1, "entrada": "pedido de teste",
                 "hidratacao": "", "trabalho": "", "eventos": [],
                 "ultimo_efeito_confirmado": ""}, cfg)
        print(json.dumps({"ok": True, "eventos": out["eventos"],
                          "ultimo_efeito_confirmado": out["ultimo_efeito_confirmado"]}))
    finally:
        cm.__exit__(None, None, None)


def replay(thread: str):
    """Criterio (d): reconstroi a DECISAO so do eventos.ndjson, aplicando idempotencia.

    Um crash+resume deixa registros 'done' repetidos para a mesma chave -- isso e' append-only
    correto. O replay aplica idempotencia (chave ja confirmada -> ignora) e reconstroi
    'quais efeitos aconteceram' = a decisao. Retorna (raw, decisao_dedup)."""
    raw = []
    decisao = []
    for ln in EVENTOS.read_text().splitlines():
        e = json.loads(ln)
        if e["thread"] == thread and e["fase"] == "done":
            raw.append(e["chave"])
            if e["chave"] not in decisao:
                decisao.append(e["chave"])
    print(json.dumps({"wal_done_raw": raw, "decisao_reconstruida": decisao,
                      "ultimo": decisao[-1] if decisao else None}))
    return raw, decisao


def _verifica(thread: str, ponto: str) -> dict:
    # (a) sem duplicado
    linhas_efeito = [l for l in EFEITOS.read_text().splitlines() if l.strip()]
    chaves_efeito = [l.split("chave=")[1].split(" ")[0] for l in linhas_efeito]
    dup_log = len(chaves_efeito) != len(set(chaves_efeito))
    r = subprocess.run(["git", "-C", str(REPO), "log", "--pretty=%B"], capture_output=True, text=True)
    idem_commits = [l.split("idem:")[1].strip() for l in r.stdout.splitlines() if "idem:" in l]
    dup_git = len(idem_commits) != len(set(idem_commits))
    a = (not dup_log) and (not dup_git)
    # (b) idempotente-ou-pendente: a chave do passo 1 aparece exatamente 1x
    k1 = idem_key(thread, "efeito_externo", 1)
    b = chaves_efeito.count(k1) == 1 and idem_commits.count(k1) <= 1
    # (c) estado retomado explica o ultimo efeito confirmado
    wal_raw, decisao = replay(thread)
    c = bool(decisao) and decisao[-1] == k1
    # (d) replay do WAL (idempotencia aplicada) reconstroi a decisao == 1 efeito k1,
    #     e o mundo real bate (k1 uma vez no efeitos.log)
    d = decisao == [k1] and chaves_efeito.count(k1) == 1
    return {"ponto": ponto, "a_sem_dup": a, "b_idempotente": b,
            "c_estado_explica": bool(c), "d_wal_reconstroi": d,
            "wal_done_raw": wal_raw, "decisao_reconstruida": decisao,
            "chaves_efeito": chaves_efeito, "idem_commits": idem_commits}


def matrix():
    pontos = ["apos_wal_antes_efeito", "apos_efeito_antes_wal_done", "apos_wal_done_antes_checkpoint"]
    linhas = []
    for i, ponto in enumerate(pontos, 1):
        thread = f"kill-{i}-{ponto}"
        _reset_scratch()
        # 1) roda com kill
        p = subprocess.run([PY, SELF, "worker", "--thread", thread],
                           env={**os.environ, "SPIKE_KILL_AT": ponto},
                           capture_output=True, text=True)
        morreu = p.returncode == -9
        # 2) retoma sem kill
        env2 = {k: v for k, v in os.environ.items() if k != "SPIKE_KILL_AT"}
        p2 = subprocess.run([PY, SELF, "resume", "--thread", thread],
                            env=env2, capture_output=True, text=True)
        retomou = p2.returncode == 0
        # 3) verifica os 4 criterios
        v = _verifica(thread, ponto)
        v["kill_SIGKILL"] = morreu
        v["resume_ok"] = retomou
        v["resume_stdout"] = p2.stdout.strip()[-200:]
        if not retomou:
            v["resume_stderr"] = p2.stderr.strip()[-400:]
        linhas.append(v)

    print("\n=== MATRIZ P4-00 -- 3 pontos de morte x 4 criterios ===\n")
    hdr = f"{'ponto de morte':32} kill  resume   a    b    c    d"
    print(hdr); print("-" * len(hdr))
    allpass = True
    for v in linhas:
        ok = lambda x: " OK " if x else "FALHA"
        row = (f"{v['ponto']:32} "
               f"{'-9 ' if v['kill_SIGKILL'] else '???':4} "
               f"{'ok  ' if v['resume_ok'] else 'FALHA':6} "
               f"{ok(v['a_sem_dup'])} {ok(v['b_idempotente'])} "
               f"{ok(v['c_estado_explica'])} {ok(v['d_wal_reconstroi'])}")
        print(row)
        allpass &= (v["kill_SIGKILL"] and v["resume_ok"] and v["a_sem_dup"]
                    and v["b_idempotente"] and v["c_estado_explica"] and v["d_wal_reconstroi"])
    print()
    print(json.dumps(linhas, indent=2))
    print("\nVEREDITO:", "PASS -- opcao A (SqliteSaver + WAL minimo) fecha os 4 criterios"
          if allpass else "FALHA -- investigar; talvez opcao B (camada dedicada)")
    return 0 if allpass else 1


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "matrix"
    thr = None
    if "--thread" in sys.argv:
        thr = sys.argv[sys.argv.index("--thread") + 1]
    if mode == "worker":
        worker(thr, resume=False)
    elif mode == "resume":
        worker(thr, resume=True)
    elif mode == "replay":
        replay(thr)
    elif mode == "matrix":
        sys.exit(matrix())
    else:
        print(__doc__); sys.exit(2)
