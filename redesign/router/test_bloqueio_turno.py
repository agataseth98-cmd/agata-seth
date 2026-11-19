"""Testes do bloqueio no lugar de aviso (19/11/2026): bloqueio_turno.py e o gancho no seth_gateway. Sem rede e sem provedor.

Cobre as funções puras (escrita afirmada sem escrita bem-sucedida, saída de ferramenta simulada, cabeçalho duplicado ou
de outro modelo, sem alarme falso em texto comum) e o gateway real com upstream falso em HTTP local: corrige na 2a
tentativa, persistindo entrega a resposta mínima, a nota de correção vai só ao contexto do modelo, resposta com tool_call
passa, escrita bem-sucedida libera, stream, chave SETH_BLOQUEIO_TURNO=0, e GET e POST depois de POST na MESMA conexão
http.client (lição do incidente de 18/11).
Rodar: pytest -q redesign/router/test_bloqueio_turno.py
"""
import http.client
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bloqueio_turno as b  # noqa: E402
import seth_gateway as g  # noqa: E402

TOKEN = "TOKEN-" + "DE-TESTE-NAO-E-SEGREDO"
U = [{"role": "user", "content": "registre isso"}]


def _turno_com(nome, resultado, id_="c1"):
    return U + [{"role": "assistant", "content": "", "tool_calls": [
        {"id": id_, "type": "function", "function": {"name": nome, "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": id_, "content": resultado}]


# --- funções puras --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("texto", ["Criei o arquivo x.md.", "Proposta: APLICADA.", "Entrada REGISTRADO com sucesso.",
                                   "A nota foi gravada.", "Gravei a decisão.", "O arquivo foi criado."])
def test_a_escrita_afirmada_sem_ferramenta_e_achado(texto):
    assert [c for c, _ in b.achados(texto, U)] == ["a"]


@pytest.mark.parametrize("texto", ["Escrevi o texto abaixo.", "Posso criar o arquivo se você quiser.", "Não gravei nada.",
                                   "Vou registrar depois da sua aprovação.", "Se eu aplicar, a proposta fica pendente.",
                                   "Qual arquivo foi criado?", "```\ncriei o arquivo\n```\nExemplo acima.", "Bom dia."])
def test_a_sem_alarme_falso_em_texto_comum(texto):
    assert b.achados(texto, U) == []


def test_a_escrita_bem_sucedida_no_turno_libera():
    ok = _turno_com("memoria_acrescentar_mcp_canon", '{"ok": true, "entrada": 1067}')
    assert b.escrita_bem_sucedida(ok) and b.achados("Registrei a entrada.", ok) == []


@pytest.mark.parametrize("resultado", ['{"ok": false, "erro": "sem capability"}', "Cancelado", "Error: not found",
                                       "aprovação negada pelo Humano", '{"erro": "não foi possível gravar"}',
                                       '{"ok": true, "erro": "não foi possível gravar o índice"}',
                                       '{"error": "nao"}', "Falha ao gravar a entrada", "Traceback (most recent call last)",
                                       "feito", '{"entrada": 1067}', "não foi possível registrar", ""])
def test_a_escrita_que_falhou_ou_foi_negada_nao_libera(resultado):
    t = _turno_com("memoria_acrescentar_mcp_canon", resultado)
    assert not b.escrita_bem_sucedida(t)
    assert [c for c, _ in b.achados("Registrei a entrada.", t)] == ["a"]


@pytest.mark.parametrize("resultado", ['{"ok": true, "entrada": 1067}', '{"success": true}', '{"status": "ok"}',
                                       '{"ok": true, "erro": null}', "Entrada registrada com sucesso (1067)"])
def test_a_so_resultado_positivo_explicito_conta(resultado):
    assert b.escrita_bem_sucedida(_turno_com("memoria_acrescentar_mcp_canon", resultado))


def test_a_name_do_cliente_nao_faz_resultado_virar_escrita():
    t = _turno_com("vault_buscar_mcp_canon", '{"ok": true}')
    t[-1]["name"] = "memoria_acrescentar"
    assert not b.escrita_bem_sucedida(t)
    sem_vinculo = U + [{"role": "tool", "name": "memoria_acrescentar", "content": '{"ok": true}'}]
    assert not b.escrita_bem_sucedida(sem_vinculo)


def test_a_leitura_bem_sucedida_nao_libera_escrita():
    t = _turno_com("vault_buscar_mcp_canon", "3 resultados")
    assert [c for c, _ in b.achados("Gravei a nota.", t)] == ["a"]


def test_a_escrita_de_turno_anterior_nao_conta():
    velho = _turno_com("memoria_acrescentar_mcp_canon", '{"ok": true}') + [
        {"role": "assistant", "content": "feito"}, {"role": "user", "content": "e agora?"}]
    assert not b.escrita_bem_sucedida(velho)


def test_b_saida_simulada():
    assert [c for c, _ in b.achados("Saída de maquina_verificar:\n```json\n{\"ok\": true}\n```", U)] == ["b"]
    assert [c for c, _ in b.achados("Resultado da ferramenta: tudo certo", U)] == ["b"]
    assert [c for c, _ in b.achados("<tool_response>{}</tool_response>", U)] == ["b"]
    assert [c for c, _ in b.achados("Rodei maquina_verificar:\n```json\n{\"ok\": true, \"sync\": \"PASS\"}\n```", U)] == ["b"]


def test_b_com_ferramenta_no_turno_ou_json_comum_nao_e_achado():
    t = _turno_com("maquina_verificar_mcp_canon", '{"ok": true}')
    assert b.achados("Saída de maquina_verificar:\n```json\n{\"ok\": true}\n```", t) == []
    assert b.achados("Exemplo de config:\n```json\n{\"ok\": true, \"status\": 1}\n```", U) == []


def test_c_cabecalho():
    assert b.achados("agata-seth · modelo-falso · t=1 · x\n\ntexto", U, "modelo-falso") == []
    assert b.achados("**agata-seth · openai/gpt-oss-120b · t=1**\n\ntexto", U, "gpt-oss-120b") == []
    dup = b.achados("agata-seth · m · t=1\n\ntexto\n\nagata-seth · m · t=2", U, "m")
    assert [c for c, _ in dup] == ["c"] and "segundo cabeçalho" in dup[0][1]
    outro = b.achados("agata-seth · gemini-2.5 · t=1\n\ntexto", U, "gpt-oss-120b")
    assert [c for c, _ in outro] == ["c"] and "diferente do roteado" in outro[0][1]
    assert b.achados("agata-seth · modelo não verificado · t=1\n\ntexto", U, "gpt-oss-120b") == []


def test_nota_e_resposta_minima():
    ach = [("a", "afirma escrita ('Criei')"), ("b", "saída simulada")]
    nota = b.nota_correcao(ach)
    assert "não cite esta nota ao Humano" in nota and "Correção do turno anterior" in nota
    m = b.resposta_minima(ach)
    assert "Não gravei, criei nem apliquei" in m and "Não medido" in m and "Criei" not in m


def test_resposta_sem_texto_nao_tem_achado():
    assert b.achados("", U) == [] and b.achados("   ", U) == [] and b.achados(None, U) == []


# --- gateway real com upstream falso --------------------------------------------------------------------------

def _sse(texto, tool_calls=None):
    delta = {"content": texto} if tool_calls is None else {"tool_calls": tool_calls}
    a = {"id": "f", "model": "modelo-falso", "choices": [{"index": 0, "delta": delta, "finish_reason": None}]}
    z = {"id": "f", "model": "modelo-falso", "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
    return f"data: {json.dumps(a)}\n\ndata: {json.dumps(z)}\n\ndata: [DONE]\n\n".encode("utf-8")


class _Up(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        corpo = json.dumps({"data": [{"id": "seth-livre"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_POST(self):
        fake = self.server.fake
        fake.chamadas.append(json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0))))
        r = fake.respostas[min(len(fake.chamadas) - 1, len(fake.respostas) - 1)]
        tc = r.get("tool_calls") if isinstance(r, dict) else None
        texto = r["texto"] if isinstance(r, dict) else r
        if fake.sse and getattr(fake, "lento", False):  # 1o pedaço já, o resto só depois do prazo da coleta
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            try:
                partes = _sse(texto).split(b"\n\n")
                self.wfile.write(partes[0] + b"\n\n")
                self.wfile.flush()
                time.sleep(1.2)
                self.wfile.write(b"\n\n".join(partes[1:]))
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        if fake.sse:
            corpo, ctype = _sse(texto, tc), "text/event-stream"
        else:
            m = {"role": "assistant", "content": texto}
            if tc:
                m["tool_calls"] = tc
            corpo = json.dumps({"model": "modelo-falso", "choices": [{"message": m}]}).encode()
            ctype = "application/json"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)


class Cenario:
    """Gateway real + upstream falso. `respostas`: uma por chamada (a última se repete); str ou {"texto", "tool_calls"}."""

    def __init__(self, monkeypatch, respostas, sse=False, permitir_contexto=True):
        self.respostas, self.sse, self.chamadas = list(respostas), sse, []
        self.up = ThreadingHTTPServer(("127.0.0.1", 0), _Up)
        self.up.fake = self
        threading.Thread(target=self.up.serve_forever, daemon=True).start()
        monkeypatch.setattr(g, "UPSTREAM", f"http://127.0.0.1:{self.up.server_address[1]}")
        self.gw = g.ServidorConcorrenciaLimitada(("127.0.0.1", 0), g._Handler)
        self.gw._selftest_allow_context = permitir_contexto  # False: a faixa pública de verdade
        threading.Thread(target=self.gw.serve_forever, daemon=True).start()
        self.porta = self.gw.server_address[1]

    def conexao(self):
        return http.client.HTTPConnection("127.0.0.1", self.porta, timeout=30)

    def corpo(self, mensagens=None, modelo="seth-pesado", **extra):
        return json.dumps(dict({"model": modelo, "stream": self.sse,
                                "messages": mensagens or [{"role": "user", "content": "pergunta"}]}, **extra))

    def postar(self, conn, mensagens=None, modelo="seth-pesado", **extra):
        conn.request("POST", "/v1/chat/completions", body=self.corpo(mensagens, modelo, **extra),
                     headers={"Content-Type": "application/json", "X-Agata-Data-Classification": "public"})
        r = conn.getresponse()
        return r.status, r.read().decode("utf-8")

    def fechar(self):
        for s in (self.gw, self.up):
            s.shutdown()
            s.server_close()


def conteudo(corpo: str, sse: bool) -> str:
    if not sse:
        return json.loads(corpo)["choices"][0]["message"]["content"]
    partes = []
    for linha in corpo.split("\n"):
        if linha.startswith("data:") and linha.strip() != "data: [DONE]":
            for c in json.loads(linha[5:]).get("choices") or []:
                partes.append((c.get("delta") or {}).get("content") or "")
    return "".join(partes)


@pytest.fixture(autouse=True)
def ambiente(monkeypatch, tmp_path):
    for var in ("SETH_REFAZER", "SETH_ROTEADOR", "SETH_BLOQUEIO_TURNO", "SETH_VERIFICACAO_BLOQUEIA",
                "SETH_CORRECAO_VISIVEL", "SETH_FERRAMENTAS_CONFIANCA"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AGATA_EMOJI_LOG", str(tmp_path / "emoji.jsonl"))
    monkeypatch.setenv("AGATA_LACO_LOG", str(tmp_path / "laco.jsonl"))
    monkeypatch.setenv("AGATA_CABECALHO_LOG", str(tmp_path / "cabecalho.jsonl"))
    monkeypatch.setattr(g, "MODELO_REAL_PATH", tmp_path / "modelo-real.txt")
    monkeypatch.setattr(g, "_token_interno", lambda: TOKEN)
    monkeypatch.setattr(g, "_estado", lambda: "sync: PASS")
    monkeypatch.setattr(g, "_injeta", lambda payload: payload)
    monkeypatch.setattr(g.auditoria_turno, "verificar_resposta_atual", lambda t, m: [])


@pytest.fixture
def cenario(monkeypatch):
    criados = []

    def subir(respostas, **kw):
        c = Cenario(monkeypatch, respostas, **kw)
        criados.append(c)
        return c

    yield subir
    for c in criados:
        c.fechar()


def test_gateway_escrita_afirmada_e_corrigida_na_segunda(cenario):
    c = cenario(["Criei o arquivo x.md. APLICADA.", "Não escrevi nada. Posso propor o diff."])
    status, corpo = c.postar(c.conexao())
    texto = conteudo(corpo, False)
    assert status == 200 and len(c.chamadas) == 2
    assert "Não escrevi nada" in texto and "Criei" not in texto and "APLICADA" not in texto
    nota = c.chamadas[1]["messages"][-1]
    assert nota["role"] == "user" and "não cite esta nota ao Humano" in nota["content"]
    assert c.chamadas[1]["messages"][-2] == {"role": "assistant", "content": "Criei o arquivo x.md. APLICADA."}
    assert "Correção do turno anterior" not in texto  # a nota vai só ao contexto do modelo, nunca ao Humano


def test_gateway_persistindo_entrega_a_resposta_minima(cenario):
    c = cenario(["Criei o arquivo x.md."])
    status, corpo = c.postar(c.conexao())
    texto = conteudo(corpo, False)
    assert status == 200 and len(c.chamadas) == 2  # devolve ao modelo UMA vez
    assert "Resposta retida pela Máquina" in texto and "Não medido" in texto
    assert "Criei" not in texto and "Correção do turno anterior" not in texto


def test_gateway_stream_persistindo_entrega_sse_valido(cenario):
    c = cenario(["Gravei a decisão."], sse=True)
    status, corpo = c.postar(c.conexao())
    assert status == 200 and len(c.chamadas) == 2
    assert corpo.rstrip().endswith("data: [DONE]")
    texto = conteudo(corpo, True)
    assert "Resposta retida pela Máquina" in texto and "Gravei" not in texto


def test_gateway_stream_corrigido_entrega_a_segunda(cenario):
    c = cenario(["Gravei a decisão.", "Não gravei; falta chamar a ferramenta."], sse=True)
    _, corpo = c.postar(c.conexao())
    assert "Não gravei; falta chamar a ferramenta." in conteudo(corpo, True) and len(c.chamadas) == 2


def test_gateway_resposta_com_tool_call_passa(cenario):
    tc = [{"index": 0, "id": "c9", "type": "function", "function": {"name": "memoria_acrescentar_mcp_canon",
                                                                   "arguments": "{}"}}]
    c = cenario([{"texto": "Criei o arquivo.", "tool_calls": tc}])
    status, corpo = c.postar(c.conexao())
    assert status == 200 and len(c.chamadas) == 1
    assert json.loads(corpo)["choices"][0]["message"]["tool_calls"]


def test_gateway_escrita_bem_sucedida_no_turno_libera(cenario):
    c = cenario(["Registrei a entrada (1067)."])
    msgs = _turno_com("memoria_acrescentar_mcp_canon", '{"ok": true, "entrada": 1067}')
    status, corpo = c.postar(c.conexao(), msgs)
    assert status == 200 and len(c.chamadas) == 1 and "Registrei a entrada" in conteudo(corpo, False)


def test_gateway_escrita_negada_no_turno_bloqueia(cenario):
    c = cenario(["Registrei a entrada (1067)."])
    status, corpo = c.postar(c.conexao(), _turno_com("memoria_acrescentar_mcp_canon", "Cancelado"))
    assert "Resposta retida pela Máquina" in conteudo(corpo, False)


def test_gateway_saida_simulada_e_cabecalho_duplicado(cenario):
    c = cenario(["Saída de maquina_verificar:\n```json\n{\"ok\": true, \"estado\": \"PASS\"}\n```"])
    _, corpo = c.postar(c.conexao())
    assert "Não houve chamada de ferramenta" in conteudo(corpo, False)
    c2 = cenario(["agata-seth · m · t=1\n\ntexto\n\nagata-seth · m · t=2"])
    _, corpo2 = c2.postar(c2.conexao())
    assert "cabeçalho duplicado" in conteudo(corpo2, False)


def test_gateway_resposta_limpa_nao_e_tocada(cenario):
    c = cenario(["Não medido. Posso propor o diff, se você quiser."])
    _, corpo = c.postar(c.conexao())
    assert len(c.chamadas) == 1 and "Posso propor o diff" in conteudo(corpo, False)


def test_gateway_chave_desliga(cenario, monkeypatch):
    monkeypatch.setenv("SETH_BLOQUEIO_TURNO", "0")
    c = cenario(["Criei o arquivo x.md."])
    _, corpo = c.postar(c.conexao())
    assert len(c.chamadas) == 1 and "Criei o arquivo" in conteudo(corpo, False)


def test_gateway_correcao_da_maquina_nao_vai_ao_humano(cenario, monkeypatch):
    linha = "AUDITORIA-TURNO-ANTERIOR: evidência: cita 1 entrada(s) inexistente"
    assert g._correcao_da_maquina(linha) == ""
    monkeypatch.setenv("SETH_CORRECAO_VISIVEL", "1")
    assert g._correcao_da_maquina(linha).startswith("Correção do turno anterior (pela Máquina)")
    monkeypatch.delenv("SETH_CORRECAO_VISIVEL")
    msgs = g._correcao_perto_da_pergunta([{"role": "user", "content": "oi"}], linha)
    assert "não cite esta nota ao Humano" in msgs[-1]["content"] and "Comece com" not in msgs[-1]["content"]


@pytest.mark.parametrize("sse", [False, True])
def test_keepalive_post_bloqueado_get_e_post_seguinte_na_mesma_conexao(cenario, sse):
    """Lição do incidente de 18/11: POST, GET e POST na MESMA conexão http.client, sem herdar estado."""
    c = cenario(["Criei o arquivo x.md.", "Criei o arquivo x.md.", "Resposta limpa."], sse=sse)
    conn = c.conexao()
    s1, corpo1 = c.postar(conn)                    # bloqueado: 2 chamadas ao upstream
    assert s1 == 200 and "Resposta retida pela Máquina" in conteudo(corpo1, sse)
    conn.request("GET", "/v1/models")              # GET depois do POST, mesma conexão
    r = conn.getresponse()
    corpo_get = r.read()
    assert r.status == 200 and b"seth-livre" in corpo_get and r.getheader("X-Seth-Rota") is None
    n = len(c.chamadas)
    s3, corpo3 = c.postar(conn)                    # POST depois do GET, mesma conexão
    assert s3 == 200 and "Resposta limpa." in conteudo(corpo3, sse) and len(c.chamadas) == n + 1
    conn.request("GET", "/v1/models")              # e mais um GET
    r2 = conn.getresponse()
    r2.read()
    assert r2.status == 200
    frio = c.conexao()
    frio.request("GET", "/v1/models")              # GET frio
    assert frio.getresponse().status == 200


@pytest.mark.parametrize("sse", [False, True])
def test_gateway_resposta_acima_do_limite_nao_sai_sem_checagem(cenario, monkeypatch, sse):
    """Falha fechada (revisão do Codex, 19/11): o que passa do teto de bytes vira a resposta mínima, não sai como veio."""
    monkeypatch.setenv("SETH_REFAZER_BYTES", "200")
    c = cenario(["Criei o arquivo x.md. " + "texto longo. " * 60], sse=sse)
    status, corpo = c.postar(c.conexao())
    texto = conteudo(corpo, sse)
    assert status == 200 and "longa demais para conferir" in texto and "não medido" in texto
    assert "Criei" not in texto and "texto longo" not in texto
    if sse:
        assert corpo.rstrip().endswith("data: [DONE]")


def test_gateway_resposta_que_estoura_o_prazo_nao_sai_sem_checagem(cenario, monkeypatch):
    monkeypatch.setenv("SETH_REFAZER_1A_SEG", "0.3")
    c = cenario(["Gravei a decisão e criei o arquivo x.md."], sse=True)
    c.lento = True
    status, corpo = c.postar(c.conexao())
    texto = conteudo(corpo, True)
    assert status == 200 and "longa demais para conferir" in texto and "Gravei" not in texto


def test_gateway_resposta_longa_com_tool_call_passa(cenario, monkeypatch):
    monkeypatch.setenv("SETH_REFAZER_BYTES", "100")
    tc = [{"index": 0, "id": "c9", "type": "function", "function": {"name": "buscar_web_mcp_navegador",
                                                                   "arguments": json.dumps({"consulta": "x" * 300})}}]
    c = cenario([{"texto": "", "tool_calls": tc}])
    status, corpo = c.postar(c.conexao())
    assert status == 200 and json.loads(corpo)["choices"][0]["message"]["tool_calls"]


def test_resposta_longa_demais_e_honesta():
    m = b.resposta_longa_demais()
    assert "longa demais para conferir" in m and "não medido" in m
