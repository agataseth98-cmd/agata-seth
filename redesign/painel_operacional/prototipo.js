"use strict";
// Painel unificado (/prototipo): uma tela com oito seções, roteadas pelo hash (#panorama, #conversa, ...).
// O arquivo inteiro fica numa IIFE; o único nome exposto no escopo global é window.AgataPainel.
(function () {
const byId = (id) => document.getElementById(id);
const AgataPainel = (window.AgataPainel = window.AgataPainel || {});
const SECOES = ["panorama", "conversa", "conselho", "sistema", "conhecimento", "historia", "custos", "qualidade"];
const navSecoes = [...document.querySelectorAll(".nav button[data-secao]")];
const shell = document.querySelector(".shell");
const sidebarToggle = byId("sidebar-toggle");
const search = byId("search");
let capFilter = "all";
let lastSnapshot = null;
let lastDetails = null;
let wikiData = null;
let busy = false;
let detailsBusy = false;
let collectionFailed = false;
let detailsFailed = false;
let lastAnnouncement = "";
let renderedSnapshotState = "";
let renderedDetailsState = "";
const proposalChecks = new Map();
// Prefixo histórico de conversas importadas em 07/11/2026: a lista desenha o título sem ele. O dado guardado não muda.
const PREFIXO_IMPORTADO = /^\[LibreChat\] +/;
const tituloDaLista = (texto) => String(texto || "").replace(PREFIXO_IMPORTADO, "");

const contar = (n, um, varios) => n + " " + (n === 1 ? um : varios);
function setSidebarCollapsed(collapsed) {
  shell.classList.toggle("sidebar-collapsed", collapsed);
  sidebarToggle.setAttribute("aria-expanded", String(!collapsed));
  sidebarToggle.setAttribute("aria-label", collapsed ? "Expandir navegação lateral" : "Recolher navegação lateral");
  sidebarToggle.title = sidebarToggle.getAttribute("aria-label");
  navSecoes.forEach((button) => { button.title = button.textContent.trim(); });
  try { localStorage.setItem("agata-sidebar-collapsed", String(collapsed)); } catch (_) { /* sem persistência */ }
}
// Gaveta (tela estreita): o menu vira painel que abre pelo botão Menu. Esc e a escolha de uma seção ou conversa fecham.
function gavetaAberta() { return shell.classList.contains("menu-aberto"); }
function setGaveta(aberta) {
  shell.classList.toggle("menu-aberto", aberta);
  byId("menu-abrir").setAttribute("aria-expanded", String(aberta));
}
byId("menu-abrir").addEventListener("click", () => setGaveta(!gavetaAberta()));
byId("menu-fechar").addEventListener("click", () => { setGaveta(false); byId("menu-abrir").focus(); });
document.addEventListener("click", (e) => {
  if (gavetaAberta() && !dentroDe(byId("sidebar-principal"), e.target) && !dentroDe(byId("menu-abrir"), e.target)) setGaveta(false);
});
let sidebarCollapsed = false;
try { sidebarCollapsed = localStorage.getItem("agata-sidebar-collapsed") === "true"; } catch (_) { /* sem persistência */ }
setSidebarCollapsed(sidebarCollapsed);
sidebarToggle.addEventListener("click", () => setSidebarCollapsed(!shell.classList.contains("sidebar-collapsed")));

// Subs visíveis da seção aberta (filhos diretos da seção, sem atributo hidden). Seções "juntos" (Conhecimento) têm vários.
const DETALHES_SUB = ["integracoes", "memoria"];
function subsAtivos() {
  return [...document.querySelectorAll(".secao:not([hidden]) > .sub:not([hidden])")];
}
function filterSearch(value) {
  const ativos = subsAtivos();
  if (!ativos.length) return;
  const query = value.toLocaleLowerCase("pt-BR");
  let cards = 0; let visible = 0; let listaAberta = false;
  ativos.forEach((ativo) => {
    const lista = ativo.dataset.sub === "integracoes";
    if (lista) listaAberta = true;
    [...ativo.querySelectorAll(".cap-card")].forEach((card) => {
      cards++;
      const matchesText = !query || card.innerText.toLocaleLowerCase("pt-BR").includes(query);
      const matchesState = !lista || capFilter === "all" || card.dataset.state === capFilter;
      card.hidden = !(matchesText && matchesState);
      if (!card.hidden) visible++;
    });
  });
  const empty = byId("no-results");
  if (empty) empty.classList.toggle("show", listaAberta && cards > 0 && visible === 0);
}

// Estados de uma seção: carregando, vazio ou erro. Ficam ocultos no HTML; aqui só um aparece por vez.
function marcarEstado(secao, tipo, texto) {
  const el = typeof secao === "string" ? byId(secao) : secao;
  if (!el) return;
  el.querySelectorAll(":scope > .estados > .estado").forEach((p) => {
    p.hidden = !tipo || p.dataset.estado !== tipo;
    if (texto && tipo && p.dataset.estado === tipo) p.textContent = texto;
  });
  el.setAttribute("aria-busy", String(tipo === "carregando"));
}
AgataPainel.marcarEstado = marcarEstado;
AgataPainel.fetchJson = (url, options, timeoutMs) => fetchJson(url, options, timeoutMs);

// Carregamento de cada subpainel quando ele abre (nomes = data-sub do HTML).
const CARREGAR_SUB = {
  integracoes: () => { loadDetails(); loadCapacidades(); },
  memoria: () => loadDetails(),
  grafo: () => carregarGrafo(),
  lacunas: () => { calcularLacunas(); carregarLacunasCanon(); },
  visao: () => carregarVisaoSistema(),
  qualidade: () => { carregarQualidade(); carregarMedicoes(); },
  sdd: () => carregarSdd(),
  frentes: () => carregarFrentes(),
  importantes: () => carregarImportantes(),
  "conselho-memoria": () => carregarMemoriaConselho(),
  // 17/11/2026: telas de leitura nova (Sistema e Qualidade). Cada uma lê a própria rota ao abrir.
  equipe: () => carregarEquipe(),
  backup: () => carregarBackup(),
  "saida-rede": () => carregarEgress(),
  perimetro: () => carregarPerimetro(),
  ci: () => carregarCI(),
  // História (11/11/2026): historia.js registra AgataPainel.carregarHistoria ao carregar; antes disso, não faz nada.
  historia: () => { if (AgataPainel.carregarHistoria) AgataPainel.carregarHistoria(); },
  // Catálogo de modelos (18/11/2026): modelos.js registra AgataPainel.carregarModelos.
  "catalogo-modelos": () => { if (AgataPainel.carregarModelos) AgataPainel.carregarModelos(); },
};

// Memória e integrações são a mesma leitura de detalhes: a rota carrega uma vez por abertura.
const ROTA_DE_SUB = {integracoes: "detalhes", memoria: "detalhes"};
function carregarSubs(nomes) {
  const feitas = new Set();
  nomes.forEach((nome) => {
    const rota = ROTA_DE_SUB[nome] || nome;
    if (feitas.has(rota)) return;
    feitas.add(rota);
    if (CARREGAR_SUB[nome]) CARREGAR_SUB[nome]();
    else if (nome.startsWith("nv-") && typeof AgataPainel.carregarNovaVersao === "function") AgataPainel.carregarNovaVersao(nome);
  });
}
function mostrarSub(secao, sub) {
  const alvo = byId(secao);
  if (!alvo) return;
  const subs = [...alvo.querySelectorAll(":scope > .sub")];
  const escolhido = subs.find((item) => item.dataset.sub === sub) || subs[0];
  if (!escolhido) return;
  if (alvo.dataset.subs === "juntos") {
    // Conhecimento: todos os blocos à vista; cada um carrega ao abrir a seção.
    subs.forEach((item) => { item.hidden = false; });
    carregarSubs(subs.map((item) => item.dataset.sub));
  } else {
    subs.forEach((item) => { item.hidden = item !== escolhido; });
    alvo.querySelectorAll(":scope > .abas > button[data-sub]").forEach((botao) => {
      const ativa = botao.dataset.sub === escolhido.dataset.sub;
      botao.setAttribute("aria-selected", String(ativa));
      botao.classList.toggle("ativa", ativa);
    });
    carregarSubs([escolhido.dataset.sub]);
  }
  filterSearch(search.value.trim());
}
function mostrarSecao(secao, sub, topo = true) {
  const alvo = byId(SECOES.includes(secao) ? secao : "panorama");
  document.querySelectorAll(".secao").forEach((item) => { item.hidden = item !== alvo; });
  navSecoes.forEach((botao) => {
    if (botao.dataset.secao === alvo.id) botao.setAttribute("aria-current", "page");
    else botao.removeAttribute("aria-current");
  });
  byId("crumb").textContent = "Agata / " + (alvo.dataset.titulo || "Panorama");
  // Na Conversa a busca do mapa some: a busca de conversas está no menu (painel-conversa-16-11).
  byId("mapa-busca").hidden = alvo.id === "conversa";
  setGaveta(false);
  search.value = "";
  mostrarSub(alvo.id, sub);
  // F7 (16/11): trocar de seção começa no topo; o navegador rolaria até a âncora #secao (~70px). Hash de item interno fica onde está.
  if (topo && window.scrollTo) window.scrollTo(0, 0);
}
function secaoDoHash() {
  let nome = "";
  try { nome = decodeURIComponent(location.hash.replace(/^#/, "")); } catch (_) { nome = ""; }
  return SECOES.includes(nome) ? nome : "panorama";
}
function irPara(secao, sub) {
  mostrarSecao(secao, sub);
  if (location.hash !== "#" + secao) history.pushState(null, "", "#" + secao);
}
function hashDeItemInterno() {
  let nome = "";
  try { nome = decodeURIComponent(location.hash.replace(/^#/, "")); } catch (_) { nome = ""; }
  return Boolean(nome) && !SECOES.includes(nome) && Boolean(byId(nome));
}
function aoMudarHash() { mostrarSecao(secaoDoHash(), undefined, !hashDeItemInterno()); }
window.addEventListener("hashchange", aoMudarHash);
window.addEventListener("popstate", aoMudarHash);
navSecoes.forEach((botao) => botao.addEventListener("click", () => irPara(botao.dataset.secao)));
document.querySelectorAll("[data-ancora]").forEach((botao) => botao.addEventListener("click", () => {
  const alvo = byId(botao.dataset.ancora);
  if (alvo && alvo.scrollIntoView) alvo.scrollIntoView({block: "start"});
}));
document.querySelectorAll(".abas > button[data-sub]").forEach((botao) => botao.addEventListener("click", () => {
  mostrarSub(botao.closest(".secao").id, botao.dataset.sub);
}));
document.addEventListener("click", (e) => { const b = e.target.closest("[data-open-page]"); if (b) irPara(b.dataset.openPage, b.dataset.openSub); });
search.addEventListener("input", () => filterSearch(search.value.trim()));
document.querySelectorAll(".filterbar button").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll(".filterbar button").forEach((item) => item.classList.remove("selected"));
  button.classList.add("selected");
  capFilter = button.dataset.filter;
  filterSearch(search.value.trim());
}));
const dialog = byId("evidence-dialog");
document.querySelectorAll(".evidence").forEach((button) => button.addEventListener("click", () => {
  byId("dialog-title").textContent = button.dataset.title || "Evidência";
  byId("dialog-body").textContent = button.dataset.body || "";
  byId("dialog-source").textContent = button.dataset.source || "Fonte não informada";
  dialog.showModal();
}));
document.querySelectorAll(".close,.close-dialog").forEach((button) => button.addEventListener("click", () => dialog.close()));
dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });

const set = (id, value) => { const el = byId(id); if (el) el.textContent = value == null ? "—" : String(value); };
const niceTime = (value) => {
  const date = new Date(value || "");
  return Number.isFinite(date.getTime()) ? new Intl.DateTimeFormat("pt-BR", {dateStyle: "short", timeStyle: "medium"}).format(date) : "não informado";
};
function stateOf(item, forcedStale = false) {
  if (!item || item.state === "unknown") return "unknown";
  // Não existe no escopo do usuário (systemctl --user): não é inativa nem sem leitura.
  if (item.state === "ausente") return "ausente";
  const until = Date.parse(item.fresh_until || "");
  if (forcedStale || item.state === "stale" || !Number.isFinite(until) || Date.now() > until) return "stale";
  return item.state === "ok" ? "ok" : "warning";
}
function stateLabel(state) {
  return {ok: "ATIVO", warning: "ATENÇÃO", stale: "DESATUALIZADO", unknown: "SEM LEITURA", ausente: "NÃO EXISTE (ESCOPO DO USUÁRIO)"}[state] || "SEM LEITURA";
}
function snapshotStateKey(snapshot, forced) {
  return JSON.stringify([
    (snapshot.services || []).map((item) => stateOf(item, forced)),
    (snapshot.timers || []).map((item) => stateOf(item, forced)),
    ...[snapshot.git, snapshot.chat, snapshot.maintenance, snapshot.proposals, snapshot.models].map((item) => stateOf(item, forced)),
  ]);
}
function detailsStateKey(data, forced) {
  return JSON.stringify([(data.integrations || []).map((item) => stateOf(item, forced)), stateOf(data.memory, forced)]);
}
function chip(id, state, text) {
  const el = byId(id);
  el.className = "chip " + ({ok: "active", warning: "partial", stale: "partial", unknown: "horizon", ausente: "ausente"}[state] ?? "horizon");
  el.textContent = text || stateLabel(state);
}
function preserveReading(oldValue, nextValue) {
  if (nextValue && nextValue.state !== "unknown") return nextValue;
  if (!oldValue || oldValue.state === "unknown") return nextValue || oldValue || {state: "unknown"};
  return {...oldValue, state: "stale", last_attempt_at: nextValue && nextValue.observed_at, last_error: "última coleta indisponível"};
}
function preserveList(previous, next, key) {
  const old = new Map((previous || []).map((item) => [item[key], item]));
  return (next || []).map((item) => preserveReading(old.get(item[key]), item));
}
function mergeSnapshot(previous, next) {
  if (!previous) return next;
  return {...next,
    services: preserveList(previous.services, next.services, "unit"),
    timers: preserveList(previous.timers, next.timers, "unit"),
    git: preserveReading(previous.git, next.git),
    chat: preserveReading(previous.chat, next.chat),
    maintenance: preserveReading(previous.maintenance, next.maintenance),
    proposals: preserveReading(previous.proposals, next.proposals),
    models: preserveReading(previous.models, next.models),
  };
}
function row(title, status, detail, labelText = null) {
  const item = document.createElement("div"); item.className = "live-row";
  const line = document.createElement("div"); line.className = "live-row-top";
  const label = document.createElement("strong"); label.textContent = title;
  const badge = document.createElement("span"); badge.className = "chip " + ({ok: "active", warning: "partial", stale: "partial", unknown: "horizon", ausente: ""}[status] ?? "horizon"); badge.textContent = labelText || stateLabel(status);
  line.append(label, badge); item.append(line);
  if (detail) { const note = document.createElement("small"); note.textContent = detail; item.append(note); }
  return item;
}
function replaceRows(id, items, empty) {
  const root = byId(id); root.replaceChildren();
  if (!items.length) { const p = document.createElement("p"); p.className = "vazio"; p.textContent = empty; root.append(p); return; }
  root.append(...items);
}
function sourceLine(item) {
  if (!item) return "Sem leitura.";
  return "Fonte: " + (item.source || "não informada") + (item.source_ref ? " · " + item.source_ref : "") +
    " · observado " + niceTime(item.observed_at) + " · válido até " + niceTime(item.fresh_until) +
    (item.last_error ? " · " + item.last_error : "");
}
const serviceNames = {"omniroute.service":"OmniRoute", "omniroute-sanitizer.service":"Sanitizador", "seth-gateway.service":"Seth Gateway", "seth-verificador.service":"Verificador", "piper-tts.service":"Piper", "openvino-whisper.service":"Whisper", "openvino-embeddings.service":"Embeddings", "obsidian-ro-proxy.service":"Proxy Obsidian", "discord-mcp.service":"Discord MCP", "navegador-mcp.service":"Navegador MCP", "laya-roteador.service":"Laya", "seth-escriba.service":"Escriba"};
const timerNames = {"agata-manutencao.timer":"Janela de manutenção"};
const taskNames = {"avaliar-decisor":"Avaliar o decisor", "memoria-semanal":"Memória semanal", "consolidacao":"Consolidar memórias", "laya-treino":"Treinar candidato do Laya"};
function unitRows(items, forced) {
  return (items || []).map((item) => row(serviceNames[item.unit] || item.unit, stateOf(item, forced),
    (item.active_state ? item.active_state + " / " + (item.sub_state || "—") + " · " : "") + sourceLine(item)));
}
function timerRows(items, forced) {
  return (items || []).map((item) => {
    const execution = item.execution || {};
    const last = execution.state === "skipped" ? "última ativação pulada por condição" :
      execution.state === "observed" ? "resultado da unidade: " + execution.result + " · término " + (execution.ended_at || "não informado") : "resultado da unidade não medido";
    return row(timerNames[item.unit] || item.unit, stateOf(item, forced),
      "Próximo disparo: " + (item.next_trigger || "não informado") + " · último disparo: " + (item.last_trigger || "não informado") + " · " + last + " · " + sourceLine(item));
  });
}
function taskRows(value, forced) {
  const configuration = stateOf(value, forced);
  return (value && value.tasks || []).map((item) => {
    const state = configuration === "stale" ? "stale" : !item.last_result ? "unknown" : item.last_result === "success" ? "ok" : "warning";
    const label = state === "stale" ? null : {success:"SAÍDA 0", skipped:"PULADA", failed:"FALHOU"}[item.last_result];
    const last = item.last_finished ? " · última execução " + niceTime(item.last_finished) : " · última execução não medida";
    return row(taskNames[item.id] || item.id, state, (item.cadence === "weekly" ? "Semanal" : "Diária") + last + " · fonte: config/janela-tarefas.txt e estado da janela", label);
  });
}
function renderModels(value, forced) {
  const state = stateOf(value, forced);
  chip("models-state", state, state === "ok" ? "REGISTRO LOCAL" : null);
  const root = byId("model-list");
  const expanded = new Set([...root.querySelectorAll("details[open]")].map((item) => item.dataset.name));
  root.replaceChildren();
  if (!value || !Array.isArray(value.models) || !value.models.length) { root.textContent = "Registro de modelos indisponível."; return; }
  for (const model of value.models) {
    const details = document.createElement("details"); details.className = "live-model";
    details.dataset.name = model.name; details.open = expanded.has(model.name);
    const summary = document.createElement("summary"); summary.textContent = model.name;
    const meta = document.createElement("p");
    meta.textContent = "Janela: " + (model.window ?? "não informada") + " · saída máxima: " + (model.max_output ?? "não informada") + " · " + (model.source || "fonte não informada") + " · registro " + (model.read_at || "sem data");
    const list = document.createElement("ul");
    for (const metric of model.metrics || []) {
      const li = document.createElement("li");
      li.textContent = [metric.metrica || "métrica", String(metric.valor ?? "não medido"), metric.data || "sem data", "amostra " + String(metric.amostra ?? "não informada"), metric.protocolo || "protocolo não informado"].join(" · ");
      list.append(li);
    }
    if (!list.children.length) { const li = document.createElement("li"); li.textContent = "Nenhuma medição registrada."; list.append(li); }
    details.append(summary, meta, list);
    if (model.metrics_truncated) { const note = document.createElement("p"); note.textContent = "Mostradas as 12 medições mais recentes do registro."; details.append(note); }
    const observed = document.createElement("p");
    observed.textContent = (model.observed || []).length ? "Uso observado nesta fonte:" : "Uso real: nenhum registro nesta fonte.";
    details.append(observed);
    for (const record of model.observed || []) {
      const note = document.createElement("p");
      note.textContent = [record.metrica || "métrica", String(record.valor ?? "não medido"), record.data || "sem data", "amostra " + String(record.amostra ?? "não informada"), record.protocolo || "protocolo não informado"].join(" · ");
      details.append(note);
    }
    if (model.observed_truncated) { const note = document.createElement("p"); note.textContent = "Mostrados os 12 registros de uso mais recentes."; details.append(note); }
    root.append(details);
  }
  set("models-source", sourceLine(value) + " · registro gerado em " + (value.recorded_at || "data não informada") + ". Catálogo, ensaio e uso são registros distintos.");
}
function renderProposals(value, forced) {
  const state = stateOf(value, forced);
  chip("proposal-state", state, state === "ok" ? "LEITURA LOCAL" : null);
  const rows = (value && value.items || []).map((item) => {
    const substituida = Boolean(item.substituida_por);
    const element = row(item.name, state,
      substituida ? "Substituída por " + item.substituida_por + ". Não vale mais."
        : (item.marker_present ? "Marcador presente; confira assinatura e aplicabilidade." : "Sem marcador de assinatura."),
      state === "ok" ? (substituida ? "SUBSTITUÍDA" : "REGISTRADA") : null);
    const result = proposalChecks.get(item.name);
    const note = document.createElement("small"); note.setAttribute("role", "status");
    if (result) {
      const expired = !Number.isFinite(Date.parse(result.fresh_until)) || Date.now() > Date.parse(result.fresh_until);
      const failures = {1:"par ausente", 2:"hash divergente", 3:"assinatura não validada", 4:"diff não aplica"};
      const descriptions = {applicable:"Par válido e diff aplicável", blocked:"Verificação bloqueada: " + (failures[result.failed_check] || "etapa não identificada"),
                            unsigned:"Sem marcador de assinatura", unknown:"Verificação indisponível"};
      note.textContent = expired ? "Verificação vencida; consulte novamente." :
        (descriptions[result.state] || "Verificação indisponível") + " · observado " + niceTime(result.observed_at) +
        (result.diff_sha256 ? " · SHA256 " + result.diff_sha256 : "");
    }
    const button = document.createElement("button"); button.type = "button"; button.className = "text-link";
    button.textContent = "Verificar assinatura e aplicabilidade";
    button.addEventListener("click", async () => {
      button.disabled = true; note.textContent = "Verificando proposta…";
      try {
        const check = await fetchJson("/api/proposals/verify", {method:"POST", headers:{"Content-Type":"application/json", Accept:"application/json"}, body:JSON.stringify({name:item.name})}, 70000);
        if (check.name !== item.name) throw new Error("resposta incompatível");
        proposalChecks.set(item.name, check);
        renderProposals(lastSnapshot.proposals, collectionFailed);
      } catch (_) { note.textContent = "Verificação indisponível."; }
      finally { button.disabled = false; }
    });
    element.append(button, note);
    return element;
  });
  replaceRows("proposal-list", rows, state === "unknown" ? "Lista indisponível." : "Nenhuma proposta nesta leitura.");
  set("proposal-source", sourceLine(value) + (value && value.truncated ? " · lista limitada a 100 propostas." : "") + " A assinatura exige verificação própria.");
  const pendentes = (value && value.items || []).filter((p) => !p.marker_present && !p.substituida_por && p.versionada !== false).length;
  set("overview-proposals", state === "unknown" ? "—" : String(pendentes));
}
// Região viva do Panorama: vazia e oculta quando não há aviso real.
function setAlerta(texto) {
  const el = byId("overview-alert");
  if (!el) return;
  el.textContent = texto || "";
  el.hidden = !texto;
}
function render(snapshot, forced = false) {
  renderedSnapshotState = snapshotStateKey(snapshot, forced);
  const services = snapshot.services || [];
  const states = services.map((item) => stateOf(item, forced));
  // 'ausente' não entra no total nem na conta de ativas.
  const presentes = states.filter((s) => s !== "ausente");
  const overall = !presentes.length || presentes.includes("unknown") ? "unknown" : presentes.includes("warning") ? "warning" : presentes.includes("stale") ? "stale" : "ok";
  const active = states.filter((s) => s === "ok").length;
  chip("units-panel-state", overall);
  set("overview-health", overall === "unknown" ? "Sem leitura" : overall === "stale" ? "Vencida" : active + "/" + presentes.length);
  replaceRows("live-services", unitRows(services, forced), "Nenhum estado recebido.");
  set("overview-updated", collectionFailed ? "Coleta indisponível; última leitura preservada." : "Leitura local observada " + niceTime(snapshot.observed_at));
  const git = snapshot.git || {}; const gitState = stateOf(git, forced);
  chip("git-panel-state", gitState, gitState === "ok" ? "LEITURA VÁLIDA" : null);
  const pendentes = ((snapshot.proposals && snapshot.proposals.items) || []).filter((p) => !p.marker_present && !p.substituida_por && p.versionada !== false).length;
  // /api/status põe ausentes e sem leitura juntos em sem_leitura: separa pelo state de cada item lido.
  const lidos = [...services, ...(snapshot.timers || [])];
  const nomeDe = (unidade) => { const item = lidos.find((i) => i.unit === unidade); return (item && item.rotulo) || serviceNames[unidade] || timerNames[unidade] || unidade; };
  const ausentes = [...new Set(lidos.filter((i) => i.state === "ausente").map((i) => i.unit))];
  const semLeitura = (Array.isArray(snapshot.sem_leitura) ? snapshot.sem_leitura : []).filter((u) => !ausentes.includes(u));
  const aviso = ausentes.length ? " · " + ausentes.length + (ausentes.length === 1 ? " unidade não existe (escopo do usuário): " : " unidades não existem (escopo do usuário): ") + ausentes.map((u) => nomeDe(u)).join(", ") : "";
  const lacunas = semLeitura.length ? " · " + semLeitura.length + (semLeitura.length === 1 ? " fonte sem leitura: " : " fontes sem leitura: ") + semLeitura.map((u) => nomeDe(u)).join(", ") : "";
  setAlerta(collectionFailed ? "Leitura vencida: a coleta falhou agora; os valores são da última leitura válida." : "");
  set("hero-status", "Unidades: " + active + " de " + presentes.length + " ativas" + aviso + " · Git: " + ({ok: "leitura válida", warning: "atenção", stale: "leitura vencida", unknown: "sem leitura"}[gitState] || "sem leitura") + " · Propostas aguardando assinatura: " + pendentes + lacunas + ".");
  set("git-branch", git.branch || "—"); set("git-head", git.head || "—");
  set("git-upstream", {tracking_up_to_date:"alinhada no último fetch",tracking_diverged:"divergente no último fetch",no_upstream:"sem referência"}[git.tracking] || "sem leitura");
  set("git-dirty", Number.isInteger(git.dirty_count) ? git.dirty_count + " item(ns)" : "—");
  set("git-age", sourceLine(git));
  renderCartoesDeStatus(snapshot, forced);
  set("hero-sync-label", gitState === "unknown" ? "Git local · sem leitura" : gitState === "stale" ? "Git local · leitura vencida" : gitState === "ok" ? "Git local · leitura válida" : "Git local · atenção");
  set("hero-sync-head", git.head || "—"); set("hero-sync-note", sourceLine(git));
  set("overview-git", gitState === "unknown" ? "—" : gitState === "stale" ? "Vencido" : gitState === "ok" ? "Em dia" : "Atenção");
  const chat = snapshot.chat || {}; const chatState = stateOf(chat, forced);
  chip("chat-state", chatState, chatState === "ok" ? "HTTP 200" : null);
  set("chat-source", sourceLine(chat) + (chat.http_status ? " · HTTP " + chat.http_status : "") + ". A saúde do endpoint não garante cada função do chat.");
  const timers = snapshot.timers || []; const timerStates = timers.map((item) => stateOf(item, forced)).filter((s) => s !== "ausente");
  const timerState = !timerStates.length || timerStates.includes("unknown") ? "unknown" : timerStates.includes("stale") ? "stale" : timerStates.includes("warning") ? "warning" : "ok";
  chip("timer-panel-state", timerState, timerState === "ok" ? "LEITURA VÁLIDA" : null);
  set("overview-timers", timerState === "unknown" ? "—" : timerState === "stale" ? "Vencida" : timerStates.filter((x) => x === "ok").length + "/" + timerStates.length);
  replaceRows("live-timers", timerRows(timers, forced), "Timers indisponíveis.");
  replaceRows("maintenance-tasks", taskRows(snapshot.maintenance, forced), "Tarefas indisponíveis.");
  set("timer-age", "Fonte: systemctl de usuário · disparo, resultado da unidade e resultado de cada tarefa são leituras distintas.");
  renderProposals(snapshot.proposals || {}, forced);
  renderModels(snapshot.models || {}, forced);
}
// Uma linha por unidade do cartão: estado do systemd, fonte e hora da leitura. Sem item, é sem leitura.
function linhaDaUnidade(unidade, item, forced) {
  if (!item) return unidade + ": sem leitura";
  if (stateOf(item, forced) === "ausente") return unidade + ": não existe (escopo do usuário) · fonte " + (item.source || "não informada") + " · observado " + niceTime(item.observed_at);
  return unidade + ": " + (item.active_state || "estado não informado") + " / " + (item.sub_state || "—") + " · fonte " + (item.source || "não informada") +
    " · observado " + niceTime(item.observed_at) + " · válido até " + niceTime(item.fresh_until);
}
// Selo do cartão a partir das unidades que ele lê. Com uma unidade, diz inativo quando o systemd diz inactive.
function rotuloDoCartao(itens, estados) {
  if (estados.every((e) => e === "ok")) return ["chip active", "ATIVO"];
  if (estados.every((e) => e === "ausente")) return ["chip ausente", "NÃO EXISTE (ESCOPO DO USUÁRIO)"];
  if (estados.every((e) => e === "unknown")) return ["chip horizon", "SEM LEITURA"];
  if (estados.length === 1 && estados[0] === "warning" && itens[0].active_state === "inactive") return ["chip partial", "INATIVO"];
  if (estados.length === 1 && estados[0] === "stale") return ["chip partial", "DESATUALIZADO"];
  return ["chip partial", "ATENÇÃO"];
}
// Cartões com data-unit (sem data-fonte) recebem o estado lido de /api/details. Os de data-fonte="status" leem /api/status.
// 17/11/2026: a lista é uma só (Sistema > Integrações). Cada cartão tem uma pílula: a da leitura da própria rota ou, sem rota, a da sonda.
function aplicarLeitura(cartao, [classe, rotulo], partes, fonte, comHora) {
  const selo = cartao.querySelector(".chip"); const linha = cartao.querySelector("p.subnote"); const hora = cartao.querySelector(".cap-hora");
  if (!selo || !linha) return;
  selo.className = classe; selo.textContent = rotulo;
  linha.textContent = partes.join("; ");
  if (hora) hora.textContent = comHora && comHora.observed_at ? "lido " + niceTime(comHora.observed_at) : "hora não medida";
  cartao.dataset.leitura = partes.join(". ");
  cartao.dataset.fonteLida = fonte;
  comporEvidencia(cartao);
}
// Evidência = texto fixo do HTML + leitura viva (unidades ou status) + sonda de capacidade. Documento não tem leitura.
function comporEvidencia(cartao) {
  const botao = cartao.querySelector("button.evidence");
  if (!botao || cartao.dataset.probe === "documento") return;
  if (!botao.dataset.base) { botao.dataset.base = botao.dataset.body || ""; botao.dataset.fonteBase = botao.dataset.source || ""; }
  botao.dataset.body = [botao.dataset.base, cartao.dataset.leitura, cartao.dataset.sonda ? "Sonda de capacidade: " + cartao.dataset.sonda : ""].filter(Boolean).join(" ");
  botao.dataset.source = [cartao.dataset.fonteLida, cartao.dataset.sondaFonte, botao.dataset.fonteBase].filter(Boolean).join(" · ");
}
function evidenciaDe(botao, texto, fonte) {
  if (!botao) return;
  botao.dataset.body = texto;
  botao.dataset.source = fonte;
}
function renderIntegrationCards(items, forced = false) {
  const porUnidade = new Map((items || []).map((item) => [item.unit, item]));
  document.querySelectorAll("#integration-list .cap-card[data-unit]:not([data-fonte])").forEach((cartao) => {
    const unidades = cartao.dataset.unit.split(" ");
    const itens = unidades.map((u) => porUnidade.get(u));
    const estados = unidades.map((u) => stateOf(porUnidade.get(u), forced));
    const partes = unidades.map((u, i) => linhaDaUnidade(u, itens[i], forced));
    aplicarLeitura(cartao, rotuloDoCartao(itens, estados), partes, "/api/details · " + unidades.join(", "), itens.find(Boolean));
  });
}
// F11 (16/11/2026): cartões que dependem de /api/status (gateway da Seth, OmniRoute e timers) leem o snapshot do Panorama.
// "Sem leitura" só aparece quando nenhuma rota lê a unidade; o texto da linha diz de onde veio a leitura.
function renderCartoesDeStatus(snapshot, forced = false) {
  const lidos = [...(snapshot.services || []), ...(snapshot.timers || [])];
  document.querySelectorAll("#integration-list .cap-card[data-fonte='status'][data-unit]").forEach((cartao) => {
    const unidades = cartao.dataset.unit.split(" ");
    const itens = unidades.map((u) => lidos.find((i) => i.unit === u));
    const estados = itens.map((item) => stateOf(item, forced));
    const partes = unidades.map((u, i) => linhaDaUnidade(u, itens[i], forced));
    aplicarLeitura(cartao, rotuloDoCartao(itens, estados), partes, "/api/status · " + unidades.join(", "), itens.find(Boolean));
  });
  const cartao = document.querySelector("#integration-list .cap-card[data-fonte='chat']");
  if (!cartao) return;
  const chat = snapshot.chat || null;
  const estado = stateOf(chat, forced);
  const http = chat && Number.isInteger(chat.http_status) ? "HTTP " + chat.http_status : null;
  const rotulos = {
    ok: ["chip active", http || "ATIVO"],
    warning: ["chip partial", http || "ATENÇÃO"],
    stale: ["chip partial", "LEITURA VENCIDA"],
    ausente: ["chip ausente", "NÃO EXISTE (ESCOPO DO USUÁRIO)"],
    unknown: ["chip horizon", "SEM LEITURA"],
  };
  aplicarLeitura(cartao, rotulos[estado] || rotulos.unknown, [sourceLine(chat) + (chat && chat.error ? " · " + chat.error : "")], "/api/status · chat", chat);
}
function renderDetails(data, forced = false) {
  renderedDetailsState = detailsStateKey(data, forced);
  renderIntegrationCards(data.integrations || [], forced);
  set("integration-source", "Consulta sob demanda · observada " + niceTime(data.observed_at) + ". Unidade ativa não comprova funcionamento da integração.");
  const memory = data.memory || {}; const state = stateOf(memory, forced);
  chip("memory-state", state, state === "ok" ? "VAULT LIDO" : null);
  set("memory-total", Number.isInteger(memory.entry_count) ? memory.entry_count : "—");
  set("memory-source", sourceLine(memory) + " · contagem de notas de entradas; não é verificação de sincronia com o canon.");
}
function announce(text) {
  if (lastAnnouncement === text) return;
  lastAnnouncement = text;
  set("collection-status", text);
}
async function fetchJson(url, options = {}, timeoutMs = 30000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {...options, credentials: "same-origin", cache: "no-store", signal: controller.signal});
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    if (!data || data.schema_version !== 1) throw new Error("versão incompatível");
    return data;
  } finally { clearTimeout(timeout); }
}
async function atualizarPanorama(manual = false) {
  if (busy || document.visibilityState === "hidden") return;
  busy = true;
  if (!lastSnapshot) marcarEstado("panorama", "carregando");
  byId("refresh-main").disabled = true; byId("refresh-status").disabled = true;
  try {
    const data = await fetchJson("/api/status", {headers: {Accept: "application/json"}});
    if (!Array.isArray(data.services) || !Array.isArray(data.timers) || !data.git) throw new Error("resposta incompleta");
    const before = lastSnapshot && JSON.stringify(lastSnapshot.services.map((item) => [item.unit, item.state]));
    lastSnapshot = mergeSnapshot(lastSnapshot, data); collectionFailed = false; marcarEstado("panorama", null);
    render(lastSnapshot);
    const after = JSON.stringify(lastSnapshot.services.map((item) => [item.unit, item.state]));
    if (manual) announce("Leitura manual concluída.");
    else if (before !== null && before !== after) announce("Estado das unidades alterado.");
    else if (!before) announce("Leitura local concluída.");
  } catch (_) {
    collectionFailed = true;
    marcarEstado("panorama", "erro", "Não medido: coleta local indisponível." + (lastSnapshot ? " Última leitura preservada como vencida." : " Sem leitura válida ainda."));
    if (lastSnapshot) render(lastSnapshot, true);
    announce(lastSnapshot ? "Coleta indisponível; última leitura preservada como vencida." : "Coleta local indisponível; sem leitura válida.");
  } finally { busy = false; byId("refresh-main").disabled = false; byId("refresh-status").disabled = false; }
}
async function loadDetails() {
  if (detailsBusy || document.visibilityState === "hidden") return;
  detailsBusy = true;
  try {
    const data = await fetchJson("/api/details", {headers: {Accept: "application/json"}});
    if (!Array.isArray(data.integrations) || !data.memory) throw new Error("resposta incompleta");
    if (lastDetails) data.integrations = preserveList(lastDetails.integrations, data.integrations, "unit");
    if (lastDetails) data.memory = preserveReading(lastDetails.memory, data.memory);
    const teveErro = detailsFailed;
    lastDetails = data; detailsFailed = false; marcarEstado("sistema", null); if (teveErro) marcarEstado("conhecimento", null); renderDetails(data);
  } catch (_) {
    detailsFailed = true;
    const sufixo = lastDetails ? " Última leitura preservada como vencida." : "";
    // Integrações ficam em Sistema; a memória fica em Conhecimento (defeito corrigido em 16/11/2026).
    marcarEstado("sistema", "erro", "Não medido: consulta de integrações indisponível." + sufixo);
    marcarEstado("conhecimento", "erro", "Não medido: consulta da memória indisponível." + sufixo);
    if (lastDetails) renderDetails(lastDetails, true);
    else { set("integration-source", "Consulta indisponível."); set("memory-source", "Consulta indisponível."); renderIntegrationCards([], false); }
  } finally { detailsBusy = false; }
}

function wikiLineSource(line) {
  if (/^memoria\/obsidian\//.test(line)) return "vault";
  if (/^(?:extras\/|\s*[\d.]+\s+extras\/)/.test(line)) return "extras";
  if (/^\s*[\d.]+\s+\(\d+\)/.test(line)) return "canon";
  return "other";
}
function renderWiki() {
  const root = byId("wiki-results"); root.replaceChildren();
  if (!wikiData) return;
  const filter = byId("wiki-source").value;
  for (const result of wikiData.results) {
    const card = document.createElement("article"); card.className = "wiki-demo-result live-wiki-result";
    const title = document.createElement("h3"); title.textContent = (result.command === "busca_semantica" ? "Busca por sentido" : "Busca por texto") + (result.partial ? " · índice parcial" : "");
    const pre = document.createElement("pre");
    if (result.error) pre.textContent = "Fonte indisponível: " + result.error;
    else if (filter === "all") pre.textContent = result.output || "A fonte não retornou conteúdo.";
    else {
      const lines = (result.output || "").split("\n").filter((line) => wikiLineSource(line) === filter);
      pre.textContent = lines.length ? lines.join("\n") : "Nenhum trecho reconhecido para este filtro nos resultados retornados.";
    }
    card.append(title, pre);
    const links = new Set();
    for (const line of (result.output || "").split("\n")) {
      const match = line.match(/^(memoria\/obsidian\/[^:\r\n]+\.md):\d+:/);
      if (!match || (filter !== "all" && filter !== "vault")) continue;
      const path = match[1].slice("memoria/obsidian/".length).replace(/\.md$/, "");
      if (path.split("/").includes("..") || links.has(path) || links.size >= 10) continue;
      links.add(path);
      const botao = document.createElement("button"); botao.type = "button"; botao.className = "text-link"; botao.dataset.vaultCaminho = path + ".md"; botao.textContent = "Abrir " + path; card.append(botao);
    }
    root.append(card);
  }
}
async function searchWiki(event) {
  event.preventDefault();
  const query = byId("conhecimento-consulta").value.trim();
  if (!query || query.length > 200 || /[\r\n\0]/.test(query)) { set("wiki-status", "Informe uma busca de até 200 caracteres em uma linha."); return; }
  byId("nv-consultar").disabled = true; wikiData = null; byId("wiki-results").replaceChildren(); marcarEstado("conhecimento", "carregando");
  set("wiki-status", "Consultando fontes locais…");
  try {
    // Busca semântica pode levar até 95 s; não repete nem guarda a consulta.
    const response = await fetch("/api/wiki/search", {method: "POST", credentials: "same-origin", cache: "no-store", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: JSON.stringify({query, mode: byId("wiki-mode").value})});
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    if (!data || data.schema_version !== 1 || !Array.isArray(data.results)) throw new Error("resposta incompatível");
    wikiData = data; renderWiki(); marcarEstado("conhecimento", null);
    set("wiki-status", "Fonte: " + data.source + " · observado " + niceTime(data.observed_at) + " · " + data.source_ref + ". O filtro atua sobre os resultados retornados.");
  } catch (_) { set("wiki-status", "Busca indisponível. Nenhum resultado foi preservado."); marcarEstado("conhecimento", "erro", "Não medido: a busca na documentação falhou. Nenhum resultado foi preservado."); }
  finally { byId("nv-consultar").disabled = false; }
}
function aplicarEscopo() {
  const escopo = byId("conhecimento-escopo").value;
  document.querySelectorAll(".busca-unica [data-escopo]").forEach((item) => { item.hidden = item.dataset.escopo !== escopo; });
}
byId("conhecimento-escopo").addEventListener("change", aplicarEscopo);
aplicarEscopo();
// Uma busca só: documentação fica aqui; Alexandria e fora do acervo passam pelo nova_versao.js.
byId("conhecimento-busca").addEventListener("submit", (event) => {
  const escopo = byId("conhecimento-escopo").value;
  if (escopo === "documentacao") { searchWiki(event); return; }
  event.preventDefault();
  if (typeof AgataPainel.buscarAcervo === "function") AgataPainel.buscarAcervo(escopo);
});
byId("wiki-source").addEventListener("change", renderWiki);
byId("refresh-main").addEventListener("click", () => atualizarPanorama(true));
byId("refresh-status").addEventListener("click", () => atualizarPanorama(true));
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") {
    atualizarPanorama();
    if (subsAtivos().some((s) => DETALHES_SUB.includes(s.dataset.sub))) loadDetails();
  }
});
setInterval(() => {
  if (document.visibilityState !== "visible") return;
  atualizarPanorama();
  if (subsAtivos().some((s) => DETALHES_SUB.includes(s.dataset.sub))) loadDetails();
}, 60000);
setInterval(() => {
  if (document.visibilityState !== "visible") return;
  if (lastSnapshot && snapshotStateKey(lastSnapshot, collectionFailed) !== renderedSnapshotState) render(lastSnapshot, collectionFailed);
  if (lastDetails && detailsStateKey(lastDetails, detailsFailed) !== renderedDetailsState) renderDetails(lastDetails, detailsFailed);
}, 5000);
atualizarPanorama();

