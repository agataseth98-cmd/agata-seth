"""Busca do navegador-mcp: funções puras (23/11/2026, seth-web2-23-11). Sem rede, sem navegador.
Rodar: pytest -q redesign/mcp/navegador/test_busca_filtro.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import busca_filtro as bf  # noqa: E402


def test_itens_wiki_le_titulo_link_e_tira_html_do_trecho():
    r = json.dumps({"query": {"search": [{"title": "Ulan Bator", "snippet": "capital da <span>Mongólia</span> &amp; x"}]}})
    assert bf.itens_wiki(r, "pt") == [{"titulo": "Ulan Bator (Wikipedia)", "href": "https://pt.wikipedia.org/wiki/Ulan_Bator",
                                      "trecho": "capital da Mongólia & x"}]


def test_itens_wiki_json_ruim_ou_sem_busca_vira_vazio():
    assert bf.itens_wiki("{", "pt") == []
    assert bf.itens_wiki(json.dumps({"error": {"code": "x"}}), "en") == []


def test_filtro_tira_o_que_casa_so_a_primeira_palavra_e_ignora_acento():
    itens = [{"titulo": "Capital.com trading", "href": "a", "trecho": ""},
             {"titulo": "Ulan Bator", "href": "b", "trecho": "capital da mongolia"},
             {"titulo": "Mongólia", "href": "c", "trecho": "país; capital Ulan Bator"}]
    assert [i["href"] for i in bf.filtrar_e_ordenar(itens, bf.termos("capital da Mongólia"))] == ["c", "b"]


def test_fracao_branda_e_sem_termos_devolve_tudo():
    itens = [{"titulo": "History of Python", "href": "a", "trecho": ""}, {"titulo": "nada", "href": "b", "trecho": ""}]
    assert [i["href"] for i in bf.filtrar_e_ordenar(itens, bf.termos("Python release"), (1, 2))] == ["a"]
    assert bf.filtrar_e_ordenar(itens, []) == itens


def test_termos_ignora_curtas_e_operador():
    assert bf.termos('capital da "Mongólia" site:x.org') == ["capital", "mongólia"]
