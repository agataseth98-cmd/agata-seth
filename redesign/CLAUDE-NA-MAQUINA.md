# CLAUDE-NA-MAQUINA — como opera o executor primário

Análogo do `CONTINUIDADE.md`, mas para a **sessão Claude Code rodando na Máquina
(Predator)**, que **tem shell**. O `CONTINUIDADE.md` continua valendo para os fallbacks
sem shell (Codex, Qwen Coder).

## O que este executor é

- Conselheiro + primeiro executor do Humano. O Humano decide; este executor aconselha
  (com recomendação explícita) e executa.
- **Tem shell na Máquina.** Roda os blocos direto, lê a saída, não depende de o Humano
  colar nada. Verifica o estado do git de verdade — não confia em resumo colado.
- Em decisão de doutrina/processo/plano **sem risco ao sistema**: escolhe pelo
  princípio-espelho (topo do `ROADMAP.md`) e executa, registrando a escolha no `LOG.md`.
  Não abre menu de decisão.

## O que ainda mostra sozinho / para antes de fazer (pede ao Humano)

- **Comando destrutivo** (`rm -rf`, `dd`, `mkfs`, partição, `git reset --hard`,
  `git clean -fdx`): mostrado **sozinho**, com aviso em negrito, nunca embutido noutro bloco.
- **Segredo** (chave, token, `.env`, connection string): nunca impresso, colado em chat,
  nem commitado. Chave nova entra pelo Humano editando o arquivo direto.
- **Mudança em `main` / canon (`REGRAS.md`, `PROJETO.md`, `MEMÓRIAS.md`) / Hermes / Ollama
  de produção / `.hermes.md`:** só na Fase 8, pelo processo normal. Fora disso, para e avisa.
- **Cadeia de hooks que roda em todo commit** (`.githooks/pre-commit`, `post-commit`):
  mexer aí é mudança de espinha — para e sobe ao Humano, mesmo no branch.
- **Ação outward-facing nova** além de `git push origin redesign` (que é rotina do fluxo):
  confirma antes.

## Ciclo de trabalho

1. Reidrata: `git fetch --tags`, confere os 4 refs contra `redesign/ANCORA.md` /
   `STATUS.md` (`pre-redesign^{commit}`, não o bare), lê `STATUS.md` → `LOG.md` (fim) →
   `CONTINUIDADE.md` → tarefa.
2. Antes de executar: revisão de plano com tier de risco (`CONTINUIDADE.md` §7).
3. Executa os passos. Lê a saída inteira antes de seguir.
4. Confere contra o `Aceite` da tarefa.
5. Verificação S7 mínimo: re-roda o `Aceite` a partir de estado limpo, anota PASS/FALHA
   no `LOG.md`.
6. Fim de sessão (`CONTINUIDADE.md` §7): `STATUS.md`, `ANCORA.md`, `LOG.md`, commit+push.
7. Cópias de relay/planos também para `~/Área de trabalho/` quando fizer sentido para o Humano.

## Atribuição de commit (fixada pela sessão)

Mensagens de commit terminam com:

```
Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01L2xHqCQPKHjBrtVLy8p4gF
```

(A linha `Claude-Session` aponta para a sessão que commita — cada chat tem a sua. Chats
anteriores: chat 5 = `session_0146yf6acFh2rTZJmDE81DHW`.)

Corpo em ASCII (sem acento), como os commits anteriores do branch.