/* (27/10/2026) Selo de cada capacidade vem de /api/capacidades; sem sonda, o cartão é documento.
   17/11/2026: os cartões da lista de integrações; a sonda entra na evidência e, sem rota de leitura, na pílula. */
async function loadCapacidades() {
  let dados = null;
  try { dados = await fetchJson("/api/capacidades", {headers: {Accept: "application/json"}}); } catch (_) { dados = null; }
  const porId = new Map(((dados && dados.items) || []).map((i) => [i.id, i]));
  const rotuloVivo = {ok: "ativo", warning: "sem resposta", unknown: "sem leitura"};
  document.querySelectorAll("[data-live]").forEach((el) => {
    const item = porId.get(el.dataset.live);
    el.textContent = item ? (rotuloVivo[item.state] || "sem leitura") : "sem leitura";
  });
  document.querySelectorAll("#integration-list .cap-card").forEach((cartao) => {
    const chip = cartao.querySelector(".chip");
    const probe = cartao.dataset.probe;
    const hora = cartao.querySelector(".cap-hora");
    if (!chip) return;
    if (probe === "documento") {
      cartao.dataset.state = "documento";
      chip.className = "chip horizon"; chip.textContent = "DOCUMENTO · sem leitura";
      if (hora) hora.textContent = "sem sonda";
      const botao = cartao.querySelector("button.evidence");
      if (botao) { botao.dataset.body = "Esta capacidade é documento: não há sonda de leitura. O texto descreve o desenho e não é medição do sistema."; botao.dataset.source = "documento do canon"; }
      return;
    }
    if (!probe) return;
    const lidaPorRota = Boolean(cartao.dataset.unit || cartao.dataset.fonte);
    const item = porId.get(probe);
    if (!item) {
      cartao.dataset.state = "planned";
      cartao.dataset.sonda = "sem leitura da sonda nesta medição.";
      if (!lidaPorRota) { chip.className = "chip planned"; chip.textContent = "SEM LEITURA"; }
    } else {
      cartao.dataset.state = {ok: "active", warning: "partial", unknown: "planned"}[item.state] || "planned";
      cartao.dataset.sonda = item.evidencia || "sem leitura nesta medição.";
      cartao.dataset.sondaFonte = item.source + " · " + item.source_ref;
      if (!lidaPorRota) {
        const rotulo = {ok: ["chip active", "LEITURA ATIVA"], warning: ["chip partial", "ATENÇÃO"], unknown: ["chip planned", "SEM LEITURA"]}[item.state];
        chip.className = rotulo[0]; chip.textContent = rotulo[1];
        if (hora) hora.textContent = dados && dados.observed_at ? "lido " + niceTime(dados.observed_at) : "hora não medida";
      }
    }
    ligarCartoesClicaveis();
    comporEvidencia(cartao);
  });
}
/* 17/11/2026: telas de leitura nova. Cada rota responde state, source, observed_at e fresh_until; sem_leitura traz motivo.
   Rota que não responde vira "sem leitura" com o motivo: nada antigo aparece como atual. */
const ESTADO_LIDO = {
  ok: ["LEITURA VÁLIDA", "chip active"], warning: ["ATENÇÃO", "chip partial"], falha: ["FALHA", "chip erro"],
  sem_leitura: ["SEM LEITURA", "chip horizon"], ausente: ["AUSENTE", "chip ausente"],
};
function estadoDe(dados) { return (dados && dados.state) || "sem_leitura"; }
function pilulaLida(el, estado) {
  if (!el) return;
  const [texto, classe] = ESTADO_LIDO[estado] || ESTADO_LIDO.sem_leitura;
  el.className = classe; el.textContent = texto;
}
async function lerRotaTela(url) {
  try {
    return await fetchJson(url, {headers: {Accept: "application/json"}});
  } catch (erro) {
    return {state: "sem_leitura", motivo: "a rota " + url + " não respondeu (" + erro.message + ")"};
  }
}
function fonteDaTela(dados) {
  if (estadoDe(dados) === "sem_leitura") return "Sem leitura: " + ((dados && dados.motivo) || "motivo não informado") + ".";
  return sourceLine(dados);
}
function mosaico(kp, rotulo, valor, nota) {
  const d = document.createElement("div"); d.className = "kpi";
  const l = document.createElement("div"); l.className = "label"; l.textContent = rotulo;
  const v = document.createElement("div"); v.className = "value"; v.textContent = valor === null || valor === undefined || valor === "" ? "não medido" : String(valor);
  d.append(l, v);
  if (nota) { const n = document.createElement("div"); n.className = "note"; n.textContent = nota; d.append(n); }
  kp.append(d);
}
function pares(dl, lista) {
  dl.replaceChildren();
  lista.forEach(([chave, valor]) => {
    const dt = document.createElement("dt"); dt.textContent = chave;
    const dd = document.createElement("dd"); dd.textContent = valor === null || valor === undefined || valor === "" ? "não medido" : String(valor);
    dl.append(dt, dd);
  });
}
// Linha de tabela: cada célula é texto, ou {pilula: true, classe, texto} para o selo de estado.
function linhasDaTabela(tbody, linhas, vazio, colunas) {
  tbody.replaceChildren();
  if (!linhas.length) {
    const tr = document.createElement("tr"); const td = document.createElement("td");
    td.className = "vazio"; td.textContent = vazio; td.colSpan = colunas; tr.append(td); tbody.append(tr);
    return;
  }
  linhas.forEach((celulas) => {
    const tr = document.createElement("tr");
    celulas.forEach((c) => {
      const td = document.createElement("td");
      if (c && c.pilula) { const s = document.createElement("span"); s.className = c.classe; s.textContent = c.texto; td.append(s); }
      else td.textContent = c === null || c === undefined || c === "" ? "não medido" : String(c);
      tr.append(td);
    });
    tbody.append(tr);
  });
}
const pilulaSim = (valor, simTxt = "sim", naoTxt = "não") => ({pilula: true, classe: valor === true ? "chip active" : valor === false ? "chip partial" : "chip horizon", texto: valor === true ? simTxt : valor === false ? naoTxt : "não medido"});

/* 17/11/2026 (contrato real): /api/equipe, /api/backup, /api/egress e /api/perimetro trazem blocos com state próprio.
   Lista vazia ou bloco com state sem_leitura nunca vira número: sai "não medido" ou o motivo que o servidor deu. */
const blocoLido = (b) => !!b && !!b.state && b.state !== "sem_leitura";
const listaDe = (x) => (Array.isArray(x) ? x : []);
const simNao = (v) => (v === true ? "sim" : v === false ? "não" : null);
const dataLida = (v) => (v ? niceTime(v) : null);

async function carregarEquipe() {
  const d = await lerRotaTela("/api/equipe");
  const estado = estadoDe(d); const lido = estado !== "sem_leitura";
  const sessao = d.sessao || {}; const sessaoLida = blocoLido(d.sessao);
  const presentes = listaDe(sessao.presentes); const esperados = listaDe(sessao.esperados);
  // Sem lista de esperados, o servidor marca os vigias como sem_leitura: a tela diz isso com as palavras dela.
  const semEsperados = !esperados.length;
  const ausentesBloco = d.ausentes || {}; const ausentesLidos = blocoLido(d.ausentes); const ausentes = listaDe(ausentesBloco.itens);
  const divergencias = listaDe(d.divergencias);
  const itensBloco = d.itens || {}; const agentes = listaDe(itensBloco.agentes);
  const vigiasBloco = d.vigias || {}; const vigias = listaDe(vigiasBloco.itens);
  const eventosBloco = d.eventos || {}; const eventos = listaDe(eventosBloco.linhas);
  set("equipe-resultado", lido
    ? "Sessão " + (sessao.estado || "não medida") + (sessao.base ? " em " + sessao.base : "") + ": " + (sessaoLida ? contar(presentes.length, "presente", "presentes") : "presentes não medidos") + ", " + (ausentesLidos ? contar(ausentes.length, "ausente", "ausentes") : "ausentes não medidos") + " e " + contar(divergencias.length, "divergência", "divergências") + "."
    : "Sem leitura da equipe: " + ((d && d.motivo) || "motivo não informado") + ".");
  const kp = byId("equipe-kpis"); kp.replaceChildren();
  mosaico(kp, "Presentes", sessaoLida ? presentes.length : null, "sessão " + (sessao.estado || "não medida"));
  mosaico(kp, "Ausentes", ausentesLidos ? ausentes.length : null, "com motivo e origem");
  mosaico(kp, "Divergências", lido ? divergencias.length : null, divergencias.length ? "em destaque abaixo" : "nenhuma nesta leitura");
  mosaico(kp, "Eventos", blocoLido(d.eventos) ? eventos.length : null, "últimos da leitura");
  pilulaLida(byId("equipe-estado"), estado);
  pares(byId("equipe-sessao"), [["estado", sessao.estado], ["base", sessao.base],
    ["agentes esperados", semEsperados ? "sessão sem lista de esperados" : esperados.join(", ")]]);
  set("equipe-fonte", fonteDaTela(d) + (lido && d.divergencias_motivo ? " Divergências: " + d.divergencias_motivo + "." : ""));
  byId("equipe-divergencias-bloco").hidden = !divergencias.length;
  const listaDiv = byId("equipe-divergencias"); listaDiv.replaceChildren();
  divergencias.forEach((texto) => { const li = document.createElement("li"); li.textContent = String(texto); listaDiv.append(li); });
  linhasDaTabela(byId("equipe-presentes"), presentes.map((p) => [p.agente, dataLida(p.desde)]), "Nenhum agente presente nesta leitura.", 2);
  linhasDaTabela(byId("equipe-ausentes"), ausentes.map((x) => [x.agente, dataLida(x.desde), x.motivo, listaDe(x.origem).join(", ")]), "Nenhum agente ausente nesta leitura.", 4);
  linhasDaTabela(byId("equipe-itens"), agentes.map((a) => [a.agente,
    (a.total != null ? "total " + a.total + " · " : "") + (Object.entries(a.por_estado || {}).map(([k, n]) => k + ": " + n).join(" · ") || "não medido")]), "Sem itens por agente.", 2);
  const vig = byId("equipe-vigias"); vig.replaceChildren();
  if (!lido || !blocoLido(vigiasBloco)) {
    const p = document.createElement("p"); p.className = "vazio";
    p.textContent = !lido ? "Vigias sem leitura: " + ((d && d.motivo) || "motivo não informado") + "."
      : semEsperados ? "Vigias: sessão sem lista de esperados."
        : "Vigias sem leitura: " + (vigiasBloco.motivo || "motivo não informado") + ".";
    vig.append(p);
  } else if (!vigias.length) {
    const p = document.createElement("p"); p.className = "vazio"; p.textContent = "Sem vigias nesta leitura."; vig.append(p);
  }
  vigias.forEach((v) => {
    const linha = document.createElement("div"); linha.className = "service";
    const nome = document.createElement("span"); nome.textContent = (v.agente ? v.agente + " · " : "") + (v.unit || "unidade não informada");
    const selo = document.createElement("b"); selo.textContent = (ESTADO_LIDO[v.state] || ESTADO_LIDO.sem_leitura)[0] + (v.active_state ? " · " + v.active_state : "");
    linha.append(nome, selo); vig.append(linha);
  });
  const ev = byId("equipe-eventos"); ev.replaceChildren();
  if (!eventos.length) {
    const li = document.createElement("li");
    li.textContent = !lido ? "Eventos sem leitura: " + ((d && d.motivo) || "motivo não informado") + "."
      : blocoLido(eventosBloco) ? "Nenhum evento nesta leitura." : "Eventos sem leitura: " + (eventosBloco.motivo || "motivo não informado") + ".";
    ev.append(li);
  }
  eventos.forEach((e) => { const li = document.createElement("li"); li.textContent = typeof e === "string" ? e : JSON.stringify(e); ev.append(li); });
}

// P-12 (17/11/2026): o veredito vem do último perímetro gravado (/api/perimetro, controle P-12), não do registro de cobertura.
function p12DoPerimetro(per) {
  if (estadoDe(per) === "sem_leitura") return {veredito: null, data: null, texto: "P-12: sem leitura (" + ((per && per.motivo) || "motivo não informado") + ")."};
  const controle = listaDe(per.controles).find((c) => c.id === "P-12");
  if (!controle) return {veredito: null, data: per.gerado_em || null, texto: "P-12: sem leitura (o último perímetro não traz o controle P-12)."};
  return {veredito: controle.veredito || null, data: per.gerado_em || null,
    texto: "P-12: " + (controle.veredito || "não medido") + " no último perímetro gravado em " + (per.gerado_em ? niceTime(per.gerado_em) : "data não informada") + "."};
}

