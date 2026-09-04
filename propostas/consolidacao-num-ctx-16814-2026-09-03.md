# Proposta de consolidacao — num_ctx 16814

_Gerada por redesign/grafo/flows/consolidacao.py em 2026-09-03. NAO e' canon. O Humano decide (P-8). Se aprovada, vira ENTRADA NOVA em MEMORIAS (append-only), nunca edicao._

**Refs:** (111), (128), (131), (132), (133), (135), (139), (152), (164), (172), (175), (234)

**Consolidação**
O bug de `num_ctx` foi resolvido e revertido, e o teste finalizado em 14/08/2026 confirmou o caminho direto e a inexistência da trava de produção.

**(110)** Confirma a causa raiz e traz a correção necessária.  
**(128)** Testa e valida que o mapa e corpo HTTP corretos não resolvem o problema sem o caminho direto.  
**(131)** Detalha o protocolo de introspecção, mencionando explicitamente o `num_ctx`.  
**(132)** Diferencia a lacuna herdada do teste anterior (`num_ctx` explícito vs caminho direto).  
**(133)** Corrobora que a causa raiz não é o hermes-agent e valida o caminho manual.  
**(135)** Revisa o conserto anterior (embelezamento do modelfile) e o valida corretamente.  
**(139)** Sugere que a trava de confirmação (Passo 5) ainda está aberta/incompleta.  
**(164)** Faz veredito final de entrega e fecha a questão do `num_ctx`.  
**(172)** Sugere o caminho final para finalizar a V1, evitando a lacuna do `grep`.  
**(175)** Aponta redundância com o título (128) na validação do protocolo HTTP.  
**(234)** Aponta redundância com o título (133) na identificação da causa raiz da trava.
