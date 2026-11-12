// Seção História do /prototipo (11/11/2026): índice de tomos, leitura de um texto e o botão Ouvir.
// Só leitura de /api/historia e /api/historia/texto; o Ouvir faz um POST de {tomo, texto} e mostra se falou.
// Nenhum conteúdo entra como HTML: o texto é montado só com createElement e createTextNode. O arquivo
// inteiro fica numa IIFE; o único nome exposto é window.AgataPainel (carregarHistoria e markdownParaNos).
(() => {
const AgataPainel = (window.AgataPainel = window.AgataPainel || {});
const byIdH = (id) => document.getElementById(id);
const el = (tag) => document.createElement(tag);
const textoNo = (s) => document.createTextNode(s);

// Marcas de origem (regra F0): cada uma vira uma etiqueta com a classe do token de cor.
const MARCAS = {medido: "marca-medido", relato: "marca-relato", "inferência": "marca-inferencia", inferencia: "marca-inferencia"};
const TOKENS_INLINE = "\\*\\*([^*]+?)\\*\\*|\\*([^*\\s][^*]*?)\\*|`([^`]+)`|\\[(medido|relato|inferência|inferencia)\\]";

// Negrito, itálico, código e marcas dentro de um trecho de texto. Cada chamada cria o seu RegExp (há recursão).
function inline(texto, pai) {
  const re = new RegExp(TOKENS_INLINE, "g");
  let pos = 0;
  let casa;
  while ((casa = re.exec(texto)) !== null) {
    if (casa.index > pos) pai.appendChild(textoNo(texto.slice(pos, casa.index)));
    if (casa[1] !== undefined) {
      const negrito = el("strong");
      inline(casa[1], negrito);
      pai.appendChild(negrito);
    } else if (casa[2] !== undefined) {
      const italico = el("em");
      inline(casa[2], italico);
      pai.appendChild(italico);
    } else if (casa[3] !== undefined) {
      const codigo = el("code");
      codigo.appendChild(textoNo(casa[3]));
      pai.appendChild(codigo);
    } else {
      const marca = el("span");
      marca.className = "marca " + MARCAS[casa[4]];
      marca.appendChild(textoNo("[" + casa[4] + "]"));
      pai.appendChild(marca);
    }
    pos = re.lastIndex;
  }
  if (pos < texto.length) pai.appendChild(textoNo(texto.slice(pos)));
}

// Markdown mínimo: títulos (# a ####, sobem um nível), listas, parágrafos, linha horizontal e o inline acima.
// Devolve uma lista de nós. Não interpreta HTML: `<` e `>` saem como texto.
function markdownParaNos(texto) {
  const nos = [];
  const linhas = String(texto).replace(/\r\n?/g, "\n").split("\n");
  let paragrafo = [];
  let lista = null;
  const fechaParagrafo = () => {
    if (!paragrafo.length) return;
    const p = el("p");
    inline(paragrafo.join(" "), p);
    nos.push(p);
    paragrafo = [];
  };
  for (const bruta of linhas) {
    const linha = bruta.trim();
    if (!linha) { fechaParagrafo(); lista = null; continue; }
    const cabecalho = /^(#{1,4})\s+(.*)$/.exec(linha);
    if (cabecalho) {
      fechaParagrafo(); lista = null;
      const h = el("h" + Math.min(cabecalho[1].length + 1, 5));
      inline(cabecalho[2], h);
      nos.push(h);
      continue;
    }
    if (/^-{3,}$/.test(linha)) { fechaParagrafo(); lista = null; nos.push(el("hr")); continue; }
    const item = /^([-*]|\d+\.)\s+(.*)$/.exec(linha);
    if (item) {
      fechaParagrafo();
      const tag = /\d/.test(item[1]) ? "ol" : "ul";
      if (!lista || lista.tag !== tag) {
        lista = {tag, no: el(tag)};
        nos.push(lista.no);
      }
      const li = el("li");
      inline(item[2], li);
      lista.no.appendChild(li);
      continue;
    }
    lista = null;
    paragrafo.push(linha);
  }
  fechaParagrafo();
  return nos;
}

let indiceCarregado = false;
let carregandoIndice = false;
let textoAberto = null;
let pedidoSeq = 0;

const OPCOES_GET = {cache: "no-store", credentials: "same-origin", headers: {Accept: "application/json"}};

function marcarIndice() {
  document.querySelectorAll(".historia-texto-item").forEach((botao) => {
    const ativo = textoAberto && botao.dataset.tomo === textoAberto.tomo && botao.dataset.texto === textoAberto.id;
    if (ativo) botao.setAttribute("aria-current", "true");
    else botao.removeAttribute("aria-current");
  });
}

function renderIndice(dados) {
  const lista = byIdH("historia-indice");
  lista.replaceChildren();
  for (const tomo of dados.tomos) {
    const item = el("li");
    item.className = "historia-tomo";
    const titulo = el("p");
    titulo.className = "historia-tomo-titulo";
    titulo.appendChild(textoNo("Tomo " + tomo.numeral + " · " + tomo.titulo));
    item.appendChild(titulo);
    const textos = el("ol");
    textos.className = "historia-textos";
    for (const texto of tomo.textos) {
      const linha = el("li");
      const botao = el("button");
      botao.type = "button";
      botao.className = "historia-texto-item";
      botao.dataset.tomo = tomo.tomo;
      botao.dataset.texto = texto.id;
      botao.appendChild(textoNo(texto.numero + ". " + texto.titulo));
      botao.addEventListener("click", () => abrirTexto(tomo.tomo, texto.id));
      linha.appendChild(botao);
      textos.appendChild(linha);
    }
    item.appendChild(textos);
    lista.appendChild(item);
  }
}

function renderTexto(dados) {
  const fm = dados.frontmatter || {};
  byIdH("historia-meta").replaceChildren(textoNo("Texto " + (fm.texto || "") + " · " + (fm.titulo || "") + " · " + (fm.periodo || "")));
  const estado = byIdH("historia-estado");
  estado.replaceChildren(textoNo("Estado: " + (fm.estado || "não informado") + ". Autor: " + (fm.autor || "não informado") + "."));
  byIdH("historia-corpo").replaceChildren(...markdownParaNos(dados.corpo));
}

async function abrirTexto(tomo, id) {
  const seq = ++pedidoSeq;
  const corpo = byIdH("historia-corpo");
  const ouvir = byIdH("historia-ouvir");
  byIdH("historia-ouvir-estado").textContent = "";
  byIdH("historia-meta").textContent = "Lendo o texto…";
  byIdH("historia-estado").textContent = "";
  corpo.replaceChildren();
  if (ouvir) ouvir.disabled = true;
  textoAberto = null;
  try {
    const url = "/api/historia/texto?tomo=" + encodeURIComponent(tomo) + "&texto=" + encodeURIComponent(id);
    const resposta = await fetch(url, OPCOES_GET);
    if (!resposta.ok) throw new Error("HTTP " + resposta.status);
    const dados = await resposta.json();
    if (seq !== pedidoSeq) return;
    textoAberto = {tomo, id};
    renderTexto(dados);
    if (ouvir) ouvir.disabled = false;
    marcarIndice();
  } catch (_) {
    if (seq !== pedidoSeq) return;
    byIdH("historia-meta").textContent = "Não medido: o texto não pôde ser lido agora. Nada antigo é mostrado como atual.";
  }
}

async function carregarHistoria() {
  if (indiceCarregado || carregandoIndice) return;
  const secao = byIdH("historia");
  if (!secao) return;
  carregandoIndice = true;
  AgataPainel.marcarEstado(secao, "carregando");
  try {
    const resposta = await fetch("/api/historia", OPCOES_GET);
    if (!resposta.ok) throw new Error("HTTP " + resposta.status);
    const dados = await resposta.json();
    if (!dados || !Array.isArray(dados.tomos)) throw new Error("resposta incompleta");
    renderIndice(dados);
    indiceCarregado = true;
    AgataPainel.marcarEstado(secao, dados.tomos.length ? null : "vazio");
    if (dados.tomos.length && dados.tomos[0].textos.length) {
      await abrirTexto(dados.tomos[0].tomo, dados.tomos[0].textos[0].id);
    }
  } catch (_) {
    AgataPainel.marcarEstado(secao, "erro");
  } finally {
    carregandoIndice = false;
  }
}

async function ouvir() {
  if (!textoAberto) return;
  const botao = byIdH("historia-ouvir");
  const saida = byIdH("historia-ouvir-estado");
  botao.disabled = true;
  saida.textContent = "Lendo em voz alta. A resposta vem quando a leitura terminar.";
  try {
    const resposta = await fetch("/api/historia/ouvir", {
      method: "POST", cache: "no-store", credentials: "same-origin",
      headers: {"Content-Type": "application/json", Accept: "application/json"},
      body: JSON.stringify({tomo: textoAberto.tomo, texto: textoAberto.id}),
    });
    if (resposta.status === 429) {
      saida.textContent = "Não falei: já estou lendo outro texto. Aguarde o fim.";
      return;
    }
    if (!resposta.ok) throw new Error("HTTP " + resposta.status);
    const dados = await resposta.json();
    const motivo = String(dados.motivo || "não falei");
    saida.textContent = dados.falou ? "Falei o texto até o fim." : motivo.charAt(0).toUpperCase() + motivo.slice(1) + ".";
  } catch (_) {
    saida.textContent = "Não falei: a página não conseguiu pedir a leitura.";
  } finally {
    botao.disabled = !textoAberto;
  }
}

const botaoOuvir = byIdH("historia-ouvir");
if (botaoOuvir) botaoOuvir.addEventListener("click", () => ouvir());

AgataPainel.carregarHistoria = carregarHistoria;
AgataPainel.markdownParaNos = markdownParaNos;

// Página aberta direto em #historia: a seção já está visível quando este script roda (defer).
const secaoHistoria = byIdH("historia");
if (secaoHistoria && !secaoHistoria.hidden) carregarHistoria();
})();
