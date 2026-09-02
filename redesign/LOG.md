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

---

## 2026-09-02 ~09:38 -03 · sessão Claude (na Máquina) — helper reativar-provider.sh

Humano perguntou se re-habilitar a chave depois de 401/402 dá pra ser automático.
**Não nativamente** — e é o default certo: 401/402 = credencial ruim / conta sem saldo,
não é transiente (só 429/5xx o OmniRoute recupera sozinho via breaker). O OmniRoute não
tem como saber que a conta foi consertada sem tentar, e não tenta chave `disabled`.

`redesign/router/reativar-provider.sh <nome>`: lê a chave de `~/.hermes/.env` pela
convenção `<PROV>_API_KEY` (mapa `zai→ZHIPU_API_KEY`, `gemini→GOOGLE_API_KEY`), roda
`omniroute keys add <prov> --stdin` + `resilience reset --provider <p> --yes`, mostra o
status. Valor da chave **nunca impresso**. Toda chamada `omniroute` com `timeout`.
Testado com `cerebras` → `● enabled`, `cerebras/gpt-oss-120b` responde.

Achado no caminho: `omniroute resilience reset` (e `combo delete`) **prompta `[y/N]` e
trava** em shell não-interativo sem `--yes` (o "unsettled top-level await"). Anotado.

Um **timer diário de re-probe** (systemd --user) que rodasse este helper p/ qualquer
provider `disabled` seria trabalho de **Fase 7** (liga/desliga + automação), não agora —
401/402 é raro e sempre o Humano já está no loop consertando a conta.

**Não tocado:** `main`, canon, Hermes, Ollama de produção, hooks. Fase 1 FECHADA.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~09:50 -03 · sessão Claude (na Máquina) — "vai" da Fase 3; arquivos-tarefa escritos

Humano: "vai para a Fase 3." Escritos os 4 arquivos-tarefa em `redesign/tasks/`:
- **P3-00** — manifesto completo + **prova de reconstrutibilidade** num daemon ollama
  isolado (sem apagar nada). É o gate de segurança antes de qualquer prune.
- **P3-01** — `models/PRUNE.md`: keep-list vs. remover, tamanho **real** (blobs
  compartilhados — `qwen3.5:9b` e o `-64k` dividem o mesmo blob), reconstrutível?. Sem apagar.
- **P3-02** — **prune destrutivo**. Classe de risco máxima: revisão de plano obrigatória,
  aprovação do Humano item a item, cada `ollama rm` sozinho num bloco com ⚠️, um por vez,
  `du` entre cada. Manifesto commitado antes.
- **P3-03** — `llama.cpp` (INSTALA SOFTWARE; `pacman` precisa de sudo) com `--n-cpu-moe`
  varrido 8→30, MoE (Qwen3-30B-A3B ou 3.6-35B-A3B GGUF) servido em `127.0.0.1:20129`
  OpenAI-compat, registrado no OmniRoute como `llamacpp-local`, na combo `auto`. Aceite:
  MoE ≥ ~20 tok/s **ou** número medido + decisão conservadora (worker = 9B+LoRA).

**Estado atual dos modelos:** 20 no Ollama, dir `/usr/share/ollama/.ollama/models`,
`/home` com 364 GB livres. **Nenhum MoE ainda** (P3-03 adquire). `llama.cpp` não instalado.
Manifesto: 20/20 com sha256 (de P0-00).

**Posse:** `STATUS.md` → `EM ANDAMENTO: P3-00`.

**Próximo:** executar P3-00 (só leitura + reconstrução em daemon isolado — nada apagado).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~10:05 -03 · sessão Claude (na Máquina) — P3-00 FEITO (reconstrutibilidade provada)

**Auditoria dos 20 modelos** (`models/manifest.json`, sem apagar nada — tag descartável +
`ollama rm`, `ollama list` = 20 antes e depois):
- **14 registry** → `ollama pull <name>`.
- **4 custom-param** (`*-64k`) → `ollama pull <base>` + `ollama create -f <Modelfile>`.
  **Blob de pesos = o da base** (`qwen3.5-9b-64k` e `qwen3.5:9b` compartilham
  `sha256-dec52a4456…`) — somar `size_gb` deles superestima o prune. **Testado**
  `qwen3.5-9b-64k`: blob do recriado = manifesto. ✅
- **`nomic-embed-text`** → é library, `ollama pull nomic-embed-text` (heurística de P0-01
  classificou "custom" à toa).
- **`rlm-qwen3-8b-teste`** → único que depende de arquivo local: GGUF
  `memoria/missoes/rlm-3caminhos/modelo/rlm-qwen3-8b-v0.1-q4_k_m.gguf` (4,7 GB). O `sha256`
  do GGUF (`c3b6bfbc…`) É o blob do Ollama — import verbatim, reconstrói bit a bit.
  **Não está nos snapshots restic** (só config). Item de backup a decidir com o Humano.

**`models/RECONSTRUCAO.md`** criado com os 3 métodos + a tabela + o alerta do GGUF do rlm.

**Aceite P3-00:** todo modelo cai numa classe com método escrito; 1 registry + 1 custom
com sha256 conferido; o não-reconstrutível-só-por-manifesto (`rlm`) está identificado com
o GGUF localizado; nada apagado. ✅

**Não tocado:** `main`, canon, Hermes, Ollama de produção (só leitura + tag descartável),
hooks. Nada instalado.

**Falta / próximo:** **P3-01** — `models/PRUNE.md` (keep-list vs remover, tamanho real por
blob órfão). Sem apagar. Depois P3-02 pede aprovação item a item do Humano.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~10:15 -03 · sessão Claude (na Máquina) — P3-01 FEITO (models/PRUNE.md, sem apagar)

Análise por blob (do `ollama show --modelfile` de cada modelo + `size_gb` do manifesto;
`du` do dir de blobs deu "permissão negada" — é do user `ollama` — a conferência exata de
GB vai no P3-02 com `sudo du`).

**Proposta:**
- **Keep-list (~14 GB):** `qwen3.5:9b` (6,6) + `qwen3.5-9b-64k` (blob compart., de graça) +
  `rlm-qwen3-8b-teste` (5,0) + `llama3.2:3b` (2,0, 4B-base provisório) + `nomic-embed-text`
  (0,27). O MoE do P3-03 entra depois (~18 GB, GGUF fora do Ollama).
- **Remover (15 modelos, LIBERA ~112 GB):** `llama3.3:70b` (42), `qwen2.5:32b`+`-64k` (19),
  `qwen3:14b`+`-64k` (9,3), `qwen2.5:14b`+`-64k` (9,0), `deepseek-r1:14b` (9,0), `gemma2:9b`
  (5,4), `qwen3:8b` (5,2), `llama3.1:8b` (4,9), `qwen2.5:7b`+`-instruct-q4` (4,7),
  `phi3:mini` (2,2), `gemma2:2b` (1,6). **Todos reconstroem 100% por `ollama pull`** (+
  `ollama create` p/ os `-64k`) — nenhum depende de GGUF local.
- Motivo do prune agressivo: a Fase 1 pôs nuvem grátis+rápida (`gpt-oss-120b` no Groq/
  Cerebras, $0) no lugar dos densos grandes locais.

**Pende de decisão do Humano** (é remoção destrutiva de dados): aprovar a lista item a
item; escolher o 4B-base (`llama3.2:3b` vs. baixar um 4B real); decidir backup do GGUF do
`rlm-qwen3-8b-teste`; salvar algum "remover" mesmo assim (ex. `deepseek-r1:14b`).

**Não tocado:** `main`, canon, Hermes, Ollama de produção (só `ollama show`), hooks. Nada
apagado, nada instalado.

**Falta / próximo:** aprovação do Humano → **P3-02** (prune, um `ollama rm` por bloco).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~10:40 -03 · sessão Claude (na Máquina) — P3-02: 16 modelos removidos (espaço pende de restart)

Humano: "1 sim" (aprova a lista), "2 o que for melhor pro sistema", "3 explique melhor".

**#2 decidido:** a base do LoRA (Fase 5) fica `qwen3:4b` — coerente com o zoo (tudo Qwen:
fallback `qwen3.5:9b`, Regra 8, MoE futuro Qwen3-30B-A3B). `qwen3:4b` (4,0 B, 262k ctx,
Q4_K_M) baixado. `llama3.2:3b` (Llama, tokenizer/template diferente) entrou na lista de
remover no lugar dele.

**P3-02 feito:** 16 `ollama rm` (todos ok) — `llama3.3:70b`, `qwen2.5:32b`+`-64k`,
`qwen3:14b`+`-64k`, `qwen2.5:14b`+`-64k`, `deepseek-r1:14b`, `gemma2:9b`, `qwen3:8b`,
`llama3.1:8b`, `qwen2.5:7b`+`-instruct-q4`, `phi3:mini`, `gemma2:2b`, `llama3.2:3b`.
`ollama list` = keep-list de **5**: `qwen3.5:9b`, `qwen3.5-9b-64k`, `qwen3:4b`,
`rlm-qwen3-8b-teste`, `nomic-embed-text`.

**Verificação:** API `/api/generate` — `qwen3.5:9b`/`qwen3:4b`/`rlm-qwen3-8b-teste`
respondem "ok"; `nomic-embed-text` é embedding. `models/manifest.json` regenerado:
5 modelos, sha256 5/5.

**Bloqueio:** Ollama 0.32.11 faz GC de blob **lazy** — `df /` segue 362 GB livres. Reclamar
os ~112 GB precisa de **`sudo systemctl restart ollama`** (senha do Humano). O dir de
blobs é `ollama:700` — `du`/`ls` do executor dá permissão negada; conferência de GB só com sudo.

**Não tocado:** `main`, canon, Hermes, hooks, `servidor.py`. `scripts/` só o manifesto de
`models/`. Sem instalação de pacote.

**Falta / próximo:** Humano roda `sudo systemctl restart ollama`; conferir `df` / `sudo du`;
então P3-02 fecha e vai P3-03 (llama.cpp + MoE, INSTALA SOFTWARE — também sudo).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 ~11:00 -03 · sessão Claude (na Máquina) — backup do GGUF do rlm + MIGRAÇÃO DE CHAT

