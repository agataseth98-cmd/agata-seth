# Decreto: botões Abrir numa janela já aberta (30/10/2026)

**Problema:** os botões "Abrir" abriam um segundo processo do Chromium com o mesmo perfil. Com o painel em modo programa, isso mostrava "Ocorreu um erro de perfil" e a página não aparecia.

**O que muda:** para os modelos e o LibreChat, o painel pede uma aba nova à janela do Chromium que já está aberta, pelo canal de depuração local do próprio Chromium (`127.0.0.1:9222`). O Obsidian continua sendo um programa separado. A lista de destinos continua fixa.

**Mudança:** só `redesign/painel_operacional/server.py`.

**Pré-requisito (configuração da máquina, não do repositório):** o Chromium do sistema precisa abrir com `--remote-debugging-port=9222`. Isso vai no arquivo de flags (`~/.config/chromium-flags.conf`), e vale a partir do próximo início do navegador.

**Segurança:** a porta só aceita conexões de `127.0.0.1` (esta máquina). Qualquer programa desta máquina poderia controlar o navegador por ela; por isso o Decreto fica restrito ao uso do sistema, e não deve ser aberto para a rede.

**Validado:** o servidor compila e os testes do painel passam.

**Aplicação:** depois da assinatura (`bash scripts/aprovar.sh abrir-janela-existente-20261030 "aprovo: abrir na janela existente"`), e depois que o navegador reiniciar com a flag.
