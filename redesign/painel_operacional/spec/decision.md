# Decisão

DECISAO: aceita

Decidido pelo Humano em 07/11/2026.

Escopo decidido pelo Humano (relatado pelo coordenador em 07/11/2026): "quero deixar perfeito hj, com o painel já unificado e funcional". Isso fixa o escopo da versão.

Respostas do Humano às perguntas abertas (07/11/2026):
- A busca da documentação (wiki) entra na busca única de Conhecimento. A busca única cobre Alexandria, Acervo e Wiki do `/index.html`.
- A barra lateral, o cabeçalho e o chip LOCAL ficam fora das sete seções, como casca registrada. A casca também inclui breadcrumb, busca "Buscar neste mapa…", nota e rodapé, diálogo de evidência (`evidence-dialog`), como lista a tabela de mapeamento da spec.

Pergunta sem resposta nesta decisão:
- A verificação no navegador é medida por quem, e quando? Fica aberta. O critério 35 de `spec.md` registra só o que for medido; o que não foi medido fica como não medido.

Pedido do Humano em 07/11/2026: aba "Memória compartilhada" dentro da seção Conselho, para acompanhar as entradas do cache do Conselho (leitura de `redesign/router/cache_conselho.py`). O Humano é membro do Conselho e a aba é só de leitura: não grava, não anota e não aprova nada. Isso abre uma exceção à regra "nenhuma rota nova de API" (`GET /api/conselho/memoria`; os sete critérios novos estão no fim de `spec/acceptance.json`). Entra no mesmo lote e na mesma assinatura do painel unificado.
