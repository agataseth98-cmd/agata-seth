// MV3 poller. Approved jobs run through Agata's official API executor.
// This extension never opens provider tabs or reads provider page content.
const PAINEL_URL = "http://127.0.0.1:20146";
const RELAY_CLIENT_ID = "agata-relay-v2";
const POLL_INTERVAL_MS = 2000;
const POLL_INTERVAL_IDLE_MS = 5000;
const POLL_TIMEOUT_MS = 5000;
const EXECUTE_TIMEOUT_MS = 185000;

let idleCount = 0;
let connected = false;
let polling = false;

chrome.alarms.create("keepalive", { periodInMinutes: 0.42 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepalive") pollOnce();
});

async function pollOnce() {
  if (polling) return;
  polling = true;
  try {
    const response = await fetch(`${PAINEL_URL}/api/relay-council/tasks`, {
      method: "GET",
      headers: { "X-Relay-Client": RELAY_CLIENT_ID },
      signal: AbortSignal.timeout(POLL_TIMEOUT_MS),
    });
    if (!response.ok) throw new Error(`painel HTTP ${response.status}`);
    const tasks = await response.json();
    connected = true;
    if (!tasks.length) {
      idleCount++;
      updateBadge("");
      return;
    }
    idleCount = 0;
    updateBadge(String(tasks.length));
    for (const task of tasks) await executeTask(task);
  } catch (error) {
    connected = false;
    updateBadge("X");
    console.warn("[relay] poll falhou:", error.message);
  } finally {
    polling = false;
  }
}

async function executeTask(task) {
  const response = await fetch(`${PAINEL_URL}/api/relay-council/execute`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Relay-Client": RELAY_CLIENT_ID,
    },
    body: JSON.stringify({ task_id: task.id, lease: task.lease }),
    signal: AbortSignal.timeout(EXECUTE_TIMEOUT_MS),
  });
  if (!response.ok) throw new Error(`executor API HTTP ${response.status}`);
  const result = await response.json();
  if (!result || result.duplicate) throw new Error("resultado de execução inválido");
}

function updateBadge(text) {
  chrome.action.setBadgeText({ text });
  chrome.action.setBadgeBackgroundColor({ color: text === "X" ? "#ff5555" : "#4a9eff" });
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || !message.cmd) return;
  if (message.cmd === "status") {
    sendResponse({ ok: true, value: { connected, idleCount } });
  } else if (message.cmd === "poll-now") {
    pollOnce();
    sendResponse({ ok: true });
  }
});

globalThis.__relayPollOnce = pollOnce;
pollOnce();
setInterval(pollOnce, POLL_INTERVAL_MS);
