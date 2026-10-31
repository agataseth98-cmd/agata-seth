# Decreto: reindexar a caixa de ferramentas e tornar o teste do índice só de leitura (31/10/2026)

1. `ferramentas/INDICE.md` e `indice.json` passam a incluir `elephant-goldfish-sdd` (skill do Codex, já no main): 412 peças, tema `agata` com 11.
2. `test_indice_em_dia` deixa de rodar `reindexar` e reescrever arquivos versionados; compara o `indice.json` gravado com `varrer()` em memória. Motivo: em 30/10 o teste reescreveu o índice na árvore viva e já havia causado falha no fiscal-p8 do PR #759.

Mudança só em `ferramentas/`. Nenhuma peça foi movida; 4 testes da caixa passam sem alterar a árvore.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh ferramentas-reindex-20261031 "aprovo: reindexar a caixa e teste só de leitura"`.
