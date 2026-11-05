# Proposta `avaliacao-prazo-20261105`: a rodada bate no prazo e não vira "concluída" (avaliação, lote 7)

**O que aconteceu:** a rodada do reservado `teste2` com as 10 rotas locais (`r-20261105-161356-d7f91b`) tinha prazo de 900 s. Eram 3.482 itens, a cerca de 6,4 s por chamada em série na GPU. Só 190 itens rodaram. Os outros 3.292 ficaram "não rodados" por prazo. Mesmo assim o estado saiu **"concluída"**, e a comparação saiu com 3 pares por rota: um número que não diz nada.

**O que muda em `redesign/avaliacao/avaliar.py`:**
1. O prazo da rodada passa a considerar o tamanho: `max(timeout×10, 900, 30 × nº de itens)`. Para 3.482 itens, são cerca de 29 h de teto, e o teto só corta de verdade se a rodada travar.
2. Se algum item bater no prazo, o estado vira **"incompleta"**, não "concluída". O veredito de comparação continua sendo calculado, mas a rodada fica marcada.

**O que não muda:** o conjunto, as condições, a política (margem 0,10, latência 60 s, teto R$ 0), a rota da família que escreveu as tarefas e o registro comum. A rodada anterior fica no registro, como está. Não é apagada.

**Ressalva que o Humano precisa saber:** os 190 itens que rodaram já olharam para as 60 tarefas do `teste2`. A rodada nova, completa, vai usar as mesmas tarefas. Não há como desfazer essa primeira olhada. O veredito deve sair só da rodada completa.

**Medido:** pytest de `redesign/avaliacao` e `redesign/conexoes` passou (35 testes). Não rodei a avaliação completa de novo; isso leva horas e depende da sua assinatura.

**Reversão:** voltar as duas linhas para o cálculo antigo.
