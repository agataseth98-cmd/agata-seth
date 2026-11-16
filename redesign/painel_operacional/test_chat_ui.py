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
  focus() { this.focado = true; } blur() {} remove() { this.removido = true; } select() {} click() {}
  closest() { return null; }
  querySelector(sel) { return buscar(this, sel)[0] || null; }
  querySelectorAll(sel) { return buscar(this, sel); }
}
function descendentes(no, saida = []) { for (const c of (no.children || [])) { if (c.removido) continue; if (c instanceof Elemento) saida.push(c); descendentes(c, saida); } return saida; }
function buscar(raiz, sel) {
  const m = /^\[data-([a-z-]+)="([^"]*)"\]$/.exec(sel);
  if (!m) return [];
  const chave = m[1].replace(/-([a-z])/g, (_, l) => l.toUpperCase());
  return descendentes(raiz).filter((e) => e.dataset[chave] === m[2]);
}
function arvore(no) {
  if (no instanceof Texto) return {t: '#texto', x: no.textContent};
  const o = {t: no.tag};
  if (no.className) o.c = no.className;
  if (no.title) o.title = no.title;
  if (no.attrs && Object.keys(no.attrs).length) o.a = Object.assign({}, no.attrs);
  const filhos = (no.children || []).filter((c) => !c.removido).map(arvore);
  if (filhos.length) o.f = filhos; else if (no.textContent) o.x = String(no.textContent);
  return o;
}
function texto(no) {
  if (!no) return '';
  if (no instanceof Texto) return no.textContent;
  if (typeof no === 'string') return no;
  return (no.textContent || '') + (no.children || []).filter((c) => !c.removido).map(texto).join('');
}
const registro = new Map();
const ouvintesDoc = {};
// Elementos que começam escondidos no HTML (o atributo hidden): o mock precisa do mesmo estado inicial.
const OCULTOS_NO_INICIO = ['atalhos-painel', 'seth-mais-menu'];
const documento = {
  visibilityState: 'visible',
  getElementById(id) {
    if (!registro.has(id)) { const e = new Elemento('id:' + id); if (OCULTOS_NO_INICIO.includes(id)) e.hidden = true; registro.set(id, e); }
    return registro.get(id);
  },
  querySelector() { return new Elemento('q'); }, querySelectorAll() { return []; },
  createElement(tag) { return new Elemento(tag); }, createElementNS(ns, tag) { return new Elemento(tag); },
  createTextNode(t) { return new Texto(t); },
  addEventListener(tipo, fn) { (ouvintesDoc[tipo] = ouvintesDoc[tipo] || []).push(fn); },
  documentElement: new Elemento('html'),
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
// Stream que espera: entrega o primeiro bloco e só responde de novo quando o fetch é abortado (botão Parar).
function respostaStreamLenta(sse, cab, sinal) {
  const bytes = new TextEncoder().encode(sse); let n = 0;
  return {ok: true, status: 200, headers: cabecalhosDe(cab), json: async () => ({}), text: async () => '', body: {getReader() { return {
    read: () => new Promise((resolve, reject) => {
      if (n === 0) { n++; resolve({done: false, value: bytes}); return; }
      const rejeitar = () => reject(Object.assign(new Error('The operation was aborted.'), {name: 'AbortError'}));
      if (sinal && sinal.aborted) return rejeitar();
      if (sinal) sinal.ouvintes.push(rejeitar);
    }),
    cancel: async () => {}}; }}};
}
function respostaStream(sse, cab) {
  const bytes = new TextEncoder().encode(sse); let lido = false;
  return {ok: true, status: 200, headers: cabecalhosDe(cab), json: async () => ({}), text: async () => '', body: {getReader() { return {
    read: async () => { if (lido) return {done: true, value: undefined}; lido = true; return {done: false, value: bytes}; },
    cancel: async () => {}}; }}};
}
const ctx = {};
const armazenamento = Object.assign({}, (cen.storage && cen.storage.inicial) || {});
const gravacoes = []; const copiados = [];
ctx.window = ctx; ctx.document = documento; ctx.location = {hash: ''}; ctx.history = {pushState() {}};
ctx.localStorage = {
  getItem(k) { if (cen.storage && cen.storage.lerErro) throw new Error('bloqueado'); return Object.prototype.hasOwnProperty.call(armazenamento, k) ? armazenamento[k] : null; },
  setItem(k, v) { if (cen.storage && cen.storage.gravarErro) throw new Error('cheio'); armazenamento[k] = String(v); gravacoes.push([k, String(v)]); }};
ctx.navigator = {clipboard: {writeText: async (t) => { copiados.push(t); }}}; ctx.Node = function () {};
if (cen.claroSistema !== undefined) ctx.matchMedia = () => ({matches: Boolean(cen.claroSistema), addEventListener() {}});
ctx.TextEncoder = TextEncoder; ctx.TextDecoder = TextDecoder;
const sessao = Object.assign({}, (cen.sessionStorage && cen.sessionStorage.inicial) || {}); const sessaoGravacoes = [];
ctx.sessionStorage = {
  getItem(k) { if (cen.sessionStorage && cen.sessionStorage.lerErro) throw new Error('bloqueado'); return Object.prototype.hasOwnProperty.call(sessao, k) ? sessao[k] : null; },
  setItem(k, v) { if (cen.sessionStorage && cen.sessionStorage.gravarErro) throw new Error('cheio'); sessao[k] = String(v); sessaoGravacoes.push([k, String(v)]); }};
// FileReader de teste: lê o texto do arquivo simulado (o painel usa readAsText, como no navegador).
// leituras: um item por FileReader criado (null se não foi lido); X1 confere que o arquivo acima do teto nem é lido.
const leituras = [];
class LeitorFalso { constructor() { leituras.push(null); } readAsText(arquivo) { leituras[leituras.length - 1] = String(arquivo.name); arquivo.text().then((t) => { this.result = t; if (this.onload) this.onload({target: this}); }, (e) => { this.error = e; if (this.onerror) this.onerror({target: this}); }); } }
ctx.FileReader = LeitorFalso;
const marcas = {};
ctx.__arvore = arvore;
// AbortController de verdade para o teste: abort() marca o sinal e acorda quem estiver esperando.
class ControleFalso { constructor() { this.signal = {aborted: false, ouvintes: [], addEventListener() {}};} abort() { if (this.signal.aborted) return; this.signal.aborted = true; this.signal.ouvintes.forEach((f) => f()); } }
ctx.AbortController = ControleFalso;
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
  if (url.startsWith('/api/seth/conversa?id=')) return respostaJson(200, (cen.porId && cen.porId[decodeURIComponent(url.split('=')[1])]) || cen.conversa);
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
    const sse = r.sse !== undefined ? r.sse : 'data: {"tipo": "texto", "delta": "resposta"}\n\ndata: {"tipo": "fim"}\n\n';
    if (r.lento) return respostaStreamLenta(sse, r.cabecalhos || {}, opcoes.signal);
    return respostaStream(sse, r.cabecalhos || {});
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
// Primeira linha da lista de conversas (lote painel-conversa-16-11): a lista agora abre com o cabeçalho do grupo (Hoje, Mais antigas...).
function primeiroItem() { return descendentes(documento.getElementById('seth-conversas')).find((e) => typeof e.className === 'string' && e.className.split(' ').includes('seth-item')); }
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
  } else if (a.tipo === 'valor') {
    const el = acharTodos(em(a.em), (e) => e.tag === a.tag)[a.indice || 0]; el.value = a.valor;
  } else if (a.tipo === 'evento') {
    const el = acharTodos(em(a.em), (e) => e.tag === a.tag)[a.indice || 0]; (el.ouvintes[a.evento] || []).forEach((f) => f({target: el}));
  } else if (a.tipo === 'tecla_doc') {
    const alvo = {tagName: a.tagName || 'BODY', isContentEditable: false};
    const ev = {key: a.tecla, ctrlKey: !!a.ctrl, metaKey: false, shiftKey: !!a.shift, target: alvo, preventDefault() { ev.prevented = true; }};
    (ouvintesDoc.keydown || []).forEach((f) => f(ev));
  } else if (a.tipo === 'arquivos' || a.tipo === 'soltar') {
    const el = documento.getElementById(a.id);
    const arquivos = a.lista.map((x) => ({name: x.nome, type: x.tipo || '', size: x.tamanho !== undefined ? x.tamanho : x.texto.length, text: async () => x.texto}));
    if (a.tipo === 'soltar') (el.ouvintes.drop || []).forEach((f) => f({target: el, preventDefault() {}, dataTransfer: {files: arquivos}}));
    else { el.files = arquivos; el.ouvintes.change[0]({target: el}); }
  } else if (a.tipo === 'colar') {
    const el = documento.getElementById(a.id);
    const ev = {target: el, clipboardData: {getData: () => a.texto}, preventDefault() { marcas.colarPrevenido = true; }};
    (el.ouvintes.paste || []).forEach((f) => f(ev));
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
  if (cen.secao) { for (const id of ['panorama', 'conversa']) documento.getElementById(id).hidden = id !== cen.secao; }
  if (cen.abrir) { primeiroItem().children[0].ouvintes.click[0](); await esperar(); }
  if (cen.renomear !== undefined) {
    const linha = primeiroItem();
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
  for (const a of cen.acoes_depois || []) await executar(a);
  const transcricao = []; coletar(documento.getElementById('seth-transcript'), transcricao);
  const salvar = documento.getElementById('seth-salvar-aviso');
  const el = (id) => documento.getElementById(id);
  const base = {chamadas, transcricao, salvarTexto: salvar.textContent, salvarOculto: salvar.hidden,
    status: el('seth-status').textContent,
    org: el('seth-org-aviso').textContent, orgOculto: el('seth-org-aviso').hidden,
    lista: itensDe('seth-conversas'), listaTexto: texto(el('seth-conversas')), grupos: descendentes(el('seth-conversas')).filter((e) => e.className === 'seth-grupo').map((e) => e.textContent),
    arquivadas: itensDe('seth-arquivadas'), arquivadasTotal: el('seth-arquivadas-total').textContent,
    listaOculta: el('seth-conversas').hidden, arquivadasOculta: el('seth-arquivadas-bloco').hidden,
    buscaOculta: el('seth-busca-resultados').hidden, busca: texto(el('seth-busca-resultados')),
    tempOculta: el('seth-temporaria-aviso').hidden, tempTexto: el('seth-temporaria-aviso').textContent,
    temporariaBotao: el('seth-temporaria').textContent, temporariaPressionado: el('seth-temporaria').getAttribute('aria-pressed'),
    temporariaTitulo: el('seth-temporaria').title,
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
    resultados};
  const extra = {
    contexto: el('seth-contexto').textContent, contextoDetalhe: el('seth-contexto-detalhe').textContent, barra: el('seth-contexto-barra').value,
    origem: texto(el('seth-origem')), origemOculta: el('seth-origem').hidden,
    paradaOculta: el('seth-parar').hidden, atalhosOculto: el('atalhos-painel').hidden,
    tema: documento.documentElement.dataset.tema, temaSelect: el('tema').value,
    gravacoes, copiados, copiadoAviso: el('seth-copiado').textContent,
    buscaFocada: Boolean(el('seth-busca').focado), pesquisaFocada: Boolean(el('search').focado),
    maisFocado: Boolean(el('seth-mais-abrir').focado),
    transcricaoCompleta: texto(el('seth-transcript')), entrada: el('seth-input').value,
    ramos: descendentes(el('seth-transcript')).filter((e) => typeof e.className === 'string' && e.className.includes('seth-ramo')).map((e) => texto(e)),
    botoes: descendentes(el('seth-transcript')).filter((e) => e.tag === 'button').map((e) => texto(e).trim()),
    pressionados: descendentes(el('seth-transcript')).filter((e) => e.tag === 'button' && e.getAttribute('aria-pressed') === 'true').map((e) => texto(e).trim()),
    campos: descendentes(el('seth-transcript')).filter((e) => e.tag === 'input' || e.tag === 'textarea').map((e) => e.value),
    anexos: texto(el('seth-anexos')), anexosOculto: el('seth-anexos').hidden,
    anexoAviso: el('seth-anexo-aviso').textContent, anexoAvisoOculto: el('seth-anexo-aviso').hidden, leituras: leituras.slice(),
    chipInstrucoesOculto: el('seth-chip-instrucoes').hidden, instrucoesContagem: el('seth-instrucoes-contagem').textContent,
    instrucoesErro: el('seth-instrucoes-erro').textContent, instrucoesErroOculto: el('seth-instrucoes-erro').hidden,
    orgMenu: el('seth-org-aviso-menu').textContent, orgMenuOculto: el('seth-org-aviso-menu').hidden,
    ilegiveisMenu: el('seth-ilegiveis-aviso-menu').textContent,
    temporariaMenu: el('seth-temporaria-menu').textContent, marcas, sessaoGravacoes, sessaoValor: sessao['agata-seth-rascunhos'] || null,
    rotulosFeedback: descendentes(el('seth-transcript')).filter((e) => e.tag === 'button' && String(e.getAttribute('aria-label') || '').startsWith('Resposta')).map((e) => ({texto: texto(e).trim(), aria: e.getAttribute('aria-label'), titulo: e.title})),
    status: el('seth-status').textContent};
  console.log(JSON.stringify({...base, ...extra}));
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


ISO_COM_FUSO = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$"


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


def menu_lateral() -> str:
    """Menu único (aside.sidebar): lista de conversas, busca e a organização ficam aqui ou no dialog (lote painel-conversa-16-11)."""
    inicio = HTML.index('<aside class="sidebar"')
    return HTML[inicio:HTML.index("</aside>", inicio) + len("</aside>")]


def organizar_dialog() -> str:
    inicio = HTML.index('<dialog id="organizar-dialog"')
    return HTML[inicio:HTML.index("</dialog>", inicio) + len("</dialog>")]


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
        # C8/C9 (16/11/2026): o corpo leva também 'instrucoes' e 'anexos' (server.py, _seth_chat_stream).
        padrao = r'"/api/seth/chat/stream".*?body:\s*JSON\.stringify\(\{mensagens,\s*modelo,\s*instrucoes,\s*anexos\}\)'
        self.assertIsNotNone(re.search(padrao, bloco_conversa_js(), flags=re.DOTALL),
                             "o stream deve enviar os campos 'mensagens', 'modelo', 'instrucoes' e 'anexos' (server.py, _seth_chat_stream)")

    def test_fallback_tambem_envia_o_modelo(self):
        self.assertIn("JSON.stringify({messages: mensagens, modelo, instrucoes, anexos})", bloco_conversa_js())

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
        antigas = [{"role": "user" if i % 2 == 0 else "assistant", "content": "\x01" * 4000} for i in range(19)]  # C10: 6 bytes por caractere no JSON passam de 262144
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
        gravada = corpo_de(salvos[-1])["mensagens"][-1]
        self.assertRegex(gravada.pop("hora"), ISO_COM_FUSO, "C5 (16/11/2026): a resposta grava a hora (ISO 8601 com fuso)")
        self.assertEqual(gravada, {"role": "assistant", "content": "resposta", "modelo": "seth-livre", "modelo_real": "openai/gpt-oss-120b"})

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

    # Lote painel-conversa-16-11: a lista, a busca e as pastas saíram da seção Conversa. Cada id tem a região certa.
    REGIOES = {
        "menu": ["seth-busca", "seth-busca-resultados", "seth-arquivadas-bloco", "seth-arquivadas", "seth-arquivadas-total",
                 "seth-lixeira-bloco", "seth-lixeira-total", "seth-lixeira", "seth-conversas"],
        "dialog": ["seth-filtro-pasta", "seth-filtro-marcador", "seth-org-aviso", "seth-ilegiveis-aviso", "seth-pastas-bloco",
                   "seth-pasta-form", "seth-pasta-nome", "seth-pasta-criar", "seth-pastas", "seth-importar-arquivo"],
        "conversa": ["seth-temporaria", "seth-temporaria-aviso", "seth-exportar-texto", "seth-export-json", "seth-export-md"],
    }

    def test_ids_da_organizacao_existem_na_regiao_certa(self):
        regiao = {"menu": menu_lateral(), "dialog": organizar_dialog(), "conversa": secao_conversa()}
        for nome, ids in self.REGIOES.items():
            for ident in ids:
                with self.subTest(ident=ident, regiao=nome):
                    self.assertIn(f'id="{ident}"', regiao[nome])
        for ident in self.IDS:
            with self.subTest(ident=ident, presente_uma_vez=True):
                self.assertEqual(HTML.count(f'id="{ident}"'), 1)

    def test_lista_de_conversas_esta_dentro_do_aside_sidebar_e_nao_na_conversa(self):
        self.assertIn('id="seth-conversas"', menu_lateral())
        self.assertNotIn('id="seth-conversas"', secao_conversa(), "lista duplicada na seção Conversa")
        self.assertNotIn("seth-lista", secao_conversa())

    def test_campo_de_busca_e_nome_de_pasta_com_limite(self):
        self.assertRegex(menu_lateral(), r'<input id="seth-busca" type="search" maxlength="120"')
        self.assertRegex(organizar_dialog(), r'<input id="seth-pasta-nome" type="text" maxlength="60"')

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
        # Lote painel-conversa-16-11: os grupos vêm da data real (atualizada), não mais de "Recentes".
        self.assertEqual(medido["grupos"][0], "Fixadas")
        self.assertIn(medido["grupos"][1], ["Hoje", "Ontem", "Últimos 7 dias", "Mais antigas"])
        self.assertIn("Fixada", medido["lista"][0]["texto"])
        self.assertTrue(medido["lista"][0]["fixada"])

    def test_grupos_pela_data_real_depois_das_fixadas(self):
        # Lote painel-conversa-16-11 (E2): Fixadas, Hoje, Ontem, Últimos 7 dias, Mais antigas; datas relativas ao dia do teste.
        from datetime import datetime, timedelta
        agora = datetime.now().astimezone()
        def dia(n):
            return (agora - timedelta(days=n)).isoformat(timespec="seconds")
        itens = [conversa_item("0000000000a5", "Antiga", atualizada=dia(40)),
                 conversa_item("0000000000a4", "Semana", atualizada=dia(3)),
                 conversa_item("0000000000a3", "Ontem", atualizada=dia(1)),
                 conversa_item("0000000000a2", "Fixada", fixada=True, atualizada=dia(400)),
                 conversa_item("0000000000a1", "Hoje", atualizada=dia(0))]
        medido = rodar_painel({"conversas": itens})
        self.assertEqual(medido["grupos"], ["Fixadas", "Hoje", "Ontem", "Últimos 7 dias", "Mais antigas"])
        self.assertEqual([i["titulo"] for i in medido["lista"]], ["Fixada", "Hoje", "Ontem", "Semana", "Antiga"])

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
        self.assertEqual(medido["temporariaBotao"], "Temporária", "J5: o botão é um interruptor curto")
        self.assertEqual(medido["temporariaPressionado"], "true")
        self.assertTrue(medido["temporariaTitulo"].startswith("Conversa temporária: ligada"), "o texto longo vai para o title")
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
        codigo = ("(async () => { const outra = {id: null, titulo: 'Outra', nos: [{id: 'c0', pai: null, role: 'user', content: 'x'}], folha: 'c0', "
                  "modelo: 'seth-livre', temporaria: false}; const ok = await __teste.sethSalvar(outra); "
                  "return {ok, outraId: outra.id, atualId: __teste.sethAtual().id}; })()")
        medido = rodar_painel({"acoes": [{"tipo": "js", "codigo": codigo}]})
        self.assertEqual(medido["resultados"][0], {"ok": True, "outraId": "0123456789ab", "atualId": None})

    def test_falha_ao_salvar_conversa_que_nao_esta_na_tela_avisa_pelo_titulo(self):
        codigo = ("(async () => { const outra = {id: null, titulo: 'Outra', nos: [{id: 'c0', pai: null, role: 'user', content: 'x'}], folha: 'c0', "
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
BASE_RAMO = [{"role": "user", "content": "pergunta"}, {"role": "assistant", "content": "resposta antiga"}]
EDITAR = [{"tipo": "clicar", "em": "seth-transcript", "texto": "Editar"},
          {"tipo": "valor", "em": "seth-transcript", "tag": "textarea", "valor": "pergunta nova"},
          {"tipo": "clicar", "em": "seth-transcript", "texto": "Enviar"}]
SETH_CONTINUAR_TXT = "Continue de onde parou, sem repetir o que já foi dito."
SETH_INTERROMPIDA_TXT = "Resposta interrompida. O texto recebido ficou salvo."
SETH_INTERROMPIDA_VAZIA_TXT = "Resposta interrompida antes do primeiro texto. Nada foi recebido."
STREAM_LENTO = {"lento": True, "sse": 'data: {"tipo": "texto", "delta": "parte do texto"}\n\n'}


class ConversaLote4Html(unittest.TestCase):
    IDS = ["tema", "atalhos-abrir", "atalhos-painel", "atalhos-fechar", "seth-parar", "seth-contexto",
           "seth-contexto-barra", "seth-origem", "seth-copiado", "seth-copiar-ultima"]

    def test_painel_sem_emoji_nos_arquivos_da_tela(self):
        # Decisão E-2 (16/10): o Agata não usa emoji. Vale para o HTML, o CSS e o JS da tela. Conta os blocos de emoji
        # e os símbolos que viram emoji; a marca de checagem (U+2713, já usada em nova_versao) não é emoji e fica de fora.
        padrao = re.compile("[\U0001F000-\U0001FAFF\u2600-\u26FF\u2705\u270A\u270B\u2728\u274C\u274E\u2753-\u2755"
                            "\u2757\u2795-\u2797\u27B0\u27BF\u2B50\u2B55]")
        css = (HERE / "prototipo.css").read_text(encoding="utf-8")
        for nome, conteudo in (("prototipo.html", HTML), ("prototipo.js", JS), ("prototipo.css", css)):
            with self.subTest(arquivo=nome):
                self.assertEqual(padrao.findall(conteudo), [])

    def test_controles_do_lote4_existem_com_id(self):
        for ident in self.IDS:
            with self.subTest(ident=ident):
                self.assertIn(f'id="{ident}"', HTML)

    def test_parar_comeca_escondido_e_atalhos_comecam_fechados(self):
        self.assertRegex(HTML, r'<button class="text-link" type="button" id="seth-parar" hidden>')
        self.assertRegex(HTML, r'<section id="atalhos-painel" class="atalhos" role="dialog"[^>]*hidden>')

    def test_seletor_de_tema_tem_as_tres_escolhas(self):
        tema = re.search(r'<select id="tema">(.*?)</select>', HTML)
        self.assertIsNotNone(tema)
        self.assertEqual(re.findall(r'<option value="(\w+)"', tema.group(1)), ["escuro", "claro", "sistema"])
        self.assertNotIn("style=", tema.group(0))


class ConversaRamos(unittest.TestCase):
    """Editar, trocar de versão, regenerar e ramificar (node + DOM mínimo, sem rede)."""

    def test_editar_cria_ramo_e_guarda_a_resposta_antiga(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(BASE_RAMO), "abrir": True, "acoes": EDITAR})
        corpo = corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])
        self.assertNotIn("mensagens", corpo, "com ramo, a árvore é que vai ao servidor")
        self.assertEqual([n["content"] for n in corpo["arvore"]["nos"]], ["pergunta", "resposta antiga", "pergunta nova", "resposta"])
        self.assertIn("pergunta nova", medido["transcricaoCompleta"])
        self.assertNotIn("resposta antiga", medido["transcricaoCompleta"], "a resposta antiga sai do caminho, mas não some")
        self.assertEqual(medido["ramos"], ["<2/2>"])

    def test_setas_trocam_de_versao_e_seguem_o_ramo_escolhido(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(BASE_RAMO), "abrir": True,
                               "acoes": EDITAR + [{"tipo": "clicar", "em": "seth-transcript", "texto": "<"}]})
        self.assertIn("pergunta", medido["transcricaoCompleta"])
        self.assertIn("resposta antiga", medido["transcricaoCompleta"])
        self.assertNotIn("pergunta nova", medido["transcricaoCompleta"])
        self.assertEqual(medido["ramos"], ["<1/2>"])
        self.assertEqual(corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])["arvore"]["folha"], "c1")

    def test_regenerar_guarda_a_resposta_antiga_como_versao(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(BASE_RAMO), "abrir": True,
                               "acoes": [{"tipo": "clicar", "em": "seth-transcript", "texto": "Regenerar"}]})
        self.assertIn("resposta", medido["transcricaoCompleta"])
        self.assertNotIn("resposta antiga", medido["transcricaoCompleta"])
        self.assertEqual(medido["ramos"], ["<2/2>"])
        nos = corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])["arvore"]["nos"]
        self.assertIn("resposta antiga", [n["content"] for n in nos])

    def test_ramificar_aqui_cria_conversa_com_o_caminho_ate_a_mensagem(self):
        conv = conversa([{"role": "user", "content": "um"}, {"role": "assistant", "content": "dois"},
                         {"role": "user", "content": "tres"}])
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True,
                               "acoes": [{"tipo": "clicar", "em": "seth-transcript", "texto": "Ramificar aqui", "indice": 1}]})
        pedidos = chamadas_para(medido, "/api/seth/conversa")
        self.assertEqual(len(pedidos), 1, "ramificar grava uma conversa nova")
        corpo = corpo_de(pedidos[0])
        self.assertEqual(corpo["ramificada_de"], {"id": CONVERSA_ID, "mensagem": 1})
        self.assertEqual(corpo["mensagens"], [{"role": "user", "content": "um"}, {"role": "assistant", "content": "dois"}])
        self.assertNotIn("id", corpo, "a conversa nova ganha id no servidor")

    def test_conversa_ramificada_mostra_de_onde_saiu_e_abre_a_original(self):
        conv = {**conversa(BASE_RAMO), "ramificada_de": {"id": CONVERSA_ID, "mensagem": 0}}
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True})
        self.assertFalse(medido["origemOculta"])
        self.assertTrue(medido["origem"].startswith("Conversa ramificada da conversa «Antiga», a partir da mensagem 1."),
                        medido["origem"])
        self.assertIn("Abrir a original", medido["origem"])

    def test_ramificar_em_conversa_temporaria_nao_aparece(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "clicar", "id": "seth-temporaria"}],
                               "enviar": ["oi"]})
        self.assertNotIn("Ramificar aqui", medido["botoes"])
        self.assertEqual(chamadas_para(medido, "/api/seth/conversa"), [])


    def test_renomear_conversa_com_ramo_grava_a_arvore_inteira(self):
        arvore = {"nos": [{"id": "c0", "pai": None, "role": "user", "content": "pergunta"},
                          {"id": "c1", "pai": "c0", "role": "assistant", "content": "resposta antiga"},
                          {"id": "k1", "pai": None, "role": "user", "content": "pergunta nova"},
                          {"id": "k2", "pai": "k1", "role": "assistant", "content": "resposta nova"}], "folha": "k2"}
        conv = {"schema_version": 1, "id": CONVERSA_ID, "titulo": "Antiga",
                "mensagens": [{"role": "user", "content": "pergunta nova"}, {"role": "assistant", "content": "resposta nova"}],
                "arvore": arvore}
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "renomear": "Novo nome"})
        pedidos = chamadas_para(medido, "/api/seth/conversa")
        self.assertEqual(len(pedidos), 1)
        corpo = corpo_de(pedidos[0])
        self.assertEqual(corpo["titulo"], "Novo nome")
        self.assertEqual(len(corpo["arvore"]["nos"]), 4, "renomear não pode perder as versões de outros ramos")
        self.assertNotIn("mensagens", corpo)


