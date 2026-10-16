#!/usr/bin/env python3
"""verificar_cofre.py -- verificação SÓ DE LEITURA do cofre de chaves (G-C, etapa F1; desenho em
propostas/desenho-cofre-chaves-2026-10-16.md). Compara config/segredos-manifesto.txt com o disco usando APENAS stat():
NUNCA abre, lê nem imprime o conteúdo de um segredo. Avisa (não bloqueia; `--estrito` devolve exit 1 se houver aviso):
  * segredo do manifesto ausente no disco;
  * permissão diferente da esperada (ex.: 644 num arquivo que deveria ser 600);
  * segredo vencido ou vencendo em 14 dias (validade_dias > 0);
  * cópia de recuperação (~/.agata-backup-staging/env-*.gpg) MAIS VELHA que ~/.config/agata/.env;
  * arquivo de segredo conhecido fora do manifesto: ~/librechat/PRIMEIRO-ACESSO.txt (deve ser apagado após trocar a senha).
Uso: python3 scripts/verificar_cofre.py [--manifesto ARQ] [--hoje AAAA-MM-DD] [--estrito] [--selftest]"""
import argparse
import datetime
import glob
import os
import stat
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMADA_PADRAO = os.path.join(RAIZ, "config", "segredos-manifesto.txt")


def ler_manifesto(caminho):
    out = []
    with open(caminho, encoding="utf-8") as f:
        for n, l in enumerate(f, 1):
            l = l.strip()
            if not l or l.startswith("#"):
                continue
            c = [x.strip() for x in l.split("|")]
            if len(c) != 6:
                raise ValueError(f"manifesto linha {n}: esperadas 6 colunas, vieram {len(c)}")
            out.append({"caminho": os.path.expanduser(c[0]), "classe": c[1], "validade": int(c[2]),
                        "rotacao": datetime.date.fromisoformat(c[3]), "modo": c[4], "uso": c[5], "rotulo": c[0]})
    return out


def verificar(manifesto, hoje, home=None, staging=None):
    """Devolve lista de (nivel, mensagem). nivel: OK | AVISO. Só stat()."""
    home = home or os.path.expanduser("~")
    staging = staging or os.path.join(home, ".agata-backup-staging")
    res = []
    for e in manifesto:
        p = e["caminho"]
        try:
            st = os.stat(p)
        except OSError:
            res.append(("AVISO", f"{e['rotulo']}: ausente no disco (classe {e['classe']})"))
            continue
        modo = oct(stat.S_IMODE(st.st_mode))[2:]
        if modo != e["modo"]:
            res.append(("AVISO", f"{e['rotulo']}: permissão {modo}, esperada {e['modo']} (classe {e['classe']}); corrija com chmod {e['modo']}"))
        else:
            res.append(("OK", f"{e['rotulo']}: permissão {modo}"))
        if e["validade"] > 0:
            vence = e["rotacao"] + datetime.timedelta(days=e["validade"])
            dias = (vence - hoje).days
            if dias < 0:
                res.append(("AVISO", f"{e['rotulo']}: VENCIDO há {-dias} dias (rotação em {e['rotacao']}, validade {e['validade']} d)"))
            elif dias <= 14:
                res.append(("AVISO", f"{e['rotulo']}: vence em {dias} dias"))
    # cópia de recuperação do .env mais velha que o próprio .env
    env = os.path.join(home, ".config", "agata", ".env")
    copias = sorted(glob.glob(os.path.join(staging, "env-*.gpg")), key=os.path.getmtime)
    if os.path.exists(env):
        if not copias:
            res.append(("AVISO", "cópia de recuperação do .env: NENHUMA em " + staging))
        else:
            d_env = datetime.date.fromtimestamp(os.path.getmtime(env))
            d_cop = datetime.date.fromtimestamp(os.path.getmtime(copias[-1]))
            if d_cop < d_env:
                res.append(("AVISO", f"cópia de recuperação do .env ({os.path.basename(copias[-1])}, {d_cop}) é MAIS VELHA que o .env ({d_env}): {(d_env - d_cop).days} dia(s) de mudanças sem cobertura; rode scripts/cifrar_env.sh"))
            else:
                res.append(("OK", f"cópia de recuperação do .env em dia ({d_cop})"))
    if os.path.exists(os.path.join(home, "librechat", "PRIMEIRO-ACESSO.txt")):
        res.append(("AVISO", "~/librechat/PRIMEIRO-ACESSO.txt ainda existe (CHAVES.md manda apagar depois de trocar a senha no app)"))
    return res


