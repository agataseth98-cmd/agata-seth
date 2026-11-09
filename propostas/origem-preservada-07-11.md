# Proposta origem-preservada-07-11

Data da proposta: 07/11/2026. Base revalidada: `origin/main` `ed28bd2c` em 09/11/2026. O diff aplica sem conflito nessa base.
Decisão do Humano (07/11/2026): "sem duplicar, sim".
Não commitado, não juntado, não assinado. O agente de CI faz o commit a partir do diff.

## Problema

O salvar de conversa (POST /api/seth/conversa, usado por prototipo.js no salvar e no renomear) grava só id, titulo e mensagens (role, content). Ao salvar uma conversa importada do LibreChat, perdem-se origem, origem_id, titulo_original, data_original, importado_em, o id interno do arquivo e, por mensagem, criada e origem_id. Ao salvar sem id com origem, nenhuma regra reconhecia a origem já presente.

## Medições antes e depois

Cópia isolada: ~/agata-documentacao/origem-preservada/ (medir_origem.py, sha256 aee1e87c49310043c6d86c1485952f5bf34ebf7dff5eaeb6818813cce6fe0122). Armazém real não lido além da contagem (16 arquivos) e de uma impressão digital de metadados (nome, tamanho, mtime), idêntica antes e depois. Importação replicada a partir de migrar.py (planejar, estado_armazem, gravar_no_armazem), sem gravar LOG, SNAPSHOT nem EXCLUIDAS. O salvar usa um servidor de teste em porta efêmera com o Handler de server.py.

Cenário A (importar 2x, salvar como o cliente, importar de novo):
- Antes (medicao-antes.json): salvar 200. Campos ausentes após salvar: origem, origem_id, titulo_original, data_original, importado_em. Chaves do arquivo: mensagens, titulo. Mensagens: content, role. Reimportação: abortada por conflito (1 conflito, nada gravado). Arquivos: 1. Importação sem salvar: 1 criada, depois 1 pulada, 1 arquivo.
- Depois (medicao-depois.json): salvar 200. Campos ausentes: nenhum. Chaves: data_original, id, importado_em, mensagens, origem, origem_id, titulo, titulo_original (as mesmas do importador). Mensagens: content, criada, origem_id, role. Reimportação: ok, 0 criadas, 1 pulada. Arquivos: 1.

Cenário B (importar, POST do objeto inteiro com origem e sem id, importar de novo):
- Antes: POST 200; 2 arquivos (um com origem, outro sem origem com o mesmo conteúdo). Reimportação: 1 pulada. Arquivos finais: 2.
- Depois: POST 200; 1 arquivo (reaproveita o arquivo com a mesma origem). Reimportação: 1 pulada. Arquivos finais: 1.

Cenário C (mensagem de 8001 caracteres):
- Antes e depois: salvar responde 400; arquivo íntegro; reimportação: 1 pulada. Não tratado nesta proposta (ver "Ficou de fora").

Versão intermediária descartada (lojas-descartadas/medicao-depois-v1.json, fora do repositório): sem a chave id dentro do arquivo. O verificador do importador (migrar.py, modo_verificar) compara atual.get("id") com o id esperado; por isso a correção passou a gravar o id.

## Mudança

- redesign/painel_operacional/armazem.py: novas funções _origem_valida, _conversa_lida, _conversa_com_origem, _origem_do_arquivo, _mensagens_com_origem; _conversa_gravar passa a (1) reaproveitar o arquivo que já tem a mesma origem e origem_id, (2) manter a origem já gravada no arquivo, (3) manter criada e origem_id das mensagens que continuam no mesmo lugar, com o mesmo papel e texto, (4) gravar o próprio id quando há origem. Campos de origem vindos de fora são validados por tipo e tamanho; o que não couber sai, sem derrubar o salvar.
- redesign/painel_operacional/test_painel.py: 5 testes novos em HttpTests, antes de test_conversa_valida_e_grava_so_formato_esperado: test_salvar_do_cliente_preserva_a_origem_da_importacao, test_salvar_com_origem_ja_presente_reusa_o_arquivo_sem_criar_outro, test_origem_do_arquivo_nao_e_reescrita_por_salvar, test_campos_de_origem_invalidos_saem_e_o_salvar_continua, test_cliente_abre_renomeia_pela_api_e_a_origem_fica.
- redesign/painel_operacional/server.py: não alterado.

