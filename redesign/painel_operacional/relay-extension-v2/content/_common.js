// content/_common.js
// Interface estável que todo site implementa. Os seletores ficam em cada site.
// Não mexer aqui para adicionar site novo — só escrever content/<site>.js.

(function () {
  "use strict";

  // Cada site registra-se em window.__relay com esta forma:
  //
  //   window.__relay = {
  //     siteId: 'deepseek',
  //     isReady:   () => true|false,
  //     readLast:  () => Promise<string>,
  //     write:     (text) => Promise<void>,
  //     submit:    () => Promise<void>,
  //     onRespond: (cb) => void,
  //     debug:     () => Promise<DebugInfo>
  //   };
  //
  // O background só fala com essa interface. Não sabe qual é o site.

  const BRIDGE_TIMEOUT_MS = 8000;

  // Helper: espera até que predicate() retorne true, com timeout.
  window.__relayCommon = {
    isVisible: function (el) {
      if (!el) return false;
      const style = window.getComputedStyle(el);
      return el.getClientRects().length > 0 && style.visibility !== "hidden" && style.display !== "none";
    },

    // Alguns chats encapsulam o compositor em Shadow DOM aberto.
    queryAllDeep: function (selector, root = document) {
      const result = Array.from(root.querySelectorAll(selector));
      for (const host of root.querySelectorAll("*")) {
        if (host.shadowRoot) result.push(...this.queryAllDeep(selector, host.shadowRoot));
      }
      return result;
    },

    findEditable: function (preferredSelector = "") {
      const generic = 'textarea, input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="file"]), [contenteditable="true"], [role="textbox"], [aria-multiline="true"]';
      const selectors = preferredSelector ? `${preferredSelector}, ${generic}` : generic;
      return this.queryAllDeep(selectors).find((el) =>
        this.isVisible(el) && !el.disabled && !el.readOnly && el.getAttribute("aria-disabled") !== "true"
      ) || null;
    },

    findSendButton: function (preferredSelector = "", editable = null) {
      const selector = preferredSelector
        ? `${preferredSelector}, button, [role="button"], input[type="submit"], input[type="button"]`
        : 'button, [role="button"], input[type="submit"], input[type="button"]';
      const candidates = this.queryAllDeep(selector).filter((el) =>
        this.isVisible(el) && !el.disabled && el.getAttribute("aria-disabled") !== "true"
      );
      const editableParent = editable?.closest('form, [class*="composer"], [class*="input"], [class*="footer"]');
      const scored = candidates.map((el) => {
        const label = `${el.getAttribute("aria-label") || ""} ${el.getAttribute("title") || ""} ${el.getAttribute("data-testid") || ""} ${el.className || ""} ${el.innerText || ""}`.toLowerCase();
        let score = 0;
        if (/send|enviar|发送|submit|message/.test(label)) score += 10;
        if (/send|submit/.test(label)) score += 5;
        if (el.type === "submit") score += 4;
        if (/cancel|stop|model|project|menu|more|attach|upload/.test(label)) score -= 12;
        if (editableParent && (el.closest('form, [class*="composer"], [class*="input"], [class*="footer"]') === editableParent)) score += 6;
        return { el, score };
      }).sort((a, b) => b.score - a.score);
      return scored[0]?.score > 0 ? scored[0].el : null;
    },

    submitEditable: function (el) {
      if (!el) throw new Error("submit: editor não encontrado");
      const form = el.closest("form");
      if (form?.requestSubmit) {
        form.requestSubmit();
        return;
      }
      el.focus();
      for (const type of ["keydown", "keypress", "keyup"]) {
        el.dispatchEvent(new KeyboardEvent(type, { key: "Enter", code: "Enter", bubbles: true, cancelable: true }));
      }
    },

    waitFor: async function (predicate, { timeout = 30000, interval = 200 } = {}) {
      const start = Date.now();
      while (Date.now() - start < timeout) {
        try {
          if (predicate()) return true;
        } catch (_) {}
        await new Promise((r) => setTimeout(r, interval));
      }
      return false;
    },

    // Helper: simular digitação num contenteditable (Gemini usa).
    // Para <textarea> normal, basta setar .value e disparar input event.
    typeIntoContentEditable: async function (el, text) {
      el.click();
      el.focus();
      // Posicionar explicitamente a seleção evita que editores ProseMirror
      // recebam o insertText no alvo anterior.
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(el);
      range.collapse(false);
      selection?.removeAllRanges();
      selection?.addRange(range);
      // execCommand ainda é o caminho mais compatível com os listeners dos
      // editores React/Vue/ProseMirror que escutam input.
      el.dispatchEvent(new InputEvent("beforeinput", {
        inputType: "insertText", data: text, bubbles: true, cancelable: true,
      }));
      document.execCommand("insertText", false, text);
      el.dispatchEvent(new InputEvent("input", { bubbles: true, data: text, inputType: "insertText" }));
      // fallback se execCommand não funcionar ou deixar apenas o <br> vazio
      if (!(el.innerText || el.textContent || "").trim()) {
        el.textContent = text;
        el.dispatchEvent(new InputEvent("input", { bubbles: true, data: text }));
      }
    },

    typeIntoTextarea: function (el, text) {
      const prototype = el instanceof HTMLInputElement
        ? window.HTMLInputElement.prototype
        : window.HTMLTextAreaElement.prototype;
      const setter = Object.getOwnPropertyDescriptor(prototype, "value").set;
      setter.call(el, text);
      el.dispatchEvent(new Event("input", { bubbles: true }));
    },

    // Helper: achar último elemento que casa um seletor, em ordem de documento.
    lastMatching: function (selector) {
      const all = document.querySelectorAll(selector);
      return all.length ? all[all.length - 1] : null;
    },

    // Helper: log estruturado no console da aba (para debug).
    log: function (...args) {
      console.log("[relay:" + (window.__relay?.siteId || "?") + "]", ...args);
    },
  };

  // Escuta comandos do background. O background envia mensagens com
  // { cmd: 'readLast' | 'write' | 'submit' | 'isReady' | 'debug', text?: string }.
  // Responde com { ok: true, value?: ... } ou { ok: false, error: string }.
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (!msg || !msg.cmd) return;
    const relay = window.__relay;
    if (!relay) {
      sendResponse({ ok: false, error: "relay interface não registrada nesta aba" });
      return;
    }
    (async () => {
      try {
        switch (msg.cmd) {
          case "isReady":
            sendResponse({ ok: true, value: !!relay.isReady() });
            return;
          case "readLast":
            sendResponse({ ok: true, value: await relay.readLast() });
            return;
          case "clear": {
            // F3: esvazia a caixa de envio visível antes de escrever, e confere que ficou vazia.
            const campos = [...document.querySelectorAll('textarea, [contenteditable="true"], [role="textbox"]')]
              .filter((el) => el.getClientRects().length > 0 && !el.readOnly && !el.disabled);
            const campo = campos[campos.length - 1];
            if (!campo) {
              sendResponse({ ok: false, error: "caixa de envio não encontrada" });
              return;
            }
            if ("value" in campo && campo.tagName === "TEXTAREA") {
              const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set;
              setter.call(campo, "");
            } else {
              campo.textContent = "";
            }
            campo.dispatchEvent(new Event("input", { bubbles: true }));
            const restante = ("value" in campo ? campo.value : campo.textContent || "").trim();
            sendResponse(restante ? { ok: false, error: "caixa ainda com texto" } : { ok: true });
            return;
          }
          case "write":
            await relay.write(msg.text);
            sendResponse({ ok: true });
            return;
          case "submit":
            await relay.submit();
            sendResponse({ ok: true });
            return;
          case "debug":
            sendResponse({ ok: true, value: await relay.debug() });
            return;
          default:
            sendResponse({ ok: false, error: "cmd desconhecido: " + msg.cmd });
        }
      } catch (e) {
        sendResponse({ ok: false, error: String(e && e.message || e) });
      }
    })();
    return true; // manter canal aberto pro async
  });

  window.__relayCommon.log("content script carregado");
})();
