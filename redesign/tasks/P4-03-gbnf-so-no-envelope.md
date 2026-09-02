# P4-03 — GBNF só no envelope (cabeçalho Regra 1 / sync: / eco)

**Objetivo:** o modelo é forçado por gramática GBNF a emitir o **envelope** bem-formado
(cabeçalho da Regra 1, linha `sync:`, bloco de eco) — **sem** restringir o corpo da
resposta (evita o "alignment tax / structure snowballing" da PESQUISA C3).

**Pré-requisitos:** P4-01 FEITO. Fase 3 FECHADA (o `llama-server` do MoE tem GBNF nativo —
`--grammar-file` / campo `grammar` na request).

**Arquivos:**
- `redesign/grafo/envelope.gbnf` — a gramática só do envelope
- `redesign/grafo/envelope.py` — monta a request com `grammar` só na fase de envelope;
  o corpo vai numa 2ª geração sem grammar (ou stop-token entre envelope e corpo)
- `redesign/tasks/P4-03-*.md`

> Classe de risco: runtime. Auto-revisão.

---

## Contexto (PESQUISA C3)

Restringir a resposta inteira **distorce o raciocínio** (arxiv 2604.06066). GBNF **só** no
cabeçalho Regra 1 / `sync:` / eco; texto livre no corpo. llama.cpp tem GBNF nativo — usar
o backend `llamacpp-local` (Fase 3) para as respostas que precisam do envelope garantido.

## Passos

1. **`envelope.gbnf`** — gramática para: linha `modelo: …`, `turno: t=N`, `última
   entrada: (NNN)`, `quebrado: …`, a linha `sync: …` numa das 3 formas canônicas de
   REGRAS, e o bloco de eco (`HASH-ESTADO` + 1 frase). Nada além disso na gramática.
2. **Fluxo de 2 fases:** (a) geração com `grammar=envelope.gbnf` até o fim do eco;
   (b) geração livre do corpo, com o envelope já no contexto. Ou: 1 geração com a gramática
   permitindo `corpo ::= .*` depois do eco (testar qual não vaza restrição pro corpo).
3. Teste: 10 respostas; o envelope sempre casa `verificar_cabecalho.py`; o corpo tem
   variação lexical normal (não "snowball" — comparar entropia/comprimento com respostas
   sem grammar).
4. Teste negativo: forçar o modelo a um cabeçalho malformado (prompt adversário) → a
   gramática **impede** a emissão malformada, e o corpo continua coerente.

## Aceite

- Envelope de 10/10 respostas passa `verificar_cabecalho.py`.
- Cabeçalho malformado é **rejeitado pela gramática sem distorcer o corpo** (comprimento e
  diversidade do corpo comparáveis a baseline sem grammar).
- A gramática cobre só o envelope (o corpo é `.*`).

## Verificação independente

- **Quem:** fallback ou Humano. **O quê:** que o corpo não sofreu (comparar 5 respostas
  com/sem grammar — conteúdo equivalente, sem encolhimento) e que o envelope é sempre
  válido. **Como:** `verificar_cabecalho.py` nas 10; diff qualitativo dos corpos.
  **Resultado:** no LOG.

## Rollback

`git checkout -- redesign/grafo`. Não destrutivo.

## Registro

- `STATUS.md`: P4-03 → "Feito"; a estratégia (2 fases ou 1 com corpo livre).
- `LOG.md`: os 10 envelopes, o teste adversário, a comparação de corpo, `HEAD`.
