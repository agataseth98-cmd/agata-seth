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
SCRIPTS = ["prototipo.js", "abrir.js", "nova_versao.js", "conselho-rede/app.js", "operator_console/app.js", "historia.js"]
JS = {arq: (HERE / arq).read_text(encoding="utf-8") for arq in SCRIPTS}
JS_TODOS = "\n".join(JS.values())

SECOES = ["panorama", "conversa", "conselho", "sistema", "conhecimento", "historia", "custos", "qualidade"]
SUBS_POR_SECAO = {
    # importantes: aba do Panorama criada em 11/11/2026 (pedido do Humano); é a única mudança nesta lista.
    # 17/11/2026: "O que posso fazer" saiu do Panorama (virou atalho para Sistema > Integrações).
    "panorama": ["panorama", "visao", "plano", "frentes", "importantes"],
    "conversa": ["conversa"],
    # conselho-memoria: aba Memória compartilhada, pedida pelo Humano em 07/11/2026 (leitura do cache do Conselho).
    "conselho": ["conselho", "conselho-memoria"],
    # 17/11/2026: Equipe, Backup e Saída de rede entram como abas de Sistema (leitura nova).
    "sistema": ["operacao", "integracoes", "modelos", "manutencao", "nv-corpo", "nv-metacognicao", "nv-conexoes",
                "equipe", "backup", "saida-rede"],
    "conhecimento": ["memoria", "grafo", "documentacao", "nv-alexandria", "nv-acervo"],
    # historia: seção nova de 11/11/2026 (texto da História, só leitura, e o Ouvir); ver test_historia.py.
    "historia": ["historia"],
    "custos": ["nv-orcamento", "nv-tarifas"],
    # 17/11/2026: Perímetro e CI entram como abas de Qualidade (último resultado gravado).
    "qualidade": ["operator-console", "qualidade", "sdd", "lacunas", "perimetro", "ci", "nv-avaliacao", "nv-sentidos"],
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
    def test_prototipo_tem_so_oito_secoes(self):
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

    def test_panorama_tem_botao_que_abre_estado_operacional(self):
        # C2 (16/11/2026): o botão voltou ao bloco de status do herói, ao lado de Atualizar, com os mesmos atributos.
        inicio = HTML.index('<section class="secao" id="panorama"')
        fim = HTML.index('<section class="secao" id="', inicio + 1)
        trecho = HTML[inicio:fim]
        botoes = [b for b in re.findall(r"<button\b[^>]*>[^<]*</button>", trecho)
                  if 'data-open-page="sistema"' in b and 'data-open-sub="operacao"' in b]
        self.assertEqual(len(botoes), 1, "o Panorama deve ter exatamente um botão para Estado operacional")
        self.assertIn(">Abrir Estado operacional</button>", botoes[0])
        bloco = trecho[trecho.index('class="hero-stamp"'): trecho.index('class="callout"')]
        self.assertIn('id="refresh-main"', bloco)
        self.assertIn(botoes[0], bloco, "o botão tem de estar no bloco de status do herói")
        # quem trata data-open-page continua existindo no JS
        self.assertIn("const b = e.target.closest(\"[data-open-page]\")", JS["prototipo.js"])
        self.assertIn("irPara(b.dataset.openPage, b.dataset.openSub)", JS["prototipo.js"])


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
        # observed_at e fresh_until saem da igualdade porque são a hora de cada pedido; o resto segue inteiro.
        ISO_COM_FUSO = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$"
        for corpo in (sem_caminho, com_caminho):
            dados = json.loads(corpo)
            for campo in ("observed_at", "fresh_until"):
                self.assertIn(campo, dados, "a resposta da memória traz a janela de leitura")
                self.assertRegex(dados[campo], ISO_COM_FUSO, "janela de leitura em ISO 8601 com fuso")
        def sem_janela(corpo):
            dados = json.loads(corpo)
            dados.pop("observed_at", None)
            dados.pop("fresh_until", None)
            return dados
        self.assertEqual(sem_janela(com_caminho), sem_janela(sem_caminho), "o caminho vindo do cliente não muda a leitura")
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
    "seth-panel": "marcador do painel da Seth; o estilo vem de .panel",
}


