#!/usr/bin/env python3
"""Rota POST /api/seth/chat/stream, redirecionamentos de entrada e origem, com gateway falso.

Nunca chama o gateway real: o gateway é um servidor HTTP local em porta livre (127.0.0.1, porta 0).
"""
import http.client
import importlib.util
import json
import socket
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

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
        pedido = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        self.server.recebidos.append(pedido)
        # X-Modelo-Real do gateway de verdade (seth_gateway.py): só vai no cabeçalho quando o teste pede.
        cabecalhos = [("X-Modelo-Real", self.server.modelo_real)] if self.server.modelo_real else []
        if pedido.get("stream") is False:  # fallback /api/seth/chat: resposta inteira em JSON (roteiro, se o teste der um)
            corpo = (self.server.roteiro or json.dumps(
                {"model": "seth-livre", "choices": [{"message": {"content": self.server.resposta_json}}]},
                ensure_ascii=False)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo)))
            for nome, valor in cabecalhos:
                self.send_header(nome, valor)
            self.end_headers()
            self.wfile.write(corpo)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        for nome, valor in cabecalhos:
            self.send_header(nome, valor)
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
        cls.gateway.resposta_json = "resposta do gateway falso"
        cls.gateway.modelo_real = ""
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
        self.gateway.modelo_real = ""
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

    # Motivo do 400/413 (a UI mostra o corpo da resposta) e teto do fallback

    def post_chat(self, corpo):
        dados = json.dumps(corpo).encode("utf-8")
        return self.request("POST", "/api/seth/chat", body=dados,
                            headers={"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{panel.PORT}"})

    def post_conversa(self, corpo_bytes, extra=None):
        cabecalhos = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{panel.PORT}",
                      "Sec-Fetch-Site": "same-origin"}
        cabecalhos.update(extra or {})
        return self.request("POST", "/api/seth/conversa", body=corpo_bytes, headers=cabecalhos)

    def test_mensagem_longa_no_stream_recusada_com_motivo_sem_ecoar_o_texto(self):
        status, corpo, _ = self.post_stream({"mensagens": [{"role": "user", "content": "SEGREDO" + "x" * 4000}]})
        self.assertEqual(status, 400)
        self.assertIn("4000 caracteres", corpo.decode("utf-8"))
        self.assertNotIn(b"SEGREDO", corpo)
        self.assertEqual(self.gateway.recebidos, [])

    def test_pedido_acima_do_limite_do_stream_tem_motivo_em_portugues(self):
        status, corpo, _ = self.post_stream(b"{}", extra={"Content-Length": str(panel.CHAT_STREAM_LIMITE_BYTES + 1)})
        self.assertEqual(status, 413)
        self.assertEqual(corpo.decode("utf-8"), f"pedido acima de {panel.CHAT_STREAM_LIMITE_BYTES} bytes")

    def test_fallback_aceita_janela_maior_que_16384_bytes(self):
        # 20 mensagens de 4000 caracteres ~ 80 KB em JSON: antes o fallback recusava acima de 16384 bytes
        mensagens = [{"role": "user" if i % 2 == 0 else "assistant", "content": "a" * 4000} for i in range(20)]
        status, corpo, _ = self.post_chat({"messages": mensagens})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(corpo)["content"], "resposta do gateway falso")
        self.assertEqual(len(self.gateway.recebidos[-1]["messages"]), 20)

    def test_fallback_recusa_acima_do_limite_do_stream_com_motivo(self):
        # Cada quebra de linha vira \\n no JSON (2 bytes): 20 x 4000 quebras passam de 131072 bytes
        mensagens = [{"role": "user", "content": "\n" * 4000} for _ in range(20)]
        status, corpo, _ = self.post_chat({"messages": mensagens})
        self.assertEqual(status, 413)
        self.assertEqual(corpo.decode("utf-8"), f"pedido acima de {panel.CHAT_STREAM_LIMITE_BYTES} bytes")
        self.assertEqual(self.gateway.recebidos, [])

    def test_fallback_recusa_mensagem_longa_com_motivo_em_portugues(self):
        status, corpo, _ = self.post_chat({"messages": [{"role": "user", "content": "x" * 4001}]})
        self.assertEqual(status, 400)
        self.assertEqual(corpo.decode("utf-8"), "mensagem vazia ou acima de 4000 caracteres")
        self.assertEqual(self.gateway.recebidos, [])

    def test_conversa_acima_do_limite_recusada_com_motivo(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel.armazem, "CONVERSAS_DIR", Path(tmp)):
            status, corpo, _ = self.post_conversa(b"{}", extra={"Content-Length": str(panel.CONVERSA_LIMITE_BYTES + 1)})
            self.assertEqual(status, 413)
            self.assertEqual(corpo.decode("utf-8"), f"conversa acima de {panel.CONVERSA_LIMITE_BYTES} bytes")
            self.assertEqual(list(Path(tmp).glob("*.json")), [])

    def test_conversa_recusada_diz_a_regra_que_falhou(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel.armazem, "CONVERSAS_DIR", Path(tmp)):
            muitas = json.dumps({"titulo": "Longa", "mensagens": [{"role": "user", "content": "oi"}] * 201}).encode("utf-8")
            status, corpo, _ = self.post_conversa(muitas)
            self.assertEqual((status, corpo.decode("utf-8")), (400, "mais de 200 mensagens"))
            grande = json.dumps({"titulo": "X", "mensagens": [{"role": "user", "content": "x" * 65537}]}).encode("utf-8")
            status, corpo, _ = self.post_conversa(grande)
            self.assertEqual((status, corpo.decode("utf-8")), (400, "uma mensagem passa de 65536 caracteres"))
            self.assertEqual(list(Path(tmp).glob("*.json")), [])
    # Modelo do chat: lista fixa. O servidor recusa o que está fora dela antes de chamar o gateway.

    def test_stream_manda_ao_gateway_o_modelo_escolhido(self):
        self.gateway.roteiro = _chunk("ok") + "\n" + "data: [DONE]\n\n"
        status, _, _ = self.post_stream({**self.MENSAGENS, "modelo": "seth-public"})
        self.assertEqual(status, 200)
        self.assertEqual(self.gateway.recebidos[0]["model"], "seth-public")

    def test_stream_sem_modelo_manda_seth_livre(self):
        self.gateway.roteiro = _chunk("ok") + "\n" + "data: [DONE]\n\n"
        status, _, _ = self.post_stream(self.MENSAGENS)
        self.assertEqual(status, 200)
        self.assertEqual(self.gateway.recebidos[0]["model"], "seth-livre")

    def test_stream_recusa_modelo_fora_da_lista_com_400_sem_chegar_ao_gateway(self):
        for ruim in ("seth-zai", "seth-gemini", "seth-hf", "seth-mistral", "seth-auto",
                     "seth-rapido", "seth-pesado", "seth-codigo", "", 3, ["seth-livre"]):
            with self.subTest(modelo=ruim):
                status, _, _ = self.post_stream({**self.MENSAGENS, "modelo": ruim})
                self.assertEqual(status, 400)
        self.assertEqual(self.gateway.recebidos, [])

    def test_get_modelos_devolve_padrao_e_lista_fixa(self):
        status, corpo, cabecalhos = self.request("GET", "/api/seth/modelos")
        self.assertEqual(status, 200)
        self.assertTrue(cabecalhos["content-type"].startswith("application/json"))
        dados = json.loads(corpo)
        self.assertEqual(dados["padrao"], "seth-livre")
        self.assertEqual([m["id"] for m in dados["modelos"]], ["seth-livre", "seth-public"])

    def test_get_modelos_recusa_origem_cruzada(self):
        status, _, _ = self.request("GET", "/api/seth/modelos", headers={"Origin": "http://evil.example"})
        self.assertEqual(status, 403)

    def test_chat_inteiro_valida_o_modelo_e_repassa_o_escolhido(self):
        self.gateway.roteiro = json.dumps({"model": "m", "choices": [{"message": {"content": "ok"}}]})
        origem = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{panel.PORT}"}
        mensagens = [{"role": "user", "content": "oi"}]
        bom = json.dumps({"messages": mensagens, "modelo": "seth-public"}).encode("utf-8")
        status, corpo, _ = self.request("POST", "/api/seth/chat", body=bom, headers=origem)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(corpo)["content"], "ok")
        self.assertEqual(self.gateway.recebidos[0]["model"], "seth-public")
        self.gateway.recebidos.clear()
        for ruim in ("seth-zai", ""):
            with self.subTest(modelo=ruim):
                corpo_ruim = json.dumps({"messages": mensagens, "modelo": ruim}).encode("utf-8")
                status, _, _ = self.request("POST", "/api/seth/chat", body=corpo_ruim, headers=origem)
                self.assertEqual(status, 400)
        self.assertEqual(self.gateway.recebidos, [])
        sem_modelo = json.dumps({"messages": mensagens}).encode("utf-8")
        status, _, _ = self.request("POST", "/api/seth/chat", body=sem_modelo, headers=origem)
        self.assertEqual(status, 200)
        self.assertEqual(self.gateway.recebidos[0]["model"], "seth-livre")

    # Modelo real: o cabeçalho X-Modelo-Real do gateway segue até o navegador, no stream e no fallback.

    def test_stream_repassa_o_modelo_real_no_cabecalho(self):
        self.gateway.modelo_real = "openai/gpt-oss-120b"
        self.gateway.roteiro = _chunk("ok") + "\n" + "data: [DONE]\n\n"
        status, corpo, cabecalhos = self.post_stream(self.MENSAGENS)
        self.assertEqual(status, 200)
        self.assertEqual(cabecalhos["x-modelo-real"], "openai/gpt-oss-120b")
        self.assertEqual(_eventos(corpo)[-1], {"tipo": "fim"})

    def test_stream_sem_cabecalho_do_gateway_nao_manda_modelo_real(self):
        self.gateway.roteiro = _chunk("ok") + "\n" + "data: [DONE]\n\n"
        status, _, cabecalhos = self.post_stream(self.MENSAGENS)
        self.assertEqual(status, 200)
        self.assertNotIn("x-modelo-real", cabecalhos)

    def test_stream_nao_repassa_cabecalho_do_gateway_fora_do_formato(self):
        self.gateway.modelo_real = "lixo com espaço"
        self.gateway.roteiro = _chunk("ok") + "\n" + "data: [DONE]\n\n"
        status, _, cabecalhos = self.post_stream(self.MENSAGENS)
        self.assertEqual(status, 200)
        self.assertNotIn("x-modelo-real", cabecalhos)

    def test_fallback_repassa_o_modelo_real_no_cabecalho(self):
        self.gateway.modelo_real = "openai/gpt-oss-120b"
        status, corpo, cabecalhos = self.post_chat({"messages": [{"role": "user", "content": "oi"}]})
        self.assertEqual(status, 200)
        self.assertEqual(cabecalhos["x-modelo-real"], "openai/gpt-oss-120b")
        self.assertEqual(json.loads(corpo)["content"], "resposta do gateway falso")

    def test_fallback_sem_cabecalho_do_gateway_nao_manda_modelo_real(self):
        status, _, cabecalhos = self.post_chat({"messages": [{"role": "user", "content": "oi"}]})
        self.assertEqual(status, 200)
        self.assertNotIn("x-modelo-real", cabecalhos)

    def test_conversa_com_modelo_fora_da_lista_recusada_com_motivo(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(panel.armazem, "CONVERSAS_DIR", Path(tmp)):
            ruim = json.dumps({"titulo": "X", "modelo": "seth-zai", "mensagens": [{"role": "user", "content": "oi"}]}).encode("utf-8")
            status, corpo, _ = self.post_conversa(ruim)
            self.assertEqual((status, corpo.decode("utf-8")), (400, "modelo fora da lista"))
            ruim_na_resposta = json.dumps({"titulo": "X", "mensagens": [{"role": "assistant", "content": "oi", "modelo": "seth-auto"}]})
            status, corpo, _ = self.post_conversa(ruim_na_resposta.encode("utf-8"))
            self.assertEqual((status, corpo.decode("utf-8")), (400, "modelo fora da lista"))
            self.assertEqual(list(Path(tmp).glob("*.json")), [])


if __name__ == "__main__":
    unittest.main()
