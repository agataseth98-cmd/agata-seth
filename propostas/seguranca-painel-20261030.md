# Decreto: segurança do painel (30/10/2026)

Origem: auditoria só de leitura de 30/10 (itens 2, 3 e 4). Mudanças pequenas em `redesign/painel_operacional/server.py` e testes.

- Leituras `/api/*` (conversas da Seth, vault, estado do Conselho com o token, eventos, lacunas) passam a recusar pedido de outra origem (403). As duas rotas da extensão (`/focos`, `/tasks`) ficam fora dessa checagem e seguem o cabeçalho do executor.
- `/api/abrir`: tamanho do corpo precisa ser número entre 0 e 512; antes, valor negativo podia travar a leitura.
- Fila de pedidos de abertura limitada a 20 (descarta os mais antigos).
- Obsidian: no máximo um pedido a cada 5 s (resposta 429).

Testes novos em `test_painel.py`; suíte do painel e do Conselho passa (41 testes).

Fica de fora, por decisão pendente: trocar o cabeçalho fixo `agata-relay-v2` por chave aleatória. A extensão teria de receber a chave de algum jeito, e qualquer programa local poderia pedi-la do mesmo jeito; o ganho é pequeno e muda a extensão. Peço a sua decisão antes.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh seguranca-painel-20261030 "aprovo: segurança do painel"`.
