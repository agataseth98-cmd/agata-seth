#!/usr/bin/env python3
"""verificar_citacao_arquivo.py -- fecha a classe de falha mais recorrente do
catalogo (REGRAS.md, "Catalogo de falhas conhecidas"): citar arquivo+linha+
trecho sem checar contra a fonte. 8 das 20 falhas catalogadas sao desta
familia ((59) ate (250)/(251)); duas ocorrencias frescas nesta sessao
(minuta externa GLM v1/v2, e uma citacao minha propria que dei por errada
num grep que falhou) motivaram esta proposta.

Uso:
  python3 verificar_citacao_arquivo.py < texto.md
  python3 verificar_citacao_arquivo.py --raiz /caminho/repo < texto.md

Le um texto (stdin) e acha citacoes no padrao que este projeto realmente usa:
  `arquivo.ext` linha N       ou   `arquivo.ext:N`
seguidas (na mesma frase ou ate ~200 chars depois) de um trecho entre aspas
retas ("...") ou crase dupla/backtick (`...`). Para cada uma, abre o arquivo
REAL (relativo a raiz do repo) e confere se a linha N contem o trecho citado.

Saida, uma linha por citacao achada:
  OK    arquivo:N
  FALHA arquivo:N -- trecho nao bate. Linha real: "..."
  FALHA arquivo:N -- arquivo nao existe
  FALHA arquivo:N -- linha nao existe (arquivo tem M linhas)

Exit 0 se tudo OK ou nada achado pra checar; exit 1 se alguma FALHA.
Nao e' juiz de prosa -- so confere o que foi citado como fato preciso.

Limitacao conhecida, testada contra documento real (nao so caso sintetico):
citacao sem trecho entre aspas para conferir, ou prosa com mais de um span
entre crases perto da citacao (ex.: um hash curto de commit entre a
referencia de linha e o trecho de verdade), pode gerar falso-positivo ou
reduzir recall. Por isso este verificador entra no perimetro como AVISO,
nunca como FALHA-class -- ver scripts/perimetro/p19_citacao_arquivo.sh.
"""
import re
import sys
import argparse
import unicodedata


def normaliza(s: str) -> str:
    # remove acentuacao e colapsa espaco, pra comparar sem depender de
    # normalizacao unicode exata (aspas curvas vs retas, etc.)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()


# Padrao de citacao: `caminho/arquivo[.ext]` com a linha DENTRO da crase
# (`arquivo.py:112`, a forma mais comum no proprio canon deste projeto,
# conferida com grep em MEMORIAS.md/REGRAS.md antes desta versao) ou FORA
# dela (`arquivo.py`:112 / `arquivo.py` linha 112, tambem usada). A
# primeira versao deste regex so' reconhecia a forma de FORA -- achado
# testando contra citacoes REAIS ja existentes no canon (nao caso
# sintetico): `scripts/ler_pagina.sh:33` e outras seis ocorrencias da
# forma "dentro" ficavam invisiveis, maioria dos casos reais do proprio
# arquivo MEMORIAS.md. O caminho tem que ter '/' (path) OU extensao
# (.ext) -- cobre tanto scripts/perimetro.sh quanto .githooks/pre-commit
# (hook sem extensao, mesma lacuna achada antes: a primeira versao do
# regex exigia extensao e nunca casava com nada em .githooks/).
CITACAO_RE = re.compile(
    r"`(?P<arq>[^`\s:]*(?:/[^`\s:]+|\.[a-zA-Z0-9]+))(?::(?P<n1>\d+))?`"
    r"(?:\s*(?:linhas?\s+(?P<n2>\d+)|:\s*(?P<n3>\d+)))?",
    re.IGNORECASE,
)

# Trecho citado: primeiro bloco entre aspas retas ou crase apos a citacao,
# dentro de uma janela curta (mesma frase, tipicamente).
TRECHO_RE = re.compile(r'["“]([^"“”]{6,300})["”]|`([^`]{6,300})`')


def achar_citacoes(texto: str):
    # Achado testando contra a minuta real (nao um caso sintetico): entre a
    # citacao "arquivo linha N" e o trecho de verdade pode haver OUTRO span
    # entre crases no meio (ex: "linha 316, HEAD `ca521306`): `trecho real`"
    # -- pegar o PRIMEIRO span da janela pega o hash curto, nao o trecho.
    # Corrigido pegando o span MAIS LONGO da janela, nao o primeiro --
    # trecho citado de verdade tende a ser mais longo que um hash/identificador
    # incidental. Descarta spans com menos de 12 chars (abaixo disso e' mais
    # provavel ser hash/nome de variavel que texto citado).
    citacoes = []
    for m in CITACAO_RE.finditer(texto):
        arquivo = m.group("arq")
        linha_n = m.group("n1") or m.group("n2") or m.group("n3")
        if not linha_n:
            continue
        # Janela apertada (200, nao 400): testando contra a minuta real,
        # 400 chars alcancava a citacao SEGUINTE e pegava o trecho errado
        # -- prosa bem formada cita o trecho logo depois da referencia de
        # linha, nao 3 frases adiante. Reduz falso-positivo, custa recall
        # em prosa mais solta (aceito: reprovar sem certeza e' mais seguro
        # que aprovar sem checar -- mesma doutrina do P-1 sobre grep
        # negativo, REGRAS catalogo (250)-(251)).
        janela = texto[m.end(): m.end() + 200]
        candidatos = [
            (g1 or g2) for g1, g2 in TRECHO_RE.findall(janela)
        ]
        candidatos = [c for c in candidatos if len(c) >= 12]
        trecho = max(candidatos, key=len) if candidatos else None
        citacoes.append((arquivo, int(linha_n), trecho))
    return citacoes


def checar(raiz: str, arquivo: str, linha_n: int, trecho):
    import os

    caminho = os.path.join(raiz, arquivo)
    if not os.path.isfile(caminho):
        return False, f"arquivo nao existe: {caminho}"
    with open(caminho, encoding="utf-8", errors="replace") as f:
        linhas = f.readlines()
    if linha_n < 1 or linha_n > len(linhas):
        return False, f"linha nao existe (arquivo tem {len(linhas)} linhas)"
    real = linhas[linha_n - 1]
    if trecho is None:
        return True, f"citacao sem trecho entre aspas para conferir -- linha real: {real.strip()[:120]!r}"
    if normaliza(trecho) in normaliza(real):
        return True, None
    # tenta vizinhanca de 1 linha pra citacao off-by-one (erro comum, achado testando)
    for offset in (-1, 1):
        idx = linha_n - 1 + offset
        if 0 <= idx < len(linhas) and normaliza(trecho) in normaliza(linhas[idx]):
            return False, f"trecho bate na linha {idx+1}, nao {linha_n} -- off-by-{offset:+d}"
    return False, f"trecho nao bate. Linha real: {real.strip()[:160]!r}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=".")
    args = ap.parse_args()
    texto = sys.stdin.read()
    citacoes = achar_citacoes(texto)
    if not citacoes:
        print("nenhuma citacao arquivo+linha achada no texto.")
        sys.exit(0)
    falhou = False
    for arquivo, linha_n, trecho in citacoes:
        ok, msg = checar(args.raiz, arquivo, linha_n, trecho)
        status = "OK   " if ok else "FALHA"
        if not ok:
            falhou = True
        extra = f" -- {msg}" if msg else ""
        print(f"{status} {arquivo}:{linha_n}{extra}")
    sys.exit(1 if falhou else 0)


if __name__ == "__main__":
    main()
