# Chat do painel, lote 1: substitui o uso diário do LibreChat

Registro da proposta `proposta/chat-lote1-07-11`. Base: origin/main 83334fde. Worktree: `.claude/worktrees/chat-lote1-07-11`. Nada commitado. Nada assinado. `scripts/aprovar.sh` não foi rodado.

## Artefato

- Diff: `propostas/chat-lote1-07-11.diff`, contra origin/main 83334fde, 40 arquivos.
- sha256 do diff: `9a026061e83bed2f6effe46c45aa148862733a7079d8644ba68abfce3235d3c9`
- Tamanho: 580006 bytes.
- Inclui o diff do painel unificado (`painel-unificado-07-11.diff`, sha256 9a3b5734d1dab510efa2e405e608099afcc98c940dbd5ac85ac8f07eef45db26), aplicado limpo antes do lote. O lote é um só, por decisão do orquestrador.
- Fora do diff: os artefatos gerados pelo CI na worktree (`redesign/nova_versao/spec/evidence.json`, `criterion-drift.md`, e os do `sdd_flow`), revertidos.

## O que entrou

- Rota automática (gateway, `redesign/router/seth_gateway.py`, `rota_regras.py`, `config/rotas/regras.json`). O painel manda só `automatico`, que vira o gatilho `seth-auto`. Regras T1, L1, R1, R2, R3 em arquivo versionado, com carga que recusa o que está fora do conjunto. Modificadores M1 (`-longo`) e M2 (disponibilidade com alternativas e `fallback`). Registro de uma linha por resposta com a regra que decidiu, sem texto do usuário. `seth-livre` pedido às claras vira fila fixa, sem regra.
- Painel (`redesign/painel_operacional/`): rota `automatico` nos dois endpoints (400 para outro valor, antes do gateway); evento `meta` (fila, modificador, regra, modelo) antes do primeiro texto; `POST /api/seth/chat` devolve os mesmos campos; botão Parar resposta (AbortController; a resposta parcial fica marcada como interrompida); aviso visível quando a conversa passa de 20 mensagens; o pedido leva só as 20 últimas, e trecho acima de 4000 caracteres vai cortado com marca; texto que não se perde (em falha de envio, a mensagem sai da conversa com aviso e o texto volta ao campo); linha de fila, regra e modelo em cada resposta, ou "não medido"; limite de mensagem explícito de 65536 caracteres no armazém (antes 8000), com os campos novos da resposta validados.
- Correção de bug existente, necessária para o uso diário: abrir conversa salva dava INDISPONÍVEL em origin/main, porque a leitura devolvia o arquivo sem `schema_version`, e `fetchJson` recusa essa resposta. Medido no navegador antes da correção. Agora `_conversa_ler` devolve `schema_version`, `id`, `titulo` e `mensagens`. Os arquivos não mudam. Afeta as 16 conversas importadas.
- Tamanho do fallback `POST /api/seth/chat`: de 16384 para 131072 bytes, igual ao stream.
- Testes e critérios: 14 critérios do lote 1 e o de reabrir conversa entram em `redesign/painel_operacional/spec/acceptance.json` e no `spec.md`, cada um com comando de teste que existe. Os testes de gateway (`redesign/router/test_rota_regras.py`) também estão nesses comandos. `chat/spec/` não está nesta worktree, então o mapeamento fica aqui.

## Testes (saída real, última rodada)

- Painel: `pytest -q redesign/painel_operacional` → 187 passed, 132 subtests passed (pytest -q redesign/painel_operacional, 7,6 s)
- Gateway: `pytest -q test_rota_regras.py test_relay_council_contract.py` em `redesign/router` → 46 passed, 10 subtests passed.
- Selftest do gateway: `python3 seth_gateway.py --selftest` → SELFTEST OK.
- CI local: `PYTEST=… bash scripts/ci_sdd_local.sh` → CI LOCAL: TUDO OK, 33 passos OK, rodada final com o critério de reabrir conversa
- Combinado com origem-preservada: lote mais o diff de trabalho de origem-preservada aplicados juntos → painel 192 passed (187 do lote, mais 5 de origem-preservada).

## Medição no navegador

