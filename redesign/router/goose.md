# P8-04 — Goose como shell operacional de fallback

**Não é canon.** Branch `redesign`. Estado: **pesquisa feita, instalação aguarda decisão do
Humano** (2026-09-03, chat 6).

## Papel

Executor-shell de fallback, agnóstico de modelo, apontado para o OmniRoute — para quando a
sessão Claude Code primária cair e o Humano precise tocar o sistema sem ela. **Não** é
conselheiro nem gate (igual aos outros fallbacks). Codex CLI é terciário (só com cota
OpenAI, não roda modelo local) — PESQUISA.md C7.

## Pesquisa da instalação vigente (2026-09-03)

O **Goose atual** (Block → Agentic AI Foundation, ~53k estrelas, Apache-2.0) é um **binário
Rust**, não o pacote Python `goose-ai` do PyPI (esse é o predecessor de 2024, deprecado —
**não usar**). "≥40 provedores, bring-your-own-key" (Anthropic/OpenAI/Google/Ollama/
OpenRouter/OpenAI-compat).

Métodos de instalação (nenhum é `pipx` para a versão Rust):

| método | sudo? | transparência | nota |
|---|---|---|---|
| **A. script oficial** `curl -fsSL .../download_cli.sh \| bash` (GitHub releases) | não | baixa binário para `~/.local/bin` — **roda um script buscado da rede** | rápido; o script é auditável antes |
| **B. binário do release, à mão** — baixar `goose-x86_64-unknown-linux-gnu.tar.bz2`, conferir sha256, extrair em `~/.local/bin` | não | alta — só um binário, checksum conferido | mais passos, sem script |
| **C. AUR** (`goose-cli` / similar) | via helper | média | `pacman -Ss goose` no repo oficial = nada; conferir AUR |
| **D. adiar** | — | — | Goose não bloqueia P8-05/06/07; pode entrar depois do merge |

**Recomendação:** **B** (binário + sha256 conferido em `~/.local/bin`) — mesma linha do
`agata-jogo` (nó nosso, sem sudo, verificável), evita `curl \| bash`. Se o Humano preferir
velocidade, **A**. Qualquer uma **precisa do "vai" para instalar software** (linha do
`CLAUDE-NA-MAQUINA.md`).

## Config planejada (depois da instalação)

- Provider Goose = **OpenAI-compat** apontando para o proxy sanitizador
  `http://127.0.0.1:20127/v1` (não o `:20128` direto — o `:20127` redige segredo antes do
  egresso).
- Modelo default: `ollama-local/qwen3.5:9b`; combos via OmniRoute.
- Sem chave: o `:20127` não exige (loopback é a proteção, como no resto).
- Teste de aceite: uma tarefa real (ler o repo, propor um diff, **sem** tocar `main`) →
  `omniroute cost` incrementa; segredo plantado é barrado (mesmo teste da P1-02).

## Pendências

1. **Humano escolhe A/B/C/D** e dá o "vai" para instalar.
2. Depois: instalar, configurar o provider `:20127`, rodar o teste, preencher esta doc com
   versão + sha256 + saída do teste.
