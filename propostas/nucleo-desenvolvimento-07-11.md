# Proposta nucleo-desenvolvimento-07-11: núcleo de desenvolvimento (Ma'at, Ptah, Thoth)

**Nome para assinatura:** `nucleo-desenvolvimento-07-11`
**Base:** origin/main 619416ed. **Revisão da proposta:** Codex, 09/11/2026. O patch de aplicação foi conferido sobre esta base; a revisão trata da correção C11b e da atualização dos registros.
**Diff:** `propostas/nucleo-desenvolvimento-07-11.diff` (tamanho atualizado no arquivo versionado, 16 caminhos).
**sha256 do diff:** `1dbab5069ad21ef8a1ae838f7cfb9bc82d228e0260b150fb0f8b95247dd00d63`
**Assinatura:** pendente do Humano, depois do merge do PR de proposta: `bash scripts/aprovar.sh nucleo-desenvolvimento-07-11`. Quem propõe não roda isso.

## Caminhos do diff
- `AGENTS.md` (uma linha de ponteiro, 130 bytes)
- `.agents/skills/agata-fluxo/SKILL.md` (guia Ma'at, 8134 bytes)
- `.agents/skills/INDICE.md` (cinco linhas novas e agata-fluxo com dono e revisor)
- `redesign/router/seth_gateway.py` (ponteiro PROCESSO, D2)
- `scripts/ci_sdd_local.sh` e `.github/workflows/sdd.yml` (pasta de testes, âncora, gate de spec e filtro de caminhos)
- `redesign/nucleo-desenvolvimento/spec/` (acceptance.json, brainstorm.md, decision.md, spec.md)
- `redesign/nucleo-desenvolvimento/tests/` (seis arquivos de teste)

## Decisões do Humano (07/11/2026), registradas em spec/decision.md como "DECISAO: aceita"
- D1: todos os modelos do Conselho recebem o ponteiro.
- D2: o ponteiro vai ao gateway, pelo canal de estado de `_injeta`, nas faixas internas; `SETH_PROCESSO_HIDRATA=0` desliga.
- D3: orçamento: ponteiro no AGENTS.md até 200 bytes; guia até 8 KiB; linha do gateway até 200 caracteres.
- D4: dono = agata-spec (escreve e mantém a especificação do processo); revisor = agata-revisor (somente leitura, independente de quem escreveu). Justificativa: quem escreve não revisa.
- D5: uma proposta só: spec, código, testes e CI, com uma assinatura.
- D6: a faixa pública fica de fora.
- D7: MEMÓRIAS.md entra só (a) pela destilação do cache (timer), com fatos e pendências já verificados, ou (b) em momento extremamente importante, e só com assinatura do Humano. Critérios vêm da medição do sistema, não de opinião. Escrito no guia, seção 7.
- D8: a proposta não depende da PR #944. Os ids de lição citados (e, f, i, l, m) estão definidos dentro do próprio guia, e o teste C9 confere lá.
- D9: pasta `redesign/nucleo-desenvolvimento`.
- D10: Ma'at = guia universal (ordem e verdade); Ptah = núcleo de construção (artífice); Thoth = canal da equipe, para escrita e registro.

## Correções obrigatórias no agata-fluxo
- §8: o comando não restaura mais. Copia para backup e faz `pull --ff-only`. Restaurar só com ordem do Humano, por nome. O `git checkout --` saiu.
- §6: saiu "A Seth carrega esta skill pela hidratação". Agora: o código mostra que a sugestão de skills (`SETH_SKILLS_SUGERE`) é desligada por padrão e não carrega o corpo; se a Seth lê o arquivo, não medido (L5).
- Índice e roteiro: `agata-processo-lote` e `agata-time-inovacao` entraram no índice e no roteiro. Também entraram `agata-disciplina`, `agata-engenharia-reversa` e `elephant-goldfish-sdd`, que faltavam (5 de 20 pastas com SKILL.md versionado).

## Testes (redesign/nucleo-desenvolvimento/tests/, pytest 9.2.0)
| Critério | Teste | Worktree | origin/main + testes |
|---|---|---|---|
| C1 | test_entrada_universal.py::test_agents_aponta_para_o_fluxo_universal | verde | vermelho (AGENTS sem ponteiro) |
| C2 | test_entrada_universal.py::test_indice_lista_toda_pasta_de_skill | verde | vermelho (5 linhas faltando) |
| C6 | test_entrada_universal.py::test_caminhos_citados_existem | verde | verde (caminhos já existiam) |
| C3 | test_fluxo_regras.py::test_fluxo_resume_as_regras_de_lote | verde | vermelho (sem resumo) |
| C4 | test_fluxo_regras.py::test_fluxo_sem_restauracao_ou_remocao_sem_ordem | verde | vermelho (checkout -- no §8) |
| C5 | test_fluxo_regras.py::test_fluxo_nao_afirma_o_que_a_seth_nao_mostrou | verde | vermelho (frase da hidratação) |
| C8 | test_fluxo_regras.py::test_skills_de_processo_passam_no_lint | verde | verde (já passava) |
| C9 | test_fluxo_regras.py::test_ids_do_resumo_existem_na_skill | verde | vermelho (sem resumo) |
| C7 | test_texto_seguro.py::test_linhas_novas_sem_segredo_nem_memoria_restrita | parcial: segredo verde; caminho restrito skip (pendência) | vermelho (região ausente) |
| C10 | test_cache_documentado.py::test_cache_fato_e_pendencia_pelo_comando_documentado | verde | vermelho (comando ausente) |
| C11a | test_ponteiro_gateway.py::test_ponteiro_so_nas_faixas_internas | verde | vermelho (sem _LINHA_PROCESSO) |
| C11b | test_ponteiro_gateway.py::test_ponteiro_desligavel_por_ambiente | verde | vermelho (sem _LINHA_PROCESSO) |
| D3 | test_ponteiro_gateway.py::test_linha_do_gateway_ate_200_caracteres | verde | vermelho |
| D3 | test_decisoes.py::test_d3_ponteiro_do_agents_ate_200_bytes | verde | vermelho |
| D3 | test_decisoes.py::test_d3_guia_ate_8_kib | verde | verde (5467 bytes antes) |
| D4 | test_decisoes.py::test_d4_dono_e_revisor_do_guia | verde | vermelho |
| D7 | test_decisoes.py::test_d7_regra_de_memorias_no_guia_e_no_registro | verde | vermelho |
| D10 | test_decisoes.py::test_d10_nomes_no_guia_e_na_spec | verde | vermelho |
| gate | test_decisoes.py::test_decision_aceita | verde | verde (spec copiada já aceita) |

Resultado na worktree: 18 passed e 1 skipped (C7, parte de caminho restrito). Vermelhos na proposta: nenhum. Em origin/main com os testes copiados: 15 falham e 4 passam (os quatro que passam estão marcados acima como verde no origin/main).

Pendência do C7: a lista de caminhos de memória restrita não é escrita no repositório (regra do sistema). Ela vem de AGATA_CAMINHOS_RESTRITOS (separada por vírgula). Sem a variável, o teste pula a parte restrita e diz por quê. Decidir onde a lista fica é do Humano.

## CI local e gates
- `PYTEST=/home/orusoua/.cache/uv/archive-v0/0obnOoJtclHllQl_/bin/pytest bash scripts/ci_sdd_local.sh`: "CI LOCAL: TUDO OK", 34 OK, 0 FALHA (saída em scratchpad).
- Reexecutado em 09/11/2026 sobre a base atual `619416ed`, com o patch de aplicação aplicado: "CI LOCAL: TUDO OK", exit 0.
- C11b, `test_ponteiro_gateway.py`: 6 testes passaram; inclui desligamento por `SETH_PROCESSO_HIDRATA=0` e atualização sem duplicar ponteiro em conversa hidratada.
- `python3 redesign/sdd_flow/spec_gate.py check redesign/nucleo-desenvolvimento/spec`: SPEC GATES: OK.
- `python3 redesign/sdd_flow/anchor.py . redesign/nucleo-desenvolvimento`: ANCHOR: OK.
- Listas de pytest em `scripts/ci_sdd_local.sh` e `.github/workflows/sdd.yml`: iguais.

## Conferência do diff
- `grep '^diff --git'`: 16 caminhos, todos dentro da lista acima.
- `git apply --cached --check` contra origin/main (índice temporário): OK.
- Export de origin/main (sem .git), `git apply` do diff: 18 passed e 1 skipped (C7, pendência), gate, âncora e lint: OK.
- Verificador mecânico (`auditoria_turno.py --verificar`) sobre este registro: nada a apontar.

## Fora desta proposta
- Registros de proposta em MEMÓRIAS.md (974) e ONDE_ESTAMOS.md estão incluídos nesta PR. Nenhuma mudança funcional do diff foi aplicada ao código rastreado.
- Revisão de agente pelo caminho oficial (passo 8 da spec, `redesign/review_mesh/mesh.py prepare` e `consolidate`): não feita. Exige revisor de outro modelo.
- PR #944: não é pré-requisito (D8).
- Artefatos do ciclo SDD gerados pelo CI local, fora do componente: `redesign/nova_versao/spec/criterion-drift.md` e `evidence.json` (modificados) e `redesign/sdd_flow/spec/criterion-drift.md` e `evidence.json` (não rastreados). Não entram no diff. Não foram restaurados nem removidos: a restauração depende de ordem do Humano.
- Canon (REGRAS, PROJETO, PROTOCOLOS, FALHAS, MEMÓRIAS, PROMPT_CARREGAMENTO): nenhuma edição na worktree.
- Lacunas L1 a L6 da spec: continuam abertas (adoção, qualidade do texto, CLIs que leem AGENTS.md, índice derivado, carregamento pela Seth, cumprimento da regra).

## Pontos para o Humano conferir
1. AGENTS.md está no diff. O texto "só código, spec e skills" não cabe nele, mas o item 4 da tarefa e o critério C1 pedem a linha no AGENTS.md. Sem ele, C1 e o ponteiro saem desta proposta.
2. CI (`scripts/ci_sdd_local.sh` e `.github/workflows/sdd.yml`) entrou porque D5 inclui CI. Sem isso, os testes novos não rodam na CI.
3. A linha "DECISAO: aceita" foi escrita por um agente de implementação, por instrução do orquestrador. A spec original dizia que modelo não escreve essa marca. Quem confere é o Humano, pela assinatura.
4. D7 fala em "timer do cache". O mecanismo medido é `scripts/memoria_semanal.py`, numa tarefa semanal da janela (`config/janela-tarefas.txt`), e ele só propõe. Não há timer medido. O guia descreve os fatos medidos.
5. O ponteiro do gateway só aparece no modo compacto, que é o padrão (`SETH_HIDRATA_MODO`). No modo full, `_hidratacao` não usa o bloco de estado.
6. O C11a prova a separação pelo caminho `_preparar_payload_publico`, que não chama `_injeta`. Não exercita o handler HTTP da faixa pública.
7. Não medido: se a Seth ou o Goose leem a linha PROCESSO; quanto ela custa em contexto por turno; a dona de fato das cinco skills novas no índice (está "não medido").
