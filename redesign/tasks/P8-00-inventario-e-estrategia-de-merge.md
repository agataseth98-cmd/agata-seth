# P8-00 — inventário do cutover + estratégia de merge

**Status:** ⏳ a fazer (só leitura + doc — zero risco).

**Objetivo:** fixar exatamente o que a Fase 8 leva para `main`, o que **não** leva, a
ordem dos passos P8-01..P8-07, e a estratégia do merge. Nada é aplicado aqui.

**Pré-requisitos:** Fase 7 fechada (P7-01 ✅, P7-02 hook ✅, P7-03 ✅; falta só o teste do
`agata-jogo` num jogo real — não bloqueia o desenho da Fase 8).

---

## O que difere `main..redesign` FORA de `redesign/` (o que toca o sistema)

`git diff main..redesign --stat -- ':!redesign/'` (03/09/2026):

| arquivo | mudança | como entra em `main` |
|---|---|---|
| `.gitignore` | +12 linhas (vault, venvs, plugin `data.json`) | direto no merge — é aditivo, sem risco |
| `PROMPT_CARREGAMENTO.md` | ±10 linhas — **só o bloco `ANCORA-SHA`**, reescrito pelo `pre-commit` a cada commit do branch | **EXCLUIR do merge.** É churn de máquina por-branch; `main` tem o seu. `git checkout main -- PROMPT_CARREGAMENTO.md` depois do merge, ou merge seletivo. |
| `models/manifest.json`, `models/PRUNE.md`, `models/RECONSTRUCAO.md` | novos / expandidos (Fase 3) | direto no merge |
| `scripts/conselho_remoto.py` | −251/+70 (Fase 1 P1-04) — rede → OmniRoute. **Foi `git commit --no-verify` no branch, nunca passou pelo P-8.** | **P8-01** — par `propostas/conselho-remoto-omniroute.diff` + `APROVADO-` retroativo, ou Cadeia de auditoria em camadas. |

Tudo o mais que difere está dentro de `redesign/` (workspace + tasks + LOG + systemd
specs). Decisão a registrar aqui: **`redesign/` acompanha o merge** como registro histórico
do redesenho (não se apaga história), OU fica só no branch. Recomendação: acompanha —
é o `LOG.md` do processo, e o canon vai citá-lo.

## Pendências abertas por passo

| passo | pendência | destrava com |
|---|---|---|
| P8-01 | `cifrar-env.diff` sem `APROVADO-` | Humano cria `redesign/propostas/APROVADO-cifrar-env` |
| P8-01 | `conselho_remoto.py` sem par P-8 | gerar o `.diff` retroativo + cadeia/aprovação |
| P8-02 | paralelo N dias não rodou | N e critério "empatou/melhorou" = Humano |
| P8-04 | Goose não instalado (`which goose` → nada) | pesquisar instalação + `sudo`/`pipx` |
| P8-06 | canon (`REGRAS`/`PROJETO`) intocado | Cadeia de auditoria em camadas + 2ª opinião |

## Estratégia de merge (rascunho — confirmar no fim da Fase 8)

1. Branch `redesign` já está limpo e empurrado a cada passo.
2. `main` recebe via **merge com `--no-ff`** (preserva a história do redesenho como um ramo
   identificável), **depois** `git checkout main -- PROMPT_CARREGAMENTO.md` para descartar
   a churn da âncora, `git commit --amend` ou commit de ajuste.
   *Alternativa:* `git merge -s ort -X ...` não resolve isto — a âncora precisa de override
   explícito. Decidir o mecanismo exato em P8-07 com a árvore na frente.
3. **Nada de `--force`/`reset`/rebase em `main`.** O merge é aditivo.
4. Pós-merge: `perimetro.sh` verde (11 controles, P-12 incluído) + **S7 por sessão
   independente** (P8-07).

## Ordem dos passos

`P8-01` (fecha P-8 de `scripts/*`) → `P8-02` (paralelo) ‖ `P8-04` (Goose) →
`P8-03` (reteste de fabricação no caminho novo) → `P8-05` (Hermes sai do loop) →
`P8-06` (canon = realidade) → `P8-07` (merge + S7 independente). **Fecha o redesenho.**

## Aceite
`redesign/tasks/P8-01..P8-07` existem no schema; este arquivo lista o diff real
`main..redesign`, as pendências, e a estratégia de merge. Sem nada aplicado.

## Verificação independente
Um 2º olhar (fallback afinado, Humano, ou `gpt-5.6-terra`) confere: o `git diff
main..redesign -- ':!redesign/'` bate com a tabela acima; a estratégia de merge não fere
"main só muda na Fase 8, sem force/reset/rebase".

## Rollback
N/A — nada aplicado.

## Registro
`STATUS.md`: FASE ATUAL → Fase 8; P8-00 → Feito; lista de pendências.
`LOG.md`: o diff real, a estratégia de merge, a ordem.
