# Proposta de consolidacao — presence_penalty

_Gerada por redesign/grafo/flows/consolidacao.py em 2026-09-07. NAO e' canon. O Humano decide (P-8). Se aprovada, vira ENTRADA NOVA em MEMORIAS (append-only), nunca edicao._

**Refs:** (135), (151), (152), (153), (154), (172)

**Estado consolidado:** A hipótese de que `presence_penalty` causa cortes de geração, embora logicamente intuitiva, foi descartada, pois rodadas controladas com esse parâmetro zerado não apresentaram a falha.

**Acrescentam:**
*   (135): Preserva os parâmetros originais onde o erro ocorre, incluindo o valor 1.5 do parâmetro.
*   (151): Estabelece a hipótese de corte ligada ao parâmetro e documenta a versão do sistema (Ollama 0.32.11).
*   (152): Teste controlado confirma a direção da hipótese (erro desaparece ao zerar o parâmetro).
*   (153): Fornece evidência mais forte para a hipótese (100% de sucesso vs 0% de sucesso).
*   (154): Corrige a conclusão, pois o teste (152) (rodadas com 1.5) e (153) (rodadas com 0) falharam em encontrar a inconsistência real.
*   (172): Nota que uma resposta parcial citou o parâmetro corretamente, mas não esclarece a causa do erro.

**Redundante/Obsoleto:**
*   (147): Obsoleto (referência implícita no (152) e (153)) pois o teste de hipótese foi realizado.
