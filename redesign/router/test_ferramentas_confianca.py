"""Testes dos rótulos de ferramenta e da confiança por provedor (19/11/2026). Sem rede e sem provedor.

Cobre: o arquivo real (toda ferramenta que o gateway oferece hoje tem rótulo; segredo não aparece; escrita nunca é de
dado público; provedores batem com a ficha de rotas), a leitura com cache por mtime e a falha fechada, o nome com sufixo
de servidor MCP, o nível por rota (faixa pública, local, filas seth-*, provedor desconhecido), o filtro de ferramentas e
de resultados (acima do nível e com segredo), a faixa pública com ferramenta de dado público, e o gateway real: o que o
upstream recebe, e GET e POST depois de POST na MESMA conexão http.client (lição do incidente de 18/11).
Rodar: pytest -q redesign/router/test_ferramentas_confianca.py
"""
import json
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ferramentas_confianca as fc  # noqa: E402
import seth_gateway as g  # noqa: E402


@pytest.fixture(autouse=True)
def _uso_capivara_em_tmp(tmp_path, monkeypatch):
    """(23/11/2026) O log de uso da Capivara vai para um temporário: teste nunca grava no uso.jsonl real."""
    monkeypatch.setenv("AGATA_CAPIVARA_USO", str(tmp_path / "uso.jsonl"))
    monkeypatch.setattr(g.sombra_capacidade, "_caminho_registro", lambda p=tmp_path / "sem-registro.json": p)  # sem escolha por capacidade
from test_bloqueio_turno import Cenario, ambiente, cenario, conteudo  # noqa: E402,F401  (o mesmo gateway e upstream falsos)

SEGREDO = "sk" + "-" + "TESTEsintetico0123456789abcdefGHIJ"  # montado em tempo de execução: não casa a varredura
OFERECIDAS = {  # as ferramentas que a Seth oferece hoje: canon-mcp, discord, navegador, mais as do servidor MCP do repositório
    "query_canon", "vault_buscar", "vault_consultar", "maquina_verificar", "memoria_acrescentar", "diario_anotar",
    "ler_mensagens", "enviar_mensagem", "navegar", "buscar_web", "ler_pagina", "fechar_navegador", "screenshot",
    "clicar", "preencher", "tool_search", "git_sync", "run_perimetro", "check_citation", "lint_header"}


def _def(nome):
    return {"type": "function", "function": {"name": nome, "parameters": {}}}


def _hist(*pares):
    """pares: (nome, resultado). Cada um vira assistente com tool_calls e a mensagem de resultado."""
    msgs = [{"role": "user", "content": "pergunta"}]
    for i, (nome, res) in enumerate(pares):
        msgs.append({"role": "assistant", "content": "", "tool_calls": [
            {"id": f"c{i}", "type": "function", "function": {"name": nome, "arguments": "{}"}}]})
        msgs.append({"role": "tool", "tool_call_id": f"c{i}", "content": res})
    return msgs


# --- o arquivo real --------------------------------------------------------------------------------------------

def test_toda_ferramenta_oferecida_tem_rotulo_valido():
    d = fc.carregar()
    assert OFERECIDAS <= set(d["ferramentas"])
    for nome, r in d["ferramentas"].items():
        assert r["dado"] in ("publico", "pessoal"), nome       # segredo nunca é rótulo de ferramenta oferecida
        assert r["efeito"] in ("leitura", "escrita"), nome


def test_escrita_nunca_e_de_dado_publico_e_leitura_web_e_publica():
    d = fc.carregar()["ferramentas"]
    assert all(r["dado"] == "pessoal" for r in d.values() if r["efeito"] == "escrita")
    assert all(d[n] == {"dado": "publico", "efeito": "leitura"} for n in ("navegar", "buscar_web", "ler_pagina"))
    assert d["memoria_acrescentar"]["efeito"] == "escrita" and d["clicar"]["efeito"] == "escrita"


def test_provedores_batem_com_a_ficha_de_rotas():
    ficha = json.load(open(os.path.join(os.path.dirname(__file__), "..", "..", "config", "rotas-ficha.json"),
                           encoding="utf-8"))
    d = fc.carregar()
    for r in ficha["rotas"]:
        nivel = fc.nivel_do_provedor(r["provedor"])
        if r["categoria"] == "local":
            assert nivel == "local", r["id"]
        if r["categoria"] == "gratuito":
            assert nivel == "gratuito", r["id"]
        # o nível nunca deixa passar dado que a ficha não permite à rota
        if "pessoal" not in r["classes_permitidas"]:
            assert fc._dado_do_nivel(nivel, d) == "publico", r["id"]


