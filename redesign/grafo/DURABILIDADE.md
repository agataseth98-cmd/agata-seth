# DURABILIDADE.md — veredito do spike P4-00

**Não é canon.** Branch `redesign`, Fase 4. Escrito 2026-09-02 ~13:10 -03 (relógio da
máquina). Fecha o GATE da Fase 4 (E2 da AUDITORIA-01: "checkpoint ≠ execução durável").

## Veredito: **OPÇÃO A** — `SqliteSaver` + WAL mínimo próprio

O loop da Fase 4 (P4-01+) usa:

1. **Checkpointer LangGraph = `SqliteSaver`** (`langgraph-checkpoint-sqlite` 3.1.1) —
   snapshot de estado por nó, retomável por `thread_id`.
2. **WAL próprio append-only** — `eventos.ndjson`, um registro `intent` **antes** de cada
   efeito externo e `done` **depois**, `os.fsync` em cada linha (write-ahead de verdade).
3. **Idempotency key por `(thread_id, node, passo)`** (`sha1(...)[:16]`) — todo efeito
   externo checa a chave antes de agir: já feito → **pula**. A chave também vai no corpo da
   mensagem de commit (`idem:<chave>`) e na linha do `efeitos.log`.

**Não** é preciso camada de durabilidade dedicada (Temporal, Diagrid). O `SqliteSaver` +
WAL + idempotência fecha os 4 critérios do E2 nos 3 pontos de morte. Temporal **não** foi
pré-comprometido (a Fase 4 fica livre para adicionar depois se a operação mostrar necessidade).

## Prova — matriz 3 pontos de morte × 4 critérios (3 execuções, determinístico)

`spike_durabilidade.py matrix` — grafo-brinquedo `hidratar → trabalhar → efeito_externo →
registrar_e_commitar`, `SIGKILL` (`os.kill(pid, 9)`) no ponto, `resume` com o mesmo `thread_id`.

| ponto de morte | kill | resume | (a) sem dup | (b) idempotente/pendente | (c) estado explica último efeito | (d) WAL reconstrói decisão |
|---|---|---|---|---|---|---|
| `apos_wal_antes_efeito` | `-9` | ok | OK | OK (refaz 1×) | OK | OK |
| `apos_efeito_antes_wal_done` | `-9` | ok | OK | OK (pula) | OK | OK |
| `apos_wal_done_antes_checkpoint` | `-9` | ok | OK | OK (pula) | OK | OK |

Critérios (do E2):
- **(a)** `efeitos.log` tem cada idempotency key 1×; `git log --grep=<key>` do repo-clone ≤ 1×.
- **(b)** morreu antes do efeito → `resume` refaz (1×); morreu depois → `resume` **pula**.
- **(c)** `state["ultimo_efeito_confirmado"]` no `resume` == última chave `done` no WAL.
- **(d)** `replay(eventos.ndjson)` puro (sem o checkpointer), **aplicando idempotência**,
  reconstrói `decisao = [k1]` e o mundo real bate (`efeitos.log` com k1 1×).

## Evidência (independente) do último run

```
kills.log:   1788365171.64 SIGKILL @ apos_wal_done_antes_checkpoint pid=575244
eventos.ndjson (kill 3): intent(k1), done(k1), [SIGKILL], intent(k1), done(k1)   <- 4 registros
git log repo-clone:      31a6e41 efeito passo=1  +  edc71c3 raiz                  <- 1 commit de efeito
efeitos.log:             passo=1 chave=86ef2f91b0f420aa :: ...                    <- 1 linha
```

## Achado — o que a P4-01 herda

- **O WAL acumula `done` repetido entre crash e resume** (kill 3: dois `done` para a mesma
  chave). Isso é append-only **correto** — o log registra a reconfirmação. **O replay tem
  que ser idempotency-aware:** dedup por chave ao reconstruir "quais efeitos aconteceram".
  `spike_durabilidade.py::replay()` faz isso (`wal_done_raw` vs `decisao_reconstruida`).
- **Ordem obrigatória em todo nó com efeito colateral:** `wal(intent)` → checar
  idempotency key → efeito → `wal(done)` → `return` (aí o LangGraph faz o checkpoint).
- O `thread_id` é o id do pedido; `SqliteSaver.from_conn_string(<db>)` é context-manager
  (`__enter__`/`__exit__`), não esquecer de fechar.
- `git commit --allow-empty` no repo real: a idempotency key no corpo é o que o
  `commit_entry` (P4-02) vai usar para não commitar 2× a mesma entrada.

## Rollback do spike

```fish
rm -rf redesign/grafo/.venv ~/.cache/agata/grafo-spike
```
(O `spike_durabilidade.py` e este doc ficam no branch como registro.)
