# LOG — redesenho do sistema local Agata (append-only)

Mais recente no fim. Cada entrada: data-hora `-03` · executor · o que foi feito · o que
falta · bloqueios · `HEAD` no fim.

---

## 2026-09-01 ~16:40 -03 · sessão Claude (Claude Code, na Máquina)

**Feito**
- Criado o branch `redesign` a partir de `main` @ `4aa90bd` (MEMÓRIAS (309)).
- Criado o scaffolding do workspace `redesign/`:
  - `README.md` — estado de exceção (gates de governança suspensos no branch por
    autorização escrita do Humano, 01/09/2026, risco assumido) + invariantes que
    continuam valendo (sem reescrita de história, sem force-push/reset em `main`,
    segredo nunca exposto, destrutivo mostrado sozinho, `main` só muda na Fase 8,
    Hermes/Ollama de produção intocados até a Fase 8).
  - `CONTINUIDADE.md` — briefing para o executor fallback (Codex / Qwen Coder):
    quem ele é (lê o GitHub, sem shell local, o Humano é mãos e olhos), o primeiro
    movimento obrigatório (sincronizar com o repo antes de propor), como entregar
    trabalho (blocos para o terminal fish, um por vez), regras de fish 4.8 vs bash,
    divisão entre executores (um de cada vez, linha de posse em STATUS.md), fim de
    sessão (STATUS + LOG + commit no branch).
  - `ROADMAP.md` — as 9 fases (0–8) com objetivo, entrega e critério de aceite,
    já com as 8 correções da pesquisa embutidas.
  - `PESQUISA.md` — estado da arte por ferramenta (set/2026) + as 8 correções
    (C1 MoE fora do Ollama, C2 iGPU é UHD não Arc, C3 grammar só no envelope,
    C4 FastMCP 3.0 traz OTel, C5 OTel sem dashboard, C6 restic não borg,
    C7 fallback shell = Goose, C8 LoRA exige `agata down`) + fontes.
  - `STATUS.md` — Fase 0 em montagem, quadro de posse vazio, próximos passos
    P0-01/P0-02/P0-03.
  - `LOG.md` — este arquivo.

**Não tocado**
- `main`, o canon (`REGRAS.md`/`PROJETO.md`/`MEMÓRIAS.md`), o Hermes, o Ollama, o
  `.hermes.md` de produção. Nada instalado, nada em `systemd`, nenhum modelo baixado
  ou removido.

**Contexto do handoff**
- O Humano conseguiu dois executores fallback de redundância: **Codex (OpenAI, plano
  gratuito)** e **Qwen Coder (plano gratuito)**, ambos com integração nativa ao GitHub
  `agataseth98-cmd/agata-seth` (`main` para leitura; `redesign` para trabalho). Eles
  assumem se a sessão Claude cair. O `CONTINUIDADE.md` é o ponto de entrada deles.

**Falta / próximo**
- P0-01: `git tag pre-redesign` + backup restic inicial + `models/manifest.json`.
- P0-02: servidor FastMCP 3.0 das ferramentas de Máquina.
- P0-03: arquivos-tarefa das Fases 1–2.
- Todos pedem o "vai" do Humano.

**HEAD (redesign) no fim:** ver `git log -1 --oneline redesign` após o commit desta entrada.

---

## 2026-09-01 ~17:10 -03 · sessão Claude (Claude Code, na Máquina)

**Contexto:** o Humano relayou (a) uma auditoria de `gpt-5.6-terra` (t=14) apontando 8
defeitos no plano da Fase 0 e propondo uma tarefa corretiva P0-00 antes de qualquer
execução, e (b) um relato de que um executor já tinha rodado P0-01 parcialmente (tag
criada, manifesto de 20 modelos gerado, `restic` v0.19.1 instalado, HD não montado) e
estava prestes a commitar.

**Verificado na Máquina:**
- Tag `pre-redesign` existe em `main` e no remoto, apontando `4aa90bd`. OK, é o ponto de
  congelamento correto — mantida.
- `models/manifest.json` estava **staged, não commitado**, na versão deficiente (só `id`
  do Ollama, 6 linhas de Modelfile, sem sha256 nem origem).
- `restic` v0.19.1 instalado. HD `AgataBkup01` não montado.
- Os 8 achados da auditoria: **todos confirmados** (incl. `consultar_indice.py --rebuild`
  escreve; `checar_citacao.sh` recebe caminho, não stdin; `git log ... redesign` ambíguo,
  que já tinha falhado nesta sessão).

**Feito (P0-00 — correção do plano, aplicada direto na Máquina):**
1. `.gitignore` — linhas explícitas para `redesign/**/.venv/`, `__pycache__`, `*.pyc`
   (`.venv/` já era coberto; reforço). Verificado com `git check-ignore`.
2. `models/manifest.json` — regenerado com `blob_sha256` (64 hex), `blob_path`, `origem`
   e Modelfile completo. 20 modelos, sha256 em 20/20. Substitui a versão staged deficiente.
3. `redesign/tasks/P0-02` — `commit_entry` removida (vai p/ Fase 4); `query_canon` passa a
   rejeitar qualquer argumento com `-` (barra `--rebuild`); `check_citation` ganha o
   adaptador de temp especificado com código; aceite atualizado; tools 6→5.
4. `redesign/tasks/P0-01` — gerador de manifesto reescrito no próprio arquivo-tarefa;
   rollbacks: parte não destrutiva separada, `rm -rf` isolado com `⚠️ DESTRUTIVO`.
5. `redesign/CONTINUIDADE.md` — `git log --oneline -12 redesign` → `... HEAD --`.
6. `redesign/README.md` — seção "Efeito automático esperado nos commits deste branch"
   (âncora SHA + derivados do post-commit).
7. `redesign/tasks/P0-00-correcao-do-plano.md` — criado, registrando os 8 achados e as
   correções, marcado FEITO.
8. `STATUS.md` — P0-00 FEITO; P0-01 parcial (tag ✅, manifesto ✅ corrigido, restic ✅,
   repo restic ⏸ HD); regra de coordenação reforçada (posse antes de executar).

**Não tocado:** `main`, canon, Hermes, Ollama, `.hermes.md` de produção.

**Coordenação:** houve auditoria e execução em paralelo sem linha de posse em `STATUS.md`.
A regra "posse antes de executar" foi reforçada no `STATUS.md` e no `CONTINUIDADE.md`.

**Migração de chat:** esta conversa Claude será encerrada e o trabalho continua num chat
novo (falso positivo recorrente de classificador `[bio]` no harness — conhecimento
registrado na memória do Claude Code). O chat novo retoma de `STATUS.md` + `LOG.md` +
`CONTINUIDADE.md` no branch `redesign`.

**Falta / próximo:** P0-01 passos 3-4 (repo restic, quando o HD montar); P0-02 (servidor
FastMCP, já corrigido); P0-03 (tarefas das Fases 1-2). Todos pedem o "vai" do Humano.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-01 ~21:55 -03 · sessão Claude (Claude Code, na Máquina — chat novo pós-migração)

**Contexto:** chat novo, reidratado do repositório (a conversa anterior foi encerrada por
falso positivo recorrente do classificador `[bio]` no harness). Reidratação conferida:
`git status` limpo; 4 refs batem — `main` 4aa90bd, `redesign` = `origin/redesign` = 798d483,
tag `pre-redesign` = 4aa90bd. `git diff main..redesign` em `PROMPT_CARREGAMENTO.md` = só o
bloco `ANCORA-SHA` (máquina, `pre-commit`), esperado, não revertido. Lidos, na ordem:
`README.md` → `STATUS.md` → `LOG.md` → `CONTINUIDADE.md` → `ROADMAP.md` + `PESQUISA.md` →
topo de `MEMÓRIAS.md` (canon em (309)).

**Direção do Humano:** "sem escolhas, em estado de exceção, você prevê meu comportamento e
apresenta só as opções que amadurecem o sistema. Prossiga." → executei a próxima tarefa
não bloqueada de maior valor de maturidade: **P0-02**. (P0-01 passos 3-4 seguem bloqueados
pelo HD; P0-03 é o próximo alvo.)

**Feito (P0-02 — servidor FastMCP das ferramentas de Máquina):**
- `redesign/mcp/.venv` — venv isolado, **fastmcp 4.0.1** (`fastmcp>=3.2` satisfeito; API
  `@mcp.tool` / `mcp.run()` estável de 3.x a 4.x). Gitignorado (`.gitignore:54`,
  `redesign/mcp/.venv/`), confirmado com `git check-ignore`.
- `redesign/mcp/servidor.py` — 5 tools read-only, cada uma wrapper fino de um script de
  `~/agata/scripts/` com `cwd=~/agata`, sem shell:
  - `git_sync` — `git fetch` + `git ls-remote origin refs/heads/main`; `{head, origin_head,
    em_dia}`. Testado: `head` 798d483 (redesign), `origin_head` 4aa90bd (main), `em_dia:false`.
  - `run_perimetro` — `bash scripts/perimetro.sh`; `{exit_code, resumo, linhas}`.
  - `check_citation` — adaptador de temp (`mkstemp` → script recebe caminho → `unlink`);
    `{exit_code, resumo, suspeitos}`.
  - `lint_header` — `verificar_cabecalho.py` por stdin; `{ok, motivo}`.
  - `query_canon` — `consultar_indice.py`; valida cada termo contra `^[\wÀ-ÿ][\wÀ-ÿ\- ]*$`,
    **rejeita** qualquer termo com `-` inicial (barra `--rebuild`); `{exit_code, trechos, erro}`.
  - Modo `--selftest <tool>` para rodar cada tool fora do protocolo MCP.
