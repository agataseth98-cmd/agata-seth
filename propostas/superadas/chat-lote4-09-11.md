# Lote chat 4 (09/11/2026): ramos, Parar, Continuar, feedback, contexto, atalhos e tema

Estado: proposta. Sem commit de código, sem assinatura, sem APROVADO. Diff: `propostas/chat-lote4-09-11.diff`, relativo a `origin/main` `c1a190c6` (base = `c1a190c6`: proteção `chat-protege-conversas-09-11` já aplicada, PR #963, commit `56c49849`), só `redesign/painel_operacional/`: 8 arquivos (7 alterados e `test_conversas_lote4.py` novo). SHA-256 do `.diff`: `49f62fadd67bed0c4ee062157d2b246f3a588612c647447a2b108bc3de09ea43` (174590 bytes). Confere com `git apply --check` e `git apply --cached --check` contra `origin/main` `c1a190c6`, limpos em 11/11/2026.

## Para o Humano confirmar

- Base: `c1a190c6`. A proteção já está no main, então esta proposta não depende de nenhuma outra proposta pendente para ser aplicada.
- As 8 decisões do agente (seção "Decisões tomadas na implementação"): confirmar cada uma, ou pedir ajuste antes da assinatura.
- Pendência: Parar com o gateway real depende da proposta `chat-stream-verificar-depois-09-11`, que ainda não tem `.diff` nem commit em `propostas/` (existe só como rascunho `.md` não versionado). Enquanto ela não for aplicada, Parar não corta o stream no servidor (ver "Não medido" e "Pendência").

## Problema

- Pedido do Humano (paridade com o LibreChat, 09/11). A conversa não tinha: editar mensagem e reenviar sem perder a resposta antiga, regenerar sem apagar a anterior, ramificar a partir de uma mensagem, parar a resposta, continuar a resposta, avaliar a resposta, ver quanto contexto vai, atalhos de teclado e tema claro.
- Ramos não são só uma lista: uma conversa com ramos guarda todas as versões. Por isso a árvore precisa ir para a lixeira junto com a conversa e voltar no restaurar.

## O que muda

- `armazem.py`
  - Conversa com ramos grava `arvore` (nós com `id` e `pai`, e `folha`) e também `mensagens`, o caminho ativo. Sem ramo, grava como antes. Validação da árvore: pai antes do filho, id no formato, papel conhecido, até 400 nós e 200 mensagens no caminho. Árvore inválida recusa a gravação; árvore ilegível, na leitura, cai no caminho `mensagens`.
  - Feedback (`bom` e `ruim`, com motivo de até 200 caracteres), resposta `interrompida`, `cortes` de continuação e `ramificada_de` são validados campo a campo; valor fora do formato sai sem recusar a conversa.
  - Lixeira: a árvore vai junto. Apagar move o arquivo inteiro (`os.replace`), então `arvore` e `mensagens` vão com ele; restaurar devolve o arquivo ao lugar, com os ramos. A conta de mensagens da lixeira usa o caminho ativo.
  - `_formato_gravar` mantém o `id` e os campos de origem (`origem`, `origem_id`, `titulo_original`, `data_original`, `importado_em`) que a proteção grava em arquivo importado.
  - Exportação JSON leva `arvore` e `ramificada_de`; Markdown leva só o caminho e avisa; importação aceita o mesmo. Busca e contagem da lista veem só o caminho ativo.
- `prototipo.js`
  - Editar e reenviar, regenerar, trocar de versão ("< 1/2 >"), ramificar, Parar (AbortController no fetch), Continuar (pede à Seth com "Continue de onde parou, sem repetir o que já foi dito." como última mensagem do pedido, sem gravar essa mensagem, e anexa a resposta à mesma mensagem com marca de continuação), feedback com motivo, barra de contexto, lista de atalhos (`?`), Ctrl+Shift+O, Ctrl+Shift+C, Esc, `/`, tema claro, escuro ou do sistema com `localStorage` em try/catch.
  - Trava única de troca: `sethTrocaBloqueada` (da proteção), baseada em `sethRespondendo`. Vale para trocar de conversa, Nova conversa, temporária e abrir outra. O bloqueio próprio do lote 4 foi removido; `sethEmCurso` passou a ser a mesma trava.
  - Salvar e responder capturam o alvo antes do primeiro `await`. `sethSalvar(alvo)` grava na conversa de origem; `sethResponder` aplica a resposta e espera o salvar antes de liberar o botão (`sethRespondendo` vale até o salvar terminar).
- `prototipo.html`: seletor de tema e botão Atalhos no topo; lista de atalhos; barra de contexto; origem da ramificação; Parar; copiar a última resposta. Sem `style=` nem script inline.
- `prototipo.css`: classes novas, com tokens. Paleta clara gerada dentro do `:root` (pares `--luz-*`), e um bloco `:root[data-tema="claro"]` que usa só `var()`.
- `test_chat_ui.py`: harness com `AbortController` real, stream que espera (`respostaStreamLenta`) ao lado da resposta pendente da proteção (`respostaPendente`), e as duas listas de ações (`depois` da proteção e `acoes_depois` do lote 4). Testes do lote 4 lado a lado com os da proteção. Os dois testes de salvar com alvo passaram a usar o formato de árvore (`nos`, `folha`).
- `test_conversas_lote4.py` (novo): testes de armazém e de rota (árvore, validação, compatibilidade, feedback, interrompida, cortes, ramificação, exportação, importação, busca) e `LixeiraComRamoTests` (apagar leva a árvore à lixeira; restaurar devolve os ramos).
- `spec/spec.md` e `spec/acceptance.json`: contrato do lote 4, mapeamento (8 linhas), 16 critérios novos. Total com a proteção: 90 critérios e 90 entradas, na mesma ordem.

## Decisões tomadas na implementação (para o Humano confirmar)

1. Trocar de versão segue a resposta mais nova de cada passo seguinte (a última criada em cada ramo).
2. Parar sem texto grava uma resposta vazia marcada como interrompida; essa resposta não vai ao gateway.
3. Erro no meio do stream também mantém o texto parcial marcado (decisão D3 aplicada a erro).
4. Continuar usa o modelo escolhido na hora e atualiza o modelo que respondeu; o campo `modelo` da primeira parte não muda.
5. Feedback: trocar de "Útil" para "Não útil" mantém o motivo já escrito.
6. Ramificar inclui a mensagem clicada e usa o mesmo título da conversa de origem.
7. Com resposta em curso, a troca de conversa fica bloqueada pela trava única da proteção (aviso na tela).
8. A nota gravada continua `bom` (útil) e `ruim` (não útil); só o rótulo mudou, por decisão E-2 (sem emoji).

## Testes medidos

- `cd redesign/painel_operacional && python3 -m unittest discover -s . -p "test_*.py"`: `Ran 383 tests`, `FAILED (failures=1)`. A única falha é `test_sdd_painel.ProjetosExternosTests.test_executar_projeto_roda_o_ciclo_e_recusa_o_que_nao_esta_em_config_sdd`, a mesma que já falhava na base. Diferença sobre a base com a proteção (323): +60 testes (26 de servidor e 34 de UI).
- CI local: `uv run --offline --with pytest bash scripts/ci_sdd_local.sh`: 33 passos OK, `CI LOCAL: TUDO OK`. O pytest 9.2.0 veio do cache do uv (`--offline`: nada foi baixado nem instalado).
- Ambiente: o `node` do sistema não carregava `libsimdjson.so.36` (o pacote instalado tem a `.34`). Para rodar o harness de UI, foi feito um link dessa biblioteca no scratchpad da sessão, com `LD_LIBRARY_PATH` usado só nesse processo. Nada foi instalado nem alterado no sistema. Para reproduzir, é preciso node funcionando.
- Navegador, Chromium headless com perfil próprio, painel de teste na porta 20250 com casa falsa e gateway falso na porta 20251 (sem provedor):
  - ramo: depois de editar, `< 2/2 >` aparece na pergunta editada;
  - Parar: durante o stream, botão visível e Enviar desabilitado; ao trocar de conversa durante a resposta, a tela avisa e não troca; depois de Esc, status INTERROMPIDA, texto parcial mantido e marca de interrompida;
  - console sem erros e sem violação de CSP.
  - Capturas: `/tmp/claude-1000/-home-orusoua-agata/634b0edc-ec9d-4b4f-92bb-7fb16f4d2c75/scratchpad/lote4-ramos.png`, `.../lote4-parar-botao.png`, `.../lote4-interrompida.png`.

## Não medido

- Parar com o gateway real. O verificador (`seth_gateway`, `_reter` e `_liberar_retidos`) ainda segura o stream das rotas `seth-*` até o fim. Com a cadeia real, Parar pode não cortar nada visível. O teste de Parar usa stream falso que espera.
- Fluxo de lixeira com ramos no navegador. Coberto por teste de servidor (`LixeiraComRamoTests`) e pelos testes de UI da proteção; não houve clique real apagar, restaurar.
- Contraste da paleta clara (inversão de luminosidade, sem medição por ferramenta); tela abaixo de 760 px; atalhos em janela real de navegador; tema "sistema" com a preferência real do sistema operacional; busca e lista com muitas conversas.
- Qualidade das respostas e alcance real de Continuar com o modelo real.

## Pendência

- Parar com o gateway real depende da proposta `chat-stream-verificar-depois-09-11`, ainda sem `.diff` nem commit em `propostas/`. Quando o modo `depois` for aplicado, Parar passa a cortar o stream de verdade. Até lá, o botão corta a espera e o texto que já chegou.
- Estado `interrompida`: hoje é o campo `interrompida: true` na resposta. A proposta `chat-stream-verificar-depois-09-11` usa `verificacao.estado = interrompida`. Na aplicação, uma das formas precisa ser convertida na outra.
- Aplicação: a base da proteção já está no main (PR #963, `c1a190c6`); a aplicação desta proposta é sobre ela, sem outra dependência de código.
- Decisões 1 a 8 acima, para o Humano.

## Reversão

Pela árvore onde foi aplicada: `git apply -R propostas/chat-lote4-09-11.diff`. Conversas gravadas com ramo continuam com `mensagens` (o caminho ativo), então uma versão anterior as abre pelo caminho, sem ver os ramos. Antes de reverter, exportar em JSON (o JSON leva `arvore`).
