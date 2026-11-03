import http.client
import importlib.util
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("painel_sdd_teste", HERE / "server.py")
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)
sdd = panel.sdd_painel


def repo_falso(raiz: Path, comando):
    (raiz / "redesign" / "x" / "spec").mkdir(parents=True)
    (raiz / "redesign" / "x" / "spec" / "spec.md").write_text(
        "# Spec\n\n## Contrato\n\nc\n\n## Critérios de aceite\n\n- [ ] criterio um\n\n## Código\n\n- `a.py`\n", encoding="utf-8")
    (raiz / "redesign" / "x" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (raiz / "redesign" / "x" / "spec" / "acceptance.json").write_text(
        json.dumps([{"criterion": "criterio um", "command": comando, "cwd": None}]), encoding="utf-8")
    (raiz / "redesign" / "sdd_flow").mkdir(parents=True)
    (raiz / "redesign" / "sdd_flow" / "anchor.py").write_text((HERE.parent / "sdd_flow" / "anchor.py").read_text(encoding="utf-8"), encoding="utf-8")


class SddPainelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_port, cls.old_origin, cls.old_root = panel.PORT, panel.ALLOWED_ORIGIN, sdd.ROOT
        cls.cache = tempfile.TemporaryDirectory()
        cls.old_cache = sdd.CACHE; sdd.CACHE = Path(cls.cache.name)
        cls.server = panel.ThreadingHTTPServer(("127.0.0.1", 0), panel.Handler)
        cls.server.daemon_threads = True
        panel.PORT = cls.server.server_address[1]
        panel.ALLOWED_ORIGIN = f"http://127.0.0.1:{panel.PORT}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close()
        panel.PORT, panel.ALLOWED_ORIGIN, sdd.CACHE = cls.old_port, cls.old_origin, cls.old_cache
        cls.cache.cleanup()

    def pedir(self, metodo, caminho, corpo=None, cabecalhos=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=10)
        try:
            conn.request(metodo, caminho, body=corpo, headers=cabecalhos or {})
            r = conn.getresponse()
            return r.status, r.read()
        finally:
            conn.close()

    def post(self, dados, **extra):
        cab = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json", **extra}
        return self.pedir("POST", "/api/sdd/executar", json.dumps(dados).encode(), cab)

    def test_estado_lista_os_componentes_ancorados(self):
        status, corpo = self.pedir("GET", "/api/sdd/estado", None, {"Sec-Fetch-Site": "same-origin"})
        self.assertEqual(status, 200)
        nomes = {i["componente"] for i in json.loads(corpo)["items"]}
        self.assertTrue({"sdd_flow", "painel_operacional"} <= nomes)

    def test_executar_recusa_acao_e_componente_fora_da_lista(self):
        self.assertEqual(self.post({"acao": "ancora", "componente": "../etc"})[0], 400)
        self.assertEqual(self.post({"acao": "apagar", "componente": "sdd_flow"})[0], 400)
        self.assertEqual(self.post({"acao": "ancora", "componente": 7})[0], 400)

    def test_executar_exige_origem_json_e_confere_a_ancora(self):
        self.assertEqual(self.post({"acao": "ancora", "componente": "sdd_flow"}, Origin="http://outro.invalid")[0], 403)
        self.assertEqual(self.pedir("POST", "/api/sdd/executar", b"{}", {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "text/plain"})[0], 415)
        status, corpo = self.post({"acao": "ancora", "componente": "sdd_flow"})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(corpo)["ok"])

    def test_criterios_recusam_comando_fora_do_padrao(self):
        with tempfile.TemporaryDirectory() as t:
            raiz = Path(t); repo_falso(raiz, ["bash", "-c", "echo oi"])
            r = sdd.executar("criterios", "x", raiz)
        self.assertFalse(r["ok"])
        self.assertTrue(any("fora do padrão" in p["detalhe"] for p in r["passos"]))

    def test_criterios_rodam_e_sem_pytest_sao_nao_medidos(self):
        with tempfile.TemporaryDirectory() as t:
            raiz = Path(t); repo_falso(raiz, ["pytest", "-q", "redesign/x/t.py"])
            with mock.patch.object(sdd.shutil, "which", return_value=None), mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("AGATA_PYTEST", None)
                r = sdd.executar("criterios", "x", raiz)
            self.assertTrue(any("não medido" in p["detalhe"] for p in r["passos"]))
            with mock.patch.dict(os.environ, {"AGATA_PYTEST": "/bin/true"}):
                r = sdd.executar("criterios", "x", raiz)
            self.assertTrue(r["ok"] and r["criterios"][0]["status"] == "pass")
            with mock.patch.dict(os.environ, {"AGATA_PYTEST": "/bin/false"}):
                r = sdd.executar("criterios", "x", raiz)
            self.assertFalse(r["ok"])

    def test_pagina_sdd_existe_e_o_js_chama_so_as_rotas_do_sdd(self):
        html = (HERE / "prototipo.html").read_text(encoding="utf-8")
        self.assertIn('id="page-sdd"', html); self.assertIn('data-page="sdd"', html)
        js = (HERE / "prototipo.js").read_text(encoding="utf-8")
        self.assertIn("/api/sdd/estado", js); self.assertIn("/api/sdd/executar", js)


if __name__ == "__main__":
    unittest.main()
