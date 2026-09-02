# PROVEDORES.md — pool de modelos atrás do OmniRoute (Fase 1, P1-03)

## Estado (2026-09-02 ~08:45) — chaves do Humano já estavam em `~/.hermes/.env`

`~/.hermes/.env` já tinha `GROQ_API_KEY`, `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`,
`GOOGLE_API_KEY`, `ZHIPU_API_KEY`. Registrei os 5 providers no OmniRoute (valores lidos do
`.env` para env vars, nunca impressos): `groq`, `deepseek`, `openrouter`, `gemini`, `zai`.

| provider | status | model ID que **funciona** (id RAW, não o nome do catálogo) | nota |
|---|---|---|---|
| `ollama-local` | active | `ollama-local/qwen3.5:9b`, `ollama-local/llama3.2:3b` | local, $0 |
| `groq` | **active** ✅ | **`groq/openai/gpt-oss-120b`** (~450 ms) | Groq **aposentou** `llama-3.3-70b-versatile`; o erro "model 'llama 3.3 70b'…" era breaker em cooldown + default velho. Re-registrado com `--default-model openai/gpt-oss-120b`. |
| `gemini` | active | **`gemini/gemini-2.5-flash`** (~2 s) | free tier do `GOOGLE_API_KEY`; ~$0,01 num parecer de 3,5k tok |
| `openrouter` | **active** ✅ | **`openrouter/minimax/minimax-m3:free`** (~1,2 s) | os `:free` rotacionam — lista viva em `openrouter.ai/api/v1/models` filtrando `pricing.prompt==0` |
| `zai` (GLM) | active | **`zai/glm-4.7-flash`** (5–13 s, oscila) | p/ `conselho`; quando passa de 15 s (`maxWaitMs`) cai no fallback |
| `deepseek` | registrado, `credits_exhausted`, **fora dos combos** | — | chave dá **402 Insufficient Balance** — a conta precisa de crédito (`platform.deepseek.com`) |
| `cerebras` | registrado 09/02, `credits_exhausted`, **fora dos combos** | `cerebras/gpt-oss-120b` (quando ativar) | chave OK (52 chars, `csk-`); modelos `gpt-oss-120b`, `gemma-4-31b`. **402 "Visit your billing tab"** — a Cerebras exige ativar billing (cartão) mesmo p/ o free. Ver INSTALAR-CEREBRAS. |

**Combos finais (2026-09-02, todos testados pelo proxy `:20127`, 1 req limpa cada):**
| combo | entradas (priority) | teste |
|---|---|---|
| `cheap` | `ollama-local/llama3.2:3b` → `groq/openai/gpt-oss-120b` → `openrouter/minimax/minimax-m3:free` | ✅ roteia (Ollama) |
| `auto` | `groq/openai/gpt-oss-120b` → `gemini/gemini-2.5-flash` → `ollama-local/qwen3.5:9b` | ✅ roteia (Groq) |
| `conselho` | `zai/glm-4.7-flash` → `gemini/gemini-2.5-flash` | ✅ **parecer real**; fallback GLM→Gemini disparou num teste |

> **Nota de operação:** rajadas de requisições em paralelo esgotam o pool de conexão do
> Gemini (`exhausted_connection`) e a Z.AI dá 529 transiente sob carga. Uso normal
> (1 pedido por vez) não vê isso. Quando `cerebras`/`deepseek` ativarem billing, pôr
> `cerebras/gpt-oss-120b` no meio de `cheap`/`auto` (entre o Groq e o fallback).

**Fallback verificado com falha real:** combo `[deepseek (402) → groq]` → resposta veio do
Groq. `omniroute cost` conta por provedor.

**P1-03 FEITO.** Quando `cerebras` entrar, acrescentar `cerebras/<modelo>` no meio de
`cheap`/`auto`. Quando a conta DeepSeek tiver crédito, reincluir `deepseek/deepseek-v4-flash`.

---

## INSTALAR-CEREBRAS (para o Humano)

Passos 1-4 **feitos** 2026-09-02 — a chave está no `.env` e o provider está registrado no
OmniRoute. **Bloqueio:** a Cerebras devolve `402 "Visit your billing tab"` — o tier grátis
dela agora exige ativar o billing.

