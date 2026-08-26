#!/usr/bin/env python3
"""Verifica se um novo MEMÓRIAS.md é uma reordenação válida do antigo.

Usado por scripts/perimetro.sh (controle P-5) só quando existe um marcador
propostas*/MIGRACAO-P5-<nome> -- o dia a dia usa a checagem de sufixo normal
(construção pelo topo); este script cobre a mudança estrutural única de
reordenar entradas já registradas, MEMÓRIAS (271).

Garantia: o conjunto de blocos de conteúdo do antigo -- o bloco "Migrado de
DIÁRIO.md" (atômico) mais cada entrada "(n) TIPO — data" -- tem que existir,
byte-idêntico, no novo. Nada perdido, nada alterado, nada acrescentado além
de cabeçalho/apresentação e reordenação. Não valida a ORDEM final (isso é
função de scripts/inverter_memorias.py, não deste verificador) -- só que
nenhum conteúdo já registrado foi tocado.

Uso: verificar_migracao_memorias.py <antigo.md> <novo.md>
Saída: PASS ou FALHA com diagnóstico. Exit 0 = PASS, 1 = FALHA.
"""
import re
import sys

MARCADOR_MIGRADO = "## Migrado de DIÁRIO.md"
PADRAO_ENTRADA = re.compile(
    r"^\(\d+\) (?:DIÁRIO|CONSELHO|MOD[^—]*|CORREÇÃO) — \d{2}/\d{2}/\d{4}",
    re.MULTILINE,
)


def dividir(texto: str):
    """Retorna (bloco_migrado_ou_None, lista_de_entradas_completas).

    Posição-agnóstico de propósito: o bloco migrado pode vir ANTES de todas
    as entradas (formato anterior a MEMÓRIAS (271)) ou DEPOIS de todas elas
    (formato novo -- fica no fim físico). Os pontos de corte são só os
    inícios de entrada mais o início do bloco migrado, ordenados; cada
    trecho vai até o próximo corte (ou EOF). Sem isso, o bloco migrado
    posicionado DEPOIS das entradas seria engolido pela última entrada
    física (bug real, achado rodando contra o arquivo já migrado -- a
    versão anterior deste script assumia migrado-sempre-antes e reportava
    "bloco sumiu" + "entrada alterada" como falso positivo).

    Cada entrada vai do início do seu cabeçalho "(n) TIPO — data" até o
    próximo corte -- nunca resplitada por um "#"/"##"/"###" interno
    (entrada (61) contém um heading do formato antigo colado dentro dela,
    verbatim; um parser que quebrasse por heading fatiaria essa entrada ao
    meio, incorretamente).
    """
    matches = list(PADRAO_ENTRADA.finditer(texto))
    idx_migrado = texto.find(MARCADOR_MIGRADO)
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
    """Espaço em branco no FIM de uma entrada é separador entre entradas
    (apresentação, Regra 7 -- livre pra otimizar), não conteúdo. Reconstrução
    (inverter_memorias.py) rejunta entradas com separador canônico único; sem
    normalizar aqui, a comparação bateria falso-negativo por causa disso, não
    por perda ou alteração real de conteúdo. Início da entrada nunca muda
    (é sempre "(n) TIPO — data", ancorado pelo próprio regex) -- só o fim é
    normalizado."""
    return entrada.rstrip()


def verificar(antigo: str, novo: str) -> list[str]:
    falhas = []
    bloco_antigo, entradas_antigo = dividir(antigo)
    bloco_novo, entradas_novo = dividir(novo)

    if bloco_antigo is not None:
        if bloco_novo is None:
            falhas.append("bloco 'Migrado de DIÁRIO.md' existia no antigo e sumiu no novo")
        elif bloco_antigo != bloco_novo:
            falhas.append(
                "bloco 'Migrado de DIÁRIO.md' mudou de CONTEÚDO -- só pode mudar de posição, nunca de byte"
            )

    contagem_antigo: dict[str, int] = {}
    for e in entradas_antigo:
        e = normalizar(e)
        contagem_antigo[e] = contagem_antigo.get(e, 0) + 1
    contagem_novo: dict[str, int] = {}
    for e in entradas_novo:
        e = normalizar(e)
        contagem_novo[e] = contagem_novo.get(e, 0) + 1

    for e, c in contagem_antigo.items():
        if contagem_novo.get(e, 0) < c:
            titulo = e.splitlines()[0][:90]
            falhas.append(f"entrada perdida ou alterada, sem par byte-idêntico no novo: {titulo!r}")
    for e, c in contagem_novo.items():
        if contagem_antigo.get(e, 0) < c:
            titulo = e.splitlines()[0][:90]
            falhas.append(
                f"conteúdo novo/diferente sem par idêntico no antigo -- alteração de história registrada, proibido: {titulo!r}"
            )

    if len(entradas_antigo) != len(entradas_novo):
        falhas.append(f"contagem de entradas mudou: antigo={len(entradas_antigo)} novo={len(entradas_novo)}")

    return falhas


def main():
    if len(sys.argv) != 3:
        print("uso: verificar_migracao_memorias.py <antigo.md> <novo.md>", file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        antigo = f.read()
    with open(sys.argv[2], encoding="utf-8") as f:
        novo = f.read()

    falhas = verificar(antigo, novo)
    if falhas:
        print("FALHA (verificar_migracao_memorias):")
        for f in falhas:
            print(f"  - {f}")
        sys.exit(1)

    _, entradas = dividir(antigo)
    print(f"PASS: {len(entradas)} entradas + bloco migrado, todas byte-idênticas ao antigo, só reordenadas/re-cabeçalhadas.")
    sys.exit(0)


if __name__ == "__main__":
    main()
