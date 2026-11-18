#!/usr/bin/env python3
"""skills_ledger.py — desfechos das skills (L8, 18/11/2026): só solução comprovada é recomendada.

Decisão do Humano (18/11/2026, decision.md da pasta l8-agentes-skills): uma skill recomenda solução só com
taxa de acerto acima de 51% e n >= 10 usos CONFERIDOS. Abaixo disso a solução aparece como "não comprovada"
e não some.

  - arquivo: ~/.local/share/agata/skills-ledger/<skill>.jsonl (pasta 0700, arquivo 0600), fora do repositório;
  - só acréscimo; trava flock no arquivo .lock da pasta; nada é apagado nem reescrito;
  - o agente registra o desfecho (pendente); o coordenador confere (conta); sem conferência, não conta;
  - guarda só slugs, ids e marcas de tempo: sem texto livre, por isso não passa pelo sanitizador;
  - linha inválida: registrar, conferir e recalcular recusam e avisam; recalcular não pula linha.

  skills_ledger.py registrar --skill S --erro E --solucao X --resultado acerto|falha --agente A --tarefa T
  skills_ledger.py conferir --ref ID --por COORD
  skills_ledger.py recalcular [--skill S]

Saída: registrar e conferir devolvem JSON; recalcular, uma tabela e o total pendente. Código 2 em recusa
ou linha inválida; 0 no resto (inclusive com solução "não comprovada").
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / ".agents" / "skills"  # pasta das skills; os testes trocam por uma temporária
TZ = ZoneInfo("America/Sao_Paulo")
SLUG = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")
ID = re.compile(r"[0-9a-f]{16}")
RESULTADOS = ("acerto", "falha")
LIMIAR_PCT = 51  # D1: acertos*100 > 51*usos
MIN_USOS = 10    # D1: n >= 10 usos conferidos
CHAVES_DESFECHO = frozenset({"tipo", "id", "skill", "erro", "solucao", "resultado", "agente", "tarefa", "ts"})
CHAVES_CONFERENCIA = frozenset({"tipo", "ref", "por", "ts"})
CAMPOS_SLUG = ("skill", "erro", "solucao", "agente", "tarefa")


class LedgerRecusado(ValueError):
    """Operação recusada: slug inválido, skill sem pasta, duplicata, id inexistente ou já conferido."""


class LedgerInvalido(ValueError):
    """Há linha inválida num ledger; nada é gravado nem calculado sobre ele."""

    def __init__(self, erros: list[str]):
        self.erros = erros
        super().__init__(f"{len(erros)} linha(s) inválida(s)")


def _pasta() -> Path:
    return Path(os.path.expanduser("~/.local/share/agata/skills-ledger"))


def _agora() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def _id_de(tarefa: str, skill: str, solucao: str, agente: str) -> str:
    return hashlib.sha256(json.dumps([tarefa, skill, solucao, agente]).encode("utf-8")).hexdigest()[:16]


def _slug(valor, campo: str) -> str:
    if not isinstance(valor, str) or not SLUG.fullmatch(valor):
        raise LedgerRecusado(f"{campo} inválido: use slug (minúsculas, números, '.', '_', '-'; até 64 caracteres)")
    return valor


def _status(acertos: int, usos: int) -> str:
    return "comprovada" if usos >= MIN_USOS and acertos * 100 > LIMIAR_PCT * usos else "não comprovada"


def _motivo(reg, skill: str, desfechos: dict, conferidos: set) -> str | None:
    """Motivo da linha ser inválida, ou None. Confere esquema, slugs, id, ordem e duplicidade."""
    if not isinstance(reg, dict):
        return "não é objeto JSON"
    tipo = reg.get("tipo")
    if tipo == "desfecho":
        if set(reg) != CHAVES_DESFECHO:
            return "campos do desfecho não batem com o esquema"
        for campo in CAMPOS_SLUG:
            if not isinstance(reg[campo], str) or not SLUG.fullmatch(reg[campo]):
                return f"{campo} não é slug"
        if reg["skill"] != skill:
            return "skill não bate com o nome do arquivo"
        if reg["resultado"] not in RESULTADOS:
            return "resultado fora de acerto|falha"
        if not isinstance(reg["id"], str) or not ID.fullmatch(reg["id"]):
            return "id com formato inválido"
        if reg["id"] != _id_de(reg["tarefa"], reg["skill"], reg["solucao"], reg["agente"]):
            return "id não bate com (tarefa, skill, solução, agente)"
        if reg["id"] in desfechos:
            return "id duplicado"
        if not isinstance(reg["ts"], str):
            return "ts inválido"
        return None
    if tipo == "conferencia":
        if set(reg) != CHAVES_CONFERENCIA:
            return "campos da conferência não batem com o esquema"
        if not isinstance(reg["ref"], str) or reg["ref"] not in desfechos:
            return "conferência de id inexistente antes dela neste ledger"
        if reg["ref"] in conferidos:
            return "id já conferido"
        if not isinstance(reg["por"], str) or not SLUG.fullmatch(reg["por"]):
            return "por não é slug"
        if not isinstance(reg["ts"], str):
            return "ts inválido"
        return None
    return f"tipo desconhecido: {tipo!r}"


def _ler(arq: Path) -> tuple[list[dict], list[str]]:
    """Devolve (linhas válidas, erros) de um ledger. Linha inválida vira erro; nunca some em silêncio."""
    if not arq.exists():
        return [], []
    validas: list[dict] = []
    erros: list[str] = []
    desfechos: dict[str, dict] = {}
    conferidos: set[str] = set()
    for n, bruto in enumerate(arq.read_bytes().split(b"\n"), 1):
        if not bruto.strip():
            continue
        rotulo = f"{arq.name} linha {n}"
        try:
            reg = json.loads(bruto)
        except ValueError:
            erros.append(f"{rotulo}: não é JSON")
            continue
        motivo = _motivo(reg, arq.stem, desfechos, conferidos)
        if motivo:
            erros.append(f"{rotulo}: {motivo}")
            continue
        if reg["tipo"] == "desfecho":
            desfechos[reg["id"]] = reg
        else:
            conferidos.add(reg["ref"])
        validas.append(reg)
    return validas, erros


def _acrescentar(arq: Path, reg: dict) -> None:
    linha = json.dumps(reg, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    fd = os.open(arq, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        while linha:
            linha = linha[os.write(fd, linha):]
        os.fsync(fd)
    finally:
        os.close(fd)
    dfd = os.open(arq.parent, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


@contextlib.contextmanager
def _travado():
    """Trava exclusiva da pasta do ledger (flock no .lock). Cria a pasta 0700 se faltar."""
    pasta = _pasta()
    pasta.mkdir(parents=True, exist_ok=True)
    os.chmod(pasta, 0o700)
    fd = os.open(pasta / ".lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield pasta
    finally:
        os.close(fd)


def registrar(skill: str, erro: str, solucao: str, resultado: str, agente: str, tarefa: str) -> str:
    """Grava um desfecho pendente e devolve o id (16 hex, derivado de tarefa, skill, solução e agente)."""
    for campo, valor in (("--skill", skill), ("--erro", erro), ("--solucao", solucao),
                         ("--agente", agente), ("--tarefa", tarefa)):
        _slug(valor, campo)
    if not (SKILLS / skill).is_dir():
        raise LedgerRecusado(f"skill sem pasta em .agents/skills/{skill}/")
    if resultado not in RESULTADOS:
        raise LedgerRecusado("--resultado deve ser acerto ou falha")
    id_ = _id_de(tarefa, skill, solucao, agente)
    with _travado() as pasta:
        arq = pasta / f"{skill}.jsonl"
        validas, erros = _ler(arq)
        if erros:
            raise LedgerInvalido(erros)
        if any(r["tipo"] == "desfecho" and r["id"] == id_ for r in validas):
            raise LedgerRecusado(f"duplicata: (tarefa, skill, solução, agente) já registrada, id {id_}")
        _acrescentar(arq, {"tipo": "desfecho", "id": id_, "skill": skill, "erro": erro, "solucao": solucao,
                           "resultado": resultado, "agente": agente, "tarefa": tarefa, "ts": _agora()})
    return id_


def conferir(ref: str, por: str) -> dict:
    """Acrescenta a conferência de um desfecho. Recusa id inexistente e id já conferido."""
    _slug(por, "--por")
    if not isinstance(ref, str) or not ID.fullmatch(ref):
        raise LedgerRecusado("--ref deve ser o id de 16 caracteres hexadecimais devolvido por registrar")
    with _travado() as pasta:
        for arq in sorted(pasta.glob("*.jsonl")):
            validas, erros = _ler(arq)
            if erros:
                raise LedgerInvalido(erros)
            achados = [r for r in validas if r["tipo"] == "desfecho" and r["id"] == ref]
            if not achados:
                continue
            if any(r["tipo"] == "conferencia" and r["ref"] == ref for r in validas):
                raise LedgerRecusado(f"id {ref} já conferido; cada desfecho é conferido uma vez")
            _acrescentar(arq, {"tipo": "conferencia", "ref": ref, "por": por, "ts": _agora()})
            return {"ok": True, "ref": ref, "skill": achados[0]["skill"], "por": por}
    raise LedgerRecusado(f"id inexistente no ledger: {ref}")


def recalcular(skill: str | None = None) -> tuple[list[dict], int]:
    """Devolve (linhas da tabela, pendentes). Solução sem conferência entra com usos 0 e 'não comprovada'."""
    if skill is not None:
        _slug(skill, "--skill")
    with _travado() as pasta:
        arquivos = [pasta / f"{skill}.jsonl"] if skill else sorted(pasta.glob("*.jsonl"))
        lidos, erros = [], []
        for arq in arquivos:
            validas, errs = _ler(arq)
            lidos.append(validas)
            erros += errs
    if erros:
        raise LedgerInvalido(erros)
    contas: dict[tuple[str, str, str], dict] = {}
    pendentes = 0
    for validas in lidos:
        conferidos = {r["ref"] for r in validas if r["tipo"] == "conferencia"}
        for r in validas:
            if r["tipo"] != "desfecho":
                continue
            conta = contas.setdefault((r["skill"], r["erro"], r["solucao"]), {"usos": 0, "acertos": 0})
            if r["id"] in conferidos:
                conta["usos"] += 1
                conta["acertos"] += int(r["resultado"] == "acerto")
            else:
                pendentes += 1
    rows = []
    for (s, e, x), conta in sorted(contas.items()):
        usos, acertos = conta["usos"], conta["acertos"]
        rows.append({"skill": s, "erro": e, "solucao": x, "usos": usos, "acertos": acertos,
                     "taxa": (100 * acertos / usos) if usos else None, "status": _status(acertos, usos)})
    return rows, pendentes


def formatar(rows: list[dict], pendentes: int) -> str:
    if not rows:
        corpo = ["ledger sem desfechos registrados"]
    else:
        corpo = ["skill | erro | solução | usos | acertos | taxa | status"]
        for r in rows:
            taxa = "-" if r["taxa"] is None else f"{r['taxa']:.1f}%"
            corpo.append(f"{r['skill']} | {r['erro']} | {r['solucao']} | {r['usos']} | {r['acertos']} | "
                         f"{taxa} | {r['status']}")
    corpo.append(f"pendentes sem conferência: {pendentes}")
    return "\n".join(corpo)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Desfechos das skills: registrar, conferir, recalcular (L8)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("registrar", help="grava desfecho pendente e devolve o id")
    for flag in ("--skill", "--erro", "--solucao", "--agente", "--tarefa"):
        r.add_argument(flag, required=True)
    r.add_argument("--resultado", required=True, choices=RESULTADOS)
    c = sub.add_parser("conferir", help="confere um desfecho (conta na taxa)")
    c.add_argument("--ref", required=True)
    c.add_argument("--por", required=True)
    k = sub.add_parser("recalcular", help="tabela de taxa e status por solução")
    k.add_argument("--skill", default=None)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "registrar":
            id_ = registrar(a.skill, a.erro, a.solucao, a.resultado, a.agente, a.tarefa)
            print(json.dumps({"ok": True, "id": id_, "pendente": True}, ensure_ascii=False))
        elif a.cmd == "conferir":
            print(json.dumps(conferir(a.ref, a.por), ensure_ascii=False))
        else:
            rows, pendentes = recalcular(a.skill)
            print(formatar(rows, pendentes))
        return 0
    except LedgerInvalido as e:
        print("recusado: ledger com linha inválida; corrija antes de gravar ou recalcular:", file=sys.stderr)
        for m in e.erros:
            print(f"  {m}", file=sys.stderr)
        return 2
    except LedgerRecusado as e:
        print(f"recusado: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
