# Corrige identificador ao salvar conversa (07/11/2026)

- Diff: `propostas/corrige-identificador-conversa-07-11.diff`
- sha256 do diff: `fd3e0fa83b6cbcae5502c59aa44d6dfe54c8d6d9ce9b0cf6a09f79873763c1b5` (9286 bytes, 5 arquivos)
- Base: `origin/main` 83334fde
- Branch sugerida: `proposta/corrige-identificador-conversa-07-11` (worktree `.claude/worktrees/corrige-identificador-conversa`)
- Status: edições no working tree da worktree, SEM commit, SEM push, SEM PR (ver "Pendências")

## Premissa e medição

Premissa do pedido: o POST grava só título e mensagens, sem identificador; o GET devolve sem identificador; o cliente (`sethAbrir`, `prototipo.js`) usa `dados.id`.

Medido no código e na cópia:
- O POST não perde o identificador. O id vem do corpo (`dados.get("id")`) e vira o nome do arquivo. Com id, atualiza; sem id, cria um id novo.
- O arquivo não guarda o id dentro (para conversas criadas pelo painel, as chaves são `mensagens` e `titulo`).
- O GET devolvia o arquivo cru, sem `id`. Por isso `sethAbrir` ficava com `id` indefinido, e o salvamento seguinte criava outro arquivo. O cliente chama `sethSalvar()` após cada resposta da Seth, então a duplicata aparece já na primeira resposta depois de reabrir.

Medição (script `medir_identificador.py`, cópia de 16 conversas, GET por HTTP em servidor local efêmero, salvamento chamando `armazem._conversa_gravar` com o JSON que o cliente manda):

| Cenário | Antes (arquivos) | Depois (arquivos) | Leitura |
|---|---|---|---|
| 1. Importada `0827f803ebdb`: abrir e salvar | 16 → 16 | 16 → 16 | sem duplicata; mas o arquivo perde `id` e metadados de importação |
| 1b. Mesma conversa, reaberta após o 1º salvar | 16 → 17 | 16 → 16 | duplicata antes; corrigida |
| 2. Nova: criar, abrir e salvar | criar 17 → 18; abrir e salvar 18 → 19 | criar 16 → 17; abrir e salvar 17 → 17 | duplicata antes; corrigida |
| 3. Importada com id gravada pela rota: importar, abrir e salvar | importar 19 → 20; abrir e salvar 20 → 21 | importar 17 → 18; abrir e salvar 18 → 18 | duplicata antes; corrigida |

Risco confirmado: abrir e salvar uma conversa cria +1 arquivo (3 de 3 cenários reabertos, antes). Depois da correção, 0.

Nota: o cenário 1 não duplica porque as conversas importadas pela migração trazem `id` dentro do arquivo. Qualquer conversa gravada pela rota (inclusive com id explícito) não traz.

Números completos: `~/agata-documentacao/risco-identificador/medicao-antes.json` e `medicao-depois.json`.

## Correção

- `armazem.py`: nova `_conversa_ler(conversa_id)`. Devolve a conversa com `id` = nome do arquivo; `None` se o id é inválido, o arquivo não existe ou não é JSON de objeto.
- `server.py`: `GET /api/seth/conversa?id=` usa `_conversa_ler`. Responde 404 se ausente ou ilegível (antes devolvia bytes crus).
- Rota de salvar (`_conversa_gravar`): sem mudança de código. Com `id` atualiza o arquivo; sem `id` cria um novo. O contrato está coberto por teste que passa antes e depois.
- `prototipo.js`: sem mudança. `sethAbrir` usa `dados.id`, que agora vem preenchido.
- Spec: uma linha no Contrato; critério novo `a conversa reaberta e salva mantém o identificador e não duplica` em `spec/acceptance.json` e checkbox idêntico em `spec/spec.md`. Os 16 critérios anteriores não mudaram (17 critérios e 17 checkboxes, mesmos textos).

## Testes

Antes da correção (código de origin/main + testes novos):
- `HttpTests::test_conversa_reaberta_e_salva_mantem_o_identificador`: FALHA (`KeyError: 'id'` no GET).
- `HttpTests::test_salvar_com_id_atualiza_e_sem_id_cria_um_novo`: passa (contrato de salvar já correto).
- Suíte `redesign/painel_operacional` sem alterações: 131 passed, 65 subtests passed.

Depois da correção:
- Os dois testes novos: 2 passed.
- Suíte `redesign/painel_operacional`: 133 passed, 65 subtests passed.
- CI local: `PYTEST=/home/orusoua/.cache/uv/archive-v0/0obnOoJtclHllQl_/bin/pytest bash scripts/ci_sdd_local.sh` → `CI LOCAL: TUDO OK` (exit 0; 33 passos OK, 0 FALHA, inclusive âncora dos componentes e drift de critérios do painel).

Os testes usam diretório temporário criado pelo próprio teste (`tempfile.TemporaryDirectory`), nunca `~/.cache/agata/painel-conversas`.

## Comandos

- Medição: `python3 medir_identificador.py <worktree>/redesign/painel_operacional <cópia> antes|depois` (cópias em `~/agata-documentacao/risco-identificador/`: `antes-limpa-painel-conversas`, `depois-limpa-painel-conversas`).
- Testes: `pytest -q -p no:cacheprovider redesign/painel_operacional`.
- CI: `PYTEST=<pytest> bash scripts/ci_sdd_local.sh`.

## Pendências e não medido

- Metadados de importação somem no primeiro salvamento pelo painel: `origem`, `origem_id`, `data_original`, `importado_em`, `titulo_original` (medido nas chaves do arquivo: antes `data_original, id, importado_em, mensagens, origem, origem_id, titulo, titulo_original`; depois do salvar `mensagens, titulo`). Não corrigido: fora do pedido. Não medido: se a migração usa `origem_id` para não reimportar; se usa, reimportar pode duplicar.
- Salvar com `id` fora do formato (12 hex) responde 400 e o cliente ignora (`sethSalvar` só trata `r.ok`). Lido no código, não medido no navegador.
- Não medido no navegador: o teste de navegador e de HTTP foi só GET. O salvamento foi feito por função, não por POST HTTP.
- Não commitado, sem push e sem PR: a regra do ambiente de execução proíbe commit e push pelo agente. Se o commit regravar âncoras SHA em canon pelo pre-commit, o corpo do PR precisa dizer isso. Não verificado.
- Checks do PR no GitHub (fiscal-p8, suite-adversarial, CodeQL): não rodados aqui.
