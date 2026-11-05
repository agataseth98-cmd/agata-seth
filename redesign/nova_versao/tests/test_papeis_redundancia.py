import sys
import tempfile
import time
import unittest
from pathlib import Path
import os

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import orcamento_turno  # noqa: E402
import papeis  # noqa: E402
import redundancia  # noqa: E402

ROTAS = [
    {"rota": "ollama-local/a", "categoria": "local", "independencia": {"familia": "qwen"}},
    {"rota": "ollama-local/b", "categoria": "local", "independencia": {"familia": "lfm3"}},
    {"rota": "claude:cli", "categoria": "assinatura", "independencia": {"familia": "claude"}},
]
APROVADAS = {"conversa": ["ollama-local/a", "ollama-local/b", "claude:cli"], "formato": ["ollama-local/a", "claude:cli"],
             "codigo": []}


class PapeisTests(unittest.TestCase):
    def test_configuracao_versionada_e_valida(self):
        p = papeis.carregar()
        self.assertEqual(p["revisor"]["independente_de"], "sintetizador")
        self.assertEqual(set(p), {"classificador", "recuperador", "sintetizador", "revisor", "suporte"})

    def test_revisor_e_de_familia_diferente_do_sintetizador(self):
        esc = {"sintetizador": {"rota": "claude:cli", "independencia": {"familia": "claude"}}}
        r = papeis.resolver("revisor", ROTAS, APROVADAS, escolhidas=esc)
        self.assertNotEqual(papeis.familia(r), "claude")
        self.assertIsNotNone(r)

    def test_papel_sem_capacidade_provada_nao_recebe_rota(self):
        self.assertIsNone(papeis.resolver("classificador", [ROTAS[1]], {"formato": []}))   # lfm3 não passou em formato

    def test_config_com_capacidade_sem_prova_e_recusada(self):
        import json
        d = Path(tempfile.mkdtemp()) / "p.json"
        d.write_text(json.dumps({"papeis": {"x": {"nivel": "leve", "capacidades": ["voar"], "categorias": ["local"],
                                                  "independente_de": None}}}), encoding="utf-8")
        with self.assertRaises(ValueError):
            papeis.carregar(d)


class RedundanciaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = str(Path(self.tmp.name) / "dados")

    def tearDown(self):
        self.tmp.cleanup()

    def test_escolhe_so_rota_aprovada(self):
        self.assertEqual(redundancia.escolher_rota("formato", ROTAS, APROVADAS)["rota"], "claude:cli")
        self.assertIsNone(redundancia.escolher_rota("codigo", ROTAS, APROVADAS))

    def test_ensaio_de_retorno_usa_alternativa_quando_a_principal_cai(self):
        def chamar(rota, prompt):
            return {"ok": True}
        r = redundancia.ensaio_retorno("conversa", ROTAS, APROVADAS, chamar)
        self.assertEqual(r["principal"], "claude:cli")           # primeira aprovada em ordem alfabética
        self.assertEqual(r["alternativa"], "ollama-local/a")
        self.assertEqual(r["estado"], "retorno_ok")
        self.assertNotEqual(r["alternativa"], r["principal"])

    def test_sem_alternativa_e_dito(self):
        r = redundancia.ensaio_retorno("formato", [ROTAS[0]], {"formato": ["ollama-local/a"]}, lambda rota, p: {"ok": True})
        self.assertEqual(r["estado"], "sem_alternativa")


class OrcamentoTurnoTests(unittest.TestCase):
    def test_esgota_por_rodadas_chamadas_e_prazo(self):
        ini = time.monotonic()
        self.assertFalse(orcamento_turno.estado(rodadas=1, chamadas=1, inicio_monotonic=ini, max_chamadas=10, prazo_s=60)["esgotado"])
        self.assertTrue(orcamento_turno.estado(rodadas=6, chamadas=1, inicio_monotonic=ini, max_chamadas=10, prazo_s=60)["esgotado"])
        self.assertTrue(orcamento_turno.estado(rodadas=1, chamadas=10, inicio_monotonic=ini, max_chamadas=10, prazo_s=60)["esgotado"])
        self.assertTrue(orcamento_turno.estado(rodadas=1, chamadas=1, inicio_monotonic=ini - 100, max_chamadas=10, prazo_s=60)["esgotado"])


if __name__ == "__main__":
    unittest.main()
