#!/usr/bin/env python3
"""Atualiza só o bloco delimitado ANCORA-SHA em PROMPT_CARREGAMENTO.md
-- item 2, 20/08/2026, ordem do Humano. Chamado por .githooks/pre-commit,
antes do commit existir.

Limite conhecido, aceito por decisão do Humano: um commit não pode
embutir o próprio SHA (problema de auto-referência). O valor escrito
aqui é sempre o SHA do HEAD ANTES deste commit -- fica até 1 commit
atrasado, nunca mais, e o próprio texto do arquivo diz isso.

Nunca toca o resto do arquivo (documento editado à mão pelo Humano).
Se os marcadores não existirem, ABORTA sem escrever nada -- silêncio
alto (stderr + exit != 0), nunca corrompe silenciosamente um arquivo
que não reconhece.

Uso: atualizar_ancora_prompt.py <caminho-do-prompt> <sha-do-head-anterior> <data-hora-local>
"""
import re
import sys

INICIO = "<!-- ANCORA-SHA:INICIO"
FIM = "<!-- ANCORA-SHA:FIM -->"


def main():
    if len(sys.argv) != 4:
        print(f"uso: {sys.argv[0]} <caminho> <sha-anterior> <data-hora>", file=sys.stderr)
        return 2

    caminho, sha, data_hora = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(caminho, encoding="utf-8") as f:
        texto = f.read()

    padrao = re.compile(
        re.escape(INICIO) + r".*?" + re.escape(FIM),
        re.DOTALL,
    )
    if not padrao.search(texto):
        print(f"ABORTADO: marcadores ANCORA-SHA não encontrados em {caminho} -- nada escrito.", file=sys.stderr)
        return 1

    novo_bloco = (
        f"{INICIO} (gerado por .githooks/pre-commit -- não editar as duas linhas abaixo à mão, "
        f"o resto do arquivo é livre) -->\n"
        f"  SHA do commit ANTERIOR a este arquivo (limite conhecido: pode estar até 1 commit "
        f"atrasado, nunca mais -- ver PROJETO.md, \"Memória e hidratação\"): {sha}\n"
        f"  Escrito em: {data_hora}\n"
        f"{FIM}"
    )
    texto_novo = padrao.sub(novo_bloco, texto, count=1)

    if texto_novo == texto:
        print("pre-commit: âncora já estava atualizada, nada mudou.")
        return 0

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto_novo)

    print(f"pre-commit: âncora de SHA atualizada em {caminho} -- {sha[:7]}, {data_hora}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
