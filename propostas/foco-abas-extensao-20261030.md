# Decreto: foco de abas pelo canal da extensão (30/10/2026)

**Problema:** os botões "Abrir" abriam um processo novo do navegador (erro de perfil), e depois passaram a usar uma porta de depuração local, que deu erro e não evitava abas duplicadas.

**O que muda:** ao clicar num modelo no painel, o pedido vai para uma fila própria de foco (separada da fila de envios). A extensão, que já está conectada às abas, lê essa fila:
- se a aba do modelo já existe, ela ativa essa aba (sem duplicar);
- se não existe, abre uma aba nova.

**Regra mantida:** a extensão só cria aba quando você clica num botão. Nenhuma tarefa de envio cria aba. O teste de contrato foi ajustado para garantir isso.

**Mudanças:**
- `server.py`: os botões passam a enfileirar o pedido de foco; nova rota de leitura da fila, só para a extensão (identificada pelo cabeçalho de cliente, como o Conselho).
- `relay-extension-v2/background.js`: lê a fila de foco a cada ciclo e ativa ou abre a aba.
- `test_conselho_rede.py`: o teste de contrato passa a permitir abrir aba só dentro da função de foco.

**Limite honesto:** a extensão lê a fila a cada ciclo, então o foco pode levar alguns segundos (o ciclo de leitura da extensão), e não é instantâneo. Esse é o custo de usar o mesmo canal do Conselho.

**Configuração da máquina (depois da aplicação):** tirar a porta de depuração (`--remote-debugging-port=9222`) do arquivo de flags, já que deixa de ser usada.

**Validado:** os testes do painel e do Conselho passam (incluindo o contrato da extensão), e o JavaScript da extensão passa na verificação de sintaxe.

**Aplicação:** depois da assinatura (`bash scripts/aprovar.sh foco-abas-extensao-20261030 "aprovo: foco de abas pela extensão"`). Depois de aplicar, recarregar a extensão no Chromium do sistema.
