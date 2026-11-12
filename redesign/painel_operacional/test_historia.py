"""Testes da seção História do painel (spec/spec.md, seção História, 11/11/2026).

Cada método corresponde a um critério automático de spec/acceptance.json. Os de rota sobem o servidor numa
porta livre (127.0.0.1), como test_painel_unificado.py. O de voz troca scripts/agata_falar.py por um falso que
grava o que recebeu e sai com o código pedido. Os de interface rodam historia.js no node, com um DOM mínimo, e
conferem que o texto vira nós (createElement e createTextNode), nunca HTML.
"""
import http.client
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import historia_painel as hp  # noqa: E402

HTML = (HERE / "prototipo.html").read_text(encoding="utf-8")
CSS = re.sub(r"/\*.*?\*/", "", (HERE / "prototipo.css").read_text(encoding="utf-8"), flags=re.S)
JS = (HERE / "historia.js").read_text(encoding="utf-8")
TEXTO_REAL = "01-a-casa-propria-da-conversa"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")

TEXTO_TESTE = """---
tomo: I
titulo_tomo: "Tomo de teste"
texto: 1
titulo: "Texto de teste"
periodo: "11/11/2026"
autor: "Modelo de teste"
estado: "rascunho"
protocolo: "protocolo de teste"
---

# Título de teste

Corpo do texto de teste, com [medido].
"""