## Testes

- Antes da correção (recorte -k "origem or cliente_abre"): os 5 testes novos falham; os outros 5 do recorte passam.
- Depois: suíte do painel, pytest 9.2.0, `pytest -q -p no:cacheprovider redesign/painel_operacional` → 136 passed, 65 subtests passed.
- CI local: `PYTEST=/home/orusoua/.cache/uv/archive-v0/0obnOoJtclHllQl_/bin/pytest bash scripts/ci_sdd_local.sh` → CI LOCAL: TUDO OK (todos os passos OK).
- Revalidação em 09/11/2026 com o diff aplicado sobre `ed28bd2c`: suíte do painel 162 passed, 118 subtests passed; CI local `TUDO OK`, exit 0.
- O CI local regravou criterion-drift.md e evidence.json de nova_versao/spec e sdd_flow/spec. Foram revertidos (git checkout) ou tirados do caminho; não entram no diff.

## Diff

propostas/origem-preservada-07-11.diff: 12126 bytes, sha256 0c0be5bffb60701fafdd8aaef0f2be0f4438475f08643e1ffc2303885fa91963.
Conferido com `git apply --cached --check` sobre origin/main, em índice temporário (a worktree não foi tocada): aplica.

## Sobreposição avaliada com proposta/corrige-identificador-conversa-07-11

**Estado atual, 09/11:** PR #945 está fechada; seu diff publicado contém apenas os artefatos da proposta e âncoras, sem aplicação de código. A verificação atual deste diff sobre `ed28bd2c` passou. As observações abaixo registram a comparação feita na proposta original, quando o estado era diferente.

Lido no worktree corrige-identificador-conversa (mudanças não commitadas, base 83334fde). A outra proposta toca armazem.py, server.py e test_painel.py.

- armazem.py: a outra insere _conversa_ler nas linhas 96-101 da base (depois de _conversas_listar). Esta proposta altera as linhas 113-126 da base (fim de _conversa_validar e _conversa_gravar). Nenhuma linha em comum, 11 linhas de distância. Aplica nas duas ordens sem conflito (testado com índices temporários).
- server.py: só a outra altera (import, linhas 39-41; GET, linhas 1041-1047). Esta proposta não toca server.py. Sobreposição: nenhuma.
- test_painel.py: a outra insere nas linhas 511-515 da base (fim da classe). Esta proposta insere nas linhas 496-501 da base. Nenhuma linha em comum. Aplica nas duas ordens sem conflito.
- Ponto a decidir na junção: o teste da outra cria o arquivo a1b2c3d4e5f6.json sem a chave id dentro e diz que é como a importação grava. O importador (migrar.py, mapear e gravar_no_armazem) grava a chave id dentro do arquivo. Esse teste não reflete o importador. Esta proposta não depende de _conversa_ler.

## Ficou de fora

- A importação (migrar.py, em ~/agata-documentacao/migracao-librechat, fora da lista desta tarefa) continua reconhecendo só pelo nome do arquivo (estado_armazem). A regra por origem_id está apenas no salvar do painel (_conversa_com_origem). Para a importação reconhecer por origem_id, é preciso alterar migrar.py: decisão do Humano.
- Mensagens acima de 8000 caracteres: o importador gravou 11 mensagens assim (migracao.log, simular), e o salvar responde 400. Essas conversas não podem ser renomeadas nem salvas pelo painel. Não tratado.
- Apagar uma conversa importada no painel e reimportar recria o arquivo (inferência do código de estado_armazem; não medido).
- criada e origem_id por mensagem só são mantidos quando a mensagem continua na mesma posição com o mesmo papel e texto. Mensagens novas não os recebem.
- Não medido: a interface no navegador; o conteúdo do armazém real; migrar.py --verificar (lê o armazém pelo caminho padrão); reimportação real contra o LibreChat (docker não usado).
