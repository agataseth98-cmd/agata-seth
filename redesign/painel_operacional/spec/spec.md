# Spec — Painel operacional (painel unificado)

## Jornadas críticas

1. O Humano abre `/` e cai em `/prototipo#panorama`. Lê serviços, Git e agenda; o que não tem medição aparece como não medido.
2. O Humano abre uma seção pelo menu ou pelo hash (`/prototipo#qualidade`). A seção mostra conteúdo, carregando, vazio ou erro. Nunca mostra valor antigo como se fosse atual.
3. O Humano prepara um turno no Conselho. O envio fica pendente até a aprovação individual dele; nada é enviado sem aprovação.
4. O Humano conversa com a Seth na seção Conversa, com o stream e o fallback atuais.
5. O Humano busca no Conhecimento uma vez e vê o acervo (Alexandria) ou a busca externa, com a fonte à vista.
6. O Humano confere orçamento e tarifas em Custos. Cada gravação continua a virar evento no ledger.
7. O Humano mede e confere em Qualidade: indicadores, medições, SDD, lacunas, Operator Console e avaliação. O que não foi medido aparece como não medido.
8. Quem tem link antigo (`/index.html`, `/frentes`, `/operator_console`, `/conselho-rede/`) é levado à seção certa.

## Base e pré-requisito

- Base: `origin/main` (e99f029c) mais o commit `d1b6b4f7` ("Aplica csp-prototipo-20261106", PR 940, branch `aplica/csp-prototipo-20261106`). A PR 940 entra antes desta spec. Esta spec não a repete: ela tira os 9 `style=` de `prototipo.html` e acrescenta `test_csp_prototipo.py`.
- Medido, base d1b6b4f7, uv com pytest 9.2.0 (a versão do CI): `pytest -q redesign/painel_operacional` = 131 passed, 65 subtests passed.
- Medido, e99f029c (sem a PR 940): 122 passed, 3 subtests passed. `prototipo.html` tem 9 `style=`; em d1b6b4f7 tem 0.
- Medido por leitura de código, não no navegador: `prototipo.js`, `nova_versao.js`, `abrir.js` e `conselho-rede/app.js` não tratam `location.hash`. Por isso o redirect atual de `/conselho-rede` para `/prototipo#conselho` não seleciona a seção. Corrigir faz parte desta versão.
- Medido por leitura de código: `prototipo.js` e `conselho-rede/app.js` declaram `refresh` no escopo global. `conselho-rede/app.js` carrega por último (defer), então o `refresh` de Panorama é o do Conselho. Corrigir faz parte desta versão.
- Medido por leitura de código: `conselho-rede/app.js` e `operator_console/app.js` declaram `const $` no escopo global. Juntar os dois na mesma página quebra o segundo script. Por isso a Operator Console só entra na página depois de isolada.
- Medido: 194 cores hexadecimais literais fora de `:root` em `prototipo.css`; 19 propriedades em `:root`; 6 classes usadas no HTML sem regra direta (`capability-list`, `close-dialog`, `close-vault`, `evidence`, `integration-legend`, `seth-panel`; algumas podem ser ganchos de JS).

## Escopo desta versão

- Uma tela, `/prototipo`, com oito seções: `panorama`, `conversa`, `conselho`, `sistema`, `conhecimento`, `historia`, `custos` e `qualidade`. A `historia` entrou em 11/11/2026, pedido do Humano (bloco História abaixo).
- Cada função das telas atuais tem uma seção e um subpainel (tabela de mapeamento abaixo). Nenhuma função some sem registro.
- Um arquivo de estilo, `prototipo.css`, com tokens de cor e tipografia em `:root` e componentes únicos. Sem `style=`, sem `<style>`, sem script inline.
- Estados carregando, vazio e erro em cada seção que consome API.
- Nenhuma rota nova de API. As rotas `/api/*` ficam como estão. Exceção pedida pelo Humano em 07/11/2026: `GET /api/conselho/memoria`, só leitura, para a aba Memória compartilhada (ver Contrato).
- Conhecimento tem uma busca única, que serve à Alexandria (escopo "dentro"), ao Acervo (escopo "fora", busca externa) e à Wiki, a documentação do `/index.html` (escopo "documentação"). Decidido pelo Humano em 07/11/2026.
- Casca registrada, fora das sete seções: barra lateral, cabeçalho e chip LOCAL (decidido pelo Humano em 07/11/2026); breadcrumb, busca "Buscar neste mapa…", nota, rodapé e diálogo de evidência, como na tabela de mapeamento.
- Lote 3 da Conversa (09/11/2026, pedido do Humano, paridade com o LibreChat): busca nas conversas, fixar, arquivar, marcadores, pastas, exportação em JSON e Markdown, importação de JSON exportado e conversa temporária. Contrato em Rotas de API e critérios no fim desta seção.
- Proteção das conversas (09/11/2026, pedido do Humano depois do sumiço de duas conversas importadas, confirmado por ele em 09/11/2026 às 16:20 como apagadas pela própria tela): apagar vai para a Lixeira, escritas exigem origem do painel e ficam registradas, salvar preserva a origem de conversa importada, e arquivo ilegível é contado e não é apagado. Contrato em Rotas de API (bloco de proteção) e critérios no fim da seção de Critérios.
- Lote 4 da Conversa (09/11/2026, pedido do Humano, paridade com o LibreChat): editar e reenviar, regenerar e ramificar, com ramos navegáveis ("< 1/2 >"); Parar; Continuar; feedback de boa e de ruim resposta; barra de contexto; atalhos de teclado; tema claro, escuro ou do sistema. Contrato em Rotas de API e critérios no fim desta seção. Nenhuma rota nova de API; o gateway não muda.
- Importantes (11/11/2026, pedido do Humano: "importantes no painel"): aba Importantes dentro de Panorama e cartão "Importantes: N abertos" no Panorama. Lista local de ideias e pendências que o Humano manda guardar: criar, marcar feito, descartar, reabrir e editar; nada é apagado de fato. Trazer as entradas marcadas com IMPORTANTE do cache do Conselho, só leitura. Contrato em Rotas de API e critérios no fim da seção de Critérios.
- História (11/11/2026, pedido do Humano): seção `historia` no `/prototipo`, com o índice de tomos e a leitura dos textos de `historia/` do checkout (só leitura), e o botão Ouvir, que lê o texto com a voz do sistema. Contrato em Rotas de API (bloco História) e critérios no fim da seção de Critérios.
- Voz da Seth (11/11/2026, pedido do Humano, paridade com o LibreChat): ler em voz alta (botão Ouvir em cada resposta e modo conversa), ditado pelo microfone e linha da voz na página Sentidos. Tudo com a voz do sistema (`pt_BR-agata-last`, pelo `scripts/agata_falar.py`, sem editar o script). Bloco Voz da Seth abaixo.

## Fora desta versão

- B1, chat com streaming novo: a Conversa continua como está (stream atual, com fallback para `/api/seth/chat`). Motivo: é funcionalidade nova, com risco próprio; o pedido desta versão é a tela unificada.
- B2, ferramentas com aprovação: a aba Ferramentas do Conselho e o fluxo de pedidos ficam como estão. Motivo: mexe em execução de ferramenta; tem spec própria.
- Remoção do LibreChat: o botão "LibreChat" continua em Sistema e a rota de abertura continua. Motivo: decisão separada.
- Ajuste fino de design: sem novo layout e sem mudar as cores escuras. A paleta clara do lote 4 é gerada a partir das cores atuais (Escopo). Motivo: a verificação visual depende do navegador; as capturas do lote 4 mostram o estado, não são aceite visual do Humano.
- Mudança em `/api/*`, em CSP, em propostas, assinatura, PR ou merge. Continuam fora do painel.
- Link público de compartilhamento de conversa: fora deste lote. Pendência: precisa decisão de segurança do Humano (quem vê, por quanto tempo, como revoga).

## Contrato

### Rotas de tela

- `GET /prototipo` responde 200. Sem hash, abre `panorama`.
- Hash `#<seção>` escolhe a seção. Trocar o hash troca a seção (`hashchange`). Hash desconhecido cai em `panorama`.
- Redirects com 302 e `Location`:
  - `/`, `/index.html` e `/frentes` para `/prototipo#panorama`;
  - `/operator_console` e `/operator_console/` para `/prototipo#qualidade`;
  - `/conselho-rede` e `/conselho-rede/` para `/prototipo#conselho`.
- Medido hoje (server.py:103-124 e 1035-1038): `/` e `/conselho-rede` já redirecionam (`/` para `/prototipo`, sem hash). `/index.html`, `/frentes`, `/operator_console`, `/operator_console/` e `/conselho-rede/` respondem 200.

### Rotas de API

