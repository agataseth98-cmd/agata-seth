"""Testes do ditado da Seth (seth_ditado.py e a rota POST /api/seth/ditado; spec/spec.md).

O ouvido é um servidor HTTP falso em 127.0.0.1 (nunca o servidor_ouvido real, porta 20137). O áudio é um
conteúdo de teste; a transcrição é a resposta que o falso devolve.
"""
import http.client
import importlib.util
import json
import socket
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import seth_ditado  # noqa: E402

AUDIO = b"\x1aE\xdf\xa3" + b"\x00" * 64  # cabeçalho de webm, só para ter bytes de áudio


def _carrega_servidor():
    spec = importlib.util.spec_from_file_location("painel_ditado_teste", HERE / "server.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


panel = _carrega_servidor()


class _Ouvido(BaseHTTPRequestHandler):
    """Ouvido falso: guarda o que chegou e responde o que o teste configurou (status, corpo em bytes)."""

    def do_POST(self):
        st = self.server.estado
        corpo = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        st["pedidos"].append({"tipo": self.headers.get("Content-Type", ""), "corpo": corpo})
        status, bruto = st["resposta"]
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(bruto)))
        self.end_headers()
        self.wfile.write(bruto)

    def log_message(self, *args):
        pass


def _porta_fechada() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    porta = s.getsockname()[1]
    s.close()
    return porta


class DitadoFalsoTests(unittest.TestCase):
    def setUp(self):
        self.ouvido = ThreadingHTTPServer(("127.0.0.1", 0), _Ouvido)
        self.ouvido.daemon_threads = True
        self.ouvido.estado = {"pedidos": [], "resposta": (200, json.dumps({"text": "olá, Seth"}).encode("utf-8"))}
        threading.Thread(target=self.ouvido.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.ouvido.server_address[1]}"
        self.salvo = seth_ditado.OUVIDO
        seth_ditado.OUVIDO = self.url

    def tearDown(self):
        seth_ditado.OUVIDO = self.salvo
        self.ouvido.shutdown()
        self.ouvido.server_close()

    def responde(self, status, corpo):
        self.ouvido.estado["resposta"] = (status, corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode("utf-8"))

    def pedidos(self):
        return self.ouvido.estado["pedidos"]


class TranscreverTests(DitadoFalsoTests):
    def test_manda_o_audio_como_multipart_e_devolve_o_texto(self):
        r = seth_ditado.transcrever(AUDIO, "audio/webm;codecs=opus")
        self.assertEqual(r, {"schema_version": 1, "texto": "olá, Seth"})
        pedido = self.pedidos()[0]
        self.assertTrue(pedido["tipo"].startswith("multipart/form-data; boundary="))
        self.assertIn(b'name="file"; filename="fala.webm"', pedido["corpo"])
        self.assertIn(b"Content-Type: audio/webm\r\n", pedido["corpo"])  # tipo base, sem o codecs
        self.assertIn(b'name="language"\r\n\r\npt', pedido["corpo"])
        self.assertIn(AUDIO, pedido["corpo"])

    def test_extensao_segue_o_tipo_do_navegador(self):
        seth_ditado.transcrever(AUDIO, "audio/ogg;codecs=opus")
        self.assertIn(b'filename="fala.ogg"', self.pedidos()[0]["corpo"])

    def test_texto_vem_limpo_e_cortado_no_teto_do_campo(self):
        self.responde(200, {"text": "  " + "a" * 5000 + "  "})
        r = seth_ditado.transcrever(AUDIO, "audio/webm")
        self.assertEqual(len(r["texto"]), seth_ditado.TEXTO_MAX)

    def test_limites_do_servidor_e_do_cliente_batem(self):
        self.assertEqual(seth_ditado.LIMITE_AUDIO_BYTES, 2 * 1024 * 1024)
        self.assertEqual(seth_ditado.DURACAO_MAX_S, 60)

    def test_audio_grande_e_recusado_antes_de_chegar_ao_ouvido(self):
        with self.assertRaises(seth_ditado.ErroDitado) as c:
            seth_ditado.transcrever(b"x" * (seth_ditado.LIMITE_AUDIO_BYTES + 1), "audio/webm")
        self.assertEqual(c.exception.status, 413)
        self.assertIn("2 MB", c.exception.motivo)
        self.assertEqual(self.pedidos(), [])

    def test_audio_vazio_e_formato_que_nao_e_audio_sao_recusados(self):
        with self.assertRaises(seth_ditado.ErroDitado) as c:
            seth_ditado.transcrever(b"", "audio/webm")
        self.assertEqual(c.exception.status, 400)
        with self.assertRaises(seth_ditado.ErroDitado) as c:
            seth_ditado.transcrever(AUDIO, "text/plain")
        self.assertEqual(c.exception.status, 415)
        self.assertEqual(self.pedidos(), [])

    def test_ouvido_fora_do_ar_diz_que_nada_foi_transcrito(self):
        with self.assertRaises(seth_ditado.ErroDitado) as c:
            seth_ditado.transcrever(AUDIO, "audio/webm", url=f"http://127.0.0.1:{_porta_fechada()}")
        self.assertEqual(c.exception.status, 503)
        self.assertIn("nada foi transcrito", c.exception.motivo)
        self.assertIn("Ligue o servidor do ouvido", c.exception.motivo)

    def test_ouvido_sem_motor_no_ar_responde_503_com_razao_clara(self):
        self.responde(503, {"error": "nenhum motor transcreveu"})
        with self.assertRaises(seth_ditado.ErroDitado) as c:
            seth_ditado.transcrever(AUDIO, "audio/webm")
        self.assertEqual(c.exception.status, 503)
        self.assertIn("não tem motor no ar", c.exception.motivo)

    def test_ouvido_que_nao_processa_o_audio_vira_422(self):
        self.responde(422, {"error": "áudio não processado"})
        with self.assertRaises(seth_ditado.ErroDitado) as c:
            seth_ditado.transcrever(AUDIO, "audio/webm")
        self.assertEqual(c.exception.status, 422)
        self.assertIn("gravar de novo", c.exception.motivo)

    def test_gravacao_sem_fala_diz_para_tentar_de_novo(self):
        self.responde(200, {"text": "   "})
        with self.assertRaises(seth_ditado.ErroDitado) as c:
            seth_ditado.transcrever(AUDIO, "audio/webm")
        self.assertEqual(c.exception.status, 422)
        self.assertIn("não ouvi fala", c.exception.motivo)

    def test_resposta_fora_do_formato_vira_502(self):
        self.responde(200, b"oi, nao sou json")
        with self.assertRaises(seth_ditado.ErroDitado) as c:
            seth_ditado.transcrever(AUDIO, "audio/webm")
        self.assertEqual(c.exception.status, 502)
        self.responde(200, {"outro": 1})
        with self.assertRaises(seth_ditado.ErroDitado) as c:
            seth_ditado.transcrever(AUDIO, "audio/webm")
        self.assertEqual(c.exception.status, 502)

    def test_uma_transcricao_por_vez(self):
        self.assertTrue(seth_ditado._TRANSCRICAO.acquire(blocking=False))
        try:
            with self.assertRaises(seth_ditado.ErroDitado) as c:
                seth_ditado.transcrever(AUDIO, "audio/webm")
            self.assertEqual(c.exception.status, 429)
        finally:
            seth_ditado._TRANSCRICAO.release()
        self.assertEqual(self.pedidos(), [])


