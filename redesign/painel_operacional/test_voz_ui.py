"""Testes de interface da voz da Seth (prototipo.js, prototipo.html, prototipo.css; spec/spec.md, 11/11/2026).

Roda o prototipo.js de verdade num contexto node, com um DOM mínimo, um fetch roteirizado, um MediaRecorder falso e
um getUserMedia falso. Nenhum microfone real é aberto e nenhuma rede é usada. O arquivo em disco não muda: o
harness só acrescenta, em memória, a exposição das funções de voz antes do fim do IIFE (como o test_chat_ui.py).
Os testes de texto conferem o HTML, o CSS e o JS novos: sem HTML dinâmico, sem atributo inline, sem emoji.
"""
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = (HERE / "prototipo.html").read_text(encoding="utf-8")
CSS = (HERE / "prototipo.css").read_text(encoding="utf-8")
JS = (HERE / "prototipo.js").read_text(encoding="utf-8")
SERVIDOR = (HERE / "server.py").read_text(encoding="utf-8")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]")

NODE_VOZ = r"""
const fs = require('fs'); const path = require('path'); const vm = require('vm');
const {TextEncoder, TextDecoder} = require('util');
process.on('unhandledRejection', () => {});
const cen = JSON.parse(fs.readFileSync(0, 'utf8')); const dir = process.env.PAINEL_DIR;
class Texto { constructor(t) { this.textContent = t; } appendData(d) { this.textContent += d; } }
class Elemento {
  constructor(tag, id) {
    this.tag = tag; this.id = id || ''; this.textContent = ''; this.hidden = false; this.className = ''; this.value = '';
    this.checked = false; this.disabled = false; this.dataset = {}; this.children = []; this.ouvintes = {}; this.attrs = {};
    this.scrollTop = 0; this.scrollHeight = 0; this.title = ''; this.type = ''; this.style = {}; this.focado = false;
    this._classes = new Set();
    this.classList = {add: (...c) => c.forEach((x) => this._classes.add(x)), remove: (...c) => c.forEach((x) => this._classes.delete(x)),
      toggle() {}, contains: (x) => this._classes.has(x)};
  }
  append(...nos) { this.children.push(...nos); }
  replaceChildren(...nos) { this.children = nos; }
  setAttribute(nome, valor) { this.attrs[nome] = String(valor); }
  getAttribute(nome) { return Object.prototype.hasOwnProperty.call(this.attrs, nome) ? this.attrs[nome] : null; }
  addEventListener(tipo, fn) { (this.ouvintes[tipo] = this.ouvintes[tipo] || []).push(fn); }
  focus() { this.focado = true; } blur() {} remove() {} select() {}
  requestSubmit() { (this.ouvintes.submit || []).forEach((f) => f({preventDefault() {}, target: this})); }
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
// Estado inicial do HTML que importa para a voz (o mock não lê o HTML).
const OCULTOS = ['atalhos-painel', 'seth-voz-parar', 'seth-parar', 'seth-chamado-estado'];
const INICIAIS = {'seth-ditado': {atributos: {'aria-pressed': 'false'}, texto: 'Ditar'}, 'seth-chamado': {atributos: {'aria-pressed': 'false'}, texto: 'Conversa por voz'}};
const registro = new Map();
const ouvintesDoc = {};
const documento = {
  visibilityState: 'visible',
  getElementById(id) {
    if (!registro.has(id)) {
      const e = new Elemento('id:' + id, id);
      if (OCULTOS.includes(id)) e.hidden = true;
      if (INICIAIS[id]) { Object.assign(e.attrs, INICIAIS[id].atributos); e.textContent = INICIAIS[id].texto; }
      registro.set(id, e);
    }
    return registro.get(id);
  },
  querySelector() { return new Elemento('q'); }, querySelectorAll() { return []; },
  createElement(tag) { return new Elemento(tag); }, createElementNS(ns, tag) { return new Elemento(tag); },
  createTextNode(t) { return new Texto(t); },
  addEventListener(tipo, fn) { (ouvintesDoc[tipo] = ouvintesDoc[tipo] || []).push(fn); },
  documentElement: new Elemento('html'),
};
const cargas = []; const chamadas = []; const timers = []; const gravadores = []; const pendentes = [];
const microfone = {pedidos: [], parados: 0};
const gravacoes = [];
const armazenamento = Object.assign({}, cen.storage && cen.storage.inicial || {});
function cabecalhosDe(cab) { return {get: (nome) => (cab || {})[String(nome).toLowerCase()] ?? null}; }
function respostaJson(status, obj) { return {ok: status >= 200 && status < 300, status, headers: cabecalhosDe({}), json: async () => obj, text: async () => JSON.stringify(obj)}; }
function respostaTexto(status, t) { return {ok: status >= 200 && status < 300, status, headers: cabecalhosDe({}), json: async () => { throw new Error('sem json'); }, text: async () => t}; }
function respostaStreamTravado() { return {ok: true, status: 200, headers: cabecalhosDe({}), json: async () => ({}), text: async () => '', body: {getReader() { return {read: () => new Promise(() => {}), cancel: async () => {}}; }}}; }
function respostaStream(sse) {
  const bytes = new TextEncoder().encode(sse); let lido = false;
  return {ok: true, status: 200, headers: cabecalhosDe({}), json: async () => ({}), text: async () => '', body: {getReader() { return {
    read: async () => { if (lido) return {done: true, value: undefined}; lido = true; return {done: false, value: bytes}; },
    cancel: async () => {}}; }}};
}
const respostas = cen.respostas || {};
function proxima(url) {
  const fila = respostas[url];
  if (!fila || !fila.length) return null;
  return fila.length > 1 ? fila.shift() : fila[0];
}
class GravadorFalso {
  constructor(fluxo, opc) {
    this.fluxo = fluxo; this.opc = opc || {}; this.mimeType = (opc && opc.mimeType) || 'audio/webm';
    this.ouvintes = {}; this.estado = 'inactive'; gravadores.push(this);
  }
  addEventListener(tipo, fn) { (this.ouvintes[tipo] = this.ouvintes[tipo] || []).push(fn); }
  start(ms) { this.estado = 'recording'; this.ms = ms; }
  stop() {
    if (this.estado !== 'recording') return;
    this.estado = 'inactive';
    const tam = cen.tamanhoAudio !== undefined ? cen.tamanhoAudio : 5;
    (this.ouvintes.dataavailable || []).forEach((f) => f({data: new Blob([new Uint8Array(tam)], {type: this.mimeType})}));
    (this.ouvintes.stop || []).forEach((f) => f({}));
  }
}
GravadorFalso.isTypeSupported = (t) => (cen.tipos || ['audio/webm;codecs=opus', 'audio/webm']).includes(t);
const ctx = {};
ctx.window = ctx; ctx.document = documento; ctx.location = {hash: ''}; ctx.history = {pushState() {}};
ctx.localStorage = {
  getItem(k) { if (cen.storage && cen.storage.lerErro) throw new Error('bloqueado'); return Object.prototype.hasOwnProperty.call(armazenamento, k) ? armazenamento[k] : null; },
  setItem(k, v) { if (cen.storage && cen.storage.gravarErro) throw new Error('cheio'); armazenamento[k] = String(v); gravacoes.push([k, String(v)]); }};
ctx.navigator = {clipboard: {writeText: async () => {}}};
if (!cen.semMicrofone) ctx.navigator.mediaDevices = {getUserMedia: async (restricoes) => {
  microfone.pedidos.push(restricoes);
  if (cen.microfone && cen.microfone.negar) { const e = new Error('negado'); e.name = 'NotAllowedError'; throw e; }
  return {getTracks: () => [{stop() { microfone.parados++; }}]};
}};
if (!cen.semGravador) { ctx.MediaRecorder = GravadorFalso; ctx.Blob = Blob; }
ctx.Node = function () {};
ctx.TextEncoder = TextEncoder; ctx.TextDecoder = TextDecoder;
class ControleFalso { constructor() { this.signal = {aborted: false, ouvintes: [], addEventListener() {}}; } abort() { if (this.signal.aborted) return; this.signal.aborted = true; this.signal.ouvintes.forEach((f) => f()); } }
ctx.AbortController = ControleFalso;
ctx.setTimeout = (f, ms) => { timers.push({f, ms, cancelado: false}); return timers.length; };
ctx.clearTimeout = (id) => { if (timers[id - 1]) timers[id - 1].cancelado = true; };
const intervalos = []; const fontes = [];
let relogio = cen.relogio !== undefined ? cen.relogio : 1000;
const nivelMic = {valor: cen.nivel !== undefined ? cen.nivel : 0};
ctx.setInterval = (f, ms) => { intervalos.push({f, ms, ativo: true}); return intervalos.length; };
ctx.clearInterval = (id) => { if (intervalos[id - 1]) intervalos[id - 1].ativo = false; };
ctx.performance = {now: () => relogio};
ctx.AudioContext = class {
  constructor() { this.destination = {}; this.state = (cen.audio && cen.audio.travado) ? 'suspended' : 'running'; }
  resume() { if (!(cen.audio && cen.audio.travado)) this.state = 'running'; return Promise.resolve(); }
  createMediaStreamSource() { return {connect() {}}; }
  createAnalyser() { return {fftSize: 0, getFloatTimeDomainData(buf) { buf.fill(nivelMic.valor); }}; }
  decodeAudioData(bytes) { return Promise.resolve({duracao: 1, bytes: bytes}); }
  createBufferSource() {
    const f = {buffer: null, tocando: false, acabou: false, onended: null, connect() {}, start() { this.tocando = true; },
      stop() { if (!this.acabou) { this.acabou = true; if (this.onended) this.onended(); } }};
    fontes.push(f); return f;
  }
  close() { return Promise.resolve(); }
};
ctx.addEventListener = (tipo, fn) => { if (tipo === 'load') cargas.push(fn); };
ctx.fetch = async (url, opcoes = {}) => {
  const metodo = String(opcoes.method || 'GET').toUpperCase();
  let corpo = null;
  if (typeof opcoes.body === 'string') corpo = opcoes.body;
  else if (opcoes.body && typeof opcoes.body.size === 'number') corpo = {blob: true, tamanho: opcoes.body.size, tipo: opcoes.body.type};
  chamadas.push({url, metodo, corpo, cabecalhos: opcoes.headers || null, temSinal: Boolean(opcoes.signal)});
  if (url === '/api/seth/conversa' && metodo === 'POST') return respostaJson(200, {schema_version: 1, id: '0123456789ab', titulo: '', mensagens: []});
  if (url === '/api/seth/conversas') return respostaJson(200, {schema_version: 1, state: 'ok', items: [], pastas: [], marcadores: [], total: 0, organizacao: 'ok', ilegiveis: 0});
  if (url === '/api/seth/chat/stream') {
    const r = proxima(url) || {};
    if (r.travado) return respostaStreamTravado();
    return respostaStream(r.sse !== undefined ? r.sse : 'data: {"tipo": "texto", "delta": "Resposta da Seth."}\n\ndata: {"tipo": "fim"}\n\n');
  }
  const r = proxima(url);
  if (r && r.wav) return {ok: true, status: 200, headers: cabecalhosDe(r.cabecalhos), json: async () => ({}), text: async () => '', arrayBuffer: async () => new ArrayBuffer(8)};
  if (r && r.pendente) return new Promise((resolver) => pendentes.push(resolver));
  if (r) {
    if (r.rede) throw new TypeError('Failed to fetch');
    if (r.json !== undefined) return respostaJson(r.status || 200, r.json);
    return respostaTexto(r.status || 200, r.texto || '');
  }
  return respostaJson(404, {erro: 'sem resposta de teste'});
};
// Ajudantes para os passos do teste (não são código do painel).
function acharBotao(idRaiz, rotulo) {
  return descendentes(documento.getElementById(idRaiz)).find((e) => e.tag === 'button' && texto(e).trim() === rotulo) || null;
}
ctx.__ouvir = (indice) => { const bs = descendentes(documento.getElementById('seth-transcript')).filter((e) => e.tag === 'button' && texto(e).trim() === 'Ouvir'); bs[indice || 0].ouvintes.click[0]({}); };
ctx.__contarOuvir = () => descendentes(documento.getElementById('seth-transcript')).filter((e) => e.tag === 'button' && texto(e).trim() === 'Ouvir').length;
ctx.__clicar = (id) => { const e = documento.getElementById(id); (e.ouvintes.click || []).forEach((f) => f({target: e})); };
ctx.__mudar = (id, valor) => { const e = documento.getElementById(id); e.checked = valor; (e.ouvintes.change || []).forEach((f) => f({target: e})); };
ctx.__tecla = (key) => (ouvintesDoc.keydown || []).forEach((f) => f({key, target: {tagName: 'BODY', isContentEditable: false}, ctrlKey: false, metaKey: false, shiftKey: false, preventDefault() {}}));
ctx.__campo = (valor) => { documento.getElementById('seth-input').value = valor; };
ctx.__enviar = (mensagem) => { documento.getElementById('seth-input').value = mensagem; const form = documento.getElementById('seth-form'); form.ouvintes.submit[0]({preventDefault() {}, target: form}); };
ctx.__resolverPendentes = (obj) => { pendentes.splice(0).forEach((f) => f(respostaJson(200, obj))); };
ctx.__disparar = (ms) => { const t = timers.find((x) => x.ms === ms && !x.cancelado); if (t) t.f(); return Boolean(t); };
ctx.__relogio = () => relogio;
ctx.__clicarDocumento = () => (ouvintesDoc.click || []).forEach((f) => f({target: {tagName: 'BODY', isContentEditable: false}}));
ctx.__tick = () => { const t = timers.find((x) => x.ms === 50 && !x.cancelado && !x.disparado); if (t) { t.disparado = true; t.f(); } return Boolean(t); };
ctx.__avanca = (ms) => { relogio += ms; };
ctx.__nivel = (v) => { nivelMic.valor = v; };
ctx.__terminarTrecho = () => { const f = fontes.find((x) => x.tocando && !x.acabou); if (!f) return false; f.acabou = true; if (f.onended) f.onended(); return true; };
ctx.__estado = () => {
  const v = documento.getElementById('seth-voz-estado'); const d = documento.getElementById('seth-ditado');
  return {voz: v.textContent, classe: v.className, pararVisivel: !documento.getElementById('seth-voz-parar').hidden,
    ditado: d.textContent, pressionado: d.getAttribute('aria-pressed'), ditadoDesabilitado: d.disabled,
    campo: documento.getElementById('seth-input').value, modo: documento.getElementById('seth-modo-conversa').checked,
    chamadoBotao: documento.getElementById('seth-chamado').textContent, chamadoAria: documento.getElementById('seth-chamado').getAttribute('aria-pressed'),
    chamadoTexto: documento.getElementById('seth-chamado-estado').textContent, chamadoOculta: documento.getElementById('seth-chamado-estado').hidden};
};
const esperar = async () => { for (let i = 0; i < 120; i++) await new Promise((r) => setImmediate(r)); };
(async () => {
  try {
    const fonte = fs.readFileSync(path.join(dir, 'prototipo.js'), 'utf8');
    const fim = fonte.lastIndexOf('})();');
    const exposto = 'window.__voz = {ouvirResposta, vozParar, ditarPeloMicrofone, vozModoLigado, vozEstado, enviarDitado, vozLigarControles};\nwindow.__chamadoTeste = {chamado, chamadoVad, chamadoVadNovo, chamadoComando, chamadoRotulo, chamadoEhEco, chamadoPalavras, sethRascunhoDe, sethChaveRascunho, CHAMADO_LIMIAR_FALA, CHAMADO_LIMIAR_INTERRUPCAO, CHAMADO_INTERRUPCAO_MS, CHAMADO_SILENCIO_MS, CHAMADO_VOZ_MIN_MS, CHAMADO_POS_FALA_MS, CHAMADO_PASSO_MS, DITADO_MAX_MS};\n';
    vm.createContext(ctx);
    vm.runInContext(fonte.slice(0, fim) + exposto + fonte.slice(fim), ctx, {filename: 'prototipo.js'});
  } catch (e) { console.log(JSON.stringify({erro: 'carga: ' + e.message})); return; }
  for (const f of cargas) { try { f(); } catch (e) { /* carga de outras seções: fora do teste */ } }
  await esperar();
  const resultados = []; const estados = [];
  for (const passo of cen.passos || []) {
    if (passo.js !== undefined) {
      try { resultados.push(await vm.runInContext(passo.js, ctx)); } catch (e) { resultados.push({erro: String((e && e.message) || e)}); }
    }
    await esperar();
    estados.push(ctx.__estado());
  }
  console.log(JSON.stringify({resultados, estados, chamadas, gravacoes, armazenamento, microfone,
    gravadores: gravadores.map((g) => ({estado: g.estado, opc: g.opc, mimeType: g.mimeType})),
    timers: timers.map((t) => ({ms: t.ms, cancelado: t.cancelado})), final: ctx.__estado(), contarOuvir: ctx.__contarOuvir(), intervalos: intervalos.map((i) => ({ms: i.ms, ativo: i.ativo})), fontes: fontes.map((f) => ({tocando: f.tocando, acabou: f.acabou}))}));
})();
"""


