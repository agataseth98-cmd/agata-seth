import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import acervo  # noqa: E402
import cadastro  # noqa: E402

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
SHA = "ab" * 32


class CadastroTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        os.environ["AGATA_NV_DIR"] = str(t / "dados")
        os.environ["AGATA_NV_CACHE"] = str(t / "cache")

    def tearDown(self):
        self.tmp.cleanup()

    def test_criar_e_idempotente_e_guarda_so_origem_limpa(self):
        a = cadastro.criar(SHA, "md", "Nota  de\nteste", origem_uri="https://ex.test/a?token=SEGREDO#x", tamanho=10)
        b = cadastro.criar(SHA, "md", "outro nome")
        self.assertEqual(a["object_id"], "ext:" + SHA)
        self.assertEqual(b["rotulo"], a["rotulo"])                    # o segundo pedido devolve o existente
        self.assertEqual(a["origem_uri"], "https://ex.test/a")         # sem query nem fragmento
        self.assertNotIn("SEGREDO", (cadastro.pasta() / f"ext:{SHA}.json").read_text(encoding="utf-8"))
        self.assertEqual(oct((cadastro.pasta() / f"ext:{SHA}.json").stat().st_mode)[-3:], "600")

    def test_uri_sem_http_ou_com_credencial_e_recusada_ou_limpa(self):
        with self.assertRaises(ValueError):
            cadastro.sanear_uri("file:///etc/passwd")
        self.assertEqual(cadastro.sanear_uri("https://user:senha@ex.test/x"), "https://ex.test/x")

    def test_sha_que_nao_e_hex_nao_vira_caminho(self):
        with self.assertRaises(ValueError):
            cadastro.criar("../" + "a" * 61, "md", "x")
        with self.assertRaises(ValueError):
            cadastro.ler("../../etc")

    def test_transicoes_automaticas_e_as_do_humano(self):
        cadastro.criar(SHA, "md", "n")
        cadastro.transicionar(SHA, "quarentena", "maquina", "parse ok")
        cadastro.transicionar(SHA, "catalogado", "maquina", "sem sinais")
        with self.assertRaises(ValueError):                              # catalogado -> revisado é só do Humano
            cadastro.transicionar(SHA, "revisado", "maquina", "x")
        with self.assertRaises(ValueError):                              # e sem direitos decididos não revisa
            cadastro.transicionar(SHA, "revisado", "humano", "x")
        with self.assertRaises(ValueError):                              # direitos: só o Humano, com evidência
            cadastro.definir_direitos(SHA, "livre", "CC-BY no site", "maquina")
        with self.assertRaises(ValueError):
            cadastro.definir_direitos(SHA, "livre", "  ", "humano")
        cadastro.definir_direitos(SHA, "livre", "CC-BY 4.0 no site do autor", "humano")
        o = cadastro.transicionar(SHA, "revisado", "humano", "conferido")
        self.assertEqual(o["editorial_status"], "revisado")
        self.assertEqual([h["para"] for h in o["historico"]], ["quarentena", "catalogado", "revisado"])

    def test_indice_so_mostra_externo_revisado_com_direitos(self):
        repo = Path(self.tmp.name) / "repo"
        repo.mkdir()
        (repo / "MEMÓRIAS.md").write_text("# M\n\n(10) DIÁRIO — x · porta do painel é 20146\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run([*GIT, "-C", str(repo), "add", "-A"], check=True)
        subprocess.run([*GIT, "-C", str(repo), "commit", "-qm", "x"], check=True)
        acervo.iniciar()
        # externo revisado, com direitos e texto
        sha_ok = "cd" * 32
        cadastro.criar(sha_ok, "md", "Guia de hortas")
        cadastro.transicionar(sha_ok, "quarentena", "maquina", "ok")
        cadastro.transicionar(sha_ok, "catalogado", "maquina", "ok")
        cadastro.definir_direitos(sha_ok, "livre", "licença aberta", "humano")
        cadastro.transicionar(sha_ok, "revisado", "humano", "ok")
        cadastro.texto_path(sha_ok).parent.mkdir(parents=True, exist_ok=True)
        cadastro.texto_path(sha_ok).write_text("A horta urbana precisa de compostagem diária.\n", encoding="utf-8")
        # externo revisado com direitos desconhecidos: só referência, sem texto
        sha_des = "ef" * 32
        cadastro.criar(sha_des, "md", "Obra sem licença")
        cadastro.transicionar(sha_des, "quarentena", "maquina", "ok")
        cadastro.transicionar(sha_des, "catalogado", "maquina", "ok")
        cadastro.definir_direitos(sha_des, "desconhecido", "não localizado", "humano")
        cadastro.transicionar(sha_des, "revisado", "humano", "ok")
        cadastro.texto_path(sha_des).parent.mkdir(parents=True, exist_ok=True)
        cadastro.texto_path(sha_des).write_text("texto que não pode aparecer na busca\n", encoding="utf-8")
        # externo só catalogado: fora da busca pública
        sha_cat = "12" * 32
        cadastro.criar(sha_cat, "md", "Rascunho")
        cadastro.transicionar(sha_cat, "quarentena", "maquina", "ok")
        cadastro.transicionar(sha_cat, "catalogado", "maquina", "ok")
        cadastro.texto_path(sha_cat).parent.mkdir(parents=True, exist_ok=True)
        cadastro.texto_path(sha_cat).write_text("rascunho sobre hortas e compostagem\n", encoding="utf-8")
        r = acervo.indexar(acervo.snapshot("HEAD", repo), skills=False)
        self.assertEqual(r["objetos"], 2)                                 # o repositório: 1 entrada + 1 arquivo
        self.assertEqual(r["externos"], 3)                                # os 3 do cadastro, cada um com seu estado
        p = acervo.consultar("horta compostagem", semantica="nunca")
        origens = {x["caminho"] for x in p["resultados"]}
        self.assertIn("ext:" + sha_ok, origens)
        self.assertNotIn("ext:" + sha_des, origens)
        self.assertNotIn("ext:" + sha_cat, origens)
        self.assertEqual(acervo.consultar("texto que não pode aparecer", semantica="nunca")["estado"], acervo.NAO_ENCONTRADO)

    def test_indice_de_schema_antigo_e_recusado(self):
        repo = Path(self.tmp.name) / "repo"
        repo.mkdir()
        (repo / "M.md").write_text("(1) DIÁRIO — x\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run([*GIT, "-C", str(repo), "add", "-A"], check=True)
        subprocess.run([*GIT, "-C", str(repo), "commit", "-qm", "x"], check=True)
        acervo.iniciar()
        acervo.indexar(acervo.snapshot("HEAD", repo), skills=False)
        import sqlite3
        con = sqlite3.connect(acervo.indice_path())
        con.execute("UPDATE meta SET valor='1' WHERE chave='schema'")
        con.commit()
        con.close()
        with self.assertRaises(FileNotFoundError):
            acervo.consultar("x", semantica="nunca")


if __name__ == "__main__":
    unittest.main()
