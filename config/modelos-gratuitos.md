# Pool de modelos gratuitos — fonte única de verdade

Criado em MEMÓRIAS (376). Este arquivo é a lista de referência dos modelos
gratuitos que o sistema usa como fallback. **Não é executado por nada** — é o
documento que o Humano mantém em sincronia com os dois mecanismos que de fato
roteiam:

1. **Seth / uso geral** → LibreChat aponta pra combo custom **`seth-livre`** do
   OmniRoute (`redesign/librechat/librechat.yaml`, default). Ver "Combo
   seth-livre" abaixo. **Antes era `auto/best-free`** — trocado em MEMÓRIAS (390):
   o `auto/*` deriva a lista de candidatos sozinho (radar/discovery) e apodreceu
   (tentava modelos arquivados/404 e deixava a Seth muda). `auto/best-free` fica
   como alternativa manual, pra quando o auto-roteador do OmniRoute se recuperar.
   Config do roteador: OmniRoute → Configurações → Global Routing (ligar
   **"Reasoning token buffer"**; **"Hide paid models"** tira Claude/GPT da
   seleção automática).
2. **Conselho Remoto** → roster próprio em `scripts/conselho_remoto.py`
   (`ROSTER`), com rotação justa + circuit breaker + portão + fallback local
   (MEMÓRIAS (374)). NÃO usa combo (decisão de (352): ninguém tem papel fixo).

Trocar o pool = editar este arquivo + a `ROSTER` do `conselho_remoto.py` (por
proposta assinada) + os combos/roteador do OmniRoute (pela UI). O OmniRoute é
produto de terceiros — não dá pra sincronizar automático; este .md é o elo.

---

## Confirmado funcionando (testado ao vivo em 08/09/2026)

| Modelo (id OmniRoute) | Família | Nota |
|---|---|---|
| `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` | OpenRouter | **novo, 20/09/2026** — testado ao vivo pelo :20127: 200, finish=stop, responde limpo até com `max_tokens` pequeno (sem reasoning burn no teste curto), 1M de contexto. Substitui `cerebras/gemma-4-31b` no ROSTER (ver "Fora"). Free tier do OpenRouter é volátil — reconferir antes de depender pesado. |
| `zai/glm-4.7-flash` | Zhipu | funciona quando a z.ai não está em 529 (sobrecarga transitória). |
| `gemini/gemini-2.5-flash` | Google | degradado (504 intermitente + ignora `thinking:disabled` e queima reasoning). Só com `max_tokens ≥ 10000`. |
| `huggingface/meta-llama/Llama-3.3-70B-Instruct` | HuggingFace | **QUEBRADO desde 16/09/2026** — a conexão `agata-free` no OmniRoute está `isActive:false`, chave marcada `apiKeyHealth: invalid` (última falha 16/09 14:21 UTC). O token em `~/.config/agata/.env` (`HF_TOKEN`) é o MESMO que está cadastrado — não adianta reenviar, precisa de um token novo. **Ação do Humano:** gerar token novo em `huggingface.co/settings/tokens` com escopo `inference.serverless.write`, atualizar `HF_TOKEN` no `.env`, e reativar com `printf '%s' "$HF_TOKEN" \| omniroute keys add huggingface --stdin` (ou pela UI). Deixado no ROSTER — o circuit breaker já pula pra próxima família sozinho, sem quebrar nada (visto ao vivo em (466)/(467)). |
| `mistral/ministral-8b-latest` | Mistral | **(379)** — 200, finish=stop, ~0,55s pelo :20127. Chave da La Plateforme com escopo "pessoal e compartilhado" (a "Studio / só compartilhado" dá 429). **`mistral/mistral-small-latest` dá 429 nesta conta** — usar só `ministral-8b` / `ministral-3b`. |
| `qwen3.5-9b-64k` (Ollama :11434) | Local | fallback final, sempre disponível. Não é opinião de família independente. |
| `llamacpp-local/qwen3-30b-a3b` | Local | MoE, fallback local alternativo. |

