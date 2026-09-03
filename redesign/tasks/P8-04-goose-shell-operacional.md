# P8-04 — Goose como shell operacional de fallback

**Status:** 🔶 **PESQUISA FEITA — 2026-09-03 (chat 6).** O Goose atual é binário Rust (o
`goose-ai` do PyPI é o predecessor deprecado — não usar). Opções de instalação em
`redesign/router/goose.md`; recomendação = binário do release + sha256 em `~/.local/bin`
(sem sudo). **Aguarda o Humano escolher o método e dar o "vai" para instalar.**

**Objetivo:** um executor-shell de fallback agnóstico, apontado para o OmniRoute, para
quando a sessão Claude Code primária cair e o Humano precisar tocar o sistema sem ela.
`Goose` é a escolha da pesquisa (PESQUISA.md C7); Codex CLI é terciário (só com cota
OpenAI, não roda modelo local).

**Pré-requisitos:** P8-01. Fase 1 (OmniRoute `:20127`/`:20128`) fechada.

## Passos
1. **Pesquisar a instalação vigente do Goose** (Block/`goose`) — binário de release,
   `pipx`, `cargo`, ou AUR. Registrar o método e a versão. Confirmar licença (Apache/MIT)
   e que aponta para endpoint OpenAI-compat arbitrário.
2. Instalar (bloco `sudo`/`pipx` **sozinho**, mostrado antes).
3. Configurar o provider do Goose = OmniRoute **pelo proxy sanitizador `:20127`**
   (OpenAI-compat), modelo `ollama-local/qwen3.5:9b` como default, combos via OmniRoute.
   Chave: o proxy não exige, loopback é a proteção.
4. **Teste:** uma tarefa simples pelo Goose (`goose run ...` ou sessão) que leia o repo e
   proponha um diff, sem tocar `main`. Conferir que a chamada passou pelo `:20127`
   (`omniroute cost` incrementa) e que segredo plantado é barrado (mesmo teste da P1-02).
5. Documentar em `redesign/router/goose.md`: instalação, config, o teste, e o papel
   (fallback operacional; **não** é conselheiro nem gate — igual aos outros fallbacks).

## Aceite
- `goose` instalado, versão registrada; config aponta para `:20127`.
- Uma tarefa real roda ponta a ponta pelo Goose via OmniRoute; `omniroute cost` contabiliza.
- `redesign/router/goose.md` escrito. Codex CLI anotado como terciário.

## Verificação independente
2º olhar: a config do Goose não tem chave em claro; a chamada de teste aparece no
`omniroute cost`; o `goose.md` diz o papel certo (fallback, não gate).

## Rollback
Desinstalar o Goose (`pipx uninstall` / `pacman -Rns` / `rm` do binário); remover a config.
Não afeta o resto.

## Registro
`STATUS.md`: P8-04 → Feito; Goose = fallback shell operacional.
`LOG.md`: método de instalação, versão, config, teste, custo.
