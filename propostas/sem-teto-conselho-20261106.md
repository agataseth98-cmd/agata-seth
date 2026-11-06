# Proposta — remover o teto de tamanho do pedido ao Conselho Remoto

**Nome para assinatura:** `sem-teto-conselho-20261106`
**Pedido do Humano (06/11/2026):** "remova o limite dos pedidos do conselho".

## Mudança
- `scripts/conselho_remoto.py`: removida a constante `TETO_CHARS_PEDIDO = 60_000` e a checagem que recusava pedidos acima dela, antes do envio.
- O teto de saída (`TETO_TOKENS_SAIDA = 4000`, vira `max_tokens`) continua. Não é o mesmo limite.

## O que muda na prática
- Pedidos de qualquer tamanho passam para o OmniRoute. O custo e o tempo de resposta sobem com o tamanho; o provedor pode recusar pedidos muito grandes com erro próprio, que o script já trata como falha de provedor.
- A checagem de conteúdo privado (`checar_conteudo_privado`) continua valendo: material de `memoria/missoes` continua recusado antes de qualquer rede.

## Evidência
- O diff aplica limpo no `origin/main`.
- O arquivo compila (`py_compile`).
- Não rodei chamada real ao Conselho com pedido grande. Não medido: custo e aceitação de pedidos acima de 60 mil caracteres pelo provedor.

## Assinatura
`bash scripts/aprovar.sh sem-teto-conselho-20261106`
