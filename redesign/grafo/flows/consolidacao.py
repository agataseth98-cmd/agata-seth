#!/usr/bin/env python3
"""
P6-03 -- consolidacao noturna como flow do grafo. Fecha a Fase 6.

    orientar -> juntar -> consolidar -> podar

- reusa estado.py / durabilidade.py (Fase 4) e consulta.py (P6-02).
- saida SO em `propostas/` -- nunca canon direto (mesma politica da
  `agata-consolidacao.service`: memoria -> proposta em propostas/).
- `podar` propoe ARQUIVAR entradas redundantes -- nunca apaga (Regra 4).
- sem portao de commit automatico: a saida e' arquivo em `propostas/`, o Humano decide (P-8).

Reformulado em MEMORIAS (371) (opcao 2 da explicacao de (370)), depois de a
versao anterior nunca ter produzido nada aproveitavel em ~1 semana:
- SELECAO dirigida pela MUDANCA, nao mais os 4 temas fixos re-rodados toda noite.
  O pool de temas e' dado (`temas-consolidacao.txt`, um por linha, curado pelo
  Humano, FORA da quarentena por nao ser .py/.sh). Um tema so entra no run se
  >= MIN_NOVAS entradas mais novas que o marcador do ultimo run o citam (chave
  do INDICE_MEMORIAS_PALAVRAS-CHAVE.md ou substring do titulo). Marcador em
  ~/.cache/agata/consolidacao/marcador.json avanca so em modo automatico.
  Nada citando um tema do pool -> nenhum arquivo escrito.
- PORTAO DE QUALIDADE mecanico ANTES de escrever: rejeita saida vazia/erro/curta,
  ou que cite `(NNN)` fora do conjunto de refs do tema, ou que nao cite nenhuma.
  Reprovado -> nao escreve `.md`, registra em
  ~/.cache/agata/consolidacao/reprovados.log. Garbage nunca chega a triagem.
- MODELO LOCAL (Ollama :11434) no lugar da combo remota `conselho` do OmniRoute
  (429/504/529 cronicos eram a causa de a maioria das saidas nem existir).

Uso:
  consolidacao.py --repo <dir> [--temas "presence_penalty;num_ctx 16814"]
  (com --temas explicito roda mesmo sem "mudanca" -- modo manual.)
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

DIR_ESTADO = Path(os.path.expanduser("~/.cache/agata/consolidacao"))
DB = DIR_ESTADO / "checkpoints.sqlite"
MARCADOR = DIR_ESTADO / "marcador.json"
REPROVADOS = DIR_ESTADO / "reprovados.log"
IDX_CHAVES = "INDICE_MEMORIAS_PALAVRAS-CHAVE.md"
# Pool de temas curado pelo Humano -- um por linha, `#` comenta. NAO e' `.py`
# nem `.sh`, entao fica FORA da quarentena P-8: o Humano acrescenta um tema
# editando o arquivo direto, sem proposta. Selecao e' que e' automatica
# (so consolida tema que MEXEU), o pool e' dado, nao logica.
TEMAS_TXT = HERE / "temas-consolidacao.txt"
TEMAS_PADRAO = ["presence_penalty", "num_ctx 16814", "âncora sha"]
MIN_NOVAS = 2    # tema so consolida se >= 2 entradas novas (desde o marcador) o citam

OLLAMA = os.environ.get("AGATA_OLLAMA_URL", "http://localhost:11434/api/generate")
MODELO_LOCAL = os.environ.get("AGATA_CONSOLIDACAO_MODELO", "qwen3.5-9b-64k:latest")

# Temas do modo manual (--temas). Global de modulo porque `Estado` (TypedDict do
# LangGraph) descarta chave nao declarada no graph.invoke -- `s.get("_temas")`
# vinha sempre vazio (bug achado em MEMORIAS (373)). `run()` seta isto antes do
# invoke; `orientar` le daqui primeiro.
_TEMAS_MANUAL = None


def _modelo(pergunta, timeout=240, tentativas=2):
    """Modelo LOCAL (Ollama :11434) desde (371). A combo remota `conselho` do
    OmniRoute (429/504/529 cronicos) era a razao de a consolidacao nunca ter
    produzido nada -- MEMORIAS (368). Local = transporte confiavel; quem
    protege o canon agora e' o portao mecanico em `consolidar`, nao a
    qualidade do provedor. Erro vira string -- o portao a rejeita."""
    body = json.dumps({"model": MODELO_LOCAL, "prompt": pergunta, "stream": False,
                       "options": {"temperature": 0.2}}).encode()
    req = urllib.request.Request(OLLAMA, data=body,
                                 headers={"content-type": "application/json"})
    ultimo_erro = "sem tentativa"
    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            conteudo = (d.get("response") or "").strip()
            if conteudo:
                return conteudo
            ultimo_erro = "resposta vazia do modelo local"
        except Exception as e:  # noqa: BLE001
            ultimo_erro = f"{type(e).__name__}: {e}"
        if tentativa < tentativas:
            time.sleep(3 * tentativa)
    return f"(sem modelo local após {tentativas} tentativas: {ultimo_erro})"


# ---------------------------------------------------- marcador + temas do que mudou
def _canon_sha(repo):
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def _ler_marcador():
    try:
        return json.loads(MARCADOR.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {"ultimo_num": 0, "sha": ""}


def _gravar_marcador(ultimo_num, sha):
    MARCADOR.parent.mkdir(parents=True, exist_ok=True)
    MARCADOR.write_text(
        json.dumps({"ultimo_num": ultimo_num, "sha": sha,
                    "quando": date.today().isoformat()}, ensure_ascii=False, indent=2),
        encoding="utf-8")


_CAB_IDX = re.compile(r"^\((\d+)\)\s+(.*)$")
_CHAVE_LINHA = re.compile(r"^\s*palavras-chave:\s*(.+)$", re.I)


def _indice(repo):
    """{num: {"titulo": str, "chaves": set}} do INDICE_MEMORIAS_PALAVRAS-CHAVE.md
    (gerado do canon quente+morno+frio pelo hook de hidratacao)."""
    p = Path(repo) / IDX_CHAVES
    txt = p.read_text(encoding="utf-8") if p.is_file() else ""
    por_num, atual = {}, None
    for ln in txt.split("\n"):
        m = _CAB_IDX.match(ln)
        if m:
            atual = int(m.group(1))
            por_num[atual] = {"titulo": m.group(2).lower(), "chaves": set()}
            continue
        mk = _CHAVE_LINHA.match(ln)
        if mk and atual is not None:
            for w in re.split(r"[,\s]+", mk.group(1).strip()):
                w = w.strip().lower()
                if len(w) >= 3:
                    por_num[atual]["chaves"].add(w)
    return por_num


def _pool_temas():
    """Pool curado -- TEMAS_TXT (uma linha por tema, `#` comenta); TEMAS_PADRAO
    se o arquivo nao existir."""
    if TEMAS_TXT.is_file():
        linhas = [ln.split("#", 1)[0].strip()
                  for ln in TEMAS_TXT.read_text(encoding="utf-8").splitlines()]
        temas = [ln for ln in linhas if ln]
        if temas:
            return temas
    return list(TEMAS_PADRAO)


def _cita(tema, ent):
    """A entrada (dict do _indice) fala desse tema? Casa se qualquer palavra do
    tema (>=3 letras) esta nas chaves OU e' substring do titulo."""
    for w in re.split(r"[^0-9A-Za-zÀ-ÿ]+", tema.lower()):
        if len(w) >= 3 and (w in ent["chaves"] or w in ent["titulo"]):
            return True
    return False