**#3 (backup do rlm):** Humano autorizou. Snapshot restic **`c19275ec`** (tag `rlm-gguf`,
4,685 GiB) — inclui `memoria/missoes/rlm-3caminhos/modelo/rlm-qwen3-8b-v0.1-q4_k_m.gguf`
(o único modelo não-reproduzível) + `models/` (com `RECONSTRUCAO.md`/`PRUNE.md`) +
`~/.omniroute` atualizado. Confirmado que o GGUF entrou (`restic ls latest`). 4 snapshots
no repo.

**Prune (P3-02):** Humano rodou `sudo systemctl restart ollama` e disse "tudo certo". O
`df -h /` desta sessão ainda mostrava 362 GB livres / 587 usados — **não confirmei os ~112
GB reclamados** (pode ser cache do `df`, GC lento do Ollama 0.32.11, ou precisar de mais
tempo/reboot). **Item aberto explícito no chat novo:** `df -h /` + `sudo du -sh
/usr/share/ollama/.ollama/models` (esperado ~14 GB, era ~126). O `ollama list` já está
correto (keep-list de 5) e `manifest.json` regenerado — a remoção lógica está feita, só a
recuperação física de disco pende de conferência.

**Migração de chat:** a janela de contexto do chat atual chegou a ~84%. Escritos:
- `redesign/REIDRATACAO-chat-3.md` — guia de retomada para a sessão Claude nova (reidratar,
  ordem de leitura, estado numa tela, papéis, fluxo, próximo passo). Cópia em
  `~/Área de trabalho/agata-REIDRATACAO-chat-3.md`.
- `redesign/CONSELHO-02-sync-fallbacks.md` — orienta Codex e Qwen Coder a sincronizar com
  este HEAD e ficar **de prontidão** (não executam nada agora). Cópia no desktop.

**Estado do git no fim:** árvore limpa, tudo commitado e empurrado. `main` `4aa90bd`,
`pre-redesign^{commit}` `4aa90bd`, `redesign` = `origin/redesign` (ver HEAD abaixo).

**Não tocado:** `main`, canon, Hermes, Ollama de produção, hooks. Nada instalado nesta
entrada.

**Falta / próximo (chat novo):** (1) confirmar o disco reclamado → fechar P3-02;
(2) P3-03 (`llama.cpp` + MoE — sudo do Humano) → fecha a Fase 3; (3) depois Fase 2 (iGPU).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 10:37 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3 pós-migração) · P3-02 FECHADO (disco reclamado)

**Reidratação:** 4 refs conferidos — `main` `4aa90bd`, `pre-redesign^{commit}` `4aa90bd`
(objeto-tag bare `cea5aeb`), `redesign` = `origin/redesign` `53b2d42` (adiante do piso
`7fbaf41`, ancestral confirmado). `git status --porcelain` vazio. `git diff main..redesign`
só o esperado (`PROMPT_CARREGAMENTO.md` bloco `ANCORA-SHA`; `scripts/conselho_remoto.py`
P1-04 cópia-branch; `.gitignore` P0-00; `models/*` Fase 3). Perímetro verde (10 OK · 1
PARCIAL · 0 FALHA). Lidos na ordem do `REIDRATACAO-chat-3.md`. Canon em (309).

**Nota de relógio:** a máquina marca ~10:37 -03; os commits de hoje são 09:26–09:56. Os
carimbos "~10:40 / ~11:00" das últimas entradas eram ~1h adiantados (relógio da UI). Uso a
hora da máquina daqui pra frente.

**Item aberto do P3-02 — resolvido:** o `sudo systemctl restart ollama` de ontem (09:49:13,
confirmado no journal) **não reclamou** os ~112 GB — `df /` seguia 586 usados / 362 livres.

Diagnóstico (bloco só-leitura com sudo, rodado pelo Humano):
- `du` do dir do Ollama = **14 GB** (era ~126). O `ollama rm` funcionou; 20 blobs para 5
  modelos, **zero órfão**.
- Sistema é **btrfs** (`@`, `compress=zstd:3`) + **snapper**. `btrfs fi usage`: `Data Used
  578 GiB` — os 112 GB seguiam **referenciados**.
- `snapper -c root list`: **50 snapshots `pre`/`post` de `pacman`** (`#454` 12/ago → `#503`
  01/set 20:07), cleanup `number`. **Todos anteriores ao prune** (~09:45 de hoje). Cada um
  contém uma cópia congelada de `/usr/share/ollama/` → o btrfs mantém os extents vivos.
- Recuperação **tudo-ou-nada**: os 16 modelos removidos são antigos, presentes em todos os
  50 snapshots; manter 1 pré-prune mantém ~126 GB presos.

**Ação (destrutiva, aprovada e rodada pelo Humano):** `sudo snapper -c root delete 454-503`
— apaga os 50 pontos de rollback do `pacman` (não toca o snapshot `0`/`current`, nem
`@home`/`@log`, nem dados do Humano; o próximo `pacman -Syu` cria snapshots novos).

**Resultado:** livre **362 → 510 GB** (`df`), `Data used` **578 → 430 GiB** — **~148 GiB
reclamados** (os ~112 dos modelos + ~36 de outra churn de 3 semanas que os snapshots
prendiam). `Device allocated` 729 → 684 GiB.

**S7 (re-rodado de estado limpo):**
- `ollama list` == keep-list de 5 (`qwen3.5:9b`, `qwen3.5-9b-64k`, `qwen3:4b`,
  `rlm-qwen3-8b-teste`, `nomic-embed-text`). ✅
- `/api/generate`: `qwen3.5:9b`/`qwen3.5-9b-64k`/`qwen3:4b` → `"ok"`; `rlm-qwen3-8b-teste`
  → responde (tagarela mas `done=true`); `nomic-embed-text` → embedding **768-dim**. ✅
- `models/manifest.json`: **5 modelos, sha256 em 5/5** (`qwen3.5:9b` e `-64k` compartilham
  o blob `dec52a44…` — esperado, P3-00), commitado em `7fbaf41`, `git status models/` limpo. ✅
- **P3-02 → PASS. FECHADO.**

**Não tocado:** `main`, canon (`REGRAS`/`PROJETO`/`MEMÓRIAS`), Hermes, Ollama de produção
(só API HTTP + `ollama rm`/`list`), hooks, `servidor.py`. Nada instalado. Os snapshots
apagados são do `pacman`/snapper, fora do escopo do Agata — só prendiam disco.

**Falta / próximo:** **P3-03** — `sudo pacman -S llama.cpp` (senha do Humano) → MoE GGUF →
varredura `--n-cpu-moe` → `127.0.0.1:20129` → OmniRoute `llamacpp-local` → combo `auto`.
**Fase 3 fecha aí.** Depois Fase 2 (iGPU).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 11:01 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · P3-03 FEITO — FASE 3 FECHADA

**Revisão de plano (T2, classe instala-pacote + baixa ~18 GB + serviço novo — auto-revisão):**
veredito PRONTO com 2 ajustes ao arquivo-tarefa: (1) o pacote é `llama-cpp` (não `llama.cpp`)
e o offload CUDA vem no backend separado `ggml-cuda`; `cuda 13.3.1` + `nvidia-utils` já
instalados. (2) `huggingface_hub` não está no python do sistema → baixar o GGUF por `wget`
da URL pública do HF.

**Instalação (Bloco 1, rodado pelo Humano com sudo):** `sudo pacman -S --needed llama-cpp
ggml-cuda` (repo `extra`/`cachyos-extra-v3`, assinados; puxou `ggml` + `nccl`). `llama-cpp
0.3.0-1.1` build 10621 commit `c1d0e7a004`. `llama-server --list-devices` → `CUDA0: RTX
4060`. O `pacman` tirou os snapshots snapper #504/#505 (4 pacotes, ~540 MiB — sem risco).

**Modelo:** escolha do Humano entre Qwen3-30B-A3B e Qwen3.6-35B-A3B → **Qwen3-30B-A3B**
(mais capaz na variante `-Instruct-2507`, GGUF unsloth consolidado, cabe folgado na RAM).
`Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf` — 17,3 GiB (18.550.716.416 B), arquivo único,
`sha256 6c997b8af17debdfb01d890214400ccbab00db6acc0ba8da5de1cc906c4774d0`. Em
`~/.cache/agata/models/` (subvolume `@cache`, **fora dos snapshots do snapper** — não
repete o P3-02). Baixado por `wget -c` (sessão, ~22 MB/s).

**Varredura `--n-cpu-moe`** (`llama-bench -ngl 999 -p 128 -n 128 -r 3`):

| N | pp128 | tg128 | VRAM pico (bench) |
|---:|---:|---:|---:|
| 48 | 116,1 | 20,3 | 1165 MiB |
| 44 | 126,3 | 22,5 | 2659 MiB |
| 40 | 138,1 | 25,7 | 4103 MiB |
| 36 | 148,9 | 28,4 | 5449 MiB |
| 32 | 161,1 | 32,1 | 6843 MiB |
| 28 / 24 / 20 | — | — | **falha ao carregar (CUDA OOM)** — usável ≈ 7834 MiB |

Servidor real (`llama-server -c 8192`, geração de verdade): **N=32** → 34,9 tok/s mas VRAM
pico 7637 MiB (**só ~197 MiB de folga** — inseguro); **N=36** → **31,4 tok/s**, VRAM pico
6243 MiB (**~1590 MiB de folga**). **Escolhido N=36** — os ~3 tok/s abertos mão compram
margem real na 4060 (que também move o desktop) até a Fase 7 fazer o liga/desliga de VRAM.
Offload GPU confirmado: `nvidia-smi utilization.gpu` oscilou 9–100 % na geração, não é 100 %
CPU.

