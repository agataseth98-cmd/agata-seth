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
const OCULTOS = ['atalhos-painel', 'seth-voz-parar', 'seth-parar'];
const INICIAIS = {'seth-ditado': {atributos: {'aria-pressed': 'false'}, texto: 'Ditar'}};
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
ctx.setInterval = () => 0; ctx.clearInterval = () => {};
ctx.addEventListener = (tipo, fn) => { if (tipo === 'load') cargas.push(fn); };
ctx.fetch = async (url, opcoes = {}) => {
  const metodo = String(opcoes.method || 'GET').toUpperCase();
  let corpo = null;
  if (typeof opcoes.body === 'string') corpo = opcoes.body;
  else if (opcoes.body && typeof opcoes.body.size === 'number') corpo = {blob: true, tamanho: opcoes.body.size, tipo: opcoes.body.type};
  chamadas.push({url, metodo, corpo, cabecalhos: opcoes.headers || null});
  if (url === '/api/seth/conversa' && metodo === 'POST') return respostaJson(200, {schema_version: 1, id: '0123456789ab', titulo: '', mensagens: []});
  if (url === '/api/seth/conversas') return respostaJson(200, {schema_version: 1, state: 'ok', items: [], pastas: [], marcadores: [], total: 0, organizacao: 'ok', ilegiveis: 0});
  if (url === '/api/seth/chat/stream') {
    const r = proxima(url) || {};
    return respostaStream(r.sse !== undefined ? r.sse : 'data: {"tipo": "texto", "delta": "Resposta da Seth."}\n\ndata: {"tipo": "fim"}\n\n');
  }
  const r = proxima(url);
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
ctx.__estado = () => {
  const v = documento.getElementById('seth-voz-estado'); const d = documento.getElementById('seth-ditado');
  return {voz: v.textContent, classe: v.className, pararVisivel: !documento.getElementById('seth-voz-parar').hidden,
    ditado: d.textContent, pressionado: d.getAttribute('aria-pressed'), ditadoDesabilitado: d.disabled,
    campo: documento.getElementById('seth-input').value, modo: documento.getElementById('seth-modo-conversa').checked};
};
const esperar = async () => { for (let i = 0; i < 120; i++) await new Promise((r) => setImmediate(r)); };
(async () => {
  try {
    const fonte = fs.readFileSync(path.join(dir, 'prototipo.js'), 'utf8');
    const fim = fonte.lastIndexOf('})();');
    const exposto = 'window.__voz = {ouvirResposta, vozParar, ditarPeloMicrofone, vozModoLigado, vozEstado, enviarDitado, vozLigarControles};\n';
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
    timers: timers.map((t) => ({ms: t.ms, cancelado: t.cancelado})), final: ctx.__estado(), contarOuvir: ctx.__contarOuvir()}));
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
        for classe in ("seth-voz", "seth-voz-modo", "seth-voz-estado", "seth-ditar"):
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


if __name__ == "__main__":
    unittest.main()
