# Proposta de consolidacao — num_ctx 16814

_Gerada por redesign/grafo/flows/consolidacao.py em 2026-09-23. NAO e' canon. O Humano decide (P-8). Se aprovada, vira ENTRADA NOVA em MEMORIAS (append-only), nunca edicao. Passou no portao mecanico de (371)._

**Refs:** (111), (128), (131), (132), (133), (135), (139), (152), (164), (175), (234), (312), (368), (382), (512)

O tema `num_ctx 16814` consolida correção de bug de contexto, validação de invocação e parâmetros, com status `[FECHADO]`/`[PARCIAL]`. (111) reverte violação de barreira 64k; (128) prova código/mapa HTTP; (131)-(132) investigam caminho direto vs `hermes-agent`; (133) fecha bug não no fallback automático.
(135) valida Modelfile customizado; (139) define ramos de produção real; (152) confirma hipótese `presence_penalty`. (164) condensa PROJETO.md e vereditos; (175) analisa padrão grep; (234) especifica runners e `num_ctx` explícito.
(312) remove scripts mortos; (368) triagem de consolidações vazia/HTTP 529; (382) valida parâmetros válidos; (512) consolidação automática aprovada pelo Humano. Títulos (131)-(132) sugerem redundância na investigação de `num_ctx` explícito; (368) indica `num-ctx-16814` vazia, contrastando com (512).
