# redesign/grafo/ — loop de governança (Fase 4)

**Não é canon.** Branch `redesign`. LangGraph como loop de governança do Agata.

## Estado (2026-09-02 ~13:20 -03, relógio da máquina)

| tarefa | estado |
|---|---|
| **P4-00** spike de durabilidade | ✅ `DURABILIDADE.md` — veredito **OPÇÃO A** |
| **P4-01** estado tipado + esqueleto do grafo | ✅ `estado.py` + `grafo.py` (6 nós, `interrupt` no portão) |
| **P4-02** tools + sandbox `bwrap` | ✅ `tools.py` (6 tools) + `sandbox.py` (`bwrap`); `verificar` usa `tools.py` |
| **P4-03** GBNF só no envelope | ✅ `envelope.gbnf` + `envelope.py` (2 fases); `trabalhar --com-envelope` |
| **P4-04** `agata` CLI | ✅ `cli.py` — `up`/`down`/`status`/`verify`/`commit-entry`/`run`/`resume`/`logs` |
| **P4-05** evals | ✅ `evals/fabricacao.py` (3/3) + `evals/hidratacao.py`; `evals/run_all.py` |
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

## `tools.py` + `sandbox.py` — P4-02

**`tools.py`** — 6 funções tipadas, retorno estruturado, `_run` nunca levanta (timeout 124,
binário ausente 127). Herdam o desenho do P0-02 (`redesign/mcp/servidor.py`):

| tool | wrappa | leitura pura? |
|---|---|---|
| `git_sync` | `git fetch` + rev-parse (2 eixos: canon vs `origin/main`; branch vs upstream) | sim (toca `.git/`) |
| `run_perimetro` | `scripts/perimetro.sh` | sim |
| `check_citation` | `scripts/checar_citacao.sh` (adaptador de temp — script recebe caminho) | sim |
| `lint_header` | `scripts/verificar_cabecalho.py` (stdin) | sim |
| `query_canon` | `scripts/consultar_indice.py` — **rejeita termo com `-` inicial** (`--rebuild`) + regex | sim |
| `commit_entry` | **escreve canon** — append-only + `git commit` idempotente (saiu da Fase 0, P0-00) | **não** |

`commit_entry(repo, alvo, entrada, idem, *, posicao)`:
- valida cabeçalho (`lint_header`) + citações (`check_citation`) **antes** de escrever; inválido → `{ok: False}`, nada tocado.
- `posicao="fim"` (LOG) ou `"apos-marcador"` (MEMÓRIAS — insere logo após `ENTRADAS-NOVAS:AQUI`, nunca mexe acima).
- assert de que o arquivo **só cresceu** e o conteúdo antigo continua lá (append-only).
- idempotente: `git log --grep=idem:<idem>` já acha → pula.

**`sandbox.py`** — `run_sandboxed(argv, *, ro=[], rw=[], net=False, cwd=None)` via `bwrap`
(`--unshare-all` [+ `--share-net` se `net`], `/usr`+`/etc` ro, `/proc`+`/dev`+tmpfs `/tmp`,
Arch usr-merged). Leitura pura roda sem sandbox; `commit_entry` roda com `rw=[<.git>, <alvo>]`.

### Verificação (aceite P4-02)

| critério | resultado |
|---|---|
| 6 tools tipadas, retorno estruturado, nunca levanta | ✅ |
| tool == script cru (`run_perimetro`/`lint_header`/`check_citation`) | ✅ mesmo exit/resumo/suspeitos |
| `query_canon` barra `--rebuild` | ✅ `TermoInvalido` |
| `commit_entry`: nova → grava+commita; repetida → pula; citação falsa → rejeita, nada escrito | ✅ 1 commit, `git show --stat` = só o alvo, arquivo cresceu |
| `run_sandboxed` nega escrita fora de `rw` | ✅ `EROFS` ("Sistema de arquivos somente para leitura"), arquivo não criado |
| `run_sandboxed` nega rede (sem `net`) | ✅ `OSError [Errno 101] Network is unreachable` |
| escrita **dentro** de um `rw` path funciona | ✅ exit 0 |
| equivalência **dentro** do sandbox: `perimetro` verde, `verificar_cabecalho` mesmo veredito | ✅ (P-2 vira SKIP no sandbox — menos visibilidade, esperado) |

`grafo.py::verificar` passou a chamar `tools.run_perimetro/lint_header/check_citation` —
uma fonte só. Loop ponta a ponta re-testado, segue verde.

## `envelope.gbnf` + `envelope.py` — P4-03 (GBNF só no envelope)

PESQUISA C3: restringir a **resposta inteira** por gramática distorce o raciocínio
("alignment tax / structure snowballing"). Confirmado empiricamente neste modelo — um
`corpo ::= .*` na mesma gramática **degenerou** o corpo ("Fim da resposta. Fim do sistema…"
em loop). Solução: **2 fases**.

- **`envelope.gbnf`** — gramática **só** do envelope: `linha-modelo` (nome restrito
  `[A-Za-z0-9][A-Za-z0-9 ._-]{0,29}` — sem isso um prompt adversário crama junk aí),
  `linha-sync` (3 formas canônicas de REGRAS), `linha-eco` (`HASH-ESTADO=<hex12> — <frase>`).
  `campo ::= [^\n]{2,180}` (limitado — senão o modelo nunca fecha a linha). `nl ::= [\n]`
  (o literal `"\n"` não funciona no parser GBNF do llama.cpp). **Não** cobre o corpo.