async function carregarBackup() {
  const [d, per] = await Promise.all([lerRotaTela("/api/backup"), lerRotaTela("/api/perimetro")]);
  const estado = estadoDe(d); const lido = estado !== "sem_leitura";
  const p12 = p12DoPerimetro(per);
  const hd = d.hd || {};
  const recursos = listaDe(d.recursos);
  const dentro = recursos.filter((r) => r.dentro_da_regua === true).length;
  const pendentes = typeof d.pendentes_hd === "number" ? d.pendentes_hd : null;
  const regua = d.regua_dias;
  set("backup-resultado", p12.texto + " " + (lido
    ? "Registro de cobertura (última verificação anotada): " + dentro + " de " + recursos.length + " recursos dentro da régua de " + (regua ?? "não medida") + " dias."
    : "Sem leitura do registro de cobertura: " + ((d && d.motivo) || "motivo não informado") + "."));
  const chipP12 = byId("backup-p12-estado");
  if (chipP12) {
    chipP12.className = p12.veredito ? classeDoVeredito(p12.veredito) : "chip horizon";
    chipP12.textContent = p12.veredito ? "P-12 " + String(p12.veredito).toUpperCase() : "P-12 SEM LEITURA";
  }
  pares(byId("backup-p12"), [["veredito", p12.veredito], ["perímetro gravado em", p12.data ? niceTime(p12.data) : null]]);
  set("backup-p12-fonte", "Fonte: " + ((per && per.source) || "/api/perimetro") + ". Controle P-12 do perímetro, não o registro de cobertura abaixo.");
  const kp = byId("backup-kpis"); kp.replaceChildren();
  mosaico(kp, "Recursos dentro da régua", lido && recursos.length ? dentro + " de " + recursos.length : null, "registro de cobertura, abaixo");
  mosaico(kp, "Régua do registro", lido && regua != null ? regua + " dias" : null, "não é o veredito do P-12");
  mosaico(kp, "Pendentes no HD", lido ? pendentes : null, "a copiar");
  pilulaLida(byId("backup-estado"), estado);
  pares(byId("backup-presenca"), [["HD presente", simNao(hd.presente)], ["repositório presente", simNao(hd.repositorio_presente)]]
    .concat(hd.motivo ? [["motivo", hd.motivo]] : []));
  set("backup-fonte", fonteDaTela(d));
  set("backup-regua-nota", "O registro de cobertura (última verificação anotada) tem régua de " + (regua ?? "não medida") + " dias. Essa régua não é o veredito do P-12: o P-12 vem do último perímetro gravado.");
  linhasDaTabela(byId("backup-recursos"), recursos.map((r) => [r.recurso, dataLida(r.verificado_em), r.idade_dias, r.snapshot, pilulaSim(r.dentro_da_regua, "dentro", "fora")]), "Sem recursos lidos.", 5);
  byId("backup-recursos-vazio").hidden = recursos.length > 0;
  set("backup-pendentes", pendentes === null ? "" : "Pendentes no HD: " + pendentes + " (a copiar).");
}

// Saída de rede (17/11/2026): binarios é uma lista; cada item traz nome, presente, mtime e em_dia.
function seloEmDia(b) {
  if (b.em_dia === true) return {pilula: true, classe: "chip active", texto: "em dia"};
  if (b.presente === false) return {pilula: true, classe: "chip erro", texto: "ausente"};
  if (b.em_dia === false) return {pilula: true, classe: "chip partial", texto: "fora de dia"};
  return {pilula: true, classe: "chip horizon", texto: "não medido"};
}
async function carregarEgress() {
  const d = await lerRotaTela("/api/egress");
  const estado = estadoDe(d); const lido = estado !== "sem_leitura";
  const bins = listaDe(d.binarios);
  const emDia = bins.filter((b) => b.em_dia === true).length;
  const rust = simNao(d.navegador_usa_rust);
  const paridade = d.paridade === null || d.paridade === undefined || d.paridade === "" ? "sem registro" : (typeof d.paridade === "string" ? d.paridade : JSON.stringify(d.paridade));
  set("egress-resultado", lido
    ? "Binários em dia: " + emDia + " de " + bins.length + ". Navegador usa Rust: " + (rust || "não medido") + ". Paridade: " + paridade + "."
    : "Sem leitura da saída de rede: " + ((d && d.motivo) || "motivo não informado") + ".");
  const kp = byId("egress-kpis"); kp.replaceChildren();
  mosaico(kp, "Binários em dia", lido && bins.length ? emDia + " de " + bins.length : null, "egress e egress-socks5");
  pilulaLida(byId("egress-estado"), estado);
  linhasDaTabela(byId("egress-binarios"), bins.map((b) => [b.nome, simNao(b.presente), b.mtime, seloEmDia(b)]), "Sem binários lidos.", 4);
  pares(byId("egress-dl"), [["navegador usa Rust", rust], ["paridade", paridade]]);
  set("egress-fonte", fonteDaTela(d) + (lido && d.motivo ? " Motivo: " + d.motivo + "." : ""));
}

// Veredito de controle (perímetro e P-12): cor e palavra, nunca só cor.
// O perímetro grava o veredito em maiúsculas (OK, PARCIAL, SKIP, FALHA): a comparação ignora a caixa.
const classeDoVeredito = (v) => ({ok: "chip active", falha: "chip erro", parcial: "chip partial", skip: "chip horizon"}[String(v || "").toLowerCase()] || "chip horizon");

async function carregarPerimetro() {
  const d = await lerRotaTela("/api/perimetro");
  const estado = estadoDe(d); const lido = estado !== "sem_leitura";
  const cont = d.contagens || {}; const controles = listaDe(d.controles);
  // R1 (17/11/2026): resultado gravado há mais de 24 h aparece com aviso, mesmo com contagens OK.
  const aviso = lido && d.envelhecido ? " Atenção: " + (d.motivo || "resultado gravado há muito tempo") + "." : "";
  set("perimetro-resultado", lido
    ? "Resultado geral: " + (d.resultado_geral || "não medido") + ". Contagens: " + (cont.ok ?? "não medido") + " ok, " + (cont.falha ?? "não medido") + " falha(s)." + aviso
    : "Sem leitura do perímetro: " + ((d && d.motivo) || "motivo não informado") + ".");
  const kp = byId("perimetro-kpis"); kp.replaceChildren();
  mosaico(kp, "Resultado geral", lido ? d.resultado_geral : null);
  mosaico(kp, "OK", lido ? cont.ok : null, "controles");
  mosaico(kp, "Skip", lido ? cont.skip : null, "pulados");
  mosaico(kp, "Parcial", lido ? cont.parcial : null, "controles");
  mosaico(kp, "Falha", lido ? cont.falha : null, "controles");
  mosaico(kp, "Idade do resultado", lido && d.idade_horas != null ? d.idade_horas + " h" : null, "desde a gravação");
  pilulaLida(byId("perimetro-estado"), estado);
  linhasDaTabela(byId("perimetro-controles"), controles.map((c) => [c.id, {pilula: true, classe: classeDoVeredito(c.veredito), texto: String(c.veredito || "não medido")}]),
    "Sem controles lidos.", 2);
  set("perimetro-fonte", fonteDaTela(d) + " · head " + (d.head || "não informado") + " · gerado em " + (dataLida(d.gerado_em) || "não informado") + ".");
}

async function carregarCI() {
  const d = await lerRotaTela("/api/ci");
  const estado = estadoDe(d); const lido = estado !== "sem_leitura";
  const atual = lastSnapshot && lastSnapshot.git && lastSnapshot.git.head ? String(lastSnapshot.git.head) : null;
  const ciHead = d.head ? String(d.head) : null;
  const mesmo = ciHead && atual ? (ciHead.startsWith(atual) || atual.startsWith(ciHead)) : null;
  const comparacao = !ciHead ? "CI sem head gravado" : mesmo === null ? "head atual não medido" : mesmo ? "mesmo head do repositório" : "head diferente do atual";
  // Falhas primeiro: ok falso antes de ok verdadeiro.
  const passos = (Array.isArray(d.passos) ? d.passos : []).slice().sort((a, b) => (a.ok === true) - (b.ok === true));
  // R1 (17/11/2026): resultado gravado há mais de 24 h aparece com aviso, mesmo com linha final OK.
  const avisoCI = lido && d.envelhecido ? " Atenção: " + (d.motivo || "resultado gravado há muito tempo") + "." : "";
  set("ci-resultado", lido ? (d.linha_final || "Sem linha final nesta leitura.") + avisoCI : "Sem leitura do CI: " + ((d && d.motivo) || "motivo não informado") + ".");
  const kp = byId("ci-kpis"); kp.replaceChildren();
  mosaico(kp, "Passos ok", lido ? d.ok : null, "da última execução");
  mosaico(kp, "Falhas", lido ? d.falha : null, !lido ? "sem leitura" : passos.some((p) => p.ok === false) ? "primeiros na lista" : "nenhuma falha");
  mosaico(kp, "Idade", lido && d.idade_horas != null ? d.idade_horas + " h" : null, "desde a gravação");
  mosaico(kp, "Head", lido ? comparacao : null, ciHead ? ciHead.slice(0, 10) : null);
  pilulaLida(byId("ci-estado"), estado);
  pares(byId("ci-dl"), [["linha final", d.linha_final], ["head do CI", ciHead], ["head atual", atual], ["comparação", comparacao]]);
  set("ci-fonte", fonteDaTela(d) + " · gerado em " + (dataLida(d.gerado_em) || "não informado") + ".");
  linhasDaTabela(byId("ci-passos"), passos.map((p) => [p.nome, {pilula: true,
    classe: p.ok === true ? "chip active" : p.ok === false ? "chip erro" : "chip horizon",
    texto: p.ok === true ? "OK" : p.ok === false ? "FALHOU" : "não medido"}]), "Sem passos lidos.", 2);
}

// Provedores (17/11/2026): /api/provedores é a fonte única (catálogo do Conselho). Botões, tabela e Conexões leem daqui.
async function lerProvedores() {
  const dados = await lerRotaTela("/api/provedores");
  const lista = Array.isArray(dados.items) ? dados.items : [];
  // Sem lista não há leitura, mesmo que a rota diga "ok".
  const state = lista.length ? estadoDe(dados) : "sem_leitura";
  return {state, provedores: lista, motivo: dados.motivo || null, fonte: dados.source || null, observed_at: dados.observed_at || null};
}
AgataPainel.lerProvedores = lerProvedores;
async function montarBotoesDoConselho() {
  const raiz = byId("modelos-links");
  if (!raiz) return;
  const r = await lerProvedores();
  const titulo = document.createElement("div"); titulo.className = "abrir-titulo"; titulo.textContent = "Modelos";
  if (r.state === "sem_leitura") {
    const p = document.createElement("p"); p.className = "subnote";
    p.textContent = "Sem leitura dos provedores: " + (r.motivo || "motivo não informado") + ".";
    raiz.replaceChildren(titulo, p);
    return;
  }
  raiz.replaceChildren(titulo, ...r.provedores.map((p) => {
    const b = document.createElement("button"); b.type = "button"; b.className = "btn"; b.dataset.alvo = p.id; b.textContent = p.nome;
    return b;
  }));
}
window.addEventListener("load", () => { montarBotoesDoConselho(); });

/* F5: ao carregar a página, atualiza todas as leituras (não só a aba aberta). */
window.addEventListener("load", () => { loadDetails(); loadCapacidades(); });

/* (27/10/2026) Cartões com sonda abrem o mesmo popup da EVIDÊNCIA, sobre a tela. Teclado: Enter ou Espaço. */
function abrirEvidenciaDoCartao(cartao) {
  const botao = cartao.querySelector("button.evidence");
  const dialogo = document.getElementById("evidence-dialog");
  if (!botao || !dialogo) return;
  document.getElementById("dialog-title").textContent = cartao.querySelector("h3").textContent;
  document.getElementById("dialog-body").textContent = botao.dataset.body || "";
  document.getElementById("dialog-source").textContent = botao.dataset.source || "Fonte não informada";
  dialogo.showModal();
}
function ligarCartoesClicaveis() {
  document.querySelectorAll("#integration-list .cap-card[data-probe]:not([data-probe='documento'])").forEach((cartao) => {
    if (cartao.dataset.ligado) return;
    cartao.dataset.ligado = "1";
    cartao.tabIndex = 0; cartao.setAttribute("role", "button");
    cartao.addEventListener("click", (e) => { if (!e.target.closest("button")) abrirEvidenciaDoCartao(cartao); });
    cartao.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); abrirEvidenciaDoCartao(cartao); } });
  });
}

