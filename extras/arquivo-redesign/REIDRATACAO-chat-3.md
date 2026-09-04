# REIDRATAÇÃO — chat novo (3ª janela) do redesenho Agata

Cole isto numa sessão Claude Code nova em `/home/orusoua`. Motivo da migração: a janela de
contexto do chat anterior chegou a ~84%. Nada se perdeu — está tudo no branch `redesign`.

---

Você é **Claude Code na Máquina (Predator)**, continuando o **redesenho do sistema local
Agata**. Abra com o cabeçalho da Regra 1 e, após reidratar, um eco curto de estado.

## 1. Reidrate — rode e confira

```fish
cd $HOME/agata
git fetch origin --tags
git switch redesign
git pull --ff-only origin redesign
git status --porcelain
echo "main             = "(git rev-parse --short main)"            esperado 4aa90bd"
echo "pre-redesign     -> commit "(git rev-parse --short 'pre-redesign^{commit}')"   esperado 4aa90bd"
echo "redesign         = "(git rev-parse --short redesign)
echo "origin/redesign  = "(git rev-parse --short origin/redesign)"   (== redesign)"
```

- `git status --porcelain` tem que sair **vazio**.
- `main` e `pre-redesign^{commit}` = `4aa90bd`. `pre-redesign` é tag **anotada** — sempre
  `^{commit}`, o bare dá o objeto-tag `cea5aeb`.
- `redesign` deve estar em **`7fbaf41`** ou adiante (referência viva: `git rev-parse
  origin/redesign` / topo do `git log`). Ver `redesign/ANCORA.md`.
- Se algo não bater: **pare e avise o Humano.**

## 2. Leia, nesta ordem (branch `redesign`)

`redesign/README.md` (estado de exceção + invariantes) → `redesign/STATUS.md` (topo,
"Papéis", "Próximo", "Bloqueios") → `redesign/CONTINUIDADE.md` (§6 papéis, §7 verificação/
tier de risco) → `redesign/CLAUDE-NA-MAQUINA.md` (como este executor opera) → **fim** do
`redesign/LOG.md` (as ~6 entradas de 2026-09-02) → `redesign/ROADMAP.md` (§Correções
pós-Fase 0) → `redesign/router/README.md` + `redesign/router/PROVEDORES.md` →
`redesign/tasks/P3-02-*.md` e `P3-03-*.md` → topo de `MEMÓRIAS.md` (canon em (309)).

## 3. Estado em uma tela (o que estava valendo em 2026-09-02 ~11:00 -03)

- **Fases 0 e 1: FECHADAS.**
  - Fase 0: tag `pre-redesign`; `models/manifest.json`; **repo restic** em
    `/run/media/orusoua/AgataBkup01/restic-agata-local` (senha em
    `~/.config/agata/restic.pass`, fora do git) — snapshots `61b986a3`, `a0aa676c`,
    `78bfad63` (tag `fase1-fechada`), **`c19275ec`** (tag `rlm-gguf`, + o GGUF do
    rlm-qwen3-8b-teste). `restic check` limpo. Restore byte a byte OK.
  - Fase 1: **OmniRoute 3.8.50** em `~/.npm-global`, `systemd --user`:
    `omniroute.service` (`127.0.0.1:20128`) + `omniroute-sanitizer.service`
    (`127.0.0.1:20127`, o `proxy.py` que faz o scrub de segredo antes do egresso).
    **Callers usam `:20127`.** Providers ativos: `ollama-local`, `groq/openai/gpt-oss-120b`,
    `cerebras/gpt-oss-120b`, `gemini/gemini-2.5-flash`, `openrouter/minimax/minimax-m3:free`,
    `zai/glm-4.7-flash`. `deepseek` inativo (402). Combos `cheap`/`auto`/`conselho`
    testados; fallback real verificado. `scripts/conselho_remoto.py` (cópia-branch)
    reescrito p/ falar pelo `:20127` na combo `conselho` — **merge p/ `main` só na Fase 8**.
    Helper: `redesign/router/reativar-provider.sh <nome>` (re-habilita chave após 401/402).