- `redesign/mcp/requisitos.txt`, `redesign/mcp/README.md` (com a tabela de equivalência).

**Equivalência MCP ↔ script cru (verificada):**
- `run_perimetro`: script exit 0 · `RESULTADO GERAL: OK — 10 OK · 0 SKIP · 1 PARCIAL · 0
  FALHA`; MCP idêntico (mesmo placar, mesmo exit).
- `lint_header`: cabeçalho válido → `OK`/exit 0 ↔ `{ok:true}`; cabeçalho sem `t=`/sem
  citação → 2 linhas `FALHA:`/exit 1 ↔ mesmas 2 linhas/`ok:false`/exit 1.
- `check_citation`: `(302 - ...)` real → `suspeitos=0`/exit 0 ↔ `suspeitos:[]`; `(99999 -
  ...)` inexistente → `SUSPEITO (P-7)`/exit 1 ↔ mesma linha em `suspeitos[]`/exit 1.
- `query_canon`: `["--rebuild","x"]` (e `["--","--rebuild"...]`) → erro de validação/exit 3,
  **índice não regenerado**; `["hidratação","âncora"]` → 8 seções de REGRAS + títulos/exit 0.
- `git status` limpo depois de tudo (fora as mudanças intencionais); `.venv` e `__pycache__`
  não aparecem (`!!` ignorado).

**Aceite P0-02:** servidor sobe e lista **5** tools (`mcp.list_tools()`); resultado por MCP
= resultado do script cru em `run_perimetro`/`check_citation`/`lint_header`; `query_canon`
rejeita `--rebuild` e aceita termos válidos sem regenerar índice; `.venv` fora do git. ✅
O outro item do critério da Fase 0 ("restore do restic num scratch reproduz config")
depende de P0-01 passos 3-4 (HD) — anotado em `STATUS.md` como "aceite de restore".

**Não tocado:** `main`, canon (`REGRAS.md`/`PROJETO.md`/`MEMÓRIAS.md`), Hermes, Ollama,
`.hermes.md` de produção, `scripts/` (só lidos e chamados, nunca editados), índice derivado.

**Nota de fato:** esta sessão Claude Code roda na Máquina e **tem shell** — executou os
blocos direto. Os fallbacks (Codex/Qwen) continuam sem shell. `STATUS.md` "Notas de
handoff" atualizado para refletir isso e para registrar a migração de chat como feita.

**Falta / próximo:** P0-01 passos 3-4 (HD); P0-03 (arquivos-tarefa das Fases 1-2);
aceite de restore do P0-02 (com HD). Pedem o "vai" do Humano.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-01 ~21:55 -03 · sessão Claude (Claude Code, na Máquina)

**Pedido do Humano:** auditar atrito entre a equipe de executores; alcançar o estado da
arte; orientar Humano e equipe. "Você está na fronteira; se seguro, prossiga; senão, o
sistema aconselha pedir ajuda dos pares, todos os disponíveis."

**Decisão de fronteira:** feito solo o que é observação/verificação (auditoria de atrito,
delta de estado da arte, lista de decisões do Humano). Enviado ao Conselho o que é
estrutural ou conflito de interesse (verificação independente do P0-02; parecer sobre as
propostas de doutrina T2/T3; peso do delta E1/E2 nas Fases 4/6) — estou auditando uma
equipe da qual faço parte, e o atrito central (A1/A2) envolve meus próprios outputs.

**Feito:**
- `redesign/AUDITORIA-01.md` — 8 pontos de atrito ranqueados:
  - A1 (mais grave): sob o estado de exceção não há verificação independente. `gpt-5.6-terra`
    auditou o *plano* (P0-00), não a *execução*. P0-02 comitado por 1 executor, sem 2º par
    de olhos. A "equipe" hoje = 1 ativo + 2 fallbacks dormentes + 1 auditor de plano.
  - A2: gate de qualidade de plano veio depois da execução começar (P0-00). Schema de
    tarefa não tem passo "plano revisado antes de executar".
  - A3: posse (`EM ANDAMENTO` em STATUS.md) é markdown sem trava; fallbacks veem com
    latência (GitHub + relay).
  - A4: âncora de coordenação do redesenho vive fora do git (guia em chat diz "798d483",
    HEAD já é bc567f6). Canon resolve com âncora-SHA; redesenho não tem equivalente.
  - A5: doc de handoff com deriva factual (STATUS.md dizia "nenhum executor tem shell";
    falso p/ esta sessão — corrigido hoje). CONTINUIDADE.md só cobre executor sem shell.
  - A6: `main` (PROJETO.md, ONDE_ESTAMOS.md) não aponta para o redesenho. Tensão real
    entre "main congelado até Fase 8" e continuidade.
  - A7 (positiva): a doutrina de atrito (Conselho §4, Regra 8) funciona no canon
    ((308)/(309)); nunca foi exercida entre executores.
  - A8: migração de chat por falso-positivo `[bio]` é custo recorrente.
- Delta de estado da arte (verificação web, PESQUISA.md é de hoje mas em parte escrita de
  memória):
  - E1: MCP virou **stateless** (spec 2026-07-28); FastMCP em **4.0.1** (PESQUISA diz
    3.x). Servidores FastMCP 3 sobem sem mudança — P0-02 passa. Fases 4/6 desenhadas
    contra o modelo com sessão precisam de revisão leve. SDK Python v2: tipos em
    `mcp_types` (alias `mcp.types`), snake_case.
  - E2: "checkpoint do LangGraph ≠ execução durável" virou crítica mainstream
    (Temporal+LangGraph, Diagrid). Fase 4 (checkpointer append-only "estilo dsh") tem
    premissa não validada — talvez precise de spike de durabilidade / camada externa.
  - E3: RLM — somar refs `alexzhang13/rlm` e `recursive-lm` (PyPI, fev/2026); paper
    2512.24601 revisado mai/2026. Não urgente.
- 4 decisões para o Humano (H1 verificação sob exceção — recomendo S7 mínimo por commit;
  H2 âncora de coordenação do redesenho; H3 pointer em `main`; H4 provocar 1ª divergência
  entre executores em P0-03). 4 mudanças de processo: T1 (campo "Verificação independente"
  no schema de tarefa) e T4 (`CLAUDE-NA-MAQUINA.md`) aplicáveis já; T2 (plano auditado
  antes de executar) e T3 (posse com TTL) pendentes de parecer dos pares.
- `redesign/CONSELHO-01-relay.md` — pacote de relay p/ Codex / Qwen Coder / `gpt-5.6-terra`
  (3 perguntas: verificação do P0-02; parecer T2/T3; peso do delta E1/E2). Cópias em
  `~/Área de trabalho/` (`CONSELHO-01-relay.md`, `agata-AUDITORIA-01.md`).

**Não tocado:** `main`, canon, Hermes, Ollama, `.hermes.md` de produção, `scripts/`,
índice derivado, `PESQUISA.md` (o delta está na AUDITORIA-01; PESQUISA em si não foi
editada — proposta é atualizar depois do parecer do Conselho).

**Falta / próximo:** Humano decide H1-H4; Conselho responde ao relay; então aplicar T1/T4
e (se aprovados) T2/T3; então P0-03.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-01 ~22:10 -03 · sessão Claude (Claude Code, na Máquina) — Conselho 01, 1ª resposta

**`gpt-5.6-terra` (via relay) parou** na conferência de refs: `git rev-parse pre-redesign`
deu `cea5aeb`, não `4aa90bd`. Verificado na Máquina: **não é divergência.** `pre-redesign`
é tag **anotada** (`git tag -a`, P0-01 passo 1); `git cat-file -t pre-redesign` = `tag`; o
objeto-tag `cea5aeb` desreferencia (`pre-redesign^{commit}`) para o commit `4aa90bd` =
MEMÓRIAS (309). Local e remoto (`git ls-remote --tags`) concordam em `cea5aeb`. Estado OK;
o check é que era impreciso (comparou objeto-tag com SHA de commit).

**Afinado (pedido do Humano "afine-o"):**
- `CONTINUIDADE.md` §3 PRIMEIRO MOVIMENTO — bloco de reidratação agora ecoa os 4 refs com
  `pre-redesign^{commit}` desreferenciado + nota de 3 linhas sobre tag anotada.
- `STATUS.md` — linha `BASE:` explicita objeto-tag `cea5aeb` → commit `4aa90bd`; nova linha
  ÂNCORA leve (piso conhecido = `16fecc5`, referência viva = `git rev-parse origin/redesign`).
- `CONSELHO-01-relay.md` — removido o HEAD hardcoded (estava `bc567f6`, já stale — A4 em
  ação); referência viva = topo de `STATUS.md`. Nota da tag anotada + do falso alarme.
- `AUDITORIA-01.md` A4 — registrada a instância concreta; consequência para H2 (um futuro
  `redesign/ANCORA.md` tem que emitir `pre-redesign^{commit}`, nunca o bare).

