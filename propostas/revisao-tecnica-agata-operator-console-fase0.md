# Revisão técnica — Operator Console fase 0

Status: revisão local do agente; não substitui revisão independente nem aprovação humana.

## Evidências examinadas

- `redesign/operator_console/index.html`
- `redesign/operator_console/app.js`
- `redesign/operator_console/style.css`
- `propostas/agata-operator-console-fase0-sdd.md`
- `propostas/agata-operator-console-fase0-20261030.diff`

## Achados

### 1. Alto — conteúdo do pacote é inserido como HTML

`capabilities.md` é convertido com `replaceAll` e atribuído a `innerHTML`; nomes de arquivos também são interpolados em HTML no painel de revisões. Um pacote local pode conter marcação ativa. Isso contradiz a intenção de exibir dados como conteúdo passivo.

Decisão sugerida: usar `textContent` e criar nós DOM, ou sanitizar com uma política explícita. O aceite deve incluir um caso com `<img onerror=...>` e verificar que não há execução.

### 2. Médio — a folha de estilo depende de rede

`style.css` importa fontes do Google Fonts. A interface pode continuar parcialmente funcional offline, mas isso contradiz o requisito de não depender funcionalmente de rede e torna a ausência de rede um comportamento não testado.

Decisão sugerida: remover o `@import` ou empacotar fontes locais; adicionar verificação que bloqueie dependências externas.

### 3. Médio — o critério “sem rede” não está demonstrado

Não há teste automatizado nem inspeção de runtime que prove ausência de chamadas de rede. A presença do `@import` já impede declarar o critério como atendido.

### 4. Baixo — declaração de integridade é deliberadamente limitada

O protótipo exibe “não medido”, o que é coerente com a spec, mas não verifica hashes. O texto de aceite deve manter essa limitação visível para evitar interpretação de integridade confirmada.

## Resultado

Não recomendar assinatura do diff atual. Recomendar revisão do escopo para corrigir a injeção de HTML e a dependência externa, seguida de nova revisão e novo hash do diff.
