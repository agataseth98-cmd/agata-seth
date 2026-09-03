# P8-07 — o merge para `main` + S7 por sessão independente

**Status:** 🔶 **DRY-RUN FEITO — 2026-09-03 (chat 6).** `git merge --no-ff redesign` num
clone descartável: **rc 0, sem conflito**. Fora de `redesign/`, o merge traz exatamente o
que o P8-00 previu (`.gitignore`, `PROMPT_CARREGAMENTO.md` [âncora — restaurar de `main`],
`models/*`, `scripts/{cifrar_env.sh,conselho_remoto.py,perimetro.sh}`). O descarte da
âncora (`git checkout 4aa90bd -- PROMPT_CARREGAMENTO.md` + `--amend`) aplica limpo.
`perimetro.sh` no tree mergeado: `RESULTADO GERAL: OK — 10 OK · 1 SKIP · 1 PARCIAL · 0
FALHA` — o **1 SKIP é o P-10** (vault não gerado no clone); em `main` real o `post-commit`
regenera → roda `python3 scripts/gerar_obsidian.py` antes do check final para dar 11 OK.
Nota: o merge-commit não dispara o caminho de P-8 do `pre-commit` (nada "staged"); os pares
`.diff`+`APROVADO-` viajam no merge dentro de `redesign/propostas/` — o registro acompanha.
**Ainda falta:** P8-05/06 verdes, o `push` (Humano), a sessão independente p/ o S7.

**É o merge para `main`.** Comando destrutivo nenhum; merge aditivo,
sem `--force`/`reset`/rebase. Autorização explícita do Humano no passo do `push`.

**Objetivo:** `redesign` → `main`. O caminho novo vira o único. Canon == realidade,
confirmado por uma sessão independente.

**Pré-requisitos:** P8-01..P8-06 todos verdes.

## Passos
1. **Pré-merge, no branch:** `git status` limpo; `perimetro.sh` verde (11 controles,
   P-12 incluído); `redesign/grafo/evals/run_all.py` PASS (P8-03).
2. **Merge:**
   ```fish
   git switch main
   git pull --ff-only origin main
   git merge --no-ff redesign -m "redesenho do sistema local Agata -- Fases 0..8 (ver redesign/LOG.md)"
   ```
3. **Descartar a churn da âncora:** `PROMPT_CARREGAMENTO.md` do merge traz o bloco
   `ANCORA-SHA` do branch. Restaurar o de `main` e deixar o `pre-commit` reescrever:
   ```fish
   git checkout HEAD~1 -- PROMPT_CARREGAMENTO.md   # o de main pre-merge
   git commit --amend --no-edit
   ```
   (confirmar o mecanismo exato com `git diff HEAD~1 -- PROMPT_CARREGAMENTO.md` na frente —
   P8-00 previu isto.)
4. **`perimetro.sh` em `main`** — verde, 11 controles, P-12 incluído. Se algo `scripts/*`
   staged não bater byte a byte com `.diff`+`APROVADO-`, o P-8 trava — resolver antes do push.
5. **Push:** `git push origin main` — **"vai" explícito do Humano aqui.**
6. **S7 pós-push por sessão INDEPENDENTE** (Cadeia de auditoria, item 6): outra sessão
   (Claude Code nova, ou fallback afinado com acesso ao remoto) faz `git fetch` + confere
   `git rev-parse origin/main` contra o hash que esta sessão reportou, roda `perimetro.sh`
   do checkout limpo, e re-roda o aceite de fabricação. Resultado no `LOG.md` **pela sessão
   independente**, não por esta.
7. **`pre-redesign` fica** como tag do estado anterior (rollback total: `git reset --hard
   pre-redesign` em `main` — destrutivo, mostrado sozinho, só com "vai" e só se o cutover
   falhar feio).

## Aceite (ROADMAP)
- `perimetro.sh` **verde incluindo P-12** em `main` pós-merge.
- **S7 pós-push por sessão independente** — hash cruzado, `perimetro.sh` e fabricação
  re-rodados por quem não fez o merge.
- **canon == realidade** — `ONDE_ESTAMOS.md`/`PROJETO.md` descrevem o que está rodando.
- `redesign/LOG.md` e as entradas (0–8) de `MEMÓRIAS.md` contam a história completa.

## Verificação independente
O passo 6 **é** a verificação independente, e é obrigatória (Cadeia, item 6: "push alegado
nunca é cruzado contra o hash real"). Esta sessão não fecha a Fase 8 sozinha.

## Rollback
Antes do push: `git switch redesign; git branch -D` de qualquer merge local. Depois do push:
`git revert` do commit de merge (aditivo, seguro) ou, em último caso e só com "vai",
`git reset --hard pre-redesign` + `git push --force-with-lease` (destrutivo — mostrado
sozinho, com aviso).

## Registro
`STATUS.md`: FASE ATUAL → "redesenho FECHADO"; `main` @ \<hash\>.
`LOG.md`: o merge, o tratamento da âncora, o `perimetro.sh` de `main`, e **o bloco da
sessão independente** (S7). `ONDE_ESTAMOS.md` já reescrito em P8-06.
