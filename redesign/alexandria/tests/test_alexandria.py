import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import acervo  # noqa: E402
import skills  # noqa: E402

GIT = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]


def commit(repo: Path, msg="x"):
    subprocess.run([*GIT, "-C", str(repo), "add", "-A"], check=True)
    subprocess.run([*GIT, "-C", str(repo), "commit", "-qm", msg], check=True)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        os.environ["AGATA_NV_DIR"] = str(t / "dados")
        os.environ["AGATA_NV_CACHE"] = str(t / "cache")
        self.repo = t / "repo"
        (self.repo / "memoria" / "privado").mkdir(parents=True)
        (self.repo / ".agents" / "skills" / "foo-bar").mkdir(parents=True)
        (self.repo / "ferramentas").mkdir()
        (self.repo / "MEMÓRIAS.md").write_text(
            "# M\n\n(10) DIÁRIO — x · travamento no suspend, ver (11)\n\n(11) DIÁRIO — y · base do suspend\n", encoding="utf-8")
        (self.repo / "memoria" / "privado" / "nota.md").write_text("segredo do jardim travamento\n", encoding="utf-8")
        (self.repo / ".agents" / "skills" / "foo-bar" / "SKILL.md").write_text(
            "---\nname: foo-bar\ndescription: aplicar proposta assinada no repositório\n---\ncorpo\n", encoding="utf-8")
        (self.repo / "ferramentas" / "indice.json").write_text(json.dumps([
            {"nome": "continuous-learning-x", "tipo": "skill", "fonte": "ecc", "caminho": "", "resumo": "aplicar proposta sozinho"},
            {"nome": "doc-helper", "tipo": "skill", "fonte": "ecc", "caminho": "", "resumo": "escrever documentação"}]), encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        commit(self.repo)
        acervo.iniciar()

    def tearDown(self):
        self.tmp.cleanup()

    def indexar(self):
        return acervo.indexar(acervo.snapshot("HEAD", self.repo))


class AlexandriaTests(Base):
    def test_indice_reconstruivel_e_deterministico(self):
        self.indexar()
        con = sqlite3.connect(acervo.indice_path())
        a = con.execute("SELECT object_id, sha256, classification FROM objects ORDER BY 1").fetchall()
        con.close()
        os.remove(acervo.indice_path())
        self.indexar()
        con = sqlite3.connect(acervo.indice_path())
        b = con.execute("SELECT object_id, sha256, classification FROM objects ORDER BY 1").fetchall()
        con.close()
        self.assertEqual(a, b)
        self.assertTrue(any(o.startswith("alex:entrada:10@") for o, *_ in a))

    def test_hash_muda_e_derivado_fica_pendente(self):
        self.indexar()
        pac = acervo.consultar("suspend travamento", semantica="nunca")
        self.assertTrue(acervo.contexto_valido(pac)["valido"])
        (self.repo / "MEMÓRIAS.md").write_text(
            "# M\n\n(10) DIÁRIO — x · travamento no suspend corrigido\n\n(11) DIÁRIO — y · base do suspend\n", encoding="utf-8")
        commit(self.repo, "muda")
        r = self.indexar()
        self.assertGreaterEqual(r["mudaram"], 1)
        v = acervo.contexto_valido(pac)
        self.assertFalse(v["valido"])
        ledger = Path(os.environ["AGATA_NV_DIR"]) / "eventos" / "ledger.jsonl"
        self.assertTrue(any(json.loads(x)["kind"] == "drift" for x in ledger.read_text().splitlines()))

    def test_privado_nao_aparece_em_consulta_publica(self):
        self.indexar()
        pub = acervo.consultar("jardim", semantica="nunca")
        self.assertEqual(pub["estado"], acervo.NAO_ENCONTRADO)
        priv = acervo.consultar("jardim", acesso="private", semantica="nunca")
        self.assertTrue(priv["resultados"] and priv["resultados"][0]["classification"] == "private")

    def test_semantica_fora_degrada_para_lexico_com_rotulo(self):
        self.indexar()

        def cai(q, n):
            raise ConnectionError("e5 fora")
        p = acervo.consultar("suspend", semantica="sempre", buscar_semantica=cai)
        self.assertEqual(p["metodos"][0], "lexico")
        self.assertTrue(any("semântica indisponível" in a for a in p["avisos"]))
        q = acervo.consultar("xyzwq", semantica="sempre", buscar_semantica=lambda q, n: [{"num": 11, "score": 0.8}])
        self.assertEqual([r["metodo"] for r in q["resultados"]], ["semantica"])

    def test_ausencia_e_nao_encontrado_nesta_busca(self):
        self.indexar()
        p = acervo.consultar("palavrainexistentezz", semantica="nunca")
        self.assertEqual(p["estado"], "não encontrado nesta busca")
        self.assertEqual(p["resultados"], [])

    def test_skill_selecionada_nao_executa_e_quarentena_fica_fora(self):
        self.indexar()
        s = skills.selecionar("use foo-bar para aplicar proposta")
        self.assertEqual(s["candidatos"][0]["nome"], "foo-bar")
        self.assertEqual(s["candidatos"][0]["motivo"], "mencao_explicita")
        self.assertTrue(all(c["aplicada"] is False and c["estado"] == "selecionada" for c in s["candidatos"]))
        self.assertFalse(any(c["nome"] == "continuous-learning-x" for c in s["candidatos"]))


if __name__ == "__main__":
    unittest.main()
