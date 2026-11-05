import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(AQUI.parent))
sys.path.insert(0, str(AQUI.parents[1] / "alexandria"))
import avaliar  # noqa: E402
import conjunto  # noqa: E402
import recuperacao  # noqa: E402
import registro  # noqa: E402

ROTAS = [{"rota": "ollama-local/fake", "categoria": "local", "tipo": "ollama", "modelo": "fake",
          "independencia": {"familia": "fake"}},
         {"rota": "claude:cli", "categoria": "assinatura", "tipo": "conexao", "provedor": "claude", "modo": "cli",
          "modelo": "haiku", "independencia": {"familia": "claude"}}]


def sabe_tudo(_rota, prompt):
    """Executor falso que responde certo só quando as fontes trazem o necessário."""
    if "20146" in prompt and "PEDIDO: Em que porta" in prompt:
        return {"ok": True, "texto": "A porta é 20146 [d1].", "usage": {"input_tokens": 10, "output_tokens": 5}, "latencia_ms": 50}
    return {"ok": True, "texto": "Não encontrei nas fontes.", "usage": {"input_tokens": 10, "output_tokens": 5}, "latencia_ms": 50}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AGATA_NV_DIR"] = str(Path(self.tmp.name) / "dados")

    def tearDown(self):
        self.tmp.cleanup()

    def reservado(self, tarefas):
        p = conjunto.pasta_reservado()
        p.mkdir(parents=True, exist_ok=True)
        (p / conjunto.ARQ_RESERVADO).write_text("".join(json.dumps(t) + "\n" for t in tarefas), encoding="utf-8")


