#!/usr/bin/env python3
"""PROTÓTIPO, teste em clone descartável -- item "MEMÓRIAS por período" do
backlog "Ponto Cego", autorizado pelo Humano ("Autorizado, vai.") só pra
construir e testar o par gerar+verificar, NADA ainda no repositório real.

Move entradas de MEMÓRIAS.md (quente) pra MEMORIAS-MORNO.md (morno) quando
saem do orçamento de caracteres que a hidratação já usa de verdade
(`JANELA_ORCAMENTO_CHARS`, `.githooks/gerar-hidratacao.sh` -- lido do
arquivo real, nunca copiado a mão, pra não haver deriva entre os dois
números). Quando morno ultrapassa ~500 linhas (linha única do PROJETO.md,
Fase 4), congela o trecho mais ANTIGO dele (as entradas que já eram as
mais antigas de morno) num chunk frio novo, selado com scripts/selar.sh
(SHA-256 em SELOS.txt) e uma tag de git.

Nunca corta uma entrada ao meio -- cada corte é em fronteira de entrada,
igual a toda janela deste sistema (mesmo princípio de
`.githooks/gerar-hidratacao.sh`, `janela_memorias`).

Cada chamada é DELIBERADA: move o que precisa mover nesta passada só, não
tenta prever passadas futuras. Rodar de novo processa o que ainda resta
(morno pode continuar acima do teto depois de uma passada, se o histórico
acumulado for grande -- bootstrap tem essa forma, dia a dia normal não).

Uso: migrar_periodo.py [--aplicar] (sem --aplicar, só relata o que faria)
"""
import argparse
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI"
PADRAO_MIGRADO = re.compile(r"^## Migrado de DIÁRIO\.md", re.MULTILINE)
PADRAO_ENTRADA = re.compile(
    r"^\(\d+\) (?:DI[AÁ]RIO|CONSELHO|MOD[^—\-\n]*|CORRE[CÇ][AÃ]O) [—-] \d{2}/\d{2}/\d{4}",
    re.MULTILINE,
)
TETO_LINHAS_FRIO = 500


def ler_orcamento_quente() -> int:
    """Lê JANELA_ORCAMENTO_CHARS de .githooks/gerar-hidratacao.sh -- fonte
    única, evita o número duplicado (e divergente) em dois arquivos."""
    texto = (RAIZ / ".githooks/gerar-hidratacao.sh").read_text(encoding="utf-8")
    m = re.search(r"^JANELA_ORCAMENTO_CHARS=(\d+)", texto, re.MULTILINE)
    if not m:
        raise SystemExit("JANELA_ORCAMENTO_CHARS não encontrado em gerar-hidratacao.sh -- não presumo o valor.")
    return int(m.group(1))


