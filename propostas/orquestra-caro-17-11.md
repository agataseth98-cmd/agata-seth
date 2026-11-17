# O mais caro orquestra, os mais baratos executam (`orquestra-caro-17-11`)

Classe: Comportamento (regra comum a todos os modelos).

Proposta P-8 de `orquestra-caro-17-11`. Diff: `propostas/orquestra-caro-17-11.diff` (2 arquivos). Base: `origin/main`. O diff não traz registro nem `ONDE_ESTAMOS.md`.

Decisão do Humano (17/11/2026, 14:07): "a partir de agora o modelo mais caro orquestra e os modelos mais baratos executam, torne isso regra para todos os modelos quando for o caso".

## O que muda

1. `AGENTS.md`, lista "Sempre": regra nova, antes de "Economia de tokens é permanente". O modelo mais capaz da sessão planeja, distribui, revisa e responde pelo resultado; a execução operacional vai para o modelo mais barato que dá conta. Quem orquestra confere o resultado, não o relatório. Tarefa curta é feita direto. Quem executa não decide escopo nem assina.
2. `scripts/testar_sincronia.py`: a contagem de regras do AGENTS.md passa de 15 para 16 (dois asserts), porque o teste fixa o número de regras.

## Medido (17/11/2026)

- CI local (`scripts/ci_sdd_local.sh`, pytest 9.2.0): `CI LOCAL: TUDO OK`, rc=0. Antes do ajuste da contagem, 2 FALHA (sincronia: 16 != 15), corrigidas no item 2. Log: `/home/orusoua/agata-arquivo/roteador-capacidade-17-11/ci-orquestra.log`.
- Cópia limpa a partir de `origin/main`: `git apply --check` APLICA; `testar_sincronia.py` OK.
- `grep '^diff --git'`: `AGENTS.md` e `scripts/testar_sincronia.py`.

## Não medido

- Se os modelos fora do Claude Code (Codex, OpenCode, Seth) passam a seguir a regra; ela entra no texto que todos leem, sem verificação mecânica.

## Reversão

`git apply -R propostas/aplicadas/orquestra-caro-17-11.diff` numa worktree a partir do `main`, por proposta.

## Comando de assinatura

Depois do merge deste PR, no terminal, sem `!`:

bash scripts/aprovar.sh orquestra-caro-17-11

## Modelos

Claude Opus 5.5 (Claude Code, na Máquina), sem agentes neste lote.
