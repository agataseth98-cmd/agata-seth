#!/usr/bin/env python3
"""Guarded GitHub handoff for an SDD run.

The command never invents approval: it stops until the signed APROVADO file
exists, and it reports every external action before executing it.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, text=True, capture_output=True).stdout


def approval(repo: Path, name: str) -> Path:
    path = repo / "propostas" / f"APROVADO-{name}"
    if not path.exists():
        raise SystemExit(f"assinatura ausente: {path}")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", type=Path)
    ap.add_argument("name")
    ap.add_argument("--pr", type=int)
    ap.add_argument("--create", action="store_true")
    ap.add_argument("--merge", action="store_true")
    args = ap.parse_args()
    repo = args.repo.resolve()
    approval(repo, args.name)
    pr = args.pr
    if args.create:
        branch = f"aplica/{args.name}"
        print(f"AÇÃO EXTERNA: criar PR de aplicação {branch} contra main")
        url = gh("pr", "create", "--base", "main", "--head", branch,
                 "--title", f"aplica: {args.name}", "--body", f"Aplicação assinada {args.name}.")
        pr = int(url.rstrip("/\n").split("/")[-1])
    if not pr:
        raise SystemExit("informe --pr ou --create")
    print(f"AÇÃO EXTERNA: aguardar CI do PR #{pr}")
    subprocess.run(["gh", "pr", "checks", str(pr), "--watch", "--interval", "10"], check=True)
    if args.merge:
        print(f"AÇÃO EXTERNA: mergear PR #{pr}")
        gh("pr", "merge", str(pr), "--merge", "--delete-branch=false")
    result = json.loads(gh("pr", "view", str(pr), "--json", "state,mergeCommit"))
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
