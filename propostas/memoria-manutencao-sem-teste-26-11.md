# Proposta memoria-manutencao-sem-teste-26-11 — forward-declara SEM_TESTE[P-28]

Classe: Comportamento (`scripts/testar_perimetro.sh`).

**Origem:** correção de omissão na proposta `memoria-manutencao-26-11` (PR #1130, já mergeada). A aplicação dela foi barrada pelo `pre-commit` (P-16: controle sem caso na suíte e sem motivo escrito), mesmo caso que P-24 e P-26 resolvem por `SEM_TESTE`.

## O que muda

Uma linha nova em `scripts/testar_perimetro.sh`, dentro do mapa `SEM_TESTE`: entrada para `P-28` com o mesmo texto estrutural dos `P-24`/`P-26` (AVISO só, `_acusacoes()` não conta), apontando a medida isolada feita na proposta memoria-manutencao-26-11 (MORNO 1.173.260 B contra limite 1.024.000 B).

## O que **não** muda

Nada mais. O `P-28` em si continua no PR #1130 já mergeado, aguardando a aplicação separada.

## Por que separada

O lote `memoria-manutencao-26-11` já tem assinatura do Humano (sha256 `bff1eefc0cb4`). Alterar aquele `.diff` invalidaria a assinatura. A forma limpa é um lote corretivo mínimo: uma linha em `SEM_TESTE`. Depois dessa aplicação, a aplicação do `memoria-manutencao-26-11` passa no P-16.

## Testado

- `scripts/ci_sdd_local.sh` com pytest 9.2.0: **94/95 OK**. Única falha: `[1/95] testes SDD (pytest)` → `ModuleNotFoundError: No module named 'yaml'` em `tests/ferramentas_unificadas/ferr_helpers.py`. Pré-existente no `origin/main` (b32fe9e2, hoje `633aaab2`), já registrada por Codex em cache 964.
- `pytest redesign/projeto_indice/tests/`: 24/24 OK depois de `python3 scripts/gerar_estado.py` (ESTADO.md é regerado pelo pre-commit no commit real).
- `git apply --check` em worktree limpa de `origin/main`: OK.

## Reversão

`git apply -R propostas/aplicadas/memoria-manutencao-sem-teste-26-11.diff`.

## Apetite (R2)

1 arquivo, 1 linha. Mínimo.

## Assinatura

`bash scripts/aprovar.sh memoria-manutencao-sem-teste-26-11`
