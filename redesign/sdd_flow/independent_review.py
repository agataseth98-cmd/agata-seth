#!/usr/bin/env python3
"""Validate independent review packets and preserve disagreements."""
from __future__ import annotations

import argparse
from pathlib import Path


ROLES = ("simplificador", "operador", "implementador")
REQUIRED = ("Contexto do revisor", "Veredito", "Achados")


def check_packet(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return [heading for heading in REQUIRED if f"## {heading}" not in text]


def consolidate(root: Path, output: Path) -> None:
    blocks = []
    for role in ROLES:
        report = root / role / "report.md"
        gaps = check_packet(report)
        if gaps:
            raise SystemExit(f"relatório incompleto: {role}: {', '.join(gaps)}")
        blocks.append(f"## {role}\n\n{report.read_text(encoding='utf-8').rstrip()}\n")
    output.write_text("# Consolidação independente\n\n" + "\n".join(blocks), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("reviews", type=Path); ap.add_argument("output", type=Path)
    args = ap.parse_args(); consolidate(args.reviews.resolve(), args.output.resolve()); return 0


if __name__ == "__main__":
    raise SystemExit(main())
