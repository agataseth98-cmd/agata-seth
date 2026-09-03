# AUDITORIA-01 — atrito de equipe + estado da arte (Fase 0)

DATA: 2026-09-01 ~21:54 -03 · por: sessão Claude (Claude Code, na Máquina)
HEAD (`redesign`): `bc567f6` · `main` intocado `4aa90bd` · tag `pre-redesign` `4aa90bd`

Pedido do Humano: auditar atrito entre a equipe de executores; alcançar o estado da
arte; orientar o Humano e a equipe. Autorização para prosseguir onde eu estiver seguro;
onde não, o sistema aconselha convocar os pares (Codex, Qwen Coder, `gpt-5.6-terra`).

## Decisão de fronteira

- **Feito solo (alta confiança, baseado em evidência do repo + verificação web):** a
  auditoria de atrito abaixo, o delta de estado da arte, e a lista de decisões do Humano.
- **Enviado ao Conselho (fronteira / conflito de interesse):** (a) verificação
  independente do P0-02 — escrito, testado e comitado por um único executor sem segundo
  par de olhos; (b) as propostas de doutrina de coordenação T2/T3, que são estruturais;
  (c) se o delta de estado da arte E1/E2 obriga a re-planejar as Fases 4 e 6 agora.
  Pacote de relay em `redesign/CONSELHO-01-relay.md`.
- **Motivo de não fazer tudo solo:** estou auditando uma equipe da qual faço parte. O
  padrão de atrito central (A1/A2) envolve meus próprios outputs. Auto-auditoria tem
  ponto cego. É o caso-livro de segundo par de olhos — e é a própria doutrina do Agata
  (Regra 8, Cadeia A→B→C, Conselho §4-5).

---

## Auditoria de atrito (ranqueada por gravidade)

### A1 — Nenhuma verificação independente sob o estado de exceção *(mais grave)*
A Cadeia A→B→C e o S7 (confirmação pós-push por sessão independente) estão suspensos no
branch `redesign`. `gpt-5.6-terra` auditou o **plano** (P0-00), não a **execução**. O
P0-02 (servidor MCP, 2 commits até `bc567f6`) foi escrito, testado e comitado por um
único executor. Velocidade subiu; verificação foi a zero. É decisão do Humano e está
autorizado — mas é o atrito central: a "equipe" hoje é **1 executor ativo + 2 fallbacks
dormentes + 1 auditor de plano**, não uma equipe que se checa.

### A2 — Gate de qualidade de plano veio depois da execução começar
P0-00 existiu porque `gpt-5.6-terra` achou 8 defeitos num plano que eu escrevi e que
outro executor já tinha começado a rodar (tag criada, manifesto gerado, restic
instalado). O schema de tarefa (CONTINUIDADE §8) não tem passo "plano revisado antes de
qualquer execução". Foi corrigido ad hoc; o processo, não.

### A3 — Posse sem trava
"Escreva `EM ANDAMENTO` em STATUS.md antes de executar" (reforçada 01/09 após retrabalho)
é uma linha de markdown, sem mecanismo. Dois executores podem escrever a mesma linha; os
fallbacks veem STATUS.md com latência de minutos-a-horas (GitHub + relay do Humano). A
coordenação depende de todos lerem a mesma versão ao mesmo tempo — o que não acontece.

### A4 — Âncora de coordenação do redesenho vive fora do git
O guia de reidratação (em chat) diz "todos convergem em 798d483". O HEAD já é `bc567f6` —
qualquer fallback segurando `798d483` está 2 commits atrás. O canon resolve isso com a
âncora-SHA em `PROMPT_CARREGAMENTO.md`; o redesenho não tem equivalente. STATUS.md é o
mais próximo, mas não é pinado em nenhum lugar externo nem regenerado por hook.

**Instância concreta (Conselho 01):** `gpt-5.6-terra` parou porque `git rev-parse
pre-redesign` deu `cea5aeb`, não `4aa90bd`. Não é divergência — `pre-redesign` é tag
**anotada**, e o SHA do objeto-tag (`cea5aeb`) não é o do commit (`4aa90bd`); desreferenciar
com `pre-redesign^{commit}`. O check de "4 refs batem" nos docs e nos relays não
especificava a desreferência. Corrigido em `CONTINUIDADE.md` §3 e `STATUS.md` (01/09).
Consequência para H2: um futuro `redesign/ANCORA.md` regenerado por hook tem que emitir
`pre-redesign^{commit}`, nunca o bare.

### A5 — Doc de handoff com deriva factual
STATUS.md dizia "nenhum executor tem shell local" — falso para esta sessão (Claude Code
na Máquina, tem shell). Corrigido hoje. CONTINUIDADE.md é escrito inteiro para executor
**sem** shell (Codex/Qwen); não há doc de "como o Claude-na-Máquina opera". Assimetria
não documentada = risco de um fallback assumir com o modelo mental errado.

