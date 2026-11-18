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
    # nuvem nunca recebe dado pessoal e nenhuma rota por tipo é de nuvem
    assert all(r["categoria"] == "local" for r in por_id.values())


def test_ficha_rejeita_tipo_em_nuvem_e_sem_teto():
    erros, _ = ficha_mod.verificar({"rotas": [dict(_rota("x", "m", ["codigo"]), categoria="gratuito",
                                                   classes_permitidas=["publico"])]})
    assert any("só vale para rota local" in e for e in erros)
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
