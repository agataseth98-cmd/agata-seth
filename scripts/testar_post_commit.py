#!/usr/bin/env python3
"""Suite sintetica do .githooks/post-commit com worktrees. CANDIDATO, nao aplicado.

Repositorio descartavel + HOME descartavel + stubs no lugar dos geradores reais: nenhum vault,
Drive, servico ou arquivo do Agata e tocado. `core.hooksPath` e ABSOLUTO para o checkout principal,
como no Agata real, o que e o que faz o hook rodar com o ambiente de uma worktree.

Casos:
  A  commit no principal: o gerador roda 1 vez, rotulado com o HEAD do principal; bundle valido
  B  commit em worktree: derivados NAO rodam; bundle contem o commit da worktree
  C  o hook ANTIGO (HEAD do repo real) no caso B: reproduz o defeito (rotulo = commit da worktree,
     arquivos = os do principal)
  D  commits simultaneos (principal + worktree), varias rodadas: bundle sempre valido, sem sobra
Uso: python3 -I scripts/testar_post_commit.py [caminho-do-post-commit]
"""
import os
import shutil
import subprocess
import sys
import tempfile
import threading

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOVO = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, ".githooks", "post-commit")

BASE_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
BASE_ENV.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, LC_ALL="C.UTF-8")


def sh(cwd, *a, env=None, ok=True):
    p = subprocess.run(a, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env or BASE_ENV)
    if ok and p.returncode:
        raise RuntimeError(" ".join(a) + "\n" + p.stdout.decode("utf-8", "replace"))
    return p.stdout.decode("utf-8", "replace")


STUB_OBSIDIAN = r'''
import os, subprocess, sys
head = subprocess.run(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE, text=True).stdout.strip()
ramo = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], stdout=subprocess.PIPE, text=True).stdout.strip()
with open(os.environ["P8_LOG"], "a") as f:
    f.write(f"obsidian rotulo={os.environ.get('AGATA_CANON_SHA','')} head={head} ramo={ramo} cwd={os.path.basename(os.getcwd())}\n")
'''
STUB_BUSCA = r'''
import os
with open(os.environ["P8_LOG"], "a") as f:
    f.write("busca atualizar\n")
if os.environ.get("P8_MUTAR"):  # simula pull/edição concorrente durante a geração
    with open("a.txt", "a") as f:
        f.write("mudou durante a geracao\n")
'''


def montar(hook_fonte):
    td = tempfile.mkdtemp(prefix="pc-")
    home = os.path.join(td, "home")
    os.makedirs(home)
    env = dict(BASE_ENV, HOME=home, P8_LOG=os.path.join(td, "log.txt"), USER="teste")
    r = os.path.join(td, "principal")
    os.makedirs(r)
    sh(r, "git", "init", "-q", "-b", "main", env=env)
    sh(r, "git", "config", "user.email", "t@example.invalid", env=env)
    sh(r, "git", "config", "user.name", "t", env=env)
    os.makedirs(os.path.join(r, ".githooks"))
    os.makedirs(os.path.join(r, "scripts"))
    shutil.copy(hook_fonte, os.path.join(r, ".githooks", "post-commit"))
    os.chmod(os.path.join(r, ".githooks", "post-commit"), 0o755)
    with open(os.path.join(r, "scripts", "gerar_obsidian.py"), "w") as f:
        f.write(STUB_OBSIDIAN)
    with open(os.path.join(r, "scripts", "busca_semantica.py"), "w") as f:
        f.write(STUB_BUSCA)
    with open(os.path.join(r, "scripts", "gerar_indice_derivado.py"), "w") as f:
        f.write("import sys; sys.exit(1)\n")
    with open(os.path.join(r, "a.txt"), "w") as f:
        f.write("a\n")
    sh(r, "git", "add", "-A", env=env)
    sh(r, "git", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "base", env=env)
    sh(r, "git", "config", "core.hooksPath", os.path.join(r, ".githooks"), env=env)  # ABSOLUTO, como no Agata
    wt = os.path.join(td, "wt")
    sh(r, "git", "worktree", "add", "-q", "-b", "ramo-wt", wt, env=env)
    return td, r, wt, env


def commitar(cwd, env, nome):
    with open(os.path.join(cwd, nome), "w") as f:
        f.write(nome + "\n")
    sh(cwd, "git", "add", nome, env=env)
    return sh(cwd, "git", "commit", "-qm", nome, env=env)


def log(td):
    p = os.path.join(td, "log.txt")
    return open(p).read().splitlines() if os.path.exists(p) else []


