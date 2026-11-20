# Proposta painel-ferramentas-20-11 — a Seth do painel ganha as ferramentas de leitura e anota no cache do Conselho

Lote 1 das decisões do Humano por voz, 20/11/2026 (cache do Conselho, decisão "cache do Conselho vira a memória principal de todos"). Defeito medido no mesmo dia: no painel a Seth escreveu `maquina_verificar` como texto, porque o chat não manda `tools` nem executa chamadas.

**O quê** (`redesign/painel_operacional/`):
- `ferramentas_seth.py` (novo): oferece, só em seth-livre, as ferramentas de leitura do MCP do canon (`redesign/librechat/canon-mcp.mjs`): maquina_verificar, vault_buscar, query_canon, vault_consultar; mais `cache_anotar` (autor fixo "Seth (painel)", tipos fato/decisao/pendencia/nota; o cache recusa segredo e marca dado pessoal). Lista fixa: memoria_acrescentar e qualquer outro nome nunca são oferecidos nem executados. Timeout 60 s, resultado truncado em 12000 caracteres, erro vira texto ao modelo, máximo 5 rodadas.
- `chat_stream.py` / `server.py`: o pedido seth-livre leva `tools`; o servidor executa o laço; Seth pública inalterada, sem ferramentas; `/api/seth/chat` sem stream inalterado.
- `prototipo.js`: estado "A Seth está consultando X…" durante a ferramenta (Regra 0), sem script inline.
- Spec e acceptance do painel com 3 critérios novos; 12 testes novos.

**Fora deste lote:** busca na web e leitura de página — o navegador-mcp é HTTP com sessão e estado de página; vai em lote próprio. `git_sync` e as ferramentas de escrita ficam fora por decisão.

**Medido:** 765 testes do painel + 12 novos; CI local TUDO OK (agente); na Máquina, pelo módulo: as 5 ferramentas oferecidas; maquina_verificar (git_status) e vault_buscar responderam de verdade; memoria_acrescentar recusada. query_canon e vault_consultar dependem do obsidian-ro-proxy (:27125), hoje parado (sistema sob demanda): com ele parado devolvem erro como texto, sem quebrar a conversa.

**Prova depois de aplicar:** reiniciar painel-operacional e repetir no painel o pedido 4 de 20/11.

**Risco:** cache_anotar grava no cache real; até 60 s por ferramenta. **Reversão:** git revert e reiniciar o painel. **Modelo:** Sonnet 5.5 (código), Opus 5.5 (revisão e medição).