def _temas_do_que_mudou(repo, desde_num):
    """Do pool curado, so os temas que >= MIN_NOVAS entradas com num > desde_num
    citam. Selecao dirigida pela mudanca; pool e' dado. Devolve (temas, novos)."""
    idx = _indice(repo)
    if not idx:
        return list(TEMAS_PADRAO), []
    novas = sorted(n for n in idx if n > desde_num)
    if len(novas) < MIN_NOVAS:
        return [], novas
    temas = []
    for tema in _pool_temas():
        if sum(1 for n in novas if _cita(tema, idx[n])) >= MIN_NOVAS:
            temas.append(tema)
    return temas, novas


# ------------------------------------------------------------------ portao
def _portao(corpo, refs_validas):
    """(ok, motivo) -- checagem MECANICA antes de escrever qualquer arquivo."""
    c = (corpo or "").strip()
    if len(c) < 40:
        return False, f"saida curta demais ({len(c)} chars)"
    baixo = c.lower()
    for ruim in ("sem modelo", "httperror", "http error", "traceback (most recent"):
        if ruim in baixo:
            return False, f"saida bate padrao de erro ({ruim!r})"
    citadas = set(re.findall(r"\((\d{1,4})\)", c))
    validas = {re.sub(r"\D", "", r) for r in refs_validas}
    fora = sorted(citadas - validas, key=lambda x: int(x))
    if fora:
        return False, f"cita refs fora do conjunto do tema: {fora}"
    if not citadas:
        return False, "nao cita ref nenhuma (nao consolida nada)"
    return True, "ok"


