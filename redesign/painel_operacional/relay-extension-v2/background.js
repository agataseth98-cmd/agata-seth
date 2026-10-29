// Executor local: apenas abas abertas pelo usuário e tarefas aprovadas no painel.
const PAINEL_URL = "http://127.0.0.1:20146";
const RELAY_CLIENT_ID = "agata-relay-v2";
// O relay trabalha apenas com abas que o Humano abriu e autenticou.
// Abrir abas automaticamente pode gerar popups, telas de login e estado
// visual inesperado; quando desabilitado, a ausência vira erro manual claro.
const POLL_INTERVAL_MS = 2000;      // normal
const POLL_INTERVAL_IDLE_MS = 5000;  // após 5 polls vazios
const POLL_TIMEOUT_MS = 5000;
const TURN_STABLE_MS = 8000;         // 8s sem mudança = resposta terminada
const TURN_MAX_WAIT_MS = 150000;     // 2,5 min por turno; depois disso o item vira sem_leitura
const READY_TIMEOUT_MS = 60000;      // 1 min para a página ficar pronta
const TAB_ACTIVATION_SETTLE_MS = 900; // dá ao site tempo para receber foco/visibilidade
const TAB_OPERATION_TIMEOUT_MS = 4000;

let idleCount = 0;
let connected = false;

// keepalive: alarm a cada 25s pra evitar service worker morrer
chrome.alarms.create("keepalive", { periodInMinutes: 0.42 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepalive") {
    pollOnce();
  }
  if (alarm.name === "active-wait") {
    // não usado ainda; placeholder pra wait ativo durante turno
  }
});

async function pollOnce() {
  try {
    const activeProviders = await findOpenProviders();
    const r = await fetch(`${PAINEL_URL}/api/relay-council/tasks`, {
      method: "GET",
      headers: {
        "X-Relay-Client": RELAY_CLIENT_ID,
        "X-Relay-Providers": activeProviders.join(","),
      },
      signal: AbortSignal.timeout(POLL_TIMEOUT_MS),
    });
    if (!r.ok) {
      console.warn("[relay] painel respondeu", r.status);
      connected = false;
      updateBadge("X");
      return;
    }
    const tasks = await r.json();
    connected = true;
    if (!tasks.length) {
      idleCount++;
      updateBadge("");
      return;
    }
    idleCount = 0;
    updateBadge(String(tasks.length));
    for (const task of tasks) {
      await executeTask(task);
    }
  } catch (e) {
    console.warn("[relay] poll falhou:", e.message);
    connected = false;
    updateBadge("X");
  }
}