- Os caminhos e verbos existentes permanecem; o JS só chama caminhos presentes no servidor. A resposta da leitura de conversa salva é normalizada com `schema_version` e `id`, exigidos pelo cliente. Mensagens importadas até 65536 caracteres são aceitas.
- Seletor de modelo da conversa (09/11/2026): `GET /api/seth/modelos` devolve `padrao` (`seth-livre`) e a lista fixa `modelos` (`id`, `rotulo`, `descricao`): `seth-livre` e `seth-public`. `/api/seth/chat/stream` e `/api/seth/chat` aceitam `modelo` opcional (ausente vale o padrão); fora da lista, 400 sem chamar o gateway. A conversa salva guarda `modelo` e o `modelo` de cada resposta da Seth; conversa antiga sem o campo abre como `seth-livre`. Fora da lista ficam `seth-zai`, `seth-gemini`, `seth-hf`, `seth-mistral` e `seth-auto`, porque o gateway recusa com 403 quem não é `seth-livre` nem `seth-public` sem classificação pública.
- Modelo que respondeu (09/11/2026): o gateway manda o cabeçalho `X-Modelo-Real` com o nome real do modelo (não o alias). `/api/seth/chat/stream` e `/api/seth/chat` repassam esse cabeçalho ao navegador só quando o valor tem formato de nome (`chat_stream.modelo_real_valido`). A conversa salva guarda `modelo_real` em cada resposta da Seth quando o cabeçalho veio; gravação com `modelo_real` fora do formato descarta só esse campo. A UI mostra o modelo real em cada resposta; sem ele, mostra o escolhido com `(escolhido)`.
- Conversa, lote 3 (09/11/2026). Tudo local, em `~/.cache/agata/painel-conversas`; nenhum serviço externo.
  - `GET /api/seth/conversas` (já existia) devolve, em cada item, `fixada`, `arquivada`, `marcadores` e `pasta`; e no topo `pastas` (`id`, `nome`, `conversas`), `marcadores` (distintos), `total` (conversas salvas) e `organizacao` (`ok` ou `ilegivel`). Fixadas vêm primeiro. Mostra até 200 conversas, as mais recentes.
  - `GET /api/seth/conversas/busca?q=` procura `q` (1 a 120 caracteres, sem diferenciar caixa nem acento) em títulos e mensagens das conversas salvas. Resposta 200: `termo`, `total` e `resultados` (até 50; cada um com `id`, `titulo`, `atualizada`, `arquivada`, `ocorrencias`, `campo` `titulo` ou `mensagem`, `mensagem` (posição na conversa, ou `null` se foi no título) e `trecho`, de até 120 caracteres com reticências). `q` vazio ou acima de 120 caracteres: 400 com motivo. Termo sem resultado: 200 com `total` 0.
  - `POST /api/seth/conversa/organizar` com `{id, fixada?, arquivada?, marcadores?, pasta?}`: muda só a organização da conversa, nunca o conteúdo. `marcadores` é lista de até 10 textos de até 24 caracteres (letras, números, espaço e hífen), guardados em minúsculas e sem repetir. `pasta` é `null` ou o `id` de pasta existente. Corpo até 4096 bytes; acima, 413. Conversa inexistente: 404. Campo desconhecido ou valor fora do contrato: 400 com motivo.
  - `POST /api/seth/pastas` com `{acao: criar|renomear|apagar, id?, nome?}`. Nome de 1 a 60 caracteres, sem repetir (sem diferenciar caixa), até 50 pastas. Apagar pasta não apaga conversa: as conversas dela ficam sem pasta. Ação desconhecida ou id inválido: 400; pasta inexistente: 404.
  - `GET /api/seth/conversa/exportar?id=&formato=json|md`: download (`Content-Disposition: attachment`) com nome `agata-conversa-<id>.json` ou `.md`. JSON: `formato` (`agata-conversa`), `versao` (1), `id`, `origem_id`, `titulo`, `modelo`, `mensagens` e `exportada_em`. Formato fora da lista: 400; conversa inexistente: 404. A conversa temporária não é salva e não tem exportação.
  - `POST /api/seth/conversa/importar` com o JSON exportado. Limite de 263168 bytes (262144 da conversa mais 1024 de cabeçalho); acima, 413. Valida `formato`, `versao`, identificador e conversa (as mesmas regras da gravação). Reconhece pelo `id` e pelo `origem_id` do arquivo: se o id já é de uma conversa daqui, ou se alguma conversa daqui guarda esse `origem_id`, responde `estado: ja_existe` e não grava nada; senão grava com id novo e guarda o `origem_id`. Resposta: `estado` (`importada` ou `ja_existe`), `id` e `titulo`.
  - Origem cruzada nas rotas novas: 403, como nas outras leituras e escritas de `/api/seth/*`.
  - `organizacao.json`, dentro da pasta de conversas, guarda `pastas` e uma entrada por conversa (`fixada`, `arquivada`, `marcadores`, `pasta`, `origem_id`). Sem o arquivo, toda conversa vale o padrão (sem fixada, sem arquivada, sem marcador, sem pasta). Entrada malformada é ignorada na leitura. Arquivo ilegível: a lista avisa (`organizacao: ilegivel`) e as escritas respondem 409 sem sobrescrever.
  - Conversa temporária: existe só na tela. A UI não chama `POST /api/seth/conversa` enquanto ela está ligada.
  - Conversa, proteção (09/11/2026, `chat-protege-conversas-09-11`). Tudo local, em `~/.cache/agata/painel-conversas`.
    - `POST /api/seth/conversa/apagar` não apaga de vez: move a conversa para `.lixeira/<id>-<AAAAMMDD-HHMMSS>.json` (mesmos bytes) e leva a entrada de organização junto, guardada na chave `lixeira` de `organizacao.json`. Resposta 200 com `apagada` e `lixeira` (nome do item). Conversa inexistente: 404. Organização ilegível: 409, nada é movido.
    - `GET /api/seth/lixeira` devolve `schema_version`, `items` (até 200, mais recentes primeiro; cada um com `nome`, `id`, `titulo`, `apagada_em` em `dd/mm/aaaa hh:mm` e `mensagens`), `total` (itens legíveis) e `ilegiveis`.
    - `POST /api/seth/lixeira/restaurar` com `{nome}`: devolve a conversa ao lugar dela e a entrada de organização (pasta apagada enquanto a conversa estava fora vira sem pasta). Nome inválido: 400; item fora da lixeira: 404; já existe conversa com o mesmo id, ou organização ilegível: 409, nada é mexido.
    - `POST /api/seth/lixeira/purgar` com `{nome}`: apaga de vez, só por pedido manual (a tela pede confirmação). Nenhuma rotina apaga sozinha. Nome inválido: 400; fora da lixeira: 404; organização ilegível: 409.
    - Escritas (salvar, apagar, organizar, pastas, importar, restaurar e purgar) exigem `Origin` igual ao do painel ou `Sec-Fetch-Site: same-origin`. Sem cabeçalho nenhum: 403. Cabeçalho que diz outra origem (cross-site, `Origin` de outro site ou `null`): 403, mesmo que o outro cabeçalho bata.
    - Registro: cada pedido de escrita, inclusive o recusado, acrescenta uma linha em `.registro.jsonl`: `hora` (ISO com -03:00), `rota`, `id` (12 hex, ou nome do item da lixeira; `null` quando não há) e `status`. Sem título, texto, marcador ou nome de pasta. Só acréscimo. Se o arquivo não puder ser escrito, a ação segue e a linha se perde (limite declarado).
    - Conversa importada (LibreChat): o arquivo guarda `origem`, `origem_id`, `titulo_original`, `data_original`, `importado_em` e `id`. O salvar não reescreve essa origem; quem envia sem `id`, mas com origem já gravada, cai no mesmo arquivo. Campo de origem fora do formato sai sem recusar o salvar. Mensagem mantém `criada` e `origem_id` só se continua no mesmo lugar, com o mesmo papel e texto.
    - Importação: item que está na lixeira conta como existente: responde `ja_existe` com `lixeira: true`, sem gravar.
    - Listagem: `total` passa a contar só as conversas legíveis; `ilegiveis` conta os arquivos de conversa que não puderam ser lidos. Eles não aparecem na lista e não são apagados nem mexidos.
    - Tela: a aba Conversa tem a seção Lixeira (restaurar; apagar de vez em dois cliques). Enquanto a Seth responde, trocar de conversa, Nova conversa e temporária ficam bloqueados, com aviso. Apagar só sai da tela depois da confirmação do painel. Salvar grava na conversa de origem. A contagem de arquivos ilegíveis aparece na lista.
- Conversa, lote 4 (09/11/2026). Sem rota nova. `POST /api/seth/conversa` e `GET /api/seth/conversa?id=` aceitam e devolvem a árvore de ramos; `mensagens` continua sendo o caminho ativo.
  - Sem ramo, a conversa grava `mensagens` como antes. Com ramo, grava `arvore` (`nos`: cada nó com `id` de 1 a 16 letras e números, `pai` (id de um nó que vem antes no arquivo, ou `null`), `role`, `content` e os campos de resposta; e `folha`, o último nó do caminho ativo) e também `mensagens`, o caminho, para que uma versão anterior abra a conversa. O caminho sai da folha subindo pelos pais. Com `arvore` no pedido, `mensagens` é ignorado. O painel manda só a árvore quando há ramo.
  - Limites: até 400 nós; até 200 mensagens no caminho; 65536 caracteres por mensagem; 262144 bytes por gravação. Árvore fora do formato responde 400 com motivo e nada é gravado. Na leitura, árvore ilegível cai no caminho `mensagens`, se houver.
  - Campos da resposta da Seth, só quando têm valor: `interrompida: true` (Parar, ou erro no meio do stream); `feedback` (`nota` `bom` ou `ruim`, e `motivo` opcional de até 200 caracteres); `cortes` (posições, no texto, onde começa uma continuação; até 20). Valor fora do formato sai da mensagem sem recusar a conversa. `interrompida` e `feedback` só valem para resposta da Seth.
  - `ramificada_de` (opcional): `{id, mensagem}`, a conversa de onde a ramificação saiu e a posição da mensagem no caminho (inclusive, a partir de 0). Fora do formato, sai sem recusar.
  - Exportação JSON leva `arvore` e `ramificada_de` quando existem. Markdown leva só o caminho e avisa. Importação aceita o mesmo; a regra de não duplicar não muda.
  - Busca e contagem da lista veem só o caminho ativo.
  - Ao trocar de versão (setas `< 1/2 >`), a conversa segue pela resposta mais nova de cada passo seguinte: a última criada em cada ramo. Parar e Continuar atuam na última resposta do caminho ativo.
  - Editar e reenviar, regenerar, trocar de versão, ramificar, Continuar e feedback usam as rotas que já existem. Continuar manda a janela do caminho com `Continue de onde parou, sem repetir o que já foi dito.` como última mensagem do usuário, só no pedido; essa mensagem não é gravada e a continuação entra na mesma resposta, a partir de um corte.
  - Parar aborta o fetch do stream (AbortController) e mantém o texto recebido, marcado `interrompida`. O gateway não mudou: o verificador ainda retém o stream das rotas `seth-*` até o fim (`redesign/router/seth_gateway.py`, `_reter` e `_liberar_retidos`; medido no lote 1, `083a4627`). Com a cadeia real, Parar corta a espera e o texto que já chegou, que pode ser nenhum. O gateway também segura o turno no servidor até a retenção acabar: uma pergunta logo após Parar pode receber 429 `busy`.
  - A UI mostra a nota de Parar com o texto que já foi gravado. Tratamento do estado `interrompida` em relação à proposta `chat-stream-verificar-depois-09-11`: ver Riscos.
- Exceção pedida pelo Humano em 07/11/2026 (aba Memória compartilhada, seção Conselho): `GET /api/conselho/memoria?n=40`. Só leitura do cache do Conselho (`redesign/router/cache_conselho.py`, função `ler`), com o mesmo filtro de dado pessoal e segredo da gravação (`filtrar`). Não aceita caminho de arquivo do cliente e não escreve nada.
  - `n` é inteiro de 1 a 200; padrão 40; acima de 200 corta em 200; zero, negativo ou não numérico responde 400. `n` vazio vale o padrão.
  - Resposta 200 em JSON: `estado` (`ok` ou `vazio`), `n` (aplicado), `entradas` (mais recentes primeiro; cada uma com `n`, `data_hora` em `dd/mm/aaaa hh:mm`, `autor`, `tipo`, `texto`), `observed_at` e `fresh_until`.
  - Cache inexistente ou sem entradas: `estado` `vazio`, lista vazia, 200. Não é erro.
  - Falha de leitura (arquivo ilegível ou linha que não é JSON): 500 com `memoria indisponivel`; a tela mostra `erro`.
  - Origem cruzada: 403, como as outras leituras de `/api/*`.
  - Tipos: `fato`, `decisao`, `pendencia`, `nota` e `diario` (os cinco de `cache_conselho.TIPOS`). A aba filtra por tipo no próprio navegador, sobre as entradas já recebidas.

