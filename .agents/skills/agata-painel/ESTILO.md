# Estilo Agata: o último filtro de requinte

Decisão do Humano, 16/11/2026, 18:27: o estilo do documento `agata-conceito-16-11-2026.html` (seção "A Máquina agora" como exemplo) "é o último filtro de requinte a partir de agora".
Referência congelada: `referencia-agata-conceito-16-11-2026.html`, nesta pasta. Este arquivo descreve o que se mede nela; em dúvida, vale a referência.
Uso: toda interface e todo documento visual do Agata passa por este filtro ANTES de ser entregue. Não é tema opcional.

## Princípios (o que a referência faz)
1. Plano e calmo: superfícies lisas, borda de 1px, sem sombra, sem gradiente, sem brilho, sem imagem decorativa, sem animação de enfeite.
2. Um acento só: o verde-água marca título de seção, link e controle ativo. As outras cores só dizem estado.
3. Estado sempre com marca e palavra: pílula de contorno (aplicado, em sombra, proposta, sem decisão, não medido), nunca só cor.
4. Texto primeiro: resultado no topo, uma faixa de aviso com a conclusão, depois a evidência em tabela ou cartão, com a fonte na própria linha.
5. Respiro: muito espaço antes de cada seção, pouco dentro dos blocos; largura de leitura limitada.
6. Número é dado: algarismos tabulares, alinhados à direita em tabela; número grande só em mosaico de medida, com rótulo pequeno em cima e uma frase embaixo.
7. Nada repetido: cada informação aparece uma vez; a navegação é uma faixa fina e fixa.
8. Honestidade visível: "não medido" e "sem decisão" têm marca própria e ficam à vista.

## Medidas da referência
- Cores, tema escuro: fundo `#0f141b`; superfície `#18212c`; superfície 2 `#1f2b38`; linha `#324354`; texto `#e8edf3`; texto apagado `#a9b7c6`; acento `#7fd3c2`. Estado: ouro `#e2b873`, violeta `#a99be0`, vermelho `#ec8f86`, verde `#8fd69a`, azul `#8dbdf0`.
- Cores, tema claro: fundo `#f6f4ef`; superfície `#ffffff`; superfície 2 `#f0ede6`; linha `#d5d0c4`; texto `#1b232c`; apagado `#56626f`; acento `#146f62`. Estado: ouro `#8a5a0c`, violeta `#5a48a8`, vermelho `#a8392f`, verde `#256b33`, azul `#1f5c9c`.
- Tipo: fonte do sistema; corpo 16px com entrelinha 1,6; título principal fluido de 36 a 66px, entrelinha 1,04, espaçamento -0,02em; título de seção 24px na cor do acento; título de cartão 16px; texto de apoio 14px; fonte e legenda 12,5 a 13px; sobrelinha em maiúsculas 12,5px com espaçamento 0,13em; código em monoespaçada 13px sobre a superfície 2.
- Medida de leitura: parágrafo até 76 caracteres; página até 1080px, com 20px de margem lateral.
- Espaço: 60px antes de cada título de seção; 12px entre cartões; cartão com 16 a 18px por dentro; célula de tabela 10 por 12px.
- Cantos: 12px em cartão e tabela; 11px em caixa de organograma; 8px em botão; pílula em marca de estado; 4px em código.
- Borda: 1px na cor da linha. Autoridade: borda ouro. Ideia sem decisão: borda violeta tracejada.
- Tabela: dentro de moldura com borda e canto, rolagem horizontal dentro da moldura; cabeçalho pequeno, em maiúsculas, na cor do acento, sobre a superfície 2; linhas separadas por 1px.
- Mosaico de medida: rótulo 12,5px em maiúsculas, número 30px peso 700, uma frase de 14px.
- Botão: superfície 2, borda de 1px, 13px; ativo: fundo do acento com texto escuro.
- Foco: contorno de 2px na cor do acento.
- Navegação: faixa fixa no topo, fina, com fundo quase opaco e desfoque leve; links na cor apagada, acento ao passar.
- Responsivo: grades com `auto-fit` e mínimo de 230px; nenhuma rolagem horizontal da página; 16 a 20px de margem em celular.
- Impressão: fundo branco, navegação e controles ocultos.

## Checklist do filtro (aplicar antes de entregar)
- [ ] Sem sombra, gradiente, brilho ou imagem decorativa.
- [ ] Um acento; as demais cores só em marca de estado, com palavra.
- [ ] Toda cor vem de token; os dois temas definidos.
- [ ] Corpo em 16px; no máximo os tamanhos listados acima.
- [ ] Parágrafo com largura de leitura limitada.
- [ ] Cada informação uma vez; nenhum cartão que só remete a outro.
- [ ] Resultado antes da evidência; fonte junto do dado; "não medido" à vista.
- [ ] Tabela em moldura, com rolagem interna; números tabulares.
- [ ] Conferido em 360, 768, 1440 e 2560px, sem rolagem horizontal da página.
- [ ] Contraste de texto de pelo menos 4,5:1 nos dois temas.
- [ ] Sem emoji.
