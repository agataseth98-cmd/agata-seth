#!/usr/bin/env python3
"""Testes do critério de "em dia" de scripts/egress_em_dia.py, com arquivos temporários e mtimes fixos.
Não compila nada: sem cargo, sem rede, sem git. Quem decide compilar é o instalar/testar_egress_rust, não este teste."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import egress_em_dia as ed  # noqa: E402

T0 = 1_700_000_000  # época fixa: o teste controla o mtime, sem sleep


def montar(raiz: Path, mudar=None, sem=(), fonte=T0, binario=T0 + 100) -> Path:
    """Crate mínimo: fontes com mtime `fonte`, binários com `binario`. `mudar` troca mtimes; `sem` omite arquivos."""
    crate = raiz / "egress"
    arquivos = {"Cargo.toml": fonte, "Cargo.lock": fonte, "src/lib.rs": fonte, "src/main.rs": fonte,
                "src/bin/egress-socks5.rs": fonte, "tests/paridade.rs": fonte,
                "target/release/egress": binario, "target/release/egress-socks5": binario}
    arquivos.update(mudar or {})
    for rel, t in arquivos.items():
        if rel in sem:
            continue
        p = crate / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8")
        os.utime(p, (t, t))
    return crate


def main() -> int:
    casos = []
    with tempfile.TemporaryDirectory() as d:
        R = Path(d)
        n = [0]

        def novo(**kw):
            n[0] += 1
            return montar(R / f"c{n[0]}", **kw)

        casos.append(("em dia: binários mais novos que todas as fontes", ed.motivo(novo()) == ""))
        casos.append(("fonte em subpasta (src/bin) mais nova que o binário invalida",
                      ed.motivo(novo(mudar={"src/bin/egress-socks5.rs": T0 + 200})) != ""))
        casos.append(("Cargo.lock mais novo invalida", ed.motivo(novo(mudar={"Cargo.lock": T0 + 200})) != ""))
        casos.append(("Cargo.toml mais novo invalida", ed.motivo(novo(mudar={"Cargo.toml": T0 + 200})) != ""))
        casos.append(("tests/ mais novo NÃO invalida (cargo build não compila tests/)",
                      ed.motivo(novo(mudar={"tests/paridade.rs": T0 + 200})) == ""))
        casos.append(("comparação estrita: binário com o mesmo mtime da fonte não está em dia",
                      ed.motivo(novo(fonte=T0, binario=T0)) != ""))
        casos.append(("falta egress-socks5: precisa compilar",
                      "egress-socks5" in ed.motivo(novo(sem=("target/release/egress-socks5",)))))
        casos.append(("sem target/: precisa compilar", "falta" in ed.motivo(novo(sem=("target/release/egress", "target/release/egress-socks5")))))
        casos.append(("um binário mais velho que a fonte nova: aponta o binário atrasado",
                      ed.motivo(novo(mudar={"src/lib.rs": T0 + 150, "target/release/egress": T0 + 100, "target/release/egress-socks5": T0 + 200})) == "binário não é mais novo que a fonte mais nova: egress"))
        c = novo()
        ok_cli = subprocess.run([sys.executable, "-I", str(AQUI / "egress_em_dia.py"), str(c)], capture_output=True, text=True)
        casos.append(("CLI: em dia sai 0", ok_cli.returncode == 0 and ok_cli.stdout.startswith("em dia")))
        c2 = novo(mudar={"src/main.rs": T0 + 500})
        r2 = subprocess.run([sys.executable, "-I", str(AQUI / "egress_em_dia.py"), str(c2)], capture_output=True, text=True)
        casos.append(("CLI: precisa compilar sai 1 com o motivo", r2.returncode == 1 and r2.stdout.startswith("precisa compilar")))
    for nome, ok in casos:
        print(("PASS  " if ok else "FALHA ") + nome)
    ruins = [nome for nome, ok in casos if not ok]
    print(f"critério de em dia do egress: {len(casos) - len(ruins)}/{len(casos)}")
    return 1 if ruins else 0


if __name__ == "__main__":
    sys.exit(main())
