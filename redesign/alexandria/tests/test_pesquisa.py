"""Hierarquia de buscas da Alexandria: planejador puro e execução com busca falsa (lote 9)."""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))
import pesquisa  # noqa: E402


def test_auto_para_no_lexico_quando_basta():
    assert pesquisa.etapas_para("auto", suficiente=True, externa_disponivel=True) == ["lexico"]


def test_auto_acrescenta_semantica_e_externa_quando_falta():
    assert pesquisa.etapas_para("auto", suficiente=False, externa_disponivel=True) == ["lexico", "semantica", "externa"]
    assert pesquisa.etapas_para("auto", suficiente=False, externa_disponivel=False) == ["lexico", "semantica"]


def test_modos_explicitos_so_fazem_o_pedido():
    assert pesquisa.etapas_para("lexico") == ["lexico"]
    assert pesquisa.etapas_para("semantica") == ["semantica"]
    assert pesquisa.etapas_para("externa", externa_disponivel=False) == []
    assert pesquisa.etapas_para("todos", externa_disponivel=True) == ["lexico", "semantica", "externa"]


def test_modo_desconhecido_levanta():
    try:
        pesquisa.etapas_para("adivinhar")
    except ValueError:
        return
    raise AssertionError("deveria levantar ValueError")


def test_executa_auto_com_consulta_falsa(monkeypatch):
    chamadas = []

    def consulta_falsa(consulta, *, acesso, n, semantica):
        chamadas.append(semantica)
        suf = {"suficiente": semantica != "nunca", "cobertura": 0.2, "motivo": "teste", "precisa_externa": False}
        return {"resultados": [], "suficiencia": suf}

    pac = pesquisa.pesquisar("pergunta", modo="auto", consultar=consulta_falsa, externa_disponivel=False)
    assert chamadas == ["nunca", "auto"]          # léxico primeiro; semântica só porque faltou
    assert [e["etapa"] for e in pac["hierarquia"]["etapas"]] == ["lexico", "semantica"]
    assert pac["externa"] == []
