# Processo ágil de lote (R1, R3, R5, R2) — proposta de 11/11/2026

Proposta P-8 sobre `origin/main` `1d69754a`. Assinatura do Humano, uma vez, depois do merge deste PR de proposta.

## O que muda

Uma seção nova, "Fluxo e pronto (ágil, 11/11)", em `.agents/skills/agata-processo-lote/SKILL.md` (14 linhas, nenhuma removida). O diff `propostas/processo-agil-11-11.diff` toca só esse arquivo.

- **R1 Limite de trabalho aberto:** no máximo 2 propostas abertas, sem aplicação, por componente. Antes de abrir a 3ª, aplicar, superar ou fechar uma. Base: Kanban Guide, edição 2025 (v2025.5, https://kanbanguides.org/english/; verificado nesta rodada: a página mostra essa edição e fala de limite de WIP). A Lei de Little (L = λ·W) não aparece no guia pelo nome; entra aqui como teoria de filas.
- **R3 Definição de pronto do lote:** checklist que o relatório do agente preenche. Base: Scrum Guide 2020, Definition of Done (citado da fonte conhecida, não buscado nesta rodada).
- **R5 Retrospectiva de 3 linhas:** ao fechar cada lote, nota no cache do Conselho com gargalo com número, regra que mudou e o que saiu do WIP. Base: Manifesto Ágil, princípio 12 (citado da fonte conhecida, não buscado nesta rodada).
- **R2 Apetite (em medição até 25/11/2026):** cada proposta declara o máximo de arquivos e de horas de agente, e registra quando passa dele. Nada é cortado automaticamente nesse período.

## Problema medido

Medição feita com `git` e `gh` na base `c1a190c6` (antes da PR #964); os números de fila são da base `1d69754a`.

- **Propostas sem assinatura:** 10 na base `c1a190c6`, com idade de 4,1 a 5,4 dias (de 06/11 09:35 a 07/11 15:31). Na base `1d69754a` são 11, porque a `chat-lote4-09-11` entrou. Na base `98dd5839` são 10: a `origem-preservada-07-11` foi arquivada como superada pela PR #965. Relatório: 10. Reproduzido na base anterior.
- **Mediana proposta até aplicação:** relatório 6,5 h. Medido em `origin/main` como a adição do `.diff` em `propostas/` até a mudança para `propostas/aplicadas/`: mediana 0,20 h em 432 pares; desde 01/10, 335 pares, mediana 0,17 h, p90 1,6 h, máximo 110 h, com 7 acima de 24 h. Medido por PR, com título pareado: 5 pares, mediana 2,8 h, máximo 50 h. **A mediana de 6,5 h não reproduziu com nenhuma das duas medidas.** A cauda reproduziu: 50 h em `chat-protege-conversas-09-11` (PR #962 em 09/11, PR #963 em 11/11).
- **MEMÓRIAS nos commits:** relatório 60%. Medido em commits sem merge de `origin/main`: 767 de 1669 (46%) alteram uma entrada DIÁRIO; desde 12/10, 291 de 810 (36%). Desde 12/10, 714 de 810 (88%) alteram o arquivo em alguma linha, incluindo o bloco de máquina. **Nenhuma medida dá 60%.** O relatório não diz qual conta usou.
- **E-2 (emoji):** relatório diz "esquecida até o lote 4". Medido: a skill `agata-processo-lote` não tinha regra de emoji antes desta proposta (grep sem resultado). **Quando foi esquecida: não medido** aqui; a data de introdução da regra não foi levantada.

## Como medir (14 dias, até 25/11/2026)

- **R1:** contar, por componente, as propostas em `propostas/*.diff` sem `APROVADO-` correspondente. Meta: no máximo 2 por componente. Medir a mediana e o p90 de proposta até aplicação pelo mesmo método acima.
- **R3:** do total de lotes no período, quantos têm o checklist preenchido no relatório do agente.
- **R5:** contar as notas de retrospectiva no cache do Conselho (`cache_conselho.py ler`), uma por lote fechado.
- **R2:** quantas propostas declaram apetite, e quantas registram que passaram dele.

Critério para manter ou reverter: **proposto, o Humano decide** em 25/11/2026. Proposta deste autor: manter se nenhum componente passar de 2 propostas abertas e as propostas sem assinatura caírem para até 5; senão, reverter R1 e rever a medição.

## Apetite desta proposta (R2, declarado)

- Arquivos de código: 1 (`.agents/skills/agata-processo-lote/SKILL.md`).
- Horas de agente: 1 h (estimativa). Medido com `date`: 18:56 a 19:06, cerca de 10 min de relógio para esta rodada. **Não passou do apetite.**

## Testes medidos

- `bash scripts/ci_sdd_local.sh` com `PYTEST` do cache do uv (pytest 9.2.0): saída `CI LOCAL: TUDO OK`, código de saída 0.
- `python3 redesign/painel_operacional/qualidade_llm.py`: a skill `agata-processo-lote` tem `linhas: 168`, `problemas: []`, `avisos: []`.
- `python3 -I ferramentas/ferramentas.py reindexar`: nenhum arquivo gerado mudou (só a skill entrou no índice).
- Base do diff: o blob da skill em `origin/main` é `1443ccc`, igual ao hash `index` do cabeçalho do diff. Por isso o `git apply` sobre a base é exato. `git apply --check -R` passou na árvore com a mudança.
- Uma checagem de `git apply --cached --check` contra um índice temporário de `origin/main` não rodou (bloqueada pelo classificador de comandos); a conferência acima a substitui.

## Não medido

- O efeito das regras sobre o fluxo: só começa a ser medido no próximo lote.
- Quando o E-2 foi esquecido (ver acima).
- Falha `test_sdd_painel` da suíte unittest do painel, conhecida desde a aplicação de 11/11 (MEMÓRIAS 986). Não é do CI local e esta proposta não a toca. **Dono e data: não registrados.** Pendência para o Humano.
- Interface: não há tela nesta mudança, então a captura de tela de R3 não se aplica.

## Checklist de pronto deste lote (R3)

- [x] CI local `TUDO OK` (saída colada acima).
- [ ] Run verde no GitHub no `headSha` do PR: preenchido depois do push, com `gh run list --branch proposta/processo-agil-11-11 --json headSha`.
- [x] Captura de tela: não se aplica (sem interface).
- [x] Sem emoji: conferido no texto desta proposta, no diff e nas entradas de MEMÓRIAS.
- [x] `.md` com testes medidos, não medido e reversão.
- [ ] Falha pré-existente com dono e data: não registrados para `test_sdd_painel`; pendente com o Humano.
- [x] Texto da entrada de MEMÓRIAS sem `caminho:número` (P-19 só avisa; conferido).

## Reversão

Proposta própria que aplica `propostas/aplicadas/processo-agil-11-11.diff` ao contrário (`git apply -R`), assinada à parte, porque a skill está no caminho protegido. Entradas de MEMÓRIAS são append-only: a reversão do registro é entrada nova.

## Registro fora do diff

`ONDE_ESTAMOS.md` (tabela "Lotes em andamento"), a entrada (988) desta proposta e a correção (989) entram neste PR de proposta, sem assinatura. Não entram no diff assinado: `scripts/perimetro/p08_quarentena.sh` não protege `ONDE_ESTAMOS.md` e `MEMÓRIAS.md`.

## Assinatura

Depois do merge deste PR, o Humano roda:

```
bash scripts/aprovar.sh processo-agil-11-11 "<motivo>"
```

Verificação depois da assinatura, no checkout vivo, com `git rev-parse HEAD` igual a `origin/main`:

```
bash scripts/p8_verificar.sh processo-agil-11-11
```
