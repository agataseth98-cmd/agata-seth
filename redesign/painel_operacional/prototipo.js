"use strict";
// Painel unificado (/prototipo): uma tela com sete seções, roteadas pelo hash (#panorama, #conversa, ...).
// O arquivo inteiro fica numa IIFE; o único nome exposto no escopo global é window.AgataPainel.
(function () {
const byId = (id) => document.getElementById(id);
const AgataPainel = (window.AgataPainel = window.AgataPainel || {});
const SECOES = ["panorama", "conversa", "conselho", "sistema", "conhecimento", "custos", "qualidade"];
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

function setSidebarCollapsed(collapsed) {
  shell.classList.toggle("sidebar-collapsed", collapsed);
  sidebarToggle.setAttribute("aria-expanded", String(!collapsed));
  sidebarToggle.setAttribute("aria-label", collapsed ? "Expandir navegação lateral" : "Recolher navegação lateral");
  sidebarToggle.title = sidebarToggle.getAttribute("aria-label");
  navSecoes.forEach((button) => { button.title = button.textContent.trim(); });
  try { localStorage.setItem("agata-sidebar-collapsed", String(collapsed)); } catch (_) { /* sem persistência */ }
}
let sidebarCollapsed = false;
try { sidebarCollapsed = localStorage.getItem("agata-sidebar-collapsed") === "true"; } catch (_) { /* sem persistência */ }
setSidebarCollapsed(sidebarCollapsed);
sidebarToggle.addEventListener("click", () => setSidebarCollapsed(!shell.classList.contains("sidebar-collapsed")));

// Subpainel visível da seção aberta (filho direto da seção, sem atributo hidden).
function subAtivo() {
  return document.querySelector(".secao:not([hidden]) > .sub:not([hidden])");
}
function filterSearch(value) {
  const ativo = subAtivo();
  if (!ativo) return;
  const cards = [...ativo.querySelectorAll(".cap-card")];
  const query = value.toLocaleLowerCase("pt-BR");
  let visible = 0;
  cards.forEach((card) => {
    const matchesText = !query || card.innerText.toLocaleLowerCase("pt-BR").includes(query);
    const matchesState = ativo.dataset.sub !== "capacidades" || capFilter === "all" || card.dataset.state === capFilter;
    card.hidden = !(matchesText && matchesState);
    if (!card.hidden) visible++;
  });
  const empty = byId("no-results");
  if (empty) empty.classList.toggle("show", ativo.dataset.sub === "capacidades" && cards.length > 0 && visible === 0);
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
  integracoes: () => loadDetails(),
  memoria: () => loadDetails(),
  capacidades: () => loadCapacidades(),
  grafo: () => carregarGrafo(),
  lacunas: () => { calcularLacunas(); carregarLacunasCanon(); },
  visao: () => carregarVisaoSistema(),
  qualidade: () => { carregarQualidade(); carregarMedicoes(); },
  sdd: () => carregarSdd(),
  frentes: () => carregarFrentes(),
  "conselho-memoria": () => carregarMemoriaConselho(),
};

function mostrarSub(secao, sub) {
  const alvo = byId(secao);
  if (!alvo) return;
  const subs = [...alvo.querySelectorAll(":scope > .sub")];
  const escolhido = subs.find((item) => item.dataset.sub === sub) || subs[0];
  if (!escolhido) return;
  subs.forEach((item) => { item.hidden = item !== escolhido; });
  alvo.querySelectorAll(":scope > .abas > button[data-sub]").forEach((botao) => {
    const ativa = botao.dataset.sub === escolhido.dataset.sub;
    botao.setAttribute("aria-selected", String(ativa));
    botao.classList.toggle("ativa", ativa);
  });
  const nome = escolhido.dataset.sub;
  if (CARREGAR_SUB[nome]) CARREGAR_SUB[nome]();
  else if (nome.startsWith("nv-") && typeof AgataPainel.carregarNovaVersao === "function") AgataPainel.carregarNovaVersao(nome);
  filterSearch(search.value.trim());
}
function mostrarSecao(secao, sub) {
  const alvo = byId(SECOES.includes(secao) ? secao : "panorama");
  document.querySelectorAll(".secao").forEach((item) => { item.hidden = item !== alvo; });
  navSecoes.forEach((botao) => {
    if (botao.dataset.secao === alvo.id) botao.setAttribute("aria-current", "page");
    else botao.removeAttribute("aria-current");
  });
  byId("crumb").textContent = "Agata / " + (alvo.dataset.titulo || "Panorama");
  search.value = "";
  mostrarSub(alvo.id, sub);
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
function aoMudarHash() { mostrarSecao(secaoDoHash()); }
window.addEventListener("hashchange", aoMudarHash);
window.addEventListener("popstate", aoMudarHash);
navSecoes.forEach((botao) => botao.addEventListener("click", () => irPara(botao.dataset.secao)));
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
  const until = Date.parse(item.fresh_until || "");
  if (forcedStale || item.state === "stale" || !Number.isFinite(until) || Date.now() > until) return "stale";
  return item.state === "ok" ? "ok" : "warning";
}
function stateLabel(state) {
  return {ok: "ATIVO", warning: "ATENÇÃO", stale: "DESATUALIZADO", unknown: "SEM LEITURA"}[state] || "SEM LEITURA";
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
  el.className = "chip " + ({ok: "active", warning: "partial", stale: "partial", unknown: "horizon"}[state] || "horizon");
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
  const badge = document.createElement("span"); badge.className = "chip " + ({ok: "active", warning: "partial", stale: "partial", unknown: "horizon"}[status] || "horizon"); badge.textContent = labelText || stateLabel(status);
  line.append(label, badge); item.append(line);
  if (detail) { const note = document.createElement("small"); note.textContent = detail; item.append(note); }
  return item;
}
function replaceRows(id, items, empty) {
  const root = byId(id); root.replaceChildren();
  if (!items.length) { const p = document.createElement("p"); p.textContent = empty; root.append(p); return; }
  root.append(...items);
}
function sourceLine(item) {
  if (!item) return "Sem leitura.";
  return "Fonte: " + (item.source || "não informada") + (item.source_ref ? " · " + item.source_ref : "") +
    " · observado " + niceTime(item.observed_at) + " · válido até " + niceTime(item.fresh_until) +
    (item.last_error ? " · " + item.last_error : "");
}
const serviceNames = {"omniroute.service":"OmniRoute", "omniroute-sanitizer.service":"Sanitizador", "seth-gateway.service":"Seth Gateway", "seth-verificador.service":"Verificador", "piper-tts.service":"Piper", "openvino-whisper.service":"Whisper", "openvino-embeddings.service":"Embeddings", "obsidian-ro-proxy.service":"Proxy Obsidian", "discord-mcp.service":"Discord MCP", "navegador-mcp.service":"Navegador MCP", "laya-roteador.service":"Laya", "seth-escriba.service":"Escriba"};
const timerNames = {"agata-manutencao.timer":"Janela de manutenção", "agata-vault-inbox.timer":"Inbox do Obsidian"};
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
function render(snapshot, forced = false) {
  renderedSnapshotState = snapshotStateKey(snapshot, forced);
  const services = snapshot.services || [];
  const states = services.map((item) => stateOf(item, forced));
  const overall = !states.length || states.includes("unknown") ? "unknown" : states.includes("warning") ? "warning" : states.includes("stale") ? "stale" : "ok";
  const active = services.filter((item) => stateOf(item, forced) === "ok").length;
  chip("units-panel-state", overall);
  set("overview-health", overall === "unknown" ? "Sem leitura" : overall === "stale" ? "Vencida" : active + "/" + services.length);
  set("overview-units-note", services.length + " unidades observadas · seth-verificador");
  set("overview-alert", overall === "ok" ? active + " de " + services.length + " unidades observadas ativas." : overall === "stale" ? "Última leitura das unidades está vencida." : "Há unidade sem leitura ou que requer atenção.");
  replaceRows("live-services", unitRows(services, forced), "Nenhum estado recebido.");
  if (byId("overview-services")) replaceRows("overview-services", unitRows(services, forced), "Nenhum estado recebido.");
  if (byId("overview-source")) set("overview-source", "Coleta concluída " + niceTime(snapshot.observed_at) + " · válida até " + niceTime(snapshot.fresh_until));
  set("overview-updated", collectionFailed ? "Coleta indisponível; última leitura preservada." : "Leitura local observada " + niceTime(snapshot.observed_at));
  const git = snapshot.git || {}; const gitState = stateOf(git, forced);
  chip("git-panel-state", gitState, gitState === "ok" ? "LEITURA VÁLIDA" : null);
  const pendentes = ((snapshot.proposals && snapshot.proposals.items) || []).filter((p) => !p.marker_present && !p.substituida_por && p.versionada !== false).length;
  set("hero-status", "Serviços: " + active + " de " + services.length + " ativos · Git: " + ({ok: "leitura válida", warning: "atenção", stale: "leitura vencida", unknown: "sem leitura"}[gitState] || "sem leitura") + " · Propostas aguardando assinatura: " + pendentes + ".");
  set("git-branch", git.branch || "—"); set("git-head", git.head || "—");
  set("git-upstream", {tracking_up_to_date:"alinhada no último fetch",tracking_diverged:"divergente no último fetch",no_upstream:"sem referência"}[git.tracking] || "sem leitura");
  set("git-dirty", Number.isInteger(git.dirty_count) ? git.dirty_count + " item(ns)" : "—");
  set("git-age", sourceLine(git));
  set("hero-sync-label", gitState === "unknown" ? "Git local · sem leitura" : gitState === "stale" ? "Git local · leitura vencida" : gitState === "ok" ? "Git local · leitura válida" : "Git local · atenção");
  set("hero-sync-head", git.head || "—"); set("hero-sync-note", sourceLine(git));
  set("overview-git", gitState === "unknown" ? "—" : gitState === "stale" ? "Vencido" : gitState === "ok" ? "Em dia" : "Atenção");
  const chat = snapshot.chat || {}; const chatState = stateOf(chat, forced);
  chip("chat-state", chatState, chatState === "ok" ? "HTTP 200" : null);
  set("chat-source", sourceLine(chat) + (chat.http_status ? " · HTTP " + chat.http_status : "") + ". A saúde do endpoint não garante cada função do chat.");
  const timers = snapshot.timers || []; const timerStates = timers.map((item) => stateOf(item, forced));
  const timerState = !timerStates.length || timerStates.includes("unknown") ? "unknown" : timerStates.includes("stale") ? "stale" : timerStates.includes("warning") ? "warning" : "ok";
  chip("timer-panel-state", timerState, timerState === "ok" ? "LEITURA VÁLIDA" : null);
  set("overview-timers", timerState === "unknown" ? "—" : timerState === "stale" ? "Vencida" : timerStates.filter((x) => x === "ok").length + "/" + timerStates.length);
  replaceRows("live-timers", timerRows(timers, forced), "Timers indisponíveis.");
  replaceRows("maintenance-timers", timerRows(timers, forced), "Timers indisponíveis.");
  replaceRows("live-tasks", taskRows(snapshot.maintenance, forced), "Tarefas indisponíveis.");
  replaceRows("maintenance-tasks", taskRows(snapshot.maintenance, forced), "Tarefas indisponíveis.");
  set("timer-age", "Fonte: systemctl de usuário · disparo, resultado da unidade e resultado de cada tarefa são leituras distintas.");
  renderProposals(snapshot.proposals || {}, forced);
  renderModels(snapshot.models || {}, forced);
}
function renderDetails(data, forced = false) {
  renderedDetailsState = detailsStateKey(data, forced);
  const integrations = data.integrations || [];
  const states = integrations.map((item) => stateOf(item, forced));
  const aggregate = !states.length || states.includes("unknown") ? "unknown" : states.includes("stale") ? "stale" : states.includes("warning") ? "warning" : "ok";
  chip("integration-state", aggregate, aggregate === "ok" ? "LEITURA VÁLIDA" : null);
  replaceRows("integration-list", unitRows(integrations, forced), "Unidades indisponíveis.");
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
    lastDetails = data; detailsFailed = false; marcarEstado("sistema", null); renderDetails(data);
  } catch (_) {
    detailsFailed = true;
    marcarEstado("sistema", "erro", "Não medido: consulta de integrações indisponível." + (lastDetails ? " Última leitura preservada como vencida." : ""));
    if (lastDetails) renderDetails(lastDetails, true);
    else { set("integration-source", "Consulta indisponível."); set("memory-source", "Consulta indisponível."); }
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
    const ativo = subAtivo();
    if (ativo && ["integracoes", "memoria"].includes(ativo.dataset.sub)) loadDetails();
  }
});
setInterval(() => {
  if (document.visibilityState !== "visible") return;
  atualizarPanorama();
  const ativo = subAtivo();
  if (ativo && ["integracoes", "memoria"].includes(ativo.dataset.sub)) loadDetails();
}, 60000);
setInterval(() => {
  if (document.visibilityState !== "visible") return;
  if (lastSnapshot && snapshotStateKey(lastSnapshot, collectionFailed) !== renderedSnapshotState) render(lastSnapshot, collectionFailed);
  if (lastDetails && detailsStateKey(lastDetails, detailsFailed) !== renderedDetailsState) renderDetails(lastDetails, detailsFailed);
}, 5000);
atualizarPanorama();

