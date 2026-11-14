# Spec: núcleo de desenvolvimento universal (transição do modo de trabalho)

Status: spec da proposta nucleo-desenvolvimento-07-11. Decisão: aceita (decision.md, D1 a D10, decididas pelo Humano em 07/11/2026). Base: origin/main 86704396, medida em 14/11/2026 (a base de 07/11 era 83334fde). Revisão de 14/11 no fim de decision.md. Nomes (D10): Ma'at é o guia universal (agata-fluxo); Ptah é o núcleo de construção; Thoth é o canal da equipe, para escrita e registro.
Brainstorm com as alternativas e as medições: brainstorm.md, na mesma pasta.
Rótulos: [medido], [lido], [inferido], [não medido].

## Escopo

Entra:
- O fluxo universal que já existe, agata-fluxo (consolidado no main em 12/11), ganha nomes e papéis, a seção de regras de lote (resumo), os ids de lição e a regra de MEMÓRIAS (seção 8). Corrige os dois trechos que contradizem o processo: a seção 6 (Seth) e o comando que restaurava arquivo (seção 9).
- Índice de skills com uma linha para cada pasta de skill com SKILL.md.
- AGENTS.md com um ponteiro de uma linha para agata-fluxo.
- Por decisão D2 (aceita): uma linha de ponteiro no bloco de estado da Seth, nas faixas internas (faixa pública fica de fora, D6).
- Testes que travam esses pontos, sem navegador e sem provedor real.

Não entra:
- Mudança em REGRAS.md, PROJETO.md ou PROTOCOLOS.md.
- Código de produto novo, serviço novo ou módulo novo de guia.
- Mudança em scripts/equipe/equipe.py, no formato do cache ou nos dados do cache.
- Mudança em .claude/agents/ (formato do Claude Code).
- A aplicação do PR #944 (lições de 07/11), que é outro lote.
- Qualquer pedido de carregamento de skill pela Seth: não medido, fica como lacuna L5.

Universal e específico de modelo:
- Universal: regras, papéis, fluxo de proposta, lições, uso do cache e do verificador. A regra é a mesma para todos os modelos.
- Específico de modelo: nada na regra. A diferença de capacidade, como subagentes do Claude Code ou ferramentas da Seth, é da sessão. A regra já prevê o caso: sem delegação, o modelo faz a operação com a mesma disciplina (agata-processo-lote, seção "Uso de agentes").

## Jornadas críticas

- J1. Modelo novo abre sessão no Agata (Codex, Gemini, Goose, Claude Code ou outro). Lê AGENTS.md, segue o ponteiro para agata-fluxo, mede o estado (§0), lê o cache com `ler --n 20` e só então age.
- J2. Seth, pelo gateway, numa faixa interna, pede mudança no sistema. Recebe a doutrina fixa, o estado e, se D2 for aprovada, a linha de PROCESSO com o caminho do fluxo. Ler a skill é ação dela; não medido se ela lê (L5).
- J3. Orquestrador delega operação. O agente recebe o caminho da worktree e a lista de arquivos que pode editar. O orquestrador confere código e teste, não o relatório.
- J4. Proposta P-8. Worktree a partir de origin/main, CI local com "CI LOCAL: TUDO OK", .diff conferido com grep, PR só com .diff e registro, Humano assina. A aplicação continua no agata-processo-lote.
- J5. Decisão do Humano dita em conversa. Vira registro antes de virar código: entrada de cache `decisao` provisória, e entrada em MEMÓRIAS por PR.
- J6. Faixa pública. Nada do processo sai para fora. Negativo: o teste C11a cobre.

## Contrato

