"use strict";

const $ = (id) => document.getElementById(id);
const state = { csrf: "", providers: [], actions: [], legacy: [] };

async function api(path, options = {}) {
  const response = await fetch(path, {
    cache: "no-store",
    ...options,
    headers: { Accept: "application/json", ...(options.headers || {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `${response.status} ${response.statusText}`);
  }
  return response.json();
}

function jsonOptions(body) {
  return { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, csrf: state.csrf }) };
}

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined && text !== null) element.textContent = String(text);
  if (className) element.className = className;
  return element;
}

const statusText = {
  pending: "aguardando aprovação humana", approved: "aprovado; aguardando extensão",
  running: "em execução na aba autorizada", executing: "ferramenta aprovada em execução",
  completed: "concluído", rejected: "rejeitado pelo Humano", error: "falha",
  unknown: "resultado incerto; reenvio bloqueado",
};

function renderProviders(items) {
  const body = $("providerTable").querySelector("tbody");
  body.replaceChildren();
  for (const provider of items) {
    const row = document.createElement("tr");
    for (const value of [provider.name, provider.kind, provider.access_mode, provider.availability]) {
      row.append(node("td", value));
    }
    body.append(row);
  }
  const select = $("site");
  const selected = select.value;
  select.replaceChildren(node("option", "Selecione um adaptador"));
  select.options[0].value = "";
  for (const id of state.providers) {
    const option = node("option", items.find((item) => item.id === id)?.name || id);
    option.value = id;
    select.append(option);
  }
  if (state.providers.includes(selected)) select.value = selected;
}

function renderApproval(item) {
  const card = node("li", null, "approval-card");
  const payload = item.payload || {};
  card.append(node("div", `${item.kind === "send" ? "ENVIO" : "FERRAMENTA"} · ${payload.site || "ferramenta local"} · ${statusText[item.status] || item.status}`, "meta"));
  const details = item.kind === "send" ? payload.text
    : `${payload.tool || "ferramenta"}\nArgumentos: ${JSON.stringify(payload.args || {})}${payload.text ? `\nTexto: ${payload.text}` : ""}`;
  card.append(node(item.kind === "send" ? "pre" : "pre", details, "history-text"));
  if (item.status === "pending") {
    const actions = node("div", null, "approval-actions");
    const approve = node("button", item.kind === "send" ? "Aprovar e enviar" : "Aprovar e executar ferramenta", "primary");
    approve.type = "button";
    approve.addEventListener("click", () => decide(item, true));
    const reject = node("button", "Rejeitar", "danger");
    reject.type = "button";
    reject.addEventListener("click", () => decide(item, false));
    actions.append(approve, reject);
    card.append(actions);
  }
  if (item.result?.text) card.append(node("pre", item.result.text));
  if (item.result?.error) card.append(node("p", item.result.error, "error"));
  return card;
}

async function decide(item, approve) {
  const what = item.kind === "send" ? `enviar para ${item.payload.site}` : `executar ${item.payload.tool}`;
  if (!window.confirm(`${approve ? "Confirmar" : "Confirmar rejeição"}: ${what}?\n\nRevise o pedido exibido antes de continuar.`)) return;
  try {
    await api("/api/relay-council/decision", jsonOptions({ id: item.id, hash: item.hash, approve }));
    await refresh();
  } catch (error) { $("status").textContent = `decisão não concluída: ${error.message}`; }
}

function renderQueue(items) {
  const pending = items.filter((item) => item.status === "pending");
  const sends = pending.filter((item) => item.kind === "send");
  const tools = pending.filter((item) => item.kind === "tool");
  $("filaCount").textContent = String(sends.length);
  $("filaLista").replaceChildren(...(sends.length ? sends.map((item) => renderApproval(item)) : [node("li", "nenhum envio aguardando aprovação.", "hint")]));
  $("decisaoLista").replaceChildren(...(tools.length ? tools.map((item) => renderApproval(item)) : [node("li", "nenhuma ferramenta aguardando aprovação.", "hint")]));
}

function renderGroups(groups) {
  const root = $("rodadasLista");
  root.replaceChildren();
  if (!groups.length) { root.append(node("li", "nenhuma rodada registrada.", "hint")); return; }
  for (const group of groups) {
    const item = node("li", null, "approval-card");
    const kind = { debate: "debate", chain: "cadeia", evaluation: "bateria" }[group.kind] || group.kind;
    item.append(node("div", `${kind} · ${group.sites.join(", ")} · ${group.completed}/${group.actions.length} respostas · ${group.pending_approval} aprovações pendentes`, "meta"));
    if (group.synthesis) item.append(node("p", `síntese: ${group.synthesis}`));
    for (const action of group.actions) {
      item.append(node("div", `${action.payload.site} · ${statusText[action.status] || action.status}`, "meta"));
      if (action.result?.text) item.append(node("pre", action.result.text));
    }
    root.append(item);
  }
}

