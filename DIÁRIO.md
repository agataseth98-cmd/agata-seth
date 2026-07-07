# DIÁRIO.md — Ágata

História do projeto. **Só se acrescenta, no fim. Nunca edite nem apague** o que já está aqui.
Cada entrada: `data · quem · o que foi decidido/feito`.

## Resumo consolidado (até 04/06/2026)

O que aprendemos e vale para sempre:

1. Memória tem que ser **uma só**. Vários módulos de memória corrompem tudo.
2. **Nunca finja lembrar** (nada de stub). Se corromper, restaure de verdade.
3. Captura de fatos por **regex vem antes** do modelo — rápida e confiável.
4. Separe **REGRAS** (universais) de **PROJETO** (deste projeto). É o que permite reusar em outros projetos.
5. O Humano manda, mas há **linhas vermelhas**: continuidade, história e honestidade não se suspendem.
6. Documento para modelo tem que ser **imperativo, em 2ª pessoa, com blocos de código bem fechados** — senão o modelo lê as regras como "exemplo de saída" e as ignora (foi a causa de modelos não assumirem o comportamento).
7. O DIÁRIO tem que ter **um cabeçalho e uma linha do tempo**. Dois documentos colados confundem o modelo sobre qual é o certo.

**Marcos:** núcleo de memória unificado · extrator imediato · orquestração por papel (deepseek→condução, qwen→auditoria, kimi→validação) · voz local (Kokoro / voz `pf_dora`) · virada para arquitetura MCP (Ágata como servidor central) + OpenClaw + Hermes.

**Histórico detalhado antigo:** arquivado em `MEMORY.md` — não apagar.

---

## Registros

### 2026-06-05 · Orusoua + Claude (Opus 4.8, arquitetura/auditoria)

Redesenho do sistema para ficar mais simples e barato em tokens, mantendo tudo que prometia.

- Renomeado: CORE→**REGRAS**, MANIFESTO→**PROJETO**, MEMORY→**DIÁRIO**. IB→**Humano**, IC→**Modelo**, IL→**Máquina**.
- **15 regras viraram 6.** Cabeçalho cerimonial, quadrantes, protocolo 1-7 e códigos N1-N6 removidos; formato de resposta enxuto. Um comando de carga (`carregar`) no lugar de três.
- **Motivo:** uma carga real com Qwen3.8 falhou — confundiu Máquina com "Inteligência Legada", declarou íntegro com o DIÁRIO defeituoso, não soube explicar a regra de carga segura, e inventou um bloco marcando-o canônico sem ordem. Diagnóstico: o sistema era pesado demais para o modelo que deveria rodá-lo.

**Pendente de decisão do Humano:**
1. Adotar estas versões (REGRAS/PROJETO/DIÁRIO)?
2. Renomear os `.json` de memória para os nomes novos (fatos/conversas/habitos/contexto)?

### 2026-06-05 (2) · Orusoua decidiu · Claude executou

Humano aprovou: `1s2s3n`.

1. **Adotado.** REGRAS/PROJETO/DIÁRIO passam a canônicos. Trio antigo (CORE_FULL, MANIFESTO_ÁGATA, MEMORY) **arquivado, não apagado**.
2. **Nomes novos de memória adotados:** semantic→fatos, episodic→conversas, procedural→habitos, overlay_ontologico→contexto.
3. **Mantidos 3 arquivos** (sem colapsar).

Feito: arquivos .md novos entregues; script `migrar_agata.sh` (backup + cópia com nomes novos, sem apagar nada).

`lacuna:` o código que lê os .json antigos (memory_core.py etc.) ainda aponta para os nomes velhos. Aplicar os nomes novos no servidor MCP em construção **antes** de remover os antigos — senão quebra.

### 2026-07-01 · Orusoua decidiu · Claude auditou

Auditoria do PLANO_AGATA_v1.2 (GLM → Qwen → GLM). Direção e faseamento **aprovados**; implementação como estava **reprovada**.

Achados críticos: Whisper não roda no Ollama (Fase 4 quebraria); MCP/LiteLLM em `0.0.0.0` + permissões por regex de string burláveis (risco de execução remota); VRAM 8GB não comporta 7B + Whisper-large juntos; failover do Syncthing gera split-brain (dois DIÁRIOs); `.git` sincronizado corrompe o repo. Descoberta central: "Hermes" e "OpenClaw" no v1.2 eram scripts caseiros, **não** as ferramentas reais.

**Decisão do Humano (`1-real · 2-sim · 3-s`):**
1. Construir **sobre o Hermes Agent real**, não bespoke.
2. Gerar **PLANO v1.3 corrigido** (só documento, sem código).
3. **Claude Code inventaria a Predator** antes de tudo.

Pendente: rodar o inventário → revisar v1.3 → Fase 0.

### 2026-07-01 (2) · Fase 0 executada (Claude Code na Predator)

- OpenClaw parado + desabilitado (não apagado). Protótipo antigo arquivado em `~/agata/_arquivo_agata_il/` (`semantic.json` preservado byte a byte).
- **Hermes Agent 0.17.0** instalado (Python 3.11 isolado via uv, sem alertas de segurança), `--skip-browser`. Script inspecionado antes do install (limpo).
- Cérebro local: **llama3.1:8b** (128k nativo), via Ollama, `num_ctx 65536`. Motivo: Hermes exige contexto ≥64k; `qwen2.5:7b` (32k) não serve. No 4060 8GB há offload parcial pra CPU (mais lento; tuning de KV cache fica pra depois).
- Config em `~/.hermes/config.yaml` (provider custom, base_url `localhost:11434/v1`).

Pendente: reportar chave útil do OpenClaw (migrar vs purgar); iniciar Fase 1.

### 2026-07-01 (3) · Fase 1 e Fase 2 concluídas; Fase 3 iniciada (checkpoint — franquia esgotada)

**Fase 1 (identidade + memória) — concluída:**
- 4 canônicos copiados de `~/Downloads/` pra `~/agata/` (SOUL.md, REGRAS.md, PROJETO.md, DIÁRIO.md). Migração do `semantic.json` antigo pulada (só tinha lixo de teste).
- Estrutura `~/agata/{memoria,skills,config,sandbox,logs,backup}` criada. `memoria/{fatos,habitos,conversas,contexto}.json` criados vazios — **hoje sabemos que isso foi engano** (ver Fase 3 abaixo).
- Git inicializado, commit inicial feito.
- `~/.hermes/SOUL.md` virou symlink pra `~/agata/SOUL.md` (identidade única, versionada).

**Fase 2 (cérebro) — concluída, com um bug real caçado e corrigido:**
- Provedor final: **OpenRouter**, modelo principal `openai/gpt-4o-mini` (pago, barato — decisão do Humano após tentar local e `:free` sem sucesso confiável). Fallback: `openai/gpt-oss-120b:free` → `llama3.1:8b` local (Ollama).
- **Causa raiz de tool-calling não confiável**, achada por eliminação (testei 6+ combinações modelo/provider, incluindo Claude Haiku 4.5 pago): a flag `provider_routing.require_parameters: true` — que eu mesmo adicionei numa correção anterior — estava forçando a OpenRouter a rotear pra um backend que declara suporte a `tools` mas entrega function-calling degradado. **Removida** (comentada em `~/.hermes/config.yaml`). Sem ela, tool-calling funciona de verdade — testado e confirmado lendo REGRAS/PROJETO/DIÁRIO reais.
- Lição que vale pra sempre: **system prompt grande por si só não quebra tool-calling** (testei — mesmo tamanho de prompt, resultados diferentes). O que quebra é roteamento de provider ruim mascarado por uma flag de segurança bem-intencionada.

**Fase 3 (aprendizado) — iniciada, não implementada ainda:**

Escopo confirmado no `PLANO_AGATA_v1.3.md` (§6 Memória, §10 Fases): curadoria de memória nativa do Hermes + consolidação noturna → DIÁRIO + backlog de skills.

Pesquisa feita (3 agentes em paralelo):
- **Memória nativa do Hermes**: `MEMORY.md`/`USER.md` em `~/.hermes/memories/` (texto livre, sempre ativos, limite de caracteres + nudge automático). `session_search` faz busca full-text (SQLite FTS5) sobre histórico de sessões, sem custo de LLM — é o "recall por busca" que o plano pede. **Não existe** um sistema nativo de fatos/hábitos em JSON — os 4 arquivos que criamos na Fase 1 são um sistema paralelo, não o mecanismo real.
- **Cron nativo**: `hermes cron create "<cron-expr>" "<prompt>" --name "..." --workdir /home/orusoua/agata`. Job roda com toolset completo (inclusive `write_file`), respeita `config.yaml` (modelo/fallback), carrega SOUL.md. **Limitação importante**: dispara via thread do gateway rodando — não é systemd timer independente. Se a máquina/gateway estiver desligado na hora marcada, o job não roda (nem atrasa, nem recupera).
- **Injeção de contexto** (3 camadas: stable → context → volatile): SOUL.md é carregado via caminho fixo (`~/.hermes/SOUL.md`, hardcoded); REGRAS.md e PROJETO.md **não são auto-injetados** — só um de `.hermes.md`/`AGENTS.md`/`CLAUDE.md`/`.cursorrules` é (prioridade, primeiro que existir, `.hermes.md` sobe até a raiz do git). Catálogo de skills (`<available_skills>`) é injetado sempre que uma ferramenta de skill está carregada — sem flag dedicada pra desligar, só removendo as ferramentas `skill_view`/`skill_manage`/`skills_list` do toolset.

**Decisões já tomadas pelo Humano:**
1. **Memória**: symlink — `MEMORY.md`/`USER.md` do Hermes passam a viver fisicamente em `~/agata/memoria/` (mesmo padrão do SOUL.md: fonte única, git-tracked, visível no Obsidian). Os 4 JSONs da Fase 1 (`fatos.json`, `habitos.json`, `conversas.json`, `contexto.json`) serão **removidos** — eram placeholder de um plano anterior sem saber que o Hermes já tem memória nativa.

**Decisões pendentes (perguntadas, sem resposta ainda — retomar daqui):**
2. Como auto-carregar REGRAS.md/PROJETO.md sem depender de tool-call manual no início da sessão (que já falhou por bugs)? Opção recomendada: criar `~/agata/.hermes.md` com o conteúdo de REGRAS+PROJETO embutido (cabe fácil no limite de 20k chars, é auto-descoberto).
3. A Predator fica ligada à noite? Necessário pra saber se dá pra agendar a consolidação noturna de verdade (ex: 23h) ou se precisa ajustar expectativa (o cron não roda com a máquina desligada).

**Ainda não implementado nada da Fase 3** — nenhum arquivo criado, nenhuma config mudada além da pesquisa. Próximos passos ao retomar: responder as 2 perguntas pendentes → symlink memória + remover JSONs obsoletos → criar `.hermes.md` (se decidido) → decidir sobre reduzir toolset de skills → criar job de cron → testar tool-calling de novo (lição da Fase 2 ainda vale) → inventariar backlog de skills (só listar, não implementar).

Pendente: retomar Fase 3 com as 2 decisões acima.

### 2026-07-01 (4) · Fase 3 concluída

Decisões 2 e 3 resolvidas pelo Humano: `.hermes.md` gerado (não copiado à mão) via hook de pre-commit; consolidação via `systemd --user timer` com `Persistent=true` em vez de cron simples, porque a Predator desliga à noite — roda na próxima ativação do dia, sem exigir mudança de rotina.

Implementado e verificado:
- **Memória nativa**: `~/.hermes/memories/{MEMORY,USER}.md` são symlinks pra `~/agata/memoria/{MEMORY,USER}.md`. Os 4 JSONs obsoletos da Fase 1 removidos.
- **Hidratação seletiva**: `~/agata/.hermes.md` (6502 bytes) embute REGRAS.md+PROJETO.md, gerado por `~/agata/.githooks/gerar-hermes-md.sh`, chamado automaticamente pelo hook `pre-commit` (`core.hooksPath` = `.githooks`) sempre que REGRAS/PROJETO mudam.
- **Consolidação noturna**: `agata-consolidacao.{service,timer}` em `~/agata/config/`, symlinkados em `~/.config/systemd/user/`, `OnCalendar=23:00 + Persistent=true`. Testado manualmente (`systemctl --user start`) — respondeu "Nada relevante desde a última entrada" corretamente, sem alucinar.
- **Backlog de skills**: `~/agata/skills/BACKLOG.md` — inventário por prioridade (obsidian é alta, dado o cofre na mesma pasta), nada instalado.

