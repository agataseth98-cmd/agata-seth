#!/usr/bin/env python3
"""Gera o hook de início de sessão que lê a skill agata-arranque (R2, lote ferramentas-unificadas-26-11).

Acrescenta um grupo SessionStart em ~/.claude/settings.json e em ~/.codex/hooks.json. Sem --aplicar, só mostra
o que faria. Com --aplicar: copia o original para <base>/backup/<ts>/ (pasta 700, arquivo 600) e grava, mantendo
o modo do arquivo. Idempotente: se o grupo já existe (marca agata-arranque/SKILL.md), não duplica.
Não roda pelo sync: o Humano chama à mão. O repositório só traz este script, nunca os JSONs do home.
Uso: python3 scripts/ferramentas/instalar_hook_arranque.py [--aplicar] [--home DIR]
Códigos: 0 ok ou nada a fazer; 2 arquivo existente que não lê como JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estado as E  # noqa: E402

MARCA = "agata-arranque/SKILL.md"
COMANDO = {
    "claude": 'cat "$HOME/.claude/skills/agata-arranque/SKILL.md" 2>/dev/null || true',
    "codex": 'cat "$HOME/.codex/skills/agata-arranque/SKILL.md" 2>/dev/null || true',
}
# Formato medido: ~/.claude/settings.json tem hooks.SessionStart[] com matcher e hooks; ~/.codex/hooks.json tem o
# mesmo esqueleto, sem matcher. Ambos com entradas {type, command, timeout}.
GRUPO = {
    "claude": {"matcher": "startup", "hooks": [{"type": "command", "command": COMANDO["claude"], "timeout": 10}]},
    "codex": {"hooks": [{"type": "command", "command": COMANDO["codex"], "timeout": 10}]},
}
ALVOS = {"claude": ".claude/settings.json", "codex": ".codex/hooks.json"}


class ErroHook(ValueError):
    """Arquivo existente que não lê ou tem formato inesperado. Nada é gravado."""


def ler(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        dados = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ErroHook(f"{p.name} não lê como JSON") from None
    if not isinstance(dados, dict):
        raise ErroHook(f"{p.name}: o topo não é um mapa")
    return dados


def ja_presente(dados: dict) -> bool:
    grupos = (dados.get("hooks") or {}).get("SessionStart") or []
    return any(MARCA in h.get("command", "") for g in grupos for h in g.get("hooks", []) if isinstance(h, dict))


def acrescentar(dados: dict, grupo: dict) -> dict:
    hooks = dados.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ErroHook("hooks não é um mapa")
    lista = hooks.setdefault("SessionStart", [])
    if not isinstance(lista, list):
        raise ErroHook("hooks.SessionStart não é lista")
    lista.append(grupo)
    return dados


def executar(home: Path, aplicar: bool, imprimir=print) -> int:
    ctx = E.contexto_padrao(home)
    pendentes = []
    for cli, rel in ALVOS.items():
        alvo = home / rel
        try:
            dados = ler(alvo)
        except ErroHook as e:
            imprimir(f"ERRO: {e}")
            return 2
        if ja_presente(dados):
            imprimir(f"{cli}: grupo agata-arranque já presente em {rel}; nada a fazer")
            continue
        pendentes.append((cli, alvo, acrescentar(dados, GRUPO[cli])))
        imprimir(f"{cli}: acrescentaria SessionStart agata-arranque em {rel}")
    if not pendentes:
        return 0
    if not aplicar:
        imprimir("simulação: nada gravado (rode com --aplicar)")
        return 0
    backup = E.criar_backup(ctx, ctx.agora())
    for cli, alvo, novo in pendentes:
        if alvo.exists():
            E.gravar_bytes(backup / f"{cli}.json", alvo.read_bytes())
        E.gravar_bytes(alvo, (json.dumps(novo, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        imprimir(f"{cli}: gravado {ALVOS[cli]}")
    imprimir(f"cópia do original em {backup}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Acrescenta o hook SessionStart que lê agata-arranque.")
    p.add_argument("--aplicar", action="store_true", help="grava (sem isso, só simula)")
    p.add_argument("--home", type=Path, default=None, help="diretório home (padrão: o seu)")
    a = p.parse_args(argv)
    home = a.home or Path.home()
    return executar(home, a.aplicar)


if __name__ == "__main__":
    sys.exit(main())