/* (27/10/2026) Conversa com a Seth pelo gateway local (/api/seth/chat/stream, com fallback para /api/seth/chat). Só texto; histórico só na memória desta aba. */
const SETH_MODELO_PADRAO = "seth-livre";
let sethAtual = {id: null, titulo: "", modelo: SETH_MODELO_PADRAO, temporaria: false, nos: [], folha: null, ramificada_de: null, instrucoes: "", rascunho: "nova-inicial", erro: null};
// Uso informado pelo gateway no último pedido (C11): {alvo, entrada, saida}. Vale só para a conversa que pediu.
let sethUso = null;
let sethSeqRascunho = 0;
// Rascunhos (C6): texto e anexos pendentes, por conversa. Só em memória (um Map): sem armazenamento do navegador (R9, 16/11/2026).
// Resposta em curso (AbortController, para o botão Parar) e mensagem do usuário em edição (id).
let sethControle = null;
let sethEditandoId = null;
// Lista do seletor. Vem de GET /api/seth/modelos (lista fixa no servidor); sem ela, fica só o padrão.
let sethModelos = [{id: SETH_MODELO_PADRAO, rotulo: "Seth (padrão)", descricao: ""}];
const SETH_EXEMPLOS = ["Quais propostas aguardam assinatura?", "O que o decisor Jev faz?", "Como o canon protege as decisões?"];
const SETH_NOTAS = ["Correção do turno anterior", "Verificação da Máquina"];
// Limites espelhados do servidor: chat_stream.py (MAX_MENSAGENS, MAX_CARACTERES_MENSAGEM), server.py (CHAT_STREAM_LIMITE_BYTES)
// e armazem.py (CONVERSA_LIMITE_BYTES). test_chat_ui.py confere que os números são os mesmos.
const SETH_MAX_MENSAGENS = 20;
const SETH_MAX_CARACTERES = 4000;
const SETH_LIMITE_PEDIDO_BYTES = 262144; // C10 (16/11/2026): 20 mensagens com acentos mais anexos; igual a CHAT_STREAM_LIMITE_BYTES
const SETH_LIMITE_CONVERSA_BYTES = 262144;
const SETH_LIMITE_IMPORTACAO_BYTES = 263168;
const SETH_BUSCA_MAX_CARACTERES = 120;
// C8/C9 (16/11/2026): instruções da conversa e anexos de texto (espelho de chat_stream.py: MAX_INSTRUCOES, MAX_ANEXOS,
// MAX_ANEXO_NOME, MAX_ANEXO_TEXTO, MAX_ANEXOS_TOTAL). SETH_COLAR_LIMITE: texto colado acima disso vira anexo colado.txt.
const SETH_INSTRUCOES_LIMITE = 2000;
const SETH_ANEXOS_MAX = 3;
const SETH_ANEXO_NOME_MAX = 120;
const SETH_ANEXO_TEXTO_MAX = 20000;
const SETH_ANEXOS_TOTAL_MAX = 40000;
const SETH_ANEXO_BYTES_MAX = 4 * SETH_ANEXO_TEXTO_MAX; // X1 (16/11/2026): teto do arquivo em bytes (File.size), conferido antes da leitura; o servidor confere caracteres.
const SETH_COLAR_LIMITE = 4000;
const SETH_ANEXO_EXTENSOES = [".txt", ".md", ".json", ".csv", ".log", ".py", ".js", ".ts", ".html", ".css", ".yaml", ".yml", ".toml", ".sh"];
const SETH_IMAGEM_EXTENSOES = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"];
const sethRascunhos = new Map(); // R9: rascunhos por chave de conversa; somem ao recarregar a página (nunca vão para o navegador)
// Lote 4 (09/11/2026): motivo do feedback (espelho de armazem.FEEDBACK_MOTIVO_LIMITE) e textos das respostas.
const SETH_FEEDBACK_MOTIVO_LIMITE = 200;
const SETH_CONTINUAR = "Continue de onde parou, sem repetir o que já foi dito.";
const SETH_INTERROMPIDA = "Resposta interrompida. O texto recebido ficou salvo.";
const SETH_INTERROMPIDA_VAZIA = "Resposta interrompida antes do primeiro texto. Nada foi recebido.";
// Organização (lote 3, 09/11/2026): estado da lista vindo de GET /api/seth/conversas; filtros e busca só na tela.
let sethLista = {items: [], pastas: [], marcadores: [], total: 0, organizacao: "ok"};
let sethFiltro = {pasta: "", marcador: ""};
let sethBuscaSeq = 0;
// Lixeira (09/11/2026): conversas apagadas, de GET /api/seth/lixeira. `sethRespondendo` vale enquanto a Seth responde e o salvar termina.
let sethLixeira = {items: [], total: 0, ilegiveis: 0, indisponivel: false};
let sethRespondendo = false;
function sethNova(temporaria = false) { return {id: null, titulo: "", modelo: sethAtual.modelo, temporaria, nos: [], folha: null, ramificada_de: null, instrucoes: "", rascunho: sethChaveNova(), erro: null}; }
// Hora da mensagem (C5): ISO 8601 com o fuso local (ex.: 2026-11-16T18:05:00-03:00), a mesma forma que armazem.py aceita.
function sethHora(data = new Date()) {
  const p = (n) => String(n).padStart(2, "0");
  const minutos = -data.getTimezoneOffset(); const sinal = minutos >= 0 ? "+" : "-"; const abs = Math.abs(minutos);
  return data.getFullYear() + "-" + p(data.getMonth() + 1) + "-" + p(data.getDate()) + "T" + p(data.getHours()) + ":" + p(data.getMinutes())
    + ":" + p(data.getSeconds()) + sinal + p(Math.floor(abs / 60)) + ":" + p(abs % 60);
}
// Mostrado na transcrição: hora curta e, no title, a data completa. Hora ausente ou inválida não mostra nada.
function sethHoraCurta(iso) { const d = new Date(iso); return isNaN(d) ? "" : d.toLocaleTimeString("pt-BR", {hour: "2-digit", minute: "2-digit"}); }
function sethHoraCompleta(iso) { const d = new Date(iso); return isNaN(d) ? "" : d.toLocaleString("pt-BR", {day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit"}); }
function sethStatus(texto, classe) { const e = byId("seth-status"); e.textContent = texto; e.className = "chip " + classe; }
function sethTitulo(texto) { byId("seth-titulo").textContent = texto || (sethAtual.temporaria ? "Conversa temporária" : "Nova conversa"); }
function sethMostrarModelo() {
  const select = byId("seth-modelo"); const desc = byId("seth-modelo-desc");
  if (select.value !== sethAtual.modelo) select.value = sethAtual.modelo;
  const escolhido = sethModelos.find((m) => m.id === sethAtual.modelo);
  desc.textContent = escolhido ? escolhido.descricao : "";
}
async function sethCarregarModelos() {
  const select = byId("seth-modelo");
  try {
    const dados = await fetchJson("/api/seth/modelos", {headers: {Accept: "application/json"}});
    if (!Array.isArray(dados.modelos) || !dados.modelos.length) return;
    sethModelos = dados.modelos;
    select.replaceChildren();
    sethModelos.forEach((m) => { const o = document.createElement("option"); o.value = m.id; o.textContent = m.rotulo; select.append(o); });
    sethMostrarModelo();
  } catch (_) { /* sem a lista, fica só o padrão do HTML; a conversa segue com seth-livre */ }
}
// Modelo que respondeu: o real (cabeçalho X-Modelo-Real do gateway); sem ele, o escolhido, marcado "(escolhido)".
function sethTextoModelo(m) {
  if (m.modelo_real) return (m.modelo_real.includes("+") ? "modelos (um por rodada): " : "modelo: ")
    + m.modelo_real.split("+").join(" → ");
  if (m.modelo) return "modelo: " + m.modelo + " (escolhido)";
  return "modelo: não registrado";
}
// Inline (C1, C2): código, negrito, tachado, itálico, [texto](url) e URL solta. Só elementos e textNode; nunca `a`.
// No split com grupo de captura, os trechos casados caem nos índices ímpares; o resto é texto puro.
const SETH_INLINE_RE = /(`[^`\n]+`|\[[^\]\n]+\]\([^)\s]+\)|https?:\/\/[^\s<>()]+|\*\*[^*\n]+\*\*|~~[^~\n]+~~|(?<![\w*])\*(?![\s*])[^*\n]+?\*(?![\w*])|(?<![\w_])_(?![\s_])[^_\n]+?_(?![\w_]))/;
function sethInline(container, texto) {
  String(texto).split(SETH_INLINE_RE).forEach((p, i) => {
    if (!p) return;
    if (i % 2 === 0) { container.append(document.createTextNode(p)); return; }
    if (p.startsWith("`")) { const c = document.createElement("code"); c.textContent = p.slice(1, -1); container.append(c); }
    else if (p.startsWith("**")) { const b = document.createElement("strong"); b.textContent = p.slice(2, -2); container.append(b); }
    else if (p.startsWith("~~")) { const d = document.createElement("del"); d.textContent = p.slice(2, -2); container.append(d); }
    else if (p.startsWith("[")) sethLinkMarkdown(container, p);
    else if (p.startsWith("http")) {
      // A pontuação colada logo depois da URL (ponto, vírgula) fica como texto, fora do link.
      const [, url, fim] = p.match(/^(.*?)([.,;:!?]*)$/);
      sethLinkCopiavel(container, "", url);
      if (fim) container.append(document.createTextNode(fim));
    }
    else { const e = document.createElement("em"); e.textContent = p.slice(1, -1); container.append(e); }
  });
}
// Só http e https viram link (com o endereço visível e botão Copiar link). Outro esquema fica como texto puro.
function sethLinkMarkdown(container, trecho) {
  const m = trecho.match(/^\[([^\]\n]+)\]\(([^)\s]+)\)$/);
  if (!m || !/^https?:\/\//i.test(m[2])) { container.append(document.createTextNode(trecho)); return; }
  sethLinkCopiavel(container, m[1], m[2]);
}
function sethLinkCopiavel(container, rotulo, endereco) {
  const bloco = document.createElement("span"); bloco.className = "md-link";
  if (rotulo) { const nome = document.createElement("span"); nome.className = "md-link-rotulo"; nome.textContent = rotulo; bloco.append(nome, document.createTextNode(" ")); }
  const url = document.createElement("code"); url.className = "md-link-url"; url.textContent = endereco;
  const copiar = sethTexto("Copiar link", async () => {
    try { await navigator.clipboard.writeText(endereco); copiar.textContent = "Link copiado"; }
    catch (_) { copiar.textContent = "Não foi possível copiar"; }
    setTimeout(() => { copiar.textContent = "Copiar link"; }, 1600);
  });
  bloco.append(url, document.createTextNode(" "), copiar);
  container.append(bloco);
}
// Bloco de código (C3): cabeçalho com a linguagem, botão Copiar e região aria-live para o "Copiado" (2 s).
function sethBlocoCodigo(lingua, destino) {
  const bloco = document.createElement("div"); bloco.className = "md-codigo";
  const cab = document.createElement("div"); cab.className = "md-codigo-cab";
  const nome = document.createElement("span"); nome.className = "md-codigo-lingua"; nome.textContent = lingua || "código";
  const aviso = document.createElement("span"); aviso.className = "md-codigo-aviso"; aviso.setAttribute("role", "status"); aviso.setAttribute("aria-live", "polite");
  const pre = document.createElement("pre"); const code = document.createElement("code"); pre.append(code);
  const copiar = sethTexto("Copiar", async () => {
    try { await navigator.clipboard.writeText(code.textContent.replace(/\n$/, "")); aviso.textContent = "Copiado"; }
    catch (_) { aviso.textContent = "Não foi possível copiar"; }
    setTimeout(() => { aviso.textContent = ""; }, 2000);
  });
  cab.append(nome, aviso, copiar);
  bloco.append(cab, pre); destino.append(bloco);
  return code;
}
// Tabela (C1): cabeçalho com |, linha de traços e linhas; dentro de moldura com rolagem horizontal.
const SETH_SEPARADOR_TABELA = /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/;
function sethCelulas(linha) { return linha.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim()); }
function sethTabela(cabecalho, linhas, destino) {
  const moldura = document.createElement("div"); moldura.className = "md-tabela"; moldura.setAttribute("role", "region");
  moldura.setAttribute("aria-label", "Tabela"); moldura.tabIndex = 0;
  const tabela = document.createElement("table");
  const thead = document.createElement("thead"); const cabeca = document.createElement("tr");
  sethCelulas(cabecalho).forEach((c) => { const th = document.createElement("th"); th.setAttribute("scope", "col"); sethInline(th, c); cabeca.append(th); });
  thead.append(cabeca);
  const tbody = document.createElement("tbody");
  linhas.forEach((l) => { const tr = document.createElement("tr"); sethCelulas(l).forEach((c) => { const td = document.createElement("td"); sethInline(td, c); tr.append(td); }); tbody.append(tr); });
  tabela.append(thead, tbody); moldura.append(tabela); destino.append(moldura);
}
// Markdown por elementos do DOM (C1): títulos #/##/### em h3/h4/h5, listas (aninhadas por dois espaços), citação, tabela,
// linha horizontal, bloco de código com linguagem. Texto vem só por textContent ou por sethInline.
// J1 (16/11/2026): a próxima linha não vazia, depois de linhas em branco, é item de lista?
function sethItemDepois(linhas, i) {
  let j = i + 1;
  while (j < linhas.length && !linhas[j].trim()) j++;
  return j < linhas.length && /^\s*([-*+]|\d+[.)])\s+/.test(linhas[j]);
}
function sethMarkdown(texto, destino) {
  const linhas = String(texto).split("\n");
  let codigo = null, cit = null, pilha = [];
  for (let i = 0; i < linhas.length; i++) {
    const linha = linhas[i];
    if (codigo) {
      if (/^\s*```/.test(linha)) { codigo.textContent = codigo.textContent.replace(/\n$/, ""); codigo = null; }
      else codigo.textContent += linha + "\n";
      continue;
    }
    if (/^\s*```/.test(linha)) { codigo = sethBlocoCodigo(linha.trim().slice(3).trim().split(/\s+/)[0], destino); cit = null; pilha = []; continue; }
    if (!/^\s*>/.test(linha)) cit = null;
    if (SETH_NOTAS.some((p) => linha.trim().startsWith(p))) { const aside = document.createElement("aside"); aside.className = "nota"; aside.textContent = linha.trim(); destino.append(aside); pilha = []; continue; }
    // Linha em branco não quebra a lista: se o próximo texto é item, a lista segue (J1, 16/11/2026).
    if (!linha.trim()) { if (!sethItemDepois(linhas, i)) pilha = []; continue; }
    if (/^\s*([-*_])(?:\s*\1){2,}\s*$/.test(linha)) { destino.append(document.createElement("hr")); pilha = []; continue; }
    const cabeca = linha.match(/^(#{1,3})\s+(.*)$/);
    if (cabeca) { const h = document.createElement(["h3", "h4", "h5"][cabeca[1].length - 1]); sethInline(h, cabeca[2]); destino.append(h); pilha = []; continue; }
    if (linha.includes("|") && i + 1 < linhas.length && SETH_SEPARADOR_TABELA.test(linhas[i + 1])) {
      const corpo = []; let j = i + 2;
      while (j < linhas.length && linhas[j].includes("|") && linhas[j].trim()) corpo.push(linhas[j++]);
      sethTabela(linha, corpo, destino); pilha = []; i = j - 1; continue;
    }
    if (/^\s*>/.test(linha)) {
      if (!cit) { cit = document.createElement("blockquote"); destino.append(cit); }
      const p = document.createElement("p"); sethInline(p, linha.replace(/^\s*>\s?/, "")); cit.append(p); pilha = []; continue;
    }
    const item = linha.match(/^(\s*)([-*+]|\d+[.)])\s+(.*)$/);
    if (item) {
      // Nível pelo recuo (dois espaços por nível). Lista de outro tipo no mesmo nível começa uma lista nova.
      const nivel = Math.floor(item[1].replace(/\t/g, "  ").length / 2); const ordenada = /\d/.test(item[2]);
      while (pilha.length && (pilha[pilha.length - 1].nivel > nivel || (pilha[pilha.length - 1].nivel === nivel && pilha[pilha.length - 1].ordenada !== ordenada))) pilha.pop();
      let topo = pilha[pilha.length - 1];
      if (!topo || topo.nivel < nivel) {
        const lista = document.createElement(ordenada ? "ol" : "ul");
        // Número inicial do texto (J1): "3." começa em 3; "1." segue o padrão do navegador.
        if (ordenada && parseInt(item[2], 10) !== 1 && Number.isFinite(parseInt(item[2], 10))) lista.setAttribute("start", String(parseInt(item[2], 10)));
        (topo ? (topo.li || topo.lista) : destino).append(lista);
        topo = {nivel, ordenada, lista, li: null}; pilha.push(topo);
      }
      const li = document.createElement("li"); sethInline(li, item[3]); topo.lista.append(li); topo.li = li;
      continue;
    }
    const p = document.createElement("p"); sethInline(p, linha); destino.append(p); pilha = [];
  }
  if (codigo) codigo.textContent = codigo.textContent.replace(/\n$/, "");
}
function sethMensagem(m, indice) {
  const log = byId("seth-transcript");
  const msg = document.createElement("article");
  msg.className = "msg msg-" + (m.role === "user" ? "user" : "assistant") + (m.interrompida ? " msg-interrompida" : "");
  msg.dataset.indice = String(indice);
  const cab = document.createElement("div"); cab.className = "msg-head";
  const quem = document.createElement("strong"); quem.textContent = m.role === "user" ? "Você" : "Seth";
  // Hora (C5): só com hora gravada; mensagem antiga sem hora não mostra nada.
  const hora = document.createElement("time");
  if (m.hora) { hora.setAttribute("datetime", m.hora); hora.textContent = sethHoraCurta(m.hora); hora.title = sethHoraCompleta(m.hora); }
  cab.append(quem, hora);
  if (m.role === "assistant") { const modelo = document.createElement("span"); modelo.className = "msg-modelo"; modelo.textContent = sethTextoModelo(m); cab.append(modelo); }
  if (m.interrompida) cab.append(sethSelo("interrompida", "seth-selo-interrompida"));
  const corpo = document.createElement("div"); corpo.className = "msg-body";
  if (m.role === "user") { if (sethEditandoId === m.id) sethFormEdicao(m, corpo); else corpo.textContent = m.content; }
  else sethCorpo(m, corpo);
  msg.append(cab, corpo);
  // Anexos da mensagem do usuário (C9): só o metadado gravado (nome e caracteres); o texto do anexo não fica na conversa.
  if (m.role === "user" && m.anexos && m.anexos.length && sethEditandoId !== m.id) msg.append(sethEtiquetasAnexos(m.anexos));
  if (m.aviso) { const aviso = document.createElement("p"); aviso.className = "seth-aviso"; aviso.textContent = m.aviso; msg.append(aviso); }
  if (m.interrompida) { const aviso = document.createElement("p"); aviso.className = "seth-aviso"; aviso.textContent = m.content ? SETH_INTERROMPIDA : SETH_INTERROMPIDA_VAZIA; msg.append(aviso); }
  const irmaos = sethIrmaos(m);
  if (irmaos.length > 1) msg.append(sethRamo(m, irmaos));
  if (sethEditandoId !== m.id) msg.append(sethAcoesMensagem(m, indice));
  log.append(msg);
}
function sethDesenhar() {
  const log = byId("seth-transcript"); log.replaceChildren();
  const caminho = sethCaminho();
  caminho.forEach((no, i) => sethMensagem(no, i));
  // Falha da última resposta (C7): fica no fim da transcrição até "Tentar de novo" ou uma nova pergunta.
  if (sethAtual.erro) log.append(sethBlocoErro(sethAtual.erro));
  // Estado vazio central (saudação e sugestões) só enquanto a conversa não tem mensagem.
  const central = byId("seth-vazio-central"); if (central) central.hidden = caminho.length > 0;
  log.scrollTop = log.scrollHeight;
  sethTitulo(sethAtual.titulo);
  sethPintarAvisoSalvar();
  sethPintarTemporaria();
  sethPintarInstrucoes();
  sethPintarExportar();
  sethPintarOrigem();
  sethPintarContexto(caminho);
  sethPintarParar();
  sethAtualizarFim();
}
function sethExemplos() {
  const box = byId("seth-exemplos"); if (!box) return;
  box.replaceChildren();
  SETH_EXEMPLOS.forEach((texto) => {
    const b = document.createElement("button"); b.type = "button"; b.className = "seth-exemplo"; b.textContent = texto;
    b.addEventListener("click", () => { byId("seth-input").value = texto; byId("seth-input").focus(); });
    box.append(b);
  });
}
function sethOpcao(valor, rotulo) { const o = document.createElement("option"); o.value = valor; o.textContent = rotulo; return o; }
function sethTexto(rotulo, aoClicar) { const b = document.createElement("button"); b.type = "button"; b.className = "text-link"; b.textContent = rotulo; b.addEventListener("click", aoClicar); return b; }
function sethSelo(texto, classe) { const s = document.createElement("span"); s.className = "seth-selo " + classe; s.textContent = texto; return s; }
function sethVazio(texto) { const p = document.createElement("p"); p.className = "seth-vazio"; p.textContent = texto; return p; }
// C12b (16/11/2026): o aviso de organização aparece no diálogo e também no menu, junto da lista de conversas.
function sethEspelhos(id) { return [byId(id), byId(id + "-menu")].filter(Boolean); }
function sethMostrarOrg(texto) { sethEspelhos("seth-org-aviso").forEach((aviso) => { aviso.textContent = texto || ""; aviso.hidden = !texto; }); }
// Motivo de recusa do painel em português, sem o conteúdo da conversa (o servidor só devolve a regra).
function sethErroOrg(status, motivo) {
  if (status === 404) return "Conversa ou pasta não encontrada; a lista foi atualizada.";
  if (status === 409) return "A organização das conversas está ilegível; nada foi alterado.";
  if (status === 413) return "Pedido grande demais; nada foi alterado.";
  if (status === 400) return "Não foi possível salvar: " + (motivo || "pedido recusado") + ".";
  return "Não foi possível salvar: o painel respondeu com erro " + status + ".";
}
// Lista: fixadas no topo, arquivadas numa seção própria, filtros por pasta e marcador. Estado vem de GET /api/seth/conversas.
async function sethListar() {
  const box = byId("seth-conversas"); if (!box) return;
  try {
    const [dados, lixeira] = await Promise.all([
      fetchJson("/api/seth/conversas", {headers: {Accept: "application/json"}}),
      fetchJson("/api/seth/lixeira", {headers: {Accept: "application/json"}}).catch(() => null)]);
    sethLista = {items: dados.items || [], pastas: dados.pastas || [], marcadores: dados.marcadores || [], total: dados.total || 0,
      organizacao: dados.organizacao || "ok", ilegiveis: dados.ilegiveis || 0};
    sethLixeira = lixeira
      ? {items: lixeira.items || [], total: lixeira.total || 0, ilegiveis: lixeira.ilegiveis || 0, indisponivel: false}
      : {items: [], total: 0, ilegiveis: 0, indisponivel: true};
    sethPintarLista();
    sethPintarLixeira();
    sethPintarIlegiveis();
  } catch (erro) { box.textContent = "Lista indisponível (" + erro.message + ")."; }
}
// Arquivos de conversa que não puderam ser lidos (na lista ou na lixeira): o servidor só conta, não apaga nada.
function sethPintarIlegiveis() {
  const n = sethLista.ilegiveis + sethLixeira.ilegiveis;
  const texto = !n ? "" : n === 1
    ? "1 arquivo de conversa não pôde ser lido e não aparece aqui. Nada foi apagado; confira a pasta de conversas."
    : n + " arquivos de conversa não puderam ser lidos e não aparecem aqui. Nada foi apagado; confira a pasta de conversas.";
  sethEspelhos("seth-ilegiveis-aviso").forEach((aviso) => { aviso.textContent = texto; aviso.hidden = !texto; });
}
// Lixeira: restaurar devolve a conversa com a organização dela; apagar de vez pede confirmação (purga manual).
function sethPintarLixeira() {
  const box = byId("seth-lixeira"); if (!box) return;
  byId("seth-lixeira-total").textContent = String(sethLixeira.total);
  box.replaceChildren();
  if (sethLixeira.indisponivel) { box.append(sethVazio("Lixeira indisponível agora.")); return; }
  if (!sethLixeira.items.length) { box.append(sethVazio("A lixeira está vazia.")); return; }
  sethLixeira.items.forEach((c) => box.append(sethLinhaLixeira(c)));
  if (sethLixeira.total > sethLixeira.items.length) box.append(sethVazio("Mostrando as " + sethLixeira.items.length + " mais recentes de " + sethLixeira.total + "."));
}
function sethLinhaLixeira(c) {
  const linha = document.createElement("div"); linha.className = "seth-item";
  const titulo = document.createElement("strong"); titulo.textContent = tituloDaLista(c.titulo);
  const meta = document.createElement("p"); meta.className = "seth-resultado-meta";
  meta.textContent = "Apagada em " + c.apagada_em + " · " + c.mensagens + (c.mensagens === 1 ? " mensagem" : " mensagens");
  const acoes = document.createElement("div"); acoes.className = "seth-item-acoes";
  const restaurar = sethTexto("Restaurar", () => sethLixeiraMudar("restaurar", c.nome));
  const purgar = sethTexto("Apagar de vez", () => {
    if (purgar.dataset.confirma !== "1") { purgar.dataset.confirma = "1"; purgar.textContent = "Confirmar apagar de vez"; return; }
    sethLixeiraMudar("purgar", c.nome);
  });
  acoes.append(restaurar, purgar);
  linha.append(titulo, meta, acoes);
  return linha;
}
function sethErroLixeira(status, motivo) {
  if (status === 404) return "Esta conversa já não está na lixeira; a lista foi atualizada.";
  if (status === 409) return "Não foi possível: " + (motivo || "conflito com a conversa salva") + ".";
  if (status === 400) return "Pedido recusado: " + (motivo || "item inválido") + ".";
  return "Não foi possível: o painel respondeu com erro " + status + ".";
}
async function sethLixeiraMudar(acao, nome) {
  const restaurando = acao === "restaurar";
  const rota = restaurando ? "/api/seth/lixeira/restaurar" : "/api/seth/lixeira/purgar";
  try {
    const r = await fetch(rota, {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: JSON.stringify({nome})});
    if (!r.ok) sethMostrarOrg(sethErroLixeira(r.status, await sethMotivo(r)));
    else if (restaurando) { const dados = await r.json(); sethMostrarOrg("Conversa restaurada: " + dados.titulo + "."); }
    else sethMostrarOrg("Conversa apagada de vez. Não tem como desfazer.");
  } catch (_) { sethMostrarOrg("Não foi possível " + (restaurando ? "restaurar" : "apagar") + " a conversa: sem resposta do painel."); }
  await sethListar();
}
function sethPassaFiltro(c) {
  const semPasta = sethFiltro.pasta === "-";
  if (semPasta ? c.pasta : (sethFiltro.pasta && c.pasta !== sethFiltro.pasta)) return false;
  return !sethFiltro.marcador || (c.marcadores || []).includes(sethFiltro.marcador);
}
function sethPintarFiltros() {
  const pasta = byId("seth-filtro-pasta"); const marcador = byId("seth-filtro-marcador");
  if (sethFiltro.pasta && sethFiltro.pasta !== "-" && !sethLista.pastas.some((p) => p.id === sethFiltro.pasta)) sethFiltro.pasta = "";
  if (sethFiltro.marcador && !sethLista.marcadores.includes(sethFiltro.marcador)) sethFiltro.marcador = "";
  pasta.replaceChildren(sethOpcao("", "Todas as pastas"), sethOpcao("-", "Sem pasta"), ...sethLista.pastas.map((p) => sethOpcao(p.id, p.nome)));
  pasta.value = sethFiltro.pasta;
  marcador.replaceChildren(sethOpcao("", "Todos os marcadores"), ...sethLista.marcadores.map((m) => sethOpcao(m, "#" + m)));
  marcador.value = sethFiltro.marcador;
}
function sethGrupo(texto) { const h = document.createElement("p"); h.className = "seth-grupo"; h.textContent = texto; return h; }
// Grupos da lista: Fixadas e depois pela data real (campo atualizada). Vazio não aparece.
const SETH_GRUPOS = ["Fixadas", "Hoje", "Ontem", "Últimos 7 dias", "Mais antigas"];
function sethGrupoDaData(c, agora = new Date()) {
  const data = new Date(c.atualizada || "");
  if (!Number.isFinite(data.getTime())) return "Mais antigas";
  const dia = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const dias = Math.round((dia(agora) - dia(data)) / 86400000);
  if (dias <= 0) return "Hoje";
  if (dias === 1) return "Ontem";
  if (dias <= 7) return "Últimos 7 dias";
  return "Mais antigas";
}
function sethPreencher(box, itens, vazio) {
  box.replaceChildren();
  if (!itens.length) { box.append(sethVazio(vazio)); return; }
  const grupos = new Map(SETH_GRUPOS.map((nome) => [nome, []]));
  itens.forEach((c) => grupos.get(c.fixada ? "Fixadas" : sethGrupoDaData(c)).push(c));
  SETH_GRUPOS.forEach((nome) => {
    const lista = grupos.get(nome);
    if (!lista.length) return;
    box.append(sethGrupo(nome));
    lista.forEach((c) => box.append(sethLinha(c)));
  });
}
function sethPintarLista() {
  if (!byId("seth-conversas")) return;
  sethPintarFiltros();
  sethPintarPastas();
  const filtrando = Boolean(sethFiltro.pasta || sethFiltro.marcador);
  const visiveis = sethLista.items.filter(sethPassaFiltro);
  const lista = byId("seth-conversas");
  sethPreencher(lista, visiveis.filter((c) => !c.arquivada), filtrando ? "Nenhuma conversa com este filtro." : "Nenhuma conversa salva.");
  if (sethLista.total > sethLista.items.length) lista.append(sethVazio("Mostrando as " + sethLista.items.length + " conversas mais recentes de " + sethLista.total + "."));
  const arquivadas = sethLista.items.filter((c) => c.arquivada);
  byId("seth-arquivadas-total").textContent = String(arquivadas.length);
  sethPreencher(byId("seth-arquivadas"), visiveis.filter((c) => c.arquivada), arquivadas.length ? "Nenhuma conversa arquivada com este filtro." : "Nenhuma conversa arquivada.");
  if (sethLista.organizacao === "ilegivel") sethMostrarOrg("A organização das conversas (fixadas, arquivadas, marcadores e pastas) está ilegível. Nada será alterado até o arquivo ser conferido.");
}
// Menus de ação: um aberto por vez; Esc e clique fora fecham; setas andam entre os itens (painel-conversa-16-11).
let menuAberto = null;
// J8 (16/11/2026): ao fechar por Esc ou escolha, o foco volta ao botão "Mais" (se a ação não levou o foco a outro lugar).
function fecharMenuAberto(devolverFoco = false) {
  if (!menuAberto) return;
  const {gatilho, menu} = menuAberto;
  const ativo = document.activeElement;
  const foco = !ativo || ativo === document.body || dentroDe(menu, ativo);
  menu.hidden = true;
  gatilho.setAttribute("aria-expanded", "false");
  menuAberto = null;
  if (devolverFoco && foco) gatilho.focus();
}
function dentroDe(no, alvo) { for (let n = alvo; n; n = n.parentNode) if (n === no) return true; return false; }
document.addEventListener("click", (e) => {
  if (!menuAberto) return;
  if (dentroDe(menuAberto.menu, e.target) || dentroDe(menuAberto.gatilho, e.target)) return;
  fecharMenuAberto();
});
function ligarMenu(gatilho, menu, fecharAoEscolher = false) {
  gatilho.addEventListener("click", () => {
    const abrir = menu.hidden;
    fecharMenuAberto();
    if (!abrir) return;
    menu.hidden = false;
    gatilho.setAttribute("aria-expanded", "true");
    menuAberto = {gatilho, menu};
    const primeiro = menu.querySelector('[role="menuitem"]');
    if (primeiro) primeiro.focus();
  });
  menu.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { e.preventDefault(); fecharMenuAberto(true); return; }
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    e.preventDefault();
    const itens = [...menu.querySelectorAll('[role="menuitem"]')];
    const atual = itens.indexOf(document.activeElement);
    const proximo = (atual + (e.key === "ArrowDown" ? 1 : -1) + itens.length) % itens.length;
    if (itens[proximo]) itens[proximo].focus();
  });
  if (fecharAoEscolher) menu.addEventListener("click", (e) => {
    if (e.target && e.target.getAttribute && e.target.getAttribute("role") === "menuitem") fecharMenuAberto(true);
  });
}
function sethItemMenu(texto, aoClicar, fecha = true) {
  const b = document.createElement("button"); b.type = "button"; b.className = "seth-menu-item"; b.textContent = texto;
  b.setAttribute("role", "menuitem");
  b.addEventListener("click", () => { if (fecha) fecharMenuAberto(); aoClicar(); });
  return b;
}
function sethLinkExportar(c, formato, rotulo) {
  const a = document.createElement("a"); a.className = "seth-menu-item"; a.setAttribute("role", "menuitem");
  a.href = "/api/seth/conversa/exportar?id=" + encodeURIComponent(c.id) + "&formato=" + formato;
  a.download = ""; a.textContent = rotulo;
  a.addEventListener("click", () => fecharMenuAberto());
  return a;
}
// Uma linha por conversa: título (com reticências), selos e o menu "Mais ações de <título>".
function sethLinha(c) {
  const linha = document.createElement("div");
  linha.className = "seth-item" + (c.id === sethAtual.id ? " ativa" : "") + (c.fixada ? " fixada" : "");
  const tituloLido = tituloDaLista(c.titulo) || "sem título";
  const abrir = document.createElement("button"); abrir.type = "button"; abrir.className = "seth-item-abrir"; abrir.textContent = tituloLido;
  abrir.title = tituloLido + " · " + c.mensagens + " mensagens · " + c.atualizada;
  if (c.id === sethAtual.id) abrir.setAttribute("aria-current", "true");
  abrir.addEventListener("click", () => sethAbrir(c.id));
  const meta = document.createElement("div"); meta.className = "seth-item-meta";
  if (c.fixada) meta.append(sethSelo("Fixada", "seth-selo-fixada"));
  if (c.arquivada) meta.append(sethSelo("Arquivada", "seth-selo-arquivada"));
  const pasta = sethLista.pastas.find((p) => p.id === c.pasta);
  if (pasta) meta.append(sethSelo("Pasta: " + pasta.nome, "seth-selo-pasta"));
  (c.marcadores || []).forEach((m) => meta.append(sethSelo("#" + m, "seth-selo-marcador")));
  const mais = document.createElement("div"); mais.className = "seth-item-mais";
  const gatilho = document.createElement("button"); gatilho.type = "button"; gatilho.className = "seth-mais-gatilho";
  gatilho.textContent = "Mais";
  gatilho.setAttribute("aria-haspopup", "menu"); gatilho.setAttribute("aria-expanded", "false");
  gatilho.setAttribute("aria-label", "Mais ações de " + tituloLido);
  const menu = document.createElement("div"); menu.className = "seth-menu"; menu.setAttribute("role", "menu"); menu.hidden = true;
  const renomear = sethItemMenu("Renomear", () => sethRenomear(c, linha));
  const fixar = sethItemMenu(c.fixada ? "Desfixar" : "Fixar", () => sethOrganizar(c.id, {fixada: !c.fixada}));
  const arquivar = sethItemMenu(c.arquivada ? "Desarquivar" : "Arquivar", () => sethOrganizar(c.id, {arquivada: !c.arquivada}));
  // Apagar leva a conversa para a Lixeira (09/11/2026); a purga definitiva fica só na própria Lixeira.
  const apagar = sethItemMenu("Apagar", () => {
    if (apagar.dataset.confirma !== "1") { apagar.dataset.confirma = "1"; apagar.textContent = "Confirmar: mover para a Lixeira"; return; }
    fecharMenuAberto(); sethApagar(c.id);
  }, false);
  const org = document.createElement("details"); org.className = "seth-item-org";
  org.setAttribute("aria-label", "Pasta e marcadores da conversa " + tituloLido);
  const resumo = document.createElement("summary"); resumo.textContent = "Pasta e marcadores";
  org.append(resumo, sethCampoPasta(c), sethCampoMarcadores(c));
  menu.append(renomear, fixar, arquivar, apagar, sethLinkExportar(c, "json", "Exportar JSON"), sethLinkExportar(c, "md", "Exportar Markdown"), org);
  mais.append(gatilho, menu);
  ligarMenu(gatilho, menu);
  linha.append(abrir, meta, mais);
  return linha;
}
// Cópia de uma mensagem (usuário ou Seth), com a mesma confirmação curta do botão de resposta.
function sethCopiarMensagem(texto) {
  const b = sethTexto("Copiar", async () => {
    try { await navigator.clipboard.writeText(texto); b.textContent = "Copiado"; } catch (_) { b.textContent = "Não foi possível copiar"; }
    setTimeout(() => { b.textContent = "Copiar"; }, 1600);
  });
  return b;
}
// Conversa: "Nova conversa" e a lista levam à Conversa; a gaveta fecha ao escolher.
function abrirConversaNoPainel() {
  const conversa = byId("conversa");
  if (conversa && conversa.hidden) irPara("conversa");
  setGaveta(false);
}
// Aviso de rolagem: "Ir para o fim" aparece quando a transcrição não está no fim.
function sethNoFim(log) { return !(log.scrollHeight - log.scrollTop - log.clientHeight > 48); }
function sethAtualizarFim() {
  const log = byId("seth-transcript"); const botao = byId("seth-ir-fim");
  if (!log || !botao) return;
  botao.hidden = sethNoFim(log);
}
// Ligação dos menus e da rolagem da Conversa (uma vez, com o formulário).
function ligarCompositorEMenus() {
  ligarMenu(byId("seth-mais-abrir"), byId("seth-mais-menu"), true);
  byId("seth-export-json").setAttribute("role", "menuitem");
  byId("seth-export-md").setAttribute("role", "menuitem");
  const log = byId("seth-transcript");
  log.addEventListener("scroll", sethAtualizarFim);
  byId("seth-ir-fim").addEventListener("click", () => { log.scrollTop = log.scrollHeight; sethAtualizarFim(); });
}
// Diálogo "Organizar conversas" (padrão de dialog do painel): abre pelo menu e fecha pelo botão ou pelo fundo.
const dialogOrganizar = byId("organizar-dialog");
byId("organizar-abrir").addEventListener("click", () => { if (dialogOrganizar.showModal) dialogOrganizar.showModal(); });
dialogOrganizar.querySelectorAll(".close-organizar").forEach((b) => b.addEventListener("click", () => dialogOrganizar.close()));
dialogOrganizar.addEventListener("click", (event) => { if (event.target === dialogOrganizar) dialogOrganizar.close(); });
function sethCampoPasta(c) {
  const rotulo = document.createElement("label"); rotulo.className = "seth-org-campo";
  const select = document.createElement("select"); select.className = "seth-org-pasta";
  select.append(sethOpcao("", "Sem pasta"), ...sethLista.pastas.map((p) => sethOpcao(p.id, p.nome)));
  select.value = c.pasta || "";
  select.addEventListener("change", () => sethOrganizar(c.id, {pasta: select.value || null}));
  rotulo.append(document.createTextNode("Pasta "), select);
  return rotulo;
}
function sethCampoMarcadores(c) {
  const bloco = document.createElement("div"); bloco.className = "seth-org-campo";
  const titulo = document.createElement("span"); titulo.textContent = "Marcadores";
  const lista = document.createElement("div"); lista.className = "seth-marcadores";
  (c.marcadores || []).forEach((m) => {
    const tirar = sethTexto("tirar", () => sethOrganizar(c.id, {marcadores: (c.marcadores || []).filter((x) => x !== m)}));
    tirar.setAttribute("aria-label", "Tirar o marcador " + m);
    lista.append(sethSelo("#" + m, "seth-selo-marcador"), tirar);
  });
  const form = document.createElement("form"); form.className = "seth-marcador-form";
  const campo = document.createElement("input"); campo.type = "text"; campo.maxLength = 24; campo.placeholder = "novo marcador";
  campo.setAttribute("aria-label", "Novo marcador");
  const adicionar = document.createElement("button"); adicionar.type = "submit"; adicionar.className = "text-link"; adicionar.textContent = "Adicionar";
  form.append(campo, adicionar);
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const novo = campo.value.trim();
    if (!novo) { sethMostrarOrg("Digite o marcador antes de adicionar."); return; }
    sethOrganizar(c.id, {marcadores: [...(c.marcadores || []), novo]});
  });
  bloco.append(titulo, lista, form);
  return bloco;
}
async function sethOrganizar(id, campos) {
  let ok = false;
  try {
    const r = await fetch("/api/seth/conversa/organizar", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"},
      body: JSON.stringify({id, ...campos})});
    if (!r.ok) sethMostrarOrg(sethErroOrg(r.status, await sethMotivo(r)));
    else { ok = true; sethMostrarOrg(""); }
  } catch (_) { sethMostrarOrg("Não foi possível salvar: sem resposta do painel."); }
  await sethListar();
  return ok;
}
// Pastas (projetos). Apagar pasta não apaga conversa: as conversas dela ficam sem pasta.
function sethPintarPastas() {
  const ul = byId("seth-pastas"); if (!ul) return;
  ul.replaceChildren();
  if (!sethLista.pastas.length) { const li = document.createElement("li"); li.append(sethVazio("Nenhuma pasta ainda. Crie uma para agrupar conversas.")); ul.append(li); return; }
  sethLista.pastas.forEach((p) => ul.append(sethLinhaPasta(p)));
}
function sethLinhaPasta(p) {
  const li = document.createElement("li"); li.className = "seth-pasta";
  const nome = document.createElement("button"); nome.type = "button"; nome.className = "seth-item-abrir";
  nome.textContent = p.nome + " (" + p.conversas + ")"; nome.title = "Mostrar só as conversas desta pasta";
  nome.addEventListener("click", () => { sethFiltro = {pasta: p.id, marcador: sethFiltro.marcador}; sethPintarLista(); });
  const acoes = document.createElement("div"); acoes.className = "seth-item-acoes";
  const renomear = sethTexto("Renomear", () => sethRenomearPasta(p, li));
  const apagar = sethTexto("Apagar", () => {
    if (apagar.dataset.confirma !== "1") { apagar.dataset.confirma = "1"; apagar.textContent = "Confirmar apagar pasta"; return; }
    sethPastaMudar({acao: "apagar", id: p.id});
  });
  acoes.append(renomear, apagar);
  li.append(nome, acoes);
  return li;
}
function sethRenomearPasta(p, li) {
  const campo = document.createElement("input"); campo.type = "text"; campo.value = p.nome; campo.maxLength = 60; campo.className = "seth-renomear";
  campo.setAttribute("aria-label", "Novo nome da pasta");
  li.replaceChildren(campo); campo.focus();
  campo.addEventListener("keydown", (e) => { if (e.key === "Enter") sethPastaMudar({acao: "renomear", id: p.id, nome: campo.value}); if (e.key === "Escape") sethPintarLista(); });
  campo.addEventListener("blur", () => sethPintarLista());
}
function sethAvisoPasta(acao, dados) {
  if (acao === "criar") return "Pasta criada: " + dados.nome + ".";
  if (acao === "renomear") return "Pasta renomeada: " + dados.nome + ".";
  const n = dados.conversas_soltas || 0;
  if (!n) return "Pasta apagada. Não havia conversas nela.";
  if (n === 1) return "Pasta apagada. A conversa dela continua na lista, sem pasta.";
  return "Pasta apagada. As " + n + " conversas dela continuam na lista, sem pasta.";
}
async function sethPastaMudar(corpo) {
  let ok = false;
  try {
    const r = await fetch("/api/seth/pastas", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: JSON.stringify(corpo)});
    if (!r.ok) sethMostrarOrg(sethErroOrg(r.status, await sethMotivo(r)));
    else { ok = true; sethMostrarOrg(sethAvisoPasta(corpo.acao, await r.json())); }
  } catch (_) { sethMostrarOrg("Não foi possível salvar a pasta: sem resposta do painel."); }
  await sethListar();
  return ok;
}
// Busca nas conversas salvas. Resposta antiga (de uma digitação anterior) não sobrescreve a atual.
async function sethBuscar(texto) {
  const termo = String(texto || "").trim();
  if (!termo) { sethLimparBusca(); return; }
  const seq = ++sethBuscaSeq;
  const box = byId("seth-busca-resultados");
  byId("seth-conversas").hidden = true; byId("seth-arquivadas-bloco").hidden = true;
  box.hidden = false; box.replaceChildren(sethVazio("Buscando…"));
  byId("seth-lixeira-bloco").hidden = true;
  try {
    const r = await fetch("/api/seth/conversas/busca?q=" + encodeURIComponent(termo), {headers: {Accept: "application/json"}, credentials: "same-origin", cache: "no-store"});
    if (seq !== sethBuscaSeq) return;
    if (!r.ok) { box.replaceChildren(sethVazio(sethErroBusca(r.status, await sethMotivo(r)))); return; }
    const dados = await r.json();
    if (seq === sethBuscaSeq) sethPintarBusca(dados);
  } catch (_) { if (seq === sethBuscaSeq) box.replaceChildren(sethVazio("Busca indisponível: sem resposta do painel.")); }
}
function sethErroBusca(status, motivo) {
  if (status === 400) return "Busca não feita: " + (motivo || "termo recusado") + ".";
  return "Busca indisponível: o painel respondeu com erro " + status + ".";
}
function sethPintarBusca(dados) {
  const box = byId("seth-busca-resultados");
  const total = dados.total || 0; const lista = dados.resultados || [];
  box.replaceChildren();
  let resumo = "Nenhuma conversa salva tem este texto (a busca vê só as conversas salvas).";
  if (total) resumo = total + (total === 1 ? " conversa salva tem este texto." : " conversas salvas têm este texto.") + (total > lista.length ? " Mostrando as " + lista.length + " primeiras." : "");
  box.append(sethVazio(resumo));
  lista.forEach((r) => box.append(sethResultado(r)));
}
function sethResultado(r) {
  const item = document.createElement("div"); item.className = "seth-resultado";
  const titulo = document.createElement("strong"); titulo.textContent = tituloDaLista(r.titulo);
  const trecho = document.createElement("p"); trecho.className = "seth-trecho"; trecho.textContent = r.trecho;
  const meta = document.createElement("p"); meta.className = "seth-resultado-meta";
  meta.textContent = (r.ocorrencias === 1 ? "1 ocorrência" : r.ocorrencias + " ocorrências") + (r.arquivada ? " · arquivada" : "") + " · " + (r.mensagem === null ? "no título" : "na mensagem " + (r.mensagem + 1));
  const abrir = sethTexto(r.mensagem === null ? "Abrir conversa" : "Abrir na mensagem " + (r.mensagem + 1), () => sethAbrir(r.id, r.mensagem));
  item.append(titulo, trecho, meta, abrir);
  return item;
}
function sethLimparBusca() {
  sethBuscaSeq++;
  const campo = byId("seth-busca"); if (campo) campo.value = "";
  const box = byId("seth-busca-resultados"); box.replaceChildren(); box.hidden = true;
  byId("seth-conversas").hidden = false; byId("seth-arquivadas-bloco").hidden = false; byId("seth-lixeira-bloco").hidden = false;
}
// Durante a resposta da Seth a tela não troca de conversa: a resposta e o salvar são da conversa de origem (09/11/2026).
function sethTrocaBloqueada() {
  if (!sethRespondendo) return false;
  sethMostrarOrg("A Seth ainda está respondendo. Espere a resposta para trocar de conversa.");
  return true;
}
async function sethAbrir(id, indice = null) {
  abrirConversaNoPainel();
  if (sethTrocaBloqueada()) return;
  try {
    const dados = await fetchJson("/api/seth/conversa?id=" + encodeURIComponent(id), {headers: {Accept: "application/json"}});
    if (sethTrocaBloqueada()) return; // uma resposta começou enquanto a conversa carregava
    sethAtual = sethDeDados(dados);
    sethEditandoId = null;
    sethDesenhar(); sethListar(); sethMostrarModelo(); sethRestaurarRascunho();
    if (indice !== null) sethDestacar(indice);
  } catch (erro) { sethStatus("INDISPONÍVEL", "horizon"); }
}
// Leva à mensagem que a busca apontou: rola até ela e marca com a borda de destaque.
function sethDestacar(indice) {
  const alvo = byId("seth-transcript").querySelector('[data-indice="' + indice + '"]');
  if (!alvo) return;
  alvo.classList.add("destacada");
  if (typeof alvo.scrollIntoView === "function") alvo.scrollIntoView({block: "center"});
}
// Conversa temporária: não é gravada, não entra na lista nem na busca, e não tem exportação. Some ao trocar de conversa.
function sethPintarTemporaria() {
  const botao = byId("seth-temporaria"); const aviso = byId("seth-temporaria-aviso");
  if (!botao || !aviso) return;
  const ligada = Boolean(sethAtual.temporaria);
  botao.setAttribute("aria-pressed", ligada ? "true" : "false");
  // J5 (16/11/2026): interruptor curto; o texto longo vai para o title e para o aviso do rodapé.
  botao.textContent = "Temporária";
  botao.title = "Conversa temporária: " + (ligada ? "ligada" : "desligada") + ". Não é salva e não aparece na lista nem na busca.";
  // C12c: no celular o mesmo controle fica no menu Mais (espelho com o mesmo estado).
  const espelho = byId("seth-temporaria-menu");
  if (espelho) { espelho.setAttribute("aria-pressed", ligada ? "true" : "false"); espelho.textContent = "Conversa temporária: " + (ligada ? "ligada" : "desligada"); }
  aviso.hidden = !ligada;
}
function sethAlternarTemporaria() {
  if (sethTrocaBloqueada()) return;
  const ligar = !sethAtual.temporaria;
  sethAtual = sethNova(ligar); sethEditandoId = null;
  sethDesenhar(); sethListar(); sethRestaurarRascunho();
  sethStatus(ligar ? "TEMPORÁRIA" : "PRONTA", ligar ? "partial" : "planned");
  byId("seth-input").focus();
}
function sethPintarExportar() {
  const texto = byId("seth-exportar-texto"); const json = byId("seth-export-json"); const md = byId("seth-export-md");
  if (!texto || !json || !md) return;
  const salva = Boolean(sethAtual.id) && !sethAtual.temporaria;
  json.hidden = !salva; md.hidden = !salva;
  if (salva) {
    json.href = "/api/seth/conversa/exportar?id=" + encodeURIComponent(sethAtual.id) + "&formato=json";
    md.href = "/api/seth/conversa/exportar?id=" + encodeURIComponent(sethAtual.id) + "&formato=md";
  }
  if (sethAtual.temporaria) texto.textContent = "Conversa temporária não é salva, por isso não há o que exportar.";
  else texto.textContent = salva ? "Exporta a última gravação." : "Exporta depois de salvar (uma resposta basta).";
}
// Importa um JSON exportado. O servidor valida o formato e não duplica: se o id ou a origem já existe, não grava.
async function sethImportar(arquivo) {
  if (!arquivo) return;
  if (arquivo.size > SETH_LIMITE_IMPORTACAO_BYTES) { sethMostrarOrg("Arquivo não importado: passa do limite de " + SETH_LIMITE_IMPORTACAO_BYTES + " bytes (257 KB)."); return; }
  try {
    const texto = await arquivo.text();
    const r = await fetch("/api/seth/conversa/importar", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: texto});
    if (!r.ok) { sethMostrarOrg(sethErroImportacao(r.status, await sethMotivo(r))); }
    else {
      const dados = await r.json();
      if (dados.estado === "importada") sethMostrarOrg("Conversa importada: " + dados.titulo + ".");
      else if (dados.lixeira) sethMostrarOrg("Esta conversa já estava na Lixeira (" + dados.titulo + "); nada foi duplicado. Restaure-a por lá.");
      else sethMostrarOrg("Esta conversa já estava aqui (" + dados.titulo + "); nada foi duplicado.");
    }
  } catch (_) { sethMostrarOrg("Não foi possível importar: sem resposta do painel."); }
  await sethListar();
}
function sethErroImportacao(status, motivo) {
  if (status === 413) return "Arquivo não importado: passa do limite de " + SETH_LIMITE_IMPORTACAO_BYTES + " bytes (257 KB).";
  if (status === 400) return "Arquivo não importado: " + (motivo || "arquivo recusado") + ".";
  if (status === 409) return "Arquivo não importado: a organização das conversas está ilegível; nada foi alterado.";
  return "Arquivo não importado: o painel respondeu com erro " + status + ".";
}
// Só a resposta da Seth leva o modelo escolhido (modelo) e o real (modelo_real, cabeçalho do gateway). O servidor recusa modelo escolhido fora da lista.
function sethParaSalvar(m) {
  const item = {role: m.role, content: m.content};
  if (m.hora) item.hora = m.hora; // C5: a hora vai gravada (ISO 8601 com fuso)
  if (m.role === "user" && m.anexos && m.anexos.length) item.anexos = m.anexos.map((a) => ({nome: a.nome, caracteres: a.caracteres})); // C9: só metadado
  if (m.role === "assistant") {
    if (m.modelo) item.modelo = m.modelo;
    if (m.modelo_real) item.modelo_real = m.modelo_real;
    if (m.interrompida) item.interrompida = true;
    if (m.feedback) item.feedback = {...m.feedback};
    if (m.cortes && m.cortes.length) item.cortes = [...m.cortes];
  }
  return item;
}
// Grava a conversa `alvo` (por padrão, a aberta). O id e o aviso são gravados nela, não na tela: se a tela trocou
// durante o await, só a conversa de origem muda e a tela não é repintada com ela (09/11/2026).
async function sethSalvar(alvo = sethAtual) {
  if (alvo.temporaria || !alvo.nos.length) return false; // conversa temporária nunca é gravada
  const caminho = sethCaminhoDe(alvo.folha, alvo);
  if (!caminho.length) return false;
  if (!alvo.titulo) alvo.titulo = caminho[0].content.slice(0, 60);
  // C8: as instruções da conversa vão em cada gravação ("" limpa); o servidor descarta o que estiver vazio.
  const corpo = {id: alvo.id, titulo: alvo.titulo, modelo: alvo.modelo, instrucoes: alvo.instrucoes || ""};
  // Com ramo, vai a árvore (o caminho sai dela); sem ramo, a lista de sempre.
  if (alvo.nos.length > caminho.length) corpo.arvore = {nos: alvo.nos.map(sethNoParaSalvar), folha: alvo.folha};
  else corpo.mensagens = caminho.map(sethParaSalvar);
  if (alvo.ramificada_de) corpo.ramificada_de = alvo.ramificada_de;
  const texto = JSON.stringify(corpo);
  if (new TextEncoder().encode(texto).length > SETH_LIMITE_CONVERSA_BYTES) { sethNaoSalvou(sethMotivoRecusa(413), true, alvo); return false; }
  try {
    const r = await fetch("/api/seth/conversa", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: texto});
    if (!r.ok) { sethNaoSalvou(sethMotivoRecusa(r.status, await sethMotivo(r)), r.status === 413 || r.status === 400, alvo); return false; }
    const dados = await r.json(); alvo.id = dados.id; alvo.naoSalva = "";
    if (alvo === sethAtual) { sethPintarAvisoSalvar(); sethTitulo(alvo.titulo); }
    sethListar();
    return true;
  } catch (_) { sethNaoSalvou("sem resposta do painel", false, alvo); return false; }
}
/* Aviso persistente de conversa não salva (seth-salvar-aviso). Fica na aba até uma gravação dar certo ou a conversa trocar. */
function sethNaoSalvou(motivo, comecarDeNova, alvo = sethAtual) {
  const guardado = alvo.id ? "O que está guardado é a última gravação feita; o que veio depois não está salvo." : "Nada desta conversa está guardado ainda.";
  const texto = "Conversa não salva: " + motivo + ". " + guardado + (comecarDeNova ? " Para seguir salvando, comece uma conversa nova." : "");
  alvo.naoSalva = texto;
  if (alvo === sethAtual) { sethPintarAvisoSalvar(); return; }
  sethMostrarAviso("A conversa \"" + alvo.titulo + "\" não foi salva: " + motivo + ". Abra-a para conferir.");
}
/* Texto do motivo quando o painel recusa a gravação: 413 é tamanho; 400 é regra, com o detalhe que o servidor devolve. */
function sethMotivoRecusa(status, motivo) {
  if (status === 413) return "a conversa passou de " + SETH_LIMITE_CONVERSA_BYTES + " bytes (256 KB), o limite de cada gravação";
  if (status === 400) return "o painel recusou a conversa (" + (motivo || "sem detalhe") + ")";
  return "o painel respondeu com erro " + status;
}
/* Aviso de uma gravação que falhou sem ser da conversa aberta (ex.: renomear uma conversa fechada). Some na próxima atualização da aba. */
function sethMostrarAviso(texto) {
  const aviso = byId("seth-salvar-aviso"); if (!aviso) return;
  aviso.textContent = texto; aviso.hidden = false;
}
function sethPintarAvisoSalvar() {
  const aviso = byId("seth-salvar-aviso"); if (!aviso) return;
  aviso.textContent = sethAtual.naoSalva || ""; aviso.hidden = !sethAtual.naoSalva;
}
// Apagar leva a conversa para a Lixeira (09/11/2026). Só sai da tela quando o painel confirma (r.ok).
async function sethApagar(id) {
  if (id === sethAtual.id && sethRespondendo) { sethMostrarOrg("A Seth ainda está respondendo. Espere a resposta para apagar esta conversa."); return; }
  try {
    const r = await fetch("/api/seth/conversa/apagar", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: JSON.stringify({id})});
    if (!r.ok) sethMostrarOrg(sethErroApagar(r.status, await sethMotivo(r)));
    else {
      if (id === sethAtual.id) { sethAtual = sethNova(false); sethDesenhar(); sethRestaurarRascunho(); }
      sethMostrarOrg("Conversa movida para a Lixeira. Restaure-a por lá, se precisar.");
    }
  } catch (_) { sethMostrarOrg("Não foi possível apagar a conversa: sem resposta do painel."); }
  await sethListar();
}
function sethErroApagar(status, motivo) {
  if (status === 404) return "Conversa não encontrada; a lista foi atualizada.";
  if (status === 409) return "Não foi possível apagar: " + (motivo || "a organização está ilegível") + ".";
  return "Não foi possível apagar a conversa: o painel respondeu com erro " + status + ".";
}
function sethRenomear(c, linha) {
  const campo = document.createElement("input"); campo.type = "text"; campo.value = c.titulo; campo.maxLength = 80; campo.className = "seth-renomear"; campo.setAttribute("aria-label", "Novo nome da conversa");
  linha.replaceChildren(campo); campo.focus();
  const confirmar = async () => {
    const novo = campo.value.trim() || c.titulo;
    if (c.id === sethAtual.id) { sethAtual.titulo = novo; sethSalvar(); return; }
    const dados = await fetchJson("/api/seth/conversa?id=" + encodeURIComponent(c.id), {headers: {Accept: "application/json"}});
    try {
      // Renomear grava a conversa inteira: com ramo, manda a árvore (senão os ramos sumiriam).
      const corpo = dados.arvore ? {id: c.id, titulo: novo, modelo: dados.modelo, arvore: dados.arvore} : {id: c.id, titulo: novo, modelo: dados.modelo, mensagens: dados.mensagens};
      if (dados.ramificada_de) corpo.ramificada_de = dados.ramificada_de;
      const r = await fetch("/api/seth/conversa", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: JSON.stringify(corpo)});
      if (!r.ok) sethMostrarAviso("Não foi possível salvar o novo nome da conversa \"" + c.titulo + "\": " + sethMotivoRecusa(r.status, await sethMotivo(r)) + ".");
    } catch (_) { sethMostrarAviso("Não foi possível salvar o novo nome da conversa: sem resposta do painel."); }
    sethListar();
  };
  campo.addEventListener("keydown", (e) => { if (e.key === "Enter") confirmar(); if (e.key === "Escape") sethListar(); });
  campo.addEventListener("blur", () => sethListar());
}
function sethErro(status, motivo) {
  if (status === 429) return "outra conversa está em curso; tente de novo em instantes";
  if (status === 502) return "o gateway não respondeu; confira o serviço seth-gateway em Operação";
  if (status === 400 || status === 413) return "o painel recusou o pedido (" + (motivo || "sem detalhe") + ")";
  if (status) return "o painel respondeu com erro " + status;
  return "falha desconhecida";
}
/* Motivo que o servidor devolve no corpo de um erro (texto curto, em português; mostrado só em 400 e 413). */
async function sethMotivo(resposta) {
  try { return (await resposta.text()).trim().slice(0, 200); } catch (_) { return ""; }
}
/* Janela enviada ao gateway: as últimas 20 mensagens, cada uma com até 4000 caracteres, e o pedido inteiro até 262144 bytes.
   `pedido` (modelo, instruções e anexos) entra na conta do limite, como entra no corpo do pedido (C10).
   Corta o que passa do limite (a conversa salva não muda) e conta o que cortou ou deixou de fora, para o aviso. */
