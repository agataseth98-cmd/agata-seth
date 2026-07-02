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