function renderHistory(actions, legacy) {
  const root = $("historicoLista");
  root.replaceChildren();
  const current = actions.map((item) => ({
    when: Number(item.created || 0) * 1000,
    title: `${item.payload?.site || item.payload?.tool || item.kind} · ${statusText[item.status] || item.status}`,
    text: item.result?.text || item.result?.error || item.payload?.text || JSON.stringify(item.payload || {}),
  }));
  const old = (legacy.items || []).map((entry) => {
    const data = entry.data || {};
    return { when: Number(data.ts || 0), title: `${data.site || "protótipo"} · ${data.ok ? "OK" : "ERRO"} · histórico anterior`, text: data.text || data.error || "sem conteúdo" };
  });
  const rows = [...current, ...old].sort((a, b) => b.when - a.when).slice(0, 30);
  if (!rows.length) root.append(node("li", "nenhum turno registrado.", "hint"));
  for (const row of rows) {
    const item = node("li", null, "approval-card");
    const when = Number.isFinite(row.when) && row.when > 0 ? new Date(row.when).toLocaleString("pt-BR") : "horário não informado";
    item.append(node("div", `${row.title} · ${when}`, "meta"), node("pre", row.text, "history-text"));
    root.append(item);
  }
}

async function refresh() {
  try {
    const [snapshot, catalog] = await Promise.all([
      api("/api/relay-council/state"), api("/api/relay-council/catalog"),
    ]);
    state.csrf = snapshot.csrf;
    state.providers = snapshot.providers || [];
    state.actions = snapshot.actions || [];
    state.legacy = snapshot.legacy_history || [];
    renderProviders(catalog.providers || []);
    renderQueue(state.actions);
    renderGroups(snapshot.groups || []);
    renderHistory(state.actions, state.legacy);
    const pending = snapshot.pending || 0;
    const age = snapshot.last_poll ? `${Math.round(Date.now() / 1000 - snapshot.last_poll)}s` : "sem poll";
    $("status").textContent = `painel conectado · ${pending} pedidos pendentes · extensão: ${age}`;
    $("status").className = "status connected";
  } catch (error) {
    $("status").textContent = `indisponível: ${error.message}`;
    $("status").className = "status disconnected";
  }
}

$("promptForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const site = $("site").value;
  const text = $("pergunta").value.trim();
  if (!site || !text) { $("turnoHint").textContent = "Escolha o adaptador e escreva um prompt."; return; }
  try {
    await api("/api/relay-council/actions", jsonOptions({ kind: "send", payload: { site, text } }));
    $("pergunta").value = "";
    $("turnoHint").textContent = "Pedido criado. Ele só será enviado depois da sua aprovação na fila.";
    await refresh();
  } catch (error) { $("turnoHint").textContent = `pedido não criado: ${error.message}`; }
});

$("btnConversa").addEventListener("click", async () => {
  const sites = $("chainSites").value.split(",").map((value) => value.trim()).filter(Boolean);
  const prompt = $("pergunta").value.trim();
  const kind = $("groupKind").value;
  const repetitions = Number.parseInt($("groupRepetitions").value, 10);
  if (!prompt) { $("turnoHint").textContent = "Escreva o tema no campo Prompt antes de preparar a rodada."; return; }
  if (kind === "evaluation" && sites.length !== 1) { $("turnoHint").textContent = "Para a bateria, informe exatamente um adaptador."; return; }
  if (!window.confirm(`Preparar ${kind} para ${sites.join(", ")}? Cada envio ainda exigirá aprovação individual.`)) return;
  try {
    await api("/api/relay-council/groups", jsonOptions({ kind, sites, prompt, repetitions }));
    $("turnoHint").textContent = "Rodada preparada; cada prompt aguarda sua aprovação individual.";
    await refresh();
  } catch (error) { $("turnoHint").textContent = `rodada não preparada: ${error.message}`; }
});

$("tool").addEventListener("change", () => {
  const defaults = { SEARCH: { canon: "" }, STATE: {}, CACHE: { ler: 5 }, AUDIT: {}, RELAY: { to: "gemini", question: "" }, DELIVER: {} };
  $("toolArgs").value = JSON.stringify(defaults[$("tool").value] || {});
});

$("toolForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  let args;
  try { args = JSON.parse($("toolArgs").value || "{}"); }
  catch (_) { $("status").textContent = "argumentos precisam ser JSON válido"; return; }
  const tool = $("tool").value;
  const text = $("toolText").value.trim();
  if (!window.confirm(`Solicitar ${tool}? A ferramenta só será executada após sua aprovação na fila.`)) return;
  try {
    await api("/api/relay-council/actions", jsonOptions({ kind: "tool", payload: { tool, args, text } }));
    $("toolText").value = "";
    await refresh();
  } catch (error) { $("status").textContent = `pedido de ferramenta não criado: ${error.message}`; }
});

refresh();
window.setInterval(refresh, 3000);
