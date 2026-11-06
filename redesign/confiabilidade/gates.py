#!/usr/bin/env python3
"""Seis gates de confiabilidade (P4) como casos executáveis sobre redesign/mvp_autoaprimoramento/mvp.py.

rodar() -> list[dict]; cada item: gate, resultado ("pass"|"fail"), evidencia, limiar.
O limiar ainda não está definido (D10): o gate só registra pass ou fail, sem métrica.
Escrita só em diretórios temporários. mvp.py não é alterado.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

LIMIAR = "não definido (D10)"
COMMIT_FIXO = "b" * 40
DIFF = "--- a/escopo/a.txt\n+++ b/escopo/a.txt\n@@\n-x\n+y\n"

_MVP_DIR = Path(__file__).resolve().parents[1] / "mvp_autoaprimoramento"
if str(_MVP_DIR) not in sys.path:
    sys.path.insert(0, str(_MVP_DIR))
sys.dont_write_bytecode = True  # não gravar __pycache__ dentro da pasta do mvp
import mvp  # noqa: E402


def _recusa(fn, *args) -> bool:
    """True se a chamada levantou ValueError (recusa explícita do mvp)."""
    try:
        fn(*args)
    except ValueError:
        return True
    return False


def _fixture(tmp: Path):
    """Árvore temporária com um arquivo de escopo, para não depender do estado do repo."""
    raiz = tmp / "raiz"
    (raiz / "escopo").mkdir(parents=True)
    (raiz / "escopo" / "a.txt").write_text("conteudo fixo\n", encoding="utf-8")
    return raiz


def _pedido_evidencias(tmp: Path):
    raiz = _fixture(tmp)
    pedido = mvp.criar_pedido("ajustar escopo fixo", ["escopo/a.txt"])
    evid = mvp.coletar_evidencias(pedido, raiz)
    return pedido, evid, raiz


def _proposta(tmp: Path, commit: str = COMMIT_FIXO) -> dict:
    pedido, evid, _ = _pedido_evidencias(tmp)
    return mvp.criar_proposta(pedido, evid, DIFF, commit)


def _gate(nome: str, fn) -> dict:
    try:
        ok, evidencia = fn()
    except Exception as exc:  # exceção vira fail com evidência, não some
        ok, evidencia = False, f"exceção {type(exc).__name__}: {exc}"
    return {"gate": nome, "resultado": "pass" if ok else "fail", "evidencia": evidencia, "limiar": LIMIAR}


def _g_regras_autoridade():
    with tempfile.TemporaryDirectory() as t:
        pr = _proposta(Path(t))
        dig = pr["digest"]
        casos = {
            "sem humano": ("aceita", "", dig),
            "humano = modelo": ("aceita", "modelo", dig),
            "humano = Seth": ("aceita", "Seth", dig),
            "digest errado": ("aceita", "Humano", "0" * 64),
        }
        for nome, (d, h, g) in casos.items():
            if not _recusa(mvp.registrar_decisao, pr, d, h, g):
                return False, f"aceitou indevidamente: {nome}"
        ok = mvp.registrar_decisao(pr, "aceita", "Humano", dig)
        if ok["aplicado"] is not False or ok["digest"] != dig:
            return False, "decisão válida não saiu como esperado (aplicado deve ser False)"
        return True, f"recusou {len(casos)}/{len(casos)} casos inválidos; decisão válida com aplicado=False"


def _g_escopo_ferramentas():
    recusados_ok = all(_recusa(mvp.criar_pedido, "x", [rel]) for rel in
                       ["../x", "/etc/passwd", "a/../../x"])
    if not recusados_ok:
        return False, "pedido com caminho fora do escopo não foi recusado"
    try:
        mvp.criar_pedido("x", ["escopo/a.txt"])
    except ValueError as exc:
        return False, f"caminho dentro do escopo recusado: {exc}"
    return True, "recusou ../x, /etc/passwd e a/../../x; aceitou escopo/a.txt"


def _g_qualidade():
    with tempfile.TemporaryDirectory() as t:
        pedido, evid, _ = _pedido_evidencias(Path(t))
        sem_diff = _recusa(mvp.criar_proposta, pedido, evid, "", COMMIT_FIXO)
        diff_branco = _recusa(mvp.criar_proposta, pedido, evid, "   \n", COMMIT_FIXO)
        sem_evid = _recusa(mvp.criar_proposta, pedido, [], DIFF, COMMIT_FIXO)
        if not (sem_diff and diff_branco and sem_evid):
            return False, f"recusas: sem_diff={sem_diff} diff_branco={diff_branco} sem_evidencia={sem_evid}"
        valida = mvp.criar_proposta(pedido, evid, DIFF, COMMIT_FIXO)
        if not valida.get("digest"):
            return False, "proposta com diff e evidência não gerou digest"
    return True, "recusou diff vazio, diff em branco e proposta sem evidência; aceitou a válida"


def _g_robustez_recuperacao():
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        pr = _proposta(t)
        pasta = t / "propostas"
        p1 = mvp.salvar(pr, pasta)
        b1 = p1.read_bytes()
        p2 = mvp.salvar(pr, pasta)
        b2 = p2.read_bytes()
        if p1 != p2:
            return False, f"caminhos diferentes: {p1.name} x {p2.name}"
        if b1 != b2:
            return False, "segunda gravação gerou bytes diferentes"
        arquivos = sorted(x.name for x in pasta.iterdir())
        if len(arquivos) != 1:
            return False, f"esperado 1 arquivo na pasta, achei {arquivos}"
        # recuperação: arquivo truncado é regravado com o conteúdo correto
        p1.write_bytes(b1[: len(b1) // 2])
        mvp.salvar(pr, pasta)
        if p1.read_bytes() != b1:
            return False, "arquivo truncado não foi restaurado pela nova gravação"
        carregado = json.loads(p1.read_text(encoding="utf-8"))
        corpo = {k: v for k, v in carregado.items() if k != "digest"}
        if mvp._digest(corpo) != carregado["digest"]:
            return False, "digest recomputado do arquivo não confere"
    return True, f"2 gravações -> 1 arquivo, bytes idênticos; truncado restaurado; digest confere ({p1.name})"


def _g_rastreabilidade():
    commit = mvp.head_git(mvp.RAIZ)
    with tempfile.TemporaryDirectory() as t:
        pr = _proposta(Path(t), commit)
    if not isinstance(pr.get("pedido"), dict) or not pr["pedido"].get("objetivo"):
        return False, "proposta sem pedido (objetivo) rastreável"
    evid = pr.get("evidencias") or []
    if not evid:
        return False, "proposta sem evidências"
    sem_sha = [e.get("caminho") for e in evid if not re.fullmatch(r"[0-9a-f]{64}", str(e.get("sha256")))]
    if sem_sha:
        return False, f"evidências sem sha256 válido: {sem_sha}"
    if not re.fullmatch(r"[0-9a-f]{40}", str(pr.get("commit_base"))):
        return False, f"commit_base não é SHA-1 de 40 hex: {pr.get('commit_base')!r}"
    return True, f"pedido.objetivo presente; {len(evid)} evidência(s) com sha256; commit_base={commit[:12]}"


_SCRIPT_REPETICAO = """
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, {mvp_dir!r})
from pathlib import Path
import mvp
p = mvp.criar_pedido("ajustar escopo fixo", ["escopo/a.txt"])
e = mvp.coletar_evidencias(p, Path({raiz!r}))
pr = mvp.criar_proposta(p, e, {diff!r}, {commit!r})
print(pr["digest"])
"""


def _g_repeticao():
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        pedido, evid, raiz = _pedido_evidencias(t)
        digests = [
            mvp.criar_proposta(pedido, evid, DIFF, COMMIT_FIXO)["digest"],
            mvp.criar_proposta(pedido, evid, DIFF, COMMIT_FIXO)["digest"],
        ]
        script = _SCRIPT_REPETICAO.format(mvp_dir=str(_MVP_DIR), raiz=str(raiz), diff=DIFF, commit=COMMIT_FIXO)
        for _ in range(2):
            saida = subprocess.run([sys.executable, "-I", "-c", script], capture_output=True, text=True,
                                   check=True, timeout=60)
            digests.append(saida.stdout.strip())
    if len(set(digests)) != 1:
        return False, f"digests divergentes: {[d[:12] for d in digests]}"
    return True, f"4 execuções (2 no processo, 2 em subprocessos) -> mesmo digest {digests[0][:16]}"


def rodar() -> list[dict]:
    return [
        _gate("regras_autoridade", _g_regras_autoridade),
        _gate("escopo_ferramentas", _g_escopo_ferramentas),
        _gate("qualidade", _g_qualidade),
        _gate("robustez_recuperacao", _g_robustez_recuperacao),
        _gate("rastreabilidade", _g_rastreabilidade),
        _gate("repeticao", _g_repeticao),
    ]


if __name__ == "__main__":
    print(json.dumps(rodar(), ensure_ascii=False, indent=2))