function sethJanela(mensagens, pedido = {}) {
  const marca = "\n[cortado pelo painel para caber no limite de " + SETH_MAX_CARACTERES + " caracteres]";
  const espaco = SETH_MAX_CARACTERES - Array.from(marca).length;
  let cortadas = 0;
  const janela = mensagens.slice(-SETH_MAX_MENSAGENS).map((m) => {
    const pontos = Array.from(m.content);
    if (pontos.length <= SETH_MAX_CARACTERES) return {role: m.role, content: m.content};
    cortadas++;
    return {role: m.role, content: pontos.slice(0, espaco).join("") + marca};
  });
  const bytes = (lista) => new TextEncoder().encode(JSON.stringify({mensagens: lista, ...pedido})).length;
  let deixadas = 0;
  while (janela.length > 1 && bytes(janela) > SETH_LIMITE_PEDIDO_BYTES) { janela.shift(); deixadas++; }
  return {mensagens: janela, cortadas, deixadas};
}
function sethAvisoJanela(janela) {
  if (!janela.cortadas && !janela.deixadas) return "";
  const partes = [];
  if (janela.cortadas) partes.push((janela.cortadas === 1 ? "1 mensagem antiga longa foi cortada" : janela.cortadas + " mensagens antigas longas foram cortadas") + " para " + SETH_MAX_CARACTERES + " caracteres");
  if (janela.deixadas) partes.push((janela.deixadas === 1 ? "1 mensagem mais antiga ficou" : janela.deixadas + " mensagens mais antigas ficaram") + " de fora, porque o pedido passou do tamanho máximo");
  return "Para responder, a Seth recebeu a conversa com ajuste: " + partes.join("; ") + ". A conversa salva continua completa.";
}
/* Stream SSE de /api/seth/chat/stream: linhas "data: {json}" separadas por linha em branco.
   Erro de transporte (sem stream, 404, 5xx, rede) antes do primeiro delta cai para /api/seth/chat inteiro.
   Erro do próprio stream (tipo "erro") mostra o motivo e não repete a pergunta. */
function sethErroStream(motivo) { return Object.assign(new Error(String(motivo || "falha no stream")), {motivoStream: true}); }
async function sethLerStream(mensagens, modelo, parcial, aoTexto, sinal, instrucoes = "", anexos = [], aoEstado = null) {
  const r = await fetch("/api/seth/chat/stream", {method: "POST", credentials: "same-origin", cache: "no-store", signal: sinal,
    headers: {"Content-Type": "application/json", Accept: "text/event-stream"}, body: JSON.stringify({mensagens, modelo, instrucoes, anexos})});
  if (!r.ok) throw Object.assign(new Error(sethErro(r.status, await sethMotivo(r))), {status: r.status});
  parcial.modelo_real = r.headers.get("X-Modelo-Real") || "";
  if (!r.body || typeof r.body.getReader !== "function" || typeof TextDecoder !== "function") throw Object.assign(new Error("navegador sem streaming"), {semStream: true});
  const leitor = r.body.getReader(); const decodificador = new TextDecoder("utf-8");
  let pendente = "", fim = false;
  const tratarBloco = (bloco) => {
    const dados = bloco.split("\n").filter((l) => l.startsWith("data: ")).map((l) => l.slice(6)).join("\n");
    if (!dados) return;
    let evento;
    try { evento = JSON.parse(dados); } catch (_) { throw sethErroStream("linha de dados inválida"); }
    if (evento.tipo === "texto" && typeof evento.delta === "string") { parcial.texto += evento.delta; aoTexto(evento.delta); }
    else if (evento.tipo === "uso") parcial.uso = {entrada: evento.entrada, saida: evento.saida}; // C11: uso informado pelo gateway
    else if (evento.tipo === "estado" && typeof evento.texto === "string") { if (aoEstado) aoEstado(evento.texto); } // 20/11: ferramenta em curso
    else if (evento.tipo === "modelo" && typeof evento.modelo === "string") { // 23/11: outra rodada, outro modelo
      const junto = parcial.modelo_real ? parcial.modelo_real + "+" + evento.modelo : evento.modelo;
      if (junto.length <= 120) parcial.modelo_real = junto;
    }
    else if (evento.tipo === "agata_code") (parcial.agata_code = parcial.agata_code || []).push(evento); // 20/11: trabalho do Agata Code
    else if (evento.tipo === "fim") fim = true;
    else if (evento.tipo === "erro") throw sethErroStream(evento.motivo);
  };
  try {
    for (;;) {
      const {value, done} = await leitor.read();
      if (done) break;
      pendente += decodificador.decode(value, {stream: true}).replace(/\r\n/g, "\n");
      const blocos = pendente.split("\n\n"); pendente = blocos.pop();
      blocos.forEach(tratarBloco);
    }
    pendente += decodificador.decode().replace(/\r\n/g, "\n");
    if (pendente.trim()) tratarBloco(pendente);
    if (!fim) throw sethErroStream("stream interrompido");
    return parcial.texto;
  } finally {
    try { await leitor.cancel(); } catch (_) { /* stream já fechado ou cancelado pelo Parar */ }
  }
}
async function sethChatInteiro(mensagens, modelo, parcial, sinal, instrucoes = "", anexos = []) {
  const r = await fetch("/api/seth/chat", {method: "POST", signal: sinal, headers: {"Content-Type": "application/json", Accept: "application/json"},
    body: JSON.stringify({messages: mensagens, modelo, instrucoes, anexos})});
  if (!r.ok) throw Object.assign(new Error(sethErro(r.status, await sethMotivo(r))), {status: r.status});
  parcial.modelo_real = r.headers.get("X-Modelo-Real") || "";
  const dados = await r.json();
  if (dados && dados.uso) parcial.uso = dados.uso; // C11: uso informado pelo gateway, quando houver
  return dados;
}
async function sethEnviar(texto, anexos = []) {
  if (sethEmCurso()) return;
  // A conversa de origem é capturada antes de qualquer await: a pergunta, a resposta e o salvar são dela (09/11/2026).
  const alvo = sethAtual;
  alvo.erro = null;
  // C9: a mensagem guarda só o metadado dos anexos (nome e caracteres); o texto vai no pedido desta vez.
  const metadado = anexos.length ? {anexos: anexos.map((a) => ({nome: a.nome, caracteres: a.caracteres}))} : {};
  const usuario = sethAdicionar({role: "user", content: texto, pai: alvo.folha, hora: sethHora(), ...metadado}, alvo);
  alvo.folha = usuario.id;
  sethDesenhar();
  await sethResponder({modo: "nova", alvo, paiId: usuario.id, novoUsuarioId: usuario.id, textoDoUsuario: texto, anexos});
}
// "Tentar de novo" (C7): reenvia a mesma pergunta (o ramo já existe na conversa; nada é duplicado).
function sethTentarDeNovo() {
  const erro = sethAtual.erro;
  if (!erro || !erro.paiId || sethEmCurso()) return;
  sethAtual.erro = null;
  sethDesenhar();
  sethResponder({modo: "nova", paiId: erro.paiId, anexos: erro.anexos || []});
}
function sethBlocoErro(erro) {
  const bloco = document.createElement("div"); bloco.className = "seth-erro-bloco";
  bloco.append(sethVazio("Não consegui responder agora: " + (erro.motivo || "falha desconhecida") + "."));
  if (erro.paiId) bloco.append(sethTexto("Tentar de novo", () => sethTentarDeNovo()));
  return bloco;
}
// Regenerar: a resposta nova é irmã da última; a antiga não some, vira outra versão ("< 1/2 >").
function sethRegerar() {
  const folha = sethNoPorId(sethAtual.folha);
  if (sethEmCurso() || !folha || folha.role !== "assistant" || !folha.pai) return;
  sethResponder({modo: "nova", paiId: folha.pai});
}
// Voz da Seth (11/11/2026, pedido do Humano: paridade com o chat anterior). Tudo com a voz do sistema.
// 1) Ouvir: o servidor fala a resposta em partes (POST /api/seth/ouvir) e diz se falou ou NÃO falou.
// 2) Ditar: o navegador grava o microfone e manda o áudio só ao painel (POST /api/seth/ditado); o texto entra no
//    campo para revisão. Nada vai à Seth sozinho.
// 3) Modo conversa (preferência guardada no navegador, desligada por padrão): lê cada resposta concluída. Esc ou Parar voz interrompem.
// Texto da voz, do ditado e dos avisos entra só por textContent.
const DITADO_MAX_MS = 60000;
const DITADO_MAX_BYTES = 2 * 1024 * 1024;
let vozLendo = false, vozFila = null, ditadoGravador = null, ditadoTimer = null, ditadoPedacos = [];
function vozEstado(texto, classe) { const e = byId("seth-voz-estado"); e.textContent = texto; e.className = "seth-voz-estado" + (classe ? " " + classe : ""); }
function vozBotaoParar(ligado) { byId("seth-voz-parar").hidden = !ligado; }
async function vozErro(resposta) {
  let motivo = "Não consegui agora (" + resposta.status + ").";
  try { const dados = await resposta.json(); if (dados && typeof dados.erro === "string") motivo = dados.erro; } catch (_) { /* resposta sem JSON */ }
  return motivo;
}
function vozEnviarParar() { fetch("/api/seth/ouvir/parar", {method: "POST"}).catch(() => {}); }
// Ler em voz alta. O botão Ouvir (automatico = false) não interrompe leitura em curso: pede para parar antes.
// O modo conversa (automatico = true) para a leitura atual e guarda esta resposta; só a mais nova fica na fila.
async function ouvirResposta(texto, automatico) {
  if (typeof texto !== "string" || !texto.trim()) return;
  if (vozLendo) {
    if (!automatico) { vozEstado("Já estou lendo em voz alta. Use Parar voz antes.", "erro"); return; }
    vozFila = texto;
    vozEstado("Parando a leitura anterior para ler a resposta nova.", "");
    vozEnviarParar();
    return;
  }
  vozLendo = true; vozBotaoParar(true); vozEstado("Lendo em voz alta…", "");
  let motivo = "", classe = "erro";
  try {
    const resposta = await fetch("/api/seth/ouvir", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({texto: texto})});
    if (resposta.ok) { const dados = await resposta.json(); motivo = typeof dados.motivo === "string" ? dados.motivo : ""; classe = dados.falou ? "ok" : "erro"; }
    else motivo = await vozErro(resposta);
  } catch (_) {
    motivo = "NÃO falei: não consegui falar com o painel agora.";
  }
  vozLendo = false; vozBotaoParar(false); vozEstado(motivo, classe);
  const proxima = vozFila; vozFila = null;
  if (proxima !== null && vozModoLigado()) ouvirResposta(proxima, true);
}
// Parar voz: interrompe entre trechos e descarta a fila. Sem leitura em curso, não chama o painel.
function vozParar() {
  vozFila = null;
  if (!vozLendo) return;
  vozEnviarParar();
  vozEstado("Parando: a leitura para depois do trecho que está tocando.", "");
}
function ditarMarcar(gravando) { const b = byId("seth-ditado"); b.setAttribute("aria-pressed", gravando ? "true" : "false"); b.textContent = gravando ? "Parar gravação" : "Ditar"; }
// Ditar: grava pelo microfone do navegador (o próprio navegador pede a permissão). Clique de novo, ou o limite de
// 60 s, para a gravação. O áudio vai só ao painel, que repassa ao ouvido local.
async function ditarPeloMicrofone() {
  if (ditadoGravador) { ditadoGravador.stop(); return; }
  if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== "function" || typeof window.MediaRecorder !== "function") {
    vozEstado("Este navegador não grava áudio aqui. Digite a mensagem.", "erro"); return;
  }
  let fluxo;
  try { fluxo = await navigator.mediaDevices.getUserMedia({audio: true}); }
  catch (erro) {
    const negado = erro && (erro.name === "NotAllowedError" || erro.name === "SecurityError");
    vozEstado(negado ? "Permissão do microfone negada. Libere o microfone para este endereço no navegador e tente de novo." : "Não consegui abrir o microfone. Confira se ele está ligado e livre.", "erro");
    return;
  }
  const tipo = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"].find((t) => MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(t)) || "";
  let gravador;
  try { gravador = new MediaRecorder(fluxo, tipo ? {mimeType: tipo, audioBitsPerSecond: 32000} : {audioBitsPerSecond: 32000}); }
  catch (_) { fluxo.getTracks().forEach((t) => t.stop()); vozEstado("Não consegui gravar neste navegador. Digite a mensagem.", "erro"); return; }
  ditadoPedacos = [];
  gravador.addEventListener("dataavailable", (e) => { if (e.data && e.data.size) ditadoPedacos.push(e.data); });
  gravador.addEventListener("stop", () => {
    clearTimeout(ditadoTimer);
    fluxo.getTracks().forEach((t) => t.stop());
    const blob = new Blob(ditadoPedacos, {type: gravador.mimeType || tipo || "audio/webm"});
    ditadoGravador = null; ditadoPedacos = [];
    ditarMarcar(false);
    enviarDitado(blob);
  });
  ditadoGravador = gravador;
  ditarMarcar(true);
  vozEstado("Gravando. Clique em Parar gravação quando terminar (limite de 60 segundos).", "");
  gravador.start(1000);
  ditadoTimer = setTimeout(() => { vozEstado("A gravação parou no limite de 60 segundos.", ""); if (ditadoGravador) ditadoGravador.stop(); }, DITADO_MAX_MS);
}
async function enviarDitado(blob) {
  const botao = byId("seth-ditado");
  if (!blob.size) { vozEstado("Nada foi gravado. Tente de novo.", "erro"); return; }
  if (blob.size > DITADO_MAX_BYTES) { vozEstado("Gravação grande demais: o limite é 2 MB, cerca de 60 segundos. Grave menos.", "erro"); return; }
  botao.disabled = true; vozEstado("Transcrevendo no ouvido local…", "");
  try {
    const resposta = await fetch("/api/seth/ditado", {method: "POST", headers: {"Content-Type": blob.type || "audio/webm"}, body: blob});
    if (!resposta.ok) { vozEstado(await vozErro(resposta), "erro"); return; }
    const dados = await resposta.json();
    const texto = dados && typeof dados.texto === "string" ? dados.texto : "";
    if (!texto) { vozEstado("Não veio texto da gravação. Tente de novo.", "erro"); return; }
    const campo = byId("seth-input");
    const atual = campo.value.trim();
    campo.value = (atual ? atual + " " + texto : texto).slice(0, 4000);
    campo.focus();
    vozEstado("Texto ditado. Revise e envie quando quiser.", "ok");
  } catch (_) {
    vozEstado("Não consegui mandar a gravação ao painel. Digite a mensagem.", "erro");
  } finally {
    botao.disabled = false;
  }
}
function vozLigarControles() {
  const modo = byId("seth-modo-conversa");
  modo.checked = vozModoLigado();
  modo.addEventListener("change", (e) => {
    vozGuardarModo(e.target.checked);
    if (!e.target.checked) vozFila = null;
    vozEstado(e.target.checked ? "Modo conversa ligado: cada resposta será lida em voz alta." : "Modo conversa desligado.", "");
  });
  byId("seth-voz-parar").addEventListener("click", vozParar);
  byId("seth-ditado").addEventListener("click", ditarPeloMicrofone);
}
/* Rascunho por conversa (C6): o texto do campo e os anexos pendentes ficam em sethRascunhos, por chave da conversa
   ("conversa-<id>", ou uma chave própria da conversa nova). Cada digitação grava; trocar de conversa restaura. */
