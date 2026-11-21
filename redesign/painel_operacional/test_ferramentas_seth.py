#!/usr/bin/env python3
"""Ferramentas da Seth no painel (20/11/2026): só seth-livre, lista fixa, laço de até 5 rodadas, cache_anotar.

Nunca chama gateway nem MCP reais: gateway falso em porta livre; o MCP é trocado por função falsa.
"""
import http.client
import importlib.util
import json
import os
import stat
import subprocess
import tempfile
import time
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import chat_stream
import ferramentas_seth as fs

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("painel_ferramentas_teste", HERE / "server.py")
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)

MSG = [{"role": "user", "content": "oi"}]
ESQ_FALSOS = [{"type": "function", "function": {"name": n, "description": "", "parameters": {"type": "object"}}}
              for n in fs.NOMES_MCP] + [fs.ESQUEMA_ANOTAR, fs.ESQUEMA_AGATA_CODE]


def sse_chamada(nome, args="{}", id_="c1"):
    ev = {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": id_, "type": "function",
                                                   "function": {"name": nome, "arguments": args}}]}}]}
    return ["data: " + json.dumps(ev), "", "data: [DONE]", ""]


def sse_texto(texto):
    return ["data: " + json.dumps({"choices": [{"delta": {"content": texto}}]}), "", "data: [DONE]", ""]


class ChatStreamChamadasTests(unittest.TestCase):
    def test_tool_calls_viram_evento_chamadas_com_argumentos_juntados(self):
        parte = lambda a, nome="": "data: " + json.dumps({"choices": [{"delta": {"tool_calls": [
            {"index": 0, "id": "x", "function": {"name": nome, "arguments": a}}]}}]})
        evs = list(chat_stream.eventos_do_stream([parte('{"q":', "vault_buscar"), parte('"a"}'), "data: [DONE]"]))
        self.assertEqual(evs, [{"tipo": "chamadas", "chamadas": [{"id": "x", "nome": "vault_buscar", "argumentos": '{"q":"a"}'}]}])

    def test_seth_public_nao_manda_tools_e_livre_so_com_a_lista(self):
        self.assertNotIn("tools", chat_stream.montar_pedido(MSG, "seth-public", ferramentas=ESQ_FALSOS))
        self.assertNotIn("tools", chat_stream.montar_pedido(MSG, "seth-livre"))
        livre = chat_stream.montar_pedido(MSG, "seth-livre", ferramentas=ESQ_FALSOS)
        self.assertEqual({t["function"]["name"] for t in livre["tools"]}, set(fs.NOMES_PERMITIDOS))

    def test_descricao_nao_diz_mais_que_nao_ha_ferramentas(self):
        livre = [m for m in chat_stream.MODELOS_CHAT if m["id"] == "seth-livre"][0]
        self.assertNotIn("não há ferramentas", livre["descricao"])


class ListaFixaTests(unittest.TestCase):
    def test_memoria_acrescentar_nunca_oferecida_nem_executada(self):
        self.assertNotIn("memoria_acrescentar", fs.NOMES_PERMITIDOS)
        mcp_lista = {1: {"result": {"tools": [{"name": n, "inputSchema": {"type": "object"}}
                                               for n in fs.NOMES_MCP + ("memoria_acrescentar",)]}}}
        with mock.patch.object(fs, "_rpc_mcp", return_value=mcp_lista):
            fs._cache_esquemas.update(quando=0.0, lista=None)
            nomes = [f["function"]["name"] for f in fs.esquemas()]
            fs._cache_esquemas.update(quando=0.0, lista=None)
        self.assertEqual(nomes, list(fs.NOMES_MCP) + ["cache_anotar", "agata_code"])
        with mock.patch.object(fs, "_rpc_mcp") as rpc:
            self.assertIn("não permitida", fs.executar("memoria_acrescentar", '{"texto":"x"}'))
            rpc.assert_not_called()

    def test_mcp_fora_do_ar_oferece_so_cache_anotar_e_agata_code(self):
        with mock.patch.object(fs, "_rpc_mcp", side_effect=fs.ErroMCP("x")):
            fs._cache_esquemas.update(quando=0.0, lista=None)
            self.assertEqual([f["function"]["name"] for f in fs.esquemas()], ["cache_anotar", "agata_code"])

    def test_resultado_truncado_e_erro_do_mcp_vira_texto(self):
        longo = {1: {"result": {"content": [{"type": "text", "text": "a" * 30000}]}}}
        with mock.patch.object(fs, "_rpc_mcp", return_value=longo):
            r = fs.executar("query_canon", '{"doc":"REGRAS"}')
        self.assertLess(len(r), fs.MAX_RESULTADO + 100)
        self.assertIn("truncado", r)
        with mock.patch.object(fs, "_rpc_mcp", side_effect=fs.ErroMCP("tempo esgotado")):
            self.assertEqual(fs.executar("vault_buscar", "{}"), "erro: tempo esgotado")
        self.assertTrue(fs.executar("vault_buscar", "{isso não").startswith("erro:"))


