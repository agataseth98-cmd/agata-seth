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
import tempfile

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


MAX_SAIDA = 2_000_000          # bytes por fluxo (stdout/stderr); acima disso, corta (lote 5: bomba de saída)
MEM_MB_PADRAO = 512            # teto de memória virtual do processo filho


def _decodifica(b) -> str:
    if b is None:
        return ""
    if isinstance(b, str):
        return b[:MAX_SAIDA]
    return b[:MAX_SAIDA].decode("utf-8", errors="replace")   # bytes inválidos viram �, nunca levantam


def _limites(cpu_s: int, mem_mb: int):
    """preexec do filho: CPU, memória e tamanho de escrita limitados (o kernel corta a saída no teto)."""
    def aplicar():
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s))
        resource.setrlimit(resource.RLIMIT_AS, (mem_mb * 1024 * 1024, mem_mb * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_SAIDA, MAX_SAIDA))
    return aplicar


def _ler_limitado(f) -> str:
    f.seek(0)
    return f.read(MAX_SAIDA).decode("utf-8", errors="replace")


def run_sandboxed(
    argv: list[str],
    *,
    ro: list[str] | None = None,
    rw: list[str] | None = None,
    net: bool = False,
    cwd: str | None = None,
    stdin: str | None = None,
    timeout: int = 120,
    mem_mb: int = MEM_MB_PADRAO,
) -> dict:
    args = _base_args(net, cwd)
    for p in (ro or []):
        p = os.path.abspath(p)
        args += ["--ro-bind", p, p]
    for p in (rw or []):
        p = os.path.abspath(p)
        args += ["--bind", p, p]
    args += ["--"] + list(argv)
    entrada = stdin.encode("utf-8") if isinstance(stdin, str) else None
    # saída vai para arquivos temporários: o pai nunca guarda a saída inteira na memória
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            r = subprocess.run(args, input=entrada, stdout=out, stderr=err, timeout=timeout,
                               preexec_fn=_limites(max(1, int(timeout)), mem_mb))
            return {"exit_code": r.returncode, "stdout": _ler_limitado(out), "stderr": _ler_limitado(err),
                    "sandboxed": True}
        except subprocess.TimeoutExpired:
            return {"exit_code": 124, "stdout": _ler_limitado(out),
                    "stderr": _ler_limitado(err) + f"\n[timeout {timeout}s]", "sandboxed": True}
        except OSError as e:
            return {"exit_code": 127, "stdout": "", "stderr": f"[bwrap indisponivel: {e}]", "sandboxed": True}


def disponivel() -> bool:
    return bool(shutil.which("bwrap"))
