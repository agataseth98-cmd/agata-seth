# ESTADO.md sem contagem de aplicadas (`estado-aplicadas-14-11`)

Proposta P-8 de `estado-aplicadas-14-11`. Diff: `propostas/estado-aplicadas-14-11.diff` (2 arquivos; sha256 `c074ba149d2311bf97b8d57760583ef124e16cada78c77393c58bb6d0ac10971`). Base: `origin/main` `5407cb02`.

## Problema (medido em 14/11, no #988)

O `ESTADO.md` traz a linha "Aplicadas (propostas/aplicadas/): N". O pre-commit gera o arquivo, e o `aplicar.py` move a proposta para `aplicadas/` depois disso. O resultado é que, em todo PR de aplicação, a contagem fica um número atrás:
- o `gerar_estado.py --verificar` do `sdd` falha;
- regenerar o arquivo no PR quebra o `fiscal-p8`, que exige o head idêntico à base mais o diff assinado (`divergente: ESTADO.md`).

## Correção

`scripts/gerar_estado.py` para de escrever a contagem. No lugar dela entra a linha fixa "Aplicadas: ver propostas/aplicadas/ (sem contagem aqui, de propósito).", e um comentário no código explica o motivo. As propostas abertas continuam listadas: o arquivo `APROVADO-` já existe antes da aplicação, então a lista não muda no commit de aplicação.

## Testes

- `pytest redesign/projeto_indice/tests`: 24 passaram.
- `git apply --check` limpo.

Reversão: `git revert` do commit de aplicação.
