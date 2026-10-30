# Decreto: hierarquia visual do painel (30/10/2026)

**Por que:** a inspeção no navegador (cópia do painel, com o inspetor da skill `design-taste-frontend`) ainda apontava título grande demais, cartões de altura diferente, bordas de contraste muito alto e textos colados na borda do celular.

**O que muda (só `prototipo.css`):**
- Título principal menor: de até 78 px para até 56 px. O título de telas internas fica em 40 px no celular.
- Cartões de uma mesma linha passam a ter a mesma altura.
- Bordas dos painéis mais suaves (contraste de 8:1 para cerca de 3:1, com a mesma cor).
- No celular, a barra lateral e o conteúdo ganham 16 px de margem nas laterais.

**O que fica de propósito:**
- O véu escuro sobre a foto do agente no topo da página principal (exceção aceita pela skill).
- Rótulo acima do título e fonte monoespaçada para códigos e identificadores.

**Resultado da inspeção:** a falha de título grande foi resolvida; o aviso de borda caiu para o mesmo número de itens, mas com cor mais suave. Um cartão ainda tem uma faixa vazia (268 px), e isso é um efeito de igualar as alturas; fica para o próximo ajuste de conteúdo.

**Validado:** os 22 testes do painel passam.

**Aplicação:** depois da assinatura (`bash scripts/aprovar.sh frontend-hierarquia-20261030 "aprovo: hierarquia visual do painel"`). Depois de aplicar, reiniciar o painel.
