import json
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent


class FerramentasTests(unittest.TestCase):
    def test_indice_em_dia(self):
        antes = (RAIZ / "indice.json").read_text(encoding="utf-8")
        subprocess.run([sys.executable, "-I", str(RAIZ / "ferramentas.py"), "reindexar"], check=True, capture_output=True)
        self.assertEqual(antes, (RAIZ / "indice.json").read_text(encoding="utf-8"))

    def test_quarentena_nao_vaza_para_outros_temas(self):
        for p in json.loads((RAIZ / "indice.json").read_text(encoding="utf-8")):
            if p["nome"] in ("continuous-learning-v2", "unified-memory", "agentic-os"):
                self.assertEqual(p["tema"], "quarentena")

    def test_fontes_presas_a_commit_com_licenca(self):
        for fonte in ("ecc", "superpowers"):
            self.assertEqual(len((RAIZ / "fontes" / fonte / "COMMIT").read_text().strip()), 40)
            self.assertTrue((RAIZ / "fontes" / fonte / "LICENSE").is_file())

    def test_nada_executavel_em_fontes(self):
        for f in (RAIZ / "fontes").rglob("*"):
            if f.is_file():
                self.assertFalse(f.stat().st_mode & 0o111, str(f))


if __name__ == "__main__":
    unittest.main()
