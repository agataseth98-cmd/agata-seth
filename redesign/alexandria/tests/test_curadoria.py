import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import acervo  # noqa: E402
import curadoria  # noqa: E402

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]


class CuradoriaTests(unittest.TestCase):
    def notas(self, fs, i):
        return " ".join(next(f for f in fs if f["id"] == i).get("notas", []))

    def test_copia_correcao_autoridade_e_medicao_anotadas_e_ordenadas(self):
        fs = curadoria.organizar([
            {"id": "a", "texto": "Estudo X: 90%.", "origem": "blog-a, cópia do comunicado Y", "autoridade": "nenhuma"},
            {"id": "b", "texto": "Estudo X: 90%.", "origem": "blog-b, cópia do comunicado Y", "autoridade": "nenhuma"},
            {"id": "c", "texto": "(700) A voz é faber.", "autoridade": "canon", "data": "2026-10-01"},
            {"id": "d", "texto": "(800) CORREÇÃO de (700): a voz é agata-last.", "autoridade": "canon", "data": "2026-11-03"},
            {"id": "e", "texto": "serviço ativo", "autoridade": "medição", "data": "2026-11-04T10:00"},
            {"id": "f", "texto": "serviço parado", "autoridade": "medição", "data": "2026-11-04T10:05"}])
        self.assertIn("não é confirmação independente", self.notas(fs, "b"))
        self.assertIn("corrigida por [d]", self.notas(fs, "c"))
        self.assertIn("vale a mais recente", self.notas(fs, "e"))
        self.assertIn("sem autoridade", self.notas(fs, "a"))
        self.assertNotIn("notas", next(f for f in fs if f["id"] == "f"))
        self.assertEqual([f["id"] for f in fs][:2], ["f", "d"])          # autoridade, depois data mais recente
        self.assertEqual({f["id"] for f in fs[-2:]}, {"a", "b"})         # sem autoridade por último

    def test_sem_conflito_nada_muda(self):
        fs = curadoria.organizar([{"id": "d1", "texto": "porta 20146", "autoridade": "canon"}])
        self.assertEqual(fs, [{"id": "d1", "texto": "porta 20146", "autoridade": "canon"}])


class CorrecaoNoAcervoTests(unittest.TestCase):
    def test_entrada_corrigida_sai_marcada_so_pela_primeira_citada(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        t = Path(tmp.name)
        os.environ["AGATA_NV_DIR"] = str(t / "dados")
        os.environ["AGATA_NV_CACHE"] = str(t / "cache")
        repo = t / "repo"
        repo.mkdir()
        (repo / "MEMÓRIAS.md").write_text(
            "# M\n\n(10) DIÁRIO — x · porta do painel é 8080\n\n(11) DIÁRIO — y · outra coisa\n\n"
            "(12) CORREÇÃO — z · **Correção de (10): a porta do painel é 20146; ver também (11).**\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run([*GIT, "-C", str(repo), "add", "-A"], check=True)
        subprocess.run([*GIT, "-C", str(repo), "commit", "-qm", "x"], check=True)
        acervo.iniciar()
        acervo.indexar(acervo.snapshot("HEAD", repo), skills=False)
        p = acervo.consultar("porta painel outra coisa", semantica="nunca")
        marc = {r["entrada"]: r.get("corrigida_por") for r in p["resultados"]}
        self.assertEqual(marc.get(10), [12])
        self.assertIsNone(marc.get(11))      # citada no cabeçalho, mas não é a corrigida
        self.assertIsNone(marc.get(12))


if __name__ == "__main__":
    unittest.main()
