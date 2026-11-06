# Atalho de voz no LibreChat (Ctrl+Alt+M)

**O que faz:** Ctrl+Alt+M liga e desliga o microfone do LibreChat, usando o mesmo botão da tela. Só age em `localhost:3080`. Não envia nada à rede.

**Por que não Ctrl+Q:** no Chrome e no Chromium, Ctrl+Q fecha o navegador inteiro, e a página não consegue interceptar esse atalho.

**Instalação (perfil "Sistema Agata"):**
1. Abra `chrome://extensions`.
2. Ative o "Modo do desenvolvedor".
3. Clique em "Carregar sem compactação" e escolha esta pasta (`extras/atalhos-librechat`).

**Ainda não validado:** o seletor do botão de microfone no DOM real do LibreChat. Se o atalho não responder, o ajuste é em `atalho.js`, na lista de seletores.
