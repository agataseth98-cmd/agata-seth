# Integração Mistral / HuggingFace / GitHub Models — achados 08/09/2026

Registro de investigação. O que virou canon está em MEMÓRIAS (379) e na
proposta assinada `propostas/aplicadas/roster-huggingface-mistral`.

Contexto: item 3a do fork pós-B5. O Humano pôs três chaves em
`~/.config/agata/.env` (`MISTRAL_API_KEY`, `GITHUB_MODELS_TOKEN`, `HF_TOKEN`).
Objetivo: mais famílias de modelo grátis no roster (o P-15 avisava que só 1
família teve sucesso em 24h).

## Correção de digitação no .env

As três linhas entraram com os `< >` do template literal
(`MISTRAL_API_KEY=<N6Uw...>`). Removidos com `sed` (backup em
`~/.config/agata/.env.bak-<timestamp>`).

## Mecanismo do OmniRoute

Chave de provedor fica cifrada em `provider_connections` do `storage.sqlite`
(a `STORAGE_ENCRYPTION_KEY` de `~/.omniroute/.env` cifra) — não dá pra
escrever à mão. Caminho usado: `POST /api/providers` no loopback (`:20128`),
documentado no OpenAPI do próprio produto ("Create provider connection",
`security:false`, body `{provider,url,name,apiKey,isActive}`), +
`POST /api/providers/{id}/test` + `PATCH /api/providers/{id}`. Mesma classe da
mudança de `maxWaitMs` (363) e do `hidePaidModels` (377): config de runtime de
produto de terceiro. Slugs em `/api/v1/provider-plugin-manifest`.

## Resultado final

| Provedor | Conexão | Estado | Modelo no roster |
|---|---|---|---|
| **HuggingFace** | `1ec9cdc4-…` (`provider=huggingface`, `router.huggingface.co/v1`) | ✅ `isActive:true`, funciona ao vivo | `huggingface/meta-llama/Llama-3.3-70B-Instruct` — 200, stop, ~1,3s |
| **Mistral** | `bb21c2af-…` (`provider=mistral`) | ✅ `isActive:true`, funciona ao vivo | `mistral/ministral-8b-latest` — 200, stop, ~0,55s |
| **GitHub Models** | — | ❌ descontinuado | — |

### HuggingFace — o que resolveu
O token inicial era só-leitura (`repo.content.read`) → o `test` passava (só
bate no `/whoami`) mas a inferência dava `403 sufficient permissions... call
Inference Providers`. O Humano recriou o token *fine-grained* com **"Make calls
to Inference Providers"** (`inference.serverless.write`). Depois disso: 200.
Ressalva viva: o free tier da HF é crédito mensal pequeno; esgotou dá 402 e o
circuit breaker do Conselho põe em cooldown (rotação segue nos outros).

### Mistral — o que resolveu
Duas camadas de problema:
1. **Chave errada.** A primeira chave era tipo **"Studio"** com escopo
   **"Somente compartilhado"** — não acessa a API crua da La Plateforme.
   Toda chamada dava `429 code 1300` (mensagem enganosa; não era rate limit).
   O Humano recriou com escopo **"pessoal e compartilhado"**.
2. **Modelo errado.** Mesmo com a chave certa, `mistral/mistral-small-latest`
   segue dando `429` nesta conta (free tier não libera esse modelo). Os
   pequenos (`ministral-8b-latest`, `ministral-3b-latest`) respondem 200
   normal. Roster usa `ministral-8b-latest`.
   `mistral/open-mistral-nemo` → OmniRoute rejeita ("not in active live
   catalog"); `ministral-*` passam por passthrough.

### GitHub Models — sem saída
`curl` direto pra `models.github.ai/inference`: `410
github_models_retirement_brownout` ("scheduled retirement"). A GitHub está
desligando o produto. Não há slug `github-models` neste build do OmniRoute de
qualquer forma (`provider=openai`+url custom cai no OpenAI real). O
`GITHUB_MODELS_TOKEN` no `.env` virou peso morto — pode remover.

## Roster resultante (MEMÓRIAS (379))

```
zai/glm-4.7-flash                              (zhipu)
gemini/gemini-2.5-flash                        (google)
cerebras/gemma-4-31b                           (cerebras)
huggingface/meta-llama/Llama-3.3-70B-Instruct  (huggingface)   NOVO
mistral/ministral-8b-latest                    (mistral)        NOVO
```

5 famílias independentes, breaker + rotação justa. Fecha o AVISO recorrente
do P-15.

## Teste de fumaça pós-commit (MEMÓRIAS (380)) — o que rodou de verdade

Rodei `conselho_remoto.py` e depois um teste por-modelo pelo `:20127`:

| Modelo | Estado real 08/09 ~16:00 |
|---|---|
| `zai/glm-4.7-flash` | ✅ confiável, 200 com `thinking` |
| `gemini/gemini-2.5-flash` | ⚠️ funciona, mas a conexão do OmniRoute entrou em `model_cooldown` de tanto teste hoje — transitório |
| `cerebras/gemma-4-31b` | ❌ **Cloudflare Error 1010 `browser_signature_banned` em `api.cerebras.ai`**, `retryable:false` ("Do not retry — your user-agent has been banned by the site owner"). No log do OmniRoute desde ~13:19 local — **não foi o nosso teste**, é ban de assinatura no cliente HTTP do OmniRoute, mesma classe do Groq (374). Efetivamente morto via OmniRoute enquanto durar. |
| `huggingface/…Llama-3.3-70B` | ✅ 200 em chamada espaçada; só dá 403 sob rajada (challenge de rate do Cloudflare em `router.huggingface.co`, que passa) — o breaker absorve |
| `mistral/ministral-8b-latest` | ✅ confiável, 200 sem `thinking` (o fix de (380) tirou o 422) |

**Efeito líquido:** roster de 5, **4 famílias funcionando** (zai, gemini, huggingface, mistral) — já mais que suficiente pro P-15 (≥2/24h). `cerebras` fica no roster mas cada rotação que cai nele = falha garantida + cooldown; o breaker sobe o cooldown exponencial até 6h e a rotação para de escolhê-lo na prática. **Rechecar `cerebras` em ~1 dia** — bans 1010 do Cloudflare às vezes são temporários. Se não voltar, sai do ROSTER por proposta.