Chromium headless (perfil `~/agata-documentacao/painel-unificado/perfil-chromium`), CDP, sem script inline (verificado). Capturas em `~/agata-documentacao/chat-lote1/`. Números em `~/agata-documentacao/chat-lote1/medicao.json` e `medicao-parar-stream-vivo.json`.

Gateway de medição: `seth_gateway.py` do worktree na porta 20126, com upstream falso local (`fake_upstream.py`, porta 20190) no lugar de OmniRoute. Nenhum provedor de modelo foi chamado. Painel do worktree na porta 20247 (conversas isoladas em `~/agata-documentacao/chat-lote1/conversas-medicao`, fora do cache real).

- Envio normal (cadeia real): resposta em 1213 ms. Primeira linha começa com `agata-seth ·`; segunda `Última entrada:`; terceira `pronto.`. Linha de campos: `Fila seth-rapido · regra rapido_trivial · modelo fake/medicao-local`.
- Janela de 20 mensagens: aviso visível ("Ela tem 22"). O pedido levou 20 mensagens e `rota: "automatico"`. 2 mensagens longas foram cortadas (maior no pedido: 3942 caracteres). As 5 mensagens antigas sem campos mostram "não medido"; as 6 com campos mostram os valores. A conversa de 22 mensagens foi reaberta e gravada.
- Falha de envio simulada (interceptação: stream e fallback, 2 pedidos falhos): mensagem do usuário saiu da conversa (12 → 12); texto voltou ao campo; aviso "Não enviada: sem conexão com o painel. O texto voltou ao campo."; reenvio ok.
- Parar com stream ao vivo (gateway de teste `gateway_vivo.py`, porta 20248, sem retenção): primeiro texto em 513 ms; botão visível durante o stream; 81 caracteres no clique e 81 dois segundos depois (o texto parou); nota "Resposta interrompida. O texto recebido ficou salvo."; linha de campos mantida; envio liberado em 1 ms; segunda pergunta sem busy.
- Parar na cadeia real: não atuou. A resposta de 30 s chegou inteira aos 30,1 s, porque o gateway retém o stream para o verificador (ver "Achado"). No clique, a resposta já estava completa (1354 caracteres) e o botão já estava escondido.
- Limite de mensagem (rota de gravação): 18973 caracteres → HTTP 200; 65537 caracteres → HTTP 400.
- CSP e DOM: 0 atributos `style`, 0 `on*`, 0 scripts inline, 0 tags `style` na página. Cabeçalho: `default-src 'none'; script-src 'self'; style-src 'self'; …`. Console: 5 entradas, nenhuma violação de CSP. As entradas: 2 "Password field is not contained in a form" (recomendação do navegador, campo que já existia), 1 favicon 404 (já conhecido), 2 `ERR_CONNECTION_FAILED` causadas pela interceptação de propósito. localStorage: uma chave (`agata-sidebar-collapsed`); nenhum texto de conversa em storage.
- Capturas: `01-conversa-inicial.png`, `02-resposta-com-cabecalho-e-campos.png`, `03-parada-texto-marcado.png` (cadeia real), `03-parada-stream-vivo.png`, `04-janela-20-mensagens.png`, `05-janela-resposta-gravada.png`, `06-falha-envio-texto-volta.png`.

## Achado que muda o contrato (decisão para o Humano)

O gateway retém a resposta dos modelos `seth-*` até o fim do upstream, para o verificador (`_reter`, `_enviar` e `_liberar_retidos` em `seth_gateway.py`, ligados por padrão em `SETH_VERIFICACAO_BLOQUEIA`). Medido: a resposta chega inteira no fim. Três rodadas com 15,1 s, 30,1 s e 60,1 s de upstream confirmam. Com isso, a jornada "ver a resposta chegar aos poucos" e o botão Parar não funcionam pela cadeia real. O painel está correto: com stream vivo, Parar funciona (medido acima). O Humano decide: manter a retenção (verificação antes de mostrar) ou liberar o stream e verificar o que já chegou.

## Não medido

