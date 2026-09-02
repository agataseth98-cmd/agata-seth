#!/usr/bin/env python3
"""
`agata` CLI (P4-04) -- opera o sistema pela linha de comando.

    agata up [--moe]      sobe os servicos --user (omniroute, sanitizer, whisper, embeddings; +llamacpp se --moe)
    agata down            para os servicos; DRENA (nao corta no meio de um efeito -- checa o WAL)
    agata status          servicos + git_sync (canon vs origin/main; branch vs upstream) + HASH-ESTADO
    agata verify [--entrada <arq>]   perimetro.sh (+ cabecalho + citacoes se --entrada). exit 0/!=0. SEM MODELO.
    agata commit-entry <arq> [--alvo redesign/LOG.md] [--posicao fim|apos-marcador]   append-only + git commit. SEM MODELO.
    agata run "<pedido>" [--tipo trabalho|conselho|verificacao] [--com-envelope] [--repo <dir>]
    agata resume --thread <id> [--recusar] [--repo <dir>]
    agata logs [--thread <id>]        tail do event-stream (eventos.ndjson)

`verify` e `commit-entry` NAO importam langgraph nem tocam modelo -- sao a espinha
deterministica, rodam com tudo desligado.

Na Fase 8 isto vira /usr/local/bin/agata. Aqui fica no branch.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tools  # noqa: E402  (verify / commit-entry / status -- sem modelo)

AGATA = Path(os.path.expanduser("~/agata"))
DIR_ESTADO = Path(os.path.expanduser("~/.cache/agata/grafo"))
EVENTOS = DIR_ESTADO / "eventos.ndjson"

SERVICOS = ["omniroute", "omniroute-sanitizer", "openvino-whisper", "openvino-embeddings"]
SERVICO_MOE = "llamacpp-agata"


def _sc(*args):
    return subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True)


def _ativo(unit):
    return _sc("is-active", f"{unit}.service").stdout.strip()


# --------------------------------------------------------------------------- up / down
def cmd_up(moe=False):
    alvo = SERVICOS + ([SERVICO_MOE] if moe else [])
    for u in alvo:
        _sc("start", f"{u}.service")
    time.sleep(1)
    for u in alvo:
        print(f"  {u:22} {_ativo(u)}")
    return 0


def _pendencias_wal():
    """threads com 'intent' sem 'done' correspondente -- efeito em curso, nao cortar."""
    if not EVENTOS.exists():
        return []
    intents, dones = {}, set()
    for ln in EVENTOS.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        e = json.loads(ln)
        k = (e["thread"], e["node"], e["passo"], e["chave"])
        if e["fase"] == "intent":
            intents[k] = e
        elif e["fase"] == "done":
            dones.add(k)
    return [v for k, v in intents.items() if k not in dones]


def cmd_down():
    pend = _pendencias_wal()
    if pend:
        print(f"  DRENANDO: {len(pend)} efeito(s) em curso no WAL -- aguardando ate 30s...")
        for _ in range(30):
            time.sleep(1)
            if not _pendencias_wal():
                print("  drenado.")
                break
        else:
            print("  AVISO: ainda ha efeito(s) pendente(s) no WAL. Marque como pendente antes de agir de novo:")
            for p in _pendencias_wal():
                print(f"    - thread={p['thread']} node={p['node']} chave={p['chave']}")
    for u in SERVICOS + [SERVICO_MOE]:
        _sc("stop", f"{u}.service")
    for u in SERVICOS + [SERVICO_MOE]:
        print(f"  {u:22} {_ativo(u)}")
    return 0


# --------------------------------------------------------------------------- status
def cmd_status():
    print("servicos --user:")
    for u in SERVICOS + [SERVICO_MOE]:
        en = _sc("is-enabled", f"{u}.service").stdout.strip()
        print(f"  {u:22} {_ativo(u):10} ({en})")
    print("\ngit_sync:")
    g = tools.git_sync()
    print(f"  canon (main vs origin/main): {g['canon_local']} vs {g['canon_remote']}  "
          f"{'em dia' if g['canon_em_dia'] else 'DIVERGE'}")
    print(f"  branch vs upstream: {'em dia' if g['branch_em_dia'] else 'DIVERGE'}  "
          f"(HEAD {g['branch_head'][:8] if g['branch_head'] else '?'})")
    if g["fetch_error"]:
        print(f"  fetch_error: {g['fetch_error']}")
    print("\nHASH-ESTADO (estado_para_eco.sh):")
    r = subprocess.run(["bash", "scripts/estado_para_eco.sh"], cwd=str(AGATA),
                       capture_output=True, text=True)
    for ln in r.stdout.splitlines():
        if ln.startswith(("HEAD:", "TOPO-MEMÓRIAS:", "sync:", "HASH-ESTADO:")):
            print(f"  {ln}")
    return 0


# --------------------------------------------------------------------------- verify (SEM MODELO)
def cmd_verify(entrada=None):
    per = tools.run_perimetro()
    print(f"perimetro: exit {per['exit_code']} -- {per['resumo']}")
    rc = 1 if per["exit_code"] not in (0,) else 0
    # perimetro tem veredito "AVISO SO"; consideramos != 0 como falha real
    rc = per["exit_code"]
    if entrada:
        txt = Path(entrada).read_text(encoding="utf-8")
        cab = tools.lint_header(txt)
        cit = tools.check_citation(txt)
        print(f"cabecalho: {'OK' if cab['ok'] else 'FALHA -- ' + cab['motivo'].splitlines()[0]}")
        print(f"citacoes:  exit {cit['exit_code']} -- {len(cit['suspeitos'])} suspeita(s)")
        if not cab["ok"]:
            rc = rc or 1
        if cit["suspeitos"]:
            rc = rc or 1
    return rc


# --------------------------------------------------------------------------- commit-entry (SEM MODELO)
def cmd_commit_entry(arquivo, alvo="redesign/LOG.md", posicao="fim", repo=None):
    repo = repo or str(AGATA)
    texto = Path(arquivo).read_text(encoding="utf-8")
    import hashlib
    idem = "ce-" + hashlib.sha1((alvo + texto).encode()).hexdigest()[:12]
    r = tools.commit_entry(repo, alvo, texto, idem, posicao=posicao,
                           validar_cabecalho=(posicao == "apos-marcador"))
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r.get("ok") else 1


# --------------------------------------------------------------------------- run / resume / logs
def cmd_run(pedido, tipo="trabalho", com_envelope=False, repo=None):
    import grafo
    grafo.run(pedido, repo or str(AGATA), f"agata-{int(time.time())}", tipo, com_envelope)
    return 0


def cmd_resume(thread, recusar=False, repo=None):
    import grafo
    grafo.resume(thread, repo or str(AGATA), not recusar)
    return 0


def cmd_logs(thread=None):
    if not EVENTOS.exists():
        print("(sem eventos.ndjson ainda)")
        return 0
    for ln in EVENTOS.read_text(encoding="utf-8").splitlines()[-40:]:
        if not ln.strip():
            continue
        e = json.loads(ln)
        if thread and e["thread"] != thread:
            continue
        print(f"  {time.strftime('%H:%M:%S', time.localtime(e['ts']))} "
              f"{e['thread']:20} {e['node']:22} {e['fase']:7} {e['chave']}")
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    g = lambda f, d=None: rest[rest.index(f) + 1] if f in rest else d
    if cmd == "up":
        return cmd_up("--moe" in rest)
    if cmd == "down":
        return cmd_down()
    if cmd == "status":
        return cmd_status()
    if cmd == "verify":
        return cmd_verify(g("--entrada"))
    if cmd == "commit-entry":
        return cmd_commit_entry(rest[0], g("--alvo", "redesign/LOG.md"),
                                g("--posicao", "fim"), g("--repo"))
    if cmd == "run":
        return cmd_run(rest[0], g("--tipo", "trabalho"), "--com-envelope" in rest, g("--repo"))
    if cmd == "resume":
        return cmd_resume(g("--thread"), "--recusar" in rest, g("--repo"))
    if cmd == "logs":
        return cmd_logs(g("--thread"))
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