## Candidatos testados, funcionam, fora do ROSTER por ora (20/09/2026)

Achados pesquisando o catálogo `:free` ao vivo da OpenRouter
(`openrouter.ai/api/v1/models`, filtro `pricing.prompt==0` — 24 modelos grátis
hoje, lista rotativa). Testados pelo :20127, um por um. Não entraram no ROSTER
pra não inflar com duas entradas da mesma família (`openrouter`) — `_familia()`
em `conselho_remoto.py` classifica qualquer `openrouter/...` como família única.

| Modelo | Estado testado | Nota |
|---|---|---|
| `openrouter/google/gemma-4-31b-it:free` | OK, sem reasoning burn | mesmo peso do `cerebras/gemma-4-31b` banido, por rota diferente — candidato natural se o de cima cair |
| `openrouter/z-ai/glm-5.2:free` | OK, mas só com `max_tokens` alto (queima 106/109 num teste de 6000) | GLM mais novo que o `zai/glm-4.7-flash` da tabela de cima; precisaria de entrada em `MAX_TOKENS_POR_MODELO` |
| `openrouter/nvidia/nemotron-3.5-lightning:free` | OK, mesma ressalva de reasoning burn (271/285 tokens) | 1M contexto |
| `openrouter/qwen/qwen3.8-27b:free` | timeout nas 2 tentativas | provavelmente cold/sobrecarregado agora — reconferir depois |

## Fora — não usar

| Modelo | Motivo |
|---|---|
| `cerebras/gemma-4-31b` | **Reconfirmado banido, 20/09/2026 (sessão da tarde, horário exato não registrado no momento do teste — falha minha, corrigida aqui em vez de inventar).** Cloudflare, `error_name: browser_signature_banned`, `retryable: false`, `owner_action_required: true` (`ray_id a3e1ee6c5ed24ceb`, zona `api.cerebras.ai`) — o texto do próprio erro diz pra não reenviar, é o user-agent do OmniRoute banido pelo dono do site (Cerebras), não credencial nem cota. Mesma classe do bloqueio do Groq abaixo. Achado externo, não confirmado por nós: uma busca (20/09/2026) sugere que a Cerebras trocou o free tier por um trial de US$5 com cartão — **não verificado na fonte primária** (`cloud.cerebras.ai`), citado aqui só como pista pro Humano conferir, nunca como fato. |
| `cerebras/gpt-oss-120b` | **Reconfirmado banido, 20/09/2026 — mesmo bloqueio Cloudflare da linha de cima, mesmo teste ao vivo.** Isto CONTRADIZ a linha "SUPERADO" abaixo, que dizia essa entrada ter voltado a funcionar em (416) — e é hoje o **tier 0** dos três combos da Seth (`seth-rapido`/`seth-livre`/`seth-pesado`, ver seção abaixo), que agora cai pro tier 1 em toda chamada. Nada quebra (o `priority` do OmniRoute já faz o fallthrough sozinho, testado), só fica mais lento. Riscado, não apagado, pelo mesmo motivo da linha de baixo: a avaliação MUDA de novo, fingir que nunca oscilou é que seria desonesto. |
| `groq/openai/gpt-oss-*` | Cloudflare fichou o cliente do OmniRoute como bot (`403 browser_signature_banned`), persistente; e gpt-oss queima reasoning. Reconfirmado ao vivo 20/09/2026 — mesmo bloqueio, ainda não recuperou. |
| `openrouter/auto` | **PAGO** — "Auto Best Available" da OpenRouter, não é alias grátis (o painel de Combos do OmniRoute avisa). |
| `openrouter/minimax/minimax-m3:free` | rota 404 — modelo saiu do free tier. |
| ~~`cerebras/gpt-oss-120b`~~ | **[SUPERADO por (416), 09/09/2026 — não está mais fora.]** O motivo antigo era "queima o orçamento em reasoning e devolve vazio". Medição nova, ao vivo: grátis, ~0,4s, tools+stream OK — virou **tier 0** dos três combos da Seth (tabela abaixo). Esta linha ficou aqui contradizendo a de baixo até a auditoria de (419) achar; mantida riscada em vez de apagada porque saber que a avaliação MUDOU vale mais que fingir que nunca houve a outra. Intermitente: quando cai, o `priority` desce sozinho. **[Por sua vez superada de novo, 20/09/2026 — ver a linha nova de `cerebras/gpt-oss-120b` acima. Oscila; as duas notas ficam, não se apaga história de config também.]** |
| **GitHub Models** (`models.github.ai`) | **descontinuado pela GitHub** — `410 github_models_retirement_brownout` ("scheduled retirement"), 08/09/2026. Não há slug de provedor pra ele neste build do OmniRoute de qualquer forma. |
| `mistral/mistral-small-latest` | `429 code 1300` nesta conta (free tier). Usar `mistral/ministral-8b-latest` no lugar (tabela de cima). |

