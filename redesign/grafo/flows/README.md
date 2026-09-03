# redesign/grafo/flows/ — flows do grafo (reusam estado.py / durabilidade.py)

## `consolidacao.py` — consolidação noturna (P6-03, Fase 6)

`orientar → juntar → consolidar → podar`. Saída **só em `propostas/`** — nunca canon
(mesma política da `agata-consolidacao.service`).

- **`orientar`** — para cada tema, `consulta.py` (P6-02) devolve as refs `(NNN)` **e o
  título real** de cada entrada. Sem modelo.
- **`juntar`** — monta o `diff_proposto` com as refs rastreáveis por tema. Sem modelo.
- **`consolidar`** — o modelo (via `:20127`) redige **uma proposta por tema** a partir dos
  **títulos reais** (não dos números — senão fabrica, a falha de MEMÓRIAS (138)). Escreve
  `propostas/consolidacao-<tema>-<data>.md` com o cabeçalho "NÃO é canon; o Humano decide
  (P-8); se aprovada vira ENTRADA NOVA append-only". WAL (`durabilidade.py`) + idempotência.
- **`podar`** — propõe ARQUIVAR entradas redundantes (≥3 por tema). **Nada é apagado**
  (Regra 4) — `aprovado: false`, o Humano decide.
- **Sem portão de commit automático.** `commit_sha` fica vazio.

### Verificação (aceite P6-03) — num clone

- 4 nós ponta a ponta; `git status` do clone = **só `propostas/consolidacao-*.md`**
  (nada em MEMÓRIAS/REGRAS/PROJETO). ✅
- Cada proposta cita refs `(NNN)` + o cabeçalho de quarentena. ✅
- Feeding os **títulos reais** ao modelo → a proposta é fiel (ex.: "(154) corrige (151)-(153),
  a hipótese do presence_penalty não se sustenta" — bate com o título real de (154)).
  Com só os números, o modelo **fabricava** ("host-rating", "dias de prisão"). ✅
- `podar` = proposta de arquivamento, nada apagado. ✅

Uso: `consolidacao.py --repo <dir> [--temas "a;b;c"]`. Timer (Fase 7) rodaria isto e o
`git add propostas/` ficaria pro Humano.
