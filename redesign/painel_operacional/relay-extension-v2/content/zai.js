// content/zai.js
// Seletores: MELHOR-ESFORÇO. DOM do chat.z.ai muda sem aviso.
// Rode no console: window.__relay.debug().then(console.log)

(function () {
  "use strict";
  const C = window.__relayCommon;

  const SELECTORS = {
    // Z.ai (GLM chat) costuma usar estrutura semelhante a ChatGPT.
    // Container de mensagem do assistente.
    assistantMessage:
      '[class*="response-content"], [data-role="assistant"], [data-message-role="assistant"], [class*="assistant-message"], [class*="message-"] [class*="markdown"]',

    // Input: tipicamente <textarea>.
    inputTextarea:
      'textarea#chat-input, textarea[placeholder*="Pergunte"], textarea[placeholder*="Ask"], textarea, div[contenteditable="true"]',

    // Botão de envio.
    submitButton:
      'button[type="submit"], [aria-label*="Send"], [aria-label*="Enviar"], [aria-label*="发送"], [title*="Send"], [title*="发送"], [data-testid*="send"], [data-testid*="submit"], [role="button"][class*="send"], [role="button"][class*="Send"]',

    generatingIndicator:
      '[class*="loading"], [class*="generating"], [class*="typing"], [class*="thinking"]',
  };

  const SITE_ID = "zai";

  function visible(el) {
    return !!el && el.offsetParent !== null && !el.disabled && el.getAttribute("aria-disabled") !== "true";
  }

  function findInput() {
    return C.findEditable(SELECTORS.inputTextarea);
  }

  function findSubmitButton() {
    return C.findSendButton(SELECTORS.submitButton, findInput());
  }

  function responseCandidates() {
    const explicit = Array.from(document.querySelectorAll(SELECTORS.assistantMessage))
      .filter(visible)
      .filter((el) => (el.innerText || "").trim());
    if (explicit.length) return explicit;

    // Fallback para mudanças de classe do Z.ai. Mensagens reais usam um
    // contêiner próprio; menus laterais não devem ser tratados como resposta.
    return Array.from(document.querySelectorAll('[class*="message-"], [data-message-id], [data-testid*="message"]'))
      .filter(visible)
      .filter((el) => {
        if (el.closest("nav, aside, [role=menu]")) return false;
        const text = (el.innerText || "").trim();
        if (!text || /More than coding|Full-Stack|Choose project|GLM-5\.3-Flash/.test(text)) return false;
        return true;
      });
  }

  function isReady() {
    return !!findInput();
  }

  async function readLast() {
    const el = responseCandidates().at(-1);
    if (!el) throw new Error("readLast: nenhum container de mensagem do assistente");
    const text = el.innerText.trim();
    if (!text) throw new Error("readLast: container encontrado mas vazio");
    return text;
  }

  async function write(text) {
    const el = findInput();
    if (!el) throw new Error("write: input não encontrado");
    if (el.tagName === "TEXTAREA") {
      C.typeIntoTextarea(el, text);
    } else {
      await C.typeIntoContentEditable(el, text);
    }
    await C.waitFor(() => {
      const current = findInput();
      return current && (current.value === text || current.textContent === text);
    }, { timeout: 3000, interval: 100 });
  }

  async function submit() {
    const btn = findSubmitButton();
    if (!btn) {
      const ta = findInput();
      if (ta) {
        C.submitEditable(ta);
        return;
      }
      throw new Error("submit: nem botão nem textarea encontrado");
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
        assistantMessage: responseCandidates().length,
        inputTextarea: !!findInput(),
        submitButton: !!findSubmitButton(),
        generatingIndicator: !!document.querySelector(SELECTORS.generatingIndicator),
      },
      candidates: {
        textareas: Array.from(document.querySelectorAll("textarea")).map((e) => ({
          id: e.id,
          classes: e.className.slice(0, 80),
          placeholder: e.placeholder,
          visible: e.offsetParent !== null,
        })),
        contentEditables: C.queryAllDeep(
          '[contenteditable="true"]'
        ).map((e) => ({
          tag: e.tagName,
          classes: e.className.slice(0, 80),
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
