# Lote chat 2 (09/11/2026): falhas silenciosas, seletor de modelo e modelo real

Estado: proposta. Sem commit, sem assinatura, sem APROVADO. Diff: `propostas/chat-lote2-09-11.diff` (contra `origin/main`, só `redesign/`).

## Problema

- Duas frentes do chat do painel estavam em worktrees separadas, sem commit, e tocavam os mesmos arquivos:
  - A: falhas silenciosas do chat (aviso de janela cortada, aviso de conversa não salva, motivo de 400/413, teto do fallback em CHAT_STREAM_LIMITE_BYTES).
  - B: seletor de modelo (allowlist `seth-livre` e `seth-public`, `GET /api/seth/modelos`, modelo salvo na conversa).
  - Os dois trocaram o fallback para `GATEWAY_CHAT_URL`. Ficou uma só versão.
- O painel mostrava sempre o modelo escolhido, nunca o que respondeu. O gateway já envia `X-Modelo-Real` (`redesign/router/seth_gateway.py`, linha 1493), mas o painel não lia esse cabeçalho.

## O que muda

- `server.py`
  - Lê `X-Modelo-Real` da resposta do gateway, no stream e no fallback, e repassa ao navegador no cabeçalho da resposta. Só repassa o valor que passa em `chat_stream.modelo_real_valido`.
  - Motivos de 400/413 em português, sem eco do conteúdo. Conversa recusada por modelo fora da lista responde `modelo fora da lista`.
  - `GET /api/seth/modelos`. O fallback usa `GATEWAY_CHAT_URL` e o teto `CHAT_STREAM_LIMITE_BYTES`.
- `chat_stream.py`: lista fixa `MODELOS_CHAT`, `modelo_permitido`, `modelo_valido`, `lista_modelos` e `modelo_real_valido` (novo). O nome real passa se tiver até 120 caracteres de `[A-Za-z0-9._:/+-]`, começando com letra ou dígito.
- `armazem.py`: a conversa guarda `modelo` (o escolhido, da lista fixa) e, em cada resposta da Seth, `modelo_real` quando o cabeçalho veio. `modelo_real` fora do formato é descartado; não recusa a gravação.
- `prototipo.js`
  - O seletor carrega a lista do servidor e envia `modelo` no stream e no fallback.
  - Lê `X-Modelo-Real` nos dois caminhos.
  - Cada resposta mostra `modelo: <real>`. Sem o cabeçalho, mostra `modelo: <escolhido> (escolhido)`.
  - Janela de mensagens de A, com o modelo capturado no envio.
- `prototipo.html` e `prototipo.css`: aviso de conversa não salva, seletor de modelo e estilos.
- `spec/spec.md`: regra do `X-Modelo-Real` e do `modelo_real`. Nenhum arquivo novo em `redesign/`, então a seção Código não muda.

Decisão de desenho: o campo `modelo` de cada resposta continua sendo o escolhido (lista fixa, como em B). O nome real vai no campo separado `modelo_real`. Assim o teste de B que recusa `seth-auto` numa mensagem continua valendo, e o nome real da Máquina (por exemplo `openai/gpt-oss-120b`) não passa pela lista fixa.

Testes novos desta mesclagem: 14. Em `test_chat_stream.py` (`ModeloRealTest`, 2), `test_chat_stream_rota.py` (6), `test_chat_ui.py` (5, JS no node) e `test_painel.py` (1).

## Testes medidos

- `cd redesign/painel_operacional && python3 -m unittest discover -s . -p "test_*.py"`: `Ran 215 tests`, `FAILED (failures=1)`. A única falha é `test_sdd_painel.ProjetosExternosTests.test_executar_projeto_roda_o_ciclo_e_recusa_o_que_nao_esta_em_config_sdd`, a falha pré-existente citada na tarefa.
- `node --check prototipo.js` e `py_compile` dos módulos alterados: OK.
- `git apply --check --cached` (contra o índice, que é o HEAD 047c5b3c): OK. `git apply --check -R` (contra a árvore): OK.
- Suíte de novo após o acabamento de CSS: `Ran 215 tests`, `FAILED (failures=1)`, a mesma falha pré-existente.
- Screenshot da aba Conversa, cópia na porta 20248, conversas em diretório temporário vazio: seletor "Modelo: Seth (padrão)" com a descrição vinda de `/api/seth/modelos`. Select e textarea ficaram no tema escuro (`seletor2.png`).

## Não testado

- Resposta real do gateway com `X-Modelo-Real`. Os testes usam gateway falso local. Nenhum provedor foi chamado. O cabeçalho do gateway real foi lido no código, não medido ao vivo.
- Tela de resposta mostrando `modelo: <real>` não capturada. O screenshot mostra só o seletor, sem conversa.
- Envio com `seth-public` ao gateway real (e a recusa 403 dos outros modelos) não medido ao vivo. O comportamento vem da leitura de `_politica_dados_externos`.
- JS testado em node com DOM mínimo, não em navegador de verdade. O screenshot prova só a carga da aba.
- pytest não instalado; não rodado.
- Pipeline de CI da proposta (checagens P-8 e âncora) não rodado.
- Acabamento visual: select e textarea usam os tokens de `:root` (paper, line, ink, teal), conferidos só no screenshot. Não houve revisão de design nem teste em outras larguras.
- `origin/main` avançou de 047c5b3c para e6857870 (10 commits; nenhum toca `redesign/`). O diff de `redesign/` é idêntico contra as duas bases (mesmo md5).

## Reversão

Pela árvore onde foi aplicado: `git apply -R propostas/chat-lote2-09-11.diff`. Conversas já gravadas com `modelo_real` mantêm o campo no disco; reverter o código não apaga nada.
