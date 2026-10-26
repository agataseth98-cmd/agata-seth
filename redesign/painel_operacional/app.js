"use strict";

const SERVICE_LABELS = {
  "omniroute.service": "OmniRoute",
  "omniroute-sanitizer.service": "Sanitizador",
  "seth-gateway.service": "Gateway da Seth",
  "seth-verificador.service": "Verificador",
};
const STATE_LABELS = {
  ok: "ATIVO",
  warning: "ATENÇÃO",
  unknown: "DESCONHECIDO",
  stale: "DESATUALIZADO",
};
let lastSnapshot = null;
let lastUnitSignature = null;
let collectionUnavailable = false;
let lastNoticeKey = null;
let busy = false;
let pollTimer = null;

function byId(id) {
  return document.getElementById(id);
}

function stateLabel(state) {
  return STATE_LABELS[state] || STATE_LABELS.unknown;
}

function formatTime(value) {
  if (!value) return "não disponível";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "não disponível";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(date);
}

function expired(item) {
  const deadline = Date.parse(item && item.fresh_until);
  return !Number.isFinite(deadline) || deadline < Date.now();
}

function effectiveState(item, forcedStale = false) {
  if (!item || item.state === "unknown") return "unknown";
  return forcedStale || expired(item) ? "stale" : item.state;
}

function makeTag(state, text) {
  const tag = document.createElement("span");
  tag.className = "state-tag " + state;
  tag.textContent = text || stateLabel(state);
  return tag;
}

function renderServices(services, forcedStale = false) {
  const root = byId("services");
  root.replaceChildren();
  for (const service of services || []) {
    const state = effectiveState(service, forcedStale);
    const card = document.createElement("article");
    card.className = "service-card";

    const titleGroup = document.createElement("div");
    const title = document.createElement("h3");
    title.className = "service-name";
    title.textContent = SERVICE_LABELS[service.unit] || "Unidade";
    const unit = document.createElement("div");
    unit.className = "service-unit";
    unit.textContent = service.unit || "unidade não informada";
    titleGroup.append(title, unit);

    card.append(titleGroup, makeTag(state));
    const meta = document.createElement("div");
    meta.className = "service-meta";
    const detail = document.createElement("span");
    detail.textContent = service.active_state
      ? service.active_state + "/" + (service.sub_state || "?") +
        (service.last_error ? " · última coleta falhou" : "")
      : (service.error || "estado sem leitura");
    const source = document.createElement("span");
    source.textContent =
      "Fonte: " + (service.source || "não informada") +
      " · ref. " + (service.source_ref || "não informada");
    const observed = document.createElement("span");
    observed.textContent = "Observado: " + formatTime(service.observed_at);
    const validity = document.createElement("span");
    validity.textContent = "Válido até: " + formatTime(service.fresh_until);
    meta.append(detail, source, observed, validity);
    if (service.last_attempt_at) {
      const attempt = document.createElement("span");
      attempt.textContent = "Última tentativa sem resposta: " + formatTime(service.last_attempt_at);
      meta.append(attempt);
    }
    card.append(meta);
    root.append(card);
  }
  if (!services || !services.length) {
    const empty = document.createElement("p");
    empty.className = "service-card";
    empty.textContent = "Nenhum estado de unidade foi recebido.";
    root.append(empty);
  }
}

function trackingLabel(value) {
  if (value === "tracking_up_to_date") return "referência local do último fetch: alinhada";
  if (value === "tracking_diverged") return "referência local do último fetch: divergente";
  if (value === "no_upstream") return "sem referência local";
  return "sem leitura";
}

function renderGit(git, forcedStale = false) {
  const state = effectiveState(git, forcedStale);
  byId("git-state").className = "state-tag " + state;
  byId("git-state").textContent = stateLabel(state);
  byId("git-branch").textContent = git.branch || "—";
  byId("git-head").textContent = git.head || "—";
  byId("git-dirty").textContent = Number.isInteger(git.dirty_count)
    ? (git.dirty_count === 0 ? "árvore limpa" : String(git.dirty_count) + " item(ns)")
    : "—";
  byId("git-tracking").textContent = trackingLabel(git.tracking);
  byId("git-source").textContent =
    "Fonte: " + (git.source || "não informada") +
    " · ref. " + (git.source_ref || "não informada") +
    " · commit " + (git.commit || git.head || "não disponível") +
    " · observado " + formatTime(git.observed_at) +
    " · válido até " + formatTime(git.fresh_until) +
    (git.last_attempt_at ? " · última tentativa falhou " + formatTime(git.last_attempt_at) : "") +
    " · sem consulta à rede.";
}

function aggregateUnitState(services) {
  const states = services.map((service) => effectiveState(service));
  if (states.includes("unknown")) return "unknown";
  if (states.includes("warning")) return "warning";
  if (states.includes("stale")) return "stale";
  return "ok";
}

function preserveLastKnown(snapshot) {
  if (!lastSnapshot) return snapshot;
  const previousUnits = new Map((lastSnapshot.services || []).map((service) => [service.unit, service]));
  const services = (snapshot.services || []).map((service) => {
    if (service.state !== "unknown") return service;
    const previous = previousUnits.get(service.unit);
    if (!previous || previous.state === "unknown") return service;
    return {
      ...previous,
      state: "stale",
      last_error: service.error || "leitura indisponível",
      last_attempt_at: service.observed_at,
    };
  });
  let git = snapshot.git || {};
  if (git.state === "unknown" && lastSnapshot.git && lastSnapshot.git.state !== "unknown") {
    git = {
      ...lastSnapshot.git,
      state: "stale",
      last_error: git.error || "leitura indisponível",
      last_attempt_at: git.observed_at,
    };
  }
  return { ...snapshot, services, git, state: aggregateUnitState(services) };
}

