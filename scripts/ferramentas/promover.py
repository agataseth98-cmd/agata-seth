#!/usr/bin/env python3
"""Gera a proposta P-8 que leva uma entrada do overlay para a fonte canônica (lote ferramentas-unificadas-26-11; AC-12).

Uso: promover.py <nome>
Escreve SÓ propostas/<ts>-promover-<nome>.diff. Não aplica: config/ferramentas/ muda quando o Humano assina
a proposta. O overlay não é alterado aqui. A entrada do overlay pode ficar até a proposta ser aplicada.
Códigos: 0 ok; 2 nome fora do overlay, já na fonte canônica, ou schema inválido.
"""
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estado as E  # noqa: E402
import schema as S  # noqa: E402


def promover(ctx: E.Contexto, nome: str, imprimir=print) -> int:
    try:
        ov = S.carregar_overlay(ctx.overlay)
        canon, _ = S.carregar_canonico(ctx.raiz)
    except S.ErroSchema as e:
        imprimir(f"ERRO: {e}")
        return 2
    achados = [t for t in S.TIPOS if nome in ov[t]]
    if not achados:
        imprimir(f"ERRO: {nome} não está no overlay")
        return 2
    tipo = achados[0]
    if nome in canon[tipo]:
        imprimir(f"ERRO: {nome} já está na fonte canônica ({tipo})")
        return 2
    arq = ctx.raiz / "config" / "ferramentas" / S.ARQUIVO_CANON[tipo]
    antigo = arq.read_text(encoding="utf-8")
    base = antigo if antigo.endswith("\n") else antigo + "\n"
    item = yaml.safe_dump([S.para_yml(tipo, ov[tipo][nome])], sort_keys=False, allow_unicode=True)
    novo = base + "".join("  " + linha if linha.strip() else linha for linha in item.splitlines(True))
    # o texto novo tem de validar e ter exatamente uma entrada a mais
    try:
        dados = yaml.safe_load(novo)
        lista = S._lista(tipo, dados.get(tipo), arq.name)
    except (yaml.YAMLError, S.ErroSchema) as e:
        imprimir(f"ERRO: a proposta não valida: {type(e).__name__}")
        return 2
    if len(lista) != len(canon[tipo]) + 1 or nome not in lista:
        imprimir("ERRO: a proposta não acrescenta exatamente uma entrada")
        return 2
    rel = arq.relative_to(ctx.raiz).as_posix()
    corpo = "".join(difflib.unified_diff(
        antigo.splitlines(True), novo.splitlines(True), fromfile=f"a/{rel}", tofile=f"b/{rel}"))
    destino = ctx.raiz / "propostas" / f"{ctx.agora()[:15]}-promover-{nome}.diff"
    n = 1
    while destino.exists():
        destino = ctx.raiz / "propostas" / f"{ctx.agora()[:15]}-{n}-promover-{nome}.diff"
        n += 1
    destino.write_text(f"diff --git a/{rel} b/{rel}\n" + corpo, encoding="utf-8")
    imprimir(f"proposta escrita: {destino}")
    imprimir("nada aplicado: a assinatura do Humano decide (aprovar.sh)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gera o .diff P-8 que promove uma entrada do overlay ao canônico.")
    p.add_argument("nome")
    a = p.parse_args(argv)
    return promover(E.contexto_padrao(), a.nome)


if __name__ == "__main__":
    sys.exit(main())
