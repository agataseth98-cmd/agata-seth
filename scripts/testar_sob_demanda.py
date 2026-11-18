#!/usr/bin/env python3
"""Testes do desenho sob demanda do Laya e do Ollaya (17/11/2026, decisão do Humano: subir conforme a
necessidade e derrubar após um tempo seguro).

Cada serviço tem três unidades: o .socket (porta pública, fica de pé com o agata.target), o proxy
(systemd-socket-proxyd, sai após 15 min ociosos) e o backend (laya-roteador.service ou ollaya.service, que
sobe pelo proxy e cai com ele por StopWhenUnneeded). Os testes leem config/ e rodam o probe do ExecStartPost
contra listeners locais em porta efêmera, com prazo de 3 s no lugar dos 60 s da unidade. Não tocam em systemd,
em ~/.config/systemd, em produção nem em serviço real.

Rodar: python3 scripts/testar_sob_demanda.py
"""
from __future__ import annotations

import os
import re
import shlex
import socket
import subprocess
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "config"
PROXY_BIN = "/usr/lib/systemd/systemd-socket-proxyd"
CURL_BIN = "/usr/bin/curl"
TIMEOUT_BIN = "/usr/bin/timeout"
PRAZO_PROBE_S = 60    # prazo global do ExecStartPost (timeout 60)
TIMEOUT_START_S = 90  # TimeoutStartSec do backend: tem de passar do prazo do probe

# (socket, proxy, backend, porta pública, porta interna)
SERVICOS = (
    ("laya-roteador.socket", "laya-roteador-proxy.service", "laya-roteador.service", 11436, 11446),
    ("ollaya.socket", "ollaya-proxy.service", "ollaya.service", 11435, 11445),
    ("ollama-agata.socket", "ollama-agata-proxy.service", "ollama-agata.service", 11434, 11447),
)


def ler_unidade(caminho: Path) -> dict:
    """Seções -> chave -> lista de valores. Comentário e linha em branco saem; `\\` no fim junta a linha seguinte."""
    logicas, buf = [], ""
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        s = linha.strip()
        if buf == "" and (not s or s.startswith("#")):
            continue
        if linha.rstrip().endswith("\\"):
            buf += linha.rstrip()[:-1] + " "
            continue
        logicas.append(buf + s)
        buf = ""
    secoes: dict = {}
    atual = None
    for linha in logicas:
        if linha.startswith("[") and linha.endswith("]"):
            atual = linha[1:-1]
            secoes.setdefault(atual, {})
            continue
        chave, _, valor = linha.partition("=")
        secoes.setdefault(atual, {}).setdefault(chave.strip(), []).append(valor.strip())
    return secoes


def ler_manifesto() -> list[list[str]]:
    linhas = []
    for linha in (CONFIG / "servicos-agata.txt").read_text(encoding="utf-8").splitlines():
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        campos = [c.strip() for c in linha.split("|")]
        assert len(campos) == 5, linha
        linhas.append(campos)
    return linhas


def comando_do_probe(unidade: Path) -> list[str]:
    """O ExecStartPost da unidade, separado em argumentos: [timeout, 60, bash, -c, script]."""
    valor = ler_unidade(unidade)["Service"]["ExecStartPost"][0]
    argv = shlex.split(valor)
    assert argv[:4] == [TIMEOUT_BIN, str(PRAZO_PROBE_S), "/usr/bin/bash", "-c"], argv[:4]
    return argv


