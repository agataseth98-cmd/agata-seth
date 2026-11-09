"""Testes do painel unificado (spec em redesign/painel_operacional/spec/spec.md, decidida em 07/11/2026).

Cada método corresponde a um critério automático de spec/acceptance.json. Os de rota sobem o servidor
numa porta livre (127.0.0.1). O de globais roda os cinco scripts do /prototipo no mesmo contexto vm,
com um DOM simulado (node), como o navegador faria: nome repetido vira erro ou aparece como global.
"""
import http.client
import importlib.util
import json
import os
import re
import subprocess
import tempfile
import threading
import unittest
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE / "spec" / "spec.md"
HTML = (HERE / "prototipo.html").read_text(encoding="utf-8")
CSS = (HERE / "prototipo.css").read_text(encoding="utf-8")
SCRIPTS = ["prototipo.js", "abrir.js", "nova_versao.js", "conselho-rede/app.js", "operator_console/app.js"]
JS = {arq: (HERE / arq).read_text(encoding="utf-8") for arq in SCRIPTS}
JS_TODOS = "\n".join(JS.values())

SECOES = ["panorama", "conversa", "conselho", "sistema", "conhecimento", "custos", "qualidade"]
SUBS_POR_SECAO = {
    "panorama": ["panorama", "visao", "capacidades", "plano", "frentes"],
    "conversa": ["conversa"],
    # conselho-memoria: aba Memória compartilhada, pedida pelo Humano em 07/11/2026 (leitura do cache do Conselho).
    "conselho": ["conselho", "conselho-memoria"],
    "sistema": ["operacao", "integracoes", "modelos", "manutencao", "nv-corpo", "nv-metacognicao", "nv-conexoes"],
    "conhecimento": ["memoria", "grafo", "documentacao", "nv-alexandria", "nv-acervo"],
    "custos": ["nv-orcamento", "nv-tarifas"],
    "qualidade": ["operator-console", "qualidade", "sdd", "lacunas", "nv-avaliacao", "nv-sentidos"],
}
ARQUIVOS_RETIRADOS = ["/app.js", "/styles.css", "/frentes.js", "/nova_versao.css",
                      "/conselho-rede/style.css", "/operator_console/style.css"]
# Estados que cada seção com API precisa ter no HTML.
ESTADOS = ("carregando", "vazio", "erro")

_NODE_GLOBAIS = r"""
const fs = require('fs'); const path = require('path'); const vm = require('vm');
process.on('unhandledRejection', () => {});
const dir = process.argv[process.argv.length - 1];
const arquivos = JSON.parse(process.env.ARQUIVOS_PAINEL);
function coisa() {
  const f = function () {};
  return new Proxy(f, {
    get(t, k) {
      if (k === Symbol.iterator) return function* () {};
      if (k === Symbol.toPrimitive) return () => '';
      if (k === 'then') return undefined;
      if (k === 'value' || k === 'textContent' || k === 'innerText' || k === 'className') return '';
      if (k === 'length') return 0;
      return coisa();
    },
    apply() { return coisa(); },
    construct() { return coisa(); },
    set() { return true; },
  });
}
const ctx = {};
ctx.window = ctx; ctx.document = coisa(); ctx.location = {hash: ''}; ctx.history = coisa();
ctx.localStorage = coisa(); ctx.fetch = coisa(); ctx.setTimeout = () => 0; ctx.clearTimeout = () => {};
ctx.setInterval = () => 0; ctx.clearInterval = () => {}; ctx.addEventListener = () => {};
ctx.AbortController = function () { this.signal = {}; this.abort = () => {}; };
ctx.Node = function () {};
vm.createContext(ctx);
const antes = new Set(Object.getOwnPropertyNames(ctx));
const erros = [];
for (const arq of arquivos) {
  try { vm.runInContext(fs.readFileSync(path.join(dir, arq), 'utf8'), ctx, {filename: arq}); }
  catch (e) { erros.push(arq + ': ' + e.message); }
}
const novos = Object.getOwnPropertyNames(ctx).filter((n) => !antes.has(n));
console.log(JSON.stringify({erros, novos}));
"""


