# Dossiê — Seleção do silo por modelo no gateway (LACUNA de MEMÓRIAS (305))

**Read-only. Não decide nada. Insumo da Camada A da sub-cadeia de seleção.**
**SEM `APROVADO-`.**

- Sessão de Máquina, 31/08/2026, continuação de (307). Autorização do Humano:
  "todos na ordem que fizer mais sentido" (31/08) — lida como autorização de
  **preparar insumo read-only**, não de ser Camada A nem de tocar canon.
- Base: canon HEAD `e250672` (MEMÓRIAS (307)). Vendored `~/.hermes/hermes-agent/`
  — fora do repo, sem backup, mesma classe de risco do patch 429 (PROJETO.md).
- Método: leitura de código no vendored + `git`/`grep` na Máquina. Zero escrita
  fora deste arquivo.

---

## 1. O que (305) deixou pronto e o que ficou faltando

**Pronto (aplicado em (305), no canon):** `.githooks/gerar-hermes-md.sh` gera, a
cada commit, `.hermes.md` (comum) **e** quatro silos `.hermes-<modelo>.md` para
`ALVOS_SILO=(claude seth gemini glm)`, na **raiz do repo**. Silos gitignorados
(`.hermes-*.md`), P-11 barra `git add -f` de silo. Verificado nesta sessão:
os cinco arquivos existem na árvore (`.hermes.md` + 4 silos, ~141 KB cada),
`git check-ignore` confirma silo ignorado e `.hermes.md` não.

**Faltando (a LACUNA, registrada em (305) e no ONDE_ESTAMOS):** nenhum modelo
recebe o próprio silo. O Hermes injeta sempre o `.hermes.md` comum. Os silos são
peso morto até existir o mecanismo de entrega — e é isso que este dossiê mapeia.

---

## 2. Por que o Hermes hoje só entrega o `.hermes.md` comum

`agent/prompt_builder.py`:
- `_HERMES_MD_NAMES = (".hermes.md", "HERMES.md")` — **nome fixo**. Sem env var,
  sem chave de config para trocar (procurado: só `HERMES_HOME`, que é do `SOUL.md`).
- `_find_hermes_md(cwd)` procura a partir do **cwd**, subindo até a raiz do git,
  devolve o primeiro match. `.hermes-claude.md` **nunca casa** — o glob é nome
  literal, não prefixo.

`agent/runtime_cwd.py`:
- `resolve_context_cwd()` (usada pela descoberta de context-file, via
  `agent/system_prompt.py:161/613`) checa `_SESSION_CWD` (ContextVar) **primeiro**,
  depois `TERMINAL_CWD`, depois nada (cai no launch dir).
- `set_session_cwd(cwd)` grava esse ContextVar.

`gateway/run.py` — **o ponto exato da lacuna:** `_set_session_env()`
(≈ linha 23020) chama `set_session_vars(platform=…, profile=…, async_delivery=…,
cron_session="")` — **sem passar `cwd`**. Então `set_session_cwd` recebe o default
(vazio), `_SESSION_CWD` fica `""`, e `resolve_context_cwd()` cai no `TERMINAL_CWD`
global — **o mesmo diretório para todo modelo**. Confirmado lendo os parâmetros
passados na chamada (não há `cwd=` na lista).

`profile` **é** propagado: `set_session_vars` grava `_SESSION_PROFILE`
(`gateway/session_context.py:275`). E `agent/system_prompt.py:165` lê
`get_active_profile_name()` de `hermes_cli.profiles`. Ou seja: **existe um
identificador de sessão que chega ao build do system prompt** — só não está
ligado à escolha do arquivo de contexto.

---

## 3. Três mecanismos de entrega — nenhum verificável só medindo (Regra 8)

### Opção A — rota por cwd de sessão (sem patch vendored)
Gateway passa um `cwd` por modelo a `set_session_vars`; cada `cwd` é um diretório
(ex.: `~/agata/silos/<modelo>/`) que contém um arquivo **literalmente chamado
`.hermes.md`** que É o silo daquele modelo (symlink para `../../.hermes-<modelo>.md`,
ou o hook grava direto lá). `_find_hermes_md` acha o do cwd antes de subir para a
raiz e pegar o comum.
- **Prós:** zero toque no código vendored (imune a `hermes update`). Usa gancho
  nativo (`_SESSION_CWD`).
- **Contras:** exige mudar `gateway/run.py` (`_set_session_env`) — que **é**
  vendored. Exige o gateway saber, por sessão, qual é o `<modelo>` (ver §4).
  Muda o cwd efetivo da sessão inteira, não só o context-file: efeito colateral
  em ferramentas que usam `resolve_agent_cwd()` (terminal, edição de arquivo) —
  **precisa de teste**, pode ser indesejável ("claude" editando em `silos/claude/`).