**Substância do Conselho (minha 1ª resposta, marcada como auto-revisão + voto, não a
verificação independente que A1 pede):** P1 — 5 tools confirmadas read-only quanto ao
estado do projeto (`--rebuild` inalcançável: leading-dash barrado + args em lista sem
shell; `perimetro.sh`/`verificar_cabecalho.py` sem escrita; `commit_entry` ausente);
4 defeitos de robustez achados (sem timeout no `_run`; regex de `query_canon` mais frouxo
do que parece — defesa real é `shell=False`; fd leak no `check_citation` se `os.write`
falha; sem erro estruturado p/ script ausente). P2 — T2 sim com tier de risco
(instala/runtime/escreve-fora = bloqueante; só-doc = leve e assíncrono); T3 — TTL não
resolve a raiz, propor posse-por-commit (`redesign/posse/<tarefa>.claim`, push atômico
desempata). P3 — E1 anotar não re-desenhar (+ pin `fastmcp==4.0.1`); E2 spike pequeno
obrigatório antes do desenho da Fase 4 (teste matar-e-retomar sem commit duplicado), sem
pré-comprometer Temporal.

**Falta:** verificação de P1 por par que não seja o autor; respostas de Codex/Qwen a
P2/P3; Humano decide H1-H4.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-01 ~22:35 -03 · sessão Claude (Claude Code, na Máquina) — Conselho 01, parecer do gpt-5.6-terra aplicado

**`gpt-5.6-terra` respondeu P1/P2/P3** (via relay; a verificação web dele voltou HTTP 401,
então P3 dele se apoia na evidência do branch, não em confirmação externa nova).
**Convergência forte** com a minha 1ª resposta — sem divergência a subir ao Humano. Ele
confirmou: 5 tools não escrevem workspace/canon, `commit_entry` ausente, `--rebuild`
inalcançável (subprocess sem shell + args em lista; `"x --rebuild"` vira um argumento de
texto), `check_citation` resistente a injeção. Achados novos aplicados agora em
`servidor.py` + `mcp/README.md` (mudança só no branch, doc + robustez, reversível por
`git checkout -- redesign/mcp`):

1. **Frase errada corrigida** (era erro factual meu): a doc dizia `query_canon` "nunca
   toca `memoria/missoes/`" — o script **lê** o índice derivado lá. Agora: "lê, não
   escreve; índice ausente/corrompido continua sendo erro de leitura, nunca reconstrução".
2. **`_run` ganhou timeout** (124) e trata binário ausente (127) sem levantar exceção —
   erro vai em campo estruturado. Fecha o "sem erro estruturado p/ script ausente".
3. **`check_citation`**: `os.write`+`os.close` → `os.fdopen(fd,'w')` num `with` — fd
   sempre fechado mesmo em erro de escrita; `unlink` no `finally` com `try/except`.
4. **`git_sync` re-desenhado** — a versão antiga comparava `HEAD` (branch atual) com
   `origin/main`, o que na `redesign` mede "outra coisa" (terra). Agora reporta **dois
   eixos separados**: `canon_local/canon_remote/canon_em_dia` (`main` vs `origin/main` —
   alimenta o `sync:`) e `branch_*` (branch atual vs `@{upstream}`), mais
   `fetch_exit_code/fetch_error` (não mascara erro de transporte como `em_dia:false`).
5. **`mcp/README.md`**: invariante "read-only" reescrita (= sem escrita em
   workspace/canon, não zero escrita no filesystem — `git fetch` toca `.git/`, o temp do
   `check_citation` é criado e apagado); tabela de equivalência + 6 casos de borda novos
   (git_sync na redesign, erro de rede, termo composto, índice ausente, script ausente
   →127, subprocess travado →124).

**Equivalência re-rodada, MCP ↔ script cru, tudo bate:** `run_perimetro` (exit 0, mesmo
placar 10/0/1/0); `lint_header` 3 casos (válido 0/0, `Nonce:` incompleto 1/1, vazio 1/1);
`check_citation` real 0/0 e inexistente 1/1 (mesmo `__RESUMO_P7__`). Servidor sobe e lista
as 5 tools. `git status` só com `servidor.py` + `README.md` — índice **não** regenerado.

**P2 — convergência terra + Claude (aguarda Codex/Qwen ou "vai" do Humano p/ virar norma):**
- T2: verificação prévia **com tier de risco** — checagem mecânica curta de schema em toda
  tarefa; revisão independente por 2º executor só quando instala pacote / toca runtime /
  escreve fora do repo / mexe em rede / cria credencial / muda garantia. 3 resultados:
  pronto / ajustes exigidos / lacuna. Separa legibilidade barata de revisão de risco.
- T3: TTL sozinho não resolve corrida por cópia atrasada. Mecanismo mínimo (convergente
  com o "posse-por-commit" que propus): grava posse com hora+expiração → commit+push →
  **só age após confirmar que o remoto aponta para o commit que contém a posse** → posse
  expirada torna a tarefa elegível mas não autoriza tomada automática (novo executor
  publica a nova posse antes) → fechamento também commitado+enviado antes de outro pegar
  trabalho. TTL vira recuperação de abandono; a trava de concorrência é a confirmação do
  commit remoto.

**P3 — convergência:**
- E1: **não re-desenhar agora.** PESQUISA.md/ROADMAP.md desatualizados (P0-02 usa fastmcp
  4.0.1, PESQUISA diz 3.x). Tratar o transporte MCP como stateless; estado de
  execução/autorização/continuidade mora no grafo / storage / cliente, nunca em sessão
  MCP implícita. Entra como correção de premissa + critério de aceite nas tarefas das
  Fases 4 e 6. Some: pin `fastmcp==4.0.1` no `requisitos.txt` (feito? — ver próximo).
- E2: premissa de durabilidade **não validada**; spike explícito antes de comprometer a
  arquitetura da Fase 4. Aceite do spike: iniciar execução, interromper em pontos
  definidos, retomar e provar (a) nenhum commit/escrita duplicado, (b) efeito externo
  idempotente ou registrado como pendente, (c) estado retomado explica o último efeito
  confirmado, (d) log append-only reconstrói a decisão. O resultado decide entre
  checkpointer + camada externa mínima ou camada de durabilidade dedicada — não
  pré-comprometer Temporal.

**Falta:** respostas de Codex e Qwen Coder (P1 verificação + P2/P3); Humano decide H1-H4 e
se T2/T3 (convergência de 2 modelos) já viram norma ou esperam os outros 2; aplicar o pin
do `fastmcp` + as linhas de premissa MCP-stateless nas Fases 4/6 do ROADMAP; P0-03.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-01 ~23:08 -03 · sessão Claude (Claude Code, na Máquina) — papéis + AUDITORIA-01 resolvida

**Humano fixou 2 coisas nesta rodada:**
1. "Quem decide sou eu, você é meu conselheiro e primeiro executor; os fallbacks devem
   estar apenas afinados, nada mais." → seção "Papéis" no `STATUS.md` (commit anterior
   `e4398e2`); `CONTINUIDADE.md` §6 reescrita.
2. "Não me faça mais essa pergunta [menu de decisão] a menos que o sistema esteja exposto
   a risco; caso não, opte pelo que segue mais próximo o espelho do sistema." → salvo na
   memória do Claude Code (`feedback_agata_decide_por_espelho`). Daqui pra frente:
   decisão de doutrina/processo/plano sem risco = escolho pelo princípio-espelho (topo do
   ROADMAP) e executo, registrando o porquê; pergunto só em risco (destrutivo, segredo,
   `main`/canon/Hermes/Ollama, quebrar a espinha).

**AUDITORIA-01 resolvida assim (nenhum item expõe o sistema a risco):**
- **H1** — S7 mínimo apoiado na espinha: após cada commit, re-rodar o `Aceite` da tarefa
  de estado limpo, PASS/FALHA no LOG. Não depende de "outro modelo".
- **H2** — `redesign/ANCORA.md` criado, atualizado à mão (piso = commit anterior;
  referência viva = `git rev-parse origin/redesign`). **Promoção a hook NÃO feita** —
  mexer na cadeia de hooks de todo commit é mudança de espinha, pende do Humano.
- **H3** — não. A invariante "main só muda na Fase 8" vence; branch + STATUS + ANCORA bastam.
- **H4** — retirada. Fallbacks só afinados ⇒ sem divergência entre executores a exercitar.
- **T1** — campo "Verificação independente" no schema de tarefa (`CONTINUIDADE.md` §8).
- **T2** — plano auditado antes de executar, **tier de risco**: schema-check mecânico em
  toda tarefa; revisão por 2º par de olhos só p/ instala-pacote / runtime / escreve-fora /
  rede / credencial / garantia (`CONTINUIDADE.md` §7).
- **T3** — documentada dormente (1 executor ativo). Forma "confirmada por commit remoto"
  escrita para o caso de um fallback ser ativado (`CONTINUIDADE.md` §6).
- **T4** — `redesign/CLAUDE-NA-MAQUINA.md` criado (executor primário com shell: o que faz
  direto, o que mostra sozinho, quando para, atribuição de commit).
- **E1** — `ROADMAP.md`: seção "Correções pós-Fase 0"; premissa MCP-stateless nas Fases
  4/6; célula da Fase 0 corrigida (FastMCP 4.0.1, 5 tools, `commit_entry` → Fase 4);
  `mcp/requisitos.txt` já pinado `fastmcp==4.0.1`.
- **E2** — `ROADMAP.md`: decisão do checkpointer da Fase 4 vira **tarefa-spike P4-00**
  (aceite: matar processo / retomar / provar sem commit duplicado + efeito externo
  idempotente-ou-pendente + estado explica último efeito + log reconstrói a decisão);
  Fase 4 não pré-compromete Temporal.

