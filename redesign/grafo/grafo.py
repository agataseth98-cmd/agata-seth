#!/usr/bin/env python3
"""
Esqueleto do loop de governanca da Fase 4 (P4-01).

    hidratar -> rotear -> trabalhar -> verificar -> portao -> registrar_e_commitar

- estado tipado: estado.py
- durabilidade: durabilidade.py (padrao do spike P4-00 -- SqliteSaver + WAL + idem key)
- `interrupt()` no portao: pausa, apresenta as tres perguntas + o diff, espera Command(resume=...)
- os nos `verificar` e (a parte de escrita do) `registrar_e_commitar` sao ESPINHA
  deterministica: `verificar` roda com o modelo desligado.

Uso:
    grafo.py run   "<pedido>" --repo <dir> [--thread <id>] [--tipo trabalho|conselho|verificacao]
    grafo.py resume --thread <id> --repo <dir> [--aprovar | --recusar]
"""
import json
import re
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from estado import Estado, estado_inicial          # noqa: E402
from durabilidade import WAL, efeito_idempotente   # noqa: E402
import tools                                       # noqa: E402  (P4-02 -- wrappers dos scripts)

AGATA = Path(os.path.expanduser("~/agata"))
SCRIPTS = AGATA / "scripts"
PROXY = os.environ.get("AGATA_PROXY", "http://127.0.0.1:20127")
DIR_ESTADO = Path(os.path.expanduser("~/.cache/agata/grafo"))
DB = DIR_ESTADO / "checkpoints.sqlite"
LOG_LOOP = "redesign/grafo/loop.log"   # relativo ao repo alvo -- onde registrar_e_commitar escreve


