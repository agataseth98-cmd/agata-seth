"use strict";

const byId = (id) => document.getElementById(id);
const nav = [...document.querySelectorAll(".nav button")];
const pages = [...document.querySelectorAll(".page")];
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
  nav.forEach((button) => { button.title = button.textContent.trim(); });
  try { localStorage.setItem("agata-sidebar-collapsed", String(collapsed)); } catch (_) { /* sem persistência */ }
}
let sidebarCollapsed = false;
try { sidebarCollapsed = localStorage.getItem("agata-sidebar-collapsed") === "true"; } catch (_) { /* sem persistência */ }
setSidebarCollapsed(sidebarCollapsed);
sidebarToggle.addEventListener("click", () => setSidebarCollapsed(!shell.classList.contains("sidebar-collapsed")));

function filterSearch(value) {
  const active = document.querySelector(".page.active");
  if (!active) return;
  const cards = [...active.querySelectorAll(".cap-card")];
  const query = value.toLocaleLowerCase("pt-BR");
  let visible = 0;
  cards.forEach((card) => {
    const matchesText = !query || card.innerText.toLocaleLowerCase("pt-BR").includes(query);
    const matchesState = active.id !== "page-capacidades" || capFilter === "all" || card.dataset.state === capFilter;
    card.hidden = !(matchesText && matchesState);
    if (!card.hidden) visible++;
  });
  const empty = byId("no-results");
  if (empty) empty.classList.toggle("show", active.id === "page-capacidades" && cards.length > 0 && visible === 0);
}
function showPage(name) {
  const page = byId("page-" + name);
  if (!page) return;
  pages.forEach((item) => item.classList.toggle("active", item === page));
  nav.forEach((button) => {
    if (button.dataset.page === name) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  byId("crumb").textContent = "Agata / " + (page.dataset.title || "Panorama");
  search.value = "";
  filterSearch("");
  if (name === "integracoes" || name === "memoria") loadDetails();
  if (name === "capacidades") loadCapacidades();
  if (name === "grafo") carregarGrafo();
}
nav.forEach((button) => button.addEventListener("click", () => showPage(button.dataset.page)));
document.querySelectorAll("[data-open-page]").forEach((button) => button.addEventListener("click", () => showPage(button.dataset.openPage)));
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
  set("overview-proposals", state === "unknown" ? "—" : String(value.total));
}
function render(snapshot, forced = false) {
  renderedSnapshotState = snapshotStateKey(snapshot, forced);
  const services = snapshot.services || [];
  const states = services.map((item) => stateOf(item, forced));
  const overall = !states.length || states.includes("unknown") ? "unknown" : states.includes("warning") ? "warning" : states.includes("stale") ? "stale" : "ok";
  const active = services.filter((item) => stateOf(item, forced) === "ok").length;
  chip("units-panel-state", overall);
  set("overview-health", overall === "unknown" ? "Sem leitura" : overall === "stale" ? "Vencida" : active + "/" + services.length);
  set("overview-alert", overall === "ok" ? "Quatro unidades observadas ativas." : overall === "stale" ? "Última leitura das unidades está vencida." : "Há unidade sem leitura ou que requer atenção.");
  replaceRows("live-services", unitRows(services, forced), "Nenhum estado recebido.");
  if (byId("overview-services")) replaceRows("overview-services", unitRows(services, forced), "Nenhum estado recebido.");
  if (byId("overview-source")) set("overview-source", "Coleta concluída " + niceTime(snapshot.observed_at) + " · válida até " + niceTime(snapshot.fresh_until));
  set("overview-updated", collectionFailed ? "Coleta indisponível; última leitura preservada." : "Leitura local observada " + niceTime(snapshot.observed_at));
  const git = snapshot.git || {}; const gitState = stateOf(git, forced);
  chip("git-panel-state", gitState, gitState === "ok" ? "LEITURA VÁLIDA" : null);
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
async function refresh(manual = false) {
  if (busy || document.visibilityState === "hidden") return;
  busy = true;
  byId("refresh-main").disabled = true; byId("refresh-status").disabled = true;
  try {
    const data = await fetchJson("/api/status", {headers: {Accept: "application/json"}});
    if (!Array.isArray(data.services) || !Array.isArray(data.timers) || !data.git) throw new Error("resposta incompleta");
    const before = lastSnapshot && JSON.stringify(lastSnapshot.services.map((item) => [item.unit, item.state]));
    lastSnapshot = mergeSnapshot(lastSnapshot, data); collectionFailed = false;
    render(lastSnapshot);
    const after = JSON.stringify(lastSnapshot.services.map((item) => [item.unit, item.state]));
    if (manual) announce("Leitura manual concluída.");
    else if (before !== null && before !== after) announce("Estado das unidades alterado.");
    else if (!before) announce("Leitura local concluída.");
  } catch (_) {
    collectionFailed = true;
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
    lastDetails = data; detailsFailed = false; renderDetails(data);
  } catch (_) {
    detailsFailed = true;
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
      const link = document.createElement("a"); link.href = "obsidian://open?vault=agata&file=" + encodeURIComponent(path); link.textContent = "Abrir " + path + " ↗"; card.append(link);
    }
    root.append(card);
  }
}
async function searchWiki(event) {
  event.preventDefault();
  const query = byId("wiki-query").value.trim();
  if (!query || query.length > 200 || /[\r\n\0]/.test(query)) { set("wiki-status", "Informe uma busca de até 200 caracteres em uma linha."); return; }
  byId("wiki-submit").disabled = true; wikiData = null; byId("wiki-results").replaceChildren();
  set("wiki-status", "Consultando fontes locais…");
  try {
    // Busca semântica pode levar até 95 s; não repete nem guarda a consulta.
    const response = await fetch("/api/wiki/search", {method: "POST", credentials: "same-origin", cache: "no-store", headers: {"Content-Type": "application/json", Accept: "application/json"}, body: JSON.stringify({query, mode: byId("wiki-mode").value})});
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    if (!data || data.schema_version !== 1 || !Array.isArray(data.results)) throw new Error("resposta incompatível");
    wikiData = data; renderWiki();
    set("wiki-status", "Fonte: " + data.source + " · observado " + niceTime(data.observed_at) + " · " + data.source_ref + ". O filtro atua sobre os resultados retornados.");
  } catch (_) { set("wiki-status", "Busca indisponível. Nenhum resultado foi preservado."); }
  finally { byId("wiki-submit").disabled = false; }
}
byId("wiki-form").addEventListener("submit", searchWiki);
byId("wiki-source").addEventListener("change", renderWiki);
byId("refresh-main").addEventListener("click", () => refresh(true));
byId("refresh-status").addEventListener("click", () => refresh(true));
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") {
    refresh();
    const active = document.querySelector(".page.active");
    if (active && ["page-integracoes", "page-memoria"].includes(active.id)) loadDetails();
  }
});
setInterval(() => {
  if (document.visibilityState !== "visible") return;
  refresh();
  const active = document.querySelector(".page.active");
  if (active && ["page-integracoes", "page-memoria"].includes(active.id)) loadDetails();
}, 60000);
setInterval(() => {
  if (document.visibilityState !== "visible") return;
  if (lastSnapshot && snapshotStateKey(lastSnapshot, collectionFailed) !== renderedSnapshotState) render(lastSnapshot, collectionFailed);
  if (lastDetails && detailsStateKey(lastDetails, detailsFailed) !== renderedDetailsState) renderDetails(lastDetails, detailsFailed);
}, 5000);
refresh();

