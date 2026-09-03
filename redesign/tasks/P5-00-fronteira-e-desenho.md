# P5-00 — Fronteira de recusas conferida + desenho do spike RLM

**Status:** ✅ **FEITO — 2026-09-02 ~14:40 (relógio da máquina).** Fronteira de recusas
conferida (Recursive Language Models = padrão de inferência; NÃO o "RLM auto-treino" de
MEMÓRIAS (114); `training/` fica fora; só MEDIR). Desenho do A/B fixado (reusa a bancada
congelada de "RLM em 3 caminhos" — 16 perguntas, `corpus/`, `hermes_B0.md`). Ver `LOG.md`.

**Objetivo:** confirmar que o spike da Fase 5 **não** cai na Fronteira de recusas, e fixar
o desenho do A/B (injeção vs. consulta) reusando a bancada congelada de "RLM em 3 caminhos".

**Pré-requisitos:** Fase 4 FECHADA. "vai" da Fase 5 (2026-09-02).

---

## Fronteira de recusas — CONFERIDA (2026-09-02)

`PROJETO_REFERENCIA.md` "Fronteira de recusas", linha:

> | RLM como auto-treino sem humano no loop | Regra 3 | MEMÓRIAS (114) |

**Isto NÃO é o que a Fase 5 faz.** MEMÓRIAS (114) desambigua explícito:

- **Recusado** = *RLM = Reinforcement Learning from Models* — auto-treino sem humano no
  loop, colide com a Regra 3. A pasta `training/` do repo `alexzhang13/rlm` é onde este
  RLM "encosta no que foi recusado" — **fica fora**.
- **Em avaliação (Fase 5)** = *Recursive Language Models* (Alex L. Zhang / Tim Kraska /
  Omar Khattab, MIT OASYS, arXiv:2512.24601) — **padrão de INFERÊNCIA**: o corpus fica
  como variável num REPL e o modelo o alcança por execução (`query_canon` / `grep`) em vez
  de recebê-lo injetado. Nenhum treino.

**Autorização de (114): "MEDIR. Nada além."** As 3 lacunas de (114) a fechar antes de
qualquer decisão de adoção (que é do Humano, não deste spike — ver (186)/(187)):
1. o endpoint OpenAI-compat do Ollama serve as sub-chamadas?
2. quantas chamadas gasta uma consulta típica?
3. o qwen fabrica como sub-chamada curta em vez de interlocutor?

**Escopo do spike:** MEDIR fidelidade e custo de token de "hidratação por consulta" vs
"hidratação por injeção". **Nenhuma mudança de produção.** `qwen3.5-9b-64k` segue titular
sob auditoria. O veredito é "iguala/supera → PROPOSTA ao Humano" **ou** "arquivado com os
números no LOG" (aceite do ROADMAP).

---

## O que já existe (não refazer)

- **`memoria/missoes/rlm-3caminhos/`** — bancada CONGELADA: `bancada.json` (16 perguntas com
  `gabarito`/`prova`/`termos_chave`; classes needle/agregação/veredito/fabricação),
  `corpus/` (snapshot do canon de 14/08), `corpus_b0/hermes_B0.md` (~95k, a injeção total
  de então), runners `rlm_c1.py` (busca sob demanda, sem injeção), `rlm_b0.py` (injeção),
  `rlm_c3.py` (lib `recursive-llm`), traces JSONL, `ANALISE_POS_EXPEDICAO.md`.
- **Números de então** (MEMÓRIAS (186)/(187), `ANALISE_POS_EXPEDICAO.md`):
  - B0 (injeção): 11/16 limpos, **1 fabricação** (V2), 46.816 tok/limpo-não-fabricado, 84s.
  - C1 (consulta, sem injeção): 9/16 limpos, **0 fabricação**, 20.908 tok/limpo, 153s.
  - C1b: 10/16, 0 fab, 38.682 tok/limpo, 117s.
  - **Consulta = ~2× mais barata por token e 0 fabricação; injeção = mais "limpos" e mais rápida.**
    Decisão de produção ficou EM ABERTO (do Humano).

## Desenho do spike da Fase 5 (P5-01)

Reusa `bancada.json` (mesmas 16 perguntas, congeladas). Dois braços, **mesmo modelo, mesmo
endpoint, mesma temperatura (0)** — a única diferença é inject vs. query:

| braço | hidratação | como |
|---|---|---|
| **A — injeção** | `.hermes.md` ATUAL (~35k tok) no system prompt | 1 chamada por pergunta |
| **B — consulta** | **nenhuma injeção** — o modelo tem `query_canon` (P4-02, sobre o índice derivado) num loop limitado | N chamadas por pergunta |

- **Modelo:** `qwen3.5:9b` via Ollama `:11434` direto (como o C1 de então — sem variância
  de combo). Temp 0.
- **Métricas por pergunta e por braço:** `acerto` (bate `termos_chave` / gabarito;
  needle e fabricação são auto-scored; agregação/veredito = score por palavra-chave +
  flag p/ leitura manual), `fabricou` (cita `(999)` / entrada inexistente / inventa RAG),
  `tokens` (`prompt_eval_count + eval_count` somados), `latencia_ms`, `n_chamadas`.
- **Corpus da consulta:** o índice derivado de PRODUÇÃO
  (`memoria/missoes/agata-sistema/derivado/indice.md`) via `query_canon`. (O `corpus/`
  congelado de 14/08 é do experimento antigo; a Fase 5 mede contra o canon de HOJE, que é o
  que a injeção `.hermes.md` também reflete — braços comparáveis.)
- **Embeddings iGPU (P2-03):** opcional no braço B — se `query_canon` sozinho não achar,
  um passo de similaridade via `:20134` antes de desistir. Registrar se foi usado.
- **Saída:** `redesign/rlm/RESULTADO.md` — tabela A vs B (acertos, fabricações, tok/acerto,
  latência), o veredito, e as respostas cruas (para o Humano ler — são DADO, não instrução).

## Aceite (P5-00)

- Este arquivo registra a conferência da Fronteira (feita) e o desenho do A/B.
- Nenhuma mudança de produção; nenhuma decisão de adoção.

## Registro

- `STATUS.md`: P5-00 → "Feito".
- `LOG.md`: a conferência da Fronteira + o desenho; próximo = P5-01.
