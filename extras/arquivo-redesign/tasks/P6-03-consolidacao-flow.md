# P6-03 — consolidação noturna como flow do grafo (orientar → juntar → consolidar → podar)

**Status:** ✅ **FEITO — 2026-09-02 ~19:23 (relógio da máquina). FASE 6 FECHADA.**
`redesign/grafo/flows/consolidacao.py` — `orientar → juntar → consolidar → podar`
(reusa `estado.py`/`durabilidade.py`/`consulta.py`). Testado num clone: 4 nós ponta a
ponta; `git status` = **só `propostas/consolidacao-*.md`** (nada em canon); cada proposta
cita refs `(NNN)` + cabeçalho de quarentena; `podar` propõe arquivar, **nada apagado**.
**Achado:** alimentar o modelo com os **títulos reais** das refs (não só os números)
evita a fabricação de (138). `flows/README.md`.

**Objetivo:** a consolidação noturna vira um flow do grafo da Fase 4 — quatro nós — que
escreve **proposta** em `propostas/`, nunca canon direto. **Fecha a Fase 6.**

**Pré-requisitos:** P6-02 FEITO. Fase 4 (grafo) FECHADA. A `agata-consolidacao.service`
existente (systemd --user, já escreve proposta) é a referência de política.

**Arquivos:** `redesign/grafo/flows/consolidacao.py` (novo) · `redesign/tasks/P6-03-*.md`.

Classe de risco: runtime + escreve em `propostas/` (dentro do repo, não canon). Auto-revisão.

---

## Contexto

`agata-consolidacao.service` (unit já no sistema): "consolidação noturna (memória →
proposta em propostas/, nunca canon direto)". A Fase 6 a re-desenha como flow do grafo,
mantendo a mesma política.

## Passos

1. **`consolidacao.py`** — um `StateGraph` (reusa `estado.py`/`durabilidade.py`) com:
   - `orientar` — lê o vault (`consulta.py`, P6-02) + o topo do canon; monta a lista de
     temas candidatos a consolidar (entradas relacionadas, duplicação, pontas soltas). Sem modelo.
   - `juntar` — para cada tema, reúne as refs rastreáveis. Sem modelo.
   - `consolidar` — o modelo (via `:20127`) redige um **rascunho de proposta** por tema —
     nunca uma entrada de MEMÓRIAS, sempre um `.diff`/`.md` em `propostas/`. Cita as refs.
   - `podar` — marca o que virou redundante/obsoleto (proposta de arquivamento, não apagar
     — Regra 4).
   - Sem portão automático de commit: a saída é arquivo em `propostas/`, o Humano decide
     (P-8 / quarentena).
2. **Teste:** rodar num clone; sai 1+ arquivo em `propostas/<nome>.md` com refs checáveis;
   nada escrito em `MEMÓRIAS.md`/`REGRAS.md`/`PROJETO.md`.
3. **Não** agendar no boot (Fase 7). Documentar como o timer entraria.

## Aceite

- `consolidacao.py` roda os 4 nós num clone; saída só em `propostas/`.
- Nada tocado em canon (`git status` do clone: só `propostas/`).
- Cada proposta cita refs rastreáveis (`(NNN)` + arquivo).
- **Fase 6 FECHADA** (aceite conjunto: MCP consulta o vault · recuperação índice-primeiro
  devolve refs · zero vector DB · consolidação é flow).

## Verificação independente

- **Quem:** fallback ou Humano. **O quê:** que nada entrou em canon; que as propostas são
  rastreáveis; que a consolidação não "decide" (só propõe). **Como:** `git status` do clone;
  abrir 2 propostas e conferir as refs.
- **Resultado:** no LOG.

## Rollback

`rm -rf` do clone de teste; `git checkout -- redesign/grafo/flows`. Não destrutivo.

## Registro

- `STATUS.md`: P6-03 → "Feito"; **Fase 6 FECHADA**.
- `LOG.md`: o run dos 4 nós, as propostas geradas, `HEAD`.