- Importantes (11/11/2026). Tudo local, em `~/.cache/agata/painel-importantes.json` (escrito inteiro, por troca atômica). Registro de escritas em `painel-importantes.registro.jsonl`: hora, rota, id e status; sem texto. Só acréscimo.
  - `GET /api/importantes` devolve `schema_version`, `estado` (`ok`, `vazio` ou `ilegivel`), `itens` (abertos primeiro; dentro de cada estado, o mais recente antes) e `contagem` (`aberto`, `feito`, `descartado`). Cada item tem `id` (12 hex), `texto`, `origem` (`humano`, `cache` ou `modelo`), `criado_em`, `estado` (`aberto`, `feito` ou `descartado`), `feito_em`, `nota` e `cache_n` (número da entrada do cache do Conselho; só quando `origem` é `cache`).
  - `POST /api/importantes` com `{texto}` cria um item de origem `humano`. Texto de 1 a 4000 caracteres, sem caractere nulo. Lista com até 2000 itens; acima, 409. A rota grava só `humano`: a origem `modelo` existe no esquema e nenhuma rota a grava ainda.
  - `POST /api/importantes/estado` com `{id, estado}`: `feito`, `descartado` ou `aberto` (reabrir). Sair de `feito` limpa `feito_em`.
  - `POST /api/importantes/editar` com `{id, texto?, nota?}`: nota de até 500 caracteres; nota vazia limpa a nota. Campo fora do contrato, ou pedido sem `texto` nem `nota`: 400.
  - `POST /api/importantes/trazer` (corpo `{}`): lê o cache do Conselho com `cache_conselho.ler`, sem escrever nele, e cria um item para cada entrada cujo texto começa com `IMPORTANTE`, com `origem` `cache` e `cache_n` igual ao número da entrada. Entrada já trazida, mesmo descartada depois, não entra de novo. O texto passa por `cache_conselho.filtrar`: segredo não é trazido (conta em `recusadas`); dado pessoal vira marca. Resposta: `trazidas`, `ja_estavam`, `recusadas`, `lidas`.
  - Escritas exigem origem do painel (`_escrita_permitida`): 403 sem cabeçalho ou com origem de outro site. Corpo acima de 4096 bytes: 413. JSON inválido: 400. Item inexistente: 404. Arquivo ilegível: 409, sem gravar. Falha de gravação: 500, sem alterar. Cada pedido, inclusive o recusado, acrescenta uma linha no registro.
  - Arquivo fora do formato (JSON quebrado, `schema_version` diferente ou item fora do esquema) vale `ilegivel`: a leitura diz `ilegivel` e nenhuma escrita o sobrescreve.

- História (11/11/2026). Tudo lido de `historia/` do checkout; nada é gravado nele.
  - `GET /api/historia` devolve `schema_version`, `estado` (`ok` ou `vazio`) e `tomos`. Cada tomo traz `tomo`, `numeral`, `titulo` e `textos`; cada texto traz `id`, `numero`, `titulo`, `periodo`, `autor`, `estado` e `protocolo`, sem o corpo. Pasta ausente ou sem texto: `vazio`, 200.
  - `GET /api/historia/texto?tomo=<tomo-NN>&texto=<NN-titulo>` devolve `frontmatter` (pares `chave: valor` do bloco inicial, sem as aspas externas) e `corpo` (o texto sem o bloco). Fora do formato, 400: o cliente não escolhe caminho. Inexistente ou link para fora de `historia/`, 404. Acima de 65536 bytes, 413.
  - `POST /api/historia/ouvir` com `{tomo, texto}` (até 512 bytes) lê o corpo com `scripts/agata_falar.py --arquivo`, sem o frontmatter, e responde `falou` (verdadeiro só com código de saída 0) e `motivo`. Uma fala por vez: com outra em curso, 429. Só aceita JSON da própria origem: outra origem ou outro tipo, 403.
  - As leituras da História recusam origem cruzada com 403, como as demais de `/api/*`.

- Voz da Seth (11/11/2026). Tudo com a voz do sistema (piper `pt_BR-agata-last`, pelo `scripts/agata_falar.py`); nenhuma outra voz, e o texto do Agata não sai da Máquina.
  - `POST /api/seth/ouvir` com `{texto}` (pedido até 65536 bytes) fala por parágrafo e responde `falou` (verdadeiro se pelo menos um trecho foi tocado), `completo`, `codigo` (`completo`, `parado`, `falha`, `texto`, `voz` ou `player`), `trechos_falados`, `trechos` e `motivo` em português simples. Texto que passa de 12.000 caracteres depois do preparo não é lido. Demora o tempo da leitura. Com outra leitura em curso (Seth ou História): 429. Escrita: 403 sem origem do painel.
  - `POST /api/seth/ouvir/parar`: pede a parada, que vale entre trechos (o trecho que está tocando termina). Sem leitura, responde `falando` falso e não faz nada. Escrita: 403 sem origem do painel.
  - `GET /api/seth/ouvir`: só leitura, com `falando`, `trecho`, `trechos`, `ultimo_uso` e `ultimo_motivo` (em memória, desde o início do painel). Origem cruzada: 403.
  - Serviço: quem fala liga o `piper-tts.service` se estiver parado e desliga depois, só se foi ele que ligou. Piper com modelo diferente de `pt_BR-agata` não fala (`codigo` `voz`).
  - `POST /api/seth/ditado`: corpo cru do áudio do navegador (`Content-Type` de áudio, até 2 MB; o cliente para em 60 s). O painel repassa a `POST /v1/audio/transcriptions` do `servidor_ouvido` (127.0.0.1:20137) e responde `{texto}` (até 4000 caracteres). Erros em JSON `{erro}`: 403 origem, 411 sem tamanho, 413 grande, 415 não é áudio, 422 sem fala ou áudio não processado, 429 ocupado, 502 formato, 503 ouvido fora do ar ou sem motor. Não liga o ouvido.
  - Página Sentidos: a linha `voz` vem de `seth_voz.resumo_voz()`, que só lê o `/health` do piper e o último uso.

### Ativos servidos

- Ficam: `/prototipo`, `/prototipo.css`, `/prototipo.js`, `/nova_versao.js`, `/abrir.js`, `/conselho-rede/app.js`, `/operator_console/app.js`, `/assets/agata-portrait.png`, `/historia.js`.
- Saem (404 na versão nova): `/app.js`, `/styles.css`, `/frentes.js`, `/nova_versao.css`, `/conselho-rede/style.css`, `/operator_console/style.css`.
- Viram redirect: `/index.html`, `/frentes`, `/operator_console/index.html`, `/conselho-rede/index.html` (os arquivos saem do disco na aplicação).
- CSP: sem mudança. `default-src 'none'; script-src 'self'; style-src 'self'; frame-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'`.

### Seções e navegação

- Cada seção é `<section id="<seção>">` dentro de `/prototipo`. Dentro dela há subpainéis `<div id="sub-<nome antigo>">`, com o nome da tela antiga da tabela. Abas internas (`data-sub`) trocam subpainéis dentro da seção.
- Menu lateral: oito botões com `data-secao`. O botão da seção aberta tem `aria-current="page"`.
- Breadcrumb mostra `Agata / <nome da seção>`.
- Atalhos `data-open-page` passam a apontar para uma seção e, se for o caso, um subpainel.
- Submenus recolhíveis (`nav-group`) saem.

### Estados

- Cada seção que consome API tem três marcadores ocultos por padrão: `data-estado="carregando"`, `data-estado="vazio"` e `data-estado="erro"`. O JS mostra um deles.
- `carregando`: texto curto e `aria-busy="true"` na área.
- `vazio`: diz o que falta para aparecer (ex.: "Nenhuma fonte ainda").
- `erro`: motivo curto e "não medido". Não mostra valor antigo como atual; quando há valor anterior, mostra a hora dele.
- HTTP 429 (ocupado) é `erro` com o texto "ocupado; tente depois".
- Medido no código atual: os estados não são padronizados. Há textos soltos ("Calculando…", "Carregando frentes…") e elementos `*-vazio` em algumas páginas.

### APIs usadas por seção (sem rota nova)

- panorama: GET `/api/status`, `/api/details`, `/api/capacidades`, `/api/frentes`, `/api/importantes` (aba Importantes e cartão, 11/11/2026; POST `/api/importantes`, `/api/importantes/estado`, `/editar` e `/trazer`); POST `/api/proposals/verify` (só por ação do Humano); GET `/api/vault/item` (diálogo).
- conversa: GET `/api/seth/conversas`, `/api/seth/conversa?id=`; POST `/api/seth/chat/stream` (com fallback `/api/seth/chat`), `/api/seth/conversa`, `/api/seth/conversa/apagar`; GET `/api/seth/lixeira`; POST `/api/seth/lixeira/restaurar` e `/api/seth/lixeira/purgar`.
- conselho: GET `/api/relay-council/state`, `/api/relay-council/catalog`, e (aba Memória compartilhada, 07/11/2026) `/api/conselho/memoria`; POST `/api/relay-council/actions`, `/groups`, `/decision`; POST `/api/abrir` (alvo `conselho` ou nome de conselheiro).
- sistema: GET `/api/status`, `/api/details`, `/api/nova-versao/estado`; POST `/api/nova-versao/executar` (`fotografar`, `classificar`, `gravar_chave`, `remover_chave`, `adicionar_provedor`, `testar_rotas`, `cancelar_teste`); POST `/api/abrir` (Obsidian, LibreChat, OmniRoute).
- conhecimento: GET `/api/grafo`, `/api/vault/item`, `/api/nova-versao/estado`; POST `/api/wiki/search`, `/api/nova-versao/executar` (`consultar`, `skills`, `indexar`, `iniciar`, `acervo_*`, `acervo_externa_*`), POST `/api/nova-versao/upload`.
- historia: GET `/api/historia`, `/api/historia/texto`; POST `/api/historia/ouvir`.
- custos: GET `/api/nova-versao/estado`; POST `/api/nova-versao/executar` (`salvar_orcamento`, `ajustar_conexao`).
- qualidade: GET `/api/qualidade-llm`, `/api/medicoes/estado`, `/api/sdd/estado`, `/api/lacunas`, `/api/nova-versao/estado`; POST `/api/medicoes/executar`, `/api/sdd/executar`, `/api/nova-versao/executar` (`avaliar`, `cancelar_avaliacao`, `medir_recuperacao`, `medir_ouvido`, `salvar_politica`, `ver_reservado`, `revisar_reservado`, `ver_execucao`).

