#!/usr/bin/env python3
"""cifrar_recuperacao.py -- cópia de recuperação dos segredos (cofre G-C, etapa F2; desenho em
propostas/desenho-cofre-chaves-2026-10-16.md). Empacota TODOS os caminhos de config/segredos-manifesto.txt e cifra com `age`
para a chave PÚBLICA do Humano (config/segredos-destinatario.txt). A chave privada fica cifrada com senha no pendrive do Humano
e nunca entra aqui: este script NÃO consegue decifrar o que cria.

* Sem arquivo de texto puro no disco: `tar` escreve no pipe e `age` lê do pipe (nada de .tar temporário).
* Saída: ~/.agata-backup-staging/segredos-AAAAMMDD-HHMM.tar.age (modo 600) + um .txt irmão com SÓ nomes, data e sha256 da cópia.
  Mantém as 3 cópias mais recentes. Não imprime nem registra nenhum conteúdo de segredo.
* A chave de assinatura do Humano (classe H) ENTRA na cópia de propósito: perdê-la impede assinar qualquer proposta e a rotação
  do `.allowed_signers` exige uma assinatura da chave antiga.
* NÃO prova que a cópia decifra (a máquina não tem a chave privada). A prova é o teste de restauração do Humano, com o pendrive:
      age -d -i (age -d "<pendrive>/agata-recuperacao.key.age" | psub) <cópia>.tar.age | tar -tvf -        # fish; lista, não extrai
Uso: python3 scripts/cifrar_recuperacao.py [--saida DIR] [--selftest]"""
import argparse
import datetime
import glob
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import verificar_cofre as vc  # noqa: E402  (mesma régua do manifesto)


def destinatario(arq=None):
    arq = arq or os.path.join(RAIZ, "config", "segredos-destinatario.txt")
    for l in open(arq, encoding="utf-8"):
        l = l.strip()
        if l.startswith("age1") and " " not in l:
            return l
    raise ValueError("config/segredos-destinatario.txt sem chave pública age1…")


