const $ = (id) => document.getElementById(id);

async function refresh() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ cmd: "status" }, (resp) => {
      if (chrome.runtime.lastError || !resp || !resp.ok) {
        $("status").textContent = "erro";
        $("status").className = "status disconnected";
        return resolve();
      }
      const { connected, idleCount } = resp.value;
      $("status").textContent = connected
        ? `conectado · idle ${idleCount}`
        : "desconectado do Painel";
      $("status").className = "status " + (connected ? "connected" : "disconnected");
      resolve();
    });
  });
}

$("btnPoll").addEventListener("click", async () => {
  await new Promise((r) => {
    chrome.runtime.sendMessage({ cmd: "poll-now" }, r);
  });
  setTimeout(refresh, 500);
});

refresh();
setInterval(refresh, 2000);