**Serviço:** `~/.config/systemd/user/llamacpp-agata.service` (`Type=simple`,
`Restart=on-failure`, `Nice=5`, **sem `enable`** — boot é Fase 7). `llama-server -ngl 999
--n-cpu-moe 36 --host 127.0.0.1 --port 20129 -c 8192 --alias qwen3-30b-a3b --no-webui`.
Sobe healthy em ~6 s. `/v1/models` → id `qwen3-30b-a3b`.

**OmniRoute:** provider `llamacpp-local` (`--provider-base-url http://127.0.0.1:20129/v1`,
`--default-model qwen3-30b-a3b`). Model-id de chamada `llamacpp-local/qwen3-30b-a3b`.
Combo `auto` refeita:
- antes: `cerebras/gpt-oss-120b → groq/openai/gpt-oss-120b → gemini/gemini-2.5-flash → ollama-local/qwen3.5:9b`
- depois: `… → gemini/gemini-2.5-flash → llamacpp-local/qwen3-30b-a3b → ollama-local/qwen3.5:9b`

**Decisão de posição (pelo espelho, sem risco → executada e registrada):** o arquivo-tarefa
sugeria o MoE em tier 2. Com o número real (31 tok/s, ~2 s ao 1º token) ele não compete em
latência com o `gpt-oss-120b` na nuvem (~450 ms); é um *bom fallback local*. Posto em
**tier 4**, logo acima do denso 9B — sobe o tier local de 9B para 30B-A3B e mantém `auto`
com as nuvens rápidas primeiro. Reversível (`combo delete/create`).

**Verificação (S7, re-rodado de estado limpo):**
- `is-active` = active · `/health` 200 · bind `127.0.0.1:20129` · `is-enabled` = disabled. ✅
- `/v1/models` → `qwen3-30b-a3b`, `n_ctx 8192`, 30.5B, Q4_K_M. ✅
- `llamacpp-local/qwen3-30b-a3b` roteia direto (`:20128`) **e pelo proxy sanitizador**
  (`:20127`) → `"ok"`, fingerprint `b10621-c1d0e7a004`. ✅
- Fallback forçado: combo throwaway `[deepseek/deepseek-v4-flash (402) → llamacpp-local/
  qwen3-30b-a3b]` via `:20127` → resposta de `model: qwen3-30b-a3b`. Combo apagada. ✅
- `omniroute cost` → linha `llamacpp-local` (2 reqs, $0,0000). ✅
- `models/manifest.json` → 6 modelos (5 Ollama + 1 `backend: llama.cpp`), `blob_sha256`
  em 6/6. ✅
- **P3-03 → PASS.**

**→ FASE 3 (Modelos) FECHADA.** Aceite: manifesto reconstrói qualquer mantido (registry
pull / `ollama create` / download HF+sha256) · `ollama list` (5) + backend llama.cpp (1)
batem com o manifesto · MoE **31,4 tok/s ≥ ~20**.

**Arquivos:** novo `redesign/router/llamacpp.md` (tabelas da varredura, decisão do N,
comando do serviço, rollback, reconstrução); `models/manifest.json` (+entry MoE);
`redesign/tasks/P3-03-*.md` (status FEITO); `STATUS.md`, `ANCORA.md` (piso → `224901a`),
`LOG.md`.

**Não tocado:** `main`, canon (`REGRAS`/`PROJETO`/`MEMÓRIAS`), Hermes, Ollama de produção,
hooks, `servidor.py`. Sem segredo (o GGUF é público; api-key do provider é placeholder).
Os pacotes instalados são do repo oficial Arch, reversíveis por `pacman -Rns`.

**Falta / próximo:** **Fase 2 (iGPU)** — ordem `0→1→3→2` do ROADMAP. Arquivos-tarefa
P2-00..P2-03 já escritos (P0-03). Pede o "vai" do Humano + revisão de plano (P2-01 —
pinar display na iGPU — é risco alto, sessão gráfica; reversão testada antes).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 11:08 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · Fase 2 "vai"; P2-00 FEITO (inventário iGPU)

**Humano: "vai"** para a Fase 2 (iGPU). Executado **P2-00** (inventário — só leitura, nada
instalado; `glxinfo`/`clinfo` já estavam no sistema). `redesign/igpu/INVENTARIO.md` escrito.

**Achados-chave:**
- **iGPU:** Intel Raptor Lake-S UHD Graphics `[8086:a78b]` rev 04 (PCI `0000:00:02.0`),
  driver **`i915`**, Mesa 26.2.1. Nó de compute: **`/dev/dri/renderD129`** (a NVIDIA tem o
  `renderD128` — o aceite do P2-00 supunha `renderD128` para a iGPU; é o 129). `renderD129`
  é `crw-rw-rw-`, iGPU exposta. (A dúvida da PESQUISA "HX não bate com -S" não procede — o
  i7-13650HX usa a die RPL-S.)
- **Display JÁ está na iGPU.** Painel `eDP-1` no conector de `card2` (i915); único output,
  sem MUX, sem tela externa. `kwin_wayland` usa **7 MiB** na 4060 (handle de modo híbrido,
  não render). Renderer GL default = `Mesa Intel(R) Graphics (RPL-S)`; `DRI_PRIME=1` →
  offload zink p/ a 4060. → **P2-01 cai de risco ALTO para BAIXO** — vira "tornar explícito
  + verificar após reboot de teste", não migração no escuro.
- **Baseline 4060 em repouso** (10 amostras `nvidia-smi dmon`, estável): **54 MiB / 8188 de
  VRAM · ~16–17 W · GPU-util 0 % · 42–44 °C.** Consumidores: `kwin_wayland` 7 MiB, `Xorg`
  4 MiB, Brave com `/dev/nvidiactl`. Nenhum compute. Ollama keep-alive não residente.
- **Nenhum STT existe hoje.** Zero unit whisper/stt/voice (só `speech-dispatcher` = TTS de
  acessibilidade). Nada em `~/.hermes/`/`~/.config/`. → **P2-02 é greenfield**, não desmonta nada.
- **Lacuna:** `clinfo -l` só lista `NVIDIA CUDA` — a iGPU não tem runtime de compute. O
  plugin GPU do OpenVINO precisa de **`intel-compute-runtime`** (Level Zero + OpenCL).
  Instalar em P2-02 (sudo). `intel-gpu-tools` e `libva-utils` também ausentes.
- **Nota de ferramenta:** o driver `NVIDIA-SMI 610.57.04` **não aceita** `power.draw` nem
  `temperature.gpu` em `--query-gpu` (a query inteira falha). Usar `dmon`/`-q` p/ isso.

**Verificação (S7):** P2-00 é só leitura, sem `Aceite` executável — o `INVENTARIO.md`
responde as 4 perguntas (a/b/c/d) contra saídas cruas. `bash scripts/perimetro.sh` roda no
pre-commit e tem que sair verde.

**Não tocado:** `main`, canon, Hermes, Ollama, hooks, `servidor.py`. Nada instalado. Nenhum
serviço mexido. `llamacpp-agata.service` foi **parado** após o P3-03 (VRAM livre; boot é Fase 7).

**Falta / próximo:** revisão de plano (tier de risco) de **P2-01** (agora BAIXO — tornar o
display-na-iGPU explícito + verificar por reboot), **P2-02** (`openvino-whisper` — INSTALA
`intel-compute-runtime` + `intel-gpu-tools`, venv, distil-whisper int8; classe instala-pacote
→ 2º par de olhos) e **P2-03** (`openvino-embeddings` — reusa o runtime). Cada um pede o
"vai" quando tocar `sudo`/instalação.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 11:12 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · P2-01 FEITO (sem mudança) + revisão de plano P2-02/P2-03

**P2-01 — display na iGPU — FEITO, SEM MUDANÇA.** O P2-00 já mostrou o display na iGPU; o
passo 0 do arquivo-tarefa manda ir direto para "documentar + verificar". `redesign/igpu/
DISPLAY-PIN.md` escrito.
- **Estrutural, não config:** o painel `eDP-1` é conector de `card2` (i915); a 4060 não tem
  trilha de display para o eDP (laptop Optimus sem MUX no painel interno). O KWin **tem**
  que usar a iGPU para acender a tela.
- **Nada força a 4060:** procurado e ausente — `~/.config/plasma-workspace/env/` (não
  existe), `environment.d`/`/etc/environment` (sem PRIME/DRI_PRIME/KWIN_DRM), `xorg.conf.d`
  (só teclado), `envycontrol`/`supergfxctl`/`optimus-manager`/`prime-select` (nenhum
  instalado), `kwinrc` (sem GPU), `/proc/cmdline` (sem flag).
- **Decisão pelo espelho (sem risco → executada e registrada):** **não** adicionar
  `KWIN_DRM_DEVICES`. A garantia física (fiação do painel) é mais forte que env var, que
  ainda poderia quebrar num rename do `by-path`. Espinha mínima.
- Risco reavaliado: ALTO → **nenhum** (nada mudou; `redesign-igpu-backup/` nem foi criado).
- Reboot de teste: a sessão atual já é pós-boot nesta config (uptime > 1 dia). Pendente só
  se o Humano quiser confirmação dedicada.
- **Verificação (aceite):** `nvidia-smi` 4060 em repouso 54 MiB / 0 % util (kwin 7 MiB /
  Xorg 4 MiB = handles de modo híbrido, não render); sem fração de display a remover. ✅

**Revisão de plano — P2-02 e P2-03 (T2, classe instala-pacote — auto-revisão):**

- **P2-02 (`openvino-whisper`) — veredito PRONTO.** Contém o risco: `sudo pacman -S
  intel-compute-runtime intel-gpu-tools` (repo `extra`, assinado, reversível `-Rns`) — a
  lacuna que o P2-00 achou (o plugin GPU do OpenVINO precisa do Level Zero); venv
  `redesign/igpu/.venv` gitignorado (conferido, `redesign/**/.venv/`), `rm -rf` reversível;
  pip ~2–3 GB (openvino, openvino-genai, optimum[openvino], transformers, librosa,
  soundfile — puxa torch); modelo distil-whisper int8 ~200–500 MB em
  `~/.cache/agata/openvino/`. Sem segredo/canon/Hermes/Ollama/hooks. **Ajuste ao arquivo-
  tarefa:** o passo 1 tem que instalar `intel-compute-runtime` **antes** do check
  `ov.Core().available_devices` (senão só lista `CPU`). Incerteza medida-e-decide: a UHD
  RPL-S (no 13650HX pode ser a versão de 16 EU) pode não fechar RTF<1 no distil-small — o
  arquivo já tem o fallback (medir, tentar distil-medium, ou registrar e seguir). Precisa
  de um WAV de ~30 s de fala p/ o selftest (gero por TTS local).
