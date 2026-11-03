#!/usr/bin/env python3
"""Create and validate the evidence-bearing SDD documents."""
from __future__ import annotations

import argparse
from pathlib import Path


BRAINSTORM = ("Usuários", "Estado que muda", "Erros e concorrência", "Migração", "Observabilidade", "Reversão", "Sucesso")
SPEC = ("Jornadas críticas", "Contrato", "Critérios de aceite", "Desenho e alternativas", "Implementação e testes", "Migração e reversão", "Riscos e dependências")


def template(path: Path, title: str, sections: tuple[str, ...]) -> None:
    path.write_text("# " + title + "\n\n" + "\n\n".join(f"## {s}\n\n[preencher]" for s in sections) + "\n", encoding="utf-8")


def missing(path: Path, sections: tuple[str, ...]) -> list[str]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return [s for s in sections if f"## {s}" not in text or "[preencher]" in text.split(f"## {s}", 1)[1].split("## ", 1)[0]]


def check(root: Path) -> None:
    gaps = []
    gaps += [f"brainstorm: {s}" for s in missing(root / "brainstorm.md", BRAINSTORM)]
    gaps += [f"spec: {s}" for s in missing(root / "spec.md", SPEC)]
    decision = (root / "decision.md").read_text(encoding="utf-8") if (root / "decision.md").exists() else ""
    if "DECISAO: aceita" not in decision:
        gaps.append("decision: DECISAO: aceita")
    if gaps:
        raise SystemExit("gates incompletos:\n" + "\n".join(f"- {gap}" for gap in gaps))
    print("SPEC GATES: OK")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init"); i.add_argument("root", type=Path)
    c = sub.add_parser("check"); c.add_argument("root", type=Path)
    args = ap.parse_args(); root = args.root.resolve()
    if args.cmd == "init":
        root.mkdir(parents=True, exist_ok=True)
        template(root / "brainstorm.md", "Brainstorm", BRAINSTORM)
        template(root / "spec.md", "Spec", SPEC)
        (root / "decision.md").write_text("# Decisão\n\nDECISAO: pendente\n", encoding="utf-8")
    else:
        check(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