def _carrega_servidor():
    spec = importlib.util.spec_from_file_location("painel_unificado_teste", HERE / "server.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


panel = _carrega_servidor()


class Estrutura(HTMLParser):
    """Para cada seção (class 'secao'): ids, subpainéis, estados e campos de busca. Pilha de <section> para achar a seção."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pilha = []
        self.secoes = []
        self.botoes_menu = []
        self.sub_em = {}
        self.ids_em = {}
        self.estados_em = {}
        self.campos_em = {}
        self.opcoes_escopo = []
        self._no_escopo = False
        self.cadeia = {}

    def _secao_atual(self):
        for nome in reversed(self.pilha):
            if nome:
                return nome
        return None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "section":
            nome = None
            if "secao" in classes:
                nome = a.get("id")
                self.secoes.append(nome)
            self.pilha.append(nome)
        atual = self._secao_atual()
        if tag == "button" and "data-secao" in a:
            self.botoes_menu.append(a["data-secao"])
        if tag == "div" and "sub" in classes and atual:
            self.sub_em.setdefault(atual, []).append(a.get("data-sub"))
            if a.get("data-secao") != atual:
                self.sub_em.setdefault("_erro", []).append(a.get("id"))
        if a.get("id") and atual:
            self.ids_em.setdefault(atual, set()).add(a["id"])
        if a.get("data-estado") and atual:
            self.estados_em.setdefault(atual, set()).add(a["data-estado"])
        if tag == "input" and atual:
            self.campos_em.setdefault(atual, []).append(a.get("type", "text"))
        if a.get("id") == "conhecimento-escopo":
            self._no_escopo = True
        if tag == "option" and self._no_escopo:
            self.opcoes_escopo.append(a.get("value"))
        if tag == "select" and a.get("id") != "conhecimento-escopo":
            self._no_escopo = False

    def handle_endtag(self, tag):
        if tag == "section" and self.pilha:
            self.pilha.pop()
        if tag == "select":
            self._no_escopo = False


def estrutura():
    parser = Estrutura()
    parser.feed(HTML)
    return parser


class ServidorDeTeste(unittest.TestCase):
    """Sobe o servidor do painel numa porta livre para os testes de rota."""

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

    def pede(self, caminho, metodo="GET"):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=5)
        try:
            conn.request(metodo, caminho, headers={})
            resposta = conn.getresponse()
            return resposta.status, resposta.read(), {k.lower(): v for k, v in resposta.getheaders()}
        finally:
            conn.close()


class RotasDaTelaUnicaTests(ServidorDeTeste):
    def test_telas_antigas_redirecionam_para_a_secao_certa(self):
        esperado = {
            "/": "/prototipo#panorama",
            "/index.html": "/prototipo#panorama",
            "/frentes": "/prototipo#panorama",
            "/operator_console": "/prototipo#qualidade",
            "/operator_console/": "/prototipo#qualidade",
            "/conselho-rede": "/prototipo#conselho",
            "/conselho-rede/": "/prototipo#conselho",
        }
        for caminho, destino in esperado.items():
            with self.subTest(caminho=caminho):
                status, _, cabecalhos = self.pede(caminho)
                self.assertEqual(status, 302)
                self.assertEqual(cabecalhos["location"], destino)
        self.assertEqual(self.pede("/prototipo")[0], 200)

    def test_rotas_de_api_e_chamadas_do_js_nao_mudam(self):
        servidor = (HERE / "server.py").read_text(encoding="utf-8")
        chamadas = set()
        for texto in JS.values():
            chamadas.update(re.findall(r"""["'`](/api/[A-Za-z0-9/_-]+)""", texto))
        self.assertTrue(chamadas, "nenhuma chamada /api encontrada no JS")
        faltam = sorted(c for c in chamadas if c not in servidor)
        self.assertEqual(faltam, [], "o JS chama caminho que o servidor não tem")

    def test_csp_continua_script_e_style_self(self):
        status, _, cabecalhos = self.pede("/prototipo")
        self.assertEqual(status, 200)
        csp = cabecalhos["content-security-policy"]
        self.assertIn("script-src 'self'", csp)
        self.assertIn("style-src 'self'", csp)