## Candidatos — precisam de chave do Humano em `~/.config/agata/.env`

Depois da chave: configurar o provedor no OmniRoute (Provedores → Adicionar),
1 chamada de teste ao vivo, e então entrar no `auto/*` / `ROSTER` por proposta.

| Provedor | Família | Free tier (set/2026) | OpenAI-compat |
|---|---|---|---|
| Cloudflare Workers AI | Cloudflare | 10.000 neurons/dia | parcial |
| NVIDIA NIM | NVIDIA | prototipagem, sem limite publicado | parcial |

Descartados por não serem free tier de verdade: SambaNova / Fireworks / AI21
(créditos que expiram). Cohere: só avaliação (1.000 chamadas/mês).

**Integrados em 08/09/2026 (MEMÓRIAS (379)):** HuggingFace e Mistral saíram
desta lista pra tabela "Confirmado". Conexões criadas no OmniRoute
(`provider=huggingface` / `provider=mistral`, ambas `isActive:true`). GitHub
Models foi pra "Fora — não usar" (descontinuado).

---

## 3 modelos locais novos, instalados 20/09/2026 (ordem do Humano; um 4º tentado, travou)

Baixados via `llama.cpp` (mesmo motor do `Qwen3-30B-A3B-Instruct-2507` já em produção,
`redesign/router/llamacpp.md`), GGUF em `~/.cache/agata/models/`. Cada um tem seu próprio
serviço systemd (`~/.config/systemd/user/llamacpp-<nome>.service`, **sob demanda**, sem
`enable` — mesmo padrão do `llamacpp-agata` original: não cabem todos rodando ao mesmo
tempo nos 38GB de RAM desta Máquina) e sua própria conexão no OmniRoute (catálogo
`llama-cpp`, uma por porta — o CLI `omniroute providers add llama-cpp --provider-specific-data
'{"baseUrl":"http://127.0.0.1:<porta>/v1"}'` permite múltiplas conexões do mesmo tipo
catálogo, distinguidas pelo `defaultModel`/porta, não por um `provider` customizado).

