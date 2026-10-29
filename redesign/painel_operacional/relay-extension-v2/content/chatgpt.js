(function () {
  window.__relayRegisterGeneric({
    siteId: "chatgpt",
    input: 'textarea, [contenteditable="true"]',
    submit: 'button[data-testid*="send"], button[aria-label*="Send"], button[aria-label*="Enviar"]',
    // A versão atual do ChatGPT não expõe mais data-message-author-role.
    // Esses contêineres são específicos do renderer da resposta e não incluem
    // o balão do usuário.
    assistant: '[class*="DilResponseRoot"], [class*="MarkdownRoot"]',
  });
})();
