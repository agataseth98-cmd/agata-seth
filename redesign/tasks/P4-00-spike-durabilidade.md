# P4-00 — spike de durabilidade (matar-e-retomar) — GATE da Fase 4

**Objetivo:** decidir a estratégia de durabilidade do loop de governança **antes** de
comprometer a arquitetura — provando, com um grafo-brinquedo que tem os nós reais do
desenho, o comportamento matar-processo-e-retomar. Sai um veredito escrito.

**Status:** ✅ **FEITO — 2026-09-02 ~13:10 (relógio da máquina). VEREDITO: OPÇÃO A.**
`langgraph 1.2.11` + `langgraph-checkpoint-sqlite 3.1.1` em venv isolado. `spike_durabilidade.py`
(grafo-brinquedo + harness `SIGKILL`). Matriz **3 pontos de morte × 4 critérios do E2 = PASS**
em 3 execuções (determinístico). **`SqliteSaver` + WAL próprio (`eventos.ndjson` fsync,
intent-antes/done-depois) + idempotency key `(thread,node,passo)`** fecha os 4 critérios —
**não** precisa Temporal / camada dedicada. Achado: o WAL acumula `done` repetido no
crash+resume (append-only correto) → replay tem que ser idempotency-aware. Veredito completo:
`redesign/grafo/DURABILIDADE.md`.

**Pré-requisitos:** Fase 4 recebeu o "vai" (2026-09-02). Independente das outras `P4-*`.

**Arquivos que a tarefa toca:**
- venv isolado `redesign/grafo/.venv` (gitignorado — `redesign/**/.venv/`, conferido)
- `redesign/grafo/spike_durabilidade.py` (novo) — o grafo-brinquedo + o harness matar/retomar
- `redesign/grafo/DURABILIDADE.md` (novo) — **o veredito** (alimenta P4-01)
- scratch **fora do repo**: `~/.cache/agata/grafo-spike/` (repo-clone descartável, event-logs)
- `redesign/tasks/P4-00-*.md`

> **Classe de risco: instala-pacote.** `langgraph` + checkpointer num venv isolado, `rm -rf`
> reversível. Revisão de plano por 2º par de olhos antes (auto-revisão serve — fallback não
> é gate). Sem `sudo`, sem canon, sem rede além do PyPI.

---

## Contexto (E2 da AUDITORIA-01 / ROADMAP "Correções pós-Fase 0")

O checkpointer do LangGraph é **save point de snapshot**, não log de eventos. Append-only
real é via reducers (`Annotated[list, operator.add]`), não nativo. O padrão emergente 2026
para durabilidade de produção é uma **camada externa** (Temporal, Diagrid). A Fase 4 previa
"checkpointer append-only estilo dsh" como decisão de desenho — **premissa não validada**.
Este spike valida ou derruba. **Não pré-comprometer Temporal** — o spike decide entre:
- (A) *checkpointer LangGraph (`SqliteSaver`) + camada WAL mínima própria* — o mínimo que passa;
- (B) *camada de durabilidade dedicada* — se (A) não fechar os 4 critérios.

---

## Passos

### 1. **INSTALA SOFTWARE** — venv + LangGraph

```fish
cd $HOME/agata
python3 -m venv redesign/grafo/.venv
redesign/grafo/.venv/bin/pip install --upgrade pip
redesign/grafo/.venv/bin/pip install "langgraph" "langgraph-checkpoint-sqlite"
redesign/grafo/.venv/bin/python -c "import langgraph, langgraph.checkpoint.sqlite as s; print('langgraph', langgraph.__version__)"
```
Colar de volta: a versão. `git check-ignore redesign/grafo/.venv/x` tem que casar.

### 2. Grafo-brinquedo com os nós reais do desenho

`redesign/grafo/spike_durabilidade.py` — um `StateGraph` com o esqueleto da Fase 4:
`hidratar → trabalhar → efeito_externo → registrar_e_commitar` (rotear/verificar/portão
entram só na P4-01; o spike foca no trecho que tem efeito colateral).

- **Estado tipado** (`TypedDict`): `thread_id`, `passo`, `eventos: Annotated[list, operator.add]`
  (o event-stream append-only via reducer), `ultimo_efeito_confirmado`.
