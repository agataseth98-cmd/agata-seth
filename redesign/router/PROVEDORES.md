# PROVEDORES.md — pool de modelos atrás do OmniRoute (Fase 1, P1-03)

**Estado (2026-09-02 ~00:35):** estrutura adiantada pela sessão autônoma. Combos `cheap`
e `auto` criados (só com `ollama-local/qwen3.5:9b` por ora), roteiam OK pelo proxy
`:20127`. `conselho` fica para P1-04. **As entradas nuvem aguardam o Humano pôr as chaves
em `~/.hermes/.env`** e rodar os comandos abaixo. Os limites free **mudam sempre** — a
fonte da verdade é a lista curada, não este arquivo.

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

Ajustar com `omniroute resilience config set` só se a operação mostrar necessidade.

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