**Passo 5 — ativar o billing (só você faz):**
1. Abrir **`https://cloud.cerebras.ai`** → menu lateral → **Billing** (ou **Settings → Billing**).
2. Adicionar um método de pagamento. O free tier continua grátis (não cobra dentro da
   cota), mas a Cerebras exige o cartão cadastrado para liberar o acesso à API.
3. Conferir no dashboard que a cota/quota aparece como ativa.
4. Avisar o Claude — ele re-testa `cerebras/gpt-oss-120b` e, se responder, põe
   `cerebras/gpt-oss-120b` no meio de `cheap` e `auto` (entre o Groq e o fallback).

Se você preferir não cadastrar cartão: o pool atual (Ollama + Groq + Gemini + OpenRouter)
já cobre `cheap`/`auto` com folga. Cerebras é ganho de velocidade, não necessidade.

---

## (Histórico) plano quando as chaves ainda não existiam

## Comandos (rodar quando as chaves existirem no `~/.hermes/.env`)

```fish
# 1. carregar as chaves no ambiente da sessão que roda o omniroute CLI:
#    (o OmniRoute lê do ambiente do processo)
for L in (grep -E '^(GROQ|CEREBRAS|DEEPSEEK|GITHUB_MODELS|OPENROUTER|MISTRAL|ZHIPU|GOOGLE)_' ~/.hermes/.env)
    set -x (string split -m1 '=' $L)
end

# 2. adicionar cada provider (o --api-key le do ambiente se passar o nome da env;
#    se o omniroute exigir o valor, usar "$GROQ_API_KEY" etc. -- NUNCA colar literal):
omniroute setup --add-provider --non-interactive --provider groq        --provider-name "Groq"        --api-key "$GROQ_API_KEY"        --default-model "llama-3.3-70b-versatile"
omniroute setup --add-provider --non-interactive --provider cerebras    --provider-name "Cerebras"    --api-key "$CEREBRAS_API_KEY"
omniroute setup --add-provider --non-interactive --provider deepseek    --provider-name "DeepSeek"    --api-key "$DEEPSEEK_API_KEY"    --default-model "deepseek-chat"
# GitHub Models / OpenRouter / Mistral: conferir o --provider id em `omniroute providers available`

# 3. preencher os combos (substituir os provider/model reais):
omniroute combo delete cheap; omniroute combo create cheap --strategy priority \
  --models "ollama-local/qwen3.5:9b,groq/llama-3.3-70b-versatile,cerebras/<modelo>,deepseek/deepseek-chat"
omniroute combo delete auto;  omniroute combo create auto  --strategy priority \
  --models "cerebras/<modelo>,groq/llama-3.3-70b-versatile,openrouter/<modelo>:free"

# 4. testar fallback: parar o Ollama, pedir model="cheap", ver vir do 2o provedor:
systemctl --user stop ollama    # ou o gerenciador dele
curl -s http://127.0.0.1:20127/v1/chat/completions -H 'content-type: application/json' \
  -d '{"model":"cheap","messages":[{"role":"user","content":"ok"}]}' | head -c 400
systemctl --user start ollama
```

## Circuit breaker / cooldown — defaults do OmniRoute 3.8.50 (usados como estão)

`omniroute resilience status` (02/09/2026):

| mecanismo | valor (apikey) | valor (oauth) |
|---|---|---|
| providerBreaker `failureThreshold` | **12** | 8 |
| providerBreaker `degradationThreshold` | 7 | 5 |
| providerBreaker `resetTimeoutMs` | **30 000** (30 s) | 60 000 (60 s) |
| connectionCooldown `baseCooldownMs` | 3 000 (backoff até 5 passos, usa retry-hints) | 5 000 (8 passos) |
| requestQueue | 60 rpm · 350 ms entre req · 6 concorrentes · maxWait 15 s | — |
| comboCooldownWait | enabled · maxWait 90 s · maxAttempts 5 · budget 300 s | — |

Ajustar com `omniroute resilience config set` (só expõe `--threshold`, `--reset-timeout`,
`--base-cooldown`) só se a operação mostrar necessidade.

**Achado 02/09 (P1-04):** `resilienceSettings.requestQueue.maxWaitMs=15000` (bloco
"legacy", **não** exposto pelo `resilience config set`) é curto demais para modelo local
lento — `qwen3.5:9b` (~13 s) deu **504** `gateway_timeout` pela combo. Fica como está por
ora (os provedores nuvem são rápidos); se um combo precisar de um local lento, achar o
jeito de subir esse valor (DB / env não documentada) é tarefa da execução com chaves.

