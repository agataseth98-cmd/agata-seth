import unittest
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
SECOES = ["panorama", "conversa", "conselho", "sistema", "conhecimento", "historia", "custos", "qualidade"]


class Menu(HTMLParser):
    """Colhe os botões do menu lateral (data-secao), as seções (class secao) e restos do menu antigo."""

    def __init__(self):
        super().__init__()
        self.botoes, self.secoes, self.restos_antigos = [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "button" and "data-secao" in a:
            self.botoes.append(a["data-secao"])
        if tag == "section" and "secao" in classes:
            self.secoes.append(a.get("id"))
        if "data-page" in a or "nav-group" in classes or "nav-sub" in classes:
            self.restos_antigos.append(tag)


class MenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.menu = Menu()
        cls.menu.feed((HERE / "prototipo.html").read_text(encoding="utf-8"))

    def test_menu_tem_um_botao_para_cada_uma_das_sete_secoes(self):
        self.assertEqual(self.menu.botoes, SECOES)

    def test_toda_secao_do_menu_existe_na_pagina(self):
        self.assertEqual(self.menu.secoes, SECOES)

    def test_sem_submenus_nem_botoes_de_pagina_antiga(self):
        self.assertEqual(self.menu.restos_antigos, [])

    def test_js_navega_pelo_botao_de_secao(self):
        js = (HERE / "prototipo.js").read_text(encoding="utf-8")
        self.assertIn('".nav button[data-secao]"', js)
        self.assertIn("function mostrarSecao", js)
        self.assertNotIn("alternarGrupo", js)


if __name__ == "__main__":
    unittest.main()
