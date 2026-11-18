"""Testes da base do roteador (17/11/2026, proposta seth-base-17-11). Sem rede, sem provedor.

Cobre: ferramenta escrita como texto (regra estrita e detecção SSE, com as revisões do Codex), cabeçalho da Máquina
(prefixo, duplicata, resposta correta, SSE tardio, cabeçalho tardio contra o do modelo), served_by (JSON, chunk SSE,
log), a chave SETH_TOOLCALL_TEXTO e o modo do roteador.
Rodar: pytest -q redesign/router/test_seth_base.py
"""
import json
import os
import queue
import re
import sys
import time
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import seth_gateway as g  # noqa: E402

CAB = ("agata-seth · modelo: x (nuvem) · sync: PASS · 2026-11-17 18:00 -0300 (relógio da Máquina)\n"
       "Última entrada: (1) x\npronto.\n\n")
TOOLS = frozenset({"ler_arquivo", "buscar"})
BLOCO = ("<tool_call>\n<function=ler_arquivo>\n<parameter=caminho>\nnotas.md\n</parameter>\n"
         "<parameter=linhas>\n10\n</parameter>\n</function>\n</tool_call>")  # só o bloco, sem texto em volta
BLOCO_BUSCAR = ('<tool_call>{"name": "buscar", "arguments": {"q": "agata"}}</tool_call>')
QWEN = BLOCO + "\nFeito."  # com texto depois do bloco: a regra estrita não converte


def _resposta(content, tool_calls=None, model="openai/gpt-oss-120b"):
    m = {"role": "assistant", "content": content}
    if tool_calls is not None:
        m["tool_calls"] = tool_calls
    return json.dumps({"id": "c1", "model": model,
                       "choices": [{"index": 0, "message": m, "finish_reason": "stop"}]}).encode("utf-8")