### Mantido (contrato anterior, sem mudança)

- Servidor escuta só em 127.0.0.1 e responde 421 a `Host` diferente.
- Leituras de API recusam origem cruzada. A extensão do Conselho é a exceção declarada.
- Corpo de POST JSON até 64 KB (65 536 bytes; server.py:1185); acima disso, 413.
- Qualidade (`qualidade_llm`): `GET /api/qualidade-llm` devolve indicadores medidos; item sem medição vem como `unknown` e `não medido`.
- Medição: `GET /api/medicoes/estado` e `POST /api/medicoes/executar` rodam só `medir_recuperacao.py` (lexical ou `--semantico`) e `medir_contexto_efetivo.py` (tarefa `agulha`, `varias`, `rastreio` ou `agregacao`; raciocínio `desligado` ou `ligado`). Um por vez, em segundo plano. O modelo precisa estar na lista de tags do Ollama local. Resultados ficam fora do repositório (`AGATA_MEDICOES_DIR`).
- SDD (`sdd_painel`): `GET /api/sdd/estado` lista os componentes ancorados, seus critérios e o estado da âncora. `POST /api/sdd/executar` aceita só `{acao: ancora|criterios, componente}` de componente ancorado, exige JSON e origem igual, e roda um por vez. Os comandos do manifesto precisam ser `pytest -q redesign/...`. Projetos externos de `config/sdd/*.json` rodam com `acao: projeto`, só com nome de descritor existente; o manifesto do projeto só pode ter `pytest` com alvos relativos.
- Nova versão (`nova_versao_painel`): `GET /api/nova-versao/estado` e `POST /api/nova-versao/executar` aceitam ações de lista fechada, uma por vez: `iniciar`, `indexar`, `consultar`, `skills`, `classificar`, `fotografar`, `salvar_orcamento`, `gravar_chave`, `remover_chave`, `ajustar_conexao`, `adicionar_provedor`, `testar_rotas`, `cancelar_teste`, `salvar_politica`, `ver_reservado`, `revisar_reservado`, `rotas_disponiveis`, `avaliar`, `medir_recuperacao`, `cancelar_avaliacao`, `ver_execucao`, `medir_ouvido` e as ações de acervo usadas pela tela (`acervo_importar`, `acervo_processar`, `acervo_url`, `acervo_direitos`, `acervo_transicionar`, `acervo_externa_pesquisar`, `acervo_externa_guardar`). A consulta tem até 300 caracteres e só vira pacote de evidência. O orçamento só aceita os campos e limites de `redesign/nova_versao/orcamento.py`, e cada mudança vira evento no ledger. Dados ficam fora do repositório (`AGATA_NV_DIR`).
- Chave de API: vai para o cofre de `redesign/conexoes/segredos.py`. O campo é `password`, é limpo ao enviar, e nenhuma resposta nem estado a devolve.
- Avaliação: recusa o reservado sem revisão do Humano e sem política fixada; o estado nunca traz o gabarito.
- Upload de fonte: só `.md`; recusa o resto sem deixar temporário.
- Proposta: `/api/proposals/verify` só lê a origem local. Assinatura, PR e merge não são executados pelo painel.
- Abrir programas (`/api/abrir`): lista fixa no servidor; o cliente só manda o nome.
- Conselho: nada é enviado nem executado sem aprovação individual.

### Substituído (contrato de 03/11/2026)

- "A navegação lateral agrupa as 24 páginas em Panorama, Conselho e quatro submenus recolhíveis" sai. Substituído por sete seções e abas internas.
- "As páginas da nova versão usam só classes de `nova_versao.css`" sai. Substituído por um arquivo de estilo só (`prototipo.css`).
- "Página Acervo e fontes" (lote 5) vira o subpainel `sub-nv-acervo` dentro de Conhecimento. A rota de upload não muda.

## Mapeamento de funções

Origem: as 25 seções de `/prototipo`, mais `/frentes`, `/index.html`, `/operator_console` e `/conselho-rede`. A coluna "Subpainel e ids" traz o id do subpainel ou dos controles. "Casca" são elementos de moldura; estão listados para não sumirem, e a decisão de não mapeá-los a uma seção é pedida ao Humano.

