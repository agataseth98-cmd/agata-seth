#!/usr/bin/env python3
"""Testes locais do modo historia e do mapa gerado para PROJETO."""
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MIGRADOR = RAIZ / "scripts/migrar_periodo.py"
MAPA = RAIZ / "scripts/gerar_mapa_projeto.py"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rodar(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=RAIZ, text=True, capture_output=True)

def main() -> int:
    resultados = {}
    memoria = RAIZ / "MEMÓRIAS.md"
    antes = sha(memoria)
    with tempfile.TemporaryDirectory(prefix="agata-historia-") as tmp:
        destino = Path(tmp) / "memorias-copia.md"
        r = rodar(str(MIGRADOR), "historia", "--origem", "MEMÓRIAS.md", "--destino", str(destino))
        resultados["cópia gera destino e compara SHA-256 origem/destino"] = (
            r.returncode == 0 and destino.is_file() and sha(destino) == antes and sha(memoria) == antes
            and antes in r.stdout and "PASS historia" in r.stdout
        )
        destino_existente = Path(tmp) / "não-sobrescrever.md"
        destino_existente.write_bytes("conteúdo anterior\n".encode("utf-8"))
        r = rodar(str(MIGRADOR), "historia", "--origem", "MEMÓRIAS.md", "--destino", str(destino_existente))
        resultados["destino existente é recusado sem sobrescrita"] = (
            r.returncode != 0 and destino_existente.read_bytes() == "conteúdo anterior\n".encode("utf-8")
        )
        interno = RAIZ / "nao-escrever-no-canon.md"
        r = rodar(str(MIGRADOR), "historia", "--origem", "MEMÓRIAS.md", "--destino", str(interno))
        resultados["destino dentro do clone/canon é recusado"] = r.returncode != 0 and not interno.exists()
        r = rodar(str(MIGRADOR), "historia", "--origem", "MEMÓRIAS.md", "--destino", "relativo.md")
        resultados["destino relativo é recusado"] = r.returncode != 0
    legado = rodar(str(MIGRADOR))
    resultados["modo padrão segue como simulação sem escrita"] = legado.returncode == 0 and sha(memoria) == antes
    resultados["origem intacta ao final dos testes"] = sha(memoria) == antes

    mapa1 = rodar(str(MAPA))
    mapa2 = rodar(str(MAPA))
    texto = mapa1.stdout
    resultados["mapa reproduzível, menor que 25.000 chars e sem âncora de máquina"] = (
        mapa1.returncode == 0 and mapa2.returncode == 0 and texto == mapa2.stdout
        and len(texto) <= 25_000 and "## O que é — PROJETO.md:" in texto
        and "## Estado dos bugs e dos testes — PROJETO.md:" in texto
        and "ANCORA-SHA" not in texto
    )
    for nome, ok in resultados.items():
        print(f"{'PASS' if ok else 'FALHA'} {nome}")
    print(f"placar: {sum(resultados.values())}/{len(resultados)}")
    if mapa1.returncode == 0:
        print(f"mapa_chars={len(texto)}")
    return 0 if all(resultados.values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
