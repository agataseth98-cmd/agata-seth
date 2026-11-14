#!/usr/bin/env python3
"""Teto mecânico do PROJETO.md (componente projeto-indice, 12/11/2026).

O pre-commit chama este script com o conteúdo em staging (`git show :PROJETO.md`)
e recusa o commit quando passa de TETO_BYTES. Decisão do Humano (cache do Conselho,
entrada 522): o teto vira bloqueio mecânico, não aviso. Por que 6.000: topo da faixa-alvo
do índice (3 a 6 KB); ver redesign/projeto_indice/spec/spec.md, "Contrato".

Uso: python3 redesign/projeto_indice/teto.py [CAMINHO]   (padrão: PROJETO.md)
      python3 redesign/projeto_indice/teto.py - < arquivo  (lê da entrada padrão)
Código 0 se cabe no teto; 1 se passou (mensagem diz para onde vai cada conteúdo).
"""
from __future__ import annotations

import sys
from pathlib import Path

TETO_BYTES = 6000


def mensagem(tamanho: int) -> str:
    return (
        f"PROJETO.md tem {tamanho} bytes; o teto é {TETO_BYTES} (redesign/projeto_indice/teto.py). "
        "O PROJETO.md é índice: não guarda estado nem história. "
        "Estado (portas, serviços, modelos, lotes, bugs) vai para o gerado ESTADO.md (scripts/gerar_estado.py); "
        "prosa de estado vai para extras/projeto-detalhe/; como (mecanismo, procedimento) vai para PROTOCOLOS.md; "
        "histórico vai para extras/arquivo/ ou MEMÓRIAS.md. Ver redesign/projeto_indice/spec/spec.md."
    )


def checar(dados: bytes) -> tuple[bool, str]:
    tamanho = len(dados)
    if tamanho <= TETO_BYTES:
        return True, f"PROJETO.md: {tamanho} bytes, teto {TETO_BYTES}: OK"
    return False, mensagem(tamanho)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "-":
        dados = sys.stdin.buffer.read()
    else:
        caminho = Path(args[0]) if args else Path("PROJETO.md")
        dados = caminho.read_bytes()
    ok, texto = checar(dados)
    print(texto, file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
