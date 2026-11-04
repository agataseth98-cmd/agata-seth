import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class NovaVersaoPainelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = self.tmp.name + "/dados"
        os.environ["AGATA_NV_CACHE"] = self.tmp.name + "/cache"
        import nova_versao_painel
        self.m = nova_versao_painel

    def tearDown(self):
        self.tmp.cleanup()

    def test_recusa_acao_e_consulta_fora_do_contrato(self):
        with self.assertRaises(ValueError):
            self.m.executar("rm -rf", {})
        with self.assertRaises(ValueError):
            self.m.executar("consultar", {"consulta": "x" * 301})
        with self.assertRaises(ValueError):
            self.m.executar("skills", {"consulta": "   "})

    def test_orcamento_recusa_fora_do_limite_e_registra_mudanca(self):
        with self.assertRaises(ValueError):
            self.m.executar("salvar_orcamento", {"orcamento": {"max_chamadas": -1}})
        with self.assertRaises(ValueError):
            self.m.executar("salvar_orcamento", {"orcamento": {"provedores": {"outro": True}}})
        r = self.m.executar("salvar_orcamento", {"orcamento": {"provedores": {"local": True, "gratuito": True},
                                                               "max_chamadas": 50}})
        self.assertTrue(r["resultado"]["mudou"])
        ledger = Path(os.environ["AGATA_NV_DIR"]) / "eventos" / "ledger.jsonl"
        ev = [json.loads(x) for x in ledger.read_text().splitlines()]
        self.assertEqual(ev[-1]["source"], "orcamento")
        self.assertEqual(ev[-1]["antes"]["provedores"]["gratuito"], False)
        self.assertEqual(ev[-1]["depois"]["provedores"]["gratuito"], True)

    def test_estado_sem_dados_diz_nao_medido(self):
        e = self.m.estado()
        self.assertEqual(e["corpo"]["saude"]["estado"], "não medido")
        self.assertIsNone(e["alexandria"]["indice"])
        self.assertEqual(e["orcamento"]["provedores"], {"local": True, "gratuito": False, "pago": False})

    def test_js_externo_e_sem_innerhtml(self):
        html = (HERE / "prototipo.html").read_text(encoding="utf-8")
        self.assertIn('<script src="nova_versao.js"></script>', html)
        js = (HERE / "nova_versao.js").read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", js)


if __name__ == "__main__":
    unittest.main()
