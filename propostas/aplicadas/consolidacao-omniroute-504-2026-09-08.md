# Proposta de consolidacao — OmniRoute 504

_Gerada por redesign/grafo/flows/consolidacao.py em 2026-09-08. NAO e' canon. O Humano decide (P-8). Se aprovada, vira ENTRADA NOVA em MEMORIAS (append-only), nunca edicao. Passou no portao mecanico de (371)._

**Refs:** (313), (314), (316), (344), (350), (353), (360), (362), (363), (364), (368), (374), (376), (380), (383)

O tema OmniRoute 504 consolida correções de timeouts, gestão de modelos e proteção contra falhas externas no Agata.
(313) define interface plugável sem tocar núcleo; (314) verifica sobrevivência de modelos antigos via `curl`; (316) reporta bug de stream LibreChat; (344) corrige bugs de tokens e timeout; (350) confirma `tailscale` logado.
(353) cobre todos modelos incluindo `gpt-oss-120b`; (360) alerta sobre identidade falsa GLM/Claude no JSON cru; (362) identifica causa raiz de 504s; (363) aplica mitigação de waitMs; (364) registra estado dos bugs no PROJETO.md.
(368) anota falhas noturnas e rejeita conteúdo errado desde 03/09; (374) protege Conselho Remoto contra modelos grátis após Groq 403; (376) remove `openrouter/auto` do roster por ser pago.
(380) explica causa de rajada de chamadas; (383) descreve três formas de uso Seth/OmniRoute; (364) torna (362) redundante ao registrar a mitigação; (376) sugere obsolescência de (374) ao remover auto.
(380) e (383) complementam sem apagar; todos os títulos fornecidos foram considerados para esta proposta consolidada no Agata.
