# Teto de profundidade do sanitizador sobe de 12 para 32 (`teto-sanitizador-17-11`)

Classe: Comportamento (código).

Proposta P-8 de `teto-sanitizador-17-11`. Diff: `propostas/teto-sanitizador-17-11.diff` (1 arquivo, 49 linhas). Base: `origin/main` (48da27d1). O diff não traz registro nem `ONDE_ESTAMOS.md`; esses entram no PR de proposta, fora do diff assinado.

Decisão do Humano (17/11/2026, 10:49): "pode fazer", em resposta à oferta deste P-8.

## Problema medido

Em 17/11, 10:30 a 10:31, a rota seth-livre devolveu 422 três vezes, categoria teto-de-varredura-excedido (journalctl do usuário). O erro gravado pelo OpenCode aponta o campo `tools[4].function.parameters.properties.questions.items.properties.options.items.properties.label.type`, com profundidade 13 e 126 nós. É o schema da tool `question` do OpenCode TUI. O teto era 12, com o comentário de que payload real não passaria disso; deixou de ser verdade.

Contenção já feita fora do repo: `"tools": { "question": false }` em `~/.config/opencode/opencode.jsonc` (cópia em `~/agata-arquivo/opencode.jsonc.bak-2026-11-17`). Depois de aplicada esta proposta, a linha pode sair e a tool volta.

## O que muda

1. `redesign/router/sanitizar.py`: `_PROFUNDIDADE_MAX` passa de 12 para 32, com o motivo no comentário. O teto de nós (20000) não muda. Acima do teto continua falha fechada (422).
2. Autoteste: o caso "acima do teto" passa a usar `_PROFUNDIDADE_MAX + 1`; entram dois casos novos: segredo no nível 13 continua bloqueado (agora é varrido de verdade), e o schema da tool `question` (profundidade 13) não bloqueia.

## Medido (17/11/2026)

- `python3 redesign/router/sanitizar.py --autoteste`: `AUTOTESTE OK`, com os 5 casos de teto em PASS (33 > 32 bloqueado; segredo no nível 13 bloqueado; nós > 20000 bloqueado; tool question não bloqueia; payload normal não bloqueia).
- CI local (`scripts/ci_sdd_local.sh`, pytest 9.2.0 conferido por `--version`): `CI LOCAL: TUDO OK`, 88 linhas OK, 0 FALHA, rc=0. Log: `/home/orusoua/agata-arquivo/teto-sanitizador-17-11/ci-local.log`.
- Cópia limpa `check-teto-sanitizador-17-11` a partir de `origin/main`: `git apply --check` = APLICA; `git apply` = APLICADO; autoteste na cópia: `AUTOTESTE OK`.
- `grep '^diff --git'`: 1 caminho, `redesign/router/sanitizar.py`.

## Não medido

- O TUI do OpenCode com a tool question religada, depois de aplicado (passo da aplicação: tirar a linha da config, reiniciar o gateway, mandar uma mensagem e conferir journalctl sem 422).
- Custo de tempo da varredura com profundidade até 32 (o teto de nós é o que limita o trabalho, e não muda).

## Reversão

`git apply -R propostas/aplicadas/teto-sanitizador-17-11.diff` numa worktree a partir do `main`, por proposta; religar `"tools": { "question": false }` na config do OpenCode.

## Comando de assinatura

Depois do merge deste PR, no terminal, sem `!`:

bash scripts/aprovar.sh teto-sanitizador-17-11

## Modelos

Claude Opus 5.5 (Claude Code, na Máquina), sem agentes.

## Definição de pronto (R3)

- [x] CI local com `CI LOCAL: TUDO OK` (log acima)
- [ ] run verde no GitHub no `headSha` do PR (fica no registro do PR)
- [x] captura de tela: não se aplica (sem interface)
- [x] sem emoji no `.md`
- [x] testes medidos, o que não foi medido e a reversão (acima)
- [x] nenhuma falha pré-existente sem dono e data
- [x] texto da entrada de MEMÓRIAS sem citação `caminho:número`
