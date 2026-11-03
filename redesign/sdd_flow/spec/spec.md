# Spec

## Jornadas críticas

1. Quem implementa escreve brainstorm, spec e critérios; o Humano assina uma vez; o ciclo confere tudo e a CI repete a conferência.
2. Um componente existente é ancorado: a spec lista seu código, e arquivo novo sem dono falha na CI.

## Contrato

- `runner.py <state> cycle <root> <manifest> --scope <pasta>...` executa, nesta ordem: gates de spec, âncora, critérios de aceite e drift por critério; para no primeiro que falha.
- `anchor.py <repo> <pasta>...` falha se faltar spec, seção obrigatória, dono de arquivo-fonte ou se a spec citar arquivo inexistente.
- `runner.py <state> proposal <nome> <worktree> <saida.diff> [--base origin/main] [--test alvo...]` gera o `.diff` único do lote e só o grava depois de aplicá-lo, conferi-lo (`git diff --check`) e testá-lo num checkout limpo da base; não assina, não abre PR.
- `github_flow.py` só inicia o handoff com `--state` de um ciclo que registrou a etapa `cycle`.
- Nenhum comando decide pelo Humano: `DECISAO: aceita` só entra em `decision.md` junto da assinatura P-8 que aplica este arquivo.

## Critérios de aceite

- [ ] gates de spec recusam seção não preenchida
- [ ] critério com comando de retorno diferente de zero vira defeito na evidência
- [ ] drift por critério falha quando falta evidência
- [ ] âncora recusa código sem dono na spec
- [ ] ciclo para no primeiro portão que falha
- [ ] proposta grava um diff único e não deixa worktree temporária
- [ ] proposta com diff vazio ou erro de espaço é recusada sem gravar
- [ ] handoff do GitHub exige ciclo registrado
- [ ] a verificação usa python -m pytest quando o binário não está no PATH

## Desenho e alternativas

Reaproveita as peças existentes (`spec_gate`, `acceptance_runner`, `criterion_drift`) e acrescenta só a âncora e o comando `cycle`. Alternativa descartada: grafo de specs com assembler de contexto (Spec Growth Engine); é grande demais para o retrofit e fica como evolução se a âncora provar valor. Alternativa descartada: spec única na raiz do repositório; não escala por componente.

## Implementação e testes

`anchor.py`, `cycle` e `proposal` em `runner.py`, `require_cycle` em `github_flow.py`, testes em `tests/test_anchor.py`, `tests/test_cycle.py` e `tests/test_proposal.py`, job `sdd` na CI. Os critérios acima estão ligados a testes em `acceptance.json`.

## Migração e reversão

Ancoragem gradual por componente, começando por `sdd_flow`. Reversão por revert do commit de aplicação.

## Riscos e dependências

A spec pode divergir do código em comportamento que nenhum teste cobre; a âncora só pega ownership, não semântica. Depende de pytest na CI (versão fixada no workflow).

## Código

- `runner.py`
- `anchor.py`
- `spec_gate.py`
- `acceptance_runner.py`
- `criterion_drift.py`
- `independent_review.py`
- `agent_dispatch.py`
- `github_flow.py`
- `tests/`
- `README.md`