def _carrega_servidor():
    spec = importlib.util.spec_from_file_location("painel_historia_teste", HERE / "server.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


panel = _carrega_servidor()


class ServidorHistoriaTests(unittest.TestCase):
    """Sobe o servidor numa porta livre e aponta a História para um diretório temporário."""

    @classmethod
    def setUpClass(cls):
        cls.porta_antiga = panel.PORT
        cls.servidor = panel.ThreadingHTTPServer(("127.0.0.1", 0), panel.Handler)
        cls.servidor.daemon_threads = True
        panel.PORT = cls.servidor.server_address[1]
        cls.thread = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.thread.join(timeout=3)
        panel.PORT = cls.porta_antiga

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name) / "historia"
        self.salvo = (hp.HISTORIA_DIR, hp.FALA)
        hp.HISTORIA_DIR = self.raiz
        self.falso = Path(self.tmp.name) / "falar_falso.py"
        self.falso.write_text(
            "import os, sys, pathlib\n"
            "arq = sys.argv[sys.argv.index('--arquivo') + 1]\n"
            "pathlib.Path(os.environ['FALSO_LOG']).write_text(pathlib.Path(arq).read_text(encoding='utf-8'), encoding='utf-8')\n"
            "pathlib.Path(os.environ['FALSO_LOG'] + '.caminho').write_text(arq, encoding='utf-8')\n"
            "sys.exit(int(os.environ['FALSO_CODIGO']))\n",
            encoding="utf-8")
        hp.FALA = self.falso
        self.log = Path(self.tmp.name) / "falou.txt"
        self.ambiente = {k: os.environ.get(k) for k in ("FALSO_LOG", "FALSO_CODIGO")}
        os.environ["FALSO_LOG"] = str(self.log)
        os.environ["FALSO_CODIGO"] = "0"

    def tearDown(self):
        hp.HISTORIA_DIR, hp.FALA = self.salvo
        for chave, valor in self.ambiente.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor
        self.tmp.cleanup()

    def monta_texto(self, tomo="tomo-01", nome="01-teste", conteudo=TEXTO_TESTE):
        pasta = self.raiz / tomo
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / f"{nome}.md").write_text(conteudo, encoding="utf-8")

    def pede(self, caminho, metodo="GET", corpo=None, cabecalhos=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=10)
        try:
            cab = dict(cabecalhos or {})
            if corpo is not None:
                cab.setdefault("Content-Type", "application/json")
            conn.request(metodo, caminho, body=corpo, headers=cab)
            resposta = conn.getresponse()
            return resposta.status, resposta.read(), {k.lower(): v for k, v in resposta.getheaders()}
        finally:
            conn.close()

    def ouvir(self, tomo="tomo-01", texto="01-teste", cabecalhos=None):
        corpo = json.dumps({"tomo": tomo, "texto": texto}).encode("utf-8")
        cab = {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin"}
        cab.update(cabecalhos or {})
        status, dados, _ = self.pede("/api/historia/ouvir", "POST", corpo, cab)
        return status, (json.loads(dados) if status == 200 else dados)


class RotasHistoriaTests(ServidorHistoriaTests):
    def test_lista_tomos_e_textos_com_frontmatter(self):
        self.monta_texto()
        self.monta_texto("tomo-02", "02-outro")
        status, corpo, cabecalhos = self.pede("/api/historia")
        self.assertEqual(status, 200)
        self.assertIn("application/json", cabecalhos["content-type"])
        self.assertEqual(cabecalhos["cache-control"], "no-store")
        dados = json.loads(corpo)
        self.assertEqual((dados["estado"], [t["tomo"] for t in dados["tomos"]]), ("ok", ["tomo-01", "tomo-02"]))
        primeiro = dados["tomos"][0]
        self.assertEqual((primeiro["numeral"], primeiro["titulo"]), ("I", "Tomo de teste"))
        texto = primeiro["textos"][0]
        self.assertEqual(texto["id"], "01-teste")
        self.assertEqual((texto["numero"], texto["titulo"], texto["periodo"]), ("1", "Texto de teste", "11/11/2026"))
        self.assertEqual((texto["autor"], texto["estado"], texto["protocolo"]), ("Modelo de teste", "rascunho", "protocolo de teste"))
        self.assertNotIn("corpo", texto, "a lista não traz o corpo")

    def test_texto_devolve_frontmatter_e_corpo(self):
        self.monta_texto()
        status, corpo, cabecalhos = self.pede("/api/historia/texto?tomo=tomo-01&texto=01-teste")
        self.assertEqual(status, 200)
        self.assertEqual(cabecalhos["cache-control"], "no-store")
        dados = json.loads(corpo)
        self.assertEqual((dados["tomo"], dados["texto"]), ("tomo-01", "01-teste"))
        self.assertEqual(dados["frontmatter"]["titulo"], "Texto de teste")
        self.assertTrue(dados["corpo"].lstrip().startswith("# Título de teste"), "o corpo começa depois do frontmatter")
        self.assertNotIn("tomo: I", dados["corpo"])

    def test_pasta_vazia_ou_ausente_da_estado_vazio(self):
        for cenario in ("ausente", "vazia"):
            with self.subTest(cenario=cenario):
                if cenario == "vazia":
                    self.raiz.mkdir(parents=True, exist_ok=True)
                status, corpo, _ = self.pede("/api/historia")
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(corpo), {"schema_version": 1, "estado": "vazio", "tomos": []})
                if cenario == "vazia":
                    self.raiz.rmdir()

    def test_caminho_do_cliente_e_recusado(self):
        self.monta_texto()
        fora = Path(self.tmp.name) / "fora.md"
        fora.write_text("segredo fora da História", encoding="utf-8")
        (self.raiz / "tomo-03").mkdir()
        os.symlink(fora, self.raiz / "tomo-03" / "03-link.md")
        ruins = [("../tomo-01", "01-teste"), ("tomo-01", "../01-teste"), ("tomo-01", "01-teste/../../x"),
                 ("tomo-1", "01-teste"), ("tomo-01", "1-teste"), ("tomo-01", "01-TESTE"), ("tomo-01", "")]
        for tomo, texto in ruins:
            with self.subTest(tomo=tomo, texto=texto):
                status, _, _ = self.pede(f"/api/historia/texto?tomo={quote(tomo, safe='')}&texto={quote(texto, safe='')}")
                self.assertEqual(status, 400)
        self.assertEqual(self.pede("/api/historia/texto?tomo=tomo-01&texto=99-nao-existe")[0], 404)
        self.assertEqual(self.pede("/api/historia/texto?tomo=tomo-03&texto=03-link")[0], 404, "link para fora não sai")
        self.assertEqual(self.pede("/api/historia/texto?tomo=tomo-01")[0], 400, "sem texto, 400")

    def test_leituras_recusam_origem_cruzada(self):
        self.monta_texto()
        for cabecalhos in ({"Origin": "http://evil.example"}, {"Sec-Fetch-Site": "cross-site"}):
            with self.subTest(cabecalhos=cabecalhos):
                self.assertEqual(self.pede("/api/historia", cabecalhos=cabecalhos)[0], 403)
                self.assertEqual(self.pede("/api/historia/texto?tomo=tomo-01&texto=01-teste", cabecalhos=cabecalhos)[0], 403)
        self.assertEqual(self.pede("/api/historia")[0], 200)

    def test_historia_js_servido_como_arquivo_externo(self):
        status, corpo, cabecalhos = self.pede("/historia.js")
        self.assertEqual(status, 200)
        self.assertIn("javascript", cabecalhos["content-type"])
        self.assertEqual(corpo, (HERE / "historia.js").read_bytes())

    def test_ouvir_so_aceita_json_da_propria_origem(self):
        self.monta_texto()
        corpo = json.dumps({"tomo": "tomo-01", "texto": "01-teste"}).encode("utf-8")
        self.assertEqual(self.pede("/api/historia/ouvir", "POST", corpo, {"Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.pede("/api/historia/ouvir", "POST", corpo,
                                   {"Origin": "http://evil.example", "Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.pede("/api/historia/ouvir", "POST", corpo,
                                   {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin",
                                    "Content-Type": "text/plain"})[0], 403)
        grande = b"{" + b" " * 600 + b"}"
        self.assertEqual(self.pede("/api/historia/ouvir", "POST", grande,
                                   {"Origin": panel.ALLOWED_ORIGIN, "Sec-Fetch-Site": "same-origin",
                                    "Content-Type": "application/json"})[0], 400)
        self.assertFalse(self.log.exists(), "pedido recusado não fala")

    def test_ouvir_responde_falou_pelo_exit_code_e_manda_so_o_corpo(self):
        self.monta_texto()
        status, dados = self.ouvir()
        self.assertEqual(status, 200)
        self.assertEqual((dados["falou"], dados["motivo"]), (True, "falei o texto"))
        falado = self.log.read_text(encoding="utf-8")
        self.assertIn("Corpo do texto de teste", falado)
        self.assertNotIn("tomo: I", falado, "o frontmatter não é falado")
        caminho = Path(Path(str(self.log) + ".caminho").read_text(encoding="utf-8"))
        self.assertFalse(caminho.exists(), "o arquivo temporário é apagado depois da fala")
        os.environ["FALSO_CODIGO"] = "2"
        status, dados = self.ouvir()
        self.assertEqual((status, dados["falou"]), (200, False))
        self.assertTrue(dados["motivo"].startswith("não falei"))

    def test_ouvir_sem_voz_diz_que_nao_falou(self):
        self.monta_texto()
        os.environ["FALSO_CODIGO"] = "3"
        status, dados = self.ouvir()
        self.assertEqual(status, 200)
        self.assertIs(dados["falou"], False)
        self.assertIn("a voz do sistema não respondeu", dados["motivo"])

    def test_ouvir_recusa_fala_em_curso_e_texto_inexistente(self):
        self.monta_texto()
        self.assertTrue(hp._FALA_LOCK.acquire(blocking=False))
        try:
            status, _ = self.ouvir()
            self.assertEqual(status, 429, "com outra fala em curso, não fala")
        finally:
            hp._FALA_LOCK.release()
        status, _ = self.ouvir(texto="99-nao-existe")
        self.assertEqual(status, 404)
        self.assertFalse(self.log.exists(), "texto inexistente não chama a voz")


class ConsistenciaHistoriaTests(unittest.TestCase):
    def test_historia_do_repo_tem_o_texto_1(self):
        salvo = hp.HISTORIA_DIR
        hp.HISTORIA_DIR = ROOT / "historia"
        try:
            dados = hp.listar()
            texto = hp.ler("tomo-01", TEXTO_REAL)
        finally:
            hp.HISTORIA_DIR = salvo
        tomo = next(t for t in dados["tomos"] if t["tomo"] == "tomo-01")
        self.assertEqual(tomo["numeral"], "I")
        self.assertEqual([t["id"] for t in tomo["textos"]], [TEXTO_REAL])
        self.assertIn("rascunho", texto["frontmatter"]["estado"])
        self.assertIn("[medido]", texto["corpo"])

    def test_p8_protege_historia(self):
        texto = (ROOT / "scripts/perimetro/p08_quarentena.sh").read_text(encoding="utf-8")
        self.assertIn("historia/*) return 0 ;;", texto)

    def test_sem_emoji_na_historia(self):
        for arquivo in (HERE / "historia_painel.py", HERE / "historia.js", ROOT / "historia" / "README.md"):
            with self.subTest(arquivo=arquivo.name):
                self.assertEqual(EMOJI.findall(arquivo.read_text(encoding="utf-8")), [])


class TelaHistoriaTests(unittest.TestCase):
    def test_secao_historia_na_navegacao(self):
        botoes = re.findall(r'<button type="button" data-secao="([a-z]+)"', HTML)
        self.assertEqual(botoes[botoes.index("conhecimento") + 1], "historia", "História entra logo depois de Conhecimento")
        inicio = HTML.index('<section class="secao" id="historia"')
        fim = HTML.index('<section class="secao" id="custos"')
        secao = HTML[inicio:fim]
        self.assertIn(" hidden>", secao[:200], "a seção começa escondida")
        for estado in ("carregando", "vazio", "erro"):
            self.assertIn(f'data-estado="{estado}"', secao)
        for id_ in ("historia-indice", "historia-meta", "historia-estado", "historia-ouvir",
                    "historia-ouvir-estado", "historia-corpo"):
            self.assertEqual(secao.count(f'id="{id_}"'), 1, id_)
        self.assertIn('<script src="historia.js" defer></script>', HTML)

    def test_marcas_tem_regra_com_tokens(self):
        for classe, token in (("marca-medido", "--teal"), ("marca-relato", "--gold"), ("marca-inferencia", "--violet")):
            with self.subTest(classe=classe):
                regra = re.search(r"\." + classe + r"\{([^}]*)\}", CSS)
                self.assertIsNotNone(regra, classe)
                self.assertIn(f"var({token})", regra.group(1))
        bloco = CSS[CSS.index(".historia-legenda"):]
        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", bloco), [], "cor literal na seção História")


class UiHistoriaTests(unittest.TestCase):
    """Roda historia.js no node, com um DOM mínimo, e compara a árvore de nós com o esperado."""

    NODE = r"""
const fs = require('fs'); const vm = require('vm');
const entrada = JSON.parse(fs.readFileSync(0, 'utf8'));
class No { constructor(tag) { this.tag = tag; this.filhos = []; this.className = ''; } appendChild(n) { this.filhos.push(n); return n; } }
class Texto { constructor(t) { this.tag = '#texto'; this.texto = t; } }
const documento = {createElement: (t) => new No(t), createTextNode: (t) => new Texto(t),
  getElementById: () => null, querySelectorAll: () => []};
const janela = {};
const ctx = {window: janela, document: documento};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(entrada.arquivo, 'utf8'), ctx, {filename: 'historia.js'});
function ser(n) { if (n.tag === '#texto') return n.texto; const o = {tag: n.tag}; if (n.className) o.class = n.className; o.filhos = n.filhos.map(ser); return o; }
const md = janela.AgataPainel.markdownParaNos;
console.log(JSON.stringify({amostra: md(entrada.amostra).map(ser), real: md(entrada.real).map(ser)}));
"""

    def roda(self, amostra, real=""):
        entrada = json.dumps({"arquivo": str(HERE / "historia.js"), "amostra": amostra, "real": real})
        resultado = subprocess.run(["node", "-e", self.NODE], input=entrada, capture_output=True, text=True, timeout=120)
        if resultado.returncode != 0:
            self.fail("node não rodou (não medido): " + resultado.stderr[-300:])
        return json.loads(resultado.stdout)

    def test_markdown_vira_nos_sem_html(self):
        amostra = ("# Título\n\nTexto com **negrito**, *itálico*, `código` e [medido].\n\n"
                   "- item um\n- item [relato]\n\n1. primeiro\n2. segundo\n\n---\n\n"
                   "#### Sub [inferência]\n\n<img src=x onerror=alert(1)> e <script>x</script>")
        saida = self.roda(amostra)["amostra"]
        esperado = [
            {"tag": "h2", "filhos": ["Título"]},
            {"tag": "p", "filhos": ["Texto com ", {"tag": "strong", "filhos": ["negrito"]}, ", ",
                                    {"tag": "em", "filhos": ["itálico"]}, ", ", {"tag": "code", "filhos": ["código"]},
                                    " e ", {"tag": "span", "class": "marca marca-medido", "filhos": ["[medido]"]}, "."]},
            {"tag": "ul", "filhos": [{"tag": "li", "filhos": ["item um"]},
                                     {"tag": "li", "filhos": ["item ", {"tag": "span", "class": "marca marca-relato", "filhos": ["[relato]"]}]}]},
            {"tag": "ol", "filhos": [{"tag": "li", "filhos": ["primeiro"]}, {"tag": "li", "filhos": ["segundo"]}]},
            {"tag": "hr", "filhos": []},
            {"tag": "h5", "filhos": ["Sub ", {"tag": "span", "class": "marca marca-inferencia", "filhos": ["[inferência]"]}]},
            {"tag": "p", "filhos": ["<img src=x onerror=alert(1)> e <script>x</script>"]},
        ]
        self.assertEqual(saida, esperado)

    def test_marcas_e_titulos_do_texto_real(self):
        bruto = (ROOT / "historia" / "tomo-01" / f"{TEXTO_REAL}.md").read_text(encoding="utf-8")
        nos = self.roda("", hp.frontmatter(bruto)[1])["real"]
        contagem = {}

        def conta(no):
            if isinstance(no, dict):
                contagem[no["tag"]] = contagem.get(no["tag"], 0) + 1
                if "class" in no:
                    contagem[no["class"]] = contagem.get(no["class"], 0) + 1
                for filho in no["filhos"]:
                    conta(filho)

        for no in nos:
            conta(no)
        for classe in ("marca marca-medido", "marca marca-relato", "marca marca-inferencia"):
            self.assertGreater(contagem.get(classe, 0), 0, classe)
        self.assertGreater(contagem.get("h3", 0), 0, "## do texto vira h3")
        self.assertGreater(contagem.get("ul", 0) + contagem.get("ol", 0), 0)
        self.assertEqual(contagem.get("script", 0) + contagem.get("img", 0), 0)

    def test_historia_js_sem_html_dinamico(self):
        for proibido in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
            with self.subTest(proibido=proibido):
                self.assertNotIn(proibido, JS)

    def test_ouvir_chama_a_rota_e_mostra_o_resultado(self):
        self.assertIn('"/api/historia/ouvir"', JS)
        self.assertIn('method: "POST"', JS)
        self.assertIn("JSON.stringify({tomo: textoAberto.tomo, texto: textoAberto.id})", JS)
        self.assertIn("dados.falou", JS)
        self.assertIn("if (!textoAberto) return;", JS)
        self.assertIn("botaoOuvir.addEventListener", JS)
        self.assertIn("botao.disabled = !textoAberto", JS)
        self.assertIn('"/api/historia/texto?tomo="', JS)
