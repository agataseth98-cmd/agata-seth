import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(AQUI.parents[1] / "router"))
import posterior  # noqa: E402
import previo  # noqa: E402

NADA = lambda t: []  # noqa: E731


def msg(*textos):
    return {"messages": [{"role": "user" if i % 2 == 0 else "assistant", "content": t} for i, t in enumerate(textos)]}


class PrevioTests(unittest.TestCase):
    def test_marca_risco_privacidade_atualidade_e_problema(self):
        r = previo.classificar(msg("apague o log de hoje, o problema é meu e-mail a@b.c"), lambda t: [1] if "@" in t else [])
        self.assertEqual(r["risco"], "efeito")
        self.assertTrue(r["privado"])
        self.assertEqual(r["atualidade"], "volatil")
        self.assertIn("erro", r["problema_ambiguo"])
        self.assertTrue(any("só rota local" in e for e in r["estrategia"]))
        leitura = previo.classificar(msg("explique a regra 2"), NADA)
        self.assertEqual((leitura["risco"], leitura["atualidade"], leitura["problema_ambiguo"]), ("leitura", "estavel", None))

    def test_conta_o_limite_de_perguntas_combinado(self):
        r = previo.classificar(msg("você tem três perguntas", "ok", "primeira?", "r", "segunda?"), NADA)
        self.assertEqual(r["limite_interacao"], {"declarado": 3, "usadas": 2, "restantes": 1})


class PosteriorTests(unittest.TestCase):
    def test_estados_de_saida(self):
        self.assertEqual(posterior.classificar("ok", {}, achados=[])["estado"], "apto")
        self.assertEqual(posterior.classificar("custo não medido", {}, achados=[])["estado"], "parcial")
        self.assertEqual(posterior.classificar("x", {}, achados=["P-99 inexistente"])["estado"], "inconclusivo")
        self.assertEqual(posterior.classificar("x", {"risco": "efeito"}, achados=[])["estado"], "aguardando_humano")
        self.assertEqual(posterior.classificar("x", {"privado": True}, rota_remota=True, achados=[])["estado"], "bloqueado")


class SombraTests(unittest.TestCase):
    def test_sombra_nao_altera_o_pedido_e_nao_grava_texto(self):
        import sombra_nova_versao as s
        with tempfile.TemporaryDirectory() as t:
            os.environ["AGATA_NV_DIR"] = t
            os.environ["AGATA_NV_CACHE"] = t + "/c"
            payload = msg("mande o relatório-sigiloso-4471 hoje")
            antes = copy.deepcopy(payload)
            linha = s.observar(payload, "seth-livre", NADA)
            self.assertEqual(payload, antes)
            bruto = json.dumps(linha, ensure_ascii=False)
            self.assertNotIn("sigiloso", bruto)
            self.assertNotIn("relatório", bruto)
            self.assertEqual(linha["previo"]["risco"], "efeito")


if __name__ == "__main__":
    unittest.main()