**Arquivos tocados:** `CONTINUIDADE.md`, `ROADMAP.md`, `STATUS.md`, `AUDITORIA-01.md`
(§Resolução), `LOG.md`; novos `redesign/ANCORA.md`, `redesign/CLAUDE-NA-MAQUINA.md`.
**Não tocado:** `main`, canon, Hermes, Ollama, `scripts/`, hooks, `servidor.py`.

**Verificação:** doc-only, sem `Aceite` executável; `bash scripts/perimetro.sh` roda no
pre-commit (tem que sair verde).

**Falta / próximo:** **P0-03** (arquivos-tarefa das Fases 1-2) — começa a seguir. HD para
P0-01 passos 3-4 + aceite de restore do P0-02.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-01 ~23:30 -03 · sessão Claude (Claude Code, na Máquina) — P0-03 (arquivos-tarefa Fases 1 e 2)

**Feito:** 9 arquivos-tarefa em `redesign/tasks/`, no schema (com o campo "Verificação
independente" da T1). São **planos para execução futura** (cada fase pega o "vai" do
Humano e passa pela revisão de plano com tier de risco da T2 antes de rodar).

**Fase 1 — Router / OmniRoute** (fecha o aceite: um pedido roteia · fallback sob falha ·
custo logado · segredo bloqueado antes de sair · aposenta a rede do `conselho_remoto.py`):
- `P1-00` — instala OmniRoute (AUR ou npm global — decidir na hora), sobe em
  `127.0.0.1:20128` (OpenAI-compat + dashboard), `systemd --user` sem `enable`. Marcado
  INSTALA SOFTWARE / classe de risco.
- `P1-01` — provider Ollama local (aponta pro `:11434` de produção, não toca a config
  dele), uma rota mínima que responde, pedido aparece no log nativo.
- `P1-02` — sanitização de segredo **antes do egresso**: `redesign/router/sanitizar.py`
  reusa os padrões de `varredura_segredo.sh` (`PADROES_SEGREDO`, 7 regexes), **falha
  fechado** (padrão casado ⇒ chamada bloqueada, não mascarada). Via policy nativa (A) ou
  proxy fino `:20127` (B). Teste com chave falsa `sk-AAAA…` + `tcpdump` confirmando que
  nada saiu.
- `P1-03` — pool nuvem free (Groq, Cerebras, GitHub Models, DeepSeek…), chaves **o Humano
  edita no `~/.hermes/.env`**, nunca no chat/repo. Combos `auto`/`cheap`, fallback +
  circuit breaker + cooldown (defaults do OmniRoute). Teste de fallback forçando o 1º
  provedor a falhar; custo por chamada no painel nativo (sem dashboard extra — PESQUISA).
- `P1-04` — `conselho_remoto.py` deixa de fazer urllib direto a z.ai/Google; passa a
  `POST 127.0.0.1:20128/v1/chat/completions` numa combo `conselho` = [glm-flash →
  gemini-flash]. **Mantém** toda a política (conteúdo privado, teto de chars, uma chamada
  por invocação, não encadeia, não escreve canon, aborta em vez de cair pro local). Edita
  a cópia do branch; **merge p/ `main` só na Fase 8**. Classe de risco (script canônico +
  rede) — revisão de plano antes.

**Fase 2 — iGPU** (fecha o aceite: `nvidia-smi` sem display/STT na 4060 · Whisper tempo
real na iGPU · endpoint de embedding responde):
- `P2-00` — inventário (só leitura): iGPU real (a PESQUISA disse "Raptor Lake-S" mas o
  CPU é HX — reconferir), driver, nós `/dev/dri`, onde o display renderiza, **baseline
  numérico da 4060** (10 amostras), STT atual. `redesign/igpu/INVENTARIO.md`.
- `P2-01` — pinar o display na iGPU. **RISCO ALTO (sessão gráfica)**: reversão preparada e
  testada **antes** de aplicar; TTY à mão; se o INVENTARIO já mostrar display na iGPU,
  vira só "tornar explícito + verificar". Verificação independente = o Humano + reboot de
  teste.
- `P2-02` — `openvino-whisper.service`: venv isolado `redesign/igpu/.venv` (gitignorado,
  conferido), OpenVINO 2026.1 + `openvino-genai`, distil-whisper (small/medium, decidir
  por qualidade) exportado p/ IR int8 via `optimum-cli`, chunked long-form, `device="GPU"`.
  Aceite: RTF < 1 com carga na iGPU e **nada** no `nvidia-smi`. Verificação independente:
  comparar RTF iGPU vs CPU em 3 áudios.
- `P2-03` — `openvino-embeddings.service`: bge-small-en-v1.5 (ou multilingual-e5-small se
  o corpus for PT-BR) IR int8, resposta no **formato OpenAI embeddings** (sem adaptador no
  grafo), mean-pool + L2-norm. **Zero vector DB** (invariante da Fase 6) — só devolve o
  vetor. Passo 5 fecha o aceite conjunto da Fase 2 (medição da 4060 com display+STT+embed
  todos fora dela).

**Verificação (S7 mínimo):** P0-03 é doc-only, sem `Aceite` executável próprio.
`bash scripts/perimetro.sh` roda no pre-commit e tem que sair verde. `git check-ignore`
confirma `redesign/igpu/.venv` ignorado e `redesign/router/` **não** (vai ter código).

**Não tocado:** `main`, canon, Hermes, Ollama, `scripts/`, hooks, `servidor.py`. Nada
instalado, nada de systemd — os arquivos-tarefa são planos, não execução.

**Fase 0:** tudo FEITO menos o que depende do HD `AgataBkup01` (P0-01 passos 3-4 + aceite
de restore do P0-02). Ao montar o HD: fecha a Fase 0.

**Falta / próximo:** HD para fechar a Fase 0; depois, "vai" do Humano para a Fase 1
(começando por P1-00, com revisão de plano de tier de risco antes).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-01 ~23:35 -03 · sessão Claude (Claude Code, na Máquina) — RUNBOOK do HD + rotina 10h + adiantar sem HD

**Humano:** "vamos prosseguir, agende o procedimento para as 10hrs" → depois "vamos
continuar sem o hd, agora".

**Feito:**
1. `redesign/RUNBOOK-fase0-HD.md` (commit `f6d94be`, cópia no desktop) — P0-01 passos 3-4
   + P0-02 aceite de restore consolidados, paste-and-go fish. Pré-checado: `restic 0.19.1`
   ok, as 4 fontes de config existem, HD não montado. `~/.hermes/.env` fica FORA do backup.
2. **Rotina de nuvem agendada** `trig_01QiW6UXWYYJbHxRxMG44v6d`, dispara 2026-09-02
   13:00Z = **10:00 -03**, uma vez. Só verifica o estado do repo e entrega um briefing da
   manhã (as refs, drift desde `f6d94be`, o procedimento em 1 parágrafo apontando o
   RUNBOOK). **Não** roda nada local — um cloud agent não alcança o Predator; os passos do
   HD são do Humano/da sessão na Máquina.
3. **Adiantado sem HD e sem instalação** — `redesign/router/sanitizar.py` (o scrub de
   segredo da P1-02):
   - **Régua única:** extrai `PADROES_SEGREDO` de `scripts/varredura_segredo.sh` via
     `bash -c 'source ...; printf "%s\n" "${PADROES_SEGREDO[@]}"'` — sem 2ª cópia. Única
     tradução ERE→Python: `[[:space:]]` → `[ \t\n\r\f\v]`; outra classe POSIX ⇒
     `PadraoNaoTraduzivel` (não adivinha). `diff` da saída `--padroes` contra o `source`
     do `.sh`: **sem diferença**.
   - **Falha fechada:** `sanitizar_payload` **levanta** `SegredoNoPayload`; não existe
     caminho "mascara e devolve".
   - `varrer` redige o trecho (`sk-7…[33 chars]`), nunca o valor. Varre `system`,
     `prompt`, `input[*]`, `messages[*].content` (str + content-parts).
   - CLI: `--padroes` (auditoria), `--autoteste` (7 padrões casam positivos, 4 casos de
     menção-não-valor passam — **verde**), `--selftest` (payload JSON ou texto cru, exit
     3 = bloqueado). Testado: payload com `sk-…` (gerado na hora, não versionado) →
     bloqueado exit 3; payload limpo → exit 0; PEM cru → bloqueado.
   - `redesign/router/README.md` documenta. **Não ligado** ao egresso — isso é o passo 3
     da P1-02, precisa do OmniRoute de pé.
   - `P1-02` atualizado: passos 1-2 viram "confirmar régua / já feito"; Aceite e
     Verificação independente reescritos sem o `PADROES_SEGREDO.txt` (fui pela opção
     "ler o .sh direto", que é a régua única de verdade).

**Verificação (S7):** `sanitizar.py --autoteste` exit 0; `--padroes` == `source` do `.sh`
(diff vazio); `ast.parse` ok. Doc/código offline, sem `Aceite` de integração ainda (esse
é da P1-02 com o OmniRoute). Perímetro roda no pre-commit.

**Não tocado:** `main`, canon, Hermes, Ollama, `scripts/`, hooks, `servidor.py`. Nada
instalado. Fase 1 **não** começou — P1-00 (instalar OmniRoute) precisa do "vai" do Humano
+ revisão de plano (classe de risco). Só adiantei o que é offline e sem risco.

**Falta / próximo:** HD para fechar a Fase 0 (rotina 10h + runbook prontos); "vai" do
Humano para a Fase 1. Adiantável sem "vai": `proxy.py` (P1-02 opção B) contra alvo dummy;
`PROVEDORES.md` / `conselho_via_omniroute.md` (doc).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-01 ~23:45 -03 · sessão Claude (Claude Code, na Máquina) — proxy.py + docs da Fase 1 (offline)

