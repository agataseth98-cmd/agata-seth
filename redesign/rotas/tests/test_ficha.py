import json
import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import ficha  # noqa: E402

BASE = {"id": "x", "provedor": "p", "modelo": "m", "categoria": "gratuito", "classes_permitidas": ["publico"],
        "treina_com_prompts": "nao", "cota": "c", "compartilhada_com_seth": False, "cota_medida": True,
        "conferida_em": "2026-11-06", "fonte": "f"}


def rota(**kw):
    r = dict(BASE); r.update(kw); return r


class FichaTests(unittest.TestCase):
    def test_dado_pessoal_fora_de_rota_local_e_erro(self):
        erros, _ = ficha.verificar({"rotas": [rota(classes_permitidas=["pessoal"])]})
        self.assertTrue(any("D2" in e for e in erros))

    def test_dado_pessoal_em_rota_local_passa(self):
        erros, _ = ficha.verificar({"rotas": [rota(categoria="local", classes_permitidas=["pessoal"])]})
        self.assertEqual(erros, [])

    def test_segredo_nunca_passa_em_rota_nenhuma(self):
        erros, _ = ficha.verificar({"rotas": [rota(categoria="local", classes_permitidas=["segredo"])]})
        self.assertTrue(any("segredo" in e for e in erros))

    def test_cota_compartilhada_sem_teto_gera_aviso_d3(self):
        _, avisos = ficha.verificar({"rotas": [rota(compartilhada_com_seth=True)]})
        self.assertTrue(any("D3" in a for a in avisos))

    def test_campo_ausente_e_erro(self):
        r = rota(); del r["cota"]
        erros, _ = ficha.verificar({"rotas": [r]})
        self.assertTrue(any("cota" in e for e in erros))

    def test_ficha_do_repositorio_e_valida(self):
        caminho = AQUI.parents[2] / "config" / "rotas-ficha.json"
        erros, _ = ficha.verificar(json.loads(caminho.read_text(encoding="utf-8")))
        self.assertEqual(erros, [])


if __name__ == "__main__":
    unittest.main()
