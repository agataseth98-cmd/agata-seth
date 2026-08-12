#!/usr/bin/env python3
# Busca por deslizamento de janela: prova o offset da fatia (1)-(62) de MEMÓRIAS.md
# por comprimento + hash, sem depender de número de linha ou formato de cabeçalho.
# Uso: python3 scripts/achar_ancora_1_62.py

import hashlib
import sys

ARQUIVO = "MEMÓRIAS.md"
COMPRIMENTO = 128671
HASH_ESPERADO = "b26ac113f7a6f72c875391c2d07d94f6f6c827cc9d14c180ecc324b14ab4e03a"

with open(ARQUIVO, "rb") as f:
    dados = f.read()

n = len(dados)
if n < COMPRIMENTO:
    print(f"arquivo tem {n} bytes, menor que a janela ({COMPRIMENTO}) — impossível.")
    sys.exit(1)

achados = []
for offset in range(0, n - COMPRIMENTO + 1):
    janela = dados[offset:offset + COMPRIMENTO]
    h = hashlib.sha256(janela).hexdigest()
    if h == HASH_ESPERADO:
        achados.append(offset)

if not achados:
    print("NENHUM offset bateu. Âncora não reproduzida em nenhuma janela do arquivo atual.")
    sys.exit(1)

for offset in achados:
    inicio = dados[offset:offset + 60]
    fim = dados[offset + COMPRIMENTO - 60:offset + COMPRIMENTO]
    print(f"OFFSET={offset}")
    print(f"marcador_inicio={inicio!r}")
    print(f"marcador_fim={fim!r}")
    print(f"byte_seguinte_ao_fim={dados[offset + COMPRIMENTO:offset + COMPRIMENTO + 40]!r}")
    print()

sys.exit(0)