def _linha_sse(delta, model="m", finish=None):
    o = {"id": "s", "model": model, "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
    return b"data: " + json.dumps(o, ensure_ascii=False).encode("utf-8") + b"\n\n"


FIM = _linha_sse({}, finish="stop") + b"data: [DONE]\n\n"          # fim normal do upstream
KA = b'data: {"id":"chatcmpl-keepalive","model":"keepalive","choices":[{"delta":{},"finish_reason":null}]}\n\n'


class _LeitorFalso:
    """Imita _Leitor: entrega os pedaços em ordem, depois b"" (fim). Um item Exception é levantado (prazo ou upstream)."""

    def __init__(self, itens):
        self._itens = list(itens)

    def ler(self, timeout):
        item = self._itens.pop(0) if self._itens else b""
        if isinstance(item, BaseException):
            raise item
        return item


def _h_fake():
    """Handler sem socket: só os atributos que _escrever_linhas_completas usa. Guarda o que seria enviado."""
    h = g._Handler.__new__(g._Handler)
    h._resgate, h._emoji_estados, h._cab_estados, h._laco_estados = {}, {}, {}, {}
    h._cab_injetado = CAB
    h._cab_pendente = CAB
    h._served_by = None
    h._enviado = []
    h._enviar = lambda s: h._enviado.append(s)
    return h


def _chamadas_do_stream(raw: bytes):
    """Nomes e argumentos das tool_calls de um stream SSE já montado (para checar o que o cliente recebe)."""
    nomes, args, fins = [], "", []
    for linha in raw.split(b"\n"):
        if not linha.startswith(b"data: {"):
            continue
        ch = json.loads(linha[5:])["choices"][0]
        for c in ch["delta"].get("tool_calls", []):
            nomes.append(c["function"]["name"])
            args += c["function"].get("arguments", "")
        if ch.get("finish_reason"):
            fins.append(ch["finish_reason"])
    return nomes, args, fins


# --- modo do roteador -------------------------------------------------------------------------------------

def test_modo_roteador_padrao_e_legado(monkeypatch):
    monkeypatch.delenv("SETH_ROTEADOR", raising=False)
    assert g._modo_roteador() == "legado"
    monkeypatch.setenv("SETH_ROTEADOR", "   ")
    assert g._modo_roteador() == "legado"
    monkeypatch.setenv("SETH_ROTEADOR", " Sombra ")
    assert g._modo_roteador() == "sombra"
    monkeypatch.setenv("SETH_ROTEADOR", "capacidade:4")
    assert g._modo_roteador() == "capacidade:4"


# --- parser de tool_call em texto: formato e nomes --------------------------------------------------------

def test_parser_xml_qwen_so_bloco_converte():
    chamadas = g._extrair_tool_calls(BLOCO, TOOLS)
    assert chamadas is not None and len(chamadas) == 1
    c = chamadas[0]
    assert re.fullmatch(r"call_[0-9a-f]{8}", c["id"])
    assert c["type"] == "function" and c["function"]["name"] == "ler_arquivo"
    assert json.loads(c["function"]["arguments"]) == {"caminho": "notas.md", "linhas": 10}


def test_parser_json_converte():
    chamadas = g._extrair_tool_calls(BLOCO_BUSCAR, TOOLS)
    assert chamadas[0]["function"]["name"] == "buscar"
    assert json.loads(chamadas[0]["function"]["arguments"]) == {"q": "agata"}


def test_parser_json_com_arguments_em_texto_converte():
    t = '<tool_call>{"name": "buscar", "arguments": "{\\"q\\": \\"x\\"}"}</tool_call>'
    assert json.loads(g._extrair_tool_calls(t, TOOLS)[0]["function"]["arguments"]) == {"q": "x"}


def test_parser_nome_fora_de_tools_nao_converte():
    t = '<tool_call>{"name": "apagar_tudo", "arguments": {}}</tool_call>'
    assert g._extrair_tool_calls(t, TOOLS) is None
    assert g._extrair_tool_calls(BLOCO, frozenset({"outra"})) is None


def test_parser_sem_tools_nao_converte():
    assert g._extrair_tool_calls(BLOCO, frozenset()) is None
    corpo = _resposta(BLOCO)
    assert g._tool_calls_do_json(corpo, frozenset()) == corpo


def test_parser_bloco_quebrado_ou_sem_bloco_nao_converte():
    assert g._extrair_tool_calls("<tool_call>{nao é json</tool_call>", TOOLS) is None
    assert g._extrair_tool_calls("<tool_call>\n<function=buscar>\n<parameter=q>\nx", TOOLS) is None  # sem fechar
    assert g._extrair_tool_calls("texto normal, sem bloco nenhum", TOOLS) is None


def test_parser_nao_mexe_em_mensagem_que_ja_tem_tool_calls():
    tc = [{"id": "x", "type": "function", "function": {"name": "buscar", "arguments": "{}"}}]
    corpo = _resposta(BLOCO, tool_calls=tc)
    assert g._tool_calls_do_json(corpo, TOOLS) == corpo


def test_parser_nao_json_grava_tool_calls_content_vazio_e_finish():
    o = json.loads(g._tool_calls_do_json(_resposta(BLOCO), TOOLS))
    ch = o["choices"][0]
    assert ch["finish_reason"] == "tool_calls"
    assert ch["message"]["tool_calls"][0]["function"]["name"] == "ler_arquivo"
    assert ch["message"]["content"] == ""


def test_nomes_de_tools_nos_dois_formatos():
    tools = [{"type": "function", "function": {"name": "a"}}, {"name": "b"}, "lixo"]
    assert g._nomes_de_tools(tools) == frozenset({"a", "b"})
    assert g._nomes_de_tools(None) == frozenset()


# --- regra estrita (revisão do Codex, rodada 2, achado 2 e a regra nova) ----------------------------------

def test_regra_estrita_texto_depois_do_bloco_nao_converte():
    assert g._extrair_tool_calls(QWEN, TOOLS) is None
    corpo = _resposta(QWEN)
    assert g._tool_calls_do_json(corpo, TOOLS) == corpo


def test_c2_chamada_valida_mais_exemplo_e_outro_bloco_nao_gera_duas():
    t = BLOCO + "\nExemplo:\n" + BLOCO_BUSCAR
    assert g._extrair_tool_calls(t, TOOLS) is None
    corpo = _resposta(t)
    assert g._tool_calls_do_json(corpo, TOOLS) == corpo
    assert g._sse_tool_calls(_linha_sse({"content": t}, finish="stop") + b"data: [DONE]\n\n", TOOLS) is None


def test_c2_segundo_bloco_em_cerca_sem_fechar_nao_converte():
    assert g._extrair_tool_calls(BLOCO + "\n```\n" + BLOCO, TOOLS) is None
    assert g._extrair_tool_calls(BLOCO + "\n~~~\n" + BLOCO, TOOLS) is None
    assert g._extrair_tool_calls(BLOCO + "\n```xml\n" + BLOCO_BUSCAR, TOOLS) is None


def test_c2_segundo_bloco_em_cerca_fechada_nao_converte():
    assert g._extrair_tool_calls(BLOCO + "\n```\n" + BLOCO + "\n```", TOOLS) is None


def test_r2_exemplo_em_cerca_de_codigo_nao_converte():
    exemplo = "Exemplo:\n```xml\n" + BLOCO + "\n```"
    assert g._extrair_tool_calls(exemplo, TOOLS) is None
    corpo = _resposta(exemplo)
    assert g._tool_calls_do_json(corpo, TOOLS) == corpo
    assert g._sse_tool_calls(_linha_sse({"content": exemplo}, finish="stop") + b"data: [DONE]\n\n", TOOLS) is None


def test_r2_texto_antes_do_bloco_nao_converte():
    assert g._extrair_tool_calls("Vou ler o arquivo.\n" + BLOCO, TOOLS) is None


def test_c2_dois_blocos_so_com_espaco_entre_eles_convertem_os_dois():
    chamadas = g._extrair_tool_calls(BLOCO + "\n\n  " + BLOCO_BUSCAR + "\n", TOOLS)
    assert [c["function"]["name"] for c in chamadas] == ["ler_arquivo", "buscar"]


def test_r2_cabecalho_da_maquina_antes_do_bloco_nao_impede():
    chamadas = g._extrair_tool_calls(CAB + BLOCO, TOOLS)
    assert chamadas is not None and len(chamadas) == 1


# --- stream: só converte com o fim normal do upstream (revisão do Codex, achado NOVO) ---------------------

def test_stream_sem_done_nao_converte():
    buf = _linha_sse({"content": BLOCO}, finish="stop")  # sem data: [DONE]
    assert g._sse_tool_calls(buf, TOOLS) is None


def test_stream_sem_finish_reason_nao_converte():
    buf = _linha_sse({"content": BLOCO}) + b"data: [DONE]\n\n"  # sem finish_reason do upstream
    assert g._sse_tool_calls(buf, TOOLS) is None


def test_stream_timeout_com_primeira_chamada_completa_passa_como_chegou():
    buf = _linha_sse({"content": BLOCO + "\n<tool_call>\n<function=buscar>\n<parameter=q>\nagat"})
    saida, _ = g._converter_sse_stream(buf, _LeitorFalso([queue.Empty()]), TOOLS)
    assert saida == buf
    assert b"tool_calls" not in saida and b"[DONE]" not in saida


def test_stream_erro_do_upstream_passa_como_chegou():
    buf = _linha_sse({"content": BLOCO})
    saida, _ = g._converter_sse_stream(buf, _LeitorFalso([RuntimeError("upstream caiu")]), TOOLS)
    assert saida == buf


def test_stream_fim_sem_done_passa_como_chegou():
    buf = _linha_sse({"content": BLOCO})
    fim_sem_done = _linha_sse({}, finish="stop")
    saida, _ = g._converter_sse_stream(buf, _LeitorFalso([fim_sem_done]), TOOLS)
    assert saida == buf + fim_sem_done


def test_stream_fim_normal_converte_e_fecha_com_done():
    buf = _linha_sse({"content": BLOCO[:30]})
    saida, leitor = g._converter_sse_stream(buf, _LeitorFalso([_linha_sse({"content": BLOCO[30:]}), FIM]), TOOLS)
    nomes, args, fins = _chamadas_do_stream(saida)
    assert nomes == ["ler_arquivo"] and fins == ["tool_calls"] and saida.endswith(b"data: [DONE]\n\n")
    assert json.loads(args) == {"caminho": "notas.md", "linhas": 10}
    assert isinstance(leitor, g._LeitorVazio)


# --- detecção SSE (revisão do Codex, achado 3 e a regra nova) ---------------------------------------------

def test_sse_detecta_texto_que_comeca_com_tool_call():
    assert g._texto_inicia_tool_call(_linha_sse({"content": "  <tool_call>\n<function=buscar>"}))
    assert not g._texto_inicia_tool_call(_linha_sse({"content": "Oi, <tool_call> no meio"}))


def test_r3_prefixo_fragmentado_espera_antes_de_decidir():
    assert g._decisao_tool_call(_linha_sse({"content": "<tool"})) == "mais"
    assert g._decisao_tool_call(_linha_sse({"content": "<tool"}) + _linha_sse({"content": "_call>"})) == "sim"
    assert g._decisao_tool_call(_linha_sse({"content": "<tool"})
                                + _linha_sse({"content": " ing a fazer agora"})) == "nao"
    assert g._decisao_tool_call(_linha_sse({"content": "Oi"})) == "mais"  # menos de 11 caracteres sem espaços
    assert g._decisao_tool_call(_linha_sse({"content": "Oi, tudo bem por aqui"})) == "nao"
    assert g._decisao_tool_call(KA) == "nao"


def test_r3_fragmentado_em_tool_e_call_converte_no_fim():
    buf = _linha_sse({"content": "<tool"})
    saida, _ = g._converter_sse_stream(
        buf, _LeitorFalso([_linha_sse({"content": "_call>\n<function=buscar>\n<parameter=q>\nagata\n</parameter>\n"
                                                   "</function>\n</tool_call>"}), FIM]), TOOLS)
    nomes, args, fins = _chamadas_do_stream(saida)
    assert nomes == ["buscar"] and json.loads(args) == {"q": "agata"} and fins == ["tool_calls"]


def test_c3_cabecalho_completo_em_chunk_separado_nao_decide_nao():
    cab_chunk = _linha_sse({"content": CAB})
    assert g._decisao_tool_call(cab_chunk) == "mais"
    assert g._decisao_tool_call(cab_chunk + _linha_sse({"content": BLOCO})) == "sim"
    saida, _ = g._converter_sse_stream(cab_chunk, _LeitorFalso([_linha_sse({"content": BLOCO}), FIM]), TOOLS)
    nomes, _, fins = _chamadas_do_stream(saida)
    assert nomes == ["ler_arquivo"] and fins == ["tool_calls"]


def test_c3_primeiro_fragmento_agata_nao_decide_nao():
    assert g._decisao_tool_call(_linha_sse({"content": "agata"})) == "mais"
    assert g._decisao_tool_call(_linha_sse({"content": "agata-seth · x · t=2\n"})) == "mais"
    buf = _linha_sse({"content": "agata"})
    saida, _ = g._converter_sse_stream(
        buf, _LeitorFalso([_linha_sse({"content": "-seth · modelo: x · t=2\n" + BLOCO}), FIM]), TOOLS)
    nomes, _, _ = _chamadas_do_stream(saida)
    assert nomes == ["ler_arquivo"]


def test_stream_texto_normal_passa_sem_segurar():
    buf = _linha_sse({"content": "Oi, tudo bem por aqui?"})
    saida, leitor = g._converter_sse_stream(buf, _LeitorFalso([_linha_sse({"content": " Sim."})]), TOOLS)
    assert saida == buf  # decidido "nao" já na 1ª leitura: não foi segurado
    assert not isinstance(leitor, g._LeitorVazio)


# --- cabeçalho da Máquina (item 2) ------------------------------------------------------------------------

def test_cabecalho_prefixa_quando_falta(monkeypatch):
    monkeypatch.delenv("SETH_CABECALHO_UNICO", raising=False)
    assert g._cabecalho_unico_texto("Corpo.", CAB) == CAB + "Corpo."


def test_cabecalho_nao_mexe_quando_esta_correto(monkeypatch):
    monkeypatch.delenv("SETH_CABECALHO_UNICO", raising=False)
    texto = CAB + "Corpo.\nSegunda linha."
    assert g._cabecalho_unico_texto(texto, CAB) == texto


DUP = "Agata · modelo: x · sync: PASS · HEAD=4975b44 · 2026-10-17 11:56 -0300\nÚltima entrada: (741) x\npronto.\n"


def test_cabecalho_copia_no_bloco_inicial_sai(monkeypatch):
    monkeypatch.delenv("SETH_CABECALHO_UNICO", raising=False)
    assert g._cabecalho_unico_texto(CAB + DUP + "Corpo.", CAB) == CAB + "Corpo."


def test_cabecalho_depois_do_1o_paragrafo_nao_mexe(monkeypatch):
    # antes (rodada 2) a cópia era apagada aqui também; o Codex (r3) reprovou: só o bloco inicial é tocado
    monkeypatch.delenv("SETH_CABECALHO_UNICO", raising=False)
    texto = CAB + "Corpo.\n" + DUP + "Fim."
    assert g._cabecalho_unico_texto(texto, CAB) == texto


def test_cabecalho_exemplo_em_cerca_nao_some(monkeypatch):
    # reprodução do Codex (r3): "agata · exemplo" e "pronto." dentro de cerca sumiam
    monkeypatch.delenv("SETH_CABECALHO_UNICO", raising=False)
    texto = CAB + "Exemplo:\n```text\nagata · exemplo\npronto.\n```\nFim."
    assert g._cabecalho_unico_texto(texto, CAB) == texto


def test_cabecalho_linha_agata_sem_rodape_no_inicio_nao_some(monkeypatch):
    monkeypatch.delenv("SETH_CABECALHO_UNICO", raising=False)
    texto = CAB + "agata · exemplo\nlinha seguinte"
    assert g._cabecalho_unico_texto(texto, CAB) == texto


def test_cabecalho_resposta_sem_cabecalho_do_modelo_fica_igual(monkeypatch):
    monkeypatch.delenv("SETH_CABECALHO_UNICO", raising=False)
    texto = CAB + "Resposta com\n\nvárias linhas."
    assert g._cabecalho_unico_texto(texto, CAB) == texto


# --- revisão do Codex (r3, achado 1): escolhas diferentes não se misturam, e não convertem -----------------

def _evento_escolhas(*pares):
    """Um evento SSE com uma escolha por (index, conteúdo)."""
    escolhas = [{"index": i, "delta": {"content": c}, "finish_reason": None} for i, c in pares]
    return b"data: " + json.dumps({"id": "s", "model": "m", "choices": escolhas}).encode() + b"\n\n"


def test_r3_escolhas_diferentes_no_mesmo_evento_nao_convertem():
    buf = _evento_escolhas((0, BLOCO), (1, BLOCO_BUSCAR)) + FIM
    assert g._sse_tool_calls(buf, TOOLS) is None
    saida, _ = g._converter_sse_stream(buf, _LeitorFalso([]), TOOLS)
    assert saida == buf  # passa como chegou, sem duas chamadas na mesma escolha


def test_r3_escolhas_diferentes_em_eventos_separados_nao_convertem():
    buf = _linha_sse({"content": BLOCO}) + b"data: " + json.dumps(
        {"id": "s", "model": "m", "choices": [{"index": 1, "delta": {"content": BLOCO_BUSCAR}, "finish_reason": None}]}
    ).encode() + b"\n\n" + FIM
    assert g._sse_tool_calls(buf, TOOLS) is None


def test_r3_so_escolha_index_1_nao_converte():
    buf = _evento_escolhas((1, BLOCO)) + FIM
    assert g._sse_tool_calls(buf, TOOLS) is None


# --- revisão do Codex (r4): um evento com mais de uma escolha não converte, nem com index 0 nem sem index ----

def test_r4_duas_escolhas_index_0_no_mesmo_evento_nao_convertem():
    # reprodução 1 do Codex (r4): as duas escolhas têm index 0; antes o conteúdo das duas era somado e convertido
    buf = _evento_escolhas((0, BLOCO), (0, BLOCO_BUSCAR)) + FIM
    assert g._sse_tool_calls(buf, TOOLS) is None
    saida, _ = g._converter_sse_stream(buf, _LeitorFalso([]), TOOLS)
    assert saida == buf  # passa como chegou


def test_r4_duas_escolhas_sem_index_no_mesmo_evento_nao_convertem():
    # reprodução 2 do Codex (r4): escolhas sem o campo index (contam como 0); mesmo efeito do caso anterior
    evento = b"data: " + json.dumps({"id": "s", "model": "m", "choices": [
        {"delta": {"content": BLOCO}, "finish_reason": None},
        {"delta": {"content": BLOCO_BUSCAR}, "finish_reason": None}]}).encode() + b"\n\n"
    buf = evento + FIM
    assert g._sse_tool_calls(buf, TOOLS) is None
    saida, _ = g._converter_sse_stream(buf, _LeitorFalso([]), TOOLS)
    assert saida == buf  # passa como chegou


def test_r3_nao_stream_com_duas_escolhas_nao_converte():
    corpo = json.dumps({"id": "c", "model": "m", "choices": [
        {"index": 0, "message": {"role": "assistant", "content": BLOCO}, "finish_reason": "stop"},
        {"index": 1, "message": {"role": "assistant", "content": BLOCO_BUSCAR}, "finish_reason": "stop"}]}).encode()
    assert g._tool_calls_do_json(corpo, TOOLS) == corpo


def test_r3_nao_stream_com_escolha_index_1_nao_converte():
    corpo = json.dumps({"id": "c", "model": "m", "choices": [
        {"index": 1, "message": {"role": "assistant", "content": BLOCO}, "finish_reason": "stop"}]}).encode()
    assert g._tool_calls_do_json(corpo, TOOLS) == corpo


def test_cabecalho_com_flag_desligada_nao_remove_mas_prefixa(monkeypatch):
    monkeypatch.setenv("SETH_CABECALHO_UNICO", "0")
    texto = CAB + "Corpo.\nAgata · x · t=4 · hora\nFim."
    assert g._cabecalho_unico_texto(texto, CAB) == texto
    assert g._cabecalho_unico_texto("Corpo.", CAB) == CAB + "Corpo."


def test_cabecalho_json_prefixa_e_ignora_resposta_so_de_ferramenta(monkeypatch):
    monkeypatch.delenv("SETH_CABECALHO_UNICO", raising=False)
    o = json.loads(g._cabecalho_unico_json(_resposta("Corpo."), CAB))
    assert o["choices"][0]["message"]["content"] == CAB + "Corpo."
    so_ferramenta = _resposta("", tool_calls=[{"id": "x", "type": "function",
                                               "function": {"name": "buscar", "arguments": "{}"}}])
    assert g._cabecalho_unico_json(so_ferramenta, CAB) == so_ferramenta


def test_cabecalho_sse_tardio_sai_antes_do_primeiro_texto():
    linha_texto = b'data: {"id":"s","model":"m","choices":[{"index":0,"delta":{"content":"oi"},"finish_reason":null}]}'
    ch = g._cabecalho_sse_tardio(linha_texto, CAB)
    assert ch is not None and ch.startswith(b"data: ") and ch.endswith(b"\n\n")
    assert json.loads(ch[5:])["choices"][0]["delta"]["content"] == CAB
    so_ferramenta = b'data: {"choices":[{"index":0,"delta":{"tool_calls":[{"index":0}]}}]}'
    assert g._cabecalho_sse_tardio(so_ferramenta, CAB) is None
    assert g._cabecalho_sse_tardio(linha_texto, "") is None


# --- cabeçalho tardio contra o do modelo (revisão do Codex, achado 4) -------------------------------------

def test_r4_cabecalho_tardio_nao_duplica_com_o_do_modelo():
    h = _h_fake()
    modelo = "Agata · modelo: x · sync: PASS · HEAD=4975b44 · 2026-10-17 11:56 -0300\nÚltima entrada: (741) x\npronto.\n\nOi."
    g._Handler._escrever_linhas_completas(h, _linha_sse({"content": modelo}, model="gemini-2.5-flash"))
    texto = g._texto_do_sse(h._enviado)
    assert texto.count("agata-seth ·") == 1 and texto.count("Agata ·") == 0, repr(texto)
    assert texto == CAB + "Oi."
    assert h._cab_pendente == ""


def test_r4_cabecalho_tardio_sem_cabecalho_do_modelo_sai_uma_vez():
    h = _h_fake()
    g._Handler._escrever_linhas_completas(h, _linha_sse({"content": "Oi."}, model="gemini-2.5-flash"))
    assert g._texto_do_sse(h._enviado) == CAB + "Oi."


# --- served_by (item 1) -----------------------------------------------------------------------------------

def test_served_by_sai_do_json():
    assert g._Handler._modelo_de_bytes(_resposta("x", model="openai/gpt-oss-120b")) == "openai/gpt-oss-120b"


def test_served_by_sai_do_primeiro_chunk_sse_e_pula_keepalive():
    sse = (b'data: {"id":"chatcmpl-keepalive","model":"keepalive","choices":[{"delta":{},"finish_reason":null}]}\n\n'
           b'data: {"id":"c2","model":"gemini-2.5-flash","choices":[{"delta":{"content":"oi"}}]}\n\n')
    assert g._Handler._modelo_de_bytes(sse) == "gemini-2.5-flash"


def test_served_by_ausente_fica_none():
    assert g._Handler._modelo_de_bytes(b'data: {"choices":[{"delta":{"content":"oi"}}]}\n\n') is None


def test_log_mostra_served_by_ou_interrogacao(capsys):
    h = types.SimpleNamespace(_rota="seth-livre", path="/v1/chat/completions", _served_by="qwen3.5-9b")
    g._Handler._log(h, "ok", time.monotonic())
    err = capsys.readouterr().err
    assert "served_by=qwen3.5-9b" in err and "rota=seth-livre" in err
    h._served_by = None
    g._Handler._log(h, "upstream HTTP 429", time.monotonic())
    assert "served_by=?" in capsys.readouterr().err


# --- chave SETH_TOOLCALL_TEXTO=0: desliga só o item 3; o cabeçalho continua sempre -------------------------

def test_chave_toolcall_texto_desliga_so_a_conversao(monkeypatch):
    p = {"tools": [{"type": "function", "function": {"name": "buscar"}}]}
    monkeypatch.delenv("SETH_TOOLCALL_TEXTO", raising=False)
    assert g._toolcall_texto_ligado() is True
    assert g._ferramentas_convertiveis(p, False) == frozenset({"buscar"})
    monkeypatch.setenv("SETH_TOOLCALL_TEXTO", "0")
    assert g._toolcall_texto_ligado() is False
    assert g._ferramentas_convertiveis(p, False) == frozenset()
    assert g._cabecalho_unico_texto("Corpo.", CAB) == CAB + "Corpo."
    monkeypatch.delenv("SETH_TOOLCALL_TEXTO", raising=False)
    assert g._ferramentas_convertiveis(p, True) == frozenset()                   # faixa pública
    assert g._ferramentas_convertiveis({**p, "tool_choice": "none"}, False) == frozenset()
