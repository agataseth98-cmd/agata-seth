# Telemetria experimental de rota — spec V1 (`telemetria-spec-v1-20261117`)

Classe: Comportamento (spec de avaliação; sem implementação nesta proposta).

Base: `origin/main` (`ac08bf4fcd13f6f519cef27cc8774089a932f4e6`). O diff contém somente `redesign/avaliacao/spec/spec.md`, `brainstorm.md` e `decision.md`. Este registro fica fora do diff assinado.

## Resumo

Documentar uma extensão de medição experimental, restrita a rodadas de avaliação explicitamente iniciadas. A spec descreve tempos e metadados disponíveis no cliente, valores ausentes como `null`, limites de chamadas, medições agregadas de recursos locais, comparação de overhead e uso do ciclo de dados já existente. Os critérios da futura implementação são informativos nesta proposta; `acceptance.json` e testes executáveis entram junto com o código numa proposta posterior.

## Limites

- Não inclui código, testes, instrumentação contínua do gateway, mudanças de roteamento, chamadas adicionais ou nova política de retenção.
- Não escolhe cache ou rota de produção; a medição não prova economia nem custo por tarefa correta.
- Parâmetros como o limiar de overhead pertencem ao experimento futuro, não viram política permanente.
- O comportamento da implementação futura não foi medido.

## Apetite

Máximo de 3 arquivos no diff e 2 horas de agente.

## Testes medidos

- `python3 redesign/sdd_flow/anchor.py . redesign/avaliacao` → `ANCHOR: OK`.
- `PYTEST=/home/orusoua/.cache/uv/archive-v0/0obnOoJtclHllQl_/bin/pytest bash scripts/ci_sdd_local.sh` → `CI LOCAL: TUDO OK`, 88/88 passos OK; o binário informou `pytest 9.2.0`.

## Não medido

- Implementação futura e seus critérios funcionais.
- Precisão dos tempos/metadados dos adapters, custo reportado, coleta agregada GPU/RAM e overhead experimental.
- Resultado econômico por tarefa correta.

## Reversão

Reverter o diff desta proposta remove os três documentos alterados/adicionados. Não há código ou dados de medição criados por este lote.

## Comando futuro de assinatura

Depois que a proposta estiver no `main` e o Humano tiver lido o diff:

`bash scripts/aprovar.sh telemetria-spec-v1-20261117`
