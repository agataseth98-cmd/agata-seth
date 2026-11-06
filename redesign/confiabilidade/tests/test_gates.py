#!/usr/bin/env python3
"""Testes dos seis gates de confiabilidade (P4). Exige pass em todos e limiar 'não definido (D10)'."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gates  # noqa: E402

NOMES_ESPERADOS = [
    "regras_autoridade",
    "escopo_ferramentas",
    "qualidade",
    "robustez_recuperacao",
    "rastreabilidade",
    "repeticao",
]


class TestGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.itens = gates.rodar()

    def test_seis_gates_na_ordem(self):
        self.assertEqual([i["gate"] for i in self.itens], NOMES_ESPERADOS)

    def test_todos_pass(self):
        for item in self.itens:
            with self.subTest(gate=item["gate"]):
                self.assertEqual(item["resultado"], "pass", msg=item["evidencia"])

    def test_limiar_nao_definido_d10(self):
        for item in self.itens:
            with self.subTest(gate=item["gate"]):
                self.assertIn("limiar", item)
                self.assertEqual(item["limiar"], "não definido (D10)")


if __name__ == "__main__":
    unittest.main()
