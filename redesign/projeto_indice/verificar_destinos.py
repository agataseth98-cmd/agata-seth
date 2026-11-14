#!/usr/bin/env python3
"""Verifica a migração do PROJETO.md para índice (componente projeto-indice, 12/11/2026).

Regras (redesign/projeto_indice/spec/spec.md, "Contrato"):
  (a) o arquivo de histórico tem o sha256 registrado em destinos.json;
  (b) toda seção do PROJETO anterior tem entrada, e nenhuma entrada sobra;
  (c) todo parágrafo que saiu do índice aparece, normalizado (espaços colapsados),
      no destino da sua seção (ou da exceção que bate no começo do parágrafo);
  (d) todo parágrafo mantido no índice aparece no PROJETO.md atual, e todo prefixo
      mantido bate com pelo menos um parágrafo.

"Parágrafo" = unidade: blocos separados por linha vazia; um item de lista ("- ",
"* ", "1. ") começa unidade nova; um título ("#...") é unidade própria.
Blocos de máquina (ANCORA-SHA e comentários HTML) não contam.

Uso: python3 redesign/projeto_indice/verificar_destinos.py [--raiz CAMINHO]
Saída: uma linha por achado. Código 1 se houver falha.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DESTINOS = Path(__file__).resolve().with_name("destinos.json")
ANCORA_INI = "<!-- ANCORA-SHA:INICIO"
ANCORA_FIM = "<!-- ANCORA-SHA:FIM -->"
ITEM = re.compile(r"^(?:- |\* |\d+[.)] )")


def norm(texto: str) -> str:
    return " ".join(texto.split())


def sem_maquina(linhas: list[str]) -> list[str]:
    """Tira o bloco ANCORA-SHA e comentários HTML: são de máquina, não de conteúdo."""
    saida: list[str] = []
    ancora = comentario = False
    for linha in linhas:
        if ANCORA_INI in linha:
            ancora = True
        if ancora:
            if ANCORA_FIM in linha:
                ancora = False
            continue
        if comentario:
            if "-->" in linha:
                comentario = False
            continue
        if linha.lstrip().startswith("<!--"):
            comentario = "-->" not in linha
            continue
        saida.append(linha)
    return saida


def secoes(texto: str) -> dict[str, list[str]]:
    """Seções de nível 2 ("## "), na ordem do arquivo. Antes da primeira: '__preambulo__'."""
    ordem: dict[str, list[str]] = {"__preambulo__": []}
    atual = "__preambulo__"
    for linha in sem_maquina(texto.splitlines()):
        if linha.startswith("## "):
            atual = linha[3:].strip()
            ordem.setdefault(atual, [])
            continue
        ordem[atual].append(linha)
    return ordem


def unidades(linhas: list[str]) -> list[str]:
    saida: list[str] = []
    atual: list[str] = []

    def fecha() -> None:
        if atual:
            saida.append("\n".join(atual))
            atual.clear()

    for linha in linhas:
        s = linha.rstrip()
        if not s.strip():
            fecha()
            continue
        if s.startswith("#"):
            fecha()
            saida.append(s)
            continue
        if ITEM.match(s):
            fecha()
        atual.append(s)
    fecha()
    return saida


def destino_da_unidade(unidade: str, secao: dict) -> str:
    for prefixo, arquivo in secao.get("excecoes", {}).items():
        if norm(unidade).startswith(norm(prefixo)):
            return arquivo
    return secao["padrao"]


def mantida(unidade: str, secao: dict) -> bool:
    return any(norm(unidade).startswith(norm(p)) for p in secao.get("manter", []))


def verificar(raiz: Path = RAIZ) -> list[str]:
    achados: list[str] = []
    cfg = json.loads(DESTINOS.read_text(encoding="utf-8"))
    hist = raiz / cfg["historico"]["arquivo"]
    if not hist.is_file():
        return [f"(a) histórico ausente: {cfg['historico']['arquivo']}"]
    dados = hist.read_bytes()
    if hashlib.sha256(dados).hexdigest() != cfg["historico"]["sha256"]:
        achados.append(f"(a) histórico com sha256 diferente do registrado: {cfg['historico']['arquivo']}")
    antigo = secoes(dados.decode("utf-8"))
    mapa = cfg["secoes"]
    for nome in antigo:
        if nome not in mapa:
            achados.append(f"(b) seção sem destino: {nome!r}")
    for nome in mapa:
        if nome not in antigo:
            achados.append(f"(b) destino para seção inexistente no PROJETO anterior: {nome!r}")
    atual = norm("\n".join(sem_maquina((raiz / "PROJETO.md").read_text(encoding="utf-8").splitlines())))
    textos: dict[str, str] = {}

    def texto_de(arquivo: str) -> str | None:
        if arquivo not in textos:
            caminho = raiz / arquivo
            if not caminho.is_file():
                return None
            textos[arquivo] = norm(caminho.read_text(encoding="utf-8"))
        return textos[arquivo]

    for nome, linhas in antigo.items():
        if nome not in mapa:
            continue
        secao = mapa[nome]
        us = unidades(linhas)
        for prefixo in secao.get("manter", []):
            if not any(norm(u).startswith(norm(prefixo)) for u in us):
                achados.append(f"(d) prefixo mantido sem parágrafo em {nome!r}: {prefixo!r}")
        for u in us:
            if mantida(u, secao):
                if norm(u) not in atual:
                    achados.append(f"(d) parágrafo mantido sumiu do PROJETO.md: {u[:70]!r}")
                continue
            arquivo = destino_da_unidade(u, secao)
            corpo = texto_de(arquivo)
            if corpo is None:
                achados.append(f"(c) destino ausente: {arquivo} (seção {nome!r})")
            elif norm(u) not in corpo:
                achados.append(f"(c) parágrafo saiu sem estar em {arquivo}: {u[:70]!r} (seção {nome!r})")
    return achados


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", type=Path, default=RAIZ)
    args = ap.parse_args(argv)
    achados = verificar(args.raiz)
    for a in achados:
        print(a)
    if not achados:
        print("destinos: OK (todo parágrafo que saiu do índice está no destino declarado)")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