def test_niveis_do_arquivo():
    d = fc.carregar()
    assert fc._dado_do_nivel("local", d) == "pessoal" and fc._dado_do_nivel("pago_sem_treino", d) == "pessoal"
    assert fc._dado_do_nivel("gratuito", d) == "publico" and fc._dado_do_nivel("inexistente", d) == "publico"


# --- nomes, rótulos, níveis ------------------------------------------------------------------------------------

def test_nome_com_sufixo_de_servidor_mcp():
    assert fc.nome_base("vault_buscar_mcp_canon") == "vault_buscar"
    assert fc.nome_base("buscar_web_mcp_navegador") == "buscar_web"
    assert fc.rotulo("buscar_web_mcp_navegador") == {"dado": "publico", "efeito": "leitura"}
    assert fc.rotulo("ferramenta_que_nao_existe") == {"dado": "pessoal", "efeito": "escrita"}  # na dúvida, o restrito


def test_dado_maximo_por_rota():
    assert fc.dado_maximo("seth-livre", True) == "publico"                 # faixa pública = gratuito
    assert fc.dado_maximo("ollama-local/qwen3-30b:latest", False) == "pessoal"
    assert fc.dado_maximo("llamacpp-x", False) == "pessoal"
    assert fc.dado_maximo("seth-pesado", False) == "pessoal"                # fila seth-*: via sanitizador (a confirmar)
    assert fc.dado_maximo("gemini/gemini-2.5-flash", False) == "publico"   # provedor gratuito
    assert fc.dado_maximo("nuvem-nova/modelo", False) == "publico"         # provedor desconhecido: o mais restrito
    assert fc.dado_maximo("", False) == "publico"


def test_segredo_nunca_cabe():
    assert not fc.cabe("segredo", "pessoal") and not fc.cabe("segredo", "publico") and not fc.cabe("x", "pessoal")
    assert fc.cabe("publico", "publico") and fc.cabe("publico", "pessoal") and fc.cabe("pessoal", "pessoal")
    assert not fc.cabe("pessoal", "publico")


def test_cache_por_mtime_e_falha_fechada(tmp_path):
    arq = tmp_path / "r.json"
    arq.write_text(json.dumps({"ferramentas": {"x": {"dado": "publico", "efeito": "leitura"}}}), encoding="utf-8")
    assert fc.rotulo("x", arq)["dado"] == "publico"
    arq.write_text(json.dumps({"ferramentas": {"x": {"dado": "pessoal", "efeito": "escrita"}}}), encoding="utf-8")
    os.utime(arq, (time.time() + 5, time.time() + 5))
    assert fc.rotulo("x", arq) == {"dado": "pessoal", "efeito": "escrita"}        # releu: o mtime mudou
    arq.write_text("não é json", encoding="utf-8")
    os.utime(arq, (time.time() + 10, time.time() + 10))
    assert fc.rotulo("x", arq) == {"dado": "pessoal", "efeito": "escrita"}        # quebrado: o restrito
    assert fc.dado_maximo("seth-livre", False, arq) == "publico"                  # faixas ausentes: o mais restrito
    assert fc.rotulo("x", tmp_path / "ausente.json") == {"dado": "pessoal", "efeito": "escrita"}


# --- filtros ---------------------------------------------------------------------------------------------------

def test_filtra_ferramentas_pelo_nivel():
    p = {"tools": [_def("buscar_web_mcp_navegador"), _def("vault_buscar_mcp_canon"), _def("memoria_acrescentar_mcp_canon"),
                   _def("desconhecida")], "tool_choice": {"type": "function", "function": {"name": "vault_buscar_mcp_canon"}}}
    tiradas = fc.filtrar_ferramentas(p, "publico")
    assert [t["function"]["name"] for t in p["tools"]] == ["buscar_web_mcp_navegador"]
    assert set(tiradas) == {"vault_buscar_mcp_canon", "memoria_acrescentar_mcp_canon", "desconhecida"}
    assert "tool_choice" not in p                                                  # apontava para ferramenta retirada
    q = {"tools": [_def("vault_buscar_mcp_canon"), _def("memoria_acrescentar_mcp_canon")]}
    assert fc.filtrar_ferramentas(q, "pessoal") == [] and len(q["tools"]) == 2     # nível pessoal: tudo que é conhecido
    r = {"tools": [_def("memoria_acrescentar")], "tool_choice": "required"}
    fc.filtrar_ferramentas(r, "publico")
    assert "tools" not in r and "tool_choice" not in r                             # sem sobra, nada de tool_choice


