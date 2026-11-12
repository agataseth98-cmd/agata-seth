#!/usr/bin/env python3
"""Testes da aba Importantes e do cartão do Panorama (11/11/2026), no prototipo.js de verdade.

Carrega prototipo.js num contexto node com um DOM mínimo (árvore montada aqui, só com o que a aba usa) e um fetch
roteirizado pelo cenário. Nada sai da máquina e nenhuma rota real é chamada. Também confere, em texto, que o bloco
novo não usa innerHTML, atributo style nem on* (a CSP do painel não permite script inline).
"""
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = (HERE / "prototipo.html").read_text(encoding="utf-8")
JS = (HERE / "prototipo.js").read_text(encoding="utf-8")
CSS = (HERE / "prototipo.css").read_text(encoding="utf-8")
BLOCO_JS = JS[JS.index("const IMPORTANTES_ESTADOS"): JS.index("// Entrada: a seção vem do hash")]

NODE_IMPORTANTES = r"""
const fs = require('fs'); const path = require('path'); const vm = require('vm');
const {TextEncoder, TextDecoder} = require('util');
process.on('unhandledRejection', (e) => console.error('REJEICAO ' + (e && e.stack)));
const cen = JSON.parse(fs.readFileSync(0, 'utf8')); const dir = process.env.PAINEL_DIR;

class Elemento {
  constructor(tag) {
    this.tag = tag; this._texto = ''; this.children = []; this.parent = null;
    this.hidden = false; this.className = ''; this.value = ''; this.disabled = false; this.type = '';
    this.placeholder = ''; this.maxLength = 0; this.rows = 0; this.id = ''; this.title = '';
    this.dataset = {}; this.attrs = {}; this.ouvintes = {};
  }
  get textContent() { return this._texto + this.children.map((c) => c.textContent).join(''); }
  set textContent(valor) { this._texto = String(valor); this.children = []; }
  get classes() { return String(this.className || '').split(' ').filter(Boolean); }
  get classList() {
    const self = this;
    return {
      add(...c) { const s = new Set(self.classes); c.forEach((x) => s.add(x)); self.className = [...s].join(' '); },
      remove(...c) { self.className = self.classes.filter((x) => !c.includes(x)).join(' '); },
      toggle(c, forca) { const tem = self.classes.includes(c); const quer = forca === undefined ? !tem : !!forca; quer ? this.add(c) : this.remove(c); return quer; },
      contains(c) { return self.classes.includes(c); },
    };
  }
  append(...nos) { for (const n of nos) { n.parent = this; this.children.push(n); } }
  replaceChildren(...nos) { for (const c of this.children) c.parent = null; this.children = []; this._texto = ''; this.append(...nos); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; }
  addEventListener(tipo, fn) { (this.ouvintes[tipo] = this.ouvintes[tipo] || []).push(fn); }
  focus() {} blur() {} select() {} scrollIntoView() {} remove() {}
  closest(sel) { let n = this; while (n) { if (casa(n, sel)) return n; n = n.parent; } return null; }
  querySelector(sel) { return buscar(this, sel)[0] || null; }
  querySelectorAll(sel) { return buscar(this, sel); }
}
function casa(el, sel) {
  const tag = /^[a-z][a-z0-9-]*/i.exec(sel);
  if (tag && el.tag !== tag[0].toLowerCase()) return false;
  const partes = sel.slice(tag ? tag[0].length : 0).match(/\.[\w-]+|\[[^\]]+\]/g) || [];
  for (const p of partes) {
    if (p[0] === '.') { if (!el.classes.includes(p.slice(1))) return false; continue; }
    const [chave, valor] = p.slice(1, -1).split('=');
    const v = valor === undefined ? undefined : valor.replace(/"/g, '');
    if (chave.startsWith('data-')) {
      const nome = chave.slice(5).replace(/-([a-z])/g, (_, l) => l.toUpperCase());
      if (!(nome in el.dataset)) return false;
      if (v !== undefined && el.dataset[nome] !== v) return false;
    } else {
      if (!(chave in el.attrs)) return false;
      if (v !== undefined && el.attrs[chave] !== v) return false;
    }
  }
  return true;
}
function descendentes(no, saida = []) { for (const c of no.children) { saida.push(c); descendentes(c, saida); } return saida; }
// Seletor simples: ":scope", descendente (espaço) e filho (>). Suficiente para os seletores que o painel usa.
function buscar(raiz, sel) {
  let atuais = [raiz]; let modo = 'desc';
  for (const token of sel.replace(/\s*>\s*/g, ' > ').split(/\s+/).filter(Boolean)) {
    if (token === ':scope') continue;
    if (token === '>') { modo = 'filho'; continue; }
    const proximos = [];
    for (const no of atuais) {
      const alvo = modo === 'filho' ? no.children : descendentes(no);
      for (const c of alvo) if (casa(c, token) && !proximos.includes(c)) proximos.push(c);
    }
    atuais = proximos; modo = 'desc';
  }
  return atuais;
}
const registro = new Map();
const raiz = new Elemento('body');
function elementoDoId(id) {
  if (!registro.has(id)) { const e = new Elemento('div'); e.id = id; registro.set(id, e); }
  return registro.get(id);
}
const documento = {
  visibilityState: 'visible',
  getElementById: elementoDoId,
  querySelector(sel) { return buscar(raiz, sel)[0] || new Elemento('div'); },
  querySelectorAll(sel) { return buscar(raiz, sel); },
  createElement(tag) { return new Elemento(tag); },
  createElementNS(ns, tag) { return new Elemento(tag); },
  createTextNode(texto) { const e = new Elemento('#texto'); e._texto = String(texto); return e; },
  addEventListener() {},
};
// Montagem mínima do que a aba usa: a seção Panorama com um subpainel visível (o próprio do painel) e a aba.
const secao = new Elemento('section'); secao.className = 'secao'; secao.id = 'panorama'; secao.dataset.titulo = 'Panorama';
registro.set('panorama', secao); raiz.append(secao);
const subPanorama = new Elemento('div'); subPanorama.className = 'sub'; subPanorama.dataset.sub = 'panorama'; subPanorama.dataset.secao = 'panorama';
secao.append(subPanorama);
const abas = new Elemento('nav'); abas.className = 'abas';
const botaoAba = new Elemento('button'); botaoAba.dataset.sub = 'importantes'; botaoAba.textContent = 'Importantes';
abas.append(botaoAba); secao.append(abas);
const sub = elementoDoId('sub-importantes'); sub.className = 'sub'; sub.dataset.sub = 'importantes'; sub.dataset.secao = 'panorama'; sub.hidden = true;
const estados = new Elemento('div'); estados.className = 'estados';
for (const nome of ['carregando', 'vazio', 'erro']) {
  const p = new Elemento('p'); p.className = 'estado'; p.dataset.estado = nome; p.hidden = true; estados.append(p);
}
sub.append(estados); secao.append(sub);
const lista = elementoDoId('importantes-lista'); lista.className = 'importantes-lista';
const formulario = elementoDoId('importantes-form'); formulario.tag = 'form';
const filtro = elementoDoId('importantes-filtro'); filtro.tag = 'select'; filtro.value = 'abertos';
const campoTexto = elementoDoId('importantes-texto'); campoTexto.tag = 'textarea';
// Os demais ids usados no boot entram vazios; o que a aba escreve neles é lido pelo teste.

const ctx = {};
ctx.window = ctx; ctx.document = documento; ctx.location = {hash: ''}; ctx.history = {};
ctx.localStorage = {getItem() { return null; }, setItem() {}}; ctx.navigator = {clipboard: {}}; ctx.Node = function () {};
ctx.TextEncoder = TextEncoder; ctx.TextDecoder = TextDecoder;
ctx.AbortController = function () { this.signal = {}; this.abort = () => {}; };
ctx.setTimeout = () => 0; ctx.clearTimeout = () => {}; ctx.setInterval = () => 0; ctx.clearInterval = () => {};
ctx.addEventListener = () => {};

const chamadas = [];
function escolher(valor) { if (Array.isArray(valor)) return valor.length > 1 ? valor.shift() : valor[0]; return valor; }
function respostaJson(status, obj) { return {ok: status >= 200 && status < 300, status, json: async () => obj, text: async () => JSON.stringify(obj)}; }
function respostaTexto(status, texto) { return {ok: status >= 200 && status < 300, status, json: async () => { throw new Error('sem json'); }, text: async () => texto}; }
ctx.fetch = async (url, opcoes = {}) => {
  const metodo = String(opcoes.method || 'GET').toUpperCase();
  chamadas.push({url, metodo, corpo: typeof opcoes.body === 'string' ? JSON.parse(opcoes.body) : null});
  if (url === '/api/importantes' && metodo === 'GET') {
    const r = escolher(cen.lista) || {};
    if (r.status && r.status !== 200) return respostaTexto(r.status, '');
    return respostaJson(200, r.corpo);
  }
  if (metodo === 'POST' && cen.posts && cen.posts[url]) {
    const r = escolher(cen.posts[url]) || {};
    if (r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
    return respostaJson(200, r.corpo || {});
  }
  return respostaTexto(404, '');
};

const esperar = async () => { for (let i = 0; i < 120; i++) await new Promise((r) => setImmediate(r)); };
function botaoNoItem(indice, rotulo) {
  const li = lista.children[indice];
  if (!li) throw new Error('item ' + indice + ' não existe');
  return descendentes(li).find((e) => e.tag === 'button' && e.textContent.trim() === rotulo);
}
function clicar(el) { el.ouvintes.click[0]({target: el}); }
async function executar(a) {
  if (a.tipo === 'clicarNoItem') clicar(botaoNoItem(a.indice, a.texto));
  else if (a.tipo === 'clicarNaAba') clicar(botaoAba);
  else if (a.tipo === 'clicar') clicar(elementoDoId(a.id));
  else if (a.tipo === 'digitar') { const el = elementoDoId(a.id); el.value = a.valor; }
  else if (a.tipo === 'valorNoItem') {
    const li = lista.children[a.indice];
    const alvo = descendentes(li).find((e) => e.tag === a.tag);
    alvo.value = a.valor;
  }
  else if (a.tipo === 'mudar') { const el = elementoDoId(a.id); el.value = a.valor; el.ouvintes.change[0]({target: el}); }
  else if (a.tipo === 'enviar') formulario.ouvintes.submit[0]({preventDefault() {}, target: formulario});
  await esperar();
}
(async () => {
  try {
    vm.createContext(ctx);
    vm.runInContext(fs.readFileSync(path.join(dir, 'prototipo.js'), 'utf8'), ctx, {filename: 'prototipo.js'});
  } catch (e) { console.log(JSON.stringify({erro: 'carga: ' + e.message})); return; }
  await esperar();
  for (const a of cen.acoes || []) await executar(a);
  const visivel = (nome) => estados.children.find((p) => p.dataset.estado === nome).hidden === false;
  const itens = lista.children.map((li) => ({
    classe: li.className,
    texto: descendentes(li).find((e) => e.className === 'importantes-texto').textContent,
    origem: descendentes(li).find((e) => e.className === 'importantes-origem').textContent,
    botoes: descendentes(li).filter((e) => e.tag === 'button').map((b) => b.textContent),
    campos: descendentes(li).filter((e) => e.tag === 'textarea' || e.tag === 'input').map((c) => c.value),
  }));
  const aviso = elementoDoId('importantes-aviso');
  console.log(JSON.stringify({
    chamadas, itens,
    estadosVisiveis: ['carregando', 'vazio', 'erro'].filter(visivel),
    subOculta: sub.hidden,
    cartaoResumo: elementoDoId('importantes-cartao-resumo').textContent,
    cartaoEstado: elementoDoId('importantes-cartao-estado').textContent,
    resumoLista: elementoDoId('importantes-resumo-lista').textContent,
    avisoOculto: aviso.hidden, aviso: aviso.textContent,
    campoTexto: campoTexto.value, trazerDesabilitado: elementoDoId('importantes-trazer').disabled,
    listaVazia: lista.children.length === 0,
  }));
})();
"""


