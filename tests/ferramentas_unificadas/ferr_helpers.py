"""Auxiliares dos testes do lote ferramentas-unificadas-26-11 (nome próprio, para não colidir com outros conftest).

Cada contexto de teste: HOME temporária, raiz temporária com cópia de config/ferramentas/ e propostas/,
as três CLIs imitadas em memória (fakes.FakeCLIs) e relógio determinístico. O checkout de skills aponta para o
repositório real, só para leitura (o SKILL.md de agata-arranque).
"""
from __future__ import annotations

import itertools
import shutil
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "ferramentas"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import estado as E  # noqa: E402
from fakes import FakeCLIs  # noqa: E402


def _relogio():
    contador = itertools.count(1)
    return lambda: f"20261126-120000-{next(contador):06d}"


def montar_ctx(tmp_path: Path, nome: str = "t") -> E.Contexto:
    base = tmp_path / nome
    home = base / "home"
    raiz = base / "repo"
    (raiz / "config" / "ferramentas").mkdir(parents=True)
    for arq in (REPO / "config" / "ferramentas").glob("*.yml"):
        shutil.copy(arq, raiz / "config" / "ferramentas" / arq.name)
    (raiz / "propostas").mkdir()
    home.mkdir(parents=True, exist_ok=True)
    ctx = E.Contexto(
        home=home,
        raiz=raiz,
        checkout=REPO,
        overlay=home / "agata-local" / "ferramentas.yml",
        base=home / ".local" / "share" / "agata" / "ferramentas",
        claude_json=home / ".claude.json",
        codex_dir=home / ".codex",
        opencode_jsonc=home / ".config" / "opencode" / "opencode.jsonc",
        claude_skills=home / ".claude" / "skills",
        codex_skills=home / ".codex" / "skills",
        agora=_relogio(),
    )
    ctx.runner = FakeCLIs(home)
    return ctx


def escrever_overlay(ctx: E.Contexto, dados: dict) -> None:
    ctx.overlay.parent.mkdir(parents=True, exist_ok=True)
    ctx.overlay.write_text(yaml.safe_dump(dados, sort_keys=False, allow_unicode=True), encoding="utf-8")


def entrada_teste(**extra) -> dict:
    """MCP stdio de teste, nas três CLIs, com uma variável de ambiente (só o nome vai à fonte)."""
    base = {"nome": "agata-teste", "transporte": "stdio", "comando": "echo", "args": ["ola"],
            "env": ["AGATA_TESTE_VAR"], "clis": ["claude", "codex", "opencode"]}
    base.update(extra)
    return base