class ConversaParar(unittest.TestCase):
    """Parar corta o fetch (AbortController) e mantém o texto recebido marcado como interrompida."""

    def test_parar_mantem_o_texto_recebido_marcado_interrompida(self):
        medido = rodar_painel({"conversas": LISTA, "stream": STREAM_LENTO, "enviar": ["pergunta"],
                               "acoes_depois": [{"tipo": "clicar", "id": "seth-parar"}]})
        self.assertEqual(medido["status"], "INTERROMPIDA")
        self.assertIn("parte do texto", medido["transcricaoCompleta"])
        self.assertIn(SETH_INTERROMPIDA_TXT, medido["transcricaoCompleta"])
        self.assertTrue(medido["paradaOculta"], "sem resposta em curso, o botão Parar some")
        ultima = corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])["mensagens"][-1]
        self.assertEqual((ultima["content"], ultima["interrompida"]), ("parte do texto", True))

    def test_parar_antes_do_primeiro_texto_deixa_resposta_vazia_marcada(self):
        medido = rodar_painel({"conversas": LISTA, "stream": {"lento": True, "sse": ""}, "enviar": ["pergunta"],
                               "acoes_depois": [{"tipo": "clicar", "id": "seth-parar"}]})
        self.assertIn(SETH_INTERROMPIDA_VAZIA_TXT, medido["transcricaoCompleta"])
        ultima = corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])["mensagens"][-1]
        self.assertEqual((ultima["content"], ultima["interrompida"]), ("", True))
        self.assertEqual(len(chamadas_para(medido, "/api/seth/chat")), 0, "parar não repete a pergunta pelo fallback")

    def test_esc_para_a_resposta_em_curso(self):
        medido = rodar_painel({"conversas": LISTA, "stream": STREAM_LENTO, "enviar": ["pergunta"],
                               "acoes_depois": [{"tipo": "tecla_doc", "tecla": "Escape"}]})
        self.assertEqual(medido["status"], "INTERROMPIDA")
        self.assertIn("parte do texto", medido["transcricaoCompleta"])

    def test_erro_no_meio_do_stream_mantem_o_texto_marcado(self):
        sse = 'data: {"tipo": "texto", "delta": "meio"}\n\ndata: {"tipo": "erro", "motivo": "stream interrompido"}\n\n'
        medido = rodar_painel({"conversas": LISTA, "stream": {"sse": sse}, "enviar": ["pergunta"]})
        self.assertIn("meio", medido["transcricaoCompleta"])
        self.assertIn("Não consegui terminar a resposta: stream interrompido.", medido["transcricaoCompleta"])
        self.assertTrue(corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])["mensagens"][-1]["interrompida"])

    def test_erro_sem_texto_mantem_a_pergunta_e_oferece_tentar_de_novo(self):
        # C7 (16/11/2026): a pergunta fica na conversa (não volta ao campo); o erro traz o botão "Tentar de novo".
        medido = rodar_painel({"stream": {"status": 400, "texto": "mensagem 1 acima de 4000 caracteres"}, "enviar": ["oi"]})
        self.assertEqual(medido["entrada"], "", "a pergunta não volta ao campo: ela já está na conversa")
        self.assertIn("Você", medido["transcricaoCompleta"], "a pergunta fica na conversa")
        self.assertIn("Tentar de novo", medido["botoes"])
        self.assertIn("Não consegui responder agora: o painel recusou o pedido (mensagem 1 acima de 4000 caracteres).",
                      medido["transcricaoCompleta"])


