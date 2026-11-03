#!/usr/bin/env python3
"""Anchor existing components to a SPEC.md and block orphan or ghost code.

Brownfield retrofit: a component is anchored when its directory has spec/spec.md
(or SPEC.md)
with the sections Contrato and Critérios de aceite, and a Código section that
lists every source file (backticked). Listing `tests/` owns that whole subtree.
The check is mechanical: it never writes and never invents ownership.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


SOURCE = (".py", ".sh", ".js", ".html")
REQUIRED = ("Contrato", "Critérios de aceite", "Código")


def section(text: str, name: str) -> str | None:
    parts = re.split(rf"^## {re.escape(name)}\s*$", text, maxsplit=1, flags=re.M)
    return parts[1].split("\n## ", 1)[0] if len(parts) == 2 else None


def check_component(root: Path, scope: str) -> list[str]:
    base = root / scope
    spec = next((c for c in (base / "spec" / "spec.md", base / "SPEC.md") if c.exists()), None)
    if spec is None:
        return [f"{scope}: sem SPEC.md (nem spec/spec.md)"]
    text = spec.read_text(encoding="utf-8")
    gaps = [f"{scope}: seção ausente ou vazia: {name}" for name in REQUIRED if not (section(text, name) or "").strip()]
    owned = set(re.findall(r"`([^`\n]+)`", section(text, "Código") or ""))
    files = sorted(
        p.relative_to(base).as_posix()
        for p in base.rglob("*")
        if p.is_file() and p.suffix in SOURCE and "__pycache__" not in p.parts
    )
    for rel in files:
        if not any(rel == own or (own.endswith("/") and rel.startswith(own)) for own in owned):
            gaps.append(f"{scope}: código órfão (sem dono na SPEC): {rel}")
    for own in sorted(owned):
        if not (base / own).exists():
            gaps.append(f"{scope}: SPEC cita arquivo inexistente: {own}")
    return gaps


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", type=Path)
    ap.add_argument("scopes", nargs="+")
    args = ap.parse_args()
    gaps = [gap for scope in args.scopes for gap in check_component(args.repo.resolve(), scope)]
    if gaps:
        raise SystemExit("âncora incompleta:\n" + "\n".join(f"- {gap}" for gap in gaps))
    print("ANCHOR: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