def _run(argv, cwd=None, stdin=None, timeout=60):
    try:
        p = subprocess.run(argv, cwd=cwd, input=stdin, capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except FileNotFoundError as e:
        return 127, "", str(e)


# --------------------------------------------------------------------------- nós
def hidratar(s: Estado) -> dict:
    """estado_para_eco.sh no repo alvo -- read-only, deterministico, sem modelo."""
    rc, out, err = _run(["bash", str(SCRIPTS / "estado_para_eco.sh")], cwd=s["repo"])
    fatos = {}
    for ln in out.splitlines():
        if ":" in ln and ln[0] not in " -":
            k, _, v = ln.partition(":")
            fatos[k.strip().lower().replace("-", "_")] = v.strip()
    h = {
        "hash_estado": fatos.get("hash_estado", ""),
        "head": fatos.get("head", ""),
        "topo_memorias": fatos.get("topo_memórias", fatos.get("topo_memorias", "")),
        "sync": next((l.strip() for l in out.splitlines() if l.startswith("sync:")), ""),
        "eco_rc": rc,
    }
    return {"hidratacao": h,
            "eventos": [f"hidratar:hash={h['hash_estado']}:rc={rc}"],
            "decisao_log": [f"hidratado sobre HEAD={h['head'][:12]}"]}


def rotear(s: Estado) -> dict:
    """Escolhe a combo do OmniRoute pela natureza do pedido (heuristica simples -- P4-01)."""
    tipo = s.get("tipo", "trabalho")
    if tipo == "conselho":
        rota = "conselho"
    elif tipo == "verificacao" or len(s["entrada"]) < 120:
        rota = "cheap"
    else:
        rota = "auto"
    return {"rota": rota, "eventos": [f"rotear:{rota}"],
            "decisao_log": [f"rota={rota} (tipo={tipo})"]}


def trabalhar(s: Estado) -> dict:
    """Chama o modelo. Se `s["com_envelope"]`, usa envelope.gerar (GBNF so no envelope,
    2 fases, direto no llama.cpp da Fase 3 -- P4-03). Senao, o proxy sanitizador (:20127)
    na combo escolhida. Degrada limpo se nao houver modelo."""
    if s.get("com_envelope"):
        try:
            import envelope as _env
            h = s.get("hidratacao", {})
            txt = _env.gerar(s["entrada"],
                             hash_estado=h.get("hash_estado") or "000000000000",
                             entrada=int(re.search(r"\((\d+)\)", h.get("topo_memorias", "(0)")).group(1) or 0),
                             sync=(h.get("sync") or "não verificado").replace("sync: ", ""))
            return {"trabalho": txt, "trabalho_erro": "",
                    "eventos": [f"trabalhar:envelope-gbnf:{len(txt)}ch"],
                    "decisao_log": ["modelo respondeu com envelope garantido (GBNF, 2 fases)"]}
        except Exception as e:  # noqa: BLE001
            return {"trabalho": "(sem modelo)", "trabalho_erro": f"envelope: {type(e).__name__}: {e}",
                    "eventos": [f"trabalhar:envelope_falhou:{type(e).__name__}"],
                    "decisao_log": ["envelope GBNF indisponivel -- segue para verificar/portao"]}
    body = json.dumps({
        "model": s["rota"],
        "messages": [{"role": "user", "content": s["entrada"]}],
        "max_tokens": 400, "stream": False,
    }).encode()
    req = urllib.request.Request(f"{PROXY}/v1/chat/completions", data=body,
                                 headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read())
        txt = d["choices"][0]["message"].get("content") or d["choices"][0]["message"].get("reasoning", "")
        return {"trabalho": txt, "trabalho_erro": "",
                "eventos": [f"trabalhar:ok:{len(txt)}ch:{d.get('model','?')}"],
                "decisao_log": [f"modelo respondeu ({d.get('model','?')})"]}
    except Exception as e:  # noqa: BLE001
        return {"trabalho": "(sem modelo)", "trabalho_erro": f"{type(e).__name__}: {e}",
                "eventos": [f"trabalhar:sem_modelo:{type(e).__name__}"],
                "decisao_log": ["modelo indisponivel -- segue para verificar/portao"]}


def verificar(s: Estado) -> dict:
    """ESPINHA deterministica: perimetro + cabecalho + citacao via tools.py (P4-02).
    Roda com o modelo desligado. As 3 sao leitura pura -> nao precisam de sandbox."""
    repo = s["repo"]
    per = tools.run_perimetro(repo=repo)
    cab = tools.lint_header(s.get("trabalho", ""), repo=repo)
    cit = tools.check_citation(s.get("trabalho", ""), repo=repo)

    v = {"perimetro_exit": per["exit_code"], "perimetro_resumo": per["resumo"],
         "cabecalho_ok": cab["ok"],
         "cabecalho_falhas": [] if cab["ok"] else [l for l in cab["motivo"].splitlines() if l.strip() and l != "OK"],
         "citacao_exit": cit["exit_code"], "citacoes_suspeitas": cit["suspeitos"]}
    resumo_per = per["resumo"]
    rc_per = per["exit_code"]
    suspeitos = cit["suspeitos"]
    cab_ok = cab["ok"]
    rc_cit = cit["exit_code"]
    return {"verificacao": v,
            "eventos": [f"verificar:per={rc_per}:cab={'ok' if cab_ok else 'falha'}:cit={rc_cit}"],
            "decisao_log": [f"verificacao: {resumo_per or 'perimetro sem resumo'}; "
                            f"cabecalho {'OK' if cab_ok else 'FALHA'}; "
                            f"{len(suspeitos)} citacao(oes) suspeita(s)"]}


def portao(s: Estado) -> dict:
    """As tres perguntas + o diff proposto -> interrupt(). Retoma com Command(resume={'aprovado': bool})."""
    from langgraph.types import interrupt
    v = s.get("verificacao", {})
    diff = (f"[loop.log +1 linha] pedido={s['entrada'][:60]!r} rota={s['rota']} "
            f"trabalho={s.get('trabalho','')[:80]!r}")
    perguntas = {
        "reversivel": "o efeito e' 1 commit (git revert desfaz) + 1 linha em loop.log",
        "alcance": f"toca so {LOG_LOOP} no repo {s['repo']}",
        "silencio": ("verificacao limpa" if (v.get("cabecalho_ok") and not v.get("citacoes_suspeitas")
                     and v.get("perimetro_exit") == 0)
                     else "ATENCAO: verificacao com pendencia -- ver estado.verificacao"),
    }
    decisao = interrupt({"perguntas": perguntas, "diff_proposto": diff, "verificacao": v})
    aprovado = bool(decisao.get("aprovado")) if isinstance(decisao, dict) else bool(decisao)
    return {"diff_proposto": diff,
            "portao": {**perguntas, "aprovado": aprovado},
            "eventos": [f"portao:{'aprovado' if aprovado else 'recusado'}"],
            "decisao_log": [f"portao: Humano {'aprovou' if aprovado else 'recusou'}"]}


def registrar_e_commitar(s: Estado) -> dict:
    """Efeito externo. Idempotente pela chave (thread, node, passo) -- padrao P4-00."""
    if not s.get("portao", {}).get("aprovado"):
        return {"eventos": ["registrar:pulado(nao aprovado)"],
                "decisao_log": ["nada registrado -- portao recusou"]}
    try:
        tools._exige_raiz_git(s["repo"])   # trava: repo tem que ser raiz de worktree git
    except tools.RepoInvalido as e:
        return {"eventos": [f"registrar:abortado:repo_invalido"],
                "decisao_log": [f"registrar_e_commitar ABORTADO -- {e}"]}
    repo = Path(s["repo"])
    wal = WAL(DIR_ESTADO)
    passo = 1
    linha = (f"{s['thread_id']} :: {s['entrada'][:80]} :: rota={s['rota']} :: "
             f"hash_estado={s['hidratacao'].get('hash_estado','')}")
    logf = repo / LOG_LOOP

    def ja_feito(chave: str) -> bool:
        in_log = logf.exists() and any(chave in l for l in logf.read_text().splitlines())
        r = subprocess.run(["git", "-C", str(repo), "log", "--grep", chave, "--oneline"],
                           capture_output=True, text=True)
        return in_log and bool(r.stdout.strip())

    def aplicar(chave: str):
        logf.parent.mkdir(parents=True, exist_ok=True)
        with open(logf, "a") as f:
            f.write(f"{linha} :: idem={chave}\n")
            f.flush()
            os.fsync(f.fileno())
        subprocess.run(["git", "-C", str(repo), "add", LOG_LOOP], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m",
                        f"loop: registro de {s['thread_id']}\n\nidem:{chave}"], check=True)
        if os.environ.get("GRAFO_KILL_AFTER_COMMIT"):   # gancho de teste P4-01 (herda P4-00)
            os.kill(os.getpid(), 9)

    chave, res = efeito_idempotente(wal, s["thread_id"], "registrar_e_commitar", passo,
                                    ja_feito, aplicar)
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    return {"commit_sha": sha, "ultimo_efeito_confirmado": chave,
            "eventos": [f"registrar_e_commitar:{res}:{chave}:HEAD={sha}"],
            "decisao_log": [f"registrado e commitado ({res}) -- HEAD={sha}, idem={chave}"]}