class ConversaContinuar(unittest.TestCase):
    def test_continuar_pede_a_seth_e_anexa_na_mesma_resposta(self):
        conv = conversa([{"role": "user", "content": "pergunta"}, {"role": "assistant", "content": "parte um"}])
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True,
                               "stream": {"sse": 'data: {"tipo": "texto", "delta": "parte dois"}\n\ndata: {"tipo": "fim"}\n\n'},
                               "acoes": [{"tipo": "clicar", "em": "seth-transcript", "texto": "Continuar"}]})
        pedido = corpo_de(chamadas_para(medido, "/api/seth/chat/stream")[0])
        self.assertEqual(pedido["mensagens"][-1], {"role": "user", "content": SETH_CONTINUAR_TXT})
        self.assertEqual(pedido["mensagens"][-2], {"role": "assistant", "content": "parte um"})
        ultima = corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])["mensagens"][-1]
        self.assertEqual(ultima["content"], "parte umparte dois")
        self.assertEqual(ultima["cortes"], [8], "a continuação começa depois de 'parte um' (8 caracteres)")
        self.assertIn("Continuação", medido["transcricaoCompleta"])
        self.assertEqual(len([m for m in medido["transcricao"] if m.startswith("modelo:")]), 1, "não vira outra resposta")

    def test_continuar_so_aparece_com_texto_na_resposta(self):
        conv = conversa([{"role": "user", "content": "x"}, {"role": "assistant", "content": ""}])
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True})
        self.assertNotIn("Continuar", medido["botoes"])

    def test_continuacao_interrompida_mantem_o_que_chegou(self):
        conv = conversa([{"role": "user", "content": "pergunta"}, {"role": "assistant", "content": "parte um"}])
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True,
                               "stream": {"lento": True, "sse": 'data: {"tipo": "texto", "delta": " e mais"}\n\n'},
                               "acoes": [{"tipo": "clicar", "em": "seth-transcript", "texto": "Continuar"}],
                               "acoes_depois": [{"tipo": "clicar", "id": "seth-parar"}]})
        ultima = corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])["mensagens"][-1]
        self.assertEqual((ultima["content"], ultima.get("interrompida")), ("parte um e mais", True))


