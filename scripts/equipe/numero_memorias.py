#!/usr/bin/env python3
"""numero_memorias.py -- número das entradas novas de MEMÓRIAS.md, sempre sobre o main do último instante.

Por que existe (incidente 12/11/2026): duas propostas com base 2ec04181 receberam o mesmo (999). A
segunda a entrar no main (#979) tomou o número que a aplicação (PR #980) já tinha escrito; a PR ficou
atrás da base e foi fechada. Número escolhido na abertura da branch morre sozinho: o número vale no
instante do merge, e só ali.

Entradas do registro começam com `(N) <palavra> — `, em ordem decrescente de cima para baixo (a mais
nova no topo do bloco ENTRADAS-NOVAS). Uma entrada é NOVA quando a primeira linha dela não existe na base.

Uso:
  python3 -I scripts/equipe/numero_memorias.py --base <MEMÓRIAS da base> --alvo <MEMÓRIAS da proposta> [--gravar]
  python3 -I scripts/equipe/numero_memorias.py --selftest

Sem --gravar: só mostra o mapa (N antigo -> N novo). Com --gravar: reescreve --alvo.
Fluxo da proposta (propostas/README.md): `git show origin/main:MEMÓRIAS.md > base.md`, roda este script
sobre o MEMÓRIAS.md da branch; se mudou, commit, push, espera o CI de novo, e só então `gh pr merge
--match-head-commit`. Exit 0 = ok (mesmo sem mudança); 1 = erro (nada gravado); 2 = uso.
"""
import re
import sys

PADRAO_LINHA = re.compile(r"^\((\d+)\) \S+ — ")


def _numeros(texto):
    return [int(m.group(1)) for m in (PADRAO_LINHA.match(l) for l in texto.splitlines()) if m]


def proximo(texto):
    """Próximo número livre (topo + 1). Mesmo critério que scripts/equipe/aplicar.py usava."""
    nums = _numeros(texto)
    if not nums:
        raise ValueError("nenhuma entrada numerada encontrada em MEMÓRIAS.md")
    return max(nums) + 1


def renumerar(base, alvo):
    """Devolve (texto_novo, mapa). `mapa` é lista de (N_antigo, N_novo) das entradas novas de `alvo`.

    Entradas novas = primeira linha que não existe na base. Recebem topo(base)+k..topo(base)+1 na
    ordem do arquivo (a mais alta recebe o maior número). Entradas da base e corpos ficam intactos."""
    base_primeiras = {l for l in base.splitlines() if PADRAO_LINHA.match(l)}
    topo = proximo(base) - 1
    linhas = alvo.splitlines(keepends=True)
    novas = [i for i, l in enumerate(linhas) if PADRAO_LINHA.match(l) and l.rstrip("\n") not in base_primeiras]
    k = len(novas)
    mapa = []
    for ordem, i in enumerate(novas):
        antigo = int(PADRAO_LINHA.match(linhas[i]).group(1))
        novo = topo + (k - ordem)
        mapa.append((antigo, novo))
        linhas[i] = re.sub(r"^\(\d+\)", f"({novo})", linhas[i], count=1)
    return "".join(linhas), mapa


def _selftest():
    base = (
        "# MEMÓRIAS\n<!-- ENTRADAS-NOVAS:AQUI -->\n\n"
        "(999) DIÁRIO — 12/11/2026 · **Proposta skills publicada.**\n\ncorpo\n\n"
        "(998) DIÁRIO — 12/11/2026 · **Proposta anterior.**\n\ncorpo\n"
    )
    falhas = []
    # 1. sem entrada nova: nada muda, mapa vazio
    t, m = renumerar(base, base)
    if t != base or m:
        falhas.append("sem novas: deveria ficar igual")
    # 2. entrada nova com (999), que a base já ocupa: vira (1000)
    alvo = base.replace(
        "(999) DIÁRIO — 12/11/2026 · **Proposta skills",
        "(999) DIÁRIO — 12/11/2026 · **Aplicado pacote.**\n\ncorpo\n\n(999) DIÁRIO — 12/11/2026 · **Proposta skills", 1)
    t, m = renumerar(base, alvo)
    if m != [(999, 1000)] or "(1000) DIÁRIO — 12/11/2026 · **Aplicado pacote.**" not in t:
        falhas.append(f"uma nova: mapa {m}")
    # 3. duas novas: a de cima = topo+2, a de baixo = topo+1; ordem decrescente preservada
    alvo2 = base.replace(
        "(999) DIÁRIO — 12/11/2026 · **Proposta skills",
        "(999) DIÁRIO — x · **A.**\n\n(999) DIÁRIO — x · **B.**\n\n(999) DIÁRIO — 12/11/2026 · **Proposta skills", 1)
    t, m = renumerar(base, alvo2)
    if m != [(999, 1001), (999, 1000)]:
        falhas.append(f"duas novas: mapa {m}")
    linhas = [l for l in t.splitlines() if PADRAO_LINHA.match(l)]
    if linhas[:3] != ["(1001) DIÁRIO — x · **A.**", "(1000) DIÁRIO — x · **B.**", "(999) DIÁRIO — 12/11/2026 · **Proposta skills publicada.**"]:
        falhas.append(f"duas novas: ordem {linhas[:3]}")
    # 4. sem nenhuma entrada numerada: erro, não chuta número
    try:
        proximo("sem registro nenhum")
        falhas.append("proximo() deveria falhar sem entradas")
    except ValueError:
        pass
    if falhas:
        print("SELFTEST FALHOU:\n  " + "\n  ".join(falhas))
        return 1
    print("SELFTEST OK -- 4 casos (sem nova, colisão, duas novas com ordem, sem entradas)")
    return 0


def main(argv):
    if argv == ["--selftest"]:
        return _selftest()
    base_path = alvo_path = None
    gravar = False
    i = 0
    while i < len(argv):
        if argv[i] == "--base" and i + 1 < len(argv):
            base_path = argv[i + 1]; i += 2
        elif argv[i] == "--alvo" and i + 1 < len(argv):
            alvo_path = argv[i + 1]; i += 2
        elif argv[i] == "--gravar":
            gravar = True; i += 1
        else:
            print(__doc__, file=sys.stderr)
            return 2
    if not base_path or not alvo_path:
        print("uso: numero_memorias.py --base <arq> --alvo <arq> [--gravar]", file=sys.stderr)
        return 2
    try:
        base = open(base_path, encoding="utf-8").read()
        alvo = open(alvo_path, encoding="utf-8").read()
        livre = proximo(base)
        texto, mapa = renumerar(base, alvo)
    except (OSError, ValueError) as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1
    mudou = [(a, b) for a, b in mapa if a != b]
    if not mudou:
        print(f"OK: nenhuma entrada nova com número ocupado; próximo número livre na base: {livre}")
        return 0
    print("RENUMERADO: " + ", ".join(f"({a}) -> ({b})" for a, b in mudou))
    if gravar:
        open(alvo_path, "w", encoding="utf-8").write(texto)
        print(f"gravado: {alvo_path}")
    else:
        print("(sem --gravar: nada foi escrito)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
