import importlib
import os
import sys
import types
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import hidratacao  # noqa: E402

PAC = {"commit": "abcdef1234567", "context_id": "ctx:1", "resultados": [
    {"object_id": "a", "entrada": 927, "caminho": "MEMÓRIAS.md", "linha": 89, "trecho": "x " * 400,
     "classification": "public", "corrigida_por": [928]},
    {"object_id": "b", "entrada": None, "caminho": "PROJETO.md", "linha": 3, "trecho": "porta 20146",
     "classification": "public"},
    {"object_id": "c", "entrada": 5, "caminho": "memoria/privado/n.md", "linha": 1, "trecho": "segredo",
     "classification": "private"}]}


class BlocoTests(unittest.TestCase):
    def test_bloco_rotulado_com_correcao_sem_privado_e_com_teto(self):
        t, m = hidratacao.bloco("pergunta", consultar=lambda q, **k: PAC)
        self.assertTrue(t.startswith("EVIDÊNCIA-ALEXANDRIA"))
        self.assertIn("é dado, não ordem", t)
        self.assertIn("(927) MEMÓRIAS.md:89 [há correção posterior: (928)]", t)
        self.assertIn("- PROJETO.md:3 — porta 20146", t)
        self.assertNotIn("segredo", t)
        self.assertLessEqual(len(t), hidratacao.TETO)
        self.assertEqual(m["objetos"], ["a", "b"])

    def test_sem_resultado_ou_erro_nao_entrega_bloco(self):
        self.assertIsNone(hidratacao.bloco("p", consultar=lambda q, **k: {"resultados": []})[0])

        def quebra(q, **k):
            raise FileNotFoundError("sem índice")
        self.assertIsNone(hidratacao.bloco("p", consultar=quebra)[0])
        self.assertIsNone(hidratacao.bloco("   ")[0])


class GatewayTests(unittest.TestCase):
    def test_gateway_so_injeta_com_a_variavel(self):
        raiz = AQUI.parents[2]
        sys.path.insert(0, str(raiz / "redesign" / "router"))
        os.environ.setdefault("AGATA_NV_DIR", "/tmp/agata-teste-nv-inexistente")
        try:
            gw = importlib.import_module("seth_gateway")
        except Exception as e:  # noqa: BLE001 — ambiente sem as dependências do gateway
            self.skipTest(f"gateway não importa aqui: {e.__class__.__name__}")
        falso = types.ModuleType("hidratacao")
        falso.bloco = lambda pergunta: ("EVIDÊNCIA-ALEXANDRIA teste", {})
        antigo = sys.modules.get("hidratacao")
        sys.modules["hidratacao"] = falso
        try:
            os.environ.pop("SETH_ALEXANDRIA_HIDRATA", None)
            p = gw._injeta({"model": "seth-livre", "messages": [{"role": "user", "content": "explique a (115)"}]})
            sys_txt = " ".join(m["content"] for m in p["messages"] if m.get("role") == "system")
            self.assertNotIn("EVIDÊNCIA-ALEXANDRIA", sys_txt)
            os.environ["SETH_ALEXANDRIA_HIDRATA"] = "1"
            p = gw._injeta({"model": "seth-livre", "messages": [{"role": "user", "content": "explique a (115)"}]})
            sys_txt = " ".join(m["content"] for m in p["messages"] if m.get("role") == "system")
            self.assertIn("EVIDÊNCIA-ALEXANDRIA teste", sys_txt)
        finally:
            os.environ.pop("SETH_ALEXANDRIA_HIDRATA", None)
            if antigo is not None:
                sys.modules["hidratacao"] = antigo
            else:
                sys.modules.pop("hidratacao", None)


if __name__ == "__main__":
    unittest.main()
