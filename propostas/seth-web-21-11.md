# Proposta seth-web-21-11 — a Seth no painel lê a web (uma assinatura)

Pendência do lote 1 de 20/11 (spec do painel: "Leitura da web não entrou... fica para lote próprio").

**Achado antes do lote (medido 21/11, 16:30):** o `buscar_web` do navegador-mcp devolvia vazio para todo cliente (2 de 2 consultas). A página comum do Bing chega ao Brave automatizado só com o menu; o DuckDuckGo HTML pede captcha (não se contorna). O RSS do Bing (`format=rss`) devolve resultados: 10 itens na consulta de teste, pelo `politica_egress.buscar_seguro`.

**1. navegador-mcp** (`redesign/mcp/navegador/servidor.py`): `buscar_web` lê o RSS pelo `buscar_seguro` (IP fixado, cada redirect revalidado, teto de 2 MB), fora da fila única do navegador; só se o RSS falhar cai na página comum (na fila). Parser `_itens_rss` recusa DOCTYPE e ENTITY. Autoteste offline cobre o parser.

**2. painel** (`redesign/painel_operacional/ferramentas_seth.py`): `buscar_web(consulta)` e `ler_pagina(url, inicio)` na lista fixa da Seth (só seth-livre), pelo MCP HTTP do navegador; `ler_pagina` = navegar + ler na mesma sessão, só http(s), 8000 caracteres por vez. Todo resultado abre com o selo de DADO EXTERNO. clicar, preencher, navegar e screenshot nunca entram.

**3. Correções da revisão independente (agata-revisor, Haiku):** erro de ferramenta (`isError`) e endereço lido diferente do aberto viram erro (antes podia devolver a página anterior); `cache_anotar` recusado na resposta que já leu a web (instrução escondida em página não chega à memória comum); `politica_egress` bloqueia host com rótulo longo sem exceção (`UnicodeError`).

**Risco declarado ((716), assumido pelo Humano):** a consulta e o endereço saem para a internet; o texto da web volta ao modelo só com o selo, e as leituras do vault seguem disponíveis na mesma resposta. Não medido: qualidade do RSS contra a página comum; sessões MCP não são encerradas (sem DELETE).

**Medido:** painel 45/45 testes; autoteste offline do navegador OK; selftest do politica_egress OK; CI local TUDO OK. **Depois de aplicar:** `systemctl --user restart navegador-mcp` (o painel lê o módulo a cada pedido? não medido; reiniciar o painel também). **Reversão:** git revert + restart dos dois. **Modelo:** Opus 5.5 (código), Haiku 5.5 (revisão).