- **`efeito_externo`** = duas ações mensuráveis e idempotentes por chave:
  1. `append` de uma linha em `~/.cache/agata/grafo-spike/efeitos.log` com uma
     **idempotency key** `sha1(thread_id + node + passo)`; se a chave já está no arquivo,
     **não repete** (idempotente).
  2. `git commit` num **repo-clone descartável** (`~/.cache/agata/grafo-spike/repo/`) com a
     mesma chave no corpo da mensagem; se `git log --grep=<chave>` já acha, não commita.
- **WAL próprio:** antes de cada efeito, `append` de `{ts, thread, node, passo, chave,
  fase:"intent"}` em `eventos.ndjson` + `os.fsync`. Depois do efeito, outro registro
  `fase:"done"` + `fsync`. O checkpoint do LangGraph (`SqliteSaver`) roda por cima.
- `registrar_e_commitar` grava `ultimo_efeito_confirmado = chave` no estado.

### 3. Harness matar-e-retomar

`spike_durabilidade.py --run <thread_id> --kill-at <ponto>` onde `<ponto>` ∈:
- `apos_wal_antes_efeito` — morre entre o WAL `intent` e o efeito
- `apos_efeito_antes_wal_done` — morre entre o efeito e o WAL `done`
- `apos_wal_done_antes_checkpoint` — morre entre o WAL `done` e o checkpoint do LangGraph

O harness roda o grafo num subprocesso e manda `SIGKILL` no ponto (marcador em arquivo que
o nó toca + `os.kill(os.getpid(), 9)` guardado por env `SPIKE_KILL_AT`). Depois:
`spike_durabilidade.py --resume <thread_id>` — retoma do checkpoint com o **mesmo**
`thread_id`.

### 4. Rodar os 3 pontos de morte, provar os 4 critérios

Para cada ponto: `--run ... --kill-at X` → `--resume ...` → conferir:

| critério (E2) | como se prova no spike |
|---|---|
| (a) nenhum commit/escrita duplicado | `wc -l efeitos.log` == nº de passos; `git log --oneline` no repo-clone sem 2 commits com a mesma idempotency key |
| (b) efeito externo idempotente ou pendente | se morreu antes do efeito: o `resume` refaz (chave nova, 1 vez); se morreu depois: o `resume` **pula** (chave já no arquivo/log) |
| (c) estado retomado explica o último efeito confirmado | `state.ultimo_efeito_confirmado` no `resume` == a última chave com `fase:"done"` em `eventos.ndjson` |
| (d) log append-only reconstrói a decisão | um `replay(eventos.ndjson)` puro (sem o checkpointer) reproduz a sequência de efeitos e o estado final |

### 5. `DURABILIDADE.md` — o veredito

Escrever: qual opção venceu (A ou B), a tabela dos 3 pontos de morte × 4 critérios
(PASS/FALHA), os números (nº de eventos, nº de commits, tempo de resume), e **o que a
P4-01 deve usar** (ex.: "`SqliteSaver` + `eventos.ndjson` com fsync + idempotency key por
`(thread,node,passo)`; efeito externo sempre precedido de WAL `intent`").

---

## Aceite

- Os **3 pontos de morte** testados; para cada um, os **4 critérios (a/b/c/d)** = PASS.
- `redesign/grafo/DURABILIDADE.md` existe com o veredito (A ou B) e os números.
- `redesign/grafo/.venv` não aparece em `git status`.
- Scratch (`~/.cache/agata/grafo-spike/`) fora do repo.
- **Não** foi pré-comprometido Temporal nem nenhuma dependência pesada.

## Verificação independente

- **Quem:** fallback afinado ou Humano.
- **O quê:** que os 3 kills aconteceram de fato (SIGKILL, não shutdown limpo) e que o
  `resume` não duplicou efeito — relendo `eventos.ndjson` + `efeitos.log` + `git log` do
  repo-clone colados no LOG.
- **Como:** re-rodar 1 ponto de morte; `grep` das idempotency keys (cada uma 1× em
  `efeitos.log`, ≤1× em `git log`).
- **Resultado:** anotar no LOG (veredito, tabela, HEAD).

## Rollback

Não destrutivo:
```fish
rm -rf redesign/grafo/.venv ~/.cache/agata/grafo-spike
git checkout -- redesign/grafo redesign/tasks/P4-00-spike-durabilidade.md
```

## Registro

- `STATUS.md`: P4-00 → "Feito"; o veredito (A/B) em uma linha.
- `LOG.md`: a tabela 3×4, os números, o veredito, o que a P4-01 herda, `HEAD` no fim.