**Achado 02/09:** `omniroute combo delete <name>` **exige `--yes`** — sem ele, prompt
interativo trava em shell não-interativo (`exit 13`, "unsettled top-level await").

---

**Template original abaixo** — preencher com os valores reconferidos e a data.

- Lista curada: `github.com/amardeeplakshkar/awesome-free-llm-apis`
- Painel de custo/uso: o do próprio OmniRoute (`/dashboard`, "Requests"/"Usage") — **não
  montar dashboard extra** (PESQUISA).
- Chaves: só em `~/.hermes/.env`, o Humano edita direto, nunca no chat nem no repo. O
  OmniRoute lê do ambiente / do store local dele.
- Todo egresso passa antes pela sanitização da P1-02 (`sanitizar.py` via policy ou
  `proxy.py`), inclusive nas rotas nuvem.

## Provedores (estado PESQUISA 01/09/2026 — RECONFERIR)

| Provedor | Env var (sugerida) | Base URL | Modelo(s) alvo | Limite visto (reconferir) | Combo |
|---|---|---|---|---|---|
| Ollama (local) | — | `http://127.0.0.1:11434` | denso 9B (nome do `ollama list`) | — | `cheap` #1, fallback local |
| Groq | `GROQ_API_KEY` | `https://api.groq.com/openai/v1` | Llama 3.3 70B (~320 tok/s) | ~30 RPM / 1000 RPD / 100K TPD | `cheap` #2, `auto` |
| Cerebras | `CEREBRAS_API_KEY` | `https://api.cerebras.ai/v1` | modelo ~120B | 30 RPM / 14.400 RPD / 1M TPD | `auto` #1, `cheap` #3 |
| DeepSeek | `DEEPSEEK_API_KEY` | `https://api.deepseek.com` | deepseek-chat | conferir (barato, não zero) | `cheap` #4 |
| GitHub Models | `GITHUB_MODELS_TOKEN` | `https://models.inference.ai.azure.com` | conferir catálogo | conferir | `auto` |
| Gemini free | `GOOGLE_API_KEY` | (Google) | gemini-2.5-flash | ~20/dia **compartilhado** com Hermes e `conselho_remoto.py` | combo `conselho` (P1-04); evitar em `auto`/`cheap` |
| OpenRouter `:free` | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1` | modelos `:free` | rotativo | `auto` reserva |
| Mistral free | `MISTRAL_API_KEY` | `https://api.mistral.ai/v1` | conferir | conferir | `auto` reserva |

**Não roda local nesta máquina** (8 GB VRAM + 38 GB RAM): Qwen3.8-Flash-Next (125B), o
120B da Cerebras — são escolha de nuvem, nunca worker local.

## Combos

| Combo | Ordem | Uso |
|---|---|---|
| `cheap` | Ollama 9B → Groq → Cerebras → DeepSeek | tarefas toleráveis a modelo menor; para/segue por custo |
| `auto` | Cerebras → Groq → (OpenRouter/Mistral reserva) | qualidade/latência; fallback na falha |
| `conselho` | glm-4.7-flash (z.ai) → gemini-2.5-flash | só o `conselho_remoto.py` (P1-04); esgotou ⇒ ABORTA, não cai pro local |

## Circuit breaker / cooldown

Usar os defaults do OmniRoute. **Anotar aqui na execução** os valores efetivos:
- N falhas seguidas (429/5xx/timeout) para abrir: `____`
- Cooldown antes de retentar: `____`
- Comportamento com todos os provedores da combo abertos: `____` (esperado: erro ao caller, não resposta silenciosa de lugar nenhum)

## Verificado na execução (preencher)

- [ ] cada provedor testado pelo botão "test" do dashboard: data / resultado
- [ ] `model: "cheap"` com o 1º provedor forçado a falhar → resposta do 2º (P1-03 passo 4)
- [ ] custo por chamada aparece no painel nativo
- [ ] segredo plantado numa rota nuvem → bloqueado antes de sair (P1-02 vale na nuvem)
- [ ] nenhuma chave em `~/.config/omniroute/` nem nos logs