class TelaUnicaTests(ServidorDeTeste):
    def test_prototipo_tem_so_sete_secoes(self):
        e = estrutura()
        self.assertEqual(e.secoes, SECOES)
        self.assertEqual(e.botoes_menu, SECOES)

    def test_conselho_so_abre_modelos_ao_entrar_pelo_menu(self):
        js = (HERE / "abrir.js").read_text(encoding="utf-8")
        self.assertIn('button[data-secao="conselho"]', js)
        self.assertNotIn("querySelectorAll('[data-secao=\"conselho\"]", js)

    def test_cada_tela_antiga_tem_subpainel_na_secao_certa(self):
        e = estrutura()
        self.assertNotIn("_erro", e.sub_em, "subpainel com data-secao diferente da seção onde está")
        for secao, subs in SUBS_POR_SECAO.items():
            with self.subTest(secao=secao):
                self.assertEqual(e.sub_em.get(secao), subs)
                for sub in subs:
                    self.assertIn(f'id="sub-{sub}"', HTML)

    def test_cada_funcao_do_mapeamento_existe_na_tela(self):
        texto = SPEC.read_text(encoding="utf-8")
        mapa = texto[texto.index("## Mapeamento de funções"): texto.index("## Critérios de aceite")]
        faltam = []
        for linha in mapa.split("\n"):
            if not linha.startswith("| "):
                continue
            colunas = [c.strip() for c in linha.strip().strip("|").split("|")]
            if len(colunas) < 4 or colunas[2] not in SECOES:
                continue
            for token in re.findall(r"`([^`]+)`", colunas[3]):
                if not _existe_na_tela(token):
                    faltam.append(f"{colunas[2]}: {token}")
        self.assertEqual(faltam, [])

    def test_hash_escolhe_a_secao_e_cai_em_panorama(self):
        js = JS["prototipo.js"]
        self.assertIn("location.hash", js)
        self.assertIn('window.addEventListener("hashchange", aoMudarHash)', js)
        self.assertIn('SECOES.includes(nome) ? nome : "panorama"', js)
        self.assertIn("aoMudarHash();\n})();", js)
        abertas = [(m.group(1), "hidden" in m.group(0)) for m in re.finditer(r'<section class="secao" id="([a-z]+)"[^>]*>', HTML)]
        self.assertEqual(abertas[0], ("panorama", False), "panorama deve abrir visível")
        self.assertTrue(all(oculta for _, oculta in abertas[1:]), "só panorama começa aberta")

    def test_html_sem_style_nem_script_inline(self):
        self.assertIsNone(re.search(r"(?<![\w-])style\s*=", HTML, re.I))
        self.assertIsNone(re.search(r"<style\b", HTML, re.I))
        scripts = re.findall(r"<script\b([^>]*)>", HTML, re.I)
        self.assertTrue(scripts)
        self.assertTrue(all("src=" in atributos for atributos in scripts), "script sem src")

    def test_uma_so_folha_de_estilo(self):
        folhas = re.findall(r'<link rel="stylesheet" href="([^"]+)"', HTML)
        self.assertEqual(folhas, ["prototipo.css"])
        for arq in ("nova_versao.css", "styles.css", '"frentes.js"'):
            self.assertNotIn(arq, HTML)
        self.assertEqual(self.pede("/prototipo.css")[0], 200)
        for caminho in ARQUIVOS_RETIRADOS:
            with self.subTest(caminho=caminho):
                self.assertEqual(self.pede(caminho)[0], 404)

    def test_tokens_em_root_e_sem_cor_literal_fora(self):
        css = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
        raizes = re.findall(r":root\s*\{([^}]*)\}", css)
        self.assertEqual(len(raizes), 1, "deve haver um único :root")
        raiz = raizes[0]
        self.assertGreaterEqual(len(re.findall(r"--[\w-]+\s*:", raiz)), 19)
        for token in ("--sans", "--serif", "--mono", "--paper", "--ink", "--teal"):
            self.assertIn(token + ":", raiz)
        fora = css.replace(re.search(r":root\s*\{[^}]*\}", css).group(0), "")
        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", fora), [], "cor hexadecimal fora de :root")
        self.assertEqual(re.findall(r"rgba?\(", fora), [], "cor rgb literal fora de :root")
        definidas = set(re.findall(r"(--[\w-]+)\s*:", raiz))
        usadas = set(re.findall(r"var\(\s*(--[\w-]+)", css))
        self.assertEqual(sorted(usadas - definidas), [], "var() sem definição no :root")

    def test_toda_classe_do_html_tem_regra_no_css(self):
        css = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
        seletores = " ".join(re.findall(r"([^{}]+)\{", css))
        classes = set()
        for valor in re.findall(r'class="([^"]*)"', HTML):
            classes.update(valor.split())
        sem_regra = sorted(c for c in classes - set(GANCHOS_JS)
                           if not re.search(rf"\.{re.escape(c)}(?![\w-])", seletores))
        self.assertEqual(sem_regra, [])

    def test_scripts_sem_globais_repetidos(self):
        import os
        ambiente = dict(os.environ, ARQUIVOS_PAINEL=json.dumps(SCRIPTS))
        resultado = subprocess.run(["node", "-e", _NODE_GLOBAIS, str(HERE)], capture_output=True,
                                   text=True, timeout=120, env=ambiente)
        if resultado.returncode != 0 and not resultado.stdout:
            self.fail("node não rodou (não medido): " + resultado.stderr[-300:])
        medido = json.loads(resultado.stdout.strip().splitlines()[-1])
        self.assertEqual(medido["erros"], [], "erro ao carregar os scripts juntos")
        self.assertEqual(sorted(set(medido["novos"]) - {"AgataPainel"}), [],
                         "script declarou nome global além de window.AgataPainel")

    def test_secoes_com_api_tem_estados(self):
        e = estrutura()
        for secao in SECOES:
            with self.subTest(secao=secao):
                self.assertTrue(set(ESTADOS) <= e.estados_em.get(secao, set()))

    def test_conhecimento_tem_uma_busca_so(self):
        e = estrutura()
        self.assertEqual(e.campos_em["conhecimento"].count("search"), 1)
        for velho in ('id="wiki-form"', 'id="wiki-query"', 'id="nv-consulta"', 'id="nv-ext-consulta"', 'id="nv-ext-pesquisar"'):
            self.assertNotIn(velho, HTML)
        self.assertEqual(e.opcoes_escopo, ["dentro", "fora", "documentacao"])
        self.assertIn('"documentacao"', JS["prototipo.js"])
        self.assertIn("AgataPainel.buscarAcervo", JS["nova_versao.js"])
        self.assertIn("/api/wiki/search", JS["prototipo.js"])

    def test_custos_tem_orcamento_eventos_e_tarifas(self):
        import nova_versao_painel
        e = estrutura()
        self.assertIn("nv-orcamento", e.sub_em["custos"])
        self.assertIn("nv-tarifas", e.sub_em["custos"])
        ids_custos = e.ids_em["custos"]
        for id_ in ("nv-orc-salvar", "nv-orc-reais", "nv-eventos-titulo", "nv-api-provedor",
                    "nv-api-modelo", "nv-tar-entrada", "nv-api-ajustar"):
            with self.subTest(id=id_):
                self.assertIn(id_, ids_custos)
        for acao in ("salvar_orcamento", "ajustar_conexao"):
            with self.subTest(acao=acao):
                self.assertIn(acao, nova_versao_painel.ACOES)
                self.assertIn(f'"{acao}"', JS["nova_versao.js"])

    def test_operator_console_sem_iframe_na_qualidade(self):
        e = estrutura()
        self.assertNotIn("<iframe", HTML)
        self.assertIn("sub-operator-console", [f"sub-{s}" for s in e.sub_em["qualidade"]])
        self.assertIn("oc-raiz", e.ids_em["qualidade"])
        oc = JS["operator_console/app.js"]
        self.assertTrue(oc.lstrip().startswith("//"))
        self.assertIn("(function () {", oc)
        self.assertIn("getElementById('oc-raiz')", oc)


