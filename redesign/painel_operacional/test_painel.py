#!/usr/bin/env python3
"""Verifica o contrato local do painel sem acessar os serviços de produção."""
import collections
import http.client
import importlib.util
import json
import os
import re
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
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
        for name in ("conhecimento-busca", "conhecimento-consulta", "conhecimento-escopo", "wiki-mode", "wiki-source", "wiki-results",
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
        with mock.patch.object(panel.http.client, "HTTPConnection", return_value=connection) as conexao:
            result = panel._chat_snapshot()
        self.assertEqual((result["state"], result["http_status"]), ("ok", 200))
        self.assertEqual((result["source"], result["source_ref"]), ("seth-gateway", "127.0.0.1:20126/"))
        conexao.assert_called_once_with("127.0.0.1", 20126, timeout=3)
        connection.request.assert_called_once_with("GET", "/")
        connection.close.assert_called_once()

    def test_sem_leitura_lista_so_fontes_desconhecidas_ou_ausentes(self):
        ok = {"state": "ok"}
        services = [{"unit": "a.service", "state": "ok"}, {"unit": "b.service", "state": "ausente"}]
        timers = [{"unit": "c.timer", "state": "unknown"}]
        # 17/11/2026 (D9): 'ausente' já aparece separado; sem_leitura lista só o que não foi lido (unknown).
        self.assertEqual(panel._fontes_sem_leitura(services, timers, ok, ok, ok, ok, ok), ["c.timer"])
        self.assertEqual(panel._fontes_sem_leitura([{"unit": "a.service", "state": "ok"}], [], ok,
                                                   {"state": "unknown"}, ok, ok, ok),
                         ["Conversa com a Seth (gateway)"])
        self.assertEqual(panel._fontes_sem_leitura([], [], ok, ok, ok, ok, ok), [])

    def test_unidade_inexistente_vira_ausente_e_nao_inactive_nem_unknown(self):
        nao_existe = "$ unidade (exit=0)\n\nId=laya-roteador.service\nLoadState=not-found\nActiveState=inactive\nSubState=dead\n"
        with mock.patch.object(panel, "_verify", return_value=nao_existe):
            servico = panel._service_snapshot("laya-roteador.service")
        texto = "unidade não existe no escopo do usuário desta Máquina"  # C5 (16/11/2026): systemctl --user, não o sistema todo
        self.assertEqual((servico["state"], servico["error"]), ("ausente", texto))
        timer_nao = "Id=agata-vault-inbox.timer\nLoadState=not-found\nActiveState=inactive\nSubState=dead\n"
        with mock.patch.object(panel.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=timer_nao)):
            timer = panel._timer_snapshot("agata-vault-inbox.timer")
        self.assertEqual((timer["state"], timer["error"], timer["execution"]["state"]),
                         ("ausente", texto, "ausente"))
        self.assertEqual(panel._overall_state(["ok", "ausente"]), "warning")

    def test_lacunas_separam_unidade_ausente_de_inativa(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ESTADO.md").write_text("## Serviços (boot)\n- `laya-roteador.service` (declarada)\n"
                                            "- `seth-escriba.service` (declarada)\n- `ollama.service` (declarada)\n\n## Outra\n",
                                            encoding="utf-8")

            def systemctl(argv, **_kwargs):
                unit, sistema = argv[-1], "--user" not in argv
                if unit == "seth-escriba.service" and not sistema:
                    return SimpleNamespace(returncode=0, stdout="LoadState=loaded\nActiveState=inactive\n")
                if unit == "ollama.service" and sistema:
                    return SimpleNamespace(returncode=0, stdout="LoadState=loaded\nActiveState=active\n")
                return SimpleNamespace(returncode=0, stdout="LoadState=not-found\nActiveState=inactive\n")

            with mock.patch.object(panel, "ROOT", root), mock.patch.object(panel.subprocess, "run", side_effect=systemctl):
                data = panel._lacunas_snapshot()
        por_nome = {item["nome"]: item for item in data["items"]}
        self.assertEqual((por_nome["laya-roteador.service"]["state"], por_nome["laya-roteador.service"]["motivo"]),
                         ("ausente", "unidade não existe no escopo do usuário desta Máquina"))
        self.assertEqual(por_nome["seth-escriba.service"]["motivo"], "declarada no boot e inativa agora")
        self.assertNotIn("ollama.service", por_nome)

    def test_integracoes_incluem_painel_e_vigia_com_rotulo_e_nome_valido(self):
        self.assertIn("painel-operacional.service", panel.INTEGRATION_ALLOWLIST)
        self.assertIn("agata-vigia@claude.service", panel.INTEGRATION_ALLOWLIST)
        self.assertEqual(panel.INTEGRATION_ROTULOS["painel-operacional.service"], "Painel operacional")
        self.assertEqual(panel.INTEGRATION_ROTULOS["agata-vigia@claude.service"], "Vigia do Claude")
        # Mesmo formato que o verificador aceita para unidade de usuário (inclui `@` de instância).
        formato = re.compile(r"[a-z0-9][a-z0-9_.@-]{0,80}\.(?:service|timer|socket|target)")
        self.assertTrue(all(formato.fullmatch(unit) for unit in panel.INTEGRATION_ALLOWLIST))
        with mock.patch.object(panel, "_verify", return_value="$ unidade (exit=0)\n\nLoadState=loaded\nActiveState=active\nSubState=running\n") as verify:
            panel._service_snapshot("agata-vigia@claude.service")
        self.assertEqual(verify.call_args.kwargs, {"consulta": "agata-vigia@claude.service"})
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel, "ROOT", Path(tmp)), \
                mock.patch.object(panel, "_service_snapshot", side_effect=lambda unit: {"unit": unit, "state": "ok"}):
            detalhes = panel._details_snapshot()
        por_unidade = {item["unit"]: item for item in detalhes["integrations"]}
        self.assertEqual(por_unidade["agata-vigia@claude.service"]["rotulo"], "Vigia do Claude")
        self.assertNotIn("rotulo", por_unidade["piper-tts.service"])

    def test_painel_nao_cita_o_chat_antigo_e_rotula_a_porta_do_ouvido(self):
        fonte = (HERE / "server.py").read_text(encoding="utf-8") + (HERE / "nova_versao_painel.py").read_text(encoding="utf-8")
        for proibido in ("librechat", "3080"):
            self.assertNotIn(proibido, fonte.lower())
        self.assertIn("ouvido (porta 20137)", (HERE / "nova_versao_painel.py").read_text(encoding="utf-8"))

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

    def test_upload_de_fonte_aceita_md_e_recusa_o_resto(self):
        import os
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        antigo = os.environ.get("AGATA_NV_DIR")
        os.environ["AGATA_NV_DIR"] = tmp.name + "/dados"          # nunca escreve nos dados reais
        base = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin",
                "Content-Type": "application/octet-stream", "X-Extensao": "md", "X-Nome": "nota%20teste.md"}
        try:
            code, body, _ = self.request("POST", "/api/nova-versao/upload", b"# Nota\nhortas\n", base)
            self.assertEqual(code, 201)
            sha = json.loads(body)["sha256"]
            code2, body2, _ = self.request("POST", "/api/nova-versao/upload", b"# Nota\nhortas\n", base)
            self.assertEqual((code2, json.loads(body2)["duplicado"]), (200, True))
            self.assertEqual(self.request("POST", "/api/nova-versao/upload", b"x", {**base, "Origin": "http://evil"})[0], 403)
            self.assertEqual(self.request("POST", "/api/nova-versao/upload", b"x", {**base, "Content-Type": "application/json"})[0], 415)
            self.assertEqual(self.request("POST", "/api/nova-versao/upload", b"x", {**base, "X-Extensao": "exe"})[0], 422)
            self.assertEqual(self.request("POST", "/api/nova-versao/upload", b"\x7fELF\x02", base)[0], 422)
            entrada = Path(tmp.name) / "dados" / "alexandria" / "entrada"
            self.assertTrue((entrada / f"{sha}.md").exists())
            self.assertEqual(list(entrada.glob(".up-*")), [])      # nenhum temporário sobrou
        finally:
            if antigo is None:
                os.environ.pop("AGATA_NV_DIR", None)
            else:
                os.environ["AGATA_NV_DIR"] = antigo
            tmp.cleanup()

    def test_upload_acima_do_teto_e_recusado_antes_de_ler(self):
        base = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin",
                "Content-Type": "application/octet-stream", "X-Extensao": "md"}
        big = {**base, "Content-Length": str(26 * 1024 * 1024)}     # 26 MiB > 25 MiB: 413 pelo cabeçalho
        self.assertEqual(self.request("POST", "/api/nova-versao/upload", b"x", big)[0], 413)

    def test_html_e_status_sao_servidos_e_origem_cruzada_recusada(self):
        self.assertEqual(self.request("GET", "/prototipo")[0], 200)
        self.assertEqual(self.request("GET", "/prototipo.js")[0], 200)
        # Operator Console agora vive na seção Qualidade: a tela antiga redireciona; só o script continua servido.
        status, _, console_headers = self.request("GET", "/operator_console/")
        self.assertEqual(status, 302)
        self.assertEqual(console_headers["Location"], "/prototipo#qualidade")
        self.assertEqual(self.request("GET", "/operator_console/index.html")[0], 404)
        self.assertEqual(self.request("GET", "/operator_console/app.js")[0], 200)
        self.assertEqual(self.request("GET", "/operator_console/style.css")[0], 404)
        _, _, panel_headers = self.request("GET", "/prototipo")
        self.assertIn("frame-ancestors 'none'", panel_headers["Content-Security-Policy"])
        with mock.patch.object(panel, "_cached_status", return_value={"schema_version": 1, "state": "ok"}):
            code, body, headers = self.request("GET", "/api/status")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["state"], "ok")
        self.assertIn("default-src 'none'", headers["Content-Security-Policy"])
        self.assertEqual(self.request("GET", "/api/status", headers={"Origin": "https://exemplo.invalid"})[0], 403)
        self.assertEqual(self.request("GET", "/prototipo", headers={"Host": "exemplo.invalid"})[0], 421)
        self.assertEqual(self.request("GET", "/nao-existe")[0], 404)

    def test_status_e_capacidades_nao_citam_o_chat_antigo(self):
        def fake_verify(command, **_arguments):
            if command == "unidade":
                body = "LoadState=loaded\nActiveState=active\nSubState=running\n"
            elif command == "git_status":
                body = "## main...origin/main\n"
            elif command == "git_log":
                body = "abc123def456 mensagem de exemplo\n"
            else:
                raise AssertionError("comando inesperado no teste")
            return f"$ {command} (exit=0)\n\n" + body

        gateway = {"state": "ok", "http_status": 200, "source": "seth-gateway", "source_ref": "127.0.0.1:20126/"}
        with tempfile.TemporaryDirectory() as tmp:
            patches = [mock.patch.object(panel, "ROOT", Path(tmp)),
                       mock.patch.object(panel, "MAINTENANCE_STATE", Path(tmp) / "estado.json"),
                       mock.patch.object(panel, "_verify", side_effect=fake_verify),
                       # 17/11/2026 (D9): ausente não entra em sem_leitura; aqui a leitura do timer não foi feita (unknown).
                       mock.patch.object(panel, "_timer_snapshot", side_effect=lambda unit: {"unit": unit, "state": "unknown"}),
                       mock.patch.object(panel, "_chat_snapshot", return_value=gateway),
                       mock.patch.object(panel, "_unidade_ativa", return_value=True),
                       mock.patch.object(panel, "_http_ok", return_value=True)]
            panel._STATUS_CACHE = panel._STATUS_CACHE_AT = None
            panel._CACHE_CURTO.clear()
            for patch in patches:
                patch.start()
            try:
                status, corpo_status, _ = self.request("GET", "/api/status")
                status_cap, corpo_cap, _ = self.request("GET", "/api/capacidades")
            finally:
                for patch in reversed(patches):
                    patch.stop()
                panel._STATUS_CACHE = panel._STATUS_CACHE_AT = None
                panel._CACHE_CURTO.clear()
        self.assertEqual((status, status_cap), (200, 200))
        for corpo in (corpo_status, corpo_cap):
            texto = corpo.decode("utf-8").lower()
            self.assertNotIn("3080", texto)
            self.assertNotIn("librechat", texto)
        self.assertEqual(json.loads(corpo_status)["chat"]["source_ref"], "127.0.0.1:20126/")
        conversar = next(item for item in json.loads(corpo_cap)["items"] if item["id"] == "conversar")
        self.assertEqual(conversar["source"], "seth-gateway · 127.0.0.1:20126")
        self.assertIn("127.0.0.1:20126", corpo_cap.decode("utf-8"))
        self.assertIn("agata-manutencao.timer", json.loads(corpo_status)["sem_leitura"])

    def test_capacidades_e_lacunas_nao_repetem_a_consulta_em_seguida(self):
        vazio = {"schema_version": 1, "state": "ok", "items": []}
        panel._CACHE_CURTO.clear()
        try:
            with mock.patch.object(panel, "_capacidades_snapshot", return_value=vazio) as capacidades, \
                    mock.patch.object(panel, "_lacunas_snapshot", return_value=vazio) as lacunas:
                for _ in range(2):
                    self.assertEqual(self.request("GET", "/api/capacidades")[0], 200)
                    self.assertEqual(self.request("GET", "/api/lacunas")[0], 200)
            self.assertEqual((capacidades.call_count, lacunas.call_count), (1, 1))
        finally:
            panel._CACHE_CURTO.clear()

    def test_cache_curto_tem_lock_por_nome_e_rota_lenta_nao_segura_a_outra(self):
        # C6 (16/11/2026): cada nome de cache tem o seu lock; a produção lenta de um nome não prende o outro.
        self.assertIsNot(panel._lock_do_cache_curto("teste-a"), panel._lock_do_cache_curto("teste-b"))
        self.assertIs(panel._lock_do_cache_curto("teste-a"), panel._lock_do_cache_curto("teste-a"))
        entrou, sai, rapida = threading.Event(), threading.Event(), {}

        def lenta():
            entrou.set()
            sai.wait(5)
            return {"lenta": True}

        def outra_rota():
            rapida["valor"] = panel._cached_curto("teste-rapida", lambda: {"rapida": True})

        fio_lenta = threading.Thread(target=panel._cached_curto, args=("teste-lenta", lenta), daemon=True)
        fio_lenta.start()
        try:
            self.assertTrue(entrou.wait(5))
            fio_rapida = threading.Thread(target=outra_rota, daemon=True)
            fio_rapida.start()
            fio_rapida.join(2)
            self.assertFalse(fio_rapida.is_alive(), "a rota rápida ficou presa atrás da lenta")
            self.assertEqual(rapida.get("valor"), {"rapida": True})
        finally:
            sai.set()
            fio_lenta.join(5)
            for chave in ("teste-lenta", "teste-rapida"):
                panel._CACHE_CURTO.pop(chave, None)

    def test_get_conversa_salva_devolve_schema_e_id_e_recusa_ausente(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel.armazem, "CONVERSAS_DIR", Path(tmp)):
            conversa_id = "0123456789ab"
            panel._conversa_gravar({"id": conversa_id, "titulo": "Importada", "mensagens": [{"role": "user", "content": "oi"}]})
            status, body, _ = self.request("GET", f"/api/seth/conversa?id={conversa_id}")
            self.assertEqual(status, 200)
            dados = json.loads(body)
            self.assertEqual((dados["schema_version"], dados["id"]), (1, conversa_id))
            headers = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin",
                       "Content-Type": "application/json"}
            status_salvar, body_salvar, _ = self.request("POST", "/api/seth/conversa",
                json.dumps(dados).encode("utf-8"), headers)
            self.assertEqual(status_salvar, 200)
            self.assertEqual(json.loads(body_salvar)["id"], conversa_id)
            self.assertEqual(len(list(Path(tmp).glob("*.json"))), 1)
            self.assertEqual(self.request("GET", "/api/seth/conversa?id=aaaaaaaaaaaa")[0], 404)


    def test_leituras_de_api_recusam_origem_cruzada_mas_a_extensao_passa(self):
        for rota in ("/api/seth/conversas", "/api/eventos", "/api/lacunas", "/api/relay-council/state"):
            self.assertEqual(self.request("GET", rota, headers={"Origin": "https://exemplo.invalid"})[0], 403, rota)
            self.assertEqual(self.request("GET", rota, headers={"Sec-Fetch-Site": "cross-site"})[0], 403, rota)
        # as rotas da extensão seguem o cabeçalho do executor, não a origem do navegador
        self.assertEqual(self.request("GET", "/api/relay-council/focos", headers={"Origin": "chrome-extension://x"})[0], 403)
        code, body, _ = self.request("GET", "/api/relay-council/focos",
                                     headers={"Origin": "chrome-extension://x", "X-Relay-Client": panel.RELAY_CLIENT_ID})
        self.assertEqual(code, 200)

    def test_abrir_recusa_corpo_invalido_limita_fila_e_frequencia(self):
        base = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json"}
        for tamanho in ("-1", "abc", "513"):
            self.assertEqual(self.request("POST", "/api/abrir", "{}", {**base, "Content-Length": tamanho})[0], 400, tamanho)
        panel.FOCOS_PENDENTES.clear()
        for _ in range(panel.FOCOS_MAX + 5):
            self.assertEqual(self.request("POST", "/api/abrir", json.dumps({"alvo": "deepseek"}), base)[0], 202)
        self.assertEqual(len(panel.FOCOS_PENDENTES), panel.FOCOS_MAX)
        panel.FOCOS_PENDENTES.clear()
        panel._OBSIDIAN_ULTIMA[0] = 0.0
        with mock.patch.object(panel.subprocess, "Popen") as popen:
            self.assertEqual(self.request("POST", "/api/abrir", json.dumps({"alvo": "obsidian"}), base)[0], 202)
            self.assertEqual(self.request("POST", "/api/abrir", json.dumps({"alvo": "obsidian"}), base)[0], 429)
            self.assertEqual(popen.call_count, 1)

    def test_abrir_librechat_responde_400_e_nao_enfileira_foco(self):
        # LibreChat saiu do painel (07/11/2026, atalho de ligar o sistema): o alvo fica fora da lista.
        base = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json"}
        panel.FOCOS_PENDENTES.clear()
        try:
            code, body, _ = self.request("POST", "/api/abrir", json.dumps({"alvo": "librechat"}), base)
            self.assertEqual(code, 400)
            self.assertIn(b"destino fora da lista", body)
            self.assertEqual(list(panel.FOCOS_PENDENTES), [])
        finally:
            panel.FOCOS_PENDENTES.clear()

    def test_abrir_conselho_pede_so_os_conselheiros_que_faltam(self):
        base = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json"}
        estado = SimpleNamespace(available_providers=lambda: ("deepseek", "gemini", "claude"))
        panel.FOCOS_PENDENTES.clear()
        panel._CONSELHO_ULTIMA.clear()
        with mock.patch.object(panel, "_council_state", return_value=estado):
            status, corpo = self.request("POST", "/api/abrir", json.dumps({"alvo": "conselho"}), base)[:2]
            self.assertEqual(status, 202)
            resposta = json.loads(corpo)
            self.assertEqual(resposta["abertos"], 3)
            self.assertEqual(sorted(resposta["faltando"]), sorted(set(panel.CONSELHEIROS) - {"deepseek", "gemini", "claude"}))
            self.assertEqual({p["site"] for p in panel.FOCOS_PENDENTES}, set(resposta["faltando"]))
            self.assertTrue(all(p["janela"] is False for p in panel.FOCOS_PENDENTES))
            n = len(panel.FOCOS_PENDENTES)
            self.request("POST", "/api/abrir", json.dumps({"alvo": "conselho"}), base)
            self.assertEqual(len(panel.FOCOS_PENDENTES), n)  # repetir o clique não duplica
        estado_cheio = SimpleNamespace(available_providers=lambda: panel.CONSELHEIROS)
        panel.FOCOS_PENDENTES.clear()
        panel._CONSELHO_ULTIMA.clear()
        with mock.patch.object(panel, "_council_state", return_value=estado_cheio):
            resposta = json.loads(self.request("POST", "/api/abrir", json.dumps({"alvo": "conselho"}), base)[1])
            self.assertEqual(resposta["faltando"], [])
            self.assertEqual(panel.FOCOS_PENDENTES, [])
        panel.FOCOS_PENDENTES.clear()

    def test_pagina_do_painel_nao_tem_script_inline_por_causa_da_csp(self):
        # A CSP serve script-src 'self': <script> sem src é bloqueado e o botão não faz nada.
        for nome in ("prototipo.html",):
            html = (Path(__file__).parent / nome).read_text(encoding="utf-8")
            inline = []

            class _Scripts(HTMLParser):
                def handle_starttag(self, tag, attrs):
                    if tag == "script" and not dict(attrs).get("src"):
                        inline.append(tag)

            _Scripts().feed(html)
            self.assertEqual([], inline, nome)
        self.assertEqual(self.request("GET", "/abrir.js", None, {"Host": f"127.0.0.1:{panel.PORT}", "Sec-Fetch-Site": "same-origin"})[0], 200)

    def test_urls_de_abrir_dos_conselheiros_batem_com_o_catalogo(self):
        # Kimi em www.kimi.com abre em chinês e o Qwen precisa abrir em inglês: Humano escolheu chat.qwen.ai e www.kimi.ai/en.
        import relay_catalog
        sites = {p["id"]: p["site"] for p in relay_catalog.PROVIDERS}
        for conselheiro in panel.CONSELHEIROS:
            self.assertEqual(panel.ABRIR_PROVEDORES[conselheiro], sites[conselheiro], conselheiro)

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

    def test_relay_catalog_and_evaluation_boundary(self):
        code, body, headers = self.request("GET", "/api/relay-council/catalog")
        self.assertEqual(code, 200)
        providers = json.loads(body)["providers"]
        self.assertEqual(len(providers), 9)
        self.assertNotIn("perplexity", {provider["id"] for provider in providers})
        self.assertIn("no-store", headers["Cache-Control"])

        payload = {
            "task_id": "task-1", "provider": "gemini", "site": "gemini",
            "access_mode": "browser_tab", "state": "green", "ok": True,
            "text": "resposta formal", "latency_ms": 1234,
            "timestamp": "2026-10-28T10:00:00-03:00",
        }
        base = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin",
                "Content-Type": "application/json"}
        with mock.patch.object(panel, "_relay_store", return_value={"n": 42, "h": "abc123"}) as store:
            code, body, _ = self.request("POST", "/api/relay-council/evaluations", json.dumps(payload), base)
        self.assertEqual(code, 201)
        self.assertEqual(json.loads(body), {"schema_version": 1, "stored": True, "entry": 42,
                                            "hash": "abc123", "duplicate": False})
        store.assert_called_once_with(payload)

        self.assertEqual(self.request("POST", "/api/relay-council/evaluations", json.dumps(payload),
                                      {"Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.request("POST", "/api/relay-council/evaluations", json.dumps(payload),
                                      {**base, "Content-Type": "text/plain"})[0], 415)
        dom = {**payload, "access_mode": "browser_dom"}
        code, _, _ = self.request("POST", "/api/relay-council/evaluations", json.dumps(dom), base)
        self.assertEqual(code, 400)
        mismatched = {**payload, "provider": "copilot", "access_mode": "browser_tab"}
        self.assertEqual(self.request("POST", "/api/relay-council/evaluations", json.dumps(mismatched), base)[0], 400)

    def test_relay_evaluation_rejects_oversized_body_and_busy_cache(self):
        base = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin",
                "Content-Type": "application/json"}
        self.assertEqual(self.request("POST", "/api/relay-council/evaluations", "x" * 65537, base)[0], 413)
        payload = json.dumps({"task_id": "task-1", "provider": "gemini", "site": "gemini",
                              "access_mode": "browser_tab", "state": "green", "ok": True,
                              "text": "resposta", "timestamp": "2026-10-28T10:00:00-03:00"})
        large = json.dumps({"task_id": "task-1", "provider": "gemini", "site": "gemini",
                            "access_mode": "browser_tab", "state": "green", "ok": True,
                            "text": "r" * 5000, "timestamp": "2026-10-28T10:00:00-03:00"})
        self.assertTrue(panel._RELAY_LOCK.acquire(blocking=False))
        try:
            self.assertEqual(self.request("POST", "/api/relay-council/evaluations", payload, base)[0], 429)
        finally:
            panel._RELAY_LOCK.release()
        self.assertEqual(self.request("POST", "/api/relay-council/evaluations", large, base)[0], 413)
        deeply_nested = "{" + '"a":{' * 1500 + '"x":0' + "}" * 1501
        self.assertEqual(self.request("POST", "/api/relay-council/evaluations", deeply_nested, base)[0], 400)

    def test_json_post_aceita_ate_64k_e_recusa_acima(self):
        # teto geral de POST JSON (decisão do Humano, 05/11: "aumenta tudo"): 64 KB, não 4 KB
        base = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json"}
        medio = json.dumps({"acao": "nao-existe", "pad": "x" * 10000})
        self.assertEqual(self.request("POST", "/api/nova-versao/executar", medio, base)[0], 400)
        grande = json.dumps({"acao": "nao-existe", "pad": "x" * 70000})
        self.assertEqual(self.request("POST", "/api/nova-versao/executar", grande, base)[0], 413)

    def test_relay_quota_and_idempotent_receipts(self):
        base = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin",
                "Content-Type": "application/json"}
        payload = json.dumps({"task_id": "task-3", "provider": "gemini", "site": "gemini",
                              "access_mode": "browser_tab", "state": "green", "ok": True,
                              "text": "resposta", "timestamp": "2026-10-28T10:00:00-03:00"})
        with mock.patch.object(panel, "_relay_store", return_value={"n": 8, "h": "hash", "duplicate": True}):
            code, body, _ = self.request("POST", "/api/relay-council/evaluations", payload, base)
        self.assertEqual(code, 200)
        self.assertTrue(json.loads(body)["duplicate"])
        with mock.patch.object(panel, "_relay_store", side_effect=panel.RelayDailyQuotaExceeded):
            self.assertEqual(self.request("POST", "/api/relay-council/evaluations", payload, base)[0], 429)
        with mock.patch.object(panel, "_relay_store", side_effect=panel.RelayIdempotencyConflict):
            self.assertEqual(self.request("POST", "/api/relay-council/evaluations", payload, base)[0], 409)

    def test_relay_rate_limit_returns_retry_after(self):
        base = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin",
                "Content-Type": "application/json"}
        payload = json.dumps({"task_id": "task-rate", "provider": "gemini", "site": "gemini",
                              "access_mode": "browser_tab", "state": "green", "ok": True,
                              "text": "resposta", "timestamp": "2026-10-28T10:00:00-03:00"})
        with panel._RELAY_RATE_LOCK:
            panel._RELAY_REQUESTS.clear()
        try:
            with mock.patch.object(panel, "_RELAY_RATE_LIMIT", 1), \
                    mock.patch.object(panel, "_relay_store", return_value={"n": 1, "h": "hash"}):
                self.assertEqual(self.request("POST", "/api/relay-council/evaluations", payload, base)[0], 201)
                code, _, headers = self.request("POST", "/api/relay-council/evaluations", payload, base)
                self.assertEqual(code, 429)
                self.assertEqual(headers["Retry-After"], "60")
        finally:
            with panel._RELAY_RATE_LOCK:
                panel._RELAY_REQUESTS.clear()

    def test_relay_store_validates_sanitizes_and_appends_to_isolated_common_cache(self):
        cache, _catalog, _contract, _sanitizer = panel._relay_modules()
        payload = {"task_id": "task-2", "provider": "gemini", "site": "gemini",
                   "access_mode": "browser_tab", "state": "green", "ok": True,
                   "text": "resposta formal", "timestamp": "2026-10-28T10:00:00-03:00"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(cache, "ARQ", root / "cache" / "cache.jsonl"), \
                    mock.patch.object(cache, "LISTA_P20", root / "p20.txt"):
                receipt = panel._relay_store(payload)
                self.assertEqual(receipt["n"], 1)
                self.assertTrue(cache.verificar()[0])
                self.assertNotIn("task-2", cache.ler()[0]["texto"])
                retry = panel._relay_store(payload)
                self.assertEqual((retry["n"], retry["duplicate"]), (1, True))
                next_attempt = panel._relay_store({
                    **payload, "timestamp": "2026-10-28T10:01:00-03:00"
                })
                self.assertEqual(next_attempt["n"], 2)
                secret = "".join(("sk", "-", "d" * 20))
                with self.assertRaises(ValueError):
                    panel._relay_store({**payload, "text": secret})
                self.assertEqual(len(cache.ler()), 2)


    def test_vault_so_abre_itens_da_lista_fechada_e_nao_tem_link_externo(self):
        for nome in panel.VAULT_ITENS.values():
            self.assertNotIn("..", nome)
            self.assertNotIn("/", nome)
        html = (Path(__file__).parent / "prototipo.html").read_text(encoding="utf-8")
        self.assertNotIn("obsidian://", html)
        self.assertNotIn('target="_blank"', html)

    def test_vault_item_mede_ausente_como_lacuna(self):
        raiz = panel.armazem.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            panel.armazem.ROOT = Path(tmp)
            try:
                data = panel._vault_item("inicio")
            finally:
                panel.armazem.ROOT = raiz
        self.assertEqual(data["state"], "unknown")
        self.assertIn("ausente", data["motivo"])

    def test_vault_caminho_recusa_saida_do_vault(self):
        for ruim in ("../../etc/passwd.md", "/etc/passwd.md", "entradas/../../../x.md", "naoexiste.txt"):
            self.assertIsNone(panel._vault_caminho(ruim), ruim)

    def test_conversa_valida_e_grava_so_formato_esperado(self):
        with tempfile.TemporaryDirectory() as tmp:
            antes = panel.armazem.CONVERSAS_DIR
            panel.armazem.CONVERSAS_DIR = Path(tmp)
            try:
                self.assertIsNone(panel._conversa_gravar({"mensagens": [{"role": "system", "content": "x"}]}))
                self.assertIsNone(panel._conversa_gravar({"mensagens": [{"role": "user", "content": "x"}], "id": "../../etc"}))
                salvo = panel._conversa_gravar({"titulo": "Teste", "mensagens": [{"role": "user", "content": "oi"}]})
                self.assertIsNotNone(salvo)
                self.assertEqual(panel._conversa_caminho(salvo["id"]).name, salvo["id"] + ".json")
                self.assertTrue(panel._conversa_apagar(salvo["id"]))
                self.assertFalse(panel._conversa_apagar(salvo["id"]))
            finally:
                panel.armazem.CONVERSAS_DIR = antes

    def test_conversa_importada_com_mensagem_de_18973_caracteres_e_lida(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel.armazem, "CONVERSAS_DIR", Path(tmp)):
            conversa_id = "0123456789ab"
            salvo = panel._conversa_gravar({"id": conversa_id, "mensagens": [{"role": "user", "content": "x" * 18973}]})
            self.assertIsNotNone(salvo)
            lida = panel._conversa_ler(conversa_id)
            self.assertEqual(lida["schema_version"], 1)
            self.assertEqual(lida["id"], conversa_id)
            self.assertEqual(len(lida["mensagens"][0]["content"]), 18973)
            self.assertIsNotNone(panel.armazem._conversa_validar({"mensagens": [{"role": "user", "content": "x" * 65536}]}))
            self.assertIsNone(panel.armazem._conversa_validar({"mensagens": [{"role": "user", "content": "x" * 65537}]}))

    # Persistência do modelo escolhido (armazem.py): a conversa guarda o modelo dela e o de cada resposta.

    def test_conversa_grava_e_le_o_modelo_da_conversa_e_de_cada_resposta(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel.armazem, "CONVERSAS_DIR", Path(tmp)):
            conversa_id = "2123456789ab"
            salvo = panel._conversa_gravar({"id": conversa_id, "titulo": "Com modelo", "modelo": "seth-public",
                                            "mensagens": [{"role": "user", "content": "oi"},
                                                          {"role": "assistant", "content": "olá", "modelo": "seth-public"}]})
            self.assertIsNotNone(salvo)
            lida = panel._conversa_ler(conversa_id)
            self.assertEqual(lida["modelo"], "seth-public")
            self.assertEqual(lida["mensagens"][0], {"role": "user", "content": "oi"})
            self.assertEqual(lida["mensagens"][1], {"role": "assistant", "content": "olá", "modelo": "seth-public"})
            gravado = json.loads((Path(tmp) / (conversa_id + ".json")).read_text(encoding="utf-8"))
            self.assertEqual(gravado["modelo"], "seth-public")

    def test_conversa_sem_modelo_grava_e_le_seth_livre(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel.armazem, "CONVERSAS_DIR", Path(tmp)):
            conversa_id = "3123456789ab"
            salvo = panel._conversa_gravar({"id": conversa_id, "mensagens": [{"role": "user", "content": "oi"}]})
            self.assertEqual(salvo["modelo"], "seth-livre")
            self.assertEqual(panel._conversa_ler(conversa_id)["modelo"], "seth-livre")

    def test_gravacao_recusa_modelo_fora_da_lista_e_nao_escreve_arquivo(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel.armazem, "CONVERSAS_DIR", Path(tmp)):
            mensagens = [{"role": "user", "content": "oi"}]
            self.assertIsNone(panel._conversa_gravar({"id": "4123456789ab", "modelo": "seth-zai", "mensagens": mensagens}))
            self.assertIsNone(panel._conversa_gravar({"id": "4123456789ab",
                                                      "mensagens": [{"role": "assistant", "content": "x", "modelo": "seth-auto"}]}))
            self.assertIsNone(panel._conversa_gravar({"id": "4123456789ab", "modelo": ["seth-livre"], "mensagens": mensagens}))
            self.assertEqual(list(Path(tmp).glob("*.json")), [])

    def test_conversa_antiga_com_modelo_fora_da_lista_abre_com_o_padrao(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel.armazem, "CONVERSAS_DIR", Path(tmp)):
            conversa_id = "5123456789ab"
            antiga = {"titulo": "Antiga", "modelo": "seth-zai",
                      "mensagens": [{"role": "user", "content": "oi"}, {"role": "assistant", "content": "x", "modelo": "seth-gemini"}]}
            (Path(tmp) / (conversa_id + ".json")).write_text(json.dumps(antiga), encoding="utf-8")
            lida = panel._conversa_ler(conversa_id)
            self.assertIsNotNone(lida)
            self.assertEqual(lida["modelo"], "seth-livre")
            self.assertNotIn("modelo", lida["mensagens"][1])

    def test_http_salva_e_devolve_o_modelo_e_recusa_o_que_esta_fora(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel.armazem, "CONVERSAS_DIR", Path(tmp)):
            headers = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "application/json"}
            conversa_id = "6123456789ab"
            boa = {"id": conversa_id, "titulo": "HTTP", "modelo": "seth-public",
                   "mensagens": [{"role": "user", "content": "oi"}, {"role": "assistant", "content": "ok", "modelo": "seth-public"}]}
            self.assertEqual(self.request("POST", "/api/seth/conversa", json.dumps(boa).encode("utf-8"), headers)[0], 200)
            dados = json.loads(self.request("GET", f"/api/seth/conversa?id={conversa_id}")[1])
            self.assertEqual(dados["modelo"], "seth-public")
            self.assertEqual(dados["mensagens"][1]["modelo"], "seth-public")
            ruim = {**boa, "modelo": "seth-zai"}
            self.assertEqual(self.request("POST", "/api/seth/conversa", json.dumps(ruim).encode("utf-8"), headers)[0], 400)
            depois = json.loads(self.request("GET", f"/api/seth/conversa?id={conversa_id}")[1])
            self.assertEqual(depois["modelo"], "seth-public")

    def test_modelo_real_da_resposta_e_guardado_e_formato_ruim_e_descartado(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel.armazem, "CONVERSAS_DIR", Path(tmp)):
            conversa_id = "7123456789ab"
            salvo = panel._conversa_gravar({"id": conversa_id, "mensagens": [
                {"role": "user", "content": "oi", "modelo_real": "openai/gpt-oss-120b"},
                {"role": "assistant", "content": "ola", "modelo": "seth-livre", "modelo_real": "openai/gpt-oss-120b"},
                {"role": "assistant", "content": "tudo", "modelo": "seth-livre", "modelo_real": "lixo com espaço"}]})
            self.assertIsNotNone(salvo, "modelo_real fora do formato descarta o campo; não recusa a conversa")
            mensagens = panel._conversa_ler(conversa_id)["mensagens"]
            self.assertEqual(mensagens[0], {"role": "user", "content": "oi"})
            self.assertEqual(mensagens[1], {"role": "assistant", "content": "ola", "modelo": "seth-livre",
                                            "modelo_real": "openai/gpt-oss-120b"})
            self.assertEqual(mensagens[2], {"role": "assistant", "content": "tudo", "modelo": "seth-livre"})