def rodar_probe(argv: list[str], porta_orig: int, porta_nova: int, prazo: int = 3) -> int:
    """Roda o probe com a porta trocada e prazo de `prazo` s (a unidade tem 60 s)."""
    script = re.sub(rf"(127\.0\.0\.1[:/]){porta_orig}\b", rf"\g<1>{porta_nova}", argv[4])
    assert str(porta_nova) in script and "127.0.0.1" in script, script
    r = subprocess.run([TIMEOUT_BIN, str(prazo), "/usr/bin/bash", "-c", script],
                       capture_output=True, text=True, timeout=60)
    return r.returncode


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class UnidadesTest(unittest.TestCase):
    def test_socket_fica_na_porta_publica_no_loopback_e_no_target(self):
        for sock, proxy, _backend, publica, _interna in SERVICOS:
            with self.subTest(unidade=sock):
                s = ler_unidade(CONFIG / sock)
                self.assertEqual(s["Socket"]["ListenStream"], [f"127.0.0.1:{publica}"])
                self.assertEqual(s["Socket"]["Service"], [proxy])
                self.assertEqual(s["Install"]["WantedBy"], ["agata.target"])
                self.assertEqual(s["Unit"]["PartOf"], ["agata.target"])
                self.assertNotIn("Service", s, "socket não tem [Service]")

    def test_proxy_tem_idle_de_15_min_e_so_sobe_com_o_backend(self):
        for _sock, proxy, backend, _publica, interna in SERVICOS:
            with self.subTest(unidade=proxy):
                p = ler_unidade(CONFIG / proxy)
                self.assertNotIn("Install", p, "proxy é ativado só pelo socket")
                self.assertEqual(p["Service"]["ExecStart"],
                                 [f"{PROXY_BIN} --exit-idle-time=15min 127.0.0.1:{interna}"])
                self.assertEqual(p["Unit"]["Requires"], [backend])
                self.assertEqual(p["Unit"]["After"], [backend])
                self.assertEqual(p["Unit"]["PartOf"], ["agata.target"])

    def test_backend_nao_sobe_no_boot_e_cai_quando_ninguem_precisa(self):
        for _sock, _proxy, backend, _publica, _interna in SERVICOS:
            with self.subTest(unidade=backend):
                b = ler_unidade(CONFIG / backend)
                self.assertNotIn("Install", b, "backend não tem [Install]: quem fica no target é o socket")
                self.assertEqual(b["Unit"]["StopWhenUnneeded"], ["yes"])
                self.assertEqual(b["Unit"]["PartOf"], ["agata.target"])

    def test_prazo_do_probe_cabe_dentro_do_timeout_de_start(self):
        for _sock, _proxy, backend, _publica, _interna in SERVICOS:
            with self.subTest(unidade=backend):
                b = ler_unidade(CONFIG / backend)
                self.assertEqual(b["Service"]["TimeoutStartSec"], [str(TIMEOUT_START_S)])
                self.assertGreater(TIMEOUT_START_S, PRAZO_PROBE_S)
                comando_do_probe(CONFIG / backend)

    def test_backend_escuta_na_porta_interna_e_nao_na_publica(self):
        laya = ler_unidade(CONFIG / "laya-roteador.service")
        self.assertIn("LAYA_PORT=11446", laya["Service"]["Environment"])
        self.assertNotIn("LAYA_PORT=11436", laya["Service"]["Environment"])
        ollaya = ler_unidade(CONFIG / "ollaya.service")
        exec_start = ollaya["Service"]["ExecStart"][0]
        self.assertIn("-p 127.0.0.1:11445:11435", exec_start)
        self.assertNotIn("127.0.0.1:11435:11435", exec_start)

    def test_ollama_escuta_so_na_porta_interna_com_modelos_do_usuario(self):
        o = ler_unidade(CONFIG / "ollama-agata.service")
        env = o["Service"]["Environment"]
        self.assertIn("OLLAMA_HOST=127.0.0.1:11447", env)
        self.assertNotIn("OLLAMA_HOST=127.0.0.1:11434", env)
        self.assertNotIn("User", o["Service"], "unit de usuário, sem User=")
        self.assertIn("OLLAMA_MODELS=%h/.local/share/ollama/models", env)
        self.assertEqual(o["Service"]["ExecStart"], ["/usr/local/bin/ollama serve"])
        self.assertIn("ReadWritePaths", o["Service"])
        self.assertFalse(any("0.0.0.0" in v for vs in o["Service"].values() for v in vs))

    def test_ollaya_derruba_o_conteiner_mesmo_se_o_probe_falhar(self):
        ollaya = ler_unidade(CONFIG / "ollaya.service")
        self.assertEqual(ollaya["Service"]["ExecStop"], ["/usr/bin/docker stop ollaya"])
        self.assertEqual(ollaya["Service"]["ExecStopPost"], ["-/usr/bin/docker stop ollaya"])

    def test_clientes_seguem_usando_a_porta_publica(self):
        decisor = (RAIZ / "redesign" / "router" / "decisor.py").read_text(encoding="utf-8")
        self.assertIn('"AGATA_DECISOR_URL", "http://127.0.0.1:11435"', decisor)
        self.assertIn('"AGATA_LAYA_URL", "http://127.0.0.1:11436"', decisor)
        rota = (RAIZ / "redesign" / "laya" / "laya_roteador.py").read_text(encoding="utf-8")
        self.assertIn("http://127.0.0.1:11435/v1/systemone", rota)

    def test_avaliar_decisor_tira_os_sockets_junto(self):
        fonte = (RAIZ / "scripts" / "avaliar_decisor.py").read_text(encoding="utf-8")
        for unidade in ("ollaya.socket", "laya-roteador.socket", "ollaya-proxy.service", "laya-roteador-proxy.service"):
            self.assertIn(f'"{unidade}"', fonte)

    def test_todo_unit_do_config_com_target_esta_no_manifesto(self):
        declaradas = {c[0] for c in ler_manifesto()}
        for arq in sorted(CONFIG.iterdir()):
            if arq.suffix not in {".service", ".socket", ".timer"}:
                continue
            texto = arq.read_text(encoding="utf-8")
            if re.search(r"^(WantedBy|PartOf)=agata\.target\s*$", texto, re.M):
                self.assertIn(arq.name, declaradas, f"{arq.name} tem agata.target e falta em servicos-agata.txt")