- Parar pela cadeia real com resposta ainda sendo gerada (a retenção impede).
- Se o gateway cancela o upstream após o Parar. Não medido; pelo código, a geração segue até o fim.
- Janela de 429 "busy" logo após Parar na cadeia real. Não medido, pelo mesmo motivo.
- Qualidade das respostas, precisão da regra automática e se `seth-codigo` responde melhor que `seth-pesado` (R1). Não medido. Nenhum modelo real foi chamado.
- Taxa de respostas com o formato da D3 (Evidência, Próximo passo). Não medido; sem checker mecânico.
- Gravação de conversa acima de 262144 bytes (o POST leva a conversa inteira; a rota responde 413). Não medido. O aviso de gravação não salva está pronto.
- Unidade `seth-gateway.service`: não subida. Motivos: `ExecStart` aponta para `~/agata/redesign/router/seth_gateway.py` (main, sem `seth-auto`); tem `Requires=omniroute-sanitizer.service`, que tem `Wants=omniroute.service`. Subir a unit ligaria a cadeia até OmniRoute e provedores reais, o que a regra de não chamar provedor proíbe. Para medir pela unit: merge (não feito) ou drop-in apontando para o worktree (mudança de config do usuário, fora da lista).
- Visual em 390 px e rolagem da conversa longa.
- PR #945: os testes dele não foram rodados contra este lote (ver Sobreposições).

## Sobreposições

- PR #945 (`proposta/corrige-identificador-conversa-07-11`, aberta, não aplicada): conflito textual com este lote em 4 pontos. (1) `armazem.py`: ambos definem `_conversa_ler` com o mesmo nome. A versão deste lote tem `schema_version` (obrigatório para `fetchJson`); a de #945 não tem. Na junção, manter a deste lote. (2) `server.py`: o import e a rota GET de `/api/seth/conversa?id=` (mesmas linhas). Manter a deste lote. (3) `spec/acceptance.json`: ambos acrescentam entradas no fim. (4) `spec/spec.md`: ambos acrescentam uma linha no contrato. Os testes de #945 (`test_conversa_reaberta_e_salva_mantem_o_identificador`, `test_salvar_com_id_atualiza_e_sem_id_cria_um_novo`) estão no fim de `HttpTests` (`test_painel.py`); não conflitam com este lote, mas não foram rodados.
- origem-preservada (`proposta/origem-preservada-07-11`, sem commit, alterações de trabalho em `armazem.py` e `test_painel.py`): `git apply --check` limpo sobre este lote. Aplicado por cima do lote, a suíte do painel passa (192 passed). Sobreposição textual no mesmo bloco de `armazem.py` (validação e `_conversa_gravar`), compatível.
- painel-unificado-07-11: incluído no diff (combinado).

## Divergências em relação à spec do chat

- Limite de mensagem: a spec dizia "11 conversas importadas têm mensagens acima de 8000". A medição dá 4 conversas com 11 mensagens acima de 8000 (maior: 18973 caracteres). Limite novo: 65536.
- `seth-livre` pedido às claras agora é fila fixa (spec, D2). Clientes que mandam `seth-livre` deixam de ter rota automática. Não medido quantos.
- Regra R1 (cerca de código → `seth-codigo`) muda o comportamento da heurística antiga (`seth-pesado`). Não medido se é melhor.
- Gatilho `seth-auto` e evento `meta` dependem do gateway deste lote. Com o gateway de main, o painel cai para `não medido` na regra (fila vem do cabeçalho `X-Seth-Rota` que já existe).
- Limite de envio por mensagem continua 4000 caracteres (`montar_pedido`, critério existente). Mensagens antigas acima disso entram cortadas no pedido, com marca.

## Não feito, do lote 1

- Checker mecânico do formato da resposta (Evidência, Próximo passo): fica para o lote seguinte, com amostra medida.
- Regra do Goose no painel (`prototipo.html`, cartão): fora do lote 1.
- Chip "LibreChat" na lista de serviços da barra lateral (visto na captura): pré-existente no painel unificado; sai com o critério de remoção do LibreChat, não com este lote.
- `chat/spec/` (spec de origem) não está no worktree; o mapeamento de critérios está em `spec/acceptance.json` do painel.
- Os testes de gateway (`redesign/router/`) não rodam em `ci_sdd_local.sh`; rodam pelos comandos de `acceptance.json`. Não há `spec/` para `redesign/router` (D-Gateway pendente).

## Decisões pendentes do Humano

1. Retenção do stream pelo verificador (ver "Achado").
2. Aceitar a mudança de `seth-livre` (fila fixa) e a regra R1.
3. Junção com #945: manter `_conversa_ler` deste lote.
