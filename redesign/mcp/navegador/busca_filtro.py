"""Funções puras da busca do navegador-mcp (23/11/2026, seth-web2-23-11): sem fastmcp nem playwright, para o CI testar.
Leitura da resposta da Wikipedia, filtro e ordem por termos sem acento."""
from __future__ import annotations

import json
import urllib.parse


def termos(consulta: str) -> list[str]:
    """Palavras da consulta com 3+ letras, sem aspas nem operador (`site:`)."""
    return [t for t in (w.strip('"\'').lower() for w in consulta.split())
            if len(t) >= 3 and ":" not in t]


def itens_wiki(json_texto: str, lang: str) -> list[dict]:
    """[{titulo, href, trecho}] da resposta da API de busca. JSON ruim = lista vazia."""
    import html
    import re as _re
    try:
        dados = json.loads(json_texto)
        lista = dados["query"]["search"]
    except (ValueError, KeyError, TypeError):
        return []
    itens = []
    for r in lista if isinstance(lista, list) else []:
        titulo = str((r or {}).get("title") or "").strip()
        if not titulo:
            continue
        trecho = html.unescape(_re.sub(r"<[^>]+>", "", str(r.get("snippet") or "")))
        itens.append({"titulo": f"{titulo} (Wikipedia)",
                      "href": f"https://{lang}.wikipedia.org/wiki/" + urllib.parse.quote(titulo.replace(" ", "_")),
                      "trecho": trecho})
    return itens


def sem_acento(texto: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(c))


def filtrar_e_ordenar(itens: list[dict], termos: list[str], fracao: tuple[int, int] = (2, 3)) -> list[dict]:
    """Tira o que casa menos de 2/3 dos termos (o RSS do Bing casa só a 1ª palavra: "capital da Mongólia" vinha
    com corretoras e rádios) e ordena o resto."""
    if not termos:
        return list(itens)
    a, b = fracao
    minimo = max(1, -(-a * len(termos) // b))  # fração dos termos, para cima (2/3: 1→1, 2→2, 3→2, 4→3)
    termos = [sem_acento(t) for t in termos]

    def n(it):
        alvo = sem_acento(" ".join(str(v) for v in it.values()))
        return sum(1 for t in termos if t in alvo)
    return ordenar_por_termos([it for it in itens if n(it) >= minimo], termos)


def ordenar_por_termos(itens: list[dict], termos: list[str]) -> list[dict]:
    """Mais termos da consulta casados primeiro (no título valem 2, no trecho 1); empate mantém a ordem de chegada."""
    def casados(it):
        titulo, trecho = sem_acento(str(it.get("titulo") or "")), sem_acento(str(it.get("trecho") or ""))
        termos_n = [sem_acento(t) for t in termos]
        return sum(2 if t in titulo else 1 if t in trecho else 0 for t in termos_n)
    return sorted(itens, key=casados, reverse=True)