function unitSignature(snapshot) {
  return (snapshot.services || []).map((service) =>
    service.unit + ":" + effectiveState(service)
  ).join("|");
}

function announce(key, message) {
  if (key === lastNoticeKey) return;
  lastNoticeKey = key;
  byId("notice").textContent = message;
}

function render(snapshot, forcedStale = false) {
  const services = snapshot.services || [];
  const states = services.map((service) => effectiveState(service, forcedStale));
  const overall = states.includes("unknown") ? "unknown"
    : states.includes("warning") ? "warning"
      : states.includes("stale") ? "stale" : "ok";
  byId("overall-indicator").className = "indicator " + overall;
  byId("overall-state").textContent = stateLabel(overall);
  byId("summary-detail").textContent = overall === "stale"
    ? "Último estado de serviço preservado; leitura fora do prazo."
    : overall === "unknown"
      ? "Sem leitura válida para pelo menos uma unidade; estado atual não verificável."
      : snapshot.scope;
  byId("observed-at").textContent = formatTime(snapshot.observed_at);
  byId("collection-note").textContent =
    "Resumo calculado só das quatro unidades · leitura concluída " +
    formatTime(snapshot.observed_at) + " · validade até " + formatTime(snapshot.fresh_until) + ".";
  renderServices(services, forcedStale);
  renderGit(snapshot.git || {}, forcedStale);
}

function showFirstFailure() {
  byId("overall-indicator").className = "indicator unknown";
  byId("overall-state").textContent = "Sem leitura";
  byId("summary-detail").textContent = "A coleta local ainda não respondeu.";
  renderServices([]);
  renderGit({});
}

async function refresh(manual = false) {
  if (busy || document.visibilityState === "hidden") return;
  busy = true;
  byId("refresh").disabled = true;
  try {
    const response = await fetch("/api/status", {
      method: "GET",
      cache: "no-store",
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) throw new Error("HTTP " + response.status);
    const snapshot = await response.json();
    if (snapshot.schema_version !== 1) throw new Error("versão de dados incompatível");

    const mergedSnapshot = preserveLastKnown(snapshot);
    const nextSignature = unitSignature(mergedSnapshot);
    const previousSignature = lastUnitSignature;
    const recovered = collectionUnavailable;
    lastSnapshot = mergedSnapshot;
    lastUnitSignature = nextSignature;
    collectionUnavailable = false;
    render(mergedSnapshot);

    if (manual) {
      announce("manual:" + formatTime(snapshot.observed_at), "Leitura manual concluída.");
    } else if (recovered) {
      announce("recovered:" + nextSignature, "Coleta das unidades retomada.");
    } else if ((mergedSnapshot.services || []).some((service) => effectiveState(service) === "stale")) {
      announce("stale:" + nextSignature, "Leitura das unidades desatualizada.");
    } else if (previousSignature !== null && previousSignature !== nextSignature) {
      announce("changed:" + nextSignature, "Estado das unidades alterado.");
    }
  } catch (_error) {
    collectionUnavailable = true;
    if (lastSnapshot) {
      render(lastSnapshot, true);
      announce("unavailable", "Coleta indisponível; última leitura preservada.");
    } else {
      showFirstFailure();
      announce("unavailable", "Coleta local indisponível.");
    }
  } finally {
    busy = false;
    byId("refresh").disabled = false;
  }
}

function syncPollingWithVisibility() {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
  if (document.visibilityState === "visible") {
    refresh(false);
    pollTimer = window.setInterval(() => refresh(false), 60000);
  }
}

async function searchWiki(event) {
  event.preventDefault();
  const query = byId("wiki-query").value.trim();
  const mode = byId("wiki-mode").value;
  const button = byId("wiki-submit");
  const status = byId("wiki-status");
  const root = byId("wiki-results");
  if (!query || query.length > 200) {
    status.textContent = "Informe uma busca com até 200 caracteres.";
    return;
  }
  button.disabled = true;
  root.replaceChildren();
  status.textContent = "Buscando no vault e no índice local…";
  try {
    const response = await fetch("/api/wiki/search", {
      method: "POST",
      cache: "no-store",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ query, mode }),
    });
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    if (data.schema_version !== 1 || !Array.isArray(data.results)) throw new Error("resposta incompatível");
    for (const item of data.results) {
      const article = document.createElement("article");
      article.className = "wiki-result";
      const heading = document.createElement("h3");
      heading.textContent = item.command === "busca_semantica" ? "Busca por sentido" : "Busca por texto";
      const output = document.createElement("pre");
      output.textContent = item.error ? "Busca indisponível: " + item.error : item.output || "Sem conteúdo retornado.";
      article.append(heading, output);
      root.append(article);
    }
    status.textContent = "Fonte: " + data.source + " · observado " + formatTime(data.observed_at) + " · " + data.source_ref;
  } catch (_error) {
    status.textContent = "Busca indisponível. O painel não preserva resultados anteriores.";
  } finally {
    button.disabled = false;
  }
}

byId("refresh").addEventListener("click", () => refresh(true));
byId("wiki-search-form").addEventListener("submit", searchWiki);
document.addEventListener("visibilitychange", syncPollingWithVisibility);
syncPollingWithVisibility();
