import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = HERE / "prototipo.html"
CSS = HERE / "prototipo.css"

# style-src 'self' no servidor: o navegador descarta style="..." e <style>. Estilo fica em prototipo.css.
ATRIBUTO_STYLE = re.compile(r"(?<![\w-])style\s*=", re.IGNORECASE)
TAG_STYLE = re.compile(r"<style\b", re.IGNORECASE)
CLASSES_NOVAS = (
    "grafo-modos", "grafo-form", "grafo-entrada", "grafo-svg", "lista-coluna",
    "linha-medicoes", "medir-nota", "lista-componentes", "vault-canvas",
)
IDS_PRESERVADOS = (
    "grafo-form", "grafo-entrada", "grafo-svg", "lacunas-lista", "qualidade-lista",
    "sdd-lista", "visao-melhorias", "medir-nota", "vault-canvas",
)

# Mapeamento copiado do diff de correção: o elemento com este id deve ter esta classe e esta tag.
ELEMENTOS_COM_CLASSE = (
    ("grafo-form", "grafo-form", "form"),
    ("grafo-entrada", "grafo-entrada", "input"),
    ("grafo-svg", "grafo-svg", "svg"),
    ("lacunas-lista", "lista-coluna", "ul"),
    ("qualidade-lista", "lista-coluna", "ul"),
    ("visao-melhorias", "lista-coluna", "ul"),
    ("sdd-lista", "lista-componentes", "div"),
    ("medir-nota", "medir-nota", "p"),
    ("vault-canvas", "vault-canvas", "ul"),
)
# Dois dos 11 elementos não têm id no diff: o alvo é o pai do filho com este id.
PAI_DO_ID = (
    ("grafo-modo-relacoes", "grafo-modos", "div"),
    ("medir-recuperacao", "linha-medicoes", "div"),
)

# Valores dos style= originais (linhas '-' do diff de correção). O CSS tem que declarar exatamente isto.
VALORES_ESPERADOS = {
    "grafo-modos": {"display": "flex", "gap": "8px", "flex-wrap": "wrap"},
    "grafo-form": {"display": "flex", "gap": "8px", "margin": "10px 0"},
    "grafo-entrada": {"width": "7em"},
    "grafo-svg": {"width": "100%", "max-height": "60vh"},
    "lista-coluna": {"margin": "0", "padding-left": "18px", "display": "flex",
                     "flex-direction": "column", "gap": "8px"},
    "linha-medicoes": {"display": "flex", "flex-wrap": "wrap", "gap": "10px", "align-items": "center"},
    "medir-nota": {"margin": "8px 0 0"},
    "lista-componentes": {"display": "flex", "flex-direction": "column", "gap": "10px"},
    "vault-canvas": {"margin": "8px 0", "padding-left": "18px"},
}

VAZIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
COMENTARIO_CSS = re.compile(r"/\*.*?\*/", re.S)
REGRA_CSS = re.compile(r"([^{}]+)\{([^{}]*)\}")