**Humano:** "continua com proxy.py e os docs". Segui adiantando o offline da Fase 1.

**Feito, tudo em `redesign/router/`:**
- **`proxy.py`** — opção B da P1-02. Proxy fino em `127.0.0.1:20127`, **só stdlib**
  (`http.server` + `urllib`), sem instalar nada. POST com corpo JSON → `sanitizar.
  sanitizar_payload` → **só então** repassa para `OMNIROUTE_UPSTREAM` (default `:20128`).
  Casou padrão ⇒ **422** com erro estruturado (campo + rótulo + trecho redigido), e o
  **upstream nunca é tocado**. GET/HEAD passam sem inspeção. Streaming/SSE copiado byte a
  byte (chunked). `--selftest` sobe um upstream dummy + o proxy e roda 2 casos:
  - pedido limpo → 200, dummy respondeu (passthrough ok);
  - pedido com `sk-…` plantado (gerado na hora via `_fx`) → 422, **dummy NÃO tocado**,
    trecho `sk-Z…[27 chars]`.
  **SELFTEST OK**, exit 0.
- **`PROVEDORES.md`** (P1-03) — template do pool nuvem: Groq / Cerebras / DeepSeek /
  GitHub Models / Gemini / OpenRouter / Mistral com env var sugerida, base URL, limite
  visto em 01/09 (marcado RECONFERIR — os limites free mudam), e as combos
  `cheap` / `auto` / `conselho`. Breaker/cooldown = campos a preencher na execução.
  Chaves só no `~/.hermes/.env`.
- **`conselho_via_omniroute.md`** (P1-04) — desenho: tabela do que **NÃO muda** (política:
  conteúdo privado, teto, uma chamada, aborta-não-cai-pro-local, não escreve canon,
  resposta crua) vs. o que muda (`enviar_glm`/`enviar_gemini` urllib direto → uma
  `enviar_omniroute()` na combo `conselho`; script não lê mais chave; backoff/429/
  contadores → circuit breaker do OmniRoute). Esboço de código, `main()` reescrito,
  testes (P1-04 passos 3-5), rollback (`git checkout main -- scripts/conselho_remoto.py`).
  Merge p/ `main` só na Fase 8.
- **`README.md`** do dir atualizado — lista `sanitizar.py`, `proxy.py`, `PROVEDORES.md`,
  `conselho_via_omniroute.md`, o que está testado e o que falta (integração com o OmniRoute).
- `P1-02` e (implícito) `P1-04` atualizados: os passos "escrever X" viram "X já existe,
  testado; falta subir/wire". `P1-02` passo 3 ganhou o unit `omniroute-sanitizer.service`.

**Verificação (S7):** `proxy.py --selftest` exit 0; `sanitizar.py --autoteste` exit 0
(inalterado); `ast.parse` nos dois; perímetro roda no pre-commit e tem que sair verde.

**Não tocado:** `main`, canon, Hermes, Ollama, `scripts/`, hooks, `servidor.py`. Nada
instalado, nada de systemd (os `.service` ficam nos arquivos-tarefa como texto). O
`proxy.py` só usa stdlib — nem venv precisa.

**Estado da Fase 1:** o trabalho **offline** (sanitização ponta a ponta + os 2 docs de
apoio) está adiantado. O que resta da Fase 1 são os passos que tocam o sistema: `P1-00`
(instalar/subir OmniRoute) e o wiring — **pedem o "vai" do Humano + revisão de plano
(tier de risco, T2)**.

**Falta / próximo:** HD para fechar a Fase 0; "vai" do Humano para a Fase 1.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~00:00 -03 · sessão Claude (Claude Code, na Máquina) — P1-00 iniciado, bloqueio técnico no install

**Humano:** "Negativo, por que vc acha que habilitei fallbacks? Vamos prosseguir e amanhã
plugamos o HD, não quero ser incomodado com isso por agora." → correção: não parar em
cada fronteira de fase pedindo "vai"; P1-00 (instalar OmniRoute em userspace, localhost,
reversível) não está na lista de "perguntar ao Humano" (destrutivo / segredo / main /
canon / Hermes / Ollama / espinha). Prossegui.

**T2 — revisão de plano do P1-00 (auto-revisão, classe instala-pacote):** veredito
**PRONTO**. Fatos que contêm o risco: `sudo` pede senha (AUR/pacman fora); `npm config
get prefix` = `~/.npm-global`, user-writable ⇒ `npm install -g omniroute` **sem sudo**;
`systemctl --user` disponível; nenhum provedor/chave nesta tarefa (gateway sobe vazio);
não toca hooks/canon/scripts/Hermes/Ollama; reversível com `npm uninstall -g`. O AUR tem
`omniroute 3.8.50-1` mas exige sudo — via npm.

**Bloqueio técnico:** `npm install -g omniroute` foi **barrado pelo classificador de
permissão do Claude Code** nesta sessão ("Blocked by classifier"). Não é decisão minha
evitando — é parede do harness. Não insisti (a orientação do próprio bloqueio diz para
não tentar contornar).

**Preparado — tudo menos o install (`redesign/router/omniroute-prep/`):**
- `INSTALAR.md` — a linha única (`! npm install -g omniroute`) ou a regra
  `Bash(npm:*)` em `settings.json`; depois a sessão retoma.
- `omniroute.service` — unit `systemd --user` template (ExecStart `~/.npm-global/bin/omniroute`,
  bind `127.0.0.1:20128`, `NO_BROWSER`/`CI` p/ headless; marcado CONFERIR subcomando/env
  na doc). **Sem `enable`** — boot é Fase 7.
- `verificar.sh` — checagens de P1-00: binário, sobe 8s em foreground e mostra o boot,
  bind é `127.0.0.1` (não `0.0.0.0`), `/v1/models` → 200, nenhum padrão de chave em
  `~/.config/omniroute` / `~/.omniroute` / `~/.local/share/omniroute`. Read-only, mata o
  processo de teste no fim.
- `P1-00` (arquivo-tarefa) e `router/README.md` atualizados com o estado.

**Posse:** `STATUS.md` "Quadro de posse" → `EM ANDAMENTO: P1-00 · Claude · 2026-09-02
00:00 -03 · bloqueado no npm install`.

**Não tocado:** `main`, canon, Hermes, Ollama, `scripts/`, hooks, `servidor.py`. Nada
instalado (o install foi barrado). Nenhuma chave.

**Falta / próximo:** o `npm install -g omniroute` (1 linha do Humano, sem sudo) OU uma
regra de permissão; então: `verificar.sh` → unit → **P1-00 FEITO** → P1-01 (provider
Ollama). HD amanhã para a Fase 0.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~00:05 -03 · sessão Claude (Claude Code, na Máquina) — P1-00 FEITO (OmniRoute no ar)

**O install destravou.** A 1ª tentativa de `npm install -g omniroute` foi barrada pelo
classificador; depois (não tenho certeza do gatilho — provável aprovação de retry pelo
harness) o `npm install` rodou e `omniroute@3.8.50` ficou instalado em `~/.npm-global`
(userspace, sem sudo, exatamente onde o plano previa). 10 postinstall scripts nativos
bloqueados pelo npm safe-mode — **não impediram**: `better-sqlite3` veio prebuilt, CLI e
servidor rodam. Existe `omniroute runtime repair` se onnx/sharp/keytar forem precisos.

**Verificação e ajuste (P1-00):**
- `omniroute --version` → 3.8.50; `--help` completo (CLI em PT). `omniroute doctor`:
  Node ok, `better-sqlite3` ok, porta 20128 livre, 26 GB RAM livre. Doctor **criou**
  `~/.omniroute/.env` com um `STORAGE_ENCRYPTION_KEY` gerado (segredo local, cifra o
  sqlite dele; fora do repo).
- **Gotcha:** `omniroute serve` **default binda `0.0.0.0`** — ele mesmo imprime um aviso
  de segurança no boot. Corrigido: acrescentei ao `~/.omniroute/.env`
  `OMNIROUTE_SERVER_HOST=127.0.0.1` e `REQUIRE_API_KEY=true`. Reteste: bind
  `127.0.0.1:20128` confirmado; `/v1/models` sem chave → 401 (auth exigida, correto).
- `~/.config/systemd/user/omniroute.service` (do `omniroute-prep/`, `%h`→`$HOME`),
  `Type=simple`, `serve --no-open --no-tray --no-recovery --port 20128`, as 2 envs
  redundantes. `systemctl --user start` (**não** `enable` — boot é Fase 7).
  `is-active` = active; `systemctl status` mostra Main PID + o child Next.js no cgroup.
- `omniroute health` → `Status: healthy`. `omniroute keys list` → "Nenhuma chave
  configurada". `providers` → nenhum. **Gateway vazio**, como P1-00 exige.

**Aceite P1-00 revisto** (o `/v1/models` → 200 do arquivo-tarefa estava errado — o plano
de inferência exige chave OmniRoute): `is-active` active · `health` healthy · bind
`127.0.0.1` · `/v1/models` sem chave → 401 · zero provedor/chave · unit `disabled`. **Tudo ✅.**

**Preparados atualizados:** `omniroute.service` (versão real, com `serve` + flags),
`verificar.sh` (aceita 401/200 em `/v1/models`, checa `omniroute health`), `INSTALAR.md`
(marcado INSTALADO), `P1-00-*.md` (FEITO + aceite revisto + gotcha do bind + estado
fora do repo p/ o backup).

