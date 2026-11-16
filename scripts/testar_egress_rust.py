#!/usr/bin/env python3
"""Paridade Python x Rust da política de egress (D6, decisão do Humano, 15/11/2026).

Compila redesign/rust/egress (cargo build --release), roda `egress ip` em cada
caso e compara o veredito (bloqueia ou não) com politica_egress._ip_bloqueado_py.
Também prova que, com AGATA_EGRESS_RUST, _ip_bloqueado nunca afrouxa.
Sem cargo: SKIP com código 0 só se AGATA_EGRESS_RUST_OPCIONAL=1; senão falha.

Robustez (16/11/2026): a compilação roda com `nice -n 15` e CARGO_BUILD_JOBS (padrão 2, sobrescrevível pela variável).
Pula a compilação quando os binários de target/release estão em dia (scripts/egress_em_dia.py).
`--sem-compilar` nunca compila: usa o binário que já existe (falha se faltar).
"""
import os, shutil, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import politica_egress as pe  # noqa: E402
import egress_em_dia as ed  # noqa: E402

CASOS = ["1.1.1.1", "8.8.8.8", "127.0.0.1", "10.0.0.5", "172.16.0.1", "192.168.1.1",
         "169.254.169.254", "0.0.0.0", "100.64.0.1", "224.0.0.1", "255.255.255.255",
         "::1", "fe80::1", "fc00::1", "2606:4700:4700::1111", "::ffff:127.0.0.1"]
# Divergência medida em 15/11/2026: o ipaddress do Python 3.14 trata multicast
# 224.0.0.1 como global (passa); o Rust bloqueia. Com AGATA_EGRESS_RUST vale o bloqueio.
RUST_MAIS_ESTRITO = {"224.0.0.1"}


def _pedir(url: str, ip: bytes, porta: int) -> int:
    import socket
    host, p = url.rsplit("/", 1)[1].split(":")
    with socket.create_connection((host, int(p)), timeout=5) as c:
        c.sendall(b"\x05\x01\x00"); c.recv(2)
        c.sendall(b"\x05\x01\x00\x01" + ip + porta.to_bytes(2, "big"))
        return c.recv(10)[1]


def _testar_socks5(binario: Path) -> bool:
    """O binário real recusa loopback e rede privada com status 2, via EgressProxy."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ep", RAIZ / "redesign/mcp/navegador/egress_proxy.py")
    ep = importlib.util.module_from_spec(spec); spec.loader.exec_module(ep)
    os.environ["AGATA_EGRESS_RUST_SOCKS5"] = str(binario)
    proxy = ep.EgressProxy().start()
    ok = type(proxy).__name__ == "_EgressProxyRust"
    try:
        for ip in (b"\x7f\x00\x00\x01", b"\x0a\x00\x00\x05", b"\xa9\xfe\xa9\xfe"):
            st = _pedir(proxy.url, ip, 80)
            print(f"{'PASS' if st == 2 else 'FALHA'}  socks5 rust recusa {'.'.join(map(str, ip))} (status {st})")
            ok = ok and st == 2
    finally:
        proxy.close()
    os.environ["AGATA_EGRESS_RUST_SOCKS5"] = "/inexistente"
    py = ep.EgressProxy(); ok = ok and type(py).__name__ == "_EgressProxyPython"; py.start(); py.close()
    print(f"{'PASS' if ok else 'FALHA'}  socks5: Rust quando há binário, Python quando não há")
    return ok


def _compilar(crate: Path) -> None:
    """cargo build --release com nice -n 15 e CARGO_BUILD_JOBS (padrão 2; a variável sobrescreve)."""
    env = dict(os.environ, CARGO_BUILD_JOBS=os.environ.get("CARGO_BUILD_JOBS", "2"))
    subprocess.run(["nice", "-n", "15", "cargo", "build", "--release", "--quiet"], cwd=crate, check=True, env=env)


def main() -> int:
    crate = RAIZ / "redesign/rust/egress"
    if "--sem-compilar" in sys.argv[1:]:
        faltam = [b.name for b in ed.binarios(crate) if not b.is_file()]
        if faltam:
            if os.environ.get("AGATA_EGRESS_RUST_OPCIONAL") == "1":
                print(f"SKIP  --sem-compilar sem binário ({', '.join(faltam)})"); return 0
            print(f"FALHA --sem-compilar sem binário ({', '.join(faltam)}); rode scripts/instalar_egress_rust.sh"); return 1
        print("PULA  compilação (--sem-compilar): usando os binários de target/release")
    elif ed.motivo(crate) == "":
        print("PULA  compilação: binários de target/release em dia")
    else:
        if not shutil.which("cargo"):
            if os.environ.get("AGATA_EGRESS_RUST_OPCIONAL") == "1":
                print("SKIP  cargo ausente"); return 0
            print("FALHA cargo ausente"); return 1
        _compilar(crate)
    binario = str(crate / "target/release/egress")
    ok = True
    for ip in CASOS:
        py = pe._ip_bloqueado_py(ip) is not None
        r = subprocess.run([binario, "ip", ip], capture_output=True, text=True)
        rs = r.returncode == 1
        esperado_ok = (py == rs) or (ip in RUST_MAIS_ESTRITO and rs and not py)
        nota = " (divergência conhecida: Rust mais estrito)" if py != rs and esperado_ok else ""
        print(f"{'PASS' if esperado_ok else 'FALHA'}  {ip}: python={'bloq' if py else 'livre'} rust={'bloq' if rs else 'livre'}{nota}")
        ok = ok and esperado_ok
    os.environ["AGATA_EGRESS_RUST"] = binario
    for ip in CASOS:
        if pe._ip_bloqueado_py(ip) is not None and pe._ip_bloqueado(ip) is None:
            print(f"FALHA {ip}: segunda opinião afrouxou"); ok = False
    for ip in RUST_MAIS_ESTRITO:
        if pe._ip_bloqueado(ip) is None:
            print(f"FALHA {ip}: com a camada Rust ligada deveria bloquear"); ok = False
    os.environ["AGATA_EGRESS_RUST"] = "/inexistente/egress"
    ok = ok and pe._ip_bloqueado("1.1.1.1") is None
    ok = _testar_socks5(crate / "target/release/egress-socks5") and ok
    print("PARIDADE OK" if ok else "PARIDADE FALHOU")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