| Tela atual | Função | Seção | Subpainel e ids |
|---|---|---|---|
| prototipo · Panorama | Serviços, Git e agenda, com fonte e hora | panorama | sub-panorama (`overview-alert`) |
| prototipo · Panorama | Atualizar leitura; atualização automática a cada 60 s; pausa com a aba oculta | panorama | sub-panorama (`refresh-main`) |
| prototipo · Panorama | Cartão de conversa com o estado do chat | panorama | sub-panorama (`chat-state`) |
| prototipo · Panorama | Atalhos "Abrir" para Estado operacional, Visão, Conselho e conversa da Seth | panorama | sub-panorama (`data-open-page`, vira `data-secao`) |
| prototipo · Panorama | Atalhos de memória: Começar no vault, Linha do tempo, Mapa do sistema, Brain Atlas, Base de memórias | panorama | sub-panorama (abrem `vault-dialog`; dono conhecimento) |
| prototipo · Visão do sistema | Indicadores clicáveis que levam à seção de origem | panorama | sub-visao (`visao-kpis`) |
| prototipo · Visão do sistema | Melhorias a propor: o que falta ou está pendente | panorama | sub-visao (`visao-melhorias`) |
| prototipo · O que posso fazer | Filtros: tudo, disponível, parcial, planejado, horizonte | panorama | sub-capacidades (classe `filterbar`) |
| prototipo · O que posso fazer | Cartões de capacidade e botão EVIDÊNCIA (diálogo de evidência) | panorama | sub-capacidades (classe `cap-card`, `evidence-dialog`) |
| prototipo · O que posso fazer | Marca de lacuna nos cartões sem medição | panorama | sub-capacidades (`marcarLacunasNosCartoes`) |
| prototipo · Plano de trabalho | Propostas para examinar, só leitura de origem local | panorama | sub-plano (`/api/proposals/verify`) |
| prototipo · Plano de trabalho | Atalhos Estado do sistema e Início do vault | panorama | sub-plano |
| prototipo · Importantes (11/11/2026) | Lista local: guardar, marcar feito, descartar, reabrir, editar e trazer do Conselho | panorama | sub-importantes (`importantes-lista`, `importantes-form`, `importantes-trazer`) |
| /frentes | Lista de frentes, somente leitura (`config/frentes.json`) | panorama | sub-frentes (`frentes-lista`, `frentes-estado`, `frentes-cabecalho`) |
| /index.html | Serviços e Git do painel antigo | panorama | sub-panorama (já coberto; sem card duplicado) |
| /index.html | Wiki da Agata: busca, pela busca única de Conhecimento (escopo "documentação") | conhecimento | busca única (`conhecimento-busca`, `conhecimento-consulta`, `conhecimento-escopo`, `wiki-mode`, `wiki-source`, `wiki-results`) |
| prototipo · Conversa com a Seth | Lista de conversas; nova, abrir, renomear e apagar | conversa | sub-conversa (`seth-conversas`, `seth-nova`) |
| prototipo · Conversa com a Seth (lote 3, 09/11/2026) | Busca nas conversas salvas (título e mensagens), com trecho e link para a mensagem | conversa | sub-conversa (`seth-busca`, `seth-busca-resultados`) |
| prototipo · Conversa com a Seth (lote 3) | Fixar e desfixar; fixadas no topo da lista | conversa | sub-conversa (`seth-conversas`) |
| prototipo · Conversa com a Seth (lote 3) | Arquivar e desarquivar; seção Arquivadas | conversa | sub-conversa (`seth-arquivadas-bloco`, `seth-arquivadas`) |
| prototipo · Conversa com a Seth (lote 3) | Marcadores (tags livres) por conversa e filtro por marcador | conversa | sub-conversa (`seth-filtro-marcador`) |
| prototipo · Conversa com a Seth (lote 3) | Pastas (projetos): criar, renomear, apagar (as conversas ficam), mover conversa e filtrar por pasta | conversa | sub-conversa (`seth-pasta-form`, `seth-pastas`, `seth-filtro-pasta`) |
| prototipo · Conversa com a Seth (lote 3) | Exportar a conversa salva em JSON e Markdown (download pelo navegador) | conversa | sub-conversa (`seth-export-json`, `seth-export-md`) |
| prototipo · Conversa com a Seth (lote 3) | Importar JSON exportado (valida; não duplica) | conversa | sub-conversa (`seth-importar-arquivo`) |
| prototipo · Conversa com a Seth (lote 3) | Conversa temporária: não é salva, com aviso visível | conversa | sub-conversa (`seth-temporaria`, `seth-temporaria-aviso`) |
| prototipo · Conversa com a Seth (lote 4, 09/11/2026) | Editar e reenviar, regenerar, trocar de versão ("< 1/2 >") | conversa | sub-conversa (`seth-transcript`, `seth-input`) |
| prototipo · Conversa com a Seth (lote 4) | Ramificar a partir de uma mensagem; mostra a origem da conversa ramificada | conversa | sub-conversa (`seth-origem`) |
| prototipo · Conversa com a Seth (lote 4) | Parar a resposta (botão e Esc); texto parcial marcado como interrompida | conversa | sub-conversa (`seth-parar`) |
| prototipo · Conversa com a Seth (lote 4) | Continuar a última resposta, na mesma mensagem, com marca de continuação | conversa | sub-conversa (`seth-transcript`) |
| prototipo · Conversa com a Seth (lote 4) | Feedback de boa e de ruim resposta, com motivo opcional, salvo na conversa | conversa | sub-conversa (`seth-transcript`) |
| prototipo · Conversa com a Seth (lote 4) | Barra de contexto: caracteres e KB da próxima pergunta contra o limite do painel | conversa | sub-conversa (`seth-contexto`, `seth-contexto-barra`) |
| prototipo · Conversa com a Seth (lote 4) | Copiar a última resposta, pelo botão ou por Ctrl+Shift+C | conversa | sub-conversa (`seth-copiar-ultima`, `seth-copiado`) |
| prototipo · Atalhos de teclado e tema (lote 4) | Lista de atalhos (?), tema claro, escuro ou do sistema, salvo em localStorage | panorama | topo (`atalhos-abrir`, `atalhos-painel`, `tema`) |
| prototipo · Conversa com a Seth | Envio com stream e fallback para o chat inteiro; Enter envia | conversa | sub-conversa (`seth-form`, `seth-input`) |
| prototipo · Conversa com a Seth | Copiar, regerar, exemplos e salvamento automático | conversa | sub-conversa |
| prototipo · Conselho e /conselho-rede | Novo turno: aba, prompt e solicitação de aprovação de envio | conselho | sub-conselho (`promptForm`, `site`, `pergunta`, `btnEnviar`) |
| prototipo · Conselho | Preparar rodada: debate, cadeia ou bateria; participantes e repetições | conselho | sub-conselho (`groupKind`, `chainSites`, `groupRepetitions`, `btnConversa`) |
| prototipo · Conselho | Abas de chat suportadas e catálogo | conselho | sub-conselho (`providerTable`) |
| prototipo · Conselho | Links dos modelos (DeepSeek a Kimi) que abrem a aba | conselho | sub-conselho (`data-alvo`, `/api/abrir`) |
| prototipo · Conselho | Ao entrar na seção, confere os conselheiros e abre só os que faltam | conselho | abrir.js (`/api/abrir`, alvo `conselho`) |
| prototipo · Conselho | Fila de aprovação: aprovar ou recusar cada envio | conselho | sub-conselho (`filaLista`, `filaCount`) |
| prototipo · Conselho | Debates e baterias em andamento | conselho | sub-conselho (`rodadasLista`) |
| prototipo · Conselho | Ferramentas: pedido com aprovação individual (B2 fica como está) | conselho | sub-conselho (`toolForm`, `tool`, `toolArgs`) |
| prototipo · Conselho | Histórico recente | conselho | sub-conselho (`historicoLista`) |
| prototipo · Conselho | Pedidos de ferramentas pendentes | conselho | sub-conselho (`decisaoLista`) |
| prototipo · Conselho | Estado do conselho e atualização | conselho | sub-conselho (`status`) |
| prototipo · Conselho (nova, pedida pelo Humano em 07/11/2026) | Memória compartilhada do Conselho, só leitura do cache: número, data e hora, autor, tipo e texto; filtro por tipo; atualizar | conselho | sub-conselho-memoria (`memoria-lista`, `memoria-tipo`, `memoria-atualizar`, `memoria-resumo`) |
| prototipo · Estado operacional | Unidades, repositório, agenda observada, tarefas da janela e atualizar leitura | sistema | sub-operacao (`refresh-status`) |
| prototipo · Integrações | Estado das unidades de integração, fronteiras e fontes (FONTE) | sistema | sub-integracoes |
| prototipo · Modelos & rota | Capacidades registradas, decisão e ficha do modelo | sistema | sub-modelos |
| prototipo · Manutenção | Próximos e últimos disparos; tarefas | sistema | sub-manutencao |
| casca · barra lateral | Abrir Obsidian, LibreChat e OmniRoute (`/api/abrir`, lista fixa) | sistema | servicos-locais |
| prototipo · Nova versão · Corpo operacional | Fotografia de serviços e fotografar agora | sistema | sub-nv-corpo (`nv-fotografar`, `nv-corpo-lista`) |
| prototipo · Nova versão · Metacognição | Classificar um pedido; último registro da sombra do gateway | sistema | sub-nv-metacognicao (`nv-classificar`, `nv-sombra`) |
| prototipo · Nova versão · Conexões | Estado por caminho | sistema | sub-nv-conexoes |
| prototipo · Nova versão · Conexões | Gravar e remover chave de API (campo `password`; nunca volta) | sistema | sub-nv-conexoes (`nv-api-gravar`, `nv-api-remover`) |
| prototipo · Nova versão · Conexões | Adicionar provedor pelo mesmo formato | sistema | sub-nv-conexoes (`nv-add-salvar`) |
| prototipo · Nova versão · Conexões | Testar rotas do orçamento e cancelar o teste | sistema | sub-nv-conexoes (`nv-red-testar`, `nv-red-cancelar`) |
| prototipo · Memória & mapas | A memória como mapa; Começar no vault; Brain Atlas; Canvas 2D; Vistas da Base; Linha do tempo | conhecimento | sub-memoria (`memory-state`) |
| prototipo · Grafo do vault | Visualizador; modos Relações, Regiões e Brain Atlas; abrir nota por número | conhecimento | sub-grafo (`grafo-form`, `grafo-entrada`, `grafo-svg`) |
| prototipo · Documentação viva | Busca na documentação (agora pela busca única); estado e mudanças; memórias e documentos; mapas navegáveis | conhecimento | sub-documentacao (`conhecimento-busca`, `conhecimento-consulta`) |
| prototipo · Nova versão · Alexandria | Pacote de evidência (consultar) e sugerir skills, pela busca única | conhecimento | busca única (`conhecimento-busca`, `conhecimento-consulta`, `conhecimento-escopo`, `nv-consultar`, `nv-skills`) |
| prototipo · Nova versão · Alexandria | Estado do índice; reindexar a partir do HEAD; criar pastas e indexar | conhecimento | sub-nv-alexandria (`nv-indexar`, `nv-iniciar`) |
| prototipo · Nova versão · Acervo e fontes | Enviar arquivo (md, txt, html, pdf até 25 MB), importar pasta, processar pendentes, baixar endereço https | conhecimento | sub-nv-acervo (`nv-acv-enviar`, `nv-acv-importar`, `nv-acv-processar`, `nv-acv-baixar`) |
| prototipo · Nova versão · Acervo e fontes | Lista de fontes com direitos e transições editoriais (revisar, contestar, arquivar, rejeitar) | conhecimento | sub-nv-acervo (`nv-acv-vazio`) |
| prototipo · Nova versão · Acervo e fontes | Busca externa (Wikipédia) e guardar resultado, pela busca única no escopo "fora" | conhecimento | busca única (`conhecimento-escopo`, `nv-ext-lista`, `nv-ext-nota`) |
| prototipo · diálogo do vault | Leitura do item do vault (`/api/vault/item`), também usada por Panorama | conhecimento | vault-dialog |
| /operator_console | Página própria (tela antiga) | qualidade | sub-operator-console (redirect) |
| prototipo · Operator Console | Abrir pacote; abas Visão, Capacidades, Revisões e Drift; frescor e integridade | qualidade | sub-operator-console (`package`, `state`, `freshness`, `integrity`) — sem iframe |
| prototipo · Qualidade de LLM | Indicadores medidos; sem medição sai como não medido | qualidade | sub-qualidade (`qualidade-lista`, `qualidade-titulo`) |
| prototipo · Qualidade de LLM | Medir recuperação, medir busca por sentido, medir contexto efetivo (modelo, tarefa, raciocínio) | qualidade | sub-qualidade (`medir-recuperacao`, `medir-semantica`, `medir-contexto`, `medir-modelo`) |
| prototipo · SDD | Componentes ancorados e estado da âncora | qualidade | sub-sdd (`sdd-lista`, `sdd-titulo`) |
| prototipo · SDD | Âncora e critérios por componente; projetos externos de `config/sdd` | qualidade | sub-sdd |
| prototipo · Lacunas | Declarado e não confirmado (canon); lista de lacunas | qualidade | sub-lacunas (`lacunas-canon`, `lacunas-lista`, `lacunas-total`) |
| prototipo · Nova versão · Avaliação | O que falta; margem e tetos (política); revisão do reservado | qualidade | sub-nv-avaliacao (`nv-pol-salvar`, `nv-res-revisar`, `nv-res-ver`) |
| prototipo · Nova versão · Avaliação | Nova rodada (avaliar, cancelar, medir só a busca); última rodada | qualidade | sub-nv-avaliacao (`nv-run-rodar`, `nv-run-cancelar`, `nv-run-recuperacao`, `nv-out-run`) |
| prototipo · Nova versão · Sentidos | Fala → texto: medir o ouvido; tabela de motores | qualidade | sub-nv-sentidos (`nv-sen-medir`, `nv-sen-wrap`) |
| prototipo · Nova versão · Orçamento e eventos | Categorias e tetos (local, gratuito, assinatura, pago; chamadas, tokens, timeout, R$); salvar | custos | sub-nv-orcamento (`nv-orc-salvar`, `nv-orc-reais`) |
| prototipo · Nova versão · Orçamento e eventos | Últimos eventos do ledger | custos | sub-nv-orcamento (`nv-eventos-titulo`) |
| prototipo · Nova versão · Conexões | Tarifas e modelo por provedor (US$/M tokens de entrada e saída, câmbio, data, fonte); salvar modelo e tarifa | custos | sub-nv-tarifas (`nv-api-provedor`, `nv-api-modelo`, `nv-tar-entrada`, `nv-api-ajustar`) |
| canon (História, 11/11/2026) | Índice de tomos e textos de `historia/`, com o estado de cada texto | historia | sub-historia (`historia-indice`, `historia-meta`) |
| canon (História) | Leitura de um texto: marcas de origem, frontmatter e corpo | historia | sub-historia (`historia-corpo`, `historia-estado`) |
| canon (História) | Botão Ouvir: lê o corpo com a voz do sistema e diz se falou ou não | historia | sub-historia (`historia-ouvir`, `historia-ouvir-estado`) |
| casca | Barra lateral com as oito entradas e botão de recolher | casca | não é seção |
| casca | Breadcrumb, chip LOCAL, nota "O Humano no centro" e rodapé | casca | não é seção |
| casca | Busca "Buscar neste mapa…" (filtra os cartões da seção aberta) | casca | não é seção |
| casca | Diálogo de evidência (`evidence-dialog`) | casca | usado por Panorama e Sistema |
| retirado | Submenus recolhíveis (Sistema, Memória e conhecimento, Qualidade, Nova versão) | retirado | substituídos pelas sete seções e pelas abas internas |
| retirado | Páginas próprias de `/index.html`, `/frentes`, `/operator_console` e `/conselho-rede` | redirect | cobertas pelas linhas acima |
| retirado | Iframe da Operator Console | retirado | o conteúdo vai para `sub-operator-console` |

## Critérios de aceite