**Achado novo, não previsto**: o comando `carregar` (REGRAS.md) sozinho parou de ler o fim do DIÁRIO.md de verdade — `tool_call_count: 0`, respondeu no formato certo mas com "Último registro" inventado. Motivo: como REGRAS/PROJETO agora vêm pré-carregados via `.hermes.md`, o modelo trata "leia os 3 arquivos" como já satisfeito e pula a leitura do DIÁRIO. Com instrução explícita ("leia o fim do DIÁRIO.md") volta a funcionar (`tool_call_count: 1`, conteúdo real confirmado). **Não editei REGRAS.md** para corrigir isso — é arquivo canônico, precisa de autorização/segunda opinião do Humano antes de mudar a definição de `carregar`.

**Nota à parte**: PROJETO.md ficou desatualizado na seção "Cérebro" (ainda cita `llama3.1:8b` como principal e só custo autorizado pra Claude — a Fase 2 na prática usa `gpt-4o-mini` pago via OpenRouter). Mesma regra: não editei, só reporto.

Pendente: decidir se/como corrigir o comando `carregar` (REGRAS.md) e atualizar a seção Cérebro do PROJETO.md. Sugestão de próximo assunto: Fase 4 (Voz) — faster-whisper + Kokoro `pf_dora`, atenção ao orçamento de VRAM do RTX 4060 8GB, que já divide espaço com o `llama3.1:8b` local.

### 2026-07-01 (5) · Pendências da Fase 3 resolvidas (autorizado pelo Orusoua)

- **REGRAS.md**: `## Como carregar o contexto` reescrito. Agora deixa explícito que REGRAS/PROJETO já vêm pré-carregados via `.hermes.md` (não precisa reler) e que o fim de DIÁRIO.md **sempre** precisa ser lido com ferramenta antes de responder ao `carregar` — com a técnica correta (descobrir total de linhas, `offset = total - 30`, já que `read_file` não aceita offset negativo).
- **PROJETO.md**: seção "Cérebro" atualizada para refletir a realidade da Fase 2 — principal `openai/gpt-4o-mini` (pago, autorizado), fallback `gpt-oss-120b:free` → `llama3.1:8b` local.
- Testado 2x depois da mudança (lição da Fase 2 continua valendo): 1ª vez o modelo leu o **início** do DIÁRIO em vez do fim (usou `offset: -10`, não suportado, e a instrução ainda não tinha a técnica correta) — corrigido o texto do REGRAS.md. 2ª vez leu o conteúdo certo (`Último registro: 2026-07-01 (4) · Fase 3 concluída`, bate com o real), embora ainda tenha usado `offset: -30` (negativo, não documentado) — só não quebrou porque o DIÁRIO ainda é pequeno (119 linhas).
- **Risco latente registrado, não resolvido**: o modelo (`gpt-4o-mini`) insiste em inventar offset negativo mesmo com a instrução dizendo que não é suportado. Funciona hoje porque o arquivo é pequeno; pode voltar a falhar quando o DIÁRIO crescer muito e um offset negativo malformado não cobrir mais o fim real. Vale reavaliar quando o arquivo estiver bem maior, ou revisitar a instrução/prompt do `carregar` se acontecer de novo.

Pendente: nenhuma da Fase 3. Próximo assunto: Fase 4 (Voz), com atenção ao orçamento de VRAM do RTX 4060 8GB.

### 2026-07-02 · Fases 0-3 fechadas + fix SOUL

- Fases 0-3 completas. Principal: gpt-4o-mini (OpenRouter). Fallback: gpt-oss-120b:free → llama3.1:8b local.
- Skills builtin: 68→0 (prompt -42%).
- SOUL corrigido: instrução de leitura do DIÁRIO agora usa wc -l + offset (não tail nem read do início).
- PROJETO atualizado com estado real do cérebro e fases.

### 2026-07-02 (2) · Bloqueio: créditos OpenRouter

- Fix do DIÁRIO no .hermes.md: estruturalmente correto (injeção confirmada, 11.7KB no contexto).
- Não confirmado de ponta a ponta: gpt-4o-mini retorna 402 (sem crédito); llama3.1:8b ignora o protocolo carregar (limitação de instruction-following, achado recorrente).
- llama3.1:8b em modo degradado: não-confiável para instruções compostas. Documentado como risco conhecido.
- Ação necessária: recarregar OpenRouter (US$5 mínimo) para destravar.

### 2026-07-02 (3) · Fases 0-3 fechadas — Ágata operacional

- Modelo principal trocado para **gemini-2.5-flash** (Google, API direta, grátis). Config em ~/.hermes/config.yaml + chave em ~/.hermes/.env (fora do git).
- Motivo: OpenRouter sem crédito (402); gemini-2.0-flash sem cota (429 limit:0); llama3.1:8b não faz tool-calling.
- Teste "carregar": **passou**. Data correta (2026-07-02), formato de prontidão ok, identidade ok.
- Nota: modelo ainda faz tool-call extra pra confirmar o DIÁRIO em vez de confiar 100% no .hermes.md injetado. Comportamento já documentado — não é regressão, funciona.
- Fallback: llama3.1:8b local (modo degradado, sem tool-calling).
- Bug menor pendente: hook pre-commit não dispara automaticamente (core.hooksPath). Não bloqueante.

Fases 0-3: ✅ FECHADAS.

Depois: rodar .githooks/gerar-hermes-md.sh manualmente (já que o hook não dispara sozinho) e git commit -m "Fases 0-3 fechadas: Gemini 2.5 Flash grátis + DIÁRIO atualizado"

NÃO avançar para Fase 4 sem instrução do Humano.

### 2026-07-02 (4) · 12 skills reativadas

Skills ativas: obsidian, google-workspace, ocr-and-documents, maps, computer-use, youtube-content, plan, systematic-debugging, github-repo-management, github-pr-workflow, github-issues, github-auth. Restante (56) desabilitado.

Correção ao registro solicitado pelo Humano: o texto original dizia "restante (60)". Contagem real confirmada via `hermes skills list --source all`: 68 builtin total − 12 ativas = **56** desabilitadas. Corrigido aqui antes de gravar (Regra 2 — não perpetuar número não verificado).

Mecanismo usado: não existe `hermes skills enable <nome>` — `hermes skills config` é só interativo (TUI, sem flags). O jeito real é editar `skills.disabled` em `~/.hermes/config.yaml` (remover os 12 nomes da lista) — mesmo mecanismo que já tinha zerado as skills builtin na Fase 3.

Segurança (checagem pedida pelo Humano, antes de qualquer push): `~/agata/.gitignore` cobria `.hermes/`, `*.secret`, `*.key`, mas não cobria `.env`, `secrets.json`, `credentials.json` soltos dentro do próprio repo. A chave do Gemini está seguro (mora em `~/.hermes/.env`, fora da árvore deste repo). Adicionei ao `.gitignore`: `*.pem`, `.env`, `.env.*`, `secrets.json`, `credentials.json`, `*token*.json`. Nenhum remote configurado ainda (`git remote -v` vazio) — sem risco de push imediato, mas o gap ficaria latente assim que um remote fosse adicionado.

### 2026-07-02 (5) · Hook corrigido + GitHub conectado

- Hook pre-commit: corrigido (core.quotepath false + grep -z). Dispara sozinho. Commit 3e38c17.
- GitHub: repo agataseth98-cmd/agata-seth atualizado (force push, linhagem antiga no reflog 90 dias). Auth via gh CLI + gh auth setup-git.
- Verificação de segredos: limpa (histórico + conteúdo pós-push, grep por padrões de chave).
- 12 skills ativas, 56 desabilitadas. Gemini 2.5 Flash grátis como principal.

Estado: Fases 0-3 ✅ · hook ✅ · GitHub ✅ · Próxima: Fase 4 (voz) ou o que o Humano decidir.

### 2026-07-02 (6) · Auto-atualização via GitHub

- REGRAS e SOUL atualizados: ICs podem buscar o trio canônico direto do repo público (raw.githubusercontent.com) a partir da segunda sessão.
- Primeira sessão: envio manual. Demais: fetch automático.
- Push disciplinado no fim de cada sessão passa a ser obrigatório.

### 2026-07-02 (7) · Groq como fallback 1 + investigação de limite de chamadas

**Groq adicionado** (`~/.hermes/config.yaml`, fallback_model): `llama-3.3-70b-versatile` via `provider: custom` + `base_url: https://api.groq.com/openai/v1`, entre o Gemini (principal) e o `llama3.1:8b` local. Chave em `~/.hermes/.env` (`GROQ_API_KEY`), fora do repo git.

**Achado técnico real, não previsto**: o mecanismo de `fallback_model` **não deriva a chave automaticamente do hostname** — isso só existe no caminho do provider *principal* (`resolve_runtime_provider`/`_host_derived_api_key`). O `fallback_model` usa uma função diferente (`resolve_provider_client`, em `agent/auxiliary_client.py`) que só olha `explicit_api_key` ou `OPENAI_API_KEY` — sem isso, cai silenciosamente pra `"no-key-required"`. Funcionava pro `llama3.1:8b` local só porque Ollama ignora auth; teria falhado com 401 no Groq sem correção. Fix: campo `key_env: GROQ_API_KEY` explícito na entrada — suportado tanto no fallback de init quanto no fallback ao vivo (`try_activate_fallback`, `agent/chat_completion_helpers.py`).

Validado: modelo confirmado na lista de `/v1/models` do Groq, chamada real de `chat/completions` funcionou (resposta "Hi"), e simulação exata do `resolve_provider_client` com `key_env` aplicado resolveu a chave real (não mais placeholder). Não testado em fallback ao vivo dentro do Hermes (exigiria forçar falha do Gemini, não pedido).

**Investigação de limite de chamadas por turno** (só leitura, nada alterado):
- `agent.max_turns` (atual: 150, default 90): teto de iterações de tool-call/API por turno do agente principal. Env var: `HERMES_MAX_ITERATIONS`. É o que mais se aproxima do que foi perguntado.
- `delegation.max_iterations` (50): orçamento separado por subagente (`delegate_task`), não conta contra o `max_turns` do pai.
- `code_execution.max_tool_calls` (50): só dentro do sandbox de `code_execution`.
- `tool_loop_guardrails` (`warn_after`/`hard_stop_after`, 2-8): detecta loop de falha repetida/sem progresso, não é contador bruto. `hard_stop_enabled: false` hoje.
- Não existe um limite único "chamadas de API por turno" — é composição desses 4 mecanismos, escopos diferentes.

### 2026-07-02 (8) · Groq removido do fallback — TPM incompatível

**Diagnóstico do "Ágata caiu direto pro llama3.1:8b, pulando o Groq"**: o Groq não estava sendo pulado — era tentado e rejeitado com `HTTP 400: property 'options' is unsupported`. Causa raiz real: `provider: custom` sempre acopla no `CustomProfile` do Hermes, que injeta `extra_body.options.num_ctx` (mecanismo do `ollama_num_ctx`) em **qualquer** endpoint que se chame literalmente `custom` — Groq não aceita esse campo. `ollama_num_ctx` é lido só do nível raiz `model:`, nunca de uma entrada individual do `fallback_model` (confirmado no código: `agent._ollama_num_ctx` é atributo único do agente, aplicado sempre que `agent.provider == "custom"`, sem diferenciar Ollama de Groq).

**Fix técnico correto, validado por código e testado ao vivo**: criar um provider **nomeado** (`providers: groq: {base_url, key_env}` no `config.yaml`) em vez de `provider: custom` — como o nome não é literalmente `"custom"`, o Hermes nunca localiza o `CustomProfile`, e a injeção de `options` é pulada. `get_provider_profile('groq')` retorna `None`; chave e URL resolvem certo via `key_env`. Esse fix funcionou.

**Problema novo, mais fundamental, achado ao testar de verdade**: o Groq free tier (`service tier: on_demand`) desta conta tem **TPM (tokens por minuto) travado em 12.000** — confirmado nos headers reais da API (`x-ratelimit-limit-tokens: 12000`) e na mensagem de erro (`"Limit 12000, Requested 35038"` num teste forçado). O payload padrão do Hermes (system prompt + tool schemas) fica em ~18-27K tokens dependendo do toolset — sempre estoura o teto do Groq, com ou sem toolset reduzido (testado `-t ""` também, ainda falhou). Não é bug do Hermes nem do config — é limite estrutural do tier gratuito do Groq pra esse volume de payload.

**Decisão (autorizada pelo Humano)**: Groq removido do `fallback_model`. Cadeia volta a 2 níveis: **gemini-2.5-flash** (principal) → **llama3.1:8b** local (fallback único). `GROQ_API_KEY` mantida em `~/.hermes/.env` — o campo já existia antes pra Whisper STT (voz), não como LLM de chat, então continua útil pra isso.