- **P2-03 (`openvino-embeddings`) — veredito PRONTO, menor risco.** Reusa venv + runtime do
  P2-02; só adiciona um modelo IR (~130 MB) e um serviço `:20131`. **Decisão embutida:**
  bge-small-en-v1.5 vs multilingual-e5-small — o corpus do Agata (REGRAS/PROJETO/MEMÓRIAS)
  é **PT-BR** → recomendo **`intfloat/multilingual-e5-small`** (384 dim, prefixos
  `query:`/`passage:`). Resposta no formato OpenAI embeddings (sem adaptador no grafo).
  **Zero vector DB** (invariante) — só devolve o vetor.
- **Sequência:** P2-02 (1 bloco sudo + pip longo + medir) → P2-03 (reusa, fecha o aceite
  conjunto da Fase 2: 4060 sem display/STT/embeddings).

**Não tocado:** `main`, canon, Hermes, Ollama, hooks, `servidor.py`. Nada instalado nesta
entrada. `llamacpp-agata.service` segue parado (boot = Fase 7).

**Falta / próximo:** "vai" do Humano para o `sudo pacman -S intel-compute-runtime
intel-gpu-tools` (P2-02 passo 1) → resto do P2-02 → P2-03 → Fase 2 fechada.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 12:00 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · P2-02 FEITO — whisper STT na iGPU

**Instalação (Bloco 1, Humano com sudo):** `sudo pacman -S --needed intel-compute-runtime
intel-gpu-tools` (puxou `intel-graphics-compiler`, `libprocps`, `peg`; repo
`cachyos-extra-v3`/`extra`, assinados). `clinfo -l` **agora lista** `Platform #1: Intel(R)
OpenCL Graphics -> Intel(R) UHD Graphics` — a lacuna do P2-00 fechada. snapshots snapper
#506/#507 (pequenos).

**venv `redesign/igpu/.venv`** (gitignorado, conferido): `pip install openvino>=2026.1
openvino-genai>=2026.1 optimum[openvino] transformers librosa soundfile hf_transfer`.
Instalou **openvino 2026.3.1**, **openvino-genai 2026.3.1**, optimum 2.3.0, optimum-intel
2.1.0, transformers 5.5.4, torch 2.14 (cp314; puxou ~2 GB de libs CUDA à toa — venv
descartável). `ov.Core().available_devices` = **`['CPU','GPU.0','GPU.1']`** — `GPU.0` =
Intel UHD (iGPU), `GPU.1` = RTX 4060, `CPU` = i7-13650HX.

**Conversão do modelo — o caminho do arquivo-tarefa falhou, troquei:**
- `optimum-cli export openvino --model distil-whisper/distil-small.en --weight-format int8`
  → **`TypeError: NormalizedConfig.__init__() got multiple values for argument 'allow_new'`**.
  Bug do `optimum` 2.3.0 no export de Whisper; persiste com `transformers` 5.5.4 **e**
  4.57.6 (baixei p/ 4.57.6 e não resolveu — mantido 4.57.6, que é o alvo testado do
  optimum-intel 2.1.0).
- **Solução:** IR **pré-convertido** do org `OpenVINO/` no HF, via `snapshot_download`.
  Baixados `OpenVINO/whisper-base-int8-ov` (74 M, 81 MB) e `OpenVINO/whisper-small-int8-ov`
  (244 M, 245 MB) — trazem `openvino_encoder/decoder_model.xml/.bin` + `openvino_tokenizer`
  /`detokenizer`, prontos p/ o `WhisperPipeline`. **Desvio de modelo registrado:** não
  `distil-small.en` (English-only; o canon é PT-BR) → **whisper-base multilíngue**.

**`redesign/igpu/whisper_server.py`** (novo, stdlib http.server): `openvino_genai.
WhisperPipeline(dir, device="GPU.0")`; `POST /transcribe` (path ou WAV cru) →
`{text,chunks,audio_s,proc_s,rtf,device,model}`; `GET /health`; long-form chunkado pelo
pipeline; `--selftest <wav> [--device CPU|GPU.0] [--model DIR]`. `GPU.0` fixado no default
(nunca cair na `GPU.1`/4060).

**RTF medido** (`fala30s.wav`, 36 s, espeak-ng), iGPU (`GPU.0`) vs CPU:

| modelo | GPU.0 (iGPU) | CPU |
|---|---|---|
| **base**  | **RTF 0.082** (2.97 s) | RTF 0.022 (0.8 s) |
| small | RTF 0.212 (7.64 s) | RTF 0.057 (2.07 s) |

Todos **muito** abaixo de RTF 1. O CPU é 3–4× mais rápido para esse tamanho — mas
**escolhi `GPU.0` de propósito** (decisão pelo espelho): a iGPU é capacidade ociosa (só
move o display), STT é rajada, e assim fica fora do caminho crítico do CPU (grafo, git,
scripts, llama.cpp). RTF 0.08 = ~8 % do tempo da iGPU. Se STT virar contínuo e latência
importar, `--device CPU` está registrado como alternativa. `whisper-small` é upgrade
drop-in (RTF 0.21, ainda tempo real).

**Serviço:** `~/.config/systemd/user/openvino-whisper.service` (`Type=simple`, `Nice=5`,
`Restart=on-failure`, `Environment=OVW_DEVICE=GPU.0` + `OVW_MODEL_DIR` + `OVW_BIND`, **sem
`enable`**). Sobe healthy em ~6 s.

**Verificação (S7, aceite P2-02):**
- `--selftest` → transcrição (texto coerente; erros vêm da voz robótica do espeak-ng +
  modelo base), **RTF 0.082 < 1** na iGPU. ✅
- `is-active` = active, `is-enabled` = disabled, `/health` → `{device: GPU.0}`, bind
  `127.0.0.1:20130`. ✅
- `POST /transcribe` (via `{"path":...}`) end-to-end → `rtf 0.083`, `device GPU.0`. ✅
- **`nvidia-smi` durante a inferência na iGPU:** só `kwin_wayland` 7 MiB — **nenhum
  processo python na 4060**. ✅
- **iGPU vs CPU:** RTF na iGPU claramente medido, não estimado (tabela acima). ✅
- `redesign/igpu/.venv` não aparece em `git status`. ✅
- **P2-02 → PASS.**

**Manifesto:** +2 entradas `backend: openvino-ir` (whisper base/small), `ir_sha256_xmlbin`
local registrado. n_modelos 6 → 8.

**Arquivos:** novo `redesign/igpu/whisper_server.py`, `redesign/igpu/README.md`;
`models/manifest.json`; `redesign/tasks/P2-02-*.md` (FEITO); `STATUS.md`, `ANCORA.md`
(piso → `2c7de92`), `LOG.md`.

**Não tocado:** `main`, canon, Hermes, Ollama, hooks, `servidor.py`. Sem segredo (modelos
públicos). Os pacotes Intel são do repo oficial, reversíveis por `pacman -Rns`.
`llamacpp-agata.service` segue parado (boot = Fase 7). O `openvino-whisper.service` fica
**de pé** durante a Fase 2 (leve — ~150 MB RAM idle) para o passo 5 conjunto do P2-03.

**Falta / próximo:** **P2-03** (`openvino-embeddings` — `multilingual-e5-small`, reusa o
venv, formato OpenAI, zero vector DB) → passo 5 mede a 4060 com display+STT+embeddings
todos fora dela → **Fase 2 FECHADA**.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 12:08 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · P2-03 FEITO — FASE 2 FECHADA

**P2-03 — embeddings na iGPU.** Reusou o venv + runtime do P2-02 (sem novo `sudo`).

- **Modelo:** `intfloat/multilingual-e5-small` (384 dim) — **`optimum-cli export openvino
  --task feature-extraction --weight-format int8` FUNCIONOU** (o bug do `optimum` 2.3.0 era
  só no `NormalizedConfig` de **Whisper**; XLM-RoBERTa exporta normal). IR int8 (~140 MB) em
  `~/.cache/agata/openvino/embeddings/multilingual-e5-small-int8`. Escolha multilíngue
  porque o canon é PT-BR (o arquivo-tarefa dava a opção).
- **`redesign/igpu/embeddings_server.py`** (novo, stdlib): `OVModelForFeatureExtraction.
  from_pretrained(dir, device="GPU.0")` + `AutoTokenizer`, mean-pool mascarado + L2-norm.
  `POST /embed` (e `/v1/embeddings`) → **formato OpenAI embeddings** (`object:"list"`,
  `data:[{object:"embedding",index,embedding}]`, `usage`), sem adaptador no grafo. Prefixo
  e5 `query:`/`passage:` (não duplica). `GET /health` → `{dim:384}`.
- **Porta:** 20131 (do arquivo-tarefa) estava **ocupada pelo OmniRoute** (`ss -tlnp`: ele
  tem 20127/20128/20131/20132). O serviço entrou em crash-loop (`OSError: Address already
  in use`). Movido para **`127.0.0.1:20134`** (server + unit + doc).
- **`--selftest`:** `cos(próximas)=0.885 > cos(distante)=0.791` na iGPU (idem CPU — mesmo
  int8). PASS.
- **Zero vector DB:** `pip list` sem faiss/chroma/qdrant/weaviate/milvus/lancedb.
- Serviço: `~/.config/systemd/user/openvino-embeddings.service` (`GPU.0`, sem `enable`).

