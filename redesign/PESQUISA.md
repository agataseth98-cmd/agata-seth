# PESQUISA — estado da arte por ferramenta (set/2026)

Levantamento feito na sessão Claude de 01/09/2026, com busca web. Fontes no fim.
Serve para o executor fallback não reabrir a pesquisa do zero.

## Verificação por ferramenta

| Ferramenta | Estado atual | Serve para | Pegadinha |
|---|---|---|---|
| **OmniRoute** | MIT, local `:20128`, ~19 estratégias de rota, combos+breaker+cooldown, painel de custo, servidor MCP, protocolo A2A. Chaves ficam locais. | gateway único de modelo (Fase 1) | o painel próprio já é observabilidade suficiente; não montar dashboard extra |
| **LangGraph** | GA. `langgraph dev` local e grátis (grafo visual + time-travel por checkpoint + hot reload). Checkpointer configurável. | o loop de governança (Fase 4) | checkpointer default é snapshot de estado — **configurar como event-stream append-only** (ideia roubada do dsh) |
| **DeepSeek Harness (`dsh`)** | `0.1.0-rc.5`, Node 24, micro-kernel Cordis, seams: models/tools/skills/sessions/sandboxes/storage/loops/scheduling/UI. "THERE WILL BE COMPATIBILITY-BREAKING CHANGES". Session log append-only nativo. | alternativa dormente ao LangGraph | preview instável — adapter escrito com `enabled: false`, só reavaliar em tag estável |
| **Ollama** | simples, 1 binário. **Bug #10458: MoE 30B-A3B com GPU-util ruim** — modelos densos rendem mais na prática enquanto não resolvem. | só o modelo **denso 9B** (fallback) | **não roda o MoE bem** — ver correção C1 |
| **llama.cpp** (`--n-cpu-moe`) | roda 35B-A3B a 50–60 tok/s em 12–16 GB de VRAM (experts na RAM, atenção na GPU). Varrer `--n-cpu-moe` em 8/12/16/20/24/30 olhando tok/s e saturação de CPU. Fork `ik_llama.cpp` p/ CPU melhor. | o worker **MoE** (Fase 3), exposto ao OmniRoute como 2º backend | é o caminho certo p/ MoE, **não** o Ollama |
| **Qwen3-30B-A3B** | MoE 30,5 B total / ~3,3 B ativos, 128 experts (8/token), 48 camadas. Q4 ≈ 17 GB VRAM (não cabe nos 8 GB desta 4060). Já existe **Qwen3.6-35B-A3B** mais novo. | julgamento local via llama.cpp + offload de experts | não cabe todo na VRAM aqui; roda por offload, ~20–30 tok/s esperado |
| **RLM (Recursive Language Models)** | **real e empacotado**: `rlms==0.1.1` (PyPI), Prime Intellect (`verifiers` + Environments Hub), `grishahq/recursive-llm` (GitHub), artigo em Google ADK. Paper MIT dez/2025 (arXiv:2512.24601). LLM usa REPL Python p/ inspecionar o input e chamar sub-LLMs. **~100x contexto, 2–3x eficiência de token.** | spike de hidratação (Fase 5) | "RLM self-training" na Fronteira de recusas do PROJETO é **outra coisa** (treino). Isto é padrão de inferência. Conferir a tabela mesmo assim. |
| **OpenVINO** (iGPU) | Whisper / distil-whisper + NNCF int8; algoritmo chunked long-form 9x mais rápido; troca CPU↔GPU pelo parâmetro `device`, sem mudar código. Suporta iGPU Intel. | STT + embeddings pequenos (Fase 2) | **a iGPU desta máquina é UHD 32 EU (Raptor Lake-S), não Arc** — dá p/ Whisper em tempo real e modelo de embedding pequeno, e só |
| **Constrained decoding** | **XGrammar** é o default de vLLM/SGLang/TensorRT-LLM desde mar/2026 (<40 µs/token). **llguidance** (Microsoft, Earley em Rust) tem latência **menor** que geração sem restrição. **Outlines** é lento em schema complexo (compilação 40 s–10 min) e teve a pior taxa de conformidade. llama.cpp tem **GBNF nativo**. | forçar o formato dos blocos-envelope (Fase 4) | **"alignment tax / structure snowballing"**: restringir a resposta inteira distorce o raciocínio → grammar **só** no cabeçalho Regra 1 / `sync:` / eco, texto livre no corpo |
| **FastMCP 3.0** (jan/2026, v3.2.4 abr/2026) | Python, decorator, ~70% dos MCP servers em produção. **OpenTelemetry embutido.** Versionamento de componente, autorização granular, providers FileSystem/Skills/OpenAPI. `mcp.run()` stdio p/ local. | servidor MCP das ferramentas de Máquina (Fase 0) | resolve a lacuna de OTel e parte do versionamento de prompt **de graça** |
| **OpenTelemetry GenAI** | convenções GenAI + MCP ainda em status **"Development"/experimental** (mai/2026). Atributos `gen_ai.request.model`, `gen_ai.usage.input_tokens/output_tokens`, `gen_ai.response.finish_reasons`. CNCF; adotado por Datadog/Google/AWS/Azure. | tracing neutro de fornecedor (Fase 7) | schema muda — traces p/ arquivo/coletor local, **sem dashboard pesado agora** |
| **restic** vs **borg** | restic: 1 binário Go, sem deps, cross-plat, restore mais rápido, bom p/ object storage. borg: repo menor, archives montáveis, dedup ~10–15% melhor, Python/Unix. | **restic** para o tier de blobs + estado de runtime (Fase 7) | argumento de handoff: restic é 1 binário sem dep. `git bundle` continua p/ o canon. |
| **Feral GameMode** | `[custom]` em `~/.config/gamemode.ini` com `start=` / `end=`. Exemplo oficial já é "parar o compositor no launch e retomar ao sair". Config mesclada de `$HOME/.config/`. | gatilho automático do liga/desliga (Fase 7) | sintaxe confirmada — `start=/usr/local/bin/agata down`, `end=/usr/local/bin/agata up` |
| **Unsloth QLoRA** | 8–9 B treinável em 8 GB de VRAM (6–6,5 GB), 1–2 h. Unsloth 2x mais rápido que HF baseline, 70% menos VRAM. Unsloth Desktop no-code. | LoRA de formato Agata p/ o 4B (Fase 5, opcional) | precisa da VRAM livre → `agata down` antes de treinar |
| **Fallback executor CLI** | landscape consolidou em Claude Code / Codex CLI / OpenCode. **Codex CLI não roda modelo local** (só infra OpenAI). **Goose** e **OpenCode** são agnósticos (MIT/Apache), apontam p/ OmniRoute; Goose "automação além de código". | shell operacional de fallback (Fase 8) = **Goose**; Codex CLI é terciário (só com cota OpenAI) | Codex CLI depende de cota OpenAI e não faz modelo local |
| **obsidian-local-rest-api** | serve **MCP nativo** em `https://127.0.0.1:27124/mcp/` desde jul/2026, bearer token. Claude Code e Cursor conectam direto. | superfície MCP de leitura do vault (Fase 6) | o loop local lê os `.md` direto do disco — não depende do Obsidian estar aberto |
| **Pool nuvem free** | Groq (Llama 3.3 70B ~320 tok/s; ~30 RPM / 1000 RPD / 100K TPD). Cerebras (modelo 120B; 30 RPM / 14.400 RPD / 1M TPD). Google AI Studio cortou cota no fim de 2025. GitHub Models, OpenRouter `:free`, Mistral free. Lista curada: `awesome-free-llm-apis`. | tiers de raciocínio atrás do OmniRoute (Fase 1) | **limites mudam sempre** — os combos + breakers do OmniRoute absorvem; a lista curada é a fonte da verdade |
| **Qwen3.8-Flash-Next** | aberto (Qwen Community 1.0), MoE **125 B total / 6 B ativos** + componente n-gram de 51 B, contexto 262 k nativo → 1 M, multimodal, prévia da arquitetura Qwen4. Lançado 26/08/2026. | tier de nuvem no OmniRoute | **não roda local nesta máquina** (125 B não cabe em 8 GB VRAM + 38 GB RAM). É escolha de nuvem, não de worker local. |

