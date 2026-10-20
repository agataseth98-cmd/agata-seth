#!/usr/bin/env python3
"""Execute os testes do módulo realmente acrescentado pelo patch do fork."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "redesign/librechat/fork/agata-capabilities.patch"
INCLUDES = (
    "api/server/services/agataCapabilities.js",
    "api/server/services/agataCapabilities.test.js",
)


def main() -> int:
    if not shutil.which("node") or not shutil.which("git"):
        print("FALHA: node e git são necessários para testar o módulo do fork")
        return 1
    with tempfile.TemporaryDirectory(prefix="agata-librechat-patch-test-") as temp:
        target = Path(temp)
        command = ["git", "apply", "-p1"]
        for path in INCLUDES:
            command.extend((f"--include={path}",))
        command.append(str(PATCH))
        applied = subprocess.run(command, cwd=target, text=True, capture_output=True)
        if applied.returncode:
            print(applied.stderr or "FALHA: não foi possível extrair os arquivos do patch")
            return applied.returncode
        test_file = target / INCLUDES[1]
        result = subprocess.run(
            ["node", "--test", str(test_file)], cwd=target, text=True
        )
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