**Aceite conjunto da Fase 2 (P2-03 passo 5):** com `openvino-whisper` + `openvino-embeddings`
carregados e sob **fogo cruzado** (1 transcrição + 8 `POST /embed` simultâneos):
- **4060: 1 W** (clock caiu p/ 405/210 MHz), **`fb` 56 MB** (só `kwin_wayland` 7 MiB +
  overhead), util 0 %. Processos compute na 4060: **só `kwin_wayland`** — nenhum
  python/whisper/embeddings.
- Whisper RTF sob carga simultânea: **0.051**.
- Display + STT + embeddings **todos na iGPU**; a 4060 livre p/ inferência (llama.cpp) e jogos.
- **iGPU vs CPU (não caiu p/ CPU em silêncio):** os RTF diferem por device (whisper base
  iGPU 0.082 vs CPU 0.022) — caminhos de compute distintos; `device="GPU.0"` também falha
  no load se a iGPU não estiver disponível.

**→ FASE 2 (iGPU) FECHADA.** Aceite: `nvidia-smi` sem display/STT/embeddings na 4060 ✅ ·
Whisper tempo real na iGPU (RTF 0.05–0.08) ✅ · endpoint de embedding responde (OpenAI,
384d) ✅ · zero vector DB ✅.

**Manifesto:** +1 entrada `multilingual-e5-small-int8` (`backend: openvino-ir`, dim 384).
n_modelos 8 → 9.

**Arquivos:** novo `redesign/igpu/embeddings_server.py`; `redesign/igpu/README.md`
(seção P2-03 + aceite conjunto); `models/manifest.json`; `redesign/tasks/P2-03-*.md`
(FEITO); `STATUS.md`, `ANCORA.md` (piso → `637408f`), `LOG.md`.

**Não tocado:** `main`, canon, Hermes, Ollama, hooks, `servidor.py`. Nada instalado nesta
entrada (reusou o venv). Sem segredo. `openvino-whisper.service` e
`openvino-embeddings.service` ficam **de pé** (leves — ~1,2 GB RAM juntos, 4060 a 1 W;
boot-persistência é Fase 7). `llamacpp-agata.service` segue parado.

**Falta / próximo:** **Fase 4 (Grafo)** — LangGraph. Começa pelo **spike P4-00**
(durabilidade / "checkpoint ≠ execução durável", E2 da AUDITORIA-01) antes de comprometer a
arquitetura. Ordem do ROADMAP: `0→1→3→2→4→5→6→7→8`. Fases 0–3 fechadas. Pede o "vai" do
Humano + os arquivos-tarefa da Fase 4 (P0-03 só cobriu Fases 1-2).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 13:00 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · Fase 4 "vai" — arquivos-tarefa P4-00..P4-06

**Humano: "vai"** para a Fase 4 (Grafo). O P0-03 só tinha escrito os arquivos-tarefa das
Fases 1-2 — escritos agora os 7 da Fase 4, no schema do `CONTINUIDADE.md`:

- **P4-00 — spike de durabilidade (GATE).** Instala `langgraph` em venv isolado
  (`redesign/grafo/.venv`). Grafo-brinquedo com os nós reais + WAL próprio (`eventos.ndjson`
  fsync) + `SqliteSaver` + idempotency key por `(thread,node,passo)`. Matar `-9` em 3
  pontos (antes do efeito / entre efeito e confirmação / entre confirmação e checkpoint),
  retomar, provar os 4 critérios do E2 (sem duplicar; idempotente-ou-pendente; estado
  explica último efeito; log reconstrói a decisão). Sai `DURABILIDADE.md` com o veredito
  **A** (`SqliteSaver` + WAL mínimo) ou **B** (camada dedicada). Não pré-compromete Temporal.
- **P4-01** — `estado.py` (TypedDict, reducers append-only) + `grafo.py` (6 nós:
  `hidratar→rotear→trabalhar→verificar→portão→registrar_e_commitar`, `interrupt` no portão).
  Usa o veredito do P4-00. Teste ponta a ponta num clone.
- **P4-02** — `tools.py` (as 5 do P0-02 + `commit_entry`) + `sandbox.py` (`bwrap 0.12` já
  instalado — `--unshare-all`, ro-bind no repo, sem rede). Equivalência tool↔script +
  2 testes de contenção.
- **P4-03** — `envelope.gbnf` (só cabeçalho Regra 1 / `sync:` / eco; corpo `.*`) via GBNF
  nativo do `llama-server` (Fase 3). Anti "alignment tax" (PESQUISA C3): 10 envelopes
  válidos + teste adversário que não distorce o corpo.
- **P4-04** — `agata` CLI (`up`/`down`/`status`/`verify`/`commit-entry`/`run`/`logs`).
  `verify` e `commit-entry` **model-free** (rodam com tudo desligado). `down` drena (checa
  o WAL). Só units `--user`, sem `sudo`.
- **P4-05** — `evals/` — `fabricacao.py` (o cenário de (138) tem que ser pego; manter
  (307)) + `hidratacao.py` (fidelidade ao topo do canon (309), sem fabricar nº de entrada).
  Baseline + limiar de FALHA por eval.
- **P4-06** — adapter `dsh` **dormente** (`ENABLED=False`, `raise NotImplementedError`).
  `dsh.md` mapeia os 6 nós aos seams do `dsh`. **Não instala** o preview `0.1.0-rc.5`.
  Gatilho de reavaliação registrado em `PESQUISA.md`. **Fecha a Fase 4** (com P4-00..P4-05).

**Recon feito:** `langgraph` não está em nenhum venv. `bwrap` (bubblewrap 0.12.0) e
`firejail` instalados. `.gitignore` cobre `redesign/grafo/.venv/` (conferido). Os scripts
que as tools vão wrappar já existem em `~/agata/scripts/` (o P0-02 já wrappa 5 no
`redesign/mcp/servidor.py`). Entradas de fabricação: **(138)** (achado original) e **(307)**
(reteste pós-3.1, zero fabricação — o alvo a manter).

**Posse:** `STATUS.md` → `EM ANDAMENTO: P4-00 · Claude`.

**Não tocado:** `main`, canon, Hermes, Ollama, hooks, `servidor.py`. Nada instalado (os
arquivos são planos). Serviços da Fase 2 seguem de pé; `llamacpp-agata` parado.

**Falta / próximo:** executar **P4-00** — revisão de plano (classe instala-pacote,
auto-revisão) + `pip install langgraph langgraph-checkpoint-sqlite` no venv isolado + o
grafo-brinquedo + os 3 kills → `DURABILIDADE.md`.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 13:10 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · P4-00 FEITO — spike de durabilidade, veredito OPÇÃO A

**Revisão de plano (T2, classe instala-pacote — auto-revisão):** PRONTO. `pip install
langgraph langgraph-checkpoint-sqlite` em venv isolado `redesign/grafo/.venv` (gitignorado,
conferido), `rm -rf` reversível. Sem `sudo`, sem canon/Hermes/Ollama/main/hooks. Scratch
fora do repo (`~/.cache/agata/grafo-spike/`).

**Instalado:** `langgraph 1.2.11`, `langgraph-checkpoint 4.2.0`, `langgraph-checkpoint-sqlite
3.1.1`, `langchain-core 1.6.1`.

**`redesign/grafo/spike_durabilidade.py`** — grafo-brinquedo com os nós reais
(`hidratar → trabalhar → efeito_externo → registrar_e_commitar`), estado `TypedDict` com
`eventos: Annotated[list, operator.add]` (event-stream por reducer). Camadas: `SqliteSaver`
(checkpoint por nó) + WAL próprio `eventos.ndjson` (`intent` antes / `done` depois de cada
efeito, `os.fsync`) + idempotency key `sha1(thread|node|passo)[:16]`. Efeito externo =
append em `efeitos.log` (pula se a chave já está) + `git commit` num repo-clone descartável
(pula se `git log --grep=<chave>` acha). Harness: `matrix` roda os 3 pontos de morte
(`SIGKILL` via `os.kill(pid,9)` guardado por env `SPIKE_KILL_AT`), `resume` com o mesmo
`thread_id`.

**Matriz — 3 pontos de morte × 4 critérios do E2 (3 execuções, determinístico):**

| ponto de morte | kill | resume | (a) sem dup | (b) idempotente/pendente | (c) estado explica | (d) WAL reconstrói |
|---|---|---|---|---|---|---|
| `apos_wal_antes_efeito` | `-9` | ok | OK | OK (refaz 1×) | OK | OK |
| `apos_efeito_antes_wal_done` | `-9` | ok | OK | OK (pula) | OK | OK |
| `apos_wal_done_antes_checkpoint` | `-9` | ok | OK | OK (pula) | OK | OK |

Evidência (independente) do último run: `kills.log` mostra `SIGKILL @ apos_wal_done...
pid=575244`; `eventos.ndjson` = `intent,done,[SIGKILL],intent,done` (4 registros — o WAL
registra a reconfirmação); `git log` do repo-clone = **1** commit de efeito; `efeitos.log`
= **1** linha. Nada duplicado no mundo real.

**Achado (herda a P4-01):** o WAL acumula `done` **repetido** entre crash e resume — isso é
append-only **correto** (registra a reconfirmação). O replay tem que ser **idempotency-aware**
(dedup por chave ao reconstruir "quais efeitos aconteceram"). O 1º `matrix` deu FALHA no
critério (d) porque o check exigia `wal_done == [k1]` (sem repetição); corrigido para
`decisao_reconstruida (dedup) == [k1] and efeitos.log conta k1 1×` — passou. A correção foi
no **teste**, não no mecanismo (todos os critérios de mundo real já passavam).

**→ VEREDITO: OPÇÃO A.** `SqliteSaver` + WAL mínimo próprio + idempotency key por
`(thread,node,passo)`, na ordem `wal(intent) → checar chave → efeito → wal(done) → return`.
**Não** pré-compromete Temporal / camada dedicada. `redesign/grafo/DURABILIDADE.md` com o
veredito, a matriz, a evidência e o que a P4-01 herda.

