# Lote chat-protege-conversas-09-11: lixeira, origem na escrita, registro, origem preservada e ilegíveis

Estado: proposta. Sem commit, sem assinatura, sem APROVADO. Diff: `propostas/chat-protege-conversas-09-11.diff` (contra `origin/main` `1e9c90f4`, só `redesign/painel_operacional/`: 8 arquivos alterados e `test_conversas_protege.py` novo). SHA-256 do `.diff`: `b8570b0c44b79d28ca158fc90b0068e4423c976a8357b105b6d0d7054eeb12be` (124049 bytes).

## Problema

- Em 09/11, duas conversas importadas do LibreChat (`0827f803ebdb`, `1dee050d6de2`) sumiram da pasta de conversas e foram restauradas do backup `armazem-backup-07-11` às 16:04. O Humano confirmou em 16:20 que apagou pela própria tela, em teste (memória comum do Conselho, entrada 452).
- O código da época apagava de vez (`arq.unlink()`), sem lixeira, sem registro e sem checagem de origem na escrita. Sem cabeçalho de origem, qualquer cliente local gravava e apagava.
- Salvar uma conversa importada perdia `origem`, `origem_id`, `titulo_original`, `data_original`, `importado_em` e `id`. Medido na proposta origem-preservada-07-11.
- A listagem escondia arquivo ilegível sem aviso.
- `origem-preservada-07-11` (PR #947, juntada em 09/11 às 09:32 de Brasília): só a proposta entrou no `main`; o código não. O diff dela não aplica mais à base atual: `git apply --cached --check` contra `origin/main` falha em `redesign/painel_operacional/armazem.py:113` (medido em índice temporário). A lógica foi portada à mão para `_conversa_gravar`, com os cinco cenários dela reescritos em `test_conversas_protege.py`.

## O que muda

- `armazem.py`
  - Apagar vira mover: `_conversa_apagar` faz `os.replace` para `.lixeira/<id>-<AAAAMMDD-HHMMSS>.json` (mesmos bytes) e leva a entrada de organização para a chave `lixeira` de `organizacao.json`. Organização ilegível: 409, nada é movido.
  - `_lixeira_listar`, `_lixeira_restaurar` (409 em id repetido; pasta apagada enquanto a conversa estava fora vira sem pasta) e `_lixeira_purgar` (só por pedido).
  - `_conversas_listar`: `total` conta só as conversas legíveis; `ilegiveis` conta os arquivos que não puderam ser lidos. Nada é apagado nem mexido.
  - `_conversa_gravar`: preserva a origem (portado de origem-preservada-07-11). Reaproveita o arquivo que já tem a mesma origem, não reescreve a origem gravada, mantém `criada` e `origem_id` das mensagens que continuam no mesmo lugar, com o mesmo papel e texto, e grava o próprio `id`.
  - `_conversa_importar`: item que está na lixeira conta como existente (`ja_existe`, com `lixeira: true`).
  - `_registro_escrever`: acrescenta em `.registro.jsonl` uma linha com `hora`, `rota`, `id` e `status`. Nunca título, texto, marcador ou nome de pasta.
- `server.py`
  - `_escrita_permitida`: escrita exige `Origin` igual ao do painel ou `Sec-Fetch-Site: same-origin`. Sem cabeçalho, 403. Cabeçalho que diz outra origem (cross-site, `Origin` de outro site, `null`) também é 403, mesmo que o outro cabeçalho bata. A regra pura OU deixava passar `Sec-Fetch-Site: cross-site` com a origem do painel, e `test_conversas_lote3.py` já exige 403 nesse caso.
  - Rotas novas: `GET /api/seth/lixeira`, `POST /api/seth/lixeira/restaurar`, `POST /api/seth/lixeira/purgar`.
  - `_responder_escrita`: toda resposta de escrita de conversa passa pelo registro, inclusive 403, 400, 404, 409 e 413.
  - `POST /api/seth/conversa/apagar`: a resposta passa a `{apagada, lixeira}`.
- `prototipo.html`: seção Lixeira (`details#seth-lixeira-bloco`) e aviso `seth-ilegiveis-aviso`. Sem `style=` nem script inline.
- `prototipo.js`
  - Lixeira: restaurar; apagar de vez em dois cliques.
  - `sethSalvar(alvo)` grava o id e o aviso na conversa de origem e repinta a tela só se ela ainda é a aberta. `sethEnviar` captura o alvo antes do primeiro `await` e espera o salvar antes de liberar o botão.
  - `sethTrocaBloqueada`: durante a resposta, trocar de conversa, Nova conversa e temporária ficam bloqueados, com aviso.
  - `sethApagar` confere `r.ok`: a conversa só sai da tela com a confirmação do painel. Aviso de ilegíveis com a contagem.
- `test_conversas_protege.py` (novo, 33 testes): lixeira, origem na escrita, registro, origem preservada e ilegíveis, com servidor numa porta livre.
- `test_chat_ui.py`: harness com as rotas da lixeira, uma ação `js` e `depois`; classe nova `ConversaProtecao` (17 testes, em node com DOM mínimo). `sethSalvar` é exposta só na cópia em memória do arquivo, durante o teste (uma linha antes do fim da IIFE). O arquivo em disco não muda.
- `spec/spec.md`: contrato do bloco de proteção, 18 critérios novos (total 74), Código, reversão e risco.
- `spec/acceptance.json`: 18 entradas novas (total 74), no formato existente.
- `README.md`: uma linha sobre lixeira, origem e registro.

## Decisões de desenho

- A lixeira fica dentro de `CONVERSAS_DIR`, com nome `<id>-<data>`. Listagem e busca leem só a pasta principal, então a conversa apagada some sem que nada seja apagado.
- A entrada de organização vai junto na chave `lixeira` de `organizacao.json`, em uma escrita atômica sob a trava de organização.
- Purga só por pedido e com confirmação na tela. Nenhuma rotina apaga sozinha; listar e buscar não tocam na lixeira.
- O registro é só de acréscimo. Se o arquivo não puder ser escrito, a ação segue e a linha se perde. Isso fica declarado em Ficou de fora.
- A troca de conversa fica bloqueada enquanto a Seth responde. Com isso, a captura do alvo em `sethSalvar` é defensiva: não consegui reproduzir pela tela a conversa mudando durante o salvar.

## Testes medidos

- `cd redesign/painel_operacional && python3 -m unittest discover -s . -p "test_*.py"`: `Ran 323 tests`, `FAILED (failures=1)`. A única falha é `test_sdd_painel.ProjetosExternosTests.test_executar_projeto_roda_o_ciclo_e_recusa_o_que_nao_esta_em_config_sdd`, que já falhava na base (273 testes antes da alteração, mesma falha). Diferença: +50 testes (33 em `test_conversas_protege.py` e 17 em `ConversaProtecao`).
- `test_conversas_protege.py` isolado: `Ran 33 tests`, `OK`. `test_chat_ui.ConversaProtecao` isolado: `Ran 17 tests`, `OK`.
- CI local: `PYTEST=/home/orusoua/.cache/uv/archive-v0/0obnOoJtclHllQl_/bin/pytest bash scripts/ci_sdd_local.sh`, com pytest 9.2.0 (a versão fixada no CI). Resultado: 33 passos OK, `CI LOCAL: TUDO OK`, exit 0. Esse pytest já estava no cache do uv; nada foi instalado.
- O CI local regrava `redesign/nova_versao/spec/criterion-drift.md` e `evidence.json`, e cria `redesign/sdd_flow/spec/criterion-drift.md` e `evidence.json`. Esses arquivos foram revertidos (`git checkout`) ou apagados (`rm` de caminho exato). Não entram no diff.
- `git apply --cached --check` contra `origin/main` em índice temporário: passa. `git apply --check -R` contra a árvore da worktree: passa.
- Navegador, cópia na porta 20253 com HOME falso (a 20251 estava ocupada por outro processo, que não foi tocado), Chromium headless com perfil próprio. Capturas da Lixeira em `protege-lixeira.png` e `protege-lista.png` na pasta de scratchpad da sessão. Fluxo com cliques reais: restaurar (lixeira 2 para 1, lista 3 para 4); apagar com confirmação (lista 4 para 3, lixeira 1 para 2); apagar de vez com confirmação (lixeira 2 para 1). Os POSTs de lixeira e de apagar responderam 200 e geraram linhas no registro, sem erro de console e sem violação de CSP.

## Não medido

- Navegador do Humano e tela estreita (abaixo de 760 px).
- Armazém real: não foi aberto nem alterado.
- Custo da listagem com muitas conversas: `_conversas_listar` lê todos os arquivos a cada chamada.
- Corrida de troca durante o salvar: não reproduzida pela tela.

## Ficou de fora

- `migrar.py` (fora da lista desta tarefa) continua reconhecendo a importação só pelo nome do arquivo. Reimportação real contra o LibreChat não testada. Decisão do Humano, como em origem-preservada-07-11.
- As rotas de chat (`/api/seth/chat`, `/api/seth/chat/stream`) seguem com a regra antiga: sem cabeçalho, passam. Não são rotas de conversa salva.
- Salvar com um `id` que está na lixeira recria o arquivo com esse id; a restauração depois responde 409. Não se perde nada, mas não há aviso específico para isso na tela.
- `.registro.jsonl` não tem limite de tamanho nem rotação.
- Falha ao gravar o registro é silenciosa: sem linha e sem aviso.
- Item 8 do relatório (o botão "Confirmar apagar" fica armado até o próximo repaint): não alterado.
- O aviso de ilegíveis soma a lista e a lixeira numa frase só.
- Link público de compartilhamento de conversa: fora, pendência do lote 3.

## Reversão

`git revert` do commit de aplicação. A pasta `.lixeira/` e o `.registro.jsonl` ficam no disco; o código antigo os ignora. A chave `lixeira` de `organizacao.json` também é ignorada. Para trazer uma conversa de volta à mão, mover `.lixeira/<id>-<data>.json` para `<id>.json` na pasta de conversas.

## Pendência

- Decisão do Humano: aceitar a regra de origem (403 para escrita sem cabeçalho) e a purga manual por item.
- Fluxo padrão: este PR só abre a proposta. Assinatura e aplicação ficam com o Humano.
