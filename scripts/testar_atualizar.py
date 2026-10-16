#!/usr/bin/env python3
"""Suite sintetica de scripts/atualizar.sh (verificacao de saude e pausa). CANDIDATO.

HOME descartavel, repositorio e `origin` descartaveis, perimetro e geradores substituidos por stubs:
nada do Agata real e tocado. Uso: python3 -I scripts/testar_atualizar.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
BASE.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, LC_ALL="C.UTF-8")


def sh(cwd, *a, env=None, ok=True):
    p = subprocess.run(a, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env or BASE, text=True)
    if ok and p.returncode:
        raise RuntimeError(" ".join(a) + "\n" + p.stdout)
    return p


def escrever(r, nome, dados, modo=None):
    p = os.path.join(r, nome)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(dados)
    if modo:
        os.chmod(p, modo)


def montar():
    td = tempfile.mkdtemp(prefix="atu-")
    home = os.path.join(td, "home")
    r = os.path.join(home, "agata")
    os.makedirs(r)
    env = dict(BASE, HOME=home)
    sh(r, "git", "init", "-q", "-b", "main", env=env)
    sh(r, "git", "config", "user.email", "t@example.invalid", env=env)
    sh(r, "git", "config", "user.name", "t", env=env)
    shutil.copy(os.path.join(RAIZ, "scripts", "atualizar.sh"), os.path.join(r, "atualizar.sh"))
    os.makedirs(os.path.join(r, "scripts"))
    shutil.copy(os.path.join(RAIZ, "scripts", "atualizar.sh"), os.path.join(r, "scripts", "atualizar.sh"))
    os.remove(os.path.join(r, "atualizar.sh"))
    escrever(r, ".githooks/gerar-hidratacao.sh", "#!/usr/bin/env bash\necho hidrata-ok\n", 0o755)
    escrever(r, "scripts/perimetro.sh", "#!/usr/bin/env bash\n[ -e \"$HOME/falha-perimetro\" ] && { echo 'P-5 FALHOU'; exit 1; }\necho '=== RESULTADO GERAL: OK -- 20 OK ==='\n", 0o755)
    escrever(r, "scripts/inventario_componentes.py", "print('AVISO: deriva simulada (opcional, nao pode falhar a atualizacao)')\n")
    escrever(r, "a.txt", "a\n")
    sh(r, "git", "add", "-A", env=env)
    sh(r, "git", "commit", "-qm", "base", env=env)
    bare = os.path.join(td, "origin.git")
    sh(td, "git", "clone", "-q", "--bare", r, bare, env=env)
    sh(r, "git", "remote", "add", "origin", bare, env=env)
    sh(r, "git", "fetch", "-q", "origin", env=env)
    sh(r, "git", "branch", "-q", "--set-upstream-to=origin/main", "main", env=env)
    outro = os.path.join(td, "outro")
    sh(td, "git", "clone", "-q", bare, outro, env=env)
    sh(outro, "git", "config", "user.email", "t@example.invalid", env=env)
    sh(outro, "git", "config", "user.name", "t", env=env)
    return td, home, r, outro, env


def publicar(outro, env, nome):
    escrever(outro, nome, nome + "\n")
    sh(outro, "git", "add", "-A", env=env)
    sh(outro, "git", "commit", "-qm", nome, env=env)
    sh(outro, "git", "push", "-q", "origin", "main", env=env)


def rodar(r, env, **extra):
    return subprocess.run(["bash", "scripts/atualizar.sh", "TUDO"], cwd=r, env=dict(env, **extra),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def main():
    res = {}
    td, home, r, outro, env = montar()
    pausa = os.path.join(home, ".cache", "agata", "atualizacao-pausada")
    try:
        p = rodar(r, env)
        res["1 sem novidade: conclui e NAO roda a verificação de saúde"] = p.returncode == 0 and "verificação de saúde" not in p.stdout
        publicar(outro, env, "n1.txt")
        p = rodar(r, env)
        res["2 com novidade e perímetro OK: roda a saúde, mostra o resultado e conclui"] = \
            p.returncode == 0 and "RESULTADO GERAL: OK" in p.stdout and "componentes externos (opcional" in p.stdout
        res["3 aviso opcional dos componentes NÃO derruba a atualização"] = p.returncode == 0 and "deriva simulada" in p.stdout
        # falha do perímetro
        open(os.path.join(home, "falha-perimetro"), "w").close()
        publicar(outro, env, "n2.txt")
        head_antes = sh(r, "git", "rev-parse", "HEAD", env=env).stdout.strip()
        p = rodar(r, env)
        head_depois = sh(r, "git", "rev-parse", "HEAD", env=env).stdout.strip()
        res["4 perímetro falha: sai com erro, cria a pausa e NÃO reverte (história preservada)"] = \
            p.returncode == 1 and os.path.exists(pausa) and head_depois != head_antes and "git revert" in open(pausa).read() \
            and "reset --hard" in open(pausa).read() and "nunca" in open(pausa).read()
        publicar(outro, env, "n3.txt")
        p = rodar(r, env)
        res["5 com a pausa de pé, a próxima atualização RECUSA e não puxa nada"] = \
            p.returncode == 1 and "PAUSADA" in p.stdout and not os.path.exists(os.path.join(r, "n3.txt"))
        os.remove(os.path.join(home, "falha-perimetro"))
        p = rodar(r, env, AGATA_ATUALIZAR_RETOMAR="1")
        res["6 retomada explícita atualiza, a saúde passa e a pausa é removida"] = \
            p.returncode == 0 and os.path.exists(os.path.join(r, "n3.txt")) and not os.path.exists(pausa)
        escrever(r, "sujo.txt", "mudança local\n")
        sh(r, "git", "add", "sujo.txt", env=env)
        publicar(outro, env, "n4.txt")
        p = rodar(r, env)
        res["7 mudança local não commitada: recusa (comportamento anterior preservado)"] = p.returncode == 1 and "não vou sobrescrever" in p.stdout
    finally:
        shutil.rmtree(td, ignore_errors=True)
    for k, v in res.items():
        print(("OK    " if v else "FALHOU"), k)
    ruins = [k for k, v in res.items() if not v]
    print(f"\n{len(res) - len(ruins)}/{len(res)} verificações conforme o esperado")
    return 1 if ruins else 0


if __name__ == "__main__":
    sys.exit(main())
