import http.client
import importlib.util
import json
import re
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("painel_qualidade_teste", HERE / "server.py")
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


class QualidadeLlmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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

    def test_pagina_e_navegacao_existem_sem_script_inline(self):
        html = (HERE / "prototipo.html").read_text(encoding="utf-8")
        self.assertIn('id="page-qualidade"', html)
        self.assertIn('data-page="qualidade"', html)
        self.assertEqual(re.findall(r"<script(?![^>]*\bsrc=)[^>]*>", html), [])
        js = (HERE / "prototipo.js").read_text(encoding="utf-8")
        self.assertIn("/api/qualidade-llm", js)
        self.assertIn('name === "qualidade"', js)


if __name__ == "__main__":
    unittest.main()
