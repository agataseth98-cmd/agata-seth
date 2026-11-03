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


def dispatch_reviews(state: dict, out: Path, commands: Path) -> None:
    reviews = out / "review-package"
    run("redesign/review_mesh/mesh.py", "prepare", str(out / "spec.md"), str(reviews))
    run("redesign/sdd_flow/agent_dispatch.py", str(reviews), str(commands))
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
    artifacts = state.get("artifacts", {})
    for key in ("spec", "consolidated_review", "evidence", "criterion_drift"):
        if not artifacts.get(key) or not Path(artifacts[key]).exists():
            missing.add(key)
    if missing:
        raise SystemExit("etapas ausentes: " + ", ".join(sorted(missing)))
    record(state, "complete", "ciclo SDD encerrado")


def artifact(state: dict, key: str, path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"artefato inexistente: {path}")
    state.setdefault("artifacts", {})[key] = str(path.resolve())


def spec_init(state: dict, root: Path) -> None:
    run("redesign/sdd_flow/spec_gate.py", "init", str(root)); artifact(state, "spec", root / "spec.md")


def spec_check(state: dict, root: Path) -> None:
    run("redesign/sdd_flow/spec_gate.py", "check", str(root)); artifact(state, "spec", root / "spec.md")


def review_check(state: dict, reviews: Path, output: Path) -> None:
    run("redesign/sdd_flow/independent_review.py", str(reviews), str(output)); artifact(state, "consolidated_review", output)


def acceptance(state: dict, manifest: Path, output: Path) -> None:
    run("redesign/sdd_flow/acceptance_runner.py", str(manifest), str(output)); artifact(state, "evidence", output)


def criterion_drift(state: dict, spec: Path, evidence: Path, output: Path) -> None:
    run("redesign/sdd_flow/criterion_drift.py", str(spec), str(evidence), str(output)); artifact(state, "criterion_drift", output)


def cycle(state: dict, root: Path, manifest: Path, scopes: list[str]) -> None:
    """Mechanical gates in order; stops at the first one that fails."""
    run("redesign/sdd_flow/spec_gate.py", "check", str(root))
    run("redesign/sdd_flow/anchor.py", str(ROOT), *scopes)
    evidence = root / "evidence.json"
    try:
        run("redesign/sdd_flow/acceptance_runner.py", str(manifest), str(evidence))
    finally:
        if evidence.exists():
            artifact(state, "evidence", evidence)
    artifact(state, "spec", root / "spec.md")
    criterion_drift(state, root / "spec.md", evidence, root / "criterion-drift.md")
    record(state, "cycle", "spec, âncora, aceite e drift por critério: OK")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("state", type=Path)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bootstrap")
    b.add_argument("project", type=Path); b.add_argument("out", type=Path); b.add_argument("--goal", required=True)
    for name in ("review", "consolidate"):
        sub.add_parser(name).add_argument("out", type=Path)
    rd = sub.add_parser("dispatch-reviews"); rd.add_argument("out", type=Path); rd.add_argument("commands", type=Path)
    d = sub.add_parser("decision"); d.add_argument("--accepted", action="store_true")
    sub.add_parser("implementation").add_argument("worktree", type=Path)
    v = sub.add_parser("verify"); v.add_argument("tests", nargs="+", type=str); v.add_argument("--pytest-bin", default="pytest")
    dr = sub.add_parser("drift"); dr.add_argument("project", type=Path); dr.add_argument("previous", type=Path); dr.add_argument("output", type=Path)
    sub.add_parser("complete")
    si = sub.add_parser("spec-init"); si.add_argument("root", type=Path)
    sc = sub.add_parser("spec-check"); sc.add_argument("root", type=Path)
    rc = sub.add_parser("review-check"); rc.add_argument("reviews", type=Path); rc.add_argument("output", type=Path)
    ac = sub.add_parser("acceptance"); ac.add_argument("manifest", type=Path); ac.add_argument("output", type=Path)
    cd = sub.add_parser("criterion-drift"); cd.add_argument("spec", type=Path); cd.add_argument("evidence", type=Path); cd.add_argument("output", type=Path)
    cy = sub.add_parser("cycle"); cy.add_argument("root", type=Path); cy.add_argument("manifest", type=Path); cy.add_argument("--scope", nargs="+", required=True)
    sub.add_parser("status")
    args = ap.parse_args()
    state = load(args.state)
    if args.cmd == "bootstrap": bootstrap(state, args.project.resolve(), args.out.resolve(), args.goal)
    elif args.cmd == "review": review(state, args.out.resolve())
    elif args.cmd == "dispatch-reviews": dispatch_reviews(state, args.out.resolve(), args.commands.resolve())
    elif args.cmd == "consolidate": consolidate(state, args.out.resolve())
    elif args.cmd == "decision": decision(state, args.accepted)
    elif args.cmd == "implementation": implementation(state, args.worktree)
    elif args.cmd == "verify": verification(state, args.tests, args.pytest_bin)
    elif args.cmd == "drift": drift(state, args.project, args.previous, args.output)
    elif args.cmd == "complete": complete(state)
    elif args.cmd == "spec-init": spec_init(state, args.root.resolve())
    elif args.cmd == "spec-check": spec_check(state, args.root.resolve())
    elif args.cmd == "review-check": review_check(state, args.reviews, args.output)
    elif args.cmd == "acceptance": acceptance(state, args.manifest, args.output)
    elif args.cmd == "criterion-drift": criterion_drift(state, args.spec, args.evidence, args.output)
    elif args.cmd == "cycle": cycle(state, args.root.resolve(), args.manifest.resolve(), args.scope)
    else: print(json.dumps(state, ensure_ascii=False, indent=2))
    if args.cmd != "status":
        save(args.state, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
