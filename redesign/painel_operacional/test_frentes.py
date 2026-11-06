"""Testes da página somente leitura de frentes (/frentes, /api/frentes, /frentes.js)."""
import http.client
import importlib.util
import json
import threading
import unittest
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("painel_frentes_teste", HERE / "server.py")
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)

FRENTES_JSON = panel.ROOT / "config/frentes.json"


class MarcacoesPerigosas(HTMLParser):
    """Conta script sem src, qualquer <style> e atributos style=."""

    def __init__(self):
        super().__init__()
        self.script_inline = 0
        self.style_tag = 0
        self.style_attr = 0

    def handle_starttag(self, tag, attrs):
        nomes = {nome for nome, _ in attrs}
        if tag == "script" and "src" not in nomes:
            self.script_inline += 1
        if tag == "style":
            self.style_tag += 1
        if "style" in nomes:
            self.style_attr += 1


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

    def test_pagina_sem_script_inline_nem_style(self):
        status, corpo, cabecalhos = self.request("GET", "/frentes")
        self.assertEqual(status, 200)
        self.assertTrue(cabecalhos["Content-Type"].startswith("text/html"))
        marcas = MarcacoesPerigosas()
        marcas.feed(corpo.decode("utf-8"))
        self.assertEqual(marcas.script_inline, 0)
        self.assertEqual(marcas.style_tag, 0)
        self.assertEqual(marcas.style_attr, 0)
        self.assertIn(b'src="/frentes.js"', corpo)
        self.assertIn(b'href="/prototipo"', corpo)

    def test_script_servido_como_javascript(self):
        status, corpo, cabecalhos = self.request("GET", "/frentes.js")
        self.assertEqual(status, 200)
        self.assertTrue(cabecalhos["Content-Type"].startswith("text/javascript"))
        self.assertNotIn(b"innerHTML", corpo)

    def test_post_em_api_frentes_e_recusado(self):
        status, _, cabecalhos = self.request(
            "POST", "/api/frentes", body=b"{}", headers={"Content-Type": "application/json"}
        )
        self.assertEqual(status, 405)
        self.assertNotEqual(status, 200)
        self.assertIn("GET", cabecalhos.get("Allow", ""))


if __name__ == "__main__":
    unittest.main()
