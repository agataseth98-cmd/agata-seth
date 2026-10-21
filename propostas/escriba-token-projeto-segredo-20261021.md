# Escriba: token por projeto e recusa de segredo (atualização)

Estado: proposta P-8; não assinada, não aplicada e sem token de produção provisionado.

O diff inclui validação de token por `AGATA_PROJETO_RAIZ`, bloqueio de conteúdo com padrões de segredo, encaminhamento do token pelo cliente MCP e configuração do segredo no compose. Sem caminho de token configurado, o compose monta `/dev/null`; o cliente recusa o dispositivo antes de conectar. O cliente usa o caminho padrão interno, sem depender de variável de ambiente no container. Os testes novos entram na seleção P-16.

Base: `origin/main` em `5f0ec6af165c9cff8bfaf65229493bdee3ade366`.

SHA-256 do diff: `012da50fdef400cd36c0053cfb16d4546f7e45f31af660aecd959e2233301cce`.

Provas medidas em servidor local de porta efêmera: cinco recusas passaram sem gravar; `/memoria` e `/diario` passaram com capability de fixture, incluindo verificação pós-escrita. A suíte completa passou: 58 casos, 0 falhas. `docker compose config` passou com token presente e ausente. O token usado nos testes é sintético; nenhum token real foi provisionado.
