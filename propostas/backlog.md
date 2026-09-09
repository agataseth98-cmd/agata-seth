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
| B6 | **Reorg do `redesign/` — parte código** — promover `grafo/`, `router/`, `librechat/`, `mcp/`, `igpu/`, `obsidian/`, `systemd/`, `fase7-hd/` pra fora de `redesign/` (nome permanente, ex. `runtime/` ou raiz). "redesign" descreve um processo terminado, não o que o código É — mover melhora coerência, rastreabilidade e compreensão do sistema. | Só registrado (ordem do Humano, 08/09/2026). | Migração grande: ~10 units systemd (fonte + instaladas, `.venv` no `ExecStart`), `perimetro.sh` (padrões P-8 + lista P-9), `scripts/gerar_obsidian.py` (lista hard-coded), `PROJETO.md` (18 refs), `config/modelos-gratuitos.md`, `redesign/librechat/canon-mcp.mjs` (dict `CANON` — já tem chave `ROADMAP` quebrada; `ACESSO-GRADUADO.md` vai junto). Plano faseado próprio + aprovação assinada por peça. |
| B2 | **Rotação por família** (`propostas/dossie-rotacao-por-familia.md`, 07/09) | **Parte 1 FEITA — MEMÓRIAS (381).** 4 perguntas respondidas; `conselho_remoto.py` rotaciona por família + `REGRAS.md` "O Conselho" item 3. **Resta:** mecanizar Cadeia de auditoria A/B/C (hoje norma) + rename do arquivo de silo (sem efeito hoje). | — |
| B7 | **P-8 não aprova DELEÇÃO de arquivo de comportamento** (achado em (403)) | `_p8_arquivo_aprovado` faz `git rev-parse ":$f"` p/ o blob staged; num arquivo deletado isso falha → SUSPEITO, sem caminho. Precisa de um ramo: staged como deleção + `.diff` assinado cujo hunk pro path é deleção total (`+++ /dev/null`) → aprovado. Vai junto: apagar de verdade `redesign/router/seth_local_shim.py` + `redesign/systemd/seth-local-shim.service` (hoje inertes no repo). Mudança em controle de segurança → 2ª opinião ou risco assumido por escrito (REGRAS "Mudança estrutural"). |
| B3 | **Duas costuras em REGRAS.md** | **FECHADO — MEMÓRIAS (384).** (b) já resolvido na linha 215 (nada a fazer). (a) alinhado: `lacuna: sem relógio` entra na lista de selos da Regra 1.1, com parecer do Conselho (ministral-8b). | — |
| B4 | **Roteamento por complexidade** (MEMÓRIAS (64)) | **APOSENTADO — MEMÓRIAS (383).** Premissa (Gemini principal) morta pela (140); sistema já roteia por adequação. Necessidade futura = proposta nova. | — |
| B5 | **Pendentes de (253)** — #3 carimbo de frescor nos 3 canônicos; #4 4ª pergunta na Checagem de prontidão. | **FECHADO — MEMÓRIAS (384).** #3 já feito pela (378) (bloco ANCORA-SHA). #4 não entra: `sync:` + âncora já cobrem frescor; prontidão é postura, não dados (parecer do Conselho concordou). | — |

## C — precisa de sessões de IA independentes (por desenho, não dá do executor local)

| # | Item | O que falta |
|---|---|---|
| C1 | **Fechar TES-001** | N sessões consecutivas limpas, hidratações genuinamente independentes (rodada 5 foi adversa, (360)). N ainda não definido — defina N. |
| C2 | **Reabrir TES-002** | Você entrega um nonce novo à mão a um modelo-alvo quando decidir. Silo `seth` já existe (Bloco 3.1). |

## H — horizonte da Seth (anotados em (390)/(391), pra implementação futura)

| # | Item | Detalhe |
|---|---|---|
| ~~H1~~ | ~~Índice de diretório do Obsidian fica pra trás do disco~~ | **FECHADO — MEMÓRIAS (400).** Opção (c): `_DOUTRINA_FIXA` da Seth manda LER o arquivo pra confirmar entrada recente, nunca concluir da listagem. (a)/(b) descartadas como cano a mais. |
| ~~H2~~ | ~~Pós-filtro de hora inventada no `seth_gateway`~~ | **FECHADO — MEMÓRIAS (397).** Em vez de filtro de saída (reescrever o stream, arriscado — o mesmo código que travou em (393)), `estado_para_eco.sh` mede `HORA-MAQUINA:` real e a doutrina manda copiar essa linha, não inventar. Mesmo princípio da (394). |
| ~~H3~~ | ~~`seth_gateway._estado()` `timeout=15s`~~ | **FECHADO — MEMÓRIAS (394).** Timeout `15s→25s` + doutrina proíbe inventar `(0)` quando o estado não chega; sem a linha `TOPO-MEMÓRIAS:`, vira `lacuna (estado não injetado)`. |
| ~~H4~~ | ~~Sem tier LOCAL de último recurso na cadeia da Seth~~ | **FECHADO — MEMÓRIAS (403).** Premissa refutada ao vivo: o OmniRoute já roteia `ollama-local/<model>` direto pro `:11434`. Tier 5 (`ollama-local/qwen3.5-9b-64k:latest`) adicionado ao combo `seth-livre` por `PUT /api/combos`. O `seth_local_shim` de (402) foi retirado — era cano a mais. |
| ~~H5~~ | ~~`redesign/systemd/seth` não sincroniza `librechat.yaml` nem `canon-mcp.mjs`~~ | **FECHADO — MEMÓRIAS (401).** Atalho `seth` ganha bloco de deploy (`cmp -s` → `cp` só o que difere → `docker restart librechat` só se mudou). P-9 também passa a vigiar `piper-tts.service` (lacuna aberta na (398)). |

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
