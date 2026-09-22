# Proposta de consolidacao — num_ctx 16814

_Gerada por redesign/grafo/flows/consolidacao.py em 2026-09-21. NAO e' canon. O Humano decide (P-8). Se aprovada, vira ENTRADA NOVA em MEMORIAS (append-only), nunca edicao. Passou no portao mecanico de (371)._

**Refs:** (111), (128), (131), (132), (133), (135), (139), (152), (164), (175), (234), (312), (368), (382)

Estado consolidado do tema num_ctx 16814: bug de mitigação revertido, conserto validado via Modelfile customizado e presença_penalty ajustado com veredito parcial em PROJETO.md.
(111) reverte violação de barreira 64k; (128) valida código HTTP com request_overrides vazio; (131) define prompt exato e caminho direto ou hermes-agent; (132) adiciona protocolo de introspecção não testado antes.
(133) fecha bug ao vivo sem fallback automático; (135) confirma conserto com Modelfile embutido funcionando; (139) determina qual ramo é real na produção; (152) valida hipótese presence_penalty zerado.
(164) condensa PROJETO.md e veredito nos itens restantes; (175) analisa padrão grep para num_ctx|hermes; (234) especifica runners com num_ctx explícito; (312) remove scripts Hermes-era mortos.
(368) triagem de consolidações e status HTTP 529; (382) confirma parâmetros válidos com penalty 1.5 e num_ctx 65536.
Nenhum título sugere obsolescência direta, mas (312) indica remoção de scripts antigos como `verificar_num_ctx.py`, sugerindo redundância desses arquivos na camada fria.
