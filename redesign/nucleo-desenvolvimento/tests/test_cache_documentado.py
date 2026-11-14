"""C10: o comando de cache documentado no guia grava um fato e uma pendência, e o `ler` mostra os dois.

O teste extrai o comando do próprio guia (não copia), troca o autor e o texto, e roda numa pasta temporária,
apontada por AGATA_CACHE_CONSELHO. Não toca o cache real do usuário.
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
FLUXO = RAIZ / ".agents/skills/agata-fluxo/SKILL.md"
MODELO = re.compile(r'python3 (redesign/router/cache_conselho\.py) anotar --autor "<modelo real>" --tipo (fato|pendencia) "<texto>"')


class CacheDocumentadoTests(unittest.TestCase):
    def test_cache_fato_e_pendencia_pelo_comando_documentado(self):
        texto = FLUXO.read_text(encoding="utf-8")
        comandos = {m.group(2): m.group(1) for m in MODELO.finditer(texto)}
        self.assertEqual(set(comandos), {"fato", "pendencia"},
                         "o guia precisa documentar o comando de anotar com --tipo fato e --tipo pendencia")
        with tempfile.TemporaryDirectory() as pasta:
            env = dict(os.environ)
            env["AGATA_CACHE_CONSELHO"] = str(Path(pasta) / "cache.jsonl")
            env["AGATA_P20_LISTA"] = str(Path(pasta) / "sem-lista.txt")  # lista privada não é lida aqui
            notas = {"fato": "teste c10 fato", "pendencia": "teste c10 pendencia"}
            for tipo, nota in notas.items():
                r = subprocess.run([sys.executable, comandos[tipo], "anotar", "--autor", "teste-c10",
                                    "--tipo", tipo, nota], cwd=RAIZ, env=env, capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, f"anotar --tipo {tipo} falhou: {r.stderr.strip()}")
            r = subprocess.run([sys.executable, "redesign/router/cache_conselho.py", "ler", "--n", "20"],
                               cwd=RAIZ, env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"ler falhou: {r.stderr.strip()}")
            for tipo, nota in notas.items():
                self.assertIn(nota, r.stdout, f"o ler não mostrou a entrada de {tipo}")
                self.assertIn(f"teste-c10 · {tipo}", r.stdout, f"o ler não mostrou o tipo {tipo}")


if __name__ == "__main__":
    unittest.main()
