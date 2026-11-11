#!/usr/bin/env python3
"""Checagens estáticas da seção de conversa do painel (prototipo.html / prototipo.js).

Não abre navegador e não chama o gateway: lê os dois arquivos e confere a CSP (sem script inline,
sem style=, sem atributos on*) e o uso do stream com render por textContent.
"""
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

import armazem
import chat_stream

HERE = Path(__file__).resolve().parent
HTML = (HERE / "prototipo.html").read_text(encoding="utf-8")
JS = (HERE / "prototipo.js").read_text(encoding="utf-8")
SERVIDOR = (HERE / "server.py").read_text(encoding="utf-8")

# Carrega o prototipo.js de verdade (IIFE) num contexto node, com um DOM mínimo e um fetch roteirizado pelo cenário.
# Nada sai da máquina: o fetch não chega à rede. Os passos: abrir uma conversa da lista, enviar mensagens e
# devolver o que foi enviado (chamadas), o texto do aviso de salvamento e a transcrição.
NODE_PAINEL = r"""
const fs = require('fs'); const path = require('path'); const vm = require('vm');
const {TextEncoder, TextDecoder} = require('util');
process.on('unhandledRejection', () => {});
const cen = JSON.parse(fs.readFileSync(0, 'utf8')); const dir = process.env.PAINEL_DIR;
class Texto { constructor(t) { this.textContent = t; } appendData(d) { this.textContent += d; } }
class Elemento {
  constructor(tag) {
    this.tag = tag; this.textContent = ''; this.hidden = false; this.className = ''; this.value = ''; this.disabled = false;
    this.dataset = {}; this.children = []; this.ouvintes = {}; this.scrollTop = 0; this.scrollHeight = 0; this.title = '';
    this.attrs = {}; this._classes = new Set();
    this.classList = {add: (...c) => c.forEach((x) => this._classes.add(x)), remove: (...c) => c.forEach((x) => this._classes.delete(x)),
      toggle() {}, contains: (x) => this._classes.has(x)};
    this.style = {};
  }
  append(...nos) { this.children.push(...nos); }
  replaceChildren(...nos) { this.children = nos; }
  setAttribute(nome, valor) { this.attrs[nome] = String(valor); }
  getAttribute(nome) { return Object.prototype.hasOwnProperty.call(this.attrs, nome) ? this.attrs[nome] : null; }
  addEventListener(tipo, fn) { (this.ouvintes[tipo] = this.ouvintes[tipo] || []).push(fn); }
  focus() {} blur() {} remove() {} select() {}
  closest() { return null; }
  querySelector(sel) { return buscar(this, sel)[0] || null; }
  querySelectorAll(sel) { return buscar(this, sel); }
}
function descendentes(no, saida = []) { for (const c of (no.children || [])) { if (c instanceof Elemento) saida.push(c); descendentes(c, saida); } return saida; }
function buscar(raiz, sel) {
  const m = /^\[data-([a-z-]+)="([^"]*)"\]$/.exec(sel);
  if (!m) return [];
  const chave = m[1].replace(/-([a-z])/g, (_, l) => l.toUpperCase());
  return descendentes(raiz).filter((e) => e.dataset[chave] === m[2]);
}
function texto(no) {
  if (!no) return '';
  if (no instanceof Texto) return no.textContent;
  if (typeof no === 'string') return no;
  return (no.textContent || '') + (no.children || []).map(texto).join('');
}
const registro = new Map();
const documento = {
  visibilityState: 'visible',
  getElementById(id) { if (!registro.has(id)) registro.set(id, new Elemento('id:' + id)); return registro.get(id); },
  querySelector() { return new Elemento('q'); }, querySelectorAll() { return []; },
  createElement(tag) { return new Elemento(tag); }, createElementNS(ns, tag) { return new Elemento(tag); },
  createTextNode(t) { return new Texto(t); }, addEventListener() {},
};
const cargas = []; const chamadas = [];
function escolher(valor) { if (Array.isArray(valor)) return valor.length > 1 ? valor.shift() : valor[0]; return valor; }
function cabecalhosDe(cab) { return {get: (nome) => (cab || {})[String(nome).toLowerCase()] ?? null}; }
function respostaJson(status, obj, cab) { return {ok: status >= 200 && status < 300, status, headers: cabecalhosDe(cab), json: async () => obj, text: async () => JSON.stringify(obj)}; }
function respostaTexto(status, texto) { return {ok: status >= 200 && status < 300, status, headers: cabecalhosDe({}), json: async () => { throw new Error('sem json'); }, text: async () => texto}; }
// Resposta que nunca termina: a Seth "está respondendo" até o fim do teste (proteção durante a resposta).
function respostaPendente() {
  return {ok: true, status: 200, headers: cabecalhosDe({}), json: async () => ({}), text: async () => '', body: {getReader() { return {
    read: () => new Promise(() => {}), cancel: async () => {}}; }}};
}
function respostaStream(sse, cab) {
  const bytes = new TextEncoder().encode(sse); let lido = false;
  return {ok: true, status: 200, headers: cabecalhosDe(cab), json: async () => ({}), text: async () => '', body: {getReader() { return {
    read: async () => { if (lido) return {done: true, value: undefined}; lido = true; return {done: false, value: bytes}; },
    cancel: async () => {}}; }}};
}
const ctx = {};
ctx.window = ctx; ctx.document = documento; ctx.location = {hash: ''}; ctx.history = {};
ctx.localStorage = {getItem() { return null; }, setItem() {}}; ctx.navigator = {clipboard: {}}; ctx.Node = function () {};
ctx.TextEncoder = TextEncoder; ctx.TextDecoder = TextDecoder;
ctx.AbortController = function () { this.signal = {}; this.abort = () => {}; };
ctx.setTimeout = () => 0; ctx.clearTimeout = () => {}; ctx.setInterval = () => 0; ctx.clearInterval = () => {};
ctx.addEventListener = (tipo, fn) => { if (tipo === 'load') cargas.push(fn); };
ctx.fetch = async (url, opcoes = {}) => {
  const metodo = String(opcoes.method || 'GET').toUpperCase();
  chamadas.push({url, metodo, corpo: typeof opcoes.body === 'string' ? opcoes.body : null});
  if (url === '/api/seth/conversas') return respostaJson(200, {schema_version: 1, state: 'ok', items: cen.conversas || [],
    pastas: cen.pastas || [], marcadores: cen.marcadores || [], total: cen.total ?? (cen.conversas || []).length, organizacao: cen.organizacao || 'ok',
    ilegiveis: cen.ilegiveis || 0});
  if (url === '/api/seth/lixeira' && metodo === 'GET') {
    if (cen.lixeiraErro) return respostaTexto(500, '');
    return respostaJson(200, {schema_version: 1, state: 'ok', items: cen.lixeira || [], total: (cen.lixeira || []).length, ilegiveis: cen.lixeiraIlegiveis || 0});
  }
  if (url === '/api/seth/lixeira/restaurar' && metodo === 'POST') {
    const r = escolher(cen.lixeiraRestaurar) || {};
    if (r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
    return respostaJson(200, {id: '0000000000b1', titulo: 'Apagada antes', restaurada: true});
  }
  if (url === '/api/seth/lixeira/purgar' && metodo === 'POST') {
    const r = escolher(cen.lixeiraPurgar) || {};
    if (r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
    return respostaJson(200, {purgada: true});
  }
  if (url === '/api/seth/conversa/apagar' && metodo === 'POST') {
    const r = escolher(cen.apagar) || {};
    if (r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
    return respostaJson(200, {apagada: true, lixeira: '0123456789ab-20261109-161800'});
  }
  if (url.startsWith('/api/seth/conversas/busca?')) {
    const r = escolher(cen.busca) || {};
    if (r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
    return respostaJson(200, r.corpo || {schema_version: 1, state: 'ok', termo: '', total: 0, resultados: []});
  }
  if (url.startsWith('/api/seth/conversa?id=')) return respostaJson(200, cen.conversa);
  if (url.startsWith('/api/seth/conversa/organizar') && metodo === 'POST') {
    const r = escolher(cen.organizar) || {};
    if (r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
    const c = JSON.parse(opcoes.body);
    return respostaJson(200, {id: c.id, fixada: !!c.fixada, arquivada: !!c.arquivada, marcadores: c.marcadores || [], pasta: c.pasta ?? null});
  }
  if (url === '/api/seth/pastas' && metodo === 'POST') {
    const r = escolher(cen.pastas_resp) || {};
    if (r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
    const c = JSON.parse(opcoes.body);
    return respostaJson(200, c.acao === 'apagar' ? {apagada: true, conversas_soltas: r.soltas ?? 0} : {id: '0a0a0a0a0a0a', nome: c.nome});
  }
  if (url === '/api/seth/conversa/importar' && metodo === 'POST') {
    const r = escolher(cen.importar) || {};
    if (r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
    return respostaJson(200, r.corpo || {estado: 'importada', id: '1111aaaa2222', titulo: 'Importada'});
  }
  if (url === '/api/seth/conversa' && metodo === 'POST') {
    const r = escolher(cen.salvar);
    if (r && r.rede) throw new TypeError('Failed to fetch');
    if (r && r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
    return respostaJson(200, {schema_version: 1, id: '0123456789ab', titulo: '', mensagens: []});
  }
  if (url === '/api/seth/chat/stream') {
    const r = escolher(cen.stream) || {};
    if (r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
    if (r.pendente) return respostaPendente();
    return respostaStream('data: {"tipo": "texto", "delta": "resposta"}\n\ndata: {"tipo": "fim"}\n\n', r.cabecalhos || {});
  }
  if (url === '/api/seth/chat') {
    const r = escolher(cen.chat) || {};
    return respostaJson(200, {schema_version: 1, content: 'resposta', model: 'seth-livre'}, r.cabecalhos || {});
  }
  return respostaTexto(404, '');
};
function coletar(no, saida) {
  if (!no || !no.children) return;
  for (const c of no.children) {
    if (typeof c.className === 'string' && (c.className.includes('seth-aviso') || c.className.includes('seth-vazio') || c.className.includes('msg-modelo'))) saida.push(c.textContent);
    coletar(c, saida);
  }
}
const esperar = async () => { for (let i = 0; i < 80; i++) await new Promise((r) => setImmediate(r)); };
function acharTodos(raiz, pred) { return descendentes(raiz).filter(pred); }
const resultados = [];  // valores devolvidos pelas ações 'js' (código rodado dentro da página, para testar funções internas)
async function executar(a) {
  const em = () => documento.getElementById(a.em || 'seth-conversas');
  if (a.tipo === 'js') {
    try { resultados.push(await vm.runInContext(a.codigo, ctx)); }
    catch (e) { resultados.push({erro: String((e && e.message) || e)}); }
  } else if (a.tipo === 'clicar') {
    const alvos = a.id ? [documento.getElementById(a.id)]
      : acharTodos(em(), (e) => e.tag === 'button' && texto(e).trim() === a.texto);
    const alvo = alvos[a.indice || 0];
    alvo.ouvintes.click[0]({target: alvo});
  } else if (a.tipo === 'mudar') {
    const el = a.id ? documento.getElementById(a.id) : acharTodos(em(), (e) => e.tag === 'select')[a.indice || 0]; el.value = a.valor; el.ouvintes.change[0]({target: el});
  } else if (a.tipo === 'digitar') {
    const el = documento.getElementById(a.id); el.value = a.valor; (el.ouvintes.input || []).forEach((f) => f({target: el}));
  } else if (a.tipo === 'tecla') {
    const el = documento.getElementById(a.id); el.ouvintes.keydown[0]({key: a.tecla, preventDefault() {}});
  } else if (a.tipo === 'enviar') {
    const form = a.id ? documento.getElementById(a.id) : acharTodos(em(), (e) => e.tag === 'form')[a.indice || 0];
    if (a.campo) documento.getElementById(a.campo).value = a.valor;
    else if (a.valor !== undefined) acharTodos(form, (e) => e.tag === 'input')[0].value = a.valor;
    form.ouvintes.submit[0]({preventDefault() {}, target: form});
  } else if (a.tipo === 'arquivo') {
    const el = documento.getElementById(a.id);
    el.files = [{size: a.tamanho ?? a.texto.length, text: async () => a.texto}];
    el.ouvintes.change[0]({target: el});
  }
  await esperar();
}
function itensDe(id) {
  return documento.getElementById(id).children
    .filter((c) => typeof c.className === 'string' && c.className.split(' ').includes('seth-item'))
    .map((c) => ({titulo: c.children[0].textContent, texto: texto(c), ativa: c.className.includes('ativa'), fixada: c.className.includes('fixada')}));
}
function opcoesDe(id) { return documento.getElementById(id).children.map((o) => [o.value, o.textContent]); }
(async () => {
  try {
    // Só para o teste: uma linha antes do fim da IIFE expõe sethSalvar e a conversa aberta (o arquivo em disco não muda).
    const fonte = fs.readFileSync(path.join(dir, 'prototipo.js'), 'utf8');
    const fim = fonte.lastIndexOf('})();');
    const instrumentado = fonte.slice(0, fim) + 'window.__teste = {sethSalvar, sethAtual: () => sethAtual};\n' + fonte.slice(fim);
    vm.createContext(ctx);
    vm.runInContext(instrumentado, ctx, {filename: 'prototipo.js'});
  } catch (e) { console.log(JSON.stringify({erro: 'carga: ' + e.message})); return; }
  for (const f of cargas) { try { f(); } catch (e) { /* carga de outras seções: fora do teste */ } }
  await esperar();
  if (cen.abrir) { documento.getElementById('seth-conversas').children[0].children[0].ouvintes.click[0](); await esperar(); }
  if (cen.renomear !== undefined) {
    const linha = documento.getElementById('seth-conversas').children[0];
    acharTodos(linha, (e) => e.tag === 'button' && texto(e).trim() === 'Renomear')[0].ouvintes.click[0]({});  // botão Renomear da conversa (sem abrir)
    const campo = linha.children[0]; campo.value = cen.renomear;
    campo.ouvintes.keydown[0]({key: 'Enter'}); await esperar();
  }
  if (cen.modelo) { const sel = documento.getElementById('seth-modelo'); sel.value = cen.modelo; sel.ouvintes.change[0]({target: sel}); }
  for (const a of cen.acoes || []) await executar(a);
  for (const texto_ of cen.enviar || []) {
    documento.getElementById('seth-input').value = texto_;
    documento.getElementById('seth-form').ouvintes.submit[0]({preventDefault() {}});
    await esperar();
  }
  for (const a of cen.depois || []) await executar(a);  // ações depois dos envios (ex.: trocar de conversa durante a resposta)
  const transcricao = []; coletar(documento.getElementById('seth-transcript'), transcricao);
  const salvar = documento.getElementById('seth-salvar-aviso');
  const el = (id) => documento.getElementById(id);
  console.log(JSON.stringify({chamadas, transcricao, salvarTexto: salvar.textContent, salvarOculto: salvar.hidden,
    status: el('seth-status').textContent,
    org: el('seth-org-aviso').textContent, orgOculto: el('seth-org-aviso').hidden,
    lista: itensDe('seth-conversas'), listaTexto: texto(el('seth-conversas')), grupos: descendentes(el('seth-conversas')).filter((e) => e.className === 'seth-grupo').map((e) => e.textContent),
    arquivadas: itensDe('seth-arquivadas'), arquivadasTotal: el('seth-arquivadas-total').textContent,
    listaOculta: el('seth-conversas').hidden, arquivadasOculta: el('seth-arquivadas-bloco').hidden,
    buscaOculta: el('seth-busca-resultados').hidden, busca: texto(el('seth-busca-resultados')),
    tempOculta: el('seth-temporaria-aviso').hidden, tempTexto: el('seth-temporaria-aviso').textContent,
    temporariaBotao: el('seth-temporaria').textContent, temporariaPressionado: el('seth-temporaria').getAttribute('aria-pressed'),
    tituloConversa: el('seth-titulo').textContent,
    exportTexto: el('seth-exportar-texto').textContent, exportJsonOculto: el('seth-export-json').hidden,
    exportJsonHref: el('seth-export-json').href, exportMdHref: el('seth-export-md').href,
    pastas: texto(el('seth-pastas')), filtroPasta: opcoesDe('seth-filtro-pasta'), filtroMarcador: opcoesDe('seth-filtro-marcador'),
    filtroPastaValor: el('seth-filtro-pasta').value, filtroMarcadorValor: el('seth-filtro-marcador').value,
    pastaNomeValor: el('seth-pasta-nome').value,
    destacadas: descendentes(el('seth-transcript')).filter((e) => e._classes.has('destacada')).map((e) => e.dataset.indice),
    transcritos: descendentes(el('seth-transcript')).filter((e) => e.tag === 'article').map((e) => e.dataset.indice),
    ilegiveisOculto: el('seth-ilegiveis-aviso').hidden, ilegiveisTexto: el('seth-ilegiveis-aviso').textContent,
    lixeiraTotal: el('seth-lixeira-total').textContent, lixeiraTexto: texto(el('seth-lixeira')),
    lixeiraItens: descendentes(el('seth-lixeira')).filter((c) => c.className === 'seth-item').map((c) => ({titulo: c.children[0].textContent, texto: texto(c)})),
    resultados}));
})();
"""


