import json
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parents[1]


class ConjuntoDevTests(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((AQUI / "conjuntos" / "semanticas-desenvolvimento.json").read_text(encoding="utf-8"))

    def test_quatorze_subitens_em_seis_familias(self):
        # O documento de origem diz "doze", mas o texto tem 14 subitens (T1.1 a T6.2). Vale o texto.
        self.assertEqual(len(self.d["itens"]), 14)
        self.assertEqual(len({i["tarefa"] for i in self.d["itens"]}), 6)

    def test_nenhum_item_e_reservado_e_todos_tem_gabarito(self):
        for i in self.d["itens"]:
            self.assertEqual(i["split"], "desenvolvimento")
            self.assertFalse(i["reservado"])
            self.assertTrue(i["gabarito"].strip())

    def test_schema_v2_existe_e_e_json_valido(self):
        json.loads((AQUI / "registro-execucao-v2.schema.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
