#!/usr/bin/env python3
"""Execute declared acceptance commands and emit criterion evidence."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("manifest", type=Path); ap.add_argument("output", type=Path)
    args = ap.parse_args(); manifest = json.loads(args.manifest.read_text(encoding="utf-8")); evidence = []
    for item in manifest:
        command = item["command"]
        result = subprocess.run(command, cwd=item.get("cwd") or None, capture_output=True, text=True, shell=False)
        evidence.append({"criterion": item["criterion"], "status": "pass" if result.returncode == 0 else "fail", "classification": "verified" if result.returncode == 0 else "defect", "command": command, "returncode": result.returncode, "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:], "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if all(row["status"] == "pass" for row in evidence) else 1


if __name__ == "__main__":
    raise SystemExit(main())