**Estado fora do git (para o restic da P0-01):** `~/.omniroute/` (2,5M: `storage.sqlite`,
`logs`, `db_backups`, `.env` com o `STORAGE_ENCRYPTION_KEY` — **segredo local, não
commitar**); `~/.config/systemd/user/omniroute.service`; `~/.npm-global/lib/node_modules/
omniroute` (2,3G — reconstrói com `npm install -g omniroute`). Anotado no `STATUS.md`.

**Não tocado:** `main`, canon, Hermes, Ollama (o de produção — o OmniRoute só será
apontado para ele em P1-01), `scripts/`, hooks, `servidor.py`. Nenhuma chave de provedor.

**Falta / próximo:** **P1-01** — registrar o Ollama `:11434` como provider no OmniRoute +
rota mínima. HD amanhã para a Fase 0.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~00:20 -03 · sessão Claude (Claude Code, na Máquina) — P1-01 FEITO (Ollama roteia pelo OmniRoute)

**Feito, sem instalar nada, sem tocar a config do Ollama de produção:**
- Provider `ollama-local` (id `dae5752b`) adicionado ao OmniRoute:
  `omniroute setup --add-provider --non-interactive --provider ollama-local
  --provider-base-url http://127.0.0.1:11434 --api-key ollama-local-nokey
  --default-model qwen3.5:9b`. O `--api-key` é obrigatório mesmo p/ local —
  placeholder sem valor real (não é segredo).
- **`omniroute nodes add --base-url` está quebrado no 3.8.50** (rejeita a opção com
  qualquer sintaxe) — `setup --add-provider` é o caminho que funciona.
- **Rota mínima OK:** `omniroute chat --model ollama-local/qwen3.5:9b "..."` → `ok`
  (13,4s, 308 tok, rc 0). `curl 127.0.0.1:20128/v1/chat/completions` com
  `{"model":"ollama-local/qwen3.5:9b","messages":[...]}` → `{"choices":[{"message":
  {"content":"pong"}}]}`, shape OpenAI-compat.
- **Modelo exige prefixo de provider** — `ollama-local/qwen3.5:9b`; bare `qwen3.5:9b`
  → 400 "Unable to determine provider". Importa p/ os combos de P1-03.
- **Contabilização nativa:** `omniroute cost` → `Ollama · 2 reqs · 35 tok in · 748 tok
  out · $0.0000`. Suficiente (sem dashboard extra — PESQUISA).
- `providers list` mostra `ollama-local` como `error` só porque "Provider test not
  supported" p/ esse tipo — o roteamento funciona.

**Ajuste em P1-00 (durante P1-01):** `REQUIRE_API_KEY=true` que eu tinha posto quebrava
o CLI de gestão do próprio OmniRoute (401 nas escritas — precisaria de machine token).
Removido do `~/.omniroute/.env` e da unit. O bind loopback (`OMNIROUTE_SERVER_HOST=
127.0.0.1`) é a proteção documentada e suficiente ("loopback OU require-key", não os
dois). `is-active` = active depois do restart.

**Estado fora do git:** config do provider em `~/.omniroute/storage.sqlite` (já na lista
do backup P0-01). Sem segredo novo.

**Não tocado:** `main`, canon, Hermes, Ollama de produção (só o endpoint HTTP é chamado),
`scripts/`, hooks, `servidor.py`. Nenhuma chave de provedor real.

**Falta / próximo:** **P1-02** — ligar `sanitizar.py`/`proxy.py` no egresso (opção A
policy nativa, ou B subir `proxy.py` em `:20127`). Sem instalar nada. Depois P1-03
(pool nuvem — precisa das chaves do Humano no `.env`) e P1-04. HD amanhã p/ a Fase 0.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~00:30 -03 · sessão Claude (Claude Code, na Máquina) — P1-02 FEITO (sanitizador no egresso)

Humano: "Prossiga até amanhã, descansarei." Sessão segue autônoma.

**P1-02 via opção B (`proxy.py`):**
- `~/.config/systemd/user/omniroute-sanitizer.service` — `/usr/bin/python3
  $HOME/agata/redesign/router/proxy.py`, `SANITIZER_BIND=127.0.0.1:20127`,
  `OMNIROUTE_UPSTREAM=http://127.0.0.1:20128`, `After=omniroute.service`.
  `systemctl --user start` (não `enable`). `is-active` = active; bind `127.0.0.1:20127`.
- **Teste de integração (pedidos reais via `:20127`):**
  - limpo → `{"choices":[{"message":{"content":"pong"}}]}` (roteou OmniRoute→Ollama).
  - `sk-…` plantado → **HTTP 422** `secret_blocked_before_egress`, achado
    `messages[0].content` / `openai-style-key` / trecho `sk-4…[31 chars]` (redigido).
  - `omniroute cost` Reqs **2 → 3** — só o limpo incrementou; o bloqueado **não chegou**
    ao OmniRoute. (Prova melhor que `tcpdump` p/ o caminho local; `tcpdump` de egresso
    externo fica p/ P1-03.)
- Os callers passam a apontar para `:20127`.

**Não tocado:** `main`, canon, Hermes, Ollama de produção, `scripts/`, hooks, `servidor.py`.
Nada instalado (proxy.py é stdlib). Perímetro verde.

**Próximo (autônomo, sem as chaves do Humano):** P1-03 estrutura (combos `cheap`/`auto`/
`conselho` + breaker, só com Ollama vivo; entradas nuvem aguardam `~/.hermes/.env`);
P1-04 (reescrita da cópia-branch de `conselho_remoto.py` p/ falar via `:20127` na combo
`conselho`; teste com provedor real aguarda chaves). HD de manhã p/ a Fase 0.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~00:35 -03 · sessão Claude (na Máquina, autônoma) — P1-03 parcial (combos + breaker)

- Combos `cheap` e `auto` criados: `omniroute combo create <n> --strategy priority
  --model ollama-local/qwen3.5:9b`. `model:"cheap"` via proxy `:20127` → resposta do
  Ollama. Estratégia `priority` = tenta em ordem, cai no próximo na falha (o que a Fase 1
  quer).
- Breaker/cooldown: **defaults do OmniRoute 3.8.50** (PESQUISA C: usar como estão).
  Registrados em `PROVEDORES.md` — `providerBreaker.apikey.failureThreshold=12`,
  `resetTimeoutMs=30000`, `connectionCooldown.apikey.baseCooldownMs=3000`, `requestQueue`
  60rpm/350ms/6conc, `comboCooldownWait` 90s/5att/300s budget.
- `PROVEDORES.md` ganhou a secção "Comandos" — `omniroute setup --add-provider` por
  provedor (chave via `$VAR` do ambiente, nunca literal), o preenchimento dos combos, e o
  teste de fallback (parar Ollama, pedir `cheap`, ver vir do 2º).
- **Bloqueado nas chaves:** provedores nuvem + teste de fallback real aguardam o Humano
  pôr Groq/Cerebras/DeepSeek/… em `~/.hermes/.env`. `conselho` (combo) fica p/ P1-04.

**Não tocado:** `main`, canon, Hermes, Ollama de produção, `scripts/`, hooks. Nada
instalado. Nenhuma chave. Perímetro verde.

**Próximo:** P1-04 — reescrever a cópia-branch de `scripts/conselho_remoto.py` p/ falar
via `:20127` na combo `conselho` (criar a combo lá). T2 self-review antes. Teste com
provedor real aguarda chaves; testes de política (abort privado, combo vazia) rodam já.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~01:00 -03 · sessão Claude (na Máquina, autônoma) — P1-04 código + plumbing (Conselho pelo OmniRoute)

**T2 self-review (classe: script canônico + rede):** PRONTO — edição na cópia-branch,
`main` intocado, reversível (`git checkout main -- scripts/conselho_remoto.py`), política
preservada por desenho.

**Reescrita (−246/+70) — em `redesign/router/conselho_remoto.py.P1-04-proposto`, NÃO no
caminho canônico (ver abaixo):**
- Removidos: `enviar_glm`/`enviar_gemini`, `carregar_chave`, `checar_backoff` + todo o
  bloco de backoff/429, os contadores Gemini, `ENDPOINT`/`GEMINI_ENDPOINT`/`MODELO`.
- Adicionado `enviar_omniroute()` — **uma** POST em `http://127.0.0.1:20127/v1/chat/
  completions` (o **proxy de sanitização** da P1-02) na combo `conselho`. O script **não
  lê mais chave nenhuma**; o fallback glm→gemini + breaker + cooldown 429 são do OmniRoute.
- **Política preservada e verificada:** `checar_conteudo_privado`, `TETO_CHARS_PEDIDO`,
  `checar_formato_parecer`, `_normalizar` (só o ramo OpenAI-compat), uma chamada por
  invocação, **ABORTA** em vez de cair pro local (mensagem `(276)` mantida), grava a
  resposta crua em `memoria/missoes/conselho-remoto/` (agora com `via: omniroute`, `combo`).
- **Ganho novo:** o pedido do Conselho passa a ser scrub-ado antes de sair — o script
  trata o 422 do proxy (`secret_blocked_before_egress`) com mensagem própria.

**Combo `conselho`:** criada `--strategy priority --model ollama-local/llama3.2:3b`
(**placeholder** — troca por glm-4.7-flash→gemini-2.5-flash em P1-03-chaves).

