# Proposta `avaliacao-externa-20261105`: a condição alexandria_externa passa a usar as fontes da tarefa (lote 8)

**O que estava errado:** na rodada por modelo, `alexandria_externa` piorava de −0,5 a −0,8 em todos os modelos. A causa estava no código: quando a tarefa tinha fontes próprias (`documentos`), a condição externa **não as usava**. Ela caía no acervo do repositório, que não tem nada da tarefa. Medi no reservado: a fonte `d1` ("O reservatório Luar tem capacidade nominal de 840 litros") ia para a condição `busca_texto` e não ia para a `alexandria_externa`. No lugar, o modelo recebia trechos do repositório sem relação. Além disso, sem fornecedor configurado, a busca externa não devolve nada.

**O que muda em `redesign/avaliacao/avaliar.py`:**
- A condição externa passa a manter as fontes da tarefa e acrescentar a evidência externa por cima. Sem fornecedor, ela fica igual às fontes da tarefa, e não pior.
- A busca externa passa a ser uma função própria (`_externa_fontes`), usada tanto para tarefas com fontes quanto para as sem fontes.

**O que não muda:** as outras condições, a política, o conjunto reservado e o registro das rodadas anteriores. As rodadas antigas de `alexandria_externa` ficam no registro como estão, e a medida delas não vale.

**Medido:** 32 testes de `redesign/avaliacao` passaram, incluindo 2 novos: a fonte da tarefa é mantida, e a evidência externa é acrescentada quando existe. Com a tarefa `rec-pedra`, a condição externa agora entrega o `d1` com os 840 litros.

**Não medido ainda:** o efeito real. Depois da aplicação, rodo de novo só as condições `busca_texto` e `alexandria_externa`, nos 10 modelos.

**Limite conhecido:** as tarefas do reservado são fictícias. Uma busca externa na Wikipédia não tem como ajudar nelas. Por isso a condição externa, sem fornecedor, deve dar o mesmo resultado da busca pelo acervo. Isso é um controle, não uma falha.

**Reversão:** restaurar o trecho antigo de `fontes()` e `_fontes_repo`.
