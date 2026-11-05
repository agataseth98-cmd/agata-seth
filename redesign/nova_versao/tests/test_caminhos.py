import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import caminhos  # noqa: E402


class CaminhosTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name) / "entrada"
        self.base.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_recusa_escape_absoluto_e_nulo(self):
        for ruim in ("../fora.txt", "a/../../fora", "/etc/passwd", "x\x00y", "", None):
            with self.assertRaises(ValueError, msg=str(ruim)):
                caminhos.dentro(self.base, ruim)

    def test_recusa_symlink_que_aponta_para_fora(self):
        outro = Path(self.tmp.name) / "fora"
        outro.mkdir()
        (self.base / "link").symlink_to(outro)
        with self.assertRaises(ValueError):
            caminhos.dentro(self.base, "link/segredo.txt")

    def test_aceita_nome_normal_dentro(self):
        p = caminhos.dentro(self.base, "arquivo.md")
        self.assertEqual(p.parent.resolve(), self.base.resolve())

    def test_id_precisa_casar_inteiro(self):
        self.assertEqual(caminhos.id_seguro("rec-01", caminhos.RE_ID_CURTO), "rec-01")
        for ruim in ("../rec", "rec-01/../x", "REC-01", "rec-01\n", 7):
            with self.assertRaises(ValueError, msg=str(ruim)):
                caminhos.id_seguro(ruim, caminhos.RE_ID_CURTO)

    def test_arquivo_do_acervo_so_com_sha_e_extensao_da_lista(self):
        sha = "a" * 64
        self.assertEqual(caminhos.arquivo_do_acervo(self.base, sha, "PDF").name, sha + ".pdf")
        with self.assertRaises(ValueError):
            caminhos.arquivo_do_acervo(self.base, sha, "exe")
        with self.assertRaises(ValueError):
            caminhos.arquivo_do_acervo(self.base, "../" + "a" * 61, "md")


if __name__ == "__main__":
    unittest.main()
