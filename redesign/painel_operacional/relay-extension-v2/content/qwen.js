(function () {
  window.__relayRegisterGeneric({
    siteId: "qwen",
    input: 'textarea, div[contenteditable="true"]',
    submit: 'button[aria-label*="Send"], button[aria-label*="Enviar"], button[type="submit"], [data-testid*="send"]',
    // O seletor genérico capturava o seletor de modo “Automático” do menu.
    assistant: '.qwen-chat-message-assistant .response-message-content, .qwen-chat-message-assistant .chat-response-message, [data-message-role="assistant"]',
  });
})();
