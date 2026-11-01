import json
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent


class FerramentasTests(unittest.TestCase):
    def test_indice_em_dia(self):
        # compara em memória; não reescreve INDICE.md nem indice.json
        sys.path.insert(0, str(RAIZ))
        import ferramentas
        gravado = json.loads((RAIZ / "indice.json").read_text(encoding="utf-8"))
        self.assertEqual(gravado, ferramentas.varrer())

    def test_skills_proprias_sao_so_as_versionadas(self):
        sys.path.insert(0, str(RAIZ))
        import ferramentas
        base = ferramentas.PROPRIAS[0]
        r = subprocess.run(["git", "-C", str(ferramentas.REPO), "ls-files", "--", str(base.relative_to(ferramentas.REPO))],
                           capture_output=True, text=True)
        if r.returncode != 0:
            self.skipTest("fora de um repositório git")
        for skill in ferramentas.skills_proprias(base):
            self.assertTrue(str(skill.relative_to(ferramentas.REPO)) in r.stdout.splitlines())

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
