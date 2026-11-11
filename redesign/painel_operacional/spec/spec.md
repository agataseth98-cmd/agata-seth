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

- Uma tela, `/prototipo`, com sete seções: `panorama`, `conversa`, `conselho`, `sistema`, `conhecimento`, `custos` e `qualidade`.
- Cada função das telas atuais tem uma seção e um subpainel (tabela de mapeamento abaixo). Nenhuma função some sem registro.
- Um arquivo de estilo, `prototipo.css`, com tokens de cor e tipografia em `:root` e componentes únicos. Sem `style=`, sem `<style>`, sem script inline.
- Estados carregando, vazio e erro em cada seção que consome API.
- Nenhuma rota nova de API. As rotas `/api/*` ficam como estão. Exceção pedida pelo Humano em 07/11/2026: `GET /api/conselho/memoria`, só leitura, para a aba Memória compartilhada (ver Contrato).
- Conhecimento tem uma busca única, que serve à Alexandria (escopo "dentro"), ao Acervo (escopo "fora", busca externa) e à Wiki, a documentação do `/index.html` (escopo "documentação"). Decidido pelo Humano em 07/11/2026.
- Casca registrada, fora das sete seções: barra lateral, cabeçalho e chip LOCAL (decidido pelo Humano em 07/11/2026); breadcrumb, busca "Buscar neste mapa…", nota, rodapé e diálogo de evidência, como na tabela de mapeamento.
- Lote 3 da Conversa (09/11/2026, pedido do Humano, paridade com o LibreChat): busca nas conversas, fixar, arquivar, marcadores, pastas, exportação em JSON e Markdown, importação de JSON exportado e conversa temporária. Contrato em Rotas de API e critérios no fim desta seção.
- Proteção das conversas (09/11/2026, pedido do Humano depois do sumiço de duas conversas importadas, confirmado por ele em 09/11/2026 às 16:20 como apagadas pela própria tela): apagar vai para a Lixeira, escritas exigem origem do painel e ficam registradas, salvar preserva a origem de conversa importada, e arquivo ilegível é contado e não é apagado. Contrato em Rotas de API (bloco de proteção) e critérios no fim da seção de Critérios.

## Fora desta versão

- B1, chat com streaming novo: a Conversa continua como está (stream atual, com fallback para `/api/seth/chat`). Motivo: é funcionalidade nova, com risco próprio; o pedido desta versão é a tela unificada.
- B2, ferramentas com aprovação: a aba Ferramentas do Conselho e o fluxo de pedidos ficam como estão. Motivo: mexe em execução de ferramenta; tem spec própria.
- Remoção do LibreChat: o botão "LibreChat" continua em Sistema e a rota de abertura continua. Motivo: decisão separada.
- Ajuste fino de design: sem nova paleta e sem novo layout. Os valores visuais atuais viram tokens sem mudar. Motivo: a verificação visual depende do navegador, e ele não foi medido.
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
- Exceção pedida pelo Humano em 07/11/2026 (aba Memória compartilhada, seção Conselho): `GET /api/conselho/memoria?n=40`. Só leitura do cache do Conselho (`redesign/router/cache_conselho.py`, função `ler`), com o mesmo filtro de dado pessoal e segredo da gravação (`filtrar`). Não aceita caminho de arquivo do cliente e não escreve nada.
  - `n` é inteiro de 1 a 200; padrão 40; acima de 200 corta em 200; zero, negativo ou não numérico responde 400. `n` vazio vale o padrão.
  - Resposta 200 em JSON: `estado` (`ok` ou `vazio`), `n` (aplicado), `entradas` (mais recentes primeiro; cada uma com `n`, `data_hora` em `dd/mm/aaaa hh:mm`, `autor`, `tipo`, `texto`), `observed_at` e `fresh_until`.
  - Cache inexistente ou sem entradas: `estado` `vazio`, lista vazia, 200. Não é erro.
  - Falha de leitura (arquivo ilegível ou linha que não é JSON): 500 com `memoria indisponivel`; a tela mostra `erro`.
  - Origem cruzada: 403, como as outras leituras de `/api/*`.
  - Tipos: `fato`, `decisao`, `pendencia`, `nota` e `diario` (os cinco de `cache_conselho.TIPOS`). A aba filtra por tipo no próprio navegador, sobre as entradas já recebidas.

### Ativos servidos

- Ficam: `/prototipo`, `/prototipo.css`, `/prototipo.js`, `/nova_versao.js`, `/abrir.js`, `/conselho-rede/app.js`, `/operator_console/app.js`, `/assets/agata-portrait.png`.
- Saem (404 na versão nova): `/app.js`, `/styles.css`, `/frentes.js`, `/nova_versao.css`, `/conselho-rede/style.css`, `/operator_console/style.css`.
- Viram redirect: `/index.html`, `/frentes`, `/operator_console/index.html`, `/conselho-rede/index.html` (os arquivos saem do disco na aplicação).
- CSP: sem mudança. `default-src 'none'; script-src 'self'; style-src 'self'; frame-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'`.

### Seções e navegação

- Cada seção é `<section id="<seção>">` dentro de `/prototipo`. Dentro dela há subpainéis `<div id="sub-<nome antigo>">`, com o nome da tela antiga da tabela. Abas internas (`data-sub`) trocam subpainéis dentro da seção.
- Menu lateral: sete botões com `data-secao`. O botão da seção aberta tem `aria-current="page"`.
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

