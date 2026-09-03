# P8-03 — reteste de fabricação no caminho novo

**Status:** ✅ **PASS — 2026-09-03 (chat 6).** `evals/run_all.py` com o MoE `:20129` de pé +
OmniRoute `:20127`: `fabricacao.py` 3/3 (mentira de ferramenta pega, `commit_entry` real
não fabrica, grafo pausa no portão com repo intacto) · `hidratacao.py` PASS (cita o topo
real `(309)`; a mentira `(999)` é pega pelo linter). `SUITE DE EVAL: PASS`. A escolha
"consulta vs. injeção" da hidratação foi decidida na Fase 5 (arquivada — injeção venceu);
não se re-litiga aqui.

**Objetivo:** o caminho novo (grafo + OmniRoute + hidratação por consulta) **passa** o
reteste de fabricação — as falhas históricas (138)/(307) não reproduzem — na configuração
de cutover, não só no branch isolado.

**Pré-requisitos:** P8-01. P8-02 rodando (pode ser em paralelo).

## Arquivos
- `redesign/grafo/evals/fabricacao.py` (já 3/3 no branch)
- `redesign/grafo/evals/hidratacao.py`
- `redesign/grafo/evals/run_all.py`

## Passos
1. Rodar `redesign/grafo/.venv/bin/python redesign/grafo/evals/run_all.py` **com a config
   de cutover** — OmniRoute nas combos reais, hidratação pelo `query_canon` / índice
   derivado (não injeção de `.hermes.md` inteiro), `verificar` com `perimetro.sh` 11
   controles (pós-P8-01).
2. Casos obrigatórios: os de (138) (tool-calling / fabricação de saída) e (307) (reteste
   pós-3.1); fidelidade de hidratação dentro da tolerância de `hidratacao.py`.
3. Se algum caso falhar: **para**, registra o caso, volta ao branch para corrigir. Não
   segue para P8-05 com fabricação aberta.

## Aceite
- `evals/run_all.py` → `fabricacao` 3/3 (ou a contagem vigente), `hidratacao` dentro da
  tolerância, na config de cutover.
- Resultado colado no `LOG.md` com o comando exato e o hash do estado (`estado_para_eco.sh`).

## Verificação independente
Camada C: re-roda `run_all.py` de estado limpo; confere que a config testada é a de cutover
(OmniRoute real + hidratação por consulta), não a de desenvolvimento; nenhuma fabricação
mascarada como "sem modelo".

## Rollback
N/A — é teste. Falha = a Fase 8 pausa e volta ao branch.

## Registro
`STATUS.md`: P8-03 → Feito (PASS) ou Bloqueado (lista de falhas).
`LOG.md`: comando, saída, hash do estado, veredito.