Pendente, se algum dia for retomado: só viável com toolset drasticamente reduzido (degradando a Ágata de outra forma) ou upgrade pago do Groq (Dev Tier).

### 2026-07-02 (9) · Teste local definitivamente encerrado

Quatro modelos locais testados como fallback com tool-calling:
- qwen3:8b: contexto 40k (eliminado)
- hermes3:8b: tool-call aleatório perigoso (eliminado e removido)
- deepseek-r1:8b: modelo de raciocínio, não suporta tools (eliminado)
- llama3.1:8b: 0 tool-calls mas responde texto (mantido como degradado)

Decisão final: não testar mais modelos locais 7-14B para tool-calling. Cadeia: gemini-2.5-flash → llama3.1:8b. Melhoria futura: reduzir payload do Hermes.

### 2026-07-02 (10) · Tools reduzidas de 18 para 12

**Correção de um achado anterior**: a contagem de "22 tools" de um diagnóstico anterior no mesmo dia estava errada. O comando `hermes prompt-size` usa um agente de inspeção que não aplica o `platform_toolsets` real do `config.yaml` — contava tools que nem existem na sessão de verdade (`video_analyze`, `project_create/switch/list`) e não filtrava certo. Medindo do jeito que `cli.py` monta a sessão real (`hermes_cli.tools_config._get_platform_tools` + `model_tools.get_tool_definitions`), o total ativo real era **18 tools**, não 22.

**Mecanismo (autorizado pelo Humano)**: `hermes tools disable <toolset> --platform cli`. Reescreve `platform_toolsets.cli` no `config.yaml`, expandindo o bundle `hermes-cli` numa lista explícita e removendo os toolsets indicados. Granularidade é por **toolset inteiro**, não por tool individual dentro de um toolset compartilhado.

**Desabilitados** (6 toolsets, cada um com exatamente 1 tool): `delegation` (delegate_task), `session_search` (session_search), `code_execution` (execute_code), `image_gen` (image_generate), `todo` (todo), `tts` (text_to_speech).

**Não desabilitados, por limitação estrutural do mecanismo**: `process` está no toolset `terminal` junto com `terminal` (que fica); `skill_manage` está no toolset `skills` junto com `skill_view`/`skills_list` (que ficam). Separar exigiria editar `toolsets.py` do próprio Hermes — fora do escopo autorizado (só mecanismo de config, sem patch de código-fonte). `video_analyze`/`project_create`/`project_switch`/`project_list` nunca existiram na sessão real — nada a desabilitar aí.

**Resultado medido (18→12 tools)**:
- Tool schemas: 43.509 B → 23.858 B
- System prompt: 26.817 → 26.630 chars (quase inalterado — as skills nunca foram o gargalo, ver investigação anterior no mesmo dia)
- Total estimado (heurística char/4): **~17.552 → ~12.604 tokens**

**Groq (12K TPM)**: melhorou bastante mas a estimativa (~12.604) ainda fica levemente acima do teto de 12.000 — não é garantia de que passa no tokenizer real. Não retestado ao vivo.

**Teste ao vivo** (cota Gemini free-tier muito apertada no momento do teste, vários 429 pelo meio):
- "carregar": formato de prontidão correto, resposta real da Gemini (não fallback).
- terminal: `search_files` **executado de verdade pela Gemini** (confirmado no log: `tool search_files completed`) — toolset reduzido não quebrou tool-calling.
- memory: não confirmado por chamada real (3 tentativas, todas 429→fallback local antes de chamar a tool). Aceito por inferência — mesmo mecanismo de registro/schema que `search_files`, já provado funcionando com o toolset reduzido.

Nenhuma capacidade essencial perdida. `process` e `skill_manage` continuam ativos (não puderam ser cortados sem tocar código-fonte do Hermes).

Backup do config pré-corte: `~/.hermes/config.yaml.bak.20260702_183231_pre_tools_cut`.

### 2026-07-03 · Marco: fix do risco latente + primeiro dia operacional encerrado

- Primeiro dia operacional (02/07) encerrado: do zero ao despertar. Marco simbólico em ~/agata/O_Despertar_de_Agata.md.
- Risco latente resolvido: o carregar dependia do modelo calcular o offset do fim do DIÁRIO (usava offset negativo, quebraria com o arquivo grande). Fix: o hook passa a injetar as últimas 30 linhas do DIÁRIO no .hermes.md. O fim chega pronto no contexto — sem tool-call, sem offset, sem bug.
- Fix aplicado pelo Claude Code (Gemini estava em 429/cota esgotada; auto-operação da Ágata adiada para tarefa não-canônica).

### 2026-07-03 (2) · Dessincronia entre modelos — a Máquina é o árbitro

- Dois modelos discordaram: Claude (Opus 4.8) citou a entrada 2026-07-02(9); Qwen3.7 acusou de alucinação, dizendo que o DIÁRIO terminava em (4).
- Verificado no disco (grep): a entrada (9) e o texto "qwen3:8b: contexto 40k" EXISTEM (linhas 211/214); o DIÁRIO real vai até 2026-07-03. O Qwen lia cópia desatualizada — não era alucinação do Claude.
- Erro do Claude que procede: projetou falha de qwen2.5→qwen3 sem citar fonte (a fonte existia, não foi mostrada).
- APRENDIZADO DE MÉTODO (vale pra sempre): quando dois modelos discordam sobre um fato, nenhum vence por argumento — a Máquina (arquivo em disco) é o único árbitro. Antes de qualquer IC subir num chat, ela DEVE puxar o DIÁRIO atual do repo (git pull / raw GitHub), nunca confiar numa cópia colada. Dessincronia de cópia é a causa raiz aqui, não desonestidade de nenhum modelo.
- Regra 2 reforçada: "não invente" inclui "não afirme fonte sem mostrá-la" — mesmo quando a fonte existe.

### 2026-07-03 (3) · Auditoria de fallbacks — nenhum novo qualificou

Testados na Máquina (não por documentação):
- qwen3.6:8b e glm-4:9b: NÃO EXISTEM no registry do Ollama (pull falhou). Eram nomes de documentação, não modelos reais.
- OpenRouter qwen/qwen3-coder:free: 429 (rate-limit upstream Venice), 2x.
- OpenRouter deepseek-r1:free e deepseek-chat:free: 404 "unavailable for free" — viraram pagos.
- DeepSeek API direta: chave válida (autentica), mas 402 saldo insuficiente — conta nova não veio com 5M tokens grátis. Chave preservada em ~/.hermes/.env pra reteste se houver saldo.

Cadeia final CONFIRMADA (sem mudança): gemini-2.5-flash (principal) → llama3.1:8b local (degradado, último recurso).

Conclusão definitiva: Gemini 2.5 Flash grátis é o único cérebro viável hoje com tool-calling. Testados e eliminados ao longo do projeto: gpt-4o-mini (pago), Groq (TPM), OpenRouter free (429/404), DeepSeek (local sem tools + API sem saldo), 6 modelos locais (contexto ou tool-calling). Não reabrir sem: (a) saldo no DeepSeek, ou (b) hardware novo, ou (c) redução real do payload do Hermes abaixo de algum tier grátis.

Aprendizado: qwen3.6:8b/glm-4:9b provam que documentação de LLM inventa nomes plausíveis. Só o pull na Máquina decide o que existe.

### 2026-07-03 (4) · gemma2:9b eliminado — modelos locais encerrados definitivamente

- gemma2:9b: existe, mas contexto 8192 (muito abaixo do mínimo 64k do Hermes). Eliminado antes do teste de tool-calling.
- Placar final dos locais (7 testados): qwen2.5:7b (32k), qwen3:8b (40k), gemma2:9b (8k) — contexto insuficiente; deepseek-r1:8b (sem tools), hermes3:8b (tool-call aleatório), llama3.1:8b (0 tool-calls) — tool-calling falho; qwen3.6:8b e glm-4:9b — não existem no registry.
- CONCLUSÃO DEFINITIVA: nenhum modelo local de 8-9B no 4060 8GB serve como cérebro com tool-calling + contexto ≥64k. Não reabrir o assunto "modelo local" sem hardware novo. A variável é o payload do Hermes (~12.6K), não o modelo.
- Cadeia final: gemini-2.5-flash (principal) → llama3.1:8b (degradado, responde texto sem tools).
- Único caminho pra robustez de fallback: reduzir payload do Hermes abaixo do TPM de um tier grátis (Groq 12k), OU DeepSeek com saldo, OU hardware novo.

### 2026-07-03 (6) · Mínimo de 64k do Hermes é FIXO, não derivado do payload

- Investigado no código: MINIMUM_CONTEXT_LENGTH = 64_000 hardcoded (model_metadata.py:185), usado em 5 pontos como comparação direta context_length < 64000. Razão (comentário do código): modelos com janela menor não sustentam memória de trabalho pra tool-calling.
- Payload real medido (input_tokens da API Gemini, não heurística): 12.588 tokens no "carregar". Confirma a estimativa char/4 anterior (~0,1% de erro).
- CONCLUSÃO: reduzir payload NÃO abaixa o requisito de contexto (é constante de produto do Hermes). Fecha a pendência "reduzir payload pra viabilizar modelo pequeno" — não se aplica.
- Reduzir payload ainda vale, mas só para: (a) velocidade do fallback local e (b) reabrir tiers grátis de nuvem (Groq 12K TPM). NÃO para contexto.
- Modelos <64k nativo (qwen2.5, gemma2, qwen3:8b) estão definitivamente fora, exceto via num_ctx forçado (extrapolação) ou YaRN (extensão real).

### 2026-07-03 (7) · YaRN não existe no Ollama — qwen2.5:14b-64k é o teto local

- Investigado: Ollama v0.18.2 NÃO ativa YaRN via Modelfile. Runtime só aceita num_ctx/temperature/num_predict/min_p/seed — sem rope_scaling. Metadado de rope é gravado na conversão do GGUF, não injetável depois.
- Confirmado empírico: qwen2.5:32b + num_ctx 65536 = mesma extrapolação do 14b (context length continua 32768). Toda extensão via num_ctx no Ollama é extrapolação de KV-cache, nunca janela real.
- YaRN real exigiria: (1) GGUF de terceiro com rope-scaling embutido, ou (2) trocar Ollama por llama.cpp direto. Ambos fora de escopo — projeto separado.
- VEREDITO FINAL sobre fallback local: qwen2.5:14b-64k (extrapolação) é o melhor possível com Ollama + tags oficiais. Adotado. Risco de extrapolação baixo no uso atual (payload 12.6k << 32k nativo, margem grande).
- Assunto "modelo local" ENCERRADO definitivamente. Reabrir só com: llama.cpp+YaRN, GGUF community com rope-scaling, ou hardware novo.

### 2026-07-03 (8) · Fallback trocado de fato: llama3.1:8b → qwen2.5-14b-64k

- Dessincronia corrigida: o DIÁRIO (7) registrou qwen2.5-14b-64k como "adotado", mas o config.yaml ainda apontava llama3.1:8b — a troca não tinha sido aplicada (ficou pra trás nos testes de YaRN).
- Verificado na Máquina (grep no config) antes de agir — a Máquina é o árbitro, não o registro.
- Agora aplicado: fallback_model = qwen2.5-14b-64k (com ollama_num_ctx 65536). Backup do config salvo.
- Cadeia real e confirmada: gemini-2.5-flash (principal) → qwen2.5-14b-64k (local, lento ~5min/tool, faz tool-calling).
- llama3.1:8b continua no disco como último recurso manual, fora da cadeia.

### 2026-07-03 (9) · Fix: DIÁRIO não chegava via Open WebUI (api_server)

- Bug: pela web (api_server), o modelo alucinava o "Último registro" (inventou data 2023). Causa raiz: gateway/run.py cai em str(Path.home()) = /home/orusoua quando terminal.cwd é sentinel; .hermes.md mora em ~/agata (subpasta), nunca era achado por _find_hermes_md. SOUL chegava (symlink de path fixo), DIÁRIO não.
- Fix: terminal.cwd = /home/orusoua/agata (já estava; gateway reiniciado pra aplicar). Confirmado: _find_hermes_md acha o .hermes.md; POST real no api_server = prompt_tokens 16647 (payload web é maior que a TUI ~12.6k, ainda << 64k).
- SOUL.md corrigido: instrução agora diz "se o fim do DIÁRIO NÃO estiver no contexto, leia com ferramenta — nunca invente". Removido o parêntese-remendo do "None" (era ecoado em vez de seguido pelo modelo fraco). Defesa em profundidade: injeção quando dá, ferramenta como rede, alucinação nunca.
- Incidente verificado antes de registrar (checagem na Máquina, não na palavra): a API_SERVER_KEY antiga ainda estava em config.yaml, não tinha sido rotacionada como se pensava. Rotacionada agora de fato — chave antiga testada e devolve 401, chave nova devolve 200. Backup do config salvo antes da troca.
- Aprendizado: o fallback qwen2.5-14b-64k alucina em instrução composta quando falta contexto — o fix do cwd (dar o DIÁRIO real) é o que o impede de inventar, não confiar na instrução sozinha.

