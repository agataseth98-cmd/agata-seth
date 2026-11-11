# Spec primeiro: P1 a P4 (entrevista, gate de sincronia, revisor contra a spec, classes de tarefa), 11/11/2026

Proposta P-8 sobre `origin/main` `182310d0`. Adoção decidida pelo Humano em 11/11/2026, 19:20 ("ok a todas"; cache do Conselho, entrada (495)). Spec Kit e Conductor não entram: não serão instalados.

## Ordem de aplicação (leia antes de assinar)

O diff toca `.agents/skills/agata-processo-lote/SKILL.md`, o mesmo arquivo de `processo-agil-11-11`. Ele foi gerado sobre `origin/main` mais `processo-agil-11-11` (o blob desse arquivo nessa base é `24fc9e2d`, que aparece no cabeçalho `index` do diff). Ordem: assinar e aplicar `processo-agil-11-11` primeiro; depois esta. Aplicar esta antes quebra a correspondência do cabeçalho `index`.

## Classe

Comportamento: muda script de CI, gate e snapshot de drift de `redesign/nova_versao`. Os textos de processo (skills e agentes) entram no mesmo lote e são revisados como comportamento.

## O que muda

- **P1, entrevista antes da spec.** `.agents/skills/agata-time-inovacao/SKILL.md`: passo 2 novo. Antes da spec de ideia nova de comportamento, o orquestrador faz até 5 perguntas de múltipla escolha ao Humano (AskUserQuestion quando houver); as respostas vão para `decision.md`. `.claude/agents/agata-inov-arquiteto.md`: lê `decision.md` antes de escrever e para se não houver respostas. Fonte: code.claude.com/docs/en/best-practices, "Interview me until you could write the spec". Conferida pelo orquestrador no relatório de 11/11; não reaberta nesta rodada.
- **P2, gate de sincronia das specs.** `scripts/gate_spec_sync.py` (novo, com `--selftest`). Para cada `redesign/*/spec`: os critérios do `spec.md` têm de ser o mesmo conjunto dos `criterion` do `acceptance.json`; e um `criterion-drift.md` commitado não pode ser mais antigo que o `spec.md`. Ligado em `scripts/ci_sdd_local.sh` e em `.github/workflows/sdd.yml`, antes dos ciclos SDD, porque o ciclo regenera o drift dentro da pasta da spec. `sdd.yml` ganha `fetch-depth: 0`, para haver datas de commit. Sem histórico (clone raso) ou fora de git, o gate falha.
- **P2, snapshot de nova_versao.** `redesign/nova_versao/spec/criterion-drift.md` e `evidence.json`, regenerados pelo mesmo ciclo que o CI roda. O drift passa de 6 linhas para 12, todas com status pass.
- **P3, revisor contra a spec.** `.claude/agents/agata-revisor.md`: modo com três entradas (`spec.md`, `acceptance.json`, diff), sem a conversa. Veredito por critério: conforme, desvio ou não medido. Nunca diz "aprovado".
- **P4, três classes de tarefa.** `.agents/skills/agata-processo-lote/SKILL.md`: bloco "Classe da tarefa (P4, 11/11)" antes das regras e do passo 1. Operacional (sem spec, só registro); comportamento (spec e acceptance); canon (spec e P-8). Lugar: o início do processo, antes da worktree (passo 1). É a primeira decisão do coordenador, e o registro da classe fica no próprio lote.

## Problema medido

Medido no `origin/main` `182310d0` e na árvore desta proposta:

- **P1:** `git grep` no `HEAD` por "entrevist", "AskUserQuestion" e "interview me" em `.agents/` e `.claude/`: nenhum resultado. O arquiteto não tem regra de entrada nem menção a `decision.md`.
- **P3:** `git grep` por "contra a spec" em `.claude/agents/agata-revisor.md` no `HEAD`: nenhum resultado. O revisor só tinha o modo de revisão de diff ou proposta.
- **P4:** `git grep` por "classe da tarefa" no `SKILL.md` de processo: nenhum resultado. Não há classificação de tarefa no processo.
- **P2, sincronia (12 specs):** `alexandria` tem 26 linhas de critério no `spec.md` (25 distintas) e 31 entradas no `acceptance.json` (30 distintas). As 5 do `acceptance.json` que faltam no `spec.md` estão listadas em `EXCECOES`. Os outros 11 componentes batem exatamente.
- **P2, drift (12 specs):** só `nova_versao` tem `criterion-drift.md` commitado: 6 linhas, commit `8e11de22` de 04/11 20:35. O `spec.md` dele é de `f78c3c83`, 09/11 15:22. Os outros 11 não têm snapshot: o item de drift não roda neles.
- **Gate antes da correção (medido, mesma árvore sem o drift regenerado):** `AVISO alexandria: dívida conhecida: 5 critério(s)` e `FALHA nova_versao: criterion-drift.md mais antigo que spec.md`. Ou seja, sem as duas correções o CI ficaria vermelho hoje.

## Correção mínima incluída e o que ficou de fora

- **nova_versao:** drift regenerado, dentro do diff. `criterion-drift.md` não é `spec.md`, então não exige proposta própria.
- **alexandria: não corrigido nesta proposta.** A correção é acrescentar as 5 linhas ao `spec.md`. Isso exige proposta própria, assinada à parte (processo-lote, regra 1). Tirar as 5 do `acceptance.json` perderia teste, então não foi feito. O gate trata as 5 como dívida conhecida: `EXCECOES` em `scripts/gate_spec_sync.py`, com AVISO e não FALHA. Quando a proposta da alexandria entrar, o gate avisa "exceção obsoleta" e a entrada sai.
- **11 specs sem `criterion-drift.md`:** o item de drift não roda nelas. Não é falha. Gerar snapshot para todas é outra decisão do Humano.

