#!/usr/bin/env python3
"""Verifica se uma resposta cumpre o formato de cabeçalho da Regra 1 (REGRAS.md).
Uso: python3 scripts/verificar_cabecalho.py < resposta.txt
     echo "$RESPOSTA" | python3 scripts/verificar_cabecalho.py
     python3 scripts/verificar_cabecalho.py --max-entrada 156 < resposta.txt
Sem --max-entrada, tenta ler o número da última entrada em MEMÓRIAS.md (raiz do repo).
Saída: uma linha por falha achada, exit 1. Sem falhas: "OK", exit 0.
"""
import re
import sys
from pathlib import Path

def ultima_entrada_local() -> int | None:
    caminho = Path(__file__).resolve().parent.parent / "MEMÓRIAS.md"
    if not caminho.exists():
        return None
    numeros = re.findall(r"^\((\d+)\)", caminho.read_text(encoding="utf-8"), re.MULTILINE)
    # max(), não numeros[-1]: desde MEMÓRIAS (271) o arquivo cresce pelo
    # topo, então o último match físico passou a ser a entrada mais ANTIGA,
    # não a mais recente. max() é correto nos dois sentidos de leitura.
    return max((int(n) for n in numeros), default=None)

def verificar(texto: str, max_entrada_conhecida: int | None = None) -> list[str]:
    falhas = []

    tem_prontidao = bool(re.search(r"^\s*Nonce\s*:", texto, re.MULTILINE))
    tem_t = re.search(r"t\s*[=≥]\s*\d+", texto)

    if tem_prontidao and tem_t:
        falhas.append("mistura bloco de prontidão (Nonce:) com t=<n> — REGRAS.md:110, 'Misturar as duas formas é erro de formato'")

    if tem_prontidao:
        if not re.search(r"última entrada\s*:", texto, re.IGNORECASE):
            falhas.append("bloco de prontidão sem 'Última entrada:'")
        if not re.search(r"\bpronto\.?\b|\bquebrado\s*:", texto, re.IGNORECASE):
            falhas.append("bloco de prontidão sem 'pronto.' ou 'quebrado: <o quê>'")
    else:
        if not tem_t:
            falhas.append("falta t=<n> (ou t≥<n>) no cabeçalho")
        else:
            janela = texto[tem_t.end():tem_t.end() + 60]
            if not re.search(r"contado no contexto|prefixo compactado|contador mecânico", janela):
                falhas.append("t=<n> sem qualificador de contagem (contado no contexto / contador mecânico / prefixo compactado)")

    m_entrada = re.search(
        r"última entrada[^(]{0,20}\((\d+)\)|MEMÓRIAS\s*\((\d+)\)|\((\d+)\)\s*DIÁRIO",
        texto, re.IGNORECASE,
    )
    if not m_entrada:
        falhas.append("não cita a última entrada de MEMÓRIAS (número + referência)")
    elif max_entrada_conhecida is not None:
        n = int(next(g for g in m_entrada.groups() if g))
        if n > max_entrada_conhecida:
            falhas.append(
                f"entrada citada como última é ({n}), maior que a última real conhecida ({max_entrada_conhecida}) "
                f"— implausível, confira antes de aceitar (MEMÓRIAS (157))"
            )

    return falhas

if __name__ == "__main__":
    max_entrada = ultima_entrada_local()
    if "--max-entrada" in sys.argv:
        i = sys.argv.index("--max-entrada")
        max_entrada = int(sys.argv[i + 1])

    texto = sys.stdin.read()
    falhas = verificar(texto, max_entrada)
    if not falhas:
        print("OK")
        sys.exit(0)
    for f in falhas:
        print(f"FALHA: {f}")
    sys.exit(1)
