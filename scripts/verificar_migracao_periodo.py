#!/usr/bin/env python3
"""PROTÓTIPO, ainda em teste de clone descartável -- generaliza
scripts/verificar_migracao_memorias.py (MEMÓRIAS (271)) pra N arquivos de
cada lado, em vez de exatamente 1-pra-1. Mesma garantia, mesmo algoritmo:
o CONJUNTO de blocos de conteúdo (o bloco "Migrado de DIÁRIO.md", atômico,
mais cada entrada "(n) TIPO — data") tem que existir, byte-idêntico, dos
dois lados. Nada perdido, nada alterado, nada acrescentado além de
reordenação/relocação entre arquivos.

Uso: verificar_migracao_periodo.py --antes A1.md [A2.md ...] --depois D1.md [D2.md ...]
Saída: PASS ou FALHA com diagnóstico. Exit 0 = PASS, 1 = FALHA.
"""
import argparse
import re
import sys

PADRAO_MIGRADO = re.compile(r"^## Migrado de DIÁRIO\.md", re.MULTILINE)
PADRAO_ENTRADA = re.compile(
    r"^\(\d+\) (?:DI[AÁ]RIO|CONSELHO|MOD[^—\-\n]*|CORRE[CÇ][AÃ]O) [—-] \d{2}/\d{2}/\d{4}",
    re.MULTILINE,
)


def dividir(texto: str):
    """Copiado verbatim da lógica de verificar_migracao_memorias.py -- ver
    aquele arquivo pros comentários que explicam cada achado real por trás
    de cada decisão de parsing (posição-agnóstico do bloco migrado, âncora
    em início de linha, entrada nunca resplitada por heading interno)."""
    matches = list(PADRAO_ENTRADA.finditer(texto))
    migrados = list(PADRAO_MIGRADO.finditer(texto))
    if len(migrados) > 1:
        raise SystemExit(
            f"{len(migrados)} linhas batem com o heading do bloco migrado (esperado 0 ou 1) -- "
            "ambíguo, não presumo qual é o real. Abortando."
        )
    idx_migrado = migrados[0].start() if migrados else -1
    if not matches:
        if idx_migrado == -1:
            return None, []
        return texto[idx_migrado:], []
    cortes_set = {m.start() for m in matches}
    if idx_migrado != -1:
        cortes_set.add(idx_migrado)
    cortes = sorted(cortes_set) + [len(texto)]
    bloco_migrado = None
    entradas = []
    for inicio, fim in zip(cortes, cortes[1:]):
        pedaco = texto[inicio:fim]
        if inicio == idx_migrado:
            bloco_migrado = pedaco
        else:
            entradas.append(pedaco)
    return bloco_migrado, entradas


def normalizar(entrada: str) -> str:
    return entrada.rstrip()


def coletar(caminhos: list[str]):
    """Lê N arquivos, retorna (bloco_migrado_ou_None, todas_entradas). O
    bloco migrado só pode aparecer em NO MÁXIMO UM dos arquivos do grupo --
    aparecer em dois seria duplicação real, marcado como falha."""
    bloco = None
    origem_bloco = None
    entradas = []
    for caminho in caminhos:
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        b, es = dividir(texto)
        if b is not None:
            if bloco is not None:
                raise SystemExit(
                    f"bloco 'Migrado de DIÁRIO.md' aparece em mais de um arquivo do grupo "
                    f"({origem_bloco!r} e {caminho!r}) -- duplicação real, abortando."
                )
            bloco = b
            origem_bloco = caminho
        entradas.extend(es)
    return bloco, entradas


PADRAO_NUMERO = re.compile(r'^\((\d+)\)')


def _indexar_por_numero(entradas: list[str]) -> dict[int, list[str]]:
    """Agrupa entradas normalizadas pelo número -- (49)+ é único globalmente
    (REGRAS.md), então cada chave normalmente tem 1 só valor; mais de um é
    achado (duplicação), não presumido como bug automático de outra causa."""
    idx: dict[int, list[str]] = {}
    for e in entradas:
        e_norm = normalizar(e)
        m = PADRAO_NUMERO.match(e_norm)
        if not m:
            continue
        n = int(m.group(1))
        idx.setdefault(n, []).append(e_norm)
    return idx


def verificar(antes_caminhos: list[str], depois_caminhos: list[str]) -> tuple[list[str], list[int]]:
    """Permutação por NÚMERO, não por string inteira -- achado real
    (MEMÓRIAS (357), segundo commit da própria migração de período):
    exigir multiset EXATO entre antes/depois reprova todo commit que
    combine relocação de história com uma entrada genuinamente nova (o
    caso normal -- o registro da migração É uma entrada nova, no mesmo
    commit que a aplica). Uma entrada com número que NÃO existe em ANTES
    é conteúdo novo legítimo, mesma coisa que o crescimento normal de
    quente já permite fora de marca nenhuma -- não é falha. O que continua
    proibido: número que existia em ANTES sumir, mudar de conteúdo, ou
    duplicar."""
    falhas: list[str] = []
    bloco_antes, entradas_antes = coletar(antes_caminhos)
    bloco_depois, entradas_depois = coletar(depois_caminhos)

    if bloco_antes is not None:
        if bloco_depois is None:
            falhas.append("bloco 'Migrado de DIÁRIO.md' existia no conjunto ANTES e sumiu no DEPOIS")
        elif bloco_antes != bloco_depois:
            falhas.append(
                "bloco 'Migrado de DIÁRIO.md' mudou de CONTEÚDO -- só pode mudar de posição/arquivo, nunca de byte"
            )
    elif bloco_depois is not None:
        falhas.append("bloco 'Migrado de DIÁRIO.md' não existia no conjunto ANTES e apareceu no DEPOIS -- invenção")

    idx_antes = _indexar_por_numero(entradas_antes)
    idx_depois = _indexar_por_numero(entradas_depois)

    for n, blocos in idx_antes.items():
        if n not in idx_depois:
            falhas.append(f"entrada ({n}) existia no ANTES e sumiu no DEPOIS -- perdida, restaure antes de comitar.")
            continue
        restantes = list(idx_depois[n])
        for b in blocos:
            if b in restantes:
                restantes.remove(b)
            else:
                titulo = b.splitlines()[0][:90]
                falhas.append(f"entrada ({n}) mudou de CONTEÚDO entre ANTES e DEPOIS: {titulo!r}")
        if restantes:
            falhas.append(f"entrada ({n}) aparece MAIS VEZES no DEPOIS do que no ANTES -- duplicação inesperada.")

    novos = sorted(n for n in idx_depois if n not in idx_antes)
    return falhas, novos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--antes", nargs="+", required=True)
    ap.add_argument("--depois", nargs="+", required=True)
    args = ap.parse_args()

    falhas, novos = verificar(args.antes, args.depois)
    if falhas:
        print("FALHA (verificar_migracao_periodo):")
        for f in falhas:
            print(f"  - {f}")
        sys.exit(1)

    _, entradas_antes = coletar(args.antes)
    extra = f" + {len(novos)} entrada(s) nova(s) genuína(s) {novos}" if novos else ""
    print(
        f"PASS: {len(entradas_antes)} entradas + bloco migrado (se houver) do ANTES, todas "
        f"byte-idênticas no DEPOIS (realocadas, nunca alteradas){extra}, entre os "
        f"{len(args.antes)} arquivo(s) ANTES e os {len(args.depois)} arquivo(s) DEPOIS."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