/* (27/10/2026) Selo de cada capacidade vem de /api/capacidades; sem sonda, o cartão é documento. */
async function loadCapacidades() {
  let dados = null;
  try { dados = await fetchJson("/api/capacidades", {headers: {Accept: "application/json"}}); } catch (_) { dados = null; }
  const porId = new Map(((dados && dados.items) || []).map((i) => [i.id, i]));
  const rotuloVivo = {ok: "ativo", warning: "sem resposta", unknown: "sem leitura"};
  document.querySelectorAll("[data-live]").forEach((el) => {
    const item = porId.get(el.dataset.live);
    el.textContent = item ? (rotuloVivo[item.state] || "sem leitura") : "sem leitura";
  });
  document.querySelectorAll("[data-sub='capacidades'] .cap-card").forEach((cartao) => {
    const chip = cartao.querySelector(".chip");
    const probe = cartao.dataset.probe;
    if (!chip) return;
    if (probe === "documento") {
      cartao.dataset.state = "documento";
      chip.className = "chip horizon"; chip.textContent = "DOCUMENTO · sem leitura";
      const botao = cartao.querySelector("button.evidence");
      if (botao) { botao.dataset.body = "Esta capacidade é documento: não há sonda de leitura. O texto descreve o desenho e não é medição do sistema."; botao.dataset.source = "documento do canon"; }
      return;
    }
    const item = porId.get(probe);
    if (!item) { cartao.dataset.state = "planned"; chip.className = "chip planned"; chip.textContent = "SEM LEITURA"; return; }
    cartao.dataset.state = {ok: "active", warning: "partial", unknown: "planned"}[item.state] || "planned";
    const rotulo = {ok: ["chip active", "LEITURA ATIVA"], warning: ["chip partial", "ATENÇÃO"], unknown: ["chip planned", "SEM LEITURA"]}[item.state];
    chip.className = rotulo[0]; chip.textContent = rotulo[1];
    ligarCartoesClicaveis();
    const botao = cartao.querySelector("button.evidence");
    if (botao) { botao.dataset.body = item.evidencia || "Sem leitura nesta medição."; botao.dataset.source = item.source + " · " + item.source_ref; }
  });
}
/* F5: ao carregar a página, atualiza todas as leituras (não só a aba aberta). */
window.addEventListener("load", () => { loadDetails(); loadCapacidades(); });