- [ ] as telas antigas redirecionam para a seção certa: `/`, `/index.html` e `/frentes` para `/prototipo#panorama`; `/operator_console` para `/prototipo#qualidade`; `/conselho-rede` e `/conselho-rede/` para `/prototipo#conselho`
- [ ] todos os caminhos `/api/*` chamados pelo JS existem no servidor; a rota nova `/api/conselho/memoria` é somente leitura do cache e está documentada
- [ ] a conversa salva é validada e devolvida com `schema_version` e `id`, e regrava com o mesmo id sem duplicar arquivo; conteúdo de mensagem até 65536 caracteres passa na validação, respeitado o teto total de 262144 bytes por requisição
- [ ] a CSP das respostas continua com `script-src 'self'` e `style-src 'self'`
- [ ] o `/prototipo` tem oito seções (panorama, conversa, conselho, sistema, conhecimento, historia, custos e qualidade) e um botão de menu para cada uma
- [ ] cada tela antiga tem um subpainel `sub-<nome>` dentro da seção de destino do mapeamento
- [ ] cada função do mapeamento existe na tela, pelo id, em `prototipo.html` ou `prototipo.js`
- [ ] o `/prototipo` escolhe a seção pelo hash, troca ao mudar o hash e cai em panorama com hash desconhecido
- [ ] o HTML de `/prototipo` não tem atributo `style=`, tag `style` nem script com código inline
- [ ] o `/prototipo` carrega uma só folha de estilo, `prototipo.css`, e as folhas antigas respondem 404
- [ ] cores e tipografia estão em tokens no `:root` de `prototipo.css`, e nenhuma cor hexadecimal aparece fora dele
- [ ] toda classe usada no HTML de `/prototipo` tem regra em `prototipo.css`
- [ ] os scripts de `/prototipo` não declaram o mesmo nome no escopo global
- [ ] cada seção que consome API tem marcadores de estado carregando, vazio e erro
- [ ] o Conhecimento tem uma só caixa de busca, que serve à Alexandria, ao Acervo e à Wiki
- [ ] o Custos tem orçamento, eventos e tarifas, e cada controle chama uma ação de `nova-versao/executar` que já existe
- [ ] a Operator Console fica na seção Qualidade sem iframe
- [ ] o Conselho não envia nem executa nada sem aprovação individual
- [ ] a Conversa mantém o stream com fallback para o chat inteiro
- [ ] os ids preservados e as classes mapeadas pela PR 940 continuam no HTML
- [ ] a página não tem script inline por causa da CSP
- [ ] leituras de API recusam origem cruzada
- [ ] a verificação de proposta é só leitura de origem local
- [ ] o indicador sem medição sai como não medido
- [ ] a execução do SDD recusa ação e componente fora da lista
- [ ] a execução do SDD recusa comando fora do padrão pytest
- [ ] a aba SDD lista e roda projetos externos de config/sdd e recusa o que não está lá
- [ ] `GET /api/historia` lista os tomos e os textos de `historia/` com o frontmatter (tomo, título, período, autor, estado e protocolo), sem o corpo do texto
- [ ] `GET /api/historia/texto` devolve o frontmatter separado e o corpo do texto; `tomo` e `texto` têm formato fixo e o cliente não escolhe caminho: fora do formato, 400; inexistente ou link para fora de `historia/`, 404
- [ ] `historia/` ausente ou sem texto dá estado `vazio` com 200, e não erro
- [ ] as leituras da História e o Ouvir recusam origem cruzada com 403; o Ouvir aceita só JSON da própria origem e corpo até 512 bytes
- [ ] `historia.js` é arquivo externo servido em `/historia.js`, e a seção História não tem script nem estilo inline
- [ ] o Ouvir manda só o corpo do texto, sem o frontmatter, para `scripts/agata_falar.py --arquivo`, e responde `falou` verdadeiro só com código de saída 0
- [ ] com a voz do sistema sem resposta, o Ouvir responde `falou` falso com motivo que diz `não falei`
- [ ] uma fala por vez: com outra em curso, o Ouvir responde 429 e não chama a voz; texto inexistente não chama a voz
- [ ] o botão Ouvir chama `POST /api/historia/ouvir` com `tomo` e `texto` do texto aberto, fica desligado sem texto aberto e mostra se falou ou não
- [ ] o texto da História vira nós com createElement e createTextNode: `historia.js` não usa innerHTML, outerHTML, insertAdjacentHTML, document.write nem eval, e tag HTML no texto sai como texto
- [ ] as marcas `[medido]`, `[relato]` e `[inferência]` viram etiquetas com classe própria e cor por token do `:root`
- [ ] o `/prototipo` tem a seção `historia` depois de `conhecimento`, escondida até ser escolhida, com estados carregando, vazio e erro
- [ ] o texto 1 do Tomo I, em `historia/` do checkout, aparece na lista e tem as marcas de origem
- [ ] `scripts/perimetro/p08_quarentena.sh` põe `historia/` na quarentena do P-8, e a História não muda sem assinatura
- [ ] os arquivos da História não têm emoji
- [ ] a medição recusa ação e modelo fora da lista e roda com argumentos fixos
- [ ] o indicador de recuperação usa a medição salva e volta a não medido sem ela
- [ ] a nova versão recusa ação, consulta e orçamento fora do contrato e registra a mudança de orçamento
- [ ] a chave gravada pelo painel não volta na resposta nem no estado
- [ ] as páginas da nova versão não têm estilo inline porque a CSP o bloqueia
- [ ] a avaliação pelo painel respeita revisão, política e não expõe o gabarito no estado
- [ ] o upload de fonte aceita só md e recusa o resto, sem deixar temporário
- [ ] o corpo de POST vai até 64 KB e recusa acima
- MEDIDO, manual (sem comando; fora do drift automático, que só conta caixas `- [ ]` e não tem formato para critério manual): verificação no navegador. Medição de 07/11/2026, 12h33 (Brasília), por CDP no Chromium headless, com clique de mouse no menu, perfil próprio em `~/agata-documentacao/painel-unificado/perfil-chromium` (fora do repositório), worktree servida em 127.0.0.1:20247; registro em `~/agata-documentacao/painel-unificado/verificacao-critério-35.json`; o medidor é um script temporário da sessão, fora do repositório. Medido: `/prototipo` abre no Panorama sem hash; em cada uma das sete seções, o clique no menu troca o hash (`#panorama`, `#conversa`, `#conselho`, `#sistema`, `#conhecimento`, `#custos`, `#qualidade`), a seção ativa e o breadcrumb; cada seção tem título h2 visível e texto visível (de 16 a 169 elementos com texto); nenhuma violação de CSP no console nem no evento `securitypolicyviolation`. Erros fora de CSP: 404 de `/favicon.ico` na carga; 403 de `POST /api/abrir` ao entrar em Conselho, porque o servidor de worktree fixa a origem permitida na porta 20146 (`ALLOWED_ORIGIN` é lido no import, e `serve_worktree.py` troca a porta depois). Não é CSP. Medição anterior, com capturas em 1440 px e 390 px: visto nas capturas Panorama, Conhecimento (1440 e 390 px), Conselho, Custos e Qualidade (Operator Console); `#conselho`, hash desconhecido, troca de aba (Qualidade > SDD) e escopo da busca única; `/conselho-rede` e `/operator_console/` levam ao hash certo. Não medido: Conversa e Sistema não foram revistos visualmente; estados carregando, vazio e erro não apareceram visíveis, então não foram vistos sob falha real da API; rolagem horizontal do menu em 390 px; Operator Console com pacote carregado; interação com a Seth e com o Conselho.
- [ ] `GET /api/conselho/memoria` devolve as últimas entradas do cache, mais recentes primeiro, com número, data e hora, autor, tipo e texto
- [ ] a memória do Conselho aceita `n` de 1 a 200 (padrão 40), corta acima de 200 e recusa valor não numérico ou zero
- [ ] a rota da memória do Conselho não aceita caminho de arquivo do cliente e não escreve no cache
- [ ] cache ausente ou sem entradas dá estado `vazio` explícito, sem erro
- [ ] o texto da memória do Conselho sai pelo mesmo filtro de dado pessoal e de segredo da gravação
- [ ] a rota da memória do Conselho recusa origem cruzada, como as outras leituras de API
- [ ] a aba Memória compartilhada fica dentro da seção Conselho, tem estados carregando, vazio e erro, e monta o texto do cache só com textContent
- [ ] a busca de conversas (`GET /api/seth/conversas/busca?q=`) procura em títulos e mensagens das conversas salvas, sem serviço externo, e devolve trecho, número da mensagem e data; termo vazio ou acima de 120 caracteres responde 400 com motivo
- [ ] a busca ignora caixa e acento (`acao` acha `AÇÃO`), o trecho mostra o contexto da ocorrência, e a busca devolve até 50 resultados
- [ ] fixar, arquivar e marcadores ficam em `organizacao.json` dentro da pasta de conversas e não reescrevem a conversa; conversa antiga, sem esse arquivo, abre com os valores padrão
- [ ] a conversa fixada vem antes das outras; a arquivada sai da lista principal e aparece na seção Arquivadas, com Desarquivar
- [ ] marcadores têm até 10 por conversa e até 24 caracteres (letras, números, espaço e hífen); pasta só aceita pasta existente; a recusa diz o motivo em português
- [ ] pastas: criar, renomear e apagar; apagar pasta não apaga conversa, que fica sem pasta; limite de 50 pastas e nome de até 60 caracteres
- [ ] a lista filtra por pasta e por marcador, e move a conversa para outra pasta pelo seletor da própria conversa
- [ ] a exportação baixa a conversa salva em JSON ou Markdown por `GET /api/seth/conversa/exportar`, com `Content-Disposition: attachment` e nome de arquivo só com o id; formato ou id inválido recusam
- [ ] a importação (`POST /api/seth/conversa/importar`) valida formato, versão e conversa, recusa arquivo acima de 263168 bytes com 413 e não duplica: id ou origem_id já conhecido responde `ja_existe` sem gravar
- [ ] a conversa temporária não é gravada, não aparece na lista e mostra na tela que não é salva; não tem exportação
- [ ] as rotas novas de conversa recusam origem cruzada, e a organização recusa pedido acima de 4096 bytes com 413
- [ ] organização ilegível não é sobrescrita: a lista avisa na tela e a escrita responde 409 sem gravar
- [ ] a busca abre a conversa na mensagem indicada e destaca essa mensagem; sem busca, a lista volta; a lista mostra quantas faltam quando passa de 200
- [ ] os controles novos da Conversa (busca, filtros, pastas, importação, exportação e temporária) têm id em `prototipo.html`, com limite de tamanho nos campos e as constantes da UI iguais às do servidor; a seção continua sem `style=` nem atributo `on*`
- [ ] apagar uma conversa a move para `.lixeira/<id>-<AAAAMMDD-HHMMSS>.json`, com os mesmos bytes, e leva a entrada de organização junto; ela sai da lista principal
- [ ] `GET /api/seth/lixeira` lista o título, a data de apagar e a contagem de mensagens, sem o texto delas, com `schema_version`
- [ ] restaurar devolve a conversa ao lugar dela com a organização; recusa id repetido (409), nome inválido (400) e item fora da lixeira (404) sem mexer na lixeira
- [ ] a purga apaga de vez só por pedido manual (`POST /api/seth/lixeira/purgar`); listar, buscar e abrir a lixeira não apagam nada
- [ ] a seção Lixeira da aba Conversa mostra restaurar e apagar de vez; apagar de vez pede confirmação em dois cliques e só então chama a purga
- [ ] as escritas de conversa (salvar, apagar, organizar, pastas, importar, restaurar e purgar) respondem 403 sem `Origin` igual ao do painel nem `Sec-Fetch-Site: same-origin`, e não gravam nada
- [ ] um cabeçalho que diz outra origem (cross-site, `Origin` de outro site ou `null`) recusa a escrita com 403, mesmo com a origem do painel no outro cabeçalho; a origem do painel e same-origin passam
- [ ] cada pedido de escrita de conversa, inclusive o recusado, acrescenta uma linha em `.registro.jsonl` com hora, rota, id e status, e nenhuma linha traz título, texto ou marcador
- [ ] o registro só acrescenta linhas, e se ele não puder ser escrito a ação segue
- [ ] salvar uma conversa importada mantém `origem`, `origem_id`, `titulo_original`, `data_original`, `importado_em` e `id`, e o salvar não reescreve a origem já gravada
- [ ] salvar pela API uma conversa importada, com id ou sem id, não cria segundo arquivo
- [ ] uma mensagem reeditada perde a marca de origem dela; a que continua no mesmo lugar, com o mesmo papel e texto, mantém `criada` e `origem_id`
- [ ] importar uma conversa que está na lixeira não duplica: responde `ja_existe` com `lixeira: true`
- [ ] a listagem conta os arquivos de conversa ilegíveis em `ilegiveis`, sem apagá-los nem esconder a lista; a tela mostra a contagem
- [ ] apagar só sai da tela quando o painel confirma; com erro, a mensagem diz o motivo e a conversa aberta continua
- [ ] enquanto a Seth responde, a tela não troca de conversa, não abre Nova conversa e não liga a temporária: avisa e espera; depois da resposta, volta a funcionar
- [ ] salvar grava o id e o aviso na conversa de origem, e a tela só é repintada se ela ainda é a aberta
- [ ] a lixeira fora do ar não derruba a lista de conversas, e a lixeira vazia diz que está vazia
- [ ] editar uma mensagem e reenviar, ou regenerar uma resposta, não apaga a resposta antiga: ela vira outra versão da conversa, navegável com "< 1/2 >", e as setas seguem o ramo escolhido
- [ ] ramificar a partir de qualquer mensagem cria conversa nova com o histórico até ali, guarda de onde saiu e mostra a origem; em conversa temporária o botão não aparece
- [ ] a árvore de ramos é validada (pai antes do filho, id no formato, papel conhecido, até 400 nós e 200 mensagens no caminho); árvore inválida responde 400 e nada é gravado
- [ ] conversa sem ramo continua gravada no formato de sempre, conversa salva antes do lote 4 abre igual, e árvore ilegível na leitura cai no caminho de mensagens
- [ ] renomear uma conversa com ramo grava a árvore inteira, sem perder as versões
- [ ] o botão Parar e a tecla Esc cancelam o fetch do stream; o texto que já chegou fica na tela e na conversa salva, marcado como interrompida, sem repetir a pergunta
- [ ] Parar antes do primeiro texto deixa a resposta vazia marcada como interrompida; erro no meio do stream também mantém o texto recebido marcado, e erro sem texto devolve a pergunta ao campo
- [ ] continuar pede à Seth com a mensagem "Continue de onde parou" e anexa o texto à mesma resposta, com marca de continuação; sem texto na resposta, o botão não aparece
- [ ] o feedback de boa resposta e de resposta ruim, com motivo opcional, fica salvo na conversa e não sai do navegador; em conversa temporária não grava
- [ ] a barra de contexto mostra, em português simples, quantos caracteres e KB a próxima pergunta leva, o limite do painel e quantas mensagens vão
- [ ] atalhos de teclado: ? mostra a lista (Esc fecha), Ctrl+Shift+O começa conversa nova, Ctrl+Shift+C copia a última resposta, / foca a busca; atalhos de uma tecla não disparam dentro de campo de texto
- [ ] o tema escuro é o padrão; claro e sistema trocam a paleta pelos tokens do :root; a escolha fica em localStorage com try/catch, e sem armazenamento a tela segue
- [ ] a exportação JSON leva os ramos e a origem; o Markdown traz só o caminho e avisa; a importação preserva os ramos sem duplicar; a busca e a contagem da lista veem só o caminho ativo
- [ ] os controles novos têm id em `prototipo.html`; a Conversa continua sem `style=` nem atributo `on*`, e o JS da Conversa não usa innerHTML
- [ ] a paleta clara é gerada dentro do mesmo `:root`: nenhuma cor literal fora dele, nenhum `var()` sem definição, e toda classe do HTML tem regra de estilo
- [ ] apagar uma conversa com ramos leva a árvore para a Lixeira junto com o resto, e restaurar devolve as versões de outros ramos com a conversa
- [ ] `GET /api/importantes` devolve `itens` com abertos primeiro, `contagem` e `estado`; arquivo ausente vale `vazio` e arquivo fora do formato vale `ilegivel`
- [ ] criar, marcar feito, descartar, reabrir e editar gravam o arquivo local por troca atômica; descartado fica guardado e nenhum item é apagado de fato
- [ ] texto recusado (vazio, acima de 4000 caracteres, com caractere nulo) ou campo fora do contrato responde 400 e não grava nada
- [ ] `Trazer do Conselho` lê o cache sem escrever nele, traz só as entradas `IMPORTANTE`, não duplica nem traz de novo a entrada descartada, e não traz entrada com segredo
- [ ] as escritas de importantes respondem 403 sem origem do painel ou com origem de outro site, 413 acima de 4096 bytes, e cada pedido, inclusive o recusado, gera uma linha no registro sem texto
- [ ] a aba Importantes e o cartão do Panorama mostram estados carregando, vazio e erro, e não mostram lista antiga como atual quando a leitura falha ou o arquivo é ilegível
- [ ] a aba envia criar, marcar, reabrir, descartar, editar e trazer pelas rotas de importantes, e mostra o motivo da recusa (403, 404, 409 e 500)
- [ ] o texto de um item sai como texto puro, sem innerHTML, e o bloco novo não tem `style=`, `on*` nem cor literal fora de `:root`
- [ ] a tela de Importantes chama só rotas que existem no servidor, e as quatro rotas estão em `IMPORTANTES_ROTAS`
- [ ] os arquivos da entrega de importantes (tela, módulo, testes e spec) não têm emoji
- [ ] o botão Ouvir de cada resposta da Seth manda o texto a `POST /api/seth/ouvir`; a mensagem do usuário não tem Ouvir
- [ ] o resultado do Ouvir diz falei ou NÃO falei com o motivo que o painel devolve, em português simples, e nunca mostra sucesso quando não falou
- [ ] a fala é por parágrafo, com a voz do sistema (`pt_BR-agata-last`), usando o preparo e o serviço de `scripts/agata_falar.py`; modelo diferente no piper não fala
- [ ] Parar interrompe a leitura entre trechos e não pede o trecho seguinte; sem leitura em curso, Parar e Esc não chamam o painel
- [ ] o piper só é desligado por quem o ligou, e ler o estado da voz não liga o serviço
- [ ] uma leitura por vez no painel: a Seth e a História dividem a trava, e a segunda leitura responde 429
- [ ] as rotas de voz recusam origem cruzada com 403, respondem 413 acima do tamanho e 400 para JSON ruim; o GET do estado só lê
- [ ] o ditado grava o microfone pelo navegador, manda o áudio só à rota do painel, e o texto entra no campo sem ser enviado à Seth
- [ ] o ditado para em 60 segundos, recusa áudio acima de 2 MB e diz em português o erro de permissão, de microfone, de ouvido fora do ar e de áudio sem fala
- [ ] a rota de ditado repassa o áudio só ao `servidor_ouvido` local (127.0.0.1:20137), em multipart, e devolve `texto` limitado a 4000 caracteres
- [ ] modo conversa vem desligado, guarda a preferência com try/catch, lê cada resposta concluída e, com leitura em curso, para a atual e lê a mais nova depois
- [ ] a linha `voz` da página Sentidos mostra piper no ar ou parado, o último uso e aviso se o modelo não é a voz do sistema; só lê
- [ ] a CSP do painel segue igual (sem `media-src`); o JS e o HTML da voz são externos ou de texto, sem HTML dinâmico, sem atributo inline e sem emoji
- [ ] a preferência do modo conversa fica fora do bloco da Conversa, e o bloco da Conversa não guarda nada em localStorage

