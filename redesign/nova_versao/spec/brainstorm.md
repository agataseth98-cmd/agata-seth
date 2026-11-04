# Brainstorm — nova versão (Experimento GPT)

Leitura integral da pasta em 04/11/2026: `conclusoes.md` (001–080), Alexandria, metacognição, avaliação, contrato, fundamentos, inventário, matriz de redundância, skill do experimento, briefings, fontes, transcrição e scripts da auditoria.

## O que a pasta pede

- Memória externa governada e substituibilidade de LLM (060–062, 066).
- Biblioteca operacional: acervo com proveniência, busca local primeiro e externa para atualidade (068–075).
- Seleção de skills separada da busca em documentos (063–065).
- Metacognição como controle do laço: antes, durante e depois (026–029); contar limites combinados (013); "problema" polissêmico (014).
- Consciência operacional: o corpo material entra no raciocínio sobre o que se pode fazer (034–036).
- Redundância real, testada por capacidade (043–047); paralelismo com orçamento e sincronização (048).
- Papéis com escopo, nunca posse (054–055); nada de uma LLM por "área cerebral" (039–040).
- Avaliação independente, com baseline, split reservado e métricas por dimensão (018, 024, 037–038).
- Sete palavras como ciclo, com Remoção opcional (032, 057–059).

## O que já existe e evita código novo

Hidratação, vault, índices, cache do Conselho, memória semanal, fila de revisão do inbox, auditoria do turno, sombras do gateway, `evidence_ledger`, `sdd_flow`, medidores e o painel. Lacunas medidas: nenhum acervo com hash por objeto, nenhum FTS, três índices de skills desconexos, nenhum registro de antes do turno nem de saúde datada, nenhum `run_id` comum nos medidores.

## Achados da entrada 021, conferidos em 04/11

1. Instruções de assinatura divergentes: não reproduzido (README de propostas e AGENTS.md coincidem).
2. Atualização que descarta mudanças: não reproduzido (`scripts/atualizar.sh` recusa árvore suja e manda usar `git revert`).
3. `agata-carregar` chamava de read-only um script que grava cache: confirmado; corrigido neste lote.

## Usuários

O Humano (painel, decisões de orçamento e assinatura) e os modelos do sistema (Seth pelo gateway; Claude Code, Codex e Gemini pela CLI), que consultam o acervo e passam pela metacognição.

## Estado que muda

Só fora do repo: `AGATA_NV_DIR` (pastas de trabalho, ledger, sombra, fotografias, orçamento) e `AGATA_NV_CACHE` (índice derivado). No repo, só o código e as specs desta proposta.

## Erros e concorrência

Ledger único com `flock` e chave idempotente; índice trocado atomicamente; sombra com Semaphore(1) que pula se ocupada; lock por ação no painel; semântica fora do ar degrada para léxico com aviso; erro de componente na sombra vira campo `erros`.

## Migração

Nenhuma no canon. O acervo é um snapshot do repo por commit; reindexar é reconstruir.

## Observabilidade

Painel, grupo "Nova versão" (quatro páginas); `nv.py estado`; eventos no ledger (`iniciar`, `snapshot`, `indexar`, `drift`, `orcamento`); `sombra.jsonl`.

## Reversão

Revert do commit de aplicação; apagar `AGATA_NV_DIR` e `AGATA_NV_CACHE`; a sombra nasce desligada.

## Sucesso

Lote 1: testes e âncora verdes na CI, painel funcionando no navegador, consulta real com evidência e sombra que não altera a resposta. Valor da nova versão: só o lote 3 mede, contra baseline, em conjunto reservado.
