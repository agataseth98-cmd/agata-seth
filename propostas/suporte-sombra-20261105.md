# Proposta `suporte-sombra-20261105`: revisão de suporte mecânica em sombra (nova versão, lote 6)

**O que é, em português comum:** a Seth responde com números. Hoje ninguém confere se um número afirmado pela resposta aparece no que a ferramenta ou o sistema trouxeram. Esta proposta acrescenta, só em sombra, essa conferência para a resposta anterior. Ela não altera a resposta, não bloqueia nada e não chama modelo.

**O que muda:** `redesign/router/sombra_nova_versao.py` ganha um bloco que, a cada pedido, olha a resposta anterior da Seth e grava no registro da sombra:
- `estado`: `sem_fontes` (o turno não teve ferramenta), `ok` ou `revisar`;
- quantas ferramentas o turno teve;
- quantos números a resposta afirmou que não aparecem em nenhuma fonte;
- até 5 desses números.

Nunca grava o texto da resposta nem o do pedido. Liga só com `SETH_SOMBRA_NOVA_VERSAO=1`, que continua desligado por padrão.

**Limites, para ninguém tomar isto por verificação de verdade:**
- Confere só números, não afirmações. Um fato sem número passa.
- Não confere citações `(N)` de entradas do canon: essas vêm da hidratação, que não está no histórico do turno. Por isso a checagem de citações não entra aqui.
- Sem revisor de outra família. A revisão semântica de suporte (`revisao_suporte.revisar`) segue sem ligação ao gateway; isso fica para uma proposta própria, com custo de inferência aprovado.

**Medido:** o selftest do módulo passa (6 de 6), inclusive o caso que confere: um número que a resposta afirma e que não estava na ferramenta aparece na amostra, e o texto da resposta não aparece no registro.

**Não medido:** o efeito em tráfego real. A sombra só vira dado depois que o Humano ligar `SETH_SOMBRA_NOVA_VERSAO=1`.

**Como reverter:** remover o bloco novo de `observar()`. Não há estado persistente novo; o registro é o mesmo `sombra.jsonl`.
