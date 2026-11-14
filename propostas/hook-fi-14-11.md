# Pre-commit sem `fi` depois do pacote-14-11 (`hook-fi-14-11`)

Proposta P-8 de `hook-fi-14-11`. Diff: `propostas/hook-fi-14-11.diff` (3 arquivos, 4 linhas inseridas; sha256 `9e12c966907a1cae50732f163c08cbb94f4e2736c4e7d3388d1ac8b73e0ac0b9`). Base: `origin/main` `c716b9ce`.

## Causa (medida)

Ao compor o `pacote-14-11`, o Claude Opus 5.5 resolveu à mão o conflito do `.githooks/pre-commit` mantendo os dois blocos novos. O bloco dos workflows, da fiscal-yaml, perdeu o `fi` de fechamento, que no arquivo original ficava fora da região em conflito. O resultado é `linha 177: erro de sintaxe: fim inesperado do arquivo do comando 'if' na linha 36`: todo commit com os ganchos do repositório falha. O erro foi medido em 14/11, às 18h, no primeiro commit depois da aplicação.

Nenhum CI pegou o erro. O CI local, o `sdd`, o perímetro e o fiscal não rodam o `pre-commit` como script.

## Correção

1. `.githooks/pre-commit`: devolve o `fi` (e uma linha em branco) depois de `rm -rf "$_wf_tmp"`.
2. Mecanismo: um passo novo no `ci_sdd_local.sh` e no `sdd.yml` roda `bash -n` em todo gancho shell de `.githooks/`. Com o erro de hoje, o passo teria falhado.

## Como foi commitada

Esta proposta foi commitada com `git -c core.hooksPath=<cópia dos ganchos com a correção>`, e não com `--no-verify`: o perímetro, as âncoras e a hidratação rodaram normalmente.

Reversão: `git revert` do commit de aplicação.