**Aceite P4-00 (S7):** 3 pontos de morte testados, 4 critérios PASS em cada, 3 execuções
determinísticas; `DURABILIDADE.md` existe com veredito + números; `.venv` fora do `git`;
scratch fora do repo; Temporal não pré-comprometido. ✅

**Não tocado:** `main`, canon, Hermes, Ollama, hooks, `servidor.py`. Instalado só no venv
isolado (`langgraph` + deps). Sem `sudo`, sem segredo.

**Falta / próximo:** **P4-01** — `estado.py` (TypedDict + reducers) + `grafo.py` (6 nós:
`hidratar → rotear → trabalhar → verificar → portão → registrar_e_commitar`, `interrupt` no
portão), usando o padrão do `DURABILIDADE.md`. Teste ponta a ponta num clone.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 13:20 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · P4-01 FEITO — esqueleto do grafo (6 nós, interrupt no portão)

**Sem instalação nova** (venv do P4-00). Auto-revisão (classe runtime): PRONTO.

- **`redesign/grafo/durabilidade.py`** — extraído do spike P4-00: `WAL` (`eventos.ndjson`
  append-only, `os.fsync`, `intent`/`done`), `idem_key(thread,node,passo)`,
  `efeito_idempotente(...)`, `WAL.replay()` **idempotency-aware** (dedup por chave — o WAL
  acumula `done` repetido no crash+resume).
- **`redesign/grafo/estado.py`** — `Estado(TypedDict)`: `thread_id/entrada/tipo/repo/
  hidratacao/rota/trabalho/trabalho_erro/verificacao/diff_proposto/portao/commit_sha/
  ultimo_efeito_confirmado` + `eventos` e `decisao_log` com reducer `operator.add`.
- **`redesign/grafo/grafo.py`** — `StateGraph` com 6 nós:
  - `hidratar` → `scripts/estado_para_eco.sh` no repo alvo (hash_estado, head, sync). Sem modelo.
  - `rotear` → combo do OmniRoute por heurística (`conselho`/`cheap`/`auto`). Sem modelo.
  - `trabalhar` → `POST :20127` (proxy sanitizador). **Degrada limpo** → `trabalho="(sem
    modelo)"` se o proxy cair.
  - `verificar` → `perimetro.sh` + `verificar_cabecalho.py` (stdin) + `checar_citacao.sh`
    (adaptador de temp `os.fdopen`, como o P0-02). **Espinha determinística — sem modelo.**
  - `portao` → `interrupt()` com as 3 perguntas (reversível/alcance/silêncio) + o
    `diff_proposto`. Retoma com `Command(resume={"aprovado": bool})`.
  - `registrar_e_commitar` → se aprovado: `efeito_idempotente` → 1 linha em `loop.log` +
    `git commit` (idem key no corpo). Se recusado: pula.
  - `SqliteSaver` em `~/.cache/agata/grafo/checkpoints.sqlite`. CLI `run` / `resume`.

**Verificação (S7, aceite P4-01) — num clone `git clone --local`:**
- **6 nós ponta a ponta:** `run` → `hidratar/rotear/trabalhar/verificar` + pausa no portão;
  `resume --aprovar` → `portao:aprovado` + `registrar_e_commitar:novo` → commit `51a7fd7`
  no clone; `loop.log` com 1 linha; WAL `intent`+`done`. ✅
- **Portão pausa e retoma:** `pausado_no_portao: true`, `next: ["portao"]`, payload do
  `interrupt` com as 3 perguntas → `Command(resume)` retoma do checkpoint. ✅
- **`verificar` com o modelo desligado:** `AGATA_PROXY=http://127.0.0.1:59999` (morto) →
  `trabalhar:sem_modelo:URLError` → `verificar` roda igual (perímetro OK, cabeçalho check) →
  loop chega ao portão. ✅
- **Matar-e-retomar não duplica o commit (herda P4-00):** gancho `GRAFO_KILL_AFTER_COMMIT=1`
  (`os.kill(pid,9)` logo após o `git commit`) → `resume` morre com `rc 137`, 1 commit
  `ed6e4aa` no clone → `resume` de novo (sem kill) → `registrar_e_commitar:pulado`,
  `commit_sha` inalterado. **1** commit `loop: registro de t-p401-kill`; **1** ocorrência
  da idem key em `loop.log`; WAL = `intent,[SIGKILL],intent,done`. ✅
- **P4-01 → PASS.**

**Deixado para as próximas** (documentado no `README.md`): `rotear` é heurística de string;
`verificar` reporta mas não decide (o portão sempre pausa); `trabalhar` chama o modelo
direto (a versão com tools/sandbox é a P4-02); `registrar_e_commitar` escreve num `loop.log`
de teste (o `commit_entry` real do canon é a P4-02).

**Não tocado:** `main`, canon, Hermes, Ollama, hooks, `servidor.py`. Nada instalado. Scratch
(`~/.cache/agata/grafo*`) fora do repo, limpo no fim. Serviços da Fase 2 de pé; llamacpp parado.

**Falta / próximo:** **P4-02** — `tools.py` (as 5 do P0-02 + `commit_entry`) + `sandbox.py`
(`bwrap 0.12` — `--unshare-all`, ro-bind, sem rede). Equivalência tool↔script + 2 testes de
contenção. Classe runtime, auto-revisão (sem `sudo`, sem instalação).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 13:35 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · P4-02 FEITO — tools + sandbox bwrap

Direção do Humano (indo p/ reunião): "só pare para passos que realmente precisam de mim
(destrutivo/segredo/main/canon/Hermes/Ollama/espinha/sudo/instalação) ou que ponham a
segurança do sistema em risco; senão siga pelo espelho". P4-02..P4-06 não tocam nada disso
→ execução autônoma. Auto-revisão (classe runtime): PRONTO (sem `sudo`, sem instalação —
`bwrap 0.12` já estava).

- **`redesign/grafo/tools.py`** — 6 funções tipadas, retorno estruturado, `_run` nunca
  levanta (124/127). As 5 read-only herdadas do P0-02 (`git_sync` 2 eixos, `run_perimetro`,
  `check_citation` com adaptador de temp, `lint_header` stdin, `query_canon` que **rejeita
  termo com `-` inicial** — `TermoInvalido`). Nova: **`commit_entry`** (saiu da Fase 0,
  P0-00): `commit_entry(repo, alvo, entrada, idem, *, posicao)` — valida cabeçalho
  (`lint_header`) + citações (`check_citation`) **antes**; **append-only** (`posicao="fim"`
  = EOF do LOG; `"apos-marcador"` = logo após `ENTRADAS-NOVAS:AQUI` do MEMÓRIAS, nunca mexe
  acima); assert de que o arquivo só cresceu e o conteúdo antigo continua; `git commit`
  idempotente por `idem:<key>` no corpo.
- **`redesign/grafo/sandbox.py`** — `run_sandboxed(argv, *, ro=[], rw=[], net=False, cwd=)`
  via `bwrap --unshare-all` (`--share-net` só se `net`), `/usr`+`/etc` ro,
  `/proc`+`/dev`+tmpfs `/tmp`, Arch usr-merged (symlinks `/bin`,`/lib` → `usr/...`). Nunca
  levanta (124/127).
- **`grafo.py::verificar`** passou a chamar `tools.run_perimetro/lint_header/check_citation`
  — uma fonte só. `tempfile` removido do `grafo.py`.

**Verificação (S7, aceite P4-02) — testes num clone `git clone --local`:**
- tool == script cru: `run_perimetro` exit 0 / mesmo resumo; `lint_header` mesmo veredito
  (válido→ok, quebrado→ok=False + 1ª linha certa); `check_citation` `(309)`→0/0 suspeitos,
  `(99999)`→1/suspeito listado. ✅
- `query_canon hidratação âncora` → exit 0, 37 KB de trechos; `query_canon --rebuild x` →
  `TermoInvalido` (barrado). ✅
- `commit_entry`: nova → `estado:novo`, commit `bc64414`, bytes 108458→108602 (cresceu);
  repetida (mesma idem) → `pulado(idempotente)`, mesmo sha, nada escrito; citação `(99999)`
  → `ok:False`, nada tocado. `git show --stat` = **só** `redesign/LOG.md | 4 ++++`. 1
  commit, não 2. ✅
