#!/usr/bin/env python3
"""Gate de sincronia das specs SDD (P2, proposta spec-primeiro-11-11).

Para cada redesign/*/spec:
1. Sincronia: os critérios do spec.md (linhas "- [ ] " e "- [x] ") e os
   "criterion" do acceptance.json têm de ser o mesmo conjunto, texto exato.
   Divergência listada em EXCECOES vira AVISO; qualquer outra é FALHA.
2. Drift: se criterion-drift.md for um snapshot commitado, não pode ser mais
   antigo que o spec.md. Data = último commit que tocou o arquivo; alteração
   não commitada conta como agora. Arquivo que nunca foi commitado (gerado
   por ciclo) fica fora deste item. Clone raso falha: sem histórico não há datas.

O gate roda antes dos ciclos SDD no CI, porque o ciclo regenera
criterion-drift.md dentro da pasta da spec e esconderia um drift velho.

Uso: python3 -I scripts/gate_spec_sync.py [--selftest] [--raiz CAMINHO]
Saída: uma linha por achado; código 1 se houver FALHA.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

AGORA = float("inf")

# Dívida conhecida: critérios do acceptance.json que o spec.md ainda não tem.
# A correção mexe em spec.md, que exige proposta própria (processo-lote, regra 1).
# Quando ela entrar, a entrada sai daqui; enquanto isso, o gate avisa se sobrar.
EXCECOES: dict[str, frozenset[str]] = {
    "alexandria": frozenset({
        "execução auto consulta o léxico primeiro e registra as etapas",
        "modo auto acrescenta semântica e externa só quando faltar",
        "modo auto para no léxico quando a suficiência basta",
        "modo desconhecido é recusado",
        "modos explícitos fazem só o pedido",
    }),
}


def _git(raiz: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True).stdout.strip()


def criterios_spec(spec: Path) -> set[str]:
    return {linha[6:].strip() for linha in spec.read_text(encoding="utf-8").splitlines()
            if linha.startswith("- [ ] ") or linha.startswith("- [x] ")}


def criterios_acceptance(acc: Path) -> set[str]:
    return {item["criterion"] for item in json.loads(acc.read_text(encoding="utf-8"))}


def tempo(raiz: Path, rel: str) -> float | None:
    """Último commit que tocou o arquivo; AGORA se há alteração; None se nunca foi commitado."""
    estado = _git(raiz, "status", "--porcelain", "--", rel)
    if estado.startswith("??"):
        return None
    if estado:
        return AGORA
    data = _git(raiz, "log", "-1", "--format=%ct", "--", rel)
    return int(data) if data else None


def avaliar_componente(raiz: Path, comp: Path, excecoes: dict[str, frozenset[str]]) -> list[tuple[str, str]]:
    nome = comp.parent.name
    spec, acc, drift = comp / "spec.md", comp / "acceptance.json", comp / "criterion-drift.md"
    if not spec.exists() or not acc.exists():
        return [("FALHA", "falta spec.md ou acceptance.json")]
    try:
        cb, ca = criterios_spec(spec), criterios_acceptance(acc)
    except (ValueError, KeyError, TypeError) as exc:
        return [("FALHA", f"acceptance.json ilegível: {exc}")]
    achados: list[tuple[str, str]] = []
    excecao = excecoes.get(nome, frozenset())
    so_acc, so_spec = ca - cb, cb - ca
    falha_acc = sorted(so_acc - excecao)
    if falha_acc:
        achados.append(("FALHA", f"{len(falha_acc)} critério(s) no acceptance.json sem linha no spec.md (ex.: {falha_acc[0]})"))
    if so_spec:
        achados.append(("FALHA", f"{len(so_spec)} critério(s) no spec.md sem teste no acceptance.json (ex.: {sorted(so_spec)[0]})"))
    if so_acc & excecao:
        achados.append(("AVISO", f"dívida conhecida: {len(so_acc & excecao)} critério(s) do acceptance.json sem linha no spec.md"))
    if excecao - so_acc:
        achados.append(("AVISO", f"exceção obsoleta: {len(excecao - so_acc)} item(ns) já sincronizados; tirar de EXCECOES"))
    if drift.exists():
        t_drift = tempo(raiz, str(drift.relative_to(raiz)))
        if t_drift is None:
            pass  # gerado por ciclo e nunca commitado: não é snapshot, fica fora deste item
        elif _git(raiz, "rev-parse", "--is-shallow-repository") == "true":
            achados.append(("FALHA", "histórico raso: o CI precisa de fetch-depth: 0 para comparar datas"))
        else:
            t_spec = tempo(raiz, str(spec.relative_to(raiz)))
            if t_spec is None:
                t_spec = AGORA
            if t_drift < t_spec:
                achados.append(("FALHA", "criterion-drift.md mais antigo que spec.md: rode o ciclo SDD e commite o drift"))
    if not any(nivel == "FALHA" for nivel, _ in achados):
        achados.insert(0, ("OK", f"{len(cb)} critério(s) no spec.md"))
    return achados


def avaliar(raiz: Path, excecoes: dict[str, frozenset[str]] = EXCECOES) -> list[tuple[str, str, str]]:
    comps = sorted(raiz.glob("redesign/*/spec"))
    if not comps:
        return [("(nenhum)", "FALHA", "nenhuma redesign/*/spec encontrada")]
    if _git(raiz, "rev-parse", "--is-inside-work-tree") != "true":
        return [("(nenhum)", "FALHA", "sem repositório git: o gate precisa das datas de commit")]
    return [(c.parent.name, nivel, texto) for c in comps for nivel, texto in avaliar_componente(raiz, c, excecoes)]


def _selftest() -> int:
    testes: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp) / "repo"
        raiz.mkdir()
        subprocess.run(["git", "init", "-q", str(raiz)], check=True)

        def escreve(rel: str, texto: str) -> None:
            p = raiz / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(texto, encoding="utf-8")

        def commita(data: int, msg: str) -> None:
            env = {**os.environ, "GIT_AUTHOR_DATE": f"@{data} +0000", "GIT_COMMITTER_DATE": f"@{data} +0000"}
            subprocess.run(["git", "-C", str(raiz), "add", "-A"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(raiz), "-c", "user.name=teste", "-c", "user.email=teste@local",
                            "commit", "-q", "-m", msg], check=True, capture_output=True, env=env)

        def spec(criterios: list[str], extra: str = "") -> str:
            return "# Spec de teste\n\n## Critérios de aceite\n" + "".join(f"- [ ] {c}\n" for c in criterios) + extra

        def acc(criterios: list[str]) -> str:
            return json.dumps([{"criterion": c, "command": ["true"]} for c in criterios], ensure_ascii=False)

        a, b = "critério A", "critério B"
        for nome in ("ok", "sinc", "excecao", "velho", "novo", "sujo", "regerado", "gerado"):
            escreve(f"redesign/{nome}/spec/spec.md", spec([a, b]))
            escreve(f"redesign/{nome}/spec/acceptance.json", acc([a, b]))
        escreve("redesign/sinc/spec/acceptance.json", acc([a, b, "critério C"]))
        escreve("redesign/excecao/spec/acceptance.json", acc([a, b, "critério E"]))
        for nome in ("velho", "novo", "sujo", "regerado"):
            escreve(f"redesign/{nome}/spec/criterion-drift.md", "# drift\n")
        commita(1000, "base")
        for nome in ("velho", "regerado"):
            escreve(f"redesign/{nome}/spec/spec.md", spec([a, b], "Contrato revisado.\n"))
        commita(2000, "spec revisada")
        escreve("redesign/novo/spec/criterion-drift.md", "# drift atualizado\n")
        commita(3000, "drift novo")
        escreve("redesign/sujo/spec/spec.md", spec([a, b], "Contrato sem drift.\n"))
        escreve("redesign/regerado/spec/criterion-drift.md", "# drift regerado\n")
        escreve("redesign/gerado/spec/criterion-drift.md", "# gerado pelo ciclo\n")

        excecoes = {"excecao": frozenset({"critério E"}), "gerado": frozenset({"fantasma"})}
        linhas = avaliar(raiz, excecoes)

        def niveis(comp: str) -> set[str]:
            return {n for c, n, _ in linhas if c == comp}

        def textos(comp: str) -> str:
            return " | ".join(t for c, _, t in linhas if c == comp)

        testes += [
            ("sincronizado e drift ausente passa", niveis("ok") == {"OK"}),
            ("critério só no acceptance.json é FALHA", "FALHA" in niveis("sinc") and "OK" not in niveis("sinc")),
            ("exceção conhecida vira AVISO, não FALHA", "FALHA" not in niveis("excecao") and "AVISO" in niveis("excecao")),
            ("drift mais antigo que a spec é FALHA", "FALHA" in niveis("velho") and "mais antigo" in textos("velho")),
            ("drift commitado depois da spec passa", niveis("novo") == {"OK"}),
            ("spec alterada sem commit contra drift antigo é FALHA", "FALHA" in niveis("sujo")),
            ("drift regerado sem commit conta como agora", niveis("regerado") == {"OK"}),
            ("drift nunca commitado fica fora do item", "FALHA" not in niveis("gerado")),
            ("exceção que já não existe vira AVISO", "exceção obsoleta" in textos("gerado")),
            ("repositório sem spec é FALHA", avaliar(Path(tmp) / "vazio") == [("(nenhum)", "FALHA", "nenhuma redesign/*/spec encontrada")]),
        ]
        clone = Path(tmp) / "raso"
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{raiz}", str(clone)], check=True, capture_output=True)
        raso = [t for c, n, t in avaliar(clone, {}) if c == "novo" and n == "FALHA"]
        testes.append(("clone raso falha no drift commitado", any("raso" in t for t in raso)))
        semgit = Path(tmp) / "semgit"
        (semgit / "redesign" / "x" / "spec").mkdir(parents=True)
        (semgit / "redesign" / "x" / "spec" / "spec.md").write_text(spec([a]), encoding="utf-8")
        (semgit / "redesign" / "x" / "spec" / "acceptance.json").write_text(acc([a]), encoding="utf-8")
        testes.append(("fora de git é FALHA, não passa em branco", any(n == "FALHA" and "git" in t for _, n, t in avaliar(semgit, {}))))

    for nome, ok in testes:
        print(("OK    " if ok else "FALHA ") + "selftest: " + nome)
    falhas = sum(1 for _, ok in testes if not ok)
    print(f"SELFTEST GATE: {len(testes) - falhas}/{len(testes)} OK")
    return 1 if falhas else 0


def _raiz_padrao() -> Path:
    topo = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    return Path(topo) if topo else Path.cwd()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gate de sincronia das specs SDD")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--raiz", type=Path, default=None)
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()
    linhas = avaliar((args.raiz or _raiz_padrao()).resolve())
    for comp, nivel, texto in linhas:
        print(f"{nivel:5} {comp:18} {texto}")
    falhas = sum(1 for _, nivel, _ in linhas if nivel == "FALHA")
    avisos = sum(1 for _, nivel, _ in linhas if nivel == "AVISO")
    componentes = len({c for c, _, _ in linhas if c != "(nenhum)"})
    print(f"GATE SPEC: {componentes} componente(s), {avisos} aviso(s), {falhas} falha(s)")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
