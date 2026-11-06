// Ctrl+Alt+M: clica no botão de microfone do LibreChat (liga e desliga a gravação).
// Ctrl+Q não serve: o Chrome/Chromium o usa para fechar o navegador inteiro.
// Não envia nada à rede; só aciona o botão que já existe na tela.
(function () {
  function achaBotaoMicrofone() {
    const seletores = [
      'button[aria-label*="microf" i]',
      'button[aria-label*="micro" i]',
      'button[title*="microf" i]',
      'button[title*="micro" i]',
      'button[aria-label*="record" i]',
      'button[aria-label*="grav" i]'
    ];
    for (const s of seletores) {
      const b = document.querySelector(s);
      if (b && !b.disabled) return b;
    }
    return null;
  }
  document.addEventListener("keydown", function (ev) {
    if (!ev.ctrlKey || !ev.altKey || ev.shiftKey || ev.metaKey) return;
    if ((ev.key || "").toLowerCase() !== "m") return;
    const b = achaBotaoMicrofone();
    if (!b) return;
    ev.preventDefault();
    ev.stopPropagation();
    b.click();
  }, true);
})();
