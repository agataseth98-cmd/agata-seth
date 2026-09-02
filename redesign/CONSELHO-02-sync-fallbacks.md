# Conselho 02 — sincronizar os fallbacks e ficar de prontidão

**Para:** Codex (OpenAI) e Qwen Coder. O Humano relaya. Vocês leem pelo GitHub
`agataseth98-cmd/agata-seth`, branch **`redesign`**.

**Objetivo desta mensagem:** vocês **não vão executar nada agora** — só sincronizar o
modelo mental com o estado atual do redesenho e ficar **de prontidão** para assumir se o
Humano pedir (a sessão Claude primária pode migrar de chat de novo).

---

## 1. Reidrate

```
git fetch origin --tags
git switch redesign
git pull --ff-only origin redesign
git rev-parse --short HEAD                       # referência viva
git rev-parse --short main                       # esperado 4aa90bd
git rev-parse --short 'pre-redesign^{commit}'    # esperado 4aa90bd  (tag ANOTADA -- use ^{commit})
git status --porcelain                           # esperado vazio
```

Se `main` ou `pre-redesign^{commit}` não baterem, ou a árvore estiver suja: **pare e diga
ao Humano.**

## 2. Leia, nesta ordem

`redesign/README.md` → `redesign/STATUS.md` → `redesign/CONTINUIDADE.md` (§6 papéis, §7
fluxo) → `redesign/CLAUDE-NA-MAQUINA.md` → **fim** do `redesign/LOG.md` (entradas de
2026-09-02) → `redesign/ROADMAP.md` → `redesign/router/PROVEDORES.md` →
`redesign/REIDRATACAO-chat-3.md` (o mesmo estado, resumido).

## 3. O que vocês são, nesta fase

- **Executores de reserva, afinados.** Sem shell na Máquina — o Humano é mãos e olhos,
  roda os blocos e cola a saída.
- **Não são gate nem conselho.** O plano não espera parecer de vocês para andar. Se o
  Humano pedir um parecer sobre um ponto específico, aí sim — e divergência entre
  executores vai para o `LOG.md` (as duas posições) e sobe para o Humano, sem voto.
- **Quem decide é o Humano.** Claude é conselheiro + 1º executor.

## 4. Estado do redesenho (resumo — o detalhe está no `LOG.md`/`STATUS.md`)

- **Fases 0 e 1: FECHADAS.**
  - Fase 0: repo restic no HD (`AgataBkup01`), 4 snapshots, `restic check` limpo, restore
    byte a byte OK; `models/manifest.json`; tag `pre-redesign`.
  - Fase 1: OmniRoute 3.8.50 (`systemd --user`, `127.0.0.1:20128`) + proxy de sanitização
    de segredo (`127.0.0.1:20127`, os callers usam este). 6 providers, combos
    `cheap`/`auto`/`conselho`, fallback verificado, custo logado. `scripts/conselho_remoto.py`
    (cópia-branch) reescrito p/ falar pelo gateway — **merge p/ `main` só na Fase 8**.
- **Fase 3 (Modelos) EM ANDAMENTO:** P3-00 (reconstrutibilidade provada) e P3-01
  (`PRUNE.md`) FEITO. **P3-02 quase:** 16 modelos removidos do Ollama, keep-list de 5
  (`qwen3.5:9b`, `-9b-64k`, `qwen3:4b`, `rlm-qwen3-8b-teste`, `nomic-embed-text`); item
  aberto = confirmar os ~112 GB reclamados. **P3-03 a fazer:** `llama.cpp` + MoE GGUF +
  `--n-cpu-moe` + registrar no OmniRoute.
- **Fase 2 (iGPU)** vem depois da 3 (ordem `0→1→3→2`).

## 5. Invariantes que continuam (estado de exceção suspende só a cerimônia)

`MEMÓRIAS.md` nunca se reescreve · nada de force-push/reset/rebase em `main` · segredo
nunca no chat/git (chave nova = Humano edita `~/.hermes/.env` direto) · destrutivo
mostrado sozinho, com aviso · `main` só muda na Fase 8 · Hermes/Ollama de produção
intocados · o GGUF `rlm-qwen3-8b-v0.1-q4_k_m.gguf` é o único modelo não-reproduzível
(está no snapshot restic `c19275ec`).

## 6. Prontidão

Fiquem sincronizados neste HEAD. Se o Humano disser "assume", o ponto de entrada é o
`redesign/CONTINUIDADE.md` + este arquivo + o `LOG.md` do fim. A próxima tarefa executável
é **P3-03** (arquivo-tarefa pronto em `redesign/tasks/P3-03-*.md`), que precisa de `sudo`
(instalar `llama.cpp`) — ou seja, o Humano no teclado de qualquer forma.

Não precisa responder. Se algo no `git` não bater com o descrito aqui, aí sim: avise.