def _log_reprovado(tema, dia, motivo, corpo):
    REPROVADOS.parent.mkdir(parents=True, exist_ok=True)
    resumo = " ".join((corpo or "").strip().split())[:300]
    with open(REPROVADOS, "a", encoding="utf-8") as f:
        f.write(f"[{dia}] {tema} :: {motivo}\n    saida: {resumo}\n")


# --------------------------------------------------------------------------- nós
def orientar(s: Estado) -> dict:
    """Temas do que MUDOU desde o marcador (ou --temas explicito = modo manual)
    + refs + TITULO de cada ref (consulta.py). Sem modelo.

    Guarda o titulo de cada entrada (o `query_canon` de MEMORIAS ja devolve o titulo com
    `(NNN)`): o `consolidar` redige a partir do TEXTO real, nao dos numeros -- senao fabrica
    (a falha de MEMORIAS (138))."""
    repo = Path(s["repo"])
    manual = list(_TEMAS_MANUAL or s.get("_temas") or [])
    if manual:
        temas, novas = manual, []
    else:
        temas, novas = _temas_do_que_mudou(repo, _ler_marcador().get("ultimo_num", 0))
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
            "eventos": [f"orientar:{len(achados)}temas ({len(novas)} entradas novas)"],
            "decisao_log": [f"temas do que mudou: {list(achados)}"
                            + (" (--temas manual)" if manual else "")]}


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
        titulos_txt = "\n".join(f"  {ref}: {a['titulos'].get(ref, '(titulo indisponivel)')}"
                                for ref in a["refs"])
        pedido = (
            f"Voce redige uma PROPOSTA de consolidacao para o sistema Agata (NAO e' canon; "
            f"vai para propostas/ e o Humano decide). Tema: '{tema}'.\n"
            f"Entradas relacionadas (numero: TITULO real):\n{titulos_txt}\n\n"
            f"Baseie-se SO nesses titulos. Em <= 12 linhas: (1) o estado consolidado do tema "
            f"numa frase; (2) o que cada '(NNN)' acrescenta (use so os titulos acima); "
            f"(3) se algum titulo sugere que outro ficou obsoleto/redundante, aponte (sem "
            f"apagar). Cite os numeros no formato (NNN). NAO invente refs, numeros nem "
            f"conteudo alem dos titulos dados. Se um titulo nao for claro, diga 'titulo "
            f"insuficiente' em vez de supor.")
        corpo = _modelo(pedido)

        # PORTAO (MEMORIAS (371)): so escreve `.md` se passar. Reprovado -> log,
        # nenhum arquivo em propostas/ -- garbage nao chega a triagem.
        ok, motivo = _portao(corpo, a["refs"])
        if not ok:
            _log_reprovado(tema, hoje, motivo, corpo)
            escritos.append((f"consolidacao-{slug}-{hoje}", f"reprovado: {motivo}"))
            continue

        wal.intent("consolidacao", "consolidar", slug, chave)
        texto = (f"# Proposta de consolidacao — {tema}\n\n"
                 f"_Gerada por redesign/grafo/flows/consolidacao.py em {hoje}. NAO e' canon. "
                 f"O Humano decide (P-8). Se aprovada, vira ENTRADA NOVA em MEMORIAS "
                 f"(append-only), nunca edicao. Passou no portao mecanico de (371)._\n\n"
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
    global _TEMAS_MANUAL
    _TEMAS_MANUAL = list(temas) if temas else None
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
        if not temas:  # modo automatico: avanca o marcador pro estado atual do canon
            idx = _indice(repo)
            _gravar_marcador(max(idx) if idx else 0, _canon_sha(repo))
    finally:
        cm.__exit__(None, None, None)


if __name__ == "__main__":
    a = sys.argv[1:]
    g = lambda f, d=None: a[a.index(f) + 1] if f in a else d
    repo = g("--repo", os.path.expanduser("~/agata"))
    temas = g("--temas")
    run(repo, [t.strip() for t in temas.split(";")] if temas else None)
