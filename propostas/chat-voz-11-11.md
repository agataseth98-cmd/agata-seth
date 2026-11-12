# Chat: voz da Seth no painel (11/11/2026) — ler em voz alta, ditado e modo conversa

Pedido do Humano em 11/11/2026, 20:15: paridade com o LibreChat (ditado por voz, ler em voz alta, modo conversa). Mudança só em `redesign/painel_operacional/`, mais este `.md` e o `.diff`. O `.diff` é relativo à base `origin/main` `9b27c1b4` (merge do PR #973, `aplica/pacote-11-11`, que traz o pacote-11-11 aplicado). Nesta rodada não houve commit, assinatura, push nem PR: a publicação fica com quem tem essa permissão (ver "Publicação").

## Base

- Base: `origin/main` `9b27c1b4` (merge do PR #973, `f181d3d5` "Aplica pacote-11-11 (assinado pelo Humano)"). Já traz lote4, importantes e história aplicados.
- A rodada anterior foi feita sobre `21095eaf` com as três propostas aplicadas à mão (árvore `f96be7c`). Esta versão foi refeita sobre `9b27c1b4`.
- Reaplicação: os 12 arquivos do lote de voz foram fundidos sobre a base nova por fusão de três vias (ancestral: `f96be7c`; ours: `9b27c1b4`; theirs: o lote). Resultado:
  - `server.py`: um conflito, só de imports. Mantive os dois lados (`importantes` do main e `seth_voz`/`seth_ditado` do lote).
  - `prototipo.css`, `prototipo.js`, `prototipo.html`, `nova_versao_painel.py`, `spec/spec.md`: sem conflito.
  - `spec/acceptance.json`: os 115 critérios do main são iguais aos da base antiga; o lote acrescentou 14, sem duplicata. Total: 129.
- O `.diff` tem 12 arquivos, 1686 inserções e 4 remoções, e aplica limpo sobre `9b27c1b4` (`git apply --cached --check`). Não há arquivo de `propostas/` no diff.

## Apetite

Uma rodada. Entrega: itens 1, 2, 3 e 4 com testes. Se apertar, corta nesta ordem: item 4 (linha de estado na página Sentidos), depois o modo conversa (item 3). Ditado (item 2) e leitura em voz alta (item 1) não saem.

Resultado: os quatro itens foram entregues e testados. Nenhum foi cortado.

Fora desta rodada: corte imediato de um trecho que já está tocando (Parar corta só entre partes, como pedido); fila com várias respostas; guardar o último uso em disco (fica na memória até o painel reiniciar); STT ou TTS pelo navegador ou por serviço externo; ditado com envio automático; tela nova.

## Lista de conferência de pronto

- [x] Ler em voz alta: botão Ouvir em cada resposta da Seth. `POST /api/seth/ouvir` fala por parágrafo, reutilizando `scripts/agata_falar.py` (preparo, ligar e desligar o serviço, checagem de modelo). O script não é editado. `GET /api/seth/ouvir` mostra o estado. `POST /api/seth/ouvir/parar` interrompe entre partes e desliga o piper só se foi ele que ligou. A resposta diz "falei" ou "NÃO falei" em português simples. Modelo que não é `pt_BR-agata` é recusado: nunca outra voz.
- [x] Ditado: botão Ditar no campo. `MediaRecorder` no navegador, com a permissão pedida pelo próprio navegador. O áudio vai só para `POST /api/seth/ditado`, que repassa ao `servidor_ouvido` local (127.0.0.1:20137). O texto volta ao campo para revisão e não é enviado sozinho. Limite de 2 MB no servidor e de 60 s no cliente. Erros em português simples: permissão negada, sem microfone, ouvido fora do ar, áudio vazio, áudio grande, sem fala.
- [x] Modo conversa: desligado por padrão. Preferência em `localStorage` com try/catch, fora do bloco da Conversa. Lê cada resposta concluída da conversa aberta. Esc e o botão Parar voz interrompem.
- [x] Página Sentidos: a linha "voz" mostra o piper (no ar ou parado, sob demanda), o último uso e um aviso se o piper carregou outro modelo. Só leitura. A linha é preenchida pelo estado real, não pelo texto fixo que havia antes.
- [x] Origem: POSTs de voz exigem `_escrita_permitida` (403 sem origem do painel). GET segue a regra de `/api/*` (mesma origem).
- [x] CSP: conferida, nenhuma alteração. A fala sai pelo player da Máquina; gravação e microfone não passam pela CSP. Por isso não há `media-src`.
- [x] JS externo. Sem `innerHTML`, sem atributo `on*`, sem `style=`, sem script inline. Texto transcrito e texto da resposta entram só por `textContent`.
- [x] Sem emoji em nenhuma linha nova (teste dedicado).
- [x] Testes de servidor com voz e STT falsos. Nenhum teste aciona o piper real (porta 8890) nem o `servidor_ouvido` real (porta 20137).
- [x] Testes de UI com node e DOM mínimo (`test_voz_ui.py`).
- [x] `spec/spec.md` (Escopo, Rotas de API, Critérios de aceite, Código) e `spec/acceptance.json` atualizados. Âncora OK, sem órfão.
- [x] Suíte `unittest` e `scripts/ci_sdd_local.sh` rodados sobre a base nova, com a saída abaixo.
- [~] Capturas: três PNG feitos (rodada anterior, sobre a mesma tela de Conversa) em `scratchpad/voz-conversa.png`, `voz-conversa-390.png` e `voz-conversa-390-alto.png`, porta 20257, HOME falso, processo encerrado por PID. Não há captura do botão Ouvir numa resposta nem da linha de voz na página Sentidos (ver "Não medido").
- [x] `.diff` relativo a `9b27c1b4`, só com arquivos de `redesign/painel_operacional/`. Este `.md` traz base, decisões, testes e o que não foi medido.
- [x] Nada commitado, assinado ou publicado nesta rodada.

## Testes medidos (sobre a base `9b27c1b4`)

Árvore candidata: a base `9b27c1b4` exportada (`git archive`) para uma cópia descartável, com os 12 arquivos fundidos. Node do sistema (`v24.22.2`).

- Suíte completa do painel (`python3 -m unittest discover -s . -p "test_*.py"`, com `uv run --offline --with pytest`): **519 testes, OK** ("Ran 519 tests in 33.406s / OK").
- `redesign/sdd_flow/anchor.py . redesign/painel_operacional redesign/sentidos`: `ANCHOR: OK`.
- `uv run --offline --with pytest bash scripts/ci_sdd_local.sh` sobre a cópia: **33 passos OK, 2 FALHA**. As duas falhas são de ambiente, não do lote:
  - `gate de sincronia das specs`: "sem repositório git: o gate precisa das datas de commit". O workflow (`.github/workflows/sdd.yml`) roda com `fetch-depth: 0`.
  - `testes SDD (pytest)`, caso `test_gates.py::TestGates::test_todos_pass` (gate `rastreabilidade`): precisa de `git log`.
  - As duas reproduzem igual no main original exportado, sem nenhuma mudança minha.
  - Em todos os passos de critérios e drift do painel e da sentidos o resultado foi OK, inclusive `critérios e drift: painel_operacional` (129 critérios).
- Rodada anterior, sobre `21095eaf`: 519 OK, 39 OK (servidor de voz, três rodadas), 140 OK (UI), mutação com 3 testes quebrados como esperado.

Notas:
- O `ci_sdd_local.sh` regrava arquivos rastreados de `redesign/nova_versao/spec/` (`evidence.json`, `criterion-drift.md`) e cria dois em `redesign/sdd_flow/spec/`. Na rodada anterior restaurei os rastreados e removi os criados; nada disso entra no diff.
- Para publicar: o gate de sincronia precisa de histórico git. Ele deve rodar numa checagem com `fetch-depth: 0`, depois que o commit existir.
- Um teste de 413 falhava em uma de três rodadas (reset de conexão). Passou a declarar o `Content-Length` com corpo pequeno.
- Um teste existente (`test_sem_armazenamento_local_na_conversa`) reprovou por causa da preferência do modo conversa. O helper foi para a seção do tema, fora do bloco da Conversa, e a palavra saiu de um comentário do bloco. O teste não foi alterado.

## Decisões para o Humano confirmar

1. **Leitura síncrona.** `POST /api/seth/ouvir` espera a leitura terminar (ou ser interrompida). O progresso sai pelo `GET`.
2. **Parar corta entre partes.** Um parágrafo já tocando termina (até 1.500 caracteres). Corte imediato não foi pedido.
3. **Uma leitura por vez no painel.** Ouvir da Seth e Ouvir da História dividem a trava `historia_painel._FALA_LOCK`. A segunda leitura recebe 429.
4. **Modo conversa com resposta nova durante a leitura.** Para a leitura atual (entre partes) e lê a resposta mais nova depois. Só uma fica na fila. Só a conversa aberta é lida no modo conversa.
5. **Limite de fala.** Texto acima de 12.000 caracteres depois do preparo não é lido. A resposta diz isso (regra do script).
6. **Limite de ditado.** 2 MB no servidor e 60 s no cliente. O servidor não mede duração.
7. **Último uso em memória.** Some quando o painel reinicia.
8. **CSP.** Nenhuma alteração. Não há `media-src`, porque a fala sai pelo player da Máquina.
9. **Preferência do modo conversa em `localStorage`.** Fica fora do bloco da Conversa, junto do tema, que já guarda preferência ali. É um sim ou não, não conteúdo de conversa.
10. **Ouvir e Ditar não são enviados à Seth sozinhos.** O texto ditado vai para o campo; o Humano revisa e envia.

## Publicação

Não publicado nesta rodada. O executor desta rodada não faz commit nem push, e o pedido original dizia "sem publicar". Para publicar, quem tem a permissão faz: branch `proposta/chat-voz-11-11` a partir de `origin/main` (`9b27c1b4`); commit apenas de `propostas/chat-voz-11-11.diff` e `propostas/chat-voz-11-11.md`; registro de canon (entrada `DIÁRIO` em `MEMÓRIAS.md`, no formato dos PRs recentes) num commit à parte, se for o caso; PR contra `main`.

## Não medido

- Fala real pelo piper e transcrição real pelo `servidor_ouvido`: todos os testes usam falsos. Não ouvi a qualidade da voz nem medi a latência real.
- Microfone real: nenhum teste nem captura abriu o microfone. O `getUserMedia` e o `MediaRecorder` são falsos no harness.
- Captura do botão Ouvir numa resposta da Seth: não foi feita. Exigiria uma conversa salva com resposta.
- Captura da linha "voz" na página Sentidos: não foi feita. A página abre por clique na aba, e o `--screenshot` do Chromium não clica.
- Captura em 390 px: a primeira tentativa cortou antes do formulário; a segunda mostra o formulário com janela de 2600 px, que não é uma medida de altura de tela real.
- CI com gate de sincronia e rastreabilidade: não rodou de verdade sobre a base nova, porque a cópia não é um repositório git. Precisa de uma checagem com histórico (`fetch-depth: 0`).
- Navegadores além do Chromium headless (Brave e Firefox não foram usados).
