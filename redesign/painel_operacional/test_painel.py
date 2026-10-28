#!/usr/bin/env python3
"""Verifica o contrato local do painel sem acessar os serviços de produção."""
import collections
import http.client
import importlib.util
import json
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("painel_teste", HERE / "server.py")
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "id":
                self.ids.append(value)


class PainelTests(unittest.TestCase):
    def test_html_tem_controles_sem_ids_duplicados(self):
        parser = IdParser()
        parser.feed((HERE / "prototipo.html").read_text(encoding="utf-8"))
        duplicates = [name for name, count in collections.Counter(parser.ids).items() if count > 1]
        self.assertEqual(duplicates, [])
        for name in ("wiki-form", "wiki-query", "wiki-mode", "wiki-source", "wiki-results",
                     "refresh-main", "refresh-status", "live-services", "live-timers",
                     "maintenance-tasks", "proposal-list", "model-list", "integration-list", "memory-total"):
            self.assertIn(name, parser.ids)


    def test_timer_limita_comando_e_nao_confunde_disparo_com_execucao(self):
        output = ("Id=agata-manutencao.timer\nLoadState=loaded\nActiveState=active\n"
                  "SubState=waiting\nNextElapseUSecRealtime=amanhã\nLastTriggerUSec=hoje\n")
        service = ("Id=agata-manutencao.service\nLoadState=loaded\nActiveState=inactive\n"
                   "Result=exec-condition\nExecMainExitTimestamp=\nExecMainStatus=0\n")
        with mock.patch.object(panel.subprocess, "run", side_effect=[SimpleNamespace(returncode=0, stdout=output),
                                                                    SimpleNamespace(returncode=0, stdout=service)]) as run:
            result = panel._timer_snapshot("agata-manutencao.timer")
        self.assertEqual(result["state"], "ok")
        self.assertEqual(result["last_trigger"], "hoje")
        self.assertEqual(result["execution"]["state"], "skipped")
        self.assertEqual(run.call_args_list[0].args[0][-2:], ["--", "agata-manutencao.timer"])
        self.assertEqual(run.call_args_list[1].args[0][-2:], ["--", "agata-manutencao.service"])
        self.assertNotIn("shell", run.call_args_list[0].kwargs)
        with self.assertRaises(ValueError):
            panel._timer_snapshot("unidade-arbitraria.timer")
        with mock.patch.object(panel.subprocess, "run", side_effect=OSError("falhou")):
            self.assertEqual(panel._timer_snapshot("agata-manutencao.timer")["state"], "unknown")

    def test_propostas_nao_confundem_marcador_com_assinatura_valida(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / "propostas"
            directory.mkdir()
            (directory / "primeira.diff").write_text("diff")
            (directory / "segunda.diff").write_text("diff")
            (directory / "APROVADO-segunda").write_text("sem verificação")
            with mock.patch.object(panel, "ROOT", root):
                data = panel._proposal_snapshot()
            self.assertEqual(data["total"], 2)
            self.assertEqual(data["items"], [{"name": "primeira", "marker_present": False, "versionada": None},
                                             {"name": "segunda", "marker_present": True, "versionada": None}])
            self.assertNotIn("signature_valid", json.dumps(data))

    def test_verificacao_da_proposta_distingue_etapa_e_arquivo_alterado(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / "propostas"
            directory.mkdir()
            diff = directory / "exemplo.diff"
            diff.write_text("diff", encoding="utf-8")
            (directory / "APROVADO-exemplo").write_text("marcador", encoding="utf-8")
            with mock.patch.object(panel, "ROOT", root):
                with mock.patch.object(panel, "_verify", return_value="$ p8_verificar (exit=1)\n\nFALHA 4: não aplica"):
                    result = panel._proposal_check("exemplo")
                self.assertEqual((result["state"], result["failed_check"]), ("blocked", 4))
                self.assertEqual(len(result["diff_sha256"]), 64)
                def changed(*_args, **_kwargs):
                    diff.write_text("outro diff", encoding="utf-8")
                    return "$ p8_verificar (exit=0)\n\nPODE APLICAR: exemplo"
                with mock.patch.object(panel, "_verify", side_effect=changed):
                    self.assertEqual(panel._proposal_check("exemplo")["state"], "unknown")
                with self.assertRaises(ValueError):
                    panel._proposal_check("../exemplo")

    def test_tarefa_diferencia_configuracao_do_resultado(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "config/janela-tarefas.txt"
            path.parent.mkdir()
            path.write_text("avaliar-decisor|daily|300|||comando\n", encoding="utf-8")
            state = root / "estado.json"
            state.write_text(json.dumps({"avaliar-decisor": {"last_result": "skipped", "last_finished": "2026-10-27T12:00:00-03:00"}}))
            with mock.patch.object(panel, "ROOT", root), mock.patch.object(panel, "MAINTENANCE_STATE", state):
                data = panel._maintenance_tasks()
            self.assertEqual(data["history_state"], "ok")
            self.assertEqual(data["tasks"][0]["last_result"], "skipped")

    def test_chat_http_200_nao_afirma_funcionalidade_completa(self):
        connection = mock.Mock()
        connection.getresponse.return_value.status = 200
        with mock.patch.object(panel.http.client, "HTTPConnection", return_value=connection):
            result = panel._chat_snapshot()
        self.assertEqual((result["state"], result["http_status"]), ("ok", 200))
        self.assertEqual(result["source_ref"], "127.0.0.1:3080/health")
        connection.close.assert_called_once()

    def test_modelos_mantem_origem_e_amostra(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "config/capivara/capacidades.json"
            path.parent.mkdir(parents=True)
            data = {"gerado_em": "2026-10-27", "modelos": {"local/teste": {
                "catalogo": {"janela": 1024, "fonte": "catálogo", "lido_em": "2026-10-26"},
                "medido": [{"metrica": "acerto", "valor": 0.5, "amostra": 4, "data": "2026-10-26", "protocolo": "ensaio"}]}}}
            path.write_text(json.dumps(data), encoding="utf-8")
            with mock.patch.object(panel, "ROOT", root):
                result = panel._model_snapshot()
            self.assertEqual(result["state"], "ok")
            self.assertEqual(result["models"][0]["metrics"][0]["amostra"], 4)
            self.assertEqual(result["models"][0]["source"], "catálogo")

    def test_busca_separa_sem_resultado_de_falha(self):
        with mock.patch.object(panel, "_verify", return_value="$ busca_texto  (exit=1)\n\nnenhuma ocorrência"):
            result = panel._wiki_search("palavra", "texto")
        self.assertIsNone(result["results"][0]["error"])
        with mock.patch.object(panel, "_verify", return_value="$ busca_semantica  (exit=2)\n\nerro"):
            result = panel._wiki_search("palavra", "sentido")
        self.assertEqual(result["results"][0]["error"], "fonte indisponível")
        with mock.patch.object(panel, "_verify", return_value="$ busca_semantica  (exit=0)\n\nAVISO: índice semântico ausente, vazio ou inválido"):
            result = panel._wiki_search("palavra", "sentido")
        self.assertEqual(result["results"][0]["error"], "fonte indisponível")
        with mock.patch.object(panel, "_verify", return_value="$ busca_semantica  (exit=0)\n\nAVISO: índice parcial"):
            result = panel._wiki_search("palavra", "sentido")
        self.assertTrue(result["results"][0]["partial"])
        with self.assertRaises(ValueError):
            panel._wiki_search("palavra\noutra", "texto")

    def test_cache_agrupa_consultas_concorrentes(self):
        calls = []
        def collect():
            calls.append(1)
            time.sleep(0.04)
            return {"schema_version": 1}
        panel._STATUS_CACHE = panel._STATUS_CACHE_AT = None
        with mock.patch.object(panel, "collect", side_effect=collect):
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(lambda _: panel._cached_status(), range(8)))
        self.assertEqual(len(calls), 1)
        self.assertTrue(all(result is results[0] for result in results))
        panel._STATUS_CACHE = panel._STATUS_CACHE_AT = None


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_port, cls.old_origin = panel.PORT, panel.ALLOWED_ORIGIN
        cls.server = panel.ThreadingHTTPServer(("127.0.0.1", 0), panel.Handler)
        cls.server.daemon_threads = True
        panel.PORT = cls.server.server_address[1]
        panel.ALLOWED_ORIGIN = f"http://127.0.0.1:{panel.PORT}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        panel.PORT, panel.ALLOWED_ORIGIN = cls.old_port, cls.old_origin

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=3)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            conn.close()

    def test_html_e_status_sao_servidos_e_origem_cruzada_recusada(self):
        self.assertEqual(self.request("GET", "/prototipo")[0], 200)
        self.assertEqual(self.request("GET", "/prototipo.js")[0], 200)
        with mock.patch.object(panel, "_cached_status", return_value={"schema_version": 1, "state": "ok"}):
            code, body, headers = self.request("GET", "/api/status")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["state"], "ok")
        self.assertIn("default-src 'none'", headers["Content-Security-Policy"])
        self.assertEqual(self.request("GET", "/api/status", headers={"Origin": "https://exemplo.invalid"})[0], 403)
        self.assertEqual(self.request("GET", "/prototipo", headers={"Host": "exemplo.invalid"})[0], 421)
        self.assertEqual(self.request("GET", "/nao-existe")[0], 404)


    def test_busca_exige_origem_json_e_entrada_valida(self):
        base = {"Origin": panel.ALLOWED_ORIGIN, "Content-Type": "application/json"}
        payload = json.dumps({"query": "painel", "mode": "texto"})
        self.assertEqual(self.request("POST", "/api/wiki/search", payload, {"Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.request("POST", "/api/wiki/search", payload, {"Origin": "https://exemplo.invalid", "Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.request("POST", "/api/wiki/search", payload, {"Origin": panel.ALLOWED_ORIGIN, "Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.request("POST", "/api/wiki/search", json.dumps({"query": "x" * 201}), base)[0], 400)
        self.assertEqual(self.request("POST", "/api/wiki/search", json.dumps({"query": "a\nb"}), base)[0], 400)
        self.assertEqual(self.request("POST", "/api/wiki/search", json.dumps({"query": "teste", "mode": "livre"}), base)[0], 400)
        with mock.patch.object(panel, "_verify", return_value="$ busca_texto  (exit=0)\n\nmemoria/obsidian/a.md:1: texto"):
            code, body, _ = self.request("POST", "/api/wiki/search", payload, base)
        self.assertEqual(code, 200)
        self.assertIsNone(json.loads(body)["results"][0]["error"])
        self.assertEqual(self.request("PUT", "/api/wiki/search")[0], 405)


    def test_busca_simultanea_recebe_ocupado(self):
        self.assertTrue(panel._WIKI_LOCK.acquire(blocking=False))
        try:
            code, _, _ = self.request("POST", "/api/wiki/search", '{"query":"painel","mode":"texto"}',
                                      {"Origin": panel.ALLOWED_ORIGIN, "Content-Type": "application/json"})
            self.assertEqual(code, 429)
        finally:
            panel._WIKI_LOCK.release()

    def test_verificacao_de_proposta_e_apenas_uma_leitura_de_origem_local(self):
        base = {"Origin": panel.ALLOWED_ORIGIN, "Content-Type": "application/json"}
        self.assertEqual(self.request("POST", "/api/proposals/verify", '{"name":"../x"}', base)[0], 400)
        with mock.patch.object(panel, "_proposal_check", return_value={"name": "exemplo", "state": "blocked", "failed_check": 4}):
            code, body, _ = self.request("POST", "/api/proposals/verify", '{"name":"exemplo"}', base)
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["failed_check"], 4)
        self.assertEqual(self.request("POST", "/api/proposals/verify", '{"name":"exemplo"}', {"Content-Type":"application/json"})[0], 403)


    def test_vault_so_abre_itens_da_lista_fechada_e_nao_tem_link_externo(self):
        for nome in panel.VAULT_ITENS.values():
            self.assertNotIn("..", nome)
            self.assertNotIn("/", nome)
        html = (Path(__file__).parent / "prototipo.html").read_text(encoding="utf-8")
        self.assertNotIn("obsidian://", html)
        self.assertNotIn('target="_blank"', html)

    def test_vault_item_mede_ausente_como_lacuna(self):
        raiz = panel.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            panel.ROOT = Path(tmp)
            try:
                data = panel._vault_item("inicio")
            finally:
                panel.ROOT = raiz
        self.assertEqual(data["state"], "unknown")
        self.assertIn("ausente", data["motivo"])

    def test_vault_caminho_recusa_saida_do_vault(self):
        for ruim in ("../../etc/passwd.md", "/etc/passwd.md", "entradas/../../../x.md", "naoexiste.txt"):
            self.assertIsNone(panel._vault_caminho(ruim), ruim)

    def test_conversa_valida_e_grava_so_formato_esperado(self):
        with tempfile.TemporaryDirectory() as tmp:
            antes = panel.CONVERSAS_DIR
            panel.CONVERSAS_DIR = Path(tmp)
            try:
                self.assertIsNone(panel._conversa_gravar({"mensagens": [{"role": "system", "content": "x"}]}))
                self.assertIsNone(panel._conversa_gravar({"mensagens": [{"role": "user", "content": "x"}], "id": "../../etc"}))
                salvo = panel._conversa_gravar({"titulo": "Teste", "mensagens": [{"role": "user", "content": "oi"}]})
                self.assertIsNotNone(salvo)
                self.assertEqual(panel._conversa_caminho(salvo["id"]).name, salvo["id"] + ".json")
                self.assertTrue(panel._conversa_apagar(salvo["id"]))
                self.assertFalse(panel._conversa_apagar(salvo["id"]))
            finally:
                panel.CONVERSAS_DIR = antes

if __name__ == "__main__":
    unittest.main()
