#!/usr/bin/env python3
"""
P6-02 -- recuperacao INDICE-PRIMEIRO. Refs rastreaveis, ZERO vector DB.

Duas vias, mesmo formato de saida:
  - `query_canon` (P4-02) sobre o indice derivado -- a via PRIMARIA (o loop nao depende
    do Obsidian; invariante da Fase 6).
  - o FTS do plugin via `:27125/search/simple/` (ro_proxy) -- a via SECUNDARIA.

Cada hit carrega uma REF checavel: `(NNN)` (numero de entrada de MEMORIAS) quando dá pra
derivar, mais o arquivo e -- na via MCP -- a linha. Nenhum score vetorial, nenhum store:
o `score` que o plugin devolve e' BM25 de texto, so pra ordenar.

Uso:
  consulta.py "termo1" "termo2"           # as 2 vias + convergencia
  consulta.py --via canon "termo"         # so a primaria
  consulta.py --via mcp "termo"           # so o plugin
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "grafo"))
import tools  # noqa: E402  (query_canon)

PROXY = os.environ.get("OBS_PROXY", "http://127.0.0.1:27125")
_ENTRADA_RE = re.compile(r"^\((\d{1,4})\)")
_ENTRADA_ARQ_RE = re.compile(r"entradas/0*(\d{1,4})\.md$")


def _ref_de_titulo(linha: str):
    m = _ENTRADA_RE.match(linha.strip())
    return f"({m.group(1)})" if m else None


def _ref_de_arquivo(fn: str):
    m = _ENTRADA_ARQ_RE.search(fn)
    return f"({int(m.group(1))})" if m else None


def via_query_canon(termos):
    """Via primaria: o indice derivado. Hits de MEMORIAS vem como titulo com (NNN)."""
    r = tools.query_canon(termos)
    if r["exit_code"] != 0:
        return {"erro": r.get("erro") or f"exit {r['exit_code']}", "hits": []}
    hits = []
    arquivo_atual = None
    for ln in r["trechos"].splitlines():
        ms = re.match(r"={5,}\s+(.+?):", ln) or re.match(r"={5,}\s+(MEMÓRIAS)", ln)
        if ms:
            arquivo_atual = ms.group(1).strip()
            if arquivo_atual.startswith("MEMÓRIAS"):
                arquivo_atual = "MEMÓRIAS.md"
            continue
        ref = _ref_de_titulo(ln)
        if ref:
            hits.append({"ref": ref, "arquivo": "MEMÓRIAS.md", "linha": None,
                         "trecho": ln.strip()[:180]})
        elif ln.startswith("--- ") and arquivo_atual and "›" in ln:
            hits.append({"ref": None, "arquivo": arquivo_atual, "linha": None,
                         "trecho": ln.strip("- ").strip()[:180]})
    return {"erro": None, "hits": hits}


def via_mcp(termos):
    """Via secundaria: o FTS do plugin pelo ro_proxy (:27125). Hits com arquivo + linha."""
    hits = []
    for termo in termos:
        q = urllib.parse.urlencode({"query": termo, "contextLength": 120})
        url = f"{PROXY}/search/simple/?{q}"
        req = urllib.request.Request(url, method="POST", data=b"")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                dados = json.load(resp)
        except Exception as e:  # noqa: BLE001
            return {"erro": f"{type(e).__name__}: {e}", "hits": []}
        for h in dados:
            fn = h.get("filename", "")
            # so canon + vault derivado -- fora venv/traces/missoes-nao-derivado
            if not (fn in ("MEMÓRIAS.md", "REGRAS.md", "PROJETO.md", "PROJETO_REFERENCIA.md")
                    or fn.startswith("memoria/obsidian/")):
                continue
            ref = _ref_de_arquivo(fn) or _ref_de_titulo(
                (h.get("matches", [{}])[0].get("context", "") or ""))
            for m in (h.get("matches", []) or [{}])[:2]:
                ctx = (m.get("context", "") or "").replace("\n", " ")[:180]
                hits.append({"ref": ref, "arquivo": fn, "offset": m.get("start"),
                             "trecho": ctx, "score": h.get("score")})
    # dedup por (arquivo, trecho)
    vistos, dedup = set(), []
    for h in hits:
        k = (h["arquivo"], h["trecho"])
        if k not in vistos:
            vistos.add(k)
            dedup.append(h)
    return {"erro": None, "hits": dedup}


def consultar(termos, via="ambos"):
    out = {}
    if via in ("ambos", "canon"):
        out["query_canon"] = via_query_canon(termos)
    if via in ("ambos", "mcp"):
        out["mcp"] = via_mcp(termos)
    if via == "ambos":
        refs_c = {h["ref"] for h in out["query_canon"]["hits"] if h["ref"]}
        refs_m = {h["ref"] for h in out["mcp"]["hits"] if h["ref"]}
        out["convergencia"] = {
            "refs_query_canon": sorted(refs_c),
            "refs_mcp": sorted(refs_m),
            "em_comum": sorted(refs_c & refs_m),
            "so_no_canon": sorted(refs_c - refs_m),
            "so_no_mcp": sorted(refs_m - refs_c),
        }
    return out


def _sem_vector_db():
    proibidos = ("faiss", "chromadb", "chroma", "qdrant", "weaviate", "lancedb", "milvus",
                 "pinecone", "annoy", "hnswlib")
    return [m for m in sys.modules if any(p in m.lower() for p in proibidos)]


if __name__ == "__main__":
    a = sys.argv[1:]
    via = "ambos"
    if "--via" in a:
        i = a.index("--via")
        via = a[i + 1]
        del a[i:i + 2]
    if not a:
        print(__doc__)
        sys.exit(2)
    res = consultar(a, via=via)
    vdb = _sem_vector_db()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"\nvector DB carregado? {vdb or 'NAO (ok)'}")
    sys.exit(0)
