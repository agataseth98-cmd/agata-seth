#!/usr/bin/env python3
"""SDD no painel: estado dos componentes ancorados e execução local de âncora e critérios.

Só executa o que está na lista fechada: conferir a âncora (leitura) e rodar os critérios de aceite
declarados em `spec/acceptance.json` (comandos `pytest -q redesign/...`, validados antes). Nada aqui
escreve no repositório, abre PR, assina ou mescla: ações externas continuam fora do painel.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(os.environ.get("AGATA_PAINEL_CACHE", Path.home() / ".cache" / "agata" / "painel" / "sdd"))
ACOES = ("ancora", "criterios")
NOME = re.compile(r"[a-z][a-z0-9_]{0,40}")
TIMEOUT_S = 300


def _anchor():
    spec = importlib.util.spec_from_file_location("sdd_anchor", ROOT / "redesign" / "sdd_flow" / "anchor.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _spec(raiz: Path, nome: str) -> Path | None:
    base = raiz / "redesign" / nome
    return next((p for p in (base / "spec" / "spec.md", base / "SPEC.md") if p.exists()), None)


def componentes(raiz: Path = ROOT) -> list[str]:
    base = raiz / "redesign"
    if not base.is_dir():
        return []
    return sorted(d.name for d in base.iterdir() if d.is_dir() and NOME.fullmatch(d.name) and _spec(raiz, d.name))


def _criterios(spec: Path) -> list[str]:
    return [l[6:].strip() for l in spec.read_text(encoding="utf-8").splitlines() if l.startswith(("- [ ] ", "- [x] "))]


def _manifesto(raiz: Path, nome: str) -> Path:
    return raiz / "redesign" / nome / "spec" / "acceptance.json"


def comando_valido(comando) -> bool:
    """Só `pytest -q <alvo>` com alvo dentro de redesign/ e sem sair dele."""
    if not (isinstance(comando, list) and len(comando) >= 3 and all(isinstance(c, str) for c in comando)):
        return False
    if comando[0] != "pytest" or comando[1] != "-q":
        return False
    return all(c.startswith("redesign/") and ".." not in c and not c.startswith("/") for c in comando[2:])


def _ultima(nome: str) -> dict | None:
    try:
        return json.loads((CACHE / nome / "ultima.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def estado(raiz: Path = ROOT) -> dict:
    anchor = _anchor()
    itens = []
    for nome in componentes(raiz):
        spec = _spec(raiz, nome)
        lacunas = anchor.check_component(raiz, f"redesign/{nome}")
        itens.append({"componente": nome, "spec": spec.relative_to(raiz).as_posix(), "criterios": len(_criterios(spec)),
                      "manifesto": _manifesto(raiz, nome).exists(), "ancora": "ok" if not lacunas else "falha",
                      "lacunas": lacunas[:5], "ultima": _ultima(nome)})
    return {"schema_version": 1, "acoes": list(ACOES), "items": itens}


def _rodar(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT_S)
        return r.returncode, (r.stdout + r.stderr)[-600:]
    except subprocess.TimeoutExpired:
        return 124, f"tempo esgotado ({TIMEOUT_S} s)"
    except OSError as exc:
        return 127, str(exc)[:200]


def executar(acao: str, nome: str, raiz: Path = ROOT) -> dict:
    permitidos = {c: c for c in componentes(raiz)}
    if acao not in ACOES or not isinstance(nome, str) or nome not in permitidos:
        raise ValueError("ação ou componente fora da lista")
    acao, nome = ACOES[ACOES.index(acao)], permitidos[nome]  # só valores da lista fechada seguem adiante
    passos = []
    anchor = _anchor()
    lacunas = anchor.check_component(raiz, f"redesign/{nome}")
    passos.append({"passo": "âncora", "ok": not lacunas, "detalhe": "; ".join(lacunas[:3]) or "todo código tem dono na spec"})
    criterios = []
    if acao == "criterios":
        manifesto = _manifesto(raiz, nome)
        if not manifesto.exists():
            passos.append({"passo": "critérios", "ok": False, "detalhe": "sem spec/acceptance.json: não medido"})
        else:
            itens = json.loads(manifesto.read_text(encoding="utf-8"))
            invalidos = [i.get("criterion", "?") for i in itens if not comando_valido(i.get("command"))]
            if invalidos:
                passos.append({"passo": "critérios", "ok": False, "detalhe": "comando fora do padrão pytest -q redesign/: " + "; ".join(invalidos[:2])})
            elif shutil.which("pytest") is None and not os.environ.get("AGATA_PYTEST"):
                passos.append({"passo": "critérios", "ok": False, "detalhe": "pytest não encontrado no PATH do painel: não medido"})
            else:
                for item in itens:
                    comando = list(item["command"])
                    if os.environ.get("AGATA_PYTEST"):
                        comando[0] = os.environ["AGATA_PYTEST"]
                    rc, saida = _rodar(comando, raiz)
                    criterios.append({"criterio": item["criterion"], "status": "pass" if rc == 0 else "fail"})
                    if rc != 0:
                        passos.append({"passo": "critério", "ok": False, "detalhe": f"{item['criterion']}: {saida.strip().splitlines()[-1] if saida.strip() else rc}"})
                passos.append({"passo": "critérios", "ok": all(c["status"] == "pass" for c in criterios) and bool(criterios),
                               "detalhe": f"{sum(c['status'] == 'pass' for c in criterios)}/{len(criterios)} passaram"})
    ok = all(p["ok"] for p in passos)
    resultado = {"acao": acao, "componente": nome, "ok": ok, "passos": passos, "criterios": criterios}
    try:
        (CACHE / nome).mkdir(parents=True, exist_ok=True, mode=0o700)
        (CACHE / nome / "ultima.json").write_text(json.dumps(resultado, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return resultado


def _selftest() -> int:
    falhou = 0
    def conferir(nome, cond):
        nonlocal falhou
        print(("PASS " if cond else "FALHA ") + nome); falhou += 0 if cond else 1
    conferir("comando válido: pytest -q dentro de redesign/", comando_valido(["pytest", "-q", "redesign/x/tests/t.py::a"]))
    for ruim in (["bash", "-c", "x"], ["pytest", "-q", "/etc/passwd"], ["pytest", "-q", "redesign/../x"], ["pytest"], "pytest -q redesign/x", ["pytest", "-q", "scripts/x.py"]):
        conferir(f"comando recusado: {ruim!r}", not comando_valido(ruim))
    with tempfile.TemporaryDirectory() as t:
        r = Path(t)
        try:
            executar("ancora", "inexistente", r)
            conferir("componente fora da lista levanta erro", False)
        except ValueError:
            conferir("componente fora da lista levanta erro", True)
    return 1 if falhou else 0


if __name__ == "__main__":
    raise SystemExit(_selftest() if "--selftest" in sys.argv else print(json.dumps(estado(), ensure_ascii=False, indent=2)) or 0)