- **Variante A':** `resolve_context_cwd()` e `resolve_agent_cwd()` são funções
  distintas. Um patch mínimo que separe "cwd de contexto" de "cwd de trabalho"
  evitaria o efeito colateral — mas aí já é patch vendored (vira Opção B).

### Opção B — patch vendored em `_HERMES_MD_NAMES` / `_find_hermes_md`
Fazer `_find_hermes_md` preferir `.hermes-<profile>.md` (ou `<modelo-alvo>`) quando
o identificador de sessão é conhecido, caindo em `.hermes.md` senão.
- **Prós:** cirúrgico, ~10 linhas, sem mexer no gateway nem em cwd.
- **Contras:** **vendored, sem backup, `hermes update` apaga em silêncio** — a
  mesma dívida do patch 429 (PROJETO.md, "Estado dos bugs"). Precisaria entrar na
  lista de "reverificar após update" e, idealmente, num mecanismo de
  versionamento de patches vendored que **não existe hoje** (checado:
  `scripts/` não tem nada de patch/vendor; nenhum `patches/`).

### Opção C — hook de contexto por modelo
Um hook (`pre_api_request` / equivalente) que, sabendo o modelo, troca o bloco de
context-file já montado pelo silo certo antes do envio.
- **Prós:** mecanismo de hook é nativo (`~/.hermes/config.yaml` `hooks:`), sem
  editar fonte do Hermes — igual ao que a proposta `harness-a1-trace` usa.
- **Contras:** o hook recebe o `system_prompt` **já montado** (achado de (159));
  reinjetar o silo certo = recortar e recolar o bloco de contexto no prompt, mais
  frágil que A ou B. Ordem dos hooks e reentrância a verificar.

---

## 4. Buraco comum às três opções: qual string identifica o modelo?

`ALVOS_SILO=(claude seth gemini glm)` são valores de `modelo-alvo:` de blocos MOD,
**escolhidos pelo roteiro/dossiê S1** — não se confirmou que sejam iguais ao
`profile` do Hermes nem ao nome do provider/modelo real.

- O que o gateway tem por sessão: `_SESSION_PROFILE` (string `profile`) e o
  provider/modelo do `config.yaml` (`model.default: qwen3.5-9b-64k`,
  `model.provider: custom:qwen-local-ctx-override`; `fallback_model` inclui
  `gemini`).
- O `config.yaml` desta Máquina **não** mostra profiles nomeados `claude`/`seth`/
  `gemini`/`glm` (grep não achou). Provável que os modelos do Conselho na nuvem
  entrem por **outra rota** (adapter/canal), não por profile local.
- **Pergunta pra Camada A:** existe, hoje, no gateway, uma sessão distinta por
  modelo do Conselho, com identificador estável? Se não, a seleção de silo não
  tem em que se apoiar e o Bloco vira "primeiro criar a identidade de sessão por
  modelo, depois a seleção".

---

## 5. O que a sub-cadeia de seleção precisa entregar

1. **Emenda ao `roteiro-fase2.md`:** a seleção estava dobrada no Bloco 3.1;
   (305) adiou-a explicitamente. Vira **sub-bloco próprio (3.1-b)** com cadeia
   A/B/C completa — não é o Bloco 3.2 (eco pós-carregar).
2. **Camada A** (sessão independente — **não esta**, que leu este dossiê):
   escolher entre A/B/C do §3 com Regra 8 (três passadas), resolver o §4,
   produzir `.diff` + `APROVADO-` e testar em clone descartável **com evidência
   preservada no disco** (a Camada C do v1 de 3.1 reclamou que os testes de clone
   não deixaram rastro).
3. **Camada B:** sessão separada — o silo entregue não vaza MOD alheio? o comum
   continua sem MOD com `modelo-alvo:`? o efeito colateral de cwd (Opção A) foi
   medido?
4. **Camada C na Máquina:** `grep` no `.hermes-*.md` gerado e no que o gateway
   realmente injeta (capturar system prompt efetivo), `git`/`hash`, não contra o
   texto de A/B.
5. **Humano decide → aplica+push → S7** (confirmação pós-push por sessão
   independente do executor).

---

## 6. Dependências

- **Bloco 3.3 (TES-002 com nonce novo) depende disto aplicado.** Sem entrega real
  do silo, o nonce vazaria no `.hermes.md` comum. `roteiro-fase2.md` já registra
  a dependência; ela agora aponta para o 3.1-b, não para o 3.1 genérico.
- Não bloqueia o **Bloco 3.2** (eco pós-carregar), que toca `scripts/*` e é
  independente.

---

**Rascunho read-only. Sem `APROVADO-`. Não autoriza nada.** Cada opção do §3
ainda passa pelo portão das três perguntas e pela cadeia de auditoria em camadas
antes de virar `APROVADO-<nome>`.