function sethChaveNova() { sethSeqRascunho++; return "nova-" + sethSeqRascunho + "-" + Date.now().toString(36); }
function sethChaveRascunho(c = sethAtual) {
  if (!c.rascunho) c.rascunho = sethChaveNova();
  if (!c.id) return c.rascunho;
  // Conversa que acabou de ser gravada: o rascunho que era da conversa nova passa para a chave dela.
  const chave = "conversa-" + c.id;
  if (sethRascunhos.has(c.rascunho) && !sethRascunhos.has(chave)) { sethRascunhos.set(chave, sethRascunhos.get(c.rascunho)); sethRascunhos.delete(c.rascunho); }
  return chave;
}
function sethRascunhoDe(chave) { if (!sethRascunhos.has(chave)) sethRascunhos.set(chave, {texto: "", anexos: []}); return sethRascunhos.get(chave); }
// Digitação: grava o texto do campo no rascunho da conversa aberta (e apaga o rascunho vazio, sem anexos).
function sethGuardarTexto() {
  const chave = sethChaveRascunho(); const campo = byId("seth-input");
  const r = sethRascunhoDe(chave); r.texto = campo.value;
  if (!r.texto && !r.anexos.length) sethRascunhos.delete(chave);
}
// Voltar à conversa (ou abrir uma nova): o campo mostra o rascunho dela, vazio se não há; os anexos pendentes aparecem.
function sethRestaurarRascunho() {
  const campo = byId("seth-input"); if (!campo) return;
  const r = sethRascunhos.get(sethChaveRascunho());
  campo.value = r && r.texto ? r.texto : "";
  sethAtualizarComposicao();
}
// Enviado: o rascunho da conversa some (o texto e os anexos já foram para o pedido).
function sethLimparRascunho() { sethRascunhos.delete(sethChaveRascunho()); }

/* Anexos de texto (C9). Mesmas regras do servidor (chat_stream.py): até 3 por mensagem, nome sem barra nem "..",
   até 20000 caracteres cada e 40000 no total; imagem é recusada com a frase própria; texto vazio é recusado;
   arquivo acima de 80000 bytes é recusado antes de ser lido (X1). */
function sethMostrarAnexo(texto) { const aviso = byId("seth-anexo-aviso"); if (!aviso) return; aviso.textContent = texto || ""; aviso.hidden = !texto; }
function sethExtensao(nome) { const texto = String(nome); const i = texto.lastIndexOf("."); return i >= 0 ? texto.slice(i).toLowerCase() : ""; }
// Devolve o motivo da recusa ou "". Com texto null, confere só o que dá para ver antes de ler o arquivo.
function sethMotivoAnexo(nome, tipo, texto, atuais, tamanho) {
  const ext = sethExtensao(nome);
  if (String(tipo).startsWith("image/") || SETH_IMAGEM_EXTENSOES.includes(ext)) return "A conversa ainda não lê imagens.";
  if (atuais.length >= SETH_ANEXOS_MAX) return "Arquivo recusado: no máximo " + SETH_ANEXOS_MAX + " anexos por mensagem. Tire um para anexar outro.";
  const limpo = String(nome).trim();
  if (!limpo || limpo.length > SETH_ANEXO_NOME_MAX || /[\\/]/.test(limpo) || limpo.includes(".."))
    return "Arquivo recusado: nome inválido (sem barra, sem \"..\", até " + SETH_ANEXO_NOME_MAX + " caracteres).";
  if (!String(tipo).startsWith("text/") && !SETH_ANEXO_EXTENSOES.includes(ext))
    return "Arquivo recusado: a conversa lê só arquivos de texto (" + SETH_ANEXO_EXTENSOES.join(", ") + ").";
  if (tamanho !== undefined && Number(tamanho) > SETH_ANEXO_BYTES_MAX) return "Arquivo recusado: tem mais de " + SETH_ANEXO_BYTES_MAX + " bytes; o limite por arquivo é " + SETH_ANEXO_TEXTO_MAX + " caracteres.";
  if (texto === null) return "";
  if (!texto.trim()) return "Arquivo recusado: está vazio.";
  const n = Array.from(texto).length;
  if (n > SETH_ANEXO_TEXTO_MAX) return "Arquivo recusado: tem " + n.toLocaleString("pt-BR") + " caracteres; o limite por arquivo é " + SETH_ANEXO_TEXTO_MAX + ".";
  if (atuais.reduce((t, a) => t + a.caracteres, 0) + n > SETH_ANEXOS_TOTAL_MAX)
    return "Arquivo recusado: junto com os anexos já escolhidos, passaria de " + SETH_ANEXOS_TOTAL_MAX + " caracteres.";
  return "";
}
// Lê o arquivo como texto (FileReader, UTF-8). Vale para o botão Anexar, arrastar e soltar, e para o texto colado.
function sethLerTexto(arquivo) {
  return new Promise((ok, falha) => {
    const leitor = new FileReader();
    leitor.onload = () => ok(String(leitor.result || ""));
    leitor.onerror = () => falha(leitor.error);
    leitor.readAsText(arquivo, "utf-8");
  });
}
function sethDoArquivo(f) { return {nome: f.name, tipo: f.type, tamanho: f.size, lerTexto: () => sethLerTexto(f)}; }
// Anexa itens {nome, tipo, lerTexto} ao rascunho da conversa aberta; cada recusa vira um motivo na tela.
async function sethAnexar(itens) {
  const chave = sethChaveRascunho(); const motivos = [];
  for (const item of itens) {
    const nome = String(item.nome || ""); const tipo = String(item.tipo || "");
    const atuais = sethRascunhoDe(chave).anexos;
    // X1: o tamanho em bytes (File.size) é conferido antes da leitura; acima do teto o arquivo nem é lido.
    const previo = sethMotivoAnexo(nome, tipo, null, atuais, item.tamanho);
    if (previo) { motivos.push(previo); continue; }
    let texto = "";
    try { texto = await item.lerTexto(); }
    catch (_) { motivos.push("Arquivo recusado: não consegui ler \"" + nome + "\"."); continue; }
    const motivo = sethMotivoAnexo(nome, tipo, texto, sethRascunhoDe(chave).anexos);
    if (motivo) { motivos.push(motivo); continue; }
    sethRascunhoDe(chave).anexos.push({nome: nome.trim(), texto, caracteres: Array.from(texto).length});
  }
  if (sethChaveRascunho() === chave) { sethGuardarTexto(); sethAtualizarComposicao(); }
  sethMostrarAnexo(motivos.join(" "));
}
function sethTamanhoAnexo(n) { return n.toLocaleString("pt-BR") + " caracteres"; }
// Etiquetas removíveis acima do campo (nome e tamanho).
// Repinta a composição (etiquetas e linha de contexto, que conta os anexos pendentes).
function sethAtualizarComposicao() { sethPintarAnexos(); sethPintarContexto(sethCaminho()); }
function sethPintarAnexos() {
  const caixa = byId("seth-anexos"); if (!caixa) return;
  const anexos = sethAnexosDoRascunho();
  caixa.replaceChildren(...anexos.map((a, i) => {
    const etiqueta = document.createElement("span"); etiqueta.className = "seth-anexo";
    const nome = document.createElement("span"); nome.className = "seth-anexo-nome"; nome.textContent = a.nome;
    const tamanho = document.createElement("span"); tamanho.className = "seth-anexo-tamanho"; tamanho.textContent = sethTamanhoAnexo(a.caracteres);
    const remover = sethTexto("Remover", () => sethRemoverAnexo(i));
    remover.setAttribute("aria-label", "Remover anexo " + a.nome);
    etiqueta.append(nome, tamanho, remover);
    return etiqueta;
  }));
  caixa.hidden = !anexos.length;
}
function sethRemoverAnexo(i) {
  const r = sethRascunhos.get(sethChaveRascunho()); if (!r) return;
  r.anexos.splice(i, 1);
  sethGuardarTexto(); sethAtualizarComposicao(); sethMostrarAnexo("");
}
// Na mensagem desenhada do usuário: nome e caracteres, vindos do metadado gravado.
function sethEtiquetasAnexos(lista) {
  const caixa = document.createElement("div"); caixa.className = "msg-anexos";
  lista.forEach((a) => { const e = document.createElement("span"); e.className = "seth-anexo-marca"; e.textContent = a.nome + " · " + sethTamanhoAnexo(a.caracteres); caixa.append(e); });
  return caixa;
}

/* Instruções desta conversa (C8). Valem no modelo padrão da Seth; na via pública o gateway as descarta (aviso no diálogo). */
function sethPintarInstrucoes() { const chip = byId("seth-chip-instrucoes"); if (chip) chip.hidden = !sethAtual.instrucoes; }
function sethContarInstrucoes() {
  const n = Array.from(byId("seth-instrucoes-texto").value).length;
  byId("seth-instrucoes-contagem").textContent = n.toLocaleString("pt-BR") + " de " + SETH_INSTRUCOES_LIMITE + " caracteres";
}
function sethAbrirInstrucoes() {
  const campo = byId("seth-instrucoes-texto");
  campo.value = sethAtual.instrucoes || ""; sethContarInstrucoes(); byId("seth-instrucoes-erro").hidden = true;
  const dialogo = byId("seth-instrucoes-dialog");
  if (dialogo.showModal) dialogo.showModal();
  campo.focus();
}
function sethFecharInstrucoes() { const dialogo = byId("seth-instrucoes-dialog"); if (dialogo.close) dialogo.close(); }
// Salvar (sethSalvar): grava na conversa; conversa temporária fica só na aba.
function sethGuardarInstrucoes(texto) {
  const limpo = String(texto || "").trim();
  if (Array.from(limpo).length > SETH_INSTRUCOES_LIMITE) {
    const erro = byId("seth-instrucoes-erro"); erro.textContent = "As instruções passam de " + SETH_INSTRUCOES_LIMITE + " caracteres. Encurte o texto."; erro.hidden = false;
    return false;
  }
  sethAtual.instrucoes = limpo;
  sethPintarInstrucoes();
  sethSalvar();
  return true;
}

function ligarConversaSeth() {
  const form = byId("seth-form");
  if (!form || form.dataset.ligado) return;
  form.dataset.ligado = "1";
  ligarCompositorEMenus();
  sethExemplos(); sethDesenhar(); sethListar(); sethCarregarModelos();
  byId("seth-modelo").addEventListener("change", (e) => { sethAtual.modelo = e.target.value; sethMostrarModelo(); });
  const campo = byId("seth-input");
  campo.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
  byId("seth-nova").addEventListener("click", sethComecarNova);
  byId("seth-parar").addEventListener("click", sethParar);
  byId("seth-copiar-ultima").addEventListener("click", sethCopiarUltima);
  vozLigarControles();
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const texto = campo.value.trim();
    if (!texto || byId("seth-send").disabled) return;
    // Os anexos pendentes vão com esta pergunta; o rascunho da conversa é limpo ao enviar (C6, C9).
    const anexos = sethAnexosDoRascunho().slice();
    sethLimparRascunho();
    campo.value = "";
    sethAtualizarComposicao(); sethMostrarAnexo("");
    sethEnviar(texto, anexos);
  });
  // C6: cada digitação grava o rascunho da conversa aberta; a aba restaura o da conversa que abrir.
  campo.addEventListener("input", sethGuardarTexto);
  sethRestaurarRascunho();
  // C9: anexar pelo botão, arrastar e soltar sobre o compositor, ou colar texto longo (vira colado.txt).
  const entradaAnexo = byId("seth-anexo-arquivo");
  byId("seth-anexar").addEventListener("click", () => entradaAnexo.click());
  entradaAnexo.addEventListener("change", (e) => {
    const arquivos = Array.from(e.target.files || []);
    e.target.value = "";
    sethAnexar(arquivos.map(sethDoArquivo));
  });
  form.addEventListener("dragover", (e) => { e.preventDefault(); });
  form.addEventListener("drop", (e) => {
    e.preventDefault();
    const arquivos = e.dataTransfer ? Array.from(e.dataTransfer.files || []) : [];
    if (arquivos.length) sethAnexar(arquivos.map(sethDoArquivo));
  });
  campo.addEventListener("paste", (e) => {
    const texto = e.clipboardData ? e.clipboardData.getData("text") : "";
    if (Array.from(texto).length <= SETH_COLAR_LIMITE) return;
    e.preventDefault();
    sethAnexar([{nome: "colado.txt", tipo: "text/plain", lerTexto: async () => texto}]);
  });
  // C8: instruções da conversa, pelo item "Instruções desta conversa" do menu Mais.
  byId("seth-instrucoes-abrir").addEventListener("click", sethAbrirInstrucoes);
  const dialogoInstrucoes = byId("seth-instrucoes-dialog");
  byId("seth-instrucoes-texto").addEventListener("input", sethContarInstrucoes);
  byId("seth-instrucoes-salvar").addEventListener("click", () => { if (sethGuardarInstrucoes(byId("seth-instrucoes-texto").value)) sethFecharInstrucoes(); });
  byId("seth-instrucoes-limpar").addEventListener("click", () => {
    byId("seth-instrucoes-texto").value = ""; sethContarInstrucoes();
    if (sethGuardarInstrucoes("")) sethFecharInstrucoes();
  });
  byId("seth-instrucoes-fechar").addEventListener("click", sethFecharInstrucoes);
  byId("seth-instrucoes-x").addEventListener("click", sethFecharInstrucoes);
  dialogoInstrucoes.addEventListener("click", (e) => { if (e.target === dialogoInstrucoes) sethFecharInstrucoes(); });
  // C12c: no celular, o controle de conversa temporária também fica no menu Mais.
  byId("seth-temporaria-menu").addEventListener("click", sethAlternarTemporaria);
  // Organização (lote 3, 09/11/2026): temporária, busca, filtros, pastas e importação.
  byId("seth-temporaria").addEventListener("click", sethAlternarTemporaria);
  const busca = byId("seth-busca");
  busca.addEventListener("input", () => sethBuscar(busca.value));
  busca.addEventListener("keydown", (e) => { if (e.key === "Escape") sethLimparBusca(); });
  byId("seth-filtro-pasta").addEventListener("change", (e) => { sethFiltro.pasta = e.target.value; sethPintarLista(); });
  byId("seth-filtro-marcador").addEventListener("change", (e) => { sethFiltro.marcador = e.target.value; sethPintarLista(); });
  byId("seth-pasta-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const nomeCampo = byId("seth-pasta-nome"); const nome = nomeCampo.value.trim();
    if (!nome) { sethMostrarOrg("Digite o nome da pasta."); return; }
    if (await sethPastaMudar({acao: "criar", nome})) nomeCampo.value = "";
  });
  byId("seth-importar-arquivo").addEventListener("change", async (e) => {
    const arquivo = e.target.files && e.target.files[0];
    e.target.value = "";
    await sethImportar(arquivo);
  });
}
function sethNoParaSalvar(no) { return {id: no.id, pai: no.pai || null, ...sethParaSalvar(no)}; }

function sethNoPorId(id, c = sethAtual) { return c.nos.find((n) => n.id === id) || null; }

function sethCaminhoDe(id, c = sethAtual) {
  const caminho = []; const visto = new Set(); let no = sethNoPorId(id, c);
  while (no && !visto.has(no.id)) { visto.add(no.id); caminho.unshift(no); no = no.pai ? sethNoPorId(no.pai, c) : null; }
  return caminho;
}

function sethCaminho() { return sethCaminhoDe(sethAtual.folha); }

function sethFilhos(paiId, c = sethAtual) { return c.nos.filter((n) => (n.pai || null) === (paiId || null)); }

function sethIrmaos(no, c = sethAtual) { return sethFilhos(no.pai, c); }

function sethUltimaFolha(no, c = sethAtual) {
  let atual = no;
  for (;;) { const filhos = sethFilhos(atual.id, c); if (!filhos.length) return atual; atual = filhos[filhos.length - 1]; }
}

function sethNovoId(c = sethAtual) {
  let id;
  do { id = "k" + Math.random().toString(16).slice(2, 10); } while (sethNoPorId(id, c));
  return id;
}

function sethAdicionar(campos, c = sethAtual) {
  const no = {...campos, id: sethNovoId(c), pai: campos.pai || null};
  c.nos.push(no);
  return no;
}

function sethNosDeMensagens(lista) {
  return lista.map((m, i) => ({...m, id: "c" + i, pai: i ? "c" + (i - 1) : null}));
}

function sethDeDados(dados) {
  const arvore = dados.arvore && Array.isArray(dados.arvore.nos) ? dados.arvore : null;
  const nos = arvore ? arvore.nos.map((n) => ({...n, pai: n.pai || null})) : sethNosDeMensagens(dados.mensagens || []);
  const folha = arvore ? arvore.folha : (nos.length ? nos[nos.length - 1].id : null);
  return {id: dados.id, titulo: dados.titulo, modelo: dados.modelo || SETH_MODELO_PADRAO, temporaria: false, nos, folha,
    ramificada_de: dados.ramificada_de || null, instrucoes: typeof dados.instrucoes === "string" ? dados.instrucoes : "", erro: null};
}

function sethKb(bytes) { return (bytes / 1024).toLocaleString("pt-BR", {maximumFractionDigits: 1}) + " KB"; }

function sethMensagensParaEnvio(caminho) {
  // Resposta interrompida antes do primeiro texto fica na conversa, mas não vai ao gateway (conteúdo vazio).
  return caminho.filter((m) => m.role === "user" || m.content);
}

// Anexos pendentes do rascunho desta conversa (C9), sem criar rascunho ao ler.
function sethAnexosDoRascunho() { const r = sethRascunhos.get(sethChaveRascunho()); return r && Array.isArray(r.anexos) ? r.anexos : []; }
// Parte do pedido que não é a janela: modelo, instruções da conversa e anexos (corpo de sethLerStream / sethChatInteiro).
function sethPedidoBase(anexos, c = sethAtual) {
  return {modelo: c.modelo, instrucoes: c.instrucoes || "", anexos: anexos.map((a) => ({nome: a.nome, texto: a.texto}))};
}
// Indicador de resposta em curso (C4): um cursor no fim do texto; some ao concluir (a transcrição é refeita).
function sethCursor() { const c = document.createElement("span"); c.className = "seth-digitando"; c.setAttribute("aria-hidden", "true"); return c; }
function sethPintarContexto(caminho) {
  const texto = byId("seth-contexto"); const barra = byId("seth-contexto-barra"); const detalhe = byId("seth-contexto-detalhe");
  if (!texto || !barra) return;
  const pendentes = sethAnexosDoRascunho();
  if (!caminho.length && !pendentes.length) {
    texto.textContent = "Contexto: vazio"; barra.value = 0;
    if (detalhe) detalhe.textContent = "A conversa está vazia. A Seth só recebe o que você escrever agora.";
    return;
  }
  const pedido = sethPedidoBase(pendentes);
  const janela = sethJanela(sethMensagensParaEnvio(caminho), pedido);
  const bytes = new TextEncoder().encode(JSON.stringify({mensagens: janela.mensagens, ...pedido})).length;
  // A conta inclui os anexos pendentes (C10): entram nos caracteres e nos bytes da próxima pergunta.
  const caracteres = janela.mensagens.reduce((total, m) => total + Array.from(m.content).length, 0)
    + pendentes.reduce((total, a) => total + a.caracteres, 0);
  const pct = Math.min(100, Math.round((bytes / SETH_LIMITE_PEDIDO_BYTES) * 1000) / 10); // uma casa decimal
  barra.value = pct;
  // C11: com uso informado pelo gateway no último pedido desta conversa, mostra os tokens; sem ele, a estimativa em caracteres.
  const uso = sethUso && sethUso.alvo === sethAtual ? sethUso : null;
  // Linha curta na faixa de baixo; o texto completo (caracteres, limite, uso) fica no details "Detalhes" (J3).
  texto.textContent = "Contexto: " + pct.toLocaleString("pt-BR", {maximumFractionDigits: 1}) + "% · " + janela.mensagens.length + " de " + caminho.length + " mensagens";
  if (detalhe) detalhe.textContent = "Contexto da próxima pergunta: " + caracteres.toLocaleString("pt-BR") + " caracteres, " + sethKb(bytes)
    + " de " + sethKb(SETH_LIMITE_PEDIDO_BYTES) + " (" + pct.toLocaleString("pt-BR", {maximumFractionDigits: 1}) + "%). Vão " + janela.mensagens.length + " de " + caminho.length
    + " mensagens. Se passar do limite, as mais antigas ficam de fora; a conversa salva continua completa."
    + (uso ? " Último pedido: entrada " + uso.entrada.toLocaleString("pt-BR") + " · saída " + uso.saida.toLocaleString("pt-BR") + " tokens (informado pelo gateway)."
      : " Medida: estimativa em caracteres.");
}

function sethPintarOrigem() {
  const p = byId("seth-origem"); if (!p) return;
  const rd = sethAtual.ramificada_de;
  if (!rd) { p.hidden = true; p.replaceChildren(); return; }
  const origem = sethLista.items.find((c) => c.id === rd.id);
  const partes = [document.createTextNode("Conversa ramificada " + (origem ? "da conversa «" + origem.titulo + "»" : "de outra conversa (que não está mais na lista)") + ", a partir da mensagem " + (rd.mensagem + 1) + ". ")];
  if (origem) partes.push(sethTexto("Abrir a original", () => sethAbrir(origem.id)));
  p.replaceChildren(...partes);
  p.hidden = false;
}

function sethPintarParar() {
  const botao = byId("seth-parar"); if (botao) botao.hidden = !sethEmCurso();
  const envio = byId("seth-send"); if (envio) envio.hidden = sethEmCurso();
}

function sethEmCurso() { return sethRespondendo; } // uma só trava: a mesma da troca de conversa (sethTrocaBloqueada)

function sethParar() { if (sethControle) sethControle.abort(); }

function sethCorpo(no, destino) {
  const pontos = Array.from(String(no.content || ""));
  const cortes = [...new Set(no.cortes || [])].filter((c) => c > 0 && c < pontos.length).sort((a, b) => a - b);
  let inicio = 0;
  [...cortes, pontos.length].forEach((fim, i) => {
    if (i > 0) { const marca = document.createElement("p"); marca.className = "seth-continuacao"; marca.textContent = "Continuação"; destino.append(marca); }
    sethMarkdown(pontos.slice(inicio, fim).join(""), destino);
    inicio = fim;
  });
}

function sethRamo(no, irmaos) {
  const k = irmaos.findIndex((n) => n.id === no.id);
  const nav = document.createElement("div"); nav.className = "seth-ramo";
  const anterior = sethTexto("<", () => sethTrocarVersao(irmaos[k - 1]));
  anterior.disabled = k === 0; anterior.setAttribute("aria-label", "Versão anterior");
  const contagem = document.createElement("span"); contagem.textContent = (k + 1) + "/" + irmaos.length;
  const seguinte = sethTexto(">", () => sethTrocarVersao(irmaos[k + 1]));
  seguinte.disabled = k === irmaos.length - 1; seguinte.setAttribute("aria-label", "Versão seguinte");
  nav.append(anterior, contagem, seguinte);
  return nav;
}

function sethTrocarVersao(irmao) {
  if (!irmao || sethEmCurso()) return;
  sethEditandoId = null;
  sethAtual.folha = sethUltimaFolha(irmao).id;
  sethDesenhar();
  if (!sethAtual.temporaria) sethSalvar();
}

function sethAcoesMensagem(m, indice) {
  const bloco = document.createElement("div"); bloco.className = "msg-rodape";
  const acoes = document.createElement("div"); acoes.className = "msg-acoes";
  if (m.role === "user") {
    acoes.append(sethTexto("Editar", () => { if (sethEmCurso()) return; sethEditandoId = m.id; sethDesenhar(); }));
    acoes.append(sethCopiarMensagem(m.content));
  } else {
    const copiar = document.createElement("button"); copiar.type = "button"; copiar.className = "text-link"; copiar.textContent = "Copiar";
    copiar.addEventListener("click", async () => { try { await navigator.clipboard.writeText(m.content); copiar.textContent = "Copiado"; } catch (_) { copiar.textContent = "Não foi possível copiar"; } setTimeout(() => copiar.textContent = "Copiar", 1600); });
    acoes.append(copiar);
    if (m.content) acoes.append(sethTexto("Ouvir", () => ouvirResposta(m.content, false)));
    if (m.id === sethAtual.folha) {
      acoes.append(sethTexto("Regenerar", () => sethRegerar()));
      if (m.content) acoes.append(sethTexto("Continuar", () => sethContinuar()));
    }
  }
  if (!sethAtual.temporaria) acoes.append(sethTexto("Ramificar aqui", () => sethRamificar(indice)));
  bloco.append(acoes);
  if (m.role === "assistant") bloco.append(sethFeedback(m));
  return bloco;
}

function sethFeedback(m) {
  const bloco = document.createElement("div"); bloco.className = "seth-feedback";
  const botoes = document.createElement("div"); botoes.className = "seth-feedback-botoes";
  const nota = m.feedback ? m.feedback.nota : "";
  // Sem emoji (decisão E-2, 16/10): texto curto. A nota gravada continua "bom" (útil) e "ruim" (não útil).
  const util = sethTexto("Útil", () => sethMarcarFeedback(m, "bom"));
  util.setAttribute("aria-label", "Resposta útil"); util.setAttribute("aria-pressed", String(nota === "bom")); util.title = "Resposta útil";
  const naoUtil = sethTexto("Não útil", () => sethMarcarFeedback(m, "ruim"));
  naoUtil.setAttribute("aria-label", "Resposta não útil"); naoUtil.setAttribute("aria-pressed", String(nota === "ruim")); naoUtil.title = "Resposta não útil";
  botoes.append(util, naoUtil);
  bloco.append(botoes);
  if (m.feedback) {
    const campo = document.createElement("input"); campo.type = "text"; campo.maxLength = SETH_FEEDBACK_MOTIVO_LIMITE; campo.className = "seth-motivo";
    campo.placeholder = "Motivo (opcional)"; campo.value = m.feedback.motivo || ""; campo.setAttribute("aria-label", "Motivo do feedback, opcional");
    campo.addEventListener("change", () => sethDefinirMotivo(m, campo.value));
    bloco.append(campo);
  }
  return bloco;
}

