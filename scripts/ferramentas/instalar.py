#!/usr/bin/env python3
"""Instala uma ferramenta no overlay do Humano e roda o sync (lote ferramentas-unificadas-26-11; R1, AC-11).

Uso: instalar.py <mcp|skill|agente> <nome> [--params k=v ...]
  stdio:  --params transporte=stdio --params comando=npx --params args=-y --params args=<pacote> \
          --params env=NOME_DA_VARIAVEL --params clis=claude,codex,opencode
  http:   --params transporte=http --params url=https://... --params clis=claude,codex
  skill:  --params origem=.agents/skills/<nome> --params clis=claude,codex
  agente: --params origem=.claude/agents/<nome>.md --params clis=claude

Grava SÓ o overlay (~/agata-local/ferramentas.yml) e chama o sync. Nunca config/ nem o repositório.
Pede "sim" no terminal antes de gravar (R1). Sem "sim": nada é gravado.
Códigos: 0 ok; 2 schema inválido ou sync com erro; 3 sem "sim".
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estado as E  # noqa: E402
import schema as S  # noqa: E402
import sincronizar as SYNC  # noqa: E402

TIPO_FONTE = {"mcp": "mcp", "skill": "skills", "agente": "agentes"}
LISTAS_ACUMULADAS = {"clis", "env"}  # aceitam vírgula e repetição
LISTA_REPETIDA = {"args"}  # cada --params args=... é um argumento
BOOLEANOS = {"adotar", "gerenciado"}


def montar(nome: str, pares: list[str]) -> dict:
    dados: dict = {"nome": nome}
    for par in pares:
        if "=" not in par:
            raise S.ErroSchema("--params tem de ser chave=valor")
        chave, valor = par.split("=", 1)
        if chave in LISTAS_ACUMULADAS:
            dados.setdefault(chave, []).extend(x for x in valor.split(",") if x)
        elif chave in LISTA_REPETIDA:
            dados.setdefault(chave, []).append(valor)
        elif chave in BOOLEANOS:
            if valor not in ("true", "false"):
                raise S.ErroSchema(f"{chave} é true ou false")
            dados[chave] = valor == "true"
        else:
            dados[chave] = valor
    return dados


def _resumo(tipo_fonte: str, e: dict) -> str:
    linhas = [f"Vou gravar no overlay ({tipo_fonte}): {e['nome']}", f"  clis: {', '.join(e['clis'])}"]
    if e.get("transporte"):
        linhas.append(f"  transporte: {e['transporte']}")
    if e.get("comando"):
        linhas.append(f"  comando: {e['comando']} ({len(e['args'])} argumento(s))")
    if e.get("url"):
        linhas.append(f"  host: {urlsplit(e['url']).hostname}")
    if e.get("env"):
        linhas.append("  variáveis (o valor vem do ambiente, não do arquivo): " + ", ".join(e["env"]))
    if e.get("origem"):
        linhas.append(f"  origem: {e['origem']}")
    return "\n".join(linhas)


def instalar(ctx: E.Contexto, tipo: str, nome: str, pares: list[str], pedir=input, imprimir=print) -> int:
    tipo_fonte = TIPO_FONTE[tipo]
    try:
        normal = S.validar_entrada(tipo_fonte, montar(nome, pares), f"{tipo} {nome}")
        ov = S.carregar_overlay(ctx.overlay)
    except (S.ErroSchema, E.ErroEstado) as e:
        imprimir(f"ERRO: {e}")
        return 2
    ov[tipo_fonte][nome] = normal
    imprimir(_resumo(tipo_fonte, normal))
    try:
        resposta = pedir("Digite sim para gravar no overlay e sincronizar: ")
    except EOFError:
        resposta = ""
    if resposta.strip().lower() != "sim":
        imprimir("nada gravado (sem \"sim\")")
        return 3
    if ctx.overlay.exists():
        E.gravar_bytes(ctx.base / "backup-overlay" / ctx.agora() / "ferramentas.yml", ctx.overlay.read_bytes())
    ctx.overlay.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(ctx.overlay.parent, 0o700)
    texto = yaml.safe_dump(S.serializar_overlay(ov), sort_keys=False, allow_unicode=True)
    E.gravar_bytes(ctx.overlay, texto.encode("utf-8"))
    imprimir(f"overlay gravado: {ctx.overlay}")
    return SYNC.sincronizar(ctx, None, False, imprimir)


def _terminal() -> bool:
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except (ValueError, OSError):
        return False


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Instala uma ferramenta no overlay e sincroniza.")
    p.add_argument("tipo", choices=list(TIPO_FONTE))
    p.add_argument("nome")
    p.add_argument("--params", action="append", default=[], metavar="k=v")
    a = p.parse_args(argv)
    # Gate (Alto 1, revisão independente): o "sim" tem de vir do Humano no terminal. Entrada pipeada ou
    # automatizada não passa, antes de qualquer leitura ou gravação.
    if not _terminal():
        print("ERRO: instalação exige terminal interativo com o Humano; entrada automatizada foi recusada, nada gravado")
        return 3
    return instalar(E.contexto_padrao(), a.tipo, a.nome, a.params)


if __name__ == "__main__":
    sys.exit(main())