/* (27/10/2026) Textos de evidência com data antiga viram leitura do momento (timers e unidades). */
function evidenciaDe(botao, texto, fonte) {
  if (!botao) return;
  botao.dataset.body = texto;
  botao.dataset.source = fonte;
}
function aplicarEvidenciasVivas() {
  const timers = (lastSnapshot && lastSnapshot.timers) || [];
  const porUnidade = new Map(timers.map((t) => [t.unit, t]));
  const hora = (valor) => (valor ? valor.replace(/ -03$/, "") : "não informada");
  const manutencao = porUnidade.get("agata-manutencao.timer");
  const inbox = porUnidade.get("agata-vault-inbox.timer");
  if (manutencao) {
    const botao = document.querySelector('button.evidence[data-title="Janela de manutenção"]');
    evidenciaDe(botao, "Medido agora: agata-manutencao.timer " + (manutencao.active_state || "sem estado") + "; próxima execução " + hora(manutencao.next_trigger) + "; última " + hora(manutencao.last_trigger) + ". O resultado da tarefa não é inferido do disparo.", "systemctl --user show · agata-manutencao.timer");
  }
  if (inbox) {
    const botao = document.querySelector('button.evidence[data-title="Rotinas locais"]');
    evidenciaDe(botao, "Medido agora: agata-vault-inbox.timer " + (inbox.active_state || "sem estado") + "; última execução " + hora(inbox.last_trigger) + ". Atenção: a MEMÓRIAS (804, 22/10) registra que o timer foi parado pelo Humano. Estado atual e decisão divergem; quem decide é o Humano.", "systemctl --user show · agata-vault-inbox.timer · MEMÓRIAS (804)");
  }
  fetchJson("/api/capacidades", {headers: {Accept: "application/json"}}).then((dados) => {
    const navegar = ((dados && dados.items) || []).find((i) => i.id === "navegar");
    if (!navegar) return;
    document.querySelectorAll('button.evidence[data-title="Navegador e Discord"]').forEach((botao) => {
      evidenciaDe(botao, navegar.evidencia, "systemctl --user show · navegador-mcp e discord-mcp");
    });
  }).catch(() => {});
}
window.addEventListener("load", () => setTimeout(aplicarEvidenciasVivas, 1500));

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
  document.querySelectorAll("[data-sub='capacidades'] .cap-card[data-probe]:not([data-probe='documento'])").forEach((cartao) => {
    if (cartao.dataset.ligado) return;
    cartao.dataset.ligado = "1";
    cartao.tabIndex = 0; cartao.setAttribute("role", "button");
    cartao.addEventListener("click", (e) => { if (!e.target.closest("button")) abrirEvidenciaDoCartao(cartao); });
    cartao.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); abrirEvidenciaDoCartao(cartao); } });
  });
}

