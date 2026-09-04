# P4-06 — adapter dsh escrito, `enabled: false` (armado, dormente)

**Status:** ✅ **FEITO — 2026-09-02 ~14:30 (relógio da máquina). FASE 4 FECHADA.**
`adapters/dsh.md` (mapa 6 nós↔seams do `dsh`, o que ganha/perde, gatilho de reavaliação) +
`adapters/dsh.py` (`ENABLED=False`, `run`/`resume` levantam `NotImplementedError`, interface
idêntica à de `grafo.py`) + `adapters/teste_dormente.py` (**PASS** — `ENABLED is False`,
levanta, assinaturas batem, não importado pelo loop). `PESQUISA.md` linha do `dsh` com o
gatilho. **Não instalou** o preview. Ver `redesign/grafo/README.md`.

**Incidente no aceite da fase (registrado):** um teste com args em ordem errada
(`repo="onep"`) fez `git -C onep commit` subir a árvore e commitar lixo no branch
`redesign` (local, **não empurrado**). Revertido: `git reset --soft HEAD~1` + restore do
`PROMPT_CARREGAMENTO.md` + `gerar_obsidian.py` (P-10) + `rm -rf onep`. HEAD de volta em
`81b2aea` = `origin/redesign`. **Trava adicionada:** `tools._exige_raiz_git` — `commit_entry`
e `registrar_e_commitar` abortam se `repo` não for raiz de worktree git. Ver `LOG.md`.

**Objetivo:** deixar escrito — e testado no que dá sem instalar o preview instável — um
adapter que trocaria o LangGraph pelo DeepSeek Harness (`dsh`) como executor do loop, com
a flag desligada. Reavaliar só quando o `dsh` tiver tag estável.

**Pré-requisitos:** P4-01 FEITO (o contrato do loop existe — é o que o adapter tem que cumprir).

**Arquivos:**
- `redesign/grafo/adapters/dsh.md` — o mapa: nós do grafo ↔ seams do `dsh`
  (models/tools/skills/sessions/sandboxes/storage/loops/scheduling/UI), o que o log
  append-only nativo do `dsh` substitui do WAL do P4-00, o que fica pendente
- `redesign/grafo/adapters/dsh.py` — stub com a interface, `ENABLED = False`, `raise
  NotImplementedError("dsh preview instavel — ver PESQUISA; reavaliar em tag estavel")`
- `redesign/tasks/P4-06-*.md`

> Classe de risco: doc + stub. **Não instala `dsh`** (preview `0.1.0-rc.5`, "THERE WILL BE
> COMPATIBILITY-BREAKING CHANGES" — PESQUISA). Auto-revisão leve.

---

## Passos

1. **`dsh.md`** — tabela nó↔seam. Onde o `dsh` **ganha** (session log append-only nativo →
   menos WAL caseiro; sandboxes é seam de 1ª classe) e onde **perde** hoje (instável, Node
   24, micro-kernel Cordis em fluxo). O que o adapter precisaria implementar por seam.
2. **`dsh.py`** — a mesma assinatura que o `grafo.py` expõe (`run(pedido) -> resultado`,
   `resume(thread_id)`), corpo `raise NotImplementedError` guardado por `ENABLED = False`.
   Um teste que só confirma que `ENABLED is False` e que a interface bate com a do
   LangGraph (mesmos métodos/tipos).
3. Nota em `PESQUISA.md` (linha do `dsh`): "adapter dormente escrito em P4-06; gatilho de
   reavaliação = tag estável / fim do aviso de breaking changes".

## Aceite

- `redesign/grafo/adapters/dsh.md` mapeia os 6 nós aos seams do `dsh` e lista os pendentes.
- `dsh.py` tem `ENABLED = False`, a interface idêntica à do `grafo.py`, e levanta se chamado.
- `dsh` **não** foi instalado; nada no venv depende dele.
- `PESQUISA.md` registra o gatilho de reavaliação.

## Verificação independente

- **Quem:** fallback ou Humano. **O quê:** que a flag está `False` e que a interface do
  stub == a do `grafo.py` (para o swap ser mecânico no futuro). **Como:** `grep ENABLED`;
  `diff` das assinaturas. **Resultado:** no LOG.

## Rollback

`git checkout -- redesign/grafo/adapters`. Não destrutivo.

## Registro

- `STATUS.md`: P4-06 → "Feito"; **Fase 4 FECHADA** (com P4-00..P4-05).
- `LOG.md`: o mapa nó↔seam em 1 parágrafo, a confirmação `ENABLED=False`, `HEAD`.
