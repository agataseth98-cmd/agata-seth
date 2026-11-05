#!/usr/bin/env python3
"""Extrai o texto de um PDF com pypdf (lote 5b). Roda dentro do sandbox, sem rede, só leitura do arquivo.

Uso: extrair_pdf.py ARQUIVO.pdf   -> texto em stdout (até 200 páginas). Sai com 2 em erro.
Chamado por aquisicao.py quando não há pdftotext; o Python é o venv pessoal de
~/.local/share/agata/nova-versao/ferramentas/pdf-venv (instalação de usuário, sem sudo).
"""
import sys

MAX_PAGINAS = 200


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("uso: extrair_pdf.py ARQUIVO.pdf", file=sys.stderr)
        return 2
    try:
        from pypdf import PdfReader
    except ImportError:
        print("pypdf ausente", file=sys.stderr)
        return 2
    try:
        leitor = PdfReader(argv[0])
        partes = []
        for i, pagina in enumerate(leitor.pages):
            if i >= MAX_PAGINAS:
                break
            partes.append(pagina.extract_text() or "")
    except Exception as e:  # noqa: BLE001 — PDF corrompido vira erro, não trace
        print(f"falha ao ler PDF: {e.__class__.__name__}", file=sys.stderr)
        return 2
    sys.stdout.write("\n".join(partes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