async function findOpenProviders() {
  const tabs = await chrome.tabs.query({});
  const patterns = {
    deepseek: /^https:\/\/(www\.)?(chat\.)?deepseek\.com\//,
    gemini: /^https:\/\/gemini\.google\.com\//,
    zai: /^https:\/\/(www\.)?(chat\.)?z\.ai\//,
    chatgpt: /^https:\/\/chatgpt\.com\//,
    claude: /^https:\/\/claude\.ai\//,
    grok: /^https:\/\/(www\.)?grok\.com\//,
    qwen: /^https:\/\/(chat\.)?qwen\.ai\//,
    mistral: /^https:\/\/(lechat|chat)\.mistral\.ai\//,
    kimi: /^https:\/\/(www\.)?kimi\.(com|ai)\//,
  };
  return Object.entries(patterns)
    .filter(([provider, pattern]) => tabs.some((tab) =>
      pattern.test(tab.url || "") || (provider === "grok" && /^https:\/\/x\.com\//.test(tab.url || ""))
    ))
    .map(([provider]) => provider);
}

function updateBadge(text) {
  chrome.action.setBadgeText({ text });
  chrome.action.setBadgeBackgroundColor({ color: text === "X" ? "#ff5555" : "#4a9eff" });
}

async function executeTask(task) {
  const {
    id, site, text, action, chain_id, chain_index, chain_total,
    debate_id, debate_phase, debate_index, debate_total,
    evaluation_id, evaluation_index, evaluation_total, evaluation_started_ts,
  } = task;
  const taskMeta = {
    chain_id, chain_index, chain_total,
    debate_id, debate_phase, debate_index, debate_total,
    evaluation_id, evaluation_index, evaluation_total, evaluation_started_ts,
  };
  const report = (ok, response, error) => reportResult(id, task.lease, site, ok, response, error, taskMeta);
  let previousView = null;
  try {
    const tabId = await findTabForSite(site);
    if (!tabId) {
      await report(false, null, `aba do site "${site}" não encontrada`);
      return;
    }
    if (site === "kimi") {
      const busy = await detectKimiBusy(tabId);
      if (busy) {
        await report(false, null, `provider_busy: ${busy}`);
        return;
      }
    }
    // Alguns sites, especialmente o Gemini, suspendem a UI quando a aba não
    // está visível. Tornamos a aba alvo ativa apenas durante este turno.
    previousView = await activateTabForTask(tabId);
    // injeta content script se necessário
    await ensureContentScript(tabId, site);
    // verifica isReady
    const ready = await waitForReady(tabId, READY_TIMEOUT_MS, site);
    if (!ready.ok || !ready.value) {
      const debug = await sendSiteCmd(tabId, site, "debug");
      const info = debug.ok && debug.value ? debug.value : {};
      const found = info.found ? ` input=${!!info.found.inputTextarea} botão=${!!info.found.submitButton}` : "";
      const url = info.url ? ` url=${info.url}` : "";
      await report(false, null, `aba não está pronta (logado?)${url}${found}`);
      return;
    }
    if (site === "kimi") {
      const busy = await detectKimiBusy(tabId);
      if (busy) {
        await report(false, null, `provider_busy: ${busy}`);
        return;
      }
    }
    // Guarda a última resposta antes do turno para não aceitar resposta antiga.
    const baseline = await sendSiteCmd(tabId, site, "readLast");
    // escreve
    // F3: limpa a caixa antes de escrever. Sem isso, o texto é anexado a um rascunho
    // restaurado e o mesmo pedido pode ir mais de uma vez.
    const c = await sendSiteCmd(tabId, site, "clear");
    if (!c.ok) {
      await report(false, null, `composer_nao_limpo: ${c.error}`);
      return;
    }
    const w = await sendSiteCmd(tabId, site, "write", { text });
    if (!w.ok) {
      await report(false, null, `write falhou: ${w.error}`);
      return;
    }
    // submit
    const s = await sendSiteCmd(tabId, site, "submit");
    if (!s.ok) {
      await report(false, null, `submit falhou: ${s.error}`);
      return;
    }
    // espera resposta estabilizar
    const response = await waitForResponse(tabId, site, baseline.ok ? baseline.value : "");
    if (!response) {
      // F3: sem resposta lida, o envio já saiu. Não reenvia; informa para ativar a aba e conferir.
      await report(false, null, "sem_leitura: a aba estava ativa, mas a resposta não foi lida; não reenviado");
      return;
    }
    await report(true, response, null);
  } catch (e) {
    await report(false, null, String(e.message || e));
  } finally {
    await restorePreviousView(previousView);
  }
}

async function activateTabForTask(tabId) {
  const activeTabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  const current = activeTabs[0] || null;
  const target = await chrome.tabs.get(tabId);
  const previous = current ? { tabId: current.id, windowId: current.windowId } : null;

  if (target.windowId !== undefined) {
    await withTimeout(chrome.windows.update(target.windowId, { focused: true }), TAB_OPERATION_TIMEOUT_MS, "focar janela");
  }
  await withTimeout(chrome.tabs.update(tabId, { active: true }), TAB_OPERATION_TIMEOUT_MS, "ativar aba");
  // F3: aba restaurada depois de um reinício do navegador pode estar descarregada.
  // Nesse caso recarrega e espera a página completa antes de qualquer escrita ou leitura.
  await ensureTabLoaded(tabId, target.discarded);
  await new Promise((resolve) => setTimeout(resolve, TAB_ACTIVATION_SETTLE_MS));
  return previous;
}

async function ensureTabLoaded(tabId, wasDiscarded) {
  if (wasDiscarded) {
    await withTimeout(chrome.tabs.reload(tabId), TAB_OPERATION_TIMEOUT_MS, "recarregar aba descarregada");
  }
  const deadline = Date.now() + READY_TIMEOUT_MS;
  while (Date.now() < deadline) {
    const tab = await chrome.tabs.get(tabId);
    if (tab.status === "complete" && !tab.discarded) return;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error("aba não carregou a tempo (sem_carregamento)");
}

async function restorePreviousView(previous) {
  if (!previous || previous.tabId === undefined) return;
  try {
    await withTimeout(chrome.windows.update(previous.windowId, { focused: true }), TAB_OPERATION_TIMEOUT_MS, "restaurar janela");
    await withTimeout(chrome.tabs.update(previous.tabId, { active: true }), TAB_OPERATION_TIMEOUT_MS, "restaurar aba");
  } catch (e) {
    // A aba/janela anterior pode ter sido fechada pelo usuário durante o turno.
    console.debug("[relay] não foi possível restaurar a aba anterior:", e.message);
  }
}

function withTimeout(promise, timeoutMs, operation) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error(`${operation} excedeu ${timeoutMs}ms`)), timeoutMs)),
  ]);
}