O que um modelo do Conselho recebe ao começar:
- C-a. AGENTS.md, com uma linha de ponteiro para `.agents/skills/agata-fluxo/SKILL.md`. Limite: até 200 bytes acrescentados.
- C-b. agata-fluxo/SKILL.md, com a seção "Regras de lote (resumo)", de até 12 linhas, cada uma com a fonte entre parênteses (lição do PR #944 ou passo do lote), e um link para `.agents/skills/agata-aplicar-proposta/SKILL.md`, que é a skill completa (a agata-processo-lote foi juntada nela em 12/11).
- C-c. .agents/skills/INDICE.md, com uma linha para cada skill de processo, inclusive agata-aplicar-proposta e agata-time-inovacao. A linha do agata-fluxo traz dono e revisor (D4).
- C-d. Só se D2: uma linha "PROCESSO:" no bloco de estado da Seth, em faixas internas, com o caminho do fluxo. Limite proposto: 200 caracteres.

Texto da seção de resumo, aceito nesta proposta (o texto que vale está em .agents/skills/agata-fluxo/SKILL.md; o rascunho abaixo ficou como registro do que se decidiu):

    ## Regras de lote (resumo; completo em agata-processo-lote)
    - Um lote, uma proposta, uma assinatura. Só o Humano assina com scripts/aprovar.sh. (regra 1 do lote)
    - Trabalho em worktree a partir de origin/main, em /home/orusoua/agata/.claude/worktrees/. Não no checkout vivo, não em /tmp. (lição f)
    - Antes de propor: bash scripts/ci_sdd_local.sh, com "CI LOCAL: TUDO OK". (passo 3 do lote)
    - PR de proposta traz só o .diff e o registro. Código entra só dentro do .diff, conferido com grep '^diff --git'. (passo 4 e 5 do lote)
    - Não use rm, nem -f nem -r. Para tirar algo do caminho, use mv. Remover só com ordem do Humano, por nome. (lição e)
    - Não restaure nem descarte alteração sem ordem explícita do Humano. (regra 5 do lote)
    - Delegue operação a agentes quando a sessão permitir; sem isso, faça a operação com a mesma disciplina. Confira o resultado; não aceite o relatório. (uso de agentes)
    - Memória comum: ao começar, `python3 redesign/router/cache_conselho.py ler --n 20`; ao fechar trabalho relevante, `anotar --autor "<modelo real>" --tipo fato|pendencia|nota "<texto>"`. (memória comum, AGENTS.md)
    - Decisão do Humano que só existe em conversa vira proposta ou registro antes de virar código. No cache ela é `decisao` provisória, e o cache não é canon. (lição i)
    - Perguntas ao Humano vão numeradas, na ordem da mensagem. Número sai com rótulo: medido, inferido ou não medido. (lições l e m)
    - Antes de entregar afirmação verificável: `python3 redesign/router/auditoria_turno.py --verificar < arquivo`.

Como o modelo registra no cache (contrato de escrita):
- Fato: `python3 redesign/router/cache_conselho.py anotar --autor "<modelo real>" --tipo fato "<texto>"`.
- Pendência: o mesmo comando com `--tipo pendencia`.
- Decisão do Humano dita em conversa: `--tipo decisao`, provisória. Registro definitivo só em MEMÓRIAS.md, por PR.
- Recusa: segredo na nota é recusado, com saída 2 (cache_conselho.py, CLI). Não se repete o valor do segredo na nota.
- Autor: o modelo real, medido, não de cabeça.
- Entrada e saída são de texto curto. Não se cola relatório inteiro no cache.

Saída de cada resposta (voz comum do AGENTS.md): resultado primeiro, depois evidência ou "não medido", depois o próximo passo.

## Critérios de aceite

Cada critério tem um teste. Os testes estão em redesign/nucleo-desenvolvimento/tests/ (lista em "Código"). O estado de cada critério na proposta está no registro propostas/nucleo-desenvolvimento-07-11.md. Os nomes estão em acceptance.json.

- [ ] C1: AGENTS.md aponta para o fluxo universal e o caminho existe
- [ ] C2: o índice de skills tem uma linha para cada pasta de .agents/skills com SKILL.md
- [ ] C6: os caminhos relativos citados no fluxo, no AGENTS.md e no índice existem
- [ ] C3: o resumo de regras de lote do fluxo tem os 11 pontos
- [ ] C4: nenhum bloco de comando do fluxo remove ou restaura sem ordem
- [ ] C5: o fluxo não afirma que a Seth carrega a skill sem medição
- [ ] C8: as skills de processo passam no lint de skill, sem problema
- [ ] C9: cada id de lição citado no resumo existe na skill de processo (sem depender do PR #944, D8)
- [ ] C7: nas linhas acrescentadas, nenhum valor de segredo e nenhum caminho de memória restrita
- [ ] C10: o comando de cache documentado no fluxo grava um fato e uma pendência, e o ler mostra os dois
- [ ] C11a (condicional a D2): o ponteiro de estado aparece em faixa interna e não aparece na faixa pública
- [ ] C11b (condicional a D2): o ponteiro é desligado por SETH_PROCESSO_HIDRATA=0 e não muda o MARCADOR

Detalhe de cada critério: o teste está em `tests/` (o mesmo caminho está no campo "command" de acceptance.json). Estado na v2 (14/11/2026), medido na worktree com pytest: todos passam, exceto a parte de caminho restrito de C7, que fica como pendência (skip).
- C1: `test_entrada_universal.py::test_agents_aponta_para_o_fluxo_universal`.
- C2: `test_entrada_universal.py::test_indice_lista_toda_pasta_de_skill`. Em 07/11 (base 83334fde) falhava, com 5 pastas faltando.
- C6: `test_entrada_universal.py::test_caminhos_citados_existem`. Só caminhos relativos entre crases; placeholders (`<nome>`, `*`, `{}`, `$`, `~`) ficam fora.
- C3: `test_fluxo_regras.py::test_fluxo_resume_as_regras_de_lote`. Prova presença de cada ponto, não que o modelo o cumpre (L6).
- C4: `test_fluxo_regras.py::test_fluxo_sem_restauracao_ou_remocao_sem_ordem`. Só os blocos de comando (crases triplas).
- C5: `test_fluxo_regras.py::test_fluxo_nao_afirma_o_que_a_seth_nao_mostrou`. Seção "6. Seth".
- C8: `test_fluxo_regras.py::test_skills_de_processo_passam_no_lint`. Lint: redesign/painel_operacional/qualidade_llm.py.
- C9: `test_fluxo_regras.py::test_ids_do_resumo_existem_na_skill`. Ids dentro do próprio guia (D8).
- C7: `test_texto_seguro.py::test_linhas_novas_sem_segredo_nem_memoria_restrita`. Segredo: passa. Caminho restrito: a lista vem de AGATA_CAMINHOS_RESTRITOS; sem ela, o teste pula essa parte e diz por quê.
- C10: `test_cache_documentado.py::test_cache_fato_e_pendencia_pelo_comando_documentado`. Usa AGATA_CACHE_CONSELHO apontando para pasta temporária.
- C11a: `test_ponteiro_gateway.py::test_ponteiro_so_nas_faixas_internas`. Faixa pública pelo caminho `_preparar_payload_publico`.
- C11b: `test_ponteiro_gateway.py::test_ponteiro_desligavel_por_ambiente`. O MARCADOR é conferido pelo teste `test_marcador_vem_so_da_doutrina_e_do_agents`.

Lacunas, sem teste automatizado:
- L1. Adoção: quem leu o ponteiro. [não medido] Não há telemetria de leitura.
- L2. Qualidade do texto do resumo (se a regra está certa, não só se está escrita). Fica para a revisão de agente (redesign/review_mesh/mesh.py) e para o Humano.
- L3. Quais CLIs carregam AGENTS.md por padrão. [não medido]
- L4. Índice derivado (ferramentas/indice.json) sem divergência. Não há função de leitura que compare sem gravar. [não medido]
- L5. Se a Seth lê skill por alguma ferramenta. [não medido]; o código de injeção lido não carrega skill.
- L6. Que um modelo cumpre a regra. Não é testável por teste; mede-se por auditoria de rodadas de lote.

## Desenho e alternativas

Escolhida: D (reaproveitar). agata-fluxo já é o fluxo declarado para qualquer LLM e já está no índice. Mudam texto e índice, e os testes são a única parte nova.

Alternativas descartadas (motivo resumido; detalhe no brainstorm.md):
- A. Texto inteiro em AGENTS.md. Descartada: 7193 bytes já carregados por toda sessão, mais 22305 bytes do processo de lote; o gateway não lê AGENTS.md [medido].
- B. Skill-guia nova com cache como canal. Descartada: um terceiro fluxo ao lado do universal; o cache é registro de fato e pendência, com janela de 20 entradas, e o gateway injeta 3 entradas de até 160 caracteres [lido].
- C. Módulo de código com função de guia. Descartada: código novo, com P-8 e testes, para entregar um texto que a leitura de arquivo já entrega; não resolve a lacuna de conteúdo.

Desenho do ponteiro no gateway (só se D2): uma função que devolve a linha "PROCESSO:" e uma chamada dela em `_injeta`, depois do bloco de cache do Conselho (seth_gateway.py, `_injeta`), com a mesma forma que os outros blocos de estado. A linha é desligada por SETH_PROCESSO_HIDRATA=0. Não entra na seção SETH-GATEWAY de PROTOCOLOS.md nem nas fontes do MARCADOR (`_hash_fonte`: seção + AGENTS.md).

## Implementação e testes

Não há código nesta etapa. Ordem proposta, para quando as decisões estiverem tomadas:

1. Decisões D1 a D10 (decision.md) tomadas pelo Humano.
2. Dispensado por D8 (aceita): a proposta não espera a PR #944. O teste C9 confere os ids dentro do próprio guia.
3. Worktree: `git fetch -q origin && git worktree add -b proposta/nucleo-desenvolvimento-07-11 /home/orusoua/agata/.claude/worktrees/nucleo-desenvolvimento-07-11 origin/main`.
4. Escrever os testes primeiro (C1 a C11), vendo-os vermelhos. Depois o texto, até ficarem verdes.
5. Copiar esta pasta para `redesign/nucleo-desenvolvimento/spec/` na worktree, e depois o caminho do spec entra no Código, com crase só para arquivos que já existem.
6. Lista de testes igual em scripts/ci_sdd_local.sh e em .github/workflows/sdd.yml (armadilha da lista de pytest).
7. CI local com "CI LOCAL: TUDO OK". Gates: `python3 redesign/sdd_flow/spec_gate.py check redesign/nucleo-desenvolvimento/spec` e `python3 redesign/sdd_flow/anchor.py . redesign/nucleo-desenvolvimento`.
8. Revisão de agente pelo caminho oficial (`redesign/review_mesh/mesh.py prepare` e `consolidate`). Revisão avulsa não conta (armadilha do lote).
9. Um único .diff, com spec, código, testes, CI e o texto do fluxo, conferido com `grep '^diff --git'`. Registro (.md e entrada de MEMÓRIAS) no PR de proposta, sem assinatura.

Arquivos tocados nesta proposta (o diff tem só estes caminhos; o registro está em propostas/nucleo-desenvolvimento-07-11.md):
- `AGENTS.md`: um parágrafo de ponteiro, antes de "**Sempre:**" (fora do bloco de regras, por scripts/porques.py). Protegido (P-8).
- `.agents/skills/agata-fluxo/SKILL.md`: nomes e papéis, resumo de regras de lote, ids de lição, seção 6 (Seth), seção 8 (memória, D7) e seção 9 (comando sem restauração). Protegido (P-8, `.agents/*` em scripts/perimetro/p08_quarentena.sh, linha 134).
- `.agents/skills/INDICE.md`: a linha do agata-fluxo (dono e revisor) e o exemplo da regra 3, sem caminho inexistente. Protegido (P-8).
- `ferramentas/indice.json` e `ferramentas/INDICE.md`: gerados por `reindexar`, só se alguma descrição de skill mudar.
- `redesign/nucleo-desenvolvimento/spec/` (quatro arquivos). Protegido (redesign/*).
- `redesign/nucleo-desenvolvimento/tests/` (testes C1 a C11). Protegido (redesign/*).
- `scripts/ci_sdd_local.sh`: a pasta de teste na lista, a âncora e o gate de spec. Protegido (scripts/*).
- `.github/workflows/sdd.yml`: a mesma pasta na linha de pytest, a âncora, o gate de spec e o filtro de caminhos. Fora da lista P-8 [não verificado].
- `redesign/router/seth_gateway.py`: ponteiro PROCESSO (D2), já na worktree. Protegido (redesign/*).
- `propostas/nucleo-desenvolvimento-07-11.diff` e `.md`: registro da proposta.
- `MEMÓRIAS.md`: entrada de registro da decisão de 07/11 (lição i). Registro, sem quarentena.

Não tocados: redesign/router/cache_conselho.py, redesign/router/auditoria_turno.py, redesign/router/sanitizar.py, scripts/equipe/equipe.py, .claude/agents/*, .agents/skills/agata-time-inovacao/SKILL.md, PROMPT_CARREGAMENTO.md, REGRAS.md, PROJETO.md.

## Migração e reversão

Migração:
- Sem migração de dados. O cache, o estado e as conversas em andamento não mudam.
- Conversas em andamento da Seth: a linha PROCESSO não as reidrata (canal de estado, D2). Mas a linha do AGENTS.md entra no hash do MARCADOR: as conversas em andamento são reidratadas uma vez depois do redeploy (medido em 14/11: 16ada97c para 2863a666).
- As lições de 07/11 entram no resumo sem depender da PR #944 (D8, aceita): o guia agata-fluxo traz os ids que cita (e, f, i, l, m), e o teste C9 confere os ids dentro desse mesmo arquivo. A aplicação da #944 continua outro lote.
- A decisão de 07/11 vira entrada de MEMÓRIAS por PR (lição i). O número da entrada só se fixa na junção.

Reversão:
- Ponteiro em AGENTS.md: proposta nova que remove a linha. Sem reescrever histórico (Regra 4).
- Ponteiro no gateway (D2): `SETH_PROCESSO_HIDRATA=0` desliga sem código. Aplicar a variável pede reinício do serviço: ordem do Humano.
- Seção nova e correções no fluxo: revertidas por proposta. O bloco destrutivo de §8 não volta.
- Testes e lista de CI: saem na mesma proposta.
- Nenhum arquivo é apagado. Se for preciso tirar algo do caminho, usa-se mv para uma pasta de arquivo, com ordem do Humano, por nome.

## Riscos e dependências

- R1. Governança: AGENTS.md, .agents/* e redesign/* são P-8. O Humano assina. Nenhum modelo aplica.
- R2. Dependência: PR #944 (lições). Resolvida por D8 (aceita): a proposta não depende da #944; os ids citados existem dentro do próprio guia.
- R3. Dono do arquivo: o INDICE (consolidado em 12/11) dava agata-fluxo como de doutrina do Claude. A mudança precisa de revisão cruzada e de decisão do Humano (D4: dono agata-spec, revisor agata-revisor).
- R4. Duas listas de pytest (scripts/ci_sdd_local.sh e sdd.yml) precisam ser iguais. Já houve divergência (lote de 06/11).
- R5. Contexto: o resumo entra no fluxo, que é carregado sob demanda. O ponteiro do AGENTS.md entra em toda sessão. Por isso o limite de 200 bytes (D3).
- R6. Gateway (D2): o MARCADOR é o hash de SETH-GATEWAY + AGENTS.md (`_hash_fonte`). A linha PROCESSO não entra nele (teste `test_marcador_vem_so_da_doutrina_e_do_agents`); por isso o canal de estado, e não a doutrina. A linha do AGENTS.md entra no hash e muda o MARCADOR uma vez (ver Migração).
- R7. Faixa pública: o processo não pode sair para provedor externo. O gateway já tira o sistema nessa faixa (linhas 567 a 580 e 1294 a 1295). O teste C11a trava isso.
- R8. Nomes (D10, aceita): Ma'at (guia universal, ordem e verdade), Ptah (núcleo de construção, artífice) e Thoth (canal da equipe, escrita e registro). Thoth é o nome do canal que hoje é agata-equipe e scripts/equipe/equipe.py; esta proposta não renomeia código. A linha "universalista" de MEMÓRIAS.md, linha 363, é a origem do pedido; não é a fonte dos nomes.
- R9. Cota: a proposta não consome cota de provedor. Consumo de cota da Seth: não medido, porque o ponteiro é texto.
- R10. Gate de spec: decision.md está em "DECISAO: aceita" (D1 a D10, 07/11/2026, decididas pelo Humano). `spec_gate.py check` passa; a regra do gate está em redesign/sdd_flow/spec_gate.py, linhas 27 e 28.

## Código

Dono de código deste componente (caminhos relativos a redesign/nucleo-desenvolvimento/, lidos pela âncora):
- `tests/`: a pasta inteira. Dona dos testes C1 a C11 e dos testes de decisões (test_entrada_universal.py, test_fluxo_regras.py, test_texto_seguro.py, test_cache_documentado.py, test_ponteiro_gateway.py, test_decisoes.py). Os nomes de arquivo estão sem crase de propósito: a âncora (redesign/sdd_flow/anchor.py) trata cada crase como arquivo que precisa existir na pasta do componente.

Fora da pasta do componente, nesta proposta, sem crase (a âncora não os confere): redesign/router/seth_gateway.py (ponteiro PROCESSO, D2), scripts/ci_sdd_local.sh e .github/workflows/sdd.yml (lista de testes, âncora e gate), AGENTS.md e .agents/skills/ (texto do guia e do índice).