class ConjuntoTests(Base):
    def test_trinta_tarefas_seis_grupos_reservado_fora_do_repo(self):
        dev, cal = conjunto.carregar("dev"), conjunto.carregar("calibracao")
        self.assertEqual(len(dev), 12)
        self.assertEqual(len(cal), 6)
        for g in conjunto.GRUPOS:
            self.assertEqual(sum(t["grupo"] == g for t in dev), 2)
            self.assertEqual(sum(t["grupo"] == g for t in cal), 1)
        self.assertFalse(any(t.get("split") == "teste" for t in dev + cal))
        reserv = conjunto.pasta_reservado().resolve()
        self.assertNotIn(str(RAIZ.resolve()), str(reserv))   # o gabarito reservado nunca mora no repo

    def test_executor_nunca_ve_criterio_nem_relevantes(self):
        for t in conjunto.carregar("dev") + conjunto.carregar("calibracao"):
            for c in avaliar.CONDICOES:
                fs = avaliar._fontes_documentos(t, c) if t.get("documentos") else None
                p = conjunto.prompt(t, fs)
                self.assertNotIn("criterios", p)
                self.assertNotIn("relevantes", p)
                for crit in t["criterios"] + t.get("criticos", []):
                    if crit["tipo"] == "regex":
                        self.assertNotIn(crit["valor"], p)

    def test_privado_filtrado_na_alexandria_e_cru_no_baseline(self):
        t = {"task_id": "res-x", "grupo": "resistencia", "split": "dev", "pedido": "liste",
             "documentos": [{"id": "d1", "texto": "porta 20146"},
                            {"id": "d2", "texto": "senha ZX-1", "classification": "private"}],
             "criterios": [{"tipo": "contem", "valor": ["20146"]}]}
        self.assertIn("ZX-1", conjunto.prompt(t, avaliar._fontes_documentos(t, "busca_texto")))
        self.assertNotIn("ZX-1", conjunto.prompt(t, avaliar._fontes_documentos(t, "alexandria")))
        self.assertIsNone(avaliar._fontes_documentos(t, "sem_contexto"))
        t2 = dict(t, documentos=[{"id": "d1", "texto": "X: 90%", "origem": "a, cópia do comunicado Y", "autoridade": "nenhuma"},
                                 {"id": "d2", "texto": "X: 90%", "origem": "b, cópia do comunicado Y", "autoridade": "nenhuma"}])
        self.assertIn("nota: mesmo texto de [d1]", conjunto.prompt(t2, avaliar._fontes_documentos(t2, "alexandria")))
        self.assertNotIn("nota:", conjunto.prompt(t2, avaliar._fontes_documentos(t2, "busca_texto")))

    def test_criterios_mecanicos(self):
        self.assertTrue(conjunto.checar({"tipo": "cita", "valor": ["115"]}, "ver (115) e mais"))
        self.assertTrue(conjunto.checar({"tipo": "cita", "valor": ["d1"]}, "é 20146 [d1]"))
        self.assertFalse(conjunto.checar({"tipo": "cita", "valor": ["d1"]}, "é 20146 [d2]"))
        self.assertTrue(conjunto.checar({"tipo": "abstem"}, "Não encontrei isso nas fontes."))
        self.assertTrue(conjunto.checar({"tipo": "abstem"}, "Não encontrou nas fontes."))   # 3ª pessoa: rodada de 05/11
        self.assertTrue(conjunto.checar({"tipo": "nao_contem", "valor": ["feito-42"]}, "Bolo de fubá."))
        self.assertTrue(conjunto.checar({"tipo": "contem", "valor": ["fuba"]}, "Bolo de FUBÁ."))
        r = conjunto.avaliar_resposta({"criterios": [{"tipo": "contem", "valor": ["x"]}],
                                       "criticos": [{"tipo": "nao_contem", "valor": ["segredo"], "motivo": "vazou"}]},
                                      "x e o segredo")
        self.assertFalse(r["passou"])
        self.assertEqual(r["criticos_violados"], ["vazou"])

    def test_reservado_exige_revisao_no_hash_atual_e_politica(self):
        base = conjunto.carregar("dev")[4]
        self.reservado([dict(base, split="teste")])
        with self.assertRaises(PermissionError):
            avaliar.preparar("teste", ["ollama-local/fake"], todas_rotas=ROTAS)
        conjunto.marcar_revisado("humano")
        with self.assertRaises(PermissionError):   # falta a política
            avaliar.preparar("teste", ["ollama-local/fake"], todas_rotas=ROTAS)
        avaliar.salvar_politica(0.1, 60000, 0)
        ts, rs = avaliar.preparar("teste", ["ollama-local/fake"], todas_rotas=ROTAS)
        self.assertEqual(len(ts), 1)
        self.reservado([dict(base, split="teste", pedido="mudou")])   # mudou o conjunto: revisão não vale mais
        self.assertTrue(conjunto.estado_reservado()["revisao_desatualizada"])
        with self.assertRaises(PermissionError):
            avaliar.preparar("teste", ["ollama-local/fake"], todas_rotas=ROTAS)

    def test_politica_fora_do_limite_recusada(self):
        with self.assertRaises(ValueError):
            avaliar.salvar_politica(2, 60000, 0)
        with self.assertRaises(ValueError):
            avaliar.salvar_politica("x", 60000, 0)


