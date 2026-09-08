# Backlog — itens em aberto (rascunho, SEM `APROVADO-`)

Substitui os documentos de planejamento da era Hermes, arquivados em
`extras/arquivo/` em MEMÓRIAS (372) (o Hermes foi removido em (312), então
`plano-execucao-backlog.md` / `roteiro-fase2.md` / os 2 dossiês de silo
descreviam mecanismos que não existem mais).

Não autoriza nada por si. Toda mudança estrutural ainda passa por
`propostas/<nome>.diff` + `APROVADO-<nome>` assinado (P-8, MEMÓRIAS (366)/(367)).
Varredura de MEMÓRIAS feita em (373): nada de novo executável apareceu; o que
segue é a lista completa.

---

## A — feito nesta sessão (fora da lista, só pra registro)

- Timer `agata-consolidacao` religado (marcador semeado em (371), 1º run não faz nada).
- Bundle `memoria/missoes` gravado no HD — P-6 sem AVISO.
- `presence_penalty` consolidado sob demanda — `propostas/consolidacao-presence-penalty-*.md`,
  aguarda sua decisão de virar entrada de MEMÓRIAS.

## B — precisa da sua decisão de desenho (o executor propõe, você decide)

| # | Item | Estado | Bloqueio |
|---|---|---|---|
| B1 | **Reorg do `redesign/`** — separar código vivo (grafo, router, mcp, systemd, librechat) de documento de projeto fechado. | Só flagueado. | Grande; toca caminhos quarentenados (imports, units systemd apontam pros caminhos antigos). Exige proposta cuidadosa + aprovação assinada. |
| B2 | **Rotação por família** (`propostas/dossie-rotacao-por-familia.md`, 07/09) | **Parte 1 FEITA — MEMÓRIAS (381).** 4 perguntas respondidas; `conselho_remoto.py` rotaciona por família + `REGRAS.md` "O Conselho" item 3. **Resta:** mecanizar Cadeia de auditoria A/B/C (hoje norma) + rename do arquivo de silo (sem efeito hoje). | — |
| B3 | **Duas costuras em REGRAS.md** (item O do backlog velho) — (a) selo de origem da hora com dois nomes em seções diferentes; (b) "Última entrada: (n)" pede afirmação seca mesmo sob `sync: não verificado`. | Identificado, não redigido. | REGRAS = "Mudança estrutural": **segunda opinião de outro modelo OU você assumir o risco por escrito**. Posso puxar a segunda opinião via `scripts/conselho_remoto.py`. |
| B4 | **Roteamento por complexidade** (MEMÓRIAS (64), aprovado, nunca implementado) | Premissa vencida. | O desenho original supunha Gemini como principal; a inversão de (140) (Seth local titular) mudou o sentido do roteamento. Precisa ser redesenhado antes de virar código — ou aposentado. |
| B5 | **Melhorias de catálogo pendentes de (253)** — 2 sugestões de "Ágata Opus" ao catálogo de falhas de REGRAS.md, retidas por exigirem segunda opinião. | Pendente desde 25/08. | Mesma regra do B3. |

## C — precisa de sessões de IA independentes (por desenho, não dá do executor local)

| # | Item | O que falta |
|---|---|---|
| C1 | **Fechar TES-001** | N sessões consecutivas limpas, hidratações genuinamente independentes (rodada 5 foi adversa, (360)). N ainda não definido — defina N. |
| C2 | **Reabrir TES-002** | Você entrega um nonce novo à mão a um modelo-alvo quando decidir. Silo `seth` já existe (Bloco 3.1). |

## D — bug achado em (373), pequeno

| # | Item | Detalhe |
|---|---|---|
| D1 | **`consolidacao.py --temas` (modo manual) não propaga pelo grafo** | `orientar` lê `s.get("_temas")`, mas o `Estado` (TypedDict) do LangGraph descarta a chave não declarada no `graph.invoke`. Chamada direta às funções funciona. Fix: global de módulo ou env var em `orientar`, setado por `run()` antes do invoke. Toca `redesign/grafo/flows/consolidacao.py` (quarentena) → proposta assinada. |

## Fora da lista — feito ou obsoleto (pra não voltar)

- Eco pós-carregar mecanizado — (308), `scripts/estado_para_eco.sh`.
- Geração de silo por modelo (`seth`) — Bloco 3.1, `.githooks/gerar-hidratacao.sh`.
- Harness A1 (asserção byte-a-byte) — obsoleto pós-Hermes ((312), "Estado dos bugs").
- Backlog de skills (`extras/BACKLOG-skills.md`) — era Hermes (`~/.hermes/config.yaml`).
- Detector de âncora velha como falso positivo — PROMPT_CARREGAMENTO.md reescrito (CHECAGEM DE DEFASAGEM, 3 degraus).
- Consolidação noturna — reformulada em (371).
- `ONDE_ESTAMOS.md` acima do teto — cortado em (372).
- Carimbo de "frescor" de (253) (a variante com contador numérico e sub-itens
  3-A/3-B) — **resolvido em (378)**: o parecer do GLM mandou eliminar o contador
  novo e reusar o SHA que já existe; feito, o bloco `ANCORA-SHA` agora vai também
  no preâmbulo de REGRAS/PROJETO/MEMÓRIAS. As 2 sugestões de catálogo de (253)
  (linha B5 acima) são item à parte e seguem em aberto.
