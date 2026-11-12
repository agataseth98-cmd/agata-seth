#!/usr/bin/env python3
"""diff_limpo.py <arquivo.diff | -> [--selftest]

Recusa um .diff de proposta P-8 que tem hunk tocando o bloco ANCORA-SHA dos canônicos.
Esse bloco é reescrito pelo .githooks/pre-commit em TODO commit (SHA do commit anterior,
"Escrito em:", URLs pinadas em SHA). Um hunk que inclui qualquer linha dele (+, - ou contexto)
quebra no commit seguinte, porque o texto que o diff espera já não existe mais na base.

Regra mecânica, sem juízo: se alguma linha de hunk de REGRAS.md, PROJETO.md, MEMÓRIAS.md ou
PROMPT_CARREGAMENTO.md casar um dos padrões do bloco gerado, o .diff é recusado (exit 1).
Usado por scripts/aprovar.sh (não assina), scripts/p8_verificar.sh (não aplica),
scripts/equipe/aplicar.py (não começa) e scripts/p8_verificar_pr.sh (CI, para .diff novo no PR).
Exit 0 = limpo; 1 = recusado (diz onde); 2 = uso errado.
"""
import re
import sys

CANONICOS_COM_BLOCO = ("REGRAS.md", "PROJETO.md", "MEMÓRIAS.md", "PROMPT_CARREGAMENTO.md")

# Linhas que só existem dentro do bloco gerado (ver .githooks/pre-commit e scripts/atualizar_ancora_prompt.py).
PADROES_GERADOS = [
    re.compile(r"<!-- ANCORA-SHA:"),
    re.compile(r"SHA do commit ANTERIOR a este arquivo"),
    re.compile(r"^\s*Escrito em: \d{2}/\d{2}/\d{4} \d{2}:\d{2}"),
    re.compile(r"raw\.githubusercontent\.com/[^/\s]+/[^/\s]+/[0-9a-f]{40}/"),
]


def _caminho(bruto):
    """Caminho de cabeçalho `+++ b/...`, com as aspas e os escapes octais que o git põe em não-ASCII."""
    p = bruto.strip()
    if p.startswith('"') and p.endswith('"'):
        p = bytes(p[1:-1], "ascii").decode("unicode_escape").encode("latin-1").decode("utf-8", "replace")
    if p.startswith("b/"):
        p = p[2:]
    return p


def hunks_gerados(texto):
    """Lista de (arquivo, linha_do_diff, trecho) para cada linha de hunk que casa um padrão gerado."""
    achados = []
    arquivo = None
    restam_old = restam_new = 0
    for n, linha in enumerate(texto.splitlines(), 1):
        if restam_old or restam_new:
            tipo, conteudo = (linha[:1], linha[1:]) if linha else (" ", "")
            if tipo == "\\":
                continue
            if tipo == " " or tipo == "":
                restam_old -= 1; restam_new -= 1
            elif tipo == "-":
                restam_old -= 1
            elif tipo == "+":
                restam_new -= 1
            else:
                # linha fora do formato: o contador de hunk estava errado; o diff é recusado por garantia
                return [(arquivo or "?", n, "linha de hunk malformada")]
            if arquivo in CANONICOS_COM_BLOCO and any(p.search(conteudo) for p in PADROES_GERADOS):
                achados.append((arquivo, n, conteudo.strip()[:120]))
            continue
        if linha.startswith("+++ "):
            arquivo = _caminho(linha[4:])
        elif linha.startswith("@@"):
            m = re.match(r"@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", linha)
            if not m:
                return [(arquivo or "?", n, "cabeçalho de hunk malformado")]
            restam_old = int(m.group(1)) if m.group(1) is not None else 1
            restam_new = int(m.group(2)) if m.group(2) is not None else 1
    return achados


def _selftest():
    def hunk(arq, linhas_old, linhas_new):
        corpo = []
        for l in linhas_old:
            corpo.append("-" + l[1:] if l.startswith("!") else " " + l)
        for l in linhas_new:
            corpo.append("+" + l)
        # contadores: contexto conta nos dois lados; -/+ só no seu lado
        n_old = sum(1 for l in corpo if l[0] in " -")
        n_new = sum(1 for l in corpo if l[0] in " +")
        return f"diff --git a/{arq} b/{arq}\n--- a/{arq}\n+++ b/{arq}\n@@ -1,{n_old} +1,{n_new} @@\n" + "\n".join(corpo) + "\n"

    casos = []
    # 1. bloco gerado como contexto: recusa
    casos.append(("contexto no bloco", hunk("REGRAS.md", ["<!-- ANCORA-SHA:INICIO (gerado) -->", "  Escrito em: 12/11/2026 10:06 -03"], ["x"]), 1))
    # 2. trocar o SHA do raw: recusa
    casos.append(("URL pinada em SHA", hunk("PROMPT_CARREGAMENTO.md", ["!    https://raw.githubusercontent.com/a/b/" + "a" * 40 + "/REGRAS.md"], ["    https://raw.githubusercontent.com/a/b/" + "b" * 40 + "/REGRAS.md"]), 1))
    # 3. texto de corpo que só cita o nome do bloco: passa
    casos.append(("menção no corpo", hunk("PROMPT_CARREGAMENTO.md", ["O bloco entre os marcadores ANCORA-SHA é gerado."], ["texto novo"]), 0))
    # 4. linha 'Escrito em:' em arquivo que não é canônico com bloco: passa
    casos.append(("arquivo sem bloco", hunk("propostas/x.md", ["  Escrito em: 12/11/2026 10:06 -03"], ["y"]), 0))
    # 5. hunk normal de regra: passa
    casos.append(("regra normal", hunk("REGRAS.md", ["- **Regra 1:** velho"], ["- **Regra 1:** novo"]), 0))
    falhas = []
    for nome, texto, esperado in casos:
        obtido = 1 if hunks_gerados(texto) else 0
        if obtido != esperado:
            falhas.append(f"{nome}: esperado {esperado}, veio {obtido}")
    if falhas:
        print("SELFTEST FALHOU:\n  " + "\n  ".join(falhas))
        return 1
    print(f"SELFTEST OK -- {len(casos)} casos")
    return 0


def main(argv):
    if argv == ["--selftest"]:
        return _selftest()
    if len(argv) != 1:
        print("uso: diff_limpo.py <arquivo.diff | ->  |  --selftest", file=sys.stderr)
        return 2
    origem = argv[0]
    texto = sys.stdin.read() if origem == "-" else open(origem, encoding="utf-8").read()
    achados = hunks_gerados(texto)
    if not achados:
        print("OK: nenhum hunk toca bloco gerado pelo pre-commit (ANCORA-SHA)")
        return 0
    print("FALHA: o .diff tem hunk em bloco gerado pelo pre-commit (ANCORA-SHA). Ele quebra no commit seguinte; refaça sem esse trecho:")
    for arq, n, trecho in achados[:20]:
        print(f"  {arq} (linha {n} do .diff): {trecho}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