class RodadaTests(Base):
    def test_rodada_grava_registro_comum_e_marca_contaminacao(self):
        r = avaliar.rodar("dev", ["ollama-local/fake", "claude:cli"], ["busca_texto", "alexandria"], 1,
                          todas_rotas=ROTAS, chamar=sabe_tudo,
                          fontes_kw={"buscar": lambda q: ([], 0, []),
                                     "consultar": lambda q, **k: {"resultados": [], "context_id": "ctx:x"}})
        ls = registro.linhas(r["run_id"])
        self.assertEqual(len(ls), 12 * 2 * 2)
        campos = {"run_id", "task_id", "split", "condition", "model_id", "corpus_snapshot", "context_id", "seed", "budget",
                  "usage", "latency_ms", "outcome", "failure_stage", "critical_failure", "evidence", "reviewer", "rubric_version"}
        self.assertTrue(campos <= set(ls[0]))
        self.assertTrue(all(x["contaminado"] for x in ls if x["rota"] == "claude:cli"))
        self.assertFalse(any(x["contaminado"] for x in ls if x["rota"] == "ollama-local/fake"))
        comp = r["resumo"]["comparacoes"]
        self.assertTrue(all(c["veredito"].startswith("nao_conta") for c in comp if c["rota"] == "claude:cli"))
        self.assertTrue(all(c["veredito"].startswith("inconclusivo") for c in comp if c["rota"] != "claude:cli"))  # sem política

    def test_falha_de_infra_nao_vira_erro_cognitivo_e_zero_da_null(self):
        def fora(_r, _p):
            return {"ok": False, "falha_etapa": "transporte", "erro": "x"}
        r = avaliar.rodar("calibracao", ["ollama-local/fake"], ["busca_texto"], 1, todas_rotas=ROTAS, chamar=fora,
                          fontes_kw={"buscar": lambda q: ([], 0, [])})
        pc = next(iter(r["resumo"]["por_condicao"].values()))
        self.assertEqual(pc["avaliaveis"], 0)
        self.assertIsNone(pc["dimensoes"]["F"])
        self.assertIsNone(pc["C"]["cobertura"])
        self.assertEqual(pc["falhas_infra"], {"transporte": 6})

    def test_falha_critica_veta_e_n_pequeno_e_inconclusivo(self):
        def ln(t, c, s, crit=False):
            return {"task_id": t, "condition": c, "rota": "r", "criterios_ok": s, "criterios_total": 1,
                    "critical_failure": crit, "latency_ms": 10}
        base = [ln(f"t{i}", "busca_texto", 0) for i in range(12)]
        cand = [ln(f"t{i}", "alexandria", 1) for i in range(12)]
        pol = {"margem_minima": 0.1, "teto_latencia_ms": 1000}
        v = avaliar.comparar(base + cand, pol)[0]
        self.assertEqual(v["veredito"], "melhora")
        v = avaliar.comparar(base + cand[:-1] + [ln("t11", "alexandria", 1, True)], pol)[0]
        self.assertTrue(v["veredito"].startswith("vetado"))
        v = avaliar.comparar(base[:5] + cand[:5], pol)[0]
        self.assertEqual(v["veredito"], "inconclusivo")
        pior = avaliar.comparar([ln(f"t{i}", "busca_texto", 1) for i in range(12)]
                                + [ln(f"t{i}", "alexandria", 0) for i in range(12)], None)[0]
        self.assertEqual(pior["veredito"], "piora")


class RecuperacaoTests(Base):
    def test_medidas_e_entrada_pela_linha(self):
        self.assertEqual(recuperacao.medidas(["9", "115"], {"115"}, 5), {"p_at_k": 0.2, "recall_at_k": 1.0, "rr": 0.5})
        self.assertIsNone(recuperacao.medidas([], set(), 5)["recall_at_k"])
        d = Path(self.tmp.name) / "r"
        d.mkdir()
        (d / "M.md").write_text("cabeça\n(115) DIÁRIO — x\nlinha a\nlinha b\n", encoding="utf-8")
        ach = recuperacao.recuperar("busca_texto", "q", 5, raiz=d, buscar=lambda q: ([(1, "M.md", 4, "linha b")], 1, ["q"]))
        self.assertEqual(ach, ["115"])

    def test_mecanicos_reconstrucao_e_rede_com_indice_real(self):
        if not shutil.which("git"):
            self.skipTest("sem git")
        import subprocess
        sys.path.insert(0, str(RAIZ / "redesign" / "alexandria"))
        import acervo
        os.environ["AGATA_NV_CACHE"] = str(Path(self.tmp.name) / "cache")
        repo = Path(self.tmp.name) / "repo"
        repo.mkdir()
        (repo / "MEMÓRIAS.md").write_text("# M\n\n(10) DIÁRIO — x · busca semântica secundária, ver (11)\n\n(11) DIÁRIO — y\n",
                                         encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"], check=True)
        acervo.iniciar()
        acervo.indexar(acervo.snapshot("HEAD", repo), skills=False)
        self.assertTrue(avaliar.MECANICOS["reconstrucao_indice"]()["passou"])
        self.assertTrue(avaliar.MECANICOS["rede_indisponivel"]()["passou"])


if __name__ == "__main__":
    unittest.main()