def test_resultado_acima_do_nivel_e_recusado_antes_de_voltar_ao_modelo():
    msgs = _hist(("buscar_web_mcp_navegador", "página pública"), ("vault_buscar_mcp_canon", "nota pessoal do Humano"))
    novas, recusadas = fc.filtrar_historico(msgs, "publico")
    assert recusadas == ["vault_buscar"]
    textos = [m["content"] for m in novas if m["role"] == "tool"]
    assert textos[0] == "página pública" and "omitido pela Máquina" in textos[1] and "nota pessoal" not in textos[1]
    novas2, rec2 = fc.filtrar_historico(msgs, "pessoal")
    assert rec2 == [] and novas2 == msgs


def test_resultado_com_segredo_e_recusado_em_qualquer_nivel():
    msgs = _hist(("buscar_web_mcp_navegador", f"a chave é {SEGREDO}"))
    for nivel in ("publico", "pessoal"):
        novas, rec = fc.filtrar_historico(msgs, nivel)
        assert rec == ["buscar_web"] and SEGREDO not in json.dumps(novas)


def test_resultado_sem_vinculo_verificavel_vale_pessoal():
    """Sem tool_call_id ligado a uma chamada do assistente, o resultado é dado pessoal: cai em rota gratuita, passa em local."""
    msgs = [{"role": "user", "content": "x"}, {"role": "tool", "tool_call_id": "z", "content": "origem desconhecida"}]
    novas, rec = fc.filtrar_historico(msgs, "publico")
    assert rec == ["?"] and "origem desconhecida" not in json.dumps(novas)
    novas2, rec2 = fc.filtrar_historico(msgs, "pessoal")
    assert rec2 == [] and novas2 == msgs
    sem_id = [{"role": "user", "content": "x"}, {"role": "tool", "name": "buscar_web", "content": "sem id"}]
    assert fc.filtrar_historico(sem_id, "publico")[1] == ["?"]


def test_campo_name_do_resultado_nunca_e_confiado():
    """vault_buscar com name="buscar_web" não passa por dado público: vale a chamada ligada pelo tool_call_id."""
    msgs = _hist(("vault_buscar_mcp_canon", "nota pessoal do Humano"))
    msgs[-1]["name"] = "buscar_web"
    novas, rec = fc.filtrar_historico(msgs, "publico")
    assert rec == ["vault_buscar"] and "nota pessoal" not in json.dumps(novas)
    falso_id = _hist(("buscar_web_mcp_navegador", "página"))
    falso_id[-1]["tool_call_id"] = "id-que-nao-existe"
    falso_id[-1]["name"] = "buscar_web"
    novas2, rec2 = fc.filtrar_historico(falso_id, "publico")
    assert rec2 == ["?"] and "página" not in json.dumps(novas2)
    # na faixa pública (só com par), o resultado de name falso também sai
    pub, _ = fc.filtrar_historico(msgs, "publico", so_com_par=True)
    assert "nota pessoal" not in json.dumps(pub)


def test_faixa_publica_mantem_so_o_par_de_ferramenta_publica():
    msgs = _hist(("buscar_web_mcp_navegador", "página"), ("vault_buscar_mcp_canon", "pessoal"))
    msgs.append({"role": "tool", "tool_call_id": "sem-par", "content": "órfão"})
    msgs.insert(1, {"role": "system", "content": "canon privado"})
    novas, _ = fc.filtrar_historico([m for m in msgs if m["role"] != "system"], "publico", so_com_par=True)
    s = json.dumps(novas, ensure_ascii=False)
    assert "página" in s and "pessoal" not in s and "órfão" not in s
    assert [tc["function"]["name"] for m in novas if m.get("tool_calls") for tc in m["tool_calls"]] == [
        "buscar_web_mcp_navegador"]


