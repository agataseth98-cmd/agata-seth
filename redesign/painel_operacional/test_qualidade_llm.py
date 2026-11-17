import http.client
import importlib.util
import json
import os
import tempfile
import threading
import unittest
import unittest.mock
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("painel_qualidade_teste", HERE / "server.py")
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


class ScriptInline(HTMLParser):
    """Conta <script> sem src; o HTML é lido por parser, não por expressão regular."""
    def __init__(self):
        super().__init__()
        self.inline = 0

    def handle_starttag(self, tag, attrs):
        if tag == "script" and not any(chave == "src" for chave, _ in attrs):
            self.inline += 1


class QualidadeLlmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.medicoes = tempfile.TemporaryDirectory()
        cls.nv = tempfile.TemporaryDirectory()  # 17/11/2026: a avaliação real não entra no teste
        cls.env = unittest.mock.patch.dict(os.environ, {"AGATA_MEDICOES_DIR": cls.medicoes.name, "AGATA_NV_DIR": cls.nv.name}); cls.env.start()
        cls.old_port, cls.old_origin = panel.PORT, panel.ALLOWED_ORIGIN
        cls.server = panel.ThreadingHTTPServer(("127.0.0.1", 0), panel.Handler)
        cls.server.daemon_threads = True
        panel.PORT = cls.server.server_address[1]
        panel.ALLOWED_ORIGIN = f"http://127.0.0.1:{panel.PORT}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close()
        panel.PORT, panel.ALLOWED_ORIGIN = cls.old_port, cls.old_origin
        cls.env.stop(); cls.medicoes.cleanup(); cls.nv.cleanup()

    def get(self, path, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=5)
        try:
            conn.request("GET", path, headers=headers or {})
            r = conn.getresponse()
            return r.status, r.read()
        finally:
            conn.close()

    def test_rota_devolve_indicadores_e_marca_o_que_nao_foi_medido(self):
        status, body = self.get("/api/qualidade-llm", {"Sec-Fetch-Site": "same-origin"})
        self.assertEqual(status, 200)
        dados = json.loads(body)
        itens = {i["id"]: i for i in dados["items"]}
        self.assertIn("fresh_until", dados)
        for k in ("recall_busca", "contexto_efetivo", "cache_prompt", "esforco"):
            self.assertEqual((itens[k]["estado"], itens[k]["valor"]), ("unknown", "não medido"))
        self.assertTrue({"skills", "golden", "falhas", "hidratacao"} <= set(itens))

    def test_origem_cruzada_e_recusada(self):
        self.assertEqual(self.get("/api/qualidade-llm", {"Sec-Fetch-Site": "cross-site"})[0], 403)

    def _rodada(self, nv, run_id, split, recall, medidor="recuperacao", estado="concluida"):
        pasta = Path(nv, "avaliacao", "execucoes")
        pasta.mkdir(parents=True, exist_ok=True)
        run = {"medidor": medidor, "split": split, "estado": estado, "run_id": run_id,
               "fim": "2026-11-16T10:00:00-03:00", "k": 5,
               "resumo": {"k": 5, "por_metodo": {"busca_texto": {
                   "exata": {"n": 10, "recall_at_k": recall, "mrr": 0.5},
                   "parafrase": {"n": 0, "recall_at_k": None, "mrr": None}}}}}
        Path(pasta, run_id + ".resumo.json").write_text(json.dumps(run), encoding="utf-8")

    def test_recall_busca_traz_duas_leituras_separadas_por_corpus(self):
        # D8 (17/11/2026): vault (gabarito calculado) e conjunto da avaliação por split, cada um com fonte e data;
        # nenhum número é somado nem misturado com o outro.
        qual = panel.qualidade_llm
        with tempfile.TemporaryDirectory() as med, tempfile.TemporaryDirectory() as nv, \
                tempfile.TemporaryDirectory() as raiz, \
                unittest.mock.patch.dict(os.environ, {"AGATA_MEDICOES_DIR": med, "AGATA_NV_DIR": nv}):
            Path(med, "recuperacao.json").write_text(json.dumps({"n": 40, "recall": {"1": 0.5, "5": 1.0, "10": 1.0}, "mrr": 0.7,
                                                                 "medido_em": "2026-11-16T09:00:00-03:00"}), encoding="utf-8")
            self._rodada(nv, "r-20261116-100000-aaaaaa", "dev", 0.8)
            self._rodada(nv, "r-20261116-110000-bbbbbb", "dev", 0.2, medidor="avaliacao")   # outro medidor: fora
            ind = {i["id"]: i for i in qual.indicadores(Path(raiz))}
        rec = ind["recall_busca"]
        vault, conj = rec["leituras"]
        self.assertEqual([x["corpus"] for x in rec["leituras"]], ["vault", "conjunto:dev"])
        self.assertTrue(vault["valor"].startswith("texto: @1 50% · @5 100% · MRR 0.70 (n=40)"))
        self.assertEqual((vault["fonte"], vault["medido_em"]), ("scripts/medir_recuperacao.py", "2026-11-16T09:00:00-03:00"))
        self.assertTrue(conj["valor"].startswith("@5 80% · MRR 0.50 (n=10, consultas exatas)"))
        self.assertIn("paráfrase: não medido", conj["valor"])
        self.assertIn("r-20261116-100000-aaaaaa", conj["fonte"])
        self.assertEqual(conj["medido_em"], "2026-11-16T10:00:00-03:00")
        self.assertNotIn("80%", vault["valor"])
        self.assertNotIn("100%", conj["valor"])
        self.assertEqual(rec["estado"], "warning")   # 80% no conjunto está abaixo de 90%
        self.assertTrue(rec["valor"].startswith("2 de 2 corpora medidos"))

    def test_recall_busca_so_com_conjunto_marca_o_vault_como_nao_medido(self):
        qual = panel.qualidade_llm
        with tempfile.TemporaryDirectory() as med, tempfile.TemporaryDirectory() as nv, \
                tempfile.TemporaryDirectory() as raiz, \
                unittest.mock.patch.dict(os.environ, {"AGATA_MEDICOES_DIR": med, "AGATA_NV_DIR": nv}):
            self._rodada(nv, "r-20261116-100000-cccccc", "teste", 0.95)
            rec = {i["id"]: i for i in qual.indicadores(Path(raiz))}["recall_busca"]
        self.assertEqual((rec["leituras"][0]["estado"], rec["leituras"][0]["valor"]), ("unknown", "não medido"))
        self.assertEqual((rec["leituras"][1]["corpus"], rec["leituras"][1]["estado"]), ("conjunto:teste", "ok"))
        self.assertEqual(rec["estado"], "ok")
        self.assertTrue(rec["valor"].startswith("1 de 2 corpora medidos"))

    def test_pagina_e_navegacao_existem_sem_script_inline(self):
        html = (HERE / "prototipo.html").read_text(encoding="utf-8")
        self.assertIn('id="sub-qualidade"', html)
        self.assertIn('data-sub="qualidade"', html)
        parser = ScriptInline()
        parser.feed(html)
        self.assertEqual(parser.inline, 0)
        js = (HERE / "prototipo.js").read_text(encoding="utf-8")
        self.assertIn("/api/qualidade-llm", js)
        self.assertIn("qualidade: () => { carregarQualidade(); carregarMedicoes(); }", js)  # subpainel qualidade


if __name__ == "__main__":
    unittest.main()
