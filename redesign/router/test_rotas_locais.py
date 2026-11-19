"""Testes das rotas locais por tipo (18/11/2026): rotas_locais.py e o gancho no seth_gateway. Sem rede e sem provedor.

Cobre: tipo do pedido; escolha pela ficha (tipo certo, classe, teto de entrada, prioridade); painel que SÓ
RESTRINGE (standby tira, liberado não acrescenta, arquivo ausente ou ilegível = sem efeito); Ollama fora = regra
de sempre; chave SETH_ROTAS_LOCAIS=0; a ficha real passa na validação; e o gateway de verdade, POST e GET:
rota local usada, queda segura (HTTP 500, resposta vazia, Ollama fora, standby) e GET intacto.
Rodar: pytest -q redesign/router/test_rotas_locais.py
"""
import json
import os
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rotas"))

import seth_gateway as g  # noqa: E402
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
        _rota("local-a", "a:1b", ["codigo", "conversa"], 10),
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
    grande = _p("a" * 20000)  # ~6666 tokens > teto de local-a (6000)
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

    def do_GET(self):
        self.server.gets.append(self.path)
        self._enviar(200, json.dumps({"object": "list", "data": [{"id": "seth-livre"}]}).encode())

    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
        self.server.chamadas.append(corpo.get("model"))
        nuvem = str(corpo.get("model", "")).startswith("nvidia/")
        self.server.corpos.append(corpo)
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
    assert status == 200 and texto == "fila ok"
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
    assert status == 200 and texto == "fila ok"
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
    assert status == 200 and texto == "fila ok" and vistos[-2:] == ["nvidia/nvidia/nemotron-3.5-super-vl-120b-a12b", "seth-livre"], vistos


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
    assert status == 200 and texto == "fila ok"
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
    assert status == 200 and texto == "fila ok" and len(c.up.chamadas) == 2
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
