#!/usr/bin/env python3
"""
Contencao de execucao de tool via bubblewrap (P4-02).

`run_sandboxed(argv, ro=[...], rw=[...], net=False)` roda `argv` dentro de um `bwrap`
com:
  - todos os namespaces isolados (`--unshare-all`); rede so se `net=True` (`--share-net`)
  - `/usr` e `/etc` read-only; `/proc`, `/dev`, `/tmp` (tmpfs) minimos
  - Arch e' usr-merged -> `/bin`,`/lib`,`/lib64` sao symlink para `usr/...`
  - cada caminho em `ro` entra read-only; cada caminho em `rw` entra read-write
  - `--die-with-parent`, `--new-session`

So-leitura de tool (perimetro, query_canon, ...) roda com `rw=[]`. `commit_entry` recebe
`rw=[<.git do repo>, <arquivo alvo>]` e nada mais.

Nunca levanta: timeout -> 124; bwrap ausente -> 127.
"""
from __future__ import annotations

import os
import shutil
import subprocess

BWRAP = shutil.which("bwrap") or "/usr/bin/bwrap"


def _base_args(net: bool, cwd: str | None) -> list[str]:
    a = [BWRAP, "--unshare-all"]
    if net:
        a += ["--share-net"]
    a += [
        "--die-with-parent", "--new-session",
        "--ro-bind", "/usr", "/usr",
        "--ro-bind", "/etc", "/etc",
        "--symlink", "usr/lib", "/lib",
        "--symlink", "usr/lib", "/lib64",
        "--symlink", "usr/bin", "/bin",
        "--symlink", "usr/sbin", "/sbin",
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--setenv", "HOME", "/tmp",
        "--setenv", "PATH", "/usr/bin:/usr/sbin",
    ]
    if cwd:
        a += ["--chdir", cwd]
    return a


def run_sandboxed(
    argv: list[str],
    *,
    ro: list[str] | None = None,
    rw: list[str] | None = None,
    net: bool = False,
    cwd: str | None = None,
    stdin: str | None = None,
    timeout: int = 120,
) -> dict:
    args = _base_args(net, cwd)
    for p in (ro or []):
        p = os.path.abspath(p)
        args += ["--ro-bind", p, p]
    for p in (rw or []):
        p = os.path.abspath(p)
        args += ["--bind", p, p]
    args += ["--"] + list(argv)
    try:
        r = subprocess.run(args, input=stdin, capture_output=True, text=True, timeout=timeout)
        return {"exit_code": r.returncode, "stdout": r.stdout, "stderr": r.stderr, "sandboxed": True}
    except subprocess.TimeoutExpired as e:
        return {"exit_code": 124, "stdout": e.stdout or "", "stderr": (e.stderr or "") + f"\n[timeout {timeout}s]", "sandboxed": True}
    except OSError as e:
        return {"exit_code": 127, "stdout": "", "stderr": f"[bwrap indisponivel: {e}]", "sandboxed": True}


def disponivel() -> bool:
    return bool(shutil.which("bwrap"))