def rodar(cenario):
    ambiente = dict(os.environ, PAINEL_DIR=str(HERE))
    resultado = subprocess.run(["node", "-e", NODE_IMPORTANTES], input=json.dumps(cenario, ensure_ascii=False),
                               capture_output=True, text=True, timeout=120, env=ambiente)
    if resultado.returncode != 0 and not resultado.stdout:
        raise AssertionError("node não rodou (não medido): " + resultado.stderr[-400:])
    return json.loads(resultado.stdout.strip().splitlines()[-1])


def item(i, texto, estado="aberto", origem="humano", cache_n=None, nota="", feito_em=None):
    return {"id": f"{i:012x}", "texto": texto, "origem": origem, "criado_em": "2026-11-11T10:00:00-03:00",
            "estado": estado, "feito_em": feito_em, "nota": nota, "cache_n": cache_n}


def lista(itens, estado=None):
    contagem = {e: sum(1 for x in itens if x["estado"] == e) for e in ("aberto", "feito", "descartado")}
    return {"schema_version": 1, "estado": estado or ("vazio" if not itens else "ok"), "itens": itens, "contagem": contagem}


class UiImportantesTests(unittest.TestCase):
    def test_lista_mostra_abertos_primeiro_e_o_cartao_conta_abertos(self):
        itens = [item(1, "primeira ideia"), item(2, "pendência feita", "feito", feito_em="2026-11-11T11:00:00-03:00"),
                 item(3, "segunda ideia")]
        dados = rodar({"lista": {"status": 200, "corpo": lista(itens)},
                       "acoes": [{"tipo": "mudar", "id": "importantes-filtro", "valor": "todos"}]})
        self.assertEqual([i["texto"] for i in dados["itens"]], ["primeira ideia", "pendência feita", "segunda ideia"])
        self.assertEqual(dados["cartaoResumo"], "Importantes: 2 abertos")
        self.assertEqual(dados["cartaoEstado"], "LIDO")
        self.assertEqual(dados["estadosVisiveis"], [], "com itens, nenhum estado de aviso aparece")
        self.assertEqual(dados["itens"][1]["botoes"], ["Reabrir", "Descartar", "Editar"])
        self.assertEqual(dados["itens"][0]["botoes"], ["Marcar feito", "Descartar", "Editar"])
        self.assertEqual(dados["resumoLista"], "2 abertos · 1 feitos · 0 descartados · mostrando 3")

    def test_filtro_padrao_mostra_so_os_abertos(self):
        itens = [item(1, "aberta"), item(2, "feita", "feito", feito_em="2026-11-11T11:00:00-03:00")]
        dados = rodar({"lista": {"status": 200, "corpo": lista(itens)}})
        self.assertEqual([i["texto"] for i in dados["itens"]], ["aberta"])
        self.assertIn("mostrando 1", dados["resumoLista"])

    def test_lista_vazia_mostra_estado_vazio_e_cartao_zero(self):
        dados = rodar({"lista": {"status": 200, "corpo": lista([])}})
        self.assertEqual(dados["estadosVisiveis"], ["vazio"])
        self.assertEqual(dados["cartaoResumo"], "Importantes: 0 abertos")
        self.assertTrue(dados["listaVazia"])

    def test_falha_de_leitura_mostra_erro_e_nao_mostra_lista_antiga(self):
        dados = rodar({"lista": {"status": 500, "texto": "falhou"}})
        self.assertEqual(dados["estadosVisiveis"], ["erro"])
        self.assertTrue(dados["listaVazia"])
        self.assertEqual(dados["cartaoResumo"], "Importantes: não medido (a leitura falhou).")
        self.assertEqual(dados["cartaoEstado"], "NÃO MEDIDO")

    def test_lista_ilegivel_mostra_erro_sem_itens(self):
        dados = rodar({"lista": {"status": 200, "corpo": {"schema_version": 1, "estado": "ilegivel", "itens": [],
                                                           "contagem": {"aberto": 0, "feito": 0, "descartado": 0}}}})
        self.assertEqual(dados["estadosVisiveis"], ["erro"])
        self.assertEqual(dados["cartaoEstado"], "ILEGÍVEL")
        self.assertTrue(dados["listaVazia"])

    def test_guardar_envia_o_texto_limpa_o_campo_e_recarrega(self):
        dados = rodar({
            "lista": [{"status": 200, "corpo": lista([])}, {"status": 200, "corpo": lista([item(1, "Nova ideia")])}],
            "posts": {"/api/importantes": [{"corpo": item(1, "Nova ideia")}]},
            "acoes": [{"tipo": "digitar", "id": "importantes-texto", "valor": "  Nova ideia  "}, {"tipo": "enviar"}],
        })
        posts = [c for c in dados["chamadas"] if c["metodo"] == "POST"]
        self.assertEqual(posts, [{"url": "/api/importantes", "metodo": "POST", "corpo": {"texto": "Nova ideia"}}])
        self.assertEqual(dados["campoTexto"], "")
        self.assertEqual(dados["aviso"], "Guardado.")
        self.assertEqual([i["texto"] for i in dados["itens"]], ["Nova ideia"])

    def test_guardar_vazio_nao_envia_nada(self):
        dados = rodar({"lista": {"status": 200, "corpo": lista([])}, "acoes": [{"tipo": "enviar"}]})
        self.assertEqual([c for c in dados["chamadas"] if c["metodo"] == "POST"], [])
        self.assertEqual(dados["aviso"], "Escreva o texto antes de guardar.")

    def test_marcar_feito_e_descartar_chamam_o_estado_certo(self):
        base = lista([item(1, "uma"), item(2, "duas")])
        dados = rodar({
            "lista": [{"status": 200, "corpo": base}, {"status": 200, "corpo": base}],
            "posts": {"/api/importantes/estado": [{"corpo": {}}, {"corpo": {}}]},
            "acoes": [{"tipo": "clicarNoItem", "indice": 0, "texto": "Marcar feito"},
                      {"tipo": "clicarNoItem", "indice": 1, "texto": "Descartar"}],
        })
        posts = [c for c in dados["chamadas"] if c["metodo"] == "POST"]
        self.assertEqual([p["corpo"] for p in posts], [{"id": f"{1:012x}", "estado": "feito"},
                                                       {"id": f"{2:012x}", "estado": "descartado"}])

    def test_filtro_mostra_so_o_estado_escolhido(self):
        itens = [item(1, "aberta"), item(2, "feita", "feito"), item(3, "descartada", "descartado")]
        dados = rodar({"lista": {"status": 200, "corpo": lista(itens)},
                       "acoes": [{"tipo": "mudar", "id": "importantes-filtro", "valor": "descartados"}]})
        self.assertEqual([i["texto"] for i in dados["itens"]], ["descartada"])
        self.assertIn("mostrando 1", dados["resumoLista"])

    def test_filtro_sem_itens_diz_que_nao_ha_nada_neste_filtro(self):
        dados = rodar({"lista": {"status": 200, "corpo": lista([item(1, "aberta")])},
                       "acoes": [{"tipo": "mudar", "id": "importantes-filtro", "valor": "feitos"}]})
        self.assertEqual(dados["itens"], [])
        self.assertIn("nenhum item neste filtro", dados["resumoLista"])

    def test_recusa_403_mostra_aviso_e_a_lista_volta_do_servidor(self):
        base = lista([item(1, "uma")])
        dados = rodar({
            "lista": [{"status": 200, "corpo": base}, {"status": 200, "corpo": base}],
            "posts": {"/api/importantes/estado": [{"status": 403, "texto": "cross-origin request denied"}]},
            "acoes": [{"tipo": "clicarNoItem", "indice": 0, "texto": "Marcar feito"}],
        })
        self.assertFalse(dados["avisoOculto"])
        self.assertEqual(dados["aviso"], "O painel recusou o pedido: abra esta tela pelo próprio painel.")
        self.assertEqual([i["texto"] for i in dados["itens"]], ["uma"], "o item continua aberto na lista")

    def test_conflito_409_mostra_o_motivo_do_servidor(self):
        dados = rodar({
            "lista": {"status": 200, "corpo": lista([item(1, "uma")])},
            "posts": {"/api/importantes/estado": [{"status": 409, "texto": "lista de importantes ilegível; nada foi alterado"}]},
            "acoes": [{"tipo": "clicarNoItem", "indice": 0, "texto": "Descartar"}],
        })
        self.assertEqual(dados["aviso"], "Lista de importantes ilegível; nada foi alterado.")

    def test_editar_envia_texto_e_nota_e_volta_para_a_lista(self):
        base = lista([item(1, "texto antigo")])
        dados = rodar({
            "lista": [{"status": 200, "corpo": base}, {"status": 200, "corpo": base}],
            "posts": {"/api/importantes/editar": [{"corpo": {}}]},
            "acoes": [{"tipo": "clicarNoItem", "indice": 0, "texto": "Editar"},
                      {"tipo": "valorNoItem", "indice": 0, "tag": "textarea", "valor": "texto novo"},
                      {"tipo": "valorNoItem", "indice": 0, "tag": "input", "valor": "ver com calma"},
                      {"tipo": "clicarNoItem", "indice": 0, "texto": "Salvar"}],
        })
        posts = [c for c in dados["chamadas"] if c["metodo"] == "POST"]
        self.assertEqual(posts, [{"url": "/api/importantes/editar", "metodo": "POST",
                                  "corpo": {"id": f"{1:012x}", "texto": "texto novo", "nota": "ver com calma"}}])

    def test_trazer_mostra_a_contagem_e_reabilita_o_botao(self):
        base = lista([item(1, "de fora", origem="cache", cache_n=493)])
        dados = rodar({
            "lista": [{"status": 200, "corpo": lista([])}, {"status": 200, "corpo": base}],
            "posts": {"/api/importantes/trazer": [{"corpo": {"trazidas": 1, "ja_estavam": 0, "recusadas": 2, "lidas": 9}}]},
            "acoes": [{"tipo": "clicar", "id": "importantes-trazer"}],
        })
        self.assertEqual(dados["aviso"], "Trazidas do Conselho: 1. Já estavam aqui: 0. Recusadas por segredo ou tamanho: 2.")
        self.assertFalse(dados["trazerDesabilitado"])
        self.assertEqual(dados["itens"][0]["origem"], "Do Conselho, entrada nº 493")

    def test_texto_do_item_sai_como_texto_puro(self):
        dados = rodar({"lista": {"status": 200, "corpo": lista([item(1, "<img src=x onerror=alert(1)> & fim")])}})
        self.assertEqual(dados["itens"][0]["texto"], "<img src=x onerror=alert(1)> & fim")

    def test_erro_500_no_pedido_nao_altera_a_lista_e_avisa(self):
        base = lista([item(1, "uma")])
        dados = rodar({
            "lista": [{"status": 200, "corpo": base}],
            "posts": {"/api/importantes/estado": [{"status": 500, "texto": ""}]},
            "acoes": [{"tipo": "clicarNoItem", "indice": 0, "texto": "Marcar feito"}],
        })
        self.assertEqual(dados["aviso"], "O painel respondeu com erro 500.")
        self.assertEqual([i["texto"] for i in dados["itens"]], ["uma"])


