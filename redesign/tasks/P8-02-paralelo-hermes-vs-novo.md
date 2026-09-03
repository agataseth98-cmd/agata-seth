# P8-02 — paralelo N dias: Hermes vs. grafo + OmniRoute

**Status:** 🟢 **ABERTO — 2026-09-03 (chat 6).** N = 7 dias + piso de amostragem. Harness
validado + **bateria sintética** (5 pares, marcados) cobriu o piso quase todo: ≥1 par por
tipo ✓, portão pausa ✓, zero fabricação ✓, **nenhuma divergência**. Fallback: parcial
(b2 landou no alvo do `conselho`; falta um em uso real). **Ainda aberto: os 7 dias de
calendário com pedidos reais.** Log: `redesign/grafo/paralelo.md`.

**Objetivo:** medir o caminho novo (grafo LangGraph + OmniRoute) contra o Hermes em uso
real por N dias, com número, antes de tirar o Hermes do loop (P8-05).

**Pré-requisitos:** P8-01. Fase 1 (OmniRoute) e Fase 4 (grafo) fechadas.

## O que roda em paralelo
- **Hermes** (produção, intocado) — segue sendo o caminho de fato.
- **Caminho novo** — `redesign/grafo/grafo.py run "<pedido>" --repo <dir>` → nós
  `hidratar→rotear→trabalhar→verificar→portao→registrar_e_commitar`; `trabalhar` fala no
  proxy `:20127` (OmniRoute sanitizado). `verificar` é a espinha (roda sem modelo).

## Passos
1. **Roteiro de comparação** — para cada pedido real que o Humano fizer ao Hermes no
   período, rodar o mesmo pelo `grafo.py` (thread própria, `--repo` num clone para não
   commitar em `main`). Registrar por par: latência, custo (`omniroute cost`), o
   `diff_proposto`, veredito do `verificar`, e se o portão pausou onde devia.
2. **Planilha append-only** em `redesign/grafo/paralelo.md` (data · pedido · Hermes:
   resultado/tempo · novo: resultado/tempo/custo · observação).
3. **N e critério — decididos 2026-09-03 (chat 6):** **N = 7 dias**, com piso de
   amostragem (≥1 par por `--tipo`; ≥1 fallback real; ≥1 pausa de portão; zero fabricação).
   Estende só até cobrir o piso; regressão → para e volta ao branch. Critério de aprovação:
   nenhuma regressão de fidelidade + custo ≤ Hermes + portão/fallback OK + zero fabricação.
   Detalhe e log dos pares: `redesign/grafo/paralelo.md`.

## Aceite
- `redesign/grafo/paralelo.md` com ≥ N dias de pares registrados.
- Decisão do Humano registrada: "caminho novo empatou/superou" → segue P8-05; senão, lista
  do que corrigir antes.
- Nenhum commit em `main` pelo `grafo.py` no período (rodou sempre em clone).

## Verificação independente
2º olhar confere: a planilha tem pares reais (não sintéticos não marcados); o `grafo.py`
rodou contra clone, `git -C <main> log` sem commits do loop no período.

## Rollback
N/A — nada mudou no sistema. Se o caminho novo falhar feio, a Fase 8 pausa aqui e volta ao
branch para corrigir.

## Registro
`STATUS.md`: P8-02 → Feito; a decisão do Humano (segue / lista de correções).
`LOG.md`: resumo dos N dias, os números, a decisão.