class ConversaFeedback(unittest.TestCase):
    CONV = [{"role": "user", "content": "oi"}, {"role": "assistant", "content": "ola"}]

    def test_feedback_util_e_nao_util_com_motivo_vai_salvo_na_conversa(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(self.CONV), "abrir": True, "acoes": [
            {"tipo": "clicar", "em": "seth-transcript", "texto": "Útil"},
            {"tipo": "valor", "em": "seth-transcript", "tag": "input", "valor": "resposta clara"},
            {"tipo": "evento", "em": "seth-transcript", "tag": "input", "evento": "change"},
            {"tipo": "clicar", "em": "seth-transcript", "texto": "Não útil"}]})
        feedback = corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])["mensagens"][-1]["feedback"]
        self.assertEqual(feedback, {"nota": "ruim", "motivo": "resposta clara"}, "trocar de nota mantém o motivo")
        self.assertEqual(medido["pressionados"], ["Não útil"])

    def test_botoes_de_feedback_tem_rotulo_e_titulo_sem_emoji(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(self.CONV), "abrir": True})
        self.assertEqual(medido["rotulosFeedback"], [
            {"texto": "Útil", "aria": "Resposta útil", "titulo": "Resposta útil"},
            {"texto": "Não útil", "aria": "Resposta não útil", "titulo": "Resposta não útil"}])

    def test_clicar_de_novo_tira_o_feedback(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(self.CONV), "abrir": True, "acoes": [
            {"tipo": "clicar", "em": "seth-transcript", "texto": "Útil"},
            {"tipo": "clicar", "em": "seth-transcript", "texto": "Útil"}]})
        self.assertNotIn("feedback", corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])["mensagens"][-1])
        self.assertEqual(medido["pressionados"], [])

    def test_feedback_em_conversa_temporaria_nao_grava(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "clicar", "id": "seth-temporaria"}], "enviar": ["oi"],
                               "acoes_depois": [{"tipo": "clicar", "em": "seth-transcript", "texto": "Útil"}]})
        self.assertEqual(chamadas_para(medido, "/api/seth/conversa"), [], "temporária não grava nem o feedback")
        self.assertEqual(medido["pressionados"], ["Útil"], "o botão fica marcado na tela")


class ConversaContextoAtalhosTema(unittest.TestCase):
    def test_barra_de_contexto_mostra_caracteres_e_mensagens_em_portugues(self):
        conv = conversa([{"role": "user", "content": "x" * 100}, {"role": "assistant", "content": "ok"}])
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True})
        # J3 (16/11/2026): a linha curta é "Contexto: 1,2% · 4 de 4 mensagens"; o texto longo fica no details.
        self.assertRegex(medido["contexto"], r"^Contexto: \d+,\d% · 2 de 2 mensagens$")
        self.assertTrue(medido["contextoDetalhe"].startswith("Contexto da próxima pergunta: 102 caracteres,"), medido["contextoDetalhe"])
        self.assertIn("de 256 KB", medido["contextoDetalhe"])
        self.assertIn("Medida: estimativa em caracteres.", medido["contextoDetalhe"])  # C11: sem uso do gateway
        self.assertIn("Vão 2 de 2 mensagens.", medido["contextoDetalhe"])
        self.assertIsInstance(medido["barra"], (int, float))
        self.assertLessEqual(medido["barra"], 100)
        self.assertRegex(medido["contextoDetalhe"], r"\(\d+,\d%\)", "a porcentagem tem uma casa decimal, com vírgula")

    def test_conversa_vazia_diz_que_so_vai_a_pergunta(self):
        medido = rodar_painel({"conversas": LISTA})
        self.assertEqual(medido["contexto"], "Contexto: vazio")
        self.assertTrue(medido["contextoDetalhe"].startswith("A conversa está vazia"), medido["contextoDetalhe"])

    def test_interrogacao_abre_a_lista_de_atalhos_e_esc_fecha(self):
        abre = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "tecla_doc", "tecla": "?"}]})
        self.assertFalse(abre["atalhosOculto"])
        fecha = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "tecla_doc", "tecla": "?"},
                                                             {"tipo": "tecla_doc", "tecla": "Escape"}]})
        self.assertTrue(fecha["atalhosOculto"])

    def test_interrogacao_dentro_de_campo_de_texto_nao_abre_a_lista(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "tecla_doc", "tecla": "?", "tagName": "TEXTAREA"}]})
        self.assertTrue(medido["atalhosOculto"])

    def test_ctrl_shift_o_comeca_conversa_nova(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(BASE_RAMO), "abrir": True,
                               "acoes": [{"tipo": "tecla_doc", "tecla": "O", "ctrl": True, "shift": True}]})
        self.assertEqual(medido["tituloConversa"], "Nova conversa")
        self.assertNotIn("pergunta", medido["transcricaoCompleta"])
        self.assertEqual(medido["status"], "PRONTA")

    def test_ctrl_shift_c_copia_a_ultima_resposta(self):
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(BASE_RAMO), "abrir": True,
                               "acoes": [{"tipo": "tecla_doc", "tecla": "C", "ctrl": True, "shift": True}]})
        self.assertEqual(medido["copiados"], ["resposta antiga"])
        self.assertEqual(medido["copiadoAviso"], "Última resposta copiada.")

    def test_barra_foca_a_busca_da_conversa(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "tecla_doc", "tecla": "/"}]})
        self.assertTrue(medido["buscaFocada"])
        self.assertFalse(medido["pesquisaFocada"])

    def test_tema_salvo_vale_ao_abrir_e_muda_pelo_seletor(self):
        salvo = rodar_painel({"conversas": LISTA, "storage": {"inicial": {"agata-tema": "claro"}}})
        self.assertEqual((salvo["tema"], salvo["temaSelect"]), ("claro", "claro"))
        trocado = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "mudar", "id": "tema", "valor": "sistema"}]})
        self.assertIn(["agata-tema", "sistema"], trocado["gravacoes"])
        self.assertEqual(trocado["tema"], "escuro", "sem preferência clara do navegador, o sistema vale escuro")

    def test_tema_sistema_claro_segue_o_navegador(self):
        medido = rodar_painel({"conversas": LISTA, "claroSistema": True,
                               "acoes": [{"tipo": "mudar", "id": "tema", "valor": "sistema"}]})
        self.assertEqual(medido["tema"], "claro")

    def test_tema_padrao_e_escuro_sem_nada_salvo(self):
        self.assertEqual(rodar_painel({"conversas": LISTA})["tema"], "escuro")

    def test_localstorage_com_erro_nao_derruba_a_tela(self):
        medido = rodar_painel({"conversas": LISTA, "storage": {"lerErro": True, "gravarErro": True},
                               "acoes": [{"tipo": "mudar", "id": "tema", "valor": "claro"}]})
        self.assertEqual(medido["tema"], "claro", "a escolha vale nesta aba mesmo sem guardar")
        self.assertEqual(medido["gravacoes"], [])
        self.assertIn("status", medido)


