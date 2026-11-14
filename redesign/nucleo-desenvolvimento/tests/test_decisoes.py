"""Decisões do Humano de 07/11/2026 que a proposta registra (D3, D4, D7, D10) e o estado da decisão.

D3 foi revisada pelo Humano em 14/11/2026 para o guia: teto de 24 KiB (antes 8 KiB). O ponteiro do AGENTS.md
(200 bytes) e a linha do gateway (200 caracteres) continuam como estavam.

Não é critério da spec (C1 a C11); são as decisões escritas no guia e na spec, para que a proposta não as perca.
"""
import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
AGENTS = RAIZ / "AGENTS.md"
FLUXO = RAIZ / ".agents/skills/agata-fluxo/SKILL.md"
COMPONENTE = RAIZ / "redesign/nucleo-desenvolvimento"
DECISION = COMPONENTE / "spec/decision.md"
SPEC = COMPONENTE / "spec/spec.md"
PONTEIRO = "agata-fluxo/SKILL.md"


class DecisoesTests(unittest.TestCase):
    def test_decision_aceita(self):
        # gate de spec: "DECISAO: aceita" (redesign/sdd_flow/spec_gate.py)
        self.assertIn("DECISAO: aceita", DECISION.read_text(encoding="utf-8"))

    def test_d3_ponteiro_do_agents_ate_200_bytes(self):
        linha = [l for l in AGENTS.read_text(encoding="utf-8").splitlines() if PONTEIRO in l]
        self.assertEqual(len(linha), 1, "AGENTS.md precisa de exatamente uma linha de ponteiro")
        self.assertLessEqual(len(linha[0].encode("utf-8")), 200,
                             f"ponteiro do AGENTS.md com {len(linha[0].encode('utf-8'))} bytes")

    def test_d3_guia_ate_24_kib_decisao_14_11(self):
        # Revisado pelo Humano em 14/11/2026 ("refazer v2, manter o agata-fluxo consolidado; D3 do guia revogada"):
        # o teto do guia era 8 KiB (07/11) e passa a 24 KiB. O guia consolidado do main já tem ~12 KB.
        tamanho = len(FLUXO.read_bytes())
        self.assertLessEqual(tamanho, 24 * 1024, f"agata-fluxo com {tamanho} bytes (limite 24 KiB)")

    def test_d3_revisao_14_11_registrada_na_decisao(self):
        texto = DECISION.read_text(encoding="utf-8")
        self.assertIn("14/11/2026", texto, "a revisão da D3 de 14/11 não está em decision.md")
        self.assertIn("24 KiB", texto, "o novo teto do guia (24 KiB) não está em decision.md")
        self.assertIn("D3 do guia revogada", texto, "decision.md não diz que a D3 do guia foi revogada")

    def test_d4_dono_e_revisor_do_guia(self):
        texto = FLUXO.read_text(encoding="utf-8")
        self.assertRegex(texto, r"Dono deste guia: agata-spec")
        self.assertRegex(texto, r"Revisor: agata-revisor")
        self.assertIn("Dono e revisor", DECISION.read_text(encoding="utf-8"))
        self.assertTrue((RAIZ / ".claude/agents/agata-spec.md").is_file(), "agente agata-spec não existe")
        self.assertTrue((RAIZ / ".claude/agents/agata-revisor.md").is_file(), "agente agata-revisor não existe")

    def test_d7_regra_de_memorias_no_guia_e_no_registro(self):
        texto = FLUXO.read_text(encoding="utf-8")
        for trecho in ("timer do cache", "assinatura do Humano", "medição do sistema"):
            self.assertIn(trecho, texto, f"D7: falta '{trecho}' no guia")
        self.assertIn("D7", DECISION.read_text(encoding="utf-8"))
        self.assertIn("timer do cache", DECISION.read_text(encoding="utf-8"))

    def test_d10_nomes_no_guia_e_na_spec(self):
        for arq in (FLUXO, SPEC):
            texto = arq.read_text(encoding="utf-8")
            for nome in ("Ma'at", "Ptah", "Thoth"):
                self.assertIn(nome, texto, f"D10: falta o nome {nome} em {arq.name}")
        self.assertTrue(re.search(r"Thoth.*escrita e registro|escrita e registro.*Thoth", SPEC.read_text(encoding="utf-8"), re.S))


if __name__ == "__main__":
    unittest.main()
