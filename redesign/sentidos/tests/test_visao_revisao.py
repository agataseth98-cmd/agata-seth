import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(AQUI.parents[1] / "metacognicao"))
import visao  # noqa: E402
import revisao_suporte as rs  # noqa: E402


class VisaoTests(unittest.TestCase):
    def test_descreve_com_chamada_injetada(self):
        r = visao.descrever(b"\x89PNG", chamar=lambda p, img: "um quadrado vermelho")
        self.assertTrue(r["ok"])
        self.assertEqual(r["texto"], "um quadrado vermelho")

    def test_falha_vira_estado_e_imagem_vazia_e_recusada(self):
        def cai(p, img):
            raise ConnectionError("sem modelo")
        r = visao.descrever(b"x", chamar=cai)
        self.assertFalse(r["ok"])
        self.assertEqual(r["falha"], "ConnectionError")
        with self.assertRaises(ValueError):
            visao.descrever(b"")


class RevisaoSuporteTests(unittest.TestCase):
    FONTES = [{"id": "d1", "texto": "O painel roda na porta 20146."}]

    def test_mecanico_pega_citacao_inventada_e_numero_sem_fonte(self):
        r = rs.mecanico("O painel roda na porta 20146 [d9] e tem 300 entradas.", self.FONTES)
        self.assertEqual(r["estado"], "inconsistente")
        self.assertIn("d9", r["citacoes_inexistentes"])
        self.assertIn("300", r["numeros_sem_suporte"])
        ok = rs.mecanico("O painel roda na porta 20146 [d1].", self.FONTES)
        self.assertEqual(ok["estado"], "ok")

    def test_plano_proporcional_ao_risco(self):
        self.assertEqual(rs.plano()["revisores"], 0)
        self.assertEqual(rs.plano(citacao=True)["revisores"], 1)
        self.assertEqual(rs.plano(risco="efeito")["revisores"], 1)
        self.assertEqual(rs.plano(nao_verificavel=True)["revisores"], 3)

    def test_revisor_ve_so_o_par_e_divergencia_vira_inconclusivo(self):
        prompts = []

        def revisor(prompt):
            prompts.append(prompt)
            return "SUSTENTA"
        r = rs.revisar("a porta é 20146", "porta 20146", revisor, passes=1)
        self.assertEqual(r["veredito"], "sustenta")
        self.assertIn("AFIRMAÇÃO", prompts[0])
        self.assertNotIn("CONVERSA", prompts[0].upper())
        respostas = iter(["SUSTENTA", "NAO_SUSTENTA", "SUSTENTA"])
        self.assertEqual(rs.revisar("x", "y", lambda p: next(respostas), passes=3)["veredito"], "inconclusivo")


if __name__ == "__main__":
    unittest.main()
