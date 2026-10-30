#!/usr/bin/env python3
"""Gera um pacote de bootstrap somente leitura para um projeto externo."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

IGNORED = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache"}
TEXT_EXT = {".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml", ".sh", ".html", ".css"}


def files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(part in IGNORED for part in p.relative_to(root).parts):
            continue
        yield p


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_head(path: Path, limit=4000) -> str:
    if path.suffix.lower() not in TEXT_EXT:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def build(root: Path, out: Path, goal: str) -> None:
    root = root.resolve()
    out.mkdir(parents=True, exist_ok=True)
    records = []
    headings = []
    for path in files(root):
        rel = path.relative_to(root).as_posix()
        content = read_head(path)
        records.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)})
        for line in content.splitlines():
            if line.startswith("#"):
                headings.append(f"- `{rel}`: {line[:200]}")
    dirs = sorted({p.parts[0] for p in (Path(x["path"]) for x in records) if p.parts})
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (out / "bootstrap.md").write_text(
        "# Bootstrap\n\n"
        f"- Projeto: `{root}`\n- Objetivo: {goal}\n- Gerado em: {generated}\n"
        f"- Arquivos incluídos: {len(records)}\n- Diretórios de primeiro nível: {', '.join(f'`{d}`' for d in dirs) or 'nenhum'}\n\n"
        "## Estado da medição\n\n"
        "Este inventário é somente leitura. A presença de arquivo não prova que a capacidade está ativa, segura ou homologada.\n\n"
        "## Títulos encontrados\n\n" + ("\n".join(headings[:500]) or "Não medido: nenhum título textual encontrado.") + "\n",
        encoding="utf-8",
    )
    (out / "capabilities.md").write_text(
        "# Capacidades\n\n"
        "| Capacidade | Estado | Evidência |\n|---|---|---|\n"
        "| Estrutura do projeto | medida | `provenance.json` |\n"
        "| Serviços em execução | não medido | este kit não acessa runtime |\n"
        "| Segurança operacional | não medido | requer revisão específica |\n"
        "| Qualidade funcional | não medido | requer testes do projeto |\n\n"
        "Estados são deliberadamente conservadores; não inferir disponibilidade a partir de nomes de arquivos.\n",
        encoding="utf-8",
    )
    (out / "concept-brief.md").write_text(
        f"# Concept Brief\n\n## Objetivo informado\n\n{goal}\n\n"
        "## Perguntas para o Humano\n\n- Quem usa?\n- Qual resultado observável importa?\n- O que não pode quebrar?\n- Qual risco e qual reversão são aceitáveis?\n\n"
        "## Não decidido\n\nNenhum desenho técnico ou promessa de conformidade foi inferido pelo bootstrap.\n",
        encoding="utf-8",
    )
    (out / "spec.md").write_text("# Spec\n\nRascunho bloqueado até o Concept Brief ser decidido pelo Humano.\n", encoding="utf-8")
    reviews = out / "reviews"
    reviews.mkdir(exist_ok=True)
    (reviews / "README.md").write_text("# Reviews\n\nRevisores independentes devem receber somente a spec e o material mínimo da tarefa.\n", encoding="utf-8")
    (out / "decision.md").write_text("# Decisão\n\nAguardando decisão humana.\n", encoding="utf-8")
    (out / "drift-report.md").write_text("# Drift report\n\nNão há implementação aprovada para comparar nesta fase.\n", encoding="utf-8")
    (out / "provenance.json").write_text(json.dumps({"generated_at": generated, "root": str(root), "goal": goal, "files": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--goal", required=True)
    args = ap.parse_args()
    if not args.project.is_dir():
        ap.error("project precisa ser um diretório")
    build(args.project, args.out, args.goal)


if __name__ == "__main__":
    main()
