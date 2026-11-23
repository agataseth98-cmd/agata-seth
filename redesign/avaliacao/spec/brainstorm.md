# Brainstorm — medição experimental de rota na avaliação

## Usuários

- O Humano inicia uma rodada experimental explícita para comparar custo por tarefa correta antes de decidir sobre cache ou roteamento.
- O avaliador consulta metadados já recebidos pelo cliente e distingue ausência de zero.

## Estado que muda

- Uma rodada de `avaliar.py` poderá gravar tempos e metadados no registro JSONL existente.
- Não há captura contínua de chamadas do gateway nem alteração de rota em produção.

## Erros e concorrência

- Só se medem chamadas que a avaliação já faria; nenhuma chamada ou retry adicional.
- Falhas permanecem no resultado existente da avaliação. Não há writer/buffer contínuo nem efeito sobre resposta de produção.
- Se o adapter não expõe primeiro chunk ou metadado, registra-se `null` com motivo.

## Migração

- Campos experimentais serão opcionais; rodadas antigas não recebem backfill.
- Dados ficam no diretório de execuções da avaliação e seguem o ciclo de remoção já documentado. Não se introduz retenção nova.

## Observabilidade

- Tempos no cliente: início, primeiro chunk recebido e término, em relógio monotônico.
- Modelo/rota, headers e usage entram somente se já expostos; cache/prefill e custo desconhecidos ficam nulos com motivo.
- GPU/RAM, se medidos, são fotografias agregadas antes/depois e apenas em rodada local.
- Overhead é comparado entre rodadas equivalentes ligadas/desligadas, contra limiar fixado previamente.
- Resultado e falha preservam o registro da avaliação; correção/retrabalho fica separado e custo por tarefa usa pareamento correto com baseline explícito.

## Reversão

- Desativar a opção impede medições futuras; a avaliação existente continua disponível.
- Reverter a extensão deixa registros antigos legíveis; remoção de dados segue a reversão já definida para `<dados>/avaliacao/`.
- Nenhuma mudança em `seth_gateway.py`, cache ou roteador.

## Sucesso

- A rodada informa custo conhecido e latência observada por tarefa correta pareada com baseline, sem inferir valores ausentes.
- A medição não amplia chamadas e não atua fora da avaliação explicitamente iniciada.
- Overhead é reportado e comparado ao limiar prévio, sem transformar o limiar em política permanente.
