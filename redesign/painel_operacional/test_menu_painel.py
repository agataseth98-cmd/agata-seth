import unittest
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGINAS = {"panorama", "conselho", "operacao", "visao", "integracoes", "modelos", "manutencao", "plano",
           "memoria", "grafo", "documentacao", "conversa", "qualidade", "sdd", "operator-console", "lacunas", "capacidades",
           "nv-alexandria", "nv-metacognicao", "nv-corpo", "nv-conexoes", "nv-orcamento", "nv-avaliacao", "nv-sentidos"}
GRUPOS = {"sistema": {"operacao", "visao", "integracoes", "modelos", "manutencao", "plano"},
          "memoria": {"memoria", "grafo", "documentacao", "conversa"},
          "qualidade": {"qualidade", "sdd", "operator-console", "lacunas", "capacidades"},
          "novaversao": {"nv-alexandria", "nv-metacognicao", "nv-corpo", "nv-conexoes", "nv-orcamento", "nv-avaliacao", "nv-sentidos"}}


class Menu(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pilha, self.grupo_atual = [], None
        self.botoes, self.grupos, self.secoes = {}, {}, set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "nav-group" in (a.get("class") or "").split():
            self.grupo_atual = a.get("data-group"); self.grupos[self.grupo_atual] = set()
        if tag == "button" and "data-page" in a:
            self.botoes[a["data-page"]] = self.grupo_atual
            if self.grupo_atual:
                self.grupos[self.grupo_atual].add(a["data-page"])
        if tag == "section" and (a.get("id") or "").startswith("page-"):
            self.secoes.add(a["id"][5:])

    def handle_endtag(self, tag):
        if tag == "nav":
            self.grupo_atual = None


class MenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.menu = Menu(); cls.menu.feed((HERE / "prototipo.html").read_text(encoding="utf-8"))

    def test_nenhuma_pagina_se_perdeu_no_agrupamento(self):
        self.assertEqual(set(self.menu.botoes), PAGINAS)

    def test_grupos_tem_as_paginas_esperadas(self):
        self.assertEqual(self.menu.grupos, GRUPOS)

    def test_todo_botao_do_menu_tem_pagina(self):
        faltam = PAGINAS - self.menu.secoes
        self.assertEqual(faltam, set())

    def test_js_conta_so_botoes_de_pagina_na_navegacao(self):
        js = (HERE / "prototipo.js").read_text(encoding="utf-8")
        self.assertIn('".nav button[data-page]"', js)
        self.assertIn("function alternarGrupo", js)


if __name__ == "__main__":
    unittest.main()
