# Conselho 03 — sincronizar os fallbacks e ficar em acompanhamento próximo

**Para:** Codex (OpenAI) e Qwen Coder. O Humano relaya. Vocês leem pelo GitHub
`agataseth98-cmd/agata-seth`, branch **`redesign`**.

**Objetivo desta mensagem:** vocês **não vão executar nada agora** — só sincronizar o
modelo mental com o estado atual (fim do chat 5) e ficar em **acompanhamento próximo**:
reidratar neste HEAD, e reidratar de novo a cada vez que o Humano disser que houve commit
novo, para poder assumir na hora se a sessão Claude primária cair.

---

## 1. Reidrate

```fish
git fetch origin --tags
git switch redesign
git pull --ff-only origin redesign
git rev-parse --short HEAD                       # esperado 4f4f657 ou adiante
git rev-parse --short main                       # esperado 4aa90bd
git rev-parse --short 'pre-redesign^{commit}'    # esperado 4aa90bd  (tag ANOTADA -- use ^{commit})
git status --porcelain                           # esperado vazio
```

Se `main` ou `pre-redesign^{commit}` não baterem, ou a árvore estiver suja: **pare e diga
ao Humano.**

## 2. Leia, nesta ordem

`redesign/README.md` → `redesign/STATUS.md` → `redesign/CONTINUIDADE.md` (§6 papéis, §7
fluxo) → `redesign/CLAUDE-NA-MAQUINA.md` → **fim** do `redesign/LOG.md` (as 3 entradas de
2026-09-02: chat 4 ~21:05, chat 5 ~21:47 e ~22:10) → `redesign/ROADMAP.md` (Fases 7 e 8) →
`redesign/tasks/P7-02-RUNBOOK.md` → `redesign/REIDRATACAO-chat-6.md` (o mesmo estado, na
forma de carta).

## 3. O que vocês são, nesta fase

- **Executores de reserva, afinados.** Sem shell na Máquina — o Humano é mãos e olhos,
  roda os blocos **fish** e cola a saída. (Regras de fish: `CONTINUIDADE.md` §5.)
- **Não são gate nem conselho.** O plano não espera parecer de vocês. Se o Humano pedir
  parecer sobre um ponto específico, aí sim — e divergência entre executores vai para o
  `LOG.md` (as duas posições) e sobe para o Humano, sem voto.
- **Quem decide é o Humano.** Claude é conselheiro + 1º executor.
- **Se o Humano disser "assume":** ponto de entrada = `redesign/CONTINUIDADE.md` + este
  arquivo + `redesign/REIDRATACAO-chat-6.md` + o fim do `LOG.md`. Grava a posse no
  "Quadro de posse" do `STATUS.md`, commita+empurra, confirma o remoto, **só então** age.

## 4. Estado do redesenho (resumo — o detalhe está no `LOG.md`/`STATUS.md`)

- **Fases 0, 1, 2, 3, 4, 6: FECHADAS.** Fase 5: **ARQUIVADA** (spike RLM não bateu a
  injeção; números no `LOG`/`rlm/RESULTADO.md`; nada de produção mudou).
- **Fase 7 (Liga/desliga): EM ANDAMENTO.**
  - **P7-01 FEITO** — `agata.target` (systemd `--user`) + `agata-drain` (dreno do WAL no
    stop, não corta) + `enable` no boot. **Uma regressão de boot foi achada e corrigida no
    chat 5:** `After=default.target` em 3 unidades base fechava ciclo de ordenação com o
    `agata-drain` → no 1º boot com `enable` o systemd apagava o start de `openvino-whisper`,
    `openvino-embeddings` e `obsidian-ro-proxy`. Fix (só em `~/.config/systemd/user/`, fora
    do repo): tirou `After=default.target` + `[Install] WantedBy` → `agata.target` nas 3.
    **S7 PASS.** **Pende só o reboot real de confirmação** — o Humano adiou.
  - **P7-02** — GameMode + `OLLAMA_KEEP_ALIVE=30s`. **Runbook pronto**
    (`redesign/tasks/P7-02-RUNBOOK.md`), 2 `sudo`, toca `ollama.service` de produção
    (só env). Aguarda o Humano.
  - **P7-03** — restic no HD `AgataBkup01` (esperado 03/09) + controle **P-12** no
    `perimetro.sh` + `cifrar_env.sh`. Os 2 `.diff` estão em `redesign/propostas/`
    (**não aplicados** — quarentena P-8; `git apply --check` limpo em 02/09). A régua do
    P-12 está parada em `redesign/SILO-HUMANO.md` (H-1) por decisão do Humano.
- **Fase 8 (cutover + merge p/ `main`)** vem depois da 7, com "vai". `main` só muda aí.
- **Trava do fim do chat 4:** reinício forçado, **causa não medida** (`lacuna`) — sem
  rastro no journal. Não é diagnóstico fechado. Não atribuir ao redesenho sem evidência.

## 5. Invariantes que continuam (estado de exceção suspende só a cerimônia)

`MEMÓRIAS.md` nunca se reescreve · nada de force-push/reset/rebase em `main` · segredo
nunca no chat/git (chave nova = Humano edita `~/.hermes/.env` direto) · destrutivo
mostrado sozinho, com aviso · `main` só muda na Fase 8 · Hermes/Ollama de produção
intocados · o GGUF `rlm-qwen3-8b-v0.1-q4_k_m.gguf` é o único modelo não-reproduzível
(snapshot restic `c19275ec`).

## 6. Acompanhamento próximo — o que fazer

1. Fiquem sincronizados **neste HEAD** (`4f4f657`).
2. Cada vez que o Humano avisar "commitei X" / "novo HEAD": rodem o bloco da §1 de novo e
   releiam o **fim do `LOG.md`**. É barato e mantém vocês a um passo de assumir.
3. A próxima coisa executável é **P7-02** (`P7-02-RUNBOOK.md`) — e ela precisa de `sudo`,
   ou seja, o Humano no teclado de qualquer forma. Não há tarefa "só vocês" pendente.
4. Se o `git` não bater com o descrito aqui, **aí sim** respondam. Fora isso, não precisa
   responder.
