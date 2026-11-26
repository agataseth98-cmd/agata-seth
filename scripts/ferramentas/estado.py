#!/usr/bin/env python3
"""Estado do sync: caminhos (Contexto), manifest, backups 600 e log sem valores (lote ferramentas-unificadas-26-11).

Manifest: <base>/gerenciado.json (A2), só hashes. Backup: <base>/backup/<ts>/ (A4: pasta 700, arquivos 600).
Log: <base>/log.jsonl (600), só nomes e códigos de ação. O único lugar com valor de env é a cópia 600 dos
arquivos nativos e o campo `antes` do registro da execução, ambos dentro do backup.
"""
from __future__ import annotations

import hashlib
import stat
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


class ErroEstado(RuntimeError):
    """Manifest, registro ou backup ilegível."""


class ErroComando(RuntimeError):
    """Comando nativo não rodou (ausente ou sem resposta no prazo). A mensagem nunca traz argv: o argv pode levar
    valor de env (K=valor) e não pode ir para o stderr nem para o log."""


def executar_cli(argv: list[str]):
    """Roda um comando nativo sem stdin (um prompt não pode travar o sync). Exceções saem sem argv."""
    try:
        return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120,
                              check=False)
    except subprocess.TimeoutExpired:
        raise ErroComando("comando nativo sem resposta no prazo") from None
    except OSError:
        raise ErroComando("binário ausente ou não executável") from None


def agora_ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")


@dataclass
class Contexto:
    home: Path
    raiz: Path  # repositório que contém config/ferramentas/
    checkout: Path  # checkout principal: destino dos ponteiros de skill
    overlay: Path  # ~/agata-local/ferramentas.yml
    base: Path  # ~/.local/share/agata/ferramentas
    claude_json: Path
    codex_dir: Path
    opencode_jsonc: Path
    claude_skills: Path
    codex_skills: Path
    runner: Callable | None = None
    agora: Callable[[], str] | None = None

    def __post_init__(self) -> None:
        if self.runner is None:
            self.runner = executar_cli
        if self.agora is None:
            self.agora = agora_ts


def contexto_padrao(home: Path | None = None) -> Contexto:
    h = home or Path.home()
    codex = Path(os.environ["CODEX_HOME"]) if os.environ.get("CODEX_HOME") else h / ".codex"
    xdg = Path(os.environ["XDG_CONFIG_HOME"]) if os.environ.get("XDG_CONFIG_HOME") else h / ".config"
    return Contexto(
        home=h,
        raiz=Path(__file__).resolve().parents[2],
        checkout=h / "agata",
        overlay=h / "agata-local" / "ferramentas.yml",
        base=h / ".local" / "share" / "agata" / "ferramentas",
        claude_json=h / ".claude.json",
        codex_dir=codex,
        opencode_jsonc=xdg / "opencode" / "opencode.jsonc",
        claude_skills=h / ".claude" / "skills",
        codex_skills=codex / "skills",
    )


MANIFESTO_VAZIO = {"versao": 1, "entradas": {}, "ponteiros": {}, "arquivos": {}}


def ler_manifest(ctx: Contexto) -> dict:
    p = ctx.base / "gerenciado.json"
    if not p.exists():
        return json.loads(json.dumps(MANIFESTO_VAZIO))
    try:
        dados = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ErroEstado(f"manifest ilegível: {p}") from None
    if not isinstance(dados, dict):
        raise ErroEstado(f"manifest com formato inesperado: {p}")
    for chave in ("entradas", "ponteiros", "arquivos"):
        dados.setdefault(chave, {})
    return dados


def gravar_bytes(caminho: Path, dados: bytes, modo: int | None = None) -> None:
    """Escrita atômica (tmp no mesmo diretório, depois os.replace). Modo: o do arquivo que existe, ou 600."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if modo is None:
        modo = stat.S_IMODE(caminho.stat().st_mode) if caminho.exists() else 0o600
    tmp = caminho.with_name(f".{caminho.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(dados)
    os.chmod(tmp, modo)
    os.replace(tmp, caminho)


def gravar_json(caminho: Path, obj) -> None:
    gravar_bytes(caminho, (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def criar_backup(ctx: Contexto, ts: str) -> Path:
    """Cria <base>/backup/<ts>/ com modo 700. Se já existe, o nome ganha sufixo: quem chama usa o nome devolvido."""
    raiz = ctx.base / "backup"
    raiz.mkdir(parents=True, exist_ok=True)
    os.chmod(ctx.base, 0o700)
    os.chmod(raiz, 0o700)
    d, n = raiz / ts, 1
    while d.exists():
        d = raiz / f"{ts}-{n}"
        n += 1
    d.mkdir(mode=0o700)
    os.chmod(d, 0o700)
    return d


def area_arquivo(ctx: Contexto, ts: str) -> Path:
    """Destino de mv para o que sai do lugar (nunca rm): ~/agata-arquivo/ferramentas-<ts>/."""
    d = ctx.home / "agata-arquivo" / f"ferramentas-{ts}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def registrar(ctx: Contexto, evento: dict) -> None:
    """Uma linha por ação, só com nomes e códigos. Quem chama não passa valor de segredo."""
    ctx.base.mkdir(parents=True, exist_ok=True)
    linha = json.dumps({"em": datetime.now().isoformat(timespec="seconds"), **evento}, ensure_ascii=False, sort_keys=True)
    fd = os.open(ctx.base / "log.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def hash_arquivo(p: Path) -> str | None:
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()
