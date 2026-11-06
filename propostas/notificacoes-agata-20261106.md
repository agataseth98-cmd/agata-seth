# Proposta `notificacoes-agata-20261106`: notificação por componente ao ligar e desligar o Agata

**Pedido do Humano (06/11/2026):** "deve ter notificação em todos". Ao clicar em Agata ou em Parar Agata, cada componente avisa o próprio estado no desktop, e não só o aviso geral de início e fim.

**O que muda:** `redesign/systemd/seth` (atalho Agata) e `redesign/systemd/seth-parar` (atalho Parar Agata) ganham, ao final, um aviso por serviço principal, e o estado do LibreChat no caso de Agata. A ordem de subida e parada e o boot não mudam.

**Medido:** sintaxe dos dois scripts (`bash -n`) e a função de notificação, testada com três unidades reais.

**Não medido:** o atalho completo, na próxima execução.

**Reversão:** remover o bloco `_notifica_unidades` e as linhas que o chamam.
