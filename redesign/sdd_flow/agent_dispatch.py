#!/usr/bin/env python3
"""Dispatch isolated review packets to explicit agent commands."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROLES = ("simplificador", "operador", "implementador")


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("packets", type=Path); ap.add_argument("commands", type=Path)
    args = ap.parse_args(); commands = json.loads(args.commands.read_text(encoding="utf-8"))
    for role in ROLES:
        command = commands.get(role)
        if not command: raise SystemExit(f"comando ausente: {role}")
        packet = args.packets / role
        packet.mkdir(parents=True, exist_ok=True)
        subprocess.run(command, cwd=packet, check=True)
        if not (packet / "report.md").exists(): raise SystemExit(f"relatório ausente: {role}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
