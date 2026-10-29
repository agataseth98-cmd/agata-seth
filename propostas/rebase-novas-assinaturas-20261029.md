# Reaplicação das propostas assinadas em 29/10/2026

As propostas `conselho-hidratacao-f1-20261029`, `conselho-estudo-f2-20261029` e `seth-painel-raiz-20261029` foram assinadas, mas os diffs deixaram de aplicar no `main`. Motivo: a expiração de itens (`EXPIRY`) e o atalho `seth` mudaram depois da geração dos diffs originais (PR #721 e PR #715).

Esta proposta refaz os mesmos conteúdos sobre o `main` atual, em dois diffs:
- `conselho-f1-f2-rebase-20261029.diff`: hidratação de todo envio (F1) e estudo como unidade com síntese por estudo (F2). Mantém `EXPIRY = 300`.
- `seth-painel-raiz-rebase-20261029.diff`: a primeira aba da Seth é o painel `/prototipo`.

Validado: os dois diffs aplicam no `main` limpo. Com as mudanças, `test_conselho_rede` passa com 17 testes.

Assinaturas necessárias: as duas novas. As antigas não aplicam mais e não devem ser usadas.