def _tokens_do_bloco(bloco):
    return {nome: valor.strip() for nome, valor in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", bloco)}


def _valor_resolvido(nome, tokens):
    valor = tokens[nome]
    m = re.fullmatch(r"var\((--[\w-]+)\)", valor)
    return _valor_resolvido(m.group(1), tokens) if m else valor


def _contraste(a, b):
    def luminancia(hex_):
        canais = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _margens_verticais_auto(bloco):
    """Declarações de margem que deixam o eixo vertical (topo ou base) em auto.
    Em `margin`, 2 valores são V H (vertical é o primeiro); 3 valores são T H B; 4 são T R B L."""
    achados = []
    for nome, valor in re.findall(r"(?<![\w-])(margin(?:-top|-bottom|-block(?:-start|-end)?)?)\s*:\s*([^;}]*)", bloco, flags=re.I):
        partes = valor.replace("!important", "").split()
        if not partes:
            continue
        vertical = [partes[0], partes[2] if len(partes) >= 3 else partes[0]] if nome.lower() == "margin" else partes
        if any(p.lower() == "auto" for p in vertical):
            achados.append(f"{nome}:{valor.strip()}")
    return achados


class AcabamentoTests(unittest.TestCase):
    """Acabamento de 16/11/2026 (F15): texto, estilo e contraste lidos dos arquivos, sem servidor."""

    def test_pagina_e_scripts_sem_3080_goose_nem_librechat(self):
        proibidos = ("3080", "Goose", "LibreChat")
        excecao = r"PREFIXO_IMPORTADO = /^\[LibreChat\] +/"   # única linha: prefixo histórico de título importado
        achados = []
        for nome, texto in {"prototipo.html": HTML, **JS}.items():
            for n, linha in enumerate(texto.splitlines(), 1):
                if excecao in linha:
                    continue
                achados += [f"{nome}:{n} {termo}" for termo in proibidos if termo in linha]
        self.assertEqual(achados, [])
        self.assertEqual(sum(excecao in linha for linha in JS["prototipo.js"].splitlines()), 1)

    def test_html_sem_texto_fixo_que_afirma_estado(self):
        # Rótulos de filtro são controles (ficam fora da busca); fora deles, nenhuma frase fixa afirma estado.
        sem_filtros = re.sub(r'<div class="filterbar[^"]*">.*?</div>', "", HTML, flags=re.S).lower()
        proibidas = ["consta como pausado", "estados: ativo", "sem sonda nesta tela", "tudo disponível",
                     "quatro unidades"]
        self.assertEqual([p for p in proibidas if p in sem_filtros], [])

    def test_css_tem_no_maximo_9_fs_5_raios_sem_cor_nominal_e_main_sem_margem_auto(self):
        css = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
        self.assertLessEqual(len(set(re.findall(r"--fs-\d+", css))), 9)
        self.assertLessEqual(len(set(re.findall(r"--r-(?:\d+|pill)(?![\w-])", css))), 5)
        self.assertNotIn("--cor-", css)
        # C7 (16/11/2026): afirma o que se quer (topo) e recusa auto vertical em qualquer forma escrita.
        base = re.search(r"^main\s*\{([^}]*)\}", css, flags=re.M)
        self.assertIsNotNone(base, "regra base de main não achada")
        self.assertIn("align-self:start", re.sub(r"\s+", "", base.group(1)))
        for bloco in re.findall(r"(?<![\w-])main\s*\{([^}]*)\}", css):
            self.assertEqual(_margens_verticais_auto(bloco), [], bloco)

    def test_detector_de_margem_auto_recusa_as_formas_vertical_e_aceita_a_horizontal(self):
        for recusada in ("margin:auto", "margin: auto 0", "margin:0 0 auto", "margin-top:auto",
                         "margin-bottom: auto", "margin-block:auto", "margin:auto!important"):
            with self.subTest(recusada=recusada):
                self.assertTrue(_margens_verticais_auto(recusada))
        for aceita in ("margin:0 auto", "margin-left:auto", "margin-inline:auto", "margin:0"):
            with self.subTest(aceita=aceita):
                self.assertEqual(_margens_verticais_auto(aceita), [])

    def test_contraste_de_ink_e_muted_passa_4_5_nos_dois_temas(self):
        css = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
        raiz = _tokens_do_bloco(re.search(r":root\s*\{([^}]*)\}", css).group(1))
        claro = _tokens_do_bloco(re.search(r':root\[data-tema="claro"\]\s*\{([^}]*)\}', css).group(1))
        temas = {"escuro": raiz, "claro": {**raiz, **claro}}
        for tema, tokens in temas.items():
            for texto in ("--ink", "--muted"):
                for fundo in ("--paper", "--sheet"):
                    with self.subTest(tema=tema, texto=texto, fundo=fundo):
                        a = _valor_resolvido(texto, tokens)
                        b = _valor_resolvido(fundo, tokens)
                        self.assertRegex(a, r"^#[0-9a-fA-F]{6}$")
                        self.assertRegex(b, r"^#[0-9a-fA-F]{6}$")
                        self.assertGreaterEqual(_contraste(a, b), 4.5)



# Comportamento (C3, 16/11/2026): prototipo.js e nova_versao.js rodam de verdade num contexto node, com um DOM mínimo
# (o mesmo desenho de test_chat_ui.py e test_importantes_ui.py). O prototipo.js ganha, só neste contexto, uma linha que
# expõe render(); o arquivo em disco não muda. Nada sai da máquina: o fetch devolve 404 e o estado vem do cenário.
NODE_COMPORTAMENTO = r"""
const fs = require('fs'); const path = require('path'); const vm = require('vm');
process.on('unhandledRejection', () => {});
const cen = JSON.parse(fs.readFileSync(0, 'utf8')); const dir = process.env.PAINEL_DIR;
class No {}
class Texto extends No { constructor(t) { super(); this.textContent = String(t); } }
class Elemento extends No {
  constructor(tag) {
    super();
    this.tag = tag; this.texto = ''; this.children = []; this.hidden = false; this.className = ''; this.value = '';
    this.disabled = false; this.dataset = {}; this.attrs = {}; this.ouvintes = {}; this.style = {};
    this.classList = {add() {}, remove() {}, toggle() {}, contains() { return false; }};
  }
  get textContent() { return this.texto + this.children.map((c) => c.textContent).join(''); }
  set textContent(v) { this.children = []; this.texto = String(v); }
  append(...nos) { this.children.push(...nos); }
  replaceChildren(...nos) { this.children = nos; this.texto = ''; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; }
  addEventListener(tipo, fn) { (this.ouvintes[tipo] = this.ouvintes[tipo] || []).push(fn); }
  focus() {} blur() {} remove() {} select() {}
  closest() { return null; }
  querySelector() { return null; }
  querySelectorAll() { return []; }
}
const registro = new Map();
const elementoDoId = (id) => { if (!registro.has(id)) registro.set(id, new Elemento('id:' + id)); return registro.get(id); };
const documento = {
  visibilityState: 'visible', body: new Elemento('body'), documentElement: new Elemento('html'),
  getElementById: elementoDoId, querySelector() { return new Elemento('sel'); }, querySelectorAll() { return []; },
  createElement(tag) { return new Elemento(tag); }, createElementNS(ns, tag) { return new Elemento(tag); },
  createTextNode(t) { return new Texto(t); }, addEventListener() {}, removeEventListener() {},
};
const ctx = {};
ctx.window = ctx; ctx.document = documento; ctx.location = {hash: ''}; ctx.history = {};
ctx.localStorage = {getItem() { return null; }, setItem() {}, removeItem() {}};
ctx.navigator = {clipboard: {}}; ctx.Node = No;
ctx.fetch = async () => ({ok: false, status: 404, json: async () => ({}), text: async () => ''});
ctx.AbortController = function () { this.signal = {}; this.abort = () => {}; };
ctx.setTimeout = () => 0; ctx.clearTimeout = () => {}; ctx.setInterval = () => 0; ctx.clearInterval = () => {};
ctx.addEventListener = () => {};
vm.createContext(ctx);
const esperar = async () => { for (let i = 0; i < 50; i++) await new Promise((r) => setImmediate(r)); };
(async () => {
  const saida = {erros: []};
  try {
    if (cen.modo === 'ledger') {
      ctx.AgataPainel = {fetchJson: async () => cen.estado, marcarEstado() {}};
      vm.runInContext(fs.readFileSync(path.join(dir, 'nova_versao.js'), 'utf8'), ctx, {filename: 'nova_versao.js'});
      await ctx.AgataPainel.carregarNovaVersao('nv-orcamento');
      await esperar();
      saida.linhas = elementoDoId('nv-eventos').children.map((tr) => tr.textContent);
    } else {
      const fonte = fs.readFileSync(path.join(dir, 'prototipo.js'), 'utf8');
      const marca = 'aoMudarHash();\n})();';
      if (!fonte.includes(marca)) throw new Error('marca de fim do prototipo.js não achada');
      vm.runInContext(fonte.replace(marca, 'aoMudarHash();\nwindow.__teste = {render};\n})();'), ctx, {filename: 'prototipo.js'});
      await esperar();
      ctx.__teste.render(cen.snapshot);
      await esperar();
      saida.hero = elementoDoId('hero-status').textContent;
    }
  } catch (e) { saida.erros.push(String((e && e.stack) || e).slice(0, 400)); }
  console.log(JSON.stringify(saida));
})();
"""


def _roda_comportamento(cenario):
    ambiente = dict(os.environ, PAINEL_DIR=str(HERE))
    resultado = subprocess.run(["node", "-e", NODE_COMPORTAMENTO], input=json.dumps(cenario, ensure_ascii=False),
                               capture_output=True, text=True, timeout=120, env=ambiente)
    if resultado.returncode != 0 and not resultado.stdout:
        raise AssertionError("node não rodou (não medido): " + resultado.stderr[-400:])
    return json.loads(resultado.stdout.strip().splitlines()[-1])


class ComportamentoDoPainelTests(unittest.TestCase):
    """Critérios 146 e 147 (16/11/2026): o JS roda de verdade; não é leitura do texto do código."""

    def test_tabela_de_eventos_vazia_mostra_nenhum_evento_registrado(self):
        vazio = _roda_comportamento({"modo": "ledger", "estado": {"orcamento": None, "eventos": [], "ledger_ok": True}})
        self.assertEqual(vazio["erros"], [])
        self.assertEqual(len(vazio["linhas"]), 1)
        self.assertEqual(vazio["linhas"][0], "Nenhum evento registrado.")
        # controle: com um evento, a linha de vazio some (o teste não passa por acaso)
        evento = {"timestamp": "2026-11-16T10:00:00-03:00", "componente": "painel", "kind": "teste", "status": "ok", "source": "teste"}
        com = _roda_comportamento({"modo": "ledger", "estado": {"orcamento": None, "eventos": [evento], "ledger_ok": True}})
        self.assertEqual(com["erros"], [])
        self.assertEqual(len(com["linhas"]), 1)
        self.assertNotIn("Nenhum evento registrado.", com["linhas"][0])

    def test_linha_do_heroi_separa_nao_existe_de_sem_leitura(self):
        agora = "2026-11-16T10:00:00Z"
        ativo = {"unit": "seth-gateway.service", "state": "ok", "active_state": "active", "sub_state": "running",
                 "source": "systemctl --user", "observed_at": agora, "fresh_until": "2099-01-01T00:00:00Z", "error": None}
        ausente = {"unit": "piper-tts.service", "state": "ausente", "active_state": "inactive", "sub_state": "dead",
                   "source": "systemctl --user", "observed_at": agora, "fresh_until": None, "error": "ausente"}
        sem_leitura = {"unit": "openvino-whisper.service", "state": "unknown", "observed_at": None, "fresh_until": None, "error": None}
        snapshot = {"services": [ativo, ausente, sem_leitura], "timers": [], "git": {"state": "unknown"},
                    "chat": {"state": "unknown"}, "maintenance": [], "proposals": {"items": []},
                    "models": {"state": "unknown"}, "sem_leitura": ["openvino-whisper.service", "piper-tts.service"],
                    "observed_at": agora}
        medido = _roda_comportamento({"modo": "hero", "snapshot": snapshot})
        self.assertEqual(medido["erros"], [])
        hero = medido["hero"]
        self.assertIn("1 unidade não existe (escopo do usuário)", hero)
        self.assertIn("1 fonte sem leitura", hero)
        lacunas = hero.split("fonte sem leitura: ", 1)[1]
        self.assertIn("Whisper", lacunas)
        self.assertNotIn("Piper", lacunas, "o ausente não entra na lista de sem leitura")



class LoteConversaEstruturaTests(unittest.TestCase):
    """Lote painel-conversa-16-11 (16/11/2026): menu único, Conversa com compositor, Conhecimento numa tela e gaveta.

    Conferência de marcação e de texto do JS (o comportamento de clique fica em test_chat_ui.py, com DOM mínimo).
    """

    @staticmethod
    def bloco(abre, fecha):
        i = HTML.index(abre)
        return HTML[i:HTML.index(fecha, i) + len(fecha)]

    def test_menu_tem_nova_busca_secoes_conversas_e_rodape_nessa_ordem(self):
        aside = self.bloco('<aside class="sidebar"', "</aside>")
        marcas = ['id="seth-nova"', 'id="seth-busca"', 'data-secao="panorama"', 'id="seth-conversas"',
                  'id="organizar-abrir"', 'id="servicos-locais"']
        posicoes = [aside.index(m) for m in marcas]
        self.assertEqual(posicoes, sorted(posicoes), "ordem do menu: nova, busca, seções, conversas, rodapé")
        self.assertEqual(re.findall(r'data-secao="(\w+)"', aside), SECOES)

    def test_menu_sem_redundancia_de_nota_e_rodape_unico(self):
        self.assertNotIn("O Humano no centro", HTML)
        self.assertNotIn("human-note", HTML)
        self.assertNotIn("side-bottom", HTML)
        self.assertEqual(HTML.count('class="side-foot"'), 1)

    def test_conversa_sem_lista_duplicada_nem_busca_de_conversas(self):
        secao = self.bloco('<section class="secao" id="conversa"', "</section>")
        self.assertNotIn('class="seth-lista"', secao)
        self.assertNotIn('id="seth-conversas"', secao)
        self.assertNotIn('id="seth-busca"', secao)
        self.assertNotIn("<aside", secao)

    def test_busca_do_mapa_some_na_conversa(self):
        self.assertIn('id="mapa-busca"', HTML)
        self.assertIn('byId("mapa-busca").hidden = alvo.id === "conversa"', JS["prototipo.js"])

    def test_cabecalho_da_conversa_tem_titulo_status_modelo_temporaria_e_mais(self):
        secao = self.bloco('<section class="secao" id="conversa"', "</section>")
        cabecalho = secao[secao.index('<header class="seth-cabecalho">'):secao.index("</header>")]
        for id_ in ("seth-titulo", "seth-status", "seth-modelo", "seth-temporaria", "seth-mais-abrir", "seth-mais-menu",
                    "seth-copiar-ultima", "seth-export-json", "seth-export-md"):
            with self.subTest(id=id_):
                self.assertIn(f'id="{id_}"', cabecalho)
        self.assertIn('aria-haspopup="menu"', cabecalho)
        self.assertIn('role="menu"', cabecalho)

    def test_compositor_na_base_com_ditar_enviar_parar_e_contexto_depois(self):
        secao = self.bloco('<section class="secao" id="conversa"', "</section>")
        ordem = [secao.index(f'id="{i}"') for i in ("seth-input", "seth-ditado", "seth-send", "seth-parar",
                                                     "seth-contexto", "seth-voz-estado", "seth-temporaria-aviso",
                                                     "seth-salvar-aviso", "seth-origem")]
        self.assertEqual(ordem, sorted(ordem), "compositor na base; abaixo dele, contexto, voz e avisos (E3d)")
        self.assertRegex(secao, r'<button class="text-link" type="button" id="seth-parar" hidden>')

    def test_estado_vazio_central_e_ir_para_o_fim_comecam_certos(self):
        secao = self.bloco('<section class="secao" id="conversa"', "</section>")
        self.assertIn('id="seth-vazio-central"', secao)
        self.assertIn('id="seth-exemplos"', secao[secao.index('id="seth-vazio-central"'):])
        self.assertRegex(secao, r'<button class="seth-ir-fim" type="button" id="seth-ir-fim" hidden>')
        self.assertIn("central.hidden = caminho.length > 0", JS["prototipo.js"])

    def test_conhecimento_todos_os_blocos_a_vista_sem_abas(self):
        secao = self.bloco('<section class="secao" id="conhecimento"', '<section class="secao" id="historia"')
        self.assertIn('data-subs="juntos"', secao[:secao.index(">")])
        self.assertNotIn('class="abas"', secao)
        subs = ["sub-memoria", "sub-grafo", "sub-documentacao", "sub-nv-alexandria", "sub-nv-acervo"]
        for sub in subs:
            with self.subTest(sub=sub):
                tag = re.search(r'<div class="sub[^"]*" id="%s"[^>]*>' % sub, secao).group(0)
                self.assertNotIn(" hidden", tag)
        ordem = [secao.index(f'id="{s}"') for s in subs]
        self.assertEqual(ordem, sorted(ordem), "ordem: memória, grafo, documentação, alexandria, acervo")

    def test_ancoras_do_conhecimento_apontam_para_os_blocos(self):
        ancoras = re.findall(r'data-ancora="([^"]+)"', HTML)
        self.assertEqual(ancoras, ["sub-memoria", "sub-grafo", "sub-documentacao", "sub-nv-alexandria", "sub-nv-acervo"])
        for alvo in ancoras:
            self.assertIn(f'id="{alvo}"', HTML)
        self.assertIn("alvo.scrollIntoView({block: \"start\"})", JS["prototipo.js"])

    def test_cada_rota_carrega_uma_vez_por_abertura(self):
        js = JS["prototipo.js"]
        self.assertIn('const ROTA_DE_SUB = {integracoes: "detalhes", memoria: "detalhes"};', js)
        self.assertIn("if (feitas.has(rota)) return;", js)

    def test_erro_da_memoria_marca_conhecimento_e_integracoes_marcam_sistema(self):
        js = JS["prototipo.js"]
        trecho = js[js.index("async function loadDetails()"):js.index("function wikiLineSource")]
        self.assertIn('marcarEstado("conhecimento", "erro"', trecho)
        self.assertIn('marcarEstado("sistema", "erro"', trecho)

    def test_nova_versao_compartilha_a_leitura_do_estado(self):
        nv = JS["nova_versao.js"]
        self.assertIn("if (lendo) return lendo;", nv)
        self.assertEqual(nv.count('fetchJson("/api/nova-versao/estado"'), 1)

    def test_menu_de_acoes_tem_papeis_rotulo_e_esc(self):
        js = JS["prototipo.js"]
        self.assertIn('gatilho.setAttribute("aria-haspopup", "menu")', js)
        self.assertIn('menu.setAttribute("role", "menu")', js)
        self.assertIn('b.setAttribute("role", "menuitem")', js)
        self.assertIn('gatilho.setAttribute("aria-label", "Mais ações de " + tituloLido)', js)
        # J8 (16/11/2026): Esc fecha e devolve o foco ao gatilho pelo mesmo caminho da escolha (fecharMenuAberto(true)).
        self.assertIn('if (e.key === "Escape") { e.preventDefault(); fecharMenuAberto(true); return; }', js)

    def test_barra_do_item_tem_acoes_do_menu_e_nenhuma_some(self):
        js = JS["prototipo.js"]
        for rotulo in ("Renomear", "Fixar", "Arquivar", "Apagar", "Exportar JSON", "Exportar Markdown", "Pasta e marcadores"):
            with self.subTest(rotulo=rotulo):
                self.assertIn(rotulo, js)

    def test_barra_mostra_o_titulo_completo_no_title(self):
        self.assertIn('abrir.title = tituloLido + " · " + c.mensagens + " mensagens · " + c.atualizada;', JS["prototipo.js"])

    def test_slash_foca_a_busca_de_conversas(self):
        # C12a (16/11/2026): na Conversa, "/" foca a busca de conversas; nas outras seções, a busca do mapa.
        self.assertIn('if (e.key === "/") { e.preventDefault(); if (byId("conversa").hidden) byId("search").focus(); else byId("seth-busca").focus(); }', JS["prototipo.js"])

    def test_gaveta_botao_com_aria_e_fecha_com_esc_e_escolha(self):
        botao = re.search(r'<button class="menu-abrir"[^>]*>', HTML).group(0)
        self.assertIn('aria-controls="sidebar-principal"', botao)
        self.assertIn('aria-expanded="false"', botao)
        self.assertIn('id="sidebar-principal"', HTML)
        js = JS["prototipo.js"]
        self.assertIn('if (gavetaAberta()) { setGaveta(false); byId("menu-abrir").focus(); return; }', js)
        self.assertIn("setGaveta(false);\n  byId(\"crumb\")", js.replace("  byId(\"crumb\").textContent", "setGaveta(false);\n  byId(\"crumb\")"))

    def test_gaveta_so_aparece_em_tela_estreita(self):
        self.assertRegex(CSS, r"\.menu-abrir\{display:none\}")
        inicio = CSS.index("/* Gaveta em tela estreita")
        estreita = CSS[inicio:CSS.index("@media (max-width:480px)", inicio)]
        self.assertIn("@media (max-width:1023px){", estreita)
        self.assertIn(".menu-abrir{display:inline-flex", estreita)
        self.assertIn(".shell.menu-aberto .sidebar{transform:none}", estreita)

    def test_bloco_novo_do_css_plano_sem_sombra_gradiente_nem_acento_extra(self):
        bloco = re.sub(r"/\*.*?\*/", "", CSS[CSS.index("/* ===== Lote painel-conversa-16-11"):], flags=re.S)
        for decl in re.findall(r"box-shadow\s*:\s*([^;}]+)", bloco):
            self.assertEqual(decl.strip(), "none", "sombra no bloco novo")
        self.assertNotIn("gradient", bloco)
        self.assertNotIn("drop-shadow", bloco)
        for cor in ("--gold", "--violet", "--blue", "--lime", "--green", "--orange"):
            with self.subTest(cor=cor):
                self.assertNotIn("var(" + cor, bloco, "acento único: só --teal (cores de estado só com palavra)")


if __name__ == "__main__":
    unittest.main()


# ----------------------------------------------------------------------------------------------------------------------
# Lote atualiza-17-11 (17/11/2026, lote 2b do painel): testes de página para P1 a P7.
# Estrutura lida do HTML (HTMLParser e fatias por marcador); comportamento de prototipo.js e nova_versao.js num contexto
# node com DOM mínimo e fetch roteirizado por cenário. Nada sai da máquina: as rotas são respostas fixas no teste.
# ----------------------------------------------------------------------------------------------------------------------
TEMAS_FUNDIDOS = [
    "Conversa com a Seth", "Voz: saída e entrada", "Memória: canon ↔ Obsidian", "Escrita controlada → canon",
    "Navegação: navegador e Discord", "Roteamento por capacidade", "Manutenção programada",
    "Réplica Windows e failover", "Home Assistant e WhatsApp",
]
EXCLUSIVOS = [
    "Trabalhar com código", "Verificar o sistema", "Sucessão e espelho do canon",
    "OmniRoute → painel ao vivo", "Painel operacional", "Vigia do Claude", "NotebookLM e fontes externas",
]
# Títulos que existiam antes (Panorama e Integrações) e saíram com a fusão: nenhum pode voltar como linha separada.
TITULOS_ANTIGOS = [
    "Conectar Home Assistant ou WhatsApp", "Ouvir respostas", "Falar com a Seth", "Buscar na memória",
    "Navegar e comunicar", "Escolher rota por capacidade", "Executar manutenção programada", "Acrescentar memória",
    "Réplica Windows de leitura/failover", "Conversar com a Seth", "Conversa com a Seth · gateway", "Canon ↔ Obsidian",
    "Navegador e Discord", "OmniRoute, Laya e Jev", "Rotinas de manutenção",
]
CATEGORIAS_DA_LISTA = {"USAR", "ENTENDER", "MELHORAR", "GOVERNAR", "MANTER"}


def fatia_secao(secao_id):
    """HTML de uma <section class="secao"> pelo id."""
    inicio = HTML.index(f'<section class="secao" id="{secao_id}"')
    return HTML[inicio:HTML.index('<section class="secao"', inicio + 1) if '<section class="secao"' in HTML[inicio + 1:] else len(HTML)]


def fatia_sub(sub_id):
    """HTML de um subpainel (<div class="sub"...> com id sub-<nome>) até o próximo subpainel ou o fim da seção."""
    inicio = HTML.index(f'id="sub-{sub_id}"')
    fins = [i for i in (HTML.find('<div class="sub', inicio + 1), HTML.find("</section>", inicio + 1)) if i != -1]
    return HTML[inicio:min(fins)]


class CartoesDaLista(HTMLParser):
    """Cartões da lista de integrações: título (h3), categoria (primeiro small dentro de cap-meta) e evidência."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cartoes = []
        self._cartao = None
        self._meta = False
        self._em_h3 = False
        self._em_categoria = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "article" and "cap-card" in classes:
            self._cartao = {"attrs": a, "titulo": "", "categoria": None, "evidencia": False}
            self.cartoes.append(self._cartao)
            self._meta = False
        elif self._cartao is None:
            return
        elif tag == "div" and "cap-meta" in classes:
            self._meta = True
        elif tag == "h3":
            self._em_h3 = True
        elif tag == "small" and self._meta and self._cartao["categoria"] is None:
            self._em_categoria = True
            self._cartao["categoria"] = ""
        elif tag == "button" and "evidence" in classes:
            self._cartao["evidencia"] = True

    def handle_endtag(self, tag):
        if tag == "h3":
            self._em_h3 = False
        elif tag == "small":
            self._em_categoria = False
        elif tag == "article" and self._cartao is not None:
            self._cartao = None

    def handle_data(self, data):
        if self._cartao is None:
            return
        if self._em_h3:
            self._cartao["titulo"] += data
        if self._em_categoria:
            self._cartao["categoria"] += data


class FusaoIntegracoesTests(unittest.TestCase):
    """P1 (17/11/2026): O que posso fazer e Integrações viram uma lista só, em Sistema > Integrações."""

    @classmethod
    def setUpClass(cls):
        cls.parser = CartoesDaLista()
        cls.parser.feed(HTML)

    def test_cada_tema_aparece_uma_vez_e_os_exclusivos_ficam(self):
        titulos = [c["titulo"].strip() for c in self.parser.cartoes]
        self.assertEqual(len(titulos), 16, titulos)
        for tema in TEMAS_FUNDIDOS + EXCLUSIVOS:
            with self.subTest(tema=tema):
                self.assertEqual(titulos.count(tema), 1)
        self.assertEqual(sorted({t for t in titulos if titulos.count(t) > 1}), [])
        for antigo in TITULOS_ANTIGOS:
            with self.subTest(antigo=antigo):
                self.assertNotIn(antigo, titulos)

    def test_cada_linha_tem_categoria_do_conjunto_fechado_evidencia_e_busca(self):
        for c in self.parser.cartoes:
            with self.subTest(titulo=c["titulo"]):
                self.assertIn((c["categoria"] or "").split(" · ")[0].strip(), CATEGORIAS_DA_LISTA)
                self.assertTrue(c["evidencia"], "linha sem botão de evidência")
                self.assertIn("data-search", c["attrs"])

    def test_lista_fica_em_integracoes_com_cinco_filtros_busca_e_fronteiras(self):
        sub = fatia_sub("integracoes")
        self.assertIn('id="integration-list"', sub)
        self.assertEqual(re.findall(r'data-filter="(\w+)"', sub), ["all", "active", "partial", "planned", "horizon"])
        self.assertEqual(len(re.findall(r'<article class="cap-card"', sub)), 16)
        self.assertIn("O que atravessa", sub)
        self.assertIn('class="footer-note"', sub)
        self.assertIn('id="no-results"', sub)

    def test_panorama_sem_subcapacidades_e_com_atalho_para_integracoes(self):
        self.assertNotIn('data-sub="capacidades"', HTML)
        self.assertNotIn('id="sub-capacidades"', HTML)
        self.assertNotIn("O que posso fazer", HTML)
        nav = HTML[HTML.index('aria-label="Subpainéis de Panorama"'):]
        nav = nav[:nav.index("</nav>")]
        atalhos = re.findall(r'<button[^>]*data-open-page="sistema"[^>]*data-open-sub="integracoes"[^>]*>[^<]+</button>', nav)
        self.assertEqual(len(atalhos), 1)


class DuplicatasEAtalhosTests(unittest.TestCase):
    """P2 (17/11/2026): Atualizar um por tela; timers e tarefas só em Manutenção; Visão do sistema só com números."""

    def test_atualizar_aparece_uma_vez_por_tela_e_nao_se_repete_na_secao(self):
        for secao in ("panorama", "sistema"):
            with self.subTest(secao=secao):
                botoes = re.findall(r"<button[^>]*>[^<]*Atualizar[^<]*</button>", fatia_secao(secao))
                self.assertEqual(len(botoes), 1, botoes)
        self.assertIn('id="refresh-main"', fatia_secao("panorama"))
        self.assertIn('id="refresh-status"', fatia_sub("operacao"))

    def test_estado_operacional_sem_timers_e_com_atalho_para_manutencao(self):
        op = fatia_sub("operacao")
        for velho in ('id="live-timers"', 'id="live-tasks"', "timer-panel"):
            self.assertNotIn(velho, op)
        self.assertIn('data-open-page="sistema" data-open-sub="manutencao"', op)

    def test_timers_e_tarefas_ficam_so_em_manutencao(self):
        man = fatia_sub("manutencao")
        self.assertIn('id="live-timers"', man)
        self.assertIn('id="maintenance-tasks"', man)
        self.assertEqual(HTML.count('id="live-timers"'), 1)
        self.assertEqual(HTML.count('id="maintenance-tasks"'), 1)
        self.assertNotIn("maintenance-timers", HTML)

    def test_lacunas_ficam_so_em_qualidade(self):
        # 17/11/2026 (lote 2b): a lista de lacunas tem um lugar só, Qualidade > Lacunas; Panorama, Sistema e Conhecimento não a repetem.
        lac = fatia_sub("lacunas")
        self.assertIn('id="lacunas-lista"', lac)
        self.assertIn('id="lacunas-canon"', lac)
        self.assertEqual(HTML.count('id="lacunas-lista"'), 1)
        self.assertEqual(HTML.count('id="lacunas-canon"'), 1)
        self.assertIn("lacunas", estrutura().sub_em["qualidade"])
        for secao in ("panorama", "sistema", "conhecimento"):
            with self.subTest(secao=secao):
                self.assertNotIn("lacunas", estrutura().sub_em[secao])

    def test_visao_do_sistema_so_numeros_e_atalhos(self):
        vis = fatia_sub("visao")
        self.assertNotIn("visao-melhorias", HTML)
        self.assertIn('id="visao-kpis"', vis)
        self.assertNotIn("<ul", vis)
        self.assertIn('data-open-page="qualidade" data-open-sub="lacunas"', vis)
        self.assertIn('data-open-page="sistema" data-open-sub="integracoes"', vis)


class ProvedoresETabelasTests(unittest.TestCase):
    """P3 (17/11/2026): botões e tabela do Conselho vêm de /api/provedores; Conexões tem uma tabela; Gravar chave lê o seletor certo."""

    def test_botoes_do_conselho_sao_gerados_e_abrir_delega_o_clique(self):
        bloco_modelos = HTML[HTML.index('id="modelos-links"'):HTML.index('id="status"')]
        self.assertNotIn('data-alvo="', bloco_modelos, "botão de modelo fixo no HTML")
        self.assertIn('id="modelos-links"', HTML)
        self.assertIn('id="providerTable"', HTML)
        self.assertIn(">Aba agora<", HTML)
        js = JS["prototipo.js"]
        self.assertIn('lerRotaTela("/api/provedores")', js)
        self.assertIn("b.dataset.alvo = p.id", js)
        abrir = JS["abrir.js"]
        self.assertIn("document.addEventListener('click'", abrir)
        self.assertIn("closest('[data-alvo]')", abrir)
        self.assertNotIn("querySelectorAll('[data-alvo]')", abrir)
        self.assertIn("AgataPainel.lerProvedores", JS["conselho-rede/app.js"])

    def test_conexoes_tem_uma_tabela_com_as_colunas_e_tarifas_so_o_formulario(self):
        con = fatia_sub("nv-conexoes")
        tabela = con[con.index('id="nv-con-tabela"'):]
        cabecalhos = re.findall(r"<th>([^<]+)</th>", tabela[:tabela.index("</thead>")])
        self.assertEqual(cabecalhos, ["provedor", "id", "caminhos", "aba", "chave", "modelo", "tarifa", "fonte e data"])
        tar = fatia_sub("nv-tarifas")
        self.assertNotIn("nv-con-tabela", tar)
        self.assertIn('id="nv-api-provedor"', tar)
        self.assertIn('id="nv-tar-entrada"', tar)
        self.assertIn('data-open-sub="nv-conexoes"', tar)
        self.assertIn('id="nv-chave-provedor"', con)
        self.assertNotIn('id="nv-chave-provedor"', tar)

    def test_conexoes_tem_uma_linha_por_provedor_do_catalogo(self):
        # 17/11/2026: a tabela de Conexões sai do catálogo de /api/provedores; a conexão configurada entra na linha do seu provedor.
        estado = {"conexoes": [{"id": "zai", "nome": "Z.ai / GLM", "origem": "catalogo", "modos": {"api": {
            "disponivel": True, "falta": [], "chave": {"no_cofre": True, "desde": 1700000000, "no_ambiente": False},
            "modelo": "glm-x", "tarifa": {"entrada_usd_mtok": 1, "saida_usd_mtok": 5, "cambio_brl": 5.5, "fonte": "https://oficial", "data": "2026-11-04"}}}}],
            "orcamento": {"provedores": {}}, "teste_rotas": {}}
        provedores = {"state": "ok", "motivo": None, "provedores": [
            {"id": "zai", "nome": "Z.ai / GLM", "tipo": "chat", "acesso": "browser_tab_only"},
            {"id": "chatgpt", "nome": "ChatGPT", "tipo": "chat", "acesso": "browser_tab_only"}]}
        r = _roda_telas({"modo": "gravar", "estado": estado, "provedores": provedores, "escolhas": {"seletor": "zai", "outro": "chatgpt"},
                         "ids": ["nv-con-lista"]})
        self.assertEqual(r["erros"], [])
        linhas = r["ids"]["nv-con-lista"]["filhos"]
        self.assertEqual(len(linhas), 2, "uma linha por provedor do catálogo")
        self.assertIn("no cofre desde", linhas[0])
        self.assertIn("sem conexão configurada", linhas[1])
        self.assertIn("ChatGPT", linhas[1])

    def test_gravar_e_remover_chave_leem_o_seletor_da_propria_tela(self):
        js = JS["nova_versao.js"]
        gravar = js[js.index('confirmar(byId("nv-api-gravar")'):js.index('confirmar(byId("nv-api-remover")')]
        remover = js[js.index('confirmar(byId("nv-api-remover")'):js.index('confirmar(byId("nv-add-salvar")')]
        self.assertIn('val("nv-chave-provedor")', gravar)
        self.assertNotIn("nv-api-provedor", gravar)
        self.assertIn('val("nv-chave-provedor")', remover)
        self.assertNotIn("nv-api-provedor", remover)


class RecuperacaoEMedicoesTests(unittest.TestCase):
    """P4 (17/11/2026): um indicador Recuperação com duas leituras; cada botão de medir diz o corpus; ocupado mostra o motivo."""

    def test_recuperacao_e_um_indicador_com_as_duas_leituras(self):
        js = JS["prototipo.js"]
        self.assertIn('item.id === "recall_busca"', js)
        self.assertIn("leiturasDaRecuperacao(item)", js)
        self.assertIn('l.textContent = "Recuperação"', js)
        self.assertEqual(js.count('"Recuperação"'), 1)

    def test_botoes_de_medir_dizem_o_corpus_e_mostram_ocupado(self):
        qual = re.search(r'id="medir-recuperacao">([^<]*)<', HTML).group(1)
        ava = re.search(r'id="nv-run-recuperacao">([^<]*)<', HTML).group(1)
        self.assertIn("corpus do vault", qual)
        self.assertIn("conjunto da avaliação", ava)
        self.assertIn('"ocupado: "', JS["prototipo.js"])
        self.assertIn('"ocupado: "', JS["nova_versao.js"])


class TelasDeLeituraNovaTests(unittest.TestCase):
    """P5 e P6 (17/11/2026): Equipe, Backup, Saída de rede, Perímetro e CI nas abas certas, no padrão da referência."""

    TELAS = {
        "equipe": ("equipe", "sistema", ["equipe-resultado", "equipe-estado", "equipe-fonte", "equipe-kpis", "equipe-presentes", "equipe-ausentes"]),
        "backup": ("backup", "sistema", ["backup-resultado", "backup-estado", "backup-fonte", "backup-kpis", "backup-recursos"]),
        "saida-rede": ("saida-rede", "sistema", ["egress-resultado", "egress-estado", "egress-fonte", "egress-kpis", "egress-binarios"]),
        "perimetro": ("perimetro", "qualidade", ["perimetro-resultado", "perimetro-estado", "perimetro-fonte", "perimetro-kpis", "perimetro-controles"]),
        "ci": ("ci", "qualidade", ["ci-resultado", "ci-estado", "ci-fonte", "ci-kpis", "ci-passos"]),
    }

    def test_cada_tela_nova_esta_na_secao_certa_com_resultado_pilula_e_fonte(self):
        e = estrutura()
        for sub, (_, secao, ids) in self.TELAS.items():
            with self.subTest(sub=sub):
                self.assertIn(sub, e.sub_em[secao])
                bloco = fatia_sub(sub)
                self.assertIn('class="resultado"', bloco)
                for id_ in ids:
                    self.assertIn(f'id="{id_}"', bloco)

    def test_perimetro_diz_que_mostra_o_ultimo_resultado_gravado(self):
        self.assertIn("O painel não roda o perímetro; mostra o último resultado gravado.", fatia_sub("perimetro"))

    def test_carregamento_usa_o_mesmo_mecanismo_das_abas(self):
        js = JS["prototipo.js"]
        for sub, rotulo in (("equipe", "carregarEquipe"), ("backup", "carregarBackup"), ("saida-rede", "carregarEgress"),
                            ("perimetro", "carregarPerimetro"), ("ci", "carregarCI")):
            with self.subTest(sub=sub):
                self.assertRegex(js, rf'(?:"{re.escape(sub)}"|\b{sub}):\s*\(\)\s*=>\s*{rotulo}\(\)')

    def test_classes_novas_tem_regra_so_com_tokens_e_sem_sombra_nem_gradiente(self):
        css = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
        for classe in ("resultado", "cap-estado", "cap-hora"):
            with self.subTest(classe=classe):
                regra = re.search(r"\." + classe + r"\{([^}]*)\}", css)
                self.assertIsNotNone(regra, f".{classe} sem regra")
                self.assertNotRegex(regra.group(1), r"#[0-9a-fA-F]{3,8}|rgba?\(")
        self.assertEqual(re.findall(r"box-shadow|text-shadow|gradient\(", css), [])


# Harness de comportamento das telas novas, Recuperação, Visão e Gravar chave. Mesmo desenho de NODE_COMPORTAMENTO.
NODE_TELAS = r"""
const fs = require('fs'); const path = require('path'); const vm = require('vm');
process.on('unhandledRejection', () => {});
const cen = JSON.parse(fs.readFileSync(0, 'utf8')); const dir = process.env.PAINEL_DIR;
class No {}
class Texto extends No { constructor(t) { super(); this.textContent = String(t); } }
class Elemento extends No {
  constructor(tag) {
    super();
    this.tag = tag; this.texto = ''; this.children = []; this.hidden = false; this.className = ''; this.value = '';
    this.disabled = false; this.dataset = {}; this.attrs = {}; this.ouvintes = {}; this.style = {};
    this.classList = {add() {}, remove() {}, toggle() {}, contains() { return false; }};
  }
  get textContent() { return this.texto + this.children.map((c) => c.textContent).join(''); }
  set textContent(v) { this.children = []; this.texto = String(v); }
  append(...nos) { this.children.push(...nos); }
  replaceChildren(...nos) { this.children = nos; this.texto = ''; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; }
  addEventListener(tipo, fn) { (this.ouvintes[tipo] = this.ouvintes[tipo] || []).push(fn); }
  focus() {} blur() {} remove() {} select() {}
  closest() { return null; }
  querySelector() { return new Elemento('sel'); }
  querySelectorAll() { return []; }
}
const registro = new Map();
const elementoDoId = (id) => { if (!registro.has(id)) registro.set(id, new Elemento('id:' + id)); return registro.get(id); };
const documento = {
  visibilityState: 'visible', body: new Elemento('body'), documentElement: new Elemento('html'),
  getElementById: elementoDoId, querySelector() { return new Elemento('sel'); }, querySelectorAll() { return []; },
  createElement(tag) { return new Elemento(tag); }, createElementNS(ns, tag) { return new Elemento(tag); },
  createTextNode(t) { return new Texto(t); }, addEventListener() {}, removeEventListener() {},
};
const pedidos = [];
const ctx = {};
ctx.window = ctx; ctx.document = documento; ctx.location = {hash: ''}; ctx.history = {};
ctx.localStorage = {getItem() { return null; }, setItem() {}, removeItem() {}};
ctx.navigator = {clipboard: {}}; ctx.Node = No;
ctx.fetch = async (url, opcoes) => {
  const metodo = (opcoes && opcoes.method) || 'GET';
  pedidos.push({url, metodo, corpo: opcoes && opcoes.body ? JSON.parse(opcoes.body) : null});
  const rota = (cen.rotas || {})[url.split('?')[0]];
  if (!rota) return {ok: false, status: 404, json: async () => ({}), text: async () => ''};
  const ok = rota.status === undefined || (rota.status >= 200 && rota.status < 300);
  return {ok, status: rota.status || 200, json: async () => rota.corpo || {}, text: async () => ''};
};
ctx.AbortController = function () { this.signal = {}; this.abort = () => {}; };
ctx.setTimeout = () => 0; ctx.clearTimeout = () => {}; ctx.setInterval = () => 0; ctx.clearInterval = () => {};
ctx.addEventListener = () => {};
vm.createContext(ctx);
const esperar = async () => { for (let i = 0; i < 60; i++) await new Promise((r) => setImmediate(r)); };
const leitura = (ids) => Object.fromEntries((ids || []).map((id) => { const el = elementoDoId(id);
  return [id, {texto: el.textContent, filhos: el.children.map((c) => c.textContent), alvos: el.children.map((c) => (c.dataset && c.dataset.alvo) || null), hidden: el.hidden, classe: el.className}]; }));
(async () => {
  const saida = {erros: []};
  try {
    if (cen.modo === 'gravar') {
      ctx.AgataPainel = {
        fetchJson: async (url, opcoes) => {
          pedidos.push({url, metodo: (opcoes && opcoes.method) || 'GET', corpo: opcoes && opcoes.body ? JSON.parse(opcoes.body) : null});
          return url.startsWith('/api/nova-versao/estado') ? cen.estado : {schema_version: 1, resultado: {}};
        },
        marcarEstado() {},
        lerProvedores: async () => cen.provedores,
      };
      vm.runInContext(fs.readFileSync(path.join(dir, 'nova_versao.js'), 'utf8'), ctx, {filename: 'nova_versao.js'});
      await esperar();
      await ctx.AgataPainel.carregarNovaVersao('nv-conexoes');
      await esperar();
      elementoDoId('nv-chave-provedor').value = cen.escolhas.seletor;
      elementoDoId('nv-api-provedor').value = cen.escolhas.outro;
      elementoDoId('nv-api-chave').value = 'chave-de-teste';
      const gravar = elementoDoId('nv-api-gravar').ouvintes.click[0];
      await gravar(); await gravar(); await esperar();
      elementoDoId('nv-chave-provedor').value = cen.escolhas.seletor;
      const remover = elementoDoId('nv-api-remover').ouvintes.click[0];
      await remover(); await remover(); await esperar();
    } else {
      const fonte = fs.readFileSync(path.join(dir, 'prototipo.js'), 'utf8');
      const marca = 'aoMudarHash();\n})();';
      if (!fonte.includes(marca)) throw new Error('marca de fim do prototipo.js não achada');
      vm.runInContext(fonte.replace(marca, 'aoMudarHash();\nwindow.__teste = {carregarEquipe, carregarBackup, carregarEgress, carregarPerimetro, carregarCI, carregarQualidade, carregarVisaoSistema, montarBotoesDoConselho};\n})();'), ctx, {filename: 'prototipo.js'});
      await esperar();
      if (cen.modo === 'medicao') {
        const botao = elementoDoId('medir-recuperacao');
        await botao.ouvintes.click[0](); await botao.ouvintes.click[0]();
      } else {
        await ctx.__teste[cen.funcao]();
      }
      await esperar();
    }
    saida.ids = leitura(cen.ids);
    saida.pedidos = pedidos.filter((p) => !p.url.startsWith('/api/status')).map((p) => ({url: p.url, metodo: p.metodo, corpo: p.corpo}));
  } catch (e) { saida.erros.push(String((e && e.stack) || e).slice(0, 400)); }
  console.log(JSON.stringify(saida));
})();
"""


def _roda_telas(cenario):
    ambiente = dict(os.environ, PAINEL_DIR=str(HERE))
    resultado = subprocess.run(["node", "-e", NODE_TELAS], input=json.dumps(cenario, ensure_ascii=False),
                               capture_output=True, text=True, timeout=120, env=ambiente)
    if resultado.returncode != 0 and not resultado.stdout:
        raise AssertionError("node não rodou (não medido): " + resultado.stderr[-400:])
    return json.loads(resultado.stdout.strip().splitlines()[-1])


# Formato real de /api/equipe (medido em 127.0.0.1:20199 em 17/11/2026): blocos com state próprio; listas, não dicionários.
EQUIPE_OK = {"schema_version": 1, "state": "warning", "source": "sincronia/equipe", "observed_at": "2026-11-17T08:00:00-03:00",
             "fresh_until": "2099-01-01T00:00:00Z",
             "sessao": {"state": "ok", "estado": "aguardando", "base": "619416ed99a8", "presentes": [{"agente": "codex", "desde": "2026-11-09T08:50:27-03:00"}], "esperados": []},
             "ausentes": {"state": "ok", "itens": [{"agente": "codex", "origem": ["config"], "desde": None, "motivo": None, "ate": None}]},
             "divergencias": ["codex: ausente no config e presente na sessão"], "divergencias_motivo": None,
             "itens": {"state": "ok", "agentes": [{"agente": "codex", "state": "ok", "total": 10, "por_estado": {"bloqueado": 1, "em_revisao": 1, "pronto": 8}}]},
             "vigias": {"state": "sem_leitura", "itens": [], "motivo": "a sessão não declara agentes esperados (campo esperados)"},
             "eventos": {"state": "ok", "linhas": ["08:00 sessão aberta"]}}
# Formato real de /api/backup (17/11/2026): hd é um objeto, pendentes_hd é número, recursos é lista.
BACKUP_OK = {"schema_version": 1, "state": "warning", "source": "p12-cobertura.json (cache do P-12)", "observed_at": "2026-11-17T08:00:00-03:00",
             "fresh_until": "2099-01-01T00:00:00Z", "hd": {"presente": True, "repositorio_presente": True, "motivo": None},
             "pendentes_hd": 1, "regua_dias": 14,
             "recursos": [{"recurso": "memoria", "state": "ok", "verificado_em": "2026-11-16T10:00:00+00:00", "idade_dias": 1, "snapshot": "abc", "dentro_da_regua": True},
                          {"recurso": "canon", "state": "ok", "verificado_em": "2026-10-01T10:00:00+00:00", "idade_dias": 47, "snapshot": "def", "dentro_da_regua": False}]}
# Formato real de /api/perimetro já gravado: contagens e controles, com o P-12 entre eles.
PERIMETRO_OK = {"schema_version": 1, "state": "ok", "source": "scripts/perimetro.sh → ultimo.json", "observed_at": "2026-11-17T08:00:00-03:00",
                "fresh_until": "2099-01-01T00:00:00Z", "gerado_em": "2026-11-17T08:35:00-03:00", "idade_horas": 0.4, "head": "ac08bf4f",
                "resultado_geral": "OK", "contagens": {"ok": 10, "skip": 2, "parcial": 1, "falha": 0},
                "controles": [{"id": "P-1", "veredito": "OK"}, {"id": "P-12", "veredito": "OK"}]}
# Formato real de /api/ci gravado (17/11/2026) e a parte de /api/status que a tela CI usa para o head do repositório (R2).
CI_GRAVADO = {"schema_version": 1, "state": "ok", "source": "scripts/ci_sdd_local.sh → ultimo.json", "observed_at": "2026-11-17T08:00:00-03:00",
              "fresh_until": "2099-01-01T00:00:00Z", "gerado_em": "2026-11-17T08:40:00-03:00", "idade_horas": 0.4, "head": "ac08bf4f",
              "ok": 2, "falha": 0, "linha_final": "CI LOCAL: TUDO OK", "passos": [{"nome": "testes SDD (pytest)", "ok": True}]}
STATUS_COM_HEAD = {"schema_version": 1, "services": [{"unit": "a", "state": "ok"}], "timers": [], "git": {"head": "ac08bf4f"},
                   "chat": {"http_status": 200}, "models": {"models": []}, "proposals": {"items": []}}


class TelasDeComportamentoTests(unittest.TestCase):
    """P5 e P7 (17/11/2026): cada tela mostra 'sem leitura' com o motivo quando a rota falha, e os campos quando responde."""

    def test_equipe_sem_rota_mostra_sem_leitura_com_motivo(self):
        r = _roda_telas({"modo": "telas", "funcao": "carregarEquipe", "ids": ["equipe-resultado", "equipe-estado"], "rotas": {}})
        self.assertEqual(r["erros"], [])
        self.assertIn("Sem leitura da equipe", r["ids"]["equipe-resultado"]["texto"])
        self.assertIn("/api/equipe", r["ids"]["equipe-resultado"]["texto"])
        self.assertEqual(r["ids"]["equipe-estado"]["texto"], "SEM LEITURA")

    def test_equipe_com_rota_mostra_sessao_ausentes_divergencias_e_vigias(self):
        r = _roda_telas({"modo": "telas", "funcao": "carregarEquipe", "ids": ["equipe-resultado", "equipe-estado", "equipe-presentes", "equipe-ausentes", "equipe-divergencias", "equipe-divergencias-bloco", "equipe-vigias", "equipe-eventos"],
                         "rotas": {"/api/equipe": {"corpo": EQUIPE_OK}}})
        self.assertEqual(r["erros"], [])
        ids = r["ids"]
        self.assertIn("1 presente, 1 ausente e 1 divergência.", ids["equipe-resultado"]["texto"])
        self.assertEqual(ids["equipe-estado"]["texto"], "ATENÇÃO")
        self.assertEqual(len(ids["equipe-presentes"]["filhos"]), 1)
        self.assertEqual(len(ids["equipe-ausentes"]["filhos"]), 1)
        self.assertIn("codex: ausente no config e presente na sessão", ids["equipe-divergencias"]["texto"])
        self.assertFalse(ids["equipe-divergencias-bloco"]["hidden"])
        self.assertIn("Vigias: sessão sem lista de esperados.", ids["equipe-vigias"]["texto"])
        self.assertIn("08:00 sessão aberta", ids["equipe-eventos"]["texto"])

    def test_equipe_sem_lista_de_esperados_diz_isso_na_sessao_e_nos_vigias(self):
        r = _roda_telas({"modo": "telas", "funcao": "carregarEquipe", "ids": ["equipe-sessao", "equipe-vigias"], "rotas": {"/api/equipe": {"corpo": EQUIPE_OK}}})
        self.assertEqual(r["erros"], [])
        self.assertIn("sessão sem lista de esperados", r["ids"]["equipe-sessao"]["texto"])
        self.assertIn("sessão sem lista de esperados", r["ids"]["equipe-vigias"]["texto"])

    def test_equipe_com_vigias_lidos_mostra_unidade_e_estado(self):
        dados = dict(EQUIPE_OK, vigias={"state": "ok", "itens": [{"agente": "codex", "unit": "agata-vigia@codex.service", "state": "ok", "active_state": "active"}]})
        r = _roda_telas({"modo": "telas", "funcao": "carregarEquipe", "ids": ["equipe-vigias"], "rotas": {"/api/equipe": {"corpo": dados}}})
        self.assertEqual(r["erros"], [])
        self.assertIn("codex · agata-vigia@codex.service", r["ids"]["equipe-vigias"]["texto"])
        self.assertIn("LEITURA VÁLIDA", r["ids"]["equipe-vigias"]["texto"])

    def test_backup_sem_rota_e_com_rota(self):
        vazio = _roda_telas({"modo": "telas", "funcao": "carregarBackup", "ids": ["backup-resultado", "backup-estado"], "rotas": {}})
        self.assertIn("Sem leitura do registro de cobertura", vazio["ids"]["backup-resultado"]["texto"])
        r = _roda_telas({"modo": "telas", "funcao": "carregarBackup", "ids": ["backup-resultado", "backup-presenca", "backup-recursos", "backup-regua-nota"],
                         "rotas": {"/api/backup": {"corpo": BACKUP_OK}}})
        self.assertEqual(r["erros"], [])
        self.assertIn("1 de 2 recursos dentro da régua de 14 dias", r["ids"]["backup-resultado"]["texto"])
        self.assertIn("HD presente", r["ids"]["backup-presenca"]["texto"])
        self.assertEqual(len(r["ids"]["backup-recursos"]["filhos"]), 2)
        self.assertIn("não é o veredito do P-12", r["ids"]["backup-regua-nota"]["texto"])

    def test_backup_mostra_o_p12_do_perimetro_antes_do_registro(self):
        r = _roda_telas({"modo": "telas", "funcao": "carregarBackup", "ids": ["backup-resultado", "backup-p12-estado", "backup-p12"],
                         "rotas": {"/api/backup": {"corpo": BACKUP_OK}, "/api/perimetro": {"corpo": PERIMETRO_OK}}})
        self.assertEqual(r["erros"], [])
        self.assertTrue(r["ids"]["backup-resultado"]["texto"].startswith("P-12: OK no último perímetro gravado em "))
        self.assertIn("17/11/2026", r["ids"]["backup-resultado"]["texto"])  # data legível (niceTime), não o ISO bruto
        self.assertEqual(r["ids"]["backup-p12-estado"]["texto"], "P-12 OK")
        self.assertIn("17/11/2026", r["ids"]["backup-p12"]["texto"])

    def test_backup_sem_ultimo_json_do_perimetro_diz_p12_sem_leitura(self):
        sem = {"schema_version": 1, "state": "sem_leitura", "motivo": "o perímetro ainda não gravou resultado nesta Máquina"}
        r = _roda_telas({"modo": "telas", "funcao": "carregarBackup", "ids": ["backup-resultado", "backup-p12-estado"],
                         "rotas": {"/api/backup": {"corpo": BACKUP_OK}, "/api/perimetro": {"corpo": sem}}})
        self.assertEqual(r["erros"], [])
        self.assertTrue(r["ids"]["backup-resultado"]["texto"].startswith("P-12: sem leitura (o perímetro ainda não gravou resultado nesta Máquina)."))
        self.assertEqual(r["ids"]["backup-p12-estado"]["texto"], "P-12 SEM LEITURA")

    def test_saida_de_rede_mostra_binarios_navegador_e_paridade_sem_registro(self):
        # Formato real de /api/egress (17/11/2026): binarios é uma lista com nome, presente, mtime e em_dia.
        dados = {"schema_version": 1, "state": "warning", "source": "redesign/rust/egress/target/release", "observed_at": "2026-11-17T08:00:00Z", "fresh_until": "2099-01-01T00:00:00Z",
                 "paridade": "sem registro", "motivo": "falta binário: egress-socks5",
                 "binarios": [{"nome": "egress", "presente": True, "mtime": "2026-11-16", "em_dia": True},
                              {"nome": "egress-socks5", "presente": True, "mtime": "2026-10-01", "em_dia": False}],
                 "fonte_mais_nova": "2026-11-17T08:35:50-03:00", "navegador_usa_rust": None}
        r = _roda_telas({"modo": "telas", "funcao": "carregarEgress", "ids": ["egress-resultado", "egress-binarios", "egress-dl"], "rotas": {"/api/egress": {"corpo": dados}}})
        self.assertIn("Binários em dia: 1 de 2", r["ids"]["egress-resultado"]["texto"])
        self.assertIn("Navegador usa Rust: não medido", r["ids"]["egress-resultado"]["texto"])
        self.assertIn("Paridade: sem registro", r["ids"]["egress-resultado"]["texto"])
        self.assertEqual(len(r["ids"]["egress-binarios"]["filhos"]), 2)

    def test_perimetro_sem_rota_e_com_controles(self):
        vazio = _roda_telas({"modo": "telas", "funcao": "carregarPerimetro", "ids": ["perimetro-resultado"], "rotas": {}})
        self.assertIn("Sem leitura do perímetro", vazio["ids"]["perimetro-resultado"]["texto"])
        dados = {"schema_version": 1, "state": "ok", "source": "perimetro", "observed_at": "2026-11-17T08:00:00Z", "fresh_until": "2099-01-01T00:00:00Z",
                 "gerado_em": "2026-11-16T22:00:00Z", "idade_horas": 10, "head": "abc1234", "resultado_geral": "OK",
                 "contagens": {"ok": 10, "skip": 2, "parcial": 1, "falha": 0}, "controles": [{"id": "P1", "veredito": "OK"}, {"id": "P8", "veredito": "FALHA"}]}
        r = _roda_telas({"modo": "telas", "funcao": "carregarPerimetro", "ids": ["perimetro-resultado", "perimetro-controles"], "rotas": {"/api/perimetro": {"corpo": dados}}})
        self.assertIn("Resultado geral: OK", r["ids"]["perimetro-resultado"]["texto"])
        self.assertEqual(len(r["ids"]["perimetro-controles"]["filhos"]), 2)

    def test_ci_passos_com_falha_primeiro_e_head_comparado(self):
        dados = {"schema_version": 1, "state": "ok", "source": "ci", "observed_at": "2026-11-17T08:00:00Z", "fresh_until": "2099-01-01T00:00:00Z",
                 "gerado_em": "2026-11-17T07:00:00Z", "idade_horas": 1, "head": "abc1234", "ok": 1, "falha": 1, "linha_final": "1 passou, 1 falhou",
                 "passos": [{"nome": "lint", "ok": True}, {"nome": "suite", "ok": False}]}
        r = _roda_telas({"modo": "telas", "funcao": "carregarCI", "ids": ["ci-resultado", "ci-passos", "ci-dl"], "rotas": {"/api/ci": {"corpo": dados}}})
        self.assertEqual(r["erros"], [])
        self.assertEqual(r["ids"]["ci-resultado"]["texto"], "1 passou, 1 falhou")
        self.assertIn("suite", r["ids"]["ci-passos"]["filhos"][0])
        self.assertIn("FALHOU", r["ids"]["ci-passos"]["filhos"][0])
        self.assertIn("head atual não medido", r["ids"]["ci-dl"]["texto"])

    def _pares_ci(self, r):
        filhos = r["ids"]["ci-dl"]["filhos"]
        return dict(zip(filhos[0::2], filhos[1::2]))

    def test_ci_com_mesmo_head_diz_mesmo_head_do_repositorio(self):
        # R2 (17/11/2026): o painel lê /api/status ao carregar; head do CI igual ao do repositório.
        r = _roda_telas({"modo": "telas", "funcao": "carregarCI", "ids": ["ci-dl", "ci-kpis"],
                         "rotas": {"/api/ci": {"corpo": CI_GRAVADO}, "/api/status": {"corpo": STATUS_COM_HEAD}}})
        self.assertEqual(r["erros"], [])
        par = self._pares_ci(r)
        self.assertEqual((par["head do CI"], par["head atual"]), ("ac08bf4f", "ac08bf4f"))
        self.assertEqual(par["comparação"], "mesmo head do repositório")
        self.assertIn("mesmo head do repositório", r["ids"]["ci-kpis"]["texto"])

    def test_ci_com_head_diferente_diz_head_diferente_do_atual(self):
        # R2 (17/11/2026): head do CI de outro commit; a tela diz que é diferente do atual, sem dizer que é o mesmo.
        r = _roda_telas({"modo": "telas", "funcao": "carregarCI", "ids": ["ci-dl", "ci-kpis"],
                         "rotas": {"/api/ci": {"corpo": dict(CI_GRAVADO, head="abc1234")}, "/api/status": {"corpo": STATUS_COM_HEAD}}})
        self.assertEqual(r["erros"], [])
        par = self._pares_ci(r)
        self.assertEqual((par["head do CI"], par["head atual"]), ("abc1234", "ac08bf4f"))
        self.assertEqual(par["comparação"], "head diferente do atual")
        self.assertIn("head diferente do atual", r["ids"]["ci-kpis"]["texto"])
        self.assertNotIn("mesmo head", r["ids"]["ci-dl"]["texto"])

    def test_botoes_do_conselho_saem_de_provedores(self):
        # Formato real de /api/provedores (17/11/2026): a lista vem em items, com total.
        dados = {"schema_version": 1, "state": "ok", "source": "redesign/painel_operacional/relay_catalog.py (PROVIDERS)", "observed_at": "2026-11-17T08:00:00Z",
                 "fresh_until": "2099-01-01T00:00:00Z", "total": 1, "items": [{"id": "zai", "nome": "Z.ai / GLM", "tipo": "chat", "acesso": "browser_tab_only"}]}
        r = _roda_telas({"modo": "telas", "funcao": "montarBotoesDoConselho", "ids": ["modelos-links"], "rotas": {"/api/provedores": {"corpo": dados}}})
        filhos = r["ids"]["modelos-links"]["filhos"]
        self.assertEqual(filhos[0], "Modelos")
        self.assertEqual(filhos[1], "Z.ai / GLM")
        vazio = _roda_telas({"modo": "telas", "funcao": "montarBotoesDoConselho", "ids": ["modelos-links"], "rotas": {}})
        self.assertIn("Sem leitura dos provedores", vazio["ids"]["modelos-links"]["filhos"][1])

    def test_botoes_do_conselho_levam_o_alvo_de_cada_provedor(self):
        # R3 (17/11/2026): /api/provedores com items no formato real; cada botão leva o id no data-alvo e o nome no texto.
        import relay_catalog
        itens = [{"id": p["id"], "nome": p["name"], "tipo": p["kind"], "acesso": p["access_mode"]} for p in relay_catalog.PROVIDERS]
        dados = {"schema_version": 1, "state": "ok", "source": "redesign/painel_operacional/relay_catalog.py (PROVIDERS)",
                 "observed_at": "2026-11-17T08:00:00Z", "fresh_until": "2099-01-01T00:00:00Z", "total": len(itens), "items": itens}
        r = _roda_telas({"modo": "telas", "funcao": "montarBotoesDoConselho", "ids": ["modelos-links"], "rotas": {"/api/provedores": {"corpo": dados}}})
        self.assertEqual(r["erros"], [])
        bloco = r["ids"]["modelos-links"]
        self.assertEqual(bloco["filhos"], ["Modelos", *[p["name"] for p in relay_catalog.PROVIDERS]])
        self.assertEqual(bloco["alvos"], [None, *[p["id"] for p in relay_catalog.PROVIDERS]])

    def test_perimetro_e_ci_envelhecidos_mostram_o_aviso_na_tela(self):
        # R1 (17/11/2026): resultado gravado há mais de 24 h vem com envelhecido e motivo; a tela mostra o aviso e ATENÇÃO.
        velho = dict(PERIMETRO_OK, state="warning", envelhecido=True, motivo="resultado gravado há 30 h", idade_horas=30)
        r = _roda_telas({"modo": "telas", "funcao": "carregarPerimetro", "ids": ["perimetro-resultado", "perimetro-estado"],
                         "rotas": {"/api/perimetro": {"corpo": velho}}})
        self.assertEqual(r["erros"], [])
        self.assertTrue(r["ids"]["perimetro-resultado"]["texto"].startswith("Resultado geral: OK."))
        self.assertTrue(r["ids"]["perimetro-resultado"]["texto"].endswith(" Atenção: resultado gravado há 30 h."))
        self.assertEqual(r["ids"]["perimetro-estado"]["texto"], "ATENÇÃO")
        novo = dict(PERIMETRO_OK, envelhecido=False)
        r = _roda_telas({"modo": "telas", "funcao": "carregarPerimetro", "ids": ["perimetro-resultado"],
                         "rotas": {"/api/perimetro": {"corpo": novo}}})
        self.assertNotIn("Atenção", r["ids"]["perimetro-resultado"]["texto"])
        ci = dict(CI_GRAVADO, state="warning", envelhecido=True, motivo="resultado gravado há 30 h", idade_horas=30)
        r = _roda_telas({"modo": "telas", "funcao": "carregarCI", "ids": ["ci-resultado", "ci-estado"],
                         "rotas": {"/api/ci": {"corpo": ci}}})
        self.assertEqual(r["erros"], [])
        self.assertEqual(r["ids"]["ci-resultado"]["texto"], "CI LOCAL: TUDO OK Atenção: resultado gravado há 30 h.")
        self.assertEqual(r["ids"]["ci-estado"]["texto"], "ATENÇÃO")

    def test_recuperacao_mostra_as_duas_leituras_num_indicador_so(self):
        # Formato real de /api/qualidade-llm (17/11/2026): leituras com corpus, rotulo, estado, valor, fonte e medido_em (não "data").
        dados = {"schema_version": 1, "state": "warning", "items": [{"id": "recall_busca", "titulo": "Recuperação: recall@k da busca", "estado": "warning", "valor": "2 de 2 corpora medidos",
                                                  "evidencia": "medido", "fonte": "scripts/medir_recuperacao.py", "leituras": [
            {"corpus": "vault", "rotulo": "Vault: gabarito calculado na hora", "valor": "@5 90%", "estado": "ok", "fonte": "scripts/medir_recuperacao.py", "medido_em": "2026-11-16"},
            {"corpus": "conjunto da avaliação", "rotulo": "Conjunto da avaliação, split dev", "valor": "@5 75%", "estado": "warning", "fonte": "redesign/avaliacao/recuperacao.py", "medido_em": "2026-11-15"}]}]}
        r = _roda_telas({"modo": "telas", "funcao": "carregarQualidade", "ids": ["qualidade-kpis", "qualidade-lista"], "rotas": {"/api/qualidade-llm": {"corpo": dados}}})
        self.assertEqual(r["erros"], [])
        kpis = r["ids"]["qualidade-kpis"]["texto"]
        self.assertEqual(kpis.count("Recuperação"), 1)
        self.assertIn("vault: @5 90%", kpis)
        self.assertIn("conjunto da avaliação: @5 75%", kpis)
        self.assertIn("data: 2026-11-16", kpis)
        self.assertEqual(len(r["ids"]["qualidade-kpis"]["filhos"]), 1)

    def test_visao_mostra_numeros_com_atalho_para_a_tela_de_origem(self):
        status = {"schema_version": 1, "services": [{"unit": "a", "state": "ok"}], "timers": [], "git": {"head": "abc1234"},
                  "chat": {"http_status": 200}, "models": {"models": []}, "proposals": {"items": []}}
        r = _roda_telas({"modo": "telas", "funcao": "carregarVisaoSistema", "ids": ["visao-kpis"],
                         "rotas": {"/api/status": {"corpo": status}, "/api/capacidades": {"corpo": {"schema_version": 1, "items": [{"id": "x", "state": "ok"}]}},
                                   "/api/lacunas": {"corpo": {"schema_version": 1, "items": []}}}})
        self.assertEqual(r["erros"], [])
        filhos = r["ids"]["visao-kpis"]["filhos"]
        self.assertEqual(len(filhos), 8)
        self.assertIn("Lacunas agora", filhos[6])
        self.assertIn("Capacidades com leitura", filhos[5])

    def test_medicao_com_trava_ocupada_mostra_o_motivo_no_botao(self):
        r = _roda_telas({"modo": "medicao", "ids": ["medir-recuperacao"],
                         "rotas": {"/api/medicoes/executar": {"status": 429, "corpo": {"motivo": "outra medição em curso"}}}})
        self.assertEqual(r["erros"], [])
        self.assertEqual(r["ids"]["medir-recuperacao"]["texto"], "ocupado: outra medição em curso")

    def test_gravar_e_remover_chave_usam_o_seletor_da_conexao_e_nao_o_de_tarifas(self):
        estado = {"conexoes": [{"id": "zai", "nome": "Z.ai / GLM", "origem": "catalogo", "modos": {"api": {
            "disponivel": True, "falta": [], "chave": {"no_cofre": True, "desde": 1700000000, "no_ambiente": False},
            "modelo": "glm-x", "tarifa": {"entrada_usd_mtok": 1, "saida_usd_mtok": 5, "cambio_brl": 5.5, "fonte": "https://oficial", "data": "2026-11-04"}}}}],
            "orcamento": {"provedores": {}}, "teste_rotas": {}}
        provedores = {"state": "ok", "provedores": [{"id": "zai", "nome": "Z.ai / GLM", "tipo": "chat", "acesso": "browser_tab_only"}], "motivo": None}
        r = _roda_telas({"modo": "gravar", "estado": estado, "provedores": provedores, "escolhas": {"seletor": "zai", "outro": "chatgpt"},
                         "ids": ["nv-con-lista", "nv-api-nota"]})
        self.assertEqual(r["erros"], [])
        gravados = [p["corpo"] for p in r["pedidos"] if p["corpo"] and p["corpo"].get("acao") == "gravar_chave"]
        removidos = [p["corpo"] for p in r["pedidos"] if p["corpo"] and p["corpo"].get("acao") == "remover_chave"]
        self.assertEqual([(g["provedor"], g["chave"]) for g in gravados], [("zai", "chave-de-teste")])
        self.assertEqual([x["provedor"] for x in removidos], ["zai"])
        linha = r["ids"]["nv-con-lista"]["filhos"]
        self.assertEqual(len(linha), 1)
        self.assertIn("aba do navegador", linha[0])
        self.assertIn("https://oficial · 2026-11-04", linha[0])
        self.assertIn("no cofre desde", linha[0])