function sethMarcarFeedback(m, nota) {
  // Mesmo botão de novo tira o feedback; trocar de útil para não útil (ou o contrário) mantém o motivo já escrito.
  if (m.feedback && m.feedback.nota === nota) delete m.feedback;
  else m.feedback = {nota, ...(m.feedback && m.feedback.motivo ? {motivo: m.feedback.motivo} : {})};
  sethDesenhar();
  if (!sethAtual.temporaria) sethSalvar();
}

function sethDefinirMotivo(m, texto) {
  if (!m.feedback) return;
  const limpo = Array.from(String(texto || "").split(/\s+/).filter(Boolean).join(" ")).slice(0, SETH_FEEDBACK_MOTIVO_LIMITE).join("");
  if (limpo) m.feedback.motivo = limpo; else delete m.feedback.motivo;
  sethDesenhar();
  if (!sethAtual.temporaria) sethSalvar();
}

function sethFormEdicao(m, corpo) {
  const campo = document.createElement("textarea"); campo.className = "msg-editar"; campo.maxLength = 4000; campo.value = m.content;
  campo.setAttribute("aria-label", "Texto da mensagem em edição");
  const acoes = document.createElement("div"); acoes.className = "msg-acoes";
  acoes.append(sethTexto("Enviar", () => {
    const texto = campo.value.trim();
    if (!texto || sethEmCurso()) return;
    sethEditandoId = null;
    sethEditar(m, texto);
  }), sethTexto("Cancelar", () => { sethEditandoId = null; sethDesenhar(); }));
  corpo.append(campo, acoes);
}

function sethAplicarResposta(modo, paiId, alvoId, info, c = sethAtual) {
  const texto = info.texto || "";
  if (modo === "continuar") {
    // A continuação entra na mesma resposta, a partir do fim do texto que já estava lá; a posição vira um corte.
    const no = sethNoPorId(alvoId, c);
    if (!no) return;
    if (texto) { const antes = Array.from(no.content).length; no.content += texto; no.cortes = [...(no.cortes || []), antes]; }
    if (info.parcial.modelo_real) no.modelo_real = info.parcial.modelo_real;
    if (info.interrompida) no.interrompida = true; else delete no.interrompida;
    return;
  }
  const no = sethAdicionar({role: "assistant", content: texto, pai: paiId, modelo: info.modelo, modelo_real: info.parcial.modelo_real || "",
    aviso: info.aviso, hora: sethHora()}, c);
  if (info.interrompida) no.interrompida = true;
  c.folha = no.id;
}

function sethRemover(id, c = sethAtual) {
  const no = sethNoPorId(id, c);
  if (!no || sethFilhos(id, c).length) return;
  c.nos = c.nos.filter((n) => n.id !== id);
  if (c.folha === id) c.folha = no.pai || null;
}

// Bloco recolhido "Trabalho do Agata Code" (20/11/2026): o Humano escolhe ver ou não. Fechado por padrão; só texto (textContent).
// Vale para a tela em curso: não entra na conversa salva. A transcrição completa fica no arquivo indicado.
function sethBlocoAgataCode(dados) {
  const bloco = document.createElement("details"); bloco.className = "seth-detalhes seth-agata-code";
  const resumo = document.createElement("summary"); resumo.textContent = "Trabalho do Agata Code"; bloco.append(resumo);
  const corpo = document.createElement("div"); corpo.className = "seth-detalhes-corpo";
  const campo = (rotulo, texto, pre) => {
    if (!texto) return;
    const titulo = document.createElement("p"); titulo.className = "seth-agata-code-rotulo"; titulo.textContent = rotulo;
    const valor = document.createElement(pre ? "pre" : "p"); valor.className = "seth-agata-code-texto"; valor.textContent = String(texto);
    corpo.append(titulo, valor);
  };
  campo("Verificação", dados.aviso, false);
  campo("Resposta", dados.resposta, true);
  campo("Mudanças (git diff --stat)", dados.diff_stat || "sem mudanças", true);
  campo("Erro", dados.erro, false);
  campo("Worktree", dados.worktree, false);
  campo("Transcrição completa", dados.transcricao, false);
  if (dados.tempo_s) campo("Tempo", dados.tempo_s + " s", false);
  bloco.append(corpo);
  return bloco;
}
function sethMostrarAgataCode(log, parcial) { (parcial.agata_code || []).forEach((d) => log.append(sethBlocoAgataCode(d))); }

// Motor da resposta. A conversa é `alvo` (capturada antes de qualquer await): a resposta vai para ela e o salvar grava
// ela, mesmo que a tela tenha trocado. A trava (sethRespondendo) vale até o salvar terminar.
// Envia a janela do caminho até `paiId` (nova resposta) ou até a resposta de `alvoId` mais a mensagem "continue de onde
// parou" (continuação). Parar aborta o fetch; o texto que chegou fica marcado interrompida.
async function sethResponder(op) {
  const {modo, alvo = sethAtual, paiId = null, alvoId = null, novoUsuarioId = null, textoDoUsuario = "", anexos = []} = op;
  const campo = byId("seth-input"); const log = byId("seth-transcript"); const botao = byId("seth-send");
  const controle = new AbortController(); sethControle = controle; sethRespondendo = true;
  sethUso = null; alvo.erro = null; // um pedido novo zera o uso anterior e a falha que estava na tela
  botao.disabled = true; sethPintarParar(); sethStatus("PENSANDO", "partial");
  const pensando = document.createElement("p"); pensando.className = "seth-vazio"; pensando.textContent = "A Seth está respondendo…";
  const cursor = sethCursor(); pensando.append(cursor);
  log.append(pensando);
  const pedido = modo === "continuar"
    ? [...sethMensagensParaEnvio(sethCaminhoDe(alvoId, alvo)), {role: "user", content: SETH_CONTINUAR}]
    : sethMensagensParaEnvio(sethCaminhoDe(paiId, alvo));
  const modelo = alvo.modelo; // o modelo do envio fica preso a ele, mesmo se o seletor mudar depois
  const pedidoBase = sethPedidoBase(anexos, alvo); // instruções da conversa e anexos deste envio (C8, C9)
  const janela = sethJanela(pedido, pedidoBase);
  const aviso = sethAvisoJanela(janela);
  const parcial = {texto: ""};
  let textoNo = null;
  const aoTexto = (delta) => {
    const perto = sethNoFim(log);
    if (!textoNo) {
      pensando.remove();
      const bolha = document.createElement("article"); bolha.className = "msg msg-assistant" + (modo === "continuar" ? " msg-continuacao" : "");
      const corpo = document.createElement("div"); corpo.className = "msg-body";
      textoNo = document.createTextNode(""); corpo.append(textoNo, cursor); bolha.append(corpo); log.append(bolha);
    }
    textoNo.appendData(delta); if (perto) log.scrollTop = log.scrollHeight; sethAtualizarFim();
  };
  const aoEstado = (texto) => { // Regra 0: o que a Seth está consultando fica visível enquanto espera
    sethStatus("CONSULTANDO", "partial");
    if (!textoNo) { pensando.textContent = "A Seth está " + texto.charAt(0).toLowerCase() + texto.slice(1); pensando.append(cursor); }
  };
  let conteudo = null, falha = null, parada = false;
  try {
    try {
      conteudo = await sethLerStream(janela.mensagens, modelo, parcial, aoTexto, controle.signal, alvo.instrucoes || "", pedidoBase.anexos, aoEstado);
    } catch (erro) {
      if (controle.signal.aborted) throw erro;
      const transporte = !erro.motivoStream && !parcial.texto && (erro.semStream || erro.status === undefined || erro.status === 404 || erro.status >= 500);
      if (!transporte) throw erro;
      const dados = await sethChatInteiro(janela.mensagens, modelo, parcial, controle.signal, alvo.instrucoes || "", pedidoBase.anexos);
      conteudo = dados.content;
    }
  } catch (erro) {
    if (controle.signal.aborted) parada = true;
    else { falha = erro; if (parcial.texto) parada = true; }
  }
  sethControle = null;
  pensando.remove(); cursor.remove();
  if (parcial.uso) sethUso = {alvo, entrada: parcial.uso.entrada, saida: parcial.uso.saida}; // C11
  const info = {modelo, parcial, aviso, texto: conteudo !== null ? conteudo : parcial.texto};
  if (conteudo !== null) {
    sethAplicarResposta(modo, paiId, alvoId, {...info, interrompida: false}, alvo);
    if (alvo === sethAtual) { sethDesenhar(); sethMostrarAgataCode(log, parcial); sethStatus("PRONTA", "planned"); if (vozModoLigado()) ouvirResposta(conteudo, true); }
    await sethSalvar(alvo); // espera o salvar: o botão só volta quando a conversa está gravada (ou o aviso mostra o motivo)
  } else if (parada) {
    if (modo === "nova" || parcial.texto) sethAplicarResposta(modo, paiId, alvoId, {...info, interrompida: true}, alvo);
    if (alvo === sethAtual) {
      sethDesenhar(); sethMostrarAgataCode(log, parcial);
      if (falha) log.append(sethVazio("Não consegui terminar a resposta: " + (falha.message || "falha desconhecida") + "."));
      else if (modo === "continuar" && !parcial.texto) log.append(sethVazio("Continuação parada antes do primeiro texto. A resposta ficou como estava."));
      sethStatus("INTERROMPIDA", "partial");
    }
    if (modo === "nova" || parcial.texto) await sethSalvar(alvo);
  } else {
    // Falha sem texto (C7): a pergunta fica na conversa; o erro traz "Tentar de novo", que reenvia sem duplicar a pergunta.
    alvo.erro = {paiId: modo === "nova" ? paiId : null, anexos, motivo: (falha && falha.message) || "falha desconhecida"};
    if (alvo === sethAtual) { sethDesenhar(); sethStatus("INDISPONÍVEL", "horizon"); }
  }
  sethRespondendo = false;
  botao.disabled = false; sethPintarParar(); campo.focus();
}

function sethComecarNova() {
  abrirConversaNoPainel();
  if (sethTrocaBloqueada()) return;
  sethAtual = sethNova(false); sethEditandoId = null;
  sethDesenhar(); sethListar(); sethRestaurarRascunho(); sethStatus("PRONTA", "planned");
  byId("seth-input").focus();
}

// Editar e reenviar: a mensagem nova é irmã da antiga; a resposta antiga continua na conversa, como outro ramo.
async function sethEditar(m, texto) {
  if (sethEmCurso()) return;
  const usuario = sethAdicionar({role: "user", content: texto, pai: m.pai, hora: sethHora()});
  sethAtual.folha = usuario.id;
  sethDesenhar();
  await sethResponder({modo: "nova", paiId: usuario.id, novoUsuarioId: usuario.id, textoDoUsuario: texto});
}

function sethContinuar() {
  const folha = sethNoPorId(sethAtual.folha);
  if (sethEmCurso() || !folha || folha.role !== "assistant") return;
  if (!folha.content) { byId("seth-transcript").append(sethVazio("Nada para continuar: esta resposta ainda não tem texto. Use Regenerar.")); return; }
  sethResponder({modo: "continuar", alvoId: folha.id});
}

// Ramificar: cria conversa nova com o caminho até a mensagem `indice` (inclusive) e guarda de onde saiu.
async function sethRamificar(indice) {
  if (sethAtual.temporaria || sethEmCurso()) return;
  const caminho = sethCaminho();
  if (!caminho[indice]) return;
  if (!sethAtual.id) await sethSalvar();
  if (!sethAtual.id) { sethMostrarOrg("Não foi possível ramificar: a conversa ainda não foi salva. Tente de novo em instantes."); return; }
  const corpo = {titulo: sethAtual.titulo || caminho[0].content.slice(0, 60), modelo: sethAtual.modelo, instrucoes: sethAtual.instrucoes || "",
    mensagens: caminho.slice(0, indice + 1).map(sethParaSalvar), ramificada_de: {id: sethAtual.id, mensagem: indice}};
  try {
    const r = await fetch("/api/seth/conversa", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: JSON.stringify(corpo)});
    if (!r.ok) { sethMostrarOrg("Não foi possível ramificar: " + sethMotivoRecusa(r.status, await sethMotivo(r)) + "."); return; }
    const dados = await r.json();
    await sethListar();
    sethMostrarOrg("Conversa ramificada criada.");
    await sethAbrir(dados.id);
  } catch (_) { sethMostrarOrg("Não foi possível ramificar: sem resposta do painel."); }
}

async function sethCopiarUltima() {
  const aviso = byId("seth-copiado"); if (!aviso) return;
  const ultima = sethCaminho().filter((m) => m.role === "assistant" && m.content).pop();
  if (!ultima) { aviso.textContent = "Ainda não há resposta da Seth para copiar."; return; }
  try { await navigator.clipboard.writeText(ultima.content); aviso.textContent = "Última resposta copiada."; }
  catch (_) { aviso.textContent = "Não foi possível copiar."; }
}
window.addEventListener("load", ligarConversaSeth);

/* (27/10/2026) Grafo do vault: lê /api/grafo (só leitura). Modos: Relações (cita, citada_por, parecidas) e Regiões (tags regiao/). */
let grafoModo = "citacoes", grafoCentro = "0850";
const CORES_GRAFO = {centro: "var(--teal)", cita: "var(--blue)", citada_por: "var(--violet)", parecida: "var(--gold)", entrada: "var(--blue)", regiao: "var(--rose)"};
function desenharGrafo(dados) {
  const svg = byId("grafo-svg"); const NS = "http://www.w3.org/2000/svg";
  svg.replaceChildren();
  const nos = dados.nodes || []; const pos = new Map();
  const centro = nos.find((n) => n.kind === "centro");
  const outros = nos.filter((n) => n.kind !== "centro");
  pos.set(centro ? centro.id : "", [240, 180]);
  outros.forEach((n, i) => { const a = (2 * Math.PI * i) / Math.max(outros.length, 1) - Math.PI / 2; pos.set(n.id, [240 + 150 * Math.cos(a), 180 + 130 * Math.sin(a)]); });
  (dados.edges || []).forEach(([a, b]) => {
    const pa = pos.get(a), pb = pos.get(b); if (!pa || !pb) return;
    const l = document.createElementNS(NS, "line"); l.setAttribute("x1", pa[0]); l.setAttribute("y1", pa[1]); l.setAttribute("x2", pb[0]); l.setAttribute("y2", pb[1]);
    l.setAttribute("stroke", "var(--line)"); l.setAttribute("stroke-width", "1.5"); svg.append(l);
  });
  nos.forEach((n) => {
    const [x, y] = pos.get(n.id); const g = document.createElementNS(NS, "g");
    const c = document.createElementNS(NS, "circle"); c.setAttribute("cx", x); c.setAttribute("cy", y); c.setAttribute("r", n.kind === "centro" ? 18 : 12);
    c.setAttribute("fill", CORES_GRAFO[n.kind] || "var(--muted)"); c.setAttribute("opacity", "0.85");
    const tx = document.createElementNS(NS, "text"); tx.setAttribute("x", x); tx.setAttribute("y", y + 30); tx.setAttribute("text-anchor", "middle");
    tx.setAttribute("font-size", "10"); tx.setAttribute("fill", "var(--ink)"); tx.textContent = n.label;
    g.append(c, tx);
    if (n.kind === "entrada" || n.kind === "cita" || n.kind === "citada_por" || n.kind === "parecida") {
      g.style.cursor = "pointer"; g.setAttribute("tabindex", "0"); g.setAttribute("role", "button");
      const ir = () => { grafoCentro = n.id; byId("grafo-entrada").value = n.id; carregarGrafo(); };
      g.addEventListener("click", ir); g.addEventListener("keydown", (e) => { if (e.key === "Enter") ir(); });
    }
    svg.append(g);
  });
}
async function carregarGrafo() {
  const fonte = byId("grafo-fonte");
  fonte.textContent = "Lendo o vault…";
  try {
    const dados = await fetchJson("/api/grafo?entrada=" + encodeURIComponent(grafoCentro) + "&modo=" + grafoModo, {headers: {Accept: "application/json"}});
    byId("grafo-titulo").textContent = "Entrada " + grafoCentro;
    desenharGrafo(dados);
    if (grafoModo === "atlas") { byId("grafo-titulo").textContent = "Brain Atlas"; fonte.textContent = "Fonte: memoria/obsidian · contagem de notas por região, medida agora em " + dados.total + " notas (cabeçalho de cada nota)."; }
    else fonte.textContent = "Fonte: memoria/obsidian/entradas · " + (grafoModo === "citacoes" ? "relações cita, citada_por e parecidas" : "tags de região") + " · " + (dados.nodes || []).length + " nós, medido agora.";
  } catch (erro) {
    byId("grafo-svg").replaceChildren();
    fonte.textContent = "Leitura indisponível (" + erro.message + "). Nada anterior foi mantido como atual.";
  }
}
function ligarGrafo() {
  const form = byId("grafo-form"); if (!form || form.dataset.ligado) return; form.dataset.ligado = "1";
  form.addEventListener("submit", (e) => { e.preventDefault(); const v = byId("grafo-entrada").value.trim(); if (/^\d{4}$/.test(v)) { grafoCentro = v; carregarGrafo(); } });
  const alternar = (modo) => {
    grafoModo = modo;
    byId("grafo-modo-relacoes").setAttribute("aria-pressed", String(modo === "citacoes"));
    byId("grafo-modo-regioes").setAttribute("aria-pressed", String(modo === "regioes"));
    byId("grafo-modo-atlas").setAttribute("aria-pressed", String(modo === "atlas"));
    byId("grafo-form").style.display = modo === "atlas" ? "none" : "flex";
    carregarGrafo();
  };
  byId("grafo-modo-relacoes").addEventListener("click", () => alternar("citacoes"));
  byId("grafo-modo-regioes").addEventListener("click", () => alternar("regioes"));
  byId("grafo-modo-atlas").addEventListener("click", () => alternar("atlas"));
}
window.addEventListener("load", () => { ligarGrafo(); });

/* (27/10/2026) Mapa de lacunas: cada item do painel sem fonte medida agora vira LACUNA, com o motivo. Lido do próprio DOM. */
function calcularLacunas() {
  const itens = [];
  document.querySelectorAll("#integration-list .cap-card").forEach((cartao) => {
    const titulo = cartao.querySelector("h3").textContent;
    if (cartao.dataset.probe === "documento") itens.push({nome: titulo, motivo: "sem sonda: é documento, não leitura do sistema", onde: "Sistema › Integrações"});
  });
  document.querySelectorAll("[data-live]").forEach((el) => {
    if (el.textContent === "sem leitura") itens.push({nome: el.dataset.live, motivo: "sem leitura agora", onde: "texto vivo"});
  });
  const lista = byId("lacunas-lista");
  if (lista) {
    lista.replaceChildren();
    itens.forEach((i) => { const li = document.createElement("li"); li.textContent = "LACUNA · " + i.nome + " — " + i.motivo + " (" + i.onde + ")"; lista.append(li); });
    byId("lacunas-total").textContent = itens.length + " lacuna(s) na tela agora";
  }
  return itens.length;
}
function marcarLacunasNosCartoes() {
  document.querySelectorAll("#integration-list .cap-card[data-probe='documento'] .chip").forEach((chip) => {
    chip.className = "chip horizon"; chip.textContent = "LACUNA · sem sonda";
  });
}
window.addEventListener("load", () => setTimeout(() => { marcarLacunasNosCartoes(); }, 1200));

/* (27/10/2026) Lacunas declaradas no canon (PROJETO.md, Serviços (boot)), conferidas agora em /api/lacunas. */
async function carregarLacunasCanon() {
  const lista = byId("lacunas-canon");
  if (!lista) return;
  lista.replaceChildren();
  try {
    const dados = await fetchJson("/api/lacunas", {headers: {Accept: "application/json"}});
    const itens = dados.items || [];
    const cab = document.createElement("p");
    cab.textContent = (dados.total_declaradas || 0) + " itens declarados no canon; " + itens.length + " lacuna(s) no canon agora. Fonte: PROJETO.md · Serviços (boot), medido em " + niceTime(dados.observed_at) + ".";
    lista.append(cab);
    itens.forEach((i) => { const li = document.createElement("li"); li.textContent = "LACUNA · " + i.nome + " — " + i.motivo; lista.append(li); });
  } catch (erro) {
    const p = document.createElement("p"); p.textContent = "Leitura do canon indisponível (" + erro.message + "). Nada anterior foi mantido como atual."; lista.append(p);
  }
}

/* (27/10/2026) Visão do sistema: junta as leituras já existentes (status, capacidades, lacunas). Nada novo é medido aqui. */
async function executarSdd(acao, componente, nota) {
  nota.textContent = "Executando…";
  try {
    const r = await fetchJson("/api/sdd/executar", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: JSON.stringify({acao, componente})});
    nota.textContent = (r.ok ? "OK · " : "FALHOU · ") + r.passos.map((p) => p.passo + ": " + p.detalhe).join(" | ");
  } catch (_) { nota.textContent = "Execução indisponível."; }
}
async function carregarSdd() {
  const lista = byId("sdd-lista"); const titulo = byId("sdd-titulo");
  if (!lista) return;
  lista.replaceChildren();
  let dados = null;
  try { dados = await fetchJson("/api/sdd/estado", {headers: {Accept: "application/json"}}); } catch (_) { dados = null; }
  if (!dados || !Array.isArray(dados.items)) { if (titulo) titulo.textContent = "Sem leitura"; return; }
  const falhas = dados.items.filter((i) => i.ancora !== "ok").length;
  if (titulo) titulo.textContent = dados.items.length + " componentes · " + falhas + " com âncora incompleta · " + (dados.externos || []).length + " projetos externos";
  dados.items.forEach((item) => {
    const linha = document.createElement("div"); linha.className = "cap-card";
    const nome = document.createElement("strong"); nome.textContent = item.componente;
    const resumo = document.createElement("div"); resumo.className = "note";
    resumo.textContent = item.criterios + " critérios · âncora " + item.ancora + (item.manifesto ? "" : " · sem manifesto de aceite (critérios não medidos)");
    const nota = document.createElement("div"); nota.className = "note";
    const u = item.ultima; nota.textContent = u ? "Última execução: " + (u.ok ? "OK" : "FALHOU") + " (" + u.acao + ")" : "Sem execução nesta sessão: não medido.";
    const acoes = document.createElement("div"); acoes.style.display = "flex"; acoes.style.gap = "8px";
    [["ancora", "Conferir âncora"], ["criterios", "Rodar critérios"]].forEach(([acao, rotulo]) => {
      const b = document.createElement("button"); b.type = "button"; b.className = "text-link"; b.textContent = rotulo;
      let armado = false;
      b.addEventListener("click", async () => {
        if (!armado) { armado = true; b.textContent = "Confirmar: " + rotulo.toLowerCase(); return; }
        b.disabled = true; await executarSdd(acao, item.componente, nota); b.disabled = false; armado = false; b.textContent = rotulo;
      });
      acoes.append(b);
    });
    linha.append(nome, resumo, nota, acoes); lista.append(linha);
  });
  (dados.externos || []).forEach((ext) => {
    const linha = document.createElement("div"); linha.className = "cap-card";
    const nome = document.createElement("strong"); nome.textContent = ext.nome + " · projeto externo";
    const resumo = document.createElement("div"); resumo.className = "note";
    resumo.textContent = ext.valido ? ext.raiz : "descritor inválido: " + (ext.erro || "");
    const nota = document.createElement("div"); nota.className = "note";
    nota.textContent = ext.ultimo ? "Última execução: " + (ext.ultimo.ok ? "OK" : "FALHOU") + " (" + ext.ultimo.run_id + ")" : "Sem execução: não medido.";
    linha.append(nome, resumo, nota);
    if (ext.valido) {
      const b = document.createElement("button"); b.type = "button"; b.className = "text-link"; b.textContent = "Rodar ciclo do projeto";
      let armado = false;
      b.addEventListener("click", async () => {
        if (!armado) { armado = true; b.textContent = "Confirmar: rodar ciclo do projeto"; return; }
        b.disabled = true; await executarSdd("projeto", ext.nome, nota); b.disabled = false; armado = false; b.textContent = "Rodar ciclo do projeto";
      });
      linha.append(b);
    }
    lista.append(linha);
  });
}
let medicaoTimer = null;
async function carregarMedicoes() {
  const nota = byId("medir-nota"); const sel = byId("medir-modelo");
  if (!nota || !sel) return;
  let d = null;
  try { d = await fetchJson("/api/medicoes/estado", {headers: {Accept: "application/json"}}); } catch (_) { d = null; }
  if (!d) { nota.textContent = "Medições indisponíveis."; return; }
  const atual = sel.value; sel.replaceChildren();
  (d.modelos || []).forEach((m) => { const o = document.createElement("option"); o.value = m; o.textContent = m; sel.append(o); });
  if (atual) sel.value = atual;
  const j = d.job || {};
  if (j.estado === "rodando") {
    nota.textContent = "Rodando: " + j.acao + (j.modelo ? " em " + j.modelo + (j.tarefa ? " (" + j.tarefa + ")" : "") : "") + "…";
    if (!medicaoTimer) medicaoTimer = setInterval(carregarMedicoes, 4000);
  } else {
    if (medicaoTimer) { clearInterval(medicaoTimer); medicaoTimer = null; carregarQualidade(); }
    if (d.modelos_estado === "sem_leitura") nota.textContent = "Sem leitura dos modelos locais: " + (d.modelos_motivo || "motivo não informado");
    else if (j.estado === "ok" || j.estado === "falhou") nota.textContent = (j.estado === "ok" ? "Concluído" : "Falhou") + ": " + j.acao + (j.modelo ? " em " + j.modelo : "") + " (" + j.segundos + " s). " + (j.detalhe || "");
  }
}
async function pedirComTrava(url, corpo) {
  const r = await fetch(url, {method: "POST", credentials: "same-origin", cache: "no-store", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: JSON.stringify(corpo)});
  if (r.ok) return;
  const dados = await r.json().catch(() => ({}));
  const erro = new Error("HTTP " + r.status);
  erro.ocupado = r.status === 409 || r.status === 429;
  erro.motivo = dados.motivo || dados.erro || (erro.ocupado ? "a trava comum está em uso" : "");
  throw erro;
}
function ligarMedicao(botao, rotulo, pedido) {
  let armado = false;
  botao.addEventListener("click", async () => {
    if (!armado) { armado = true; botao.textContent = "Confirmar: " + rotulo.toLowerCase(); return; }
    armado = false; botao.textContent = rotulo; botao.disabled = true;
    try {
      await pedirComTrava("/api/medicoes/executar", pedido());
    } catch (erro) {
      if (erro.ocupado) {
        const motivo = erro.motivo || "a trava comum está em uso";
        botao.textContent = "ocupado: " + motivo;
        byId("medir-nota").textContent = "Ocupado: " + motivo + ". Nada foi iniciado.";
        setTimeout(() => { if (botao.textContent.startsWith("ocupado")) botao.textContent = rotulo; }, 8000);
      } else byId("medir-nota").textContent = "Não foi possível iniciar (fora da lista).";
    }
    botao.disabled = false; carregarMedicoes();
  });
}
ligarMedicao(byId("medir-recuperacao"), "Medir recuperação · corpus do vault", () => ({acao: "recuperacao"}));
ligarMedicao(byId("medir-semantica"), "Medir busca por sentido", () => ({acao: "recuperacao_semantica"}));
ligarMedicao(byId("medir-contexto"), "Medir contexto efetivo", () => ({acao: "contexto", modelo: byId("medir-modelo").value, tarefa: byId("medir-tarefa").value, raciocinio: byId("medir-raciocinio").value}));
async function carregarQualidade() {
  const kpis = byId("qualidade-kpis"); const lista = byId("qualidade-lista"); const titulo = byId("qualidade-titulo");
  if (!kpis || !lista) return;
  kpis.replaceChildren(); lista.replaceChildren();
  let dados = null;
  try { dados = await fetchJson("/api/qualidade-llm", {headers: {Accept: "application/json"}}); } catch (_) { dados = null; }
  if (!dados || !Array.isArray(dados.items)) { if (titulo) titulo.textContent = "Sem leitura"; return; }
  dados.items.forEach((item) => {
    if (item.id === "recall_busca") {
      kpis.append(kpiRecuperacao(item));
      const li = document.createElement("li"); li.textContent = "Recuperação: " + leiturasDaRecuperacao(item).map((x) => x.corpus + " " + (x.valor ?? "não medido")).join(" · ");
      lista.append(li);
      return;
    }
    const d = document.createElement("div"); d.className = "kpi";
    const l = document.createElement("div"); l.className = "label"; l.textContent = item.titulo;
    const v = document.createElement("div"); v.className = "note"; v.textContent = item.valor;
    d.append(l, v, seloDeEstado(item.estado)); kpis.append(d);
    const li = document.createElement("li"); li.textContent = item.titulo + ": " + item.evidencia + " (fonte: " + item.fonte + ")";
    lista.append(li);
  });
  const atencao = dados.items.filter((i) => i.estado === "warning").length;
  const naoMedidos = dados.items.filter((i) => i.estado === "unknown").length;
  if (titulo) titulo.textContent = atencao + " em atenção · " + naoMedidos + " não medidos";
}
// Recuperação (17/11/2026): recall_busca traz leituras rotuladas pelo corpus (vault; conjunto da avaliação), cada uma com fonte e data.
// Sem a lista de leituras (rota antiga), a leitura única vira o corpus "não informado".
function leiturasDaRecuperacao(item) {
  if (Array.isArray(item.leituras) && item.leituras.length) return item.leituras.map((x) => ({corpus: x.corpus || x.rotulo || "corpus não informado", valor: x.valor, estado: x.estado, fonte: x.fonte, data: x.medido_em || x.data || x.observed_at}));
  return [{corpus: "corpus não informado", valor: item.valor, estado: item.estado, fonte: item.fonte, data: item.observed_at}];
}
// Estado com marca e palavra (filtro de estilo): pílula com o texto, nunca só cor.
const SELO_ESTADO = {ok: ["OK", "chip active"], warning: ["ATENÇÃO", "chip partial"], falha: ["FALHA", "chip erro"]};
function seloDeEstado(estado) {
  const [texto, classe] = SELO_ESTADO[estado] || ["NÃO MEDIDO", "chip horizon"];
  const s = document.createElement("span"); s.className = classe; s.textContent = texto; return s;
}
function kpiRecuperacao(item) {
  const d = document.createElement("div"); d.className = "kpi";
  const l = document.createElement("div"); l.className = "label"; l.textContent = "Recuperação";
  d.append(l);
  // Uma leitura por bloco: corpus e valor; estado; fonte e a data da medição (AAAA-MM-DD, sem fuso).
  leiturasDaRecuperacao(item).forEach((x) => {
    const v = document.createElement("div"); v.className = "note";
    v.textContent = x.corpus + ": " + (x.valor ?? "não medido");
    const meta = document.createElement("div"); meta.className = "note";
    meta.textContent = "fonte: " + (x.fonte || "não informada") + " · data: " + (x.data ? String(x.data).slice(0, 10) : "não informada");
    d.append(v, seloDeEstado(x.estado), meta);
  });
  return d;
}