/* (27/10/2026) Selo de cada capacidade vem de /api/capacidades; sem sonda, o cartão é documento. */
async function loadCapacidades() {
  let dados = null;
  try { dados = await fetchJson("/api/capacidades", {headers: {Accept: "application/json"}}); } catch (_) { dados = null; }
  const porId = new Map(((dados && dados.items) || []).map((i) => [i.id, i]));
  document.querySelectorAll("#page-capacidades .cap-card").forEach((cartao) => {
    const chip = cartao.querySelector(".chip");
    const probe = cartao.dataset.probe;
    if (!chip) return;
    if (probe === "documento") {
      chip.className = "chip horizon"; chip.textContent = "DOCUMENTO · sem leitura";
      const botao = cartao.querySelector("button.evidence");
      if (botao) { botao.dataset.body = "Esta capacidade é documento: não há sonda de leitura. O texto descreve o desenho e não é medição do sistema."; botao.dataset.source = "documento do canon"; }
      return;
    }
    const item = porId.get(probe);
    if (!item) { chip.className = "chip planned"; chip.textContent = "SEM LEITURA"; return; }
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
  document.querySelectorAll("#page-capacidades .cap-card[data-probe]:not([data-probe='documento'])").forEach((cartao) => {
    if (cartao.dataset.ligado) return;
    cartao.dataset.ligado = "1";
    cartao.tabIndex = 0; cartao.setAttribute("role", "button");
    cartao.addEventListener("click", (e) => { if (!e.target.closest("button")) abrirEvidenciaDoCartao(cartao); });
    cartao.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); abrirEvidenciaDoCartao(cartao); } });
  });
}

/* (27/10/2026) Conversa com a Seth pelo gateway local (/api/seth/chat). Só texto; histórico só na memória desta aba. */
const sethHistorico = [];
function sethEscrever(papel, texto) {
  const linha = document.createElement("p");
  linha.style.margin = "0";
  const quem = document.createElement("strong");
  quem.textContent = papel === "user" ? "Você: " : "Seth: ";
  linha.append(quem, document.createTextNode(texto));
  byId("seth-transcript").append(linha);
  linha.scrollIntoView({block: "end"});
}
function ligarConversaSeth() {
  const form = byId("seth-form");
  if (!form || form.dataset.ligado) return;
  form.dataset.ligado = "1";
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const campo = byId("seth-input"); const botao = byId("seth-send"); const estado = byId("seth-status");
    const texto = campo.value.trim();
    if (!texto || botao.disabled) return;
    sethHistorico.push({role: "user", content: texto});
    sethEscrever("user", texto); campo.value = "";
    botao.disabled = true; estado.textContent = "PENSANDO"; estado.className = "chip partial";
    try {
      const r = await fetch("/api/seth/chat", {method: "POST", headers: {"Content-Type": "application/json", Accept: "application/json"},
        body: JSON.stringify({messages: sethHistorico.slice(-20)})});
      if (!r.ok) throw new Error(r.status === 429 ? "outra conversa em curso" : "HTTP " + r.status);
      const dados = await r.json();
      sethHistorico.push({role: "assistant", content: dados.content});
      sethEscrever("assistant", dados.content);
      estado.textContent = "PRONTA"; estado.className = "chip planned";
    } catch (erro) {
      sethHistorico.pop();
      sethEscrever("assistant", "Não consegui responder agora: " + erro.message + ".");
      estado.textContent = "INDISPONÍVEL"; estado.className = "chip horizon";
    } finally { botao.disabled = false; campo.focus(); }
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
