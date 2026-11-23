"""Testes das rotas locais por tipo (18/11/2026): rotas_locais.py e o gancho no seth_gateway. Sem rede e sem provedor.

Cobre: tipo do pedido; escolha pela ficha (tipo certo, classe, teto de entrada, prioridade); painel que SÓ
RESTRINGE (standby tira, liberado não acrescenta, arquivo ausente ou ilegível = sem efeito); Ollama fora = regra
de sempre; chave SETH_ROTAS_LOCAIS=0; a ficha real passa na validação; e o gateway de verdade, POST e GET:
rota local usada, queda segura (HTTP 500, resposta vazia, Ollama fora, standby) e GET intacto.
Rodar: pytest -q redesign/router/test_rotas_locais.py
"""
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rotas"))

import seth_gateway as g  # noqa: E402


@pytest.fixture(autouse=True)
def _uso_capivara_em_tmp(tmp_path, monkeypatch):
    """(23/11/2026) O log de uso da Capivara vai para um temporário: teste nunca grava no uso.jsonl real."""
    monkeypatch.setenv("AGATA_CAPIVARA_USO", str(tmp_path / "uso.jsonl"))
    # sem registro de capacidades: os testes de rota local e de fila seguem o combo de sempre; a escolha por capacidade
    # tem os seus próprios testes, com registro temporário (o registro real muda com a Capivara)
    monkeypatch.setattr(g.sombra_capacidade, "_caminho_registro", lambda p=tmp_path / "sem-registro.json": p)
import rotas_locais as rl  # noqa: E402
import ficha as ficha_mod  # noqa: E402

TOKEN = "TOKEN-" + "DE-TESTE-NAO-E-SEGREDO"


def _rota(id, modelo, tipos, prio=10, maxt=6000, classes=("publico", "sintetico", "pessoal")):
    return {"id": id, "provedor": "ollama", "modelo": modelo, "categoria": "local",
            "classes_permitidas": list(classes), "tipos": list(tipos), "prioridade": prio,
            "max_tokens_entrada": maxt, "treina_com_prompts": "nao_aplica", "cota": "-",
            "compartilhada_com_seth": False, "cota_medida": False, "conferida_em": "2026-11-18", "fonte": "teste"}


@pytest.fixture
def ficha(tmp_path, monkeypatch):
    f = tmp_path / "ficha.json"
    f.write_text(json.dumps({"schema_version": 1, "decisoes": {}, "rotas": [
        _rota("local-a", "a:1b", ["codigo", "conversa"], 10, 12000),  # 23/11: a injeção real passou de 6000 tokens estimados (AGENTS.md maior)
        _rota("local-b", "b:30b", ["json", "conversa"], 20, 16000),
        _rota("local-c", "c:8b", ["ferramenta"], 10, 12000, classes=("publico",)),
        {"id": "reserva", "provedor": "ollama", "modelo": "r:9b", "categoria": "local", "tipos": [],
         "classes_permitidas": ["publico", "pessoal"], "treina_com_prompts": "nao_aplica", "cota": "-",
         "compartilhada_com_seth": False, "cota_medida": False, "conferida_em": "x", "fonte": "t"},
        {"id": "nuvem", "provedor": "gemini", "modelo": "g", "categoria": "gratuito", "tipos": ["conversa"],
         "classes_permitidas": ["publico"], "treina_com_prompts": "nao_conferido", "cota": "-",
         "compartilhada_com_seth": True, "cota_medida": False, "conferida_em": "x", "fonte": "t"},
    ]}), encoding="utf-8")
    monkeypatch.setattr(rl, "FICHA_PADRAO", f)
    monkeypatch.setenv("AGATA_DECISOES_MODELOS", str(tmp_path / "decisoes.jsonl"))
    monkeypatch.delenv("SETH_ROTAS_LOCAIS", raising=False)
    for c in (rl._CACHE_FICHA, rl._CACHE_PAINEL):
        c["mtime"] = None
    return f


def _dec(tmp_path, *linhas):
    (tmp_path / "decisoes.jsonl").write_text("\n".join(json.dumps(x) if isinstance(x, dict) else x for x in linhas)
                                             + "\n", encoding="utf-8")
    rl._CACHE_PAINEL["mtime"] = None


def _p(texto="oi", **extra):
    return dict({"model": "seth-livre", "messages": [{"role": "user", "content": texto}]}, **extra)


# --- funções puras -------------------------------------------------------------------------------------------

def test_tipo_do_pedido():
    assert rl.tipo_do_pedido(_p("bom dia")) == "conversa"
    assert rl.tipo_do_pedido(_p("```py\nx=1\n```")) == "codigo"
    assert rl.tipo_do_pedido(_p("x", tools=[{"type": "function"}])) == "ferramenta"
    assert rl.tipo_do_pedido(_p("x", response_format={"type": "json_object"})) == "json"
    assert rl.tipo_do_pedido(_p("a" * 30000)) == "contexto"
    assert rl.tipo_do_pedido({"messages": "quebrado"}) == "conversa"


def test_escolha_pelo_tipo_e_prioridade(ficha):
    e = lambda p, t, pub=False: rl.escolher(p, t, pub, checar_ollama=False)  # noqa: E731
    assert e(_p(), "codigo")["id"] == "local-a"
    assert e(_p(), "conversa")["id"] == "local-a"  # prioridade 10 vence a 20
    assert e(_p(), "json")["id"] == "local-b"
    assert e(_p(), "contexto") is None  # ninguém ganhou contexto nesta ficha
    assert e(_p(), "inexistente") is None


def test_so_rota_local_com_tipos(ficha):
    ids = {r["id"] for r in rl.carregar_rotas(ficha)}
    assert ids == {"local-a", "local-b", "local-c"}  # reserva (sem tipos) e nuvem nunca entram


def test_classe_e_teto_de_entrada(ficha):
    assert rl.escolher(_p(), "ferramenta", False, checar_ollama=False) is None  # c só aceita público
    assert rl.escolher(_p(), "ferramenta", True, checar_ollama=False)["id"] == "local-c"
    grande = _p("a" * 40000)  # ~13333 tokens > teto de local-a (12000)
    assert rl.escolher(grande, "conversa", False, checar_ollama=False)["id"] == "local-b"


def test_painel_standby_tira(ficha, tmp_path):
    _dec(tmp_path, {"id": "ollama-local/a:1b", "acao": "standby"})
    assert rl.escolher(_p(), "conversa", False, checar_ollama=False)["id"] == "local-b"
    _dec(tmp_path, {"id": "ollama-local/a:1b", "acao": "standby"}, {"id": "ollama-local/a:1b", "acao": "liberar"})
    assert rl.escolher(_p(), "conversa", False, checar_ollama=False)["id"] == "local-a"  # última decisão vale
    _dec(tmp_path, {"id": "local-a", "acao": "standby"}, {"id": "b:30b", "acao": "standby"})
    assert rl.escolher(_p(), "conversa", False, checar_ollama=False) is None


def test_painel_liberado_nao_acrescenta(ficha, tmp_path):
    _dec(tmp_path, {"id": "ollama-local/qualquer:7b", "acao": "liberar"}, {"id": "nuvem", "acao": "liberar"})
    assert rl.escolher(_p(), "contexto", False, checar_ollama=False) is None
    assert rl.escolher(_p(), "conversa", False, checar_ollama=False)["id"] == "local-a"


@pytest.mark.parametrize("conteudo", [None, "isto nao e json\n{{{\n", b"\xff\xfe\x00lixo"])
def test_painel_ausente_ou_ilegivel_nao_restringe(ficha, tmp_path, conteudo):
    arq = tmp_path / "decisoes.jsonl"
    if isinstance(conteudo, bytes):
        arq.write_bytes(conteudo)
    elif conteudo:
        arq.write_text(conteudo, encoding="utf-8")
    rl._CACHE_PAINEL["mtime"] = None
    assert rl.escolher(_p(), "conversa", False, checar_ollama=False)["id"] == "local-a"


def test_painel_caminho_e_pasta_nao_quebra(ficha, tmp_path, monkeypatch):
    monkeypatch.setenv("AGATA_DECISOES_MODELOS", str(tmp_path))  # diretório no lugar do arquivo
    assert rl.estado_painel() == {}
    assert rl.escolher(_p(), "conversa", False, checar_ollama=False)["id"] == "local-a"


def test_ollama_fora_nao_escolhe(ficha, monkeypatch):
    monkeypatch.setattr(rl, "ollama_no_ar", lambda *a, **k: False)
    assert rl.escolher(_p(), "conversa", False) is None
    monkeypatch.setattr(rl, "ollama_no_ar", lambda *a, **k: True)
    assert rl.escolher(_p(), "conversa", False)["id"] == "local-a"


def test_teste_de_porta_real_fechada():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    porta = s.getsockname()[1]
    s.close()  # porta livre e fechada
    assert rl.ollama_no_ar(("127.0.0.1", porta), validade=0) is False


def test_chave_desliga(ficha, monkeypatch):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    assert rl.escolher(_p(), "conversa", False, checar_ollama=False) is None


def test_ficha_ausente_ou_quebrada(tmp_path):
    assert rl.carregar_rotas(tmp_path / "nao-existe.json") == []
    q = tmp_path / "q.json"
    q.write_text("{{", encoding="utf-8")
    assert rl.carregar_rotas(q) == []


def test_ficha_real_valida_e_cobre_os_tipos():
    dados = json.loads(ficha_mod.PADRAO.read_text(encoding="utf-8"))
    erros, _ = ficha_mod.verificar(dados)
    assert erros == []
    por_id = {r["id"]: r for r in rl.carregar_rotas(ficha_mod.PADRAO)}
    assert {i: set(r["tipos"]) for i, r in por_id.items()} == {"local-qwen3-30b": {"json", "codigo", "contexto"}}
    todas = {r["id"]: r for r in dados["rotas"]}
    for ident in ("local-lfm3", "local-rlm", "local-lumi"):  # catalogados, não roteados
        assert todas[ident]["tipos"] == []
    # o qwen3.5-9b continua na ficha como reserva, sem tipo
    assert any(r["modelo"] == "qwen3.5-9b-64k" for r in dados["rotas"])
    assert "qwen3.5-9b-64k" not in {r["modelo"] for r in por_id.values()}
    # as rotas locais por tipo continuam só locais; a nuvem tem a sua lista, só pública
    assert all(r["categoria"] == "local" for r in por_id.values())
    nuv = {r["id"]: r for r in rl.carregar_rotas_nuvem(ficha_mod.PADRAO)}
    assert {i: set(r["tipos"]) for i, r in nuv.items()} == {
        "nvidia-nemotron-super-vl": {"conversa"}, "nvidia-nemotron-bolt": {"codigo", "json"}}
    assert {rl.nome_nuvem(r) for r in nuv.values()} == {
        "nvidia/nvidia/nemotron-3.5-super-vl-120b-a12b", "nvidia/nvidia/nemotron-3.5-bolt-e4b"}
    laguna = {r["id"]: r for r in dados["rotas"]}["nvidia-laguna-xs"]  # catalogada, liberada no painel, sem rota
    assert laguna["tipos"] == [] and "faixa publica" in laguna["papel"] and laguna["classes_permitidas"] == ["publico"]
    for r in nuv.values():
        assert r["classes_permitidas"] == ["publico"] and r["cota_medida"] is False
        assert r["treina_com_prompts"] == "nao_conferido_aceito_pelo_humano" and "19/11/2026 09:06" in r["fonte"]
    assert len(dados["rotas"]) >= 12  # nenhuma rota atual saiu


def test_ficha_rejeita_tipo_em_nuvem_paga_ou_com_dado_pessoal_e_sem_teto():
    erros, _ = ficha_mod.verificar({"rotas": [dict(_rota("x", "m", ["codigo"]), categoria="pago",
                                                   classes_permitidas=["publico"])]})
    assert any("só vale para rota local ou gratuita" in e for e in erros)
    erros, _ = ficha_mod.verificar({"rotas": [dict(_rota("x", "m", ["codigo"]), categoria="gratuito",
                                                   classes_permitidas=["publico", "pessoal"])]})
    assert any("D2" in e for e in erros) and any("classe pública" in e for e in erros)
    erros, _ = ficha_mod.verificar({"rotas": [dict(_rota("x", "m", ["codigo"]), categoria="gratuito",
                                                   classes_permitidas=["publico"])]})
    assert erros == []
    sem_teto = _rota("y", "m", ["codigo"])
    del sem_teto["max_tokens_entrada"]
    erros, _ = ficha_mod.verificar({"rotas": [sem_teto]})
    assert any("max_tokens_entrada" in e for e in erros)


# --- gateway de verdade (POST e GET) -------------------------------------------------------------------------

