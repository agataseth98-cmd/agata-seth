"""C3, C4, C5, C8 e C9: o conteúdo do guia agata-fluxo (Ma'at).

C3 prova presença de cada um dos 11 pontos, não que o modelo os cumpre (lacuna L6).
C9 confere os ids de lição citados contra os ids definidos no próprio guia (decisão D8).
"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
FLUXO = RAIZ / ".agents/skills/agata-fluxo/SKILL.md"
# Adaptado em 14/11/2026: a consolidação de 12/11 (INDICE.md) juntou agata-processo-lote em agata-aplicar-proposta.
# A pasta agata-processo-lote não existe mais no main (ls .agents/skills), por isso ela sai desta lista.
SKILLS_DE_PROCESSO = ("agata-fluxo", "agata-aplicar-proposta", "agata-time-inovacao")

PONTOS_DE_LOTE = {
    "assinatura": r"assina",
    "worktree": r"worktree",
    "CI local": r"ci_sdd_local|CI LOCAL",
    "PR de proposta": r"PR de proposta",
    "mv no lugar de rm": r"\bmv\b",
    "rm proibido": r"\brm\b",
    "restauração": r"restaur",
    "delegação": r"delega|delegu",
    "cache": r"cache_conselho\.py ler",
    "decisão fora de arquivo": r"decis.*(registro|proposta)",
    "perguntas numeradas": r"numer",
    "verificador": r"auditoria_turno\.py --verificar",
}


def secao(texto, inicio):
    """Texto de uma seção de nível 2, do título que começa com `inicio` até o próximo '## '."""
    m = re.search(rf"^## {re.escape(inicio)}.*$", texto, re.M)
    if not m:
        return None
    resto = texto[m.end():]
    prox = re.search(r"^## ", resto, re.M)
    return resto[: prox.start()] if prox else resto


def blocos_de_codigo(texto):
    return re.findall(r"```[a-z]*\n(.*?)```", texto, re.S)


class FluxoRegrasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texto = FLUXO.read_text(encoding="utf-8")

    def test_fluxo_resume_as_regras_de_lote(self):
        # C3: o resumo tem 11 pontos e cada ponto aparece.
        resumo = secao(self.texto, "Regras de lote (resumo")
        self.assertIsNotNone(resumo, "o guia não tem a seção 'Regras de lote (resumo'")
        pontos = [l for l in resumo.splitlines() if l.startswith("- ")]
        self.assertEqual(len(pontos), 11, f"o resumo deveria ter 11 pontos, tem {len(pontos)}")
        faltam = [nome for nome, rx in PONTOS_DE_LOTE.items() if not re.search(rx, resumo, re.I)]
        self.assertFalse(faltam, f"pontos de lote ausentes no resumo: {faltam}")

    def test_fluxo_sem_restauracao_ou_remocao_sem_ordem(self):
        # C4: nenhum bloco de comando remove ou restaura sem ordem.
        blocos = blocos_de_codigo(self.texto)
        self.assertGreaterEqual(len(blocos), 2, "o guia deveria ter os blocos de comando da seção 8")
        proibidos = [r"\brm\b", r"checkout\s+--", r"reset\s+--hard", r"clean\s+-\w*f"]
        achados = [(rx, b.strip().splitlines()[0]) for b in blocos for rx in proibidos if re.search(rx, b)]
        self.assertFalse(achados, f"bloco de comando com remoção ou restauração sem ordem: {achados}")

    def test_fluxo_nao_afirma_o_que_a_seth_nao_mostrou(self):
        # C5: a seção 6 não afirma que a Seth carrega a skill; diz o que foi medido e o que não foi.
        sec6 = secao(self.texto, "6. Seth")
        self.assertIsNotNone(sec6, "o guia não tem a seção '6. Seth'")
        self.assertFalse(re.search(r"carrega\s+(esta|a)\s+skill|pela hidrata", sec6),
                         "a seção 6 ainda afirma que a Seth carrega a skill pela hidratação")
        self.assertIn("não medido", sec6, "a seção 6 precisa marcar o que não foi medido")
        self.assertIn("SETH_SKILLS_SUGERE", sec6, "a seção 6 deve citar o que o código mostra (sugestão desligada)")

    def test_skills_de_processo_passam_no_lint(self):
        # C8: o lint de skill (qualidade_llm.py) não aponta problema nas skills de processo.
        saida = subprocess.run([sys.executable, "-I", "redesign/painel_operacional/qualidade_llm.py"],
                               cwd=RAIZ, capture_output=True, text=True)
        self.assertEqual(saida.returncode, 0, f"lint falhou: {saida.stderr.strip()[-300:]}")
        skills = {s["skill"]: s for s in json.loads(saida.stdout)["skills"]}
        for nome in SKILLS_DE_PROCESSO:
            self.assertIn(nome, skills, f"o lint não viu a skill {nome}")
            self.assertEqual(skills[nome]["problemas"], [], f"{nome} tem problema no lint")

    def test_ids_do_resumo_existem_na_skill(self):
        # C9: cada id de lição citado no resumo está definido no próprio guia (D8, aceita).
        resumo = secao(self.texto, "Regras de lote (resumo")
        self.assertIsNotNone(resumo, "o guia não tem a seção 'Regras de lote (resumo'")
        citados = set()
        for m in re.finditer(r"lições? ([a-z])(?: e ([a-z]))?\b", resumo):
            citados.update(g for g in m.groups() if g)
        self.assertTrue(citados, "o resumo não cita nenhuma lição")
        definidos = set(re.findall(r"^- \*\*([a-z])\.\*\*", secao(self.texto, "Lições citadas") or "", re.M))
        faltam = sorted(citados - definidos)
        self.assertFalse(faltam, f"ids citados no resumo sem item na skill: {faltam}")


if __name__ == "__main__":
    unittest.main()
