#!/usr/bin/env python3
"""
P6-03 -- consolidacao noturna como flow do grafo. Fecha a Fase 6.

    orientar -> juntar -> consolidar -> podar

- reusa estado.py / durabilidade.py (Fase 4) e consulta.py (P6-02).
- saida SO em `propostas/` -- nunca canon direto (mesma politica da
  `agata-consolidacao.service`: memoria -> proposta em propostas/).
- `podar` propoe ARQUIVAR entradas redundantes -- nunca apaga (Regra 4).
- sem portao de commit automatico: a saida e' arquivo em `propostas/`, o Humano decide (P-8).

Uso:
  consolidacao.py --repo <dir> [--temas "presence_penalty;TES-002 nonce;num_ctx 16814"]
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))            # redesign/grafo
sys.path.insert(0, str(HERE.parent.parent / "obsidian"))
from estado import Estado                        # noqa: E402
from durabilidade import WAL, idem_key           # noqa: E402
import consulta as C                             # noqa: E402

PROXY = os.environ.get("AGATA_PROXY", "http://127.0.0.1:20127")
DIR_ESTADO = Path(os.path.expanduser("~/.cache/agata/consolidacao"))
DB = DIR_ESTADO / "checkpoints.sqlite"
TEMAS_PADRAO = ["presence_penalty", "TES-002 nonce", "num_ctx 16814", "âncora sha"]


def _modelo(pergunta, rota="conselho", timeout=120, tentativas=3):
    # Causa raiz real do `HTTPError` de (338)/(339), medida ao vivo em
    # 05/09/2026, NÃO era só cota transitória como (338) concluiu -- são dois
    # problemas empilhados:
    # (1) `max_tokens=700` era baixo demais: gemini-2.5-flash (combo
    #     `conselho`, fallback) gasta boa parte do orçamento em "reasoning"
    #     antes de responder -- medido: 671/700 tokens foram raciocínio, só
    #     25 sobraram pra conteúdo visível. Subido pra 3000.
    # (2) zai/glm-4.7-flash (o principal da combo) tem overload real
    #     ocasional (HTTP 529, "temporarily overloaded"), e o fallback pro
    #     gemini às vezes estoura o teto de espera LOCAL do OmniRoute
    #     (`resilienceSettings.requestQueue.maxWaitMs=15000`, o mesmo teto já
    #     documentado em (310)/(311) pro cold-start do Ollama, aqui batendo
    #     em latência de reasoning do Gemini) -> 504. Medido 2/3 chamadas OK,
    #     1/3 estourou aos ~15,9s -- intermitente de verdade, não sempre.
    # Mitigação aqui, escopo estreito (só este script, não mexe no
    # OmniRoute): retentativa curta. Mudar o teto de 15s do OmniRoute é
    # mudança de infraestrutura compartilhada, fora do escopo desta função.
    body = json.dumps({"model": rota, "messages": [{"role": "user", "content": pergunta}],
                       "max_tokens": 3000, "stream": False}).encode()
    req = urllib.request.Request(f"{PROXY}/v1/chat/completions", data=body,
                                 headers={"content-type": "application/json"})
    ultimo_erro = "sem tentativa"
    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            conteudo = d["choices"][0]["message"].get("content") or ""
            if conteudo:
                return conteudo
            ultimo_erro = "resposta vazia (reasoning consumiu o orçamento)"
        except Exception as e:  # noqa: BLE001
            ultimo_erro = f"{type(e).__name__}: {e}"
        if tentativa < tentativas:
            time.sleep(2 * tentativa)
    return f"(sem modelo após {tentativas} tentativas: {ultimo_erro})"


# --------------------------------------------------------------------------- nós
def orientar(s: Estado) -> dict:
    """Lista temas candidatos + refs + TITULO de cada ref (consulta.py). Sem modelo.

    Guarda o titulo de cada entrada (o `query_canon` de MEMORIAS ja devolve o titulo com
    `(NNN)`): o `consolidar` redige a partir do TEXTO real, nao dos numeros -- senao fabrica
    (a falha de MEMORIAS (138))."""
    temas = s.get("_temas") or TEMAS_PADRAO
    achados = {}
    for t in temas:
        r = C.consultar(t.split(), via="ambos")
        # titulos vindos do query_canon (MEMORIAS) -- {(NNN): "titulo"}
        titulos = {}
        for h in r["query_canon"]["hits"]:
            if h["ref"]:
                titulos[h["ref"]] = h["trecho"]
        for h in r["mcp"]["hits"]:
            if h["ref"] and h["ref"] not in titulos:
                titulos[h["ref"]] = h["trecho"]
        refs = sorted(titulos, key=lambda x: int(re.sub(r"\D", "", x) or 0))[:15]
        achados[t] = {"refs": refs, "titulos": {k: titulos[k] for k in refs},
                      "n_canon": len(r["query_canon"]["hits"]),
                      "n_mcp": len(r["mcp"]["hits"])}
    return {"trabalho": json.dumps(achados, ensure_ascii=False),
            "eventos": [f"orientar:{len(temas)}temas"],
            "decisao_log": [f"temas candidatos: {list(achados)}"]}


def juntar(s: Estado) -> dict:
    """Para cada tema, o conjunto de refs rastreaveis (ja veio do orientar). Sem modelo."""
    achados = json.loads(s["trabalho"])
    linhas = [f"- **{t}** — refs {a['refs']} (canon {a['n_canon']}, fts {a['n_mcp']})"
              for t, a in achados.items() if a["refs"]]
    return {"diff_proposto": "\n".join(linhas),
            "eventos": [f"juntar:{len(linhas)}temas_com_ref"],
            "decisao_log": [f"{len(linhas)} temas com refs rastreaveis"]}


def consolidar(s: Estado) -> dict:
    """O modelo redige UMA proposta de consolidacao por tema, em propostas/. Nunca canon."""
    repo = Path(s["repo"])
    achados = json.loads(s["trabalho"])
    hoje = date.today().isoformat()
    wal = WAL(DIR_ESTADO)
    escritos = []
    for tema, a in achados.items():
        if not a["refs"]:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", tema.lower()).strip("-")[:40]
        alvo = repo / "propostas" / f"consolidacao-{slug}-{hoje}.md"
        chave = idem_key("consolidacao", "consolidar", f"{slug}-{hoje}")
        if alvo.exists():
            escritos.append((str(alvo.relative_to(repo)), "ja_existe"))
            continue
        wal.intent("consolidacao", "consolidar", slug, chave)
        titulos_txt = "\n".join(f"  {ref}: {a['titulos'].get(ref, '(titulo indisponivel)')}"
                                for ref in a["refs"])
        pedido = (
            f"Voce redige uma PROPOSTA de consolidacao para o sistema Agata (NAO e' canon; "
            f"vai para propostas/ e o Humano decide). Tema: '{tema}'.\n"
            f"Entradas relacionadas (numero: TITULO real):\n{titulos_txt}\n\n"
            f"Baseie-se SO nesses titulos. Em <= 12 linhas: (1) o estado consolidado do tema "
            f"numa frase; (2) o que cada '(NNN)' acrescenta (use so os titulos acima); "
            f"(3) se algum titulo sugere que outro ficou obsoleto/redundante, aponte (sem "
            f"apagar). NAO invente refs, numeros nem conteudo alem dos titulos dados. Se um "
            f"titulo nao for claro, diga 'titulo insuficiente' em vez de supor.")
        corpo = _modelo(pedido)
        texto = (f"# Proposta de consolidacao — {tema}\n\n"
                 f"_Gerada por redesign/grafo/flows/consolidacao.py em {hoje}. NAO e' canon. "
                 f"O Humano decide (P-8). Se aprovada, vira ENTRADA NOVA em MEMORIAS "
                 f"(append-only), nunca edicao._\n\n"
                 f"**Refs:** {', '.join(a['refs'])}\n\n{corpo.strip()}\n")
        alvo.parent.mkdir(parents=True, exist_ok=True)
        with open(alvo, "w", encoding="utf-8") as f:
            f.write(texto)
            f.flush()
            os.fsync(f.fileno())
        wal.done("consolidacao", "consolidar", slug, chave)
        escritos.append((str(alvo.relative_to(repo)), "novo"))
    return {"commit_sha": "",  # NADA commitado -- so arquivo em propostas/
            "eventos": [f"consolidar:{escritos}"],
            "decisao_log": [f"propostas escritas: {escritos}"]}


def podar(s: Estado) -> dict:
    """Marca (nao apaga) o que uma consolidacao torna redundante. Proposta de arquivamento."""
    achados = json.loads(s["trabalho"])
    candidatos = {t: a["refs"] for t, a in achados.items() if len(a["refs"]) >= 3}
    nota = ("Poda (proposta, nao executada -- Regra 4): temas com >=3 entradas onde uma "
            "consolidacao aprovada tornaria as intermediarias consultaveis por 1 ref so. "
            "NADA e' apagado; a proposta e' de ARQUIVAR/apontar, o Humano decide.\n"
            + "\n".join(f"- {t}: {r}" for t, r in candidatos.items()))
    return {"portao": {"poda_proposta": nota, "aprovado": False},
            "eventos": [f"podar:{len(candidatos)}candidatos"],
            "decisao_log": ["poda proposta, nada apagado"]}


# --------------------------------------------------------------------------- grafo
def build():
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.sqlite import SqliteSaver
    g = StateGraph(Estado)
    for n, fn in [("orientar", orientar), ("juntar", juntar),
                  ("consolidar", consolidar), ("podar", podar)]:
        g.add_node(n, fn)
    g.add_edge(START, "orientar")
    g.add_edge("orientar", "juntar")
    g.add_edge("juntar", "consolidar")
    g.add_edge("consolidar", "podar")
    g.add_edge("podar", END)
    cm = SqliteSaver.from_conn_string(str(DB))
    return g.compile(checkpointer=cm.__enter__()), cm


def run(repo, temas=None):
    DIR_ESTADO.mkdir(parents=True, exist_ok=True)
    graph, cm = build()
    try:
        st0 = {"thread_id": f"consolid-{int(time.time())}", "repo": os.path.abspath(repo),
               "entrada": "consolidacao noturna", "tipo": "trabalho", "com_envelope": False,
               "hidratacao": {}, "rota": "", "trabalho": "", "trabalho_erro": "",
               "verificacao": {}, "diff_proposto": "", "portao": {}, "commit_sha": "",
               "ultimo_efeito_confirmado": "", "eventos": [], "decisao_log": [],
               "_temas": temas}
        out = graph.invoke(st0, {"configurable": {"thread_id": st0["thread_id"]}})
        print(json.dumps({"eventos": out["eventos"], "decisao_log": out["decisao_log"],
                          "diff_proposto": out["diff_proposto"],
                          "poda": out["portao"].get("poda_proposta", "")[:400]},
                         ensure_ascii=False, indent=2))
    finally:
        cm.__exit__(None, None, None)


if __name__ == "__main__":
    a = sys.argv[1:]
    g = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    repo = g("--repo", os.path.expanduser("~/agata"))
    temas = g("--temas")
    run(repo, [t.strip() for t in temas.split(";")] if temas else None)