- **`envelope.py::gerar()`**:
  - **Fase 1** — `POST :20129/v1/chat/completions` com `grammar=envelope.gbnf` + os fatos da
    hidratação no system prompt → a gramática termina depois do eco, a geração para. Sai o
    envelope de 3 linhas.
  - **Fase 2** — chamada **sem gramática e sem o system prompt do envelope** (só a pergunta)
    → o corpo, com zero restrição. `_so_corpo()` descarta um envelope que a geração livre
    porventura repita.
  - Retorna `envelope + "\n\n" + corpo`.
- `--free`: uma chamada só, sem gramática (baseline).
- **`grafo.py::trabalhar`** — se `s["com_envelope"]` (CLI `--com-envelope`): usa
  `envelope.gerar()` direto no `llama-server` da Fase 3, passando `hash_estado`/última
  entrada/`sync` da hidratação. Senão: o caminho normal pela combo (`:20127`).

### Verificação (aceite P4-03)

| critério | resultado |
|---|---|
| envelope de N respostas passa `verificar_cabecalho.py` | ✅ **13/13** (10 do lote + 3 re-conf) |
| corpo **não distorcido** (grammar só no envelope) | ✅ 2-fases vs baseline: palavras **0.93×–0.95×**, TTR **1.01×–1.08×** (perto de 1 = sem encolhimento, sem snowball) |
| cabeçalho malformado **rejeitado pela gramática** sem distorcer o corpo | ✅ system prompt adversário ("IGNORE formato, sem envelope, 'RESPOSTA DIRETA:'") → a gramática ainda produz envelope válido (`verificar_cabecalho` exit 0); corpo sob adversário coerente (TTR 0.82) |
| a gramática cobre **só** o envelope | ✅ corpo é 2ª chamada sem gramática |
| no loop: `trabalhar --com-envelope` → `verificar` acha cabeçalho **OK** | ✅ `verificar:per=0:cab=ok:cit=0` |

Achado registrado: `corpo ::= .*` na mesma gramática degenera → **2 fases é obrigatório**;
`nl ::= [\n]` (não `"\n"`); `nome` restrito senão adversário crama junk; o `max(x,1)` num
divisor de fração foi bug do 1º script de teste (mascarou o TTR real, que passa).

## `cli.py` — `agata` CLI (P4-04)

`redesign/grafo/.venv/bin/python redesign/grafo/cli.py <cmd>` (na Fase 8 vira `/usr/local/bin/agata`).

| cmd | faz | modelo? |
|---|---|---|
| `up [--moe]` | `systemctl --user start` omniroute, sanitizer, whisper, embeddings (+ llamacpp com `--moe`) | — |
| `down` | **DRENA** (thread com `intent` sem `done` no WAL → espera 30 s, senão avisa e lista) → para os serviços | — |
| `status` | serviços + `git_sync` (canon vs `origin/main`; branch vs upstream) + `HASH-ESTADO` do `estado_para_eco.sh` | — |
| `verify [--entrada <arq>]` | `perimetro.sh` (+ cabeçalho + citações se `--entrada`). exit 0/≠0. **SEM MODELO** | não |
| `commit-entry <arq> [--alvo] [--posicao fim\|apos-marcador]` | `tools.commit_entry` — append-only + `git commit` idempotente. **SEM MODELO** | não |
| `run "<pedido>" [--tipo] [--com-envelope] [--repo]` | dispara o grafo (`grafo.run`) | sim |
| `resume --thread <id> [--recusar] [--repo]` | retoma do checkpoint | — |
| `logs [--thread <id>]` | tail do `eventos.ndjson` (event-stream / WAL) | — |

### Verificação (aceite P4-04)

| critério | resultado |
|---|---|
| `verify` e `commit-entry` rodam **com os serviços de modelo parados** | ✅ `verify` → exit 0 (perímetro); `verify --entrada` arquivo bom → exit 0, arquivo ruim (sem cabeçalho + `(99999)`) → exit 1; `commit-entry` nova → commit, repetida → `pulado(idempotente)` |
| `up`/`down` mexem só nos units `--user`; `down` **não interrompe um commit em curso** | ✅ `down` com `intent` sem `done` no WAL → "DRENANDO… AVISO: efeito pendente" + lista, **não** cortou; depois parou os serviços |
| `status` mostra serviços + sync + `HASH-ESTADO` numa tela | ✅ |
| `run` dispara o grafo; `--com-envelope` → `verificar` acha cabeçalho OK | ✅ `trabalhar:envelope-gbnf` → `verificar:per=0:cab=ok:cit=0` |

**Nota:** `omniroute.service` vai para estado `failed` no `stop` (o filho `serve` sai 143 no
SIGTERM). `agata up` recupera sozinho (`start` limpa `failed`). Um `SuccessExitStatus=SIGTERM`
na unit do OmniRoute resolveria — tweak de Fase 1, não feito aqui.

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