MARKDOWN_RICO = """# Um
## Dois
### Tres

1. primeiro
2. segundo
   - sub um
   - sub dois

> citado

| a | b |
| --- | --- |
| 1 | 2 |

---

*it* ~~tach~~ **neg** `cod`"""
CONTEUDO_LINK = "Veja [a doc](https://exemplo.org/doc), ou https://exemplo.org/x. E [mal](javascript:alert(1))."
CODIGO_PY = "```py\nprint('oi')\n```"
CLIQUE_ARVORE = {"tipo": "js", "codigo": "__arvore(document.getElementById('seth-transcript'))"}


def achar_nos(raiz, tag=None, classe=None):
    """Nós da árvore de __arvore (dicts com 't', 'c', 'a', 'f') com a tag e/ou a classe pedidas, em ordem de documento."""
    saida = []

    def andar(no):
        if (tag is None or no.get("t") == tag) and (classe is None or classe in no.get("c", "").split()):
            saida.append(no)
        for filho in no.get("f", []):
            andar(filho)

    andar(raiz)
    return saida


def texto_no(no):
    if no.get("t") == "#texto":
        return no.get("x", "")
    return no.get("x", "") + "".join(texto_no(f) for f in no.get("f", []))


def conversa_com_id(id_, mensagens):
    return {"schema_version": 1, "id": id_, "titulo": "Outra", "mensagens": mensagens}


class ConversaFuncoesChat(unittest.TestCase):
    """C1 a C5 (16/11/2026) e C9/C11 com o DOM falso: a árvore da transcrição e o que sai no pedido."""

    def arvore_da_transcricao(self, cenario):
        medido = rodar_painel(dict(cenario, depois=[*cenario.get("depois", []), CLIQUE_ARVORE]))
        return medido, medido["resultados"][-1]

    def test_titulos_em_tres_niveis_listas_aninhadas_citacao_tabela_e_enfase(self):
        conv = conversa([{"role": "user", "content": "pergunta"}, {"role": "assistant", "content": MARKDOWN_RICO}])
        _, arv = self.arvore_da_transcricao({"conversas": LISTA, "conversa": conv, "abrir": True})
        arv = achar_nos(arv, "div", "msg-body")[1]  # corpo da resposta da Seth (o primeiro é o da pergunta)
        titulos = [(n["t"], texto_no(n)) for n in achar_nos(arv) if n["t"] in ("h3", "h4", "h5")]
        self.assertEqual(titulos, [("h3", "Um"), ("h4", "Dois"), ("h5", "Tres")])
        ordenada = achar_nos(arv, "ol")
        self.assertEqual(len(ordenada), 1, "a lista numerada vira ol")
        itens = [li for li in ordenada[0]["f"] if li["t"] == "li"]
        self.assertEqual(texto_no(itens[0]), "primeiro")
        aninhada = achar_nos(itens[1], "ul")
        self.assertEqual([texto_no(li) for li in aninhada[0]["f"]], ["sub um", "sub dois"], "recuo de dois espaços vira lista aninhada")
        self.assertEqual([texto_no(n) for n in achar_nos(arv, "blockquote")], ["citado"])
        tabela = achar_nos(arv, "div", "md-tabela")
        self.assertEqual(len(tabela), 1, "a tabela fica numa moldura própria (rolagem horizontal)")
        self.assertEqual([texto_no(th) for th in achar_nos(tabela[0], "th")], ["a", "b"])
        self.assertEqual([texto_no(td) for td in achar_nos(tabela[0], "td")], ["1", "2"])
        self.assertEqual(len(achar_nos(arv, "hr")), 1)
        self.assertEqual([texto_no(n) for n in achar_nos(arv, "em")], ["it"])
        self.assertEqual([texto_no(n) for n in achar_nos(arv, "del")], ["tach"])
        self.assertEqual([texto_no(n) for n in achar_nos(arv, "strong")], ["neg"])
        self.assertEqual([texto_no(n) for n in achar_nos(arv, "code")], ["cod"])

    def test_link_vira_texto_com_endereco_visivel_e_botao_sem_elemento_a(self):
        conv = conversa([{"role": "user", "content": "q"}, {"role": "assistant", "content": CONTEUDO_LINK}])
        medido, arv = self.arvore_da_transcricao({"conversas": LISTA, "conversa": conv, "abrir": True,
                                                  "acoes_depois": [{"tipo": "clicar", "texto": "Copiar link", "em": "seth-transcript", "indice": 0}]})
        self.assertEqual(achar_nos(arv, "a"), [], "nada de link <a> saindo do painel")
        self.assertEqual([texto_no(n) for n in achar_nos(arv, "code", "md-link-url")], ["https://exemplo.org/doc", "https://exemplo.org/x"],
                         "o endereço fica visível; a pontuação colada ao fim da URL sai do link")
        self.assertIn("javascript:alert(1)", medido["transcricaoCompleta"], "esquema que não é http vira texto puro")
        self.assertIn("a doc", medido["transcricaoCompleta"])
        self.assertEqual(medido["copiados"], ["https://exemplo.org/doc"], "Copiar link copia o endereço")

    def test_bloco_de_codigo_tem_linguagem_e_botao_copiar_com_confirmacao(self):
        conv = conversa([{"role": "user", "content": "q"}, {"role": "assistant", "content": CODIGO_PY}])
        medido, arv = self.arvore_da_transcricao({"conversas": LISTA, "conversa": conv, "abrir": True,
                                                  # 0 = Copiar da pergunta; 1 = Copiar do bloco de código (vem antes dos botões da resposta)
                                                  "acoes_depois": [{"tipo": "clicar", "texto": "Copiar", "em": "seth-transcript", "indice": 1}]})
        bloco = achar_nos(arv, "div", "md-codigo")
        self.assertEqual(len(bloco), 1)
        self.assertEqual(texto_no(achar_nos(bloco[0], "span", "md-codigo-lingua")[0]), "py", "a linguagem aparece no cabeçalho do bloco")
        self.assertEqual(medido["copiados"], ["print('oi')"], "copia só o código, sem a cerca")
        self.assertIn("Copiado", medido["transcricaoCompleta"], "a confirmação aparece na região aria-live")

    def test_indicador_aparece_enquanto_a_seth_responde_e_some_ao_parar(self):
        medido = rodar_painel({"conversas": LISTA, "stream": {"lento": True, "sse": 'data: {"tipo": "texto", "delta": "parcial"}\n\n'},
                               "enviar": ["oi"], "depois": [CLIQUE_ARVORE],
                               "acoes_depois": [{"tipo": "clicar", "id": "seth-parar"}, CLIQUE_ARVORE]})
        durante, depois = medido["resultados"]
        self.assertEqual(len(achar_nos(durante, "span", "seth-digitando")), 1, "cursor no fim do texto enquanto responde")
        self.assertEqual(achar_nos(depois, "span", "seth-digitando"), [], "o cursor some quando a resposta termina")

    def test_hora_curta_com_data_no_title_e_mensagem_sem_hora_nao_mostra_nada(self):
        conv = conversa([{"role": "user", "content": "q", "hora": "2026-11-09T10:15:00-03:00"}, {"role": "assistant", "content": "ok"}])
        _, arv = self.arvore_da_transcricao({"conversas": LISTA, "conversa": conv, "abrir": True})
        horas = achar_nos(arv, "time")
        self.assertRegex(texto_no(horas[0]), r"^\d{2}:\d{2}$", "hora curta local")
        self.assertEqual(horas[0]["a"]["datetime"], "2026-11-09T10:15:00-03:00")
        self.assertIn("2026", horas[0]["title"], "o title leva a data completa")
        self.assertEqual(texto_no(horas[1]), "", "mensagem antiga sem hora não mostra nada")
        self.assertNotIn("title", horas[1])

    def test_mensagem_nova_grava_hora_iso_com_fuso_do_usuario_e_da_seth(self):
        medido = rodar_painel({"conversas": LISTA, "enviar": ["oi"]})
        mensagens = corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])["mensagens"]
        self.assertRegex(mensagens[0]["hora"], ISO_COM_FUSO)
        self.assertRegex(mensagens[1]["hora"], ISO_COM_FUSO)

    def test_anexo_aparece_como_etiqueta_com_nome_e_tamanho_e_conta_no_contexto(self):
        conv = conversa([{"role": "user", "content": "x" * 100}, {"role": "assistant", "content": "ok"}])
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True,
                               "acoes": [{"tipo": "arquivos", "id": "seth-anexo-arquivo", "lista": [{"nome": "notas.txt", "tipo": "text/plain", "texto": "linha 1\nlinha 2"}]}]})
        self.assertFalse(medido["anexosOculto"])
        self.assertIn("notas.txt", medido["anexos"])
        self.assertIn("15 caracteres", medido["anexos"])
        self.assertIn("Remover", medido["anexos"])
        self.assertTrue(medido["contextoDetalhe"].startswith("Contexto da próxima pergunta: 117 caracteres,"), medido["contextoDetalhe"])

    def test_remover_anexo_tira_a_etiqueta(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [
            {"tipo": "arquivos", "id": "seth-anexo-arquivo", "lista": [{"nome": "notas.txt", "tipo": "text/plain", "texto": "oi"}]},
            {"tipo": "clicar", "texto": "Remover", "em": "seth-anexos"}]})
        self.assertTrue(medido["anexosOculto"])
        self.assertEqual(medido["anexos"], "")

    def test_envio_leva_o_texto_do_anexo_no_pedido_e_so_o_metadado_na_conversa(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [
            {"tipo": "arquivos", "id": "seth-anexo-arquivo", "lista": [{"nome": "notas.txt", "tipo": "text/plain", "texto": "linha 1\nlinha 2"}]}],
            "enviar": ["resuma"]})
        pedido = chamadas_para(medido, "/api/seth/chat/stream")[0]
        self.assertEqual(corpo_de(pedido)["anexos"], [{"nome": "notas.txt", "texto": "linha 1\nlinha 2"}])
        self.assertIn("notas.txt · 15 caracteres", medido["transcricaoCompleta"], "a mensagem desenhada mostra nome e caracteres")
        self.assertTrue(medido["anexosOculto"], "as etiquetas somem depois do envio")
        gravada = corpo_de(chamadas_para(medido, "/api/seth/conversa")[-1])["mensagens"][0]
        self.assertEqual(gravada["anexos"], [{"nome": "notas.txt", "caracteres": 15}], "a conversa guarda só nome e caracteres")

    def test_recusas_de_anexo_dizem_o_motivo(self):
        grande = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "arquivos", "id": "seth-anexo-arquivo",
                                                              "lista": [{"nome": "grande.txt", "tipo": "text/plain", "texto": "x" * 20001}]}]})
        self.assertIn("o limite por arquivo é 20000", grande["anexoAviso"])
        self.assertNotIn("grande.txt", grande["anexos"], "acima do limite não entra")
        foto = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "arquivos", "id": "seth-anexo-arquivo",
                                                            "lista": [{"nome": "foto.png", "tipo": "image/png", "texto": "bytes"}]}]})
        self.assertEqual(foto["anexoAviso"], "A conversa ainda não lê imagens.", "imagem é recusada com a frase exata, sem prometer")
        quatro = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "arquivos", "id": "seth-anexo-arquivo",
                                                              "lista": [{"nome": f"a{i}.txt", "tipo": "text/plain", "texto": "x"} for i in range(4)]}]})
        self.assertIn("no máximo 3 anexos por mensagem", quatro["anexoAviso"])
        self.assertEqual(quatro["anexos"].count("Remover"), 3)

    def test_arquivo_acima_de_4_vezes_o_limite_e_recusado_antes_de_ler(self):
        # X1 (16/11/2026): File.size acima de 4 x 20000 (80000 bytes) é recusado antes do FileReader; o arquivo não é lido.
        grande = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "arquivos", "id": "seth-anexo-arquivo",
                                                              "lista": [{"nome": "enorme.txt", "tipo": "text/plain", "texto": "x", "tamanho": 80001}]}]})
        self.assertEqual(grande["leituras"], [], "nenhum FileReader pode ser criado para arquivo acima do teto de bytes")
        self.assertIn("80000 bytes", grande["anexoAviso"])
        self.assertIn("o limite por arquivo é 20000", grande["anexoAviso"])
        self.assertNotIn("enorme.txt", grande["anexos"])
        no_teto = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "arquivos", "id": "seth-anexo-arquivo",
                                                               "lista": [{"nome": "teto.txt", "tipo": "text/plain", "texto": "x", "tamanho": 80000}]}]})
        self.assertEqual(no_teto["leituras"], ["teto.txt"], "no teto exato (80000) o arquivo é lido, porque a recusa é acima dele")
        self.assertIn("teto.txt", no_teto["anexos"])

    def test_texto_colado_longo_vira_colado_txt_e_curto_fica_no_campo(self):
        longo = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "colar", "id": "seth-input", "texto": "p" * 4500}]})
        self.assertTrue(longo["marcas"].get("colarPrevenido"), "o colar longo não entra no campo")
        self.assertIn("colado.txt", longo["anexos"])
        curto = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "colar", "id": "seth-input", "texto": "p" * 100}]})
        self.assertFalse(curto["marcas"].get("colarPrevenido", False))
        self.assertEqual(curto["anexos"], "")

    def test_arrastar_e_soltar_anexa_no_compositor(self):
        medido = rodar_painel({"conversas": LISTA, "acoes": [{"tipo": "soltar", "id": "seth-form",
                                                              "lista": [{"nome": "log.log", "tipo": "text/plain", "texto": "erro 1"}]}]})
        self.assertIn("log.log", medido["anexos"])

    def test_uso_do_gateway_aparece_na_linha_de_contexto_e_sem_uso_fica_a_estimativa(self):
        sse = 'data: {"tipo": "texto", "delta": "oi"}\n\ndata: {"tipo": "uso", "entrada": 120, "saida": 40}\n\ndata: {"tipo": "fim"}\n\n'
        comuso = rodar_painel({"conversas": LISTA, "stream": {"sse": sse}, "enviar": ["pergunta"]})
        self.assertIn("Último pedido: entrada 120 · saída 40 tokens (informado pelo gateway).", comuso["contextoDetalhe"])
        semuso = rodar_painel({"conversas": LISTA, "enviar": ["pergunta"]})
        self.assertIn("Medida: estimativa em caracteres.", semuso["contextoDetalhe"])
        self.assertNotIn("informado pelo gateway", semuso["contextoDetalhe"])

    def test_pedido_de_vinte_mensagens_com_acentos_passa_o_teto_antigo_sem_cortar(self):
        # C10: 20 mensagens de 4000 "é" (2 bytes cada em UTF-8) passam de 131072 bytes e cabem no novo teto de 262144.
        antigas = [{"role": "user" if i % 2 == 0 else "assistant", "content": "é" * 4000} for i in range(20)]
        medido = rodar_painel({"conversas": LISTA, "conversa": conversa(antigas), "abrir": True, "enviar": ["oi"]})
        pedido = chamadas_para(medido, "/api/seth/chat/stream")[0]
        self.assertGreater(len(pedido["corpo"].encode("utf-8")), 131072)
        self.assertLessEqual(len(pedido["corpo"].encode("utf-8")), panel_limite_pedido())
        self.assertFalse(any("de fora" in t for t in medido["transcricao"]), medido["transcricao"])


