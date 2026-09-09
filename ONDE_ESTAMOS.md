# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 08/09/2026: `extras/arquivo/onde-estamos-ate-2026-09-08.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md`.

## Onde estamos — 09/09/2026

**Pilha da Seth subiu de novo** (estava desligada desde ontem à noite):
LibreChat + Mongo + Meilisearch + Kokoro + `seth-gateway` no ar, `:3080`
respondendo.

**Três buracos pequenos do cabeçalho da Seth fechados**, mesmo princípio
nos três — a Máquina mede o fato, o modelo só copia, nunca inventa:
- (394) timeout do pedido de estado subiu (15s→25s) e a doutrina proíbe
  `Última entrada: (0)` fabricado quando o estado não chega a tempo.
- (397) a Seth ganhou uma hora REAL pra copiar (`HORA-MAQUINA:`, medida
  pela Máquina) em vez de só a proibição de inventar — um glm já tinha
  furado essa proibição uma vez.

**Duas consolidações fechadas** (395, 396): TES-002 nonce (já resolvido em
(90), só faltava o sinalizador) e OmniRoute 504 (causa raiz fora do nosso
controle, mitigação aplicada, proteção do pool grátis é mecanismo à parte).
Nos dois rascunhos automáticos boa parte das referências não tinha nada a
ver com o tema — descartei as erradas e documentei por quê; **não dá pra
mecanizar esse filtro sem quebrar o consolidador** (testei duas formas,
as duas falharam contra dados reais) — a revisão seguinte manual, que já
pegou os dois casos de hoje.

## O que falta (lista completa, revista hoje — vários itens antigos aqui já
tinham fechado em sessões anteriores e a lista nunca foi limpa)

- **`redesign/` mistura código vivo com projeto fechado** — parte docs já
  reorganizada (385); a parte código é migração grande, só registrada,
  precisa de plano faseado.
- **Rotação por família** — parte 1 feita (381: rotaciona por família,
  não por modelo); falta mecanizar a cadeia de auditoria A/B/C.
- **TES-001 não fechado** — precisa de sessões de IA na nuvem
  genuinamente independentes; não dá pra fechar daqui.
- **TES-002** — reabrir com nonce novo depende de você entregar o nonce
  à mão a um modelo-alvo quando decidir.
- **Sem tier local de último recurso na cadeia da Seth** — o combo
  `seth-livre` cascateia por 4 provedores externos mas não alcança o
  modelo local se todos caírem no mesmo dia.
- **Deploy da Seth não sincroniza `librechat.yaml`/`canon-mcp.mjs`** — o
  atalho `seth` sobe os serviços, mas o `cp` desses dois arquivos pro
  `~/librechat/` ainda é manual.

## Fechado recentemente, pra não voltar

- Duas costuras em REGRAS.md (selo de hora, "última entrada" sob sync não
  verificado) — fechadas em (384).
- Âncora de frescor (carimbo de SHA no topo de REGRAS/PROJETO/MEMÓRIAS) —
  feita em (378).
- `presence_penalty` na memória — consolidado e aprovado em (382).
- Rotina de pesquisa de modelos gratuitos — rodando (377); implementação
  de achado continua manual e assinada, por desenho.
