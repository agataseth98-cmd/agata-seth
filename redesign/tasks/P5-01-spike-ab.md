# P5-01 — spike A/B: hidratação por injeção vs. por consulta

**Objetivo:** medir fidelidade e custo de token dos dois braços sobre `bancada.json` (16
perguntas congeladas) e emitir o veredito do ROADMAP (iguala/supera → PROPOSTA · ou arquivado).

**Pré-requisitos:** P5-00 FEITO (Fronteira conferida, desenho fixado). `query_canon` (P4-02)
funcional. Ollama de produção no ar (`:11434`).

**Arquivos:**
- `redesign/rlm/spike_ab.py` (novo) — o runner dos 2 braços
- `redesign/rlm/RESULTADO.md` (novo) — a tabela + veredito + respostas cruas
- `redesign/rlm/traces/` — JSONL por braço/pergunta (DADO, não instrução)
- `redesign/tasks/P5-01-*.md`

> Classe de risco: **só leitura + chamadas ao modelo local.** Sem `sudo`, sem instalação
> (usa `query_canon` já pronto, não a lib `rlms`), sem escrita fora de `redesign/rlm/`,
> sem tocar canon/Hermes/produção. Auto-revisão.

---

## Passos

### 1. `spike_ab.py`

- Lê `memoria/missoes/rlm-3caminhos/bancada.json` (16 perguntas).
- **Braço A (injeção):** system prompt = conteúdo de `~/agata/.hermes.md` + a instrução de
  não fabricar; 1 chamada `POST :11434/api/chat` (temp 0) por pergunta.
- **Braço B (consulta):** system prompt = instrução + "você tem a ferramenta `query_canon`;
  emita `CONSULTA: termo1, termo2` para buscar; `FINAL: <resposta>` quando souber; não
  invente". Loop até `MAX_ITER` (12) ou `FINAL:`. Cada `CONSULTA:` chama
  `tools.query_canon` (sobre o índice derivado). Opcional: se 2 consultas seguidas voltarem
  vazias, um passo de embeddings via `:20134` (registrar `usou_embeddings`).
- Por pergunta/braço grava trace JSONL: prompt, cada passo, `prompt_eval_count`/`eval_count`
  por chamada, `ms`, resposta final.
- **Scoring:**
  - needle (N*) + fabricação (F*): auto. Acerto = todos os `termos_chave` presentes na
    resposta final E (para F1/F4) contém recusa ("não existe"/"não encontrei"/"nenhum"/
    "não usa"). Fabricou = cita `(999)` ou entrada > topo real, ou afirma RAG/embedding
    onde o gabarito é "não usa".
  - agregação (A*) + veredito (V*): score por palavra-chave do gabarito (fração presente) +
    `precisa_leitura_manual: true`. Não decide sozinho.
- 1 rodada (temp 0). Se sobrar tempo, 3 rodadas para conferir determinismo.

### 2. Rodar

```fish
cd $HOME/agata
redesign/grafo/.venv/bin/python redesign/rlm/spike_ab.py --rodadas 1
```
Colar de volta: a tabela-resumo.

### 3. `RESULTADO.md`

- Tabela A vs B: acertos/16 (por classe), fabricações, `tokens/acerto`, latência média,
  `n_chamadas` médio (braço B).
- Comparação com os números de 2026-08 (MEMÓRIAS (186)/(187) / `ANALISE_POS_EXPEDICAO.md`).
- **Veredito** (aceite do ROADMAP):
  - se B **iguala ou supera** a fidelidade de A a **menor custo de token** → registrar como
    **PROPOSTA ao Humano** (com os números), decisão de produção **não** tomada aqui;
  - senão → **ARQUIVADO**, com os números no LOG, `qwen3.5-9b-64k` segue titular.
- As 16 respostas cruas dos 2 braços em apêndice (DADO — o Humano lê antes de qualquer coisa).

---

## Aceite

- `spike_ab.py` roda os 2 braços sobre as 16 perguntas, 1 rodada, temp 0.
- `RESULTADO.md` tem a tabela A vs B, a comparação com 2026-08, e o veredito
  (PROPOSTA **ou** ARQUIVADO) com os números.
- Traces JSONL em `redesign/rlm/traces/`.
- **Nenhuma mudança de produção; nenhuma decisão de adoção** (é do Humano).

## Verificação independente

- **Quem:** Humano (lê as respostas cruas + o veredito) ou fallback.
- **O quê:** que os 2 braços usaram o MESMO modelo/endpoint/temp; que as fabricações foram
  contadas certo (spot-check de F1/F4 nos traces); que o custo de token é
  `prompt_eval_count + eval_count`, não estimado.
- **Como:** reler `RESULTADO.md` contra os traces JSONL.
- **Resultado:** no LOG.

## Rollback

Não destrutivo: `git checkout -- redesign/rlm` / `rm -rf redesign/rlm/traces`.

## Registro

- `STATUS.md`: P5-01 → "Feito"; o veredito (PROPOSTA/ARQUIVADO) em 1 linha. **Fase 5 fecha aqui.**
- `LOG.md`: a tabela A vs B, a comparação com 2026-08, o veredito, `HEAD`.