def _registro(n, texto, autor="Seth", tipo="fato"):
    """Linha do cache no formato de cache_conselho (cadeia zerada: a rota só lê, não verifica)."""
    return {"n": n, "ts": "2026-11-07T10:%02d:00-0300" % (n % 60), "autor": autor, "tipo": tipo,
            "texto": texto, "fonte": None, "ant": "0" * 64, "h": "0" * 64}


class MemoriaConselhoTests(ServidorDeTeste):
    """Aba Memória compartilhada (pedida pelo Humano em 07/11/2026): rota só de leitura do cache do Conselho.

    O cache é trocado por um arquivo temporário, e o filtro de dado pessoal da gravação é o oráculo.
    """

    def setUp(self):
        self.cache = panel._memoria_conselho_modulo()
        self.tmp = tempfile.TemporaryDirectory()
        self.arq = Path(self.tmp.name) / "cache" / "cache.jsonl"
        self.p20 = Path(self.tmp.name) / "p20.txt"
        self.p20.write_text("apelido|Zuleica[0-9]+|Zuleica42\n", encoding="utf-8")
        self.salvo = (self.cache.ARQ, self.cache.LISTA_P20)
        self.cache.ARQ, self.cache.LISTA_P20 = self.arq, self.p20

    def tearDown(self):
        self.cache.ARQ, self.cache.LISTA_P20 = self.salvo
        self.tmp.cleanup()

    def grava(self, registros):
        self.arq.parent.mkdir(parents=True, exist_ok=True)
        self.arq.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in registros), encoding="utf-8")

    def pede_json(self, caminho, cabecalhos=None):
        conn = http.client.HTTPConnection("127.0.0.1", panel.PORT, timeout=5)
        try:
            conn.request("GET", caminho, headers=cabecalhos or {})
            resposta = conn.getresponse()
            return resposta.status, resposta.read(), {k.lower(): v for k, v in resposta.getheaders()}
        finally:
            conn.close()

    def test_memoria_conselho_devolve_as_mais_recentes(self):
        self.grava([_registro(1, "primeira"), _registro(2, "segunda", autor="Claude Code", tipo="decisao"),
                    _registro(3, "terceira", tipo="pendencia")])
        status, corpo, cabecalhos = self.pede_json("/api/conselho/memoria?n=2")
        self.assertEqual(status, 200)
        self.assertIn("application/json", cabecalhos["content-type"])
        self.assertEqual(cabecalhos["cache-control"], "no-store")
        dados = json.loads(corpo)
        self.assertEqual(dados["estado"], "ok")
        self.assertEqual(dados["n"], 2)
        self.assertEqual([e["n"] for e in dados["entradas"]], [3, 2], "mais recentes primeiro")
        self.assertEqual(set(dados["entradas"][0]), {"n", "data_hora", "autor", "tipo", "texto"})
        self.assertEqual(dados["entradas"][0]["data_hora"], "07/11/2026 10:03")
        self.assertEqual(dados["entradas"][1]["autor"], "Claude Code")
        self.assertEqual(dados["entradas"][1]["tipo"], "decisao")
        self.assertTrue(dados["observed_at"] and dados["fresh_until"])

    def test_memoria_conselho_limita_n(self):
        self.grava([_registro(i, f"entrada {i}") for i in range(1, 46)])
        dados = json.loads(self.pede_json("/api/conselho/memoria")[1])
        self.assertEqual((dados["n"], len(dados["entradas"])), (40, 40), "padrão é 40")
        self.grava([_registro(i, f"entrada {i}") for i in range(1, 206)])
        dados = json.loads(self.pede_json("/api/conselho/memoria?n=500")[1])
        self.assertEqual((dados["n"], len(dados["entradas"])), (200, 200), "acima de 200 corta em 200")
        for ruim in ("0", "-1", "abc", "1.5"):
            with self.subTest(n=ruim):
                self.assertEqual(self.pede_json(f"/api/conselho/memoria?n={ruim}")[0], 400)
        # n vazio é o mesmo que não informar n (parse_qs descarta valor em branco): vale o padrão.
        dados = json.loads(self.pede_json("/api/conselho/memoria?n=")[1])
        self.assertEqual(dados["n"], 40)

    def test_memoria_conselho_cache_ausente_ou_vazio_da_estado_vazio(self):
        for cenario in ("ausente", "vazio"):
            with self.subTest(cenario=cenario):
                if cenario == "vazio":
                    self.grava([])
                else:
                    self.cache.ARQ = Path(self.tmp.name) / "nao-existe" / "cache.jsonl"
                status, corpo, _ = self.pede_json("/api/conselho/memoria?n=40")
                self.assertEqual(status, 200)
                dados = json.loads(corpo)
                self.assertEqual((dados["estado"], dados["entradas"]), ("vazio", []))
                self.cache.ARQ = self.arq

    def test_memoria_conselho_filtra_dado_pessoal_e_segredo(self):
        self.grava([
            _registro(1, "escreva para fulano@exemplo.com e Zuleica42", autor="Claude Code", tipo="nota"),
            _registro(2, "chave sk-ant-api03-" + "A" * 40, tipo="nota"),
            _registro(3, "o gateway reiniciou às 11h04"),
        ])
        status, corpo, _ = self.pede_json("/api/conselho/memoria?n=40")
        self.assertEqual(status, 200)
        texto_todo = corpo.decode("utf-8")
        for proibido in ("fulano@exemplo.com", "Zuleica42", "sk-ant-api03-"):
            self.assertNotIn(proibido, texto_todo)
        entradas = json.loads(corpo)["entradas"]
        self.assertIn("[pessoal-email removido]", entradas[2]["texto"])
        self.assertEqual(entradas[1]["texto"], panel.MEMORIA_CONSELHO_RECUSADO, "segredo não sai, só a marca")
        for e in entradas:
            for campo in ("autor", "texto", "tipo"):
                with self.subTest(n=e["n"], campo=campo):
                    self.assertEqual(self.cache.filtrar(e[campo]), e[campo], "texto que sai já passou pelo filtro")

    def test_memoria_conselho_so_le_e_ignora_caminho_do_cliente(self):
        self.grava([_registro(1, "uma"), _registro(2, "duas")])
        antes = (self.arq.read_bytes(), sorted(os.listdir(self.arq.parent)))
        sem_caminho = self.pede_json("/api/conselho/memoria?n=2")[1]
        com_caminho = self.pede_json("/api/conselho/memoria?n=2&arquivo=/etc/hostname&caminho=../x")[1]
        self.assertEqual(com_caminho, sem_caminho, "o caminho vindo do cliente não muda a leitura")
        self.assertEqual((self.arq.read_bytes(), sorted(os.listdir(self.arq.parent))), antes, "a leitura não grava")
        servidor = (HERE / "server.py").read_text(encoding="utf-8")
        trecho = servidor[servidor.index("def _conselho_memoria"):servidor.index("def _grafo")]
        self.assertNotIn("anotar", trecho)
        self.assertNotIn("ARQ", trecho)
        self.assertNotIn("open(", trecho)

    def test_memoria_conselho_recusa_origem_cruzada(self):
        self.grava([_registro(1, "uma")])
        for cabecalhos in ({"Origin": "http://evil.example"}, {"Sec-Fetch-Site": "cross-site"}):
            with self.subTest(cabecalhos=cabecalhos):
                self.assertEqual(self.pede_json("/api/conselho/memoria?n=2", cabecalhos)[0], 403)
        self.assertEqual(self.pede_json("/api/conselho/memoria?n=2")[0], 200)

    def test_aba_memoria_fica_na_secao_conselho(self):
        e = estrutura()
        self.assertEqual(e.sub_em["conselho"], ["conselho", "conselho-memoria"])
        inicio = HTML.index('<section class="secao" id="conselho"')
        fim = HTML.index('<section class="secao" id="sistema"')
        secao = HTML[inicio:fim]
        self.assertIn('<nav class="abas"', secao)
        self.assertIn('<button type="button" data-sub="conselho-memoria"', secao)
        bloco = secao[secao.index('id="sub-conselho-memoria"'):]
        for estado in ESTADOS:
            self.assertIn(f'data-estado="{estado}"', bloco)
        for id_ in ("memoria-lista", "memoria-tipo", "memoria-atualizar", "memoria-resumo"):
            self.assertIn(f'id="{id_}"', bloco)
        self.assertEqual(re.findall(r'<option value="([^"]+)"', bloco),
                         ["todos", "fato", "decisao", "pendencia", "nota", "diario"])
        js = JS["prototipo.js"]
        self.assertIn('"conselho-memoria": () => carregarMemoriaConselho()', js)
        self.assertIn('"/api/conselho/memoria?n=40"', js)
        trecho = js[js.index("// Memória compartilhada do Conselho"):js.index("// Entrada: a seção vem do hash")]
        self.assertNotIn("innerHTML", trecho, "texto do cache entra só por textContent")
        self.assertNotIn("insertAdjacentHTML", trecho)
        # abrir.js escuta todo [data-secao="conselho"] (inclusive esta aba): o clique aqui não pode chegar a ele.
        self.assertIn('byId("sub-conselho-memoria").addEventListener("click", (e) => e.stopImmediatePropagation())', js)
        self.assertLess(HTML.index('src="prototipo.js"'), HTML.index('src="abrir.js"'),
                        "prototipo.js precisa carregar antes de abrir.js para o stopImmediatePropagation valer")


