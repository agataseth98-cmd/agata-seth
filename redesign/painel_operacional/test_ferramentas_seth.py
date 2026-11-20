#!/usr/bin/env python3
"""Ferramentas da Seth no painel (20/11/2026): só seth-livre, lista fixa, laço de até 5 rodadas, cache_anotar.

Nunca chama gateway nem MCP reais: gateway falso em porta livre; o MCP é trocado por função falsa.
"""
import http.client
import importlib.util
import json
import os
import tempfile
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
              for n in fs.NOMES_MCP] + [fs.ESQUEMA_ANOTAR]


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
        self.assertEqual(nomes, list(fs.NOMES_MCP) + ["cache_anotar"])
        with mock.patch.object(fs, "_rpc_mcp") as rpc:
            self.assertIn("não permitida", fs.executar("memoria_acrescentar", '{"texto":"x"}'))
            rpc.assert_not_called()

    def test_mcp_fora_do_ar_oferece_so_cache_anotar(self):
        with mock.patch.object(fs, "_rpc_mcp", side_effect=fs.ErroMCP("x")):
            fs._cache_esquemas.update(quando=0.0, lista=None)
            self.assertEqual([f["function"]["name"] for f in fs.esquemas()], ["cache_anotar"])

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
