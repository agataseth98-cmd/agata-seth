// content/gemini.js
// Seletores: MELHOR-ESFORÇO. DOM do gemini.google.com muda sem aviso.
// Rode no console: window.__relay.debug().then(console.log)

(function () {
  "use strict";
  const C = window.__relayCommon;

  const SELECTORS = {
    // Gemini usa <model-response> custom element em conversas recentes.
    // Fallback: último .response-container .markdown.
    assistantMessage: "model-response, .response-container .markdown, .response-container",

    // Input é um contenteditable rich-text editor.
    inputTextarea: 'rich-textarea [contenteditable="true"], .ql-editor[contenteditable="true"], div[contenteditable="true"]',

    // Botão de envio. Gemini usa mat-icon com aria-label "Send message".
    submitButton: 'button[aria-label*="Send"], button[aria-label*="Enviar"], .send-button, [role="button"][aria-label*="Send"]',

    // Indicador de "gerando". Gemini mostra "Gemini is generating" ou um loading chip.
    generatingIndicator: 'mat-progress-bar, .loading-indicator, [aria-label*="generating"], [aria-label*="gerando"]',
  };

  const SITE_ID = "gemini";

  function findInput() {
    const direct = C.queryAllDeep(SELECTORS.inputTextarea).find((el) => C.isVisible(el) && !el.disabled && !el.readOnly);
    return direct || C.findEditable();
  }

  function findSubmitButton() {
    const direct = C.queryAllDeep(SELECTORS.submitButton).find((el) => C.isVisible(el) && !el.disabled);
    return direct || C.findSendButton("", findInput());
  }

  function isReady() {
    return !!findInput();
  }

  async function readLast() {
    const el = C.lastMatching(SELECTORS.assistantMessage);
    if (!el) throw new Error("readLast: nenhum container de mensagem do assistente");
    const text = el.innerText.trim();
    if (!text) throw new Error("readLast: container encontrado mas vazio");
    return text;
  }

  async function write(text) {
    const el = findInput();
    if (!el) throw new Error("write: input não encontrado");
    // Gemini: contenteditable. limpar antes de escrever.
    el.focus();
    document.execCommand("selectAll", false);
    document.execCommand("delete", false);
    await C.typeIntoContentEditable(el, text);
    await C.waitFor(() => {
      const current = findInput();
      return current && (current.textContent === text || current.value === text);
    }, { timeout: 3000, interval: 100 });
  }

  async function submit() {
    const btn = findSubmitButton();
    if (!btn) {
      const ed = findInput();
      if (ed) {
        C.submitEditable(ed);
        return;
      }
      throw new Error("submit: nem botão nem editor encontrado");
    }
    btn.click();
  }

  let pendingRespond = null;
  function onRespond(cb) {
    pendingRespond = cb;
    const obs = new MutationObserver(() => {
      clearTimeout(onRespond._t);
      onRespond._t = setTimeout(() => {
        if (pendingRespond === cb) {
          pendingRespond = null;
          cb();
        }
      }, 8000);
    });
    const target = document.querySelector("main") || document.body;
    obs.observe(target, { childList: true, subtree: true, characterData: true });
  }

  async function debug() {
    return {
      siteId: SITE_ID,
      url: location.href,
      isReady: isReady(),
      found: {
        assistantMessage: document.querySelectorAll(SELECTORS.assistantMessage).length,
        inputTextarea: !!document.querySelector(SELECTORS.inputTextarea),
        submitButton: !!document.querySelector(SELECTORS.submitButton),
        generatingIndicator: !!document.querySelector(SELECTORS.generatingIndicator),
      },
      candidates: {
        contentEditables: Array.from(
          document.querySelectorAll('[contenteditable="true"]')
        ).map((e) => ({
          tag: e.tagName,
          classes: e.className.slice(0, 80),
          parentTag: e.parentElement?.tagName,
          visible: e.offsetParent !== null,
        })),
        buttons: Array.from(document.querySelectorAll('button, [role="button"]'))
          .slice(-10)
          .map((e) => ({
            tag: e.tagName,
            classes: e.className.slice(0, 80),
            ariaLabel: e.getAttribute("aria-label"),
            text: (e.innerText || "").slice(0, 40),
            visible: e.offsetParent !== null,
          })),
      },
    };
  }

  window.__relay = { siteId: SITE_ID, isReady, readLast, write, submit, onRespond, debug };
  C.log("registrado");
})();
