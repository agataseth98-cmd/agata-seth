#!/usr/bin/env python3
"""Verifica se uma resposta cumpre o formato de cabeçalho da Regra 1 (REGRAS.md).
Uso: python3 scripts/verificar_cabecalho.py < resposta.txt
     echo "$RESPOSTA" | python3 scripts/verificar_cabecalho.py
Saída: uma linha por falha achada, exit 1. Sem falhas: "OK", exit 0.
"""
import re
import sys

def verificar(texto: str) -> list[str]:
    falhas = []

    m_turno = re.search(r"t\s*[=≥]\s*\d+", texto)
    if not m_turno:
        falhas.append("falta t=<n> (ou t≥<n>) no cabeçalho")
    else:
        janela = texto[m_turno.end():m_turno.end() + 60]
        if not re.search(r"contado no contexto|prefixo compactado|contador mecânico", janela):
            falhas.append("t=<n> sem qualificador de contagem (contado no contexto / contador mecânico / prefixo compactado)")

    if not re.search(r"última entrada.{0,40}\(\d+\)|MEMÓRIAS\s*\(\d+\)|\(\d+\)\s*DIÁRIO", texto, re.IGNORECASE):
        falhas.append("não cita a última entrada de MEMÓRIAS (número + referência)")

    if not re.search(r"\bpronto\.?\b|\bquebrado\s*:", texto, re.IGNORECASE):
        falhas.append("falta o 4º passo do preâmbulo — 'pronto.' ou 'quebrado: <o quê>'")

    return falhas

if __name__ == "__main__":
    texto = sys.stdin.read()
    falhas = verificar(texto)
    if not falhas:
        print("OK")
        sys.exit(0)
    for f in falhas:
        print(f"FALHA: {f}")
    sys.exit(1)
