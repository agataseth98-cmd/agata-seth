#!/usr/bin/env python3
"""Projeto SDD declarativo: o ciclo mecânico sobre QUALQUER projeto, sem escrever nele.

Um descritor JSON diz onde está o projeto, onde fica a spec, o que ancorar e quais critérios rodar. O ciclo
(gates da spec, âncora, critérios de aceite, drift por critério, drift de arquivos) roda contra a raiz do
projeto, grava tudo FORA dele (padrão ~/.cache/agata/sdd/<nome>/) e acrescenta o resultado, pass ou fail, a um
ledger encadeado por hash. Falha também vira evidência: o relatório e o ledger saem mesmo quando um passo reprova.

Descritor (todas as chaves menos `nome` e `raiz` têm padrão):
  {"nome": "contador", "raiz": "/abs/projeto", "spec": "spec", "escopos": ["."],
   "criterios": "spec/acceptance.json", "ambiente": {"PYTHONPATH": "."}, "saida": "/abs/saida", "limite_s": 300}

Os critérios só podem ser `pytest [-q] [-x] <alvo>...` com alvo relativo dentro da raiz (sem `..`, sem caminho
absoluto): o manifesto mora no projeto, que não é canon, então o painel e o ciclo nunca executam comando livre.
Uso: project.py <descritor.json>   |   --selftest      Exit 0 = tudo passou; 1 = algum passo reprovou; 2 = descritor inválido.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
NOME = re.compile(r"[a-z][a-z0-9-]{0,40}")
CHAVES_AMBIENTE = {"PYTHONPATH", "PYTHONHASHSEED", "TZ", "LANG", "LC_ALL", "NODE_PATH"}
ALVO = re.compile(r"[A-Za-z0-9_./-]+(::[A-Za-z0-9_.\[\]-]+)*")


class DescritorInvalido(ValueError):
    pass


def _rel_seguro(valor: str) -> bool:
    p = Path(valor)
    return not p.is_absolute() and ".." not in p.parts


def carregar(caminho: Path) -> dict:
    try:
        d = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DescritorInvalido(f"descritor ilegível: {exc}") from exc
    if not isinstance(d, dict) or not isinstance(d.get("nome"), str) or not NOME.fullmatch(d["nome"]):
        raise DescritorInvalido("nome ausente ou inválido (minúsculas, dígitos e hífen)")
    raiz = Path(str(d.get("raiz", "")))
    if not raiz.is_absolute() or not raiz.is_dir():
        raise DescritorInvalido("raiz precisa ser um diretório absoluto existente")
    d["raiz"] = str(raiz.resolve())
    d.setdefault("spec", "spec"); d.setdefault("escopos", ["."]); d.setdefault("criterios", "spec/acceptance.json")
    d.setdefault("ambiente", {}); d.setdefault("limite_s", 300)
    for chave in ("spec", "criterios"):
        if not isinstance(d[chave], str) or not _rel_seguro(d[chave]):
            raise DescritorInvalido(f"{chave} precisa ser relativo à raiz, sem ..")
    if not isinstance(d["escopos"], list) or not d["escopos"] or not all(isinstance(e, str) and _rel_seguro(e) for e in d["escopos"]):
        raise DescritorInvalido("escopos: lista de caminhos relativos à raiz, sem ..")
    if not isinstance(d["ambiente"], dict) or not set(d["ambiente"]) <= CHAVES_AMBIENTE or not all(isinstance(v, str) for v in d["ambiente"].values()):
        raise DescritorInvalido(f"ambiente: só as chaves {sorted(CHAVES_AMBIENTE)}, com valor texto")
    if not isinstance(d["limite_s"], int) or not 1 <= d["limite_s"] <= 3600:
        raise DescritorInvalido("limite_s: inteiro de 1 a 3600")
    if d.get("saida") is not None and not Path(str(d["saida"])).is_absolute():
        raise DescritorInvalido("saida, se informada, precisa ser absoluta")
    return d


def comando_valido(comando) -> bool:
    if not (isinstance(comando, list) and len(comando) >= 2 and all(isinstance(c, str) for c in comando)) or comando[0] != "pytest":
        return False
    alvos = [c for c in comando[1:] if c not in ("-q", "-x")]
    return bool(alvos) and all(not a.startswith("-") and ALVO.fullmatch(a) and _rel_seguro(a.split("::", 1)[0]) for a in alvos)


def _ambiente(d: dict) -> dict:
    saida = {}
    for chave, valor in d["ambiente"].items():
        partes = [str(Path(d["raiz"]) / p) if _rel_seguro(p) else p for p in valor.split(os.pathsep)]
        saida[chave] = os.pathsep.join(partes) if chave in ("PYTHONPATH", "NODE_PATH") else valor
    return saida


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""


def _rodar(args: list[str], limite: int) -> tuple[int, str]:
    try:
        r = subprocess.run(args, cwd=AQUI.parents[1], capture_output=True, text=True, timeout=limite)
        return r.returncode, (r.stdout + r.stderr).strip()[-500:]
    except subprocess.TimeoutExpired:
        return 124, f"tempo esgotado ({limite} s)"


def executar(caminho_descritor: Path) -> dict:
    d = carregar(caminho_descritor)
    raiz = Path(d["raiz"])
    saida = Path(d["saida"]) if d.get("saida") else Path.home() / ".cache" / "agata" / "sdd" / d["nome"]
    (saida / "execucoes").mkdir(parents=True, exist_ok=True, mode=0o700)
    while True:  # microssegundos + exclusão mútua: duas execuções no mesmo instante não dividem a pasta
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        run = saida / "execucoes" / run_id
        try:
            run.mkdir(mode=0o700)
            break
        except FileExistsError:
            continue
    passos: list[dict] = []

    def passo(nome: str, ok: bool, detalhe: str) -> bool:
        passos.append({"passo": nome, "ok": ok, "detalhe": detalhe[:300]})
        return ok

    py = sys.executable
    seguir = True
    spec_dir = raiz / d["spec"]
    rc, txt = _rodar([py, str(AQUI / "spec_gate.py"), "check", str(spec_dir)], d["limite_s"])
    seguir = passo("gates da spec", rc == 0, txt.replace("\n", " ") or "ok")
    if seguir:
        rc, txt = _rodar([py, str(AQUI / "anchor.py"), str(raiz), *d["escopos"]], d["limite_s"])
        seguir = passo("âncora", rc == 0, txt.replace("\n", " ") or "ok")
    manifesto = raiz / d["criterios"]
    evidencia, deriva = run / "evidence.json", run / "criterion-drift.md"
    if seguir:
        try:
            itens = json.loads(manifesto.read_text(encoding="utf-8"))
            ruins = [i.get("criterion", "?") for i in itens if not comando_valido(i.get("command"))]
        except (OSError, ValueError, AttributeError):
            itens, ruins = [], ["manifesto ilegível"]
        if ruins or not itens:
            seguir = passo("critérios", False, "comando fora do padrão pytest ou manifesto vazio: " + "; ".join(ruins[:2]))
        else:
            tem_pytest = shutil.which("pytest") is not None
            # nada de bytecode nem cache dentro do projeto: o ciclo não escreve nele
            normal = [{"criterion": i["criterion"], "command": ([i["command"][0], "-p", "no:cacheprovider", *i["command"][1:]] if tem_pytest else [py, "-m", i["command"][0], "-p", "no:cacheprovider", *i["command"][1:]]),
                       "cwd": str(raiz), "env": {**_ambiente(d), "PYTHONDONTWRITEBYTECODE": "1"}, "timeout": d["limite_s"]} for i in itens]
            (run / "manifesto-normalizado.json").write_text(json.dumps(normal, ensure_ascii=False, indent=2), encoding="utf-8")
            rc, _ = _rodar([py, str(AQUI / "acceptance_runner.py"), str(run / "manifesto-normalizado.json"), str(evidencia)], d["limite_s"] * len(normal) + 30)
            ev = json.loads(evidencia.read_text(encoding="utf-8")) if evidencia.exists() else []
            aprovados = sum(1 for e in ev if e.get("status") == "pass")
            seguir = passo("critérios", rc == 0 and bool(ev), f"{aprovados}/{len(normal)} passaram")
            if evidencia.exists():
                rc2, txt2 = _rodar([py, str(AQUI / "criterion_drift.py"), str(spec_dir / "spec.md"), str(evidencia), str(deriva)], 60)
                passo("drift por critério", rc2 == 0, txt2.replace("\n", " ") or "todo critério tem evidência")
    # drift de arquivos contra a execução anterior (o kit anterior é guardado fora do projeto)
    kit, anterior = run / "kit", saida / "ultimo" / "kit"
    rc, txt = _rodar([py, str(AQUI.parent / "project_kit" / "bootstrap.py"), str(raiz), "--out", str(kit), "--goal", f"SDD {d['nome']}"], 120)
    if rc == 0 and (anterior / "provenance.json").exists():
        rc3, txt3 = _rodar([py, str(AQUI.parent / "project_kit" / "bootstrap.py"), str(raiz), "--out", str(kit), "--goal", "drift",
                            "--drift-against", str(anterior / "provenance.json"), "--drift-out", str(run / "file-drift.md")], 120)
        passo("drift de arquivos", rc3 == 0, "comparado com a execução anterior" if rc3 == 0 else txt3)
    elif rc == 0:
        passo("drift de arquivos", True, "primeira execução: sem base para comparar")
    else:
        passo("drift de arquivos", False, txt)
    ok = all(p["ok"] for p in passos)
    relatorio = {"nome": d["nome"], "raiz": d["raiz"], "run_id": run_id, "ok": ok, "passos": passos,
                 "artefatos": {n: str(p) for n, p in (("evidencia", evidencia), ("drift_criterios", deriva), ("drift_arquivos", run / "file-drift.md")) if p.exists()}}
    (run / "relatorio.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    (run / "relatorio.md").write_text(f"# SDD {d['nome']} · {run_id} · {'OK' if ok else 'FALHOU'}\n\n" + "\n".join(f"- {'OK' if p['ok'] else 'FALHOU'} · {p['passo']}: {p['detalhe']}" for p in passos) + "\n", encoding="utf-8")
    sys.path.insert(0, str(AQUI.parent / "evidence_ledger"))
    from ledger import append
    append(saida / "ledger.jsonl", {
        "id": hashlib.sha256(f"{d['nome']}|{run_id}".encode()).hexdigest()[:16], "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "actor": "sdd-project", "project": d["nome"], "kind": "verification", "status": "pass" if ok else "fail",
        "source": str(run / "relatorio.json"), "input_hash": _sha(manifesto), "output_hash": _sha(run / "relatorio.json"),
        "authorization": "human-requested-cycle", "classification": "project",
        "metadata": {"run_id": run_id, "passos": len(passos), "falhas": [p["passo"] for p in passos if not p["ok"]]}})
    if (kit / "provenance.json").exists():
        (saida / "ultimo").mkdir(parents=True, exist_ok=True)
        shutil.rmtree(saida / "ultimo" / "kit", ignore_errors=True)
        shutil.copytree(kit, saida / "ultimo" / "kit")
    (saida / "ultimo.json").write_text(json.dumps({"run_id": run_id, "ok": ok, "relatorio": str(run / "relatorio.json")}), encoding="utf-8")
    return relatorio


def _selftest() -> int:
    falhou = 0
    def conferir(nome, cond):
        nonlocal falhou
        print(("PASS " if cond else "FALHA ") + nome); falhou += 0 if cond else 1
    conferir("comando pytest com alvos relativos é aceito", comando_valido(["pytest", "-q", "tests/test_a.py::test_x"]))
    for ruim in (["bash", "-c", "x"], ["pytest", "-q", "/etc/passwd"], ["pytest", "-q", "../fora.py"], ["pytest", "-q"], ["pytest", "-q", "a b"], ["pytest", "--co", "x.py"], "pytest -q x"):
        conferir(f"comando recusado: {ruim!r}", not comando_valido(ruim))
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        def descritor(**extra):
            d = {"nome": "demo", "raiz": str(base), **extra}
            arq = base / "d.json"; arq.write_text(json.dumps(d), encoding="utf-8"); return arq
        for nome, extra in (("raiz relativa", {"raiz": "relativa"}), ("ambiente fora da lista", {"ambiente": {"LD_PRELOAD": "x"}}),
                            ("spec com ..", {"spec": "../x"}), ("limite absurdo", {"limite_s": 99999}), ("saida relativa", {"saida": "rel"})):
            try:
                carregar(descritor(**extra)); conferir(f"descritor inválido recusado: {nome}", False)
            except DescritorInvalido:
                conferir(f"descritor inválido recusado: {nome}", True)
        d = carregar(descritor(ambiente={"PYTHONPATH": "src"}))
        conferir("padrões do descritor", d["spec"] == "spec" and d["escopos"] == ["."] and d["limite_s"] == 300)
        conferir("PYTHONPATH relativo vira caminho dentro da raiz", _ambiente(d)["PYTHONPATH"] == str(base / "src"))
    return 1 if falhou else 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        r = executar(Path(argv[0]))
    except DescritorInvalido as exc:
        print(f"descritor inválido: {exc}", file=sys.stderr)
        return 2
    print((Path(r["artefatos"].get("evidencia", "")).parent / "relatorio.md").read_text(encoding="utf-8") if r["artefatos"].get("evidencia") else json.dumps(r, ensure_ascii=False))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
