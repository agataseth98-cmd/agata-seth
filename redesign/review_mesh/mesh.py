#!/usr/bin/env python3
"""Review Mesh offline: prepara pacotes mínimos e consolida relatórios."""
import argparse, json
from pathlib import Path

ROLES = {
    "simplificador": "Procure uma solução mais simples e capacidades existentes.",
    "operador": "Procure falhas sob carga, repetição, recuperação e operação.",
    "implementador": "Verifique se a spec é implementável sem adivinhação.",
}

def prepare(spec: Path, out: Path):
    text = spec.read_text(encoding="utf-8")
    out.mkdir(parents=True, exist_ok=True)
    (out / "README.md").write_text("# Review Mesh\n\nPacotes independentes; nenhum revisor recebe a conversa original.\n", encoding="utf-8")
    for role, question in ROLES.items():
        d = out / role; d.mkdir(exist_ok=True)
        (d / "packet.md").write_text(f"# Revisão: {role}\n\n## Pergunta\n{question}\n\n## Spec\n\n{text}\n\n## Relatório\n\nPreencha com achados, evidência, severidade e recomendação.\n", encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps({"spec": str(spec), "roles": sorted(ROLES)}, indent=2) + "\n", encoding="utf-8")

def consolidate(reviews: Path, output: Path):
    rows = []
    for role in sorted(ROLES):
        report = reviews / role / "report.md"
        rows.append(f"## {role}\n\n" + (report.read_text(encoding="utf-8") if report.exists() else "Relatório ausente; revisão não medida.") + "\n")
    output.write_text("# Consolidação de revisões\n\n" + "\n".join(rows), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare"); p.add_argument("spec", type=Path); p.add_argument("out", type=Path)
    c = sub.add_parser("consolidate"); c.add_argument("reviews", type=Path); c.add_argument("output", type=Path)
    a = ap.parse_args()
    if a.cmd == "prepare": prepare(a.spec, a.out)
    else: consolidate(a.reviews, a.output)

if __name__ == "__main__": main()