class Arvore(HTMLParser):
    """Guarda cada elemento (tag, atributos, índice do pai), na ordem do documento."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elementos = []
        self._abertos = []

    def handle_starttag(self, tag, attrs):
        pai = self._abertos[-1] if self._abertos else None
        self.elementos.append({"tag": tag, "attrs": dict(attrs), "pai": pai})
        if tag not in VAZIOS:
            self._abertos.append(len(self.elementos) - 1)

    def handle_endtag(self, tag):
        for pos in range(len(self._abertos) - 1, -1, -1):
            if self.elementos[self._abertos[pos]]["tag"] == tag:
                del self._abertos[pos:]
                return


def arvore_de(texto):
    arvore = Arvore()
    arvore.feed(texto)
    arvore.close()
    return arvore


def por_id(arvore, id_):
    return [e for e in arvore.elementos if e["attrs"].get("id") == id_]


def classes_de(elemento):
    return elemento["attrs"].get("class", "").split()


def declaracoes_da_classe(css, classe):
    """Parser simples: junta as declarações de cada regra cujo seletor inclui '.classe' (a última vence)."""
    css = COMENTARIO_CSS.sub("", css)
    decl = {}
    for m in REGRA_CSS.finditer(css):
        seletores = [s.strip() for s in m.group(1).split(",")]
        if "." + classe not in seletores:
            continue
        for item in m.group(2).split(";"):
            prop, sep, val = item.partition(":")
            if sep:
                decl[prop.strip().lower()] = " ".join(val.split())
    return decl


def linhas_de(texto, padrao):
    return [texto.count("\n", 0, m.start()) + 1 for m in padrao.finditer(texto)]


class CspPrototipoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")

    def test_html_sem_atributo_style(self):
        self.assertEqual([], linhas_de(self.html, ATRIBUTO_STYLE), "atributo style= nas linhas indicadas")

    def test_html_sem_tag_style(self):
        self.assertEqual([], linhas_de(self.html, TAG_STYLE), "<style> nas linhas indicadas")

    def test_classes_novas_existem_no_css(self):
        for nome in CLASSES_NOVAS:
            with self.subTest(classe=nome):
                self.assertRegex(self.css, r"\." + re.escape(nome) + r"(?![\w-])")

    def test_mapeamento_cobre_as_classes_novas(self):
        usadas = {c for _, c, _ in ELEMENTOS_COM_CLASSE} | {c for _, c, _ in PAI_DO_ID}
        self.assertEqual(set(CLASSES_NOVAS), usadas)
        self.assertEqual(11, len(ELEMENTOS_COM_CLASSE) + len(PAI_DO_ID))

    def test_elemento_tem_a_classe_do_seu_id(self):
        arvore = arvore_de(self.html)
        for id_, classe, tag in ELEMENTOS_COM_CLASSE:
            with self.subTest(id=id_, classe=classe):
                achados = por_id(arvore, id_)
                self.assertEqual(1, len(achados), f"id={id_!r} deveria aparecer 1 vez, achou {len(achados)}")
                el = achados[0]
                self.assertEqual(tag, el["tag"], f"id={id_!r}: tag {el['tag']!r}, esperado {tag!r}")
                self.assertIn(classe, classes_de(el),
                              f"id={id_!r} sem class={classe!r}; classes achadas: {classes_de(el)}")

    def test_pai_do_id_tem_a_classe(self):
        arvore = arvore_de(self.html)
        for id_filho, classe, tag in PAI_DO_ID:
            with self.subTest(filho=id_filho, classe=classe):
                achados = por_id(arvore, id_filho)
                self.assertEqual(1, len(achados), f"id={id_filho!r} deveria aparecer 1 vez, achou {len(achados)}")
                indice_pai = achados[0]["pai"]
                self.assertIsNotNone(indice_pai, f"id={id_filho!r} sem elemento pai")
                pai = arvore.elementos[indice_pai]
                self.assertEqual(tag, pai["tag"], f"pai de id={id_filho!r}: tag {pai['tag']!r}, esperado {tag!r}")
                self.assertIn(classe, classes_de(pai),
                              f"pai de id={id_filho!r} sem class={classe!r}; classes achadas: {classes_de(pai)}")

    def test_valores_cobrem_as_classes_novas(self):
        self.assertEqual(set(CLASSES_NOVAS), set(VALORES_ESPERADOS))

    def test_valores_das_classes_novas_no_css(self):
        for classe, esperado in VALORES_ESPERADOS.items():
            decl = declaracoes_da_classe(self.css, classe)
            with self.subTest(classe=classe):
                if not decl:
                    self.fail(f"nenhuma regra '.{classe} {{...}}' no CSS; esperado {esperado}")
                for prop, val in esperado.items():
                    with self.subTest(prop=prop):
                        if prop not in decl:
                            self.fail(f".{classe} não declara '{prop}' no CSS (esperado {val!r})")
                        self.assertEqual(val, decl[prop],
                                         f".{classe} {prop}: esperado {val!r}, achado {decl[prop]!r}")

    def test_ids_preservados(self):
        for id_ in IDS_PRESERVADOS:
            with self.subTest(id=id_):
                self.assertIn(f'id="{id_}"', self.html)


if __name__ == "__main__":
    unittest.main()
