#!/usr/bin/env python3
"""Cofre de chaves das conexões — só de escrita para quem está de fora.

A chave de API é digitada pelo Humano no painel (aba Conexões) e vem para cá. Regras:
- fica em `AGATA_CONEXOES_DIR` (padrão ~/.config/agata/conexoes/), pasta 0700, um arquivo
  0600 por provedor (`<id>.chave`). NÃO é o `~/.config/agata/.env`: nada aqui lê nem
  escreve aquele arquivo;
- nenhuma função devolve a chave para o painel, para o log, para o ledger ou para um
  modelo. `estado()` só diz se existe e desde quando;
- `_para_chamada()` é o único leitor, usado pelo adaptador no instante da chamada HTTP;
- variável de ambiente com o mesmo nome (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`...) também
  vale, e o estado diz só que ela existe;
- gravar e remover viram evento no ledger, sem valor nem hash da chave.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "nova_versao"))
import eventos  # noqa: E402

RE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{1,40}$")
RE_CHAVE = re.compile(r"^[A-Za-z0-9_\-.]{20,300}$")


def pasta() -> Path:
    return Path(os.environ.get("AGATA_CONEXOES_DIR", Path.home() / ".config" / "agata" / "conexoes"))


def _arquivo(pid: str) -> Path:
    """Caminho do arquivo da chave, confinado à pasta do cofre (normaliza e confere o prefixo:
    id fora do padrão ou que escape da pasta é recusado — CodeQL py/path-injection)."""
    if not isinstance(pid, str) or not RE_ID.fullmatch(pid):
        raise ValueError("id de provedor inválido")
    base = os.path.realpath(pasta())
    alvo = os.path.normpath(os.path.join(base, pid + ".chave"))
    if not alvo.startswith(base + os.sep):
        raise ValueError("caminho fora do cofre")
    return Path(alvo)


def gravar(pid: str, chave: str, prefixo: str | None = None, actor: str = "humano-painel") -> dict:
    if not isinstance(chave, str):
        raise ValueError("chave ausente")
    chave = chave.strip()
    if not RE_CHAVE.match(chave):
        raise ValueError("formato de chave recusado (20 a 300 caracteres, sem espaço)")
    if prefixo and not chave.startswith(prefixo):
        raise ValueError("a chave não tem o prefixo esperado para este provedor")
    p = _arquivo(pid)
    p.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(p.parent, 0o700)
    fd, tmp = tempfile.mkstemp(dir=p.parent, prefix=".tmp-")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(chave)
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    eventos.registrar("decision", "chave_gravada", f"conexao:{pid}", actor=actor, componente="conexoes",
                      classification="private")
    return estado_de(pid)


def remover(pid: str, actor: str = "humano-painel") -> dict:
    p = _arquivo(pid)
    existia = p.exists()
    if existia:
        p.unlink()
        eventos.registrar("decision", "chave_removida", f"conexao:{pid}", actor=actor, componente="conexoes",
                          classification="private")
    return {**estado_de(pid), "removida": existia}


def estado_de(pid: str, env: str | None = None) -> dict:
    p = _arquivo(pid)
    no_cofre = p.exists()
    return {"no_cofre": no_cofre,
            "desde": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(p.stat().st_mtime)) if no_cofre else None,
            "permissao_ok": (no_cofre and (p.stat().st_mode & 0o077) == 0) or None,
            "no_ambiente": bool(env and os.environ.get(env))}


def _para_chamada(pid: str, env: str | None = None) -> str | None:
    """Único leitor da chave. Uso exclusivo do adaptador HTTP, no momento da chamada."""
    p = _arquivo(pid)
    if p.exists():
        return p.read_text(encoding="utf-8").strip() or None
    return os.environ.get(env) if env else None
