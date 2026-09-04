# P1-03 — pool nuvem: provedores free, combos auto/cheap, fallback + circuit breaker, custo

**Objetivo:** fechar o aceite da Fase 1 — "cai no fallback sob falha forçada; custo
logado". Adicionar os provedores nuvem free atrás do OmniRoute, com combos e breaker.

**Pré-requisitos:** P1-00, P1-01, P1-02 FEITO. (P1-02 antes: nenhuma chamada nuvem sai
sem passar pela sanitização.)

**Status:** ✅ **FEITO — 2026-09-02 ~09:00.** As chaves já estavam em `~/.hermes/.env`.
- ✅ Providers **ativos**: `ollama-local`, `groq` (`groq/openai/gpt-oss-120b`), `gemini`
  (`gemini/gemini-2.5-flash`), `openrouter` (`openrouter/minimax/minimax-m3:free`), `zai`
  (`zai/glm-4.7-flash`). Valores lidos do `.env` p/ env vars, **nunca impressos**.
  `deepseek` registrado mas **fora dos combos** — chave dá `402 Insufficient Balance`.
- ✅ Combos `cheap` / `auto` / `conselho` — todos roteiam pelo proxy `:20127` (testados).
- ✅ **Fallback sob falha real**: combo `[deepseek (402) → groq]` → resposta veio do Groq.
  Também: `conselho` GLM→Gemini quando o GLM passa de `maxWaitMs`.
- ✅ **Custo logado** por provedor (`omniroute cost`): total US$0,0115 (o parecer real de
  P1-04 no Gemini); Groq/OpenRouter/Z.AI/Ollama $0.
- ✅ Breaker/cooldown = defaults do OmniRoute (registrados em `PROVEDORES.md`).
- Achados: Groq aposentou `llama-3.3-70b-versatile` (o erro "model 'llama 3.3 70b'" era
  breaker + default velho; resolvido re-registrando com `--default-model`). Os ids do
  **catálogo** do OmniRoute (nomes bonitos) não funcionam — usar sempre o id RAW do provedor.

**Arquivos que a tarefa toca:**
- `~/.hermes/.env` — **o Humano** acrescenta as chaves nuvem, editando o arquivo direto.
  Nunca coladas no chat, nunca no repo. (Groq, Cerebras, GitHub Models, DeepSeek, etc.)
- config de provedores + combos do OmniRoute (`~/.config/omniroute/`)
- `redesign/router/PROVEDORES.md` (novo) — a lista curada do que está ligado, com os
  limites conhecidos e a data; ponteiro para `github.com/amardeeplakshkar/awesome-free-llm-apis`
- `redesign/tasks/P1-03-*.md`

---

## Contexto (PESQUISA 01/09/2026 — os limites MUDAM, reconferir na execução)

| Provedor | Nota | Limite visto |
|---|---|---|
| Groq | Llama 3.3 70B ~320 tok/s | ~30 RPM / 1000 RPD / 100K TPD |
| Cerebras | modelo ~120B | 30 RPM / 14.400 RPD / 1M TPD |
| GitHub Models | free | conferir |
| DeepSeek | free/barato | conferir |
| Gemini free | Google cortou cota fim de 2025; **compartilhada** com Hermes e com `conselho_remoto.py` | ~20/dia |
| OpenRouter `:free`, Mistral free | conferir | conferir |

Fonte da verdade dos limites: a lista curada `awesome-free-llm-apis`. Os combos + breakers
do OmniRoute absorvem a variação — não codar limite fixo, deixar o breaker medir.

---

## Passos

### 1. Chaves — o Humano edita o `.env`

```
# O HUMANO faz isto, sem passar pelo chat:
#   $EDITOR ~/.hermes/.env
#   GROQ_API_KEY=...
#   CEREBRAS_API_KEY=...
#   GITHUB_MODELS_TOKEN=...
#   DEEPSEEK_API_KEY=...
# chmod 600 ~/.hermes/.env  (conferir)
```
O executor **não** vê as chaves. Confirma só: `test -f ~/.hermes/.env; and stat -c '%a' ~/.hermes/.env` → `600`.

### 2. Registrar os provedores no OmniRoute