def bundle_ok(r, env):
    b = os.path.join(env["HOME"], ".agata-backup-staging", "agata-canonico.bundle")
    return os.path.exists(b) and subprocess.run(["git", "bundle", "verify", b], cwd=r, env=env,
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0


def main():
    antigo = tempfile.NamedTemporaryFile("w", delete=False, suffix=".sh")
    # hook ANTES da correção, fixado no commit 9cc0a6c (o HEAD já tem o hook novo)
    antigo.write(sh(RAIZ, "git", "show", "9cc0a6c:.githooks/post-commit"))
    antigo.close()
    res = {}

    # A + B + C com o hook novo
    td, r, wt, env = montar(NOVO)
    try:
        commitar(r, env, "a1.txt")
        head_principal = sh(r, "git", "rev-parse", "HEAD", env=env).strip()
        l = log(td)
        res["A1 principal: gerador roda 1 vez"] = sum(x.startswith("obsidian") for x in l) == 1
        res["A2 principal: rotulo = HEAD = principal"] = any(f"rotulo={head_principal} head={head_principal} ramo=main cwd=principal" in x for x in l)
        res["A3 principal: bundle valido"] = bundle_ok(r, env)
        antes = len(l)
        commitar(wt, env, "w1.txt")
        head_wt = sh(wt, "git", "rev-parse", "HEAD", env=env).strip()
        res["B1 worktree: derivados NAO rodam"] = len(log(td)) == antes
        b = os.path.join(env["HOME"], ".agata-backup-staging", "agata-canonico.bundle")
        heads = sh(r, "git", "bundle", "list-heads", b, env=env)
        res["B2 worktree: bundle valido e contem o commit da worktree"] = bundle_ok(r, env) and head_wt in heads
    finally:
        shutil.rmtree(td, ignore_errors=True)

    # E checkout que muda durante a geração é detectado; sem mudança, sem aviso
    td, r, wt, env = montar(NOVO)
    try:
        cache = os.path.join(env["HOME"], ".cache", "agata")
        marcs = lambda: [f for f in (os.listdir(cache) if os.path.isdir(cache) else []) if f.startswith("derivados-possivelmente-misturados")]
        p0 = commitar(r, env, "e0.txt")
        res["E1 sem mudança durante a geração: sem marcador"] = not marcs()
        env2 = dict(env, P8_MUTAR="1")
        sh(r, "git", "checkout", "-q", "--", "a.txt", env=env)
        with open(os.path.join(r, "e1.txt"), "w") as f:
            f.write("e1\n")
        sh(r, "git", "add", "e1.txt", env=env2)
        c = subprocess.run(["git", "commit", "-qm", "e1"], cwd=r, env=env2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        res["E2 checkout mudou durante a geração: marcador e AVISO"] = bool(marcs()) and "mudou durante a geração" in c.stderr
        sh(r, "git", "checkout", "-q", "--", "a.txt", env=env)
        commitar(r, env, "e2.txt")
        res["E3 geração seguinte limpa: marcador some"] = not marcs()
        # E4 arquivo JÁ modificado (dirty->dirty) que muda de conteúdo durante a geração: o status continuaria " M"
        with open(os.path.join(r, "a.txt"), "a") as f:
            f.write("sujo antes\n")
        with open(os.path.join(r, "e4.txt"), "w") as f:
            f.write("e4\n")
        sh(r, "git", "add", "e4.txt", env=env2)
        c4 = subprocess.run(["git", "commit", "-qm", "e4"], cwd=r, env=env2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        res["E4 arquivo já modificado muda de conteúdo durante a geração -> detectado"] = bool(marcs()) and "mudou durante a geração" in c4.stderr
    finally:
        shutil.rmtree(td, ignore_errors=True)

    # C com o hook antigo (reproduz o defeito)
    td, r, wt, env = montar(antigo.name)
    try:
        commitar(wt, env, "w1.txt")
        head_wt = sh(wt, "git", "rev-parse", "HEAD", env=env).strip()
        l = [x for x in log(td) if x.startswith("obsidian")]
        res["C hook ANTIGO em worktree: rotulo=commit da worktree, arquivos=do principal (defeito reproduzido)"] = \
            len(l) == 1 and f"rotulo={head_wt}" in l[0] and "cwd=principal" in l[0] and "ramo=ramo-wt" in l[0]
    finally:
        shutil.rmtree(td, ignore_errors=True)

    # D simultaneidade
    td, r, wt, env = montar(NOVO)
    try:
        erros = []

        def tarefa(cwd, nome):
            try:
                commitar(cwd, env, nome)
            except Exception as e:  # noqa
                erros.append(str(e))

        for i in range(12):
            ts = [threading.Thread(target=tarefa, args=(r, f"p{i}.txt")), threading.Thread(target=tarefa, args=(wt, f"w{i}.txt"))]
            for t in ts:
                t.start()
            for t in ts:
                t.join()
        sobra = [f for f in os.listdir(os.path.join(env["HOME"], ".agata-backup-staging"))
                 if f not in ("agata-canonico.bundle", ".post-commit.lock", "PENDENTE-HD-DESCONECTADO")]
        res["D1 12 rodadas de commits simultaneos: todos terminam sem erro"] = not erros
        res["D2 bundle final valido"] = bundle_ok(r, env)
        res["D3 sem temporario sobrando no staging"] = not sobra
        if sobra:
            print("sobra:", sobra)
        if erros:
            print(erros[:2])
    finally:
        shutil.rmtree(td, ignore_errors=True)
        os.unlink(antigo.name)

    for k, v in res.items():
        print(("OK    " if v else "FALHOU"), k)
    ruins = [k for k, v in res.items() if not v]
    print(f"\n{len(res) - len(ruins)}/{len(res)} verificacoes conforme o esperado")
    return 1 if ruins else 0


if __name__ == "__main__":
    sys.exit(main())
