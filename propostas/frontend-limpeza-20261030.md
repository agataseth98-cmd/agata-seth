# Decreto: limpeza visual do painel (30/10/2026)

**Por que:** a inspeção no navegador (feita numa cópia, com o inspetor de design da skill `design-taste-frontend`) apontou 4 falhas e vários avisos. O painel é uma ferramenta de operação, não um site de vitrine, então só corrigi o que melhora a leitura.

**O que muda (só `prototipo.css`):**
- Gradientes decorativos viram cor chapada (cartões, bloco de destaque, painel da Seth, item ativo do menu).
- Sombras de texto removidas (2).
- Rótulos pequenos em maiúsculas (10–11 px) passam a texto normal, com espaçamento menor (9 regras).
- Lista "Abrir" afastada da borda da tela.

**O que fica de propósito:**
- O gradiente do topo da página principal é um véu escuro sobre a foto do agente. A própria skill aceita essa exceção.
- Rótulo acima do título e fonte monoespaçada para códigos e identificadores continuam.

**Resultado da inspeção:** de 4 falhas para 1 (a exceção do véu sobre a foto). Os avisos restantes (contraste das bordas, altura de cartões, tamanho do título, distância da borda no celular) ficam para o próximo Decreto de hierarquia.

**Validado:** os 22 testes do painel passam.

**Aplicação:** depois da assinatura (`bash scripts/aprovar.sh frontend-limpeza-20261030 "aprovo: limpeza visual do painel"`). Depois de aplicar, reiniciar o painel.
