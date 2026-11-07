# Tira o LibreChat dos atalhos e do P-9

**Proposta:** tira-librechat-07-11 · **Data:** 07/11/2026 · **Base:** origin/main 83334fde
**Status:** completa para assinatura do Humano. O commit sai pelo agente de CI, não por este registro.

**Exclusão:** o Humano excluiu hoje, 07/11/2026 às 13:22, os contêineres e os volumes do LibreChat (`librechat`, `librechat-mongodb`, `librechat-meilisearch`, `librechat-ponte-host`). Sem esta proposta, o atalho `seth` roda `docker compose up -d` em `~/librechat` e recria o LibreChat vazio.

**sha256 do `.diff`:** `3cfdd1457c38dc9dbc34d1a9b105fde7c017249efaf31e0317b3002526e4fdad` (`propostas/tira-librechat-07-11.diff`, 222 linhas, gerado contra origin/main 83334fde).

## O que muda (5 arquivos)

- `redesign/systemd/seth`: sai a variável `LC`; sai o bloco que copia `librechat.yaml`, `docker-compose.yml`, `canon-mcp.mjs` e `agata-tema.css` para `~/librechat/`; saem `docker compose up -d`, `docker restart librechat`, a espera pelo `/health` em `:3080` e a notificação "LibreChat". Comentários de cabeçalho e do Chromium ajustados. Não muda: `agata.target`, gateway, escriba, verificador, painel, MCPs Discord e navegador, Piper, vigias, Chromium.
- `redesign/systemd/seth-parar`: saem `LC` e `docker compose stop`. Não muda o resto (vigias, Obsidian, Chromium, descarga do Ollama, `agata.target`).
- `scripts/perimetro.sh`: `P9_CONTAINERS_DOCKER` passa a `()`. Saem os quatro nomes do LibreChat. Com a lista vazia, o P-9 não chama o `docker`.
- `scripts/testar_cobertura_servicos.py`: linhas 38-42 trocadas. Antes, a contraprova exigia que o P-9 acusasse `librechat-ponte-host` ausente. Agora o docker simulado não tem contêineres e a asserção confere que a saída não cita `librechat`. Resto do arquivo igual. Mudança autorizada pelo orquestrador (Humano: "nada fica para depois"), no mesmo diff.
- `scripts/testar_tira_librechat.py` (novo): 5 testes unittest. Falham se `seth` ou `seth-parar` tiverem, em linha de código, `docker compose/restart/start/stop/up/run`, a palavra LibreChat, `LC=`, caminho `~/librechat`, `docker-compose.yml` ou a porta 3080. Conferem que gateway, `agata.target`, Piper e `ollama stop` continuam. Rodam `bash -n` nos dois atalhos. Conferem que `P9_CONTAINERS_DOCKER` existe e não cita LibreChat.

## Não muda (de propósito)

- `redesign/librechat/` inteiro: histórico e fonte de referência. Continua sendo lido por `scripts/testar_net02_compose.py`, `scripts/testar_fork_librechat.py` e `redesign/router/auditoria_turno.py`.
- `~/librechat/` (com `.env` e backups): não tocado.

## Referências que ficaram (não editadas), com efeito

- `scripts/equipe/vigia.sh` linhas 31 e 56: `docker inspect librechat` a cada ciclo; ao mudar de estado avisa `LIBRECHAT: ...`. Depois da exclusão dá "fora" e avisa uma vez. Só verifica.
- `scripts/seth_golden.py` linha 220: `docker exec librechat-mongodb mongosh` (só leitura). Falha sem o contêiner.
- `scripts/perimetro-sombra-referencia.sh` linhas 1052-1108: cópia congelada do perímetro, com a lista antiga. Não é chamada pelo perímetro atual.
- `scripts/perimetro/p04_bind.sh` linhas 52-53: comentário sobre a ponte `librechat-ponte-host`. Sem efeito de execução.
- `redesign/librechat/aplicar_agente_seth.sh` linha 8: comentário com `docker restart librechat` (script manual, fora dos atalhos).
- `redesign/painel_operacional/server.py` linhas 536 e 925, `prototipo.js` linha 1026 e `prototipo.html` (botão LibreChat): sondam `:3080/health` e mostram o estado no painel. Só verificam.
- `PROJETO.md` linhas 37, 38, 43, 80 (seção Serviços (boot)) e 111: o canon ainda descreve o stack do LibreChat e diz que o `seth` sincroniza e reinicia o contêiner. Mudar o canon exige proposta própria (P-8). Até lá, canon e código divergem.
- `config/caminhos-framework.txt` linha 71 (`externo|~/librechat/`): lista de caminhos. Efeito não medido.

## Testes (com as edições, na worktree)

- `scripts/testar_cobertura_servicos.py`: `COBERTURA SERVICOS OK -- 11/11`, exit 0 (antes da proposta também 11/11). Controle: contra o `scripts/perimetro.sh` original, a nova asserção falha e lista os quatro contêineres, então ela detecta a lista antiga.
- `scripts/testar_p9.sh`: exit 0, "P-9: OK".
- `scripts/testar_tira_librechat.py`: 5 passed (pytest). Contra o origin/main original: 3 falhas (seth, seth-parar, P9).
- `scripts/ci_sdd_local.sh` (PYTEST da uv): 33 OK, "CI LOCAL: TUDO OK", medido antes da troca em `testar_cobertura_servicos.py`. O CI local não roda `scripts/testar_*.py`, então esse arquivo não entra nele.
- O CI local reescreve artefatos de spec dentro da worktree (`redesign/nova_versao/spec/criterion-drift.md`, `redesign/nova_versao/spec/evidence.json` e os dois arquivos criados em `redesign/sdd_flow/spec/`). Isso não entrou no `.diff`.

## Aplicação

O `.diff` cria `scripts/testar_tira_librechat.py`. Quando o PR for aberto, o corpo deve dizer que o hook regrava âncoras SHA.
