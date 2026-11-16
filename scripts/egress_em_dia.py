#!/usr/bin/env python3
"""Critério de "em dia" da compilação do crate redesign/rust/egress (robustez-16-11, 16/11/2026).

Em dia = os dois binários de target/release existem e têm mtime estritamente maior que o de todo arquivo de src/
(em qualquer subpasta) e de todo Cargo.* do crate. tests/ não entra: cargo build --release não compila tests/.
Só lê mtime: não chama cargo, não compila, não usa rede.

Uso: python3 -I scripts/egress_em_dia.py <dir-do-crate>
Saída 0 = em dia (pode pular a compilação); 1 = precisa compilar, com o motivo na saída.
"""
import sys
from pathlib import Path

BINARIOS = ("egress", "egress-socks5")


def binarios(crate: Path):
    return [crate / "target" / "release" / nome for nome in BINARIOS]


def fontes(crate: Path):
    return [p for p in (crate / "src").rglob("*") if p.is_file()] + [p for p in crate.glob("Cargo.*") if p.is_file()]


def motivo(crate: Path) -> str:
    """'' se os binários estão em dia; senão, o motivo de precisar compilar."""
    bins = binarios(crate)
    falta = [b.name for b in bins if not b.is_file()]
    if falta:
        return f"falta binário: {', '.join(falta)}"
    mais_nova = max((f.stat().st_mtime for f in fontes(crate)), default=0.0)
    atrasados = [b.name for b in bins if not b.stat().st_mtime > mais_nova]
    if atrasados:
        return f"binário não é mais novo que a fonte mais nova: {', '.join(atrasados)}"
    return ""


def main(argv) -> int:
    if len(argv) != 2:
        print("uso: egress_em_dia.py <dir-do-crate>")
        return 2
    m = motivo(Path(argv[1]))
    if not m:
        print("em dia: binários de target/release mais novos que src/ e Cargo.*")
        return 0
    print(f"precisa compilar: {m}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