def cifrar(manifesto, dest, saida, home, agora=None, guardar=3):
    """Devolve (caminho_da_cópia, [rótulos incluídos], [rótulos ausentes])."""
    agora = agora or datetime.datetime.now()
    itens, ausentes = [], []
    for e in manifesto:
        p = e["caminho"]
        if os.path.exists(p):
            itens.append((e["rotulo"], os.path.relpath(p, "/")))
        else:
            ausentes.append(e["rotulo"])
    if not itens:
        raise RuntimeError("nenhum segredo do manifesto existe no disco")
    os.makedirs(saida, exist_ok=True)
    os.chmod(saida, 0o700)
    nome = f"segredos-{agora:%Y%m%d-%H%M}.tar.age"
    alvo = os.path.join(saida, nome)
    tmp = alvo + ".parcial"
    tar = subprocess.Popen(["tar", "-C", "/", "-cf", "-", "--"] + [r for _, r in itens], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    age = subprocess.Popen(["age", "-r", dest, "-o", tmp], stdin=tar.stdout, stderr=subprocess.PIPE)
    tar.stdout.close()
    err_age = age.communicate()[1]
    err_tar = tar.stderr.read()
    tar.wait()
    if tar.returncode != 0 or age.returncode != 0:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise RuntimeError(f"falha ao empacotar/cifrar (tar={tar.returncode}, age={age.returncode}): {(err_tar + err_age).decode('utf-8', 'replace')[:200]}")
    with open(tmp, "rb") as f:
        cab = f.read(32)
    if not cab.startswith(b"age-encryption.org/v1") or os.path.getsize(tmp) < 200:
        os.unlink(tmp)
        raise RuntimeError("saída não parece um arquivo age válido")
    os.chmod(tmp, 0o600)
    os.replace(tmp, alvo)
    sha = hashlib.sha256(open(alvo, "rb").read()).hexdigest()
    with open(alvo[:-8] + ".txt", "w", encoding="utf-8") as f:
        f.write(f"cópia de recuperação de segredos · {agora:%Y-%m-%d %H:%M}\nsha256 da cópia: {sha}\ndestinatário: {dest}\nincluídos ({len(itens)}):\n")
        f.writelines(f"  {r}\n" for r, _ in itens)
        f.writelines(f"AUSENTE (não incluído): {r}\n" for r in ausentes)
    os.chmod(alvo[:-8] + ".txt", 0o600)
    antigas = sorted(glob.glob(os.path.join(saida, "segredos-*.tar.age")))
    for velha in antigas[:-guardar]:
        os.unlink(velha)
        txt = velha[:-8] + ".txt"
        if os.path.exists(txt):
            os.unlink(txt)
    return alvo, [r for r, _ in itens], ausentes


def _selftest():
    if not shutil.which("age") or not shutil.which("age-keygen") or not shutil.which("tar"):
        print("SKIP  age/age-keygen/tar ausentes: selftest de ida e volta não executado")
        return 0
    casos = []
    td = tempfile.mkdtemp(prefix="recup-")
    try:
        home = os.path.join(td, "home")
        os.makedirs(os.path.join(home, ".config", "agata", "google-project"))
        seg = os.path.join(home, ".config", "agata", ".env")
        open(seg, "w").write("CHAVE_SINTETICA=valor-de-teste-123\n")
        open(os.path.join(home, ".config", "agata", "google-project", "cred.json"), "w").write('{"k":"sintetico"}')
        chave = os.path.join(td, "teste.key")
        pub = subprocess.run(["age-keygen", "-o", chave], capture_output=True, text=True).stderr.split()[-1]
        man = [{"caminho": seg, "rotulo": "~/.config/agata/.env", "classe": "A"},
               {"caminho": os.path.dirname(seg) + "/google-project", "rotulo": "~/.config/agata/google-project", "classe": "B"},
               {"caminho": home + "/nao-existe", "rotulo": "~/nao-existe", "classe": "B"}]
        alvo, inc, aus = cifrar(man, pub, os.path.join(td, "staging"), home, agora=datetime.datetime(2026, 10, 16, 18, 0))
        casos.append(("gera cópia .tar.age com modo 600", os.path.exists(alvo) and oct(os.stat(alvo).st_mode)[-3:] == "600"))
        casos.append(("ausente é relatado, não derruba", aus == ["~/nao-existe"] and len(inc) == 2))
        bruto = open(alvo, "rb").read()
        casos.append(("cópia não contém o segredo em texto puro", b"valor-de-teste-123" not in bruto and b"CHAVE_SINTETICA" not in bruto))
        saida = subprocess.run(["age", "-d", "-i", chave, alvo], capture_output=True)
        casos.append(("ida e volta: decifra com a chave de teste", saida.returncode == 0))
        lst = subprocess.run(["tar", "-tf", "-"], input=saida.stdout, capture_output=True).stdout.decode()
        casos.append(("o conteúdo do tar tem os dois itens", ".config/agata/.env" in lst and "google-project/cred.json" in lst))
        ext = os.path.join(td, "ext")
        os.makedirs(ext)
        subprocess.run(["tar", "-C", ext, "-xf", "-"], input=saida.stdout)
        casos.append(("conteúdo restaurado é idêntico", open(os.path.join(ext, os.path.relpath(seg, "/"))).read() == open(seg).read()))
        txt = open(alvo[:-8] + ".txt", encoding="utf-8").read()
        casos.append(("ficha irmã tem só nomes e sha256, sem segredo", "valor-de-teste-123" not in txt and "sha256 da cópia" in txt))
        for i in range(4):  # retenção das 3 mais recentes
            cifrar(man, pub, os.path.join(td, "staging"), home, agora=datetime.datetime(2026, 10, 17, 9, i))
        casos.append(("retém só as 3 cópias mais recentes", len(glob.glob(os.path.join(td, "staging", "segredos-*.tar.age"))) == 3))
        try:
            cifrar(man, "nao-e-chave", os.path.join(td, "s2"), home)
            casos.append(("chave pública inválida falha e não deixa cópia", False))
        except RuntimeError:
            casos.append(("chave pública inválida falha e não deixa cópia", not glob.glob(os.path.join(td, "s2", "*.age*"))))
    finally:
        shutil.rmtree(td, ignore_errors=True)
    for n, ok in casos:
        print(("PASS  " if ok else "FALHA ") + n)
    bad = [n for n, ok in casos if not ok]
    print(f"cifrar_recuperacao selftest: {len(casos) - len(bad)}/{len(casos)}")
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--saida", default=os.path.expanduser("~/.agata-backup-staging"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    try:
        alvo, inc, aus = cifrar(vc.ler_manifesto(vc.CAMADA_PADRAO), destinatario(), a.saida, os.path.expanduser("~"))
    except (OSError, ValueError, RuntimeError) as e:
        print(f"ERRO: {e}")
        return 2
    print(f"cópia: {alvo}")
    print(f"incluídos: {len(inc)} · ausentes: {len(aus)}" + (f" ({', '.join(aus)})" if aus else ""))
    print("Lembrete: a máquina NÃO consegue decifrar esta cópia; a prova de restauração é do Humano, com o pendrive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