class EstaticoImportantesTests(unittest.TestCase):
    def test_bloco_novo_nao_usa_html_bruto_nem_atributo_de_estilo(self):
        for proibido in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
            with self.subTest(proibido=proibido):
                self.assertNotIn(proibido, BLOCO_JS)
        self.assertNotIn("style", BLOCO_JS.replace("estilo", ""))
        self.assertIsNone(re.search(r"\bon[a-z]+\s*=", BLOCO_JS), "nada de on* no bloco novo")

    def test_html_da_aba_e_do_cartao_sem_style_nem_on(self):
        trecho = HTML[HTML.index('id="sub-importantes"'): HTML.index('id="sub-importantes"') + 3000]
        cartao = HTML[HTML.index('id="importantes-cartao-estado"') - 400: HTML.index('id="importantes-cartao-estado"') + 400]
        for bloco in (trecho, cartao):
            self.assertIsNone(re.search(r"\sstyle\s*=", bloco))
            self.assertIsNone(re.search(r"\son[a-z]+\s*=", bloco))
        for estado in ("carregando", "vazio", "erro"):
            self.assertIn(f'data-estado="{estado}"', trecho)

    def test_cartao_e_aba_chamam_a_mesma_secao(self):
        self.assertIn('data-open-sub="importantes"', HTML)
        self.assertIn('data-sub="importantes" aria-controls="sub-importantes"', HTML)
        self.assertIn("importantes: () => carregarImportantes()", JS)

    def test_cores_do_bloco_novo_so_por_token(self):
        bloco = CSS[CSS.index("/* Importantes (11/11/2026)"):]
        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", bloco), [])

    def test_sem_emoji_nos_arquivos_da_entrega(self):
        emoji = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u26FF\uFE0F]")
        arquivos = ["prototipo.html", "prototipo.js", "prototipo.css", "importantes.py", "test_importantes.py",
                    "test_importantes_ui.py", "server.py", "spec/spec.md"]
        for nome in arquivos:
            with self.subTest(arquivo=nome):
                texto = (HERE / nome).read_text(encoding="utf-8")
                self.assertEqual(emoji.findall(texto), [], "emoji encontrado")


if __name__ == "__main__":
    unittest.main()
