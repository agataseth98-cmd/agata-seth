# Decreto: a caixa de ferramentas indexa só as skills próprias versionadas (01/11/2026)

Problema medido em 01/11/2026: `ferramentas.py` varria `.agents/skills/` pelo disco. No checkout vivo existem 5 cópias de terceiros ignoradas pelo git (`defuddle`, `json-canvas`, `obsidian-*`, listadas em `.git/info/exclude`), então a varredura local dava 18 skills próprias contra 13 no índice do `main`, e `test_indice_em_dia` falhava só nesse checkout.

Mudança: `skills_proprias()` usa `git ls-files` (só o que está versionado); fora de um repositório git, volta à busca no disco. Novo teste garante que toda skill própria indexada está versionada. O índice não muda (413 peças, tema `agata` com 13); confirmado também com uma skill solta criada e removida num worktree: ela não entrou no índice.

Só `ferramentas/ferramentas.py` e `ferramentas/test_ferramentas.py`. Consequência a saber: uma skill nova só entra no índice depois de commitada.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh ferramentas-rastreadas-20261101 "aprovo: caixa indexa só skills versionadas"`.