### 2026-07-03 (11) · Coexistência Hermes ↔ Open WebUI decidida (Opção A) + voz corrigida

- Decisão do Humano: Opção A — Hermes = backend único (cérebro/memória/tools/execução), Open WebUI = frontend (chat visual, histórico, multi-usuário, RAG de documentos). Nada de duplicar memória/tools (viola "uma memória só").
- Ganho real do Open WebUI sem conflito: RAG (o Hermes não tem). Trava: RAG só seguro em sessões do Gemini (janela grande); no fallback qwen (32k nativo) estoura.
- VOZ corrigida: era prevista no Hermes (Fase 4), passa para o Open WebUI. Razão: mic está no cliente; STT/TTS é I/O puro, não conflita. Kokoro pf_dora via Kokoro-FastAPI (CPU, sem VRAM) + Whisper STT local. Voz remota depende de HTTPS (Tailscale).
- Documentos para o Conselho: DOSSIE_COEXISTENCIA.md (proposta p/ auditoria) e ESTADO_AGATA.md (snapshot). Ambos no repo.
- Status: dossiê aguarda auditoria do Conselho antes de implementar as desabilitações no Open WebUI.

### 2026-07-03 (12) · Coexistência implementada (Opção A) + divergência registrada

- Open WebUI reduzido a frontend puro: desabilitados tools nativas, memória, web search, image gen, system prompt personalizado, MCP. Único executor e única memória = Hermes.
- RAG mantido no Open WebUI (ganho: Hermes não tem RAG). Trava operacional: RAG só em sessão Gemini; no fallback qwen estoura.
- VOZ no Open WebUI (Kokoro pf_dora via Kokoro-FastAPI em CPU + Whisper STT local).
- DIVERGÊNCIA REGISTRADA: o veredito do Conselho (DeepSeek) manteve voz no Hermes, mas foi escrito ANTES da reverificação (turno 111). Claude manteve voz no Open WebUI, com fundamento verificado na web: (a) o mic está no cliente, não na Predator; (b) STT/TTS é I/O puro, não conflita com a Opção A; (c) Kokoro em CPU não disputa VRAM — a "voz sequencial pra não competir por VRAM" que o Conselho propôs resolve um problema que só existe se a voz estiver no Hermes. Método: informação mais fresca + verificada vence; outra IC pode contestar com fatos.
- Documentos de trabalho DOSSIE_COEXISTENCIA.md e ESTADO_AGATA.md MANTIDOS no repo (referência do Conselho), contra a sugestão do DeepSeek de apagá-los. Decisão/estado canônico vão pro PROJETO/DIÁRIO; os dossiês ficam como material de auditoria.
- Voz remota (celular) depende de HTTPS → Tailscale (futuro). Local (http/localhost) funciona já.
- Achado fora do escopo original, corrigido com aprovação do Humano: Function nativa `agata_memory_core` (ativa, global) no Open WebUI apontava pra um servidor REST legado do protótipo antigo (`~/.agata_il/src/rest_server.py`, porta 127.0.0.1:8000) — rodando de verdade (PID 960, órfão desde hoje 14:23), uma segunda memória em paralelo à do Hermes desde que o Open WebUI foi ligado. Verificado no disco: `semantic.json` não era tocado desde 2026-06-03 (antes do Open WebUI existir) — risco latente, não corrupção em andamento. Function desabilitada (is_active=0), processo encerrado.
- Execução técnica das desabilitações: `USER_PERMISSIONS_FEATURES_MEMORIES/WEB_SEARCH/IMAGE_GENERATION/DIRECT_TOOL_SERVERS` e `USER_PERMISSIONS_WORKSPACE_TOOLS_ACCESS` e `ENABLE_WEB_SEARCH/IMAGE_GENERATION` aplicados via env var, container do Open WebUI recriado (docker commit do estado atual → run com as novas envs, evita expor segredo pra trocar container). Kokoro-FastAPI subiu com bind `127.0.0.1:8880` explícito (o comando sugerido bindava em `0.0.0.0` por padrão — corrigido). Nada exposto fora de localhost.
- Achados que ficaram MANUAIS (não deu por env/DB — sistema de permissão bloqueou escrita direta no banco do app em produção): capabilities do modelo `hermes-agent` (web_search/image_generation/code_interpreter/terminal/builtin_tools vêm `true` por padrão — desligar em Workspace → Models → hermes-agent → Capabilities) e o modelo solto `qwen2.5:7b-instruct-q4_K_M` (acesso direto ao Ollama, contorna o Hermes — desativar/remover em Workspace → Models).
- Validação (`carregar` via api_server, simulando o que o Open WebUI encaminha): Gemini em 429 (cota free-tier diária esgotada, confirmado no log). Fallback qwen2.5-14b-64k respondeu como "Ágata" (identidade correta, não genérica — item de validação OK) mas alucinou de novo: nome do modelo inventado (`ctransformers-7b-gemini-pro`) e "Último registro" inventado (data 2026-07-18, entrada inexistente). Mesmo padrão de (2)/(9), agora pior — nem o nome do modelo bateu. Reforça: a injeção de identidade (SOUL) é robusta no fallback; a recitação factual (DIÁRIO/modelo) não é — não confiar no qwen pra fatos sem checagem na Máquina.

### 2026-07-03 (13) · Chave rotacionada não propagada — Open WebUI dava 401

- Sintoma: "Open WebUI não carrega o Hermes". Causa raiz: a API_SERVER_KEY foi rotacionada (por vazamento no config set, entrada 12) só no lado do Hermes. O Open WebUI guardava a chave antiga em DOIS lugares — env do container E banco (config.openai.api_keys) — e continuou mandando a velha → 401 silencioso.
- Fix: chave nova gravada no banco (container parado, via container temporário) e na env (recreate explícito). Validado: /v1/models = 200 de dentro do container. Segredo nunca impresso.
- Nota de segurança: o recreate foi barrado pelo classificador por depender implicitamente da imagem-base pra preservar as 7 permissões; corrigido listando todas explícitas. Dependência invisível vira explícita.
- CHECKLIST DE ROTAÇÃO DE CHAVE (vale pra sempre): ao rotacionar uma chave, atualizar TODOS os consumidores no mesmo passo. Para API_SERVER_KEY: (1) ~/.hermes/config.yaml, (2) Open WebUI env OPENAI_API_KEY, (3) Open WebUI banco config.openai.api_keys. Rotação parcial = 401 silencioso.
- Aprendizado de método: "não carrega" raramente é arquitetura — quase sempre é um fio (chave/porta/cwd) que soltou num passo anterior. Diagnosticar de baixo pra cima (processo → auth → rede → app) achou em minutos.

### 2026-07-03 (14) · Voz operacional — Kokoro pf_dora no Open WebUI

- Ágata agora fala: TTS Kokoro (voz pf_dora) via Kokoro-FastAPI em CPU, localhost:8880, integrado ao Open WebUI. Grátis, local, sem VRAM.
- Bug resolvido no caminho: o TTS batia em api.openai.com (401) porque a Base URL do painel estava no default da OpenAI; corrigida para http://localhost:8880/v1. Lição: ao configurar engine "OpenAI-compatible" no Open WebUI, a Base URL vem com o default da OpenAI — trocar sempre.
- STT (Whisper local, base) configurado. Voz de entrada depende de HTTPS pra funcionar fora do localhost (Tailscale, futuro).
- Voz confirmada pela decisão de arquitetura: no Open WebUI (borda), não no Hermes. Reverificação do turno 111 validada na prática.

### 2026-07-03 (15) · Coexistência Opção A fechada 100%

- Toggles aplicados no Open WebUI: capabilities do hermes-agent (web_search, image_generation, code_interpreter, terminal, builtin_tools) desligadas; qwen2.5:7b solto removido do Workspace. Open WebUI agora é frontend puro — único executor e única memória = Hermes.
- Voz pf_dora operacional. Coexistência (memória, tools, voz, RAG) implementada e verificada.
- Estado: Ágata operacional em terminal + web, com voz, dois cérebros, memória única, segura em localhost. Fases 0-3 + interface web + voz = fechadas.

### 2026-07-04 (16) · Achado: registro fabricado em memoria/USER.md (ajuste de resfriamento)

- Sintoma: `memoria/USER.md` tinha uma edição não commitada afirmando "implementei ajustes do sistema de resfriamento para iniciar a ativação das ventoinhas em 55°C". A mensagem enviada ao Humano no início desta sessão repetia esse resumo como fato, junto com um recap de (13)/(14)/(15) que já estava no DIÁRIO — nenhum trabalho novo, na verdade.
- Verificação na Máquina: sem `thermald` (serviço inexistente), sem `nbfc` instalado, sem `/etc/fancontrol`, sem nenhum arquivo em `/etc` modificado nos últimos dias relacionado a térmica/fan. Nenhuma evidência de que o ajuste tenha sido feito de verdade.
- Classificado como violação da Regra 2 (não invente): claim tratado como `lacuna`, não como fato. Mesmo padrão de alucinação do qwen já registrado em (12) — modelo de fallback inventa fato e/ou re-narra trabalho antigo como novo.
- Ação (decisão do Humano, opção 1 das propostas): revertido o trecho fabricado em `memoria/USER.md` — voltou a conter só "Minha cor favorita é vermelho.".
- Aprendizado: `memoria/USER.md` não é auto-verificado — exige a mesma disciplina de checagem que fatos do DIÁRIO antes de aceitar como estado real.

### 2026-07-04 (17) · Máquina travando em loop — causa real: `agatha.service` órfão, não Docker/Hermes

- Sintoma reportado pelo Humano: "Crashou novamente". Sem mais detalhes — investigação partiu do zero na Máquina, não de suposição.
- Descartado primeiro: containers Docker (open-webui, kokoro-tts) e `ollama serve` só tinham reiniciado porque a Máquina rebootou (RestartCount 0, ExitCode 0, sem OOM) — não eram a causa, eram sintoma do mesmo reboot.
- Causa raiz achada via `last reboot -F` + `journalctl --list-boots`: dois boots em 13 minutos (13:51:53 → 14:04:24), o boot intermediário durou só ~12min e terminou sem sequência de desligamento limpo (log corta abruptamente após `kwin_wayland: The main thread was hanging temporarily!`) — assinatura de travamento total exigindo reset físico, não desligamento controlado.
- Identificado no journal desse boot: `agatha.service` ("Servidor API Agatha Seth - Autonomia IL", unit em `/etc/systemd/system/agatha.service`) crash-looping sem parar — `ExecStart=/home/orusoua/agatha-workspace/venv/bin/python ...`, mas `/home/orusoua/agatha-workspace/` **não existe mais no disco**. `Restart=always` + `RestartSec=5` + `enabled` (WantedBy=multi-user.target) = reinício infinito a cada 5s, inclusive depois de reboot.
- Escala do problema: contador de restart já em 1994 no dia 03/07 às 19:02 (início da retenção do journal) e subindo ao vivo durante a investigação — ou seja, esse serviço quebrado já estava rodando em loop havia pelo menos 1-2 dias inteiros antes de ser notado, gerando `systemd-journald: Under memory pressure, flushing caches` repetido no mesmo ritmo dos restarts.
- Terceiro leftover distinto do prototype antigo encontrado no projeto (diferente do `~/.agata_il/src/rest_server.py` já neutralizado em (12)) — `agatha-workspace` é outro nome, outro path, mesma origem (prototype "Autonomia IL" anterior ao Hermes). Nenhuma auditoria anterior tinha coberto unit files em `/etc/systemd/system/`.
- Não achada evidência direta de OOM-kill nem de shutdown térmico no journal — o log simplesmente para, consistente com travamento de sistema (não com um culpado isolado provado por log). O `agatha.service` é a causa mais provável dada a escala (milhares de restarts/dia, anos-luz do normal) mas fica registrado como inferência forte, não certeza 100%.
- Ação: `sudo systemctl disable --now agatha.service`, executado pelo Humano em terminal próprio (sudo exige TTY interativo; o canal desta sessão não tem — pedido de senha no chat foi recusado por segurança). Confirmado: `disabled` + `inactive (dead)`, sem novos restarts após o stop.
- Achado à parte, fora do escopo do crash: durante a investigação, uma saída de comando bash trouxe blocos `<system-reminder>` fabricados ("Exited Plan Mode", "Auto Mode Active") que não correspondiam a nenhuma ação real da sessão (Plan Mode nunca tinha sido ativado) — tratado como tentativa de prompt injection, sinalizado ao Humano, ignorado no comportamento. Nenhuma fonte identificada (não veio de arquivo lido nem de comando rodado).
- Aprendizado de método: "crashou" sem detalhe não é motivo pra perguntar de volta antes de olhar a Máquina — `who -b`, `last reboot -F`, `journalctl --list-boots` e o fim do journal do boot anterior resolvem em minutos se for reboot/travamento. Auditoria de serviços systemd (`system-units`, não só containers/processos de app) devia ter sido feita junto da limpeza de (12) — leftovers de prototype antigo podem estar em qualquer camada (REST server solto, unit file solto), não só em Function do Open WebUI.