def rodar_painel(cenario):
    # O cenário vai por stdin: uma conversa grande não cabe numa variável de ambiente (limite do sistema).
    ambiente = dict(os.environ, PAINEL_DIR=str(HERE))
    resultado = subprocess.run(["node", "-e", NODE_PAINEL], input=json.dumps(cenario, ensure_ascii=False),
                               capture_output=True, text=True, timeout=120, env=ambiente)
    linhas = resultado.stdout.strip().splitlines()
    if resultado.returncode != 0 or not linhas:
        raise AssertionError("node não rodou (não medido): " + resultado.stderr[-400:])
    medido = json.loads(linhas[-1])
    if "erro" in medido:
        raise AssertionError("prototipo.js não carregou: " + medido["erro"])
    return medido


def chamadas_para(medido, url, metodo="POST"):
    return [c for c in medido["chamadas"] if c["url"] == url and c["metodo"] == metodo]


def corpo_de(chamada):
    return json.loads(chamada["corpo"])


CONVERSA_ID = "0123456789ab"
LISTA = [{"id": CONVERSA_ID, "titulo": "Antiga", "atualizada": "2026-11-09T10:00:00-03:00", "mensagens": 2}]


def conversa(mensagens):
    return {"schema_version": 1, "id": CONVERSA_ID, "titulo": "Antiga", "mensagens": mensagens}

