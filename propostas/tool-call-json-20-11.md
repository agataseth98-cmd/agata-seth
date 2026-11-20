# Proposta tool-call-json-20-11 — chamada de ferramenta escrita como JSON passa a rodar

**Defeito medido (20/11 11:26, auditoria pelo painel):** pela rota seth-livre, o nemotron-3.5-super respondeu a "consulte a Máquina" escrevendo a chamada `maquina_verificar` como texto JSON (chaves `nome`/`argumentos`). O gateway só convertia blocos `<tool_call>`; a ferramenta não rodou e o Humano recebeu o JSON.

**O quê:** `redesign/router/seth_gateway.py` — `_extrair_tool_calls` passa a aceitar também, pela mesma regra estrita (texto inteiro e só isso): objeto ou lista JSON cru, ou o mesmo dentro de UMA cerca ```json/```, com chaves exatas {name, arguments} ou {nome, argumentos} e nome entre as ferramentas do pedido. No stream, só retém resposta que abre com `{`, `[` ou cerca JSON; cerca de código comum segue em stream. Não converte JSON pedido pelo usuário (chaves diferentes), nem sem ferramentas no pedido.

**Medido:** 64 testes em `redesign/router/test_seth_base.py` (8 novos: positivos pt/en, cru/cercado, lista, string; negativos texto extra, chave extra, nome fora, JSON do usuário, cerca de código); CI local TUDO OK.

**Prova depois de aplicar:** repetir o pedido 4 no painel; esperado `maquina_verificar` executada e a entrada mais recente de MEMÓRIAS na resposta.

**Risco:** resposta que começa com JSON cru fica retida até o fim do stream (sai intacta). **Reversão:** git revert. **Modelo:** Sonnet 5.5 (código), Opus 5.5 (revisão e ajuste da cerca).