| Modelo | Porta | RAM (Q4_K_M) | Papel | Ajuste de offload |
|---|---|---|---|---|
| `llama-cpp/nemotron-3.5-lightning` | 20142 | **23,7GB** (Q4_K_M, medido — corrigido de um ~19GB citado antes, de um quant Q4_0 diferente) | Geral/conversação — tier 0 do `seth-livre` (LibreChat) | **`--n-cpu-moe 44`**, confirmado pela bancada. `36` (copiado do Qwen3-30B-A3B) deu OOM ao carregar. `42` passou no `llama-bench` (que testa com prompt/gen curtos, sem reservar o `-c 8192` inteiro) mas **falhou no servidor real** com `-c 8192` — 1,1GB faltando no buffer de computação. `llama-bench` não é proxy confiável de VRAM do servidor real quando o contexto configurado é grande; só o teste com o `-c` de produção prova. `44` é o mínimo real que carrega com `-c 8192`: **75,2 tok/s prompt-processing, 24,6 tok/s geração** (`llama-bench -p 128 -n 128 -r 3`), 7081MiB de VRAM (~86%, mais apertado que os ~76% do Qwen3-30B-A3B original). **Precisa de `max_tokens` alto** — mesmo padrão do Gemini: com 400 devolveu vazio (`finish=length`, todo o orçamento em reasoning); com 3000 respondeu certo usando só 622 no total. `MAX_TOKENS_POR_MODELO["llama-cpp/nemotron-3.5-lightning"] = 6000` no `conselho_remoto.py`. Testado ao vivo direto, pelo OmniRoute e pelo combo `seth-livre`. |
| `llama-cpp/qwen3-coder-30b-a3b` | 20143 | 17,3GB (Q4_K_M, medido) | Código — tier 0 do `seth-codigo` (Goose) e do `seth-pesado` | `--n-cpu-moe 36` (mesmo do Qwen3-30B-A3B original, mesmo tamanho de modelo) — **102,2 tok/s prompt-processing, 23,7 tok/s geração** (`llama-bench`), 6967MiB de VRAM (~85%) com `-c 16384`. Testado ao vivo: 200, `finish=stop`, resposta de código correta, margem mais apertada que o Qwen3-30B-A3B original (~1,2GB de folga contra ~1,6GB). |
| `llama-cpp/phi-4-mini` | 20145 | 2,5GB (Q4_K_M, medido) | Leve/rápido — tier 0 do `seth-rapido` | denso, `-ngl 999` sem offload de MoE (não é MoE) — cabe inteiro na GPU. **4097 tok/s prompt-processing, 86,5 tok/s geração** (`llama-bench`). Testado ao vivo: 200, `finish=stop`, sem reasoning burn. |

