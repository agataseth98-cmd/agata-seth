#!/usr/bin/env python3
"""Segmentação de uma entrada de MEMÓRIAS em blocos (parágrafos) — fonte única
para scripts/gerar_obsidian.py (que marca cada bloco com `^bN` na nota) e
scripts/busca_semantica.py (que indexa cada bloco por sentido). Os dois têm de
concordar no N, senão o link "trecho parecido" abre o parágrafo errado.

Bloco = parágrafo de prosa com pelo menos MIN_CHARS caracteres. Fica de fora o
que não aceita `^id` no fim sem quebrar a renderização: bloco de código,
tabela, citação, título, linha horizontal. Lista conta como bloco inteiro (o
`^id` vai no último item, que é como o Obsidian ancora lista).

Uso: python3 scripts/agata_blocos.py --selftest
"""
import re
import sys

MIN_CHARS = 80
_NAO_ANCORA = re.compile(r"^\s*(\||>|#|---\s*$|\*\*\*\s*$)")


def blocos(linhas):
    """[(n, primeira_linha_idx, ultima_linha_idx, texto)] -- n começa em 1."""
    out, atual, em_codigo = [], [], False

    def fecha():
        if not atual:
            return
        texto = "\n".join(ln for _, ln in atual).strip()
        primeira = atual[0][1]
        if len(texto) >= MIN_CHARS and not _NAO_ANCORA.match(primeira):
            out.append((len(out) + 1, atual[0][0], atual[-1][0], texto))
        atual.clear()

    for i, ln in enumerate(linhas):
        if ln.lstrip().startswith("```"):
            fecha()
            em_codigo = not em_codigo
            continue
        if em_codigo:
            continue
        if not ln.strip():
            fecha()
            continue
        atual.append((i, ln))
    fecha()
    return out


def marcar(linhas):
    """Cópia de `linhas` com ` ^bN` no fim da última linha de cada bloco."""
    novas = list(linhas)
    for n, _ini, fim, _t in blocos(linhas):
        novas[fim] = novas[fim].rstrip() + f" ^b{n}"
    return novas


def _selftest():
    longo = "x" * 90
    ls = [longo, "", "curto", "", "```", longo, "```", "", "| a | b |", "", f"- {longo}", f"- {longo}", "", longo]
    bs = blocos(ls)
    ok = [b[0] for b in bs] == [1, 2, 3] and [b[1] for b in bs] == [0, 10, 13]
    m = marcar(ls)
    ok = ok and m[0].endswith(" ^b1") and m[11].endswith(" ^b2") and m[13].endswith(" ^b3") and m[5] == longo
    print("SELFTEST", "OK" if ok else f"FALHA {bs}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else 0)