### A6 — `main` não aponta para o redesenho
PROJETO.md e ONDE_ESTAMOS.md não mencionam que há um redesenho de 9 fases em curso.
Intencional (canon só muda na Fase 8), mas se o Humano perde o fio do chat, `main` não dá
pista. Tensão real entre a invariante "main congelado" e a continuidade.

### A7 — Atrito é doutrina e está sendo cumprido *(nota positiva)*
REGRAS "O Conselho" §4 ("fricção é esperada; conflito registrado é aprendizado") e a
Regra 8 (divergência das 3 passadas → Humano decide) foram exercidas de verdade em
(308)/(309). O mecanismo funciona **no canon**. Nunca foi exercido **entre executores**
(Claude vs Codex vs Qwen) — CONTINUIDADE §6 descreve, nada testou.

### A8 — Migração de chat como custo recorrente
O falso-positivo `[bio]` força troca de chat no meio de tarefa. O protocolo de
reidratação (guia + 4 refs conferidas) é a mitigação e funcionou hoje, mas é pesado, e
cada migração é risco de perda de estado + custo de recontextualização.

---

## Estado da arte — delta desde PESQUISA.md (mesma data, escrita de memória em parte)

### E1 — MCP virou stateless (spec 2026-07-28); FastMCP está em 4.0, não 3.x
PESQUISA descreve "FastMCP 3.0 (jan/2026, v3.2.4 abr/2026)". Instalado e atual:
**fastmcp 4.0.1**, alinhado à spec **MCP 2026-07-28** que tornou o protocolo **stateless**
("maior revisão desde o lançamento"). FastMCP 4.0 traz background tasks e interatividade
stateless de primeira classe. Servidores FastMCP 3 sobem sem mudança — o P0-02 sobe e
passa os testes de equivalência. O SDK Python v2 moveu os tipos para `mcp_types` (ainda
importável como `mcp.types`), campos em snake_case.
**Impacto:** Fase 6 (Obsidian MCP em `:27124/mcp/`) e Fase 4 (tools do grafo) foram
desenhadas contra o modelo antigo com sessão. PESQUISA precisa de um parágrafo sobre
stateless; o desenho das Fases 4/6 precisa de uma revisão leve.

### E2 — "Checkpoint não é execução durável" virou crítica mainstream
PESQUISA já mandava configurar o checkpointer do LangGraph como event-stream append-only.
O estado da arte 2026 (Temporal+LangGraph, Diagrid) é mais duro: o checkpointer do
LangGraph é **save point de snapshot**, não log de eventos; append-only real é via
reducers (`Annotated[list, operator.add]`), não nativo; para durabilidade de produção o
padrão emergente é uma **camada externa** (Temporal). A Fase 4 tem uma premissa não
validada aqui — vale um spike curto antes de comprometer o desenho do loop de governança.

### E3 — RLM: referência de implementação nova
Somar às fontes de PESQUISA: `alexzhang13/rlm` (lib do próprio autor do paper,
"plug-and-play, vários sandboxes") e `recursive-lm` no PyPI (fev/2026). Paper 2512.24601
revisado mai/2026. Não urgente (Fase 5 distante).

---

## Orientação para o Humano — decisões que só você toma