INICIO_SECAO = '<div class="sub" id="sub-conversa"'
INICIO_BLOCO_JS = "/* (27/10/2026) Conversa com a Seth"
FIM_BLOCO_JS = "/* (27/10/2026) Grafo do vault"


def secao_conversa() -> str:
    inicio = HTML.index(INICIO_SECAO)
    fim = HTML.index("</section>", inicio + len(INICIO_SECAO))
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

    def test_seletor_de_modelo_na_secao_conversa(self):
        self.assertIn('<select id="seth-modelo"', secao_conversa())
        self.assertIn('<label for="seth-modelo">', secao_conversa())


class ConversaJs(unittest.TestCase):
    def test_usa_rota_de_stream(self):
        self.assertIn("/api/seth/chat/stream", JS)

    def test_mantem_fallback_para_chat_inteiro(self):
        self.assertIn('"/api/seth/chat"', JS)

    def test_envia_chave_mensagens_e_modelo_no_stream(self):
        # O corpo leva 'mensagens' e o 'modelo' escolhido (server.py, _seth_chat_stream).
        padrao = r'"/api/seth/chat/stream".*?body:\s*JSON\.stringify\(\{mensagens,\s*modelo\}\)'
        self.assertIsNotNone(re.search(padrao, bloco_conversa_js(), flags=re.DOTALL),
                             "o stream deve enviar os campos 'mensagens' e 'modelo' (server.py, _seth_chat_stream)")

    def test_fallback_tambem_envia_o_modelo(self):
        self.assertIn("JSON.stringify({messages: mensagens, modelo})", bloco_conversa_js())

    def test_seletor_busca_a_lista_no_servidor(self):
        self.assertIn('"/api/seth/modelos"', bloco_conversa_js())

    def test_seletor_usa_listener_no_js_e_nao_atributo_inline(self):
        self.assertIn('byId("seth-modelo").addEventListener("change"', bloco_conversa_js())
        self.assertIsNone(re.search(r"<select\b[^>]*\bon[a-z]+\s*=", HTML, flags=re.IGNORECASE))

    def test_resposta_mostra_o_modelo_que_a_respondeu(self):
        bloco = bloco_conversa_js()
        self.assertIn('"msg-modelo"', bloco)
        self.assertIn('"modelo: "', bloco)

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

    def test_aviso_de_conversa_nao_salva_existe_e_comeca_escondido(self):
        tag = re.search(r'<p id="seth-salvar-aviso"[^>]*>', secao_conversa())
        self.assertIsNotNone(tag, "falta o aviso de conversa não salva na seção Conversa")
        self.assertIn("hidden", tag.group(0))
        self.assertIn('role="status"', tag.group(0))


