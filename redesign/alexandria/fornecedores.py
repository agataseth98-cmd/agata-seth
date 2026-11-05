"""Fornecedores gratuitos de conteúdo externo para a Alexandria (lote 5b).

Wikipédia em português pela API pública (sem chave, sem custo, licença CC BY-SA). Toda chamada sai por
`scripts/politica_egress.buscar_seguro`: cada salto é validado, IP pinado, teto de corpo, só HTTP 200.
A pergunta que sai já passou pela varredura de `externa.py` (dado pessoal e segredo não saem).

- `wikipedia_pesquisar(pergunta)`: resultados (título, trecho, endereço). É evidência efêmera.
- `wikipedia_guardar(titulo)`: extrato em texto puro do artigo, que entra em QUARENTENA pelo mesmo caminho
  de aquisição. Só vira consultável se o Humano revisar no painel.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import tempfile
import urllib.parse
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (AQUI, RAIZ / "scripts", RAIZ / "redesign" / "nova_versao"):
    sys.path.insert(0, str(_p))
import eventos  # noqa: E402

API = "https://pt.wikipedia.org/w/api.php"
ARTIGO = "https://pt.wikipedia.org/wiki/"
TETO_CORPO = 2 * 1024 * 1024


def _busca(url: str) -> bytes:
    import politica_egress  # noqa: E402
    pasta = eventos.dados() / "alexandria" / "tmp"
    pasta.mkdir(parents=True, exist_ok=True)
    os.chmod(pasta, 0o700)
    fd, tmp = tempfile.mkstemp(dir=pasta, prefix=".wiki-")
    os.close(fd)
    try:
        ok, status, _final, motivo = politica_egress.buscar_seguro(url, tmp, max_bytes=TETO_CORPO)
        if not ok or status != 200:
            raise RuntimeError(f"Wikipédia não respondeu: {motivo or f'status {status}'}")
        return Path(tmp).read_bytes()
    finally:
        Path(tmp).unlink(missing_ok=True)


def _url(params: dict) -> str:
    return API + "?" + urllib.parse.urlencode({**params, "format": "json", "formatversion": 2, "utf8": 1})


def wikipedia_pesquisar(pergunta: str, *, limite: int = 5, buscar=None) -> list[dict]:
    q = " ".join((pergunta or "").split())[:300]
    if not q:
        return []
    corpo = (buscar or _busca)(_url({"action": "query", "list": "search", "srsearch": q, "srlimit": limite}))
    dados = json.loads(corpo.decode("utf-8", errors="replace"))
    out = []
    for r in (dados.get("query") or {}).get("search", [])[:limite]:
        titulo = r.get("title") or ""
        trecho = html.unescape(re.sub(r"<[^>]+>", "", r.get("snippet") or ""))
        out.append({"url": ARTIGO + urllib.parse.quote(titulo.replace(" ", "_")), "titulo": titulo,
                    "trecho": " ".join(trecho.split())[:400]})
    return out


def wikipedia_guardar(titulo: str, *, buscar=None) -> dict:
    """Extrato em texto puro do artigo, guardado em quarentena (aquisicao.guardar_arquivo)."""
    import aquisicao  # noqa: E402
    t = " ".join((titulo or "").split())[:200]
    if not t:
        raise ValueError("título vazio")
    corpo = (buscar or _busca)(_url({"action": "query", "prop": "extracts", "explaintext": 1, "exlimit": 1,
                                     "titles": t}))
    paginas = (json.loads(corpo.decode("utf-8", errors="replace")).get("query") or {}).get("pages") or []
    if not paginas or "missing" in paginas[0] or not (paginas[0].get("extract") or "").strip():
        raise ValueError("artigo sem texto extraível")
    texto = paginas[0]["extract"]
    url = ARTIGO + urllib.parse.quote(t.replace(" ", "_"))
    pasta = aquisicao.entrada()
    fd, tmp = tempfile.mkstemp(dir=pasta, prefix=".wiki-txt-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(texto)
    r = aquisicao.guardar_arquivo(Path(tmp), "txt", f"Wikipédia: {t}", origem_tipo="wikipedia", origem_uri=url)
    return r