## Desenho e alternativas

- Mesmo servidor, `http.server` da biblioteca padrão, e os mesmos módulos. Sem framework.
- Uma tela com sete seções e subpainéis. Alternativa descartada: manter as 25 páginas e mudar só o menu. Não atende "uma tela só" e mantém 25 pontos de estado.
- Uma folha de estilo. Alternativa descartada: manter `nova_versao.css` separado. Dois conjuntos de tokens, e a CSP trata cada arquivo como fonte separada.
- Operator Console sem iframe: o iframe tem documento, CSS e JS próprios, e não compartilha tokens. O JS da console (`operator_console/app.js`) é isolado antes de entrar na página (ver Implementação). Se o isolamento falhar na verificação, a alternativa é manter o iframe com `operator_console/index.html` servido; isso fica registrado como risco.
- Globais: cada script de tela fica em IIFE ou usa nomes únicos. O teste de globais impede a repetição.
- Hash no lugar de rota nova: o redirect já usa hash (`/prototipo#conselho`). A mudança é só fazer o JS ler o hash.
- Lote 4: a conversa é uma árvore de nós com `pai` (um nó por mensagem; versão nova é irmão da antiga). Alternativa descartada: listas de versões por posição, com a cauda de cada versão guardada à parte. A cauda de uma versão teria ramos aninhados, e a navegação entre eles ficaria difícil de conferir.

## Implementação e testes

Ordem de aplicação (cada passo é uma proposta com par `.diff` e `APROVADO`, pelo fluxo de propostas):

