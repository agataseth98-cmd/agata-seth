#!/usr/bin/env python3
"""Busca por TEXTO no vault derivado e no arquivo histórico -- sem acento, sem
maiúscula, por palavras (MEMÓRIAS (682)).

O `grep -F` de (670) só achava a frase exata: "o despertar da Agata" não achava
"O Despertar de Ágata" (acento e uma palavra no meio). Aqui: a consulta vira
palavras (3+ letras, sem acento); uma linha casa se tiver TODAS as palavras;
sem nenhuma linha assim, casa a que tiver mais delas (e o resultado diz isso).
Entre as que casam, palavra INTEIRA vem antes de pedaço de palavra (MEMÓRIAS
(716)): "laya" achava "himalaya" e "relaya" primeiro, e a linha do canon com
`laya` saiu em 37º de 38 -- a Seth leu as de cima e negou o termo.

Onde procura (fixo, nunca vem da consulta): memoria/obsidian/ e extras/ inteiro
(inclusive extras/arquivo-redesign/, decisão do Humano em (682)). Só .md.

Uso: python3 scripts/busca_texto.py -- "frase"     |     --selftest
"""
import os
import re
import sys
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONDE = ["memoria/obsidian", "extras"]
FORA = set()  # (682) o Humano abriu o dossiê: "tudo até o dossiê"
POR_NOTA = 3
MAX_LINHAS = 40


def _norm(t):
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def palavras(consulta):
    ps = []
    for p in _norm(consulta).replace("-", " ").replace("_", " ").split():
        p = "".join(c for c in p if c.isalnum())
        if len(p) >= 3 and p not in ps:
            ps.append(p)
    return ps


def _arquivos(raiz):
    for base in ONDE:
        topo = os.path.join(raiz, base)
        for d, dirs, arqs in os.walk(topo):
            dirs[:] = sorted(x for x in dirs if not x.startswith(".") and x not in FORA)
            for a in sorted(arqs):
                if a.endswith(".md") and not a.startswith("."):
                    yield os.path.join(d, a)


def buscar(consulta, raiz=REPO):
    ps = palavras(consulta)
    if not ps:
        return [], 0, ps
    inteiras = [re.compile(r"(?<![a-z0-9])" + re.escape(p) + r"(?![a-z0-9])") for p in ps]
    achados = []  # (n_palavras, n_inteiras, caminho_rel, nº linha, trecho)
    for caminho in _arquivos(raiz):
        rel = os.path.relpath(caminho, raiz)
        nome = _norm(rel)
        try:
            with open(caminho, encoding="utf-8", errors="replace") as f:
                linhas = f.read().splitlines()
        except OSError:
            continue
        locais = []
        for i, ln in enumerate(linhas, 1):
            norm = _norm(ln)
            n = sum(p in norm for p in ps)
            if n:
                w = sum(bool(r.search(norm)) for r in inteiras)
                locais.append((n, w, rel, i, ln.strip()[:200]))
        # o nome do arquivo também conta (ex.: O_Despertar_de_Agata.md)
        n_nome = sum(p in nome for p in ps)
        if n_nome and not any(n == len(ps) for n, *_ in locais):
            locais.append((n_nome, 0, rel, 0, "(nome do arquivo)"))
        locais.sort(key=lambda x: (-x[0], -x[1], x[3]))
        achados += locais[:POR_NOTA]
    if not achados:
        return [], 0, ps
    melhor = max(n for n, *_ in achados)
    achados = [a for a in achados if a[0] == melhor]
    achados.sort(key=lambda x: (-x[1], x[2], x[3]))
    return [(n, rel, i, t) for n, _w, rel, i, t in achados[:MAX_LINHAS]], melhor, ps


def main(argv):
    if argv[:1] == ["--selftest"]:
        return _selftest()
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    if len(argv) != 1:
        print("uso: busca_texto.py -- \"frase\"", file=sys.stderr)
        return 2
    achados, melhor, ps = buscar(argv[0])
    if not achados:
        print(f"nenhuma ocorrência de {ps} (sem acento, sem maiúscula)")
        return 1
    if melhor < len(ps):
        print(f"[nenhuma linha tem as {len(ps)} palavras; mostrando as que têm {melhor}: {ps}]")
    for _n, rel, i, trecho in achados:
        print(f"{rel}:{i}: {trecho}")
    return 0


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        os.makedirs(os.path.join(t, "extras", "arquivo-redesign"))
        os.makedirs(os.path.join(t, "memoria", "obsidian"))
        open(os.path.join(t, "extras", "O_Despertar_de_Agata.md"), "w").write("# O Despertar de Ágata\n\nNasci de muitos nomes\n")
        open(os.path.join(t, "extras", "arquivo-redesign", "AUDITORIA-01.md"), "w").write("despertar agata\n")
        open(os.path.join(t, "memoria", "obsidian", "n.md"), "w").write("nada aqui\n")
        a, m, ps = buscar("o despertar da Agata", t)
        ok = (ps == ["despertar", "agata"] and m == 2 and a
              and any(x[1].endswith("O_Despertar_de_Agata.md") for x in a)
              and any("arquivo-redesign" in x[1] for x in a))
        b, _, _ = buscar("NASCI de muitos", t)
        ok = ok and b and b[0][2] == 3
        c, _, _ = buscar("xy", t)
        ok = ok and c == []
        # (716) palavra inteira antes de pedaço: "laya" acha a linha com `laya` antes de "himalaya"
        open(os.path.join(t, "extras", "a.md"), "w").write("email/himalaya\n")
        open(os.path.join(t, "memoria", "obsidian", "z.md"), "w").write("medido: `laya` 10/20\n")
        d, _, _ = buscar("Laya", t)
        ok = ok and d and d[0][1].endswith("z.md") and any(x[1].endswith("a.md") for x in d)
    print("SELFTEST", "OK" if ok else f"FALHA {a} {b}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
