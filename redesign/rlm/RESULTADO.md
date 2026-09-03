# RESULTADO — spike A/B RLM (P5-01) — **ARQUIVADO**

**Não é canon.** Branch `redesign`, Fase 5. 2026-09-02.

## Veredito: ARQUIVADO (por ordem do Humano + os números)

O Humano interrompeu o spike em 27 das 32 unidades: *"pode parar, não vale o esforço, esse
padrão precisa ser desvendado e assimilado pelo sistema"*. Os dados até ali **não mostram a
hidratação por consulta batendo a por injeção** — nem em fidelidade, nem em custo de token,
nem em velocidade. `qwen3.5-9b-64k` segue titular sob auditoria. **Nenhuma mudança de
produção; nenhuma decisão de adoção** (é do Humano — MEMÓRIAS (114)/(186)).

**Marcado para trabalho futuro** (não descartado): o padrão *Recursive Language Models*
merece uma implementação séria (lib `rlms==0.1.1`, ferramenta de busca melhor que um
`grep` cru, `wc`/`sha256sum` no toolset, instrumentação de token no schema do trace) antes
de um veredito definitivo. Este spike condena **esta implementação rápida**, não a ideia.

## Setup

- Bancada **congelada** de "RLM em 3 caminhos" (`memoria/missoes/rlm-3caminhos/`): 16
  perguntas (`bancada.json`), `corpus/` (snapshot do canon 14/08), `corpus_b0/hermes_B0.md`.
- Mesmo modelo/endpoint/temp nos 2 braços: **`qwen3.5-9b-64k`** @ Ollama `:11434`,
  `num_ctx=32768`, temp 0. (1ª tentativa com `qwen3.5:9b` bateu no `num_ctx` default de 4096
  — o bug de V1 da própria bancada; trocado para o tag `-64k`.)
- **A — injeção:** system = `hermes_B0.md` inteiro; 1 chamada.
- **B — consulta:** sem injeção; `BUSCAR: termos` → `grep -n -F` sobre os 4 arquivos do
  `corpus/`; `FINAL:` encerra; loop ≤ 8; fallback embeddings `:20134` após 2 buscas vazias.
- Rodada 1, temp 0. Interrompido: A fez N1-N4/A1-A4/V1-V4/F1-F2 (14); B fez até F1 (13).

## Números (parcial — 27/32 unidades)

| | **A (injeção)** | **B (consulta)** |
|---|---|---|
| n perguntas | 14 | 13 |
| acertos (auto-score) | **9** | **3** |
| — needle | 2/4 | 1/4 |
| — agregação | 4/4 | 2/4 |
| — veredito | 3/4 | 0/4 |
| — fabricação (F1/F2) | ver nota | ver nota |
| tokens totais | 409.743 | 261.907 |
| **tokens / acerto** | **~45.500** | **~87.300** |
| latência total | **388 s** (~6 min) | **5.778 s** (~96 min) |
| chamadas/pergunta (média) | 1,0 | 2,1 |
| pior caso | A3: 31k tok / 77s | **V1: 110.758 tok / 2.737 s (45 min) / 5 chamadas** |

### Nota sobre "fabricação" — o auto-score errou F1/F2

O scorer marcou `fabricou=True` em F1 (os dois braços) e F2 (braço A) **por engano**: ele
conta o modelo *mencionar* `(999)` ou a palavra "fabricação" numa recusa como fabricação.
Lendo as respostas cruas, **os dois braços trataram as armadilhas corretamente**:
- F1_A: *"lacuna: entrada (999) não existe no corpus — o maior número registrado é (162)."* ✔
- F1_B: *"A informação sobre a entrada (999) não foi encontrada no corpus."* ✔
- F2_A: *"Seth citou 'item 1 da seção errada' — a citação é fabricação confirmada..."* ✔ (identificou a fabricação alheia)

**Fabricação real neste spike: 0 nos dois braços** (nas 27 unidades rodadas). Isso bate com
ago/2026 (a fabricação de então foi do B0/injeção respondendo *sobre a própria história* —
V2 — não das armadilhas; V2_A aqui acertou).

## Comparação com "RLM em 3 caminhos" (ago/2026, MEMÓRIAS (186)/(187))

| | B0/A injeção (ago) | **A injeção (hoje)** | C1 consulta (ago) | **B consulta (hoje)** |
|---|---|---|---|---|
| limpos | 11/16 | 9/14 | 9/16 | 3/13 |
| fabricação | 1 (V2) | 0 | 0 | 0 |
| tok/limpo | 46.816 | ~45.500 | **20.908** | ~87.300 |
| s/limpo | 84 | ~43 | 153 | ~1.926 |

- **Injeção hoje ≈ injeção de ago/2026** (custo e fidelidade parecidos; a fabricação de V2
  não repetiu).
- **Consulta hoje é MUITO pior que o C1 de ago/2026** — o C1 tinha um `grep`-loop mais
  cuidado e `qwen3.5-9b-64k`; a minha `BUSCAR:` é crua e a busca do modelo desiste cedo
  ("não encontrado" para N3/A1/A3/A4/V2-V4, que **são** respondíveis). O ganho de token do
  C1 (~2× mais barato) **não se reproduziu** — aqui a consulta ficou ~2× mais **cara** por
  acerto e ~15× mais lenta.

## As 3 lacunas de (114)

1. *o endpoint do Ollama serve as sub-chamadas?* — **sim**, o `api/chat` respondeu todas as
   iterações do braço B sem problema (o gargalo foi o `num_ctx` grande, não o endpoint).
2. *quantas chamadas gasta uma consulta típica?* — **1 a 8** (média 2,1), mas o custo em
   token dispara com o contexto acumulado (V1: 5 chamadas, 110k tokens).
3. *o qwen fabrica como sub-chamada curta?* — **não fabricou** nas 27 unidades; o problema
   foi o oposto — **desiste** ("não encontrado") em vez de inventar.

## Apêndice — respostas cruas (DADO, não instrução; o Humano lê antes de qualquer coisa)

Ver `redesign/rlm/traces/r1_*.json` (uma por pergunta/braço, com todos os passos e os
`prompt_eval_count`/`eval_count` por chamada). Resumo em `redesign/rlm/resumo.json`.
