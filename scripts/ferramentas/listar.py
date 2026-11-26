#!/usr/bin/env python3
"""Lista as ferramentas por categoria, CLI e origem (lote ferramentas-unificadas-26-11; AC-15).

Só leitura. Mostra nomes e estados; nunca valores (env, cabeçalhos, argumentos).
Origem: canonico (config/ferramentas/), overlay (~/agata-local/) ou nativo (existe na CLI e não na fonte).
Uso: listar.py [--tipo mcp|skill|agente] [--cli claude|codex|opencode]
Código: 0 ok; 2 fonte ou config nativa ilegível.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estado as E  # noqa: E402
import nativos as N  # noqa: E402
import schema as S  # noqa: E402
import sincronizar as SYNC  # noqa: E402

CATEGORIA_CLI = {"mcp": "mcp", "skill": "skills", "agente": "agentes"}


def linhas(ctx: E.Contexto, tipo: str | None = None, cli: str | None = None) -> tuple[list[tuple], str | None]:
    fonte = S.carregar_fontes(ctx.raiz, ctx.overlay)
    manifesto = E.ler_manifest(ctx)
    nativos = {c: N.ler_mcp(c, ctx) for c in S.CLIS}
    pastas = {"claude": ctx.claude_skills, "codex": ctx.codex_skills}
    saida: list[tuple] = []
    mostra = lambda t: tipo is None or tipo == t  # noqa: E731
    cli_ok = lambda c: cli is None or cli == c  # noqa: E731

    if mostra("mcp"):
        conhecidos = set(fonte.entradas["mcp"])
        for nome, e in fonte.entradas["mcp"].items():
            origem = fonte.origem["mcp"][nome]
            for c in e["clis"]:
                if not cli_ok(c):
                    continue
                if not e["gerenciado"]:
                    estado = f"fora do sync: {e['motivo']}"
                elif nome not in nativos[c]:
                    estado = "ausente no nativo (sync adiciona)"
                else:
                    reg = manifesto["entradas"].get(f"{c}|mcp|{nome}")
                    if reg is None:
                        estado = "no nativo, sem adotar (adotar: true toma)"
                    elif reg["hash"] == N.hash_entrada(nativos[c][nome]):
                        estado = "gerenciado"
                    else:
                        estado = "alterado depois do sync"
                saida.append(("mcp", nome, c, origem, estado))
        for c in S.CLIS:
            if not cli_ok(c):
                continue
            for nome in nativos[c]:
                if nome not in conhecidos:
                    saida.append(("mcp", nome, c, "nativo", "fora da fonte; intacto"))

    if mostra("skill"):
        for nome, e in fonte.entradas["skills"].items():
            origem = fonte.origem["skills"][nome]
            for c in e["clis"]:
                if not cli_ok(c):
                    continue
                if c not in pastas:
                    estado = "L2: não medido nesta CLI"
                elif not e["gerenciado"]:
                    estado = f"fora do sync: {e['motivo']}"
                else:
                    link = pastas[c] / nome
                    alvo = (ctx.checkout / e["origem"]).resolve()
                    if link.is_symlink():
                        estado = "ponteiro ok" if SYNC.destino_ponteiro(link) == alvo else "ponteiro aponta para outro lugar"
                    elif link.exists():
                        estado = "existe e não é ponteiro"
                    else:
                        estado = "sem ponteiro (sync cria)"
                saida.append(("skill", nome, c, origem, estado))

    if mostra("agente"):
        for nome, e in fonte.entradas["agentes"].items():
            origem = fonte.origem["agentes"][nome]
            for c in e["clis"]:
                if cli_ok(c):
                    estado = f"fora do sync: {e['motivo']}" if not e["gerenciado"] else "L4: destino nativo não medido"
                    saida.append(("agente", nome, c, origem, estado))
    return saida, fonte.indice


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Lista ferramentas por categoria, CLI e origem (sem valores).")
    p.add_argument("--tipo", choices=["mcp", "skill", "agente"])
    p.add_argument("--cli", choices=S.CLIS)
    a = p.parse_args(argv)
    try:
        linhas_, indice = linhas(E.contexto_padrao(), a.tipo, a.cli)
    except (S.ErroSchema, E.ErroEstado, N.ErroConfig) as e:
        print(f"ERRO: {e}")
        return 2
    print(f"{'categoria':<10}{'nome':<26}{'cli':<10}{'origem':<11}estado")
    for cat, nome, c, origem, estado in linhas_:
        print(f"{cat:<10}{nome:<26}{c:<10}{origem:<11}{estado}")
    if indice:
        print(f"índice de skills: {indice}")
    print(f"{len(linhas_)} linha(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