/* (27/10/2026) Conversa com a Seth pelo gateway local (/api/seth/chat/stream, com fallback para /api/seth/chat). Só texto; histórico só na memória desta aba. */
const SETH_MODELO_PADRAO = "seth-livre";
let sethAtual = {id: null, titulo: "", mensagens: [], modelo: SETH_MODELO_PADRAO};
// Lista do seletor. Vem de GET /api/seth/modelos (lista fixa no servidor); sem ela, fica só o padrão.
let sethModelos = [{id: SETH_MODELO_PADRAO, rotulo: "Seth (padrão)", descricao: ""}];
const SETH_EXEMPLOS = ["Quais propostas aguardam assinatura?", "O que o decisor Jev faz?", "Como o canon protege as decisões?"];
const SETH_NOTAS = ["Correção do turno anterior", "Verificação da Máquina"];
// Limites espelhados do servidor: chat_stream.py (MAX_MENSAGENS, MAX_CARACTERES_MENSAGEM), server.py (CHAT_STREAM_LIMITE_BYTES)
// e armazem.py (CONVERSA_LIMITE_BYTES). test_chat_ui.py confere que os números são os mesmos.
const SETH_MAX_MENSAGENS = 20;
const SETH_MAX_CARACTERES = 4000;
const SETH_LIMITE_PEDIDO_BYTES = 131072;
const SETH_LIMITE_CONVERSA_BYTES = 262144;
const SETH_LIMITE_IMPORTACAO_BYTES = 263168;
const SETH_BUSCA_MAX_CARACTERES = 120;
// Organização (lote 3, 09/11/2026): estado da lista vindo de GET /api/seth/conversas; filtros e busca só na tela.
let sethLista = {items: [], pastas: [], marcadores: [], total: 0, organizacao: "ok"};
let sethFiltro = {pasta: "", marcador: ""};
let sethBuscaSeq = 0;
// Lixeira (09/11/2026): conversas apagadas, de GET /api/seth/lixeira. `respondendo` vale enquanto a Seth responde e o salvar termina.
let sethLixeira = {items: [], total: 0, ilegiveis: 0, indisponivel: false};
let sethRespondendo = false;
function sethNova(temporaria = false) { return {id: null, titulo: "", mensagens: [], modelo: sethAtual.modelo, temporaria}; }
function sethHora(data = new Date()) { return data.toLocaleTimeString("pt-BR", {hour: "2-digit", minute: "2-digit"}); }
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
  if (m.modelo_real) return "modelo: " + m.modelo_real;
  if (m.modelo) return "modelo: " + m.modelo + " (escolhido)";
  return "modelo: não registrado";
}
function sethInline(container, texto) {
  const partes = String(texto).split(/(\*\*[^*]+\*\*|`[^`]+`)/);
  for (const p of partes) {
    if (!p) continue;
    if (p.startsWith("**") && p.endsWith("**")) { const b = document.createElement("strong"); b.textContent = p.slice(2, -2); container.append(b); }
    else if (p.startsWith("`") && p.endsWith("`")) { const c = document.createElement("code"); c.textContent = p.slice(1, -1); container.append(c); }
    else container.append(document.createTextNode(p));
  }
}
function sethMarkdown(texto, destino) {
  const linhas = String(texto).split("\n");
  let lista = null, codigo = null;
  for (const linha of linhas) {
    if (linha.trim().startsWith("```")) {
      if (codigo) { codigo = null; continue; }
      codigo = document.createElement("pre"); const c = document.createElement("code"); codigo.append(c); destino.append(codigo); lista = null; continue;
    }
    if (codigo) { codigo.firstChild.textContent += linha + "\n"; continue; }
    if (SETH_NOTAS.some((p) => linha.trim().startsWith(p))) { const aside = document.createElement("aside"); aside.className = "nota"; aside.textContent = linha.trim(); destino.append(aside); lista = null; continue; }
    const cabeca = linha.match(/^(#{1,3})\s+(.*)$/);
    if (cabeca) { const h = document.createElement("h4"); sethInline(h, cabeca[2]); destino.append(h); lista = null; continue; }
    const item = linha.match(/^\s*[-*]\s+(.*)$/);
    if (item) { if (!lista) { lista = document.createElement("ul"); destino.append(lista); } const li = document.createElement("li"); sethInline(li, item[1]); lista.append(li); continue; }
    if (!linha.trim()) { lista = null; continue; }
    const p = document.createElement("p"); sethInline(p, linha); destino.append(p); lista = null;
  }
}
function sethMensagem(m, indice) {
  const log = byId("seth-transcript");
  const msg = document.createElement("article"); msg.className = "msg msg-" + (m.role === "user" ? "user" : "assistant");
  msg.dataset.indice = String(indice);
  const cab = document.createElement("div"); cab.className = "msg-head";
  const quem = document.createElement("strong"); quem.textContent = m.role === "user" ? "Você" : "Seth";
  const hora = document.createElement("span"); hora.textContent = m.hora || "";
  cab.append(quem, hora);
  if (m.role === "assistant") { const modelo = document.createElement("span"); modelo.className = "msg-modelo"; modelo.textContent = sethTextoModelo(m); cab.append(modelo); }
  const corpo = document.createElement("div"); corpo.className = "msg-body";
  if (m.role === "user") corpo.textContent = m.content; else sethMarkdown(m.content, corpo);
  msg.append(cab, corpo);
  if (m.aviso) { const aviso = document.createElement("p"); aviso.className = "seth-aviso"; aviso.textContent = m.aviso; msg.append(aviso); }
  if (m.role === "assistant") {
    const acoes = document.createElement("div"); acoes.className = "msg-acoes";
    const copiar = document.createElement("button"); copiar.type = "button"; copiar.className = "text-link"; copiar.textContent = "Copiar";
    copiar.addEventListener("click", async () => { try { await navigator.clipboard.writeText(m.content); copiar.textContent = "Copiado"; } catch (_) { copiar.textContent = "Não foi possível copiar"; } setTimeout(() => copiar.textContent = "Copiar", 1600); });
    acoes.append(copiar);
    if (indice === sethAtual.mensagens.length - 1) {
      const regerar = document.createElement("button"); regerar.type = "button"; regerar.className = "text-link"; regerar.textContent = "Regenerar";
      regerar.addEventListener("click", () => sethRegerar());
      acoes.append(regerar);
    }
    msg.append(acoes);
  }
  log.append(msg);
}
function sethDesenhar() {
  const log = byId("seth-transcript"); log.replaceChildren();
  if (!sethAtual.mensagens.length) {
    const vazio = document.createElement("p"); vazio.className = "seth-vazio"; vazio.textContent = "Nenhuma conversa aberta. Pergunte sobre o estado, uma decisão ou uma proposta.";
    log.append(vazio);
  }
  sethAtual.mensagens.forEach((m, i) => sethMensagem(m, i));
  log.scrollTop = log.scrollHeight;
  sethTitulo(sethAtual.titulo);
  sethPintarAvisoSalvar();
  sethPintarTemporaria();
  sethPintarExportar();
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
function sethMostrarOrg(texto) { const aviso = byId("seth-org-aviso"); if (!aviso) return; aviso.textContent = texto || ""; aviso.hidden = !texto; }
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
  const aviso = byId("seth-ilegiveis-aviso"); if (!aviso) return;
  const n = sethLista.ilegiveis + sethLixeira.ilegiveis;
  if (!n) { aviso.textContent = ""; aviso.hidden = true; return; }
  aviso.textContent = n === 1
    ? "1 arquivo de conversa não pôde ser lido e não aparece aqui. Nada foi apagado; confira a pasta de conversas."
    : n + " arquivos de conversa não puderam ser lidos e não aparecem aqui. Nada foi apagado; confira a pasta de conversas.";
  aviso.hidden = false;
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
  const titulo = document.createElement("strong"); titulo.textContent = c.titulo;
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
function sethPreencher(box, itens, vazio) {
  box.replaceChildren();
  if (!itens.length) { box.append(sethVazio(vazio)); return; }
  const fixadas = itens.filter((c) => c.fixada); const outras = itens.filter((c) => !c.fixada);
  if (fixadas.length) { box.append(sethGrupo("Fixadas")); fixadas.forEach((c) => box.append(sethLinha(c))); }
  if (outras.length) { if (fixadas.length) box.append(sethGrupo("Recentes")); outras.forEach((c) => box.append(sethLinha(c))); }
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
function sethLinha(c) {
  const linha = document.createElement("div");
  linha.className = "seth-item" + (c.id === sethAtual.id ? " ativa" : "") + (c.fixada ? " fixada" : "");
  const abrir = document.createElement("button"); abrir.type = "button"; abrir.className = "seth-item-abrir"; abrir.textContent = c.titulo;
  abrir.title = c.mensagens + " mensagens · " + c.atualizada;
  abrir.addEventListener("click", () => sethAbrir(c.id));
  const meta = document.createElement("div"); meta.className = "seth-item-meta";
  if (c.fixada) meta.append(sethSelo("Fixada", "seth-selo-fixada"));
  if (c.arquivada) meta.append(sethSelo("Arquivada", "seth-selo-arquivada"));
  const pasta = sethLista.pastas.find((p) => p.id === c.pasta);
  if (pasta) meta.append(sethSelo("Pasta: " + pasta.nome, "seth-selo-pasta"));
  (c.marcadores || []).forEach((m) => meta.append(sethSelo("#" + m, "seth-selo-marcador")));
  const acoes = document.createElement("div"); acoes.className = "seth-item-acoes";
  const renomear = sethTexto("Renomear", () => sethRenomear(c, linha));
  const fixar = sethTexto(c.fixada ? "Desfixar" : "Fixar", () => sethOrganizar(c.id, {fixada: !c.fixada}));
  const arquivar = sethTexto(c.arquivada ? "Desarquivar" : "Arquivar", () => sethOrganizar(c.id, {arquivada: !c.arquivada}));
  // Apagar leva a conversa para a Lixeira (09/11/2026); a purga definitiva fica só na própria Lixeira.
  const apagar = sethTexto("Apagar", () => {
    if (apagar.dataset.confirma !== "1") { apagar.dataset.confirma = "1"; apagar.textContent = "Confirmar: mover para a Lixeira"; return; }
    sethApagar(c.id);
  });
  acoes.append(renomear, fixar, arquivar, apagar);
  const org = document.createElement("details"); org.className = "seth-item-org";
  const resumo = document.createElement("summary"); resumo.textContent = "Pasta e marcadores";
  org.append(resumo, sethCampoPasta(c), sethCampoMarcadores(c));
  linha.append(abrir, meta, acoes, org);
  return linha;
}
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
  const titulo = document.createElement("strong"); titulo.textContent = r.titulo;
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
  if (sethTrocaBloqueada()) return;
  try {
    const dados = await fetchJson("/api/seth/conversa?id=" + encodeURIComponent(id), {headers: {Accept: "application/json"}});
    if (sethTrocaBloqueada()) return; // uma resposta começou enquanto a conversa carregava
    sethAtual = {id: dados.id, titulo: dados.titulo, mensagens: dados.mensagens, modelo: dados.modelo || SETH_MODELO_PADRAO, temporaria: false};
    sethDesenhar(); sethListar(); sethMostrarModelo();
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
  botao.textContent = "Conversa temporária: " + (ligada ? "ligada" : "desligada");
  aviso.hidden = !ligada;
}
function sethAlternarTemporaria() {
  if (sethTrocaBloqueada()) return;
  const ligar = !sethAtual.temporaria;
  sethAtual = sethNova(ligar);
  sethDesenhar(); sethListar();
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
  if (m.role === "assistant") { if (m.modelo) item.modelo = m.modelo; if (m.modelo_real) item.modelo_real = m.modelo_real; }
  return item;
}
// Grava a conversa `alvo` (por padrão, a aberta). O id e o aviso são gravados nela, não na tela: se a tela trocou
// durante o await, só a conversa de origem muda e a tela não é repintada com ela (09/11/2026).
async function sethSalvar(alvo = sethAtual) {
  if (alvo.temporaria || !alvo.mensagens.length) return false; // conversa temporária nunca é gravada
  if (!alvo.titulo) alvo.titulo = alvo.mensagens[0].content.slice(0, 60);
  const corpo = JSON.stringify({id: alvo.id, titulo: alvo.titulo, modelo: alvo.modelo, mensagens: alvo.mensagens.map(sethParaSalvar)});
  if (new TextEncoder().encode(corpo).length > SETH_LIMITE_CONVERSA_BYTES) { sethNaoSalvou(sethMotivoRecusa(413), true, alvo); return false; }
  try {
    const r = await fetch("/api/seth/conversa", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: corpo});
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
      if (id === sethAtual.id) { sethAtual = sethNova(false); sethDesenhar(); }
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
      const r = await fetch("/api/seth/conversa", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: JSON.stringify({id: c.id, titulo: novo, modelo: dados.modelo, mensagens: dados.mensagens})});
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
/* Janela enviada ao gateway: as últimas 20 mensagens, cada uma com até 4000 caracteres, e o pedido inteiro até 131072 bytes.
   Corta o que passa do limite (a conversa salva não muda) e conta o que cortou ou deixou de fora, para o aviso. */
function sethJanela(mensagens) {
  const marca = "\n[cortado pelo painel para caber no limite de " + SETH_MAX_CARACTERES + " caracteres]";
  const espaco = SETH_MAX_CARACTERES - Array.from(marca).length;
  let cortadas = 0;
  const janela = mensagens.slice(-SETH_MAX_MENSAGENS).map((m) => {
    const pontos = Array.from(m.content);
    if (pontos.length <= SETH_MAX_CARACTERES) return {role: m.role, content: m.content};
    cortadas++;
    return {role: m.role, content: pontos.slice(0, espaco).join("") + marca};
  });
  const bytes = (lista) => new TextEncoder().encode(JSON.stringify({mensagens: lista})).length;
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
async function sethLerStream(mensagens, modelo, parcial, aoTexto) {
  const r = await fetch("/api/seth/chat/stream", {method: "POST", credentials: "same-origin", cache: "no-store",
    headers: {"Content-Type": "application/json", Accept: "text/event-stream"}, body: JSON.stringify({mensagens, modelo})});
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
    try { await leitor.cancel(); } catch (_) { /* stream já fechado */ }
  }
}
async function sethChatInteiro(mensagens, modelo, parcial) {
  const r = await fetch("/api/seth/chat", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"},
    body: JSON.stringify({messages: mensagens, modelo})});
  if (!r.ok) throw Object.assign(new Error(sethErro(r.status, await sethMotivo(r))), {status: r.status});
  parcial.modelo_real = r.headers.get("X-Modelo-Real") || "";
  return r.json();
}
async function sethEnviar(textoUsuario, reaproveitar) {
  const estado = byId("seth-status"); const botao = byId("seth-send"); const campo = byId("seth-input"); const log = byId("seth-transcript");
  // A conversa de origem é capturada antes de qualquer await: a pergunta, a resposta e o salvar são dela (09/11/2026).
  const alvo = sethAtual;
  sethRespondendo = true;
  if (!reaproveitar) alvo.mensagens.push({role: "user", content: textoUsuario, hora: sethHora()});
  sethDesenhar();
  botao.disabled = true; sethStatus("PENSANDO", "partial");
  const pensando = document.createElement("p"); pensando.className = "seth-vazio"; pensando.textContent = "A Seth está respondendo…";
  log.append(pensando);
  const janela = sethJanela(alvo.mensagens);
  const mensagens = janela.mensagens;
  const avisoJanela = sethAvisoJanela(janela);
  const modelo = alvo.modelo; // o modelo do envio fica preso a ele, mesmo se o seletor mudar depois
  const parcial = {texto: ""};
  let textoNo = null;
  const aoTexto = (delta) => {
    if (!textoNo) {
      pensando.remove();
      const bolha = document.createElement("article"); bolha.className = "msg msg-assistant";
      const corpo = document.createElement("div"); corpo.className = "msg-body";
      textoNo = document.createTextNode(""); corpo.append(textoNo); bolha.append(corpo);
      log.append(bolha);
    }
    textoNo.appendData(delta); log.scrollTop = log.scrollHeight;
  };
  try {
    let conteudo;
    try {
      conteudo = await sethLerStream(mensagens, modelo, parcial, aoTexto);
    } catch (erro) {
      const transporte = !erro.motivoStream && !parcial.texto && (erro.semStream || erro.status === undefined || erro.status === 404 || erro.status >= 500);
      if (!transporte) throw erro;
      const dados = await sethChatInteiro(mensagens, modelo, parcial);
      conteudo = dados.content;
    }
    alvo.mensagens.push({role: "assistant", content: conteudo, hora: sethHora(), modelo, modelo_real: parcial.modelo_real || "", aviso: avisoJanela});
    if (alvo === sethAtual) { sethDesenhar(); sethStatus("PRONTA", "planned"); }
    await sethSalvar(alvo); // espera o salvar: o botão só volta quando a conversa está gravada (ou o aviso mostra o motivo)
  } catch (erro) {
    if (!reaproveitar) alvo.mensagens.pop();
    if (alvo === sethAtual) {
      sethDesenhar();
      const aviso = document.createElement("p"); aviso.className = "seth-vazio"; aviso.textContent = "Não consegui responder agora: " + (erro.message || "falha desconhecida") + ".";
      log.append(aviso);
      sethStatus("INDISPONÍVEL", "horizon");
    }
  } finally { sethRespondendo = false; botao.disabled = false; campo.focus(); }
}
function sethRegerar() {
  const ultimo = sethAtual.mensagens[sethAtual.mensagens.length - 1];
  if (!ultimo || ultimo.role !== "assistant") return;
  sethAtual.mensagens.pop();
  const pergunta = sethAtual.mensagens[sethAtual.mensagens.length - 1];
  if (pergunta && pergunta.role === "user") sethEnviar(pergunta.content, true);
}
function ligarConversaSeth() {
  const form = byId("seth-form");
  if (!form || form.dataset.ligado) return;
  form.dataset.ligado = "1";
  sethExemplos(); sethDesenhar(); sethListar(); sethCarregarModelos();
  byId("seth-modelo").addEventListener("change", (e) => { sethAtual.modelo = e.target.value; sethMostrarModelo(); });
  const campo = byId("seth-input");
  campo.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
  byId("seth-nova").addEventListener("click", () => { if (sethTrocaBloqueada()) return; sethAtual = sethNova(false); sethDesenhar(); sethListar(); sethStatus("PRONTA", "planned"); campo.focus(); });
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const texto = campo.value.trim();
    if (!texto || byId("seth-send").disabled) return;
    campo.value = "";
    sethEnviar(texto, false);
  });
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
  document.querySelectorAll("[data-sub='capacidades'] .cap-card").forEach((cartao) => {
    const titulo = cartao.querySelector("h3").textContent;
    const probe = cartao.dataset.probe;
    if (probe === "documento") itens.push({nome: titulo, motivo: "sem sonda: é documento, não leitura do sistema", onde: "O que posso fazer"});
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
  document.querySelectorAll("[data-sub='capacidades'] .cap-card[data-probe='documento'] .chip").forEach((chip) => {
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
    if (j.estado === "ok" || j.estado === "falhou") nota.textContent = (j.estado === "ok" ? "Concluído" : "Falhou") + ": " + j.acao + (j.modelo ? " em " + j.modelo : "") + " (" + j.segundos + " s). " + (j.detalhe || "");
  }
}
function ligarMedicao(botao, rotulo, pedido) {
  let armado = false;
  botao.addEventListener("click", async () => {
    if (!armado) { armado = true; botao.textContent = "Confirmar: " + rotulo.toLowerCase(); return; }
    armado = false; botao.textContent = rotulo; botao.disabled = true;
    try {
      await fetchJson("/api/medicoes/executar", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: JSON.stringify(pedido())});
    } catch (_) { byId("medir-nota").textContent = "Não foi possível iniciar (ocupado ou fora da lista)."; }
    botao.disabled = false; carregarMedicoes();
  });
}
ligarMedicao(byId("medir-recuperacao"), "Medir recuperação da busca", () => ({acao: "recuperacao"}));
ligarMedicao(byId("medir-semantica"), "Medir busca por sentido", () => ({acao: "recuperacao_semantica"}));
ligarMedicao(byId("medir-contexto"), "Medir contexto efetivo", () => ({acao: "contexto", modelo: byId("medir-modelo").value, tarefa: byId("medir-tarefa").value, raciocinio: byId("medir-raciocinio").value}));
async function carregarQualidade() {
  const kpis = byId("qualidade-kpis"); const lista = byId("qualidade-lista"); const titulo = byId("qualidade-titulo");
  if (!kpis || !lista) return;
  kpis.replaceChildren(); lista.replaceChildren();
  let dados = null;
  try { dados = await fetchJson("/api/qualidade-llm", {headers: {Accept: "application/json"}}); } catch (_) { dados = null; }
  if (!dados || !Array.isArray(dados.items)) { if (titulo) titulo.textContent = "Sem leitura"; return; }
  const rotulo = {ok: "ok", warning: "atenção", unknown: "não medido"};
  dados.items.forEach((item) => {
    const d = document.createElement("div"); d.className = "kpi";
    const l = document.createElement("div"); l.className = "label"; l.textContent = item.titulo;
    const v = document.createElement("div"); v.className = "note"; v.textContent = item.valor;
    const e = document.createElement("div"); e.className = "note"; e.textContent = (rotulo[item.estado] || "sem leitura").toUpperCase();
    d.append(l, v, e); kpis.append(d);
    const li = document.createElement("li"); li.textContent = item.titulo + ": " + item.evidencia + " (fonte: " + item.fonte + ")";
    lista.append(li);
  });
  const atencao = dados.items.filter((i) => i.estado === "warning").length;
  const naoMedidos = dados.items.filter((i) => i.estado === "unknown").length;
  if (titulo) titulo.textContent = atencao + " em atenção · " + naoMedidos + " não medidos";
}
async function carregarVisaoSistema() {
  const kpis = byId("visao-kpis"); const lista = byId("visao-melhorias");
  if (!kpis || !lista) return;
  kpis.replaceChildren(); lista.replaceChildren();
  const cartao = (rotulo, valor, aba) => {
    const d = document.createElement("div"); d.className = "kpi"; d.tabIndex = 0; d.setAttribute("role", "button");
    const l = document.createElement("div"); l.className = "label"; l.textContent = rotulo;
    const v = document.createElement("div"); v.className = "value"; v.textContent = valor;
    d.append(l, v); if (aba) { d.dataset.openPage = aba; }
    kpis.append(d);
  };
  const melhoria = (texto, aba) => {
    const li = document.createElement("li"); li.textContent = texto;
    if (aba) { const b = document.createElement("button"); b.className = "text-link"; b.type = "button"; b.dataset.openPage = aba; b.textContent = " ver aba"; li.append(b); }
    lista.append(li);
  };
  try {
    const [status, caps, lac] = await Promise.all([
      fetchJson("/api/status", {headers: {Accept: "application/json"}}),
      fetchJson("/api/capacidades", {headers: {Accept: "application/json"}}),
      fetchJson("/api/lacunas", {headers: {Accept: "application/json"}}),
    ]);
    const servicos = status.services || [];
    const ativos = servicos.filter((x) => x.state === "ok").length;
    cartao("Serviços ativos", ativos + " de " + servicos.length, "operacao");
    cartao("Timers", String((status.timers || []).filter((x) => x.state === "ok").length) + " ok", "operacao");
    cartao("Git", status.git ? status.git.head : "—", "operacao");
    cartao("Conversa (LibreChat)", status.chat && status.chat.http_status === 200 ? "responde" : "sem resposta", "operacao");
    const modelos = (status.models && status.models.models) || [];
    cartao("Modelos registrados", String(modelos.length), "modelos");
    const cap = caps.items || [];
    cartao("Capacidades com leitura", cap.filter((x) => x.state === "ok").length + " de " + cap.length, "capacidades");
    cartao("Lacunas agora", String((lac.items || []).length), "lacunas");
    const props = (status.proposals && status.proposals.items) || [];
    const naoVersionadas = props.filter((p) => p.versionada === false);
    const pendentes = props.filter((p) => !p.substituida_por && !p.marker_present && p.versionada !== false);
    cartao("Propostas sem assinatura", String(pendentes.length), "plano");
    (lac.items || []).forEach((i) => melhoria("Lacuna · " + i.nome + " — " + i.motivo, "lacunas"));
    pendentes.forEach((p) => melhoria("Proposta sem assinatura · " + p.name, "plano"));
    naoVersionadas.forEach((p) => melhoria("LACUNA · não versionada · " + p.name + " — existe só no checkout local, sem commit no git", "plano"));
    cap.filter((x) => x.state !== "ok").forEach((x) => melhoria("Capacidade sem leitura ok · " + x.id, "capacidades"));
    if (!lista.children.length) melhoria("Nada pendente nas leituras de agora.", null);
  } catch (erro) {
    const p = document.createElement("p"); p.textContent = "Visão indisponível (" + erro.message + "). Nada anterior foi mantido como atual."; lista.append(p);
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

// Entrada: a seção vem do hash; sem hash ou com hash desconhecido, abre panorama.
aoMudarHash();
})();