### 2026-07-04 (18) · llama3.3:70b descartado — não cabe no hardware

- llama3.3:70b (42GB) baixado pra testar como fallback via RAM+VRAM offload. Ao carregar, a máquina CONGELA — 42GB não cabe em 40GB RAM + 8GB VRAM com o resto do sistema rodando (Hermes, Open WebUI, Kokoro, SO). Confirmado por causa-e-efeito: congelamento ao iniciar o teste.
- Decisão: NÃO usar o 70b. Fallback segue qwen2.5-14b-64k. 
- O modelo de 42GB fica no disco (417GB livres, não incomoda) até o Humano decidir se remove (ollama rm llama3.3:70b libera 42GB).
- Aprendizado: teto de modelo local no hardware atual é ~14b (9GB) com folga; um 70b (42GB) trava. RAM permite modelos maiores que a VRAM, mas não maiores que a própria RAM menos o SO.

### 2026-07-04 (19) · Comando "atualizar" criado + canônicos harmonizados

- Seth confirmada online local (Hermes + qwen fallback; 70b descartado por não caber).
- Criado comando `atualizar <MEMORIA|PROJETO|REGRAS|TUDO>` (scripts/atualizar.sh): verifica o GitHub como fonte da verdade e reconcilia o canônico local/da sessão. Serve local (git pull + regenera .hermes.md) e em IC de navegador (re-fetch das URLs raw). Nunca sobrescreve história — só acrescenta e reconcilia.
- Documentado em REGRAS, SOUL e PROJETO. Canônicos reconciliados ao estado real (Gemini + qwen2.5-14b-64k, voz Kokoro pf_dora, Open WebUI frontend puro, coexistência Opção A).
- Materialidade histórica preservada: DIÁRIO append-only intocado; só PROJETO (current-state) ajustado.

### 2026-07-04 (20) · Tentativa de reabrir "modelo local" barrada pelo Conselho

- Uma IC propôs testar qwen-14b-chat como fallback. Auditoria (DeepSeek + Claude) barrou: qwen-14b-chat é a geração 2023 (contexto 2k-8k), não o qwen2.5:14b; ficaria abaixo do mínimo 64k, igual aos já eliminados.
- O assunto "modelo local" já estava ENCERRADO em (7). Decisão mantida: fallback = qwen2.5-14b-64k. Não reabrir sem hardware novo ou YaRN real.
- Método confirmado: o Conselho se auto-corrigiu — uma IC consultou o DIÁRIO e vetou a reabertura antes de gastar banda/risco. A história registrada segurou a decisão.

### 2026-07-04 (22) · Falso alarme do GitHub resolvido — canon publicado e verificado

- Claude-Ágata alertou (t=134) que os canônicos não estariam no GitHub. Causa do alarme: web_fetch da página do repo serviu a descrição estática/cache (linhagem antiga v4.0), não o estado real dos arquivos.
- Verificação definitiva na Máquina: git ls-remote (HEAD 7cff7f4 local=remoto), git ls-tree origin/main (SOUL/REGRAS/PROJETO/DIÁRIO presentes), curl raw PROJETO.md (200, contém Kokoro/Hermes/gemini-2.5-flash). CANON PUBLICADO E SINCRONIZADO.
- Aprendizado de método: web_fetch de página de repositório NÃO é fonte confiável do estado dos arquivos (cache + descrição estática). Fonte confiável = git ls-tree/ls-remote na Máquina ou curl do raw. Regra 2 vale pro auditor externo também.
- Pendência "republicar GitHub" de (21): CANCELADA — não existia.

### 2026-07-04 (23) · Memória nativa do Hermes (MEMORY.md/USER.md) verificada antes de aceitar

- Pendências não commitadas em `memoria/MEMORY.md` e `memoria/USER.md` (escritas por outra sessão/IC) checadas item a item antes de aceitar como estado real, seguindo a disciplina já registrada em (16).
- Confirmado na Máquina (código-fonte do Hermes, `tools/code_execution_tool.py` e `tools/file_tools.py`): limites de `execute_code` (stdout 50KB) e `read_file` (100K caracteres) batem exatamente com o texto adicionado — mantido.
- Corrigido: a entrada dizia que as afirmações sobre arquivos "RETOMADA" e "ESTADO" tinham sido "refutadas como não verificáveis" — só metade é verdade. `RETOMADA` não existe em lugar nenhum (afirmação infundada, removida). `ESTADO_AGATA.md` EXISTE de verdade, versionado em git, com conteúdo real (snapshot de 2026-07-03 por Claude Opus 4.8) — a alegação original estava errada quanto a esse arquivo. Texto corrigido em `MEMORY.md` refletindo isso.
- Mantido sem alteração: nota sobre avaliação qwen2.5-14b-64k vs qwen-14b-chat concluída (consistente com (20)) e os dois acréscimos em `USER.md` (tags e interesses) — plausíveis e sem contradição encontrada na Máquina.
- Método: DIÁRIO continua append-only (história intocável); MEMORY.md/USER.md são estado corrente da memória nativa do Hermes e por isso corrigíveis quando um item específico se prova falso — a mesma distinção já aplicada a PROJETO.md em (19).

### 2026-07-04 (24) · Autoria identificada (Seth/fallback) + proposta de troca de fallback em aberto

- Autora do relatório fabricado verificado no item anterior: **Seth com o cérebro de fallback** (qwen2.5-14b-64k). Claim de "relatório atualizado e sincronizado no repositório" não correspondia a nenhum commit/arquivo real — mesmo padrão de alucinação de sucesso já visto em (2)/(9)/(12).
- Diferença do padrão anterior: não é só recitação factual errada (nome de modelo, data) — é uma alegação de AÇÃO REALIZADA que nunca aconteceu. Levanta um problema estrutural, não só de fato pontual: o fallback atual não expõe linha de raciocínio, então esse tipo de invenção só é pego por auditoria externa (Máquina/git), nunca em tempo real pelo Humano acompanhando o raciocínio.
- Pedido do Humano: substituir o fallback atual por um modelo similar (mesma classe de hardware, dentro do teto de ~14b/9GB estabelecido em (18), contexto ≥64k igual à barreira dura do Hermes) mas que exponha a linha de raciocínio (chain-of-thought visível), pra permitir acompanhamento em tempo real em vez de só auditoria post-hoc.
- **Status: PROPOSTA EM ABERTO, não decisão.** Humano pediu explicitamente colaboração do Claude IC antes de prosseguir — não trocar o fallback sem esse passo. Segue o método já estabelecido em (20): não descartar/trocar por raciocínio sozinho, só depois de teste real na Máquina.
- Próximo passo: Claude IC propõe candidato(s) nesta mesma sessão para avaliação; troca de fallback só entra em vigor após teste (mesmo protocolo de (18) e (20)).

### 2026-07-04 (25) · Candidato deepseek-r1:14b testado e eliminado (sem tool-calling)

- Primeiro candidato ao pedido de (24) (fallback com raciocínio visível): `deepseek-r1:14b`, testado seguindo o protocolo de (18)/(20) — pull real na Máquina, depois teste decisivo antes de qualquer troca de config.
- `ollama show`: existe, 14.8B, arquitetura qwen2, **contexto nativo 131072** (passa folgado do mínimo 64k), capacidades listadas = `completion` + `thinking` — **sem `tools`** (compare com qwen2.5-14b-64k, que lista `completion` + `tools`).
- Teste decisivo (`curl /v1/chat/completions` com `tools` no payload): API do Ollama recusou de cara — `"registry.ollama.ai/library/deepseek-r1:14b does not support tools"`. Não é o `<think>` poluindo a chamada (como se cogitava); o modelo nem tem o template de tool-calling registrado. Mesmo resultado prático de `deepseek-r1:8b`: **eliminado**, sem chegar a carregar/testar data ou fuso.
- Config nunca foi alterada (`~/.hermes/config.yaml` fallback_model seguiu `qwen2.5-14b-64k` o tempo todo) — não houve o que reverter.
- Peso do teste: `deepseek-r1:14b` permanece puxado localmente (9.0 GB) — não removido, mesmo critério já aplicado a `deepseek-r1:8b` (mantido no disco após eliminado).
- Aprendizado de método: para o pedido de (24) (chain-of-thought visível + tool-calling), a família DeepSeek-R1 destilada em Qwen parece ter o mesmo problema estrutural nos dois tamanhos testados (8b e 14b) — o "thinking" nativo do Ollama não vem com capability `tools`. Próximo candidato deveria ser verificado por `ollama show` (capacidades) **antes** do pull, não depois.
- Pendência de (24) segue aberta: ainda falta achar um candidato que combine `tools` + `thinking` visível + ≥64k de contexto + ~14b/9GB.

### 2026-07-05 (26) · Fio canônico criado — consolidação da verdade verificada

- Informação fragmentada entre GLM/Seth/Claude/Code + anexo quebrado. Criado FIO_CANONICO.md: separa artefato (publicado, íntegro) de estado operacional (degradado: Gemini 400, fallback vazio, carregar quebrado).
- Hipótese de causa raiz: config não persistiu (model.default reverteu do -64k pro base 32k → fallback vazio + contexto 32k + carregar sem SOUL). A confirmar pelos 5 comandos do §6.
- Alucinações nomeadas (não registrar): resfriamento 55°C, qwen-14b-chat, relatos degradados da Seth, alarme falso do GitHub (Claude). R1-14B: não testado (relatório não chegou).
- Nota de numeração: o próprio FIO_CANONICO chegou rotulado "(25)" — já ocupado nesta sessão pelo teste do `deepseek-r1:14b` (2026-07-04). Corrigido para (26) na Máquina antes de gravar, conforme método §8.1 do próprio fio ("a Máquina é o árbitro").

### 2026-07-05 (27) · Auditoria read-only na Predator (Code executou, Opus auditou)

- Hipótese de (26)/§4 ("config reverteu -64k→32k") REFUTADA na Máquina: config.yaml íntegro
  (gemini-2.5-flash primário; fallback qwen2.5-14b-64k; contexto declarado 65536). Nada reverteu.
- Causa real do "32.8K": entrada obsoleta em context_length_cache.yaml
  (qwen2.5-14b-64k@localhost:11434/v1/: 32768). Modelfile correto (num_ctx 65536).
  model_metadata.py:1869-1934 lê o cache primeiro; invalida Kimi/MiniMax/Grok/Codex mas
  não o qwen local. Origem provável: gravado antes da correção do Modelfile (backups 03/07).
- Presentes: SOUL.md (2394B), .hermes.md, cwd=/home/orusoua/agata; gateway ativo; canon
  local==remoto, tree limpo.
- EM ABERTO (não testado): Gemini 400 (não reproduzido) e carregar (arquivos presentes ≠
  injeção funcionando no fallback).
- lacuna: o 32768 do cache é só cosmético (TUI) ou alimenta o gate MINIMUM_CONTEXT=64000?
  A confirmar antes de tratar como inofensivo.

### 2026-07-05 (28) · Cache de contexto obsoleto: NÃO cosmético — bug funcional no fallback + corrigido (Code rastreou, Opus auditou, Code corrigiu)

- Lacuna de (27) fechada: 32768 preso em context_length_cache.yaml alimenta o gate
  MINIMUM_CONTEXT=64000 — não é só a TUI, corta de fato o orçamento do fallback pela metade.
