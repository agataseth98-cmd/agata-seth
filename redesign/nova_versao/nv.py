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


LIMITE_APLICADAS = 50   # retroativo limitado: só as mais recentes entram no ledger (evita inundar com ~1100 antigas)


def sincronizar(repo: Path | None = None, limite_aplicadas: int = LIMITE_APLICADAS) -> dict:
    """(lote 5, A4) Liga as sete palavras a propostas reais. Cada proposta é um objeto:
    `.diff` aberto -> apresentacao; `APROVADO-` (assinada) -> assimilacao; em `propostas/aplicadas/` -> transicao.
    Só anda pelos passos previstos (eventos.caminho_ate) e grava cada passo com chave idempotente. Nunca Remoção."""
    raiz = Path(repo) if repo else Path(__file__).resolve().parents[2]
    pro = raiz / "propostas"
    alvos: dict[str, str] = {}
    for d in sorted(pro.glob("*.diff")):
        alvos[d.stem] = "apresentacao"
    for a in sorted(pro.glob("APROVADO-*")):
        nome = a.name[len("APROVADO-"):]
        if nome in alvos or (pro / f"{nome}.diff").exists():
            alvos[nome] = "assimilacao"
    aplicadas = sorted((pro / "aplicadas").glob("*.diff"), key=lambda p: p.stat().st_mtime) if (pro / "aplicadas").exists() else []
    for d in aplicadas[-limite_aplicadas:]:
        alvos[d.stem] = "transicao"
    feitos = []
    for nome, alvo in sorted(alvos.items()):
        objeto = f"proposta:{nome}"
        atual = eventos.ultimo_estado(objeto)
        try:
            passos = ([] if atual else ["apresentacao"]) + eventos.caminho_ate(atual or "apresentacao", alvo)
        except ValueError as e:
            feitos.append({"objeto": objeto, "erro": str(e)}); continue
        anterior = atual                      # None na primeira vez: a apresentação é o primeiro registro
        for passo in passos:
            eventos.transicao(objeto, anterior, passo, f"propostas/{nome}", chave=f"sete:{objeto}:{passo}",
                              componente="nova-versao")
            anterior = passo
        if passos:
            feitos.append({"objeto": objeto, "de": atual, "ate": alvo, "passos": passos})
    return {"propostas": len(alvos), "aplicadas_consideradas": min(len(aplicadas), limite_aplicadas), "movidas": feitos}


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    if argv[:1] == ["iniciar"]:
        print(json.dumps(iniciar(*(argv[1:2] or ["HEAD"])), ensure_ascii=False, indent=1)); return 0
    if argv == ["estado"]:
        print(json.dumps(estado(), ensure_ascii=False, indent=1)); return 0
    if argv == ["sincronizar"]:
        print(json.dumps(sincronizar(), ensure_ascii=False, indent=1)); return 0
    if argv == ["verificar"]:
        r = verificar(); print(json.dumps(r, ensure_ascii=False)); return 0 if r["ledger"] else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
