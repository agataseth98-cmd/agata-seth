// Adaptador experimental para chats cujo DOM muda com frequência.
// Cada wrapper fornece SITE_ID e alguns seletores específicos.
(function () {
  "use strict";
  const C = window.__relayCommon;
  window.__relayRegisterGeneric = function (cfg) {
    const SITE_ID = cfg.siteId;
    const selectors = {
      input: cfg.input || 'textarea, [contenteditable="true"], [role="textbox"], [aria-multiline="true"]',
      submit: cfg.submit || '',
      assistant: cfg.assistant || '[data-message-author-role="assistant"], [data-author="assistant"], [class*="assistant"], [class*="response"], [class*="message"]',
      generating: cfg.generating || '[aria-busy="true"], [class*="loading"], [class*="generat"], [class*="typing"]',
    };
    const blockedText = (cfg.blockedText || []).map((text) => String(text).toLowerCase());
    let lastWrittenText = "";

    function findInput() {
      return C.findEditable(selectors.input);
    }
    function findSubmit() {
      return C.findSendButton(selectors.submit, findInput());
    }
    function isReady() {
      return !!findInput();
    }
    async function readLast() {
      if (blockedText.length) {
        const visibleText = (document.body.innerText || "").toLowerCase();
        const blocked = blockedText.find((text) => visibleText.includes(text));
        if (blocked) throw new Error(`provider_busy: aviso do provedor detectado (${blocked})`);
      }
      const candidates = C.queryAllDeep(selectors.assistant).filter((el) => {
        if (!C.isVisible(el)) return false;
        if (el.matches('textarea, input, [contenteditable="true"], [role="textbox"]')) return false;
        if (el.querySelector('textarea, input, [contenteditable="true"], [role="textbox"]')) return false;
        return true;
      });
      const withText = candidates.map((el) => ({ el, text: (el.innerText || el.textContent || "").trim() }))
        .filter(({ text }) => text && text !== lastWrittenText);
      const item = withText[withText.length - 1];
      const el = item?.el;
      if (!el) throw new Error("readLast: resposta não encontrada");
      const text = item.text;
      if (!text) throw new Error("readLast: resposta vazia");
      return text;
    }
    async function write(text) {
      const el = findInput();
      if (!el) throw new Error("write: input não encontrado");
      lastWrittenText = text.trim();
      el.focus();
      if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
        C.typeIntoTextarea(el, text);
      } else {
        document.execCommand("selectAll", false);
        document.execCommand("delete", false);
        await C.typeIntoContentEditable(el, text);
      }
      await C.waitFor(() => {
        const current = findInput();
        return current && ((current.value || "") === text || (current.textContent || "") === text);
      }, { timeout: 3000, interval: 100 });
    }
    async function submit() {
      const button = findSubmit();
      if (button) {
        const input = findInput();
        button.click();
        const cleared = await C.waitFor(() => {
          const current = findInput();
          return !current || !(current.value || current.textContent || "").trim();
        }, { timeout: 1200, interval: 100 });
        if (cleared) return;
        // Alguns sites exibem o botão, mas não o conectam ao compositor atual.
        if (input) C.submitEditable(input);
        return;
      }
      const input = findInput();
      if (input) { C.submitEditable(input); return; }
      throw new Error("submit: botão e editor não encontrados");
    }
    function onRespond(cb) {
      let timer;
      const target = document.querySelector("main") || document.body;
      const observer = new MutationObserver(() => {
        clearTimeout(timer);
        timer = setTimeout(cb, 8000);
      });
      observer.observe(target, { childList: true, subtree: true, characterData: true });
    }
    async function debug() {
      return {
        siteId: SITE_ID, url: location.href, isReady: isReady(), experimental: true,
        found: {
          assistantMessage: C.queryAllDeep(selectors.assistant).length,
          inputTextarea: !!findInput(), submitButton: !!findSubmit(),
          generatingIndicator: !!C.queryAllDeep(selectors.generating).find(C.isVisible),
        },
      };
    }
    window.__relay = { siteId: SITE_ID, isReady, readLast, write, submit, onRespond, debug };
    C.log("adaptador experimental registrado");
  };
})();