class ConversaRascunhoErroInstrucoes(unittest.TestCase):
    """C6, C7 e C8 com o DOM falso: rascunho por conversa, "Tentar de novo" e instruções da conversa."""

    def test_rascunho_volta_ao_trocar_de_conversa(self):
        outra = conversa_com_id("bbbbbbbbbbbb", [])
        cenario = {"conversas": [LISTA[0], conversa_item("bbbbbbbbbbbb", "Segunda")], "conversa": conversa([]),
                   "porId": {"bbbbbbbbbbbb": outra}, "abrir": True}
        digitou = rodar_painel(dict(cenario, acoes=[{"tipo": "digitar", "id": "seth-input", "valor": "rascunho da antiga"},
                                                    {"tipo": "clicar", "texto": "Segunda", "em": "seth-conversas"}]))
        self.assertEqual(digitou["entrada"], "", "a conversa segunda não tem rascunho da primeira")
        voltou = rodar_painel(dict(cenario, acoes=[{"tipo": "digitar", "id": "seth-input", "valor": "rascunho da antiga"},
                                                   {"tipo": "clicar", "texto": "Segunda", "em": "seth-conversas"},
                                                   {"tipo": "clicar", "texto": "Antiga", "em": "seth-conversas"}]))
        self.assertEqual(voltou["entrada"], "rascunho da antiga", "ao voltar, o rascunho da conversa reaparece")

    def test_nova_conversa_tem_rascunho_proprio_e_enviar_limpa_o_da_conversa(self):
        vazia = rodar_painel({"conversas": LISTA, "conversa": conversa([]), "abrir": True,
                              "acoes": [{"tipo": "digitar", "id": "seth-input", "valor": "rascunho da antiga"},
                                        {"tipo": "clicar", "id": "seth-nova"}]})
        self.assertEqual(vazia["entrada"], "", "a conversa nova começa com o campo vazio")
        enviou = rodar_painel({"conversas": LISTA, "conversa": conversa([]), "abrir": True,
                               "acoes": [{"tipo": "digitar", "id": "seth-input", "valor": "rascunho da antiga"}],
                               "enviar": ["pergunta final"]})
        self.assertFalse(any("rascunho da antiga" in v for _, v in enviou["sessaoGravacoes"]), "o rascunho nunca vai para o armazenamento do navegador (R9)")
        self.assertNotIn("rascunho da antiga", enviou["sessaoValor"] or "", "enviado, o rascunho da conversa some")

    def test_rascunho_so_em_memoria_recarregar_comeca_vazio(self):
        # R9 (16/11/2026): o rascunho é um Map em memória. Um valor deixado no armazenamento da aba não é lido de volta.
        guardado = json.dumps({"nova-inicial": {"texto": "nao deve voltar", "anexos": []}})
        medido = rodar_painel({"conversas": LISTA, "sessionStorage": {"inicial": {"agata-seth-rascunhos": guardado}}})
        self.assertEqual(medido["entrada"], "", "recarregar começa com o campo vazio")

    def test_tentar_de_novo_reenvia_sem_duplicar_a_pergunta(self):
        medido = rodar_painel({"conversas": LISTA, "stream": [{"status": 400, "texto": "mensagem 1 acima de 4000 caracteres"}, {}],
                               "enviar": ["pergunta X"],
                               "acoes_depois": [{"tipo": "clicar", "texto": "Tentar de novo", "em": "seth-transcript"}]})
        pedidos = chamadas_para(medido, "/api/seth/chat/stream")
        self.assertEqual(len(pedidos), 2, "o segundo pedido é o 'Tentar de novo'")
        for pedido in pedidos:
            self.assertEqual(corpo_de(pedido)["mensagens"], [{"role": "user", "content": "pergunta X"}])
        self.assertEqual(medido["transcricaoCompleta"].count("pergunta X"), 1, "a pergunta aparece uma vez só")
        self.assertIn("resposta", medido["transcricaoCompleta"])
        self.assertNotIn("Tentar de novo", medido["botoes"], "com a resposta, o botão some")

    def test_pedido_leva_instrucoes_da_conversa_e_o_chip_aparece(self):
        conv = {**conversa([{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}]), "instrucoes": "Responda em tópicos."}
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True, "enviar": ["oi"]})
        pedido = corpo_de(chamadas_para(medido, "/api/seth/chat/stream")[0])
        self.assertEqual(pedido["instrucoes"], "Responda em tópicos.")
        self.assertEqual(pedido["anexos"], [])
        self.assertFalse(medido["chipInstrucoesOculto"], "chip 'com instruções' no cabeçalho")

    def test_fallback_tambem_leva_as_instrucoes(self):
        conv = {**conversa([]), "instrucoes": "Seja breve."}
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True, "stream": {"status": 502, "texto": ""}, "enviar": ["oi"]})
        pedido = corpo_de(chamadas_para(medido, "/api/seth/chat")[0])
        self.assertEqual(pedido["instrucoes"], "Seja breve.")
        self.assertEqual(pedido["anexos"], [])

    def test_salvar_instrucoes_grava_na_conversa_e_limpar_tira(self):
        conv = conversa([{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}])
        salvo = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True, "acoes": [
            {"tipo": "clicar", "id": "seth-instrucoes-abrir"}, {"tipo": "digitar", "id": "seth-instrucoes-texto", "valor": "Use listas."},
            {"tipo": "clicar", "id": "seth-instrucoes-salvar"}]})
        self.assertEqual(corpo_de(chamadas_para(salvo, "/api/seth/conversa")[-1])["instrucoes"], "Use listas.")
        self.assertFalse(salvo["chipInstrucoesOculto"])
        limpo = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True, "acoes": [
            {"tipo": "clicar", "id": "seth-instrucoes-abrir"}, {"tipo": "digitar", "id": "seth-instrucoes-texto", "valor": "Use listas."},
            {"tipo": "clicar", "id": "seth-instrucoes-salvar"}, {"tipo": "clicar", "id": "seth-instrucoes-abrir"},
            {"tipo": "clicar", "id": "seth-instrucoes-limpar"}]})
        self.assertEqual(corpo_de(chamadas_para(limpo, "/api/seth/conversa")[-1])["instrucoes"], "")
        self.assertTrue(limpo["chipInstrucoesOculto"])

    def test_instrucoes_acima_de_2000_nao_gravam_e_avisam(self):
        conv = conversa([{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}])
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True, "acoes": [
            {"tipo": "clicar", "id": "seth-instrucoes-abrir"}, {"tipo": "digitar", "id": "seth-instrucoes-texto", "valor": "a" * 2001},
            {"tipo": "clicar", "id": "seth-instrucoes-salvar"}]})
        self.assertFalse([c for c in chamadas_para(medido, "/api/seth/conversa") if corpo_de(c).get("instrucoes")], "nada de instrução acima do limite vai ao servidor")
        self.assertFalse(medido["instrucoesErroOculto"])
        self.assertIn("passam de 2000 caracteres", medido["instrucoesErro"])

    def test_contador_de_instrucoes_mostra_caracteres_de_2000(self):
        conv = conversa([{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}])
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True, "acoes": [
            {"tipo": "clicar", "id": "seth-instrucoes-abrir"}, {"tipo": "digitar", "id": "seth-instrucoes-texto", "valor": "Use listas."}]})
        self.assertEqual(medido["instrucoesContagem"], "11 de 2000 caracteres")


