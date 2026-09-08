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
| `cerebras/gemma-4-31b` | Cerebras | limpo (200, finish=stop, zero reasoning). Melhor aposta hoje. |
| `zai/glm-4.7-flash` | Zhipu | funciona quando a z.ai não está em 529 (sobrecarga transitória). |
| `gemini/gemini-2.5-flash` | Google | degradado (504 intermitente + ignora `thinking:disabled` e queima reasoning). Só com `max_tokens ≥ 10000`. |
| `huggingface/meta-llama/Llama-3.3-70B-Instruct` | HuggingFace | **(379)** — 200, finish=stop, ~1,3s, sem reasoning burn. Via HF Inference Providers (`router.huggingface.co`). Token precisa de `inference.serverless.write` ("Make calls to Inference Providers"). Free tier = crédito mensal pequeno; esgotou → 402 → breaker põe em cooldown. `Llama-3.1-8B-Instruct` (mesma conta) é a alternativa barata. |
| `mistral/ministral-8b-latest` | Mistral | **(379)** — 200, finish=stop, ~0,55s pelo :20127. Chave da La Plateforme com escopo "pessoal e compartilhado" (a "Studio / só compartilhado" dá 429). **`mistral/mistral-small-latest` dá 429 nesta conta** — usar só `ministral-8b` / `ministral-3b`. |
| `qwen3.5-9b-64k` (Ollama :11434) | Local | fallback final, sempre disponível. Não é opinião de família independente. |
| `llamacpp-local/qwen3-30b-a3b` | Local | MoE, fallback local alternativo. |

## Fora — não usar

| Modelo | Motivo |
|---|---|
| `groq/openai/gpt-oss-*` | Cloudflare fichou o cliente do OmniRoute como bot (`403 browser_signature_banned`), persistente; e gpt-oss queima reasoning. |
| `openrouter/auto` | **PAGO** — "Auto Best Available" da OpenRouter, não é alias grátis (o painel de Combos do OmniRoute avisa). |
| `openrouter/minimax/minimax-m3:free` | rota 404 — modelo saiu do free tier. |
| `cerebras/gpt-oss-120b` | queima o orçamento em reasoning e devolve vazio. |
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

## Combo `seth-livre` (MEMÓRIAS (390)) — a cascata do frontend da Seth

Combo **custom** do OmniRoute (`storage.sqlite`, tabela `combos`), `strategy:
priority` (tenta o 1º; falha/529/404 → próximo, sozinho). É o default da Seth no
`librechat.yaml`. Lista **curada por nós** — não a auto-derivada do `auto/*`.

| ordem | modelo | por quê |
|---|---|---|
| 1 | `zai/glm-4.7-flash` | mais capaz dos grátis; 529 transitório quando a z.ai sobrecarrega |
| 2 | `gemini/gemini-2.5-flash` | fallback histórico; teto ~20 req/dia |
| 3 | `huggingface/meta-llama/Llama-3.3-70B-Instruct` | infra independente (HF Inference Providers); crédito mensal pequeno |
| 4 | `mistral/ministral-8b-latest` | último recurso remoto; pequeno mas responde |

**Recriar** (se o `storage.sqlite` for perdido): `POST http://127.0.0.1:20128/api/combos`
com `{"name":"seth-livre","strategy":"priority","config":{},"models":[{...zai...},
{...gemini...},{...hf...},{...mistral...}]}` (cada model = `{id, kind:"model",
model:"<id>", providerId:"<prov>", weight:0}`). Sincronizar a lista acima quando
mudar.

**Lacuna conhecida:** sem tier LOCAL de último recurso — o OmniRoute só tem os
modelos de *embedding* do Ollama no catálogo, não o `qwen3.5-9b-64k` de chat. O
`conselho_remoto.py` alcança o local direto no `:11434`; a cadeia da Seth
(`:20126`→sanitizador→OmniRoute) não. Item à parte.

---

## Rotina de pesquisa/saúde (MEMÓRIAS (377))

`scripts/pesquisar_modelos_gratuitos.py`, semanal via
`config/agata-pesquisa-modelos.timer` (domingo 22:00). Read-only: re-testa o
pool + o ROSTER + os modelos do OmniRoute fora do pool, dispara o Discovery do
OmniRoute, e — **só se algo mudou** — escreve `propostas/modelos-gratuitos-<data>.md`
com um rascunho de ROSTER e o lembrete das famílias que precisam de chave.
**Nunca implementa.** O Humano aplica à mão (este .md + `ROSTER` por proposta
assinada + OmniRoute pela UI).