class _Up(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _enviar(self, status, corpo, ctype="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _sse_lento(self, pausa):
        """SSE de upstream lento: dois pedaços de conteúdo com pausa entre eles, depois o fim."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        try:
            for pedaco in ("olá ", "mundo"):
                linha = {"id": "x", "model": "m-lento", "choices": [{"delta": {"content": pedaco}, "finish_reason": None}]}
                self.wfile.write(("data: " + json.dumps(linha, ensure_ascii=False) + "\n\n").encode("utf-8"))
                self.wfile.flush()
                time.sleep(pausa)
            fim = {"id": "x", "model": "m-lento", "choices": [{"delta": {}, "finish_reason": "stop"}]}
            self.wfile.write(("data: " + json.dumps(fim) + "\n\ndata: [DONE]\n\n").encode("utf-8"))
        except OSError:
            pass
        self.close_connection = True

    def do_GET(self):
        self.server.gets.append(self.path)
        self._enviar(200, json.dumps({"object": "list", "data": [{"id": "seth-livre"}]}).encode())

    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
        self.server.chamadas.append(corpo.get("model"))
        nuvem = str(corpo.get("model", "")).startswith("nvidia/")
        self.server.corpos.append(corpo)
        self.server.cabecalhos.append(dict(self.headers))  # (23/11) prova do caminho de saída (sanitizador)
        if getattr(self.server, "sse_lento", 0) and corpo.get("stream"):  # (23/11) upstream lento, em SSE
            return self._sse_lento(self.server.sse_lento)
        modo = self.server.falhar.get(corpo.get("model"))  # (23/11) falha escolhida para um modelo concreto
        if modo == "500":
            return self._enviar(500, b'{"error":"modelo concreto indisponivel"}')
        if modo == "vazio":
            return self._enviar(200, json.dumps({"model": "m-vazio", "choices": [{"message": {
                "role": "assistant", "content": ""}}]}).encode())
        if nuvem and self.server.nuvem == "500":
            return self._enviar(500, b'{"error":"cota"}')
        if nuvem and self.server.nuvem == "keepalive":  # SSE que só manda keep-alives (nunca conteúdo)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            try:
                for _ in range(80):
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                    time.sleep(0.1)
            except OSError:
                pass
            self.close_connection = True
            return
        if nuvem and self.server.nuvem == "headers_lentos":  # demora nos headers além do prazo
            time.sleep(2.5)
        if nuvem and self.server.nuvem == "json_pingo":  # headers em t=0, 1 pedaço aos 2,5 s e silêncio
            corpo_j = json.dumps({"model": "m", "choices": [{"message": {"content": "x" * 30}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo_j)))
            self.end_headers()
            try:
                self.wfile.flush()
                time.sleep(2.5)
                self.wfile.write(corpo_j[:8])
                self.wfile.flush()
                time.sleep(6)
            except OSError:
                pass
            self.close_connection = True
            return
        if nuvem and self.server.nuvem == "json_lento":  # headers logo, corpo JSON pingado devagar
            corpo_j = json.dumps({"model": "m", "choices": [{"message": {"content": "x" * 30}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(corpo_j)))
            self.end_headers()
            try:
                for i in range(0, len(corpo_j), 8):
                    self.wfile.write(corpo_j[i:i + 8])
                    self.wfile.flush()
                    time.sleep(0.3)
            except OSError:
                pass
            self.close_connection = True
            return
        if nuvem and self.server.nuvem == "vazio":
            return self._enviar(200, json.dumps({"model": "m", "choices": [{"message": {"content": ""}}]}).encode())
        if nuvem:
            return self._enviar(200, json.dumps({"model": "m-nuvem", "choices": [{"message": {
                "role": "assistant", "content": "nuvem ok"}}]}).encode())
        local = str(corpo.get("model", "")).startswith("ollama-local/")
        if local and self.server.local == "500":
            return self._enviar(500, b'{"error":"modelo local indisponivel"}')
        texto = "" if (local and self.server.local == "vazio") else ("local ok" if local else "fila ok")
        self._enviar(200, json.dumps({"model": "m-falso", "choices": [{"message": {"role": "assistant",
                                                                                   "content": texto}}]}).encode())


class _Cen:
    def __init__(self, mp, local="ok"):
        self.up = ThreadingHTTPServer(("127.0.0.1", 0), _Up)
        self.up.chamadas, self.up.gets, self.up.local = [], [], local
        self.up.corpos, self.up.nuvem = [], "ok"
        self.up.cabecalhos, self.up.falhar = [], {}
        self.up.sse_lento = 0  # (23/11) pausa entre pedaços do SSE do upstream lento; 0 = modo normal
        threading.Thread(target=self.up.serve_forever, daemon=True).start()
        mp.setattr(g, "UPSTREAM", f"http://127.0.0.1:{self.up.server_address[1]}")
        self.gw = g.ServidorConcorrenciaLimitada(("127.0.0.1", 0), g._Handler)
        threading.Thread(target=self.gw.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.gw.server_address[1]}"

    def post(self, pergunta="explique o que é um ponteiro", modelo="seth-livre", publico=False, extra=None):
        corpo = dict({"model": modelo, "messages": [{"role": "user", "content": pergunta}]}, **(extra or {}))
        h = {"Content-Type": "application/json"}
        if publico:
            h["X-Agata-Data-Classification"] = "public"
        r = urllib.request.Request(self.base + "/v1/chat/completions", data=json.dumps(corpo).encode(),
                                   method="POST", headers=h)
        with urllib.request.urlopen(r, timeout=30) as x:
            return x.status, json.loads(x.read())["choices"][0]["message"]["content"]

    def get(self, caminho="/v1/models"):
        with urllib.request.urlopen(self.base + caminho, timeout=30) as x:
            return x.status, json.loads(x.read())

    def fechar(self):
        for s in (self.gw, self.up):
            s.shutdown()
            s.server_close()


@pytest.fixture
def gw(ficha, monkeypatch, tmp_path):
    monkeypatch.setenv("AGATA_EMOJI_LOG", str(tmp_path / "emoji.jsonl"))
    monkeypatch.setenv("AGATA_LACO_LOG", str(tmp_path / "laco.jsonl"))
    monkeypatch.setenv("AGATA_CABECALHO_LOG", str(tmp_path / "cabecalho.jsonl"))
    monkeypatch.setattr(g, "MODELO_REAL_PATH", tmp_path / "modelo-real.txt")
    monkeypatch.setattr(g, "_token_interno", lambda: TOKEN)
    monkeypatch.setattr(g, "_estado", lambda: "sync: PASS")
    monkeypatch.setattr(g, "_injeta", lambda payload: payload)
    monkeypatch.setattr(g, "_rota_laya", lambda payload: ("seth-livre", {}))  # sem Laya (rede)
    monkeypatch.setattr(g, "_sombra_rota", lambda *a, **k: None)
    monkeypatch.setattr(g.auditoria_turno, "verificar_resposta_atual", lambda t, m: [])
    monkeypatch.setattr(rl, "ollama_no_ar", lambda *a, **k: True)
    cenarios = []

    def novo(local="ok"):
        c = _Cen(monkeypatch, local)
        cenarios.append(c)
        return c
    yield novo
    for c in cenarios:
        c.fechar()


def test_post_usa_a_rota_local_do_tipo(gw):
    c = gw()
    status, texto = c.post()
    assert status == 200 and "local ok" in texto
    assert c.up.chamadas == ["ollama-local/a:1b"]


def test_post_tipo_sem_dono_segue_a_fila(gw):
    c = gw()
    c.post("a" * 30000)  # contexto: ninguém na ficha de teste
    assert c.up.chamadas == ["seth-pesado"] or c.up.chamadas[0].startswith("seth-")


def test_post_fila_explicita_nao_e_tocada(gw):
    c = gw()
    c.post(modelo="seth-pesado", publico=True)
    assert c.up.chamadas == ["seth-pesado"]


def test_post_faixa_publica_nao_e_tocada(gw):
    c = gw()
    c.post(modelo="seth-public")
    assert c.up.chamadas and c.up.chamadas[0].startswith("seth-")


def test_queda_segura_http_500(gw):
    c = gw(local="500")
    status, texto = c.post()
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas == ["ollama-local/a:1b", "seth-livre"]  # a fila ORIGINAL, não qualquer seth-*


def test_queda_segura_resposta_vazia(gw):
    c = gw(local="vazio")
    status, texto = c.post()
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas == ["ollama-local/a:1b", "seth-livre"]


def test_ollama_fora_vai_direto_para_a_fila(gw, monkeypatch):
    monkeypatch.setattr(rl, "ollama_no_ar", lambda *a, **k: False)
    c = gw()
    status, texto = c.post()
    assert status == 200 and "fila ok" in texto
    assert len(c.up.chamadas) == 1 and c.up.chamadas[0].startswith("seth-")


def test_standby_do_painel_vai_para_a_fila(gw, tmp_path):
    _dec(tmp_path, {"id": "ollama-local/a:1b", "acao": "standby"}, {"id": "ollama-local/b:30b", "acao": "standby"})
    c = gw()
    status, texto = c.post()
    assert status == 200 and len(c.up.chamadas) == 1 and c.up.chamadas[0].startswith("seth-")


def test_painel_ilegivel_nao_muda_nada(gw, tmp_path):
    (tmp_path / "decisoes.jsonl").write_bytes(b"\xff\xfe lixo")
    c = gw()
    c.post()
    assert c.up.chamadas == ["ollama-local/a:1b"]


def test_ferramenta_com_dado_pessoal_nao_vai_a_rota_que_so_aceita_publico(gw):
    c = gw()
    c.post(extra={"tools": [{"type": "function", "function": {"name": "f", "parameters": {}}}]})
    assert c.up.chamadas[0].startswith("seth-")  # local-c só aceita 'publico' nesta ficha de teste


def test_get_passa_sem_erro_e_sem_rota_local(gw):
    c = gw()
    status, corpo = c.get()
    assert status == 200 and corpo["data"][0]["id"] == "seth-livre"
    assert c.up.gets == ["/v1/models"] and c.up.chamadas == []


# --- revisão 18/11: keep-alive, quedas de conexão, segredo, faixas não tocadas --------------------------------

import http.client  # noqa: E402
import socket  # noqa: E402
import urllib.error  # noqa: E402

PERGUNTA = "explique o que é um ponteiro"


def _conn(c):
    return http.client.HTTPConnection("127.0.0.1", c.gw.server_address[1], timeout=30)


def _post_conn(conn, modelo="seth-livre", pergunta=PERGUNTA, headers=None):
    corpo = json.dumps({"model": modelo, "messages": [{"role": "user", "content": pergunta}]})
    conn.request("POST", "/v1/chat/completions", body=corpo,
                 headers=dict({"Content-Type": "application/json"}, **(headers or {})))
    r = conn.getresponse()
    return r.status, r.read()


@pytest.mark.parametrize("local", ["ok", "500", "vazio"])
def test_keepalive_post_local_e_depois_get_na_mesma_conexao(gw, local):
    c = gw(local=local)
    conn = _conn(c)
    status, txt = _post_conn(conn)
    assert status == 200
    n_posts = len(c.up.chamadas)
    conn.request("GET", "/v1/models")
    r = conn.getresponse()
    corpo = r.read()
    conn.close()
    assert r.status == 200 and json.loads(corpo)["data"][0]["id"] == "seth-livre"
    assert c.up.gets == ["/v1/models"]            # uma chamada upstream, sem refazer nada
    assert len(c.up.chamadas) == n_posts          # o GET não reenviou corpo de POST


def test_get_404_na_mesma_conexao_nao_dispara_fallback(gw, monkeypatch):
    c = gw()
    conn = _conn(c)
    _post_conn(conn)
    antes = list(c.up.chamadas)
    monkeypatch.setattr(_Up, "do_GET", lambda self: self._enviar(404, b'{"error":"x"}'))
    conn.request("GET", "/v1/models")
    r = conn.getresponse()
    r.read()
    conn.close()
    assert r.status == 404 and c.up.chamadas == antes


def _urlopen_que_falha_na_local(monkeypatch, erro):
    real = urllib.request.urlopen

    def falso(req, *a, **k):
        corpo = getattr(req, "data", None) or b""
        if b"ollama-local/" in corpo:
            raise erro
        return real(req, *a, **k)
    monkeypatch.setattr(g.urllib.request, "urlopen", falso)


@pytest.mark.parametrize("erro", [urllib.error.URLError("conexão recusada"), ConnectionResetError("reset"),
                                  socket.timeout("timed out"), TimeoutError("timeout")])
def test_queda_de_conexao_ou_timeout_da_rota_local_cai_na_fila(gw, monkeypatch, erro):
    _urlopen_que_falha_na_local(monkeypatch, erro)
    c = gw()
    status, texto = c.post()
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas == ["seth-livre"]  # a local nem chegou ao upstream; a fila de sempre respondeu


def test_timeout_na_leitura_da_rota_local_cai_na_fila(gw, monkeypatch):
    """O upstream aceita e não responde: com o prazo curto, a rota local estoura e a fila original responde."""
    real = urllib.request.urlopen
    monkeypatch.setattr(g.urllib.request, "urlopen", lambda req, *a, **k: real(req, timeout=1) if getattr(
        req, "full_url", "").startswith(g.UPSTREAM) else real(req, *a, **k))

    class Lento(_Up):
        def do_POST(self):
            corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            self.server.chamadas.append(corpo.get("model"))
            if str(corpo.get("model")).startswith("ollama-local/"):
                import time
                time.sleep(3)
                return
            self._enviar(200, json.dumps({"model": "m", "choices": [{"message": {"role": "assistant",
                                                                                 "content": "fila ok"}}]}).encode())
    monkeypatch.setattr(sys.modules[__name__], "_Up", Lento)
    c = gw()
    status, texto = c.post()
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas == ["ollama-local/a:1b", "seth-livre"]


def test_segredo_nunca_vai_a_rota_local(gw):
    c = gw()
    segredo = "sk" + "-" + "TESTEsintetico0123456789abcdefGHIJ"
    c.post(f"explique o que é um ponteiro; minha chave é {segredo}")
    assert c.up.chamadas == ["seth-livre"]  # comportamento de hoje, sem rota local


def test_escolher_recusa_segredo_e_regua_quebrada(ficha, monkeypatch):
    segredo = "sk" + "-" + "TESTEsintetico0123456789abcdefGHIJ"
    assert rl.escolher(_p(f"chave {segredo}"), "conversa", False, checar_ollama=False) is None
    assert rl.escolher(_p(), "conversa", False, checar_ollama=False)["id"] == "local-a"
    import sanitizar
    monkeypatch.setattr(sanitizar, "varrer", lambda t: (_ for _ in ()).throw(RuntimeError("régua fora")))
    assert rl.escolher(_p(), "conversa", False, checar_ollama=False) is None  # falha fechada


def test_seth_livre_com_cabecalho_public_nao_vai_a_local(gw):
    c = gw()
    c.post(publico=True)
    assert c.up.chamadas and not c.up.chamadas[0].startswith("ollama-local/")


def test_seth_pesado_nao_publico_nem_chega_ao_upstream(gw):
    c = gw()
    with pytest.raises(urllib.error.HTTPError) as e:
        c.post(modelo="seth-pesado")  # política atual: modelo externo exige classificação pública
    assert e.value.code == 403 and c.up.chamadas == []


# --- sondas da revisão 2 (do revisor, copiadas para o repositório) -----------------------------------------------
def test_probe_modelo_local_explicito_nao_e_reroteado(gw):
    c = gw()
    c.post(modelo="ollama-local/x")
    assert c.up.chamadas == ["ollama-local/x"]


def test_probe_corpo_incompleto_cai_na_fila(gw, monkeypatch):
    class Cortado(_Up):
        def do_POST(self):
            corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            self.server.chamadas.append(corpo.get("model"))
            if str(corpo.get("model", "")).startswith("ollama-local/"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "500")
                self.end_headers()
                self.wfile.write(b"0123456789")
                self.wfile.flush()
                return
            self._enviar(200, json.dumps({"model": "m", "choices": [{"message": {"role": "assistant",
                                          "content": "fila ok"}}]}).encode())
    monkeypatch.setattr(sys.modules[__name__], "_Up", Cortado)
    c = gw()
    status, texto = c.post()
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas == ["ollama-local/a:1b", "seth-livre"]


def test_probe_timeout_no_corpo_cai_na_fila(gw, monkeypatch):
    real = urllib.request.urlopen
    monkeypatch.setattr(g.urllib.request, "urlopen", lambda req, *a, **k: real(req, timeout=1) if getattr(
        req, "full_url", "").startswith(g.UPSTREAM) else real(req, *a, **k))

    class Pendura(_Up):
        def do_POST(self):
            corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            self.server.chamadas.append(corpo.get("model"))
            if str(corpo.get("model", "")).startswith("ollama-local/"):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "500")
                self.end_headers()
                self.wfile.write(b"{")
                self.wfile.flush()
                import time
                time.sleep(3)
                return
            self._enviar(200, json.dumps({"model": "m", "choices": [{"message": {"role": "assistant",
                                          "content": "fila ok"}}]}).encode())
    monkeypatch.setattr(sys.modules[__name__], "_Up", Pendura)
    c = gw()
    status, texto = c.post()
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas == ["ollama-local/a:1b", "seth-livre"]


# --- revisão r2: reuso real da conexão, prazo próprio, segredo após a injeção real -------------------------------

_INJETA_REAL = g._injeta  # guardado na importação, antes de o fixture trocá-lo por identidade


def test_handler_e_http11():
    assert g._Handler.protocol_version == "HTTP/1.1"


@pytest.mark.parametrize("local", ["ok", "500", "vazio"])
def test_keepalive_reusa_a_mesma_conexao(gw, monkeypatch, local):
    aceitas = []
    setup_orig = g._Handler.setup
    monkeypatch.setattr(g._Handler, "setup", lambda self: (aceitas.append(1), setup_orig(self))[1])
    c = gw(local=local)
    conn = _conn(c)
    status, _ = _post_conn(conn)
    sock = conn.sock
    conn.request("GET", "/v1/models")
    r = conn.getresponse()
    r.read()
    assert status == 200 and r.status == 200
    assert not r.will_close and conn.sock is sock  # a conexão não foi fechada nem refeita
    assert len(aceitas) == 1                       # uma só conexão aceita pelo gateway para os dois pedidos
    assert c.up.gets == ["/v1/models"]
    conn.close()


def test_prazo_proprio_da_rota_local(gw, monkeypatch):
    monkeypatch.setenv("SETH_ROTA_LOCAL_MS", "7000")
    prazos = []
    real = urllib.request.urlopen

    def espia(req, *a, **k):
        if getattr(req, "full_url", "").startswith(g.UPSTREAM):
            prazos.append((b"ollama-local/" in (req.data or b""), k.get("timeout")))
        return real(req, *a, **k)
    monkeypatch.setattr(g.urllib.request, "urlopen", espia)
    c = gw(local="500")
    c.post()
    assert prazos == [(True, 7.0), (False, 180)]  # local com prazo curto; a fila de sempre mantém o teto antigo


def test_prazo_padrao_e_100_5_segundos_e_invalido_volta_ao_padrao(monkeypatch):
    # maior sucesso medido do qwen3-30b-a3b-64k (70,5 s) + 30 s de folga
    monkeypatch.delenv("SETH_ROTA_LOCAL_MS", raising=False)
    assert g._ROTA_LOCAL_MS_PADRAO == 100500 and g._rota_local_seg() == 100.5
    monkeypatch.setenv("SETH_ROTA_LOCAL_MS", "lixo")
    assert g._rota_local_seg() == 100.5
    monkeypatch.setenv("SETH_ROTA_LOCAL_MS", "20000")
    assert g._rota_local_seg() == 20.0


def test_injecao_real_nao_desliga_a_rota_local(ficha, monkeypatch):
    """A hidratação injeta a doutrina (que cita segredo, chave, token): a régua de segredo olhando o payload
    depois do _injeta REAL não pode barrar todo pedido. Sem trocar o _injeta por identidade."""
    monkeypatch.setattr(g, "_estado", lambda: "sync: PASS")
    payload = _INJETA_REAL(_p())
    injetado = [m for m in payload["messages"] if m.get("role") == "system"]
    assert injetado and len(json.dumps(payload)) > 2000  # houve injeção de verdade
    assert rl.tem_segredo(payload) is False
    assert rl.escolher(payload, "conversa", False, checar_ollama=False)["id"] == "local-a"


def test_gateway_com_injecao_real_ainda_usa_a_rota_local(gw, monkeypatch):
    monkeypatch.setattr(g, "_injeta", _INJETA_REAL)
    c = gw()
    status, texto = c.post()
    assert status == 200 and c.up.chamadas[0] == "ollama-local/a:1b"


def test_partida_a_frio_dentro_do_prazo_e_servida_pela_rota_local(gw, monkeypatch):
    """Socket aberto, backend frio: o upstream demora (sobe o Ollama e carrega o modelo) mas responde dentro do
    prazo da rota local. Servida pela local, sem cair na fila."""
    import time
    monkeypatch.setenv("SETH_ROTA_LOCAL_MS", "5000")

    class Frio(_Up):
        def do_POST(self):
            corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            self.server.chamadas.append(corpo.get("model"))
            if str(corpo.get("model")).startswith("ollama-local/"):
                time.sleep(1.5)
            self._enviar(200, json.dumps({"model": "m", "choices": [{"message": {"role": "assistant",
                                          "content": "local ok" if str(corpo.get("model")).startswith("ollama") else "fila ok"}}]}).encode())
    monkeypatch.setattr(sys.modules[__name__], "_Up", Frio)
    c = gw()
    status, texto = c.post()
    assert status == 200 and "local ok" in texto and c.up.chamadas == ["ollama-local/a:1b"]


def test_partida_a_frio_estourando_o_prazo_cai_na_fila(gw, monkeypatch):
    import time
    monkeypatch.setenv("SETH_ROTA_LOCAL_MS", "1000")

    class MuitoFrio(_Up):
        def do_POST(self):
            corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            self.server.chamadas.append(corpo.get("model"))
            if str(corpo.get("model")).startswith("ollama-local/"):
                time.sleep(3)
                return
            self._enviar(200, json.dumps({"model": "m", "choices": [{"message": {"role": "assistant",
                                                                                 "content": "fila ok"}}]}).encode())
    monkeypatch.setattr(sys.modules[__name__], "_Up", MuitoFrio)
    c = gw()
    status, texto = c.post()
    assert status == 200 and "fila ok" in texto and c.up.chamadas == ["ollama-local/a:1b", "seth-livre"]


# --- X-Agata-Nao-Registrar (19/11/2026, opção A do Humano): o canal de voz pede que o pedido não seja registrado ---

def _conn(c):
    import http.client
    return http.client.HTTPConnection("127.0.0.1", int(c.base.rsplit(":", 1)[1]), timeout=30)


def _post_raw(conn, pergunta, cab=None):
    h = {"Content-Type": "application/json", **(cab or {})}
    conn.request("POST", "/v1/chat/completions", json.dumps(
        {"model": "seth-livre", "messages": [{"role": "user", "content": pergunta}]}), h)
    r = conn.getresponse()
    r.read()
    return r


@pytest.fixture
def pedidos(monkeypatch, tmp_path):
    import registro_pedidos
    monkeypatch.setattr(registro_pedidos, "DIR", tmp_path / "pedidos")
    monkeypatch.setenv("SETH_REGISTRO_PEDIDOS", "1")
    return tmp_path / "pedidos"


def _gravado(pasta, espera=1.5):
    """O gateway grava DEPOIS de entregar a resposta (corrida, vista em 19/11/2026): espera até aparecer algo, no máximo
    `espera` s; quem afirma 'não gravou' paga a espera inteira, de propósito."""
    deadline = time.monotonic() + espera
    while True:
        txt = "".join(p.read_text() for p in pasta.glob("*.jsonl")) if pasta.exists() else ""
        if txt or time.monotonic() >= deadline:
            return txt
        time.sleep(0.05)


def test_sem_cabecalho_grava_como_hoje(gw, pedidos):
    c = gw()
    r = _post_raw(_conn(c), "pergunta-visivel-aaa")
    assert r.status == 200 and r.getheader("X-Agata-Registro") is None
    assert "pergunta-visivel-aaa" in _gravado(pedidos)


def test_com_cabecalho_nada_e_gravado_e_o_gateway_confirma(gw, pedidos):
    c = gw()
    r = _post_raw(_conn(c), "pergunta-secreta-bbb", {"X-Agata-Nao-Registrar": "1"})
    assert r.status == 200 and r.getheader("X-Agata-Registro") == "nao"
    gravado = _gravado(pedidos)
    assert "pergunta-secreta-bbb" not in gravado and "fila ok" not in gravado and "local ok" not in gravado


def test_outro_valor_do_cabecalho_e_comportamento_de_hoje(gw, pedidos):
    c = gw()
    for i, v in enumerate(("0", "true", "2", "")):
        r = _post_raw(_conn(c), f"pergunta-ccc{i}", {"X-Agata-Nao-Registrar": v})
        assert r.getheader("X-Agata-Registro") is None
    assert all(f"pergunta-ccc{i}" in _gravado(pedidos) for i in range(4))


def test_so_loopback_pode_pedir_para_nao_registrar():
    class H:
        def __init__(self, ip, v="1"):
            self.client_address = (ip, 1)
            self.headers = {"X-Agata-Nao-Registrar": v}
    for ip in ("127.0.0.1", "::1"):
        assert g._pede_nao_registrar(H(ip)) is True
    for ip in ("10.0.0.5", "192.168.1.2", "8.8.8.8"):
        assert g._pede_nao_registrar(H(ip)) is False
    assert g._pede_nao_registrar(object()) is False


def test_keep_alive_get_e_post_seguinte_nao_herdam(gw, pedidos):
    c = gw()
    conn = _conn(c)
    r1 = _post_raw(conn, "primeira-ddd", {"X-Agata-Nao-Registrar": "1"})
    assert r1.getheader("X-Agata-Registro") == "nao"
    conn.request("GET", "/v1/models")                    # GET na mesma conexão, depois do POST
    r2 = conn.getresponse()
    corpo = r2.read()
    assert r2.status == 200 and b"seth-livre" in corpo and r2.getheader("X-Agata-Registro") is None
    r3 = _post_raw(conn, "terceira-eee")                 # POST sem o cabeçalho, mesma conexão
    assert r3.getheader("X-Agata-Registro") is None
    gravado = _gravado(pedidos)
    assert "terceira-eee" in gravado and "primeira-ddd" not in gravado
    conn2 = _conn(c)
    conn2.request("GET", "/v1/models")                   # GET frio
    assert conn2.getresponse().status == 200


def test_canal_de_voz_contra_o_gateway_real_nao_grava_e_recebe_a_confirmacao(gw, pedidos):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sentidos"))
    import canal_voz
    c = gw()
    resp = canal_voz.enviar_ao_modelo("fala-do-canal-fff", url=c.base + "/v1/chat/completions")
    assert resp
    assert "fala-do-canal-fff" not in _gravado(pedidos)


# --- rota de nuvem por tipo (19/11/2026): só faixa pública, ficha manda, painel só restringe, queda segura -----

def _ficha_nuvem(ficha):
    d = json.loads(ficha.read_text(encoding="utf-8"))
    for i, (modelo, tipos) in enumerate((("poolside/laguna-xs-2.1", []),  # como a ficha real: sem rota (sem ferramentas na faixa pública)
                                         ("nvidia/nemotron-3.5-super-vl-120b-a12b", ["conversa"]),
                                         ("nvidia/nemotron-3.5-bolt-e4b", ["codigo", "json"]))):
        d["rotas"].append({"id": f"nv{i}", "provedor": "nvidia", "modelo": modelo, "categoria": "gratuito",
                           "classes_permitidas": ["publico"], "tipos": tipos, "prioridade": 10,
                           "max_tokens_entrada": 6000, "treina_com_prompts": "nao_conferido", "cota": "-",
                           "compartilhada_com_seth": True, "cota_medida": False, "conferida_em": "x", "fonte": "t"})
    # a rota de nuvem do tipo "conversa" antiga (g) não conta: só as nv*
    d["rotas"] = [r for r in d["rotas"] if r["id"] != "nuvem"]
    ficha.write_text(json.dumps(d), encoding="utf-8")
    rl._CACHE_FICHA["mtime"] = None
    rl._CACHE_NUVEM["mtime"] = None


def test_escolher_nuvem_pelo_tipo(ficha):
    _ficha_nuvem(ficha)
    e = lambda t, p=None: rl.escolher_nuvem(p or _p(), t)  # noqa: E731
    assert rl.nome_nuvem(e("conversa")) == "nvidia/nvidia/nemotron-3.5-super-vl-120b-a12b"
    assert rl.nome_nuvem(e("codigo")) == "nvidia/nvidia/nemotron-3.5-bolt-e4b"
    assert rl.nome_nuvem(e("json")) == "nvidia/nvidia/nemotron-3.5-bolt-e4b"
    assert e("ferramenta") is None  # Laguna: catalogada, sem rota (a faixa pública não tem ferramentas)
    assert e("contexto") is None
    assert e("conversa", _p("a" * 30000)) is None  # acima do teto conservador


def test_escolher_nuvem_painel_so_tira_e_liga_desliga(ficha, tmp_path, monkeypatch):
    _ficha_nuvem(ficha)
    _dec(tmp_path, {"id": "nvidia/nvidia/nemotron-3.5-bolt-e4b", "acao": "standby"})
    assert rl.escolher_nuvem(_p(), "codigo") is None
    _dec(tmp_path, {"id": "nvidia/nvidia/nemotron-3.5-bolt-e4b", "acao": "standby"},
         {"id": "nvidia/nvidia/nemotron-3.5-bolt-e4b", "acao": "liberar"})
    assert rl.escolher_nuvem(_p(), "codigo")
    _dec(tmp_path, {"id": "nvidia/zzz-que-nao-esta-na-ficha", "acao": "liberar"})
    assert rl.escolher_nuvem(_p(), "contexto") is None  # liberar não acrescenta
    monkeypatch.setenv("SETH_ROTAS_NUVEM", "0")
    assert rl.escolher_nuvem(_p(), "codigo") is None
    monkeypatch.delenv("SETH_ROTAS_NUVEM")
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    assert rl.escolher_nuvem(_p(), "codigo") is None


def test_escolher_nuvem_nunca_com_segredo_ou_classe_pessoal(ficha, monkeypatch):
    _ficha_nuvem(ficha)
    chave = "sk-" + "proj-" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6"
    assert rl.escolher_nuvem(_p("use " + chave), "conversa") is None
    monkeypatch.setattr(rl, "tem_segredo", lambda p: True)
    assert rl.escolher_nuvem(_p(), "conversa") is None
    # nuvem com classe pessoal na ficha é ignorada pelo carregador
    d = json.loads(ficha.read_text(encoding="utf-8"))
    for r in d["rotas"]:
        if r["id"] == "nv1":
            r["classes_permitidas"] = ["publico", "pessoal"]
    ficha.write_text(json.dumps(d), encoding="utf-8")
    rl._CACHE_FICHA["mtime"] = None
    assert "nv1" not in {r["id"] for r in rl.carregar_rotas_nuvem(ficha)}


def test_gateway_publico_vai_a_nuvem_pelo_tipo_sem_ferramentas(gw, ficha):
    _ficha_nuvem(ficha)
    c = gw()
    assert c.post(publico=True) == (200, "nuvem ok")
    assert c.up.chamadas == ["nvidia/nvidia/nemotron-3.5-super-vl-120b-a12b"]
    c.post("```py\nx=1\n```", publico=True)
    assert c.up.chamadas[-1] == "nvidia/nvidia/nemotron-3.5-bolt-e4b"
    # pedido com ferramenta de escrita: a faixa pública retira as ferramentas ANTES de escolher o tipo; vira conversa
    c.post("anote isto no diário", publico=True,
           extra={"tools": [{"type": "function", "function": {"name": "diario_anotar"}}], "tool_choice": "auto"})
    assert c.up.chamadas[-1] == "nvidia/nvidia/nemotron-3.5-super-vl-120b-a12b"
    enviado = c.up.corpos[-1]
    assert "tools" not in enviado and "tool_choice" not in enviado and "functions" not in enviado


def test_gateway_alias_publico_tambem_vai_a_nuvem(gw, ficha):
    _ficha_nuvem(ficha)
    c = gw()
    c.post(modelo="seth-public")
    assert c.up.chamadas[0].startswith("nvidia/")


def test_gateway_nao_publico_nunca_vai_a_nuvem(gw, ficha):
    _ficha_nuvem(ficha)
    c = gw()
    c.post("a" * 30000)  # sem cabeçalho público: cascata de sempre (nem local, nem nuvem)
    assert not any(m.startswith("nvidia/") for m in c.up.chamadas)
    c.post(modelo="seth-pesado", publico=True)  # fila explícita não é tocada
    assert c.up.chamadas[-1] == "seth-pesado"


@pytest.mark.parametrize("modo", ["500", "vazio"])
def test_queda_segura_da_nuvem_volta_a_fila_de_sempre(gw, ficha, modo):
    _ficha_nuvem(ficha)
    c = gw()
    c.up.nuvem = modo
    status, texto = c.post(publico=True)
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas[0].startswith("nvidia/") and c.up.chamadas[1].startswith("seth-")


def test_nuvem_standby_ou_desligada_vai_direto_a_fila(gw, ficha, tmp_path, monkeypatch):
    _ficha_nuvem(ficha)
    c = gw()
    _dec(tmp_path, {"id": "nvidia/nvidia/nemotron-3.5-super-vl-120b-a12b", "acao": "standby"})
    c.post(publico=True)
    assert c.up.chamadas == ["seth-livre"] or c.up.chamadas[0].startswith("seth-")
    _dec(tmp_path, {"id": "x", "acao": "liberar"})
    monkeypatch.setenv("SETH_ROTAS_NUVEM", "0")
    c.post(publico=True)
    assert not any(m.startswith("nvidia/") for m in c.up.chamadas)


def test_nuvem_get_passa_intacto_na_mesma_conexao(gw, ficha):
    _ficha_nuvem(ficha)
    c = gw()
    c.post(publico=True)
    status, dados = c.get()
    assert status == 200 and dados["data"][0]["id"] == "seth-livre"
    assert c.up.gets == ["/v1/models"]


def test_nuvem_pelo_prazo_proprio(gw, ficha, monkeypatch):
    _ficha_nuvem(ficha)
    visto = []
    orig = g.urllib.request.urlopen
    monkeypatch.setattr(g.urllib.request, "urlopen", lambda req, timeout=None: (visto.append(timeout), orig(req, timeout=timeout))[1])
    c = gw()
    c.post(publico=True)
    assert visto and visto[0] == g._rota_nuvem_seg() == 30.0
    monkeypatch.setenv("SETH_ROTA_NUVEM_MS", "lixo")
    assert g._rota_nuvem_seg() == 30.0


def test_prazo_absoluto_da_nuvem_com_so_keepalives_cai_na_fila(gw, ficha, monkeypatch):
    """P1: keep-alives a cada 0,1 s não renovam o prazo; estourou o prazo total, a fila de sempre responde."""
    _ficha_nuvem(ficha)
    monkeypatch.setenv("SETH_ROTA_NUVEM_MS", "1000")
    c = gw()
    c.up.nuvem = "keepalive"
    t0 = time.monotonic()
    status, texto = c.post(publico=True)
    dt = time.monotonic() - t0
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas[0].startswith("nvidia/") and c.up.chamadas[1].startswith("seth-")
    assert len(c.up.chamadas) == 2          # sem resposta duplicada
    assert 0.9 <= dt < 5.0, dt              # ~1 s, nunca os 40 s do prazo padrão nem os 8 s dos keep-alives


def test_keepalive_real_post_nuvem_e_depois_get_na_mesma_conexao(gw, ficha):
    """P2: http.client, mesma conexão, mesmo socket, POST de sucesso na nuvem e depois GET."""
    _ficha_nuvem(ficha)
    c = gw()
    conn = _conn(c)
    conn.request("POST", "/v1/chat/completions", headers={"Content-Type": "application/json",
                                                          "X-Agata-Data-Classification": "public"},
                 body=json.dumps({"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}]}))
    r = conn.getresponse()
    corpo = r.read()
    assert r.status == 200 and b"nuvem ok" in corpo and not r.will_close
    assert c.up.chamadas[0].startswith("nvidia/")
    sock = conn.sock
    assert sock is not None
    conn.request("GET", "/v1/models")
    r2 = conn.getresponse()
    corpo2 = r2.read()
    assert conn.sock is sock                       # o mesmo socket: a conexão foi reaproveitada
    conn.close()
    assert r2.status == 200 and json.loads(corpo2)["data"][0]["id"] == "seth-livre"
    assert c.up.gets == ["/v1/models"] and len(c.up.chamadas) == 1


def test_segredo_com_cabecalho_publico_nunca_vai_a_nuvem_no_gateway(gw, ficha):
    """P3: pelo gateway real, com a régua de segredo real (não trocada), nem pelo nome seth-public."""
    _ficha_nuvem(ficha)
    c = gw()
    segredo = "sk" + "-" + "TESTEsintetico0123456789abcdefGHIJ"
    for modelo in ("seth-livre", "seth-public"):
        c.post(f"explique o que é um ponteiro; minha chave é {segredo}", modelo=modelo, publico=True)
    assert c.up.chamadas and not any(m.startswith("nvidia/") for m in c.up.chamadas)
    assert all(segredo not in json.dumps(b) for b in c.up.corpos if str(b.get("model", "")).startswith("nvidia/"))


def test_pedido_nao_publico_nunca_vai_a_nuvem_em_nenhum_tipo(gw, ficha):
    """P3: sem cabeçalho público, qualquer tipo (conversa, código, json, ferramenta) fica fora da nuvem."""
    _ficha_nuvem(ficha)
    c = gw()
    c.post("oi")
    c.post("```py\nx=1\n```")
    c.post("dê json", extra={"response_format": {"type": "json_object"}})
    c.post("use a ferramenta", extra={"tools": [{"type": "function", "function": {"name": "f"}}]})
    assert len(c.up.chamadas) >= 4 and not any(m.startswith("nvidia/") for m in c.up.chamadas)


def test_nuvem_cache_por_mtime(ficha):
    _ficha_nuvem(ficha)
    a = rl.carregar_rotas_nuvem(ficha)
    assert rl.carregar_rotas_nuvem(ficha) is a  # mesma lista: não releu o arquivo
    assert rl.carregar_rotas_nuvem(ficha.parent / "nao-existe.json") == []


def test_http_exception_do_upstream_na_nuvem_cai_na_fila(gw, ficha, monkeypatch):
    """r3 (4): resposta malformada (BadStatusLine/RemoteDisconnected) do upstream na nuvem = fila de sempre."""
    import http.client as hc
    _ficha_nuvem(ficha)
    c = gw()
    orig = g.urllib.request.urlopen
    vistos = []

    def falso(req, timeout=None):
        vistos.append(json.loads(req.data)["model"])
        if vistos[-1].startswith("nvidia/"):
            raise hc.BadStatusLine("lixo")
        return orig(req, timeout=timeout)
    monkeypatch.setattr(g.urllib.request, "urlopen", falso)
    status, texto = c.post(publico=True)
    assert status == 200 and "fila ok" in texto and vistos[-2:] == ["nvidia/nvidia/nemotron-3.5-super-vl-120b-a12b", "seth-livre"], vistos


def test_get_zera_o_prazo_da_nuvem(gw, ficha):
    """r3 (6): do_GET/do_HEAD não herdam o prazo de nuvem de um POST anterior (atributo do handler, keep-alive)."""
    _ficha_nuvem(ficha)
    c = gw()
    conn = _conn(c)
    _post_conn(conn, headers={"X-Agata-Data-Classification": "public"})
    assert c.up.chamadas[0].startswith("nvidia/")
    conn.request("GET", "/v1/models")
    conn.getresponse().read()
    conn.request("HEAD", "/v1/models")
    conn.getresponse().read()
    conn.close()
    import inspect
    for nome in ("do_GET", "do_HEAD"):
        assert "_prazo_nuvem = False" in inspect.getsource(getattr(g._Handler, nome))


@pytest.mark.parametrize("modo,teto", [("headers_lentos", 2.4), ("json_lento", 2.4)])
def test_prazo_absoluto_da_nuvem_headers_e_json_lentos(gw, ficha, monkeypatch, modo, teto):
    """P1 r2: o prazo conta desde antes do pedido (headers incluídos) e vale para JSON não-SSE lido devagar."""
    _ficha_nuvem(ficha)
    monkeypatch.setenv("SETH_ROTA_NUVEM_MS", "1000")
    c = gw()
    c.up.nuvem = modo
    t0 = time.monotonic()
    status, texto = c.post(publico=True)
    dt = time.monotonic() - t0
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas[0].startswith("nvidia/") and c.up.chamadas[-1].startswith("seth-")
    assert 0.9 <= dt < teto, dt   # ~1 s: nem os 2,5 s dos headers nem a leitura inteira do JSON (~3 s)


def test_json_pingo_e_silencio_responde_pela_fila_antes_do_prazo_mais_meio_segundo(gw, ficha, monkeypatch):
    """r3 (1): headers em t=0, um pedaço aos 2,5 s e silêncio; prazo 3 s -> a fila responde em < 3,5 s (o _derrubar
    libera a thread da leitura; close() esperaria o silêncio acabar)."""
    _ficha_nuvem(ficha)
    monkeypatch.setenv("SETH_ROTA_NUVEM_MS", "3000")
    c = gw()
    c.up.nuvem = "json_pingo"
    t0 = time.monotonic()
    status, texto = c.post(publico=True)
    dt = time.monotonic() - t0
    assert status == 200 and "fila ok" in texto and len(c.up.chamadas) == 2
    assert 2.9 <= dt < 3.5, dt


@pytest.mark.parametrize("modo", ["500", "vazio", "keepalive", "headers_lentos", "json_lento", "json_pingo"])
def test_keepalive_depois_de_queda_da_nuvem_post_fila_e_get_na_mesma_conexao(gw, ficha, monkeypatch, modo):
    """P2 r2: POST com falha na nuvem -> fila responde -> GET e novo POST não público na MESMA conexão, sem herança."""
    _ficha_nuvem(ficha)
    monkeypatch.setenv("SETH_ROTA_NUVEM_MS", "1000")
    c = gw()
    c.up.nuvem = modo
    conn = _conn(c)
    t0 = time.monotonic()
    conn.request("POST", "/v1/chat/completions", headers={"Content-Type": "application/json",
                                                          "X-Agata-Data-Classification": "public"},
                 body=json.dumps({"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}]}))
    r = conn.getresponse()
    corpo = r.read()
    assert time.monotonic() - t0 < 2.4  # prazo 1 s: nenhuma queda espera o upstream (2,5 s, ~3 s ou 8 s)
    assert r.status == 200 and b"fila ok" in corpo and not r.will_close
    assert c.up.chamadas[0].startswith("nvidia/") and c.up.chamadas[1].startswith("seth-")
    n = len(c.up.chamadas)
    sock = conn.sock
    conn.request("GET", "/v1/models")
    r2 = conn.getresponse()
    corpo2 = r2.read()
    assert conn.sock is sock and r2.status == 200 and json.loads(corpo2)["data"][0]["id"] == "seth-livre"
    assert c.up.gets == ["/v1/models"] and len(c.up.chamadas) == n   # o GET não reenviou nada
    status, txt = _post_conn(conn, pergunta="oi de novo")           # não público: fila, sem nuvem herdada
    conn.close()
    assert status == 200 and len(c.up.chamadas) == n + 1 and c.up.chamadas[-1].startswith(("seth-", "ollama-local/"))


# --- ferramentas de dado público valem também nas rotas de nuvem da faixa pública (19/11/2026, ferramentas-confianca) ---

def _def_pub(nome):
    return {"type": "function", "function": {"name": nome, "parameters": {}}}


def test_gateway_publico_com_ferramenta_publica_vai_a_nuvem_que_tem_o_tipo_ferramenta(gw, ficha):
    _ficha_nuvem(ficha)
    d = json.loads(ficha.read_text(encoding="utf-8"))
    for r in d["rotas"]:
        if r["id"] == "nv0":  # Laguna: a ficha assinada é quem dá o tipo "ferramenta"; aqui, só no teste
            r["tipos"] = ["ferramenta"]
    ficha.write_text(json.dumps(d), encoding="utf-8")
    rl._CACHE_FICHA["mtime"] = None
    rl._CACHE_NUVEM["mtime"] = None
    c = gw()
    c.post("pesquise na web", publico=True, extra={"tools": [_def_pub("buscar_web_mcp_navegador"),
                                                             _def_pub("vault_buscar_mcp_canon")]})
    assert c.up.chamadas[-1] == "nvidia/poolside/laguna-xs-2.1"
    assert [t["function"]["name"] for t in c.up.corpos[-1]["tools"]] == ["buscar_web_mcp_navegador"]  # só dado público


def test_gateway_publico_com_ferramenta_publica_sem_rota_de_nuvem_do_tipo_segue_a_fila_com_a_ferramenta(gw, ficha):
    _ficha_nuvem(ficha)  # como a ficha real: nenhuma rota de nuvem com o tipo "ferramenta"
    c = gw()
    c.post("pesquise na web", publico=True, extra={"tools": [_def_pub("buscar_web_mcp_navegador")]})
    assert not c.up.chamadas[-1].startswith("nvidia/")
    assert [t["function"]["name"] for t in c.up.corpos[-1]["tools"]] == ["buscar_web_mcp_navegador"]


def test_nome_de_modelo_de_nuvem_nvidia_e_de_nivel_gratuito():
    import ferramentas_confianca as fc
    assert fc.dado_maximo("nvidia/nvidia/nemotron-3.5-bolt-e4b", False) == "publico"
    assert fc.dado_maximo("nvidia/poolside/laguna-xs-2.1", True) == "publico"


# --- escolha por capacidade em produção e log de uso (23/11/2026) ---------------------------------------------------
# Decisão do Humano (23/11, 16:40): todos os modelos são escolhidos pelas capacidades; o Agata Code segue as mesmas
# regras. O registro aqui é temporário (o real muda com a Capivara). Cobre: concreto com nota e amostra; combo sem
# elas; pessoal só local; falha, vazio ou queda do concreto volta ao combo; flag 0; saída pelo sanitizador; log de uso
# sem texto com rota, rota_por e laya_confianca; tipo do Agata Code (ferramenta e código); sombra com "aplicada".

LOG_CAMPOS = {"ts", "modelo", "tipo", "classe", "status", "bloqueado", "latencia_ms", "rota", "rota_por",
              "laya_confianca", "achados", "refeito", "corrigido"}
FILA_CODIGO = {"seth-codigo": ["mistral/codestral-latest", "gemini/gemini-3-flash-preview"]}


def _med(metrica, valor, amostra=6):
    return {"metrica": metrica, "valor": valor, "amostra": amostra}


def _urlopen_que_falha_para(monkeypatch, marca, erro):
    real = urllib.request.urlopen

    def falso(req, *a, **k):
        if marca in (getattr(req, "data", None) or b""):
            raise erro
        return real(req, *a, **k)
    monkeypatch.setattr(g.urllib.request, "urlopen", falso)


def _ultima_linha_uso(tmp_path):
    return json.loads((tmp_path / "uso.jsonl").read_text(encoding="utf-8").splitlines()[-1])


@pytest.fixture
def capacidade(gw, tmp_path, monkeypatch):
    """Gateway com as rotas locais e de nuvem desligadas (o que se testa é a escolha por capacidade), e funções para
    pôr um registro temporário e um Laya de mentira. Devolve (registro, laya)."""
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    monkeypatch.delenv("SETH_ESCOLHA_CAPACIDADE", raising=False)

    def registro(filas, modelos):
        modelos = {m: dict(info, catalogo=info.get("catalogo") or {"janela": 128000}) for m, info in modelos.items()}
        p = tmp_path / "capacidades-teste.json"
        p.write_text(json.dumps({"filas": filas, "modelos": modelos}), encoding="utf-8")
        monkeypatch.setattr(g.sombra_capacidade, "_caminho_registro", lambda p=p: p)

    def laya(rota, choice=None, conf=None):
        dec = {} if choice is None else {"choice": choice, "confidence": conf}
        monkeypatch.setattr(g, "_rota_laya", lambda payload: (rota, dec))
    return registro, laya


def test_escolhe_o_concreto_com_nota_e_amostra_por_padrao(capacidade, gw):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]},
                           "gemini/gemini-3-flash-preview": {"medido": [_med("qualidade_codigo", 0.95, 4)]}})
    laya("seth-codigo", "codigo", 0.9)
    c = gw()
    status, texto = c.post("escreva uma função")
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas == ["mistral/codestral-latest"]  # o de amostra 4 não conta; o concreto venceu o combo


@pytest.mark.parametrize("modelos", [
    {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 5)]}},   # amostra 5 (mínimo é 6)
    {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.6, 20)]}},  # nota abaixo do piso 0,7
    {"mistral/codestral-latest": {"medido": []}},                                   # sem medida
    {},                                                                             # o modelo nem está no registro
])
def test_sem_nota_e_amostra_suficientes_vale_o_combo(capacidade, gw, modelos):
    registro, laya = capacidade
    registro(FILA_CODIGO, modelos)
    laya("seth-codigo", "codigo", 0.9)
    c = gw()
    c.post("escreva uma função")
    assert c.up.chamadas == ["seth-codigo"]


def test_dado_pessoal_so_vai_a_modelo_local(capacidade, gw):
    registro, laya = capacidade
    registro({"seth-codigo": ["mistral/codestral-latest", "ollama-local/qwen3.5-9b-64k:latest"]}, {
        "mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.95, 10)]},
        "ollama-local/qwen3.5-9b-64k:latest": {"medido": [_med("qualidade_codigo", 0.75, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    c = gw()
    c.post("escreva uma função e mande para ana@exemplo.com")
    assert c.up.chamadas == ["ollama-local/qwen3.5-9b-64k:latest"]  # o remoto, melhor, não recebe dado pessoal


def test_dado_pessoal_sem_modelo_local_qualificado_vai_ao_combo(capacidade, gw):
    registro, laya = capacidade
    registro({"seth-codigo": ["mistral/codestral-latest", "ollama-local/qwen3.5-9b-64k:latest"]}, {
        "mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.95, 10)]}})
    laya("seth-codigo", "codigo", 0.9)
    c = gw()
    c.post("escreva uma função e mande para ana@exemplo.com")
    # a escolha nova não manda dado pessoal a remoto; a queda segue a política de hoje (combo), como antes do lote
    assert c.up.chamadas == ["seth-codigo"]


@pytest.mark.parametrize("modo", ["500", "vazio"])
def test_falha_ou_resposta_vazia_do_concreto_volta_ao_combo(capacidade, gw, modo):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    c = gw()
    c.up.falhar["mistral/codestral-latest"] = modo
    status, texto = c.post("escreva uma função")
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas == ["mistral/codestral-latest", "seth-codigo"]  # o concreto falhou; a fila respondeu


@pytest.mark.parametrize("erro", [urllib.error.URLError("conexão recusada"), socket.timeout("timed out"),
                                  TimeoutError("timeout")])
def test_queda_de_conexao_do_concreto_volta_ao_combo(capacidade, gw, monkeypatch, erro):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    _urlopen_que_falha_para(monkeypatch, b"mistral/codestral-latest", erro)
    c = gw()
    status, texto = c.post("escreva uma função")
    assert status == 200 and "fila ok" in texto
    assert c.up.chamadas == ["seth-codigo"]  # o concreto nem chegou ao sanitizador; o combo respondeu


def test_flag_zero_volta_ao_comportamento_anterior(capacidade, gw, monkeypatch):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    monkeypatch.setenv("SETH_ESCOLHA_CAPACIDADE", "0")
    c = gw()
    c.post("escreva uma função")
    assert c.up.chamadas == ["seth-codigo"]


def test_concreto_remoto_sai_pelo_mesmo_sanitizador_do_combo(capacidade, gw):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    c = gw()
    c.post("escreva uma função")
    assert c.up.chamadas == ["mistral/codestral-latest"]
    cab = {k.lower(): v for k, v in c.up.cabecalhos[-1].items()}
    # o pedido chegou ao sanitizador (o servidor falso que o gateway usa como UPSTREAM), com o token interno e a
    # mesma classificação que o combo leva (sanitizado-cascata): é o mesmo caminho de saída
    assert g.UPSTREAM == f"http://127.0.0.1:{c.up.server_address[1]}"
    assert cab.get("x-agata-token") == TOKEN
    assert cab.get("x-agata-data-classification") == "sanitizado-cascata"


def test_concreto_na_faixa_publica_leva_classificacao_public(capacidade, gw):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    c = gw()
    c.post("escreva uma função", publico=True)
    assert c.up.chamadas == ["mistral/codestral-latest"]
    cab = {k.lower(): v for k, v in c.up.cabecalhos[-1].items()}
    assert cab.get("x-agata-data-classification") == "public"


def test_chamada_utilitaria_segue_o_combo(capacidade, gw, monkeypatch):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    monkeypatch.setattr(g, "_e_chamada_utilitaria", lambda payload: True)  # título do frontend: nunca escolha
    c = gw()
    c.post("escreva uma função")
    assert c.up.chamadas == ["seth-codigo"]


def test_agata_code_com_ferramenta_passa_pela_escolha(capacidade, gw, tmp_path):
    registro, laya = capacidade
    registro({"seth-livre": ["mistral/ministral-14b-latest", "gemini/gemini-2.5-flash"]}, {
        "mistral/ministral-14b-latest": {"medido": [_med("qualidade_ferramenta", 0.8, 6)]},
        "gemini/gemini-2.5-flash": {"medido": [_med("qualidade_ferramenta", 0.95, 3)]}})  # amostra 3 não conta
    laya("seth-livre", "livre", 0.9)
    c = gw()
    tools = [{"type": "function", "function": {"name": "ler_arquivo", "parameters": {}}}]
    c.post("leia o arquivo de notas", extra={"tools": tools})
    assert c.up.chamadas == ["mistral/ministral-14b-latest"]  # não fixado: a capacidade ferramenta escolheu
    assert _ultima_linha_uso(tmp_path)["tipo"] == "ferramenta"


def test_agata_code_com_codigo_passa_pela_escolha_e_o_tipo_e_codigo(capacidade, gw, tmp_path):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    c = gw()
    c.post("corrija este script python: x = 1 +")
    assert c.up.chamadas == ["mistral/codestral-latest"]
    assert _ultima_linha_uso(tmp_path)["tipo"] == "codigo"


def test_log_de_uso_sem_texto_com_os_campos(capacidade, gw, tmp_path):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    c = gw()
    marca = "PEDIDO-SEM-TEXTO-7731"
    c.post(f"escreva uma função {marca}")
    bruto = (tmp_path / "uso.jsonl").read_text(encoding="utf-8")
    assert marca not in bruto and "escreva" not in bruto and "fila ok" not in bruto  # nenhum texto do pedido ou da resposta
    linhas = [json.loads(x) for x in bruto.splitlines()]
    assert len(linhas) == 1 and set(linhas[0]) == LOG_CAMPOS
    linha = linhas[0]
    assert linha["modelo"] == "m-falso"  # o modelo servido de verdade (campo model da resposta)
    assert (linha["tipo"], linha["classe"], linha["status"], linha["bloqueado"]) == ("codigo", "publico", 200, False)
    assert isinstance(linha["latencia_ms"], int) and linha["latencia_ms"] >= 0
    assert (linha["rota"], linha["rota_por"], linha["laya_confianca"]) == ("codigo", "laya", 0.9)


@pytest.mark.parametrize("rota, dec, esperado", [
    ("seth-codigo", {"choice": "codigo", "confidence": 0.9}, ("codigo", "laya", 0.9)),
    ("seth-livre", {"choice": "livre", "confidence": 0.3}, ("livre", "regra", 0.3)),  # confiança abaixo do limiar
    ("seth-livre", {}, ("livre", "regra", None)),                                    # Laya fora ou lento
])
def test_log_traz_rota_rota_por_e_confianca_do_laya(gw, monkeypatch, tmp_path, rota, dec, esperado):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    monkeypatch.setattr(g, "_rota_laya", lambda payload: (rota, dec))
    monkeypatch.setattr(g.sombra_capacidade, "_caminho_registro", lambda p=tmp_path / "sem-registro.json": p)
    c = gw()
    c.post("oi")
    linha = _ultima_linha_uso(tmp_path)
    assert (linha["rota"], linha["rota_por"], linha["laya_confianca"]) == esperado


def test_rota_por_regra_quando_a_trava_troca_a_rota_do_laya():
    assert g._rota_laya_por("seth-pesado", {"choice": "livre", "confidence": 0.9}) == ("regra", 0.9)
    assert g._rota_laya_por("seth-livre", {"choice": "livre", "confidence": 0.9}) == ("laya", 0.9)
    assert g._rota_laya_por("seth-livre", {"choice": "livre", "confidence": True}) == ("regra", None)  # bool não é número


@pytest.mark.parametrize("payload, rota_laya, tipo", [
    ({"messages": [{"role": "user", "content": "oi"}]}, "codigo", "codigo"),
    ({"messages": [{"role": "user", "content": "oi"}], "tools": [{"type": "function"}]}, None, "ferramenta"),
    ({"messages": [{"role": "user", "content": "oi"}],
      "response_format": {"type": "json_object"}}, None, "json"),
    ({"messages": [{"role": "user", "content": "oi"}]}, "livre", "conversa"),
    ({"messages": [{"role": "user", "content": "oi " * 40000}]}, None, "contexto"),
])
def test_tipo_do_perfil_parte_da_rota_do_laya(payload, rota_laya, tipo):
    perfil = g._perfil_do_pedido(payload, payload["messages"], rota_laya)
    assert perfil["tipo"] == tipo and perfil["classe"] == "publico"


def test_segredo_nunca_escolhe_modelo(capacidade, monkeypatch):
    registro, _laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    monkeypatch.setattr(g.rotas_locais, "tem_segredo", lambda payload: True)
    msgs = [{"role": "user", "content": "oi"}]
    perfil = g._perfil_do_pedido({"messages": msgs}, msgs, "codigo")
    assert perfil["segredo"] and perfil["classe"] == "pessoal"
    assert g._escolha_capacidade(perfil, "seth-codigo") is None


def test_sombra_registra_aplicada_quando_a_escolha_foi_aplicada(capacidade, gw, monkeypatch, tmp_path):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    monkeypatch.setenv("SETH_SOMBRA_CAPACIDADE", "1")
    sombra = tmp_path / "roteador-capacidade.jsonl"
    monkeypatch.setattr(g.sombra_capacidade, "LOG", sombra)
    c = gw()
    c.post("escreva uma função")
    for _ in range(100):  # a sombra roda numa thread: espera a linha (até 5 s)
        if sombra.exists() and sombra.read_text(encoding="utf-8").strip():
            break
        time.sleep(0.05)
    linha = json.loads(sombra.read_text(encoding="utf-8").splitlines()[0])
    assert linha["aplicada"] is True and linha["escolhida"] == "mistral/codestral-latest"


def test_falha_ao_gravar_o_uso_nao_derruba_o_pedido(gw, monkeypatch, tmp_path):
    bloqueio = tmp_path / "arquivo"
    bloqueio.write_text("não é pasta", encoding="utf-8")
    monkeypatch.setenv("AGATA_CAPIVARA_USO", str(bloqueio / "uso.jsonl"))  # a "pasta" é um arquivo: não grava
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    c = gw()
    status, _texto = c.post()
    assert status == 200


def test_pasta_do_uso_e_criada_se_faltar(gw, monkeypatch, tmp_path):
    destino = tmp_path / "novo" / "sub" / "uso.jsonl"
    monkeypatch.setenv("AGATA_CAPIVARA_USO", str(destino))
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    c = gw()
    c.post()
    assert destino.exists() and len(destino.read_text(encoding="utf-8").splitlines()) == 1


def test_log_marca_bloqueado_quando_a_resposta_minima_sai(gw, monkeypatch, tmp_path):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    monkeypatch.setattr(g.bloqueio_turno, "achados", lambda texto, msgs, mod: [("X1", "achado de teste")])
    monkeypatch.setattr(g.bloqueio_turno, "resposta_minima", lambda ach: "resposta mínima de teste")
    c = gw()
    status, texto = c.post("oi")
    assert status == 200 and "resposta mínima de teste" in texto  # o cabeçalho da Máquina vem antes
    assert _ultima_linha_uso(tmp_path)["bloqueado"] is True


# --- registro de capacidades: estado da Capivara, com queda para o repositório (23/11/2026, coordenação) -----------

_CAMINHO_REGISTRO_ORIGINAL = g.sombra_capacidade._caminho_registro  # antes do fixture que o troca por um temporário


@pytest.fixture
def caminho_real(monkeypatch):
    """Restaura a resolução de verdade (o fixture de gateway a troca por um registro temporário)."""
    monkeypatch.setattr(g.sombra_capacidade, "_caminho_registro", _CAMINHO_REGISTRO_ORIGINAL)
    monkeypatch.setitem(g.sombra_capacidade._CACHE_CAMINHO, "valor", None)  # sem resultado lembrado de outro teste


def _capivara_falsa(monkeypatch, funcao=None):
    """Módulo capivara_capacidades falso em sys.modules: com a função caminho_registro (ou sem ela)."""
    import types
    mod = types.ModuleType("capivara_capacidades")
    if funcao is not None:
        mod.caminho_registro = funcao
    monkeypatch.setitem(sys.modules, "capivara_capacidades", mod)


def test_caminho_registro_usa_o_estado_da_capivara_quando_existe(monkeypatch, tmp_path, caminho_real):
    estado = tmp_path / "estado" / "capacidades.json"
    _capivara_falsa(monkeypatch, funcao=lambda: estado)
    assert g.sombra_capacidade._caminho_registro() == estado


def test_sem_caminho_registro_cai_no_repositorio(monkeypatch, caminho_real):
    _capivara_falsa(monkeypatch)  # o módulo existe, mas ainda sem a função
    assert g.sombra_capacidade._caminho_registro() == g.sombra_capacidade.REGISTRO


def test_caminho_registro_quebrado_cai_no_repositorio(monkeypatch, caminho_real):
    def _quebra():
        raise OSError("estado ilegível")
    _capivara_falsa(monkeypatch, funcao=_quebra)
    assert g.sombra_capacidade._caminho_registro() == g.sombra_capacidade.REGISTRO


def test_modulo_da_capivara_ausente_cai_no_repositorio(monkeypatch, caminho_real):
    monkeypatch.setitem(sys.modules, "capivara_capacidades", None)  # o import falha
    assert g.sombra_capacidade._caminho_registro() == g.sombra_capacidade.REGISTRO


def test_carregar_registro_le_do_caminho_da_capivara(monkeypatch, tmp_path, caminho_real):
    estado = tmp_path / "capacidades.json"
    estado.write_text(json.dumps({"filas": {"seth-codigo": ["x/y"]}, "modelos": {}}), encoding="utf-8")
    _capivara_falsa(monkeypatch, funcao=lambda: estado)
    assert g.sombra_capacidade.carregar_registro()["filas"] == {"seth-codigo": ["x/y"]}


def test_janela_declarada_e_escalar():
    sc = g.sombra_capacidade
    assert sc._janela({"declarado": {"janela": 8000}}, None) == 8000
    assert sc._janela({"catalogo": {"janela": 128000}, "declarado": {"janela": 8000}}, 4000) == 128000
    assert sc._janela({"declarado": [1, 2]}, 4000) == 4000                 # não é objeto: vale o perfil
    assert sc._janela({"declarado": {"janela": "grande"}}, 4000) == 4000   # não é número: não conta
    assert sc._janela({"declarado": {"janela": True}}, None) is None       # bool não é janela


# --- perfis de janela do gateway: a Capivara viva (caminho_perfil, sem argumento) (23/11/2026, coordenação) ---------

def test_perfis_do_gateway_usam_o_caminho_da_capivara_sem_argumento(monkeypatch, tmp_path):
    perfil = tmp_path / "perfis-viva.json"
    perfil.write_text(json.dumps({"modelos": {"m/x": {"janela": 777}}, "filas": {}}), encoding="utf-8")
    monkeypatch.setattr(g.capivara_perfis, "caminho_perfil", lambda *a, **k: perfil)
    monkeypatch.setitem(g._PERFIS, "quando", 0.0)
    monkeypatch.setitem(g._PERFIS, "caminho", None)
    assert g._perfis()["modelos"]["m/x"]["janela"] == 777
    assert g._janelas_perfis()["m/x"] == 777


def test_perfis_com_estado_da_capivara_em_pasta_temporaria(tmp_path):
    """Num subprocesso, com AGATA_CAPIVARA_ESTADO apontando para uma pasta temporária (a constante da Capivara é lida
    na importação). Sem estado: o retrato do repositório. Com estado em dia com o registro em uso: o estado."""
    estado = tmp_path / "estado"
    estado.mkdir()
    env = dict(os.environ, AGATA_CAPIVARA_ESTADO=str(estado), AGATA_CAPIVARA_USO=str(tmp_path / "uso.jsonl"))
    codigo = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "import seth_gateway as g\n"
        "import capivara_perfis as cp\n"
        "import capivara_capacidades as cap\n"
        "out = {'estado': str(cap.ESTADO_PERFIL), 'retrato': str(cp.PERFIS)}\n"
        "out['sem_estado'] = str(cp.caminho_perfil())\n"
        "reg = cap.carregar()\n"
        "out['tem_registro'] = bool(reg.get('modelos'))\n"
        "Path(cap.ESTADO_PERFIL).write_text(json.dumps(cp.derivar(reg)), encoding='utf-8')\n"
        "out['com_estado'] = str(cp.caminho_perfil())\n"
        "g._PERFIS['quando'] = 0.0\n"
        "g._PERFIS['caminho'] = None\n"
        "out['perfis_tem_modelos'] = bool(g._perfis().get('modelos'))\n"
        "print(json.dumps(out))\n"
    )
    r = subprocess.run([sys.executable, "-c", codigo, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "router")],
                       env=env, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-800:]
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["tem_registro"], "o registro em uso precisa ter modelos para o teste de estado em dia"
    assert out["estado"].startswith(str(estado))  # a variável apontou para a pasta temporária
    assert out["sem_estado"] == out["retrato"]    # sem estado, cai no retrato do repositório
    assert out["com_estado"] == out["estado"]     # com estado em dia, o gateway usa o estado da Capivara
    assert out["perfis_tem_modelos"]


# --- revisão independente (23/11/2026): comentários, privado no pedido inteiro, latência em stream, uso degradado,
# falhas no log, cache, e refazer ligado por padrão com achados no uso (Humano, 18:18) ---------------------------------

def _linhas_uso(tmp_path):
    return [json.loads(x) for x in (tmp_path / "uso.jsonl").read_text(encoding="utf-8").splitlines()]


class _RespostaTravada:
    """Resposta de upstream que não entrega nada: a leitura estoura (queda no meio do corpo)."""
    status = 200
    headers = {"Content-Type": "application/json"}

    def read(self, *a):
        raise TimeoutError("lido devagar")

    read1 = read

    def close(self):
        pass


def _upstream_com(monkeypatch, comportamento, marca=None):
    """Troca o urlopen só para o upstream (o sanitizador falso). `comportamento(req)` devolve uma resposta ou levanta."""
    real = urllib.request.urlopen

    def falso(req, *a, **k):
        url = str(getattr(req, "full_url", ""))
        if url.startswith(g.UPSTREAM) and (marca is None or marca in (getattr(req, "data", None) or b"")):
            return comportamento(req)
        return real(req, *a, **k)
    monkeypatch.setattr(g.urllib.request, "urlopen", falso)


# (2) comentários: o proxy não varre dado pessoal desde a decisão relaxa-pessoal (22/10)
def test_comentarios_nao_dizem_que_o_proxy_varre_dado_pessoal():
    aqui = os.path.dirname(os.path.abspath(g.__file__))
    proxy = open(os.path.join(aqui, "proxy.py"), encoding="utf-8").read()
    gw = open(os.path.join(aqui, "seth_gateway.py"), encoding="utf-8").read()
    sombra = open(os.path.join(aqui, "sombra_capacidade.py"), encoding="utf-8").read()
    for texto in (proxy, gw, sombra):
        assert "(segredo, dados pessoais, nomes de projeto)" not in texto
        assert "segredo + dados pessoais + nomes de projeto" not in texto
        assert "seth-livre sanitiza segredo, dado pessoal" not in texto
    assert "NÃO são varridos" in proxy
    assert "não são varridos desde a decisão relaxa-pessoal" in gw
    assert "O proxy NÃO varre dado pessoal" in sombra


# (3) dado pessoal em qualquer parte do pedido: turno anterior, tool_calls (string e objeto), papel tool e nome
@pytest.mark.parametrize("msgs, esperado", [
    ([{"role": "user", "content": "oi"},
      {"role": "assistant", "content": "o contato é ana@exemplo.com"},
      {"role": "user", "content": "obrigado"}], True),                                      # turno anterior
    ([{"role": "user", "content": "envie"},
      {"role": "assistant", "content": None, "tool_calls": [{"id": "1", "type": "function", "function": {
          "name": "enviar", "arguments": "{\"para\": \"ana@exemplo.com\"}"}}]}], True),        # argumentos em texto
    ([{"role": "user", "content": "envie"},
      {"role": "assistant", "content": None, "tool_calls": [{"id": "1", "type": "function", "function": {
          "name": "enviar", "arguments": {"para": "ana@exemplo.com"}}}]}], True),             # argumentos em objeto
    ([{"role": "user", "content": "leia"},
      {"role": "tool", "tool_call_id": "1", "content": "contato: ana@exemplo.com"}], True),     # papel tool
    ([{"role": "user", "content": "x"}, {"role": "assistant", "content": "ok", "name": "ana@exemplo.com"}], True),
    ([{"role": "user", "content": "bom dia equipe"},
      {"role": "assistant", "content": None, "tool_calls": [{"id": "1", "type": "function", "function": {
          "name": "somar", "arguments": "{\"a\": 1}"}}]}], False),                               # sem dado pessoal
])
def test_dado_pessoal_em_qualquer_parte_do_pedido(msgs, esperado):
    assert g.sombra_capacidade.privado_no_historico(msgs) is esperado


# (4) latência: em stream, o p95 do tipo tem de caber no prazo do primeiro conteúdo
def _janela_ok(modelos):
    return {m: dict(info, catalogo=info.get("catalogo") or {"janela": 128000}) for m, info in modelos.items()}


def _reg_latencia(p95_qwen=168, com_p95_qwen=True):
    qwen = [_med("qualidade_ferramenta", 0.95, 10)] + ([_med("latencia_p95_s", p95_qwen, 10)] if com_p95_qwen else [])
    return {"filas": {"seth-livre": ["ollama-local/qwen3-30b-a3b-64k:latest", "mistral/ministral-14b-latest"]},
            "modelos": _janela_ok({"ollama-local/qwen3-30b-a3b-64k:latest": {"medido": qwen},
                                   "mistral/ministral-14b-latest": {"medido": [_med("qualidade_ferramenta", 0.8, 6),
                                                                               _med("latencia_p95_s", 5, 6)]}})}


REQ_FERR = {"tipo": "ferramenta", "tokens_est": 100, "privado": False, "ferramentas": True, "codigo": False, "json": False}


def test_stream_nao_escolhe_modelo_com_p95_acima_do_prazo():
    r = g.sombra_capacidade.escolher(dict(REQ_FERR, stream=True), "seth-livre", _reg_latencia(), {}, prazo_stream_s=40.0)
    assert r["modelo"] == "mistral/ministral-14b-latest"  # qwen3 tem nota maior, mas p95 de 168 s não cabe no stream


def test_sem_stream_o_p95_nao_pesa():
    r = g.sombra_capacidade.escolher(dict(REQ_FERR), "seth-livre", _reg_latencia(), {}, prazo_stream_s=40.0)
    assert r["modelo"] == "ollama-local/qwen3-30b-a3b-64k:latest"


def test_stream_sem_p95_conhecido_nao_filtra_por_latencia():
    r = g.sombra_capacidade.escolher(dict(REQ_FERR, stream=True), "seth-livre",
                                     _reg_latencia(com_p95_qwen=False), {}, prazo_stream_s=40.0)
    assert r["modelo"] == "ollama-local/qwen3-30b-a3b-64k:latest"  # sem p95, só a amostra mínima vale


def test_gateway_stream_com_ferramenta_nao_vai_ao_modelo_lento(capacidade, gw):
    registro, laya = capacidade
    registro({"seth-livre": ["ollama-local/qwen3-30b-a3b-64k:latest", "mistral/ministral-14b-latest"]}, {
        "ollama-local/qwen3-30b-a3b-64k:latest": {"medido": [_med("qualidade_ferramenta", 0.95, 10),
                                                             _med("latencia_p95_s", 168, 10)]},
        "mistral/ministral-14b-latest": {"medido": [_med("qualidade_ferramenta", 0.8, 6),
                                                    _med("latencia_p95_s", 5, 6)]}})
    laya("seth-livre", "livre", 0.9)
    c = gw()
    tools = [{"type": "function", "function": {"name": "ler_arquivo", "parameters": {}}}]
    c.post("leia o arquivo de notas", extra={"tools": tools, "stream": True})
    assert c.up.chamadas == ["mistral/ministral-14b-latest"]


# (5) uso real: taxa_ok baixa ou taxa_achado alta, com amostra >= 20 para o tipo, tiram o modelo da escolha
def _reg_uso(observado_a):
    return {"filas": {"seth-livre": ["x/a", "x/b"]},
            "modelos": _janela_ok({"x/a": {"medido": [_med("qualidade_ferramenta", 0.95, 10)], "observado": observado_a},
                                   "x/b": {"medido": [_med("qualidade_ferramenta", 0.8, 6)]}})}


def _obs(metrica, valor, amostra, tipo="ferramenta"):
    return {"metrica": metrica, "tipo": tipo, "valor": valor, "amostra": amostra}


@pytest.mark.parametrize("observado_a, escolhido", [
    ([_obs("taxa_ok", 0.6, 25)], "x/b"),                 # uso degradado (0,6 < 0,8, amostra 25)
    ([_obs("taxa_ok", 0.0, 25)], "x/b"),                 # taxa zero também tira
    ([_obs("taxa_ok", 0.6, 19)], "x/a"),                 # amostra 19: ainda não conta
    ([_obs("taxa_ok", 0.9, 25)], "x/a"),                 # uso bom: fica
    ([_obs("taxa_achado", 0.35, 25)], "x/b"),            # muitos achados da verificação (0,35 >= 0,3)
    ([_obs("taxa_achado", 0.2, 25)], "x/a"),             # poucos achados: fica
    ([_obs("taxa_achado", 0.35, 19)], "x/a"),            # amostra 19: não conta
    ([_obs("taxa_ok", 0.6, 25, tipo="conversa")], "x/a"),  # medida de OUTRO tipo não vale para ferramenta
])
def test_uso_real_degradado_fica_fora_da_escolha(observado_a, escolhido):
    r = g.sombra_capacidade.escolher(dict(REQ_FERR), "seth-livre", _reg_uso(observado_a), {})
    assert r["modelo"] == escolhido


# (6) log de uso registra falhas: a tentativa que cai entra com o status do erro (0 = sem resposta útil)
def test_falha_do_concreto_entra_no_uso_antes_do_combo(capacidade, gw, tmp_path):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    c = gw()
    c.up.falhar["mistral/codestral-latest"] = "500"
    status, texto = c.post("escreva uma função")
    assert status == 200 and "fila ok" in texto
    linhas = _linhas_uso(tmp_path)
    assert [(x["modelo"], x["status"]) for x in linhas] == [("mistral/codestral-latest", 500), ("m-falso", 200)]
    assert linhas[0]["achados"] == [] and linhas[0]["corrigido"] is None  # tentativa que não entregou nada


@pytest.mark.parametrize("erro", [urllib.error.URLError("conexão recusada"), socket.timeout("timed out")])
def test_queda_do_concreto_entra_no_uso_com_status_zero(capacidade, gw, monkeypatch, tmp_path, erro):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    _urlopen_que_falha_para(monkeypatch, b"mistral/codestral-latest", erro)
    c = gw()
    c.post("escreva uma função")
    assert [(x["modelo"], x["status"]) for x in _linhas_uso(tmp_path)] == [("mistral/codestral-latest", 0), ("m-falso", 200)]


def test_resposta_vazia_do_concreto_entra_no_uso_com_status_zero(capacidade, gw, tmp_path):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    c = gw()
    c.up.falhar["mistral/codestral-latest"] = "vazio"
    c.post("escreva uma função")
    assert [(x["modelo"], x["status"]) for x in _linhas_uso(tmp_path)] == [("mistral/codestral-latest", 0), ("m-falso", 200)]


def test_leitura_travada_do_concreto_entra_no_uso_com_status_zero(capacidade, gw, monkeypatch, tmp_path):
    registro, laya = capacidade
    registro(FILA_CODIGO, {"mistral/codestral-latest": {"medido": [_med("qualidade_codigo", 0.9, 6)]}})
    laya("seth-codigo", "codigo", 0.9)
    _upstream_com(monkeypatch, lambda req: _RespostaTravada(), marca=b"mistral/codestral-latest")
    c = gw()
    status, texto = c.post("escreva uma função")
    assert status == 200 and "fila ok" in texto
    assert [(x["modelo"], x["status"]) for x in _linhas_uso(tmp_path)] == [("mistral/codestral-latest", 0), ("m-falso", 200)]


def test_erro_final_502_entra_no_uso(gw, monkeypatch, tmp_path):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")

    def fora(req):
        raise urllib.error.URLError("sanitizador fora")
    _upstream_com(monkeypatch, fora)
    c = gw()
    with pytest.raises(urllib.error.HTTPError) as erro:
        c.post()
    assert erro.value.code == 502
    assert [(x["modelo"], x["status"]) for x in _linhas_uso(tmp_path)] == [("seth-livre", 502)]


def test_erro_final_504_entra_no_uso(gw, monkeypatch, tmp_path):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    _upstream_com(monkeypatch, lambda req: _RespostaTravada())
    c = gw()
    with pytest.raises(urllib.error.HTTPError) as erro:
        c.post()
    assert erro.value.code == 504
    assert [(x["modelo"], x["status"]) for x in _linhas_uso(tmp_path)] == [("seth-livre", 504)]


# (8) cache: a segunda leitura dentro da validade não refaz a conferência do perfil nem do registro
def test_perfis_nao_refaz_a_conferencia_dentro_da_validade(monkeypatch, tmp_path):
    perfil = tmp_path / "perfis.json"
    perfil.write_text(json.dumps({"modelos": {}}), encoding="utf-8")
    contagem = {"n": 0}

    def conta(*a, **k):
        contagem["n"] += 1
        return perfil
    monkeypatch.setattr(g.capivara_perfis, "caminho_perfil", conta)
    monkeypatch.setitem(g._PERFIS, "quando", 0.0)
    monkeypatch.setitem(g._PERFIS, "caminho", None)
    g._perfis()
    depois_da_primeira = contagem["n"]
    g._perfis()
    g._perfis()
    assert depois_da_primeira >= 1 and contagem["n"] == depois_da_primeira


def test_registro_nao_refaz_a_conferencia_na_segunda_leitura(monkeypatch, tmp_path, caminho_real):
    estado = tmp_path / "capacidades.json"
    estado.write_text(json.dumps({"filas": {}, "modelos": {}}), encoding="utf-8")
    contagem = {"n": 0}

    def caminho():
        contagem["n"] += 1
        return estado
    _capivara_falsa(monkeypatch, funcao=caminho)
    monkeypatch.setitem(g.sombra_capacidade._CACHE_CAMINHO, "valor", None)
    a = g.sombra_capacidade.carregar_registro()
    b = g.sombra_capacidade.carregar_registro()
    assert contagem["n"] == 1 and a is b


# (B) achados no uso: códigos fixos, refações e corrigido; sem texto
def test_codigos_dos_achados_sao_rotulos_sem_texto():
    achados = ["evidência: cita 'ana@exemplo.com' como fonte, mas nenhuma chamada", "estilo: 'trecho da resposta'",
               "frase nova qualquer com trecho secreto"]
    assert g._codigos_achados(achados) == ["citacao_inventada", "estilo", "outro"]
    assert "ana@exemplo.com" not in " ".join(g._codigos_achados(achados))


def test_uso_traz_codigos_refacoes_e_corrigido(gw, monkeypatch, tmp_path):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    chamadas = {"n": 0}

    def achados(texto, msgs):
        chamadas["n"] += 1
        return ["evidência: cita 'ana@exemplo.com' como fonte, mas nenhuma chamada"] if chamadas["n"] == 1 else []
    monkeypatch.setattr(g, "_achados_do_texto", achados)
    c = gw()
    c.post("oi")
    linha = _ultima_linha_uso(tmp_path)
    assert linha["achados"] == ["citacao_inventada"]
    assert linha["refeito"] == 1 and linha["corrigido"] is True
    assert "ana@exemplo.com" not in (tmp_path / "uso.jsonl").read_text(encoding="utf-8")


def test_uso_sem_achado_marca_verificada_e_corrigido(gw, monkeypatch, tmp_path):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    c = gw()
    c.post("oi")
    linha = _ultima_linha_uso(tmp_path)
    assert (linha["achados"], linha["refeito"], linha["corrigido"]) == ([], 0, True)


def test_uso_com_achado_que_persiste_marca_nao_corrigido(gw, monkeypatch, tmp_path):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    monkeypatch.setattr(g, "_achados_do_texto", lambda texto, msgs: ["estilo: x"])
    c = gw()
    c.post("oi")
    linha = _ultima_linha_uso(tmp_path)
    assert linha["achados"] == ["estilo"] and linha["refeito"] == 2 and linha["corrigido"] is False


# (A) refazer ligado por padrão; SETH_REFAZER=0 desliga; canário capacidade:N vale quando definido
def test_refazer_ligado_por_padrao(monkeypatch):
    monkeypatch.delenv("SETH_REFAZER", raising=False)
    monkeypatch.delenv("SETH_ROTEADOR", raising=False)
    assert g._refazer_ligado_neste_pedido() is True


def test_refazer_zero_desliga_e_canario_vale_quando_definido(monkeypatch):
    monkeypatch.setenv("SETH_REFAZER", "0")
    assert g._refazer_ligado_neste_pedido() is False
    monkeypatch.delenv("SETH_REFAZER")
    monkeypatch.setenv("SETH_ROTEADOR", "capacidade:0")
    assert g._refazer_ligado_neste_pedido() is False
    monkeypatch.setenv("SETH_ROTEADOR", "capacidade:100")
    assert g._refazer_ligado_neste_pedido() is True
    monkeypatch.setenv("SETH_ROTEADOR", "capacidade:xyz")  # N inválido: sem canário, vale o padrão ligado
    assert g._refazer_ligado_neste_pedido() is True


# --- progresso visível no SSE durante a conferência (Regra 0, 23/11/2026) ----------------------------------------------

def _sse_pedido(base, pergunta="oi"):
    corpo = json.dumps({"model": "seth-livre", "messages": [{"role": "user", "content": pergunta}],
                        "stream": True}).encode("utf-8")
    r = urllib.request.Request(base + "/v1/chat/completions", data=corpo, method="POST",
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=60) as x:
        return x.read().decode("utf-8")


def _texto_sse(bruto):
    partes = []
    for linha in bruto.splitlines():
        if linha.startswith("data:") and not linha.startswith("data: [DONE]"):
            for ch in json.loads(linha[5:]).get("choices") or []:
                partes.append(((ch.get("delta") or {}).get("content")) or "")
    return "".join(partes)


def test_sse_com_conferencia_mostra_progresso_e_o_texto_final_nao_muda(gw, monkeypatch):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    monkeypatch.setattr(g, "_PROGRESSO_S", 0.1)
    c = gw()
    c.up.sse_lento = 0.5  # upstream lento: a coleta da 1ª resposta leva ~1 s
    bruto = _sse_pedido(c.base)
    comentarios = [x for x in bruto.splitlines() if x.startswith(": agata")]
    assert len(comentarios) >= 2, bruto[:400]
    assert "coletando" in comentarios[0] and "tentativa 1/3" in comentarios[0] and comentarios[0].endswith("s")
    texto = _texto_sse(bruto)
    assert "olá mundo" in texto
    monkeypatch.setattr(g, "_PROGRESSO_S", 999.0)  # mesmo pedido sem progresso: o texto entregue é o mesmo
    c2 = gw()
    c2.up.sse_lento = 0.5
    bruto2 = _sse_pedido(c2.base)
    # sem progresso não há comentário de etapa ("tentativa"); o comentário de modelo ": agata modelo ..." continua
    assert not [x for x in bruto2.splitlines() if x.startswith(": agata") and "tentativa" in x]
    assert _texto_sse(bruto2) == texto


def test_linha_de_progresso_mostra_a_etapa_real_e_os_segundos():
    import types
    ns = types.SimpleNamespace(_progresso={"etapa": "conferindo", "tentativa": 1, "total": 3})
    assert g._Handler._linha_progresso(ns, time.monotonic() - 23.4) == ": agata conferindo · tentativa 1/3 · 23s"
    ns._progresso = {"etapa": "refazendo", "tentativa": 2, "total": 3}
    assert g._Handler._linha_progresso(ns, time.monotonic()) == ": agata refazendo · tentativa 2/3 · 0s"


# --- modelo servido em comentário SSE, antes do conteúdo (23/11/2026, painel) ----------------------------------------

def test_modelo_servido_vai_em_comentario_antes_do_conteudo(gw, monkeypatch):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    c = gw()
    c.up.sse_lento = 0.01  # modo SSE do servidor falso (0 desliga o modo)
    bruto = _sse_pedido(c.base)
    linhas = bruto.splitlines()
    assert ": agata modelo m-lento" in linhas
    primeiro_dado = next(i for i, x in enumerate(linhas) if x.startswith("data:"))
    assert linhas.index(": agata modelo m-lento") < primeiro_dado
    assert "olá mundo" in _texto_sse(bruto)


# --- revisão final (23/11/2026): fila sem candidato, pessoal e janela na escolha; exceção; teto; códigos; rota ----------

def _escolha(req, filas, modelos):
    return g.sombra_capacidade.escolher(req, "seth-codigo", {"filas": filas, "modelos": modelos}, {})


def test_fila_so_nuvem_com_dado_pessoal_nao_escolhe():
    modelos = {"x/nuvem": {"catalogo": {"janela": 128000}, "medido": [_med("qualidade_codigo", 0.95, 10)]}}
    assert _escolha(dict(REQ_FERR, tipo="codigo", privado=True), {"seth-codigo": ["x/nuvem"]}, modelos) is None


def test_nuvem_com_janela_e_local_sem_janela_nao_escolhe():
    modelos = {"x/nuvem": {"catalogo": {"janela": 128000}, "medido": [_med("qualidade_codigo", 0.8, 10)]},
               "ollama-local/loc": {"medido": [_med("qualidade_codigo", 0.95, 10)]}}  # o melhor, sem janela informada
    assert _escolha(dict(REQ_FERR, tipo="codigo"), {"seth-codigo": ["x/nuvem", "ollama-local/loc"]}, modelos) is None


def test_nenhum_candidato_passa_nos_filtros_nao_escolhe():
    modelos = {"x/a": {"catalogo": {"janela": 1000}, "medido": [_med("qualidade_codigo", 0.9, 10)]}}
    assert _escolha(dict(REQ_FERR, tipo="codigo", tokens_est=500000), {"seth-codigo": ["x/a"]}, modelos) is None


def test_excecao_na_conferencia_depois_dos_cabecalhos_fecha_o_stream(gw, monkeypatch, capsys):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")

    def boom(self, *a, **k):
        raise RuntimeError("falha injetada")
    monkeypatch.setattr(g._Handler, "_refazer_antes_de_entregar", boom)
    c = gw()
    c.up.sse_lento = 0.01
    bruto = _sse_pedido(c.base)  # se o stream tivesse ficado truncado, a leitura chcaria com erro de corpo incompleto
    assert '"error"' in bruto and "[DONE]" in bruto
    assert "falha injetada" not in bruto  # a mensagem ao cliente é genérica
    assert "conferência falhou depois dos cabeçalhos" in capsys.readouterr().err


def test_pedido_teto_padrao_e_env(monkeypatch):
    monkeypatch.delenv("SETH_PEDIDO_TETO_SEG", raising=False)
    assert g._pedido_teto_seg() == 600.0
    monkeypatch.setenv("SETH_PEDIDO_TETO_SEG", "45")
    assert g._pedido_teto_seg() == 45.0
    monkeypatch.setenv("SETH_PEDIDO_TETO_SEG", "x")
    assert g._pedido_teto_seg() == 600.0


def test_teto_do_pedido_nao_pede_nova_tentativa_e_entrega_a_primeira(gw, monkeypatch):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    monkeypatch.setattr(g, "_pedido_teto_seg", lambda: 0.0)  # o teto já estourou quando a conferência começa
    monkeypatch.setattr(g, "_achados_do_texto", lambda texto, msgs: ["estilo: x"])
    c = gw()
    status, texto = c.post("oi")
    assert status == 200 and "fila ok" in texto
    assert len(c.up.chamadas) == 1  # nenhuma nova tentativa depois do teto


def test_codigos_do_bloqueio_usam_o_vocabulario_comum():
    assert g._codigos_achados([("a", "x"), ("b", "y"), ("c", "z"), ("q", "w")]) == [
        "escrita_sem_ferramenta", "saida_simulada", "cabecalho_divergente", "outro"]


def test_uso_traz_o_codigo_do_bloqueio_sem_a_descricao(gw, monkeypatch, tmp_path):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    n = {"k": 0}

    def achados(texto, msgs, mod=None):
        n["k"] += 1
        return [("a", "afirma escrita 'ana@exemplo.com'")] if n["k"] == 1 else []
    monkeypatch.setattr(g.bloqueio_turno, "achados", achados)
    c = gw()
    c.post("oi")
    assert _ultima_linha_uso(tmp_path)["achados"] == ["escrita_sem_ferramenta"]
    assert "ana@exemplo.com" not in (tmp_path / "uso.jsonl").read_text(encoding="utf-8")


def test_troca_de_rota_depois_do_cabecalho_vira_comentario(gw, monkeypatch):
    monkeypatch.setenv("SETH_ROTAS_LOCAIS", "0")
    n = {"k": 0}

    def achados(texto, msgs):
        n["k"] += 1
        return ["estilo: x"] if n["k"] == 1 else []  # a 1ª resposta tem achado: o refazer sobe a fila
    monkeypatch.setattr(g, "_achados_do_texto", achados)
    c = gw()
    c.up.sse_lento = 0.01
    corpo = json.dumps({"model": "seth-livre", "messages": [{"role": "user", "content": "oi"}],
                        "stream": True}).encode("utf-8")
    r = urllib.request.Request(c.base + "/v1/chat/completions", data=corpo, method="POST",
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=60) as x:
        cabecalho = x.headers.get("X-Seth-Rota")
        bruto = x.read().decode("utf-8")
    assert cabecalho == "seth-livre"  # o cabeçalho saiu antes da troca
    assert ": agata rota seth-pesado" in bruto.splitlines()  # a troca vai no stream, antes do conteúdo