class RotaDitadoTests(DitadoFalsoTests):
    """POST /api/seth/ditado no painel: origem, tamanho e o texto que volta para o campo."""

    @classmethod
    def setUpClass(cls):
        cls.porta_antiga = panel.PORT
        cls.servidor = panel.ThreadingHTTPServer(("127.0.0.1", 0), panel.Handler)
        cls.servidor.daemon_threads = True
        panel.PORT = cls.servidor.server_address[1]
        cls.thread = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.thread.join(timeout=3)
        panel.PORT = cls.porta_antiga

    def pede(self, corpo, cabecalhos):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=30)
        try:
            conn.request("POST", "/api/seth/ditado", body=corpo, headers=cabecalhos)
            resposta = conn.getresponse()
            return resposta.status, json.loads(resposta.read() or b"{}")
        finally:
            conn.close()

    def test_rota_devolve_o_texto_para_o_campo(self):
        status, dados = self.pede(AUDIO, {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "audio/webm"})
        self.assertEqual(status, 200)
        self.assertEqual(dados, {"schema_version": 1, "texto": "olá, Seth"})
        self.assertEqual(len(self.pedidos()), 1)

    def test_rota_recusa_origem_cruzada_sem_chamar_o_ouvido(self):
        status, _ = self.pede(AUDIO, {"Origin": "http://evil.example", "Sec-Fetch-Site": "cross-site", "Content-Type": "audio/webm"})
        self.assertEqual(status, 403)
        self.assertEqual(self.pedidos(), [])

    def test_rota_recusa_audio_maior_que_o_limite_pelo_tamanho_declarado(self):
        # A decisão é pelo Content-Length declarado: o servidor responde 413 sem ler o corpo. O cliente manda um corpo
        # pequeno, para o teste não depender de o envio de 2 MB sobreviver ao fechamento da conexão (o navegador
        # nunca manda isso: checa o tamanho antes).
        cab = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin", "Content-Type": "audio/webm",
               "Content-Length": str(seth_ditado.LIMITE_AUDIO_BYTES + 1)}
        status, dados = self.pede(b"x" * 10, cab)
        self.assertEqual(status, 413)
        self.assertIn("erro", dados)
        self.assertEqual(self.pedidos(), [])


if __name__ == "__main__":
    unittest.main()