class CacheAnotarTests(unittest.TestCase):
    def test_grava_com_autor_fixo_em_arquivo_temporario(self):
        cache = fs._cache_modulo()
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "cache.jsonl"
            with mock.patch.object(cache, "ARQ", arq):
                r = fs.executar("cache_anotar", json.dumps({"tipo": "nota", "texto": "lição de teste", "autor": "outro"}))
                self.assertIn('"ok": true', r)
                reg = json.loads(arq.read_text().splitlines()[0])
                self.assertEqual((reg["autor"], reg["tipo"]), ("Seth (painel)", "nota"))
                self.assertTrue(fs.executar("cache_anotar", '{"tipo":"diario","texto":"x"}').startswith("erro:"))
                self.assertTrue(fs.executar("cache_anotar", json.dumps({"tipo": "nota", "texto": "x" * 4001})).startswith("erro:"))
                self.assertEqual(len(arq.read_text().splitlines()), 1)


class LacoTests(unittest.TestCase):
    def test_chamada_fora_da_lista_nao_executa(self):
        pedidos = []
        def abrir(pedido):
            pedidos.append(pedido)
            return iter(sse_texto("fim"))
        with mock.patch.object(fs, "_rpc_mcp") as rpc, mock.patch.object(fs, "_cache_modulo") as cache:
            evs = list(fs.laco(abrir, iter(sse_chamada("rm_tudo")), {"messages": list(MSG)}))  # executor padrão
            rpc.assert_not_called()
            cache.assert_not_called()
        self.assertIn({"tipo": "estado", "texto": "ferramenta não permitida"}, evs)
        self.assertIn("não permitida", pedidos[0]["messages"][-1]["content"])

    def test_laco_para_em_cinco_rodadas_com_aviso(self):
        chamadas, abertas = [], []
        def exec_(nome, args):
            chamadas.append(nome)
            return "ok"
        def abrir(pedido):
            abertas.append(len(pedido["messages"]))
            return iter(sse_chamada("vault_buscar"))
        evs = list(fs.laco(abrir, iter(sse_chamada("vault_buscar")), {"messages": list(MSG)}, executor=exec_))
        self.assertEqual(len(chamadas), 5)
        self.assertEqual(len(abertas), 5)
        self.assertEqual(evs[-1], {"tipo": "fim"})
        self.assertIn("Limite de 5 rodadas", evs[-2]["delta"])
        self.assertEqual(sum(1 for e in evs if e["tipo"] == "estado"), 5)

    def test_rodada_devolve_assistant_com_tool_calls_e_tool_truncada(self):
        pedidos = []
        def abrir(pedido):
            pedidos.append(json.loads(json.dumps(pedido)))
            return iter(sse_texto("pronto"))
        evs = list(fs.laco(abrir, iter(sse_chamada("query_canon", '{"doc":"REGRAS"}', "id9")), {"messages": list(MSG)},
                           executor=lambda n, a: "r" * 30000))
        msgs = pedidos[0]["messages"]
        self.assertEqual(msgs[1]["tool_calls"][0]["id"], "id9")
        self.assertEqual((msgs[2]["role"], msgs[2]["tool_call_id"]), ("tool", "id9"))
        self.assertLess(len(msgs[2]["content"]), fs.MAX_RESULTADO + 100)
        self.assertEqual([e["tipo"] for e in evs], ["estado", "texto", "fim"])
        self.assertEqual(evs[0]["texto"], "consultando query_canon…")


