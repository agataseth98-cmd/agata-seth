#!/usr/bin/env python3
"""P-20, camada do decisor local -- dado pessoal em texto livre do canon PÚBLICO.

A régua de identificadores do P-20 só acha o que está numa lista, e só em
caminho de framework. Texto pessoal escrito à mão em MEMÓRIAS/PROJETO/ONDE_ESTAMOS
(saúde, família, finanças, endereço, rotina) entra no repositório público sem
que nada veja (MEMÓRIAS (430): MOD pessoal fica fora do canon). Aqui o decisor
local lê as linhas ADICIONADAS e avisa. Padrão "decide e confere" (PROJETO.md,
"Decisor local"): só AVISO, nunca FALHA; decisor fora do ar -> silêncio; o
texto nunca sai da máquina e nunca é reimpresso (só arquivo e trecho).

Uso: git diff --cached -U0 -- <arquivo> | p20_decisor.py <arquivo>
     p20_decisor.py --selftest
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "redesign" / "router"))
import decisor  # noqa: E402

LIMIAR = 0.7
# (705) 4000 caracteres levavam 31,5 s no winnow:e4b (CPU) e estouravam os 15 s padrão:
# 297 de 336 chamadas deram timeout em 13-14/10. 1200 cabem (~13 s medidos).
TRECHO = 1200
MAX_TRECHOS = 2
PRAZO = 30.0
_PERGUNTA = {"pessoal": {
    "type": "noul",
    "instructions": "This text reveals private personal information about a real person: "
                    "health, family, finances, home address, phone number, daily routine "
                    "or relationships."}}


def linhas_adicionadas(diff: str) -> str:
    return "\n".join(l[1:] for l in diff.splitlines()
                     if l.startswith("+") and not l.startswith("+++"))


def avisos(arquivo: str, texto: str) -> list[str]:
    saida = []
    trechos = [texto[i:i + TRECHO] for i in range(0, len(texto), TRECHO)][:MAX_TRECHOS]
    for n, trecho in enumerate(trechos, 1):
        if not trecho.strip():
            continue
        p = decisor.probabilidade(
            decisor.decidir("p20", trecho, _PERGUNTA, timeout=PRAZO, meta={"arquivo": arquivo, "trecho": n}),
            "pessoal")
        if p is not None and p >= LIMIAR:
            saida.append(
                f"AVISO (P-20, decisor): {arquivo}, trecho {n} das linhas novas, parece ter dado "
                f"pessoal (p={p:.2f}). Por que importa: o repositório é público e o que entra "
                f"não sai mais (MEMÓRIAS (430)). O que fazer: reler o trecho; se for pessoal, "
                f"tirar antes do commit. É um aviso de modelo -- pode ser falso positivo.")
    return saida


def _selftest() -> int:
    original, casos = decisor.decidir, []
    diff = "+++ b/MEMÓRIAS.md\n@@ -1,0 +1,2 @@\n+linha um\n+linha dois\n-removida\n"
    casos.append(("só linhas adicionadas, sem cabeçalho",
                  linhas_adicionadas(diff) == "linha um\nlinha dois"))
    for nome, p, quer in [("decisor fora do ar -> silêncio", None, 0),
                          ("p=0.9 -> 1 aviso", 0.9, 1), ("p=0.2 -> silêncio", 0.2, 0)]:
        decisor.decidir = lambda *a, _p=p, **k: None if _p is None else {
            "pessoal": {"type": "noul", "noul": _p}}
        casos.append((nome, len(avisos("MEMÓRIAS.md", "texto")) == quer))
    decisor.decidir = lambda *a, **k: {"pessoal": {"type": "noul", "noul": 0.99}}
    msg = avisos("MEMÓRIAS.md", "segredo-que-nao-pode-vazar")
    casos.append(("aviso nunca reimprime o texto", msg and "segredo" not in msg[0]))
    casos.append((f"texto longo -> no máximo {MAX_TRECHOS} trechos",
                  len(avisos("X", "a" * (TRECHO * 10))) == MAX_TRECHOS))
    decisor.decidir = original
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(_selftest())
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    for linha in avisos(sys.argv[1], linhas_adicionadas(sys.stdin.read())):
        print(linha)