async function waitForResponse(tabId, siteId, baseline = "") {
  const start = Date.now();
  let lastText = baseline || "";
  let stableSince = 0;
  let seenNewText = !baseline;
  while (Date.now() - start < TURN_MAX_WAIT_MS) {
    if (siteId === "kimi") {
      const busy = await detectKimiBusy(tabId);
      if (busy) throw new Error(`provider_busy: ${busy}`);
    }
    const r = await sendSiteCmd(tabId, siteId, "readLast");
    if (!r.ok && /^provider_busy:/.test(r.error || "")) {
      throw new Error(r.error);
    }
    if (r.ok && r.value) {
      const txt = r.value;
      if (baseline && txt !== baseline) seenNewText = true;
      if (txt === lastText) {
        if (!stableSince) stableSince = Date.now();
        if (seenNewText && Date.now() - stableSince > TURN_STABLE_MS) {
          return txt;
        }
      } else {
        lastText = txt;
        stableSince = 0;
      }
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
  return null;
}

async function detectKimiBusy(tabId) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        const text = (document.body?.innerText || "").toLowerCase();
        if (text.includes("too many people are chatting with kimi")) {
          return "Kimi informou excesso de usuários simultâneos";
        }
        return "";
      },
    });
    return results?.[0]?.result || "";
  } catch (_) {
    return "";
  }
}

async function waitForReady(tabId, timeoutMs, siteId) {
  const start = Date.now();
  let last = { ok: false, value: false };
  while (Date.now() - start < timeoutMs) {
    last = await sendSiteCmd(tabId, siteId, "isReady");
    if (last.ok && last.value) return last;
    await new Promise((r) => setTimeout(r, 1000));
  }
  return last;
}