class LoteChatHtmlCss(unittest.TestCase):
    """C4, C8, C9 e C12 (estática): ids, aviso do dialog, espelhos do menu, CSS do celular e ausência de "Compartilhar"."""

    def test_dialog_de_instrucoes_tem_limite_e_aviso_em_texto_simples(self):
        dialogo = HTML[HTML.index('<dialog id="seth-instrucoes-dialog"'):]
        dialogo = dialogo[:dialogo.index("</dialog>")]
        self.assertIn('id="seth-instrucoes-texto" maxlength="2000"', dialogo)
        self.assertIn("As instruções valem no modelo padrão da Seth; na via pública o gateway as descarta.", dialogo)
        self.assertNotIn("<a ", dialogo)
        for botao in ('id="seth-instrucoes-salvar"', 'id="seth-instrucoes-limpar"', 'id="seth-instrucoes-fechar"'):
            self.assertIn(botao, dialogo)

    def test_item_instrucoes_e_espelho_da_conversa_temporaria_no_menu_mais(self):
        menu = secao_conversa()[secao_conversa().index('id="seth-mais-menu"'):]
        menu = menu[:menu.index("</div>")]
        self.assertIn('id="seth-instrucoes-abrir"', menu)
        self.assertRegex(menu, r'<button[^>]*class="text-link seth-so-celular"[^>]*id="seth-temporaria-menu"')

    def test_anexar_tem_input_oculto_com_os_tipos_aceitos(self):
        self.assertRegex(HTML, r'<input id="seth-anexo-arquivo" type="file" multiple hidden accept="\.txt,\.md,\.json,\.csv,\.log,\.py,\.js,\.ts,\.html,\.css,\.yaml,\.yml,\.toml,\.sh,text/\*">')
        self.assertIn('id="seth-anexar"', secao_conversa())

    def test_avisos_de_organizacao_tem_espelho_no_menu(self):
        for id_ in ("seth-org-aviso-menu", "seth-ilegiveis-aviso-menu"):
            self.assertIn(f'id="{id_}"', menu_lateral())
            self.assertNotIn(f'id="{id_}"', organizar_dialog(), "o espelho fica no menu, separado do diálogo")

    def test_celular_cabe_em_duas_linhas_e_tira_a_temporaria_para_o_menu(self):
        css = (HERE / "prototipo.css").read_text(encoding="utf-8")
        bloco = css[css.index("@media (max-width:480px){\n  .seth-so-celular"):]
        bloco = bloco[:bloco.index("\n}")]
        self.assertIn("#seth-temporaria{display:none}", bloco)
        self.assertIn(".seth-cabecalho-acoes{flex-wrap:nowrap;justify-content:space-between", bloco)
        self.assertIn("text-overflow:ellipsis", bloco)

    def test_compartilhar_nao_existe_e_nao_foi_inventado(self):
        self.assertNotIn("Compartilh", HTML)
        self.assertNotIn("Compartilh", JS)

    def test_codigo_novo_nao_usa_innerhtml_nem_link_externo(self):
        self.assertNotRegex(JS, r"\.innerHTML\s*=")
        self.assertNotIn("insertAdjacentHTML", JS)
        self.assertNotIn("target=", HTML + JS)
        self.assertNotIn('href="http', HTML + JS)


LISTA_COM_SUBLISTA_E_BRANCO = """1. Ferramentas e fluxo
   - ferramenta um
   - ferramenta dois

2. Objetivos

   1. objetivo a
   2. objetivo b

3. Riscos"""


class ListasNumeradasMarkdown(unittest.TestCase):
    """J1 (16/11/2026): item numerado com sublista ou linha em branco segue na mesma ol; o número inicial vira start."""

    def transcricao(self, texto):
        conv = conversa([{"role": "user", "content": "q"}, {"role": "assistant", "content": texto}])
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True, "depois": [CLIQUE_ARVORE]})
        return achar_nos(medido["resultados"][-1], "div", "msg-body")[1]

    def test_lista_com_sublista_e_linha_em_branco_entre_itens_e_uma_ol_so(self):
        corpo = self.transcricao(LISTA_COM_SUBLISTA_E_BRANCO)
        oles = achar_nos(corpo, "ol")
        self.assertEqual(len(oles), 2, "a lista de topo e a dos objetivos, nada mais")
        topo = oles[0]
        self.assertNotIn("a", topo, "começa em 1: sem atributo start")
        itens = [li for li in topo["f"] if li["t"] == "li"]
        self.assertEqual([li["f"][0]["x"] for li in itens], ["Ferramentas e fluxo", "Objetivos", "Riscos"],
                         "o item 2 e o item 3 seguem a lista de 1, mesmo com sublista e linha em branco")
        self.assertEqual([texto_no(li) for li in achar_nos(itens[0], "ul")[0]["f"]], ["ferramenta um", "ferramenta dois"])
        self.assertEqual([texto_no(li) for li in achar_nos(itens[1], "ol")[0]["f"]], ["objetivo a", "objetivo b"])

    def test_numero_inicial_do_texto_vira_start(self):
        corpo = self.transcricao("3. Terceiro\n\n4. Quarto")
        oles = achar_nos(corpo, "ol")
        self.assertEqual(len(oles), 1)
        self.assertEqual(oles[0].get("a"), {"start": "3"}, "a lista começa em 3, como no texto")
        self.assertEqual(len([li for li in oles[0]["f"] if li["t"] == "li"]), 2)

    def test_paragrafo_entre_listas_recomeca_a_contagem(self):
        corpo = self.transcricao("1. Um\n2. Dois\n\nTexto no meio.\n\n1. Outro começo")
        oles = achar_nos(corpo, "ol")
        self.assertEqual(len(oles), 2, "texto sem marca quebra a lista: são duas")
        self.assertNotIn("a", oles[1], "a segunda começa em 1 de novo")