def _selftest():
    casos = []
    td = tempfile.mkdtemp(prefix="cofre-")
    try:
        home = os.path.join(td, "home")
        os.makedirs(os.path.join(home, ".config", "agata"))
        os.makedirs(os.path.join(home, ".agata-backup-staging"))
        env = os.path.join(home, ".config", "agata", ".env")
        open(env, "w").write("SEGREDO-SINTETICO=nao-deve-ser-lido\n")
        os.chmod(env, 0o644)
        man = os.path.join(td, "m.txt")
        open(man, "w").write("# c\n" + f"{env}|A|180|2026-01-01|600|teste\n{home}/ausente|B|90|2026-10-01|600|teste\n")
        m = ler_manifesto(man)
        hoje = datetime.date(2026, 10, 16)
        r = verificar(m, hoje, home=home)
        msgs = "\n".join(x[1] for x in r)
        casos.append(("detecta permissão errada", "permissão 644, esperada 600" in msgs))
        casos.append(("detecta ausente", "ausente no disco" in msgs))
        casos.append(("detecta vencido", "VENCIDO" in msgs))
        casos.append(("sem cópia de recuperação: avisa", "NENHUMA" in msgs))
        cop = os.path.join(home, ".agata-backup-staging", "env-20250101.gpg")
        open(cop, "w").write("x")
        os.utime(cop, (0, 86400 * 365))  # 1971, bem mais velha que o .env
        casos.append(("cópia mais velha que o .env: avisa", "MAIS VELHA" in "\n".join(x[1] for x in verificar(m, hoje, home=home))))
        os.chmod(env, 0o600)
        os.utime(cop, None)
        os.utime(env, (0, 86400 * 365))
        ok_msgs = "\n".join(x[1] for x in verificar(m, hoje, home=home))
        casos.append(("cópia em dia: sem aviso de cópia velha", "em dia" in ok_msgs))
        open(os.path.join(home, ".config", "agata", "x"), "w").write("y")
        casos.append(("manifesto com coluna a menos é rejeitado", _rejeita(td)))
        casos.append(("nunca abre o segredo", _nao_abre(m, hoje, home)))
    finally:
        import shutil
        shutil.rmtree(td, ignore_errors=True)
    for n, ok in casos:
        print(("PASS  " if ok else "FALHA ") + n)
    bad = [n for n, ok in casos if not ok]
    print(f"verificar_cofre selftest: {len(casos) - len(bad)}/{len(casos)}")
    return 1 if bad else 0


def _rejeita(td):
    p = os.path.join(td, "ruim.txt")
    open(p, "w").write("a|b|c\n")
    try:
        ler_manifesto(p)
        return False
    except ValueError:
        return True


def _nao_abre(m, hoje, home):
    import builtins
    abertos = []
    real = builtins.open
    def espia(f, *a, **k):
        abertos.append(str(f))
        return real(f, *a, **k)
    builtins.open = espia
    try:
        verificar(m, hoje, home=home)
    finally:
        builtins.open = real
    return not abertos


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifesto", default=CAMADA_PADRAO)
    ap.add_argument("--hoje")
    ap.add_argument("--estrito", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    hoje = datetime.date.fromisoformat(a.hoje) if a.hoje else datetime.date.today()
    try:
        res = verificar(ler_manifesto(a.manifesto), hoje)
    except (OSError, ValueError) as e:
        print(f"ERRO: {e}")
        return 2
    for n, m in res:
        print(f"{n}: {m}")
    avisos = sum(n == "AVISO" for n, _ in res)
    print(f"cofre: {len(res) - avisos} ok · {avisos} aviso(s)")
    return 1 if (a.estrito and avisos) else 0


if __name__ == "__main__":
    sys.exit(main())
