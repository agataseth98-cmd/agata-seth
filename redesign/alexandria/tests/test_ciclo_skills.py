import os
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import ciclo_skills as cs  # noqa: E402


class CicloSkillsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = str(Path(self.tmp.name) / "dados")

    def tearDown(self):
        self.tmp.cleanup()

    def rascunho(self, nome="hortas-urbanas"):
        return cs.rascunhar(nome, "Hortas urbanas", "Orienta o plantio em espaços pequenos, com fontes declaradas.",
                            ["quando o pedido falar de horta"], ["fonte-a", "fonte-b"])

    def test_rascunho_exige_fontes_e_nome_valido(self):
        with self.assertRaises(ValueError):
            cs.rascunhar("x-y", "T", "d", [], [])
        with self.assertRaises(ValueError):
            cs.rascunhar("Nome Ruim", "T", "d", [], ["f"])
        with self.assertRaises(ValueError):
            cs.rascunhar("../fora", "T", "d", [], ["f"])
        self.assertEqual(self.rascunho()["estado"], "rascunho")

    def test_so_o_humano_passa_de_quarentena_em_diante(self):
        self.rascunho()
        cs.transicionar("hortas-urbanas", "quarentena", "maquina", "entrou")
        with self.assertRaises(ValueError):
            cs.transicionar("hortas-urbanas", "em-teste", "maquina", "x")
        cs.transicionar("hortas-urbanas", "em-teste", "humano", "vou testar")
        with self.assertRaises(ValueError):                                # elegível exige evidência escrita
            cs.transicionar("hortas-urbanas", "elegivel", "humano", "ok")
        cs.transicionar("hortas-urbanas", "elegivel", "humano", "ok", evidencia="passou nos 3 casos de teste")
        self.assertEqual(cs.ler("hortas-urbanas")["estado"], "elegivel")

    def test_revogada_e_terminal_e_some_da_sugestao(self):
        self.rascunho()
        cs.transicionar("hortas-urbanas", "quarentena", "maquina", "x")
        cs.transicionar("hortas-urbanas", "revogada", "humano", "retirada")
        self.assertIn("hortas-urbanas", cs.revogadas())
        with self.assertRaises(ValueError):
            cs.transicionar("hortas-urbanas", "em-teste", "humano", "volta")
        with self.assertRaises(ValueError):
            cs.registrar_uso("hortas-urbanas", "selecionada")

    def test_uso_compara_hash_lido_e_diff_so_para_elegivel(self):
        r = self.rascunho()
        self.assertFalse(cs.registrar_uso("hortas-urbanas", "lida", sha_lido=r["sha256"])["mudou_desde_o_hash"])
        self.assertTrue(cs.registrar_uso("hortas-urbanas", "lida", sha_lido="0" * 64)["mudou_desde_o_hash"])
        with self.assertRaises(ValueError):
            cs.gerar_diff_p8("hortas-urbanas")                              # ainda não é elegível
        cs.transicionar("hortas-urbanas", "quarentena", "maquina", "x")
        cs.transicionar("hortas-urbanas", "em-teste", "humano", "x")
        cs.transicionar("hortas-urbanas", "elegivel", "humano", "ok", evidencia="passou")
        arq = cs.gerar_diff_p8("hortas-urbanas")
        texto = arq.read_text(encoding="utf-8")
        self.assertIn("b/.agents/skills/hortas-urbanas/SKILL.md", texto)
        self.assertIn("+name: hortas-urbanas", texto)

    def test_selecao_nao_sugere_revogada(self):
        import subprocess
        import skills  # noqa: E402
        import acervo  # noqa: E402
        repo = Path(self.tmp.name) / "repo"
        (repo / ".agents" / "skills" / "foo-bar").mkdir(parents=True)
        (repo / ".agents" / "skills" / "foo-bar" / "SKILL.md").write_text(
            "---\nname: foo-bar\ndescription: aplicar proposta assinada no repositório\n---\ncorpo\n", encoding="utf-8")
        (repo / "M.md").write_text("(1) DIÁRIO — x\n", encoding="utf-8")
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run([*g, "-C", str(repo), "add", "-A"], check=True)
        subprocess.run([*g, "-C", str(repo), "commit", "-qm", "x"], check=True)
        acervo.iniciar()
        acervo.indexar(acervo.snapshot("HEAD", repo))
        antes = [c["nome"] for c in skills.selecionar("foo-bar proposta", n=5)["candidatos"]]
        self.assertIn("foo-bar", antes)
        cs.rascunhar("foo-bar", "Foo bar", "procedimento de teste para a sugestão", ["teste"], ["f"])
        cs.transicionar("foo-bar", "quarentena", "maquina", "x")
        cs.transicionar("foo-bar", "revogada", "humano", "retirada da sugestão")
        depois = [c["nome"] for c in skills.selecionar("foo-bar proposta", n=5)["candidatos"]]
        self.assertNotIn("foo-bar", depois)


if __name__ == "__main__":
    unittest.main()
