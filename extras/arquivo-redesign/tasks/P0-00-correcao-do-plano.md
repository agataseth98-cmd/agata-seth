# P0-00 — correção do plano da Fase 0 (antes de qualquer instalação/escrita)

**Objetivo:** corrigir os defeitos no plano de execução da Fase 0 achados por auditoria
antes de rodar P0-01/P0-02 de verdade.

**Origem:** auditoria de `gpt-5.6-terra` (t=14), 01/09/2026, relayada pelo Humano.
8 achados — todos confirmados na Máquina por este executor (sessão Claude, na Máquina).

**Pré-requisitos:** nenhum. É a primeira tarefa da Fase 0.

**Status:** ✅ FEITO — 01/09/2026, sessão Claude (Claude Code, na Máquina).

---

## Achados e o que foi feito

| # | Achado (confirmado) | Correção aplicada |
|---|---|---|
| 1 | `git add -A redesign` do "registro" podia carregar um venv | `.gitignore` já cobria `.venv/`; adicionadas linhas explícitas `redesign/**/.venv/`, `redesign/**/__pycache__/`, `redesign/**/*.pyc`, `redesign/mcp/.venv/`. Verificado com `git check-ignore`. |
| 2 | `query_canon` dito read-only, mas `consultar_indice.py --rebuild` **escreve** (regenera o índice) — confirmado nas linhas 42-43/77 do script | P0-02: `query_canon` valida cada termo contra `^[\wÀ-ÿ][\wÀ-ÿ\- ]*$` e **rejeita qualquer argumento começando com `-`**. Aceite novo cobre isso. |
| 3 | `check_citation` descrito como passthrough de stdin, mas `checar_citacao.sh` recebe **caminho de arquivo** (`$1`, linhas 30/36/141) | P0-02: especificado o adaptador de temp (mkstemp → chama o script → `unlink` no `finally`), com código. |
| 4 | `commit_entry` na Fase 0 contradiz "canon só muda na Fase 8" e não é wrapper fino | P0-02: `commit_entry` **removida**; movida para o nó `registrar+commitar` do grafo, Fase 4. Tools da Fase 0 agora são 5, todas read-only. |
| 5 | `models/manifest.json` do gerador antigo não tinha SHA-256 nem origem → aceite de "reconstrução" não se sustentava | P0-01 passo 2: gerador reescrito — captura `blob_sha256` (64 hex da linha `FROM .../blobs/sha256-...`), `blob_path`, `origem` e o **Modelfile completo**. Regenerado agora: 20/20 modelos com sha256. |
| 6 | `rm -rf` em rollbacks sem bloco isolado e sem aviso destacado — viola a própria invariante do `README` | P0-01 e P0-02: rollbacks não destrutivos separados; o `rm -rf`, quando existe, fica em bloco isolado com `⚠️ DESTRUTIVO`. |
| 7 | `git log --oneline -12 redesign` é ambíguo (`redesign` também é diretório) — **falhou de verdade** nesta sessão | `CONTINUIDADE.md`, bloco do PRIMEIRO MOVIMENTO: trocado por `git log --oneline -12 HEAD --`. |
| 8 | Efeito automático da âncora SHA em `PROMPT_CARREGAMENTO.md` a cada commit do branch não estava registrado | `README.md`: seção nova "Efeito automático esperado nos commits deste branch". |

---

## Aceite

- `.gitignore` cobre `redesign/**/.venv/` (verificado com `git check-ignore`).
- `models/manifest.json` tem `blob_sha256` para todos os modelos.
- P0-02 lista 5 tools, sem `commit_entry`, com `query_canon` anti-flag e o adaptador de
  temp do `check_citation` especificado.
- `CONTINUIDADE.md` não tem mais `git log ... redesign` ambíguo.
- `README.md` registra o efeito da âncora.

## Rollback

`git revert` do commit desta tarefa (só toca arquivos de `redesign/` + `.gitignore` +
`models/manifest.json`; nada em `main`, nada instalado).

## Registro

- `STATUS.md`: P0-00 → "Feito"; P0-01 → parcial (ver notas de coordenação).
- `LOG.md`: entrada com os 8 achados e as correções.
