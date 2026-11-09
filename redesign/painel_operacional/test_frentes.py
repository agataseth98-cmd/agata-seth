"""Testes das frentes (somente leitura): /api/frentes continua; /frentes virou redirect para o Panorama.

A lista de frentes agora é o subpainel sub-frentes do /prototipo (prototipo.js lê /api/frentes).
"""
import http.client
import importlib.util
import json
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("painel_frentes_teste", HERE / "server.py")
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)

FRENTES_JSON = panel.ROOT / "config/frentes.json"


class FrentesHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_port = panel.PORT
        cls.server = panel.ThreadingHTTPServer(("127.0.0.1", 0), panel.Handler)
        cls.server.daemon_threads = True
        panel.PORT = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        panel.PORT = cls.old_port

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=3)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            resposta = conn.getresponse()
            return resposta.status, resposta.read(), dict(resposta.getheaders())
        finally:
            conn.close()

    def test_api_devolve_as_14_frentes_do_arquivo(self):
        status, corpo, cabecalhos = self.request("GET", "/api/frentes")
        self.assertEqual(status, 200)
        self.assertTrue(cabecalhos["Content-Type"].startswith("application/json"))
        dados = json.loads(corpo)
        self.assertEqual(len(dados["frentes"]), 14)
        self.assertEqual(dados, json.loads(FRENTES_JSON.read_text(encoding="utf-8")))
        self.assertEqual(dados["dados_reais"], "proibido nesta fase")

    def test_frentes_vira_redirect_para_o_panorama(self):
        status, _, cabecalhos = self.request("GET", "/frentes")
        self.assertEqual(status, 302)
        self.assertEqual(cabecalhos["Location"], "/prototipo#panorama")

    def test_frentes_js_saiu_e_a_lista_esta_no_prototipo(self):
        self.assertEqual(self.request("GET", "/frentes.js")[0], 404)
        html = (HERE / "prototipo.html").read_text(encoding="utf-8")
        self.assertIn('id="sub-frentes"', html)
        self.assertIn('id="frentes-lista"', html)
        self.assertIn('id="frentes-estado"', html)
        js = (HERE / "prototipo.js").read_text(encoding="utf-8")
        self.assertIn('"/api/frentes"', js)
        self.assertNotIn("innerHTML", js)

    def test_post_em_api_frentes_e_recusado(self):
        status, _, cabecalhos = self.request(
            "POST", "/api/frentes", body=b"{}", headers={"Content-Type": "application/json"}
        )
        self.assertEqual(status, 405)
        self.assertNotEqual(status, 200)
        self.assertIn("GET", cabecalhos.get("Allow", ""))


if __name__ == "__main__":
    unittest.main()