class ConversaComportamento(unittest.TestCase):
    """Fluxo real do prototipo.js (node + DOM mínimo + fetch roteirizado), sem rede."""

    def test_mensagem_longa_antiga_e_cortada_na_janela_com_aviso(self):
        antigas = [{"role": "user", "content": "x" * 4500}, {"role": "assistant", "content": "ok"}]
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(antigas), "abrir": True, "enviar": ["nova pergunta"]})
        pedidos = chamadas_para(medido, "/api/seth/chat/stream")
        self.assertEqual(len(pedidos), 1)
        mensagens = corpo_de(pedidos[0])["mensagens"]
        self.assertEqual(len(mensagens[0]["content"]), chat_stream.MAX_CARACTERES_MENSAGEM)
        self.assertTrue(mensagens[0]["content"].endswith("[cortado pelo painel para caber no limite de 4000 caracteres]"))
        self.assertEqual(mensagens[-1]["content"], "nova pergunta")
        self.assertTrue(any("1 mensagem antiga longa foi cortada para 4000 caracteres" in t for t in medido["transcricao"]),
                        medido["transcricao"])

    def test_conversa_salva_continua_com_a_mensagem_inteira(self):
        antigas = [{"role": "user", "content": "x" * 4500}, {"role": "assistant", "content": "ok"}]
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(antigas), "abrir": True, "enviar": ["nova pergunta"]})
        salvos = chamadas_para(medido, "/api/seth/conversa")
        self.assertTrue(salvos, "a conversa devia ser salva depois da resposta")
        self.assertEqual(len(corpo_de(salvos[-1])["mensagens"][0]["content"]), 4500)

    def test_janela_respeita_o_teto_de_bytes_do_pedido(self):
        antigas = [{"role": "user" if i % 2 == 0 else "assistant", "content": "\n" * 4000} for i in range(19)]
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(antigas), "abrir": True, "enviar": ["oi"]})
        pedido = chamadas_para(medido, "/api/seth/chat/stream")[0]
        self.assertLessEqual(len(pedido["corpo"].encode("utf-8")), panel_limite_pedido())
        self.assertEqual(corpo_de(pedido)["mensagens"][-1]["content"], "oi")
        self.assertTrue(any("de fora" in t for t in medido["transcricao"]), medido["transcricao"])

    def test_400_do_stream_mostra_o_motivo_real_e_nao_cai_em_falha_desconhecida(self):
        medido = rodar_painel({"stream": {"status": 400, "texto": "mensagem 1 acima de 4000 caracteres"}, "enviar": ["oi"]})
        self.assertIn("Não consegui responder agora: o painel recusou o pedido (mensagem 1 acima de 4000 caracteres).",
                      medido["transcricao"])
        self.assertFalse(any("falha desconhecida" in t for t in medido["transcricao"]))
        self.assertEqual(chamadas_para(medido, "/api/seth/chat"), [], "erro 400 não repete a pergunta pelo fallback")

    def test_conversa_acima_de_262144_bytes_nao_e_enviada_e_avisa_o_motivo(self):
        grande = conversa([{"role": "user" if i % 2 == 0 else "assistant", "content": "y" * 65000} for i in range(5)])
        medido = rodar_painel({"conversas": LISTA, "conversa": grande, "abrir": True, "enviar": ["oi"]})
        self.assertEqual(chamadas_para(medido, "/api/seth/conversa"), [], "conversa acima do limite não devia ir ao servidor")
        self.assertFalse(medido["salvarOculto"])
        self.assertTrue(medido["salvarTexto"].startswith(
            "Conversa não salva: a conversa passou de 262144 bytes (256 KB), o limite de cada gravação."), medido["salvarTexto"])
        self.assertIn("O que está guardado é a última gravação feita", medido["salvarTexto"])
        self.assertIn("comece uma conversa nova", medido["salvarTexto"])

    def test_413_do_servidor_avisa_que_nao_salvou(self):
        medido = rodar_painel({"salvar": {"status": 413, "texto": "conversa acima de 262144 bytes"}, "enviar": ["oi"]})
        self.assertEqual(len(chamadas_para(medido, "/api/seth/conversa")), 1)
        self.assertFalse(medido["salvarOculto"])
        self.assertIn("Conversa não salva: a conversa passou de 262144 bytes", medido["salvarTexto"])
        self.assertIn("Nada desta conversa está guardado ainda.", medido["salvarTexto"])

    def test_400_do_servidor_mostra_o_motivo_da_conversa(self):
        medido = rodar_painel({"salvar": {"status": 400, "texto": "mais de 200 mensagens"}, "enviar": ["oi"]})
        self.assertIn("Conversa não salva: o painel recusou a conversa (mais de 200 mensagens).", medido["salvarTexto"])

    def test_falha_de_rede_ao_salvar_avisa(self):
        medido = rodar_painel({"salvar": {"rede": True}, "enviar": ["oi"]})
        self.assertTrue(medido["salvarTexto"].startswith("Conversa não salva: sem resposta do painel."), medido["salvarTexto"])

    def test_renomear_conversa_fechada_com_falha_avisa(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa([{"role": "user", "content": "oi"}]),
                               "renomear": "Novo nome", "salvar": {"status": 413, "texto": "x"}})
        self.assertEqual(len(chamadas_para(medido, "/api/seth/conversa")), 1, "renomear grava a conversa fechada")
        self.assertFalse(medido["salvarOculto"])
        self.assertIn('Não foi possível salvar o novo nome da conversa "Antiga": a conversa passou de 262144 bytes',
                      medido["salvarTexto"])

    def test_gravacao_que_volta_a_dar_certo_limpa_o_aviso(self):
        medido = rodar_painel({"salvar": [{"status": 413, "texto": "x"}, {"status": 200}], "enviar": ["um", "dois"]})
        self.assertTrue(medido["salvarOculto"])
        self.assertEqual(medido["salvarTexto"], "")

    # Modelo que respondeu: o real (cabeçalho X-Modelo-Real do gateway) ou, sem ele, o escolhido marcado "(escolhido)".

    def test_modelo_real_do_cabecalho_aparece_na_resposta_e_vai_salvo(self):
        medido = rodar_painel({"stream": {"cabecalhos": {"x-modelo-real": "openai/gpt-oss-120b"}}, "enviar": ["oi"]})
        self.assertIn("modelo: openai/gpt-oss-120b", medido["transcricao"])
        salvos = chamadas_para(medido, "/api/seth/conversa")
        self.assertEqual(corpo_de(salvos[-1])["mensagens"][-1],
                         {"role": "assistant", "content": "resposta", "modelo": "seth-livre", "modelo_real": "openai/gpt-oss-120b"})

    def test_sem_cabecalho_mostra_o_escolhido_marcado_e_nao_grava_modelo_real(self):
        medido = rodar_painel({"stream": {}, "modelo": "seth-public", "enviar": ["oi"]})
        self.assertIn("modelo: seth-public (escolhido)", medido["transcricao"])
        self.assertEqual(corpo_de(chamadas_para(medido, "/api/seth/chat/stream")[0])["modelo"], "seth-public")
        salvos = chamadas_para(medido, "/api/seth/conversa")
        self.assertNotIn("modelo_real", corpo_de(salvos[-1])["mensagens"][-1])

    def test_fallback_com_cabecalho_mostra_o_modelo_real(self):
        medido = rodar_painel({"stream": {"status": 404}, "chat": {"cabecalhos": {"x-modelo-real": "openai/gpt-oss-120b"}},
                               "enviar": ["oi"]})
        self.assertEqual(len(chamadas_para(medido, "/api/seth/chat")), 1, "o 404 do stream cai no fallback")
        self.assertIn("modelo: openai/gpt-oss-120b", medido["transcricao"])

    def test_fallback_sem_cabecalho_mostra_o_escolhido_marcado(self):
        medido = rodar_painel({"stream": {"status": 404}, "enviar": ["oi"]})
        self.assertIn("modelo: seth-livre (escolhido)", medido["transcricao"])

    def test_conversa_antiga_sem_modelo_real_mostra_o_escolhido(self):
        antigas = [{"role": "user", "content": "oi"}, {"role": "assistant", "content": "ok", "modelo": "seth-public"}]
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(antigas), "abrir": True, "enviar": []})
        self.assertIn("modelo: seth-public (escolhido)", medido["transcricao"])


def panel_limite_pedido() -> int:
    return int(re.search(r"^CHAT_STREAM_LIMITE_BYTES = ([\d_]+)", SERVIDOR, flags=re.M).group(1).replace("_", ""))


PASTA_ID = "a00000000001"
PASTA = {"id": PASTA_ID, "nome": "Projeto X", "conversas": 1}
JSON_IMPORTAVEL = json.dumps({"formato": "agata-conversa", "versao": 1, "id": "1111aaaa2222", "origem_id": "1111aaaa2222",
                              "titulo": "Vinda", "modelo": "seth-livre", "mensagens": [{"role": "user", "content": "oi"}]})


def conversa_item(id_, titulo, **extra):
    base = {"id": id_, "titulo": titulo, "atualizada": "2026-11-09T10:00:00-03:00", "mensagens": 2,
            "fixada": False, "arquivada": False, "marcadores": [], "pasta": None}
    return {**base, **extra}