0. A PR 940 entra antes (base d1b6b4f7).
1. `server.py`: redirects das telas antigas e tabela `_ASSETS` sem os ativos retirados.
2. `prototipo.html`: sete seções, subpainéis `sub-<nome>`, menu de sete botões, sem iframe. Os ids de `test_csp_prototipo.py::IDS_PRESERVADOS` continuam.
3. `prototipo.js`: roteamento por hash (`location.hash` e `hashchange`), seção padrão `panorama`, abas internas, estados `carregando`, `vazio` e `erro`, e nomes únicos no escopo global (`refresh` de Panorama passa a ter nome próprio).
4. `conselho-rede/app.js` e `operator_console/app.js`: sem declarações de topo (IIFE), mesmas chamadas de API.
5. `prototipo.css`: tokens em `:root`; absorve `nova_versao.css`, `styles.css`, `conselho-rede/style.css` e `operator_console/style.css`; sem cor literal fora de `:root`.
6. Remoção de `index.html`, `app.js`, `styles.css`, `frentes.html`, `frentes.js`, `nova_versao.css`, `conselho-rede/index.html`, `conselho-rede/style.css`, `operator_console/index.html`, `operator_console/style.css`; atualização da seção Código.

Testes novos: `redesign/painel_operacional/test_painel_unificado.py`, com as classes `RotasDaTelaUnicaTests` e `TelaUnicaTests`. Não existe hoje. Entra na seção Código quando for criado. Os critérios novos apontam para ele em `spec/acceptance.json`; até lá, esses alvos falham (esperado).

Testes existentes reescritos, porque o contrato mudou (cobertura mantida no novo teste):

- `test_menu_painel.py`: 25 botões de página e 4 grupos viram 7 botões de seção.
- `test_chat_stream_rota.py`: `Location` de `/` passa a `/prototipo#panorama`; `/index.html` deixa de responder 200.
- `test_frentes.py`: a página `/frentes` vira redirect; `/frentes.js` sai. `/api/frentes` continua testado.
- `test_qualidade_llm.py`: `id="page-qualidade"` e `data-page="qualidade"` viram o subpainel e o botão novos.
- `test_sdd_painel.py`: `id="page-sdd"` e `data-page="sdd"` viram os novos.
- `test_chat_ui.py`: o marcador da seção Conversa muda para a seção nova.
- `test_nova_versao_painel.py`: o teste de estilo inline para de exigir o link de `nova_versao.css` e passa a checar o arquivo único; a contagem de 8 `nv-page` vira a de subpainéis.

Testes que continuam como estão: `test_csp_prototipo.py`, `test_conselho_rede.py`, `test_painel.py`, `test_medicoes_painel.py`, `test_relay_catalog.py`, `test_chat_stream.py`, e os demais que testam só API.

Comando da suíte: `python3 -m pytest -q redesign/painel_operacional`, com pytest 9.2.0 (a versão do CI).

Testes do lote de proteção (09/11/2026): `test_conversas_protege.py` (novo: lixeira, escrita com origem, registro, origem preservada ao salvar e arquivos ilegíveis, com servidor numa porta livre) e `test_chat_ui.py::ConversaProtecao` (tela: apagar, bloqueio durante a resposta, salvar na conversa de origem, lixeira e contagem de ilegíveis, em node com DOM mínimo). O harness de `test_chat_ui.py` ganhou a lixeira; `sethSalvar` é exposta só na cópia em memória do arquivo, durante o teste (uma linha antes do fim da IIFE), sem hook no código de produção.

Importantes (11/11/2026): `test_importantes.py` cobre o armazém e as rotas (sem navegador; o arquivo e o registro vão para um diretório temporário). `test_importantes_ui.py` roda `prototipo.js` em node, com um DOM mínimo montado no próprio teste e um fetch roteirizado, e confere em texto o bloco novo (sem innerHTML, style nem on*). A lista de subpainéis do Panorama em `test_painel_unificado.py` ganhou `importantes` (única mudança nesse teste).

## Migração e reversão

- Sem migração de dados. O painel não guarda estado além do cache em `~/.cache/agata/painel/`.
- Links antigos continuam funcionando: redirect para a seção certa.
- Reversão: `git revert` do commit de aplicação. Os arquivos retirados (HTML e CSS) voltam com o revert.
- Ordem de reversão: se a aplicação tiver ido em mais de um passo, reverter do último para o primeiro.
- Lote 3 (09/11/2026): `organizacao.json` nasce só quando alguém fixa, arquiva, marca ou põe em pasta uma conversa. Sem ele, as conversas valem o padrão. Reverter o código deixa o arquivo ignorado; apagá-lo desfaz a organização sem tocar nas conversas.
- Proteção (09/11/2026): a pasta `.lixeira/` e o `.registro.jsonl` nascem no primeiro uso. Reverter o código deixa a lixeira fora da lista; as conversas que estiverem nela voltam à mão (mover `.lixeira/<id>-<data>.json` para `<id>.json`). A chave `lixeira` de `organizacao.json` é ignorada pelo código antigo.
- Lote 4 (09/11/2026): sem migração. Conversa antiga abre igual. Uma conversa ganha `arvore` só quando tem ramo; enquanto não tem, grava como antes. Reverter o código deixa de mostrar as versões de outros ramos; o caminho continua aberto em versão anterior (ver Riscos).
- Importantes (11/11/2026): o arquivo `~/.cache/agata/painel-importantes.json` e o registro nascem no primeiro uso. Reverter o código deixa o arquivo sem uso; apagá-lo perde a lista (não há outra cópia). Reverter a aba deixa a lista só no arquivo, sem tela.

## Riscos e dependências

- A PR 940 precisa estar na base. Sem ela, `prototipo.html` tem 9 `style=`.
- Globais repetidos: `refresh` (prototipo.js e conselho-rede/app.js) e `$` (conselho-rede/app.js e operator_console/app.js). Medido por leitura, não no navegador. O teste de globais fica como critério.
- Operator Console sem iframe pode quebrar se o JS depender do documento próprio. Risco aceito, com a alternativa descrita em Desenho.
- Os alvos de `spec/acceptance.json` que apontam para `test_painel_unificado.py` falham até a aplicação. Isso é o estado esperado de uma spec antes da implementação.
- Decidido pelo Humano em 07/11/2026: a busca da documentação (wiki) entra na busca única de Conhecimento (Alexandria, Acervo e Wiki).
- Decidido pelo Humano em 07/11/2026: a barra lateral, o cabeçalho e o chip LOCAL ficam fora das sete seções, como casca registrada.
- A verificação no navegador foi feita em 07/11/2026 (critério 35), com o que está medido e o que não foi medido listado ali. Não é aceite visual do Humano.
- `pytest` precisa estar disponível. Sem ele, a execução devolve não medido, não falha em silêncio.
- Importantes (11/11/2026): o texto digitado pelo Humano fica local, sem filtro de segredo (como as conversas); só o texto trazido do cache passa por `filtrar`. "Trazer do Conselho" depende de a entrada começar com `IMPORTANTE`: é convenção de texto do cache, não campo do esquema.
- Proteção (09/11/2026): cliente local que escreve sem cabeçalho (curl, script) passa a receber 403 em toda escrita de conversa. O chat (`/api/seth/chat` e `/api/seth/chat/stream`) não mudou. Salvar uma conversa com um `id` que está na lixeira recria o arquivo com esse id; a restauração depois responde 409 (nada se perde).
- Lote 4 (09/11/2026), Parar e o verificador: o gateway (`redesign/router/seth_gateway.py`) não mudou, e o verificador ainda segura o stream das rotas `seth-*` até o fim. Com a cadeia real, Parar pode não cortar nada visível. Os testes de Parar usam stream falso que espera. Não medido no navegador com a cadeia real neste lote.
- Lote 4, estado `interrompida`: hoje é o campo `interrompida: true` na resposta. A proposta `chat-stream-verificar-depois-09-11` (sem assinatura) usa `verificacao.estado = interrompida` (seção 3.4). Hoje só este lote está no código; a proposta não foi aplicada. Quando ela for aplicada, uma das duas formas precisa ser convertida na outra. Pendência para o Humano decidir a ordem.
- Lote 4, reversão: a conversa com ramo grava também `mensagens` (o caminho). Uma versão anterior abre o caminho, mas não vê os ramos; se ela gravar a conversa de novo, os ramos saem. Antes de reverter, exportar em JSON (o JSON leva `arvore`).
- Lote 4, feedback sem emoji: os botões são "Útil" e "Não útil", com rótulo acessível "Resposta útil" e "Resposta não útil" e o mesmo título. Decisão E-2 do Humano (16/10): o Agata não usa emoji. A nota gravada continua "bom" (útil) e "ruim" (não útil); o teste de emoji cobre HTML, CSS e JS da tela.
- Lote 4, atalhos: o navegador pode reservar algum atalho (por exemplo, Ctrl+Shift+C em alguns navegadores). Medido só em teste de DOM e em Chromium headless, sem janela de navegador.
- Lote 4, tema claro: a paleta clara é gerada por inversão de luminosidade das cores escuras (pares `--luz-*` no `:root`; a geração foi feita por um script local, fora do repositório). Não há medição de contraste por ferramenta; as capturas mostram o estado, não aprovam.

## Código

- `server.py`
- `armazem.py`
- `relogio.py`
- `conselho_rede.py`
- `relay_catalog.py`
- `qualidade_llm.py`
- `sdd_painel.py`
- `medicoes_painel.py`
- `nova_versao_painel.py`
- `chat_stream.py`
- `nova_versao.js`
- `abrir.js`
- `prototipo.js`
- `prototipo.html`
- `prototipo.css`
- `README.md`
- `test_painel.py`
- `test_qualidade_llm.py`
- `test_sdd_painel.py`
- `test_menu_painel.py`
- `test_medicoes_painel.py`
- `test_nova_versao_painel.py`
- `test_relay_catalog.py`
- `test_conselho_rede.py`
- `test_csp_prototipo.py`
- `test_chat_stream.py`
- `test_chat_stream_rota.py`
- `test_painel_unificado.py`
- `test_conversas_lote3.py`
- `test_conversas_protege.py`
- `test_conversas_lote4.py`
- `test_chat_ui.py`
- `test_frentes.py`
- `importantes.py`
- `test_importantes.py`
- `test_importantes_ui.py`
- `historia_painel.py`
- `historia.js`
- `test_historia.py`
- `seth_voz.py`
- `seth_ditado.py`
- `test_seth_voz.py`
- `test_seth_ditado.py`
- `test_voz_ui.py`
- `conselho-rede/`
- `relay-extension-v2/`
- `operator_console/`
- `assets/`