# --------------------------------------------------------------------------- grafo
def build():
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.sqlite import SqliteSaver
    g = StateGraph(Estado)
    for name, fn in [("hidratar", hidratar), ("rotear", rotear), ("trabalhar", trabalhar),
                     ("verificar", verificar), ("portao", portao),
                     ("registrar_e_commitar", registrar_e_commitar)]:
        g.add_node(name, fn)
    g.add_edge(START, "hidratar")
    g.add_edge("hidratar", "rotear")
    g.add_edge("rotear", "trabalhar")
    g.add_edge("trabalhar", "verificar")
    g.add_edge("verificar", "portao")
    g.add_edge("portao", "registrar_e_commitar")
    g.add_edge("registrar_e_commitar", END)
    cm = SqliteSaver.from_conn_string(str(DB))
    return g.compile(checkpointer=cm.__enter__()), cm


def _cfg(thread_id):
    return {"configurable": {"thread_id": thread_id}}


def run(entrada, repo, thread_id, tipo, com_envelope=False):
    DIR_ESTADO.mkdir(parents=True, exist_ok=True)
    graph, cm = build()
    try:
        out = graph.invoke(estado_inicial(entrada, thread_id, os.path.abspath(repo), tipo, com_envelope),
                           _cfg(thread_id))
        _print_estado(graph, thread_id, out)
    finally:
        cm.__exit__(None, None, None)


def resume(thread_id, repo, aprovar):
    from langgraph.types import Command
    graph, cm = build()
    try:
        out = graph.invoke(Command(resume={"aprovado": aprovar}), _cfg(thread_id))
        _print_estado(graph, thread_id, out)
    finally:
        cm.__exit__(None, None, None)


def _print_estado(graph, thread_id, out):
    st = graph.get_state(_cfg(thread_id))
    pend = [i.value for i in (st.tasks[0].interrupts if st.tasks else [])] if st.tasks else []
    print(json.dumps({
        "thread_id": thread_id,
        "pausado_no_portao": bool(st.next) and "portao" in st.next,
        "next": list(st.next),
        "interrupt": pend[0] if pend else None,
        "eventos": out.get("eventos", []),
        "decisao_log": out.get("decisao_log", []),
        "commit_sha": out.get("commit_sha", ""),
        "ultimo_efeito_confirmado": out.get("ultimo_efeito_confirmado", ""),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(2)
    mode = a[0]
    g = lambda flag, d=None: a[a.index(flag) + 1] if flag in a else d
    if mode == "run":
        run(a[1], g("--repo", str(AGATA)), g("--thread", f"loop-{os.getpid()}"),
            g("--tipo", "trabalho"), "--com-envelope" in a)
    elif mode == "resume":
        resume(g("--thread"), g("--repo", str(AGATA)), "--recusar" not in a)
    else:
        print(__doc__); sys.exit(2)