def rodar(passos, **cenario):
    """Roda os passos no prototipo.js e devolve o que o harness mediu. Cada passo é {'js': '...'}."""
    cen = dict(cenario, passos=passos)
    ambiente = dict(os.environ, PAINEL_DIR=str(HERE))
    saida = subprocess.run(["node", "-e", NODE_VOZ], input=json.dumps(cen, ensure_ascii=False),
                           capture_output=True, text=True, timeout=120, env=ambiente)
    linhas = saida.stdout.strip().splitlines()
    if saida.returncode != 0 or not linhas:
        raise AssertionError("node não rodou (não medido): " + saida.stderr[-400:])
    medido = json.loads(linhas[-1])
    if "erro" in medido:
        raise AssertionError("prototipo.js não carregou: " + medido["erro"])
    return medido


def posts(medido, url):
    return [c for c in medido["chamadas"] if c["url"] == url and c["metodo"] == "POST"]


class VozUiTests(unittest.TestCase):
    def test_ouvir_aparece_so_nas_respostas_da_seth(self):
        m = rodar([{"js": "__enviar('Oi, Seth.')"}])
        self.assertEqual(m["contarOuvir"], 1)
        self.assertEqual(len(posts(m, "/api/seth/chat/stream")), 1)

    def test_ouvir_manda_o_texto_da_resposta_e_mostra_falei(self):
        m = rodar([
            {"js": "__enviar('Oi.')"},
            {"js": "__ouvir(0)"},
        ], respostas={"/api/seth/ouvir": [{"json": {"schema_version": 1, "falou": True, "completo": True, "codigo": "completo",
                                                      "trechos_falados": 2, "trechos": 2, "motivo": "falei a resposta inteira em 2 trechos"}}]})
        pedido = posts(m, "/api/seth/ouvir")
        self.assertEqual(len(pedido), 1)
        self.assertEqual(json.loads(pedido[0]["corpo"]), {"texto": "Resposta da Seth."})
        self.assertEqual(m["final"]["voz"], "falei a resposta inteira em 2 trechos")
        self.assertEqual(m["final"]["classe"], "seth-voz-estado ok")
        self.assertFalse(m["final"]["pararVisivel"])

    def test_ouvir_mostra_nao_falei_com_o_motivo_do_painel(self):
        motivo = "NÃO falei: a voz do sistema não respondeu, ou carregou outro modelo. Não falo com outra voz."
        m = rodar([{"js": "__enviar('Oi.')"}, {"js": "__ouvir(0)"}],
                  respostas={"/api/seth/ouvir": [{"json": {"falou": False, "completo": False, "codigo": "voz", "motivo": motivo,
                                                             "trechos_falados": 0, "trechos": 1}}]})
        self.assertEqual(m["final"]["voz"], motivo)
        self.assertEqual(m["final"]["classe"], "seth-voz-estado erro")

    def test_ouvir_com_leitura_em_curso_nao_interrompe_e_avisa(self):
        m = rodar([
            {"js": "__enviar('Oi.')"},
            {"js": "__ouvir(0)"},
            {"js": "__ouvir(0)"},
        ], respostas={"/api/seth/ouvir": [{"pendente": True}]})
        self.assertEqual(len(posts(m, "/api/seth/ouvir")), 1, "o segundo Ouvir não pode ir ao painel")
        self.assertEqual(m["final"]["voz"], "Já estou lendo em voz alta. Use Parar voz antes.")
        self.assertTrue(m["final"]["pararVisivel"])

    def test_modo_conversa_vem_desligado_e_a_preferencia_fica_guardada(self):
        m = rodar([{"js": "__estado().modo"}, {"js": "__mudar('seth-modo-conversa', true)"}, {"js": "__mudar('seth-modo-conversa', false)"}])
        self.assertIs(m["resultados"][0], False)
        guardado = [g for g in m["gravacoes"] if g[0] == "agata-modo-conversa"]
        self.assertEqual(guardado, [["agata-modo-conversa", "1"], ["agata-modo-conversa", "0"]])

    def test_modo_conversa_sem_localstorage_nao_quebra_a_pagina(self):
        m = rodar([{"js": "__mudar('seth-modo-conversa', true)"}, {"js": "__enviar('Oi.')"}],
                  storage={"lerErro": True, "gravarErro": True})
        self.assertFalse([r for r in m["resultados"] if isinstance(r, dict) and "erro" in r])
        self.assertIsNone(next((c for c in m["chamadas"] if c["url"] == "/api/seth/ouvir"), None))

    def test_modo_conversa_ligado_le_a_resposta_concluida_sem_clicar(self):
        m = rodar([{"js": "__enviar('Oi.')"}],
                  storage={"inicial": {"agata-modo-conversa": "1"}},
                  respostas={"/api/seth/ouvir": [{"json": {"falou": True, "motivo": "falei a resposta inteira"}}]})
        self.assertTrue(m["estados"][0]["modo"])
        pedido = posts(m, "/api/seth/ouvir")
        self.assertEqual(len(pedido), 1)
        self.assertEqual(json.loads(pedido[0]["corpo"]), {"texto": "Resposta da Seth."})

    def test_modo_conversa_desligado_nao_le_sozinho(self):
        m = rodar([{"js": "__enviar('Oi.')"}])
        self.assertEqual(posts(m, "/api/seth/ouvir"), [])

    def test_esc_interrompe_a_leitura_em_curso(self):
        m = rodar([
            {"js": "__enviar('Oi.')"},
            {"js": "__ouvir(0)"},
            {"js": "__tecla('Escape')"},
        ], respostas={"/api/seth/ouvir": [{"pendente": True}], "/api/seth/ouvir/parar": [{"json": {"falando": True}}]})
        self.assertEqual(len(posts(m, "/api/seth/ouvir/parar")), 1)
        self.assertTrue(m["final"]["voz"].startswith("Parando"))

    def test_parar_voz_e_esc_sem_leitura_nao_chamam_o_painel(self):
        m = rodar([{"js": "__clicar('seth-voz-parar')"}, {"js": "__tecla('Escape')"}])
        self.assertEqual(posts(m, "/api/seth/ouvir/parar"), [])

    def test_modo_conversa_com_resposta_nova_para_a_leitura_e_le_a_mais_nova_depois(self):
        m = rodar([
            {"js": "__enviar('Primeira.')"},
            {"js": "__enviar('Segunda.')"},
            {"js": "__resolverPendentes({falou: true, motivo: 'falei a primeira'})"},
        ], storage={"inicial": {"agata-modo-conversa": "1"}},
           respostas={"/api/seth/chat/stream": [{"sse": 'data: {"tipo": "texto", "delta": "Resposta um."}\n\ndata: {"tipo": "fim"}\n\n'},
                                                 {"sse": 'data: {"tipo": "texto", "delta": "Resposta dois."}\n\ndata: {"tipo": "fim"}\n\n'}],
                      "/api/seth/ouvir": [{"pendente": True}, {"json": {"falou": True, "motivo": "falei a segunda"}}]})
        pedidos = [json.loads(c["corpo"])["texto"] for c in posts(m, "/api/seth/ouvir")]
        self.assertEqual(pedidos, ["Resposta um.", "Resposta dois."])
        self.assertEqual(len(posts(m, "/api/seth/ouvir/parar")), 1, "a leitura anterior foi parada antes da nova")

    def test_ditado_grava_e_poe_o_texto_no_campo_sem_enviar_a_seth(self):
        m = rodar([
            {"js": "__clicar('seth-ditado')"},
            {"js": "__clicar('seth-ditado')"},
        ], respostas={"/api/seth/ditado": [{"json": {"schema_version": 1, "texto": "olá, Seth"}}]})
        self.assertEqual(m["microfone"]["pedidos"], [{"audio": True}])
        self.assertEqual(m["gravadores"][0]["mimeType"], "audio/webm;codecs=opus")
        self.assertEqual(m["gravadores"][0]["estado"], "inactive")
        self.assertEqual(m["estados"][0]["pressionado"], "true")
        self.assertEqual(m["estados"][0]["ditado"], "Parar gravação")
        envio = posts(m, "/api/seth/ditado")
        self.assertEqual(len(envio), 1)
        self.assertTrue(envio[0]["corpo"]["blob"])
        self.assertEqual(envio[0]["corpo"]["tipo"], "audio/webm;codecs=opus")
        self.assertEqual(m["final"]["campo"], "olá, Seth")
        self.assertEqual(m["final"]["pressionado"], "false")
        self.assertEqual(m["final"]["ditado"], "Ditar")
        self.assertEqual(posts(m, "/api/seth/chat/stream"), [], "o ditado não envia a mensagem sozinho")
        self.assertEqual(m["microfone"]["parados"], 1, "as faixas do microfone são fechadas ao parar")

    def test_ditado_acrescenta_ao_texto_que_ja_estava_no_campo(self):
        m = rodar([
            {"js": "__campo('Oi,')"},
            {"js": "__clicar('seth-ditado')"},
            {"js": "__clicar('seth-ditado')"},
        ], respostas={"/api/seth/ditado": [{"json": {"texto": "tudo bem?"}}]})
        self.assertEqual(m["final"]["campo"], "Oi, tudo bem?")

    def test_permissao_do_microfone_negada_tem_mensagem_clara(self):
        m = rodar([{"js": "__clicar('seth-ditado')"}], microfone={"negar": True})
        self.assertEqual(m["gravadores"], [])
        self.assertIn("Permissão do microfone negada", m["final"]["voz"])
        self.assertEqual(m["final"]["classe"], "seth-voz-estado erro")

    def test_navegador_sem_gravacao_diz_que_nao_grava(self):
        m = rodar([{"js": "__clicar('seth-ditado')"}], semMicrofone=True, semGravador=True)
        self.assertIn("Este navegador não grava áudio aqui", m["final"]["voz"])
        self.assertEqual(m["gravadores"], [])

    def test_limite_de_60_segundos_para_a_gravacao_sozinha(self):
        m = rodar([
            {"js": "__clicar('seth-ditado')"},
            {"js": "__disparar(60000)"},
        ], respostas={"/api/seth/ditado": [{"json": {"texto": "fim da fala"}}]})
        self.assertEqual(m["gravadores"][0]["estado"], "inactive")
        self.assertEqual(len(posts(m, "/api/seth/ditado")), 1)
        self.assertEqual(m["final"]["campo"], "fim da fala")

    def test_ditado_grande_demais_nao_vai_ao_painel(self):
        m = rodar([
            {"js": "__clicar('seth-ditado')"},
            {"js": "__clicar('seth-ditado')"},
        ], tamanhoAudio=2 * 1024 * 1024 + 1)
        self.assertEqual(posts(m, "/api/seth/ditado"), [])
        self.assertIn("Gravação grande demais", m["final"]["voz"])

    def test_ditado_sem_ouvido_mostra_o_erro_e_nao_mexe_no_campo(self):
        m = rodar([
            {"js": "__campo('Oi,')"},
            {"js": "__clicar('seth-ditado')"},
            {"js": "__clicar('seth-ditado')"},
        ], respostas={"/api/seth/ditado": [{"status": 503, "json": {"erro": "o ouvido local não tem motor no ar: nada foi transcrito."}}]})
        self.assertEqual(m["final"]["campo"], "Oi,")
        self.assertEqual(m["final"]["voz"], "o ouvido local não tem motor no ar: nada foi transcrito.")
        self.assertFalse(m["final"]["ditadoDesabilitado"])

    def test_resposta_do_painel_sem_texto_nao_entra_no_campo(self):
        m = rodar([
            {"js": "__clicar('seth-ditado')"},
            {"js": "__clicar('seth-ditado')"},
        ], respostas={"/api/seth/ditado": [{"json": {"schema_version": 1}}]})
        self.assertEqual(m["final"]["campo"], "")
        self.assertIn("Não veio texto", m["final"]["voz"])