async function carregarVisaoSistema() {
  const kpis = byId("visao-kpis");
  if (!kpis) return;
  kpis.replaceChildren();
  // Cada número abre a tela de onde ele vem (atalho); sem leitura, o número sai como não medido.
  const cartao = (rotulo, valor, aba, sub) => {
    const d = document.createElement("div"); d.className = "kpi"; d.tabIndex = 0; d.setAttribute("role", "button");
    const l = document.createElement("div"); l.className = "label"; l.textContent = rotulo;
    const v = document.createElement("div"); v.className = "value"; v.textContent = valor;
    d.append(l, v); d.dataset.openPage = aba; d.dataset.openSub = sub;
    kpis.append(d);
  };
  try {
    const [status, caps, lac] = await Promise.all([
      fetchJson("/api/status", {headers: {Accept: "application/json"}}),
      fetchJson("/api/capacidades", {headers: {Accept: "application/json"}}),
      fetchJson("/api/lacunas", {headers: {Accept: "application/json"}}),
    ]);
    const servicos = (status.services || []).filter((x) => x.state !== "ausente");
    const ativos = servicos.filter((x) => x.state === "ok").length;
    cartao("Serviços ativos", ativos + " de " + servicos.length, "sistema", "operacao");
    cartao("Timers", String((status.timers || []).filter((x) => x.state === "ok").length) + " ok", "sistema", "manutencao");
    cartao("Git", (status.git && status.git.head) || "não medido", "sistema", "operacao");
    cartao("Conversa (painel)", status.chat && status.chat.http_status === 200 ? "responde" : "sem resposta", "sistema", "operacao");
    const modelos = (status.models && status.models.models) || [];
    cartao("Modelos registrados", String(modelos.length), "sistema", "modelos");
    const cap = caps.items || [];
    cartao("Capacidades com leitura", cap.filter((x) => x.state === "ok").length + " de " + cap.length, "sistema", "integracoes");
    cartao("Lacunas agora", String((lac.items || []).length), "qualidade", "lacunas");
    const props = (status.proposals && status.proposals.items) || [];
    const pendentes = props.filter((p) => !p.substituida_por && !p.marker_present && p.versionada !== false);
    cartao("Propostas sem assinatura", String(pendentes.length), "panorama", "plano");
  } catch (erro) {
    const p = document.createElement("p"); p.textContent = "Visão indisponível (" + erro.message + "). Nada anterior foi mantido como atual."; kpis.append(p);
  }
}

/* (27/10/2026) Vault dentro do painel: cada botão de vault abre a própria tela, lida de /api/vault/item (lista fechada, só leitura). */
async function abrirVault(alvo, porCaminho = false) {
  const dlg = byId("vault-dialog");
  if (!dlg) return;
  byId("vault-title").textContent = "Carregando…";
  byId("vault-fonte").textContent = "";
  byId("vault-texto").textContent = "";
  byId("vault-canvas").replaceChildren();
  dlg.showModal();
  try {
    const consulta = porCaminho ? "caminho=" + encodeURIComponent(alvo) : "id=" + encodeURIComponent(alvo);
    const d = await fetchJson("/api/vault/item?" + consulta, {headers: {Accept: "application/json"}});
    byId("vault-title").textContent = d.titulo || d.id || alvo;
    if (d.state !== "ok") {
      byId("vault-fonte").textContent = "Fonte: " + d.fonte;
      byId("vault-texto").textContent = "Sem leitura: " + (d.motivo || "item indisponível") + ".";
      return;
    }
    byId("vault-fonte").textContent = "Fonte: " + d.fonte + " · medido em " + niceTime(d.observed_at) + " · modificado em " + niceTime(d.modificado) + (d.truncado ? " · mostrados os primeiros 64 KB" : "");
    if (d.canvas) {
      const cab = document.createElement("li");
      cab.textContent = d.canvas.nos.length + " nós e " + d.canvas.arestas + " ligações no mapa:";
      byId("vault-canvas").append(cab);
      d.canvas.nos.forEach((n) => { const li = document.createElement("li"); li.textContent = (n.tipo || "nó") + " · " + (n.texto || "(sem texto)"); byId("vault-canvas").append(li); });
    }
    byId("vault-texto").textContent = d.texto;
  } catch (erro) {
    byId("vault-texto").textContent = "Leitura indisponível (" + erro.message + "). Nada anterior foi mantido como atual.";
  }
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-vault], [data-vault-caminho]");
  if (!b) return;
  if (b.dataset.vaultCaminho) abrirVault(b.dataset.vaultCaminho, true); else abrirVault(b.dataset.vault);
});
document.querySelectorAll(".close-vault").forEach((b) => b.addEventListener("click", () => byId("vault-dialog").close()));
byId("vault-dialog").addEventListener("click", (e) => { if (e.target === byId("vault-dialog")) byId("vault-dialog").close(); });

// Frentes (antiga /frentes): leitura somente de /api/frentes, sem ação de controle.
async function carregarFrentes() {
  const estado = byId("frentes-estado");
  const lista = byId("frentes-lista");
  const cabecalho = byId("frentes-cabecalho");
  if (!estado || !lista) return;
  const CAMPOS = [["Entregável", "entregavel"], ["Gate", "gate"], ["Bloqueios", "bloqueios"]];
  const item = (frenta) => {
    const li = document.createElement("li");
    const titulo = document.createElement("h3");
    titulo.textContent = `${frenta.id} · ${frenta.nome}`;
    li.appendChild(titulo);
    for (const [rotulo, campo] of CAMPOS) {
      const p = document.createElement("p");
      const b = document.createElement("strong");
      b.textContent = `${rotulo}: `;
      p.append(b, document.createTextNode(String(frenta[campo] ?? "")));
      li.appendChild(p);
    }
    if (frenta.piloto_sintetico) {
      const p = document.createElement("p");
      const b = document.createElement("strong");
      b.textContent = "Piloto sintético: ";
      p.append(b, document.createTextNode(String(frenta.piloto_sintetico)));
      li.appendChild(p);
    }
    return li;
  };
  estado.textContent = "Carregando frentes…";
  try {
    const resposta = await fetch("/api/frentes", {cache: "no-store", credentials: "same-origin", headers: {Accept: "application/json"}});
    if (!resposta.ok) throw new Error("status " + resposta.status);
    const dados = await resposta.json();
    const frentes = Array.isArray(dados.frentes) ? dados.frentes : [];
    cabecalho.textContent = `Frentes · palavra atual: ${dados.palavra_atual ?? ""} · dados reais: ${dados.dados_reais ?? ""}`;
    lista.replaceChildren(...frentes.map(item));
    estado.textContent = `${frentes.length} frentes.`;
  } catch (_) {
    lista.replaceChildren();
    estado.textContent = "Não medido: não foi possível carregar as frentes.";
  }
}

// Memória compartilhada do Conselho (aba Conselho > Memória compartilhada): só leitura de GET /api/conselho/memoria.
// O texto do cache entra só com textContent. Erro esvazia a lista: nada antigo aparece como atual.
const MEMORIA_TIPOS = {fato: ["Fato", "active"], decisao: ["Decisão", "planned"], pendencia: ["Pendência", "partial"], nota: ["Nota", "horizon"], diario: ["Diário", ""]};
let memoriaDados = null;
let memoriaBusy = false;
function renderizarMemoria() {
  const lista = byId("memoria-lista");
  const resumo = byId("memoria-resumo");
  if (!lista || !resumo || !memoriaDados) return;
  const tipo = byId("memoria-tipo").value;
  const entradas = memoriaDados.entradas.filter((entrada) => tipo === "todos" || entrada.tipo === tipo);
  const item = (entrada) => {
    const evento = document.createElement("article");
    evento.className = "event";
    const hora = document.createElement("time");
    hora.textContent = `nº ${entrada.n} · ${entrada.data_hora}`;
    const titulo = document.createElement("h3");
    const [rotulo, classe] = MEMORIA_TIPOS[entrada.tipo] || [String(entrada.tipo), ""];
    const chip = document.createElement("span");
    chip.className = classe ? `chip ${classe}` : "chip";
    chip.textContent = rotulo;
    titulo.append(document.createTextNode(`${entrada.autor} `), chip);
    const texto = document.createElement("p");
    texto.textContent = entrada.texto;
    evento.append(hora, titulo, texto);
    return evento;
  };
  lista.replaceChildren(...entradas.map(item));
  resumo.textContent = `${entradas.length} de ${memoriaDados.entradas.length} entradas mostradas · lido em ${horaDaLeitura(memoriaDados)}`;
}
function horaDaLeitura(dados) {
  return String(dados.observed_at).slice(0, 16).replace("T", " ");
}
// Clique dentro da aba não pode disparar o "entrar no Conselho" de abrir.js, que escuta todo [data-secao="conselho"]:
// este listener é registrado antes (prototipo.js carrega antes de abrir.js; o teste confere a ordem).
byId("sub-conselho-memoria").addEventListener("click", (e) => e.stopImmediatePropagation());
async function carregarMemoriaConselho() {
  const sub = byId("sub-conselho-memoria");
  const botao = byId("memoria-atualizar");
  if (!sub || memoriaBusy) return;
  memoriaBusy = true;
  marcarEstado(sub, "carregando");
  byId("memoria-resumo").textContent = memoriaDados
    ? `Atualizando · os valores abaixo são de ${horaDaLeitura(memoriaDados)}`
    : "Lendo a memória do cache…";
  if (botao) botao.disabled = true;
  try {
    const resposta = await fetch("/api/conselho/memoria?n=40", {cache: "no-store", credentials: "same-origin", headers: {Accept: "application/json"}});
    if (!resposta.ok) throw new Error("HTTP " + resposta.status);
    const dados = await resposta.json();
    if (!dados || !Array.isArray(dados.entradas)) throw new Error("resposta incompleta");
    memoriaDados = dados;
    marcarEstado(sub, dados.entradas.length ? null : "vazio");
    renderizarMemoria();
  } catch (_) {
    memoriaDados = null;
    byId("memoria-lista").replaceChildren();
    byId("memoria-resumo").textContent = "Não medido: a leitura da memória falhou.";
    marcarEstado(sub, "erro");
  } finally {
    memoriaBusy = false;
    if (botao) botao.disabled = false;
  }
}
byId("memoria-tipo").addEventListener("change", renderizarMemoria);
byId("memoria-atualizar").addEventListener("click", () => carregarMemoriaConselho());

/* (11/11/2026) Preferência do modo conversa da Seth (ler cada resposta em voz alta, desligado por padrão). Fica fora do
bloco da Conversa: é só um sim ou não, não conteúdo de conversa. Como o tema, usa localStorage com try/catch. */
function vozModoLigado() { try { return localStorage.getItem("agata-modo-conversa") === "1"; } catch (_) { return false; } }
function vozGuardarModo(ligado) { try { localStorage.setItem("agata-modo-conversa", ligado ? "1" : "0"); } catch (_) { /* sem persistência: vale só nesta aba */ } }
/* (09/11/2026) Tema (escuro, claro ou do sistema) e atalhos de teclado. Fica fora do bloco da Conversa: o tema usa localStorage, com try/catch. */
const TEMAS = ["escuro", "claro", "sistema"];
let temaEscolhido = "escuro";
function temaEfetivo(escolha) {
  if (escolha !== "sistema") return escolha;
  try { return window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches ? "claro" : "escuro"; } catch (_) { return "escuro"; }
}
function aplicarTema(escolha, guardar) {
  temaEscolhido = TEMAS.includes(escolha) ? escolha : "escuro";
  if (document.documentElement) document.documentElement.dataset.tema = temaEfetivo(temaEscolhido);
  const seletor = byId("tema"); if (seletor) seletor.value = temaEscolhido;
  if (guardar) { try { localStorage.setItem("agata-tema", temaEscolhido); } catch (_) { /* sem persistência: vale só nesta aba */ } }
}
function lerTema() { try { return localStorage.getItem("agata-tema") || "escuro"; } catch (_) { return "escuro"; } }
function alternarAtalhos(abrir) {
  const painel = byId("atalhos-painel"); if (!painel) return;
  painel.hidden = abrir === undefined ? !painel.hidden : !abrir;
  if (!painel.hidden) byId("atalhos-fechar").focus();
}
function atalhosAbertos() { const painel = byId("atalhos-painel"); return Boolean(painel && !painel.hidden); }
function campoDeTexto(alvo) { return Boolean(alvo && (alvo.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(alvo.tagName || ""))); }
// Ctrl+Shift+O: nova conversa. Ctrl+Shift+C: copia a última resposta. Esc: para a resposta (ou fecha esta lista).
// /: busca (das conversas, na Conversa; do mapa, nas outras telas). ?: mostra ou esconde a lista de atalhos.
document.addEventListener("keydown", (e) => {
  const comCtrl = (e.ctrlKey || e.metaKey) && e.shiftKey;
  const tecla = String(e.key || "").toLowerCase();
  if (comCtrl && tecla === "o") { e.preventDefault(); irPara("conversa"); sethComecarNova(); return; }
  if (comCtrl && tecla === "c") { e.preventDefault(); sethCopiarUltima(); return; }
  if (e.key === "Escape") {
    if (menuAberto) { fecharMenuAberto(); return; }
    if (gavetaAberta()) { setGaveta(false); byId("menu-abrir").focus(); return; }
    if (atalhosAbertos()) alternarAtalhos(false); else { if (sethEmCurso()) sethParar(); vozParar(); }
    return;
  }
  if (campoDeTexto(e.target)) return;
  if (e.key === "?") { e.preventDefault(); alternarAtalhos(); return; }
  // C12a (16/11/2026): na Conversa, "/" vai para a busca de conversas; nas outras seções, para a busca do mapa.
  if (e.key === "/") { e.preventDefault(); if (byId("conversa").hidden) byId("search").focus(); else byId("seth-busca").focus(); }
});
byId("atalhos-abrir").addEventListener("click", () => alternarAtalhos());
byId("atalhos-fechar").addEventListener("click", () => alternarAtalhos(false));
byId("tema").addEventListener("change", (e) => aplicarTema(e.target.value, true));
try { if (window.matchMedia) window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", () => { if (temaEscolhido === "sistema") aplicarTema("sistema", false); }); } catch (_) { /* navegador sem aviso de mudança do sistema */ }
aplicarTema(lerTema(), false);

// Importantes (11/11/2026, pedido do Humano): ideias e pendências guardadas para depois. Aba Importantes do Panorama
// e cartão no Panorama. Leitura: GET /api/importantes. Ações: POST /api/importantes, /estado, /editar e /trazer.
// O texto do item entra só com textContent. Erro esvazia a lista: nada antigo aparece como atual.
const IMPORTANTES_ESTADOS = {aberto: ["Aberto", ""], feito: ["Feito", "active"], descartado: ["Descartado", "horizon"]};
const IMPORTANTES_ORIGENS = {humano: "Anotado por você", cache: "Do Conselho", modelo: "De um modelo"};
const IMPORTANTES_FILTROS = {abertos: "aberto", feitos: "feito", descartados: "descartado"};
const IMPORTANTES_ACOES = {
  aberto: [["Marcar feito", "feito"], ["Descartar", "descartado"]],
  feito: [["Reabrir", "aberto"], ["Descartar", "descartado"]],
  descartado: [["Reabrir", "aberto"]],
};
let importantesDados = null;
let importantesBusy = false;
let importantesPendente = false;
let importantesEnviando = false;

function importantesAviso(texto) {
  const aviso = byId("importantes-aviso");
  if (!aviso) return;
  aviso.textContent = texto || "";
  aviso.hidden = !texto;
}
function importantesData(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(String(iso || ""));
  return m ? `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}` : "data não conhecida";
}
// Pedido de escrita. Erro sai com status e o motivo curto que o servidor devolve; nunca com o texto do item.
async function importantesPedir(rota, corpo) {
  let resposta;
  try {
    resposta = await fetch(rota, {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"},
      credentials: "same-origin", cache: "no-store", body: JSON.stringify(corpo)});
  } catch (_) {
    throw Object.assign(new Error("sem resposta"), {status: 0, motivo: ""});
  }
  if (!resposta.ok) {
    let motivo = "";
    try { motivo = (await resposta.text()).trim().slice(0, 200); } catch (_) { motivo = ""; }
    throw Object.assign(new Error("recusado"), {status: resposta.status, motivo});
  }
  return resposta.json();
}
function importantesErro(status, motivo) {
  if (status === 0) return "Sem resposta do painel. Nada foi alterado.";
  if (status === 403) return "O painel recusou o pedido: abra esta tela pelo próprio painel.";
  if (status === 404) return "Item não encontrado; a lista foi atualizada.";
  if (motivo) return motivo.charAt(0).toUpperCase() + motivo.slice(1) + ".";
  return "O painel respondeu com erro " + status + ".";
}
function importantesCartao(dados, falhou) {
  const resumo = byId("importantes-cartao-resumo");
  const estado = byId("importantes-cartao-estado");
  if (!resumo || !estado) return;
  if (falhou || !dados) {
    resumo.textContent = "Importantes: não medido (a leitura falhou).";
    estado.textContent = "NÃO MEDIDO"; estado.className = "chip partial";
    return;
  }
  if (dados.estado === "ilegivel") {
    resumo.textContent = "Importantes: lista ilegível; nada foi mostrado.";
    estado.textContent = "ILEGÍVEL"; estado.className = "chip partial";
    return;
  }
  const abertos = dados.contagem.aberto;
  resumo.textContent = `Importantes: ${abertos} ${abertos === 1 ? "aberto" : "abertos"}`;
  estado.textContent = "LIDO"; estado.className = "chip active";
}
function importantesBotao(rotulo, aoClicar, classe = "text-link") {
  const botao = document.createElement("button");
  botao.type = "button"; botao.className = classe; botao.textContent = rotulo;
  botao.addEventListener("click", aoClicar);
  return botao;
}
function importantesAcoes(item, li) {
  const acoes = document.createElement("div");
  acoes.className = "importantes-acoes-item";
  for (const [rotulo, estado] of IMPORTANTES_ACOES[item.estado] || []) {
    acoes.append(importantesBotao(rotulo, () => importantesMudar(item.id, estado)));
  }
  if (item.estado !== "descartado") acoes.append(importantesBotao("Editar", () => importantesEditar(item, li)));
  return acoes;
}
function importantesItem(item) {
  const li = document.createElement("li");
  li.className = "importantes-item " + item.estado;
  const topo = document.createElement("div");
  topo.className = "importantes-topo";
  const [rotulo, classe] = IMPORTANTES_ESTADOS[item.estado] || [String(item.estado), ""];
  const chip = document.createElement("span");
  chip.className = classe ? "chip " + classe : "chip";
  chip.textContent = rotulo;
  const origem = document.createElement("span");
  origem.className = "importantes-origem";
  origem.textContent = item.origem === "cache" ? `Do Conselho, entrada nº ${item.cache_n}` : (IMPORTANTES_ORIGENS[item.origem] || "Origem não conhecida");
  topo.append(chip, origem);
  const texto = document.createElement("p");
  texto.className = "importantes-texto";
  texto.textContent = item.texto;
  li.append(topo, texto);
  if (item.nota) {
    const nota = document.createElement("p");
    nota.className = "importantes-nota";
    nota.textContent = "Nota: " + item.nota;
    li.append(nota);
  }
  const quando = document.createElement("p");
  quando.className = "importantes-quando";
  quando.textContent = "Criado em " + importantesData(item.criado_em) + (item.feito_em ? " · feito em " + importantesData(item.feito_em) : "");
  li.append(quando, importantesAcoes(item, li));
  return li;
}
function renderizarImportantes() {
  const lista = byId("importantes-lista");
  const resumo = byId("importantes-resumo-lista");
  if (!lista || !resumo || !importantesDados) return;
  const filtro = byId("importantes-filtro").value;
  const mostrados = importantesDados.itens.filter((item) => filtro === "todos" || item.estado === IMPORTANTES_FILTROS[filtro]);
  lista.replaceChildren(...mostrados.map(importantesItem));
  const c = importantesDados.contagem;
  resumo.textContent = importantesDados.estado === "ilegivel"
    ? "Lista ilegível: nada é mostrado nem alterado."
    : `${c.aberto} abertos · ${c.feito} feitos · ${c.descartado} descartados · mostrando ${mostrados.length}` + (mostrados.length ? "" : " · nenhum item neste filtro");
}
async function carregarImportantes() {
  const sub = byId("sub-importantes");
  if (!sub) return;
  if (importantesBusy) { importantesPendente = true; return; }
  importantesBusy = true;
  marcarEstado(sub, "carregando");
  byId("importantes-resumo-lista").textContent = importantesDados ? "Atualizando…" : "Lendo os importantes…";
  try {
    const resposta = await fetch("/api/importantes", {cache: "no-store", credentials: "same-origin", headers: {Accept: "application/json"}});
    if (!resposta.ok) throw new Error("HTTP " + resposta.status);
    const dados = await resposta.json();
    if (!dados || !Array.isArray(dados.itens) || !dados.contagem) throw new Error("resposta incompleta");
    importantesDados = dados;
    if (dados.estado === "ilegivel") marcarEstado(sub, "erro", "Lista de importantes ilegível no disco. Nada é mostrado nem alterado por este painel.");
    else marcarEstado(sub, dados.estado === "vazio" ? "vazio" : null);
    importantesCartao(dados, false);
    renderizarImportantes();
  } catch (_) {
    importantesDados = null;
    byId("importantes-lista").replaceChildren();
    byId("importantes-resumo-lista").textContent = "Não medido: a leitura dos importantes falhou.";
    importantesCartao(null, true);
    marcarEstado(sub, "erro");
  } finally {
    importantesBusy = false;
    if (importantesPendente) { importantesPendente = false; carregarImportantes(); }
  }
}
async function importantesMudar(id, estado) {
  if (importantesEnviando) { importantesAviso("Aguarde a ação anterior terminar."); return; }
  importantesEnviando = true;
  try { await importantesPedir("/api/importantes/estado", {id, estado}); importantesAviso(""); }
  catch (erro) { importantesAviso(importantesErro(erro.status, erro.motivo)); }
  finally { importantesEnviando = false; }
  await carregarImportantes();
}
function importantesEditar(item, li) {
  const campoTexto = document.createElement("textarea");
  campoTexto.rows = 3; campoTexto.maxLength = 4000; campoTexto.value = item.texto;
  campoTexto.setAttribute("aria-label", "Texto do importante");
  const campoNota = document.createElement("input");
  campoNota.type = "text"; campoNota.maxLength = 500; campoNota.value = item.nota || "";
  campoNota.placeholder = "Nota (opcional)"; campoNota.setAttribute("aria-label", "Nota do importante");
  const salvar = importantesBotao("Salvar", async () => {
    const texto = campoTexto.value.trim();
    if (!texto) { importantesAviso("O texto não pode ficar vazio."); return; }
    try { await importantesPedir("/api/importantes/editar", {id: item.id, texto, nota: campoNota.value.trim()}); importantesAviso("Alteração guardada."); }
    catch (erro) { importantesAviso(importantesErro(erro.status, erro.motivo)); }
    await carregarImportantes();
  }, "btn");
  const cancelar = importantesBotao("Cancelar", () => renderizarImportantes(), "btn secondary");
  const barra = document.createElement("div");
  barra.className = "importantes-barra";
  barra.append(salvar, cancelar);
  const edicao = document.createElement("div");
  edicao.className = "importantes-editar";
  edicao.append(campoTexto, campoNota, barra);
  li.replaceChildren(edicao);
  campoTexto.focus();
}
async function importantesAdicionar(evento) {
  evento.preventDefault();
  const campo = byId("importantes-texto");
  const texto = campo.value.trim();
  if (!texto) { importantesAviso("Escreva o texto antes de guardar."); return; }
  if (importantesEnviando) { importantesAviso("Aguarde a ação anterior terminar."); return; }
  importantesEnviando = true;
  try { await importantesPedir("/api/importantes", {texto}); campo.value = ""; importantesAviso("Guardado."); }
  catch (erro) { importantesAviso(importantesErro(erro.status, erro.motivo)); }
  finally { importantesEnviando = false; }
  await carregarImportantes();
}
async function importantesTrazer() {
  const botao = byId("importantes-trazer");
  if (importantesEnviando) { importantesAviso("Aguarde a ação anterior terminar."); return; }
  importantesEnviando = true;
  botao.disabled = true;
  try {
    const dados = await importantesPedir("/api/importantes/trazer", {});
    importantesAviso(`Trazidas do Conselho: ${dados.trazidas}. Já estavam aqui: ${dados.ja_estavam}. Recusadas por segredo ou tamanho: ${dados.recusadas}.`);
  } catch (erro) { importantesAviso(importantesErro(erro.status, erro.motivo)); }
  finally { importantesEnviando = false; botao.disabled = false; }
  await carregarImportantes();
}
byId("importantes-form").addEventListener("submit", importantesAdicionar);
byId("importantes-trazer").addEventListener("click", importantesTrazer);
byId("importantes-filtro").addEventListener("change", renderizarImportantes);
carregarImportantes();

// Entrada: a seção vem do hash; sem hash ou com hash desconhecido, abre panorama.
// F7 (16/11): a rolagem da carga também começa no topo; o navegador rola até #secao depois do script.
window.addEventListener("load", () => { if (window.scrollTo && !hashDeItemInterno()) window.scrollTo(0, 0); }, {once: true});
aoMudarHash();
})();