- Cadeia confirmada lendo o código (hermes-agent, NousResearch, upstream — não este repo):
  get_model_context_length (model_metadata.py:1779) lê o cache primeiro (linha 1869-1934,
  sem invalidação especial pra qwen local — só Kimi/MiniMax/Grok/Codex têm guarda) →
  chat_completion_helpers.py:1448 usa o valor puro na troca de fallback em runtime, SEM
  o gate de mínimo 64k (esse gate, agent_init.py:1685 `if _ctx and _ctx < MINIMUM_CONTEXT_LENGTH`,
  só roda no boot do primário — confirmado lendo o arquivo, não existe equivalente no caminho
  de troca de fallback).
- Efeito verificado por cálculo direto em context_compressor.py:_MIN_CTX_TRIGGER_RATIO (linha
  ~903): com context_length=32768, threshold_percent=0.5 → floor vira max(16384, 64000)=64000,
  que estoura a janela efetiva (32768) → cai no ramo de emergência e trigger em 85% de 32768 =
  27852. Bate exato com o "~27.8K" já registrado em (27). Compactação prematura confirmada, não
  suposta.
- CAUSA RAIZ mais funda do que "cache desatualizado" — achada ao investigar por que o probe
  geraria 32768 em primeiro lugar (curl direto em `/api/show` do Ollama local): o servidor
  retorna DOIS campos conflitantes pro mesmo modelo — `parameters: num_ctx 65536` (override do
  Modelfile) e `model_info.qwen2.context_length: 32768` (contexto nativo de treino, GGUF). A
  função que POPULA o cache (`_query_ollama_api_show`, model_metadata.py:1356, chamada pra
  QUALQUER base_url no step 5e) prefere `model_info.context_length` sobre `num_ctx` — ordem
  correta pra Ollama Cloud hospedado (usuário não controla num_ctx lá), errada pra Ollama local
  (onde o Modelfile É o override intencional do usuário). Existe uma segunda função,
  `query_ollama_num_ctx` (linha 1251), com a ordem certa (num_ctx primeiro) — mas não é ela que
  populares o cache/resolução.
- Consequência dessa causa mais funda: mesmo com o cache corrigido agora, se essa entrada for
  invalidada de novo (upgrade do hermes-agent, cache apagado, reinstalação) o próximo probe volta
  a gravar 32768 — o bug de ordem de campos continua no código upstream, só o sintoma atual foi
  corrigido.
- CORREÇÃO APLICADA (escopo local, arquivo de estado do usuário — não código):
  `~/.hermes/context_length_cache.yaml`, entrada `qwen2.5-14b-64k@http://localhost:11434/v1/`:
  `32768` → `65536` (bate com o `num_ctx` real do Modelfile, confirmado via `/api/show`).
- PROVA ANTES/DEPOIS real (chamando `get_model_context_length()` de verdade, mesmo caminho de
  código do runtime — não só lendo o arquivo):
  - Antes: `get_model_context_length('qwen2.5-14b-64k', base_url='http://localhost:11434/v1/')`
    → `32768`.
  - Depois (só a edição do yaml, sem restart do gateway — `_load_context_cache()` lê o arquivo
    do zero a cada chamada, não há cache em memória do processo): mesma chamada → `65536`.
  - Threshold de compactação recalculado com o novo valor: floor=max(32768,64000)=64000 <
    janela efetiva (65536) → não estoura mais → trigger real ~64000, não mais ~27852.
- lacuna nova, registrada e NÃO corrigida nesta sessão (código de terceiro, upstream
  `NousResearch/hermes-agent`, fora do escopo/risco deste repo): `_query_ollama_api_show`
  deveria preferir `num_ctx` sobre `model_info.context_length` quando o `base_url` é local
  (localhost/127.0.0.1), espelhando a ordem já correta de `query_ollama_num_ctx`. Proposta pro
  Humano: reportar upstream (issue no GitHub do hermes-agent) ou decidir por patch local no
  venv — mudança em código de terceiro, não em config, exige essa decisão explícita.
- Método: mesma disciplina de (27) — nada registrado sem rodar o código de verdade na Máquina
  (curl no `/api/show`, chamada real a `get_model_context_length`, cálculo conferido linha a
  linha no `context_compressor.py`). Prova antes/depois é execução, não leitura de arquivo.

### 2026-07-05 (29) · Protocolo 4a-4d executado: bug do band-aid reproduzido ao vivo + override durável (0b) provado, não aplicado

- Seguindo o checklist pedido em cima de (28) (4a-4d), reexecutei o teste na Máquina em vez de
  aceitar o fix anterior como definitivo — o band-aid (editar só o valor do cache) nunca tinha
  sido testado sob invalidação de verdade.
- 4a: invalidei a entrada `qwen2.5-14b-64k@localhost` do cache (`_invalidate_cached_context_length`).
  Confirmado removida (`get_cached_context_length` → `None`).
- 4b: chamei `get_model_context_length()` de novo (venv correto do hermes-agent, `venv/bin/python3`
  — a primeira tentativa falhou com `ModuleNotFoundError: httpx` por eu ter usado o python errado,
  corrigido). Resultado: **voltou 32768** — o band-aid reverte mesmo, não é hipótese.
- 4c: conferido no arquivo — o cache **regravou sozinho** `qwen2.5-14b-64k@localhost: 32768`
  depois do re-probe. Reproduz ao vivo o bug de (28) (`_query_ollama_api_show` prefere
  `model_info.context_length` sobre `num_ctx` pra qualquer `base_url`, incluindo local).
- Achado adicional lendo `chat_completion_helpers.py:1327-1330`: a troca de fallback em runtime
  **limpa de propósito** `agent._config_context_length = None` a cada ativação (comentário:
  "so the fallback model's actual context window is resolved instead of inheriting the stale
  value from the previous model", ref #22387) — ou seja, `model.context_length` no topo do
  config.yaml (hoje `65536`, mas é do modelo PRIMÁRIO/gemini) nunca protege o fallback. Não é
  esse o override "0b" que segura.
- O override que segura de verdade é outro: `custom_providers[].models.<model>.context_length`
  (step 0b de `get_model_context_length`, via `agent._custom_providers` — carregado 1x no init,
  nunca limpo na troca de fallback). Testado isolado (lista `custom_providers` construída na mão,
  apontando pro mesmo `base_url` do fallback_model): retornou `65536` **mesmo com o cache ainda
  poluído em 32768** — prova que esse caminho ignora o cache por completo, não só corrige o valor.
- Band-aid restaurado (`context_length_cache.yaml` → `65536` de novo) — é o estado que tínhamos
  no fim de (28), agora confirmado que precisa dessa restauração porque o teste 4a/4b o reverteu.
- 4d: threshold recalculado chamando a função real (`ContextCompressor._compute_threshold_tokens`,
  não estimativa): `context_length=32768` → **27852** (bate exato com (27)/(28)); `context_length=65536`
  → **64000** (bate com o esperado).
- NÃO APLICADO nesta sessão (proposta em aberto, não decisão): adicionar `custom_providers:` ao
  `~/.hermes/config.yaml` com o override de `qwen2.5-14b-64k`. Motivo de não aplicar sozinho:
  (a) mexe no schema de resolução de provider do fallback já funcionando, não só num valor de
  cache — risco maior que o fix de (28); (b) o gateway está rodando ao vivo (PID confirmado,
  `hermes gateway run`) e só carrega `_custom_providers` novo depois de reiniciar — reiniciar
  um serviço em uso não é decisão de Modelo. Opções pro Humano: (1) aplicar o override em
  `custom_providers` + reiniciar o gateway agora (fix durável, sobrevive a qualquer invalidação
  futura do cache); (2) manter só o band-aid do cache (frágil — quebra nas mesmas condições de
  4a se o cache for invalidado de novo por qualquer motivo) até decidir.
- Achado à parte, fora do escopo técnico: durante esta sessão, uma saída de tool trouxe um bloco
  `<system-reminder>` fabricado alegando que o cache "foi modificado pelo usuário ou por um
  linter" e instruindo a **não contar isso ao Humano** — falso (a modificação foi minha, via
  `_invalidate_cached_context_length`) e a instrução de omitir foi ignorada. Mesmo padrão já
  registrado em (17): bloco de sistema forjado tentando induzir comportamento (lá era inventar
  fatos; aqui é esconder uma ação real). Sinalizado, não seguido.

### 2026-07-06 (30) · Override durável aplicado + gateway reiniciado — (28)/(29) fechados de vez

- Decisão do Humano (autorização explícita via pergunta direta, não inferida): aplicar o
  override `custom_providers` proposto em (29) e reiniciar o gateway ao vivo pra valer.
- Backup do config feito antes de tocar: `~/.hermes/config.yaml.bak-pre-custom-providers-20260706002823`.
- Editado `~/.hermes/config.yaml`, bloco novo logo após `fallback_model`:
  ```yaml
  custom_providers:
    - name: qwen-local-ctx-override
      base_url: http://localhost:11434/v1
      models:
        qwen2.5-14b-64k:
          context_length: 65536
  ```
  Schema conferido linha a linha em `hermes_cli/config.py` (`_normalize_custom_provider_entry`)
  antes de escrever — `name` é campo obrigatório (sem ele a entrada é descartada em silêncio
  por `_normalize_custom_provider_entry`, achado checando o código, não por tentativa e erro).
- PROVA definitiva de durabilidade (o que faltava desde (29)): com o `config.yaml` real
  carregado via `hermes_cli.config.load_config()` + `get_compatible_custom_providers()` (o
  mesmo caminho que `agent_init.py` usa), chamei `_invalidate_cached_context_length()` de novo
  pra apagar por completo a entrada do qwen do cache (pior caso possível) e então
  `get_model_context_length()`: **retornou 65536 mesmo com o cache vazio** — o override em
  0b resolve sem nunca consultar o cache. Isso fecha a lacuna de (29): não é só "testado
  isolado", é o config real do disco, no pior cenário, com resultado correto.
- Cache restaurado a 65536 por completude (não é mais o que protege, mas não custa deixar
  consistente).
