# Lote chat 3 (09/11/2026): conversas (busca, pastas, fixar, arquivar, marcadores, exportar e importar, temporária)

Estado: proposta. Sem commit de código, sem assinatura, sem APROVADO. Diff: `propostas/chat-lote3-09-11.diff` (contra `origin/main` `e7c9b451`, só `redesign/painel_operacional/`, 9 arquivos: 8 alterados e `test_conversas_lote3.py` novo). SHA-256 do `.diff`: `62da13cab053502f4d4c98a7a5f8e17beb6f7b3a80ee0659af802508c5c26457`.

## Problema

- Pedido do Humano (paridade com o LibreChat). A aba Conversa tinha só lista, renomear e apagar. Faltavam busca nas conversas salvas, organização (fixar, arquivar, marcadores, pastas), exportar e importar, e uma conversa que não fica salva.

## O que muda

- `server.py`
  - `GET /api/seth/conversas` passa a devolver, em cada item, `fixada`, `arquivada`, `marcadores` e `pasta`; e no topo `pastas`, `marcadores`, `total` e `organizacao`. Fixadas vêm primeiro.
  - `GET /api/seth/conversas/busca?q=`: busca em títulos e mensagens, sem diferenciar caixa nem acento. Até 50 resultados, cada um com trecho de até 120 caracteres.
  - `POST /api/seth/conversa/organizar`: muda só a organização (fixar, arquivar, marcadores, pasta), nunca o conteúdo. Corpo até 4096 bytes; acima, 413.
  - `POST /api/seth/pastas`: criar, renomear e apagar. Apagar pasta não apaga conversa.
  - `GET /api/seth/conversa/exportar?id=&formato=json|md`: download com `Content-Disposition: attachment`. A conversa temporária não tem exportação.
  - `POST /api/seth/conversa/importar`: JSON exportado, até 263168 bytes (acima, 413). Não duplica: se o `id` ou o `origem_id` já existe aqui, responde `ja_existe` e não grava.
  - As rotas novas recusam origem cruzada (403), como as outras de `/api/seth/*`.
  - `motivo_conversa_recusada` saiu de `server.py` e foi para `armazem.py` (mesmo comportamento, só mudou de lugar).
- `armazem.py`
  - `organizacao.json`, dentro da pasta de conversas, guarda pastas e uma entrada por conversa. Sem o arquivo, toda conversa vale o padrão. Arquivo ilegível: a lista avisa e as escritas respondem 409 sem sobrescrever.
  - Marcadores: até 10 por conversa, até 24 caracteres (letras, números, espaço e hífen), em minúsculas, sem repetir.
  - Pastas: até 50, nome de 1 a 60 caracteres, sem repetir.
  - Exportação em JSON e Markdown; importação com validação das mesmas regras da gravação.
  - Importa `MODELO_PADRAO`, `modelo_permitido` e `modelo_real_valido` de `chat_stream.py` (dependência nova: `armazem` passa a depender de `chat_stream`; os testes passam sem ciclo).
- `prototipo.html`, `prototipo.css`, `prototipo.js`
  - Campo de busca com resultados e link para a mensagem; seção Arquivadas com Desarquivar; filtros por pasta e por marcador; criar, renomear e apagar pasta; seletor de pasta em cada conversa; exportar JSON e Markdown; importar arquivo.
  - Conversa temporária: existe só na tela, com aviso visível. A UI não chama `POST /api/seth/conversa` enquanto ela está ligada.
- `spec/spec.md` e `spec/acceptance.json`: contrato das rotas e 56 critérios.
- `test_chat_ui.py` (ajustado à nova lista) e `test_conversas_lote3.py` (novo, 411 linhas).

Decisão de desenho: `organizacao.json` nasce só quando alguém organiza uma conversa. As conversas gravadas não são reescritas pela organização.

Fora deste lote: link público de compartilhamento (ver Pendência).

## Testes medidos

- `cd redesign/painel_operacional && python3 -m unittest discover -s . -p "test_*.py"`: `Ran 273 tests`, `FAILED (failures=1)`. A única falha é `test_sdd_painel.ProjetosExternosTests.test_executar_projeto_roda_o_ciclo_e_recusa_o_que_nao_esta_em_config_sdd`, pré-existente.
- Mesmo comando num export limpo de `origin/main` (`e7c9b451`): `Ran 215 tests`, a mesma falha. Diferença líquida: +58 testes.
- CI local: `PYTEST=<venv com pytest==9.2.0, versão fixada em .github/workflows/sdd.yml> bash scripts/ci_sdd_local.sh`: 33 passos OK, `CI LOCAL: TUDO OK`. O pytest não estava instalado no sistema; o venv é de scratch, fora do repositório.
- Critérios: `redesign/painel_operacional/spec/acceptance.json` tem 56 critérios. O passo `critérios e drift: painel_operacional` do CI local passou.
- `node --check redesign/painel_operacional/prototipo.js`: OK.
- `git apply --cached --check` contra `origin/main` (índice temporário): limpo. `git apply --check -R` contra a árvore: limpo.
- Capturas, em `/tmp/claude-1000/-home-orusoua-agata/634b0edc-ec9d-4b4f-92bb-7fb16f4d2c75/scratchpad/`: `lote3-busca-resultado.png`, `lote3-lista-pasta-fixada-tag.png`, `lote3-arquivadas.png`, `lote3-temporaria.png`. Gravadas pela sessão de origem às 14:59; não foram revistas nesta etapa.

## Não medido

- Busca com muitas conversas salvas (tempo e uso de memória).
- Tela estreita, abaixo de 760px.
- Fluxo ponta a ponta no navegador (clicar em exportar, importar um arquivo real, mudar a pasta de uma conversa pelo seletor). A cobertura atual é o teste de UI com node e DOM mínimo, mais as capturas.

## Pendência

- Link público de compartilhamento de conversa: fora deste lote. Precisa decisão de segurança do Humano: quem vê, por quanto tempo, como revoga. Nada disso foi implementado.

## Reversão

Pela árvore onde foi aplicado: `git apply -R propostas/chat-lote3-09-11.diff`. Conversas gravadas não mudam. O `organizacao.json` que tiver sido criado fica ignorado pelo código revertido; apagá-lo desfaz a organização sem tocar nas conversas.
