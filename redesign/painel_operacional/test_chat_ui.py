#!/usr/bin/env python3
"""Checagens estáticas da seção de conversa do painel (prototipo.html / prototipo.js).

Não abre navegador e não chama o gateway: lê os dois arquivos e confere a CSP (sem script inline,
sem style=, sem atributos on*) e o uso do stream com render por textContent.
"""
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = (HERE / "prototipo.html").read_text(encoding="utf-8")
JS = (HERE / "prototipo.js").read_text(encoding="utf-8")

INICIO_SECAO = '<section class="page" id="page-conversa"'
INICIO_BLOCO_JS = "/* (27/10/2026) Conversa com a Seth"
FIM_BLOCO_JS = "/* (27/10/2026) Grafo do vault"


def secao_conversa() -> str:
    inicio = HTML.index(INICIO_SECAO)
    fim = HTML.index("<section", inicio + len(INICIO_SECAO))
    return HTML[inicio:fim]


def bloco_conversa_js() -> str:
    inicio = JS.index(INICIO_BLOCO_JS)
    fim = JS.index(FIM_BLOCO_JS, inicio)
    return JS[inicio:fim]


class ConversaHtml(unittest.TestCase):
    def test_nenhum_script_sem_src(self):
        for tag in re.finditer(r"<script\b([^>]*)>", HTML, flags=re.IGNORECASE):
            self.assertRegex(tag.group(1), r"\bsrc\s*=", f"script inline encontrado: {tag.group(0)[:80]}")

    def test_secao_conversa_existe(self):
        self.assertIn(INICIO_SECAO, HTML)

    def test_secao_conversa_sem_style(self):
        self.assertNotIn("style=", secao_conversa())

    def test_secao_conversa_sem_atributo_on(self):
        self.assertIsNone(re.search(r"\son[a-z]+\s*=", secao_conversa(), flags=re.IGNORECASE))


class ConversaJs(unittest.TestCase):
    def test_usa_rota_de_stream(self):
        self.assertIn("/api/seth/chat/stream", JS)

    def test_mantem_fallback_para_chat_inteiro(self):
        self.assertIn('"/api/seth/chat"', JS)

    def test_envia_chave_mensagens_no_stream(self):
        padrao = r'"/api/seth/chat/stream".*?body:\s*JSON\.stringify\(\{mensagens\}\)'
        self.assertIsNotNone(re.search(padrao, bloco_conversa_js(), flags=re.DOTALL),
                             "o stream deve enviar o campo 'mensagens' (server.py, _seth_chat_stream)")

    def test_bloco_conversa_sem_innerhtml(self):
        self.assertNotIn("innerHTML", bloco_conversa_js())

    def test_nenhum_innerhtml_com_delta(self):
        for linha in JS.splitlines():
            if "innerHTML" in linha:
                self.assertNotIn("delta", linha)

    def test_texto_do_stream_vai_por_text_node(self):
        bloco = bloco_conversa_js()
        self.assertIn("createTextNode", bloco)
        self.assertIn("appendData(delta)", bloco)

    def test_sem_armazenamento_local_na_conversa(self):
        bloco = bloco_conversa_js()
        self.assertNotIn("localStorage", bloco)
        self.assertNotIn("sessionStorage", bloco)

    def test_trata_evento_erro_com_motivo(self):
        bloco = bloco_conversa_js()
        self.assertIn('evento.tipo === "erro"', bloco)
        self.assertIn("evento.motivo", bloco)


if __name__ == "__main__":
    unittest.main()