class ManifestoTest(unittest.TestCase):
    def test_linhas_do_sob_demanda_no_manifesto(self):
        linhas = {c[0]: c for c in ler_manifesto()}
        for sock, proxy, backend, publica, interna in SERVICOS:
            with self.subTest(servico=sock):
                self.assertEqual(linhas[sock][1:4], ["usuario", str(publica), "sim"])
                self.assertEqual(linhas[proxy][1:4], ["usuario", "-", "nao"])
                self.assertEqual(linhas[backend][1:4], ["usuario", str(interna), "nao"])
                self.assertTrue(linhas[backend][4].startswith(f"config/{backend}"), linhas[backend][4])

    def test_portas_internas_declaradas_em_loopback(self):
        portas = (CONFIG / "portas-agata.txt").read_text(encoding="utf-8")
        for _sock, _proxy, _backend, _publica, interna in SERVICOS:
            with self.subTest(porta=interna):
                self.assertRegex(portas, rf"(?m)^{interna}\|[^|\n]+\|127\.0\.0\.1$")


class ProbeTest(unittest.TestCase):
    """O probe do ExecStartPost: só libera o proxy quando o backend responde na porta interna, dentro do prazo."""

    def test_sintaxe_do_probe_e_valida(self):
        for _sock, _proxy, backend, _publica, _interna in SERVICOS:
            with self.subTest(unidade=backend):
                r = subprocess.run(["/usr/bin/bash", "-n", "-c", comando_do_probe(CONFIG / backend)[4]],
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)

    def test_probe_do_laya_passa_so_com_a_porta_aberta(self):
        argv = comando_do_probe(CONFIG / "laya-roteador.service")
        self.assertNotEqual(rodar_probe(argv, 11446, porta_livre()), 0)
        with socket.socket() as srv:
            srv.bind(("127.0.0.1", 0))
            srv.listen(4)
            self.assertEqual(rodar_probe(argv, 11446, srv.getsockname()[1]), 0)

    def test_probe_do_ollama_passa_com_qualquer_resposta_http_e_falha_sem_servidor(self):
        if not os.path.exists(CURL_BIN):
            self.skipTest("sem /usr/bin/curl")
        argv = comando_do_probe(CONFIG / "ollama-agata.service")
        self.assertIn("-m 2", argv[4])

        class Ok(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Ollama is running")

            def log_message(self, *args):
                pass

        http = HTTPServer(("127.0.0.1", 0), Ok)
        threading.Thread(target=http.serve_forever, daemon=True).start()
        try:
            self.assertEqual(rodar_probe(argv, 11447, http.server_address[1]), 0)
        finally:
            http.shutdown()
            http.server_close()
        self.assertNotEqual(rodar_probe(argv, 11447, porta_livre()), 0)

    def test_probe_do_ollaya_exige_resposta_http_e_nao_so_tcp(self):
        if not os.path.exists(CURL_BIN):
            self.skipTest("sem /usr/bin/curl")
        argv = comando_do_probe(CONFIG / "ollaya.service")
        self.assertIn("-m 2", argv[4])
        # docker-proxy aceita a conexão antes de o contêiner escutar: aqui o servidor aceita e fecha sem responder.
        mudo = socket.socket()
        mudo.bind(("127.0.0.1", 0))
        mudo.listen(4)

        def fechar_sem_responder():
            while True:
                try:
                    conn, _ = mudo.accept()
                except OSError:
                    return
                conn.close()

        threading.Thread(target=fechar_sem_responder, daemon=True).start()
        try:
            self.assertNotEqual(rodar_probe(argv, 11445, mudo.getsockname()[1]), 0)
        finally:
            mudo.close()

        class Ok(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(404)
                self.end_headers()

            def log_message(self, *args):
                pass

        http = HTTPServer(("127.0.0.1", 0), Ok)
        threading.Thread(target=http.serve_forever, daemon=True).start()
        try:
            self.assertEqual(rodar_probe(argv, 11445, http.server_address[1]), 0)
        finally:
            http.shutdown()
            http.server_close()
        self.assertNotEqual(rodar_probe(argv, 11445, porta_livre()), 0)


if __name__ == "__main__":
    unittest.main()
