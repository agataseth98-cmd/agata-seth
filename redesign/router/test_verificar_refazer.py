"""Testes de verificar e refazer (18/11/2026, seth_gateway). Sem rede e sem provedor.

O gateway real sobe numa porta livre e fala com um upstream falso (HTTP em 127.0.0.1, também numa porta livre).
Cada caso conta quantas chamadas o upstream recebeu e confere o que o cliente recebe. A verificação é falsa
(um achado por marca RUIM no texto), salvo nos casos que usam a real ou um achado com segredo sintético. O token
interno e o estado do repositório são trocados por valores de teste; nada disso lê ~/.config/agata.

Cobre: resposta limpa (1 chamada), ruim e depois boa (2 chamadas, sem bloco), sempre ruim (teto de tentativas e
melhor resposta com o bloco), teto de segundos, legado intacto, chave SETH_REFAZER=0, canário capacidade:N,
stream, escalada de fila, verificação real; a 1ª resposta com prazo e teto de bytes (fluxo infinito, keepalive
para sempre, gotejo); candidata inválida que nunca vence; segredo no achado que não vai para a nota; e as funções
puras (leitura com prazo, estrutura válida, escalada, nota, texto conferido).
Rodar: pytest -q redesign/router/test_verificar_refazer.py
"""
import json
import os
import queue
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import seth_gateway as g  # noqa: E402

REAL_VERIFICAR = g.auditoria_turno.verificar_resposta_atual
VARS = ("SETH_REFAZER", "SETH_REFAZER_MAX", "SETH_REFAZER_SEG", "SETH_REFAZER_1A_SEG", "SETH_REFAZER_BYTES",
        "SETH_ROTEADOR", "SETH_VERIFICACAO_BLOQUEIA")
TOKEN = "TOKEN-" + "DE-TESTE-NAO-E-SEGREDO"
BLOCO_TOOL = '<tool_call>{"name": "buscar", "arguments": {"q": "agata"}}</tool_call>'
# segredos sintéticos, montados em tempo de execução: o literal inteiro casaria a varredura de segredo do pré-commit
SEGREDO = "sk" + "-" + "TESTEsintetico0123456789abcdefGHIJ"
PORTADOR = "abcDEF123tokenFALSO999"
KEEPALIVE = (b'data: {"id":"chatcmpl-keepalive","model":"keepalive",'
             b'"choices":[{"index":0,"delta":{},"finish_reason":null}]}\n\n')


class Bruto:
    """Corpo cru para o upstream falso: resposta malformada, truncada ou sem fim."""

    def __init__(self, corpo: bytes, ctype: str = "application/json"):
        self.corpo, self.ctype = corpo, ctype


def _achados_ruins(texto, msgs_pedido):
    """Verificação falsa e contável: um achado por marca RUIM. Assim dá para escolher a resposta com menos achados."""
    return [f"achado {i + 1}: marca RUIM" for i in range(texto.count("RUIM"))]


def _achados_com_segredo(texto, msgs_pedido):
    """Verificação falsa que devolve segredo sintético dentro do achado (o caso que a nota não pode levar)."""
    if "RUIM" in texto:
        return [f"achado: chave {SEGREDO} na saída e Authorization: Bearer {PORTADOR}"]
    return []