def dividir(texto: str):
    """Mesma lógica de scripts/verificar_migracao_memorias.py -- ver lá os
    comentários de cada achado real por trás de cada decisão de parsing."""
    matches = list(PADRAO_ENTRADA.finditer(texto))
    migrados = list(PADRAO_MIGRADO.finditer(texto))
    if len(migrados) > 1:
        raise SystemExit(f"{len(migrados)} headings de bloco migrado -- ambíguo, abortando.")
    idx_migrado = migrados[0].start() if migrados else -1
    if not matches:
        return (texto[idx_migrado:], []) if idx_migrado != -1 else (None, [])
    cortes_set = {m.start() for m in matches}
    if idx_migrado != -1:
        cortes_set.add(idx_migrado)
    cortes = sorted(cortes_set) + [len(texto)]
    bloco_migrado, entradas = None, []
    for inicio, fim in zip(cortes, cortes[1:]):
        pedaco = texto[inicio:fim]
        if inicio == idx_migrado:
            bloco_migrado = pedaco
        else:
            entradas.append(pedaco)
    return bloco_migrado, entradas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true", help="escreve os arquivos; sem isso só relata")
    args = ap.parse_args()

    caminho_quente = RAIZ / "MEMÓRIAS.md"
    texto_quente = caminho_quente.read_text(encoding="utf-8")

    pos_marcador = texto_quente.index(MARCADOR)
    fim_linha_marcador = texto_quente.index("\n", pos_marcador) + 1
    cabecalho = texto_quente[:fim_linha_marcador]
    corpo = texto_quente[fim_linha_marcador:]

    bloco_migrado, entradas = dividir(corpo)
    bloco_migrado_novo_de_quente = bloco_migrado is not None
    # Bloco migrado é sempre o conteúdo mais antigo de todos -- fica de fora
    # da lista de entradas datadas, tratado à parte, sempre destinado ao
    # chunk frio mais antigo (nunca compete por espaço em quente/morno).

    orcamento = ler_orcamento_quente()
    acumulado = 0
    corte = len(entradas)
    for i, e in enumerate(entradas):
        if acumulado + len(e) > orcamento and i > 0:
            corte = i
            break
        acumulado += len(e)
    entradas_quente = entradas[:corte]
    entradas_envelhecidas = entradas[corte:]

    print(f"orçamento quente (lido de gerar-hidratacao.sh): {orcamento} chars")
    print(f"entradas totais após marcador: {len(entradas)}")
    print(f"ficam em quente: {len(entradas_quente)} ({acumulado} chars)")
    print(f"saem pra morno nesta passada: {len(entradas_envelhecidas)}")
    if bloco_migrado:
        print(f"bloco migrado: {len(bloco_migrado)} chars, {bloco_migrado.count(chr(10))} linhas -- vai pro chunk frio mais antigo")

    caminho_morno = RAIZ / "MEMORIAS-MORNO.md"
    if caminho_morno.exists():
        texto_morno_antigo = caminho_morno.read_text(encoding="utf-8")
        pos_m = texto_morno_antigo.index(MARCADOR)
        fim_m = texto_morno_antigo.index("\n", pos_m) + 1
        cabecalho_morno = texto_morno_antigo[:fim_m]
        corpo_morno_antigo = texto_morno_antigo[fim_m:]
        bloco_migrado_morno_antigo, entradas_morno_antigas = dividir(corpo_morno_antigo)
        if bloco_migrado_morno_antigo is not None:
            if bloco_migrado is not None:
                raise SystemExit("bloco migrado já existe em morno E teria que entrar de novo -- duplicação, abortando.")
            bloco_migrado = bloco_migrado_morno_antigo
    else:
        cabecalho_morno = (
            "# MEMORIAS-MORNO.md — camada morna do sistema Agata\n\n"
            "Gerado por scripts/migrar_periodo.py a partir de MEMÓRIAS.md (quente) quando entradas "
            "saem do orçamento de hidratação. Mesma garantia de MEMÓRIAS.md (Regra 4, append-only) — "
            "só muda ONDE a entrada mora, nunca o conteúdo dela. Ver REGRAS.md, \"Como ler este arquivo\".\n\n"
            "---\n\n"
            f"{MARCADOR} -- não editar esta linha à mão) -->\n"
        )
        entradas_morno_antigas = []

    # Morno cresce pelo topo, igual quente: entrada recém-envelhecida entra
    # logo abaixo do marcador, mais recente primeiro -- entradas_envelhecidas
    # já vem nessa ordem (era o final de quente, que também é top-down).
    entradas_morno_nova = entradas_envelhecidas + entradas_morno_antigas

    # Congelamento: corta o trecho mais ANTIGO de morno (fim da lista) em
    # blocos de ~500 linhas, fronteira sempre em entrada inteira -- nunca no
    # meio. Acumula do fim pra trás até estourar o teto.
    #
    # Achado real testando (357): se o total de morno JAMAIS estoura o teto,
    # o laço original chegava a i=0 sem nunca disparar o `break` -- e
    # `corte_frio` ficava em 0, congelando TUDO (mesmo 2 entradas, 42
    # linhas, bem abaixo de 500). Efeito: morno nunca conseguia reter um
    # resíduo pequeno, sempre drenava a zero -- justamente o oposto de "só
    # congela quando esfria de verdade". Corrigido: só entra no corte se o
    # total realmente ultrapassa o teto; do contrário nada congela.
    total_linhas = sum(e.count("\n") + 1 for e in entradas_morno_nova)
    corte_frio = len(entradas_morno_nova)
    if total_linhas > TETO_LINHAS_FRIO:
        linhas_acc = 0
        for i in range(len(entradas_morno_nova) - 1, -1, -1):
            linhas_e = entradas_morno_nova[i].count("\n") + 1
            if linhas_acc + linhas_e > TETO_LINHAS_FRIO and linhas_acc > 0:
                break
            linhas_acc += linhas_e
            corte_frio = i
    entradas_frio_novas = entradas_morno_nova[corte_frio:]
    entradas_morno_final = entradas_morno_nova[:corte_frio]

    print(f"morno final: {len(entradas_morno_final)} entradas")
    if entradas_frio_novas:
        print(f"congela pra frio nesta passada: {len(entradas_frio_novas)} entradas ({linhas_acc} linhas)")
    else:
        print("nada atinge o teto de congelamento ainda")

    mudou = bool(entradas_envelhecidas) or bool(entradas_frio_novas) or bloco_migrado_novo_de_quente
    if not mudou:
        print("\nnada a migrar -- quente já cabe no orçamento e morno não atinge o teto de congelamento.")
        return

    if not args.aplicar:
        print("\n(--aplicar não passado -- nada escrito no disco)")
        return

    novo_quente = cabecalho + "".join(entradas_quente)
    caminho_quente.write_text(novo_quente, encoding="utf-8")

    novo_morno = cabecalho_morno + "".join(entradas_morno_final)
    caminho_morno.write_text(novo_morno, encoding="utf-8")

    if entradas_frio_novas or bloco_migrado_novo_de_quente:
        data_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conteudo_frio_partes = []
        nome_extra = ""
        if bloco_migrado_novo_de_quente:
            conteudo_frio_partes.append(bloco_migrado)
            nome_extra = "-com-migrado"
        conteudo_frio_partes.extend(entradas_frio_novas)

        # Mais de um chunk pode congelar no mesmo dia (bootstrap com muito
        # histórico acumulado, várias passadas seguidas) -- sufixo -N evita
        # colidir e sobrescrever um chunk já selado. Achado testando de
        # verdade: a primeira versão deste script sobrescrevia o chunk do
        # dia anterior sem aviso na segunda passada do mesmo dia.
        seq = 1
        while True:
            sufixo_seq = "" if seq == 1 else f"-{seq}"
            nome_chunk = f"MEMORIAS-FRIO-{data_str}{sufixo_seq}{nome_extra}.md"
            caminho_frio = RAIZ / nome_chunk
            if not caminho_frio.exists():
                break
            seq += 1

        cabecalho_frio = (
            f"# {nome_chunk} — camada fria do sistema Agata (selada, imutável)\n\n"
            "Congelado por scripts/migrar_periodo.py. Selado com scripts/selar.sh — "
            "SHA-256 registrado em SELOS.txt, tag de git aponta pro commit deste selamento. "
            "Depois de selado, este arquivo nunca mais recebe escrita — garantia é "
            "`scripts/selar.sh --check`, não mais P-5.\n\n---\n\n"
        )
        caminho_frio.write_text(cabecalho_frio + "".join(conteudo_frio_partes), encoding="utf-8")
        print(f"chunk frio escrito: {nome_chunk}")

        hash_frio = hashlib.sha256(caminho_frio.read_bytes()).hexdigest()
        data_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(RAIZ / "SELOS.txt", "a", encoding="utf-8") as f:
            f.write(f"{hash_frio} {nome_chunk} {data_iso}\n")
        print(f"selo registrado em SELOS.txt: {hash_frio}")

    print("\naplicado.")


if __name__ == "__main__":
    main()
