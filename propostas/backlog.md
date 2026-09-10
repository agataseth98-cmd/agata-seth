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

## B — precisa da sua decisão de desenho (o executor propõe, você decide)

| # | Item | Estado | Bloqueio |
|---|---|---|---|
| B1 | **Reorg do `redesign/` — parte docs** — separar documento de projeto fechado do código vivo. | **FEITO — MEMÓRIAS (385).** 9 docs de planejamento → `extras/arquivo-redesign/`; `redesign/README.md` reescrito (dizia, errado, "gates suspensos"). Código não foi tocado. | — |
| B6 | **Reorg do `redesign/` — parte código** | **MOVIDO PRA HORIZONTE em 09/09/2026 (ordem do Humano: "deixe o B6 como futuro/horizonte").** Sai da lista B, que é o que se decide agora. Não é bloqueio de nada: o código funciona onde está, `redesign/` é um nome feio e não um defeito. Detalhe, plano e levantamento na seção **Horizonte** abaixo. |
| ~~B2~~ | ~~Rotação por família~~ | **FECHADO.** Parte 1 em (381) (`conselho_remoto.py` + `REGRAS.md` "O Conselho" item 3). Os 2 restantes decididos como **NÃO fazer** em (404): mecanizar A/B/C (é norma, B já rotaciona, C exige Máquina, A = proponente — cano a mais) e rename do arquivo de silo (zero efeito hoje). Critério de reabertura em (404). |
| ~~B7~~ | ~~P-8 não aprova DELEÇÃO de arquivo de comportamento~~ | **FECHADO — MEMÓRIAS (407).** `_p8_arquivo_aprovado` ganhou ramo pra deleção (`.diff` assinado com hunk de deleção total; `git apply` tem que fazer o arquivo sumir). 2ª opinião ministral-8b ((405)), matriz de teste 5/5. Os 2 arquivos inertes do `seth_local_shim` apagados no mesmo commit (bootstrap auto-aprovado). |
| B3 | **Duas costuras em REGRAS.md** | **FECHADO — MEMÓRIAS (384).** (b) já resolvido na linha 215 (nada a fazer). (a) alinhado: `lacuna: sem relógio` entra na lista de selos da Regra 1.1, com parecer do Conselho (ministral-8b). | — |
| B4 | **Roteamento por complexidade** (MEMÓRIAS (64)) | **APOSENTADO — MEMÓRIAS (383).** Premissa (Gemini principal) morta pela (140); sistema já roteia por adequação. Necessidade futura = proposta nova. | — |
| B5 | **Pendentes de (253)** — #3 carimbo de frescor nos 3 canônicos; #4 4ª pergunta na Checagem de prontidão. | **FECHADO — MEMÓRIAS (384).** #3 já feito pela (378) (bloco ANCORA-SHA). #4 não entra: `sync:` + âncora já cobrem frescor; prontidão é postura, não dados (parecer do Conselho concordou). | — |

## C — precisa de sessões de IA independentes (por desenho, não dá do executor local)

| # | Item | O que falta |
|---|---|---|
| ~~C1~~ | ~~Fechar TES-001~~ | **FECHADO — TES-001 APOSENTADO em (417)** (decisão do Humano: mera formalidade). Detecção de fabricação passa pra Cadeia de auditoria + P-7 + Catálogo. |
| ~~C2~~ | ~~Reabrir TES-002~~ | **FECHADO — TES-002 APOSENTADO em (417).** Substituído pelos sinais automáticos do `estado_para_eco.sh` (`sync: PASS` ao vivo, `HASH-ESTADO`, `IDADE-HIDRATACAO`, `SETH:ESTADO-ATUAL` por turno). |

## H — horizonte da Seth (anotados em (390)/(391), pra implementação futura)

