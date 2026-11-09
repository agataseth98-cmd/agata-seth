#!/usr/bin/env python3
"""Rota POST /api/seth/chat/stream, redirecionamentos de entrada e origem, com gateway falso.

Nunca chama o gateway real: o gateway é um servidor HTTP local em porta livre (127.0.0.1, porta 0).
"""
import http.client
import importlib.util
import json
import socket
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from chat_stream import codificar_sse

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("painel_rota_teste", HERE / "server.py")
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)


_ORIGEM_VALIDA = object()  # sentinela: usa a origem do próprio servidor de teste


def _chunk(texto):
    return "data: " + json.dumps({"choices": [{"delta": {"content": texto}}]}, ensure_ascii=False) + "\n\n"


class GatewayFalsoHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length", "0"))
        self.server.recebidos.append(json.loads(self.rfile.read(tamanho).decode("utf-8")))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        self.wfile.write(self.server.roteiro.encode("utf-8"))

    def log_message(self, _format, *args):
        return


def _porta_fechada():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    porta = sock.getsockname()[1]
    sock.close()
    return porta


def _eventos(corpo: bytes):
    return [json.loads(bloco[len("data: "):])
            for bloco in corpo.decode("utf-8").split("\n\n") if bloco.startswith("data: ")]


class RotaChatStreamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.antigos = (panel.PORT, panel.ALLOWED_ORIGIN, panel.GATEWAY_CHAT_URL)
        cls.server = panel.ThreadingHTTPServer(("127.0.0.1", 0), panel.Handler)
        cls.server.daemon_threads = True
        panel.PORT = cls.server.server_address[1]
        panel.ALLOWED_ORIGIN = f"http://127.0.0.1:{panel.PORT}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

        cls.gateway = ThreadingHTTPServer(("127.0.0.1", 0), GatewayFalsoHandler)
        cls.gateway.daemon_threads = True
        cls.gateway.roteiro = ""
        cls.gateway.recebidos = []
        cls.gateway_thread = threading.Thread(target=cls.gateway.serve_forever, daemon=True)
        cls.gateway_thread.start()
        cls.gateway_url = f"http://127.0.0.1:{cls.gateway.server_address[1]}/v1/chat/completions"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.gateway.shutdown()
        cls.gateway.server_close()
        cls.gateway_thread.join(timeout=3)
        panel.PORT, panel.ALLOWED_ORIGIN, panel.GATEWAY_CHAT_URL = cls.antigos

    def setUp(self):
        self.gateway.recebidos.clear()
        self.gateway.roteiro = ""
        panel.GATEWAY_CHAT_URL = self.gateway_url

    def tearDown(self):
        panel.GATEWAY_CHAT_URL = self.antigos[2]

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=5)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            cabecalhos = {k.lower(): v for k, v in response.getheaders()}
            return response.status, response.read(), cabecalhos
        finally:
            conn.close()

    def post_stream(self, corpo, origem=_ORIGEM_VALIDA, extra=None, content_type="application/json"):
        cabecalhos = {"Content-Type": content_type}
        if origem is _ORIGEM_VALIDA:
            origem = f"http://127.0.0.1:{panel.PORT}"
        if origem is not None:  # None = sem cabeçalho Origin
            cabecalhos["Origin"] = origem
        cabecalhos.update(extra or {})
        dados = corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode("utf-8")
        return self.request("POST", "/api/seth/chat/stream", body=dados, headers=cabecalhos)

    MENSAGENS = {"mensagens": [{"role": "user", "content": "oi"}]}

    # Redirecionamento de entrada (P9-A)

    def test_raiz_redireciona_para_prototipo(self):
        status, _, cabecalhos = self.request("GET", "/")
        self.assertEqual(status, 302)
        self.assertEqual(cabecalhos["location"], "/prototipo#panorama")

    def test_conselho_rede_redireciona_para_o_conselho_no_prototipo(self):
        status, _, cabecalhos = self.request("GET", "/conselho-rede")
        self.assertEqual(status, 302)
        self.assertEqual(cabecalhos["location"], "/prototipo#conselho")

    def test_rotas_existentes_seguem_respondendo(self):
        self.assertEqual(self.request("GET", "/prototipo")[0], 200)
        status, _, cabecalhos = self.request("GET", "/index.html")
        self.assertEqual(status, 302)
        self.assertEqual(cabecalhos["location"], "/prototipo#panorama")

    # Stream

    def test_stream_repassa_deltas_e_fim_como_sse(self):
        self.gateway.roteiro = _chunk("Olá") + "\n" + _chunk(", mundo") + "\n" + "data: [DONE]\n\n"
        status, corpo, cabecalhos = self.post_stream(self.MENSAGENS)
        self.assertEqual(status, 200)
        self.assertTrue(cabecalhos["content-type"].startswith("text/event-stream"))
        self.assertEqual(cabecalhos["cache-control"], "no-store")
        self.assertEqual(_eventos(corpo), [
            {"tipo": "texto", "delta": "Olá"},
            {"tipo": "texto", "delta": ", mundo"},
            {"tipo": "fim"},
        ])
        self.assertEqual(corpo, codificar_sse({"tipo": "texto", "delta": "Olá"})
                         + codificar_sse({"tipo": "texto", "delta": ", mundo"}) + codificar_sse({"tipo": "fim"}))
        self.assertEqual(self.gateway.recebidos, [
            {"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}], "stream": True},
        ])

    def test_stream_sem_done_termina_em_erro_sse(self):
        self.gateway.roteiro = _chunk("parcial") + "\n"
        status, corpo, _ = self.post_stream(self.MENSAGENS)
        self.assertEqual(status, 200)
        self.assertEqual(_eventos(corpo), [
            {"tipo": "texto", "delta": "parcial"},
            {"tipo": "erro", "motivo": "stream interrompido"},
        ])

    def test_gateway_fora_gera_erro_sse_e_servidor_segue_vivo(self):
        panel.GATEWAY_CHAT_URL = f"http://127.0.0.1:{_porta_fechada()}/v1/chat/completions"
        status, corpo, cabecalhos = self.post_stream(self.MENSAGENS)
        self.assertEqual(status, 200)
        self.assertTrue(cabecalhos["content-type"].startswith("text/event-stream"))
        self.assertEqual(_eventos(corpo), [{"tipo": "erro", "motivo": "gateway indisponível"}])
        self.assertEqual(self.request("GET", "/prototipo")[0], 200)

    # Controle de origem e validação

    def test_origem_cruzada_e_recusada_sem_chegar_ao_gateway(self):
        for origem in ("http://evil.example", None, ""):
            with self.subTest(origem=origem):
                status, _, _ = self.post_stream(self.MENSAGENS, origem=origem)
                self.assertEqual(status, 403)
        status, _, _ = self.post_stream(self.MENSAGENS, extra={"Sec-Fetch-Site": "cross-site"})
        self.assertEqual(status, 403)
        self.assertEqual(self.gateway.recebidos, [])

    def test_entrada_invalida_e_recusada_sem_chegar_ao_gateway(self):
        status, _, _ = self.post_stream({"mensagens": [{"role": "tool", "content": "x"}]})
        self.assertEqual(status, 400)
        status, _, _ = self.post_stream({"mensagens": []})
        self.assertEqual(status, 400)
        status, _, _ = self.post_stream({"outra": 1})
        self.assertEqual(status, 400)
        status, _, _ = self.post_stream(b"{nao-json")
        self.assertEqual(status, 400)
        status, _, _ = self.post_stream(self.MENSAGENS, content_type="text/plain")
        self.assertEqual(status, 415)
        self.assertEqual(self.gateway.recebidos, [])


if __name__ == "__main__":
    unittest.main()