# ---- Agata Code (lote 2, 20/11/2026): sempre com executável falso, nunca o opencode real -----------------------------------

FAKE_OPENCODE = """#!/usr/bin/env python3
import json, os, sys, time
modo = os.environ.get("FAKE_MODO", "")
open(os.environ["FAKE_REGISTRO"], "w").write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(), "env": sorted(os.environ)}))
if modo == "dorme":
    time.sleep(30)
if modo == "muda":
    open("novo.txt", "w").write("conteudo\\n")
texto = "x" * 20000 if modo == "longo" else "pronto"
print(json.dumps({"type": "step_start"}))
print(json.dumps({"type": "text", "part": {"type": "text", "text": texto}}))
"""


class AgataCodeBase(unittest.TestCase):
    """Repo git de mentira com origin/main, pasta de arquivo temporária e opencode falso."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.repo, self.arquivo, self.reg = base / "repo", base / "arquivo", base / "registro.json"
        self.repo.mkdir()
        git = lambda *a: subprocess.run(["git", "-C", str(self.repo), *a], check=True, capture_output=True,
                                        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                                             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
        git("init", "-q")
        (self.repo / "a.txt").write_text("a\n")
        git("add", "a.txt")
        git("commit", "-q", "-m", "c")
        git("update-ref", "refs/remotes/origin/main", "HEAD")
        (self.repo / "a.txt").write_text("sujeira no repo vivo\n")  # não pode aparecer na worktree
        self.bin = base / "opencode"
        self.bin.write_text(FAKE_OPENCODE)
        self.bin.chmod(self.bin.stat().st_mode | stat.S_IEXEC)
        self.patches = [mock.patch.object(fs, "REPO_RAIZ", self.repo), mock.patch.object(fs, "ARQUIVO_CODE", self.arquivo),
                        mock.patch.object(fs, "OPENCODE_BIN", self.bin),
                        mock.patch.object(fs, "ENV_CODE_PERMITIDAS", fs.ENV_CODE_PERMITIDAS + ("FAKE_REGISTRO", "FAKE_MODO")),
                        mock.patch.dict(os.environ, {"FAKE_REGISTRO": str(self.reg), "FAKE_MODO": "",
                                                     "SEGREDO_DE_TESTE": "nao-pode-passar"})]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        subprocess.run(["git", "-C", str(self.repo), "worktree", "prune"], capture_output=True)
        self.tmp.cleanup()

    def registro(self):
        return json.loads(self.reg.read_text())


class AgataCodeOferecidoTests(unittest.TestCase):
    def test_nao_e_oferecido_na_seth_public(self):
        self.assertNotIn("tools", chat_stream.montar_pedido(MSG, "seth-public", ferramentas=ESQ_FALSOS))
        livre = chat_stream.montar_pedido(MSG, "seth-livre", ferramentas=ESQ_FALSOS)
        self.assertIn("agata_code", {t["function"]["name"] for t in livre["tools"]})
        self.assertEqual(fs.ESQUEMA_AGATA_CODE["function"]["parameters"]["properties"]["tarefa"]["maxLength"], 4000)

    def test_esta_na_lista_fixa_e_o_esquema_so_pede_tarefa(self):
        self.assertIn("agata_code", fs.NOMES_PERMITIDOS)
        self.assertEqual(list(fs.ESQUEMA_AGATA_CODE["function"]["parameters"]["properties"]), ["tarefa"])


class AgataCodeDefinicaoTests(unittest.TestCase):
    def test_agente_do_repositorio_nega_commit_push_sudo_rede_e_env_e_manda_ler_e_anotar_no_cache(self):
        md = (HERE.parents[1] / ".opencode" / "agent" / "agata-code.md").read_text(encoding="utf-8")
        cabeca = md.split("---")[1]
        for negado in ('"git commit*": deny', '"git push*": deny', '"sudo*": deny', '"rm -rf*": deny',
                       '"curl*": deny', '"wget*": deny', '"*": deny', '"*.env": deny', "webfetch: deny"):
            self.assertIn(negado, cabeca)
        self.assertIn("edit: allow", cabeca)
        self.assertIn("model: agata/seth-livre", cabeca)
        for texto in ("AGENTS.md", "cache_conselho.py ler --n 20", '--autor "Agata Code"', "Meça antes de afirmar", ".env"):
            self.assertIn(texto, md)


class AgataCodeExecucaoTests(AgataCodeBase):
    def test_tarefa_vazia_ou_acima_de_4000_e_recusada_sem_criar_nada(self):
        for args in ({}, {"tarefa": ""}, {"tarefa": "   "}, {"tarefa": 5}, {"tarefa": "x" * 4001}, "texto"):
            r = fs.executar_agata_code(args)
            self.assertFalse(r["ok"], args)
            self.assertIn("tarefa", r["erro"])
        self.assertFalse(self.arquivo.exists())
        self.assertFalse(self.reg.exists())
        self.assertTrue(fs.executar("agata_code", '{"tarefa":""}').startswith("erro:"))

    def test_comando_com_agente_e_dir_na_worktree_nova_e_nunca_no_repo_vivo(self):
        r = fs.executar_agata_code({"tarefa": "diga oi"})
        reg = self.registro()
        argv = reg["argv"]
        self.assertEqual(argv[:5], ["run", "--agent", "agata-code", "--format", "json"])
        wt = argv[argv.index("--dir") + 1]
        self.assertEqual(argv[-2:], ["--", "diga oi"])
        self.assertNotEqual(Path(wt).resolve(), self.repo.resolve())
        self.assertTrue(Path(wt).resolve().is_relative_to(self.arquivo.resolve()))
        self.assertEqual(Path(reg["cwd"]).resolve(), Path(wt).resolve())
        self.assertTrue(r["ok"])
        self.assertEqual(r["resposta"], "pronto")
        self.assertEqual((self.repo / "a.txt").read_text(), "sujeira no repo vivo\n")  # o repo vivo não foi tocado

    def test_worktree_parte_de_origin_main_e_ambiente_sem_segredo(self):
        fs.executar_agata_code({"tarefa": "x"})
        reg = self.registro()
        wt = Path(reg["argv"][reg["argv"].index("--dir") + 1])
        self.assertTrue(wt.exists() is False or (wt / "a.txt").read_text() == "a\n")  # removida sem diff; se ficou, é de origin/main
        self.assertNotIn("SEGREDO_DE_TESTE", reg["env"])
        self.assertEqual(fs._env_code().keys() - set(fs.ENV_CODE_PERMITIDAS), set())  # o filtro só deixa a lista fixa
        self.assertNotIn("SEGREDO_DE_TESTE", fs._env_code())

    def test_sem_mudanca_remove_a_worktree_e_guarda_a_transcricao(self):
        r = fs.executar_agata_code({"tarefa": "só ler"})
        self.assertIsNone(r["worktree"])
        self.assertEqual(r["diff_stat"], "")
        self.assertFalse(any(self.arquivo.glob("*/worktree")))
        transcricao = Path(r["transcricao"])
        self.assertTrue(transcricao.is_file())
        self.assertIn('"type": "text"', transcricao.read_text())
        self.assertIn("sem mudanças", fs.texto_agata_code(r))

    def test_com_mudanca_guarda_a_worktree_e_devolve_diff_stat_resposta_e_caminhos(self):
        with mock.patch.dict(os.environ, {"FAKE_MODO": "muda"}):
            r = fs.executar_agata_code({"tarefa": "crie um arquivo"})
        self.assertTrue(r["ok"])
        self.assertTrue(Path(r["worktree"], "novo.txt").is_file())
        self.assertIn("novo.txt", r["diff_stat"])
        texto = fs.texto_agata_code(r)
        for parte in ("pronto", "novo.txt", r["worktree"], r["transcricao"]):
            self.assertIn(parte, texto)

    def test_timeout_respeitado_mata_o_agente(self):
        t0 = time.monotonic()
        with mock.patch.dict(os.environ, {"FAKE_MODO": "dorme"}):
            r = fs.executar_agata_code({"tarefa": "demora"}, timeout_s=1)
        self.assertLess(time.monotonic() - t0, 10)
        self.assertFalse(r["ok"])
        self.assertIn("tempo esgotado", r["erro"])
        self.assertIn("tempo esgotado", fs.texto_agata_code(r))
        self.assertEqual(fs.TIMEOUT_AGATA_CODE_S, 600)

    def test_resposta_longa_e_truncada(self):
        with mock.patch.dict(os.environ, {"FAKE_MODO": "longo"}):
            r = fs.executar_agata_code({"tarefa": "texto grande"})
        self.assertLess(len(r["resposta"]), fs.MAX_RESPOSTA_CODE + 100)
        self.assertIn("truncado", r["resposta"])

    def test_executavel_ausente_vira_erro_em_texto_e_nao_deixa_worktree(self):
        with mock.patch.object(fs, "OPENCODE_BIN", Path(self.tmp.name) / "nao-existe"):
            r = fs.executar_agata_code({"tarefa": "x"})
        self.assertFalse(r["ok"])
        self.assertIn("não consegui iniciar", r["erro"])
        self.assertFalse(any(self.arquivo.glob("*/worktree")))


class AgataCodeLacoTests(unittest.TestCase):
    def test_laco_emite_estado_periodico_e_o_evento_do_trabalho(self):
        pedidos = []
        def abrir(pedido):
            pedidos.append(json.loads(json.dumps(pedido)))
            return iter(sse_texto("feito"))
        def lento(args, cancelar=None):
            time.sleep(0.5)
            return {"ok": True, "resposta": "r", "diff_stat": " a | 1 +", "worktree": "/w", "transcricao": "/t", "erro": None, "tempo_s": 0.5}
        evs = list(fs.laco(abrir, iter(sse_chamada("agata_code", '{"tarefa":"x"}')), {"messages": list(MSG)},
                           executor_code=lento, intervalo_pulso=0.1))
        pulsos = [e for e in evs if e["tipo"] == "estado" and e["texto"].startswith("Agata Code trabalhando…")]
        self.assertGreaterEqual(len(pulsos), 3)
        trabalho = [e for e in evs if e["tipo"] == "agata_code"]
        self.assertEqual(len(trabalho), 1)
        self.assertEqual((trabalho[0]["resposta"], trabalho[0]["diff_stat"], trabalho[0]["transcricao"]), ("r", " a | 1 +", "/t"))
        self.assertIn("/w", pedidos[0]["messages"][-1]["content"])
        self.assertEqual(evs[-1], {"tipo": "fim"})

    def test_fechar_o_gerador_cancela_o_agente(self):
        visto = {}
        def preso(args, cancelar=None):
            visto["cancelar"] = cancelar
            cancelar.wait(5)
            return {}
        g = fs.laco(lambda p: iter(sse_texto("x")), iter(sse_chamada("agata_code", '{"tarefa":"x"}')), {"messages": list(MSG)},
                    executor_code=preso, intervalo_pulso=0.05)
        for ev in g:
            if ev["texto"].startswith("Agata Code trabalhando…") and "(" in ev["texto"]:
                break
        g.close()
        self.assertTrue(visto["cancelar"].wait(2))

    def test_argumentos_invalidos_chegam_como_tarefa_recusada(self):
        pedidos = []
        def abrir(pedido):
            pedidos.append(pedido)
            return iter(sse_texto("ok"))
        list(fs.laco(abrir, iter(sse_chamada("agata_code", "{isso não")), {"messages": list(MSG)}))
        self.assertIn("tarefa", pedidos[0]["messages"][-1]["content"])


class AgataCodeTelaTests(unittest.TestCase):
    def test_bloco_trabalho_do_agata_code_fechado_por_padrao_so_textcontent_e_sem_script_inline(self):
        js = (HERE / "prototipo.js").read_text(encoding="utf-8")
        inicio = js.index("function sethBlocoAgataCode")
        corpo = js[inicio:js.index("function sethMostrarAgataCode")]
        self.assertIn("Trabalho do Agata Code", corpo)
        self.assertIn('createElement("details")', corpo)
        self.assertNotIn(".open = true", corpo)
        self.assertNotIn("innerHTML", corpo)
        self.assertIn('evento.tipo === "agata_code"', js)
        self.assertIn(".seth-agata-code", (HERE / "prototipo.css").read_text(encoding="utf-8"))


class GatewayRoteiroHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        pedido = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
        self.server.recebidos.append(pedido)
        corpo = "\n".join(self.server.roteiros.pop(0) if self.server.roteiros else sse_texto("ok")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *a):
        return


class RotaComFerramentasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.antigos = (panel.PORT, panel.ALLOWED_ORIGIN, panel.GATEWAY_CHAT_URL)
        cls.server = panel.ThreadingHTTPServer(("127.0.0.1", 0), panel.Handler)
        cls.server.daemon_threads = True
        panel.PORT = cls.server.server_address[1]
        panel.ALLOWED_ORIGIN = f"http://127.0.0.1:{panel.PORT}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.gw = ThreadingHTTPServer(("127.0.0.1", 0), GatewayRoteiroHandler)
        cls.gw.daemon_threads = True
        cls.gw.recebidos, cls.gw.roteiros = [], []
        threading.Thread(target=cls.gw.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.gw.shutdown(); cls.gw.server_close()
        panel.PORT, panel.ALLOWED_ORIGIN, panel.GATEWAY_CHAT_URL = cls.antigos

    def setUp(self):
        self.gw.recebidos.clear(); self.gw.roteiros.clear()
        panel.GATEWAY_CHAT_URL = f"http://127.0.0.1:{self.gw.server_address[1]}/v1/chat/completions"

    def post(self, modelo):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=10)
        corpo = json.dumps({"mensagens": MSG, "modelo": modelo}).encode("utf-8")
        conn.request("POST", "/api/seth/chat/stream", corpo, {
            "Content-Type": "application/json", "Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin"})
        r = conn.getresponse()
        dados = r.read().decode("utf-8")
        conn.close()
        return [json.loads(b[6:]) for b in dados.split("\n\n") if b.startswith("data: ")]

    def test_seth_public_nao_manda_tools(self):
        with mock.patch.object(fs, "esquemas", return_value=ESQ_FALSOS):
            self.post("seth-public")
        self.assertNotIn("tools", self.gw.recebidos[0])

    def test_seth_livre_manda_so_os_permitidos_e_executa_o_laco_pelo_servidor(self):
        self.gw.roteiros[:] = [sse_chamada("cache_anotar", '{"tipo":"nota","texto":"x"}'), sse_texto("feito")]
        with mock.patch.object(fs, "esquemas", return_value=ESQ_FALSOS), \
                mock.patch.object(fs, "executar", return_value="recibo") as ex:
            evs = self.post("seth-livre")
        self.assertEqual({t["function"]["name"] for t in self.gw.recebidos[0]["tools"]}, set(fs.NOMES_PERMITIDOS))
        ex.assert_called_once()
        self.assertEqual(self.gw.recebidos[1]["messages"][-1], {"role": "tool", "tool_call_id": "c1", "content": "recibo"})
        self.assertEqual([e["tipo"] for e in evs], ["estado", "texto", "fim"])


if __name__ == "__main__":
    unittest.main()