def _sse(texto):
    a = {"id": "f", "model": "modelo-falso",
         "choices": [{"index": 0, "delta": {"content": texto}, "finish_reason": None}]}
    b = {"id": "f", "model": "modelo-falso", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
    return (f"data: {json.dumps(a, ensure_ascii=False)}\n\ndata: {json.dumps(b)}\n\ndata: [DONE]\n\n").encode("utf-8")


def _sse_truncado(texto):
    """Stream que acaba no meio: sem [DONE] e sem finish_reason."""
    a = {"id": "f", "model": "modelo-falso",
         "choices": [{"index": 0, "delta": {"content": texto}, "finish_reason": None}]}
    return f"data: {json.dumps(a, ensure_ascii=False)}\n\n".encode("utf-8")


def _json_resposta(content, tool_calls=None):
    m = {"role": "assistant", "content": content}
    if tool_calls is not None:
        m["tool_calls"] = tool_calls
    return json.dumps({"model": "modelo-falso", "choices": [{"message": m}]}).encode("utf-8")


def _conteudo(corpo: str, stream: bool) -> str:
    """O texto que o cliente recebeu: `content` no JSON, ou a soma dos deltas no SSE."""
    if not stream:
        return json.loads(corpo)["choices"][0]["message"]["content"]
    partes = []
    for linha in corpo.split("\n"):
        if linha.startswith("data:") and linha.strip() != "data: [DONE]":
            for c in json.loads(linha[5:]).get("choices") or []:
                partes.append((c.get("delta") or {}).get("content") or "")
    return "".join(partes)


class _Upstream(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        fake = self.server.fake
        corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
        fake.chamadas.append(corpo)
        if fake.atraso:
            time.sleep(fake.atraso)
        if fake.modo in ("keepalive", "gotejo"):
            return self._fluxo_sem_fim(fake.modo)
        texto = fake.textos[min(len(fake.chamadas) - 1, len(fake.textos) - 1)]
        if isinstance(texto, Bruto):
            body, ctype = texto.corpo, texto.ctype
        elif fake.sse:
            body, ctype = _sse(texto), "text/event-stream"
        else:
            resposta = {"model": "modelo-falso", "choices": [{"message": {"role": "assistant", "content": texto}}]}
            body, ctype = json.dumps(resposta, ensure_ascii=False).encode("utf-8"), "application/json"
        try:
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass  # o gateway já desistiu desta tentativa (teto): nada a fazer

    def _fluxo_sem_fim(self, modo):
        """Stream que não acaba: keepalive para sempre ('gotejo' espaça os pedaços)."""
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            while True:
                self.wfile.write(KEEPALIVE)
                self.wfile.flush()
                time.sleep(0.01 if modo == "gotejo" else 0.002)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass


class _FakeUpstream:
    """Upstream falso: devolve a lista de textos, uma por chamada (repete a última). Guarda cada corpo recebido."""

    def __init__(self, textos, sse=False, atraso=0.0, modo="normal"):
        self.textos, self.sse, self.atraso, self.modo = list(textos), sse, atraso, modo
        self.chamadas = []
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), _Upstream)
        self.srv.fake = self
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()


