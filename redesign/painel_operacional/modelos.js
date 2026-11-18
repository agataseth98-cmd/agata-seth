// Catálogo de modelos do /prototipo (18/11/2026): tabela por capacidade e estado, filtros e a decisão do Humano.
// Lê /api/modelos; liberar e voltar ao standby fazem POST em /api/modelos/decisao, que só registra a decisão
// (não altera rota nem OmniRoute). Nada entra como HTML: tudo é montado com createElement e textContent.
(() => {
const AgataPainel = (window.AgataPainel = window.AgataPainel || {});
const byIdM = (id) => document.getElementById(id);
const no = (tag, classe, texto) => {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  if (texto !== undefined) e.textContent = texto;
  return e;
};
const OPCOES_GET = {headers: {Accept: "application/json"}, cache: "no-store", credentials: "same-origin"};
// Palavra e marca de cada estado: o estado nunca é só cor.
const ESTADO_ROTULO = {
  liberado: ["LIBERADO", "ok"], candidato_prova: ["CANDIDATO À PROVA", "aviso"], standby: ["STANDBY", "neutro"],
  indisponivel: ["INDISPONÍVEL", "erro"], proibido_pela_regra: ["PROIBIDO PELA REGRA", "erro"],
};
let dados = null;
let pendente = null;

// Filtro puro (testável): vazio em um campo significa "todos".
function filtrar(modelos, cap, prov, estado) {
  return modelos.filter((m) => (!cap || m.capacidades.includes(cap)) && (!prov || m.provedor === prov) && (!estado || m.estado === estado));
}

function opcoes(select, valores, rotulo) {
  const atual = select.value;
  select.replaceChildren(...[["", rotulo]].concat(valores.map((v) => [v, ESTADO_ROTULO[v] ? ESTADO_ROTULO[v][0] : v])).map(([v, t]) => {
    const o = no("option", "", t);
    o.value = v;
    return o;
  }));
  if (valores.includes(atual)) select.value = atual;
}

function selo(estado) {
  const [texto, tom] = ESTADO_ROTULO[estado] || [String(estado).toUpperCase(), "neutro"];
  return no("span", "nv-selo " + tom, texto);
}

function celulaAcao(m) {
  const td = no("td", "mod-acoes");
  if (m.estado === "proibido_pela_regra") {
    td.append(no("span", "mod-fixo", "Sem decisão possível: proibido pela regra."));
  } else if (m.estado === "indisponivel") {
    td.append(no("span", "mod-fixo", "Sem decisão: acesso não funcionou na prova."));
  }
  if (m.pode_liberar) {
    const b = no("button", "btn", "Liberar para rota");
    b.type = "button";
    b.addEventListener("click", () => pedirConfirmacao(m, "liberar"));
    td.append(b);
  }
  if (m.pode_standby) {
    const b = no("button", "btn secondary", "Voltar ao standby");
    b.type = "button";
    b.addEventListener("click", () => pedirConfirmacao(m, "standby"));
    td.append(b);
  }
  if (m.decisao) {
    td.append(no("span", "mod-fixo", "Decidido por " + m.decisao.quem + " em " + m.decisao.quando + "."));
  }
  return td;
}

function linha(m) {
  const tr = no("tr");
  const nome = no("td", "mod-nome");
  nome.append(no("strong", "", m.nome), no("div", "mod-id", m.id));
  const cap = no("td");
  m.capacidades.forEach((c) => cap.append(no("span", "nv-selo neutro", c)));
  const est = no("td");
  est.append(selo(m.estado));
  const acesso = no("td", "mod-acesso", m.acesso.verificado ? m.acesso.resumo : "Não medido");
  if (m.acesso.nota) acesso.append(no("div", "mod-id", m.acesso.nota));
  const ver = no("td", "mod-ver");
  if (m.veredito) {
    ver.append(no("span", "", m.veredito.resultado));
    const fonte = [m.veredito.data, m.veredito.fonte].filter(Boolean).join(" · ");
    if (fonte) ver.append(no("div", "mod-id", fonte));
  } else {
    ver.append(no("span", "nv-selo neutro", "SEM VEREDITO"));
  }
  tr.append(nome, no("td", "", m.provedor), cap, est, acesso, ver, celulaAcao(m));
  return tr;
}

function renderizar() {
  if (!dados) return;
  const lista = byIdM("mod-lista");
  const vistos = filtrar(dados.modelos, byIdM("mod-filtro-cap").value, byIdM("mod-filtro-prov").value, byIdM("mod-filtro-estado").value);
  lista.replaceChildren(...vistos.map(linha));
  byIdM("mod-vazio").hidden = vistos.length > 0;
  byIdM("mod-tabela").hidden = vistos.length === 0;
  const c = dados.contagens || {};
  byIdM("mod-resumo").textContent = vistos.length + " de " + dados.modelos.length + " modelos. Fonte: " + dados.fonte
    + " (" + (dados.arquivo_em || "sem hora") + "). " + Object.keys(ESTADO_ROTULO).map((e) => ESTADO_ROTULO[e][0].toLowerCase() + ": " + (c[e] || 0)).join("; ") + ".";
}

function pedirConfirmacao(m, acao) {
  pendente = {id: m.id, acao};
  const dlg = byIdM("mod-dialogo");
  byIdM("mod-dialogo-titulo").textContent = acao === "liberar" ? "Liberar para rota" : "Voltar ao standby";
  byIdM("mod-dialogo-texto").textContent = (acao === "liberar" ? "Registrar a liberação de " : "Registrar a volta ao standby de ") + m.id
    + ". Só grava a decisão; nenhuma rota é alterada por aqui.";
  dlg.returnValue = "";
  dlg.showModal();
}

async function enviar() {
  const nota = byIdM("mod-nota");
  const p = pendente;
  pendente = null;
  if (!p) return;
  try {
    const r = await fetch("/api/modelos/decisao", {
      method: "POST", cache: "no-store", credentials: "same-origin",
      headers: {"Content-Type": "application/json", Accept: "application/json"},
      body: JSON.stringify({id: p.id, acao: p.acao, confirmacao: p.id, quem: byIdM("mod-quem").value}),
    });
    if (!r.ok) {
      nota.textContent = "Não registrado: " + (await r.text()).slice(0, 200) + ".";
      return;
    }
    const j = await r.json();
    nota.textContent = "Registrado: " + j.registrado.acao + " de " + j.registrado.id + " por " + j.registrado.quem + ". " + j.aviso + ".";
    await carregar();
  } catch (_) {
    nota.textContent = "Não registrado: a página não conseguiu falar com o painel.";
  }
}

async function carregar() {
  const secao = byIdM("sub-catalogo-modelos");
  if (!secao) return;
  try {
    const r = await fetch("/api/modelos", OPCOES_GET);
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();
    if (!d || !Array.isArray(d.modelos)) throw new Error("resposta incompleta");
    dados = d;
    opcoes(byIdM("mod-filtro-cap"), d.capacidades, "todas");
    opcoes(byIdM("mod-filtro-prov"), d.provedores, "todos");
    opcoes(byIdM("mod-filtro-estado"), d.estados, "todos");
    if (d.estado === "sem_catalogo") {
      byIdM("mod-resumo").textContent = "Não medido: não há catálogo em " + d.fonte + ".";
      byIdM("mod-lista").replaceChildren();
      byIdM("mod-tabela").hidden = true;
      return;
    }
    renderizar();
  } catch (_) {
    dados = null;
    byIdM("mod-resumo").textContent = "Não medido: não foi possível ler o catálogo agora.";
    byIdM("mod-lista").replaceChildren();
  }
}

["mod-filtro-cap", "mod-filtro-prov", "mod-filtro-estado"].forEach((id) => {
  const e = byIdM(id);
  if (e) e.addEventListener("change", renderizar);
});
const recarregar = byIdM("mod-recarregar");
if (recarregar) recarregar.addEventListener("click", () => carregar());
const dialogo = byIdM("mod-dialogo");
if (dialogo) dialogo.addEventListener("close", () => { if (dialogo.returnValue === "ok") enviar(); else pendente = null; });

AgataPainel.carregarModelos = carregar;
AgataPainel.modelosFiltrar = filtrar;
})();