def test_preparar_payload_publico_com_ferramenta_publica():
    p = {"model": "seth-livre", "tools": [_def("buscar_web_mcp_navegador"), _def("vault_buscar_mcp_canon")],
         "messages": [{"role": "system", "content": "canon privado"}] + _hist(
             ("buscar_web_mcp_navegador", "página"), ("vault_buscar_mcp_canon", "pessoal"))}
    out = g._preparar_payload_publico(p)
    assert [t["function"]["name"] for t in out["tools"]] == ["buscar_web_mcp_navegador"]
    s = json.dumps(out["messages"], ensure_ascii=False)
    assert "canon privado" not in s and "pessoal" not in s and "página" in s and out["messages"][0]["role"] == "system"
    assert g._ferramentas_convertiveis(out, True) == frozenset({"buscar_web_mcp_navegador"})
    assert g._ferramentas_convertiveis({"tools": [_def("vault_buscar_mcp_canon")]}, True) == frozenset()


# --- gateway real ----------------------------------------------------------------------------------------------

def _nomes(corpo):
    return [t["function"]["name"] for t in corpo.get("tools", [])]


def test_gateway_faixa_publica_recebe_so_ferramenta_de_dado_publico(cenario):
    c = cenario(["ok"], permitir_contexto=False)       # a faixa pública de verdade
    msgs = _hist(("buscar_web_mcp_navegador", "página"), ("vault_buscar_mcp_canon", "nota pessoal"))
    status, corpo = c.postar(c.conexao(), msgs, modelo="seth-public",
                             tools=[_def("buscar_web_mcp_navegador"), _def("vault_buscar_mcp_canon"),
                                    _def("memoria_acrescentar_mcp_canon")])
    assert status == 200 and conteudo(corpo, False)
    visto = c.chamadas[0]
    assert _nomes(visto) == ["buscar_web_mcp_navegador"]
    s = json.dumps(visto["messages"], ensure_ascii=False)
    assert "página" in s and "nota pessoal" not in s


def test_gateway_faixa_publica_sem_ferramenta_publica_nao_leva_nenhuma(cenario):
    c = cenario(["ok"], permitir_contexto=False)
    c.postar(c.conexao(), modelo="seth-public", tools=[_def("memoria_acrescentar_mcp_canon")], tool_choice="auto")
    assert "tools" not in c.chamadas[0] and "tool_choice" not in c.chamadas[0]


def test_gateway_fila_seth_mantem_as_ferramentas_e_recusa_resultado_com_segredo(cenario):
    c = cenario(["ok"])
    msgs = _hist(("vault_buscar_mcp_canon", "nota"), ("buscar_web_mcp_navegador", f"token {SEGREDO}"))
    c.postar(c.conexao(), msgs, tools=[_def("vault_buscar_mcp_canon"), _def("memoria_acrescentar_mcp_canon")])
    visto = c.chamadas[0]
    assert _nomes(visto) == ["vault_buscar_mcp_canon", "memoria_acrescentar_mcp_canon"]   # o comportamento de hoje
    s = json.dumps(visto["messages"], ensure_ascii=False)
    assert "nota" in s and SEGREDO not in s and "omitido pela Máquina" in s


def test_gateway_chave_desliga_o_filtro_da_fila(cenario, monkeypatch):
    monkeypatch.setenv("SETH_FERRAMENTAS_CONFIANCA", "0")
    c = cenario(["ok"])
    c.postar(c.conexao(), _hist(("buscar_web_mcp_navegador", f"token {SEGREDO}")), tools=[_def("coisa_nova")])
    assert _nomes(c.chamadas[0]) == ["coisa_nova"] and SEGREDO in json.dumps(c.chamadas[0]["messages"])


def test_gateway_get_e_post_seguinte_na_mesma_conexao_nao_herdam_o_filtro(cenario):
    """Lição do incidente de 18/11: a faixa pública de um POST não pode vazar para o GET nem para o POST seguinte."""
    c = cenario(["ok"], permitir_contexto=False)
    conn = c.conexao()
    s1, _ = c.postar(conn, modelo="seth-public", tools=[_def("vault_buscar_mcp_canon")])
    assert s1 == 200 and "tools" not in c.chamadas[0]
    conn.request("GET", "/v1/models")
    r = conn.getresponse()
    corpo = r.read()
    assert r.status == 200 and b"seth-livre" in corpo
    s3, _ = c.postar(conn, modelo="seth-public", tools=[_def("buscar_web_mcp_navegador")])
    assert s3 == 200 and _nomes(c.chamadas[1]) == ["buscar_web_mcp_navegador"]
    frio = c.conexao()
    frio.request("GET", "/v1/models")
    assert frio.getresponse().status == 200
