#!/usr/bin/env python3
"""Curadoria do pacote de evidência (Alexandria): ordenar e anotar fontes antes de chegarem ao modelo.

A rodada reservada de 05/11/2026 (`r-20261105-082629-26a56b`) mostrou que entregar autoridade, data e origem
como metadado não basta: os modelos locais pegaram a fonte sem autoridade, trataram duas cópias como
confirmação independente e usaram uma medição antiga depois de um evento mais novo. A Alexandria passa a
dizer isso em texto, por fonte, de forma mecânica e conferível:

- autoridade: fonte sem autoridade não sobrepõe fonte com autoridade (canon, medição, decisão do Humano, spec);
- cópia: texto idêntico (normalizado) a outra fonte, ou a mesma origem declarada ("cópia de X"), conta como uma;
- correção: "(M) CORREÇÃO de (N)" marca a fonte "(N)" como corrigida por M;
- medição: entre medições, a de data mais recente vale; as anteriores ficam marcadas como anteriores.

Nada aqui decide a resposta: só ordena (autoridade, depois data) e anota. Determinístico e sem modelo.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import correcoes  # noqa: E402 — definição única de CORREÇÃO (lote 5, C1)

PESO = {"canon": 3, "humano": 3, "decisao": 3, "medicao": 3, "spec": 2, "nenhuma": 0}
RE_ENTRADA = re.compile(r"^\((\d{1,4})\)\s")
RE_COPIA_DE = re.compile(r"c[oó]pia (?:d[oae]s?|de) (.+)$", re.I)


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "")
    return re.sub(r"\s+", " ", "".join(c for c in t if not unicodedata.combining(c)).lower()).strip()


def peso(f: dict) -> int:
    a = _norm(f.get("autoridade") or "")
    return next((v for k, v in PESO.items() if k in a), 1)


def organizar(fontes: list[dict]) -> list[dict]:
    """Devolve cópias das fontes, ordenadas e com `notas` (lista de frases curtas)."""
    fs = [dict(f, notas=list(f.get("notas") or [])) for f in fontes]
    # correção explícita
    for f in fs:
        par = correcoes.correcao_de(f.get("texto") or "")
        if par and par[1] is not None:
            nova, velha = str(par[0]), str(par[1])
            for g in fs:
                mg = RE_ENTRADA.match(g.get("texto") or "")
                if g is not f and mg and mg.group(1) == velha:
                    g["notas"].append(f"corrigida por [{f['id']}] ({nova}); use a correção")
                    f["notas"].append(f"correção explícita de [{g['id']}]")
    # cópias: mesmo texto ou mesma origem declarada
    vistos: dict = {}
    origens: dict = {}
    for f in fs:
        chave = _norm(f.get("texto"))
        if chave in vistos:
            f["notas"].append(f"mesmo texto de [{vistos[chave]}]: não é confirmação independente")
        else:
            vistos[chave] = f["id"]
        mo = RE_COPIA_DE.search(_norm(f.get("origem") or ""))
        if mo:
            raiz = mo.group(1)
            if raiz in origens:
                f["notas"].append(f"mesma origem de [{origens[raiz]}] ({raiz}): não é confirmação independente")
            else:
                origens[raiz] = f["id"]
    # autoridade
    if any(peso(f) >= 2 for f in fs):
        for f in fs:
            if peso(f) == 0:
                f["notas"].append("sem autoridade: não sobrepõe fonte com autoridade")
    # instrução embutida e autoridade forjada (guarda da metacognição): só em fonte sem autoridade,
    # para não marcar o canon quando ele relata decisões do Humano
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "metacognicao"))
    import guarda
    for f in fs:
        if peso(f) < 2:
            n = guarda.nota(f.get("texto") or "")
            if n:
                f["notas"].append(n)
    # medições: a mais recente vale
    med = sorted([f for f in fs if "medi" in _norm(f.get("autoridade") or "") and f.get("data")], key=lambda f: f["data"])
    if len(med) > 1:
        for f in med[:-1]:
            f["notas"].append(f"medição anterior a [{med[-1]['id']}] ({med[-1]['data']}): vale a mais recente")
    def superada(f):
        return any(n.startswith(("corrigida", "medição anterior")) for n in f["notas"])
    ordem = sorted(fs, key=lambda f: str(f.get("data") or ""), reverse=True)   # mais recente primeiro
    ordem = sorted(ordem, key=lambda f: (-peso(f), superada(f)))               # estável: autoridade, depois vigente
    for f in fs:
        if not f["notas"]:
            f.pop("notas")
    return ordem


def texto_notas(f: dict) -> str:
    return "; ".join(f.get("notas") or [])
