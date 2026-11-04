import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import eventos  # noqa: E402
import orcamento  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()


class EventosTests(Base):
    def test_chave_idempotente_nao_grava_duas_vezes(self):
        a = eventos.registrar("execution", "ok", "x", chave="k1")
        b = eventos.registrar("execution", "ok", "x", chave="k1")
        self.assertEqual(a["id"], b["id"])
        self.assertTrue(b.get("repetido"))
        self.assertEqual(len(eventos.ultimos(100)), 1)

    def test_escritas_concorrentes_preservam_a_cadeia(self):
        ts = [threading.Thread(target=eventos.registrar, args=("observation", "ok", f"t{i}")) for i in range(20)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(len(eventos.ultimos(100)), 20)
        self.assertTrue(eventos.verificar())

    def test_transicao_recusa_salto_e_remocao_sem_autorizacao(self):
        eventos.transicao("obj", None, "apresentacao", "pergunta definida")
        eventos.transicao("obj", "apresentacao", "compreensao", "fontes descritas")
        with self.assertRaises(ValueError):
            eventos.transicao("obj", "compreensao", "transicao", "pulou")
        with self.assertRaises(ValueError):
            eventos.transicao("obj", "transicao", "remocao", "sem ok")
        ev = eventos.transicao("obj", "transicao", "remocao", "alvo exato", autorizacao="Humano 04/11")
        self.assertEqual(ev["estado_seguinte"], "remocao")


class OrcamentoTests(Base):
    def test_padrao_so_local_e_pago_sem_teto_nao_gasta(self):
        o = orcamento.ler()
        self.assertEqual(o["provedores"], {"local": True, "gratuito": False, "pago": False})
        self.assertFalse(orcamento.permite("gratuito")[0])
        orcamento.salvar({**o, "provedores": {"local": True, "gratuito": False, "pago": True}})
        ok, motivo = orcamento.permite("pago")
        self.assertFalse(ok)
        self.assertIn("teto", motivo)
        self.assertTrue(orcamento.permite("local")[0])
        self.assertFalse(orcamento.permite("local", chamadas_ja=10**6)[0])


if __name__ == "__main__":
    unittest.main()