- **H1 — Verificação sob o estado de exceção: até onde afrouxar?**
  (a) manter como está — 1 executor, sem segundo par de olhos, você confia e assume;
  (b) exigir **S7 mínimo** — cada commit no `redesign` recebe confirmação pós-push de uma
  sessão independente (pode ser um fallback, barato: "o HEAD é X, os testes do Aceite
  passam?"); (c) reintroduzir só a Camada C (parecer PRONTO/NÃO) para tarefas que
  instalam software ou tocam runtime, resto solto.
  **Recomendo (b)** — leve, fecha o buraco central (A1).

- **H2 — Âncora de coordenação do redesenho (A4).** Autorizo criar
  `redesign/ANCORA.md` (ou campo no topo do STATUS.md) regenerado por hook a cada commit
  do branch: HEAD + timestamp + os 4 refs esperados. É o equivalente da âncora-SHA do
  canon, para os fallbacks não trabalharem em cima de estado velho.

- **H3 — `main` aponta para o redesenho (A6)?** Um pointer de 1 linha em
  ONDE_ESTAMOS.md ("redesenho de 9 fases em curso no branch `redesign` — ver
  `redesign/STATUS.md`") quebra "main só muda na Fase 8". Vale a exceção pela continuidade,
  ou o guia de reidratação em chat + este branch bastam?

- **H4 — Provocar a primeira divergência entre executores (A7).** REGRAS "O Conselho"
  §4: sem discordância real em 4 semanas, provocar uma sintética. Quer que P0-03 seja
  feita em paralelo de propósito — eu e um fallback — para exercitar posse e resolução,
  com você arbitrando?

---

## Orientação para a equipe

### Aplicável já (é doc, no branch `redesign`, reversível)

- **T1 — Passo "Verificação independente" no schema de tarefa.** Somar ao schema de
  CONTINUIDADE §8 um campo entre `Aceite` e `Rollback`: *"Verificação independente — quem
  confere, o quê, como (comando/condição), resultado."* Sem isso, `FEITO` é auto-declarado.
- **T4 — `redesign/CLAUDE-NA-MAQUINA.md`.** O análogo do CONTINUIDADE.md para o executor
  primário com shell: o que ele faz direto, o que ainda mostra sozinho (destrutivo,
  segredo), quando para e chama os pares. Fecha a assimetria A5.

### Proposta — pendente de parecer dos pares (estrutural)

- **T2 — Ordem fixa: plano auditado ANTES de execução.** Toda tarefa nova (P0-03 em
  diante) passa por parecer curto de um segundo modelo sobre o **plano** antes de qualquer
  passo. P0-00 mostrou o custo de não fazer (8 defeitos, retrabalho).
- **T3 — Posse com timestamp e TTL.** `EM ANDAMENTO` ganha `expira: <hora>` (ex. +2h).
  Fallback que vê posse expirada assume; posse viva com < TTL, não toca. Reduz dois
  executores em paralelo por leitura dessincronizada (A3).

---

## Resolução (01/09/2026 ~23:05 -03)

O Humano fixou: **ele decide; Claude aconselha + executa; sem menu de decisão quando não
há risco ao sistema — escolher pelo princípio-espelho e executar.** As pendências acima
foram então resolvidas assim (nenhuma expõe o sistema a risco):

| Item | Decisão | Onde entrou |
|---|---|---|
| **H1** verificação | **S7 mínimo, apoiado na espinha:** após cada commit, re-rodar o `Aceite` da tarefa a partir de estado limpo, anotar PASS/FALHA no `LOG.md`. Não depende de "outro modelo" — depende de re-derivar dos scripts. | `CONTINUIDADE.md` §7 · `ROADMAP.md` "Verificação e revisão" |
| **H2** âncora | `redesign/ANCORA.md` criado, atualizado à mão por quem commita (piso = commit anterior; referência viva = `git rev-parse origin/redesign`). **Promoção a hook = mudança de espinha → pende do Humano** (não fiz). | `redesign/ANCORA.md` · `CONTINUIDADE.md` §8 |
| **H3** pointer em `main` | **Não.** A invariante "main só muda na Fase 8" vence; o branch + `STATUS.md` + `ANCORA.md` bastam. | — (registrado aqui) |
| **H4** divergência sintética | **Retirada.** Fallbacks só afinados, não são co-executores — não há divergência entre executores a exercitar. Fricção-doutrina fica no canon (Regra 8), onde já funciona. | `STATUS.md` "Papéis" |
| **T1** campo de verificação | Aplicado ao schema. | `CONTINUIDADE.md` §8 |
| **T2** plano auditado antes | Aplicado com **tier de risco**: schema-check mecânico em toda tarefa; revisão por 2º par de olhos só p/ instala-pacote / runtime / escreve-fora / rede / credencial / garantia. | `CONTINUIDADE.md` §7 |
| **T3** posse | **Documentada dormente** (1 executor ativo, sem corrida). Forma "confirmada por commit remoto" escrita para o caso de um fallback ser ativado. | `CONTINUIDADE.md` §6 |
| **T4** doc do executor primário | Criado. | `redesign/CLAUDE-NA-MAQUINA.md` |
| **E1** MCP stateless | Anotado nas Fases 4/6; `fastmcp` pinado; ROADMAP "Correções pós-Fase 0". | `ROADMAP.md` · `mcp/requisitos.txt` |
| **E2** durabilidade | Vira tarefa-spike **P4-00** com o teste matar-e-retomar como aceite; Fase 4 não pré-compromete checkpointer nem Temporal. | `ROADMAP.md` (Fase 4 + "Correções pós-Fase 0") |

Conselho 01: `gpt-5.6-terra` respondeu (convergência, achados de P1 aplicados ao P0-02).
Codex/Qwen não são gate — se responderem, o parecer entra como afinação, não trava.

## Próximo

- **P0-03** — escrever os arquivos-tarefa das Fases 1 e 2 no schema (já com o campo T1).
- **Quando o HD montar:** P0-01 passos 3-4 + aceite de restore do P0-02 → Fase 0 fechada.