## Como medir (proposto; o Humano decide o prazo)

- **P2:** FALHA e AVISO do gate em cada run do `sdd` (passo "Gate de sincronia das specs"). Meta: zero FALHA. A dívida da alexandria cai a zero quando a proposta dela entrar.
- **P1:** por ideia nova de comportamento: número de perguntas (até 5), respostas gravadas em `decision.md` (sim ou não), e mudanças em `spec.md` depois da primeira versão. Hoje: não medido; nenhuma ideia passou por essa etapa.
- **P3:** desvios que o revisor achar antes da proposta, contra desvios achados depois da aplicação. Hoje: não medido.
- **P4:** lotes com a linha "Classe:" preenchida, sobre o total de lotes; reclassificações registradas. Hoje: não medido.
- **Prazo sugerido:** 14 dias, até 25/11/2026, junto com a medição R2 do processo ágil. Manter ou reverter é decisão do Humano, com este `.md`.

## Testes medidos

- Selftest do gate: `python3 -I scripts/gate_spec_sync.py --selftest` deu `SELFTEST GATE: 12/12 OK` (cenários: sincronizado, critério só no acceptance, exceção, drift antigo, drift novo, spec alterada sem commit, drift regenerado sem commit, drift nunca commitado, exceção obsoleta, repositório sem spec, clone raso, fora de git).
- Gate sobre a árvore desta proposta, com o drift regenerado: `GATE SPEC: 12 componente(s), 1 aviso(s), 0 falha(s)`. O aviso é o da alexandria.
- CI local com o diff aplicado numa worktree própria: `uv run --offline --with pytest bash scripts/ci_sdd_local.sh`, com pytest 9.2.0 (confirmado com `pytest --version` dentro do uv). Saída final: `CI LOCAL: TUDO OK`, 35 passos OK, código 0. Rodada final, sobre a última edição de código (o selftest do gate passou 12 de 12 e o passo de gate ficou OK antes e depois dos ciclos).
- Lint de skill (`qualidade_llm.py`, passo "skills sem problema de lint"): OK. As skills editadas ficam dentro dos limites.
- Reindexação (`python3 -I ferramentas/ferramentas.py reindexar`): nenhum arquivo gerado mudou (`git status` vazio em `ferramentas/`).
- Cópia limpa (export de `origin/main`, sem histórico): `git apply` do diff de `processo-agil-11-11`, depois `git apply --check` e `git apply` deste diff, sem erro. Os 9 arquivos de código ficaram idênticos aos da worktree (`cmp`).

## Não medido

- Se o gate pega desvio real: testado só com 12 cenários sintéticos.
- Efeito das três classes e da entrevista: nenhum lote passou por elas ainda.
- Se `AskUserQuestion` está disponível em todas as sessões do orquestrador: não verificado.
- Se o `sdd` passa no GitHub: depende do run do `headSha` deste PR, que só existe depois do push.
- Falhas de suíte fora do CI local (por exemplo `test_sdd_painel`, do unittest do painel): não rodadas nesta proposta; o CI local não as inclui.

## Apetite (R2, declarado)

- Arquivos de código: 9 (duas skills, dois agentes, um script novo, `scripts/ci_sdd_local.sh`, `.github/workflows/sdd.yml`, `criterion-drift.md` e `evidence.json` de nova_versao). Limite declarado: 9.
- Horas de agente: limite declarado 2 h. Medido com `date`: início 19:29, fim da proposta 19:42, cerca de 13 min de relógio. Não passou do limite.

## Lista de conferência de pronto (preenchida pelo agente)

- [x] CI local `CI LOCAL: TUDO OK` com o diff aplicado (saída final colada acima).
- [ ] Run verde no GitHub no `headSha` do PR: preenchido depois do push, com `gh run list --branch proposta/spec-primeiro-11-11 --json headSha` e `gh pr checks`.
- [x] Captura de tela: não se aplica (sem interface).
- [x] Sem emoji no `.md`, no diff e na entrada de MEMÓRIAS. O corpo do PR termina com a linha de atribuição exigida, que tem um emoji; ela não entra no registro.
- [x] `.md` com testes medidos, o que não foi medido e a reversão.
- [x] Nenhuma falha pré-existente sem dono e data no CI local: o CI local não tem falha.
- [x] Entrada de MEMÓRIAS sem citação `caminho:número`.

## Reversão

Proposta própria que aplica ao contrário o `propostas/aplicadas/spec-primeiro-11-11.diff` (`git apply -R`), assinada à parte. Nessa reversão, o drift de nova_versao volta ao conteúdo anterior (commit `8e11de22`); a restauração de arquivo gerado depende de ordem do Humano. Entradas de MEMÓRIAS são append-only: reverter o registro é entrada nova.

## Registro fora do diff

`propostas/spec-primeiro-11-11.diff`, este `.md`, a entrada (990) em `MEMÓRIAS.md` e a linha em `ONDE_ESTAMOS.md` entram no PR de proposta, sem assinatura. Registro não tem quarentena (`propostas/README.md`, "SEM quarentena"). Os arquivos que o ciclo do CI gera em `redesign/sdd_flow/spec/` ficaram sem commit, fora do diff.

## Assinatura

Depois de `processo-agil-11-11` assinada e aplicada, e do merge deste PR, o Humano roda:

```
bash scripts/aprovar.sh spec-primeiro-11-11 "<motivo>"
```

Verificação depois da assinatura, no checkout vivo, com `git rev-parse HEAD` igual a `origin/main`:

```
bash scripts/p8_verificar.sh spec-primeiro-11-11
```
