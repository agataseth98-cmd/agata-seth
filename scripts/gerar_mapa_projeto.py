#!/usr/bin/env python3
"""Gera um mapa curto e reproduzível de PROJETO.md para hidratação.

O mapa é mecânico: mantém o título, os headings e o primeiro parágrafo de
cada seção/subseção. Não substitui PROJETO.md nem edita qualquer arquivo.
Por padrão escreve no stdout; pode receber o caminho-fonte como argumento.
"""
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LIMITE_CHARS = 25_000
HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*#*\s*$")


def sem_comentarios(texto: str) -> list[str]:
    linhas = []
    em_comentario = False
    em_codigo = False
    for linha in texto.splitlines():
        if linha.lstrip().startswith("```"):
            em_codigo = not em_codigo
        if not em_codigo:
            if "<!--" in linha:
                em_comentario = True
            if not em_comentario:
                linhas.append(linha)
            if "-->" in linha:
                em_comentario = False
        else:
            linhas.append(linha)
    return linhas


def paragrafo_inicial(linhas: list[str]) -> str:
    blocos = []
    atual = []
    em_codigo = False
    for linha in linhas:
        stripped = linha.strip()
        if stripped.startswith("```"):
            em_codigo = not em_codigo
            continue
        if not stripped:
            if atual:
                blocos.append(" ".join(atual))
                atual = []
            continue
        if em_codigo or stripped.startswith("<!--") or stripped.startswith("-->"):
            continue
        if stripped.startswith(("#", "---", "<")):
            continue
        item_lista = re.match(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", linha)
        if item_lista and atual:
            blocos.append(" ".join(atual))
            atual = []
        atual.append(stripped)
    if atual:
        blocos.append(" ".join(atual))
    return blocos[0] if blocos else ""


def slug(titulo: str) -> str:
    texto = unicodedata.normalize("NFKD", titulo).casefold()
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[`*_]", "", texto)
    texto = re.sub(r"[^a-z0-9 -]", "", texto)
    return re.sub(r"\s+", "-", texto.strip())


def gerar(texto: str, limite: int = LIMITE_CHARS) -> str:
    linhas = sem_comentarios(texto)
    h1 = next((l.strip() for l in linhas if l.startswith("# ")), "# PROJETO.md")
    eventos = []
    for numero, linha in enumerate(linhas, 1):
        m = HEADING.match(linha)
        if m and m.group(1) != "#":
            eventos.append((numero, len(m.group(1)), m.group(2).strip()))
    saida = [h1, "", "Mapa gerado dos títulos e parágrafos iniciais; a fonte completa é PROJETO.md.", ""]
    for i, (linha_num, nivel, titulo) in enumerate(eventos):
        proximo = len(linhas)
        for n2, nivel2, _ in eventos[i + 1:]:
            if nivel2 <= nivel:
                proximo = n2 - 1
                break
        trecho = linhas[linha_num:proximo]
        resumo = paragrafo_inicial(trecho)
        prefixo = "##" if nivel == 2 else "###"
        saida.append(f"{prefixo} {titulo} — PROJETO.md:{linha_num} (#{slug(titulo)})")
        if resumo:
            saida.append(resumo)
        saida.append("")
    resultado = "\n".join(saida).rstrip() + "\n"
    if len(resultado) > limite:
        raise ValueError(f"mapa excede o limite: {len(resultado)} > {limite} caracteres")
    return resultado


def main() -> int:
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "PROJETO.md"
    if len(sys.argv) > 2:
        print("uso: gerar_mapa_projeto.py [PROJETO.md]", file=sys.stderr)
        return 2
    if not caminho.is_absolute():
        caminho = RAIZ / caminho
    try:
        texto = caminho.read_text(encoding="utf-8")
        sys.stdout.write(gerar(texto))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"FALHA mapa PROJETO: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
