#!/usr/bin/env python3
"""Compare implemented behavior against explicit acceptance criteria."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def criteria(spec: Path) -> list[str]:
    return [line[6:].strip() for line in spec.read_text(encoding="utf-8").splitlines() if line.startswith("- [ ] ") or line.startswith("- [x] ")]


def report(spec: Path, evidence: Path, output: Path) -> None:
    wanted = criteria(spec)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    rows = []
    for item in wanted:
        match = next((entry for entry in data if entry.get("criterion") == item), None)
        if not match:
            rows.append((item, "unmeasured", "evidence missing"))
        else:
            rows.append((item, match.get("status", "unmeasured"), match.get("classification", "unclassified")))
    text = "# Criterion drift report\n\n" + "\n".join(f"- `{criterion}` — **{status}** — {classification}" for criterion, status, classification in rows) + "\n"
    output.write_text(text, encoding="utf-8")
    if any(status == "unmeasured" for _, status, _ in rows):
        raise SystemExit("critério sem evidência")


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("spec", type=Path); ap.add_argument("evidence", type=Path); ap.add_argument("output", type=Path)
    args = ap.parse_args(); report(args.spec.resolve(), args.evidence.resolve(), args.output.resolve()); return 0


if __name__ == "__main__":
    raise SystemExit(main())
