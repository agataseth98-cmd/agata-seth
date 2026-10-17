#!/usr/bin/env python3
"""verificar_expurgo.py -- ramo "expurgo assinado" do P-5 (decisão do Humano, 17/10/2026: citação inventada se expurga, inegociável).

O P-5 recusa alterar entrada já registrada (Regra 4). Esta é a ÚNICA exceção, e é estreita: o conteúdo NOVO de MEMÓRIAS.md tem de ser o
ANTIGO (HEAD) com um expurgo ASSINADO aplicado, mais, no máximo, entradas novas no topo. O expurgo é um par `propostas/expurgo-<nome>.diff`
+ `propostas/APROVADO-expurgo-<nome>` (em propostas/ ou propostas/aplicadas/) assinado pelo Humano, igual ao P-8 (sha256 do .diff + assinatura
ssh, namespace agata-aprovacao-p8, contra a raiz de confiança de HEAD). E o .diff só pode SUBSTITUIR linhas por linhas que carregam o marcador
"[citação inventada, expurgada em ": mesmo número de linhas tiradas e postas, só em MEMÓRIAS.md, nenhuma linha posta sem o marcador.
O histórico do git não é reescrito; o que muda é o arquivo vivo, de onde os modelos leem (hidratação e derivados).

Uso: verificar_expurgo.py ANTIGO NOVO [RAIZ]   exit 0 = o NOVO é o ANTIGO expurgado de forma assinada; 1 = não; 2 = uso.
     verificar_expurgo.py --selftest
"""
import glob
import hashlib
import os
import subprocess
import sys
import tempfile

MARCADOR_EXPURGO = "[citação inventada, expurgada em "
MARCADOR_P5 = "<!-- ENTRADAS-NOVAS:AQUI".encode("utf-8")


def _corpo(b):
    i = b.find(MARCADOR_P5)
    if i == -1:
        return None
    return b[b.find(b"\n", i) + 1:]


def _git(raiz, *args, entrada=None):
    return subprocess.run(["git", "-C", raiz, *args], input=entrada, capture_output=True)


def _assinatura_ok(raiz, nome, diff_path, apr_path):
    dsha = hashlib.sha256(open(diff_path, "rb").read()).hexdigest()
    linhas = open(apr_path, encoding="utf-8", errors="replace").read().splitlines()
    if f"diff-sha256: {dsha}" not in linhas:
        return False, "sha256 do .diff não bate com o APROVADO"
    sig = []
    dentro = False
    for l in linhas:
        if "BEGIN SSH SIGNATURE" in l:
            dentro = True
        if dentro:
            sig.append(l)
        if "END SSH SIGNATURE" in l:
            break
    if not sig:
        return False, "APROVADO sem bloco de assinatura"
    r = _git(raiz, "show", "HEAD:propostas/.allowed_signers")
    if r.returncode != 0 or not r.stdout.strip():
        return False, "sem propostas/.allowed_signers em HEAD"
    with tempfile.TemporaryDirectory() as td:
        open(f"{td}/signers", "wb").write(r.stdout)
        open(f"{td}/sig", "w", encoding="utf-8").write("\n".join(sig) + "\n")
        p = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", f"{td}/signers", "-I", "agata-humano", "-n", "agata-aprovacao-p8",
                            "-s", f"{td}/sig"], input=f"{dsha}  {nome}".encode(), capture_output=True)
    return (p.returncode == 0), (p.stderr or p.stdout).decode(errors="replace").strip()


def _diff_estreito(diff_path):
    """True se o .diff só troca linhas de MEMÓRIAS.md por linhas com o marcador (mesmo número, sem acréscimo livre)."""
    texto = open(diff_path, encoding="utf-8").read().splitlines()
    arquivos = [l for l in texto if l.startswith(("--- ", "+++ "))]
    if not arquivos or any(a.split("\t")[0] not in ("--- a/MEMÓRIAS.md", "+++ b/MEMÓRIAS.md") for a in arquivos):
        return False
    tiradas = [l for l in texto if l.startswith("-") and not l.startswith("---")]
    postas = [l for l in texto if l.startswith("+") and not l.startswith("+++")]
    if not tiradas or len(tiradas) != len(postas):
        return False
    return all(MARCADOR_EXPURGO in p for p in postas)


def verificar(antigo, novo, raiz):
    ca, cn = _corpo(antigo), _corpo(novo)
    if ca is None or cn is None:
        return False, "marcador ENTRADAS-NOVAS ausente"
    candidatos = glob.glob(os.path.join(raiz, "propostas", "APROVADO-expurgo-*")) + \
        glob.glob(os.path.join(raiz, "propostas", "aplicadas", "APROVADO-expurgo-*"))
    motivos = []
    for apr in sorted(candidatos):
        nome = os.path.basename(apr)[len("APROVADO-"):]
        diff = next((d for d in (os.path.join(raiz, "propostas", nome + ".diff"), os.path.join(raiz, "propostas", "aplicadas", nome + ".diff")) if os.path.isfile(d)), None)
        if not diff:
            motivos.append(f"{nome}: .diff ausente")
            continue
        ok, m = _assinatura_ok(raiz, nome, diff, apr)
        if not ok:
            motivos.append(f"{nome}: {m}")
            continue
        if not _diff_estreito(diff):
            motivos.append(f"{nome}: .diff fora do formato permitido (só trocar linhas de MEMÓRIAS.md por linhas com o marcador)")
            continue
        with tempfile.TemporaryDirectory() as td:
            open(os.path.join(td, "MEMÓRIAS.md"), "wb").write(antigo)
            p = subprocess.run(["git", "apply", os.path.abspath(diff)], cwd=td, capture_output=True)
            if p.returncode != 0:
                motivos.append(f"{nome}: não aplica sobre o HEAD ({p.stderr.decode(errors='replace').strip()[:80]})")
                continue
            remendado = open(os.path.join(td, "MEMÓRIAS.md"), "rb").read()
        cr = _corpo(remendado)
        if cr is not None and len(cn) >= len(cr) and cn.endswith(cr):
            return True, f"expurgo assinado '{nome}' aplicado; resto só cresceu pelo topo"
        motivos.append(f"{nome}: o conteúdo novo não é o antigo + este expurgo + entradas no topo")
    return False, "; ".join(motivos) or "nenhum par propostas/APROVADO-expurgo-* encontrado"