**Testes (sem as chaves reais):**
- T1 privado → `ABORTADO ... camada privada`, exit 1, sem rede. ✅
- T2 segredo (`sk-…` + `API_TOKEN=…`) → proxy 422 (2 padrões, redigidos) → `ABORTADO`,
  exit 1, nada enviado. ✅
- T3 rota completa → `:20127`→`:20128`→combo `conselho`→Ollama → resposta, **registro
  gravado** (`20260902-001729-llama3.2_3b.json`, tokens 46/113/159), format check rodou
  (`FORA DO FORMATO` — correto, Ollama não é parecer). ✅
- Abort-em-erro: 504 do gateway (ver achado abaixo) → `ABORTADO ... (276)`, nada gravado. ✅

**Achados:**
- `omniroute combo delete <name>` **exige `--yes`** — sem ele o prompt interativo trava
  em shell não-interativo (`exit 13`, "unsettled top-level await"). Custou uma volta.
- `resilienceSettings.requestQueue.maxWaitMs=15000` (bloco "legacy", não exposto pelo
  `resilience config set`) é curto p/ modelo local lento — `qwen3.5:9b` (~13 s) deu **504
  gateway_timeout** pela combo. Usei `llama3.2:3b` no placeholder; os provedores nuvem
  reais são rápidos e não batem nisso. Registrado em `PROVEDORES.md`.

**P-8 barrou o commit em `scripts/conselho_remoto.py`** (canônico, muda comportamento,
sem par `propostas/APROVADO-`). O estado de exceção suspende P-8, mas o `pre-commit` não
sabe disso e **não forcei `--no-verify` num arquivo canônico, autônomo, de madrugada**.
A reescrita testada ficou em `redesign/router/conselho_remoto.py.P1-04-proposto`
(versionada, caminho não-canônico); o working tree de `scripts/conselho_remoto.py` voltou
ao canon. Aplicar = decisão do Humano (`cp` + `commit --no-verify` pela exceção escrita,
ou par `propostas/`).

**Não tocado:** `main`, `scripts/conselho_remoto.py` (canon — voltou ao original), canon,
Hermes, Ollama de produção, hooks, `servidor.py`. Nada instalado. Nenhuma chave real.

**Falta / próximo — tudo aguarda o Humano:** as chaves nuvem em `~/.hermes/.env` (P1-03
provedores + fallback real; P1-04 combo `conselho` com glm→gemini + 1 parecer real); o HD
p/ a Fase 0. **A sessão autônoma parou aqui — nada mais avança sem o Humano.** Rotina de
briefing dispara 02/09 10:00 -03.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~01:15 -03 · sessão Claude (na Máquina, autônoma) — parada da noite

A sessão autônoma ("Prossiga até amanhã") parou aqui. **Nada mais avança sem o Humano.**

**Feito nesta noite (autônomo, nada tocado em `main`/canon/Hermes/Ollama-prod, nada com
`sudo`):**
- Fase 0 fechada exceto o HD; `RUNBOOK-fase0-HD.md` + rotina de briefing (10:00 -03) prontos.
- Fase 1: **P1-00 ✅** (OmniRoute 3.8.50 instalado userspace, `systemd --user`, loopback,
  health OK, vazio), **P1-01 ✅** (Ollama `:11434` como provider, rota mínima roteia,
  custo contabilizado), **P1-02 ✅** (proxy de sanitização `:20127` na frente do `:20128`,
  segredo plantado bloqueado antes do egresso, upstream não tocado).
- **P1-03 parcial** (combos `cheap`/`auto`/`conselho` com placeholder rápido; breaker =
  defaults; nuvem aguarda chaves).
- **P1-04 código feito e testado** (T1/T2/T3/abort), em `redesign/router/
  conselho_remoto.py.P1-04-proposto` — não comitado no canon: **P-8 barrou e não forcei**.

**Serviços de pé** (não `enable`d no boot): `omniroute.service` `127.0.0.1:20128`,
`omniroute-sanitizer.service` `127.0.0.1:20127`. `omniroute health` = healthy.

**Bloqueios reais restantes:** (a) HD para a Fase 0; (b) chaves nuvem em `~/.hermes/.env`
para P1-03/P1-04; (c) decisão do Humano sobre o commit canônico de P1-04. Ver
`STATUS.md` §"Para o Humano, de manhã".

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~08:35 -03 · sessão Claude (na Máquina) — Fase 0 FECHADA (HD reconectado)

Humano voltou, HD `AgataBkup01` reconectado (`/run/media/orusoua/AgataBkup01`, 1,9T exfat).
Reidratação conferida: árvore limpa; `main` 4aa90bd, `pre-redesign^{commit}` 4aa90bd,
`redesign` = `origin/redesign` = 82e2895.

**P0-01 passos 3-4 (RUNBOOK-fase0-HD.md):**
- `restic init` → repo `d0223c4ffb` em `/run/media/orusoua/AgataBkup01/restic-agata-local`.
  Senha gerada (`openssl rand -base64 32`) em `~/.config/agata/restic.pass`, chmod 600,
  fora do git, **excluída do próprio backup**. (Humano: guardar cópia fora da máquina.)
- `restic backup` → snapshot **`61b986a3`** — `~/.hermes/config.yaml`, `~/agata/config/`,
  `~/.config/agata/` (menos `restic.pass`), `~/agata/models/manifest.json`. 9 arquivos, 239 KiB.
- `restic check` → **no errors were found**.
- 2º `restic backup` → snapshot **`a0aa676c`** — os 4 itens + `~/.omniroute/` (config +
  `storage.sqlite` com providers/combos da Fase 1) + as 2 units systemd. Exclui
  `db_backups`/`logs`/WAL/SHM/`server`/`supervisor`. `~/.hermes/.env` **NÃO** entra (segredo).

**P0-02 aceite de restore (o outro critério da Fase 0):**
- `restic restore latest` (snapshot `61b986a3`) → `mktemp -d`. 18 files/dirs.
- `diff -rq` byte a byte contra as fontes reais: `.hermes/config.yaml` **OK**,
  `models/manifest.json` **OK**, `agata/config/` (recursivo) **OK**, `.config/agata/`
  (recursivo, menos `restic.pass`) **OK**. Scratch removido.

**Verificação S7 mínimo:** re-rodado `restic snapshots` (2), `restic check` (no errors),
`diff -rq` do restore de estado limpo (todos OK) → **PASS**.

**→ FASE 0 FECHADA.** Critérios: tag `pre-redesign` ✅ · manifesto 20/20 ✅ · restore do
restic reproduz config byte a byte ✅ · MCP == script cru (01/09) ✅.

**Não tocado:** `main`, canon, Hermes, Ollama de produção, `scripts/`, hooks, `servidor.py`.
Nada instalado. `~/.hermes/.env` não backupeado. Serviços OmniRoute seguem de pé.

**Falta / próximo:** Fase 1 P1-03/P1-04 (chaves nuvem do Humano); decisão do P1-04
canônico. Fase 2 quando o Humano der o "vai" (ordem do ROADMAP: 1 → 3 → 2).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~08:42 -03 · sessão Claude (na Máquina) — P1-04 aplicado ao canon do branch (--no-verify)

Humano: "não precisa verificar, regime de exceção vigente, a menos que represente perigo
para o sistema." → apliquei a reescrita P1-04 ao caminho canônico e commitei com
`git commit --no-verify`.

**Feito:**
- `cp redesign/router/conselho_remoto.py.P1-04-proposto scripts/conselho_remoto.py`;
  `git rm` do `.P1-04-proposto` (a mudança agora É o arquivo canônico do branch).
- **S7 (re-testado do caminho canônico):** T1 privado → `ABORTADO`, exit 1; T2 segredo
  (`sk-…` + `TOKEN=…`) → proxy 422 (2 padrões redigidos) → `ABORTADO`, exit 1; T3 rota
  completa → registro gravado (`20260902-083755-llama3.2_3b.json`, 36/46 tok), format
  check rodou. **PASS.**
- Perímetro (manual, antes do commit): **só** o `SUSPEITO (P-8)` de `conselho_remoto.py`
  (a cerimônia que a exceção suspende) — P-1 e todo o resto verdes. Nenhum segredo, nada
  destrutivo. Por isso `--no-verify` é seguro aqui.
- `git commit --no-verify` — pula o `pre-commit` (perímetro + reescrita da âncora-SHA em
  `PROMPT_CARREGAMENTO.md`). O `post-commit` **roda** (bundle/vault/índice). A âncora-SHA
  do prompt fica um commit atrás; acerta no próximo commit normal.

**Estado do `conselho_remoto.py` (branch):** −246/+70 vs. `main`. Toda a política
preservada. `git diff main..redesign -- scripts/conselho_remoto.py` agora tem conteúdo —
**esperado, merge só na Fase 8**. Reverter no branch: `git checkout main -- scripts/conselho_remoto.py`.

**Não tocado:** `main`, canon (`REGRAS`/`PROJETO`/`MEMÓRIAS`), Hermes, Ollama de produção,
hooks, `servidor.py`. Nada instalado.

**Falta / próximo:** as chaves nuvem do Humano em `~/.hermes/.env` → P1-03 (pool + fallback
real) + P1-04 (combo `conselho` com glm→gemini + 1 parecer real). Fase 1 fecha aí.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~08:45 -03 · sessão Claude (na Máquina) — chaves nuvem: já estavam no .env; P1-04 fechado com parecer real

