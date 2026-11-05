import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(AQUI.parents[1] / "alexandria"))
import avaliar  # noqa: E402
import conjunto  # noqa: E402
import registro  # noqa: E402
sys.path.insert(0, str(AQUI.parents[1] / "scripts"))

ROTAS = [{"rota": "ollama-local/a", "categoria": "local", "tipo": "ollama", "modelo": "a", "independencia": {"familia": "a"}},
         {"rota": "ollama-local/b", "categoria": "local", "tipo": "ollama", "modelo": "b", "independencia": {"familia": "b"}}]
ORC = {"max_tokens": 1000, "max_chamadas": 500, "timeout_s": 30, "provedores": {"local": True}}


class B3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = str(Path(self.tmp.name) / "dados")
        self.antigo_cache = os.environ.get("AGATA_NV_CACHE")
        os.environ["AGATA_NV_CACHE"] = str(Path(self.tmp.name) / "cache")
        self.orig_ler = avaliar.orcamento.ler
        avaliar.orcamento.ler = lambda: dict(ORC)

    def tearDown(self):
        avaliar.orcamento.ler = self.orig_ler
        if self.antigo_cache is None:
            os.environ.pop("AGATA_NV_CACHE", None)
        else:
            os.environ["AGATA_NV_CACHE"] = self.antigo_cache
        self.tmp.cleanup()

    def linhas(self, rota, notas, cond="alexandria"):
        return [{"task_id": f"t{i:02d}", "condition": cond, "rota": rota, "criterios_ok": n, "criterios_total": 1,
                 "critical_failure": False, "latency_ms": 10, "corpus_snapshot": "abc"} for i, n in enumerate(notas)]

    def test_troca_de_llm_pareia_tarefas_e_diz_qual_e_melhor(self):
        base = [1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1]
        ls = self.linhas("ollama-local/a", base) + self.linhas("ollama-local/b", [1] * 12)
        r = avaliar.comparar_rotas(ls, "ollama-local/a", "ollama-local/b")
        self.assertEqual(r["n_pares"], 12)
        self.assertEqual(r["veredito"], "b_melhor")
        self.assertEqual(r["corpus_snapshot"], "abc")
        pouca = avaliar.comparar_rotas(ls[:4] + ls[12:16], "ollama-local/a", "ollama-local/b")
        self.assertEqual(pouca["veredito"], "inconclusivo")

    def test_teto_de_tokens_do_orcamento_e_aplicado_de_verdade(self):
        conjunto.carregar  # carregado pelo rodar abaixo
        ts = conjunto.carregar("dev")[:4]
        def chamar(rota, prompt):
            return {"ok": True, "texto": "resposta", "usage": {"input_tokens": 400, "output_tokens": 200}, "latencia_ms": 5}
        r = avaliar.rodar("dev", ["ollama-local/a"], ["sem_contexto"], 1, todas_rotas=ROTAS, chamar=chamar,
                          fontes_kw={"buscar": lambda q: ([], 0, [])}, paralelo=False)
        self.assertLessEqual(r["resumo"]["tokens_usados"], 1000 + 600)   # para ao passar do teto (no máximo 1 chamada a mais)
        falhas = [x for x in registro.linhas(r["run_id"]) if x.get("failure_stage") == "orcamento"]
        self.assertGreater(len(falhas), 0)
        self.assertFalse(r["resumo"]["paralelo"])
        self.assertIn("duracao_s", r["resumo"])
        self.assertTrue(len(ts) >= 1)

    def test_criterio_rubrica_fica_fora_do_veredito(self):
        t = {"task_id": "rec-xx", "grupo": "recuperacao", "split": "dev", "pedido": "p", "autor": "t",
             "criterios": [{"tipo": "contem", "valor": ["x"]}, {"tipo": "rubrica", "motivo": "fundamenta bem?"}]}
        r = conjunto.avaliar_resposta(t, "tem x")
        self.assertEqual(r["criterios_total"], 1)
        self.assertTrue(r["passou"])
        conjunto.validar(t)

    def test_restauracao_reconstroi_em_cache_isolado_e_compara(self):
        import shutil
        if not shutil.which("git"):
            self.skipTest("sem git")
        import acervo  # noqa: E402
        repo = Path(self.tmp.name) / "repo"
        repo.mkdir()
        (repo / "MEMÓRIAS.md").write_text("# M\n\n(10) DIÁRIO — x · porta do painel é 20146\n\n(11) DIÁRIO — y\n", encoding="utf-8")
        g = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run([*g, "-C", str(repo), "add", "-A"], check=True)
        subprocess.run([*g, "-C", str(repo), "commit", "-qm", "x"], check=True)
        acervo.iniciar()
        acervo.indexar(acervo.snapshot("HEAD", repo), skills=False)
        # o snapshot precisa estar em <dados>/alexandria/acervo/snapshots/<commit>, que é onde o mecânico procura
        snap_dir = acervo.snapshot("HEAD", repo)
        r = avaliar._mec_restauracao()
        self.assertTrue(r["ok"], r)
        self.assertTrue(r["passou"], r)
        self.assertEqual(r["detalhe"]["diferencas_objetos"], 0)

    def test_condicao_externa_so_entra_com_busca_injetada(self):
        ts = conjunto.carregar("dev")
        t = next(x for x in ts if not x.get("documentos"))
        sem_indice = lambda q, **k: {"resultados": [], "context_id": "c", "palavras": []}   # o teste não monta índice
        import politica_egress  # noqa: E402
        original = politica_egress.destino_permitido
        politica_egress.destino_permitido = lambda u: (True, "")      # DNS de ex.test não existe aqui
        try:
            fs, _ = avaliar.fontes(t, "alexandria_externa", consultar=sem_indice, buscar_externa=lambda q: [
                {"url": "https://ex.test/a", "titulo": "t", "trecho": "dado externo"}])
        finally:
            politica_egress.destino_permitido = original
        self.assertTrue(any(f["estado"] == "externo, efêmero" for f in fs))
        fs2, _ = avaliar.fontes(t, "alexandria_externa", consultar=sem_indice)   # sem busca: só a local, sem o efêmero
        self.assertFalse(any(f["estado"] == "externo, efêmero" for f in fs2))


if __name__ == "__main__":
    unittest.main()