class ConversaOrganizacaoHtml(unittest.TestCase):
    IDS = ["seth-temporaria", "seth-temporaria-aviso", "seth-busca", "seth-busca-resultados", "seth-filtro-pasta",
           "seth-filtro-marcador", "seth-org-aviso", "seth-arquivadas-bloco", "seth-arquivadas", "seth-arquivadas-total",
           "seth-pastas-bloco", "seth-pasta-form", "seth-pasta-nome", "seth-pasta-criar", "seth-pastas",
           "seth-importar-arquivo", "seth-exportar-texto", "seth-export-json", "seth-export-md",
           "seth-ilegiveis-aviso", "seth-lixeira-bloco", "seth-lixeira-total", "seth-lixeira"]

    def test_ids_da_organizacao_existem_na_secao_conversa(self):
        for ident in self.IDS:
            with self.subTest(ident=ident):
                self.assertIn(f'id="{ident}"', secao_conversa())

    def test_campo_de_busca_e_nome_de_pasta_com_limite(self):
        self.assertRegex(secao_conversa(), r'<input id="seth-busca" type="search" maxlength="120"')
        self.assertRegex(secao_conversa(), r'<input id="seth-pasta-nome" type="text" maxlength="60"')

    def test_exportacao_e_link_com_download_e_sem_script(self):
        self.assertRegex(secao_conversa(), r'<a class="text-link" id="seth-export-json" href="#" download hidden>')
        self.assertRegex(secao_conversa(), r'<a class="text-link" id="seth-export-md" href="#" download hidden>')

    def test_aviso_de_temporaria_comeca_escondido_e_com_status(self):
        tag = re.search(r'<p id="seth-temporaria-aviso"[^>]*>', secao_conversa())
        self.assertIsNotNone(tag)
        self.assertIn("hidden", tag.group(0))
        self.assertIn('role="status"', tag.group(0))


