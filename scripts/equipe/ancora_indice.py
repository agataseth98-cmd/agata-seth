#!/usr/bin/env python3
"""Devolve ao índice o bloco ANCORA-SHA do HEAD, quando um commit abortado deixou um bloco novo staged (12/11/2026).

Por que existe: .githooks/pre-commit regrava o bloco ANCORA-SHA de REGRAS, PROJETO, MEMÓRIAS e PROMPT_CARREGAMENTO
e faz `git add` antes de checagens que ainda podem parar o commit (2ª passada do perímetro, guarda de âncora).
Se o commit para depois disso, o bloco novo fica no índice. No commit seguinte, o P-8 lê esse bloco como mudança
de comportamento em REGRAS.md e PROJETO.md e acusa SUSPEITO, sem nenhuma mudança do autor.

O que faz: troca o bloco ANCORA-SHA do índice pelo bloco do HEAD. O resto do staged não é tocado: mudança real do
autor continua staged. O pre-commit regrava a âncora logo depois, neste mesmo commit. O P-8 não é afrouxado: ele
continua vendo o que o autor staged, sem o bloco velho. Só mexe no bloco delimitado; nunca no resto do arquivo.

Uso:
  python3 -I scripts/equipe/ancora_indice.py ARQ...   (o pre-commit chama antes do P-8; sai 0 sempre)
  python3 -I scripts/equipe/ancora_indice.py --selftest
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

INICIO = "<!-- ANCORA-SHA:INICIO"
FIM = "<!-- ANCORA-SHA:FIM -->"
_BLOCO = re.compile(re.escape(INICIO) + r".*?" + re.escape(FIM), re.DOTALL)
RAIZ = Path(__file__).resolve().parents[2]
P8 = RAIZ / "scripts" / "perimetro" / "p08_quarentena.sh"


def normalizar(staged: str, head: str) -> str:
    """staged com o bloco ANCORA-SHA trocado pelo do head. Sem bloco em um dos dois: staged como está."""
    m = _BLOCO.search(head)
    if m is None or _BLOCO.search(staged) is None:
        return staged
    bloco = m.group(0)
    return _BLOCO.sub(lambda _: bloco, staged, count=1)


def _git(*args, cwd=None, entrada=None) -> bytes:
    return subprocess.run(["git", *args], cwd=cwd, input=entrada, capture_output=True, check=True).stdout


def _mostrar(rev: str, cwd=None):
    """Conteúdo de ':arq' (índice) ou 'HEAD:arq'. None se o caminho não existe nessa visão."""
    r = subprocess.run(["git", "show", rev], cwd=cwd, capture_output=True)
    return None if r.returncode != 0 else r.stdout.decode("utf-8")


def desfazer(arq: str, cwd=None) -> str:
    """Troca o bloco do índice pelo do HEAD. Devolve a linha para o pre-commit ('' se não havia o que trocar)."""
    staged = _mostrar(f":{arq}", cwd)
    head = _mostrar(f"HEAD:{arq}", cwd)
    if staged is None or head is None:
        return ""
    novo = normalizar(staged, head)
    if novo == staged:
        return ""
    modo = _git("ls-files", "-s", "--", arq, cwd=cwd).decode("utf-8").split()[0]
    blob = _git("hash-object", "-w", "--stdin", cwd=cwd, entrada=novo.encode("utf-8")).decode("utf-8").strip()
    _git("update-index", "--cacheinfo", f"{modo},{blob},{arq}", cwd=cwd)
    return (f"pre-commit: âncora de SHA que sobrou de um commit abortado voltou ao do HEAD no índice de '{arq}' "
            "(o resto do staged ficou como estava; a âncora é regravada logo abaixo).")


def main(argv) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    for arq in argv:
        try:
            msg = desfazer(arq)
        except Exception as e:  # noqa: BLE001 -- fail-soft: sem esta conferência, o P-8 decide sozinho
            print(f"pre-commit: AVISO -- não consegui conferir a âncora staged de '{arq}' "
                  f"({type(e).__name__}: {e}); o P-8 decide.", file=sys.stderr)
            continue
        if msg:
            print(msg)
    return 0


# --- selftest -------------------------------------------------------------------------------
def _repo(tmp: str, arquivos: dict) -> None:
    def g(*args):
        subprocess.run(["git", "-c", "user.name=agata", "-c", "user.email=agata@teste.invalid",
                        "-c", "commit.gpgsign=false", *args], cwd=tmp, check=True, capture_output=True)
    g("init", "-q")
    for nome, texto in arquivos.items():
        Path(tmp, nome).write_text(texto, encoding="utf-8")
    g("add", "-A")
    g("commit", "-q", "--no-verify", "-m", "base")


def _p8(tmp: str):
    r = subprocess.run(["bash", "-c", f'source "{P8}" && p8_quarentena'], cwd=tmp, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def _selftest() -> int:
    bloco = "<!-- ANCORA-SHA:INICIO (teste) -->\nSHA: {}\n<!-- ANCORA-SHA:FIM -->\n"
    head = "# Canon\n" + bloco.format("aaa111") + "Corpo do canon.\n"
    velho = "# Canon\n" + bloco.format("bbb222") + "Corpo do canon.\n"
    mudado = "Corpo mudado pelo autor."
    res = [
        ("bloco regravado volta ao do HEAD", normalizar(velho, head) == head),
        ("mudança do autor fora do bloco fica", normalizar(velho.replace("Corpo do canon.", mudado), head)
         == head.replace("Corpo do canon.", mudado)),
        ("sem bloco no HEAD, texto como está", normalizar(velho, "sem bloco\n") == velho),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        _repo(tmp, {"REGRAS.md": head})
        Path(tmp, "REGRAS.md").write_text(velho, encoding="utf-8")   # o que um commit abortado deixa
        subprocess.run(["git", "add", "REGRAS.md"], cwd=tmp, check=True)
        rc, saida = _p8(tmp)
        res.append(("reproduz: P-8 acusa SUSPEITO com só a âncora staged", rc == 1 and "SUSPEITO (P-8)" in saida))
        msg = desfazer("REGRAS.md", cwd=tmp)
        rc, saida = _p8(tmp)
        res.append(("depois de desfazer, P-8 passa", rc == 0 and msg != "" and _mostrar(":REGRAS.md", tmp) == head))
        res.append(("segunda passada não muda nada", desfazer("REGRAS.md", cwd=tmp) == ""))

    with tempfile.TemporaryDirectory() as tmp:
        _repo(tmp, {"REGRAS.md": head})
        Path(tmp, "REGRAS.md").write_text(velho.replace("Corpo do canon.", mudado), encoding="utf-8")
        subprocess.run(["git", "add", "REGRAS.md"], cwd=tmp, check=True)
        desfazer("REGRAS.md", cwd=tmp)
        esperado = head.replace("Corpo do canon.", mudado)
        res.append(("mudança real do autor no staged continua, com a âncora do HEAD",
                    _mostrar(":REGRAS.md", tmp) == esperado))

    falhas = 0
    for nome, ok in res:
        print(f"{'PASS' if ok else 'FALHA'}  {nome}")
        falhas += 0 if ok else 1
    print("SELFTEST OK" if not falhas else f"SELFTEST: {falhas} FALHA(S)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
