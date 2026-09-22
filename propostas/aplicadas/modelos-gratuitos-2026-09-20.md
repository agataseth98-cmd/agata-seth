# Pesquisa de modelos gratuitos — 2026-09-20

_Gerada por `scripts/pesquisar_modelos_gratuitos.py`. NÃO é canon, NÃO
implementa nada. Se aprovada, o Humano aplica à mão: edita
`config/modelos-gratuitos.md` + `ROSTER` de `conselho_remoto.py` (proposta
assinada) e os combos/roteador do OmniRoute (UI). MEMÓRIAS (377)._

## Pool re-testado

| modelo | estado | detalhe |
|---|---|---|
| `gemini/gemini-2.5-flash` | ERRO | HTTP 429: {"error":{"message":"All credentials for model gemini-2.5-flash are cooling down","type":"rate_limit_error","code":"model_cooldown","model":"gemini-2.5-flash","reset_seconds":36,"retry_after":"2026-09 |
| `huggingface/meta-llama/Llama-3.3-70B-Instruct` | ERRO | HTTP 401: {"error":{"message":"No active credentials for provider: huggingface.","type":"authentication_error","code":"invalid_api_key"}} |
| `llama-cpp/gpt-oss-20b` | ERRO | HTTP 502: {"error":{"message":"[llama-cpp/gpt-oss-20b] [502]: fetch failed (cause: ECONNREFUSED: connect ECONNREFUSED 127.0.0.1:20144) (reset after 3s)"}} |
| `llama-cpp/nemotron-3.5-lightning` | ERRO | HTTP 502: {"error":{"message":"[llama-cpp/nemotron-3.5-lightning] [502]: fetch failed (cause: ECONNREFUSED: connect ECONNREFUSED 127.0.0.1:20142) (reset after 24s)"}} |
| `llama-cpp/phi-4-mini` | ERRO | HTTP 502: {"error":{"message":"[llama-cpp/phi-4-mini] [502]: fetch failed (cause: ECONNREFUSED: connect ECONNREFUSED 127.0.0.1:20142) (reset after 1s)"}} |
| `llama-cpp/qwen3-coder-30b-a3b` | ERRO | HTTP 502: {"error":{"message":"[llama-cpp/qwen3-coder-30b-a3b] [502]: fetch failed (cause: ECONNREFUSED: connect ECONNREFUSED 127.0.0.1:20142) (reset after 1s)"}} |
| `llamacpp-local/qwen3-30b-a3b` | ERRO | HTTP 502: {"error":{"message":"[llamacpp-local/qwen3-30b-a3b] [502]: fetch failed (cause: ECONNREFUSED: connect ECONNREFUSED 127.0.0.1:20129) (reset after 3s)"}} |
| `mistral/ministral-8b-latest` | OK | 'Pong! 🎾' (7 tok) |
| `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` | OK | 'pong' (16 tok) |
| `zai/glm-4.7-flash` | ERRO | TimeoutError: timed out |

## Modelos do OmniRoute fora do pool que responderam OK

- (nenhum)

## Rascunho de ROSTER (só os OK agora, ordem = a atual + novos no fim)

```python
ROSTER = [
    "mistral/ministral-8b-latest",
    "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
]
```

## Discovery do OmniRoute

```json
{
  "erro": "HTTPError: HTTP Error 400: Bad Request"
}
```

## Famílias que dependem de chave do Humano (não integradas aqui)

- Mistral AI
- GitHub Models
- HuggingFace Inference
- Cloudflare Workers AI
- NVIDIA NIM

Pra integrar uma: pôr a chave em `~/.config/agata/.env`, adicionar o
provedor no OmniRoute, 1 teste ao vivo, e então proposta assinada.
