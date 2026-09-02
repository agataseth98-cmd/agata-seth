# P4-01 — estado tipado + esqueleto do grafo (nós + portão com interrupt)

**Objetivo:** o `StateGraph` com os 6 nós do loop de governança, estado tipado, e
`interrupt` no portão — usando a estratégia de durabilidade que o **P4-00** decidiu.

**Pré-requisitos:** **P4-00 FEITO** (o `DURABILIDADE.md` diz qual checkpointer/WAL usar).

**Arquivos:**
- `redesign/grafo/estado.py` — o `TypedDict` do estado (com reducers append-only p/ o
  event-stream e o log de decisão)
- `redesign/grafo/grafo.py` — `hidratar → rotear → trabalhar → verificar → portão → registrar_e_commitar`
- `redesign/grafo/README.md`
- `redesign/tasks/P4-01-*.md`

> Classe de risco: runtime novo (não instala pacote — o venv é do P4-00). Auto-revisão.

---

## Passos

1. **`estado.py`** — campos mínimos: `entrada` (o pedido), `hidratacao` (cabeçalho Regra 1
   + `sync:` + eco, do `estado_para_eco.sh`), `rota` (combo/modelo escolhido), `trabalho`
   (resposta crua do modelo), `verificacao` (resultado do `perimetro.sh`/`verificar_cabecalho.py`/
   `checar_citacao.sh`), `portao` (as três perguntas — reversível? alcance? silêncio?),
   `eventos: Annotated[list, operator.add]`, `decisao_log: Annotated[list, operator.add]`.
2. **Nós** (cada um wrapper fino; a lógica pesada é tool da P4-02):
   - `hidratar` — roda `estado_para_eco.sh`, põe o `HASH-ESTADO` no estado. Sem modelo.
   - `rotear` — escolhe a combo do OmniRoute (`cheap`/`auto`/`conselho`) pela natureza do pedido.
   - `trabalhar` — chama o modelo via `:20127` (proxy sanitizador). Resposta crua no estado.
   - `verificar` — `perimetro.sh` + `verificar_cabecalho.py` (stdin) + `checar_citacao.sh`.
     **Roda com o modelo desligado** (é espinha determinística).
   - `portao` — `interrupt()` do LangGraph: pausa, apresenta as três perguntas + o diff
     proposto, espera o `Command(resume=...)` do Humano.
   - `registrar_e_commitar` — só na Fase 4 real escreve; aqui, atrás de flag, escreve a
     entrada de LOG e faz `git commit` (a `commit_entry` que saiu da Fase 0 — P0-00).
3. **Checkpointer/WAL** conforme `DURABILIDADE.md`. `thread_id` = id do pedido.
4. Teste ponta a ponta num **clone** do repo (`git clone . /tmp/agata-grafo-teste`): um
   pedido entra, roda os 6 nós, o portão pausa, `resume` retoma, o commit sai no clone.

## Aceite

- `grafo.py` roda os 6 nós ponta a ponta num clone.
- O `portao` **pausa** (`interrupt`) e **retoma** (`Command(resume=...)`) sem perder estado.
- `verificar` roda e passa/falha **com os modelos desligados**.
- Matar o processo no meio e retomar não duplica o commit (herda o P4-00).

## Verificação independente

- **Quem:** fallback ou Humano. **O quê:** o loop num clone; o portão pausa/retoma; o
  `verificar` não depende de modelo. **Como:** rodar `grafo.py` no clone, interromper no
  portão, `resume`. **Resultado:** no LOG.

## Rollback

`rm -rf` do clone de teste; `git checkout -- redesign/grafo`. Não destrutivo.

## Registro

- `STATUS.md`: P4-01 → "Feito"; os 6 nós + o que o portão apresenta.
- `LOG.md`: o run ponta a ponta, o teste de pausa/retoma, `HEAD`.
