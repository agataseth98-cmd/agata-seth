# PROVEDORES.md — pool de modelos atrás do OmniRoute (Fase 1, P1-03)

**Template.** Preencher na execução da P1-03 com os valores reconferidos e a data. Os
limites free **mudam sempre** — a fonte da verdade é a lista curada, não este arquivo.

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