async function findTabForSite(siteId) {
  const patterns = {
    deepseek: [/^https:\/\/(www\.)?(chat\.)?deepseek\.com\//],
    gemini: [/^https:\/\/gemini\.google\.com\//],
    zai: [/^https:\/\/(www\.)?(chat\.)?z\.ai\//],
    chatgpt: [/^https:\/\/chatgpt\.com\//],
    claude: [/^https:\/\/claude\.ai\//],
    grok: [/^https:\/\/(www\.)?grok\.com\//, /^https:\/\/x\.com\//],
    qwen: [/^https:\/\/(chat\.)?qwen\.ai\//],
    mistral: [/^https:\/\/(lechat|chat)\.mistral\.ai\//],
    kimi: [/^https:\/\/(www\.)?kimi\.(com|ai)\//],
  };
  const re = patterns[siteId];
  if (!re) return null;
  const tabs = await chrome.tabs.query({});
  for (const t of tabs) {
    if (!t.url) continue;
    if (re.some((r) => r.test(t.url))) {
      return t.id;
    }
  }
  console.warn(`[relay] aba de ${siteId} ausente; abertura automática bloqueada`);
  return null;
}

async function ensureContentScript(tabId, siteId) {
  const ping = await sendCmd(tabId, "isReady");
  if (ping.ok) return;
  try {
    const genericSites = new Set([
      "chatgpt", "claude", "grok", "qwen", "mistral", "kimi",
    ]);
    const files = ["content/_common.js"];
    if (genericSites.has(siteId)) files.push("content/_generic.js");
    files.push(`content/${siteId}.js`);
    await chrome.scripting.executeScript({
      target: { tabId },
      files,
    });
    await new Promise((r) => setTimeout(r, 800));
  } catch (e) {
    throw new Error(`falha ao injetar content script: ${e.message}`);
  }
}

function sendCmd(tabId, cmd, extra = {}) {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, { cmd, ...extra }, (resp) => {
      const err = chrome.runtime.lastError;
      if (err) resolve({ ok: false, error: err.message });
      else resolve(resp || { ok: false, error: "sem resposta" });
    });
  });
}

async function sendSiteCmd(tabId, siteId, cmd, extra = {}) {
  if (siteId !== "claude") return sendCmd(tabId, cmd, extra);
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      world: "MAIN",
      func: (action, text) => {
        const visible = (el) => el && el.getClientRects().length > 0 &&
          getComputedStyle(el).visibility !== "hidden" && getComputedStyle(el).display !== "none";
        const editor = [...document.querySelectorAll('div[contenteditable="true"], textarea')]
          .find((el) => visible(el) && !el.disabled && !el.readOnly);
        if (action === "isReady") return !!editor;
        if (action === "debug") {
          const button = [...document.querySelectorAll("button,[role=button]")]
            .find((el) => visible(el) && !el.disabled && /send|enviar/i.test(el.getAttribute("aria-label") || ""));
          return { siteId: "claude", url: location.href, isReady: !!editor,
            experimental: false, found: { assistantMessage: document.querySelectorAll('[data-testid="assistant-message"]').length,
              inputTextarea: !!editor, submitButton: !!button, generatingIndicator: !!document.querySelector('[data-is-streaming]') } };
        }
        if (action === "readLast") {
          const nodes = [...document.querySelectorAll('[data-testid="assistant-message"], [data-is-streaming]')]
            .filter(visible).map((el) => (el.innerText || el.textContent || "").trim()).filter(Boolean);
          if (!nodes.length) throw new Error("readLast: resposta não encontrada");
          return nodes[nodes.length - 1];
        }
        if (!editor) throw new Error("editor do Claude não encontrado");
        if (action === "write") {
          editor.focus();
          document.execCommand("selectAll", false);
          document.execCommand("delete", false);
          const selection = getSelection();
          const range = document.createRange();
          range.selectNodeContents(editor); range.collapse(false);
          selection?.removeAllRanges(); selection?.addRange(range);
          document.execCommand("insertText", false, text);
          if (!(editor.innerText || editor.textContent || "").trim()) {
            editor.dispatchEvent(new InputEvent("beforeinput", { inputType: "insertText", data: text, bubbles: true, cancelable: true }));
            editor.dispatchEvent(new InputEvent("input", { inputType: "insertText", data: text, bubbles: true }));
          }
          const actual = (editor.innerText || editor.textContent || "").trim();
          if (!actual.includes(text.trim())) throw new Error("texto não permaneceu no editor");
          return true;
        }
        if (action === "submit") {
          const button = [...document.querySelectorAll("button,[role=button]")]
            .find((el) => visible(el) && !el.disabled && /send|enviar/i.test(el.getAttribute("aria-label") || ""));
          if (button) { button.click(); return true; }
          editor.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true, cancelable: true }));
          return true;
        }
        throw new Error("comando Claude desconhecido: " + action);
      },
      args: [cmd, extra.text || ""],
    });
    return { ok: true, value: results?.[0]?.result };
  } catch (e) {
    return { ok: false, error: e.message || String(e) };
  }
}

async function reportResult(taskId, lease, site, ok, text, error, meta = {}) {
  const body = JSON.stringify({ task_id: taskId, lease, site, ok, text, error, ...meta });
  let lastError = null;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const response = await fetch(`${PAINEL_URL}/api/relay-council/result`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Relay-Client": RELAY_CLIENT_ID },
        body,
        signal: AbortSignal.timeout(POLL_TIMEOUT_MS),
      });
      if (!response.ok) throw new Error(`painel respondeu HTTP ${response.status}`);
      return;
    } catch (e) {
      lastError = e;
      if (attempt < 2) await new Promise((resolve) => setTimeout(resolve, 500 * (attempt + 1)));
    }
  }
  console.error("[relay] falha ao reportar resultado após 3 tentativas:", lastError?.message || lastError);
}

// popup pede status
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || !msg.cmd) return;
  if (msg.cmd === "status") {
    sendResponse({ ok: true, value: { connected, idleCount } });
    return;
  }
  if (msg.cmd === "poll-now") {
    pollOnce();
    sendResponse({ ok: true });
    return;
  }
});

// Diagnóstico local do protótipo; não expõe credenciais nem dados do chat.
globalThis.__relayPollOnce = pollOnce;
globalThis.__relayClaudeCommand = (tabId, cmd, text = "") =>
  sendSiteCmd(tabId, "claude", cmd, { text });

// primeiro poll na instalação
pollOnce();