class LeiturasCurtasTests(unittest.TestCase):
    """Rotas de leitura da Equipe, do backup, do egress, do perímetro, do CI e dos provedores (17/11/2026, D1-D7).
    Tudo em pasta falsa; o sistema e a rede entram como dublês. Nenhum teste lê o HD real, o estado real da Equipe,
    o diário real, nem executa perímetro, CI, restic ou systemctl."""

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

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        env = mock.patch.dict(os.environ, {
            "AGATA_EQUIPE_DIR": str(self.dir / "equipe"),
            "AGATA_EQUIPE_DIARIO": str(self.dir / "eventos.log"),
            "AGATA_BACKUP_STAGING_DIR": str(self.dir / "staging"),
            "AGATA_HD_BACKUP_CONFIG": str(self.dir / "hd-backup"),
            "AGATA_RESTIC_REPO": "",
            "AGATA_PERIMETRO_DIR": str(self.dir / "perimetro"),
            "AGATA_CI_DIR": str(self.dir / "ci"),
        })
        env.start()
        self.addCleanup(env.stop)
        self.config = self.dir / "equipe-ausentes.txt"
        cfg = mock.patch.object(panel, "EQUIPE_AUSENTES_CONFIG", self.config)
        cfg.start()
        self.addCleanup(cfg.stop)
        panel._CACHE_CURTO.clear()
        self.addCleanup(panel._CACHE_CURTO.clear)

    def request(self, method, path, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=5)
        try:
            conn.request(method, path, headers=headers or {})
            resposta = conn.getresponse()
            return resposta.status, resposta.read()
        finally:
            conn.close()

    def mesmo_site(self):
        return {"Sec-Fetch-Site": "same-origin"}

    def _json(self, caminho, dados):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    def _vigias_falsas(self):
        estados = {"agata-vigia@claude.service": "ok", "agata-vigia@codex.service": "warning",
                   "agata-vigia@gemini.service": "ausente"}

        def vigia(unit):
            estado = estados[unit]
            return {"unit": unit, "state": estado, "active_state": "active" if estado == "ok" else "inactive"}
        patch = mock.patch.object(panel, "_service_snapshot", side_effect=vigia)
        patch.start()
        self.addCleanup(patch.stop)

    def _equipe_com_partida(self):
        agora = "2026-11-17T08:00:00-03:00"
        eq = self.dir / "equipe"
        self._json(eq / "sessao.json", {
            "estado": "em_andamento", "base": "a" * 40,
            "presentes": {"claude": {"chegou_em": agora, "item": "x", "base": "a" * 40},
                          "codex": {"chegou_em": agora, "item": "y", "base": "a" * 40}},
            "esperados": ["claude", "codex", "gemini"], "matriz": []})
        self._json(eq / "estado-claude.json", {"agente": "claude", "itens": {
            "a": {"estado": "em_andamento", "caminhos": ["redesign/segredo-de-caminho.py"]},
            "b": {"estado": "pronto"}, "c": {"estado": "pronto"}}})
        self._json(eq / "ausencia-gemini.json", {"desde": agora, "motivo": "cota esgotada", "ate": ""})
        self.config.write_text("# ausentes offline\ncodex\n", encoding="utf-8")
        self._vigias_falsas()
        return agora

    def test_equipe_sem_arquivos_diz_sem_leitura_com_motivo(self):
        d = panel._equipe_snapshot()
        self.assertEqual(d["state"], "sem_leitura")
        self.assertIn("nenhuma partida", d["motivo"])
        for bloco in ("sessao", "itens", "vigias", "eventos", "ausentes"):
            self.assertEqual(d[bloco]["state"], "sem_leitura", bloco)
        self.assertTrue(d["source"] and d["observed_at"] and d["fresh_until"])

    def test_equipe_le_sessao_itens_ausentes_divergencias_e_vigias(self):
        agora = self._equipe_com_partida()
        with self.dir.joinpath("eventos.log").open("w", encoding="utf-8") as f:
            f.writelines(f"10:{n:02d} MAIN andou: linha {n}\n" for n in range(25))
        d = panel._equipe_snapshot()
        self.assertEqual(d["state"], "warning")
        self.assertEqual(d["sessao"]["presentes"], [{"agente": "claude", "desde": agora}, {"agente": "codex", "desde": agora}])
        self.assertEqual(d["sessao"]["esperados"], ["claude", "codex", "gemini"])
        ausentes = {a["agente"]: a for a in d["ausentes"]["itens"]}
        self.assertEqual(ausentes["codex"]["origem"], ["config"])
        self.assertEqual((ausentes["gemini"]["origem"], ausentes["gemini"]["motivo"]), (["ausencia"], "cota esgotada"))
        self.assertIn("codex: ausente no config e presente na sessão", d["divergencias"])
        self.assertIn("gemini: ausência declarada na sessão e fora do config", d["divergencias"])
        por_agente = {i["agente"]: i for i in d["itens"]["agentes"]}
        self.assertEqual((por_agente["claude"]["total"], por_agente["claude"]["por_estado"]),
                         (3, {"em_andamento": 1, "pronto": 2}))
        self.assertEqual([(v["agente"], v["state"]) for v in d["vigias"]["itens"]],
                         [("claude", "ok"), ("codex", "warning"), ("gemini", "ausente")])
        self.assertEqual(d["eventos"]["state"], "ok")
        self.assertEqual(len(d["eventos"]["linhas"]), 20)
        self.assertEqual(d["eventos"]["linhas"][-1], "10:24 MAIN andou: linha 24")
        bruto = json.dumps(d, ensure_ascii=False)
        self.assertNotIn("segredo-de-caminho", bruto)   # caminhos de arquivo dos itens não saem
        self.assertNotIn("caminhos", bruto)

    def test_equipe_nao_le_o_canal_de_mensagens(self):
        self._equipe_com_partida()
        (self.dir / "conversa.md").write_text("## mensagem\nSEGREDO-DO-CANAL\n", encoding="utf-8")
        self.assertNotIn("SEGREDO-DO-CANAL", json.dumps(panel._equipe_snapshot(), ensure_ascii=False))

    def test_equipe_so_aceita_nome_de_vigia_valido(self):
        self._equipe_com_partida()
        self._json(self.dir / "equipe" / "sessao.json", {
            "estado": "em_andamento", "base": "a" * 40, "presentes": {},
            "esperados": ["claude", "../etc", "Nome Ruim", "x" * 40]})
        d = panel._equipe_snapshot()
        self.assertEqual([v["unit"] for v in d["vigias"]["itens"]], ["agata-vigia@claude.service"])
        self.assertNotIn("etc", json.dumps(d))

    def test_equipe_diario_so_a_cauda_e_limite_por_linha(self):
        self._json(self.dir / "equipe" / "sessao.json", {"estado": "aguardando", "base": "a" * 40, "presentes": {}})
        with self.dir.joinpath("eventos.log").open("w", encoding="utf-8") as f:
            f.writelines(("L%05d " % n) + "x" * 400 + "\n" for n in range(2000))
        linhas = panel._equipe_snapshot()["eventos"]["linhas"]
        self.assertEqual(len(linhas), 20)
        self.assertTrue(all(len(l) <= 300 for l in linhas))
        self.assertTrue(linhas[-1].startswith("L01999"))

    def test_equipe_http_responde_e_recusa_origem_cruzada(self):
        status, corpo = self.request("GET", "/api/equipe", self.mesmo_site())
        self.assertEqual(status, 200)
        d = json.loads(corpo)
        self.assertTrue({"state", "source", "observed_at", "fresh_until"} <= set(d))
        self.assertEqual(self.request("GET", "/api/equipe", {"Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(self.request("POST", "/api/equipe", {"Sec-Fetch-Site": "same-origin"})[0], 405)

    def _backup_com_cache(self, hd_existe=True):
        hd = self.dir / "hd"
        if hd_existe:
            (hd / "restic-agata-local").mkdir(parents=True)
        (self.dir / "hd-backup").write_text(f"{hd}\n", encoding="utf-8")
        agora = datetime.now(timezone.utc)
        staging = self.dir / "staging"
        self._json(staging / "p12-cobertura.json", {
            "modelo-a": {"sha256": "f" * 64, "verificado_em": (agora - timedelta(days=2)).isoformat(), "snapshot": "56038913"},
            "modelo-b": {"sha256": "e" * 64, "verificado_em": (agora - timedelta(days=20)).isoformat(), "snapshot": "9433e3b8"},
        })
        (staging / "PENDENTE-HD-DESCONECTADO").write_text("x", encoding="utf-8")
        (staging / "PENDENTE-HD-DESCONECTADO-2").write_text("y", encoding="utf-8")
        return hd

    def test_backup_hd_regua_e_pendentes(self):
        hd = self._backup_com_cache()
        d = panel._backup_snapshot()
        self.assertEqual((d["hd"]["presente"], d["hd"]["repositorio_presente"]), (True, True))
        self.assertNotIn(str(hd), json.dumps(d))          # o caminho do HD não sai na resposta
        self.assertEqual(d["pendentes_hd"], 2)
        por = {r["recurso"]: r for r in d["recursos"]}
        self.assertTrue(por["modelo-a"]["dentro_da_regua"])
        self.assertFalse(por["modelo-b"]["dentro_da_regua"])
        self.assertAlmostEqual(por["modelo-a"]["idade_dias"], 2, delta=0.1)
        self.assertEqual(por["modelo-a"]["snapshot"], "56038913")
        self.assertNotIn("sha256", json.dumps(d))
        self.assertEqual((d["state"], d["regua_dias"]), ("warning", 14))

    def test_backup_tudo_na_regua_e_hd_desmontado(self):
        self._backup_com_cache(hd_existe=False)
        staging = self.dir / "staging" / "p12-cobertura.json"
        agora = datetime.now(timezone.utc)
        self._json(staging, {"modelo-a": {"verificado_em": (agora - timedelta(days=1)).isoformat(), "snapshot": "abc12345"}})
        d = panel._backup_snapshot()
        self.assertEqual((d["hd"]["presente"], d["hd"]["repositorio_presente"]), (False, False))
        self.assertIn("desconectado", d["hd"]["motivo"])
        self.assertEqual(d["state"], "ok")

    def test_backup_sem_cache_e_sem_restic(self):
        with mock.patch.object(panel.subprocess, "run", side_effect=AssertionError("restic não pode rodar")) as run:
            d = panel._backup_snapshot()
        run.assert_not_called()
        self.assertEqual(d["state"], "sem_leitura")
        self.assertIn("p12-cobertura.json", d["motivo"])
        self.assertEqual(d["recursos"], [])

    def test_backup_registro_sem_data_vira_item_sem_leitura(self):
        self._backup_com_cache()
        self._json(self.dir / "staging" / "p12-cobertura.json", {"quebrado": {"verificado_em": "ontem"}})
        d = panel._backup_snapshot()
        self.assertEqual((d["state"], d["recursos"][0]["state"], d["recursos"][0]["dentro_da_regua"]),
                         ("warning", "sem_leitura", None))

    def _crate(self, root, binario_antigo=False):
        crate = root / "redesign/rust/egress"
        (crate / "src").mkdir(parents=True)
        (crate / "target/release").mkdir(parents=True)
        fonte, cargo = crate / "src/main.rs", crate / "Cargo.toml"
        fonte.write_text("fn main() {}\n", encoding="utf-8")
        cargo.write_text("[package]\n", encoding="utf-8")
        os.utime(fonte, (1_700_000_000, 1_700_000_000))
        os.utime(cargo, (1_700_000_000, 1_700_000_000))
        egress = crate / "target/release/egress"
        socks = crate / "target/release/egress-socks5"
        egress.write_text("bin", encoding="utf-8")
        socks.write_text("bin", encoding="utf-8")
        os.utime(egress, (1_700_000_100, 1_700_000_100))
        os.utime(socks, (1_699_999_000 if binario_antigo else 1_700_000_100,) * 2)
        return crate

    def test_egress_em_dia_por_mtime_e_navegador_so_pela_chave(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel, "ROOT", Path(tmp)):
            self._crate(Path(tmp), binario_antigo=True)
            sistema = SimpleNamespace(returncode=0, stdout="LoadState=loaded\nEnvironment=HOME=/h AGATA_EGRESS_RUST=/home/u/.local/bin/agata-egress PATH=/bin\n")
            with mock.patch.object(panel.subprocess, "run", return_value=sistema) as run:
                d = panel._egress_snapshot()
        self.assertEqual(d["state"], "warning")
        por = {b["nome"]: b for b in d["binarios"]}
        self.assertEqual((por["egress"]["presente"], por["egress"]["em_dia"]), (True, True))
        self.assertEqual((por["egress-socks5"]["presente"], por["egress-socks5"]["em_dia"]), (True, False))
        self.assertIn("egress-socks5", d["motivo"])
        self.assertIs(d["navegador_usa_rust"], True)
        self.assertNotIn("/home/u/.local/bin", json.dumps(d))   # o valor da chave não sai
        self.assertEqual(d["paridade"], "sem registro")
        self.assertEqual(run.call_args.args[0][-1], panel.EGRESS_UNIT)
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_egress_tudo_em_dia_e_chave_ausente_ou_sistema_sem_leitura(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel, "ROOT", Path(tmp)):
            self._crate(Path(tmp))
            sem_chave = SimpleNamespace(returncode=0, stdout="LoadState=loaded\nEnvironment=PATH=/bin\n")
            with mock.patch.object(panel.subprocess, "run", return_value=sem_chave):
                d = panel._egress_snapshot()
            self.assertEqual((d["state"], d["navegador_usa_rust"]), ("ok", False))
            self.assertNotIn("motivo", d)
            with mock.patch.object(panel.subprocess, "run", side_effect=OSError("sem systemctl")):
                self.assertIsNone(panel._egress_snapshot()["navegador_usa_rust"])

    def test_egress_sem_crate_diz_sem_leitura(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel, "ROOT", Path(tmp)), \
                mock.patch.object(panel.subprocess, "run", side_effect=OSError("sem systemctl")):
            d = panel._egress_snapshot()
        self.assertEqual(d["state"], "sem_leitura")
        self.assertIn("src/", d["motivo"])

    def _ha(self, horas):
        """Carimbo com fuso, `horas` atrás no relógio do painel: a regra de idade (R1) não depende da data de hoje."""
        return (panel._now() - timedelta(hours=horas)).isoformat(timespec="seconds")

    def _json_perimetro(self, **campos):
        base = {"gerado_em": self._ha(1), "head": "ac08bf4f", "resultado_geral": "OK",
                "contagens": {"ok": 14, "skip": 0, "parcial": 0, "falha": 0},
                "controles": [{"id": "P-1", "veredito": "OK"}, {"id": "P-25-SELOS", "veredito": "OK"}]}
        base.update(campos)
        self._json(self.dir / "perimetro" / "ultimo.json", base)

    def test_perimetro_le_o_ultimo_resultado_e_nao_executa(self):
        self._json_perimetro(contagens={"ok": 13, "skip": 1, "parcial": 0, "falha": 0},
                             controles=[{"id": "P-1", "veredito": "OK"}, {"id": "P-2", "veredito": "SKIP"}],
                             extra="descartado", segredo="nao-sai")
        with mock.patch.object(panel.subprocess, "run", side_effect=AssertionError), \
                mock.patch.object(panel.subprocess, "Popen", side_effect=AssertionError):
            d = panel._perimetro_snapshot()
        self.assertEqual((d["state"], d["resultado_geral"], d["head"]), ("warning", "OK", "ac08bf4f"))
        self.assertEqual(d["controles"][1], {"id": "P-2", "veredito": "SKIP"})
        self.assertNotIn("nao-sai", json.dumps(d))
        self.assertNotIn("extra", d)
        self.assertIsInstance(d["idade_horas"], float)

    def test_perimetro_falha_ok_e_leituras_invalidas(self):
        self._json_perimetro(resultado_geral="FALHA", contagens={"ok": 13, "skip": 0, "parcial": 0, "falha": 1})
        self.assertEqual(panel._perimetro_snapshot()["state"], "falha")
        self._json_perimetro()
        self.assertEqual(panel._perimetro_snapshot()["state"], "ok")
        self._json_perimetro(resultado_geral="TALVEZ")
        self.assertEqual(panel._perimetro_snapshot()["state"], "sem_leitura")
        (self.dir / "perimetro" / "ultimo.json").write_text("{ quebrado", encoding="utf-8")
        self.assertEqual(panel._perimetro_snapshot()["state"], "sem_leitura")
        (self.dir / "perimetro" / "ultimo.json").write_text(" " * 300_000, encoding="utf-8")
        self.assertEqual(panel._perimetro_snapshot()["state"], "sem_leitura")
        self.assertEqual(panel._perimetro_snapshot()["motivo"], "ultimo.json do perímetro ilegível ou acima do limite")

    def test_ci_le_o_ultimo_resultado_e_nao_executa(self):
        self._json(self.dir / "ci" / "ultimo.json", {
            "gerado_em": self._ha(1), "head": "ac08bf4f", "ok": 2, "falha": 0,
            "linha_final": "CI LOCAL: TUDO OK",
            "passos": [{"nome": "testes SDD (pytest)", "ok": True}, {"nome": "suite adversarial", "ok": True}, {"nome": 7, "ok": True}]})
        with mock.patch.object(panel.subprocess, "run", side_effect=AssertionError):
            d = panel._ci_snapshot()
        self.assertEqual((d["state"], d["ok"], d["falha"], d["linha_final"]), ("ok", 2, 0, "CI LOCAL: TUDO OK"))
        self.assertEqual(len(d["passos"]), 2)   # o passo com nome que não é texto não entra
        self._json(self.dir / "ci" / "ultimo.json", {"gerado_em": self._ha(1), "ok": 1, "falha": 1,
                                                       "linha_final": "CI LOCAL: 1 passo(s) falharam",
                                                       "passos": [{"nome": "x", "ok": False}]})
        self.assertEqual(panel._ci_snapshot()["state"], "falha")
        self.assertEqual(self.request("GET", "/api/ci", self.mesmo_site())[0], 200)

    def test_ci_sem_arquivo_diz_sem_leitura(self):
        d = panel._ci_snapshot()
        self.assertEqual(d["state"], "sem_leitura")
        self.assertTrue(d["motivo"].startswith("o CI local ainda"))

    def _get_limpo(self, caminho):
        """GET na rota de leitura curta, com o cache curto zerado: uma leitura anterior não vence a gravada agora."""
        panel._CACHE_CURTO.clear()
        status, corpo = self.request("GET", caminho, self.mesmo_site())
        return status, json.loads(corpo)

    def test_resultado_gravado_ha_mais_de_24_h_nao_sai_ok(self):
        # R1 (17/11/2026): resultado de 30 h atrás sai "warning", com envelhecido e motivo; falha continua falha.
        velho = self._ha(30)
        ci_arq = self.dir / "ci" / "ultimo.json"
        self._json_perimetro(gerado_em=velho)
        d = panel._perimetro_snapshot()
        self.assertEqual((d["state"], d["envelhecido"], d["motivo"]), ("warning", True, "resultado gravado há 30 h"))
        self.assertGreater(d["idade_horas"], 24)
        self._json_perimetro(gerado_em=self._ha(1))
        d = panel._perimetro_snapshot()
        self.assertEqual((d["state"], d["envelhecido"]), ("ok", False))
        self.assertNotIn("motivo", d)
        self._json_perimetro(gerado_em=velho, resultado_geral="FALHA", contagens={"ok": 13, "skip": 0, "parcial": 0, "falha": 1})
        self.assertEqual((panel._perimetro_snapshot()["state"], panel._perimetro_snapshot()["envelhecido"]), ("falha", True))
        self._json_perimetro(gerado_em=velho)
        status, http_d = self._get_limpo("/api/perimetro")
        self.assertEqual((status, http_d["state"], http_d["envelhecido"], http_d["motivo"]), (200, "warning", True, "resultado gravado há 30 h"))
        self._json(ci_arq, {"gerado_em": velho, "head": "ac08bf4f", "ok": 2, "falha": 0,
                            "linha_final": "CI LOCAL: TUDO OK", "passos": [{"nome": "testes", "ok": True}]})
        c = panel._ci_snapshot()
        self.assertEqual((c["state"], c["envelhecido"], c["motivo"]), ("warning", True, "resultado gravado há 30 h"))
        self._json(ci_arq, {"gerado_em": velho, "head": "ac08bf4f", "ok": 1, "falha": 1,
                            "linha_final": "CI LOCAL: 1 passo(s) falharam", "passos": [{"nome": "x", "ok": False}]})
        self.assertEqual((panel._ci_snapshot()["state"], panel._ci_snapshot()["envelhecido"]), ("falha", True))
        status, http_c = self._get_limpo("/api/ci")
        self.assertEqual((status, http_c["state"], http_c["envelhecido"]), (200, "falha", True))
        self._json(ci_arq, {"gerado_em": velho, "head": "ac08bf4f", "ok": 2, "falha": 0,
                            "linha_final": "CI LOCAL: TUDO OK", "passos": [{"nome": "testes", "ok": True}]})
        status, http_c = self._get_limpo("/api/ci")
        self.assertEqual((status, http_c["state"], http_c["envelhecido"], http_c["motivo"]), (200, "warning", True, "resultado gravado há 30 h"))

    def test_provedores_vem_do_catalogo_e_nao_constroi_o_council(self):
        import relay_catalog
        antes = panel._COUNCIL
        with mock.patch.object(panel, "_council_state", side_effect=AssertionError("o Council não pode ser construído")):
            status, corpo = self.request("GET", "/api/provedores", self.mesmo_site())
        d = json.loads(corpo)
        self.assertEqual((status, d["state"], d["total"]), (200, "ok", 9))
        self.assertEqual({i["id"] for i in d["items"]}, {p["id"] for p in relay_catalog.PROVIDERS})
        self.assertEqual(set(d["items"][0]), {"id", "nome", "tipo", "acesso"})
        nomes = {i["nome"] for i in d["items"]}
        self.assertTrue({"Z.ai / GLM", "Le Chat / Mistral"} <= nomes)
        self.assertIs(panel._COUNCIL, antes)
        self.assertEqual(set(panel.ABRIR_PROVEDORES), {p["id"] for p in relay_catalog.PROVIDERS} | {"omniroute"})

    def test_leitura_com_erro_inesperado_nao_derruba_a_rota(self):
        def quebra():
            raise RuntimeError("detalhe interno do disco")
        d = panel._leitura_segura(quebra)
        self.assertEqual(d["state"], "sem_leitura")
        self.assertNotIn("detalhe interno", json.dumps(d))

    def test_rotas_de_leitura_respondem_com_campos_e_sem_executar(self):
        # Só o systemctl do navegador (leitura do egress) é permitido; perímetro, CI, restic e cargo não podem rodar.
        with mock.patch.object(panel.subprocess, "run", side_effect=AssertionError("nada executa")), \
                mock.patch.object(panel, "_navegador_usa_rust", return_value=None), \
                mock.patch.object(panel, "ROOT", self.dir):
            for rota in panel.LEITURAS_CURTAS:
                panel._CACHE_CURTO.clear()
                status, corpo = self.request("GET", rota, self.mesmo_site())
                self.assertEqual(status, 200, rota)
                d = json.loads(corpo)
                self.assertIn("state", d, rota)
                self.assertIn("observed_at", d, rota)
                self.assertIn("fresh_until", d, rota)
                self.assertIn("source", d, rota)


if __name__ == "__main__":
    unittest.main()
