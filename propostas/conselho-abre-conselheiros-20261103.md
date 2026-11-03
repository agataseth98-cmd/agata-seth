# Decreto: a aba Conselho confere e abre os nove conselheiros (03/11/2026)

Pedido do Humano em 03/11/2026: ao clicar na aba Conselho, abrir o navegador com todos os conselheiros e conferir se estão abertos a cada clique.

Como funciona:
- Cada clique na aba Conselho manda `POST /api/abrir {"alvo": "conselho"}`.
- O servidor compara os nove conselheiros (DeepSeek, Gemini, Z.ai, ChatGPT, Claude, Grok, Qwen, Mistral, Kimi) com o inventário de abas que a extensão informa (`available_providers`) e enfileira só os que faltam.
- A extensão que já existe abre cada pedido como aba numa janela normal (ou cria a janela se não houver), sem janela nova por conselheiro e sem tirar o foco dos que já estão abertos. Não muda nada na extensão, então não precisa recarregá-la por causa deste Decreto.
- Repetir o clique não duplica: um conselheiro já na fila, ou pedido há menos de 20 s, não é pedido de novo. O limite de 20 pedidos da fila continua valendo.
- O aviso da tela diz "Os nove conselheiros estão abertos." ou "Abrindo N conselheiro(s) que faltavam…".

Limites (medidos pelo desenho, não ao vivo):
- Depende da extensão estar conectada e recarregada (pendência antiga do Humano). Sem inventário recente da extensão, o servidor trata todos como ausentes e a fila guarda os pedidos até a extensão voltar; o limite da fila evita acúmulo.
- Conselheiro logado ou não é outra coisa: o Decreto abre a página, não faz login.

Muda `redesign/painel_operacional/server.py`, `prototipo.html` e `test_painel.py`. 47 testes OK (um novo cobre faltantes, repetição e nove abertos); JS embutido passa em `node --check`. O painel precisa reiniciar depois de aplicar.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh conselho-abre-conselheiros-20261103 "aprovo: a aba Conselho confere e abre os conselheiros"`.