LIGAR = [{"js": "__clicar('seth-chamado')"}]
# Um trecho do Humano: voz por ~500 ms e silêncio de 1300 ms. Começa a gravar no primeiro tick e encerra no silêncio.
TRECHO = [{"js": "__nivel(0.1)"}, {"js": "__avanca(50)"}, {"js": "__tick()"}, {"js": "__avanca(500)"}, {"js": "__tick()"},
          {"js": "__nivel(0)"}, {"js": "__avanca(1300)"}, {"js": "__tick()"}]
RESPOSTA = 'data: {"tipo": "texto", "delta": "Resposta da Seth."}\n\ndata: {"tipo": "fim"}\n\n'
WAV = {"wav": True, "cabecalhos": {"x-trechos": "1"}}
MENSAGEM_NAO_FALEI = "NÃO falei: a voz do sistema não respondeu, ou carregou outro modelo. Não falo com outra voz."


class ChamadoVozTests(unittest.TestCase):
    """Conversa por voz (23/11/2026): liga, ouve, grava o trecho, manda à Seth, toca a resposta no navegador, interrompe
    pela voz (barge-in), Esc e comandos. O microfone e o áudio são simulados: o nível é um número que o teste escreve e o
    relógio só anda quando o teste manda. Nenhum microfone real, nenhum som, nenhuma rede."""

    def test_botao_liga_com_cancelamento_de_eco_e_mostra_ouvindo(self):
        m = rodar(LIGAR)
        self.assertEqual(m["microfone"]["pedidos"], [{"audio": {"echoCancellation": True, "noiseSuppression": True}}])
        self.assertEqual(m["final"]["chamadoBotao"], "Parar conversa por voz")
        self.assertEqual(m["final"]["chamadoAria"], "true")
        self.assertEqual(m["final"]["chamadoTexto"], "Ouvindo…")
        self.assertFalse(m["final"]["chamadoOculta"])
        self.assertEqual([t for t in m["timers"] if t["ms"] == 50 and not t["cancelado"]], [{"ms": 50, "cancelado": False}], "o microfone é lido a cada 50 ms, por um temporizador que se reagenda")

    def test_botao_desliga_para_o_microfone_e_o_passo(self):
        m = rodar(LIGAR + [{"js": "__clicar('seth-chamado')"}])
        self.assertEqual(m["final"]["chamadoBotao"], "Conversa por voz")
        self.assertTrue(m["final"]["chamadoOculta"])
        self.assertGreaterEqual(m["microfone"]["parados"], 1)
        self.assertEqual([t for t in m["timers"] if t["ms"] == 50 and not t["cancelado"]], [], "desligar cancela o passo pendente")

    def test_permissao_do_microfone_negada_nao_liga(self):
        m = rodar([{"js": "__clicar('seth-chamado')"}], microfone={"negar": True})
        self.assertEqual(m["final"]["chamadoBotao"], "Conversa por voz")
        self.assertIn("Permissão do microfone negada", m["final"]["voz"])
        self.assertEqual(m["gravadores"], [])

    def test_voz_curta_e_descartada_e_nao_vai_ao_painel(self):
        m = rodar(LIGAR + [{"js": "__nivel(0.1)"}, {"js": "__avanca(50)"}, {"js": "__tick()"}, {"js": "__avanca(100)"}, {"js": "__tick()"},
                           {"js": "__nivel(0)"}, {"js": "__avanca(1300)"}, {"js": "__tick()"}])
        self.assertEqual(posts(m, "/api/seth/ditado"), [], "menos de 0,4 s de voz não vai à transcrição")
        self.assertEqual(m["gravadores"][0]["estado"], "inactive")
        self.assertEqual(m["final"]["chamadoTexto"], "Ouvindo…")

    def test_trecho_com_voz_e_transcrito_e_enviado_a_seth_e_a_resposta_e_tocada_no_navegador(self):
        m = rodar(LIGAR + TRECHO + [{"js": "__terminarTrecho()"}],
                  respostas={"/api/seth/ditado": [{"json": {"schema_version": 1, "texto": "olá, Seth"}}],
                             "/api/seth/chat/stream": [{"sse": RESPOSTA}],
                             "/api/seth/voz-audio": [WAV]})
        self.assertEqual(len(posts(m, "/api/seth/ditado")), 1)
        envio = posts(m, "/api/seth/chat/stream")
        self.assertEqual(len(envio), 1, "o texto segue pelo caminho do Enviar")
        self.assertIn("olá, Seth", envio[0]["corpo"])
        pedido = posts(m, "/api/seth/voz-audio")
        self.assertEqual(json.loads(pedido[0]["corpo"]), {"texto": "Resposta da Seth.", "trecho": 0})
        self.assertEqual(posts(m, "/api/seth/ouvir"), [], "a fala do navegador não usa a rota que fala na Máquina")
        self.assertEqual(m["estados"][len(LIGAR + TRECHO) - 1]["chamadoTexto"], "Seth falando…")
        self.assertEqual(m["fontes"], [{"tocando": True, "acabou": True}])
        self.assertEqual(m["final"]["chamadoTexto"], "Ouvindo…", "terminada a fala, volta a ouvir sozinha")
        self.assertEqual(m["final"]["campo"], "", "o rascunho do campo não é mexido pela voz")

    def test_voz_normal_nao_interrompe_a_fala(self):
        m = rodar(LIGAR + TRECHO + [{"js": "__nivel(0.05)"}, {"js": "__avanca(2000)"}, {"js": "__tick()"}],
                  respostas={"/api/seth/ditado": [{"json": {"texto": "olá, Seth"}}],
                             "/api/seth/chat/stream": [{"sse": RESPOSTA}], "/api/seth/voz-audio": [WAV]})
        self.assertEqual(m["final"]["chamadoTexto"], "Seth falando…", "0,05 está abaixo do limiar de interrupção")
        self.assertEqual(len(m["gravadores"]), 1, "com a fala tocando, o microfone não grava outro trecho")

    def test_barge_in_para_a_fala_na_hora_e_grava_o_turno_do_humano(self):
        base = len(LIGAR + TRECHO)
        interromper = [{"js": "__nivel(0.5)"}, {"js": "__avanca(0)"}, {"js": "__tick()"},
                       {"js": "__avanca(300)"}, {"js": "__tick()"},
                       {"js": "__avanca(200)"}, {"js": "__tick()"},
                       {"js": "__nivel(0)"}, {"js": "__avanca(1300)"}, {"js": "__tick()"}]
        m = rodar(LIGAR + TRECHO + interromper,
                  respostas={"/api/seth/ditado": [{"json": {"texto": "pera ou maçã"}}],
                             "/api/seth/chat/stream": [{"sse": RESPOSTA}], "/api/seth/voz-audio": [WAV]})
        self.assertEqual(m["estados"][base + 4]["chamadoTexto"], "Ouvindo… Fala interrompida pela sua voz.")
        self.assertTrue(m["fontes"][0]["acabou"], "o áudio parou na hora")
        self.assertEqual(len(posts(m, "/api/seth/ditado")), 2, "o turno do Humano foi gravado e transcrito")
        self.assertEqual(len(posts(m, "/api/seth/chat/stream")), 2, "e enviado à Seth")

    def test_esc_com_fala_no_navegador_para_e_volta_a_ouvir_e_o_segundo_desliga(self):
        base = len(LIGAR + TRECHO)
        m = rodar(LIGAR + TRECHO + [{"js": "__tecla('Escape')"}, {"js": "__tecla('Escape')"}],
                  respostas={"/api/seth/ditado": [{"json": {"texto": "oi"}}],
                             "/api/seth/chat/stream": [{"sse": RESPOSTA}], "/api/seth/voz-audio": [WAV]})
        self.assertEqual(m["estados"][base]["chamadoTexto"], "Ouvindo… Fala interrompida.")
        self.assertTrue(m["fontes"][0]["acabou"])
        self.assertEqual(m["estados"][base + 1]["chamadoBotao"], "Conversa por voz")
        self.assertEqual(m["final"]["chamadoBotao"], "Conversa por voz")

    def test_ouvir_com_a_fala_do_navegador_tocando_para_a_fala_antes_de_comecar_a_outra(self):
        m = rodar(LIGAR + TRECHO + [{"js": "__ouvir(0)"}],
                  respostas={"/api/seth/ditado": [{"json": {"texto": "oi"}}], "/api/seth/chat/stream": [{"sse": RESPOSTA}],
                             "/api/seth/voz-audio": [WAV], "/api/seth/ouvir": [{"json": {"falou": True, "motivo": "falei a resposta inteira"}}]})
        self.assertEqual(m["fontes"], [{"tocando": True, "acabou": True}], "o áudio do navegador não toca junto com a leitura da Máquina")
        self.assertEqual(len(posts(m, "/api/seth/ouvir")), 1)

    def test_esc_com_a_seth_pensando_interrompe_a_resposta_e_volta_a_ouvir(self):
        m = rodar(LIGAR + [{"js": "__enviar('Oi.')"}, {"js": "__tecla('Escape')"}, {"js": "__tecla('Escape')"}],
                  respostas={"/api/seth/chat/stream": [{"travado": True}]})
        self.assertEqual(m["estados"][1]["chamadoTexto"], "Seth pensando…")
        self.assertEqual(m["estados"][2]["chamadoTexto"], "Ouvindo… Resposta interrompida.")
        self.assertEqual(m["estados"][3]["chamadoBotao"], "Conversa por voz")

    def test_fale_comigo_liga_sem_virar_mensagem(self):
        m = rodar([{"js": "__enviar('Fale comigo.')"}])
        self.assertEqual(m["final"]["chamadoBotao"], "Parar conversa por voz")
        self.assertEqual(posts(m, "/api/seth/chat/stream"), [], "o comando não é mensagem para a Seth")
        self.assertEqual(m["final"]["campo"], "")

    def test_encerrar_chamado_desliga_sem_virar_mensagem(self):
        m = rodar(LIGAR + [{"js": "__enviar('encerrar chamado')"}])
        self.assertEqual(m["final"]["chamadoBotao"], "Conversa por voz")
        self.assertEqual(posts(m, "/api/seth/chat/stream"), [])

    def test_ditar_com_a_conversa_ligada_e_recusado(self):
        m = rodar(LIGAR + [{"js": "__clicar('seth-ditado')"}])
        self.assertEqual(len(m["microfone"]["pedidos"]), 1, "o ditado não abre um segundo microfone")
        self.assertIn("A conversa por voz já está ouvindo o microfone", m["final"]["voz"])

    def test_ditado_com_erro_do_ouvido_volta_a_ouvir_com_o_motivo(self):
        m = rodar(LIGAR + TRECHO,
                  respostas={"/api/seth/ditado": [{"status": 503, "json": {"erro": "o ouvido local não tem motor no ar: nada foi transcrito."}}]})
        self.assertEqual(m["final"]["chamadoTexto"], "Ouvindo… o ouvido local não tem motor no ar: nada foi transcrito.")
        self.assertEqual(posts(m, "/api/seth/chat/stream"), [])

    def test_desligar_durante_a_transcricao_descarta_o_texto_que_chegar_depois(self):
        m = rodar(LIGAR + TRECHO + [{"js": "__clicar('seth-chamado')"}, {"js": "__resolverPendentes({schema_version: 1, texto: 'fala tardia'})"}],
                  respostas={"/api/seth/ditado": [{"pendente": True}]})
        self.assertEqual(m["final"]["chamadoBotao"], "Conversa por voz")
        self.assertEqual(posts(m, "/api/seth/chat/stream"), [], "depois de desligar, a fala não vai à Seth")

    def test_sintese_que_falha_no_primeiro_trecho_cai_na_fala_pela_maquina_com_aviso(self):
        m = rodar(LIGAR + TRECHO,
                  respostas={"/api/seth/ditado": [{"json": {"texto": "oi"}}], "/api/seth/chat/stream": [{"sse": RESPOSTA}],
                             "/api/seth/voz-audio": [{"status": 503, "json": {"erro": MENSAGEM_NAO_FALEI}}]})
        self.assertEqual(json.loads(posts(m, "/api/seth/ouvir")[0]["corpo"]), {"texto": "Resposta da Seth."})
        self.assertEqual(m["final"]["voz"], "A voz do navegador falhou: falo pela Máquina, sem interromper pela voz.")
        self.assertEqual(m["final"]["classe"], "seth-voz-estado erro")
        self.assertEqual(m["gravadores"][0]["estado"], "inactive")

    def test_fala_pela_maquina_nao_escuta_e_esc_pede_a_parada_e_o_segundo_desliga(self):
        m = rodar(LIGAR + TRECHO + [{"js": "__nivel(0.5)"}, {"js": "__avanca(500)"}, {"js": "__tick()"},
                                    {"js": "__tecla('Escape')"}, {"js": "__tecla('Escape')"}],
                  respostas={"/api/seth/ditado": [{"json": {"texto": "oi"}}], "/api/seth/chat/stream": [{"sse": RESPOSTA}],
                             "/api/seth/voz-audio": [{"status": 503, "json": {"erro": MENSAGEM_NAO_FALEI}}],
                             "/api/seth/ouvir": [{"pendente": True}], "/api/seth/ouvir/parar": [{"json": {"falando": True}}]})
        self.assertEqual(len(m["gravadores"]), 1, "com a fala pela Máquina, o microfone não grava (meia-duplex)")
        # O primeiro Esc pede a parada (vale entre trechos); o segundo desliga e também pede, para a Máquina calar.
        self.assertEqual(len(posts(m, "/api/seth/ouvir/parar")), 2)
        self.assertEqual(m["estados"][len(LIGAR + TRECHO) + 3]["chamadoTexto"], "Parando a fala…")
        self.assertEqual(m["final"]["chamadoBotao"], "Conversa por voz")

    def test_sintese_que_falha_no_meio_nao_repete_o_que_ja_foi_falado(self):
        m = rodar(LIGAR + TRECHO + [{"js": "__terminarTrecho()"}],
                  respostas={"/api/seth/ditado": [{"json": {"texto": "oi"}}], "/api/seth/chat/stream": [{"sse": RESPOSTA}],
                             "/api/seth/voz-audio": [{"wav": True, "cabecalhos": {"x-trechos": "2"}}, {"status": 503, "json": {"erro": MENSAGEM_NAO_FALEI}}]})
        self.assertEqual(posts(m, "/api/seth/ouvir"), [])
        self.assertTrue(m["final"]["chamadoTexto"].endswith("A voz falhou no meio da fala: o resto não foi falado."))

    def test_vad_encerra_so_depois_de_1200_ms_de_silencio(self):
        m = rodar([{"js": """(() => { const T = __chamadoTeste; const v = T.chamadoVadNovo(); const saida = [];
          for (const [t, n] of [[0, 0.5], [500, 0.5], [1000, 0], [1199, 0], [1700, 0]]) saida.push(T.chamadoVad(v, n, t)); return saida; })()"""}])
        self.assertEqual(m["resultados"][0], ["iniciar", "", "", "", "encerrar"])

    def test_vad_descarta_voz_curta_e_corta_trecho_longo_no_limite(self):
        m = rodar([{"js": """(() => { const T = __chamadoTeste; const curto = T.chamadoVadNovo(); const longo = T.chamadoVadNovo();
          const a = [[0, 0.5], [100, 0], [1300, 0]].map(([t, n]) => T.chamadoVad(curto, n, t));
          const b = [[0, 0.5], [30000, 0.5], [59999, 0.5], [60000, 0.5]].map(([t, n]) => T.chamadoVad(longo, n, t));
          return [a, b]; })()"""}])
        self.assertEqual(m["resultados"][0], [["iniciar", "", "descartar"], ["iniciar", "", "", "encerrar"]])

    def test_comandos_sem_distincao_de_maiusculas_nem_pontuacao(self):
        m = rodar([{"js": """(() => { const T = __chamadoTeste; const casos = [["Fale comigo.", "ligar"], ["  ENCERRAR CHAMADO ", "desligar"],
          ["volte ao texto!", "desligar"], ["fale com ela", ""], ["constructor", ""], ["", ""]];
          return casos.map(([t, esperado]) => [T.chamadoComando(t), esperado]); })()"""}])
        for obtido, esperado in m["resultados"][0]:
            self.assertEqual(obtido, esperado)

    def test_rotulos_dos_estados_em_portugues(self):
        m = rodar([{"js": """(() => { const T = __chamadoTeste; return [T.chamadoRotulo("falando", false), T.chamadoRotulo("falando", true),
          T.chamadoRotulo("transcrevendo", false), T.chamadoRotulo("pensando", false), T.chamadoRotulo("ouvindo", false),
          T.chamadoRotulo("abrindo", false)]; })()"""}])
        self.assertEqual(m["resultados"][0], ["Seth falando…", "Parando a fala…", "Transcrevendo…", "Seth pensando…", "Ouvindo…", "Abrindo o microfone…"])

    def test_constantes_nomeadas_do_detector(self):
        m = rodar([{"js": """(() => { const T = __chamadoTeste; return {limiar: T.CHAMADO_LIMIAR_FALA, interrupcao: T.CHAMADO_LIMIAR_INTERRUPCAO,
          interrupcaoMs: T.CHAMADO_INTERRUPCAO_MS, silencio: T.CHAMADO_SILENCIO_MS, vozMin: T.CHAMADO_VOZ_MIN_MS,
          posFala: T.CHAMADO_POS_FALA_MS, passo: T.CHAMADO_PASSO_MS, maximo: T.DITADO_MAX_MS}; })()"""}])
        c = m["resultados"][0]
        self.assertEqual((c["silencio"], c["vozMin"], c["interrupcaoMs"], c["passo"], c["maximo"]), (1200, 400, 300, 50, 60000))
        self.assertLess(c["limiar"], c["interrupcao"], "a interrupção pela voz exige nível mais alto que o de fala normal")