| # | Item | Detalhe |
|---|---|---|
| ~~H1~~ | ~~Índice de diretório do Obsidian fica pra trás do disco~~ | **FECHADO — MEMÓRIAS (400).** Opção (c): `_DOUTRINA_FIXA` da Seth manda LER o arquivo pra confirmar entrada recente, nunca concluir da listagem. (a)/(b) descartadas como cano a mais. |
| ~~H2~~ | ~~Pós-filtro de hora inventada no `seth_gateway`~~ | **FECHADO — MEMÓRIAS (397).** Em vez de filtro de saída (reescrever o stream, arriscado — o mesmo código que travou em (393)), `estado_para_eco.sh` mede `HORA-MAQUINA:` real e a doutrina manda copiar essa linha, não inventar. Mesmo princípio da (394). |
| ~~H3~~ | ~~`seth_gateway._estado()` `timeout=15s`~~ | **FECHADO — MEMÓRIAS (394).** Timeout `15s→25s` + doutrina proíbe inventar `(0)` quando o estado não chega; sem a linha `TOPO-MEMÓRIAS:`, vira `lacuna (estado não injetado)`. |
| ~~H4~~ | ~~Sem tier LOCAL de último recurso na cadeia da Seth~~ | **FECHADO — MEMÓRIAS (403).** Premissa refutada ao vivo: o OmniRoute já roteia `ollama-local/<model>` direto pro `:11434`. Tier 5 (`ollama-local/qwen3.5-9b-64k:latest`) adicionado ao combo `seth-livre` por `PUT /api/combos`. O `seth_local_shim` de (402) foi retirado — era cano a mais. |
| ~~H5~~ | ~~`redesign/systemd/seth` não sincroniza `librechat.yaml` nem `canon-mcp.mjs`~~ | **FECHADO — MEMÓRIAS (401), mas só passou a valer de fato em 09/09/2026 ((420)).** O bloco de deploy foi escrito na fonte versionada e **nunca instalado** em `~/.local/bin/` — o atalho que você de fato executava era a versão de 05/09, sem deploy e sem `piper-tts`. Ou seja: por quatro dias este item constou como FECHADO descrevendo um mecanismo que não rodava. Achado na auditoria da (419), instalado e conferido na (420). **Lição, não só conserto:** "commitado na fonte" ≠ "instalado na Máquina" para tudo que vive fora do repo (`~/.local/bin/`, units systemd copiadas, `~/librechat/`). Fechar item de deploy exige conferir o disco, não o `git`. |

## Horizonte — bússola, não backlog

REGRAS, "Contenção de escopo": *"Só a fase atual e a seguinte têm gates e prazo. O
resto é bússola, não backlog."* O que está aqui não tem prazo e não bloqueia nada.
Modelo que propuser antecipar item daqui: negado por default, salvo ordem sua.

### B6 — reorg do `redesign/` para `runtime/`

**Por que existe:** "redesign" descreve um processo que terminou em 03/09/2026
(MEMÓRIAS (310)/(311)), não o que o código É. Mover melhora coerência e
rastreabilidade. **Não é defeito** — é nome feio. Nada depende disso.

**Estado: pronto pra executar, aguardando sessão dedicada.** O que já está feito:
- Nome decidido (`runtime/`) e 2ª opinião obtida (ministral-8b, posição condicional,
  emendas incorporadas) — plano em `propostas/plano-reorg-redesign-codigo.md`.
- Levantamento completo em 09/09/2026 ((419)), que **corrigiu dois erros do plano**:
  (a) `agata-consolidacao` é *symlink* pra `config/`, não cópia de `redesign/systemd/`,
  logo `config/agata-consolidacao.service` precisa entrar no `.diff` e o plano não o
  listava; (b) são **três** wrappers em `~/.local/bin/` (`agata`, `seth`, `seth-parar`),
  não um.
- Medido: 102 arquivos rastreados sob `redesign/`; ~2,17 GB de venvs com caminho
  absoluto embutido, que se **recriam**, não se movem; 12 units instaladas citando o
  caminho (11 cópias + 1 symlink).

**Duas decisões de desenho tomadas no levantamento, pra quem executar:**
- `LOG.md` (234 KB) e `redesign/propostas/` (13 arquivos) vão pra
  `extras/arquivo-redesign/`, **não** pra `runtime/` — são história do processo, não
  código que roda. Isso também evita reescrever 284 referências dentro de um log
  histórico, o que seria falsificar história (Regra 4).
- `fase7-hd/` mantém o nome na mudança, pra não ampliar o raio de explosão. Renomear
  fica como item separado, se algum dia valer.

**Pré-requisito já cumprido:** o P-8 enxergava rename? Não enxergava — furo fechado na
(419). Executar o B6 antes daquele conserto teria passado a maior mudança estrutural do
projeto por um controle cego justamente a renomeação.

## Fora da lista — feito ou obsoleto (pra não voltar)

- **D1** — `consolidacao.py --temas` não propaga pelo grafo — FECHADO em (375) (`_TEMAS_MANUAL`).
- **D2** — busca de refs do `consolidacao.py` puxa entrada não relacionada — FECHADO sem fix mecânico, confirmado pelo Humano 09/09/2026. Duas correções testadas contra dados reais em (395)/(396), as duas refutadas (título-only corta refs corretas; convergência das duas vias dá vazio). Revisão humana antes do canon já pega — pegou os dois casos de (395)/(396). Reabrir só se o volume de consolidação crescer a ponto da revisão manual não escalar.
- **H1** — índice de diretório do Obsidian atrás do disco — FECHADO em (400) (doutrina: LER o arquivo, não a listagem).
- **H2** — pós-filtro de hora inventada — FECHADO em (397). **H3** — timeout do `_estado()` — FECHADO em (394).
- `presence_penalty` na memória — consolidado e **aprovado em (382)**; par em `propostas/aplicadas/consolidacao-presence-penalty-2026-09-08.md`.
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
