#!/usr/bin/env python3
"""Consulta dirigida ao índice derivado — trechos para dar a um modelo em nuvem.

O executor local roda isto, pega a saída em texto plano e cola no contexto de
trabalho do modelo em nuvem. Não chama LLM nenhum, não acessa rede, não
escreve nada. É um extrator: recebe palavras-chave, devolve as seções de
REGRAS/PROJETO e as linhas de título de MEMÓRIAS que casam.

Fonte: memoria/missoes/agata-sistema/derivado/indice.md (Opção A, MEMÓRIAS (298)).
Ausente -> instrui a rodar gerar_indice_derivado.py. Com --rebuild, roda antes.

Uso:
  python3 scripts/consultar_indice.py <palavra> [<palavra> ...]
  python3 scripts/consultar_indice.py --all <p1> <p2>     # casa TODAS as palavras
  python3 scripts/consultar_indice.py --rebuild <palavra>  # regenera o índice antes
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDICE = os.path.join(REPO, "memoria", "missoes", "agata-sistema", "derivado", "indice.md")
GERADOR = os.path.join(REPO, "scripts", "gerar_indice_derivado.py")

MAX_SECOES = 15
MAX_TITULOS = 50


def erro(msg, cod=1):
    print(msg, file=sys.stderr)
    sys.exit(cod)


def parse_args(argv):
    modo_all = False
    rebuild = False
    termos = []
    for a in argv:
        if a == "--all":
            modo_all = True
        elif a == "--rebuild":
            rebuild = True
        elif a.startswith("--"):
            erro(f"opção desconhecida: {a}")
        else:
            termos.append(a.lower())
    if not termos:
        erro(__doc__)
    return modo_all, rebuild, termos


def casa(texto, termos, modo_all):
    t = texto.lower()
    hits = [x for x in termos if x in t]
    return (len(hits) == len(termos)) if modo_all else bool(hits)


def secoes_de(bloco):
    """(heading, corpo) por '## ' dentro de um bloco de texto."""
    out, cur_h, cur_b = [], None, []
    for ln in bloco.split("\n"):
        if ln.startswith("## "):
            if cur_h is not None:
                out.append((cur_h, "\n".join(cur_b).strip()))
            cur_h, cur_b = ln[3:].strip(), []
        elif cur_h is not None:
            cur_b.append(ln)
    if cur_h is not None:
        out.append((cur_h, "\n".join(cur_b).strip()))
    return out


def main():
    modo_all, rebuild, termos = parse_args(sys.argv[1:])

    if rebuild:
        r = subprocess.run([sys.executable, GERADOR])
        if r.returncode != 0:
            erro("gerar_indice_derivado.py falhou — nada consultado.")

    if not os.path.isfile(INDICE):
        erro(f"índice ausente: {INDICE}\nrode: python3 scripts/gerar_indice_derivado.py")

    txt = open(INDICE, encoding="utf-8").read()
    p1 = txt.find("## PARTE 1 ")
    p1b = txt.find("## PARTE 1b")
    p1c = txt.find("## PARTE 1c")
    p2 = txt.find("## PARTE 2")
    p3 = txt.find("## PARTE 3")
    if -1 in (p1, p1b, p1c, p2, p3):
        erro("índice sem as 5 partes esperadas (1, 1b, 1c, 2, 3) — regenere.")

    # Achado real, 01/10/2026: antes da reorganização em três camadas (609), só
    # havia PARTE 1 (REGRAS) e PARTE 2 (PROJETO) -- "## PARTE 1" até "## PARTE 2"
    # era um bloco só. A reforma inseriu PARTE 1b (PROTOCOLOS) e 1c (FALHAS) NO
    # MEIO desse intervalo sem que este script soubesse -- bloco_regras engolia
    # as três partes juntas, e secoes_de() atribuía os "## " de PROTOCOLOS/FALHAS
    # a "REGRAS.md" no rótulo da saída. Achado rodando consultar_indice.py de
    # verdade contra um termo só de PROTOCOLOS.md ("Regra 1.1") e vendo o
    # resultado sair rotulado "REGRAS.md" em vez de "PROTOCOLOS.md".
    bloco_regras = txt[p1:p1b]
    bloco_protocolos = txt[p1b:p1c]
    bloco_falhas = txt[p1c:p2]
    bloco_projeto = txt[p2:p3]
    bloco_mem = txt[p3:]

    conj = " ".join(termos)
    modo = "todas" if modo_all else "qualquer"
    print(f"# consulta ao índice — termos: {conj}  (casa: {modo})")
    print(f"# fonte: {os.path.relpath(INDICE, REPO)}")
    print(txt.split('\n', 4)[2])  # a linha canon: <sha> do frontmatter
    print()

    for rotulo, bloco in (("REGRAS.md", bloco_regras), ("PROTOCOLOS.md", bloco_protocolos),
                          ("FALHAS.md", bloco_falhas), ("PROJETO.md", bloco_projeto)):
        achados = [(h, c) for h, c in secoes_de(bloco)
                   if not h.startswith("PARTE ") and casa(h + "\n" + c, termos, modo_all)]
        print(f"================  {rotulo}: {len(achados)} seção(ões)  ================")
        for h, c in achados[:MAX_SECOES]:
            print(f"\n--- {rotulo} › {h} ---\n{c}\n")
        if len(achados) > MAX_SECOES:
            print(f"... +{len(achados) - MAX_SECOES} seção(ões) não mostrada(s)\n")

    titulos = [ln for ln in bloco_mem.split("\n")
               if re.match(r"^\(\d+\) ", ln) and casa(ln, termos, modo_all)]
    print(f"================  MEMÓRIAS: {len(titulos)} título(s)  ================")
    for ln in titulos[:MAX_TITULOS]:
        print(ln)
    if len(titulos) > MAX_TITULOS:
        print(f"... +{len(titulos) - MAX_TITULOS} título(s) não mostrado(s)")
    print(f"\n# fim. Corpo de entrada de MEMÓRIAS não entra aqui — abrir MEMÓRIAS.md pelo número.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