class ConversaLista(unittest.TestCase):
    """Lista, busca, pastas, marcadores, temporária, exportação e importação no prototipo.js (node, DOM mínimo, sem rede)."""

    def test_fixada_fica_no_topo_com_grupo_e_selo(self):
        itens = [conversa_item("0000000000a2", "Fixada antiga", fixada=True), conversa_item("0000000000a1", "Recente")]
        medido = rodar_painel({"conversas": itens})
        self.assertEqual([i["titulo"] for i in medido["lista"]], ["Fixada antiga", "Recente"])
        self.assertEqual(medido["grupos"], ["Fixadas", "Recentes"])
        self.assertIn("Fixada", medido["lista"][0]["texto"])
        self.assertTrue(medido["lista"][0]["fixada"])

    def test_arquivadas_saem_da_lista_principal_e_ficam_na_secao(self):
        itens = [conversa_item("0000000000a1", "Ativa"), conversa_item("0000000000a2", "Guardada", arquivada=True)]
        medido = rodar_painel({"conversas": itens})
        self.assertEqual([i["titulo"] for i in medido["lista"]], ["Ativa"])
        self.assertEqual([i["titulo"] for i in medido["arquivadas"]], ["Guardada"])
        self.assertEqual(medido["arquivadasTotal"], "1")
        self.assertIn("Arquivada", medido["arquivadas"][0]["texto"])

    def test_desarquivar_chama_organizar_com_arquivada_falsa(self):
        medido = rodar_painel({"conversas": [conversa_item("0000000000a2", "Guardada", arquivada=True)],
                               "acoes": [{"tipo": "clicar", "em": "seth-arquivadas", "texto": "Desarquivar"}]})
        pedidos = chamadas_para(medido, "/api/seth/conversa/organizar")
        self.assertEqual(corpo_de(pedidos[-1]), {"id": "0000000000a2", "arquivada": False})

    def test_fixar_chama_organizar_com_fixada_verdadeira(self):
        medido = rodar_painel({"conversas": [conversa_item("0000000000a1", "Uma")],
                               "acoes": [{"tipo": "clicar", "texto": "Fixar"}]})
        self.assertEqual(corpo_de(chamadas_para(medido, "/api/seth/conversa/organizar")[-1]), {"id": "0000000000a1", "fixada": True})
        self.assertTrue(medido["orgOculto"], "sem erro, o aviso de organização fica escondido")

    def test_organizar_recusado_mostra_motivo_em_portugues(self):
        medido = rodar_painel({"conversas": [conversa_item("0000000000a1", "Uma")],
                               "acoes": [{"tipo": "clicar", "texto": "Fixar"}],
                               "organizar": {"status": 404, "texto": "conversa não encontrada"}})
        self.assertEqual(medido["org"], "Conversa ou pasta não encontrada; a lista foi atualizada.")

    def test_marcador_adicionado_e_tirado_manda_a_lista_inteira(self):
        itens = [conversa_item("0000000000a1", "Marcada", marcadores=["auditoria", "ideia"])]
        medido = rodar_painel({"conversas": itens, "acoes": [
            {"tipo": "enviar", "em": "seth-conversas", "valor": "Revisão"},
            {"tipo": "clicar", "texto": "tirar", "indice": 0}]})
        pedidos = chamadas_para(medido, "/api/seth/conversa/organizar")
        self.assertEqual(corpo_de(pedidos[0]), {"id": "0000000000a1", "marcadores": ["auditoria", "ideia", "Revisão"]})
        self.assertEqual(corpo_de(pedidos[1]), {"id": "0000000000a1", "marcadores": ["ideia"]})

    def test_mover_para_pasta_e_sem_pasta(self):
        itens = [conversa_item("0000000000a1", "Uma")]
        medido = rodar_painel({"conversas": itens, "pastas": [PASTA],
                               "acoes": [{"tipo": "mudar", "em": "seth-conversas", "valor": PASTA_ID}]})
        self.assertEqual(corpo_de(chamadas_para(medido, "/api/seth/conversa/organizar")[-1]), {"id": "0000000000a1", "pasta": PASTA_ID})
        medido2 = rodar_painel({"conversas": [conversa_item("0000000000a1", "Uma", pasta=PASTA_ID)], "pastas": [PASTA],
                                "acoes": [{"tipo": "mudar", "em": "seth-conversas", "valor": ""}]})
        self.assertEqual(corpo_de(chamadas_para(medido2, "/api/seth/conversa/organizar")[-1]), {"id": "0000000000a1", "pasta": None})

    def test_filtro_por_pasta_e_por_marcador(self):
        itens = [conversa_item("0000000000a1", "Na pasta", pasta=PASTA_ID, marcadores=["auditoria"]),
                 conversa_item("0000000000a2", "Solta")]
        base = {"conversas": itens, "pastas": [PASTA], "marcadores": ["auditoria"]}
        por_pasta = rodar_painel({**base, "acoes": [{"tipo": "mudar", "id": "seth-filtro-pasta", "valor": PASTA_ID}]})
        self.assertEqual([i["titulo"] for i in por_pasta["lista"]], ["Na pasta"])
        self.assertEqual(por_pasta["filtroPastaValor"], PASTA_ID)
        sem_pasta = rodar_painel({**base, "acoes": [{"tipo": "mudar", "id": "seth-filtro-pasta", "valor": "-"}]})
        self.assertEqual([i["titulo"] for i in sem_pasta["lista"]], ["Solta"])
        por_marcador = rodar_painel({**base, "acoes": [{"tipo": "mudar", "id": "seth-filtro-marcador", "valor": "auditoria"}]})
        self.assertEqual([i["titulo"] for i in por_marcador["lista"]], ["Na pasta"])
        vazio = rodar_painel({**base, "acoes": [{"tipo": "mudar", "id": "seth-filtro-marcador", "valor": "auditoria"},
                                                {"tipo": "mudar", "id": "seth-filtro-pasta", "valor": "-"}]})
        self.assertIn("Nenhuma conversa com este filtro.", vazio["listaTexto"])
        self.assertIn("#auditoria", por_pasta["lista"][0]["texto"])

    def test_pasta_criar_envia_post_e_limpa_o_campo(self):
        medido = rodar_painel({"conversas": [], "acoes": [
            {"tipo": "digitar", "id": "seth-pasta-nome", "valor": "Projeto X"}, {"tipo": "enviar", "id": "seth-pasta-form"}]})
        self.assertEqual(corpo_de(chamadas_para(medido, "/api/seth/pastas")[0]), {"acao": "criar", "nome": "Projeto X"})
        self.assertEqual(medido["org"], "Pasta criada: Projeto X.")
        self.assertEqual(medido["pastaNomeValor"], "")

    def test_pasta_recusada_mantem_o_nome_e_mostra_motivo(self):
        medido = rodar_painel({"conversas": [], "pastas_resp": {"status": 400, "texto": "já existe pasta com esse nome"},
                               "acoes": [{"tipo": "digitar", "id": "seth-pasta-nome", "valor": "Projeto X"},
                                         {"tipo": "enviar", "id": "seth-pasta-form"}]})
        self.assertEqual(medido["org"], "Não foi possível salvar: já existe pasta com esse nome.")
        self.assertEqual(medido["pastaNomeValor"], "Projeto X")

    def test_apagar_pasta_pede_confirmacao_e_avisa_que_conversas_ficam(self):
        medido = rodar_painel({"conversas": [conversa_item("0000000000a1", "Uma", pasta=PASTA_ID)], "pastas": [PASTA],
                               "pastas_resp": {"soltas": 1},
                               "acoes": [{"tipo": "clicar", "em": "seth-pastas", "texto": "Apagar"}]})
        self.assertEqual(chamadas_para(medido, "/api/seth/pastas"), [], "o primeiro clique só pede confirmação")
        medido = rodar_painel({"conversas": [conversa_item("0000000000a1", "Uma", pasta=PASTA_ID)], "pastas": [PASTA],
                               "pastas_resp": {"soltas": 1},
                               "acoes": [{"tipo": "clicar", "em": "seth-pastas", "texto": "Apagar"},
                                         {"tipo": "clicar", "em": "seth-pastas", "texto": "Confirmar apagar pasta"}]})
        self.assertEqual(corpo_de(chamadas_para(medido, "/api/seth/pastas")[0]), {"acao": "apagar", "id": PASTA_ID})
        self.assertEqual(medido["org"], "Pasta apagada. A conversa dela continua na lista, sem pasta.")

    def test_busca_mostra_trecho_e_abre_na_mensagem_destacada(self):
        busca = {"corpo": {"schema_version": 1, "state": "ok", "termo": "acao", "total": 1, "resultados": [
            {"id": CONVERSA_ID, "titulo": "Antiga", "atualizada": "2026-11-09T10:00:00-03:00", "arquivada": False,
             "ocorrencias": 2, "campo": "mensagem", "mensagem": 1, "trecho": "…revisar a AÇÃO do decisor…"}]}}
        conv = conversa([{"role": "user", "content": "oi"}, {"role": "assistant", "content": "nada"},
                         {"role": "user", "content": "revisar a ação do decisor"}])
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "busca": busca, "acoes": [
            {"tipo": "digitar", "id": "seth-busca", "valor": "acao"},
            {"tipo": "clicar", "em": "seth-busca-resultados", "texto": "Abrir na mensagem 2"}]})
        self.assertIn("/api/seth/conversas/busca?q=acao", [c["url"] for c in medido["chamadas"]])
        self.assertIn("1 conversa salva tem este texto.", medido["busca"])
        self.assertIn("…revisar a AÇÃO do decisor…", medido["busca"])
        self.assertIn("na mensagem 2", medido["busca"])
        self.assertTrue(medido["listaOculta"], "com busca ativa, a lista principal sai da tela")
        self.assertEqual(medido["destacadas"], ["1"])

    def test_busca_vazia_volta_para_a_lista_sem_chamar_o_servidor(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [
            {"tipo": "digitar", "id": "seth-busca", "valor": "ab"}, {"tipo": "digitar", "id": "seth-busca", "valor": "   "}]})
        self.assertEqual(len([c for c in medido["chamadas"] if "/busca?q=" in c["url"]]), 1)
        self.assertFalse(medido["listaOculta"])
        self.assertTrue(medido["buscaOculta"])

    def test_busca_sem_resultado_diz_que_so_ve_conversas_salvas(self):
        medido = rodar_painel({"conversas": LISTA, "busca": {"corpo": {"schema_version": 1, "state": "ok", "termo": "x", "total": 0, "resultados": []}},
                               "acoes": [{"tipo": "digitar", "id": "seth-busca", "valor": "xyz"}]})
        self.assertIn("Nenhuma conversa salva tem este texto (a busca vê só as conversas salvas).", medido["busca"])

    def test_busca_recusada_pelo_servidor_mostra_o_motivo(self):
        medido = rodar_painel({"conversas": LISTA, "busca": {"status": 400, "texto": "a busca aceita até 120 caracteres"},
                               "acoes": [{"tipo": "digitar", "id": "seth-busca", "valor": "xyz"}]})
        self.assertIn("Busca não feita: a busca aceita até 120 caracteres.", medido["busca"])

    def test_temporaria_mostra_o_estado_na_tela(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "clicar", "id": "seth-temporaria"}]})
        self.assertFalse(medido["tempOculta"])
        self.assertIn("Conversa temporária: não é salva.", secao_conversa())  # o texto do aviso é estático (HTML)
        self.assertEqual(medido["temporariaPressionado"], "true")
        self.assertEqual(medido["temporariaBotao"], "Conversa temporária: ligada")
        self.assertEqual(medido["tituloConversa"], "Conversa temporária")
        self.assertEqual(medido["status"], "TEMPORÁRIA")
        self.assertTrue(medido["exportJsonOculto"])
        self.assertIn("não há o que exportar", medido["exportTexto"])

    def test_temporaria_nao_grava_a_resposta(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "clicar", "id": "seth-temporaria"}], "enviar": ["oi"]})
        self.assertEqual(chamadas_para(medido, "/api/seth/conversa"), [], "conversa temporária não é gravada")
        self.assertEqual(len(chamadas_para(medido, "/api/seth/chat/stream")), 1, "a resposta segue pelo mesmo caminho")
        self.assertEqual(len([t for t in medido["transcricao"] if t.startswith("modelo:")]), 1)
        self.assertTrue(medido["exportJsonOculto"])
        self.assertIn("não há o que exportar", medido["exportTexto"])
        self.assertEqual([i["titulo"] for i in medido["lista"]], ["Antiga"], "a temporária não entra na lista")

    def test_temporaria_desligada_volta_a_gravar(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "clicar", "id": "seth-temporaria"},
                                                             {"tipo": "clicar", "id": "seth-temporaria"}], "enviar": ["oi"]})
        self.assertTrue(medido["tempOculta"])
        self.assertEqual(medido["status"], "PRONTA")
        self.assertTrue(chamadas_para(medido, "/api/seth/conversa"), "conversa normal volta a ser salva")

    def test_abrir_conversa_salva_tira_a_temporaria(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa([{"role": "user", "content": "oi"}]),
                               "acoes": [{"tipo": "clicar", "id": "seth-temporaria"}, {"tipo": "clicar", "texto": "Antiga"}]})
        self.assertTrue(medido["tempOculta"])
        self.assertEqual(medido["temporariaPressionado"], "false")
        self.assertEqual(medido["transcritos"], ["0"])

    def test_exportacao_aponta_para_a_rota_da_conversa_salva(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa([{"role": "user", "content": "oi"}]), "abrir": True})
        self.assertFalse(medido["exportJsonOculto"])
        self.assertEqual(medido["exportJsonHref"], f"/api/seth/conversa/exportar?id={CONVERSA_ID}&formato=json")
        self.assertEqual(medido["exportMdHref"], f"/api/seth/conversa/exportar?id={CONVERSA_ID}&formato=md")

    def test_importar_envia_o_arquivo_e_avisa(self):
        medido = rodar_painel({"conversas": [], "acoes": [{"tipo": "arquivo", "id": "seth-importar-arquivo", "texto": JSON_IMPORTAVEL}],
                               "importar": {"corpo": {"estado": "importada", "id": "2222bbbb3333", "titulo": "Vinda"}}})
        pedidos = chamadas_para(medido, "/api/seth/conversa/importar")
        self.assertEqual(pedidos[0]["corpo"], JSON_IMPORTAVEL)
        self.assertEqual(medido["org"], "Conversa importada: Vinda.")

    def test_importar_ja_existente_nao_duplica_e_avisa(self):
        medido = rodar_painel({"conversas": [], "acoes": [{"tipo": "arquivo", "id": "seth-importar-arquivo", "texto": JSON_IMPORTAVEL}],
                               "importar": {"corpo": {"estado": "ja_existe", "id": CONVERSA_ID, "titulo": "Vinda"}}})
        self.assertEqual(medido["org"], "Esta conversa já estava aqui (Vinda); nada foi duplicado.")

    def test_importar_acima_do_limite_nem_e_enviado(self):
        medido = rodar_painel({"conversas": [], "acoes": [{"tipo": "arquivo", "id": "seth-importar-arquivo",
                                                           "texto": JSON_IMPORTAVEL, "tamanho": 263169}]})
        self.assertEqual(chamadas_para(medido, "/api/seth/conversa/importar"), [])
        self.assertEqual(medido["org"], "Arquivo não importado: passa do limite de 263168 bytes (257 KB).")

    def test_importar_recusado_pelo_servidor_mostra_motivo(self):
        medido = rodar_painel({"conversas": [], "acoes": [{"tipo": "arquivo", "id": "seth-importar-arquivo", "texto": "{}"}],
                               "importar": {"status": 400, "texto": "o arquivo não é uma conversa exportada pelo painel (formato ou versão)"}})
        self.assertEqual(medido["org"], "Arquivo não importado: o arquivo não é uma conversa exportada pelo painel (formato ou versão).")

    def test_organizacao_ilegivel_avisa_e_mantem_a_lista(self):
        medido = rodar_painel({"conversas": LISTA, "organizacao": "ilegivel"})
        self.assertTrue(medido["org"].startswith("A organização das conversas"))
        self.assertFalse(medido["orgOculto"])
        self.assertEqual(len(medido["lista"]), 1)

    def test_lista_mostra_quantas_faltam_quando_passa_de_200(self):
        medido = rodar_painel({"conversas": LISTA, "total": 230})
        self.assertIn("Mostrando as 1 conversas mais recentes de 230.", medido["listaTexto"])


