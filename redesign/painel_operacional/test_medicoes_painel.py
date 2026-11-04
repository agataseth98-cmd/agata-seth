import http.client
import importlib.util
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("painel_medicoes_teste", HERE / "server.py")
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)
med = panel.medicoes_painel


class MedicoesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory()
        cls.env = mock.patch.dict(os.environ, {"AGATA_MEDICOES_DIR": cls.dir.name}); cls.env.start()
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
        cls.env.stop(); cls.dir.cleanup()

    def setUp(self):
        med._JOB.clear(); med._JOB["estado"] = "ocioso"

    def pedir(self, metodo, caminho, corpo=None, cab=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=10)
        try:
            conn.request(metodo, caminho, body=corpo, headers=cab or {})
            r = conn.getresponse()
            return r.status, r.read()
        finally:
            conn.close()

    def post(self, dados, **extra):
        cab = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json", **extra}
        return self.pedir("POST", "/api/medicoes/executar", json.dumps(dados).encode(), cab)

    def test_executar_recusa_acao_e_modelo_fora_da_lista(self):
        with mock.patch.object(med, "modelos_locais", return_value=["qwen3:4b"]):
            self.assertEqual(self.post({"acao": "apagar"})[0], 400)
            self.assertEqual(self.post({"acao": "contexto", "modelo": "../../etc/passwd"})[0], 400)
            self.assertEqual(self.post({"acao": "contexto", "modelo": "outro:7b"})[0], 400)
            self.assertEqual(self.post({"acao": "contexto"})[0], 400)
            self.assertEqual(self.post({"acao": "contexto", "modelo": "qwen3:4b", "tarefa": "rm -rf"})[0], 400)

    def test_executar_exige_origem_e_recusa_quando_ocupado(self):
        self.assertEqual(self.post({"acao": "recuperacao"}, Origin="http://outro.invalid")[0], 403)
        med._JOB.update(estado="rodando")
        self.assertEqual(self.post({"acao": "recuperacao"})[0], 429)

    def test_argv_fixo_sem_shell_e_com_modelo_so_da_lista(self):
        chamadas = []
        def falso(argv, **kw):
            chamadas.append((argv, kw)); return SimpleNamespace(returncode=0, stdout="ok", stderr="")
        with mock.patch.object(med, "modelos_locais", return_value=["qwen3:4b"]), mock.patch.object(med.subprocess, "run", side_effect=falso):
            r = med.executar("contexto", "qwen3:4b", sincrono=True)
            self.assertEqual(r["job"]["estado"], "ok")
            argv, kw = chamadas[0]
            self.assertEqual(argv[1].split("/")[-1], "medir_contexto_efetivo.py")
            self.assertEqual(argv[2:], ["--salvar", "--modelo", "qwen3:4b", "--tarefa", "agulha"])
            med.executar("contexto", "qwen3:4b", sincrono=True, tarefa="varias")
            self.assertEqual(chamadas[1][0][-2:], ["--tarefa", "varias"])
            self.assertFalse(kw.get("shell"))
            med.executar("recuperacao", sincrono=True)
            self.assertEqual(chamadas[2][0][1].split("/")[-1], "medir_recuperacao.py")
            self.assertNotIn("--semantico", chamadas[2][0])
            med.executar("recuperacao_semantica", sincrono=True)
            self.assertEqual(chamadas[3][0][-1], "--semantico")
            for nova in ("rastreio", "agregacao"):
                med.executar("contexto", "qwen3:4b", sincrono=True, tarefa=nova)
                self.assertEqual(chamadas[-1][0][-2:], ["--tarefa", nova])

    def test_estado_traz_resultados_salvos_e_lista_de_modelos(self):
        Path(self.dir.name, "recuperacao.json").write_text(json.dumps({"n": 3, "recall": {"1": 1.0, "5": 1.0}, "mrr": 1.0}), encoding="utf-8")
        with mock.patch.object(med, "modelos_locais", return_value=["m:1"]):
            status, corpo = self.pedir("GET", "/api/medicoes/estado", None, {"Sec-Fetch-Site": "same-origin"})
        d = json.loads(corpo)
        self.assertEqual((status, d["modelos"], d["recuperacao"]["n"]), (200, ["m:1"], 3))

    def test_indicador_de_recuperacao_usa_a_medicao_salva(self):
        qual = panel.qualidade_llm
        Path(self.dir.name, "recuperacao.json").write_text(json.dumps({"n": 3, "recall": {"1": 1.0, "5": 1.0}, "mrr": 1.0}), encoding="utf-8")
        antes = {i["id"]: i for i in qual.indicadores(Path(self.dir.name))}
        self.assertEqual(antes["recall_busca"]["estado"], "ok")
        Path(self.dir.name, "recuperacao.json").unlink()
        depois = {i["id"]: i for i in qual.indicadores(Path(self.dir.name))}
        self.assertEqual((depois["recall_busca"]["estado"], depois["recall_busca"]["valor"]), ("unknown", "não medido"))

    def test_pagina_tem_os_controles_e_o_js_so_chama_as_rotas_das_medicoes(self):
        html = (HERE / "prototipo.html").read_text(encoding="utf-8")
        for i in ("medir-recuperacao", "medir-semantica", "medir-modelo", "medir-tarefa", "medir-contexto", "medir-nota"):
            self.assertIn(f'id="{i}"', html)
        js = (HERE / "prototipo.js").read_text(encoding="utf-8")
        self.assertIn("/api/medicoes/estado", js); self.assertIn("/api/medicoes/executar", js)


if __name__ == "__main__":
    unittest.main()