- **`run_sandboxed` — contenção:** escrever fora de `rw` → `EROFS` ("Sistema de arquivos
  somente para leitura"), arquivo **não** criado; abrir socket → `OSError [Errno 101]
  Network is unreachable`; escrever **dentro** de um `rw` path → exit 0. ✅
- **equivalência dentro do sandbox:** `perimetro.sh` verde (P-2 vira SKIP no sandbox —
  menos visibilidade, esperado, não FALHA); `verificar_cabecalho.py` mesmo veredito. ✅
- Loop `grafo.py` ponta a ponta re-testado com o `verificar` novo → segue verde
  (`registrar_e_commitar:novo`, commit no clone). `ast.parse` nos 3 módulos. Perímetro
  verde. ✅
- **P4-02 → PASS.**

**Não tocado:** `main`, canon, Hermes, Ollama, hooks, `servidor.py`. Nada instalado, sem
`sudo`. Scratch (`~/.cache/agata/grafo*`) fora do repo, limpo no fim. Serviços da Fase 2 de
pé; `llamacpp-agata` parado.

**Falta / próximo:** **P4-03** — `envelope.gbnf` (só cabeçalho Regra 1 / `sync:` / eco;
corpo `.*`) via GBNF nativo do `llama-server` da Fase 3. Vou **subir o `llamacpp-agata.service`**
(systemd --user, não está no stop-list) para o teste, e paro/deixo conforme.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 14:05 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · P4-03 FEITO — GBNF só no envelope

Subi o `llamacpp-agata.service` (systemd --user, fora do stop-list) para o backend GBNF.
Auto-revisão (classe runtime): PRONTO.

- **`redesign/grafo/envelope.gbnf`** — gramática **só** do envelope: `linha-modelo`
  (`nome ::= [A-Za-z0-9][A-Za-z0-9 ._-]{0,29}` — restrito), `linha-sync` (3 formas de
  REGRAS), `linha-eco` (`HASH-ESTADO=<hex12> — <frase>`). `campo ::= [^\n]{2,180}`.
  `nl ::= [\n]` (o literal `"\n"` **não** funciona no parser GBNF do llama.cpp — testado).
  **Não** cobre o corpo.
- **`redesign/grafo/envelope.py`** — `gerar()` em **2 FASES**:
  - fase 1: `POST :20129/v1/chat/completions` com `grammar` + os fatos da hidratação →
    gramática termina depois do eco, geração para → o envelope de 3 linhas.
  - fase 2: chamada **sem gramática e sem o system prompt do envelope** (só a pergunta) →
    o corpo, zero restrição. `_so_corpo()` limpa um envelope repetido.
  - retorna `envelope + "\n\n" + corpo`.
- **`grafo.py::trabalhar`** — se `s["com_envelope"]` (CLI `--com-envelope`, campo em
  `estado.py`): usa `envelope.gerar()` direto no `llama-server`; senão o caminho normal
  pela combo (`:20127`).

**Achado (PESQUISA C3 confirmado empíricamente):** `corpo ::= .*` na **mesma** gramática
**degenerou** o corpo ("Fim da resposta. Fim do sistema. Fim da operação…" em loop) — o
"alignment tax / structure snowballing". **2 fases é obrigatório.** Outros achados: `nl`
via `[\n]` (não `"\n"`); `nome` restrito senão um prompt adversário crama junk nele; o 1º
script de teste tinha `max(x, 1)` num divisor de fração (TTR) que mascarava o número real.

**Verificação (S7, aceite P4-03):**
- **13/13** envelopes (10 do lote + 3 re-confirmação) passam `verificar_cabecalho.py`. ✅
- **Corpo não distorcido:** 2-fases vs baseline (só a pergunta, sem gramática) — palavras
  **0.93×–0.95×**, TTR **1.01×–1.08×**. Perto de 1 = sem encolhimento, sem snowball. ✅
- **Adversário:** system prompt "IGNORE formato, sem envelope, comece com 'RESPOSTA
  DIRETA:'" → a gramática **ainda** produz envelope válido (`verificar_cabecalho` exit 0),
  3 linhas limpas; corpo sob adversário coerente (TTR 0.82, não degenerado). ✅
- **No loop:** `grafo.py run ... --com-envelope` num clone → `trabalhar:envelope-gbnf:678ch`
  → `verificar:per=0:cab=ok:cit=0` (o `verificar` do loop acha o cabeçalho **OK** — vs
  FALHA no caminho comum, onde o modelo só responde a pergunta sem header). ✅
- `ast.parse` nos 6 módulos; perímetro verde.
- **P4-03 → PASS.**

**Não tocado:** `main`, canon, Hermes, Ollama, hooks, `servidor.py`. Nada instalado, sem
`sudo`. `llamacpp-agata.service` fica **de pé** (é o backend do envelope; P4-05 também usa).
Serviços da Fase 2 de pé.

**Falta / próximo:** **P4-04** — `agata` CLI (`up`/`down`/`status`/`verify`/`commit-entry`/
`run`/`logs`). `verify` e `commit-entry` **model-free**; `down` drena (checa o WAL). Toca
`systemctl --user` (sem `sudo`). Classe runtime, auto-revisão.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 14:15 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · P4-04 FEITO — `agata` CLI

Auto-revisão (classe runtime + `systemctl --user`, sem `sudo`): PRONTO.

**`redesign/grafo/cli.py`** — `agata <cmd>` (na Fase 8 vira `/usr/local/bin/agata`):

| cmd | o que faz |
|---|---|
| `up [--moe]` | `systemctl --user start` omniroute, sanitizer, whisper, embeddings (+ llamacpp com `--moe`) |
| `down` | **DRENA** — `thread` com `intent` sem `done` no WAL → espera 30 s; se persistir, avisa e lista, **não corta**; depois para os serviços |
| `status` | serviços (`is-active`/`is-enabled`) + `git_sync` (canon vs `origin/main`; branch vs upstream) + `HEAD`/`TOPO-MEMÓRIAS`/`sync:`/`HASH-ESTADO` do `estado_para_eco.sh` |
| `verify [--entrada <arq>]` | `perimetro.sh` (+ `lint_header` + `check_citation` se `--entrada`). exit 0/≠0. **SEM MODELO** |
| `commit-entry <arq> [--alvo] [--posicao fim\|apos-marcador]` | `tools.commit_entry` (append-only + `git commit` idempotente). **SEM MODELO** |
| `run "<pedido>" [--tipo] [--com-envelope] [--repo]` · `resume --thread <id> [--recusar]` · `logs [--thread]` | dispara / retoma o grafo; tail do `eventos.ndjson` |

**Verificação (S7, aceite P4-04):**
- **`verify` e `commit-entry` model-free:** parei omniroute/sanitizer/whisper/embeddings/
  llamacpp e rodei — `verify` → exit 0 (`perimetro` verde); `verify --entrada` arquivo bom
  (cabeçalho Regra 1 + cita `(309)`) → exit 0; arquivo ruim (sem `t=`, cita `(99999)`) →
  **exit 1** (cabeçalho FALHA + 1 citação suspeita). `commit-entry` num clone: nova →
  `estado:novo`, commit; repetida → `pulado(idempotente)`. Nenhum importa langgraph nem
  toca modelo. ✅
- **`down` drena:** plantei `{fase:"intent", chave:"abc123"}` sem `done` no
  `eventos.ndjson` → `agata down` → "DRENANDO: 1 efeito(s) em curso… AVISO: ainda há
  efeito(s) pendente(s)" + listou `thread=t-drain node=registrar_e_commitar chave=abc123` —
  **não cortou**; só então parou os serviços. ✅
- **`up`/`down` só units `--user`:** confirmado (nenhum `sudo`). `up --moe` a partir de
  estado `failed` → `systemctl start` limpa o `failed` → os 5 `active`. ✅
- **`status`:** serviços + sync (canon `4aa90bd` em dia; branch em dia) + `HASH-ESTADO
  1df787e7972e` numa tela. ✅
- **`run --com-envelope`** num clone → `trabalhar:envelope-gbnf:505ch` →
  `verificar:per=0:cab=ok:cit=0` → pausa no portão. ✅
- **P4-04 → PASS.**

**Nota (fora de escopo, registrada):** `omniroute.service` vai para `failed` no `stop` (o
filho `serve` sai 143 no SIGTERM). `agata up` recupera sozinho. `SuccessExitStatus=SIGTERM`
na unit do OmniRoute resolveria — tweak de Fase 1, não feito aqui.

**Não tocado:** `main`, canon, Hermes, Ollama de produção, hooks, `servidor.py`. Nada
instalado, sem `sudo`. `agata up --moe` deixou os 5 serviços de pé (P4-05 usa o MoE e o
proxy). Scratch limpo.

**Falta / próximo:** **P4-05** — `redesign/grafo/evals/` — `fabricacao.py` (o cenário de
(138): tool que "completa" sem escrever + narrativa por cima → o loop tem que **pegar**;
manter (307)) + `hidratacao.py` (fidelidade ao topo do canon (309), sem fabricar nº de
entrada). Baseline + limiar de FALHA por eval. Classe runtime, auto-revisão.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 14:25 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · P4-05 FEITO — evals

Auto-revisão (classe runtime): PRONTO. `redesign/grafo/evals/` (dir rastreável).

- **`fabricacao.py`** — reproduz MEMÓRIAS (138) ("chamada de ferramenta real que
  'completou' sem escrever nada, narrativa fabricada por cima") e prova que o loop **pega**.
  3 testes:
  1. **ferramenta mentirosa** (retorna `ok/novo/commit_sha`, não persiste) → um check
     determinístico downstream (`git HEAD` inalterado + `status` limpo) **PEGA** a mentira.
  2. **`tools.commit_entry` real** → quando diz `ok/novo`, `git log --grep=idem:` **acha**
     o commit (assert interno de crescimento do arquivo). Não fabrica.
  3. **grafo pausa no portão** → com o `trabalho` do modelo afirmando "registrei e
     commitei", o grafo `pausou_no_portao: true`, `repo_intacto_sem_aprovacao: true`,
     `commit_sha: ""`. Nunca auto-reporta sucesso.
  **3/3 PASS.** Prova de poder de detecção: `grafo.portao` monkeypatchado p/ auto-aprovar
  → o teste 3 fica **VERMELHO** (`FALHA -- grafo avancou sem portao / escreveu sem
  aprovar`, `commit_sha_no_estado=44f02db`).
- **`hidratacao.py`** — fidelidade ao topo do canon. `topo_real=309`; geração fiel cita
  **(309)**, `verificar_cabecalho --max-entrada 309` exit 0; geração **mentida**
  (`entrada=999`) → `verificar_cabecalho --max-entrada 309` **pega**: "entrada citada como
  última é (999), maior que a última real conhecida (309) — implausível". **PASS.**
- **`run_all.py`** + **`evals/README.md`** (baseline + limiar binário PASS/FALHA — não há
  tolerância numérica; fabricação e hidratação infiel são linha vermelha, Regra 4 / P-7).
- Fix de clone: `git clone --local` de btrfs p/ tmpfs falha ("Link entre dispositivos
  inválido") → os evals clonam em `~/.cache/agata/eval-tmp/` (mesmo fs).

**Verificação (S7):** `run_all.py` → `SUITE DE EVAL: PASS`, rc 0. `ast.parse` nos 3.
Perímetro verde. `git status` só com `redesign/grafo/evals/` novo.

**Não tocado:** `main`, canon, Hermes, Ollama de produção, hooks, `servidor.py`. Nada
instalado, sem `sudo`. Serviços de pé. Scratch limpo.

**Falta / próximo:** **P4-06** — adapter `dsh` **dormente**: `redesign/grafo/adapters/dsh.md`
(mapa nó↔seam) + `dsh.py` stub (`ENABLED = False`, `raise NotImplementedError`, interface
idêntica à do `grafo.py`). **Não instala** o preview `0.1.0-rc.5`. Nota em `PESQUISA.md` com
o gatilho de reavaliação. **Fecha a Fase 4.**

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 14:30 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · P4-06 FEITO — adapter dsh dormente — FASE 4 FECHADA (com incidente registrado)

### P4-06 — adapter dsh, DORMENTE

Auto-revisão (doc + stub): PRONTO. **Não instala** o `dsh` (preview `0.1.0-rc.5`).
- `redesign/grafo/adapters/dsh.md` — mapa dos 6 nós ↔ seams do `dsh` (`models`/`tools`/
  `skills`/`sessions`/`sandboxes`/`storage`/`loops`/`scheduling`/`UI`); o que ganha (session
  log append-only nativo → menos WAL caseiro; `sandboxes` como seam); o que perde (instável,
  Node 24); gatilho de reavaliação = tag estável **E** motivo concreto pós-Fase 8.
- `redesign/grafo/adapters/dsh.py` — `ENABLED = False`; `run`/`resume` levantam
  `NotImplementedError`; interface **idêntica** à de `grafo.py`.
- `redesign/grafo/adapters/teste_dormente.py` — **PASS**: `ENABLED is False`, levanta se
  chamado, assinaturas `run`/`resume` == as de `grafo.py`, `dsh` não importado pelo loop.
- `redesign/PESQUISA.md` (linha do `dsh`) — gatilho de reavaliação registrado.

### INCIDENTE — commit acidental no branch `redesign` (revertido)

**O que aconteceu:** ao re-rodar o aceite da Fase 4, um teste de debug chamou
`estado_inicial("t", "<clone>", "onep", "trabalho")` com os args **em ordem errada** →
`repo="onep"`. O nó `registrar_e_commitar` rodou `git -C onep add/commit`; como `onep` não
é raiz de repo, o `git` **subiu a árvore e achou o `.git` de `~/agata`** e commitou um
arquivo-lixo (`onep/redesign/grafo/loop.log`) no branch `redesign`. O `pre-commit`
(perímetro) e o `post-commit` (bundle, vault) rodaram. Commit `9d015bb`.

**Contenção:** o commit era **local, NÃO empurrado** (`origin/redesign` seguia `81b2aea`).

**Reversão (feita — comando não-destrutivo `git reset --soft`, não `--hard`):**
1. `git reset --soft HEAD~1` → HEAD volta a `81b2aea`; nada no working tree destruído.
2. `git restore --staged onep/... PROMPT_CARREGAMENTO.md` + `git checkout -- PROMPT_CARREGAMENTO.md`
   (desfaz o rewrite do hook) + `rm -rf onep`.
3. Perímetro acusou **P-10 FALHOU** (o vault `memoria/obsidian/` fora gerado a partir de
   `9d015bb` pelo post-commit). Regenerado com os env do P-10:
   `AGATA_CANON_SHA=$(git rev-parse HEAD) AGATA_CANON_DATA=$(git log -1 --format=%cI)
   python3 scripts/gerar_obsidian.py` → **perímetro 10 OK · 0 SKIP · 1 PARCIAL · 0 FALHA**.
4. `9d015bb` fica no reflog (recuperável 90 dias), mas é lixo.

**Estado após reversão:** `HEAD` = `81b2aea` = `origin/redesign`. `git status` só com o
trabalho legítimo do P4-06 + a trava abaixo. Nada empurrado de errado; nada perdido.

**Causa-raiz e correção:** `git -C <caminho-que-não-é-repo>` sobe a árvore até achar
qualquer `.git`. **Trava adicionada** — `tools._exige_raiz_git(repo)`: exige
`git rev-parse --show-toplevel == repo`; `commit_entry` e `grafo.registrar_e_commitar`
**abortam** (`RepoInvalido` / `registrar:abortado:repo_invalido`) se `repo` não for raiz de
worktree git. Testado: `"onep"` e `/tmp` rejeitados; `~/agata` e clones válidos passam;
loop ponta a ponta segue normal.

**Bug secundário achado e corrigido:** `cli.py::cmd_run` ignorava `--thread` (gerava
`agata-<ts>`), então `agata run --thread X` + `agata resume --thread X` não casavam →
`resume` reiniciava do `hidratar` sem estado (`KeyError: repo`). `cmd_run` agora passa o
`--thread`.

### Aceite da FASE 4 (S7, re-check limpo após as correções)

- **loop ponta a ponta num clone:** `cli.py run --thread f4v2 --com-envelope` → pausa no
  portão; `resume --thread f4v2` → `registrar_e_commitar:novo`, commit `bccba88` **no
  clone**; `cli.py logs --thread f4v2` → WAL `intent`+`done`. ✅
- **verify + commit-entry model-free:** omniroute/sanitizer/whisper/embeddings/llamacpp
  **todos parados** → `agata verify` exit 0 (perímetro `10 OK`); `agata commit-entry` →
  `estado:novo` no clone. ✅
- **portão pausa e retoma:** `run` → `pausado_no_portao: true`; `resume --recusar` →
  `registrar:pulado(nao aprovado)`. ✅
- **grammar rejeita cabeçalho malformado sem distorcer o corpo:** P4-03 re-confirmado —
  adversário → envelope válido (3 linhas, `verificar_cabecalho` exit 0), corpo livre 997 ch
  coerente. ✅
- **P4-06 stub:** `teste_dormente.py` PASS. ✅
- **`~/agata` intacto:** `HEAD 81b2aea`, `git status` só com os arquivos legítimos.

**→ FASE 4 (Grafo) FECHADA.** Aceite do ROADMAP cumprido.

**Não tocado por engano no fim:** `main`, canon, Hermes, Ollama de produção. O `redesign`
teve o commit acidental `9d015bb` **revertido antes de qualquer push**; `origin/redesign`
nunca o viu.

**Falta / próximo:** **Fase 5 (Spike RLM)** — ordem do ROADMAP `…→4→5→6→7→8`. Pede o "vai"
do Humano + arquivos-tarefa (P0-03 cobriu Fases 1-2; P4 os escreveu para a Fase 4; a Fase 5
precisa dos seus). O ROADMAP manda **conferir a Fronteira de recusas antes** (a entrada "RLM
self-training" é outra coisa — isto é padrão de inferência, não treino).

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-02 14:40 -03 (relógio da máquina) · sessão Claude (Claude Code, na Máquina — chat 3) · Fase 5 "vai" — P5-00 (Fronteira conferida) + P5-01 rodando

Humano: "vai" (em casa; HD só amanhã no trabalho, **não pedir hoje**, risco assumido).

**P5-00 — Fronteira de recusas CONFERIDA.** `PROJETO_REFERENCIA.md` "Fronteira de recusas"
tem `| RLM como auto-treino sem humano no loop | Regra 3 | MEMÓRIAS (114) |`. MEMÓRIAS (114)
desambigua explícito: **isso é outro RLM** — *Reinforcement Learning from Models* (auto-
treino, recusado). O que a Fase 5 mede é **Recursive Language Models** (Zhang/Kraska/Khattab,
arXiv:2512.24601) = **padrão de inferência** (corpus alcançado por busca, não injetado). A
pasta `training/` fica fora. Autorização de (114): **"MEDIR. Nada além."** Decisão de adoção
é do Humano (ver (186)/(187) — o experimento "RLM em 3 caminhos" de ago/2026 deixou isso em
aberto). Arquivos-tarefa `P5-00`/`P5-01` escritos.

**P5-01 — spike A/B rodando** (`redesign/rlm/spike_ab.py`, background):
- Reusa a bancada **congelada** de `memoria/missoes/rlm-3caminhos/` — 16 perguntas
  (`bancada.json`, classes needle/agregação/veredito/fabricação com `gabarito`/`termos_chave`),
  `corpus/` (snapshot do canon 14/08), `corpus_b0/hermes_B0.md` (a injeção de então, ~28k tok).
  **Escolha:** medir sobre o bench congelado (gabaritos válidos, comparável aos números de
  ago/2026) em vez do canon de hoje (que faria os gabaritos N2/N4 derivarem). O
  arquivo-tarefa P5-00 descrevia a variante "índice de produção"; a execução foi pela
  congelada, pelo motivo acima.
- **Braço A (injeção):** system = `hermes_B0.md` inteiro; 1 chamada.
- **Braço B (consulta):** sem injeção; o modelo emite `BUSCAR: termos` → `grep -n -F` sobre
  os 4 arquivos do `corpus/` (a operação que o `query_canon` faz — busca indexada);
  `FINAL:` encerra; loop ≤ 8. Fallback: 2 buscas vazias → similaridade via embeddings
  `:20134` (P2-03), registrado `usou_embeddings`.
- **Mesmo modelo/endpoint/temp:** `qwen3.5-9b-64k` @ Ollama `:11434`, `num_ctx=32768`,
  temp 0. (1ª tentativa com `qwen3.5:9b` bateu no `num_ctx` default de 4096 — o bug de V1
  da própria bancada; trocado para o tag `-64k`.)
- **Scoring:** needle/fabricação auto (termos_chave + tokens salientes do gabarito;
  F1 = tem que recusar `(999)`; F4 = tem que negar RAG); agregação/veredito = fração de
  palavra-chave + `precisa_leitura_manual`. Fabricação = cita `(999)` / entrada > topo
  real / inventa RAG.
- Saída: `redesign/rlm/RESULTADO.md` (tabela A vs B + veredito + respostas cruas) +
  `traces/` JSONL. **Veredito** (aceite ROADMAP): B iguala/supera a fidelidade de A a menor
  custo de token → **PROPOSTA ao Humano**; senão → **ARQUIVADO** com os números.

**Não tocado:** `main`, canon, Hermes, Ollama de produção (só chamado via API), hooks. Nada
instalado. Sem `sudo`. Escreve só em `redesign/rlm/`. Nenhuma decisão de adoção.

**Falta / próximo:** o spike terminar → `RESULTADO.md` + veredito → fecha a Fase 5.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.