class VozEstaticaTests(unittest.TestCase):
    """Conferências de texto: o que entrou é texto, não HTML; a CSP segue igual; classes e emoji."""

    BLOCO_JS = JS[JS.index("// Voz da Seth (11/11/2026"):JS.index("function ligarConversaSeth() {")]
    BARRA_HTML = HTML[HTML.index('<div class="seth-voz" id="seth-voz">'):HTML.index('</div>', HTML.index('<div class="seth-voz" id="seth-voz">')) + 6]
    BOTAO_DITAR = HTML[HTML.index('<button class="btn secondary seth-ditar"'):HTML.index('</button>', HTML.index('<button class="btn secondary seth-ditar"')) + 9]

    def test_bloco_de_voz_so_grava_texto_por_textcontent(self):
        for proibido in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("):
            self.assertNotIn(proibido, self.BLOCO_JS, proibido)
        self.assertIn("textContent", self.BLOCO_JS)

    def test_html_novo_sem_atributo_inline_nem_script(self):
        for trecho in (self.BARRA_HTML, self.BOTAO_DITAR):
            self.assertIsNone(re.search(r"\son[a-z]+=", trecho), trecho)
            self.assertNotIn("style=", trecho)
            self.assertNotIn("<script", trecho)

    def test_classes_novas_tem_regra_de_estilo(self):
        for classe in ("seth-voz", "seth-voz-modo", "seth-voz-estado", "seth-ditar", "seth-chamar"):
            self.assertRegex(CSS, r"\." + classe + r"[\s.{:\[]", classe)

    def test_sem_emoji_nas_linhas_novas(self):
        novo = self.BLOCO_JS + self.BARRA_HTML + self.BOTAO_DITAR
        self.assertIsNone(EMOJI.search(novo))
        self.assertIsNone(EMOJI.search(CSS[CSS.index("/* Voz da Seth (11/11/2026)"):CSS.index(".seth-voz-estado.ok")]))

    def test_csp_do_painel_segue_igual_e_sem_media_src(self):
        """A fala sai pelo player da Máquina, não pelo navegador: a CSP não precisa de media-src. Conferido no código."""
        self.assertIn("default-src 'none'; script-src 'self'; style-src 'self'; frame-src 'self'; ", SERVIDOR)
        self.assertIn("connect-src 'self'; img-src 'self'; base-uri 'none'; ", SERVIDOR)
        self.assertNotIn("media-src", SERVIDOR)

    def test_preferencia_do_modo_fica_fora_do_bloco_da_conversa(self):
        """A regra do bloco da Conversa (sem localStorage) vale para o histórico. A preferência sim/não fica fora dele."""
        inicio = JS.index("/* (27/10/2026) Conversa com a Seth")
        fim = JS.index("/* (27/10/2026) Grafo do vault", inicio)
        bloco = JS[inicio:fim]
        self.assertIn("function vozModoLigado()", JS)
        self.assertNotIn("function vozModoLigado()", bloco)
        self.assertNotIn("function vozGuardarModo(", bloco)
        self.assertIn("vozModoLigado()", bloco, "quem usa a preferência continua no bloco da Conversa")

    def test_modo_conversa_e_ditado_ligados_so_pela_pagina_da_conversa(self):
        self.assertIn('id="seth-modo-conversa"', HTML)
        self.assertIn('id="seth-ditado"', HTML)
        self.assertIn('vozLigarControles();', JS)
        self.assertEqual(JS.count('vozParar();'), 1, "o Esc chama vozParar() direto; o botão Parar voz a recebe como ouvinte")


class ChamadoVozRevisaoTests(unittest.TestCase):
    """Correções da revisão independente (23/11/2026): anexo pendente, eco, pausa por turnos, prazos, cauda de 800 ms,
    AudioContext que não roda, 413 próprio, comandos digitados e falados, fronteira do detector e dois trechos."""

    TURNO = TRECHO + [{"js": "__terminarTrecho()"}, {"js": "__avanca(500)"}]
    RESPOSTA_LONGA = 'data: {"tipo": "texto", "delta": "A resposta da Seth explica o que aconteceu."}\n\ndata: {"tipo": "fim"}\n\n'

    def test_anexo_pendente_nao_vai_pela_voz_e_o_texto_fica_no_campo(self):
        anexo = {"js": "__chamadoTeste.sethRascunhoDe(__chamadoTeste.sethChaveRascunho()).anexos.push({nome: 'a.txt', texto: 'abc', caracteres: 3})"}
        m = rodar(LIGAR + [anexo] + TRECHO, respostas={"/api/seth/ditado": [{"json": {"texto": "olá, Seth"}}]})
        self.assertEqual(posts(m, "/api/seth/chat/stream"), [], "com anexo pendente a fala não é enviada")
        self.assertIn("Há anexo pendente", m["final"]["chamadoTexto"])
        self.assertEqual(m["final"]["campo"], "olá, Seth")

    def test_prazos_de_ditado_e_sintese_com_sinal_de_aborto_e_desarmados_ao_fim(self):
        m = rodar(LIGAR + TRECHO + [{"js": "__terminarTrecho()"}],
                  respostas={"/api/seth/ditado": [{"json": {"texto": "olá, Seth"}}], "/api/seth/chat/stream": [{"sse": RESPOSTA}],
                             "/api/seth/voz-audio": [WAV]})
        ditado = [c for c in m["chamadas"] if c["url"] == "/api/seth/ditado"]
        voz = [c for c in m["chamadas"] if c["url"] == "/api/seth/voz-audio"]
        self.assertTrue(ditado[0]["temSinal"])
        self.assertTrue(voz[0]["temSinal"])
        prazos = [t for t in m["timers"] if t["ms"] in (130000, 60000)]
        self.assertEqual(sorted(t["ms"] for t in prazos), [60000, 130000])
        self.assertTrue(all(t["cancelado"] for t in prazos), "o prazo é desarmado quando o pedido termina")

    def test_eco_pura_compara_a_fracao_das_palavras_sem_pontuacao(self):
        m = rodar([{"js": """(() => { const T = __chamadoTeste; const fala = "A resposta da Seth explica o que aconteceu hoje.";
          return [T.chamadoEhEco("A resposta da Seth explica o que", fala), T.chamadoEhEco("Resposta, da Seth! explica o que aconteceu.", fala),
                  T.chamadoEhEco("o que aconteceu", fala), T.chamadoEhEco("outra coisa", fala), T.chamadoEhEco("sim", "Sim."),
                  T.chamadoEhEco("a resposta da seth", "A resposta da Seth.")]; })()"""}])
        self.assertEqual(m["resultados"][0], [True, True, False, False, False, True])

    def test_eco_da_ultima_fala_tocada_e_descartado_e_nao_vai_a_seth(self):
        m = rodar(LIGAR + [{"js": "__enviar('Oi.')"}, {"js": "__terminarTrecho()"}, {"js": "__avanca(500)"}] + TRECHO,
                  respostas={"/api/seth/ditado": [{"json": {"texto": "a resposta da seth explica o que aconteceu"}}],
                             "/api/seth/chat/stream": [{"sse": self.RESPOSTA_LONGA}], "/api/seth/voz-audio": [WAV]})
        self.assertEqual(len(posts(m, "/api/seth/chat/stream")), 1, "só a mensagem digitada foi à Seth")
        self.assertTrue(m["final"]["chamadoTexto"].startswith("Ouvindo… Trecho descartado: parecia eco da resposta."))

    def test_depois_de_seis_turnos_sem_tecla_pausa_e_tecla_retoma(self):
        ditados = [{"json": {"texto": f"pergunta {n}"}} for n in ("um", "dois", "tres", "quatro", "cinco", "seis", "sete")]
        m = rodar(LIGAR + self.TURNO * 6 + TRECHO + [{"js": "__tecla('a')"}] + TRECHO,
                  respostas={"/api/seth/ditado": ditados, "/api/seth/chat/stream": [{"sse": RESPOSTA}], "/api/seth/voz-audio": [WAV]})
        indice_setimo = len(LIGAR) + 10 * 6 + 7  # silêncio do sétimo trecho
        self.assertIn("Conversa pausada: diga algo ou toque para continuar.", m["estados"][indice_setimo]["chamadoTexto"])
        self.assertEqual(m["final"]["campo"], "pergunta sete", "a fala pausada fica no campo: não se perde e não vai sozinha")
        self.assertEqual(len(posts(m, "/api/seth/chat/stream")), 7, "seis turnos foram à Seth, o sétimo ficou pausado, o oitavo (depois da tecla) foi")

    def test_fronteira_do_detector_400_ms_de_voz(self):
        m = rodar([{"js": """(() => { const T = __chamadoTeste; const abaixo = T.chamadoVadNovo(), exato = T.chamadoVadNovo();
          const a = [[0, 0.5], [399, 0.5], [1599, 0]].map(([t, n]) => T.chamadoVad(abaixo, n, t));
          const b = [[0, 0.5], [400, 0.5], [1599, 0], [1600, 0]].map(([t, n]) => T.chamadoVad(exato, n, t));
          return [a, b]; })()"""}])
        self.assertEqual(m["resultados"][0], [["iniciar", "", "descartar"], ["iniciar", "", "", "encerrar"]])

    def test_resposta_em_dois_trechos_toca_os_dois_e_volta_a_ouvir(self):
        m = rodar(LIGAR + TRECHO + [{"js": "__terminarTrecho()"}, {"js": "__terminarTrecho()"}],
                  respostas={"/api/seth/ditado": [{"json": {"texto": "oi"}}], "/api/seth/chat/stream": [{"sse": RESPOSTA}],
                             "/api/seth/voz-audio": [{"wav": True, "cabecalhos": {"x-trechos": "2"}}]})
        pedidos = [json.loads(c["corpo"])["trecho"] for c in posts(m, "/api/seth/voz-audio")]
        self.assertEqual(pedidos, [0, 1])
        self.assertEqual(len(m["fontes"]), 2)
        self.assertTrue(all(f["acabou"] for f in m["fontes"]))
        self.assertEqual(posts(m, "/api/seth/ouvir"), [], "com a síntese boa, nada cai na Máquina")
        self.assertEqual(m["final"]["chamadoTexto"], "Ouvindo…")

    def test_comando_falado_encerrar_desliga_e_nao_vai_a_seth(self):
        m = rodar(LIGAR + TRECHO, respostas={"/api/seth/ditado": [{"json": {"texto": "encerrar chamado"}}]})
        self.assertEqual(m["final"]["chamadoBotao"], "Conversa por voz")
        self.assertEqual(posts(m, "/api/seth/chat/stream"), [])

    def test_comando_falado_fale_comigo_com_a_conversa_ligada_nao_vai_a_seth(self):
        m = rodar(LIGAR + TRECHO, respostas={"/api/seth/ditado": [{"json": {"texto": "fale comigo"}}]})
        self.assertEqual(m["final"]["chamadoBotao"], "Parar conversa por voz")
        self.assertEqual(posts(m, "/api/seth/chat/stream"), [])
        self.assertEqual(m["final"]["chamadoTexto"], "Ouvindo… A conversa por voz já está ligada.")

    def test_comando_digitado_so_e_comando_quando_a_conversa_esta_ligada(self):
        for frase in ("encerrar chamado", "volte ao texto"):
            m = rodar([{"js": f"__enviar('{frase}')"}], respostas={"/api/seth/chat/stream": [{"sse": RESPOSTA}]})
            self.assertEqual(len(posts(m, "/api/seth/chat/stream")), 1, f"com a conversa desligada, '{frase}' vai à Seth")

    def test_audio_que_nao_roda_depois_do_resume_desliga_com_aviso(self):
        m = rodar(LIGAR, audio={"travado": True})
        self.assertEqual(m["final"]["chamadoBotao"], "Conversa por voz")
        self.assertIn("O navegador não deixou o áudio tocar", m["final"]["voz"])
        self.assertEqual([t for t in m["timers"] if t["ms"] == 50], [], "a leitura do microfone nem começa")
        self.assertGreaterEqual(m["microfone"]["parados"], 1)

    def test_resposta_longa_demais_para_a_sintese_diz_isso_e_nao_cai_na_maquina(self):
        m = rodar(LIGAR + TRECHO,
                  respostas={"/api/seth/ditado": [{"json": {"texto": "oi"}}], "/api/seth/chat/stream": [{"sse": RESPOSTA}],
                             "/api/seth/voz-audio": [{"status": 413, "json": {"erro": "resposta longa demais para falar. Peça um resumo."}}]})
        self.assertEqual(m["final"]["chamadoTexto"], "Ouvindo… Resposta longa demais para falar.")
        self.assertEqual(posts(m, "/api/seth/ouvir"), [])

    def test_cauda_depois_da_fala_pela_maquina_e_de_800_ms(self):
        m = rodar(LIGAR + TRECHO + [{"js": "__chamadoTeste.chamado.ignorarAte - __relogio()"}],
                  respostas={"/api/seth/ditado": [{"json": {"texto": "oi"}}], "/api/seth/chat/stream": [{"sse": RESPOSTA}],
                             "/api/seth/voz-audio": [{"status": 503, "json": {"erro": MENSAGEM_NAO_FALEI}}],
                             "/api/seth/ouvir": [{"json": {"falou": True, "motivo": "falei a resposta inteira"}}]})
        self.assertEqual(m["resultados"][-1], 800)


class ConversaPorVozEstaticaTests(unittest.TestCase):
    """Conferências de texto da conversa por voz: elementos, rota, áudio no navegador (sem elemento de mídia), CSP."""

    BLOCO_CHAMADO = JS[JS.index("// Conversa por voz (23/11/2026"):JS.index("/* Rascunho por conversa (C6)")]

    def test_elementos_do_chamado_existem_e_sao_de_texto(self):
        self.assertIn('id="seth-chamado"', HTML)
        self.assertIn('id="seth-chamado-estado"', HTML)
        self.assertIn('aria-pressed="false"', HTML[HTML.index('id="seth-chamado"') - 80:HTML.index('id="seth-chamado"') + 90])
        self.assertIn('hidden></p>', HTML[HTML.index('id="seth-chamado-estado"'):HTML.index('id="seth-chamado-estado"') + 120])
        self.assertIsNone(re.search(r"\son[a-z]+=", HTML[HTML.index('id="seth-chamado"') - 80:HTML.index('id="seth-chamado-estado"') + 120]))

    def test_constantes_e_funcoes_do_chamado_ficam_no_bloco_de_voz(self):
        for nome in ("const CHAMADO_LIMIAR_FALA", "const CHAMADO_LIMIAR_INTERRUPCAO", "const CHAMADO_SILENCIO_MS",
                     "function chamadoVad(", "function chamadoComando(", "async function chamadoLigar(", "function chamadoEsc(",
                     "function chamadoPasso("):
            self.assertIn(nome, self.BLOCO_CHAMADO, nome)

    def test_fala_do_chamado_toca_no_navegador_sem_elemento_de_audio_nem_url(self):
        """A fala sai pelo AudioContext (decodeAudioData + createBufferSource), que a CSP do painel não bloqueia.
        Nada de <audio>, Audio(), blob: ou media-src: o eco é cancelado pelo navegador só se o som sai dele."""
        self.assertIn("createBufferSource", self.BLOCO_CHAMADO)
        self.assertIn("decodeAudioData", self.BLOCO_CHAMADO)
        self.assertIn('"/api/seth/voz-audio"', self.BLOCO_CHAMADO)
        for proibido in ("new Audio(", "createObjectURL", "HTMLAudioElement", "media-src"):
            self.assertNotIn(proibido, self.BLOCO_CHAMADO + SERVIDOR, proibido)

    def test_microfone_pede_cancelamento_de_eco_e_supressao_de_ruido(self):
        self.assertIn("echoCancellation: true, noiseSuppression: true", self.BLOCO_CHAMADO)

    def test_esc_e_comandos_entram_no_mesmo_caminho_do_painel(self):
        self.assertEqual(JS.count("chamadoEsc();"), 1, "o Esc chama o chamado uma vez, no manipulador único")
        self.assertIn("else if (chamadoLigado()) chamadoEsc();", JS)
        self.assertIn("chamadoComando(texto)", JS)
        self.assertIn("chamadoLerResposta(conteudo)", JS)
        self.assertIn("chamadoFimResposta(conteudo !== null && alvo === sethAtual)", JS)

    def test_rota_nova_de_voz_fica_fora_da_fala_antiga(self):
        """O /api/seth/ouvir antigo continua falando na Máquina, e só o fallback do chamado chega a ele."""
        self.assertNotIn('"/api/seth/ouvir"', self.BLOCO_CHAMADO, "o bloco do chamado não chama a rota antiga direto")
        self.assertIn("ouvirResposta(texto, true)", self.BLOCO_CHAMADO)
        self.assertIn('self.path == "/api/seth/voz-audio"', SERVIDOR)

    def test_classe_chamar_tem_regra_de_estilo_e_estado_pressionado(self):
        self.assertRegex(CSS, r"\.seth-chamar\[aria-pressed=\"true\"\]")


if __name__ == "__main__":
    unittest.main()