Pelo dashboard `/dashboard/providers` — para cada um: tipo, base URL, a env var da chave
(o OmniRoute lê do ambiente / do próprio store local; **não** colar o valor). Habilitar 1–2
modelos por provedor. Testar cada um pelo botão "test" do dashboard.

Colar de volta: `curl -s http://127.0.0.1:20128/v1/models` (lista agora com nuvem + Ollama).

### 3. Combos `auto` e `cheap` + fallback + breaker

Configurar (dashboard "Combos"/"Routes" ou arquivo):
- **`cheap`**: ordem = [Ollama local → Groq → Cerebras → DeepSeek]; para/segue por custo.
- **`auto`**: ordem por qualidade/latência; fallback na falha.
- **circuit breaker + cooldown**: após N falhas seguidas de um provedor (429/5xx/timeout),
  tira ele da rota por T minutos. Usar os defaults do OmniRoute; anotar quais são.

### 4. Teste — fallback sob falha forçada

```fish
# forçar o 1º provedor da combo a falhar: chave inválida temporária OU bloquear a saída
# dele com uma regra de firewall de teste OU parar o Ollama se ele for o 1º.
# exemplo (Ollama 1º na combo cheap):
systemctl --user stop ollama    # ou o gerenciador; se for serviço de sistema, usar um scratch
curl -s http://127.0.0.1:20128/v1/chat/completions -H 'content-type: application/json' \
  -d '{"model":"cheap","messages":[{"role":"user","content":"responda só: ok"}]}' | tee /tmp/p1_03_fb.json
systemctl --user start ollama
```
Colar de volta: o JSON (tem que ter vindo do **próximo** provedor da combo) + o log do
OmniRoute mostrando a tentativa falha + a bem-sucedida.
Sucesso: resposta 200 vinda do fallback; o breaker registrou a falha do 1º.

### 5. Custo logado

```fish
omniroute logs --tail 10        # ou o painel "Requests"/"Usage"
```
Colar de volta: as linhas dos pedidos dos passos 2 e 4 com **custo** (ou tokens+preço) por chamada.
Sucesso: cada chamada tem custo/tokens; o painel soma por provedor.

### 6. `PROVEDORES.md`

Escrever `redesign/router/PROVEDORES.md`: tabela do que ficou ligado, limites reconferidos
na execução com a data, e a combo de cada um. Ponteiro para a lista curada.

---

## Aceite

- `POST /v1/chat/completions` com `model: "cheap"` e o 1º provedor forçado a falhar ⇒
  resposta 200 do 2º provedor; o log mostra a tentativa falha + o fallback.
- Toda chamada nos logs tem custo/tokens; o painel nativo soma por provedor (sem dashboard
  extra montado — PESQUISA).
- Chave nuvem só em `~/.hermes/.env` (`stat -c '%a'` = 600); `grep -rIE '(sk-|gsk_|csk-|AIza)' ~/.config/omniroute/ redesign/` → vazio.
- Uma chamada nuvem com segredo plantado no prompt ainda é **bloqueada** (P1-02 continua valendo na rota nuvem).

## Verificação independente

- **Quem:** fallback afinado ou Humano.
- **O quê:** que nenhuma chave vazou para o repo ou para os logs do OmniRoute; que o
  breaker realmente tira o provedor da rota (não só loga).
- **Como:** `grep -rIE '[A-Za-z0-9_-]{20,}' ~/.config/omniroute/*log* redesign/router/` revisado à mão;
  repetir o passo 4 duas vezes seguidas e ver o 1º provedor sair da rota no 2º pedido sem nova tentativa.
- **Resultado:** anotar no LOG.

## Rollback

Não destrutivo: desabilitar os provedores nuvem pelo dashboard; `git checkout -- redesign/router`.
As chaves ficam no `.env` do Humano — remoção é decisão dele.

## Registro

- `STATUS.md`: P1-03 → "Feito"; **Fase 1 aceite (a)-(d) fechado** exceto P1-04.
- `LOG.md`: o JSON do fallback, as linhas de custo, os defaults do breaker, o resultado da
  verificação independente, `HEAD` no fim.
