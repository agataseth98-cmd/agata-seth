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
    this.classList = {add() {}, remove() {}, toggle() {}, contains() { return false; }}; this.style = {};
  }
  append(...nos) { this.children.push(...nos); }
  replaceChildren(...nos) { this.children = nos; }
  setAttribute() {} getAttribute() { return null; }
  addEventListener(tipo, fn) { (this.ouvintes[tipo] = this.ouvintes[tipo] || []).push(fn); }
  focus() {} blur() {} remove() {} select() {}
  closest() { return null; } querySelector() { return null; } querySelectorAll() { return []; }
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
  if (url === '/api/seth/conversas') return respostaJson(200, {schema_version: 1, state: 'ok', items: cen.conversas || []});
  if (url.startsWith('/api/seth/conversa?id=')) return respostaJson(200, cen.conversa);
  if (url === '/api/seth/conversa' && metodo === 'POST') {
    const r = escolher(cen.salvar);
    if (r && r.rede) throw new TypeError('Failed to fetch');
    if (r && r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
    return respostaJson(200, {schema_version: 1, id: '0123456789ab', titulo: '', mensagens: []});
  }
  if (url === '/api/seth/chat/stream') {
    const r = escolher(cen.stream) || {};
    if (r.status && r.status !== 200) return respostaTexto(r.status, r.texto || '');
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
(async () => {
  try {
    vm.createContext(ctx);
    vm.runInContext(fs.readFileSync(path.join(dir, 'prototipo.js'), 'utf8'), ctx, {filename: 'prototipo.js'});
  } catch (e) { console.log(JSON.stringify({erro: 'carga: ' + e.message})); return; }
  for (const f of cargas) { try { f(); } catch (e) { /* carga de outras seções: fora do teste */ } }
  await esperar();
  if (cen.abrir) { documento.getElementById('seth-conversas').children[0].children[0].ouvintes.click[0](); await esperar(); }
  if (cen.renomear !== undefined) {
    const linha = documento.getElementById('seth-conversas').children[0];
    linha.children[1].children[0].ouvintes.click[0]();  // botão Renomear da conversa (sem abrir)
    const campo = linha.children[0]; campo.value = cen.renomear;
    campo.ouvintes.keydown[0]({key: 'Enter'}); await esperar();
  }
  if (cen.modelo) { const sel = documento.getElementById('seth-modelo'); sel.value = cen.modelo; sel.ouvintes.change[0]({target: sel}); }
  for (const texto of cen.enviar || []) {
    documento.getElementById('seth-input').value = texto;
    documento.getElementById('seth-form').ouvintes.submit[0]({preventDefault() {}});
    await esperar();
  }
  const transcricao = []; coletar(documento.getElementById('seth-transcript'), transcricao);
  const salvar = documento.getElementById('seth-salvar-aviso');
  console.log(JSON.stringify({chamadas, transcricao, salvarTexto: salvar.textContent, salvarOculto: salvar.hidden,
                              status: documento.getElementById('seth-status').textContent}));
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


class LimitesDaUi(unittest.TestCase):
    def test_constantes_da_ui_sao_as_do_servidor(self):
        constantes = dict(re.findall(r"^const (SETH_[A-Z_]+) = ([\d_]+);", JS, flags=re.M))
        self.assertEqual(int(constantes["SETH_MAX_MENSAGENS"]), chat_stream.MAX_MENSAGENS)
        self.assertEqual(int(constantes["SETH_MAX_CARACTERES"]), chat_stream.MAX_CARACTERES_MENSAGEM)
        self.assertEqual(int(constantes["SETH_LIMITE_PEDIDO_BYTES"]), panel_limite_pedido())
        self.assertEqual(int(constantes["SETH_LIMITE_CONVERSA_BYTES"]), armazem.CONVERSA_LIMITE_BYTES)


if __name__ == "__main__":
    unittest.main()
