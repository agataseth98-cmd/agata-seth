# Proposta de consolidacao — OmniRoute 504

_Gerada por redesign/grafo/flows/consolidacao.py em 2026-09-24. NAO e' canon. O Humano decide (P-8). Se aprovada, vira ENTRADA NOVA em MEMORIAS (append-only), nunca edicao. Passou no portao mecanico de (371)._

**Refs:** (314), (316), (350), (353), (360), (362), (363), (364), (374), (376), (380), (383), (396), (402), (403)

Esta proposta consolida o estado do OmniRoute 504, resolvendo timeouts e riscos externos com roteamento local direto confirmado.
(362) descobre causa raiz dos 504 por teto exposto curto; (363) aplica mitigação subindo maxWaitMs para 45000ms; (364) registra isso no PROJETO.md.
(374) e (376) estabelecem proteção contra modelos externos gratuitos após queda Groq, removendo `openrouter/auto` do roster.
(380) detalha rajada de chamadas coladas devido a `"thinking": {"type": "disabled"}` no envio.
(402) propõe `seth_local_shim` para Ollama local; contudo, (403) corrige indicando que roteamento direto já existe, tornando (402) obsoleto.
(396) consolida as refs (362), (363), (364), (374), (376), (380).
(314) e (350) mantêm status de modelos antigos e tailscale ativo sem impacto direto na correção.
(316) e (353) tratam de bugs de stream no LibreChat e preços, respectivamente, fora do escopo principal da correção 504.
(360) alerta sobre identidade falsa GLM-4.7-Flash assinando como Claude Sonnet 5, mantendo-se na observação.
Conclusão: A correção é técnica, a segurança via remoção de fontes externas, e o local shim torna-se desnecessário conforme (403).