- panorama: GET `/api/status`, `/api/details`, `/api/capacidades`, `/api/frentes`; POST `/api/proposals/verify` (só por ação do Humano); GET `/api/vault/item` (diálogo).
- conversa: GET `/api/seth/conversas`, `/api/seth/conversa?id=`; POST `/api/seth/chat/stream` (com fallback `/api/seth/chat`), `/api/seth/conversa`, `/api/seth/conversa/apagar`; GET `/api/seth/lixeira`; POST `/api/seth/lixeira/restaurar` e `/api/seth/lixeira/purgar`.
- conselho: GET `/api/relay-council/state`, `/api/relay-council/catalog`, e (aba Memória compartilhada, 07/11/2026) `/api/conselho/memoria`; POST `/api/relay-council/actions`, `/groups`, `/decision`; POST `/api/abrir` (alvo `conselho` ou nome de conselheiro).
- sistema: GET `/api/status`, `/api/details`, `/api/nova-versao/estado`; POST `/api/nova-versao/executar` (`fotografar`, `classificar`, `gravar_chave`, `remover_chave`, `adicionar_provedor`, `testar_rotas`, `cancelar_teste`); POST `/api/abrir` (Obsidian, LibreChat, OmniRoute).
- conhecimento: GET `/api/grafo`, `/api/vault/item`, `/api/nova-versao/estado`; POST `/api/wiki/search`, `/api/nova-versao/executar` (`consultar`, `skills`, `indexar`, `iniciar`, `acervo_*`, `acervo_externa_*`), POST `/api/nova-versao/upload`.
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
| casca | Barra lateral com as sete entradas e botão de recolher | casca | não é seção |
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
- [ ] o `/prototipo` tem sete seções (panorama, conversa, conselho, sistema, conhecimento, custos e qualidade) e um botão de menu para cada uma
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

## Desenho e alternativas

- Mesmo servidor, `http.server` da biblioteca padrão, e os mesmos módulos. Sem framework.
- Uma tela com sete seções e subpainéis. Alternativa descartada: manter as 25 páginas e mudar só o menu. Não atende "uma tela só" e mantém 25 pontos de estado.
- Uma folha de estilo. Alternativa descartada: manter `nova_versao.css` separado. Dois conjuntos de tokens, e a CSP trata cada arquivo como fonte separada.
- Operator Console sem iframe: o iframe tem documento, CSS e JS próprios, e não compartilha tokens. O JS da console (`operator_console/app.js`) é isolado antes de entrar na página (ver Implementação). Se o isolamento falhar na verificação, a alternativa é manter o iframe com `operator_console/index.html` servido; isso fica registrado como risco.
- Globais: cada script de tela fica em IIFE ou usa nomes únicos. O teste de globais impede a repetição.
- Hash no lugar de rota nova: o redirect já usa hash (`/prototipo#conselho`). A mudança é só fazer o JS ler o hash.

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

## Migração e reversão

- Sem migração de dados. O painel não guarda estado além do cache em `~/.cache/agata/painel/`.
- Links antigos continuam funcionando: redirect para a seção certa.
- Reversão: `git revert` do commit de aplicação. Os arquivos retirados (HTML e CSS) voltam com o revert.
- Ordem de reversão: se a aplicação tiver ido em mais de um passo, reverter do último para o primeiro.
- Lote 3 (09/11/2026): `organizacao.json` nasce só quando alguém fixa, arquiva, marca ou põe em pasta uma conversa. Sem ele, as conversas valem o padrão. Reverter o código deixa o arquivo ignorado; apagá-lo desfaz a organização sem tocar nas conversas.
- Proteção (09/11/2026): a pasta `.lixeira/` e o `.registro.jsonl` nascem no primeiro uso. Reverter o código deixa a lixeira fora da lista; as conversas que estiverem nela voltam à mão (mover `.lixeira/<id>-<data>.json` para `<id>.json`). A chave `lixeira` de `organizacao.json` é ignorada pelo código antigo.

## Riscos e dependências

- A PR 940 precisa estar na base. Sem ela, `prototipo.html` tem 9 `style=`.
- Globais repetidos: `refresh` (prototipo.js e conselho-rede/app.js) e `$` (conselho-rede/app.js e operator_console/app.js). Medido por leitura, não no navegador. O teste de globais fica como critério.
- Operator Console sem iframe pode quebrar se o JS depender do documento próprio. Risco aceito, com a alternativa descrita em Desenho.
- Os alvos de `spec/acceptance.json` que apontam para `test_painel_unificado.py` falham até a aplicação. Isso é o estado esperado de uma spec antes da implementação.
- Decidido pelo Humano em 07/11/2026: a busca da documentação (wiki) entra na busca única de Conhecimento (Alexandria, Acervo e Wiki).
- Decidido pelo Humano em 07/11/2026: a barra lateral, o cabeçalho e o chip LOCAL ficam fora das sete seções, como casca registrada.
- A verificação no navegador foi feita em 07/11/2026 (critério 35), com o que está medido e o que não foi medido listado ali. Não é aceite visual do Humano.
- `pytest` precisa estar disponível. Sem ele, a execução devolve não medido, não falha em silêncio.
- Proteção (09/11/2026): cliente local que escreve sem cabeçalho (curl, script) passa a receber 403 em toda escrita de conversa. O chat (`/api/seth/chat` e `/api/seth/chat/stream`) não mudou. Salvar uma conversa com um `id` que está na lixeira recria o arquivo com esse id; a restauração depois responde 409 (nada se perde).

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
- `test_chat_ui.py`
- `test_frentes.py`
- `conselho-rede/`
- `relay-extension-v2/`
- `operator_console/`
- `assets/`
