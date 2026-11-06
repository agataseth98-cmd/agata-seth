import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import mvp  # noqa: E402


class MvpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        (self.raiz / "a.py").write_text("x = 1\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def proposta(self, conteudo="x = 1\n"):
        (self.raiz / "a.py").write_text(conteudo, encoding="utf-8")
        p = mvp.criar_pedido("ajustar x", ["a.py"])
        return mvp.criar_proposta(p, mvp.coletar_evidencias(p, self.raiz), "--- a\n+++ b\n", "abc")

    def test_pedido_sem_objetivo_ou_escopo_e_recusado(self):
        with self.assertRaises(ValueError):
            mvp.criar_pedido("  ", ["a.py"])
        with self.assertRaises(ValueError):
            mvp.criar_pedido("ok", [])

    def test_caminho_fora_do_escopo_e_recusado(self):
        for ruim in ("../segredo.txt", "/etc/passwd"):
            with self.assertRaises(ValueError):
                mvp.criar_pedido("ajustar", [ruim])

    def test_evidencia_muda_o_digest_da_proposta(self):
        d1 = self.proposta("x = 1\n")["digest"]
        d2 = self.proposta("x = 2\n")["digest"]
        self.assertNotEqual(d1, d2)

    def test_arquivo_ausente_fica_registrado_como_ausente(self):
        p = mvp.criar_pedido("ajustar", ["nao_existe.py"])
        e = mvp.coletar_evidencias(p, self.raiz)
        self.assertTrue(e[0]["ausente"])

    def test_decisao_exige_digest_exato(self):
        pr = self.proposta()
        with self.assertRaises(ValueError):
            mvp.registrar_decisao(pr, "aceita", "orusoua", "0" * 64)

    def test_decisao_por_modelo_e_recusada(self):
        pr = self.proposta()
        with self.assertRaises(ValueError):
            mvp.registrar_decisao(pr, "aceita", "claude", pr["digest"])

    def test_decisao_humana_nunca_marca_aplicado(self):
        pr = self.proposta()
        d = mvp.registrar_decisao(pr, "aceita", "orusoua", pr["digest"])
        self.assertFalse(d["aplicado"])

    def test_modulo_nao_aplica_mudanca(self):
        fonte = (AQUI.parent / "mvp.py").read_text(encoding="utf-8")
        self.assertNotIn("git apply", fonte)
        self.assertNotIn("git commit", fonte)

    def test_selftest(self):
        self.assertTrue(mvp._selftest())


if __name__ == "__main__":
    unittest.main()
