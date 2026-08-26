#!/usr/bin/env python3
"""Duas resoluções no corpo do índice, lido do stdin.
Primeiras N linhas inteiras (as mais recentes — desde MEMÓRIAS (271) o
stream chega mais recente primeiro); anteriores truncadas em M CARACTERES
(não bytes). Número e data ficam sempre no início da linha, então truncar
por prefixo os preserva por construção — exigência da Regra 4, onde a
numeração pré-(49) não é única e a data é o desambiguador."""
import sys
N = int(sys.argv[1]); M = int(sys.argv[2])
linhas = [l.rstrip("\n") for l in sys.stdin]
for i, l in enumerate(linhas):
    print(l if (i < N or len(l) <= M) else l[:M].rstrip() + " …")
