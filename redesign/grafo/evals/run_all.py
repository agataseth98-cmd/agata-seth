#!/usr/bin/env python3
"""Roda a suite de eval do loop (P4-05). exit 0 = tudo PASS."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable

rc = 0
for nome in ("fabricacao.py", "hidratacao.py"):
    print(f"\n{'=' * 20} {nome} {'=' * 20}", flush=True)
    r = subprocess.run([PY, str(HERE / nome)])
    rc = rc or r.returncode
print("\n" + ("SUITE DE EVAL: PASS" if rc == 0 else "SUITE DE EVAL: FALHA"), flush=True)
sys.exit(rc)
