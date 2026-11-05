import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import acervo  # noqa: E402
import hidratacao  # noqa: E402


def pac(ps, trechos, corr=None):
    rs = [{"trecho": t, "corrigida_por": corr} if corr else {"trecho": t} for t in trechos]
    return {"palavras": ps, "resultados": rs}


class SuficienciaTests(unittest.TestCase):
    def test_cobertura_alta_e_suficiente(self):
        s = acervo.suficiencia(pac(["porta", "painel", "20146"], ["O painel roda na porta 20146."]))
        self.assertTrue(s["suficiente"])
        self.assertEqual(s["cobertura"], 1.0)
        self.assertEqual(s["lacunas"], [])

    def test_cobertura_baixa_pede_externa(self):
        s = acervo.suficiencia(pac(["preco", "plano", "pro", "mes"], ["O painel roda na porta 20146."]))
        self.assertFalse(s["suficiente"])
        self.assertTrue(s["precisa_externa"])
        self.assertIn("pro", s["lacunas"])

    def test_volatil_nunca_basta_so_com_o_acervo(self):
        s = acervo.suficiencia(pac(["versao", "modelo"], ["modelo versao 2 de 2024"]), volatil=True)
        self.assertTrue(s["precisa_externa"])
        self.assertIn("atualidade", s["motivo"])

    def test_sem_resultado_ou_sem_palavras(self):
        self.assertTrue(acervo.suficiencia(pac(["porta"], []))["precisa_externa"])
        self.assertIsNone(acervo.suficiencia(pac([], []))["cobertura"])

    def test_correcao_vai_como_lacuna_de_atualidade_sem_bloquear(self):
        s = acervo.suficiencia(pac(["porta", "painel"], ["porta do painel 20146"], corr=[928]))
        self.assertTrue(s["suficiente"])
        self.assertIn("correção posterior", s["motivo"])

    def test_bloco_de_hidratacao_avisa_quando_local_nao_basta(self):
        def consulta(q, **k):
            return {"commit": "abc", "context_id": "ctx:x", "palavras": ["hoje", "noticia"],
                    "resultados": [{"object_id": "alex:entrada:5@MEMÓRIAS.md", "entrada": 5, "caminho": "MEMÓRIAS.md", "linha": 3, "trecho": "algo antigo"}],
                    "suficiencia": {"precisa_externa": True, "motivo": "pergunta pede atualidade"}}
        t, _ = hidratacao.bloco("hoje qual a noticia", consultar=consulta)
        self.assertIn("pesquisa externa indicada", t)
        self.assertIn("pergunta pede atualidade", t)


if __name__ == "__main__":
    unittest.main()
