# Painel operacional local

O painel oferece leitura local do estado da Agata e um registro manual limitado de avaliações do Conselho. O caminho `/prototipo` contém as áreas da interface; `/` mantém a tela operacional compacta. O servidor escuta apenas em `127.0.0.1:20146` e não instala nem inicia uma unidade systemd.

## Executar

Na raiz do repositório:

```sh
python3 redesign/painel_operacional/server.py
```

Abra `http://127.0.0.1:20146/prototipo`. Para encerrar uma execução manual, use Ctrl-C no terminal em que ela foi iniciada.

## Leituras e limites

- `/api/status` consulta quatro unidades e o Git pelo seth-verificador. Inclui, separadamente, a saúde HTTP de `/health` do LibreChat, dois timers de usuário e o estado de suas unidades, as tarefas configuradas e os últimos resultados registrados da janela, propostas locais e o catálogo de capacidades da capivara.
- As propriedades dos timers são lidas por `systemctl --user show` com nomes e campos fixos, sem shell e com tempo limitado. Um disparo não prova execução; o resultado da unidade e o resultado de cada tarefa são apresentados separadamente. Uma condição que pulou a unidade não é sucesso de execução.
- As tarefas vêm de `config/janela-tarefas.txt`; seus últimos resultados vêm de `~/.cache/agata/janela/state.json`. O painel expõe apenas nome, cadência, resultado e horário. Estado ausente ou inválido aparece como não medido.
- Os modelos vêm de `config/capivara/capacidades.json`: catálogo, medições e uso observado são registros distintos, com datas e amostras. São dados históricos, não disponibilidade ou rota atual. Cada lista é limitada e informa o corte.
- A lista de propostas informa se há marcador. O botão de verificação consulta `p8_verificar` por nome validado e mostra a etapa de falha ou a aplicabilidade naquele momento; não assina nem aplica. O hash do diff é conferido antes e depois da chamada.
- `/api/details` consulta sob demanda oito unidades de integração e conta notas de entradas do vault derivado. Unidade ativa não prova funcionamento completo da integração, e contagem de notas não prova sincronia com o canon.
- `/api/wiki/search` consulta somente `busca_texto` e `busca_semantica` pelo verificador. A consulta é limitada a 200 caracteres e uma linha, e o retorno é limitado e redigido pelo verificador. Falha, índice semântico ausente e índice parcial são identificados; ausência de resultado não prova ausência no canon. Há apenas uma busca em andamento por vez. A interface não guarda histórico.
- A integração RelayCouncil usa o mesmo servidor loopback e a mesma origem do painel: `GET /api/relay-council/catalog` expõe o roster tipado; `POST /api/relay-council/evaluations` valida um resultado com `relay_council_contract.py`, exige timestamp explícito para retry idempotente, confere o modo de acesso contra o provedor, aplica a régua de segredo e acrescenta a avaliação ao cache comum do Conselho. O POST exige `Origin` exata, `Sec-Fetch-Site` same-origin/none e JSON; o corpo tem teto de 65.536 bytes, cada avaliação cabe nos 4.000 caracteres por entrada do cache, e o processo aceita até 60 POSTs por minuto. O identificador da tarefa é resumido por SHA-256 com provedor e timestamp no cache. A mesma tarefa, provedor e timestamp devolvem o recibo existente em retries; conteúdo diferente com essa chave retorna conflito. Limite de frequência e quota diária retornam HTTP 429 com `Retry-After` no primeiro caso. Nenhuma rota chama provedores, lê sessões/cookies ou automatiza DOM.
- A página **Conselho de Modelos em Rede** lê o catálogo e envia somente avaliações preenchidas manualmente por uma pessoa. Para provedores cujo modo registrado exige API oficial, o formulário marca a origem como `official_api`; o painel não armazena nem usa chaves e não faz a chamada ao provedor. Em falha de rede ou limite temporário, a repetição reutiliza o mesmo payload e timestamp para preservar a idempotência. A página não controla abas nem acessa cookies, sessões ou DOM.
- A referência do Git é local, correspondente ao último fetch; a API não consulta o remoto. Estado Git não altera a saúde das unidades. Cada leitura informa origem, observação e validade. Se uma coleta falhar, o navegador conserva o último valor válido como vencido e anuncia a falha; sem valor anterior, exibe ausência de leitura.
- A interface atualiza a cada 60 segundos, permite atualização manual, agrupa pedidos de status próximos e pausa consultas quando a aba está oculta. Os dados complementares são consultados ao abrir Memória ou Integrações.

## Fronteiras

Host, `Origin` e `Sec-Fetch-Site` são verificados nas consultas da interface; POST exige origem local e JSON. Loopback e essas verificações não autenticam outros processos locais. O Conselho em Rede acrescenta somente avaliações sanitizadas ao cache comum; não altera arquivos canônicos ou histórico do painel. O servidor não recebe comandos livres, assinatura, reinício de serviço ou credenciais. Nenhum endereço público ou acesso remoto é configurado. As buscas ajudam a localizar fontes; confirme o texto no canon antes de citar.

Links para Obsidian e LibreChat dependem dos aplicativos existentes. A interface mostra recursos e planos documentados com identificação histórica quando não há leitura viva. `active` do systemd não comprova saúde funcional, e HTTP 200 de `/health` não comprova cada função do chat. A coleta não inclui todos os serviços, resultados internos das tarefas, preços, quota de provedores ou todo o perímetro.

## Verificar em cópia isolada

```sh
python3 redesign/painel_operacional/server.py --selftest
python3 -m unittest redesign/painel_operacional/test_painel.py
node --check redesign/painel_operacional/prototipo.js
```

O teste HTTP usa porta local temporária e fontes simuladas; não exige nem altera o painel em produção.