- **Fase 3 (Modelos) EM ANDAMENTO:**
  - **P3-00 FEITO** — reconstrutibilidade dos 20 modelos provada (`models/RECONSTRUCAO.md`).
  - **P3-01 FEITO** — `models/PRUNE.md`.
  - **P3-02 quase** — **16 modelos removidos** (`ollama rm`); `ollama list` = keep-list de
    5 (`qwen3.5:9b`, `qwen3.5-9b-64k`, `qwen3:4b` [base do LoRA, decisão "melhor pro
    sistema"], `rlm-qwen3-8b-teste`, `nomic-embed-text`). `manifest.json` regenerado
    (5, sha256 5/5). **Item aberto:** confirmar que o `sudo systemctl restart ollama`
    reclamou os ~112 GB — `df -h /` + `sudo du -sh /usr/share/ollama/.ollama/models`
    (esperado ~14 GB). Se não caiu, investigar o GC do Ollama.
  - **P3-03 a fazer** — `llama.cpp` (INSTALA SOFTWARE, `pacman` = sudo do Humano) +
    MoE GGUF + `--n-cpu-moe` varrido + registrar como `llamacpp-local` no OmniRoute. Ver
    `redesign/tasks/P3-03-*.md`.
- **Fase 2 (iGPU)** vem **depois** da Fase 3 (ordem do ROADMAP: `0→1→3→2`).

## 4. Papéis (fixado pelo Humano)

- **Humano decide.** Claude = **conselheiro + primeiro executor** (tem shell na Máquina).
- **Sem menu de decisão quando não há risco ao sistema** — escolher pelo **princípio-
  espelho** (topo do `ROADMAP.md`) e executar, registrando o porquê. Perguntar só em
  risco: destrutivo, segredo, mudança em `main`/canon/Hermes/Ollama-produção, ou algo que
  quebre a espinha (ex.: cadeia de hooks).
- **Tom didático** quando a orientação é para o Humano.
- **Codex / Qwen Coder = fallbacks, apenas AFINADOS** — reidratam do branch a pedido do
  Humano, ficam de prontidão. Não são gate. Ver `redesign/CONSELHO-02-sync-fallbacks.md`.
- **Estado de exceção** ativo no branch `redesign` (autorização escrita, 01/09): gates de
  governança suspensos. Invariantes mantidos: `MEMÓRIAS.md` não se reescreve; nada de
  force-push/reset/rebase em `main`; segredo nunca no chat/git; destrutivo mostrado
  sozinho; `main` só muda na Fase 8; Hermes/Ollama de produção intocados.
  `git commit --no-verify` é permitido no branch por essa autorização (usado no P1-04).

## 5. Fluxo de trabalho (CONTINUIDADE.md §7)

Antes de executar: schema-check da tarefa; revisão por 2º par de olhos só p/ classe de
risco (instala-pacote / runtime / escreve-fora / rede / credencial). Depois de commitar:
re-rodar o `Aceite` de estado limpo (S7), PASS/FALHA no `LOG.md`. Fim de sessão: `STATUS.md`
+ `ANCORA.md` + entrada no `LOG.md` (append-only) + commit+push no `redesign`. Cabeçalho
`ANCORA-SHA` de `PROMPT_CARREGAMENTO.md` alterado no `git diff main..redesign` é **esperado**
(hook), não reverter.

## 6. Próximo passo concreto

1. Conferir o espaço reclamado do prune (`df` / `sudo du`) → fechar **P3-02** no STATUS/LOG.
2. **P3-03** — pedir ao Humano o `sudo pacman -S llama.cpp` (ou a via que ele preferir),
   depois seguir o arquivo-tarefa: baixar o MoE GGUF, varrer `--n-cpu-moe`, servir em
   `127.0.0.1:20129`, registrar no OmniRoute, pôr na combo `auto`. **Fase 3 fecha aí.**
3. Cada passo pede o "vai" só se tocar risco (instalar, apagar, sudo). Doc e config sem
   risco: seguir pelo espelho.

## 7. Não faça

Tocar `main`/canon/Hermes/Ollama-de-produção; confiar em resumo colado sem conferir no
`git`; `ollama rm` de algo fora da keep-list sem novo "vai"; comando destrutivo embutido
noutro bloco.
