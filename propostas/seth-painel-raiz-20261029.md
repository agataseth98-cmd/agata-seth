# Proposta: a primeira aba da Seth é o painel geral (29/10/2026)

Ao clicar em Seth, o Chromium do sistema abre primeiro o painel geral (`http://127.0.0.1:20146/`) e depois o LibreChat. Hoje abre primeiro o Conselho em Rede.

Muda uma linha em `redesign/systemd/seth`. O resto não muda.

Testado sem instalar: parar com `seth-parar`, subir com a versão corrigida; a primeira aba foi o painel, 9 provedores detectados e LibreChat respondendo HTTP 200.

Aplicação: depois da assinatura (`bash scripts/aprovar.sh seth-painel-raiz-20261029`), copio o atalho para `~/.local/bin`.
