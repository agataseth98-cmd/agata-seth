# Decisão — medição experimental de rota na avaliação

- Direção da proposta: medir antes de escolher cache/roteamento e buscar menor custo total por tarefa correta.
- Arquitetura proposta para V1: medição apenas em rodada experimental explicitamente iniciada, reutilizando `avaliar.py`, o cliente de rota existente e `registro.py`; sem instrumentação contínua do gateway.
- Ausências são representadas por `null` e motivo; não se fazem chamadas extras nem se cria retenção nova. Recursos de rotas locais são agregados antes/depois da rodada.
- Pareamento correto e baseline são declarados para métricas por tarefa; retrabalho posterior fica separado.
- O limiar de overhead é fixado antes de cada experimento e não constitui decisão permanente de sistema.
- Os critérios enumerados na spec são orientação para implementação posterior, não critérios executáveis desta proposta. `acceptance.json` e testes entram junto com o código numa próxima proposta.
- A implementação permanece pendente de revisão/decisão; nenhum código foi alterado.

DECISAO: pendente
