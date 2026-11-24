"""Testes de ler em voz alta da Seth (seth_voz.py e as rotas /api/seth/ouvir, /api/seth/ouvir/parar; spec/spec.md).

Nenhum teste aciona o piper real nem o player de verdade: o piper é um servidor HTTP falso nesta máquina, o
player é um script de shell que grava o que recebeu e espera um pouco, e o systemctl é outro script que só
cria ou apaga um arquivo que diz se o serviço está "no ar". O scripts/agata_falar.py é o de verdade, com o
endereço e os players trocados em tempo de teste.
"""
import http.client
import importlib.util
import json
import os
import stat
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT_REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import seth_voz  # noqa: E402

MODELO_CERTO = "pt_BR-agata-last.onnx"
MODELO_ERRADO = "pt_BR-faber-medium.onnx"
PARAGRAFOS = "Primeiro parágrafo da resposta.\n\nSegundo parágrafo, com mais uma frase.\n\nTerceiro e último."


def _carrega_servidor():
    spec = importlib.util.spec_from_file_location("painel_voz_teste", HERE / "server.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


panel = _carrega_servidor()


class _Piper(BaseHTTPRequestHandler):
    """Piper falso: /health diz o modelo (ou 503 se o arquivo 'no ar' não existe) e /v1/audio/speech devolve um WAV falso."""

    def do_GET(self):
        st = self.server.estado
        if self.path != "/health" or not os.path.exists(st["no_ar"]):
            return self._responde(503, b'{"status":"fora"}')
        return self._responde(200, json.dumps({"status": "ok", "model": st["modelo"]}).encode("utf-8"))

    def do_POST(self):
        st = self.server.estado
        pedido = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
        st["pedidos"].append(pedido)
        if st.get("falha_no_pedido") == len(st["pedidos"]):
            return self._responde(500, b"falha de teste")
        if st.get("nao_wav"):
            return self._responde(200, b"isto nao e um wav", "audio/wav")
        return self._responde(200, b"RIFF" + b"\0" * 40, "audio/wav")

    def _responde(self, status, corpo, tipo="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


class FalaFalsaTests(unittest.TestCase):
    """Base: piper falso, player falso, systemctl falso, e a trava da leitura livre antes de cada teste."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        pasta = Path(self.tmp.name)
        self.no_ar = pasta / "no_ar"
        self.no_ar.write_text("sim", encoding="utf-8")
        self.log_player = pasta / "tocou.txt"
        self.log_systemctl = pasta / "systemctl.txt"
        self.player = pasta / "player_falso.sh"
        self.player.write_text(
            "#!/bin/sh\necho \"$1\" >> \"$FALSO_LOG_PLAYER\"\nsleep \"${FALSO_ESPERA:-0}\"\nexit \"${FALSO_CODIGO_PLAYER:-0}\"\n",
            encoding="utf-8")
        self.player.chmod(self.player.stat().st_mode | stat.S_IEXEC)
        self.systemctl = pasta / "systemctl_falso.sh"
        self.systemctl.write_text(
            "#!/bin/sh\necho \"$@\" >> \"" + str(self.log_systemctl) + "\"\n"
            "case \"$*\" in\n  *start*) touch \"" + str(self.no_ar) + "\" ;;\n  *stop*) rm -f \"" + str(self.no_ar) + "\" ;;\nesac\nexit 0\n",
            encoding="utf-8")
        self.systemctl.chmod(self.systemctl.stat().st_mode | stat.S_IEXEC)
        self.piper = ThreadingHTTPServer(("127.0.0.1", 0), _Piper)
        self.piper.daemon_threads = True
        self.piper.estado = {"no_ar": str(self.no_ar), "modelo": MODELO_CERTO, "pedidos": [], "falha_no_pedido": None}
        threading.Thread(target=self.piper.serve_forever, daemon=True).start()
        self.falar = seth_voz._falar()
        self.salvo = (self.falar.BASE, self.falar.PLAYERS)
        self.falar.BASE = f"http://127.0.0.1:{self.piper.server_address[1]}"
        self.falar.PLAYERS = ((str(self.player), []),)
        self.ambiente = {k: os.environ.get(k) for k in ("AGATA_FALAR_SYSTEMCTL", "FALSO_LOG_PLAYER", "FALSO_ESPERA", "FALSO_CODIGO_PLAYER")}
        os.environ["AGATA_FALAR_SYSTEMCTL"] = str(self.systemctl)
        os.environ["FALSO_LOG_PLAYER"] = str(self.log_player)
        os.environ["FALSO_ESPERA"] = "0"
        os.environ["FALSO_CODIGO_PLAYER"] = "0"
        seth_voz._ESTADO.update(falando=False, trecho=0, trechos=0, ultimo_uso=None, ultimo_motivo=None)
        seth_voz._PARAR.clear()

    def tearDown(self):
        self.piper.shutdown()
        self.piper.server_close()
        self.falar.BASE, self.falar.PLAYERS = self.salvo
        for chave, valor in self.ambiente.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor
        self.tmp.cleanup()

    def pedidos(self):
        return self.piper.estado["pedidos"]

    def tocados(self):
        return self.log_player.read_text(encoding="utf-8").splitlines() if self.log_player.exists() else []

    def systemctl_log(self):
        return self.log_systemctl.read_text(encoding="utf-8") if self.log_systemctl.exists() else ""


class FalaTests(FalaFalsaTests):
    def test_fala_em_partes_com_a_voz_do_sistema(self):
        r = seth_voz.iniciar(PARAGRAFOS)
        self.assertTrue(r["falou"])
        self.assertTrue(r["completo"])
        self.assertEqual(r["codigo"], "completo")
        self.assertEqual((r["trechos_falados"], r["trechos"]), (3, 3))
        self.assertEqual(r["motivo"], "falei a resposta inteira em 3 trechos")
        self.assertEqual(len(self.pedidos()), 3)
        self.assertTrue(all(p["voice"] == "agata" and p["model"] == "tts-1" for p in self.pedidos()))
        self.assertEqual(len(self.tocados()), 3)

    def test_preparo_do_script_tira_codigo_tabela_e_marcacao(self):
        seth_voz.iniciar("# Título\n\nVeja `scripts/x.py` e **negrito** e o SDD.\n\n```\ncodigo()\n```\n\n| a | b |\n|---|---|\n")
        falado = " ".join(p["input"] for p in self.pedidos())
        self.assertNotIn("```", falado)
        self.assertNotIn("**", falado)
        self.assertNotIn("|", falado)
        self.assertNotIn("scripts/x.py", falado)
        self.assertIn("S-D-D", falado)

    def test_outro_modelo_no_piper_nao_fala(self):
        self.piper.estado["modelo"] = MODELO_ERRADO
        r = seth_voz.iniciar("Uma resposta qualquer.")
        self.assertFalse(r["falou"])
        self.assertEqual(r["codigo"], "voz")
        self.assertTrue(r["motivo"].startswith("NÃO falei"))
        self.assertEqual(self.pedidos(), [])
        self.assertEqual(self.tocados(), [])

    def test_servico_parado_e_ligado_por_quem_fala_e_desligado_depois(self):
        self.no_ar.unlink()
        r = seth_voz.iniciar("Uma frase.")
        self.assertTrue(r["falou"])
        log = self.systemctl_log()
        self.assertIn("start", log)
        self.assertIn("stop", log)

    def test_servico_que_ja_estava_no_ar_nao_e_desligado(self):
        r = seth_voz.iniciar("Uma frase.")
        self.assertTrue(r["falou"])
        self.assertEqual(self.systemctl_log(), "")

    def test_servico_que_nao_sobe_diz_que_nao_falou(self):
        self.no_ar.unlink()
        with mock.patch.object(self.falar, "garantir_servico", return_value=(None, True)):
            r = seth_voz.iniciar("Uma frase.")
        self.assertFalse(r["falou"])
        self.assertEqual(r["codigo"], "voz")
        self.assertEqual(self.pedidos(), [])

    def test_sem_player_nao_fala_e_nao_liga_o_servico(self):
        self.no_ar.unlink()
        self.falar.PLAYERS = (("comando-que-nao-existe-xyz", []),)
        r = seth_voz.iniciar("Uma frase.")
        self.assertFalse(r["falou"])
        self.assertEqual(r["codigo"], "player")
        self.assertIn("NÃO falei", r["motivo"])
        self.assertEqual(self.systemctl_log(), "")

    def test_parar_entre_trechos_nao_fala_o_resto(self):
        os.environ["FALSO_ESPERA"] = "0.6"
        resultado = {}
        t = threading.Thread(target=lambda: resultado.update(r=seth_voz.iniciar(PARAGRAFOS)))
        t.start()
        prazo = time.monotonic() + 15
        while not self.tocados() and time.monotonic() < prazo:
            time.sleep(0.02)
        self.assertTrue(self.tocados(), "o primeiro trecho não começou a tocar")
        pedido = seth_voz.parar()
        self.assertTrue(pedido["falando"])
        t.join(timeout=30)
        self.assertFalse(t.is_alive())
        r = resultado["r"]
        self.assertEqual(r["codigo"], "parado")
        self.assertEqual((r["trechos_falados"], r["trechos"]), (1, 3))
        self.assertTrue(r["falou"])
        self.assertEqual(len(self.pedidos()), 1, "o segundo trecho não devia ser pedido depois do Parar")
        self.assertFalse(seth_voz.estado()["falando"])

    def test_parar_sem_leitura_diz_que_nao_estava_lendo(self):
        r = seth_voz.parar()
        self.assertFalse(r["falando"])
        self.assertIn("nada para parar", r["motivo"])

    def test_leitura_ocupada_responde_429(self):
        self.assertTrue(seth_voz._TRAVA.acquire(blocking=False))
        try:
            with self.assertRaises(seth_voz.ErroVoz) as contexto:
                seth_voz.iniciar("Outra frase.")
            self.assertEqual(contexto.exception.status, 429)
        finally:
            seth_voz._TRAVA.release()
        self.assertEqual(self.pedidos(), [])

    def test_texto_vazio_e_texto_acima_do_limite_nao_falam(self):
        with self.assertRaises(seth_voz.ErroVoz) as contexto:
            seth_voz.iniciar("   ")
        self.assertEqual(contexto.exception.status, 400)
        r = seth_voz.iniciar("Frase longa. " * 1200)
        self.assertFalse(r["falou"])
        self.assertEqual(r["codigo"], "texto")
        self.assertIn("resumo", r["motivo"])
        self.assertEqual(self.pedidos(), [])

    def test_falha_no_meio_diz_quantos_trechos_falou(self):
        self.piper.estado["falha_no_pedido"] = 2
        r = seth_voz.iniciar(PARAGRAFOS)
        self.assertTrue(r["falou"])
        self.assertFalse(r["completo"])
        self.assertEqual(r["codigo"], "falha")
        self.assertEqual(r["trechos_falados"], 1)
        self.assertIn("falei 1 de 3", r["motivo"])
        self.assertIn("NÃO falei o resto", r["motivo"])

    def test_ultimo_uso_e_resumo_da_voz_na_pagina_sentidos(self):
        self.assertIn("nenhum desde que o painel abriu", seth_voz.resumo_voz())
        seth_voz.iniciar("Uma frase.")
        self.assertIsNotNone(seth_voz.estado()["ultimo_uso"])
        self.assertIn("no ar", seth_voz.resumo_voz())
        self.assertIn("último uso: ", seth_voz.resumo_voz())
        self.assertEqual(seth_voz.estado()["ultimo_motivo"], "falei a resposta inteira")

    def test_resumo_diz_parado_quando_o_piper_esta_fora(self):
        self.no_ar.unlink()
        self.assertIn("parado (sobe sob demanda", seth_voz.resumo_voz())
        self.assertEqual(self.systemctl_log(), "", "ler o resumo não pode ligar o serviço")

    def test_resumo_diz_quando_o_piper_carregou_outro_modelo(self):
        self.piper.estado["modelo"] = MODELO_ERRADO
        self.assertIn("NÃO é a voz do sistema", seth_voz.resumo_voz())


class VozAudioTests(FalaFalsaTests):
    """Conversa por voz (23/11/2026): sintetizar() devolve o WAV de um trecho e não toca nada na Máquina."""

    def test_sintetiza_um_trecho_com_a_voz_do_sistema_sem_tocar(self):
        wav, total = seth_voz.sintetizar(PARAGRAFOS, 1)
        self.assertTrue(wav.startswith(b"RIFF"))
        self.assertEqual(total, 3)
        self.assertEqual(self.pedidos()[-1]["input"], "Segundo parágrafo, com mais uma frase.")
        self.assertEqual(self.pedidos()[-1]["voice"], "agata")
        self.assertEqual(self.pedidos()[-1]["response_format"], "wav")
        self.assertEqual(self.tocados(), [], "quem toca é o navegador: nada pode sair pelo player da Máquina")

    def test_servico_parado_sobe_e_nao_e_desligado_depois_de_sintetizar(self):
        self.no_ar.unlink()
        seth_voz.sintetizar("Um trecho só.")
        self.assertIn("start", self.systemctl_log())
        self.assertNotIn("stop", self.systemctl_log(), "cada trecho pediria um ciclo de liga e desliga")

    def test_texto_vazio_ou_so_codigo_nao_sintetiza(self):
        with self.assertRaises(seth_voz.ErroVoz) as c:
            seth_voz.sintetizar("   ")
        self.assertEqual(c.exception.status, 400)
        with self.assertRaises(seth_voz.ErroVoz) as c:
            seth_voz.sintetizar("```\nprint(1)\n```")
        self.assertEqual(c.exception.status, 400)
        self.assertEqual(self.pedidos(), [])

    def test_texto_acima_do_limite_depois_de_preparado_e_413(self):
        with self.assertRaises(seth_voz.ErroVoz) as c:
            seth_voz.sintetizar("palavra " * 2000)
        self.assertEqual(c.exception.status, 413)
        self.assertEqual(c.exception.motivo, "resposta longa demais para falar. Peça um resumo.")
        self.assertEqual(self.pedidos(), [])

    def test_trecho_booleano_nao_vale_como_indice(self):
        for trecho in (True, False):
            with self.assertRaises(seth_voz.ErroVoz) as c:
                seth_voz.sintetizar(PARAGRAFOS, trecho)
            self.assertEqual(c.exception.status, 400, trecho)
        self.assertEqual(self.pedidos(), [])

    def test_segunda_sintese_espera_a_primeira_e_depois_recebe_503(self):
        """Semáforo de uma síntese: enquanto outra segura a vaga, o pedido espera o prazo e recebe 503."""
        seth_voz._SINTESE.acquire()
        try:
            with mock.patch.object(seth_voz, "ESPERA_SINTESE_S", 0.2):
                with self.assertRaises(seth_voz.ErroVoz) as c:
                    seth_voz.sintetizar("Olá.")
            self.assertEqual(c.exception.status, 503)
            self.assertIn("ocupada", c.exception.motivo)
            self.assertEqual(self.pedidos(), [], "o pedido que esperou não chegou ao piper")
        finally:
            seth_voz._SINTESE.release()
        wav, _total = seth_voz.sintetizar("Olá.")
        self.assertTrue(wav.startswith(b"RIFF"), "liberada a vaga, a síntese volta a funcionar")

    def test_a_vaga_volta_mesmo_quando_a_sintese_falha(self):
        self.piper.estado["falha_no_pedido"] = 1
        with self.assertRaises(seth_voz.ErroVoz):
            seth_voz.sintetizar("Olá.")
        self.assertTrue(seth_voz._SINTESE.acquire(timeout=1), "a vaga é liberada no erro")
        seth_voz._SINTESE.release()

    def test_trecho_fora_do_texto_ou_que_nao_e_numero_e_400(self):
        for trecho in (9, -1, "1"):
            with self.assertRaises(seth_voz.ErroVoz) as c:
                seth_voz.sintetizar(PARAGRAFOS, trecho)
            self.assertEqual(c.exception.status, 400, trecho)
        self.assertEqual(self.pedidos(), [])

    def test_outro_modelo_no_piper_nao_sintetiza(self):
        self.piper.estado["modelo"] = MODELO_ERRADO
        with self.assertRaises(seth_voz.ErroVoz) as c:
            seth_voz.sintetizar("Olá.")
        self.assertEqual(c.exception.status, 503)
        self.assertEqual(self.pedidos(), [])

    def test_falha_da_sintese_e_502(self):
        self.piper.estado["falha_no_pedido"] = 1
        with self.assertRaises(seth_voz.ErroVoz) as c:
            seth_voz.sintetizar("Olá.")
        self.assertEqual(c.exception.status, 502)

    def test_resposta_que_nao_e_wav_e_502(self):
        self.piper.estado["nao_wav"] = True
        with self.assertRaises(seth_voz.ErroVoz) as c:
            seth_voz.sintetizar("Olá.")
        self.assertEqual(c.exception.status, 502)


class RotasVozTests(FalaFalsaTests):
    """As rotas do painel: origem, tamanho, formato e o que chega ao módulo. Sobe o painel numa porta livre."""

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

    def pede(self, caminho, metodo="GET", corpo=None, cabecalhos=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=60)
        try:
            cab = dict(cabecalhos or {})
            if corpo is not None:
                cab.setdefault("Content-Type", "application/json")
            conn.request(metodo, caminho, body=corpo, headers=cab)
            resposta = conn.getresponse()
            bruto = resposta.read()
            try:
                return resposta.status, json.loads(bruto or b"{}")
            except ValueError:  # 403 de origem cruzada sai em texto, como as demais rotas /api/*
                return resposta.status, bruto.decode("utf-8", errors="replace")
        finally:
            conn.close()

    MESMA_ORIGEM = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin"}

    def test_fala_pela_rota_responde_falou(self):
        corpo = json.dumps({"texto": "Olá. Teste pela rota."}).encode("utf-8")
        status, dados = self.pede("/api/seth/ouvir", "POST", corpo, self.MESMA_ORIGEM)
        self.assertEqual(status, 200)
        self.assertTrue(dados["falou"])
        self.assertEqual(self.pedidos()[0]["voice"], "agata")

    def test_fala_sem_origem_ou_de_outro_site_recebe_403(self):
        corpo = json.dumps({"texto": "Olá."}).encode("utf-8")
        self.assertEqual(self.pede("/api/seth/ouvir", "POST", corpo, {})[0], 403)
        self.assertEqual(self.pede("/api/seth/ouvir", "POST", corpo,
                                   {"Origin": "http://evil.example", "Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(self.pedidos(), [], "pedido recusado não pode chegar à voz")

    def test_fala_com_json_ruim_ou_grande_e_recusada(self):
        self.assertEqual(self.pede("/api/seth/ouvir", "POST", b"{nao-json", self.MESMA_ORIGEM)[0], 400)
        # 413 pelo Content-Length declarado (o servidor não lê o corpo); corpo pequeno, para o teste não depender do fechamento.
        pequeno = json.dumps({"texto": "x"}).encode("utf-8")
        self.assertEqual(self.pede("/api/seth/ouvir", "POST", pequeno,
                                   {**self.MESMA_ORIGEM, "Content-Length": str(seth_voz.LIMITE_CORPO_BYTES + 10)})[0], 413)
        self.assertEqual(self.pede("/api/seth/ouvir", "POST", json.dumps({"texto": ""}).encode(), self.MESMA_ORIGEM)[0], 400)

    def test_estado_so_le_e_recusa_origem_cruzada(self):
        status, dados = self.pede("/api/seth/ouvir", "GET", None, self.MESMA_ORIGEM)
        self.assertEqual(status, 200)
        self.assertFalse(dados["falando"])
        self.assertEqual(self.pede("/api/seth/ouvir", "GET", None, {"Origin": "http://evil.example"})[0], 403)

    def test_parar_responde_e_recusa_origem_cruzada(self):
        status, dados = self.pede("/api/seth/ouvir/parar", "POST", b"", self.MESMA_ORIGEM)
        self.assertEqual(status, 200)
        self.assertFalse(dados["falando"])
        self.assertEqual(self.pede("/api/seth/ouvir/parar", "POST", b"", {"Origin": "http://evil.example"})[0], 403)

    def test_ditado_pela_rota_recusa_origem_cruzada_e_formato_que_nao_e_audio(self):
        self.assertEqual(self.pede("/api/seth/ditado", "POST", b"\x00\x01", {"Content-Type": "audio/webm"})[0], 403)
        status, dados = self.pede("/api/seth/ditado", "POST", b"\x00\x01", {**self.MESMA_ORIGEM, "Content-Type": "text/plain"})
        self.assertEqual(status, 415)
        self.assertIn("erro", dados)

    def pede_bruto(self, corpo, cabecalhos):
        """Pedido de voz-audio: devolve (status, cabeçalhos em minúsculas, corpo cru). O WAV não é JSON."""
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=60)
        try:
            cab = {"Content-Type": "application/json", **cabecalhos}
            conn.request("POST", "/api/seth/voz-audio", body=corpo, headers=cab)
            resposta = conn.getresponse()
            return resposta.status, {k.lower(): v for k, v in resposta.getheaders()}, resposta.read()
        finally:
            conn.close()

    def test_voz_audio_devolve_o_wav_de_um_trecho_e_os_cabecalhos(self):
        corpo = json.dumps({"texto": PARAGRAFOS, "trecho": 2}).encode("utf-8")
        status, cab, wav = self.pede_bruto(corpo, self.MESMA_ORIGEM)
        self.assertEqual(status, 200)
        self.assertEqual(cab["content-type"], "audio/wav")
        self.assertEqual(cab["x-trechos"], "3")
        self.assertEqual(cab["x-trecho"], "2")
        self.assertTrue(wav.startswith(b"RIFF"))
        self.assertEqual(self.pedidos()[-1]["input"], "Terceiro e último.")
        self.assertEqual(self.tocados(), [], "a rota não toca na Máquina")

    def test_voz_audio_manda_um_so_cabecalho_de_cache(self):
        corpo = json.dumps({"texto": PARAGRAFOS}).encode("utf-8")
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=60)
        try:
            conn.request("POST", "/api/seth/voz-audio", body=corpo, headers={"Content-Type": "application/json", **self.MESMA_ORIGEM})
            resposta = conn.getresponse()
            resposta.read()
            cabecalhos = [nome.lower() for nome, _valor in resposta.getheaders()]
        finally:
            conn.close()
        self.assertEqual(cabecalhos.count("cache-control"), 1)

    def test_voz_audio_sem_origem_ou_de_outro_site_recebe_403_e_nao_chega_a_voz(self):
        corpo = json.dumps({"texto": "Olá."}).encode("utf-8")
        self.assertEqual(self.pede_bruto(corpo, {})[0], 403)
        self.assertEqual(self.pede_bruto(corpo, {"Origin": "http://evil.example", "Sec-Fetch-Site": "cross-site"})[0], 403)
        self.assertEqual(self.pedidos(), [])

    def test_voz_audio_texto_vazio_json_ruim_ou_corpo_grande_nao_sintetiza(self):
        self.assertEqual(self.pede("/api/seth/voz-audio", "POST", json.dumps({"texto": ""}).encode(), self.MESMA_ORIGEM)[0], 400)
        self.assertEqual(self.pede("/api/seth/voz-audio", "POST", b"{nao-json", self.MESMA_ORIGEM)[0], 400)
        pequeno = json.dumps({"texto": "x"}).encode("utf-8")
        self.assertEqual(self.pede("/api/seth/voz-audio", "POST", pequeno,
                                   {**self.MESMA_ORIGEM, "Content-Length": str(seth_voz.LIMITE_CORPO_BYTES + 10)})[0], 413)
        self.assertEqual(self.pedidos(), [])

    def test_voz_audio_com_falha_da_sintese_responde_502_em_json(self):
        self.piper.estado["falha_no_pedido"] = 1
        corpo = json.dumps({"texto": "Olá."}).encode("utf-8")
        status, dados = self.pede("/api/seth/voz-audio", "POST", corpo, self.MESMA_ORIGEM)
        self.assertEqual(status, 502)
        self.assertIn("erro", dados)

    def test_voz_audio_com_outro_modelo_responde_503(self):
        self.piper.estado["modelo"] = MODELO_ERRADO
        corpo = json.dumps({"texto": "Olá."}).encode("utf-8")
        status, dados = self.pede("/api/seth/voz-audio", "POST", corpo, self.MESMA_ORIGEM)
        self.assertEqual(status, 503)
        self.assertIn("NÃO falei", dados["erro"])
        self.assertEqual(self.pedidos(), [])

    def test_ouvir_continua_igual_ao_lado_da_voz_audio(self):
        corpo = json.dumps({"texto": "Olá. Teste pela rota."}).encode("utf-8")
        status, dados = self.pede("/api/seth/ouvir", "POST", corpo, self.MESMA_ORIGEM)
        self.assertEqual(status, 200)
        self.assertTrue(dados["falou"])
        self.assertEqual(len(self.tocados()), 1, "o ouvir antigo continua tocando na Máquina, um trecho, pelo player")


class SentidosVozTests(unittest.TestCase):
    """A linha 'voz' da página Sentidos vem do estado real (nova_versao_painel._estado_sentidos), só leitura."""

    def test_linha_voz_da_pagina_sentidos_usa_o_estado_real(self):
        import nova_versao_painel  # noqa: E402
        with mock.patch.object(seth_voz, "resumo_voz", return_value="piper pt_BR-agata-last · no ar · último uso: 11/11/2026 20:30"):
            estado = nova_versao_painel._estado_sentidos()
        self.assertEqual(estado["ouvido"]["voz"], "piper pt_BR-agata-last · no ar · último uso: 11/11/2026 20:30")
        self.assertNotIn("(inalterada)", estado["ouvido"]["voz"])

    def test_se_a_leitura_da_voz_falhar_a_pagina_nao_quebra(self):
        import nova_versao_painel  # noqa: E402
        with mock.patch.object(seth_voz, "resumo_voz", side_effect=RuntimeError("quebrou")):
            estado = nova_versao_painel._estado_sentidos()
        self.assertEqual(estado["ouvido"]["voz"], "piper pt_BR-agata-last · estado não lido agora")


class ConsistenciaVozTests(unittest.TestCase):
    def test_fala_usa_o_script_do_sistema_e_nao_fixa_a_porta(self):
        """O preparo e o serviço vêm do scripts/agata_falar.py (P-8, de outro dono). O módulo não fixa o endereço do piper."""
        script = (ROOT_REPO / "scripts" / "agata_falar.py").read_text(encoding="utf-8")
        self.assertIn('MODELO_DO_SISTEMA = "pt_BR-agata"', script)
        fonte = (HERE / "seth_voz.py").read_text(encoding="utf-8")
        self.assertIn("agata_falar", fonte)
        self.assertNotIn("127.0.0.1:8890", fonte)


if __name__ == "__main__":
    unittest.main()