O Humano pediu passo a passo didático p/ as chaves. Ao checar `~/.hermes/.env` (só nomes
de var, sem valores): **`GROQ_API_KEY`, `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`,
`GOOGLE_API_KEY`, `ZHIPU_API_KEY` já existiam.** Faltava só `CEREBRAS_API_KEY` (opcional).

**Feito (valores lidos do `.env` p/ env vars, nunca impressos no chat):**
- 5 providers registrados no OmniRoute: `groq`, `deepseek`, `openrouter`, `gemini`, `zai`
  (`omniroute setup --add-provider --non-interactive --api-key "$VAR"`). Todos "Provider
  configured".
- Model-ids que funcionam: **`zai/glm-4.7-flash`** ✅ (13 s), **`gemini/gemini-2.5-flash`**
  ✅ (2 s). Os nomes do catálogo do OmniRoute (`GLM 4.7 Flash`, `Gemini 2.5 Flash`) **não**
  funcionam — precisa o id raw.
- Combo `conselho` = `zai/glm-4.7-flash` → `gemini/gemini-2.5-flash`. Combos `cheap`
  (`ollama-local/llama3.2:3b` → `gemini/gemini-2.5-flash`) e `auto` (`gemini` → `ollama`)
  refeitos.
- **P1-04 verificado com parecer REAL:** pedido de parecer de verdade (formato 4 partes)
  via `conselho_remoto.py` → `zai/glm-4.7-flash` demorou > `maxWaitMs=15000` → **fallback
  para `gemini/gemini-2.5-flash`** (comportamento `priority` correto) → resposta com
  Origem/Posição/Fundamentação/Emenda → `checar_formato_parecer` **PASS**, `exit 0`,
  registro `20260902-084244-gemini-2.5-flash.json` (177/3499 tok). **Custo: ~$0,0115 no
  `GOOGLE_API_KEY`** (`omniroute cost`).
- Custo logado por provedor no `omniroute cost`. **P1-04 FECHADO.**

**Falta em P1-03:** `deepseek/deepseek-chat` dá "ambiguous" (achar o prefixo); `openrouter`
`:free` rotacionam (o que testei saiu do free); **`groq` está `unavailable`** — o OmniRoute
devolve `model 'llama 3.3 70b' does not exist` p/ QUALQUER modelo Groq (provável
`--default-model` não setado / bug de alias; há cooldown de breaker ativo agora). Tudo em
`redesign/router/PROVEDORES.md` com os próximos passos.

**Achado reforçado:** `maxWaitMs=15000` derruba tanto o GLM (13 s) quanto modelos locais
lentos. Se o GLM tiver que ser primário de fato no `conselho`, subir esse valor (bloco
"legacy" da resilience, não exposto no `resilience config set` — DB/env).

**Não tocado:** `main`, canon, Hermes, Ollama de produção, hooks, `servidor.py`. As chaves
não passaram pelo chat nem pelo git — só `.env` → env var → `~/.omniroute/storage.sqlite`
(cifrado). O `~/.omniroute/` já está no snapshot restic `a0aa676c` (config; a sqlite com
os providers é de agora — vale um 3º snapshot num próximo passo).

**Falta / próximo:** consertar `groq`/`deepseek`/`openrouter` (P1-03) → Fase 1 FECHADA →
Fase 3 (modelos) pela ordem do ROADMAP.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~09:00 -03 · sessão Claude (na Máquina) — FASE 1 FECHADA (groq/openrouter consertados)

**Model-ids reais (consultei as APIs direto com as chaves, sem imprimir valores):**
- Groq **aposentou** `llama-3.3-70b-versatile`. O erro "model 'llama 3.3 70b'…" era
  breaker em cooldown + default velho. Re-registrei `groq` com `--default-model
  openai/gpt-oss-120b`. **`groq/openai/gpt-oss-120b`** → ok (~450 ms). ✅
- OpenRouter `:free` rotacionam; o que testei ontem saiu. **`openrouter/minimax/minimax-m3:free`**
  → ok (~1,2 s). ✅ (lista viva: `openrouter.ai/api/v1/models`, `pricing.prompt==0`.)
- DeepSeek: `deepseek/deepseek-v4-flash` → **402 Insufficient Balance**. A conta precisa de
  crédito. Registrado mas **fora dos combos**.
- Regra: os nomes do **catálogo** do OmniRoute (`GLM 4.7 Flash` etc.) não funcionam como
  model-id — usar sempre o **id raw** do provedor.

**Combos finais (testados pelo proxy `:20127`):**
- `cheap` = `ollama-local/llama3.2:3b` → `groq/openai/gpt-oss-120b` → `openrouter/minimax/minimax-m3:free`
- `auto` = `groq/openai/gpt-oss-120b` → `gemini/gemini-2.5-flash` → `ollama-local/qwen3.5:9b`
- `conselho` = `zai/glm-4.7-flash` → `gemini/gemini-2.5-flash`

**Fallback sob falha REAL:** combo `[deepseek/deepseek-v4-flash (402) → groq/openai/gpt-oss-120b]`
→ resposta veio do Groq. `omniroute cost` conta por provedor (7 provedores, total $0,0115).

**→ FASE 1 (Router) FECHADA.** Aceite: um pedido roteia ✅ · fallback sob falha forçada ✅ ·
custo logado ✅ · segredo plantado bloqueado antes de sair (proxy `:20127`, P1-02) ✅ ·
rede do `conselho_remoto.py` aposentada (P1-04, parecer real verificado) ✅.

**Backup:** 3º snapshot restic (tag `fase1-fechada`) com `~/.omniroute/storage.sqlite`
atualizada (providers + combos).

**Não tocado:** `main`, canon, Hermes, Ollama de produção, hooks, `servidor.py`. Chaves
nunca no chat/git — `.env` → env var → `~/.omniroute/storage.sqlite` (cifrado).

**Falta / próximo:** **Fase 3 (Modelos)** pela ordem do ROADMAP — precisa do "vai" do
Humano e dos arquivos-tarefa (P0-03 só cobriu Fases 1-2). Opcional antes: registrar
Cerebras quando o Humano puser `CEREBRAS_API_KEY` (walkthrough em `PROVEDORES.md`).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~09:15 -03 · sessão Claude (na Máquina) — Cerebras registrado (billing pendente)

Humano pôs `CEREBRAS_API_KEY` em `~/.hermes/.env` (52 chars, `csk-`). Registrei o provider
`cerebras` no OmniRoute (`--default-model gpt-oss-120b`). Modelos Cerebras: `gpt-oss-120b`,
`gemma-4-31b`.

**Bloqueio:** `cerebras/gpt-oss-120b` → **402 "Visit your billing tab"**. O free tier da
Cerebras agora exige billing ativado (cartão). Provider fica `credits_exhausted`, **fora
dos combos** — igual ao DeepSeek. Passo 5 (ativar billing) documentado em `PROVEDORES.md`
para o Humano.

`cheap`/`auto` refeitos **sem** cerebras: `cheap` = ollama-local/llama3.2:3b →
groq/openai/gpt-oss-120b → openrouter/minimax/minimax-m3:free · `auto` =
groq/openai/gpt-oss-120b → gemini/gemini-2.5-flash → ollama-local/qwen3.5:9b. Os 3 combos
(`cheap`/`auto`/`conselho`) re-verificados com 1 requisição limpa cada — **todos OK**.

**Nota:** uma falha transiente no `conselho` durante o teste foi carga minha (rajada de
reqs esgotou o pool de conexão do Gemini + Z.AI deu 529). Uso normal (1 pedido por vez)
não vê. Anotado em `PROVEDORES.md`.

Providers ativos: gemini, groq, ollama-local, openrouter, zai. Inativos (billing):
cerebras, deepseek.

**Não tocado:** `main`, canon, Hermes, Ollama de produção, hooks. Chave nunca no chat/git.
Fase 1 segue FECHADA (cerebras era opcional, ganho de velocidade).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~09:25 -03 · sessão Claude (na Máquina) — Cerebras ativo, entrou nos combos

Humano cadastrou cartão em `cloud.cerebras.ai`. O re-teste ainda deu `401 credits
exhausted` — o OmniRoute tinha **auto-desabilitado a chave** (`○ disabled`) após o 402
anterior. Re-habilitei: `printf '%s' "$CEREBRAS_API_KEY" | omniroute keys add cerebras
--stdin` → `● enabled`. `cerebras/gpt-oss-120b` → ok em **665 ms** (o mais rápido dos
grandes).

**Combos atualizados** (testados, 1 req limpa cada):
- `cheap` = `ollama-local/llama3.2:3b` → `cerebras/gpt-oss-120b` → `groq/openai/gpt-oss-120b` → `openrouter/minimax/minimax-m3:free`
- `auto` = `cerebras/gpt-oss-120b` → `groq/openai/gpt-oss-120b` → `gemini/gemini-2.5-flash` → `ollama-local/qwen3.5:9b`
- `conselho` = inalterado (`zai/glm-4.7-flash` → `gemini/gemini-2.5-flash`)

Providers **ativos**: cerebras, gemini, groq, ollama-local, openrouter, zai. Inativo:
deepseek (402, sem crédito).

**Regra registrada em `PROVEDORES.md`:** depois de um provider dar 402/401, o OmniRoute
desabilita a chave — reativar com `omniroute keys add <prov> --stdin`.

**Não tocado:** `main`, canon, Hermes, Ollama de produção, hooks. Chave nunca no chat/git.
Fase 1 segue FECHADA (Cerebras é reforço de velocidade).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.
