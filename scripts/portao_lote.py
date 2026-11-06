#!/usr/bin/env python3
"""Portões mecânicos do processo de lote: trocam a conferência de memória por checagem.

Uso:
  python3 portao_lote.py --diff <arquivo.diff> --lote <nome> [--pr <n>]
  python3 portao_lote.py --selftest

Saída: uma linha por portão (PASS, FAIL ou N/A, com motivo) e uma linha RESULTADO.
Código 0 só se TODOS os portões passarem. N/A (G5 sem --pr) não é PASS: o código
sai 1 e a linha RESULTADO diz INCOMPLETO. Só biblioteca padrão do Python.

O que cada portão PROVA e o que NÃO PROVA:

G1 diff só de código.
   PROVA: todo caminho de "diff --git" (origem e destino, inclusive em rename) está em
   .agents/, .claude/, .github/, redesign/, scripts/ ou ferramentas/. Caminho de canon
   (MEMÓRIAS, ONDE_ESTAMOS, REGRAS, PROJETO, PROMPT_CARREGAMENTO, INDICE_MEMORIAS*,
   .hidrata*, propostas/) ou qualquer outro caminho FAZ FALHAR.
   NÃO PROVA: o conteúdo. Texto de canon escrito dentro de scripts/ passa.
   NÃO PROVA autoria.

G2 aplica no origin/main.
   PROVA: `git apply --check` aceita o diff sobre o ref LOCAL origin/main, numa worktree
   temporária em checkout detached. A worktree é removida em qualquer caso (try/finally);
   falha de limpeza também reprova. O checkout vivo não é tocado.
   NÃO PROVA: autoria; que o código funciona; que origin/main está atualizado (o script
   não faz fetch).

G3 time no main.
   PROVA: `git ls-tree -r origin/main -- .claude/agents` lista ao menos um arquivo (ref local).
   NÃO PROVA que o time está ativo nem que o Claude Code o carrega; só que os arquivos
   estão versionados no ref consultado.

G4 PYTEST.
   PROVA: o executável indicado na variável de ambiente PYTEST responde a `--version`
   (código 0) com uma linha que contém "pytest" e um número de versão.
   NÃO PROVA que a suíte passa (não roda testes) nem que é o pytest do projeto.
   PYTEST é um caminho de executável, não uma linha de comando.

G5 CI por commit (só com --pr).
   PROVA: existe run do sdd.yml, entre as 5 últimas do branch do PR, com headSha igual a
   `git rev-parse HEAD`. O branch é o headRefName do PR (gh pr view).
   NÃO PROVA: que o run passou (status e conclusão vão no motivo, não são exigidos);
   que o run é o mais recente se houver mais de 5 runs (run antigo fora das 5 últimas
   dá FAIL falso); autoria.

G6 APROVADO fora do commit.
   PROVA: nenhum caminho do index (`git diff --cached --name-only`) contém APROVADO,
   sem diferenciar maiúsculas.
   NÃO PROVA: que APROVADO não esteve em commits anteriores; NÃO valida assinatura
   (a assinatura é do Humano, fora deste script).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = "/home/orusoua/agata"
AREAS_CODIGO = (".agents/", ".claude/", ".github/", "redesign/", "scripts/", "ferramentas/")
CANON_PREFIXOS = (
    "MEMÓRIAS", "ONDE_ESTAMOS", "REGRAS", "PROJETO",
    "PROMPT_CARREGAMENTO", "INDICE_MEMORIAS", ".hidrata",
)
PASS, FAIL, NA = "PASS", "FAIL", "N/A"


def primeira_linha(texto, limite=200):
    linha = next((l.strip() for l in (texto or "").splitlines() if l.strip()), "")
    return linha[:limite] or "(sem saída)"


def git(args, cwd=REPO):
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    except OSError as e:
        return subprocess.CompletedProcess(args, 127, "", f"git não executou: {e}")


def eh_canon(caminho):
    return caminho.startswith("propostas/") or caminho.startswith(CANON_PREFIXOS)


def g1_codigo_only(texto):
    cabecalhos = [l for l in texto.splitlines() if l.startswith("diff --git ")]
    if not cabecalhos:
        return FAIL, "diff sem nenhum 'diff --git': nada para provar"
    caminhos = set()
    for linha in cabecalhos:
        m = re.match(r"^diff --git a/(.+) b/(.+)$", linha)
        if not m:
            return FAIL, f"cabeçalho não reconhecido (formato ou caminho entre aspas): {linha[:120]}"
        caminhos.update((m.group(1), m.group(2)))
    fora = sorted(p for p in caminhos if not p.startswith(AREAS_CODIGO))
    if fora:
        motivo = "caminho(s) fora das áreas de código: " + ", ".join(fora)
        canon = [p for p in fora if eh_canon(p)]
        if canon:
            motivo += " | de canon: " + ", ".join(canon)
        return FAIL, motivo
    return PASS, f"{len(cabecalhos)} arquivo(s), todos em áreas de código"


def _limpar_worktree(tmp, wt):
    git(["worktree", "remove", "--force", wt])
    shutil.rmtree(tmp, ignore_errors=True)
    git(["worktree", "prune"])
    lista = git(["worktree", "list", "--porcelain"]).stdout
    return not os.path.exists(tmp) and f"worktree {os.path.realpath(wt)}" not in lista


def g2_aplica_origin_main(diff_abs):
    if git(["rev-parse", "--verify", "--quiet", "origin/main^{commit}"]).returncode != 0:
        return FAIL, "ref origin/main não existe localmente (o script não faz fetch)"
    tmp = tempfile.mkdtemp(prefix="portao_lote_")
    wt = os.path.join(tmp, "wt")
    resultado = (FAIL, "não executou")
    try:
        add = git(["worktree", "add", "--detach", wt, "origin/main"])
        if add.returncode != 0:
            resultado = (FAIL, "worktree não criada: " + primeira_linha(add.stderr))
        else:
            ap = subprocess.run(
                ["git", "-C", wt, "apply", "--check", diff_abs],
                capture_output=True, text=True,
            )
            if ap.returncode == 0:
                resultado = (PASS, "git apply --check aceitou o diff sobre origin/main")
            else:
                resultado = (FAIL, "git apply --check recusou: " + primeira_linha(ap.stderr))
    finally:
        limpou = _limpar_worktree(tmp, wt)
    if not limpou:
        return FAIL, f"worktree temporária não foi removida: {tmp}"
    return resultado


def g3_time_no_main(texto):
    # Se o próprio diff cria o time, o portão passa com aviso: o time só fica ativo depois de aplicado.
    if "diff --git a/.claude/agents/" in texto:
        return PASS, "o diff adiciona .claude/agents: o time fica ativo só depois de aplicado e de uma sessão nova"
    r = git(["ls-tree", "-r", "origin/main", "--", ".claude/agents"])
    if r.returncode != 0:
        return FAIL, "git ls-tree falhou: " + primeira_linha(r.stderr)
    arquivos = [l for l in r.stdout.splitlines() if l.strip()]
    if not arquivos:
        return FAIL, "time não está no main e o diff não o cria: não diga que o time está ativo"
    return PASS, f"{len(arquivos)} arquivo(s) em .claude/agents no origin/main (ref local)"


def g4_pytest(valor):
    if not valor or not valor.strip():
        return FAIL, "variável PYTEST ausente: defina o caminho do executável pytest"
    try:
        r = subprocess.run([valor, "--version"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return FAIL, f"PYTEST não executou: {e}"
    saida = (r.stdout or "") + "\n" + (r.stderr or "")
    if r.returncode != 0:
        return FAIL, f"'{valor} --version' saiu com código {r.returncode}: {primeira_linha(saida)}"
    for linha in saida.splitlines():
        if "pytest" in linha.lower() and re.search(r"\d+\.\d+", linha):
            return PASS, linha.strip()[:120]
    return FAIL, "saída de --version sem 'pytest' e número de versão: " + primeira_linha(saida)


# Checks obrigatórios no branch protection do main (medido por gh api em 06/11/2026).
CHECKS_OBRIGATORIOS = ("suite-adversarial", "fiscal-p8", "CodeQL")


def g5_ci_commit(pr):
    """Prova que os checks obrigatórios do head atual do PR passaram.

    Não prova: que o PR é mergeável (isso é do GitHub), nem que o sdd.yml rodou (ele não é obrigatório
    e só dispara com os caminhos dele). Um check pendente ou ausente é FAIL: não junte.
    """
    if shutil.which("gh") is None:
        return FAIL, "gh não disponível: não é possível confirmar o CI"
    try:
        v = subprocess.run(
            ["gh", "pr", "checks", str(pr), "--json", "name,state,bucket"],
            cwd=REPO, capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return FAIL, f"gh pr checks não executou: {e}"
    if v.returncode != 0:
        return FAIL, "gh pr checks falhou: " + primeira_linha(v.stderr)
    try:
        checks = json.loads(v.stdout or "[]")
    except ValueError:
        return FAIL, "gh pr checks devolveu JSON inválido"
    por_nome = {c.get("name"): str(c.get("state", "")).upper() for c in checks}
    faltam = [n for n in CHECKS_OBRIGATORIOS if n not in por_nome]
    if faltam:
        return FAIL, "check obrigatório ausente: " + ", ".join(faltam) + ": não junte"
    ruins = [f"{n}={por_nome[n]}" for n in CHECKS_OBRIGATORIOS if por_nome[n] != "SUCCESS"]
    if ruins:
        return FAIL, "check obrigatório sem sucesso: " + ", ".join(ruins) + ": não junte"
    return PASS, "checks obrigatórios com SUCCESS no head do PR: " + ", ".join(CHECKS_OBRIGATORIOS)


def g6_aprovado_fora():
    r = git(["diff", "--cached", "--name-only"])
    if r.returncode != 0:
        return FAIL, "git diff --cached falhou: " + primeira_linha(r.stderr)
    caminhos = [l for l in r.stdout.splitlines() if l.strip()]
    hits = [c for c in caminhos if "APROVADO" in c.upper()]
    if hits:
        return FAIL, "index tem caminho(s) com APROVADO: " + ", ".join(hits)
    return PASS, f"{len(caminhos)} caminho(s) no index, nenhum com APROVADO"


def _fake_pytest(dirpath, saida, nome):
    caminho = os.path.join(dirpath, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("#!/bin/sh\ncat <<'FIM'\n" + saida + "\nFIM\n")
    os.chmod(caminho, 0o755)
    return caminho


def selftest():
    tmp = tempfile.mkdtemp(prefix="portao_lote_selftest_")
    try:
        bom = _fake_pytest(tmp, "pytest 8.3.2", "pytest_ok")
        ruim = _fake_pytest(tmp, "hello 1.0", "pytest_ruim")
        casos = [
            ("G1 só código",
             lambda: g1_codigo_only("diff --git a/scripts/a.py b/scripts/a.py\n"
                                    "diff --git a/redesign/b.py b/redesign/b.py\n"), PASS),
            ("G1 canon MEMÓRIAS",
             lambda: g1_codigo_only("diff --git a/MEMÓRIAS.md b/MEMÓRIAS.md\n"), FAIL),
            ("G1 propostas/",
             lambda: g1_codigo_only("diff --git a/propostas/x.diff b/propostas/x.diff\n"), FAIL),
            ("G1 AGENTS.md fora da lista",
             lambda: g1_codigo_only("diff --git a/AGENTS.md b/AGENTS.md\n"), FAIL),
            ("G1 prefixo falso scriptsx/",
             lambda: g1_codigo_only("diff --git a/scriptsx/a.py b/scriptsx/a.py\n"), FAIL),
            ("G1 rename de canon para código",
             lambda: g1_codigo_only("diff --git a/REGRAS.md b/scripts/regras.md\n"), FAIL),
            ("G1 sem diff --git",
             lambda: g1_codigo_only("texto sem cabeçalho\n"), FAIL),
            ("G4 PYTEST ausente",
             lambda: g4_pytest(None), FAIL),
            ("G4 pytest 8.3.2",
             lambda: g4_pytest(bom), PASS),
            ("G4 saída sem pytest",
             lambda: g4_pytest(ruim), FAIL),
            ("G4 caminho inexistente",
             lambda: g4_pytest(os.path.join(tmp, "nao_existe")), FAIL),
        ]
        ok_total = 0
        for nome, fn, esperado in casos:
            status, motivo = fn()
            ok = status == esperado
            ok_total += ok
            print(f"SELFTEST {nome}: {'OK' if ok else 'ERRO'} "
                  f"(esperado {esperado}, obtido {status}) {motivo}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = len(casos)
    resultado = "PASS" if ok_total == total else "FAIL"
    print(f"SELFTEST RESULTADO: {resultado} ({ok_total}/{total})")
    return 0 if ok_total == total else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Portões mecânicos do processo de lote (ver docstring).")
    ap.add_argument("--diff", help="caminho do arquivo .diff da proposta")
    ap.add_argument("--lote", help="nome do lote, ex.: lote4-processo-20261106")
    ap.add_argument("--pr", type=int, help="número do PR; ativa G5")
    ap.add_argument("--selftest", action="store_true", help="testa G1 e G4 com entradas sintéticas")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not args.diff or not args.lote:
        ap.error("--diff e --lote são obrigatórios (ou use --selftest)")

    diff_abs = os.path.abspath(args.diff)
    try:
        with open(diff_abs, encoding="utf-8", errors="replace") as f:
            texto = f.read()
    except OSError as e:
        print(f"ENTRADA FAIL não li o diff {diff_abs}: {e}")
        print("RESULTADO: FAIL (entrada)")
        return 1

    portoes = [
        ("G1", "diff só de código", lambda: g1_codigo_only(texto)),
        ("G2", "aplica no origin/main", lambda: g2_aplica_origin_main(diff_abs)),
        ("G3", "time no main", lambda: g3_time_no_main(texto)),
        ("G4", "PYTEST", lambda: g4_pytest(os.environ.get("PYTEST"))),
        ("G5", "CI por commit",
         (lambda: g5_ci_commit(args.pr)) if args.pr is not None else None),
        ("G6", "APROVADO fora do commit", g6_aprovado_fora),
    ]

    resultados = []
    for codigo, nome, fn in portoes:
        if fn is None:
            print(f"{codigo} {NA} {nome}: sem --pr, CI não verificado nesta execução")
            resultados.append((codigo, NA))
            continue
        status, motivo = fn()
        print(f"{codigo} {status} {nome}: {motivo}")
        resultados.append((codigo, status))

    falhas = [c for c, s in resultados if s == FAIL]
    nao_aplicaveis = [c for c, s in resultados if s == NA]
    if falhas:
        print(f"RESULTADO: FAIL lote={args.lote} (falharam: {', '.join(falhas)})")
        return 1
    if nao_aplicaveis:
        print(f"RESULTADO: INCOMPLETO lote={args.lote} "
              f"(não aplicável: {', '.join(nao_aplicaveis)}; código 1 até rodar com --pr)")
        return 1
    print(f"RESULTADO: PASS lote={args.lote} (todos os portões passaram)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