def _existe_na_tela(token):
    """Um token do mapeamento existe se for arquivo do painel, id, classe, atributo data-* ou nome nos scripts."""
    if token.endswith((".js", ".html", ".css", ".py")):
        return (HERE / token).exists()
    if token.startswith("/"):
        return f'"{token}"' in JS_TODOS or f"'{token}'" in JS_TODOS or token in JS_TODOS
    if re.search(rf'\bid="{re.escape(token)}"', HTML):
        return True
    for valor in re.findall(r'class="([^"]*)"', HTML):
        if token in valor.split():
            return True
    if token.startswith("data-") and f"{token}=" in HTML:
        return True
    return bool(re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", JS_TODOS))


# Ganchos de JavaScript ou de marcação, sem regra própria: o estilo vem da classe com que dividem o elemento.
# Criar uma regra aqui mudaria o layout sem medição visual; por isso ficam listadas com o motivo.
GANCHOS_JS = {
    "capability-list": "marcador da grade de capacidades; o estilo vem de .cards",
    "close-dialog": "gancho do JS que fecha o diálogo de evidência; o estilo vem de .btn",
    "close-vault": "gancho do JS que fecha o diálogo do vault; o estilo vem de .btn",
    "evidence": "gancho do JS dos botões EVIDÊNCIA; o estilo vem de .btn",
    "integration-legend": "marcador da legenda de integrações; o estilo vem de .filterbar",
    "seth-panel": "marcador do painel da Seth; o estilo vem de .panel",
}


if __name__ == "__main__":
    unittest.main()