**`llama-cpp/gpt-oss-20b` NÃO ENTROU — trava, não é gap de tuning, é bug real (20/09/2026).**
Baixado (11,6GB, hash bate com o repo), serviço systemd criado (porta 20144), mas o
`llama-server` (build 10964, commit `b29c606e28`) crasha em TODA chamada de
`chat/completions`, sempre no primeiro token:
```
llama-server: .../llama-sampler.cpp:1211: void llama_sampler_dist_apply(...): Assertion `found' failed.
```
3 tentativas de contorno, todas o mesmo crash: com `--jinja`, com sampling permissivo
(`--temp 1.0 --top-k 0 --top-p 1.0 --min-p 0.0`), e sem `--n-cpu-moe` nenhum (esse último
só provou que sem offload o modelo nem carrega — precisa de 11,2GB de buffer CUDA, a
placa tem 8GB). Não é parâmetro errado, é incompatibilidade entre este quant
(`unsloth/gpt-oss-20b-GGUF`) e esta versão do llama.cpp com split de MoE — a mesma classe
de risco que a ressalva "não rebenchmarcado" abaixo já cobria, só que descoberta na
prática em vez de só declarada. Arquivo e unit ficam no disco (`llamacpp-gptoss20b.service`,
parado) pra quem quiser investigar depois (outro quant — `bartowski`/`ggml-org` — ou
versão nova do llama.cpp). Não está em ROSTER nem em combo nenhum.

**Bancada rodada em 20/09/2026** (fechando o gap declarado antes): números de tokens/s
na tabela acima, `llama-bench -p 128 -n 128 -r 3` por modelo, no `--n-cpu-moe` que o
servidor real usa. `lacuna` que continua: tokens/s sob CARGA SUSTENTADA (várias chamadas
seguidas, concorrência) — a bancada mede uma janela curta, não o comportamento em uso
contínuo real.

**Pesquisa que embasou a escolha** (WebSearch, 20/09/2026, dado externo — não confirmado
por medição própria além do teste de fumaça acima): Nemotron-3.5-Lightning é MoE híbrido
mamba+atenção, ~3B ativos de 30B, lançado ago/2026, GGUF de terceiros (`bartowski`,
`unsloth`, `ggml-org`). Qwen3-Coder-30B-A3B é a variante de código da mesma arquitetura
MoE do modelo já em produção. gpt-oss-20b é o irmão menor do `gpt-oss-120b` que a Seth já
usa via Cerebras/Groq na nuvem — mesma família, mesmo desenho agentic. Phi-4-mini é o
menor viável (3,8B) segundo os comparativos consultados. `gpt-oss-120b` (~63GB em
Q4_K_M, medido) foi **descartado** — não cabe com folga nos 38GB de RAM desta Máquina.

## Combos da Seth + roteador por complexidade (MEMÓRIAS (390), roteador em (416); ampliado 20/09/2026)

4 combos **custom** do OmniRoute (`storage.sqlite`, tabela `combos`), todos
`strategy: priority` (tenta o 1º; falha/529/404 → próximo, sozinho). Lista
**curada por nós** — não a auto-derivada do `auto/*`.

- **LibreChat** (chat, prioriza conversação): Agent aponta pra `seth-livre`; o
  **`seth_gateway`** reescreve pra `seth-rapido`/`seth-pesado` por heurística de
  complexidade (MEMÓRIAS (416), reabre (383)) — só quando o Agent pede `seth-livre`,
  specs manuais passam intactas.
  - **`seth-rapido`** (trivial: <400 chars, sem `tools`, ≤2 msgs user)
  - **`seth-livre`** (normal — tudo que não é trivial nem pesado)
  - **`seth-pesado`** (>6000 chars OU cerca de código OU >10 msgs)
- **Goose** (`~/.config/goose/config.yaml`, `model: seth-codigo`, 20/09/2026 —
  **antes** apontava pra `auto/coding`, um alias que o próprio PROJETO.md já
  documentava como apodrecido desde (390); nunca tinha sido atualizado pro sistema de
  combos novo): sempre `seth-codigo`, sem heurística — Goose é sempre trabalho de
  código, não precisa de tiering por tamanho.

Princípio novo, 20/09/2026: **Cerebras e Groq nunca são tier 0 em combo nenhum.** Os
dois estão atrás do Cloudflare do próprio provedor e já levaram bloqueio persistente
duas vezes (`groq/openai/gpt-oss-*` desde antes; `cerebras/gemma-4-31b` e
`cerebras/gpt-oss-120b` reconfirmados banidos em 20/09 — ver "Fora — não usar").
Hipótese de trabalho, não provada: martelar os dois como primeira tentativa em todo
combo, toda hora, é tráfego repetitivo pro mesmo endpoint — o padrão que detector de
bot de Cloudflare mais pune. Os dois continuam no sistema, só como última tentativa
remota antes do fallback local, nunca na frente.

### `seth-rapido` (LibreChat, trivial)
| ordem | modelo | por quê |
|---|---|---|
| 0 | `llama-cpp/phi-4-mini` | **novo, local, $0** — leve, resposta rápida pra pedido trivial |
| 1 | `zai/glm-4.7-flash` | estável quando a z.ai não está em 529 |
| 2 | `cerebras/gpt-oss-120b` | oportunista — banido agora, entra se recuperar |
| 3 | `ollama-local/qwen3.5-9b-64k:latest` | fundo local, sempre disponível |

### `seth-livre` (LibreChat, rota normal — favorece conversação)
| ordem | modelo | por quê |
|---|---|---|
| 0 | `llama-cpp/nemotron-3.5-lightning` | **novo, local, $0** — geral/conversação, poupa token de nuvem |
| 1 | `zai/glm-4.7-flash` | mais capaz dos free-tier estáveis |
| 2 | `gemini/gemini-2.5-flash` | fallback histórico; teto ~20 req/dia |
| 3 | `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` | backup em nuvem do mesmo peso do tier 0, se o local cair |
| 4 | `huggingface/meta-llama/Llama-3.3-70B-Instruct` | infra independente; crédito mensal pequeno |
| 5 | `mistral/ministral-8b-latest` | último recurso remoto pequeno |
| 6 | `cerebras/gpt-oss-120b` | oportunista — banido agora |
| 7 | `ollama-local/qwen3.5-9b-64k:latest` | fundo local final |

### `seth-pesado` (LibreChat, >6000 chars OU código OU >10 msgs)
| ordem | modelo | por quê |
|---|---|---|
| 0 | `llama-cpp/qwen3-coder-30b-a3b` | **novo, local, $0** — cobre o gatilho "código" direto, sem sair da Máquina |
| 1 | `gemini/gemini-2.5-flash` | contexto grande, `max_tokens ≥ 10000` |
| 2 | `huggingface/meta-llama/Llama-3.3-70B-Instruct` | independente, crédito pequeno |
| 3 | `cerebras/gpt-oss-120b` | oportunista |
| 4 | `ollama-local/qwen3.5-9b-64k:latest` | fundo local final |

### `seth-codigo` (Goose — novo, 20/09/2026)
| ordem | modelo | por quê |
|---|---|---|
| 0 | `llama-cpp/qwen3-coder-30b-a3b` | **especialista em código, local, $0** |
| 1 | `zai/glm-4.7-flash` | generalista capaz, cobre código também |
| 2 | `gemini/gemini-2.5-flash` | contexto grande |
| 3 | `huggingface/meta-llama/Llama-3.3-70B-Instruct` | independente |
| 4 | `mistral/ministral-8b-latest` | pequeno, último remoto |
| 5 | `cerebras/gpt-oss-120b` | oportunista |
| 6 | `ollama-local/qwen3.5-9b-64k:latest` | fundo local final |

**Recriar / reverter** (se o `storage.sqlite` for perdido):
`PUT http://127.0.0.1:20128/api/combos/<id>` (existente) ou `POST /api/combos` (novo),
corpo `{"name":"<nome>","strategy":"priority","models":[…]}`, cada model =
`{id, kind:"model", model:"<id>", weight:0}`. IDs: `seth-livre`
`563700ea-bf7d-45f0-97ab-c336f84b2361` · `seth-rapido`
`d37e5f27-d216-4e85-94f5-3621ad860260` · `seth-pesado`
`3980b8a1-776b-475a-9e8b-76c65f1e6cf5` · `seth-codigo` (criado 20/09/2026, POST —
`id` fica no `.diff`/log da sessão, não fixado aqui à mão pra não citar de memória).
Sincronizar as tabelas acima quando mudar.

O fundo LOCAL usa a connection `ollama-local` já existente (`baseUrl`
`http://127.0.0.1:11434`). O OmniRoute repassa a string do `model` depois do prefixo
direto pro Ollama — testado ao vivo em (403): `ollama-local/qwen3.5-9b-64k:latest`
roteia e responde (não-stream e stream). A tag `-64k` (com `PARAMETER num_ctx 65536`
no Modelfile — PROJETO.md "Cérebro") tem que vir explícita no `model`; nunca
`qwen3.5:9b` crua, que reproduz (121)/#16814. **Não há shim:** o `seth_local_shim` de
(402) foi retirado em (403) — o OmniRoute já alcançava o modelo local, o shim era
cano a mais.

---

## Rotina de pesquisa/saúde (MEMÓRIAS (377))

`scripts/pesquisar_modelos_gratuitos.py`, semanal via
`config/agata-pesquisa-modelos.timer` (domingo 22:00). Read-only: re-testa o
pool + o ROSTER + os modelos do OmniRoute fora do pool, dispara o Discovery do
OmniRoute, e — **só se algo mudou** — escreve `propostas/modelos-gratuitos-<data>.md`
com um rascunho de ROSTER e o lembrete das famílias que precisam de chave.
**Nunca implementa.** O Humano aplica à mão (este .md + `ROSTER` por proposta
assinada + OmniRoute pela UI).