def ids_focaveis(trecho: str) -> list:
    """Ids dos controles que recebem Tab, em ordem de documento (botão, campo, link com href ou elemento com tabindex)."""
    from html.parser import HTMLParser

    class Coletor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids = []

        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            focavel = tag in ("button", "input", "select", "textarea") or (tag == "a" and "href" in d) or "tabindex" in d
            if focavel and d.get("type") != "hidden" and "hidden" not in d and d.get("id"):
                self.ids.append(d["id"])

    coletor = Coletor()
    coletor.feed(trecho)
    return coletor.ids


class LoteAjustesFinais(unittest.TestCase):
    """J2 a J8 (16/11/2026): ajustes vistos nas fotos. O que é visual (respiro, alinhamento, mosaico) tem medição em foto; aqui, a estrutura e o CSS."""

    CSS = (HERE / "prototipo.css").read_text(encoding="utf-8")

    def bloco_css(self, abertura: str) -> str:
        inicio = self.CSS.index(abertura)
        return self.CSS[inicio:self.CSS.index("\n}", inicio) + 2]

    def test_faixa_de_baixo_e_uma_linha_com_detalhes_e_modo_conversa_a_direita(self):  # J3
        faixa = secao_conversa()
        bloco = faixa[faixa.index('<div class="seth-linha-baixo">'):faixa.index("</footer>")]
        self.assertIn('<details class="seth-detalhes" id="seth-detalhes"><summary>Detalhes</summary>', bloco)
        dentro = bloco[bloco.index('<details class="seth-detalhes"'):bloco.index("</details>")]
        self.assertIn('id="seth-contexto-detalhe"', dentro, "o texto longo de contexto fica no Detalhes")
        self.assertIn('id="seth-modelo-desc"', dentro, "o aviso de filtro (descrição do modelo) fica no Detalhes")
        self.assertLess(bloco.index('id="seth-contexto"'), bloco.index("<details"), "contexto curto vem antes")
        self.assertLess(bloco.index("<details"), bloco.index('id="seth-modo-conversa"'), "modo conversa vem depois, na mesma faixa")
        self.assertIn("Modo conversa</label>", bloco)
        self.assertNotIn("Modo conversa: ler cada resposta", bloco, "o texto longo do modo vai para o title")
        self.assertIn(".seth-linha-baixo .seth-voz{margin:0 0 0 auto", self.CSS, "o modo conversa vai à direita")

    def test_botao_temporaria_e_interruptor_curto_com_titulo(self):  # J5
        secao = secao_conversa()
        botao = re.search(r'<button[^>]*id="seth-temporaria"[^>]*>([^<]*)</button>', secao)
        self.assertIsNotNone(botao)
        self.assertEqual(botao.group(1), "Temporária")
        self.assertIn('aria-pressed="false"', botao.group(0))
        self.assertIn('title="Conversa temporária: desligada.', botao.group(0), "o texto explicativo vai para o title")
        self.assertIn("Conversa temporária: não é salva.", secao, "o aviso do rodapé continua")

    def test_menu_mais_devolve_o_foco_ao_botao_com_esc(self):  # J8, harness
        conv = conversa([{"role": "user", "content": "q"}])
        medido = rodar_painel({"conversas": LISTA, "conversa": conv, "abrir": True,
                               "acoes": [{"tipo": "clicar", "id": "seth-mais-abrir"}, {"tipo": "tecla", "id": "seth-mais-menu", "tecla": "Escape"}]})
        self.assertTrue(medido["maisFocado"], "Esc fecha o menu e o foco volta a Mais")

    def test_transcricao_e_focavel_com_nome_e_ordem_de_tab_da_conversa(self):  # J8
        aside = menu_lateral()
        conversa_html = secao_conversa()
        ids = ids_focaveis(aside) + ids_focaveis(conversa_html)
        self.assertIn('aria-label="Mensagens da conversa" tabindex="0"', conversa_html, "a transcrição entra no Tab e tem nome")
        self.assertIn('role="log"', conversa_html)
        self.assertIn('aria-live="polite"', conversa_html)
        self.assertRegex(conversa_html, r'<button class="seth-ir-fim" type="button" id="seth-ir-fim" hidden>Ir para o fim</button>',
                         "Ir para o fim tem texto próprio (aparece só fora do fim)")
        ordem = [ids.index(x) for x in ("seth-nova", "seth-temporaria", "seth-mais-abrir", "seth-transcript", "seth-input", "seth-send")]
        self.assertEqual(ordem, sorted(ordem), "menu -> cabeçalho -> mensagens -> compositor")
        self.assertLess(ids.index("seth-busca"), ids.index("seth-temporaria"), "o menu vem antes do cabeçalho")

    def test_gaveta_tem_fechar_no_lugar_da_seta_e_rodape_fixo(self):  # J4
        aside = menu_lateral()
        self.assertIn('id="menu-fechar"', aside)
        self.assertRegex(aside, r'<button class="text-link menu-fechar"[^>]*>Fechar</button>')
        self.assertIn(".menu-fechar{display:none}", self.CSS, "fora da gaveta o Fechar não aparece")
        conversas = aside.index('class="menu-conversas"')
        rodape = aside.index('class="menu-rodape"')
        self.assertLess(conversas, rodape)
        for id_ in ("seth-arquivadas-bloco", "seth-lixeira-bloco", "organizar-abrir", "servicos-locais"):
            self.assertGreater(aside.index(f'id="{id_}"'), rodape, f"{id_} fica no rodapé fixo da gaveta")
        self.assertNotIn('id="seth-lixeira-bloco"', aside[conversas:rodape], "a lixeira não está mais na lista rolável")
        gaveta = self.bloco_css("@media (max-width:1023px){")
        self.assertIn(".sidebar{position:fixed", gaveta)
        self.assertIn("overflow:hidden}", gaveta)
        self.assertIn(".menu-fechar{display:inline-flex", gaveta)
        self.assertIn(".sidebar .menu-conversas .seth-conversas{flex:1 1 0;min-height:96px}", gaveta)
        self.assertIn(".sidebar-toggle{display:none}", gaveta, "a seta some na gaveta")

    def test_mosaicos_ficam_dois_por_linha_ate_360_quando_cabem(self):  # J7
        bloco = self.bloco_css("@media (max-width:480px){\n  .kpis{grid-template-columns:repeat(auto-fit")
        self.assertIn("repeat(auto-fit,minmax(min(100%,140px),1fr))", bloco)
        self.assertNotIn("grid-template-columns:minmax(0,1fr)}", bloco.split("}")[0] + "}")

    def test_cartoes_do_panorama_alinhados_no_topo_com_cabecalho_de_mesma_altura(self):  # J6
        self.assertIn(".nv-cartoes>.panel{margin:0}", self.CSS, "o irmão + irmão não empurra os cartões da direita")
        self.assertIn(".nv-cartoes .panel-head{min-height:56px", self.CSS)
        panorama = HTML[HTML.index('<div class="sub" id="sub-panorama"'):HTML.index('<div class="footer-note">')]
        self.assertEqual(panorama.count('<article class="panel'), 3, "três cartões: memória, conversa e importantes")

    def test_respiro_no_fim_da_transcricao(self):  # J2
        self.assertIn("gap:18px;padding:12px 4px 36px;overflow:auto}", self.CSS)


class LimitesDaUi(unittest.TestCase):
    def test_constantes_da_ui_sao_as_do_servidor(self):
        constantes = dict(re.findall(r"^const (SETH_[A-Z_]+) = ([\d_]+);", JS, flags=re.M))
        self.assertEqual(int(constantes["SETH_MAX_MENSAGENS"]), chat_stream.MAX_MENSAGENS)
        self.assertEqual(int(constantes["SETH_MAX_CARACTERES"]), chat_stream.MAX_CARACTERES_MENSAGEM)
        self.assertEqual(int(constantes["SETH_LIMITE_PEDIDO_BYTES"]), panel_limite_pedido())
        self.assertEqual(int(constantes["SETH_LIMITE_CONVERSA_BYTES"]), armazem.CONVERSA_LIMITE_BYTES)
        self.assertEqual(int(constantes["SETH_BUSCA_MAX_CARACTERES"]), armazem.BUSCA_TERMO_LIMITE)
        self.assertEqual(int(constantes["SETH_LIMITE_IMPORTACAO_BYTES"]), armazem.IMPORTACAO_LIMITE_BYTES)
        self.assertEqual(int(constantes["SETH_FEEDBACK_MOTIVO_LIMITE"]), armazem.FEEDBACK_MOTIVO_LIMITE)
        # C8/C9 (16/11/2026): instruções e anexos com os mesmos números do servidor.
        self.assertEqual(int(constantes["SETH_INSTRUCOES_LIMITE"]), chat_stream.MAX_INSTRUCOES)
        self.assertEqual(int(constantes["SETH_ANEXOS_MAX"]), chat_stream.MAX_ANEXOS)
        self.assertEqual(int(constantes["SETH_ANEXO_NOME_MAX"]), chat_stream.MAX_ANEXO_NOME)
        self.assertEqual(int(constantes["SETH_ANEXO_TEXTO_MAX"]), chat_stream.MAX_ANEXO_TEXTO)
        self.assertEqual(int(constantes["SETH_ANEXOS_TOTAL_MAX"]), chat_stream.MAX_ANEXOS_TOTAL)


if __name__ == "__main__":
    unittest.main()