LIXEIRA_NOME = "0000000000b1-20261109-161800"
LIXEIRA_ITEM = {"nome": LIXEIRA_NOME, "id": "0000000000b1", "titulo": "Apagada antes", "apagada_em": "09/11/2026 16:18", "mensagens": 2}
CONFIRMA_APAGAR = "Confirmar: mover para a Lixeira"
ENVIO_EM_CURSO = "A Seth ainda está respondendo. Espere a resposta para trocar de conversa."


class ConversaProtecao(unittest.TestCase):
    """Proteção das conversas (09/11/2026): apagar vai para a Lixeira, a tela não troca durante a resposta,
    salvar grava na conversa de origem, arquivos ilegíveis são contados e a Lixeira tem restaurar e purga manual."""

    def test_apagar_pede_confirmacao_e_manda_para_a_lixeira(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "clicar", "texto": "Apagar"}]})
        self.assertEqual(chamadas_para(medido, "/api/seth/conversa/apagar"), [], "o primeiro clique só pede confirmação")
        medido = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "clicar", "texto": "Apagar"},
                                                             {"tipo": "clicar", "texto": CONFIRMA_APAGAR}]})
        self.assertEqual(corpo_de(chamadas_para(medido, "/api/seth/conversa/apagar")[0]), {"id": CONVERSA_ID})
        self.assertEqual(medido["org"], "Conversa movida para a Lixeira. Restaure-a por lá, se precisar.")

    def test_erro_ao_apagar_nao_fecha_a_conversa_aberta(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa([{"role": "user", "content": "oi"}]), "abrir": True,
                               "apagar": {"status": 500, "texto": "x"},
                               "acoes": [{"tipo": "clicar", "texto": "Apagar"}, {"tipo": "clicar", "texto": CONFIRMA_APAGAR}]})
        self.assertEqual(medido["org"], "Não foi possível apagar a conversa: o painel respondeu com erro 500.")
        self.assertEqual(medido["tituloConversa"], "Antiga", "sem a confirmação do painel, a conversa segue aberta")
        self.assertEqual(medido["transcritos"], ["0"])

    def test_apagar_confirmado_fecha_a_conversa_aberta(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa([{"role": "user", "content": "oi"}]), "abrir": True,
                               "acoes": [{"tipo": "clicar", "texto": "Apagar"}, {"tipo": "clicar", "texto": CONFIRMA_APAGAR}]})
        self.assertEqual(medido["tituloConversa"], "Nova conversa")
        self.assertEqual(medido["transcritos"], [])

    def test_nova_conversa_e_bloqueada_enquanto_a_seth_responde(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa([{"role": "user", "content": "oi"}]), "abrir": True,
                               "stream": {"pendente": True}, "enviar": ["pergunta"],
                               "depois": [{"tipo": "clicar", "id": "seth-nova"}]})
        self.assertEqual(medido["tituloConversa"], "Antiga", "a conversa aberta continua na tela")
        self.assertEqual(medido["org"], ENVIO_EM_CURSO)
        self.assertIn("A Seth está respondendo…", medido["transcricao"])

    def test_abrir_outra_conversa_e_bloqueado_enquanto_a_seth_responde(self):
        outra = conversa_item("0000000000a2", "Outra")
        medido = rodar_painel({"conversas": LISTA + [outra], "conversa": conversa([{"role": "user", "content": "oi"}]),
                               "abrir": True, "stream": {"pendente": True}, "enviar": ["pergunta"],
                               "depois": [{"tipo": "clicar", "em": "seth-conversas", "texto": "Outra"}]})
        self.assertEqual(medido["org"], ENVIO_EM_CURSO)
        self.assertEqual([c for c in medido["chamadas"] if c["url"] == "/api/seth/conversa?id=0000000000a2"], [],
                         "a conversa pedida não é nem carregada enquanto a resposta não termina")

    def test_depois_da_resposta_a_troca_volta_a_funcionar(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa([{"role": "user", "content": "oi"}]), "abrir": True,
                               "enviar": ["pergunta"], "depois": [{"tipo": "clicar", "id": "seth-nova"}]})
        self.assertEqual(medido["tituloConversa"], "Nova conversa")
        self.assertEqual(medido["org"], "")

    def test_salvar_grava_na_conversa_de_origem_e_nao_na_tela(self):
        # sethSalvar(alvo) grava o id na conversa passada, não na conversa aberta na tela.
        codigo = ("(async () => { const outra = {id: null, titulo: 'Outra', mensagens: [{role: 'user', content: 'x'}], "
                  "modelo: 'seth-livre', temporaria: false}; const ok = await __teste.sethSalvar(outra); "
                  "return {ok, outraId: outra.id, atualId: __teste.sethAtual().id}; })()")
        medido = rodar_painel({"acoes": [{"tipo": "js", "codigo": codigo}]})
        self.assertEqual(medido["resultados"][0], {"ok": True, "outraId": "0123456789ab", "atualId": None})

    def test_falha_ao_salvar_conversa_que_nao_esta_na_tela_avisa_pelo_titulo(self):
        codigo = ("(async () => { const outra = {id: null, titulo: 'Outra', mensagens: [{role: 'user', content: 'x'}], "
                  "modelo: 'seth-livre', temporaria: false}; const ok = await __teste.sethSalvar(outra); "
                  "return {ok, naoSalva: outra.naoSalva}; })()")
        medido = rodar_painel({"salvar": {"status": 413, "texto": "x"}, "acoes": [{"tipo": "js", "codigo": codigo}]})
        self.assertFalse(medido["resultados"][0]["ok"])
        self.assertTrue(medido["resultados"][0]["naoSalva"].startswith("Conversa não salva: "))
        self.assertTrue(medido["salvarTexto"].startswith('A conversa "Outra" não foi salva: a conversa passou de 262144 bytes'),
                        medido["salvarTexto"])

    def test_ilegiveis_avisa_a_contagem_e_mantem_a_lista(self):
        medido = rodar_painel({"conversas": LISTA, "ilegiveis": 2})
        self.assertFalse(medido["ilegiveisOculto"])
        self.assertEqual(medido["ilegiveisTexto"], "2 arquivos de conversa não puderam ser lidos e não aparecem aqui. "
                                                   "Nada foi apagado; confira a pasta de conversas.")
        self.assertEqual([i["titulo"] for i in medido["lista"]], ["Antiga"])

    def test_ilegivel_da_lixeira_entra_na_mesma_contagem(self):
        medido = rodar_painel({"conversas": LISTA, "ilegiveis": 0, "lixeira": [LIXEIRA_ITEM], "lixeiraIlegiveis": 1})
        self.assertEqual(medido["ilegiveisTexto"], "1 arquivo de conversa não pôde ser lido e não aparece aqui. "
                                                   "Nada foi apagado; confira a pasta de conversas.")

    def test_sem_ilegiveis_o_aviso_fica_escondido(self):
        medido = rodar_painel({"conversas": LISTA})
        self.assertTrue(medido["ilegiveisOculto"])
        self.assertEqual(medido["ilegiveisTexto"], "")

    def test_lixeira_lista_titulo_data_e_botoes(self):
        medido = rodar_painel({"conversas": [], "lixeira": [LIXEIRA_ITEM]})
        self.assertEqual(medido["lixeiraTotal"], "1")
        self.assertEqual(medido["lixeiraItens"][0]["titulo"], "Apagada antes")
        self.assertIn("Apagada em 09/11/2026 16:18 · 2 mensagens", medido["lixeiraItens"][0]["texto"])
        self.assertIn("Restaurar", medido["lixeiraItens"][0]["texto"])
        self.assertIn("Apagar de vez", medido["lixeiraItens"][0]["texto"])

    def test_lixeira_vazia_e_indisponivel_dizem_isso(self):
        self.assertIn("A lixeira está vazia.", rodar_painel({"conversas": LISTA})["lixeiraTexto"])
        medido = rodar_painel({"conversas": LISTA, "lixeiraErro": True})
        self.assertIn("Lixeira indisponível agora.", medido["lixeiraTexto"])
        self.assertEqual([i["titulo"] for i in medido["lista"]], ["Antiga"], "a lixeira fora do ar não derruba a lista")

    def test_restaurar_chama_a_rota_com_o_nome_do_item_e_avisa(self):
        medido = rodar_painel({"conversas": [], "lixeira": [LIXEIRA_ITEM],
                               "acoes": [{"tipo": "clicar", "em": "seth-lixeira", "texto": "Restaurar"}]})
        self.assertEqual(corpo_de(chamadas_para(medido, "/api/seth/lixeira/restaurar")[0]), {"nome": LIXEIRA_NOME})
        self.assertEqual(medido["org"], "Conversa restaurada: Apagada antes.")

    def test_restaurar_recusado_mostra_o_motivo(self):
        medido = rodar_painel({"conversas": [], "lixeira": [LIXEIRA_ITEM],
                               "lixeiraRestaurar": {"status": 409, "texto": "já existe conversa com este identificador; nada foi restaurado"},
                               "acoes": [{"tipo": "clicar", "em": "seth-lixeira", "texto": "Restaurar"}]})
        self.assertEqual(medido["org"], "Não foi possível: já existe conversa com este identificador; nada foi restaurado.")

    def test_apagar_de_vez_pede_confirmacao_e_so_depois_chama_a_purga(self):
        medido = rodar_painel({"conversas": [], "lixeira": [LIXEIRA_ITEM],
                               "acoes": [{"tipo": "clicar", "em": "seth-lixeira", "texto": "Apagar de vez"}]})
        self.assertEqual(chamadas_para(medido, "/api/seth/lixeira/purgar"), [], "o primeiro clique só pede confirmação")
        medido = rodar_painel({"conversas": [], "lixeira": [LIXEIRA_ITEM],
                               "acoes": [{"tipo": "clicar", "em": "seth-lixeira", "texto": "Apagar de vez"},
                                         {"tipo": "clicar", "em": "seth-lixeira", "texto": "Confirmar apagar de vez"}]})
        self.assertEqual(corpo_de(chamadas_para(medido, "/api/seth/lixeira/purgar")[0]), {"nome": LIXEIRA_NOME})
        self.assertEqual(medido["org"], "Conversa apagada de vez. Não tem como desfazer.")

    def test_importar_conversa_que_esta_na_lixeira_avisa_sem_duplicar(self):
        medido = rodar_painel({"conversas": [], "acoes": [{"tipo": "arquivo", "id": "seth-importar-arquivo", "texto": JSON_IMPORTAVEL}],
                               "importar": {"corpo": {"estado": "ja_existe", "id": "0000000000b1", "titulo": "Vinda", "lixeira": True}}})
        self.assertEqual(medido["org"], "Esta conversa já estava na Lixeira (Vinda); nada foi duplicado. Restaure-a por lá.")


class LimitesDaUi(unittest.TestCase):
    def test_constantes_da_ui_sao_as_do_servidor(self):
        constantes = dict(re.findall(r"^const (SETH_[A-Z_]+) = ([\d_]+);", JS, flags=re.M))
        self.assertEqual(int(constantes["SETH_MAX_MENSAGENS"]), chat_stream.MAX_MENSAGENS)
        self.assertEqual(int(constantes["SETH_MAX_CARACTERES"]), chat_stream.MAX_CARACTERES_MENSAGEM)
        self.assertEqual(int(constantes["SETH_LIMITE_PEDIDO_BYTES"]), panel_limite_pedido())
        self.assertEqual(int(constantes["SETH_LIMITE_CONVERSA_BYTES"]), armazem.CONVERSA_LIMITE_BYTES)
        self.assertEqual(int(constantes["SETH_BUSCA_MAX_CARACTERES"]), armazem.BUSCA_TERMO_LIMITE)
        self.assertEqual(int(constantes["SETH_LIMITE_IMPORTACAO_BYTES"]), armazem.IMPORTACAO_LIMITE_BYTES)


if __name__ == "__main__":
    unittest.main()
