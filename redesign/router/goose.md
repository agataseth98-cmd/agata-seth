# P8-04 — Goose como shell operacional de fallback

**Não é canon.** Branch `redesign`. **FEITO — 2026-09-03 (chat 6), método B.**

## Papel

Executor-shell de fallback, agnóstico de modelo, apontado para o OmniRoute — para quando a
sessão Claude Code primária cair e o Humano precise tocar o sistema sem ela. **Não** é
conselheiro nem gate. Codex CLI é terciário (só com cota OpenAI, não roda modelo local) —
PESQUISA.md C7.

## Instalação (método B — binário do release + sha256)

O **Goose atual** (Block → Agentic AI Foundation, `github.com/block/goose` → assets em
`aaif-goose/goose`, Apache-2.0) é **binário Rust**. O pacote PyPI `goose-ai` é o
predecessor de 2024 — **deprecado, não usado**.

- Versão: **v1.48.0** (publicada 2026-08-27).
- Asset: `goose-x86_64-unknown-linux-gnu.tar.bz2` (86,8 MB).
- **sha256 conferido contra o `digest` da API do GitHub:**
  `fbe2f128ff68383cdab57431c577ed771e2ada035a9639520b2e28a871a56a1f` — bateu.
- Instalado: `install -m755 goose ~/.local/bin/goose` (sem sudo; `~/.local/bin` já no
  PATH). Binário ~311 MB descompactado. Tarball do install removido.
- Atualizar depois: `goose update` (subcomando nativo).

## Config — `~/.config/goose/config.yaml`

```yaml
GOOSE_PROVIDER: openai
GOOSE_MODEL: ollama-local/qwen3.5:9b
OPENAI_HOST: http://127.0.0.1:20127     # proxy sanitizador (NAO :20128 direto)
OPENAI_API_KEY: nao-usada-proxy-loopback
GOOSE_MODE: approve                      # pede confirmacao antes de cada acao de ferramenta
```

- `:20127` = o proxy da P1-02 — redige segredo antes do egresso. Sem chave: loopback é a
  proteção.
- Modelo exige prefixo de provider (`ollama-local/...`); combos (`cheap`/`auto`/`conselho`)
  também servem como `GOOSE_MODEL`.

## Teste de aceite (2026-09-03)

- `goose run` (pergunta simples, sem ferramentas) → sessão `openai ollama-local/qwen3.5:9b`,
  respondeu `42`. Caminho ponta a ponta pelo OmniRoute ✓.
- `omniroute cost` contabilizou o tráfego (Ollama 41 reqs).
- **Segredo barrado:** `POST :20127` com `sk-ABCDEF…0123456789` (casa `sk-[A-Za-z0-9]{20,}`)
  → **422** `secret_blocked_before_egress`, trecho redigido, não chegou ao provedor. Idem
  `AKIA…` → 422. (Uma string tipo `sk-proj-…XX` passa 200 — não casa o padrão; correto.)

## Achado — deadline do OmniRoute vs. cold start do Ollama

A **primeira** chamada a um modelo Ollama não carregado (~30 s de load) estoura o
`resilienceSettings.requestQueue.maxWaitMs=15000` do OmniRoute → **504**
`RATE_LIMIT_EXECUTION_TIMEOUT`. O modelo **carrega mesmo assim** e as chamadas seguintes
(modelo quente) respondem em ~0,5 s. Mitigação p/ o cutover (P8-02/P8-05): pré-aquecer o
modelo local no `agata up`, ou subir o `maxWaitMs`. Anotado, não bloqueia.

## Rollback

`rm ~/.local/bin/goose ~/.config/goose/config.yaml`. Não afeta o resto.
