# Decreto: botões Abrir mostram a aba na hora (30/10/2026)

Motivo: ao clicar num modelo no painel, a aba era criada, mas não aparecia. A causa é que a aba nova ia para a janela do modo app, que não mostra abas. Só aparecia depois de alguém trazê-la para uma janela normal.

Mudança (só `relay-extension-v2/background.js`): a aba nova vai para uma janela normal do navegador. Se não houver nenhuma, a extensão abre uma janela normal com a aba.

Validado: a sintaxe da extensão passa, e os testes do Conselho passam.

Aplicação: depois da assinatura (`bash scripts/aprovar.sh foco-janela-normal-20261030 "aprovo: aba aberta numa janela normal"`). Depois de aplicar, recarregar a extensão no Chromium do sistema.
