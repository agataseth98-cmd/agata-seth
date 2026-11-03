#!/usr/bin/env python3
"""Deterministic coordinator for the Agata SDD lifecycle.

The runner performs only mechanical steps. Human decisions remain explicit
state transitions and are never inferred from generated files.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STAGES = ("bootstrap", "review", "decision", "implementation", "verification", "drift", "complete")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "stage": "new", "history": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record(state: dict, stage: str, detail: str) -> None:
    state["stage"] = stage
    state.setdefault("history", []).append({"at": now(), "stage": stage, "detail": detail})


def run(*args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def bootstrap(state: dict, project: Path, out: Path, goal: str) -> None:
    run("redesign/project_kit/bootstrap.py", str(project), "--out", str(out), "--goal", goal)
    record(state, "bootstrap", str(out))


def review(state: dict, out: Path) -> None:
    spec = out / "spec.md"
    reviews = out / "review-package"
    run("redesign/review_mesh/mesh.py", "prepare", str(spec), str(reviews))
    record(state, "review", str(reviews))


def consolidate(state: dict, out: Path) -> None:
    report = out / "consolidated-review.md"
    run("redesign/review_mesh/mesh.py", "consolidate", str(out / "review-package"), str(report))
    record(state, "decision", str(report))


def decision(state: dict, accepted: bool) -> None:
    if not accepted:
        raise SystemExit("decisão humana não aprovada")
    record(state, "decision", "decisão humana registrada")


def implementation(state: dict, worktree: Path) -> None:
    if not worktree.exists():
        raise SystemExit(f"worktree inexistente: {worktree}")
    record(state, "implementation", str(worktree.resolve()))


def verification(state: dict, tests: list[str], pytest_bin: str) -> None:
    executable = shutil.which(pytest_bin) if "/" not in pytest_bin else pytest_bin
    if not executable:
        raise SystemExit(f"pytest não encontrado: {pytest_bin}; informe --pytest-bin ou ajuste PATH")
    for target in tests:
        subprocess.run([executable, "-q", target], cwd=ROOT, check=True)
    record(state, "verification", f"{executable}:" + ";".join(tests))


def drift(state: dict, project: Path, previous: Path, output: Path) -> None:
    run("redesign/project_kit/bootstrap.py", str(project.resolve()), "--out", str(output.parent / "drift-kit"),
        "--goal", "drift", "--drift-against", str(previous.resolve()), "--drift-out", str(output.resolve()))
    record(state, "drift", str(output.resolve()))


def complete(state: dict) -> None:
    required = {entry["stage"] for entry in state.get("history", [])}
    missing = {"decision", "implementation", "verification", "drift"} - required
    if missing:
        raise SystemExit("etapas ausentes: " + ", ".join(sorted(missing)))
    record(state, "complete", "ciclo SDD encerrado")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("state", type=Path)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bootstrap")
    b.add_argument("project", type=Path); b.add_argument("out", type=Path); b.add_argument("--goal", required=True)
    for name in ("review", "consolidate"):
        sub.add_parser(name).add_argument("out", type=Path)
    d = sub.add_parser("decision"); d.add_argument("--accepted", action="store_true")
    sub.add_parser("implementation").add_argument("worktree", type=Path)
    v = sub.add_parser("verify"); v.add_argument("tests", nargs="+", type=str); v.add_argument("--pytest-bin", default="pytest")
    dr = sub.add_parser("drift"); dr.add_argument("project", type=Path); dr.add_argument("previous", type=Path); dr.add_argument("output", type=Path)
    sub.add_parser("complete")
    sub.add_parser("status")
    args = ap.parse_args()
    state = load(args.state)
    if args.cmd == "bootstrap": bootstrap(state, args.project.resolve(), args.out.resolve(), args.goal)
    elif args.cmd == "review": review(state, args.out.resolve())
    elif args.cmd == "consolidate": consolidate(state, args.out.resolve())
    elif args.cmd == "decision": decision(state, args.accepted)
    elif args.cmd == "implementation": implementation(state, args.worktree)
    elif args.cmd == "verify": verification(state, args.tests, args.pytest_bin)
    elif args.cmd == "drift": drift(state, args.project, args.previous, args.output)
    elif args.cmd == "complete": complete(state)
    else: print(json.dumps(state, ensure_ascii=False, indent=2))
    if args.cmd != "status":
        save(args.state, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
