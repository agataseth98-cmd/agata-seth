// content/deepseek.js
// Seletores: MELHOR-ESFORÇO. DOM do chat.deepseek.com muda sem aviso.
// Antes de usar, rode no console da aba:
//   window.__relay.debug().then(console.log)
// e confirme que cada campo aponta pro elemento certo.
// Para ajustar, edite SELECTORS abaixo. Não mexa na lógica.

(function () {
  "use strict";
  const C = window.__relayCommon;

  // TODO: confirmar cada seletor com debug() antes da primeira execução.
  const SELECTORS = {
    // Container de mensagens do assistente (precisa do último).
    // DeepSeek costuma usar classes com hashing; usar atributo mais estável.
    assistantMessage: '[class*="message"] [class*="content"]',
    // Alternativa mais específica (descomente se a acima pegar ruído):
    // assistantMessage: 'div[class*="agent"] > div[class*="content"]',

    // Input. DeepSeek usa <textarea> com contenteditable wrapper.
    inputTextarea: 'textarea#chat-input, textarea[id*="input"], textarea[placeholder*="message"], textarea[placeholder*="消息"], div[contenteditable="true"], [role="textbox"]',
    // Botão de envio. Costuma ser <div> com role=button.
    submitButton: 'div[role="button"][class*="send"], button[type="submit"], [aria-label*="Send"], [aria-label*="发送"], [data-testid*="send"], [data-testid*="submit"]',

    // Indicador de "gerando" (some quando termina o stream).
    // Se não achar, o relay usa um fallback de timeout fixo (menos confiável).
    generatingIndicator: '[class*="loading"], [class*="generating"], [class*="typing"]',
  };

  const SITE_ID = "deepseek";

  function visible(el) {
    return !!el && el.offsetParent !== null && !el.disabled && el.getAttribute("aria-disabled") !== "true";
  }

  function findInput() {
    return C.findEditable(SELECTORS.inputTextarea);
  }

  function findSubmitButton() {
    return C.findSendButton(SELECTORS.submitButton, findInput());
  }

  function isReady() {
    return !!findInput();
  }

  async function readLast() {
    const el = C.lastMatching(SELECTORS.assistantMessage);
    if (!el) throw new Error("readLast: nenhum container de mensagem do assistente");
    // O texto pode estar em parágrafos; preservar quebras.
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
    // esperar o texto aparecer no DOM (framework pode re-renderizar)
    const ok = await C.waitFor(() => {
      const current = findInput();
      return current && (current.value === text || current.textContent === text);
    }, {
      timeout: 3000,
      interval: 100,
    });
    if (!ok) C.log("warn: texto pode não ter sido aceito pelo input");
  }

  async function submit() {
    const btn = findSubmitButton();
    if (!btn) {
      // fallback: Enter no textarea
      const ta = findInput();
      if (ta) {
        C.submitEditable(ta);
        return;
      }
      throw new Error("submit: nem botão nem textarea encontrado");
    }
    btn.click();
  }

  // Detectar fim da resposta. Estratégia: monitorar o indicador de "gerando"
  // sumir, com fallback para 8s de silêncio no MutationObserver.
  let pendingRespond = null;
  function onRespond(cb) {
    pendingRespond = cb;
    // Implementação simplificada: observa o container de mensagens e dispara
    // quando não há mudança por 8s. Substituir por detecção do indicador
    // real quando o seletor estiver confirmado.
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
        assistantMessage: C.queryAllDeep(SELECTORS.assistantMessage).length,
        inputTextarea: !!findInput(),
        submitButton: !!findSubmitButton(),
        generatingIndicator: !!document.querySelector(SELECTORS.generatingIndicator),
      },
      // lista de candidatos para ajudar a achar seletor certo
      candidates: {
        textareas: C.queryAllDeep("textarea").map((e) => ({
          id: e.id,
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