def _selftest():
    ok_geral = True
    res = {}
    with tempfile.TemporaryDirectory() as td:
        raiz = os.path.join(td, "repo")
        os.makedirs(os.path.join(raiz, "propostas"))
        subprocess.run(["git", "init", "-q", raiz], check=True)
        chave = os.path.join(td, "k")
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", chave], check=True)
        pub = open(chave + ".pub").read().split()
        open(os.path.join(raiz, "propostas", ".allowed_signers"), "w").write(f'agata-humano namespaces="agata-aprovacao-p8" {pub[0]} {pub[1]}\n')
        cab = "# MEMÓRIAS\n<!-- ENTRADAS-NOVAS:AQUI -- teste -->\n"
        antigo = cab + "(2) DIÁRIO — a · disse \"frase inventada X\" e mais.\n\n(1) DIÁRIO — b · texto b.\n"
        open(os.path.join(raiz, "MEMÓRIAS.md"), "w").write(antigo)
        _git(raiz, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
        _git(raiz, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base")
        mod = antigo.replace('disse "frase inventada X" e mais', f'disse {MARCADOR_EXPURGO}17/10/2026] e mais')
        novo_ok = cab + "(3) DIÁRIO — nova no topo.\n\n" + mod[len(cab):]
        with tempfile.TemporaryDirectory() as t2:
            open(os.path.join(t2, "a"), "w").write(antigo)
            open(os.path.join(t2, "b"), "w").write(mod)
            d = subprocess.run(["git", "diff", "--no-index", "-U1", "a", "b"], cwd=t2, capture_output=True, text=True).stdout
        d = d.replace("a/a", "a/MEMÓRIAS.md").replace("b/b", "b/MEMÓRIAS.md")
        nome = "expurgo-teste"
        dpath = os.path.join(raiz, "propostas", nome + ".diff")
        open(dpath, "w", encoding="utf-8").write(d)
        dsha = hashlib.sha256(d.encode("utf-8")).hexdigest()
        p = subprocess.run(["ssh-keygen", "-Y", "sign", "-f", chave, "-n", "agata-aprovacao-p8"], input=f"{dsha}  {nome}".encode(), capture_output=True)
        assinatura = p.stdout.decode()
        apr = os.path.join(raiz, "propostas", "APROVADO-" + nome)
        open(apr, "w", encoding="utf-8").write(f"diff-sha256: {dsha}\n{assinatura}")
        _git(raiz, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
        _git(raiz, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "chave e par")
        # o HEAD agora tem a raiz de confiança; antigo = HEAD:MEMÓRIAS.md
        a = antigo.encode()
        res["1 expurgo assinado + entrada nova no topo passa"] = verificar(a, novo_ok.encode(), raiz)[0]
        res["2 expurgo assinado sozinho passa"] = verificar(a, mod.encode(), raiz)[0]
        res["3 sem aplicar o expurgo (só entrada nova) não é este ramo"] = not verificar(a, (cab + "(3) x\n\n" + antigo[len(cab):]).encode(), raiz)[0]
        res["4 edição qualquer fora do expurgo não passa"] = not verificar(a, novo_ok.replace("texto b.", "texto B alterado.").encode(), raiz)[0]
        res["5 apagar a entrada inteira não passa"] = not verificar(a, (cab + "(1) DIÁRIO — b · texto b.\n").encode(), raiz)[0]
        # assinatura adulterada: muda o .diff depois de assinado
        open(dpath, "a").write("\n")
        res["6 .diff alterado depois de assinado não passa"] = not verificar(a, mod.encode(), raiz)[0]
        open(dpath, "w", encoding="utf-8").write(d)
        # sem par
        os.remove(apr)
        res["7 sem o APROVADO não passa"] = not verificar(a, mod.encode(), raiz)[0]
        # diff largo (põe linha sem marcador)
        d2 = d.replace(MARCADOR_EXPURGO, "[outra coisa ")
        open(dpath, "w", encoding="utf-8").write(d2)
        dsha2 = hashlib.sha256(d2.encode("utf-8")).hexdigest()
        p2 = subprocess.run(["ssh-keygen", "-Y", "sign", "-f", chave, "-n", "agata-aprovacao-p8"], input=f"{dsha2}  {nome}".encode(), capture_output=True)
        open(apr, "w", encoding="utf-8").write(f"diff-sha256: {dsha2}\n{p2.stdout.decode()}")
        res["8 .diff assinado mas sem o marcador de expurgo não passa"] = not verificar(a, mod.replace(MARCADOR_EXPURGO, "[outra coisa ").encode(), raiz)[0]
    for k, v in res.items():
        print(("OK    " if v else "FALHOU"), k)
        ok_geral = ok_geral and v
    print(f"verificar_expurgo selftest: {sum(res.values())}/{len(res)}")
    return 0 if ok_geral else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    raiz = sys.argv[3] if len(sys.argv) > 3 else os.getcwd()
    ok, msg = verificar(open(sys.argv[1], "rb").read(), open(sys.argv[2], "rb").read(), raiz)
    print(("P-5 expurgo: " if ok else "P-5 expurgo NÃO vale: ") + msg)
    sys.exit(0 if ok else 1)
