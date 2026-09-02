# redesign/grafo/ — loop de governança (Fase 4)

**Não é canon.** Branch `redesign`. LangGraph como loop de governança do Agata.

## Estado (2026-09-02 ~13:20 -03, relógio da máquina)

| tarefa | estado |
|---|---|
| **P4-00** spike de durabilidade | ✅ `DURABILIDADE.md` — veredito **OPÇÃO A** |
| **P4-01** estado tipado + esqueleto do grafo | ✅ `estado.py` + `grafo.py` (6 nós, `interrupt` no portão) |
| P4-02 tools + sandbox `bwrap` | ⏳ |
| P4-03 GBNF só no envelope | ⏳ |
| P4-04 `agata` CLI | ⏳ |
| P4-05 evals | ⏳ |
| P4-06 adapter dsh dormente | ⏳ |

## venv

`redesign/grafo/.venv` (gitignorado, `redesign/**/.venv/`). `langgraph 1.2.11`,
`langgraph-checkpoint-sqlite 3.1.1`, `langchain-core 1.6.1`.

## `durabilidade.py` — padrão do P4-00 (veredito A)

- **`WAL`** — `<dir_estado>/eventos.ndjson` append-only, `os.fsync` por linha. `intent`
  antes de cada efeito externo, `done` depois.
- **`idem_key(thread_id, node, passo)`** — `sha1[:16]`. Todo efeito checa a chave antes.
- **`efeito_idempotente(wal, thread, node, passo, ja_feito, aplicar)`** — roda `aplicar()`
  no máximo 1× para a chave.
- **`WAL.replay(thread)`** — reconstrói a decisão do WAL **deduplicando por chave** (o WAL
  acumula `done` repetido no crash+resume — append-only correto).

O checkpointer LangGraph (`SqliteSaver`, `~/.cache/agata/grafo/checkpoints.sqlite`) roda
por cima. Ordem em todo nó com efeito: `wal(intent) → checar chave → efeito → wal(done) → return`.

## `estado.py` — `Estado` (TypedDict)

`thread_id · entrada · tipo · repo · hidratacao · rota · trabalho · trabalho_erro ·
verificacao · diff_proposto · portao · commit_sha · ultimo_efeito_confirmado`
\+ `eventos: Annotated[list, add]` e `decisao_log: Annotated[list, add]` (append-only, reducer).

## `grafo.py` — os 6 nós

```
hidratar → rotear → trabalhar → verificar → portao → registrar_e_commitar
```

| nó | o que faz | modelo? |
|---|---|---|
| `hidratar` | `scripts/estado_para_eco.sh` no repo alvo → `hash_estado`, `head`, `sync`, topo de MEMÓRIAS | não |
| `rotear` | escolhe a combo do OmniRoute (`conselho` se `tipo=conselho`; `cheap` se curto/verificação; senão `auto`) | não |
| `trabalhar` | `POST :20127/v1/chat/completions` (proxy sanitizador) com a combo. **Degrada limpo** → `trabalho="(sem modelo)"` se o proxy cair | sim (opcional) |
| `verificar` | `perimetro.sh` + `verificar_cabecalho.py` (stdin) + `checar_citacao.sh` (adaptador de temp, como P0-02). **ESPINHA — roda com o modelo desligado** | não |
| `portao` | `interrupt()` — as 3 perguntas (reversível / alcance / silêncio) + o `diff_proposto`. Retoma com `Command(resume={"aprovado": bool})` | não |
| `registrar_e_commitar` | se aprovado: `efeito_idempotente` → 1 linha em `redesign/grafo/loop.log` + `git commit` (idem key no corpo). Se recusado: pula | não |

### Uso

```fish
redesign/grafo/.venv/bin/python redesign/grafo/grafo.py run "<pedido>" --repo <dir> [--thread <id>] [--tipo trabalho|conselho|verificacao]
redesign/grafo/.venv/bin/python redesign/grafo/grafo.py resume --thread <id> --repo <dir> [--recusar]
```

## Verificação (aceite P4-01) — testado num clone `git clone --local`

| critério | resultado |
|---|---|
| 6 nós ponta a ponta num clone | ✅ `run` → 5 nós + pausa no portão; `resume` → 6º nó + commit no clone (`51a7fd7`) |
| portão **pausa** (`interrupt`) e **retoma** (`Command(resume)`) sem perder estado | ✅ `pausado_no_portao: true` → `resume --aprovar` → `portao:aprovado` |
| `verificar` roda **com o modelo desligado** | ✅ `AGATA_PROXY` morto → `trabalhar:sem_modelo` → `verificar` roda igual, loop chega ao portão |
| matar o processo no meio e retomar **não duplica o commit** (herda P4-00) | ✅ `GRAFO_KILL_AFTER_COMMIT=1` no `resume` → `rc 137` → `resume` de novo → `registrar_e_commitar:pulado`; **1** commit `loop: registro de t-p401-kill`, **1** ocorrência da idem key em `loop.log`; WAL = `intent,[SIGKILL],intent,done` |

Gancho de teste: `GRAFO_KILL_AFTER_COMMIT=1` (`os.kill(pid,9)` logo após o `git commit`).

## O que a P4-01 deixa para as próximas

- `rotear` é heurística de string — smarter routing depois (P4-02+ pode dar contexto).
- `verificar` reporta mas **não decide** — o `portao` sempre pausa; auto-aprovar
  verificação limpa é decisão de doutrina (não feita).
- `trabalhar` chama o modelo direto — a versão com tools/sandbox é a **P4-02**.
- `registrar_e_commitar` escreve num `loop.log` de teste — o `commit_entry` real (que
  escreve MEMÓRIAS/LOG do canon) é a **P4-02** (herdou da Fase 0 via P0-00).

## Rollback (P4-00 + P4-01)

```fish
rm -rf redesign/grafo/.venv ~/.cache/agata/grafo ~/.cache/agata/grafo-spike ~/.cache/agata/grafo-clone-teste
git checkout -- redesign/grafo
```
