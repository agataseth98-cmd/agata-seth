#!/usr/bin/env python3
"""Paridade Python x Rust da política de egress (D6, decisão do Humano, 15/11/2026).

Compila redesign/rust/egress (cargo build --release), roda `egress ip` em cada
caso e compara o veredito (bloqueia ou não) com politica_egress._ip_bloqueado_py.
Também prova que, com AGATA_EGRESS_RUST, _ip_bloqueado nunca afrouxa.
Sem cargo: SKIP com código 0 só se AGATA_EGRESS_RUST_OPCIONAL=1; senão falha.
"""
import os, shutil, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import politica_egress as pe  # noqa: E402

CASOS = ["1.1.1.1", "8.8.8.8", "127.0.0.1", "10.0.0.5", "172.16.0.1", "192.168.1.1",
         "169.254.169.254", "0.0.0.0", "100.64.0.1", "224.0.0.1", "255.255.255.255",
         "::1", "fe80::1", "fc00::1", "2606:4700:4700::1111", "::ffff:127.0.0.1"]
# Divergência medida em 15/11/2026: o ipaddress do Python 3.14 trata multicast
# 224.0.0.1 como global (passa); o Rust bloqueia. Com AGATA_EGRESS_RUST vale o bloqueio.
RUST_MAIS_ESTRITO = {"224.0.0.1"}


def main() -> int:
    if not shutil.which("cargo"):
        if os.environ.get("AGATA_EGRESS_RUST_OPCIONAL") == "1":
            print("SKIP  cargo ausente"); return 0
        print("FALHA cargo ausente"); return 1
    crate = RAIZ / "redesign/rust/egress"
    subprocess.run(["cargo", "build", "--release", "--quiet"], cwd=crate, check=True)
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
    print("PARIDADE OK" if ok else "PARIDADE FALHOU")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