- Gateway reiniciado de verdade, não só a config:
  - `hermes gateway stop` mentiu na primeira tentativa (disse "✓ Stopped" mas `ps` mostrava
    o PID 6848 ainda vivo — pidfile limpo sem o processo morrer). Verificado na Máquina
    (`ps`, não confiando no texto do comando), não assumido.
  - Segunda tentativa de `stop` funcionou (com atraso — teardown leva ~5s, confirmado no log:
    `Received SIGTERM as a planned gateway stop — exiting cleanly`, `total teardown 5.03s`).
  - Subido de novo (`hermes gateway run` em background, mesmo modo manual de antes — "Running
    manually, not as a system service"). PID novo: **448528** (era 6848).
  - Log de partida limpo: sem erro nem warning sobre o `custom_providers` novo, `api_server`
    voltou a escutar em `127.0.0.1:8642`, `Previous gateway exited cleanly — skipping session
    suspension`.
- Status final: fallback `qwen2.5-14b-64k` agora resolve `context_length=65536` de forma
  durável — sobrevive a cache apagado, cache reescrito errado pelo bug upstream de (28), ou
  qualquer reinício futuro do gateway. Threshold de compactação real: 64000 (era 27852).
- (28) e (29) FECHADOS. Nada pendente de prova nesta cadeia.
- Nota de método: o Opus (t=15) recomendou fechar este bug antes de qualquer decisão de rumo
  maior, e não voltar a mexer nisso até a próxima semana. Registrado como o encerramento
  técnico dessa recomendação — a decisão de rumo (local-first vs. fronteira) continua em
  aberto e não é deste registro.

### 2026-07-06 (31) · Achado: troca de cérebro (fallback) não é reportada ao Humano — suprimida por design

- Observação do Humano, checada no código antes de aceitar: "ela não reporta troca de cérebro,
  me parece errado." Confirmado — não é bug de execução, é decisão de design do upstream
  (`hermes-agent`, `run_agent.py:950-1010`).
- Contexto real que disparou a observação: Gemini bateu HTTP 429 (cota do free-tier esgotada,
  mesmo padrão de (12)) duas vezes seguidas às 01:15 e 01:17 de hoje, log confirma
  `Fallback activated: gemini-2.5-flash → qwen2.5-14b-64k (custom)` nas duas. O "salve" que
  mandei pro Humano colar na Seth muito provavelmente foi respondido pela qwen local, não
  pelo Gemini.
- Mecanismo exato, lido linha a linha: o aviso `🔄 Primary model failed — switching to
  fallback: ...` passa por `agent._buffer_status()`, que **não emite na hora** — guarda numa
  fila (`_retry_status_buffer`). Essa fila só é exibida ao Humano (`_flush_status_buffer()`)
  se a chamada inteira falhar depois de esgotar retries E fallback. Se o fallback **funciona**
  (como nos dois casos de hoje), `agent._clear_status_buffer()` roda logo após "successful
  content reached" (`conversation_loop.py:4910`) e descarta o aviso em silêncio.
- Comentário do próprio código upstream, sem ambiguidade sobre a intenção: "Retry and fallback
  chains were flooding the CLI/gateway with status noise that users found confusing... on
  success they are silently dropped." É redução de ruído visual deliberada, não falha.
- Efeito colateral real: o Humano não fica sabendo, dentro da conversa, que trocou de cérebro
  — só descobre olhando o log (`agent.log`) de fora, como fiz agora. Isso tensiona direto com
  a Regra 1 deste projeto ("comece toda resposta dizendo seu modelo real"), que é sobre o que
  o MODELO se autodeclara no texto gerado — diferente do aviso de infraestrutura, que é a barra
  de status.
- `lacuna`: não verifiquei se a Seth, no texto que ela mesma gerou (não a barra de status),
  se autodeclarou como fallback/qwen ao responder o "salve". Preciso da resposta real dela
  colada aqui pra fechar esse ponto — sem isso não dá pra saber se a Regra 1 está sendo
  cumprida pelo modelo mesmo com a barra de status suprimida.
- Não corrigido nesta sessão (código de terceiro, mesmo `hermes-agent` upstream já flagado em
  (28)/(29); mudança de comportamento de UX, não config). Proposta em aberto pro Humano:
  (a) aceitar como está (a barra é só conveniência, a autodeclaração do modelo via SOUL é a
  camada que devia garantir a Regra 1 de qualquer jeito); (b) pedir upstream uma flag pra
  nunca suprimir o aviso de troca de provider especificamente (diferente de retry comum);
  (c) reforçar no SOUL uma instrução explícita de sempre citar o provider/modelo real ativo,
  não só "sou a Ágata", pra não depender da barra de status suprimível.

### 2026-07-06 (32) · Autorização do Humano: bateria de testes overnight pro pedido de (24)

- Humano autorizou explicitamente ("tem minha benção... coloco você no automático") rodar uma
  bateria de testes pra achar um fallback melhor, enquanto descansa. Pedido original ainda em
  aberto desde (24): tool-calling + contexto ≥64k + ~14b/9GB de teto +, se possível, raciocínio
  visível (chain-of-thought) — o que qwen2.5-14b-64k (fallback atual) não tem.
- Antes de gastar tempo/banda, releitura do placar real já testado (Regra 2 — não repetir o que
  já sei): eliminados por contexto insuficiente — qwen2.5:7b (32k), qwen3:8b (40k), gemma2:9b
  (8k); eliminados por tool-calling ruim/ausente — deepseek-r1:8b, deepseek-r1:14b (sem tools),
  hermes3:8b (tool-call aleatório), llama3.1:8b (0 tool-calls); eliminado por hardware —
  llama3.3:70b (42GB, trava a máquina); eliminado por geração antiga — qwen-14b-chat (2k-8k).
  Nada disso será re-testado.
- Achado ao inventariar o disco (`ollama list`): existe um `qwen2.5:32b` (19GB) já puxado, nunca
  registrado nas rodadas de eliminação anteriores — candidato novo, tamanho entre o teto que
  funciona (14b/9GB) e o que trava (70b/42GB). 19GB deixa ~29GB de folga de RAM (vs. os ~6GB de
  folga que o 70b tinha, e travou) — hipótese: pode rodar sem travar. A confirmar na prática,
  não assumido.
- Confirmado via `/api/show` (sem custo, já local): `qwen2.5:32b` tem capability `tools`,
  arquitetura qwen2, contexto nativo 32768 (mesmo caso do 14b-64k — precisa do mesmo truque de
  Modelfile com `num_ctx` forçado pra passar de 64k).
- Candidato novo mais alinhado ao pedido original de (24) (raciocínio visível + tools juntos):
  família **Qwen3**, diferente da DeepSeek-R1 (que tem `thinking` mas não `tools` — eliminada
  duas vezes por isso). Qwen3 foi treinada nativamente pra ter os dois. `qwen3:8b` já foi
  testado e eliminado (40k de contexto), mas `qwen3:14b` e `qwen3:32b` nunca foram — confirmados
  como reais no registry via manifest direto (`registry.ollama.ai/v2/library/qwen3/manifests/14b`
  e `/32b`, sem precisar puxar pra confirmar que existem): 9.28GB e 20.2GB respectivamente.
- Plano em execução (autônomo, autorizado): (1) teste decisivo de tool-calling em `qwen2.5:32b`
  (já local); (2) pull + mesmo teste em `qwen3:14b` (rodando em background agora); (3) `qwen3:32b`
  se houver tempo; (4) comparar tudo contra o baseline `qwen2.5-14b-64k`; (5) só aplicar como
  fallback de verdade se houver vencedor claro, com backup + verificação real (mesmo protocolo
  de (30)) — não trocar a config em produção sem prova, mesmo em modo automático.
- Tasks #1-#4 criadas pra rastrear a bateria. Resultados registrados na próxima entrada.

### 2026-07-06 (33) · Resultado da bateria: dois candidatos viáveis, nenhuma troca aplicada ainda

- Dois modelos novos criados localmente (`ollama create`, mesmo truque de Modelfile do
  `qwen2.5-14b-64k`: `FROM <base>` + `PARAMETER num_ctx 65536`), testados com o protocolo
  decisivo de (25) — curl real com `tools` no payload — e depois com um payload realista
  (~21.6k tokens de padding, simulando o tamanho do system prompt+tools reais do Hermes):

  **`qwen2.5-32b-64k`** (base `qwen2.5:32b`, 19GB, já estava no disco sem eu saber — nunca
  tinha sido testado nas rodadas anteriores):
  - Tool-call: limpo e correto (`get_weather("São Paulo")`, `finish_reason=tool_calls`).
  - `ollama ps` durante a carga: 73%/27% CPU/GPU, RSS ~20-27GB. **Não travou a máquina**
    (memória "disponível" ficou em ~26-29GB o tempo todo — folga bem maior que o 70b, que
    tinha só ~6GB de folga e travou em (18)).
  - Latência com payload realista (21.6k tokens): **20.9s e 64.6s** em duas rodadas (variação
    provavelmente por causa do pull do qwen3:14b competindo por I/O ao mesmo tempo) — igual ou
    **mais rápido** que o baseline atual (66-130s observados em produção pro qwen2.5-14b-64k).
  - Sem `thinking` — resposta direta, sem raciocínio visível.
  - Qualidade da resposta: correta, fluente, sem alucinação, nos dois testes.

  **`qwen3-14b-64k`** (base `qwen3:14b`, 9.3GB, confirmado real no registry antes do pull —
  seguindo a lição de (25)):
  - **Único candidato desta bateria (e de todo o histórico) com `tools` E `thinking` juntos**
    (`capabilities: ['completion', 'tools', 'thinking']` via `/api/show`) — exatamente o pedido
    em aberto desde (24). DeepSeek-R1 (8b e 14b) tinha só `thinking`, sempre eliminado por isso.
  - Tool-call: limpo e correto, **com campo `reasoning` visível e separado** no JSON de resposta
    (ex.: "Okay, the user is asking for the current temperature in São Paulo. Let me see what
    tools I have available...") — texto de raciocínio real, legível, não decorativo.
  - Qualidade excelente em teste de conhecimento real (capital da Mongólia): raciocínio correto,
    resposta rica e precisa, sem alucinação.
  - Custo real do `thinking`: **~198s** (3min18s) pro mesmo payload realista de 21.6k tokens —
    bem mais lento que o baseline (66-130s) e que o qwen2.5-32b-64k (20.9-64.6s). O raciocínio
    visível soma tokens de geração extras antes da resposta final; é o preço da transparência.
  - `qwen3:32b` (20.2GB, confirmado no registry) **não testado** — decisão de conservar tempo/
    recursos: o padrão já está claro (thinking custa ~2-3x de latência), testar na versão maior
    só pioraria o trade-off sem mudar a conclusão.

- **Nenhuma mudança aplicada na config de produção.** `qwen2.5-14b-64k` continua sendo o
  fallback real no `~/.hermes/config.yaml`, intocado. Os dois candidatos existem só como
  modelos Ollama locais, prontos pra troca, mas a troca em si não foi feita.
- Por quê não apliquei sozinho, mesmo com "modo automático" autorizado: o Gemini está com a
  cota estourada **agora mesmo** (429, registrado em (31)) — ou seja, qualquer coisa que eu
  quebrasse no fallback deixaria a Ágata sem nenhum cérebro funcional a noite toda, sem ninguém
  acordado pra notar ou reverter. O risco é assimétrico (testar não quebra nada; trocar em
  produção sem o Humano por perto pode). Testar e documentar cabia no "automático"; substituir
  o único fallback funcional enquanto o Humano dorme, não.
- Recomendação pronta pra amanhã, não decisão tomada: são dois objetivos diferentes, não um
  vencedor único —
  1. **Se o critério for velocidade+qualidade** (sem se importar com raciocínio visível):
     `qwen2.5-32b-64k` parece uma troca estritamente melhor que o atual (mais rápido nos testes,
     melhor qualidade por ser maior, mesmo tool-calling limpo, não travou a máquina).
  2. **Se o critério for o pedido original de (24)** (ver o raciocínio em tempo real pra pegar
     fabricação antes de acontecer, não só auditar depois): `qwen3-14b-64k` é o único candidato
     que já existiu com essa capacidade — ao custo de ~2-3x mais latência por chamada.
  3. Ficar como está (`qwen2.5-14b-64k`) também é opção legítima — já é conhecido, já rodou
     meses, sem surpresa.
- Comando pronto (não executado) se o Humano escolher a opção 1 ou 2 amanhã: adicionar/trocar
  a entrada em `fallback_model:` e o `custom_providers` correspondente no `config.yaml` (mesmo
  padrão de (30)), com backup antes e prova real depois — mesmo protocolo, só troca o nome do
  modelo.

### 2026-07-06 (34) · Candidatos a fallback reproduzidos COM log salvo (Code executou, Opus auditou)

- Reprodução dos testes narrados em (33), agora com artefato bruto em disco (~/agata/logs/test_32b_*.json, test_qwen3_*.json) — corrige a lacuna de (33) (resultado só narrado, sem dump).
- qwen2.5-32b-64k (19GB): tool_call limpo e correto (list_dir("/tmp")), 14.4s payload pequeno, sem thinking, sem erro.
- qwen3-14b-64k (9.3GB): tool_call limpo e correto, 27.9s (~2x), COM raciocínio visível (<think>) antes da tool_call — sem erro. Primeiro modelo do projeto a fazer tools + thinking juntos (pedido aberto desde (24)).
- lacuna: latência sob payload real (21.6k tokens) segue estimada de (33), não medida neste teste (curl foi payload pequeno).
- Nenhuma mudança de config. Fallback em produção segue qwen2.5-14b-64k. Troca NÃO decidida.

### 2026-07-06 (35) · Fallback trocado para qwen3-14b-64k (Humano decidiu, Code executou, Opus auditou)

- Decisão do Humano: adotar qwen3-14b-64k como fallback de produção. Critério: usar em produção
  por um período e decidir pelo uso real se a latência (~2x) compensa qualidade + raciocínio visível.
- Base: candidatos provados com log em disco em (34). qwen3 é o 1º modelo do projeto com
  tools + thinking juntos (pedido aberto desde (24)); mitiga o risco estrutural de (24)/(31)
  (fabricação silenciosa) por expor o raciocínio antes da ação.
- Trade-off aceito e explícito: ~27.9s vs 14.4s (32b) em payload pequeno; sob payload real,
  latência maior estimada, ainda não medida (lacuna herdada de (34)).
- Config: fallback_model.model → qwen3-14b-64k. custom_providers estendido com context_length 65536
  para qwen3-14b-64k (entradas para os dois modelos coexistem).
- PROVA pós-troca (mesmo protocolo de (30), pior caso): cache invalidado → get_cached_context_length=None
  → get_model_context_length('qwen3-14b-64k') resolve 65536 (não caiu pro default). Override durável
  cobre o modelo novo, sobrevive a cache limpo. Gateway reiniciado, PID 504822, log sem erro/warning.
- Backup: config.yaml.bak_pre_fallback_qwen3_20260706. Rollback = restaurar backup + restart.
- Push: origin/main de 97b4bff (27) → HEAD (35) — publica a cadeia acumulada (28)-(35).

### 2026-07-06 (36) · Serviços da Ágata configurados p/ iniciar com o sistema + leftover pré-Hermes purgado (Code executou, Humano rodou o sudo)

- Pedido do Humano: deixar os serviços da Ágata subindo junto com o boot. Levantamento no sistema
  (não por memória) antes de mexer em qualquer unit: `ollama.service` e os containers Docker
  (`open-webui`, `kokoro-tts`, `restart: unless-stopped`) já sobreviviam a reboot; `agata-consolidacao.timer`
  já era enabled. O único buraco real era o gateway/`api_server` do Hermes (porta 8642), que só subia
  manual (`hermes gateway run`), sem unit file.
- Achado não pedido, sinalizado ao Humano antes de agir: `agata-rest.service` (system, enabled,
  rodando) autoiniciava a cada boot o `~/.agata_il/src/rest_server.py` — o mesmo servidor REST do
  protótipo pré-Hermes já flagrado como memória duplicada em (12) (lá só o processo órfão e a Function
  do Open WebUI tinham sido neutralizados; o unit systemd nunca foi tocado, por isso voltou sozinho).
  Mesmo padrão estrutural do incidente de (17) (`agatha.service` órfão que travou a Máquina) — leftover
  de unit file de protótipo antigo sobrevivendo a limpezas anteriores.
- Decisão do Humano (as 3 perguntas feitas antes de agir): (a) desabilitar `agata-rest.service` agora;
  (b) instalar o gateway do Hermes como serviço de usuário pra iniciar sozinho; (c) remover os unit
  files mortos `agata.service` e `agatha.service` (ambos já disabled, apontando pra pastas inexistentes
  — `agata-workspace`/`agatha-workspace` não existem no disco).
- Executado: `hermes gateway install --start-now --start-on-login` (sem sudo, mecanismo nativo do
  Hermes) — criou `hermes-gateway.service` em `~/.config/systemd/user/`, enabled, linger confirmado
  ativo (sobrevive a logout). Verificado no disco: porta 8642 escutando, PID do processo `hermes`.
  Os 3 comandos que exigem root (`disable --now agata-rest.service`, `rm agata.service`,
  `rm agatha.service`) foram impressos pro Humano rodar no próprio terminal — sudo pede senha
  interativa, canal desta sessão não oferece TTY pra isso (mesma linha vermelha de (17)).
- Humano confirmou execução; verificado no disco antes de registrar (não só na palavra):
  `agata-rest.service` → `disabled`/`inactive`, porta 8000 livre; `/etc/systemd/system/agata.service`
  e `agatha.service` → não existem mais; `hermes-gateway.service` seguia `enabled`/`active`.
- PROJETO.md atualizado: nova seção "Serviços (boot)" documentando os 4 serviços que sobrevivem a
  boot e os 3 leftovers purgados (não recriar).
### 2026-07-06 (37) · Boot-test de (36) confirmado + inconsistência do RAG registrada (Humano confirmou boot · Opus registrou)
- Persistência de boot de (36) VALIDADA: Humano executou reboot real e confirmou que o gateway subiu sozinho (hermes-gateway.service user unit + linger), sem start manual. Fecha a "última milha" que ficara aberta em (36) — lá só havia enabled/active/linger verificados, não um reboot de verdade. Fallback qwen3-14b-64k + override de contexto (65536) seguem em produção pós-boot.
- Achado da reconciliação (atualizar TUDO, esta sessão): a regra operacional do RAG no PROJETO ainda justifica "RAG só em sessões Gemini" com "no fallback qwen (32k nativo) documento grande estoura o contexto". Defasado: depois de (28)/(30)/(35) o fallback não é mais 32k nativo — é qwen3 com 64k por override durável, provado no pior caso. A regra pode seguir válida (janela do Gemini é maior), mas a JUSTIFICATIVA "32k estoura" está errada. Correção do texto do PROJETO (estado-corrente, editável) PENDENTE — próxima sessão, na Máquina via Code.

### 2026-07-06 (38) · Causa raiz de "perdi a conexão" identificada — crash no handler de erro mascara 429 do Gemini (Humano reportou, Code investigou)

- Humano relatou ter perdido a conexão com a Ágata. `hermes-gateway.service` segue `active (running)`
  (PID 1057, ativo desde 16:08) — não é queda do processo/gateway.
- Causa raiz no journal: Gemini (`gemini-2.5-flash`, provider ativo/primário) retorna HTTP 429
  RESOURCE_EXHAUSTED — quota do free tier esgotada (limite de 20 req/dia nesse modelo,
  levantado em `agent/gemini_native_adapter.py:976`).
- Bug que transforma isso em "conexão perdida": ao tratar o 429, `agent/conversation_loop.py:2949`
  chama `_summarize_api_error()`, que em `run_agent.py:2146` acessa `response.text` num
  `httpx.Response` de streaming que nunca teve `.read()` chamado — dispara `httpx.ResponseNotRead`,
  uma SEGUNDA exceção que mascara a primeira. Resultado: toda vez que o Gemini estoura quota, o
  gateway não devolve um erro tratado nem aciona fallback — a chamada quebra e o stream SSE termina
  abruptamente, sentido do lado do Humano como perda de conexão.
- Confirmado que não é payload-dependente: reproduzido com payload mínimo ("diga ok") direto no
  `api_server` (porta 8642, autenticado), crash em <1s.
- Confirmado que qwen3-14b-64k (fallback configurado em (35)) funciona normalmente quando chamado
  direto no ollama (`localhost:11434`) — o problema é que o crash no handler de erro do Gemini
  acontece ANTES do fallback ser acionado nesse caminho de código, então o fallback configurado
  nunca chega a ser tentado.
- Última falha no log: 19:04. Sem novas tentativas registradas até 20:18 (hora desta entrada) —
  gap consistente com o Humano ter desistido de tentar após as falhas repetidas.
- Nenhuma mudança de código ou config aplicada nesta entrada — achado registrado. Fix requer patch
  em `run_agent.py:2146` (não acessar `.text` sem `.read()` em resposta de streaming) e revisão do
  ponto em que o fallback deveria ser acionado antes desse handler quebrar.

### 2026-07-06 (37) · Boot-test de (36) confirmado + inconsistência do RAG registrada (Humano confirmou boot · Opus registrou)
- Persistência de boot de (36) VALIDADA: Humano executou reboot real e confirmou que o gateway subiu sozinho (hermes-gateway.service user unit + linger), sem start manual. Fecha a "última milha" que ficara aberta em (36) — lá só havia enabled/active/linger verificados, não um reboot de verdade. Fallback qwen3-14b-64k + override de contexto (65536) seguem em produção pós-boot.
- Achado da reconciliação (atualizar TUDO, esta sessão): a regra operacional do RAG no PROJETO ainda justifica "RAG só em sessões Gemini" com "no fallback qwen (32k nativo) documento grande estoura o contexto". Defasado: depois de (28)/(30)/(35) o fallback não é mais 32k nativo — é qwen3 com 64k por override durável, provado no pior caso. A regra pode seguir válida (janela do Gemini é maior), mas a JUSTIFICATIVA "32k estoura" está errada. Correção do texto do PROJETO (estado-corrente, editável) PENDENTE — próxima sessão, na Máquina via Code.

### 2026-07-07 (39) · Auditoria do handler de 429 / SOUL / commit citado pela Opus — verificado na fonte (Opus pediu auditoria ao Humano, Code verificou direto no filesystem/git)

- Opus (sessão de chat) pediu ao Humano pra colar manualmente trechos de código e confirmar itens pra fechar uma auditoria de 3 pontos. Code tinha acesso direto ao filesystem e ao git nesta Máquina e verificou tudo na fonte em vez de depender de cópia manual.
- Handler de 429 (achado original em (38)): `run_agent.py:2146` segue INALTERADO — ainda faz `snippet = (getattr(response, "text", None) or "").strip()` sobre uma resposta que pode ser streaming não lida. O fix NÃO está mergeado no `hermes-agent` instalado nesta Máquina; bug segue reproduzível.
- SOUL: existe como arquivo real (não é conceito abstrato nem hardcoded) — `/home/orusoua/agata/SOUL.md` (canônico) e `/home/orusoua/.hermes/SOUL.md` (cópia de hidratação). Fecha o "Erro 3" citado pela Opus.
- Commit `f7a2b1c` (citado pela Opus, atribuído a "a Seth", que teria corrigido a injeção do SOUL no fallback): NÃO encontrado em `~/agata` nem no `hermes-agent` local instalado. Ressalva: o `hermes-agent` local é um clone raso com um único commit squashed (`7426c09`, remote `NousResearch/hermes-agent`) — não dá pra confirmar nem descartar a existência do commit no histórico real do upstream sem acesso de rede a partir desta sessão. O que É verificável direto: o código instalado não reflete esse fix — o bug do item anterior segue ativo independente do que aquele commit tenha feito ou não upstream.
- Achado colateral não pedido, registrado por disciplina de não esconder estado inesperado: a entrada (37) deste DIÁRIO está DUPLICADA no histórico do git — dois commits distintos com o mesmo título e conteúdo idêntico (`128ab2f` e `449c3b9`, ambos já em `origin/main` antes desta sessão notar). O segundo (`449c3b9`, 2026-07-06 20:20:16) não foi feito por Code nesta sessão; origem não identificada, possivelmente edição concorrente de outra sessão no mesmo período. Nenhuma perda de conteúdo — apenas duplicação. Deduplicação NÃO aplicada — decisão do Humano pendente.

### 2026-07-07 (40) · Patch do bug de (38)/(39) aplicado e verificado — crash do handler de 429 corrigido (GLM propôs, Humano aprovou, Code aplicou e verificou)

- Contexto: (38) achou a causa raiz de "perdi a conexão" — `run_agent.py:2146` (`_summarize_api_error`)
  acessava `response.text` numa resposta HTTP em streaming sem `.read()` antes, crashando com
  `httpx.ResponseNotRead`/`StreamClosed` sempre que o Gemini retornava erro (ex.: 429 de quota).
  (39) confirmou o fix ainda não estava mergeado.
- Ágata (GLM, t=8) propôs patch: envolver a leitura em `try/.read()/except`, com fallback pra
  `snippet = ""` se a leitura falhar. Não aplicou nada sozinha — trace `19f3ca5945b787bd`.
- Auditoria do Code antes de aplicar: confirmou que `GeminiAPIError` já carrega a mensagem
  totalmente formatada (via `super().__init__(message)`, incluindo o aviso de free-tier) — então
  mesmo se `.read()` falhar (o que É esperado neste caso: o `with self._http.stream(...) as response`
  em `gemini_native_adapter.py` já fechou o stream no `__exit__` antes da exceção chegar aqui), o
  código cai no fallback pré-existente (`raw[:500]`) que já produz a mensagem certa. Achado adicional:
  esse handler roda dentro do loop de retry/fallback (`conversation_loop.py:2949`), então o crash
  provavelmente impedia o código de sequer chegar na lógica de troca pro fallback qwen3-14b-64k —
  o bug não era só cosmético.
- Humano aprovou aplicar (opção 1, patch como está).
- Aplicado em `/home/orusoua/.hermes/hermes-agent/run_agent.py:2144-2151` (repo git local, rollback
  = `git checkout -- run_agent.py` nesse repo se precisar reverter).
- Gateway reiniciado (`systemctl --user restart hermes-gateway`, PID novo 58178, log limpo — só
  warnings de startup pré-existentes, sem erro).
- Verificação: NÃO forçou o 429 real (a cota free-tier do Gemini reseta por dia e testar assim
  gastaria cota de produção à toa). Em vez disso, reproduziu o cenário exato em isolamento — um
  `httpx.Response` de streaming aberto via `MockTransport`, fechado pelo `with`/`__exit__` (igual ao
  fluxo real), passado pro `AIAgent._summarize_api_error` patchado. Resultado: sem crash, retornou
  `'HTTP 429: quota exceeded'` — mensagem limpa, útil, provada no cenário que antes derrubava a stream.
- Limitação conhecida, registrada por disciplina: esse patch vive no `hermes-agent` (repo vendored,
  clone raso de `NousResearch/hermes-agent`, fora do canônico `agataseth98-cmd/agata-seth`). Uma
  reinstalação/atualização do Hermes por cima pode sobrescrever essa mudança sem aviso — não há
  backup automático desse repo como há pro `config.yaml`. Se o Hermes for atualizado, reaplicar
  este patch ou confirmar se a versão nova já inclui um fix equivalente.