## Correções que a pesquisa forçou no plano

- **C1 — MoE não roda bem no Ollama (bug #10458).** O worker MoE roda em **llama.cpp direto**
  (`--n-cpu-moe` varrido 8→30), exposto ao OmniRoute como 2º backend local. Ollama fica só
  com o denso 9B. Cotar **Qwen3.6-35B-A3B** junto do 30B-A3B. Alternativa conservadora:
  9B + LoRA é o worker e o MoE é experimento da Fase 5.
- **C2 — iGPU é UHD 32 EU, não Arc.** Expectativa realista na Fase 2: distil-whisper int8 em
  tempo real + 1 modelo de embedding pequeno (bge-small / e5-small). Nada além disso na iGPU.
- **C3 — grammar só no envelope.** GBNF (llama.cpp nativo) no cabeçalho Regra 1 / `sync:` /
  eco. **Nunca** na resposta inteira — distorce raciocínio (tax medido). Na nuvem,
  `response_format`/JSON-schema onde o provedor suporta (Groq, Gemini); validação pós-hoc
  onde não.
- **C4 — FastMCP 3.0 é o servidor MCP das ferramentas** (Fase 0). Traz OTel e versionamento
  de componente embutidos — encolhe a Fase 7.
- **C5 — OTel: sem dashboard pesado.** Convenções GenAI ainda mudam. Traces → arquivo /
  coletor local, visão sob demanda.
- **C6 — restic, não borg**, para blobs/estado de runtime — 1 binário, zero dep, argumento
  de handoff. `git bundle` continua para o canon.
- **C7 — fallback shell operacional = Goose** (ou OpenCode), apontado para o OmniRoute.
  Codex CLI é terciário (só com cota OpenAI, sem modelo local).
- **C8 — LoRA exige `agata down`** (precisa da VRAM). A tarefa de treino assume o sistema
  parado — encaixa no liga/desliga da Fase 7.

## Fontes

- RLM: primeintellect.ai/blog/rlm · github.com/grishahq/recursive-llm · introl.com/blog/recursive-language-models-rlm-context-management-2026
- Qwen MoE: apxml.com/models/qwen3-30b-a3b · github.com/ollama/ollama/issues/10458 · mychen76.medium.com (35B-A3B em 6GB via llama.cpp) · openclawdc.com/blog/llama-cpp-moe-offload-flags-explained
- OpenVINO/Whisper: blog.openvino.ai (Whisper + NNCF) · github.com/openvinotoolkit/openvino.genai
- Constrained decoding: arxiv 2601.04426 (XGrammar-2) · github.com/guidance-ai/llguidance · arxiv 2604.06066 (alignment tax)
- FastMCP: github.com/PrefectHQ/fastmcp · firecrawl.dev/blog/fastmcp-tutorial-building-mcp-servers-python
- OTel GenAI: opentelemetry.io/blog/2026/genai-observability · mlflow.org/docs/latest/genai/tracing/opentelemetry/genai-semconv
- Free APIs: openrouter.ai/blog/tutorials/free-llm-apis-compared · github.com/amardeeplakshkar/awesome-free-llm-apis · wetheflywheel.com/en/ai-model-access/free-llm-api-tiers-2026
- restic vs borg: servercrate.net/restic-vs-borg · matthewswong.com/en/blog/restic-vs-borg-encrypted-backups
- GameMode: github.com/FeralInteractive/gamemode · example/gamemode.ini
- CLI agents: amux.io/blog/best-terminal-ai-coding-agents-2026 · codex.danielvaughan.com/2026/04/09/opencode-vs-codex-cli
- Unsloth: sitepoint.com/fine-tune-local-llms-2026 · promptquorum.com/local-llms/fine-tuning-local-llms-lora
- Obsidian: github.com/coddingtonbear/obsidian-local-rest-api · mcp.directory/blog/obsidian-mcp-complete-guide-2026
- OmniRoute: github.com/pitbaden/omniroute · explainx.ai/blog/omniroute-ai-gateway-free-llm-proxy-claude-code-2026
- dsh: thenewstack.io/deepseek-harness-open-source-plugins · digitalapplied.com/blog/deepseek-harness-open-source-agent-framework-2026
- LangGraph: langchain.com/blog/langgraph-platform-ga · ema.ai (alternativas)
