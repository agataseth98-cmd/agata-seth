#!/usr/bin/env python3
"""nv — a nova versão do Agata (Experimento GPT) num só comando, para terminal e painel.

Spec-mãe: `redesign/nova_versao/spec/spec.md`. Componentes do lote 1 (sombra, sem
inferência): Alexandria (acervo, consulta, skills), metacognição (antes/depois),
corpo (fotografia e saúde), orçamento e eventos.

  nv.py iniciar          cria as pastas de trabalho, tira snapshot do HEAD e indexa
  nv.py estado           estado de todos os componentes (JSON)
  nv.py verificar        confere o ledger encadeado e o índice
  nv.py --selftest       teste offline, em pasta temporária
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RED = AQUI.parent
for _p in (AQUI, RED / "alexandria", RED / "corpo", RED / "metacognicao"):
    sys.path.insert(0, str(_p))
import eventos  # noqa: E402
import orcamento  # noqa: E402


def iniciar(commit: str = "HEAD") -> dict:
    import acervo  # noqa: E402
    base = acervo.iniciar()
    snap = acervo.snapshot(commit)
    return {"dados": str(base), "snapshot": str(snap), **acervo.indexar(snap)}


def _sombra() -> dict:
    p = eventos.dados() / "metacognicao" / "sombra.jsonl"
    try:
        linhas = p.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {"registros": 0, "ultimo": None}
    ultimo = json.loads(linhas[-1]) if linhas else None
    return {"registros": len(linhas), "ultimo": ultimo}


def estado() -> dict:
    import acervo  # noqa: E402
    import fotografar  # noqa: E402
    import saude  # noqa: E402
    foto = fotografar.ultima()
    try:
        ledger_ok = eventos.verificar()
    except Exception as e:  # noqa: BLE001
        ledger_ok = f"FALHA: {e}"
    return {"schema_version": 1, "dados": str(eventos.dados()), "alexandria": acervo.estado(),
            "orcamento": orcamento.ler(),
            "corpo": {"fotografia": {k: foto[k] for k in ("quando", "revalidar_ate", "servicos", "recursos")} if foto else None,
                      "saude": saude.classificar(foto) if foto else {"estado": "não medido"}},
            "sombra": _sombra(), "ledger_ok": ledger_ok, "eventos": eventos.ultimos(12)}


def verificar() -> dict:
    import acervo  # noqa: E402
    out = {"ledger": eventos.verificar(), "indice": bool(acervo.meta())}
    return out


def _selftest() -> int:
    import subprocess
    with tempfile.TemporaryDirectory() as t:
        os.environ["AGATA_NV_DIR"] = t + "/dados"
        os.environ["AGATA_NV_CACHE"] = t + "/cache"
        repo = Path(t) / "repo"
        (repo / "memoria").mkdir(parents=True)
        (repo / "MEMÓRIAS.md").write_text("# M\n\n(10) DIÁRIO — x · travamento no suspend, ver (11)\n\n(11) DIÁRIO — y · base\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"], check=True)
        import acervo  # noqa: E402
        acervo.iniciar()
        snap = acervo.snapshot("HEAD", repo)
        r = acervo.indexar(snap, skills=False)
        pac = acervo.consultar("suspend travamento", semantica="nunca")
        vazio = acervo.consultar("palavrainexistentezz", semantica="nunca")
        casos = [
            ("estrutura criada", (Path(t) / "dados" / "LEIA-ME.md").exists()),
            ("índice com 2 entradas", r["objetos"] >= 2),
            ("consulta acha (10) com sha e commit", pac["resultados"] and pac["resultados"][0]["entrada"] == 10
             and len(pac["resultados"][0]["sha256"]) == 64 and pac["commit"]),
            ("relação (10)->(11) segue", any(x["metodo"] == "relacao" and x["entrada"] == 11 for x in pac["resultados"])),
            ("ausência diz 'não encontrado nesta busca'", vazio["estado"] == acervo.NAO_ENCONTRADO),
            ("orçamento padrão só local", orcamento.ler()["provedores"] == {"local": True, "gratuito": False, "assinatura": False, "pago": False}),
            ("ledger íntegro", eventos.verificar()),
        ]
    for nome, ok in casos:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
    falhas = sum(not ok for _, ok in casos)
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    if argv[:1] == ["iniciar"]:
        print(json.dumps(iniciar(*(argv[1:2] or ["HEAD"])), ensure_ascii=False, indent=1)); return 0
    if argv == ["estado"]:
        print(json.dumps(estado(), ensure_ascii=False, indent=1)); return 0
    if argv == ["verificar"]:
        r = verificar(); print(json.dumps(r, ensure_ascii=False)); return 0 if r["ledger"] else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
