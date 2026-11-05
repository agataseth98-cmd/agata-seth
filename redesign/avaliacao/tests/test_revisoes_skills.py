import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import recuperacao  # noqa: E402
import registro  # noqa: E402
import revisoes  # noqa: E402
import conjunto  # noqa: E402


class RevisoesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = str(Path(self.tmp.name) / "dados")
        self.run = registro.abrir("avaliar", "dev", "sha256:x")
        registro.linha(self.run, task_id="rec-01", condition="alexandria", model_id="m", outcome="passou",
                       rota="ollama-local/m", resposta="resposta A")
        registro.linha(self.run, task_id="rec-01", condition="busca_texto", model_id="m", outcome="falhou",
                       rota="ollama-local/m", resposta="resposta B")

    def tearDown(self):
        self.tmp.cleanup()

    def test_cegas_nao_revela_condicao_nem_rota(self):
        c = revisoes.cegas(self.run["run_id"])
        bruto = json.dumps(c, ensure_ascii=False)
        self.assertNotIn("alexandria", bruto)
        self.assertNotIn("busca_texto", bruto)
        self.assertNotIn("ollama-local", bruto)
        self.assertEqual(len(c), 2)

    def test_revelar_so_depois_de_tudo_revisado(self):
        rot = [x["rotulo"] for x in revisoes.cegas(self.run["run_id"])]
        revisoes.registrar(self.run["run_id"], rot[0], "ok", "Humano")
        with self.assertRaises(PermissionError):
            revisoes.revelar(self.run["run_id"])
        revisoes.registrar(self.run["run_id"], rot[1], "falhou", "Humano")
        mapa = revisoes.revelar(self.run["run_id"])
        self.assertEqual({v["condicao"] for v in mapa.values()}, {"alexandria", "busca_texto"})
        self.assertEqual(revisoes.resumo(self.run["run_id"])["taxa_ok"], 0.5)

    def test_rotulo_estranho_e_veredito_fora_da_lista_recusados(self):
        with self.assertRaises(ValueError):
            revisoes.registrar(self.run["run_id"], "R00000000", "ok", "Humano")
        rot = revisoes.cegas(self.run["run_id"])[0]["rotulo"]
        with self.assertRaises(ValueError):
            revisoes.registrar(self.run["run_id"], rot, "talvez", "Humano")
        with self.assertRaises(ValueError):
            revisoes.registrar("../fora", rot, "ok", "Humano")


class SkillsTests(unittest.TestCase):
    def test_omissao_falso_positivo_e_sucesso(self):
        tarefas = [{"task_id": "s1", "consulta": "a", "skill": {"esperadas": ["x"], "proibidas": ["y"]}},
                   {"task_id": "s2", "consulta": "b", "skill": {"esperadas": ["z"], "proibidas": ["w"]}}]
        escolhas = {"a": ["x"], "b": ["w", "z"]}
        r = recuperacao.rodar_skills(tarefas, selecionar=lambda q: {"candidatos": [{"nome": n} for n in escolhas[q]]})
        self.assertEqual(r["n"], 2)
        self.assertEqual(r["omissao"], 0.0)
        self.assertEqual(r["falso_positivo"], 0.5)
        self.assertEqual(r["sucesso"], 0.5)

    def test_denominador_zero_da_null(self):
        tarefas = [{"task_id": "s1", "consulta": "a", "skill": {"esperadas": [], "proibidas": []}}]
        r = recuperacao.rodar_skills(tarefas, selecionar=lambda q: {"candidatos": []})
        self.assertIsNone(r["omissao"])
        self.assertIsNone(r["falso_positivo"])


if __name__ == "__main__":
    unittest.main()
