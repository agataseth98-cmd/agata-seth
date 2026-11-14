# Decisão

DECISAO: aceita

Data: 07/11/2026. Decidido pelo Humano, em conversa de 07/11/2026. O time de inovação não decide (regra do time, agata-time-inovacao). A linha "DECISAO: aceita" foi escrita por um agente de implementação, por instrução do orquestrador, com as decisões do Humano; a versão anterior desta regra dizia que modelo não escreve a marca de aceite. O portão real continua a assinatura P-8 do Humano: nenhum modelo roda scripts/aprovar.sh.

Registro da proposta: propostas/nucleo-desenvolvimento-07-11.md (PR de proposta, sem assinatura).

## Decisões do Humano (07/11/2026)

D1. Todos os modelos do Conselho recebem o ponteiro do AGENTS.md e do índice. Aceita (07/11/2026, decidido pelo Humano).

D2. O ponteiro vai ao gateway, pelo canal de estado de `_injeta`, nas faixas internas (Seth, Goose e o que passa pelo gateway). A saída é SETH_PROCESSO_HIDRATA=0. Aceita (07/11/2026, decidido pelo Humano). Efeito: C11a e C11b ficam no acceptance.json.

D3. Orçamento de contexto, equilibrando custo e desempenho. Aceita (07/11/2026, decidido pelo Humano): ponteiro no AGENTS.md de até 200 bytes; guia agata-fluxo de até 8 KB; linha do gateway de até 200 caracteres.

D4. Dono e revisor do guia agata-fluxo, por critério de função. Aceita (07/11/2026, decidido pelo Humano).
- Dono: agata-spec (escreve e mantém a especificação do processo).
- Revisor: agata-revisor (somente leitura, independente de quem escreveu).
- Justificativa: quem escreve a regra não a revisa. O dono tem a função de especificar; o revisor só lê e não grava, o que separa a escrita da conferência.

D5. Uma proposta só: spec, código, testes e CI, com uma assinatura. Aceita (07/11/2026, decidido pelo Humano).

D6. A faixa pública fica de fora. Aceita (07/11/2026, decidido pelo Humano). O gateway já tira o sistema e o histórico oculto nessa faixa (`_preparar_payload_publico`, que não chama `_injeta`).

D7. Memórias do sistema (MEMÓRIAS.md) entram só de duas formas. Aceita (07/11/2026, decidido pelo Humano):
(a) pelo timer do cache, que destila fatos e pendências já verificados; (b) em momentos extremamente importantes, e só com assinatura do Humano.
Os critérios de destilação vêm da medição do sistema, não de opinião. Esta regra está escrita no guia agata-fluxo, seção "Memória do Conselho e MEMÓRIAS.md".

D8. A proposta NÃO depende da PR #944. O texto dos 11 pontos de regras de lote fica dentro do próprio guia agata-fluxo, e o teste de ids (C9) confere os ids dentro desse mesmo arquivo. Aceita (07/11/2026, decidido pelo Humano). Efeito: C9 passa sem esperar a #944; a aplicação da #944 continua outro lote.

D9. Pasta redesign/nucleo-desenvolvimento (P-8). Aceita (07/11/2026, decidido pelo Humano).

D10. Nomes, com termos da mitologia egípcia, com respeito. Aceita (07/11/2026, decidido pelo Humano):
- Ma'at: guia universal (ordem e verdade). É o agata-fluxo.
- Ptah: núcleo de construção (artífice).
- Thoth: canal da equipe, para escrita e registro. Hoje é o que a skill agata-fluxo-equipe e scripts/equipe/equipe.py fazem; esta proposta não renomeia código.

## Medido nesta proposta (não é decisão)

- Lacunas L1 a L6 da spec continuam abertas. A aceitação das decisões não as fecha.
- A entrada de registro em MEMÓRIAS.md (lição i) não entra no diff desta proposta. Fica como pendência do PR de proposta.

## Revisão de 14/11/2026 (proposta refeita sobre origin/main 86704396)

Decisão do Humano, 14/11/2026: "refazer v2, manter o agata-fluxo consolidado; D3 do guia revogada". A v2 mantém o `.agents/skills/agata-fluxo/SKILL.md` consolidado do main (entrada única, da consolidação de 12/11) e acrescenta só o que é novo do guia Ma'at: nomes (D10), dono e revisor (D4), regra de MEMÓRIAS (D7), regras de lote (resumo), ids de lição e o que os testes exigem.

- D3 do guia revogada: o teto do `agata-fluxo` passa a 24 KiB (teste `test_d3_guia_ate_24_kib_decisao_14_11`). O teto de 8 KiB de 07/11 não vale mais para o guia. Continuam valendo: ponteiro do AGENTS.md até 200 bytes e linha do gateway até 200 caracteres.
- D4, medido em 14/11/2026: `.claude/agents/agata-spec.md` e `.claude/agents/agata-revisor.md` existem no main. O revisor é somente leitura (`tools: Read, Grep, Glob, Bash`, sem Edit/Write).
- D8, medido em 14/11/2026: a pasta `.agents/skills/agata-processo-lote/` não existe mais no main (consolidação de 12/11, em `agata-aplicar-proposta`). O resumo do guia aponta para `agata-aplicar-proposta`, e a lista de skills de processo do teste C8 passou a ser `agata-fluxo`, `agata-aplicar-proposta` e `agata-time-inovacao`. Os ids e, f, i, l e m continuam definidos dentro do guia (D8); a fonte de cada um está em `agata-aplicar-proposta`, seção "Lições medidas em 07/11/2026".
- D10, medido em 14/11/2026: Thoth é hoje a skill `agata-equipe` (consolidação de 12/11), não `agata-fluxo-equipe`. Ptah e Ma'at não têm skill própria; Ma'at é este guia.
- Ponteiro do AGENTS.md (C1): fica num parágrafo antes de "**Sempre:**", e não como bullet. Motivo medido: `scripts/porques.py` conta cada bullet do bloco "Sempre" como regra com origem obrigatória; um bullet novo faz `scripts/testar_sincronia.py` falhar (15 para 16 regras, e a regra sem origem). Um bullet novo exigiria registro em `config/porques.json` e ajuste de contagem em `scripts/testar_sincronia.py`, que estão fora desta proposta.
- Marcador da Seth (D2, medido em 14/11/2026): `MARCADOR` é o hash de (seção SETH-GATEWAY de PROTOCOLOS.md + AGENTS.md), em `_hash_fonte()`. A linha PROCESSO do gateway não entra nesse hash, e o teste `test_marcador_vem_so_da_doutrina_e_do_agents` prova isso. A linha do AGENTS.md entra: o MARCADOR muda uma vez quando esta proposta é aplicada (hash 16ada97c no main de 14/11; 2863a666 com o ponteiro desta v2, medido em 14/11). Efeito: conversas em andamento da Seth são reidratadas uma vez depois do redeploy do gateway. Não medido: quanto isso custa em contexto.
- D7, medido em 14/11/2026: o mecanismo que destila MEMÓRIAS é `scripts/memoria_semanal.py`, numa tarefa semanal de `config/janela-tarefas.txt`, e ele só propõe. Não há timer medido. O guia diz isso na seção 8.