class _Cenario:
    def __init__(self, monkeypatch):
        self._mp = monkeypatch
        self.up = None
        self.gw = None

    def subir(self, textos, sse=False, atraso=0.0, modo="normal"):
        self.up = _FakeUpstream(textos, sse, atraso, modo)
        self._mp.setattr(g, "UPSTREAM", self.up.url)
        self.gw = g.ServidorConcorrenciaLimitada(("127.0.0.1", 0), g._Handler)
        self.gw._selftest_allow_context = True  # fora da faixa pública: o pedido segue o caminho seth-*
        threading.Thread(target=self.gw.serve_forever, daemon=True).start()
        return self

    def _requisicao(self, modelo, stream, pergunta):
        corpo = {"model": modelo, "stream": stream, "messages": [{"role": "user", "content": pergunta}]}
        return urllib.request.Request(
            f"http://127.0.0.1:{self.gw.server_address[1]}/v1/chat/completions",
            data=json.dumps(corpo).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"})

    def pedir(self, modelo="seth-pesado", stream=False, pergunta="Qual é o estado?"):
        with urllib.request.urlopen(self._requisicao(modelo, stream, pergunta), timeout=30) as r:
            return r.status, dict(r.headers.items()), r.read().decode("utf-8")

    def pedir_parcial(self, n, modelo="seth-pesado"):
        """Lê só `n` bytes do stream e fecha: para os casos em que o upstream nunca termina."""
        with urllib.request.urlopen(self._requisicao(modelo, True, "Qual é o estado?"), timeout=30) as r:
            return r.status, r.read(n).decode("utf-8", "replace")

    def fechar(self):
        for s in (self.gw, self.up.srv if self.up else None):
            if s is not None:
                s.shutdown()
                s.server_close()


@pytest.fixture(autouse=True)
def ambiente(monkeypatch, tmp_path):
    for var in VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AGATA_EMOJI_LOG", str(tmp_path / "emoji.jsonl"))
    monkeypatch.setenv("AGATA_LACO_LOG", str(tmp_path / "laco.jsonl"))
    monkeypatch.setenv("AGATA_CABECALHO_LOG", str(tmp_path / "cabecalho.jsonl"))
    monkeypatch.setattr(g, "MODELO_REAL_PATH", tmp_path / "modelo-real.txt")
    monkeypatch.setattr(g, "_token_interno", lambda: TOKEN)
    monkeypatch.setattr(g, "_estado", lambda: "sync: PASS")
    monkeypatch.setattr(g, "_injeta", lambda payload: payload)  # sem hidratação: o caso não depende do repositório
    monkeypatch.setattr(g.auditoria_turno, "verificar_resposta_atual", _achados_ruins)


@pytest.fixture
def cenario(monkeypatch):
    criados = []

    def subir(textos, sse=False, atraso=0.0, modo="normal"):
        c = _Cenario(monkeypatch).subir(textos, sse, atraso, modo)
        criados.append(c)
        return c

    yield subir
    for c in criados:
        c.fechar()


# --- casos de ponta a ponta (gateway real, upstream falso) ------------------------------------------------

def test_resposta_limpa_faz_uma_chamada(cenario, monkeypatch, capsys):
    monkeypatch.setenv("SETH_REFAZER", "1")
    c = cenario(["resposta boa"])
    status, _, corpo = c.pedir()
    texto = _conteudo(corpo, False)
    assert status == 200 and len(c.up.chamadas) == 1
    assert "resposta boa" in texto and "Verificação da Máquina" not in texto
    assert "refazer_tentativas=0 achados_inicio=0 achados_fim=0" in capsys.readouterr().err


def test_ruim_depois_boa_entrega_a_boa_sem_bloco(cenario, monkeypatch, capsys):
    monkeypatch.setenv("SETH_REFAZER", "1")
    c = cenario(["RUIM", "resposta boa"])
    _, _, corpo = c.pedir()
    texto = _conteudo(corpo, False)
    assert len(c.up.chamadas) == 2
    assert "resposta boa" in texto and "Verificação da Máquina" not in texto and "RUIM" not in texto
    segunda = c.up.chamadas[1]["messages"]
    assert segunda[-2] == {"role": "assistant", "content": "RUIM"}
    assert segunda[-1]["role"] == "user" and "achado 1: marca RUIM" in segunda[-1]["content"]
    assert TOKEN not in json.dumps(c.up.chamadas, ensure_ascii=False)  # o token vai no cabeçalho, nunca no corpo
    assert "refazer_tentativas=1 achados_inicio=1 achados_fim=0" in capsys.readouterr().err


def test_sempre_ruim_respeita_o_teto_e_entrega_a_melhor(cenario, monkeypatch, capsys):
    monkeypatch.setenv("SETH_REFAZER", "1")
    c = cenario(["RUIM RUIM RUIM", "RUIM", "RUIM RUIM"])  # 3, 1 e 2 achados: a melhor é a do meio
    _, _, corpo = c.pedir()
    texto = _conteudo(corpo, False)
    assert len(c.up.chamadas) == 3  # 1 + SETH_REFAZER_MAX (2)
    assert "RUIM RUIM" not in texto  # a de 3 achados não foi a entregue
    assert "Verificação da Máquina" in texto and texto.count("- achado") == 1
    assert "- achado 1: marca RUIM" in texto
    assert "refazer_tentativas=2 achados_inicio=3 achados_fim=1" in capsys.readouterr().err


def test_maximo_de_tentativas_pela_variavel(cenario, monkeypatch, capsys):
    monkeypatch.setenv("SETH_REFAZER", "1")
    monkeypatch.setenv("SETH_REFAZER_MAX", "1")
    c = cenario(["RUIM", "RUIM", "RUIM"])
    _, _, corpo = c.pedir()
    assert len(c.up.chamadas) == 2
    assert "Verificação da Máquina" in _conteudo(corpo, False)
    assert "refazer_tentativas=1" in capsys.readouterr().err


def test_teto_de_segundos_corta_a_nova_tentativa(cenario, monkeypatch, capsys):
    # cada chamada leva 0,5 s; o teto das novas tentativas é 0,2 s: a 1ª tentativa nova não chega no prazo
    # e o gateway para
    monkeypatch.setenv("SETH_REFAZER", "1")
    monkeypatch.setenv("SETH_REFAZER_MAX", "5")
    monkeypatch.setenv("SETH_REFAZER_SEG", "0.2")
    c = cenario(["RUIM", "RUIM", "RUIM"], atraso=0.5)
    t0 = time.monotonic()
    _, _, corpo = c.pedir()
    assert time.monotonic() - t0 < 5
    assert len(c.up.chamadas) == 2
    assert "Verificação da Máquina" in _conteudo(corpo, False)  # entregue a melhor até ali, com o bloco
    assert "refazer_tentativas=1 achados_inicio=1 achados_fim=1" in capsys.readouterr().err


def test_legado_nao_refaz_e_anexa_o_bloco(cenario, capsys):
    c = cenario(["RUIM", "resposta boa"])  # sem nenhuma variável: padrão legado
    _, _, corpo = c.pedir()
    assert len(c.up.chamadas) == 1
    assert "RUIM" in _conteudo(corpo, False) and "Verificação da Máquina" in _conteudo(corpo, False)
    assert "refazer_tentativas" not in capsys.readouterr().err


def test_chave_zero_desliga_mesmo_com_canario_em_100(cenario, monkeypatch, capsys):
    monkeypatch.setenv("SETH_REFAZER", "0")
    monkeypatch.setenv("SETH_ROTEADOR", "capacidade:100")
    c = cenario(["RUIM", "resposta boa"])
    _, _, corpo = c.pedir()
    assert len(c.up.chamadas) == 1
    assert "Verificação da Máquina" in _conteudo(corpo, False)
    assert "refazer_tentativas" not in capsys.readouterr().err


@pytest.mark.parametrize("roteador, chamadas", [("capacidade:100", 2), ("capacidade:0", 1), ("capacidade", 1),
                                                ("sombra", 1)])
def test_canario_capacidade_decide_por_pedido(cenario, monkeypatch, roteador, chamadas):
    monkeypatch.setenv("SETH_ROTEADOR", roteador)
    c = cenario(["RUIM", "resposta boa"])
    c.pedir()
    assert len(c.up.chamadas) == chamadas


def test_stream_ruim_depois_boa(cenario, monkeypatch):
    monkeypatch.setenv("SETH_REFAZER", "1")
    c = cenario(["RUIM", "resposta boa"], sse=True)
    _, _, corpo = c.pedir(stream=True)
    texto = _conteudo(corpo, True)
    assert len(c.up.chamadas) == 2
    assert "resposta boa" in texto and "Verificação da Máquina" not in texto and "RUIM" not in texto


def test_stream_limpo_faz_uma_chamada(cenario, monkeypatch):
    monkeypatch.setenv("SETH_REFAZER", "1")
    c = cenario(["resposta boa"], sse=True)
    _, _, corpo = c.pedir(stream=True)
    assert len(c.up.chamadas) == 1 and "resposta boa" in _conteudo(corpo, True)


def test_stream_sempre_ruim_entrega_a_melhor_com_bloco(cenario, monkeypatch):
    monkeypatch.setenv("SETH_REFAZER", "1")
    monkeypatch.setenv("SETH_REFAZER_MAX", "1")
    c = cenario(["RUIM RUIM", "RUIM"], sse=True)
    _, _, corpo = c.pedir(stream=True)
    texto = _conteudo(corpo, True)
    assert len(c.up.chamadas) == 2
    assert "Verificação da Máquina" in texto and "- achado 1: marca RUIM" in texto
    assert texto.count("- achado") == 1


def test_escala_a_fila_a_cada_tentativa(cenario, monkeypatch):
    monkeypatch.setenv("SETH_REFAZER", "1")
    c = cenario(["RUIM", "RUIM", "resposta boa"])
    _, headers, corpo = c.pedir(modelo="seth-rapido")
    assert [x["model"] for x in c.up.chamadas] == ["seth-rapido", "seth-livre", "seth-pesado"]
    assert headers.get("X-Seth-Rota") == "seth-pesado"
    assert "resposta boa" in _conteudo(corpo, False)


def test_auditoria_real_confere_caminho_inexistente(cenario, monkeypatch):
    # sem a verificação falsa: a checagem real de caminho de arquivo é que manda refazer
    monkeypatch.setattr(g.auditoria_turno, "verificar_resposta_atual", REAL_VERIFICAR)
    monkeypatch.setenv("SETH_REFAZER", "1")
    c = cenario(["Veja `scripts/nao_existe_refazer_18_11.py` para o detalhe.",
                 "Veja `scripts/turno.py` para o detalhe."])
    _, _, corpo = c.pedir()
    assert len(c.up.chamadas) == 2
    assert "cita caminho que não existe" in json.dumps(c.up.chamadas[1]["messages"], ensure_ascii=False)
    assert "Verificação da Máquina" not in _conteudo(corpo, False)


# --- 1ª resposta: prazo absoluto e teto de bytes (upstream que nunca termina) ------------------------------

def test_primeira_sse_com_keepalive_sem_fim_para_no_limite_de_bytes(cenario, monkeypatch, capsys):
    # O upstream manda keepalive para sempre e nenhum conteúdo. A espreita (0,2 s) junta uns 11 KB; a coleta da 1ª
    # resposta para no teto de 50 KB, sem prazo. Prova: o pedido não fica preso e o keepalive chega ao cliente pelo
    # caminho legado (convertido em comentário, o JSON cru não sai).
    # Por que é 1 chamada (medido, não suposto): o pedido vai direto a seth-pesado, sem passar pela rota. self._rota
    # fica vazio (o log do refazer mostra rota=-), e o resgate do 709 só age com self._rota definido (rota seth-livre
    # pelo Laya). O mapa _FILA_RAPIDA (seth-pesado -> seth-rapido) não chega a ser consultado. O controle
    # test_livre_via_laya_pesado_faz_a_nova_tentativa_709 faz as duas chamadas quando a rota existe.
    monkeypatch.setenv("SETH_REFAZER", "1")
    monkeypatch.setenv("SETH_REFAZER_BYTES", "50000")
    monkeypatch.setattr(g, "PRAZO_1O_CONTEUDO", 0.2)  # o espreita do stream não espera 40 s por conteúdo
    c = cenario([], modo="keepalive")
    t0 = time.monotonic()
    status, trecho = c.pedir_parcial(300)
    err = capsys.readouterr().err
    assert status == 200 and time.monotonic() - t0 < 20
    assert ": ka" in trecho and "chatcmpl-keepalive" not in trecho
    assert len(c.up.chamadas) == 1
    assert "passou do limite (limite)" in err  # a causa: a coleta parou no teto de bytes
    assert "nova tentativa" not in err         # o 709 não disparou
    assert "rota=-" in err                     # o pedido não tem rota


def test_keepalive_sem_conteudo_na_rota_livre_segue_a_fila_rapida(cenario, monkeypatch, capsys):
    # Rota seth-livre: o 709 manda o pedido à fila mais rápida quando não chega conteúdo no prazo. Duas chamadas
    # (seth-livre e seth-rapido), e a 2ª é a que a entrega. O Laya é trocado por uma escolha fixa (sem rede) e a
    # sombra fica desligada.
    monkeypatch.setenv("SETH_REFAZER", "1")
    monkeypatch.setenv("SETH_REFAZER_BYTES", "50000")
    monkeypatch.setattr(g, "PRAZO_1O_CONTEUDO", 0.2)
    monkeypatch.setattr(g, "_rota_laya", lambda payload: ("seth-livre", {}))
    monkeypatch.setattr(g, "_sombra_rota", lambda *a, **k: None)
    c = cenario([], modo="keepalive")
    status, trecho = c.pedir_parcial(300, modelo="seth-livre")
    assert status == 200 and ": ka" in trecho
    assert [x["model"] for x in c.up.chamadas] == ["seth-livre", "seth-rapido"]
    assert "passou do limite (limite)" in capsys.readouterr().err


def test_livre_via_laya_pesado_faz_a_nova_tentativa_709(cenario, monkeypatch, capsys):
    # Controle do caso de seth-pesado direto: a rota seth-livre escolhe seth-pesado pelo Laya (trocado por escolha
    # fixa, sem rede). Aí self._rota é seth-pesado, o resgate do 709 age e o mapa _FILA_RAPIDA leva a seth-rapido.
    monkeypatch.setenv("SETH_REFAZER", "1")
    monkeypatch.setenv("SETH_REFAZER_BYTES", "50000")
    monkeypatch.setattr(g, "PRAZO_1O_CONTEUDO", 0.2)
    monkeypatch.setattr(g, "_rota_laya", lambda payload: ("seth-pesado", {}))
    monkeypatch.setattr(g, "_sombra_rota", lambda *a, **k: None)
    c = cenario([], modo="keepalive")
    status, trecho = c.pedir_parcial(300, modelo="seth-livre")
    err = capsys.readouterr().err
    assert status == 200 and ": ka" in trecho
    assert [x["model"] for x in c.up.chamadas] == ["seth-pesado", "seth-rapido"]
    assert "nova tentativa" in err and "passou do limite (limite)" in err


def test_pre_leitura_acima_do_teto_nao_vai_a_auditoria_nem_a_refazer(cenario, monkeypatch, capsys):
    # r2, achado 1: 300 keepalives e depois um achado (RUIM), num corpo só. A espreita já leu tudo (uns 33 KB) com teto
    # de 1000 bytes. Antes da correção, a coleta seguinte recebia o teto cheio e a resposta ia à auditoria e refazia.
    monkeypatch.setenv("SETH_REFAZER", "1")
    monkeypatch.setenv("SETH_REFAZER_BYTES", "1000")
    c = cenario([Bruto(KEEPALIVE * 300 + _sse("RUIM"), "text/event-stream")], sse=True)
    _, _, corpo = c.pedir(stream=True)
    assert len(c.up.chamadas) == 1
    assert "passou do limite (limite)" in capsys.readouterr().err
    assert "RUIM" in _conteudo(corpo, True) and "Verificação da Máquina" in _conteudo(corpo, True)  # caminho legado


def test_corpo_json_acima_do_teto_nao_vai_a_refazer(cenario, monkeypatch, capsys):
    monkeypatch.setenv("SETH_REFAZER", "1")
    monkeypatch.setenv("SETH_REFAZER_BYTES", "10")
    c = cenario(["RUIM", "resposta boa"])
    _, _, corpo = c.pedir()
    assert len(c.up.chamadas) == 1
    assert "passou do limite (limite)" in capsys.readouterr().err
    assert "RUIM" in _conteudo(corpo, False)


def test_primeira_sse_gotejando_para_no_prazo(cenario, monkeypatch, capsys):
    monkeypatch.setenv("SETH_REFAZER", "1")
    monkeypatch.setenv("SETH_REFAZER_1A_SEG", "0.3")
    monkeypatch.setattr(g, "PRAZO_1O_CONTEUDO", 0.2)
    c = cenario([], modo="gotejo")
    t0 = time.monotonic()
    status, trecho = c.pedir_parcial(300)
    err = capsys.readouterr().err
    assert status == 200 and ": ka" in trecho and time.monotonic() - t0 < 10
    # Por que é 1 chamada (medido): seth-pesado direto, sem rota (rota=- no log), e o 709 só age com rota definida.
    assert len(c.up.chamadas) == 1
    assert "passou do limite (prazo)" in err   # a causa: a coleta parou no prazo
    assert "nova tentativa" not in err         # o 709 não disparou
    assert "rota=-" in err


def test_primeira_sse_truncada_nao_refaz(cenario, monkeypatch, capsys):
    monkeypatch.setenv("SETH_REFAZER", "1")
    c = cenario([Bruto(_sse_truncado("RUIM parcial"), "text/event-stream")], sse=True)
    _, _, corpo = c.pedir(stream=True)
    assert len(c.up.chamadas) == 1
    assert "sem estrutura válida" in capsys.readouterr().err


# --- candidata inválida nunca vence -----------------------------------------------------------------------

@pytest.mark.parametrize("corpo", [
    # sem o campo model a espreita não para no conteúdo: lê o EOF antes da coleta (r4)
    b'data: {"choices":[{"delta":{"content":"oi"},"finish_reason":null}]}\n\n'
    b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n',
    b"data: [DONE]\n\n",  # SSE vazio: o EOF também cai na espreita
], ids=["com-texto", "so-done"])
def test_sse_curto_que_termina_na_pre_leitura_nao_espera_o_prazo(cenario, monkeypatch, capsys, corpo):
    # Com teto de 5 s para a 1ª coleta, a resposta tem de sair em menos de 1 s e sem o registro de prazo: o EOF já foi
    # lido, então o leitor não tem o que dar. Antes da correção, a coleta esperava o teto inteiro no leitor esgotado.
    monkeypatch.setenv("SETH_REFAZER", "1")
    monkeypatch.setenv("SETH_REFAZER_1A_SEG", "5")
    c = cenario([Bruto(corpo, "text/event-stream")], sse=True)
    t0 = time.monotonic()
    _, _, texto = c.pedir(stream=True)
    decorrido = time.monotonic() - t0
    err = capsys.readouterr().err
    assert decorrido < 1, decorrido
    assert "passou do limite" not in err and "nova tentativa" not in err
    assert len(c.up.chamadas) == 1


@pytest.mark.parametrize("bruto", [
    Bruto(b'{"choices":[{"message":{"content":"PARCIAL-SEM-FIM"'),  # JSON cortado
    Bruto(b'{"resposta": "PARCIAL-SEM-FIM"}'),                       # sem choices
])
def test_retry_json_invalido_nunca_vence(cenario, monkeypatch, capsys, bruto):
    monkeypatch.setenv("SETH_REFAZER", "1")
    c = cenario(["RUIM", bruto])  # a candidata inválida teria 0 achados e venceria a seleção
    _, _, corpo = c.pedir()
    texto = _conteudo(corpo, False)
    assert len(c.up.chamadas) == 2
    assert "RUIM" in texto and "Verificação da Máquina" in texto and "PARCIAL-SEM-FIM" not in texto
    assert "refazer_tentativas=1 achados_inicio=1 achados_fim=1" in capsys.readouterr().err


def test_retry_sse_sem_fim_nao_vence(cenario, monkeypatch, capsys):
    monkeypatch.setenv("SETH_REFAZER", "1")
    c = cenario(["RUIM", Bruto(_sse_truncado("PARCIAL-SEM-FIM"), "text/event-stream")], sse=True)
    _, _, corpo = c.pedir(stream=True)
    texto = _conteudo(corpo, True)
    assert len(c.up.chamadas) == 2
    assert "RUIM" in texto and "Verificação da Máquina" in texto and "PARCIAL-SEM-FIM" not in texto
    assert "refazer_tentativas=1 achados_inicio=1 achados_fim=1" in capsys.readouterr().err


# --- segredo no achado não vai para a nota -----------------------------------------------------------------

def test_retry_nao_leva_segredo_do_achado(cenario, monkeypatch):
    monkeypatch.setenv("SETH_REFAZER", "1")
    monkeypatch.setattr(g.auditoria_turno, "verificar_resposta_atual", _achados_com_segredo)
    c = cenario(["RUIM", "resposta boa"])
    _, _, corpo = c.pedir()
    assert len(c.up.chamadas) == 2
    enviado = json.dumps(c.up.chamadas, ensure_ascii=False)
    assert SEGREDO not in enviado and PORTADOR not in enviado  # nem a nota nem o resto do corpo levam o segredo
    assert "[segredo removido]" in enviado
    assert "resposta boa" in _conteudo(corpo, False) and "Verificação da Máquina" not in _conteudo(corpo, False)


# --- funções puras --------------------------------------------------------------------------------------

def test_escalada_sobe_uma_fila_e_para_no_topo():
    assert g._proxima_fila_refazer("seth-rapido") == "seth-livre"
    assert g._proxima_fila_refazer("seth-livre") == "seth-pesado"
    assert g._proxima_fila_refazer("seth-pesado") == "seth-pesado"  # o mapa do resgate daria seth-livre: rebaixar não
    assert g._proxima_fila_refazer("seth-livre-longo") == "seth-livre-longo"
    assert g._proxima_fila_refazer("") == ""


def test_decisao_do_canario_e_da_chave(monkeypatch):
    for var in VARS:
        monkeypatch.delenv(var, raising=False)
    assert g._refazer_ligado_neste_pedido() is False  # legado
    monkeypatch.setenv("SETH_REFAZER", "1")
    assert g._refazer_ligado_neste_pedido() is True
    monkeypatch.setenv("SETH_ROTEADOR", "capacidade:100")
    monkeypatch.setenv("SETH_REFAZER", "0")
    assert g._refazer_ligado_neste_pedido() is False  # a chave 0 vence o canário
    monkeypatch.delenv("SETH_REFAZER")
    for modo in ("capacidade:0", "capacidade", "capacidade:abc", "sombra"):
        monkeypatch.setenv("SETH_ROTEADOR", modo)
        assert g._refazer_ligado_neste_pedido() is False, modo
    monkeypatch.setenv("SETH_ROTEADOR", "capacidade:100")
    assert g._refazer_ligado_neste_pedido() is True


def test_limites_com_padrao_e_valor_invalido(monkeypatch):
    for var in VARS:
        monkeypatch.delenv(var, raising=False)
    assert g._refazer_max() == 2 and g._refazer_seg() == 60.0
    assert g._refazer_1a_seg() == 180.0 and g._refazer_bytes() == 4 * 1024 * 1024
    monkeypatch.setenv("SETH_REFAZER_MAX", "5")
    monkeypatch.setenv("SETH_REFAZER_SEG", "0.5")
    monkeypatch.setenv("SETH_REFAZER_1A_SEG", "2")
    monkeypatch.setenv("SETH_REFAZER_BYTES", "1000")
    assert g._refazer_max() == 5 and g._refazer_seg() == 0.5
    assert g._refazer_1a_seg() == 2.0 and g._refazer_bytes() == 1000
    monkeypatch.setenv("SETH_REFAZER_MAX", "-3")
    monkeypatch.setenv("SETH_REFAZER_SEG", "x")
    monkeypatch.setenv("SETH_REFAZER_1A_SEG", "x")
    monkeypatch.setenv("SETH_REFAZER_BYTES", "-5")
    assert g._refazer_max() == 0 and g._refazer_seg() == 60.0
    assert g._refazer_1a_seg() == 180.0 and g._refazer_bytes() == 0


class _LeitorFalso:
    def __init__(self, itens):
        self._itens = list(itens)

    def ler(self, timeout):
        item = self._itens.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


class _LeitorInfinito:
    """Upstream que nunca acaba: tem dados prontos a cada leitura (o caso que o revisor reproduziu)."""

    def __init__(self, pausa=0.0):
        self.lidos, self.pausa = 0, pausa

    def ler(self, timeout):
        self.lidos += 1
        if self.pausa:
            time.sleep(self.pausa)
        return b"x" * 100


def test_consumir_le_ate_o_fim_erro_ou_prazo():
    assert g._consumir(_LeitorFalso([b"a", b"b", b""])) == (b"ab", "fim")
    assert g._consumir(_LeitorFalso([b"a", RuntimeError("caiu")])) == (b"a", "erro")
    assert g._consumir(_LeitorFalso([b"a", queue.Empty()]), time.monotonic() + 5) == (b"a", "prazo")


def test_consumir_para_no_prazo_mesmo_com_dados_prontos():
    # prazo já vencido: não lê nada, nem com dados prontos (antes lia até o fim do fluxo)
    l = _LeitorInfinito()
    assert g._consumir(l, time.monotonic() - 1) == (b"", "prazo")
    assert l.lidos == 0
    # prazo no futuro, fluxo infinito: para no prazo
    t0 = time.monotonic()
    dados, motivo = g._consumir(_LeitorInfinito(pausa=0.001), time.monotonic() + 0.1)
    assert motivo == "prazo" and dados and time.monotonic() - t0 < 5


def test_consumir_para_no_limite_de_bytes():
    dados, motivo = g._consumir(_LeitorInfinito(), None, limite=1000)
    assert motivo == "limite" and 1000 < len(dados) <= 1100


def test_resposta_valida_so_com_estrutura_minima():
    assert g._resposta_valida(_json_resposta("oi"), False)
    assert g._resposta_valida(_json_resposta("", tool_calls=[{"id": "x"}]), False)
    assert not g._resposta_valida(b'{"choices":[{"message":{"content":"PARCIAL', False)  # JSON cortado
    assert not g._resposta_valida(b'{"x": "PARCIAL"}', False)                          # sem choices
    assert not g._resposta_valida(_json_resposta(""), False)                           # vazia
    assert g._resposta_valida(_sse("oi"), True)                                        # [DONE] e finish
    assert g._resposta_valida(b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\n', True)  # só finish
    assert not g._resposta_valida(_sse_truncado("PARCIAL"), True)                      # sem fim
    assert not g._resposta_valida(KEEPALIVE, True)                                     # só keepalive


def test_texto_conferido_e_o_que_a_entrega_mostraria():
    json_texto = json.dumps({"choices": [{"message": {"content": "oi"}}]}).encode()
    assert g._texto_auditavel(json_texto, False, frozenset()) == "oi"
    ferramenta = json.dumps({"choices": [{"message": {"content": BLOCO_TOOL}}]}).encode()
    # ferramenta escrita como texto vira chamada: sobra texto nenhum para conferir
    assert g._texto_auditavel(ferramenta, False, frozenset({"buscar"})) == ""
    sse = _sse("olá")
    assert g._texto_auditavel(sse, True, frozenset()) == "olá"


def test_nota_nao_leva_segredo_sintetico():
    nota = g._nota_refazer([f"achado: chave {SEGREDO} na saída", f"Authorization: Bearer {PORTADOR}"])
    assert SEGREDO not in nota and PORTADOR not in nota and "Bearer" not in nota
    assert "[segredo removido]" in nota and "Authorization: [segredo removido]" in nota
    assert "achado 1: marca RUIM" in g._nota_refazer(["achado 1: marca RUIM"])  # o que não é segredo fica


def test_sem_regua_de_segredo_o_detalhe_do_achado_nao_vai_a_nota(monkeypatch):
    monkeypatch.setitem(sys.modules, "sanitizar", None)  # a importação falha: a régua não está disponível
    nota = g._nota_refazer([f"achado: chave {SEGREDO}"])
    assert SEGREDO not in nota and "régua de segredo indisponível" in nota


def test_pedido_leva_so_a_resposta_ruim_e_a_nota():
    corpo = json.dumps({"model": "seth-rapido", "messages": [{"role": "user", "content": "oi"}]}).encode()
    pedido = json.loads(g._pedido_refazer(corpo, "RUIM", ["achado A"], "seth-livre"))
    assert pedido["model"] == "seth-livre"
    assert pedido["messages"][1:] == [{"role": "assistant", "content": "RUIM"},
                                      {"role": "user", "content": g._nota_refazer(["achado A"])}]
