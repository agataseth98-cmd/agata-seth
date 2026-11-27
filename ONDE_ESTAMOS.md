# Onde estamos

**Proposta nova 27/11/2026 (`memoria-manutencao-sem-teste-26-11`):** correção mínima (1 linha). Acrescenta o P-28 na tabela de controles que só avisam e não precisam de caso de teste na suíte — mesmo texto que P-24 e P-26 já têm. Sem isso, a aplicação do lote `memoria-manutencao-26-11` (que você já assinou) trava no pre-commit. Assinatura: `bash scripts/aprovar.sh memoria-manutencao-sem-teste-26-11`.

**Proposta nova 26/11/2026 (`memoria-manutencao-26-11`):** duas melhorias pedidas pelo Gemini no canal. Primeira: `PROTOCOLOS.md` passa a dizer que a guarda oficial do selo das primeiras 62 entradas é o comando `bash scripts/selar.sh --check` — o script antigo não acha mais o trecho porque ele saiu de `MEMÓRIAS.md` para a camada fria. Segunda: um controle novo (P-28) avisa quando `MEMORIAS-MORNO.md` passa de 1.000 KB, lembrando de rodar o próximo congelamento (hoje está em 1.173 KB). Só aviso, não bloqueia nada. Já assinado; aguarda a corretiva acima para poder aplicar.

**Aplicado 26/11/2026 (`ferramentas-unificadas-26-11`):** fonte única de ferramentas para todos os modelos do Conselho + skill de arranque universal. Instalar ferramenta nova: `python3 scripts/ferramentas/instalar.py <tipo> <nome> [--params k=v …]` (gate TTY + confirmação interativa, escreve só no overlay `~/agata-local/ferramentas.yml`). Sincronizar nativamente: `python3 scripts/ferramentas/sincronizar.py`. Reverter: `python3 scripts/ferramentas/reverter.py <ts>`. Promover overlay → canônico: `python3 scripts/ferramentas/promover.py <nome>` (gera `.diff` para P-8). Skill de arranque: `.agents/skills/agata-arranque/SKILL.md` (lida no SessionStart em Claude e Codex). R4 do `claude-in-chrome` fica para lote 2 (Humano decide E ou C); o lote 2 também cobre L2-A a L2-H (migração física, Gemini CLI, slash commands, subagentes sync, L7-L9).

## Hoje, 25/11 (proposta rea-pe-linux-2026-11-25)

Estado: proposta P-8 assinada e aplicada em worktree própria; CI local 95/95 e revisão independente 10/10. Aguarda PR de aplicação; a junção cabe ao Humano. O REA ganha quatro comandos para inspecionar arquivos PE em modo estático e somente de leitura; as análises não confirmam sozinhas que um arquivo seja DLL ou driver.

Atualizado em 20/11/2026. Em 20/11 os 7 lotes que ainda constavam como "proposta" foram conferidos: todos estão em `propostas/superadas/`; o estado na tabela abaixo foi corrigido.

Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 22/10/2026: `extras/arquivo/onde-estamos-ate-2026-10-22.md`; 28 e 29/10: `extras/arquivo/onde-estamos-ate-2026-10-29.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md`.

## Hoje, 23/11, noite (proposta capacidade-producao-23-11)

Uma proposta espera sua assinatura (`capacidade-producao-23-11`). Para quem usa: a Seth e o Agata Code passam a escolher o modelo pela qualidade medida em cada tipo de pedido; o perfil de cada modelo vem de pesquisa na internet e melhora com o uso; e nenhuma resposta sai sem ser conferida e, se preciso, refeita — com a etapa visível na tela enquanto você espera.

## Hoje, 23/11, tarde (proposta caminho-visao-23-11)

Uma proposta espera sua assinatura (`caminho-visao-23-11`). Para quem usa: o painel para de mostrar como problema o que só está dormindo de propósito e se atualiza sozinho; o teste local mostra quanto falta; o sistema avisa quando os atalhos ficam diferentes do repositório; e entra a skill que mapeia você, com o protocolo de inserção humana. Confira a sua frase de 18/11 citada na proposta.

## Hoje, 23/11 (proposta reaproveita-23-11)

A casa foi limpa: das 41 branches antigas no GitHub, 39 já estavam no sistema e saíram (cópia guardada em `~/agata-arquivo/limpeza-23-11/`). As duas que traziam algo novo viraram uma proposta só, esperando sua assinatura (`reaproveita-23-11`): a voz do sistema numa chamada de app que tem voz própria, e a especificação de como medir tempo e recursos nas avaliações.

## Hoje, 17/11 (proposta atualiza-17-11)

Há uma proposta esperando sua assinatura (`atualiza-17-11`). O painel ganha uma lista única de integrações em Sistema, e os provedores aparecem numa tabela só, em Conexões. Equipe, Backup, Saída de rede, Perímetro e CI passam a ter tela de leitura, com a idade do último resultado; o painel só lê o que já foi gerado. Perímetro, CI, equipe e restic continuam rodando só pelo terminal. Comando: `bash scripts/aprovar.sh atualiza-17-11` (depois do merge do PR de proposta, no terminal, sem `!`).

A proposta `spec-mae-cofre-17-11` está esperando sua assinatura. A spec-mãe passa a descrever o cofre de chaves que o código já usa, com um critério novo provado por teste. Comando: `bash scripts/aprovar.sh spec-mae-cofre-17-11`, no terminal, sem `!`. Assinatura só depois do merge deste PR.

Os blocos de 16/11 sobre o painel e a higiene já foram aplicados (entradas 1023, 1025 e 1027). O bloco de 06/11 que pede para juntar o PR 927 está superado: o PR entrou em 07/11.

## Hoje, 16/11 (proposta painel-conversa-16-11)

Há uma proposta do painel esperando sua assinatura (`painel-conversa-16-11`). Para quem usa: a conversa com a Seth fica no padrão de ChatGPT e Claude, com o menu único no menu geral. O painel inteiro fica responsivo e segue o estilo que você fixou em 16/11, às 18h27. Comando: `bash scripts/aprovar.sh painel-conversa-16-11`, no terminal, sem `!`. Assinatura só depois do merge deste PR. O registro é a entrada (1026) de `MEMÓRIAS.md`.

## Hoje, 16/11 (higiene-16-11 aplicada)

A higiene-16-11 foi assinada por você e aplicada (entrada 1025 de `MEMÓRIAS.md`). O teste local do sistema agora roda também a suíte que barrou a painel-funcional-16-11 no GitHub, e saíram do texto vivo as menções ao chat antigo e ao Goose.

## Hoje, 16/11 (painel-funcional-r2-16-11 aplicada)

A painel-funcional-r2-16-11 foi assinada por você e aplicada (entrada 1023 de `MEMÓRIAS.md`). O painel sai sem o chat antigo, com estados honestos e estilo consolidado.

## Lotes em andamento (medido em 12/11/2026, 09h, base `origin/main` `3f1e9055`)

Fonte: `propostas/*.diff` sem `APROVADO-` e `propostas/aplicadas/`. Última aplicação: `pacote-11-11`, 12/11 08:29 (PR #973). Limite R1 (2 propostas abertas por componente): com o pacote-12-11, as duas propostas do OpenCode saem da fila.

| componente | proposta | estado | desde |
|---|---|---|---|
| Teste comparativo (Agata, chat e spec leve): desenho no repositório; a rodada pede aprovação à parte. Ouvir/Ditar: teste real com o Humano, outro dia | teste-comparativo-14-11 | superada (em propostas/superadas/, conferido 20/11) | 14/11 21:00 |
| Pacote de assinatura único de 14/11: sincronia, PROJETO índice, correções de 12/11 e reversão da nova versão. A fiscal-yaml-12-11 já foi aplicada (#986); falta recolocar o `fiscal-p8` como obrigatório no `main` | pacote-14-11 | superada (em propostas/superadas/, conferido 20/11) | 14/11 11:45 |
| Workflow do fiscal com chave repetida (o GitHub recusa o fiscal-p8 desde o merge de #982; PR #983 bloqueado) e gate de YAML dos workflows | fiscal-yaml-12-11 | superada (em propostas/superadas/, conferido 20/11) | 12/11 16h |
| Pacote de assinatura único: chat lote 4, processo ágil, spec primeiro, voz, Importantes e História (Tomo I) | pacote-11-11 | aplicada (PR #973, 12/11 08:29) | 11/11 20:21 |
| Pacote 12/11: tira o LibreChat, canon de boot, OpenCode no terminal (docs e agente), `--verificar` com rastro, lições da skill e registro do Texto 1 da História | pacote-12-11 | aplicada (PR #976, 12/11) | 12/11 09:01 |
| Skills do Agata: 20 pastas viram 10, sem perder texto (originais em extras/); aplicar depois do pacote mecânico | skills-consolidadas-12-11 | superada (em propostas/superadas/, conferido 20/11) | 12/11 10:30 |
| Pacote mecânico: a verificação vale para todo modelo (contador de turno, aviso de fim de turno, negação do .env, ponteiros para AGENTS.md, subagentes com pacote mínimo) | pacote-mecanico-12-11 | superada (em propostas/superadas/, conferido 20/11) | 12/11 09:47 |
| Correção de estado (12/11): `pacote-mecanico-12-11` e `skills-consolidadas-12-11` (linhas acima, ainda com "proposta") estão superadas pelo `pacote-mecanico-skills-12-11`, aplicado com a assinatura do Humano | pacote-mecanico-skills-12-11 | aplicada (PR #982, 12/11) | 12/11 |
| Chat lote 4: editar, ramos, parar, feedback, atalhos, tema | chat-lote4-09-11 | incluída em pacote-11-11 | 11/11 18:54 |
| Processo ágil da skill de lote (R1, R3, R5, R2) | processo-agil-11-11 | incluída em pacote-11-11 | 11/11 |
| História canônica: Tomo I, Texto 1 e aba História no painel (somente leitura, botão Ouvir) | historia-tomo1-11-11 | incluída em pacote-11-11 | 11/11 19:56 |
| Spec primeiro: entrevista, gate de sincronia, revisor contra a spec, classes de tarefa (P1 a P4) | spec-primeiro-11-11 | incluída em pacote-11-11 | 11/11 19:40 |
| Troca Goose por OpenCode no terminal | agente-opencode-07-11 | incluída em pacote-12-11 | 07/11 13:40 |
| Docs canon e skills da troca OpenCode | docs-opencode-07-11 | incluída em pacote-12-11 (refeita) | 07/11 13:42 |
| PROJETO.md: o que sobe no boot | canon-boot-07-11 | incluída em pacote-12-11 | 07/11 13:07 |
| Núcleo de desenvolvimento (Ma'at, Ptah, Thoth) | nucleo-desenvolvimento-07-11 | superada (em propostas/superadas/, conferido 20/11) | 07/11 15:31 |
| Origem preservada ao salvar conversas | origem-preservada-07-11 | superada (PR #965) | 07/11 13:39 |
| Skill de processo: lições medidas | skill-processo-lessons-07-11 | incluída em pacote-12-11 (só as que não repetem a skill) | 07/11 13:18 |
| Tira o LibreChat dos atalhos e do P-9 | tira-librechat-07-11 | incluída em pacote-12-11 | 07/11 13:39 |
| Nova versão (lote 2) | nova-versao-lote2-20261106 | superada (em propostas/superadas/, conferido 20/11) | 06/11 21:21 |
| Orçamento do turno em sombra (lote 9) | sombra-orcamento-20261106 | superada pela spec v2 | 06/11 09:35 |
| `--verificar` deixa rastro no log da auditoria | verificar-rastro-20261106 | incluída em pacote-12-11 (refeita) | 06/11 23:54 |

Assinadas e aplicadas nesta rodada: `pacote-11-11` (12/11, PR #973). Superadas: `origem-preservada-07-11` (PR #965) e `sombra-orcamento-20261106` (spec v2). Fora desta tabela: `chat-voz-11-11` (PR #974, só proposta, aguarda assinatura do Humano).

## Hoje, 12/11 (proposta: skills mais enxutas)

Proposta `skills-consolidadas-12-11`, com registro (999). As skills do Agata passam de 20 pastas para 10, sem perder texto: os originais estão em `extras/arquivo-skills-12-11/`. A lista que todo modelo carrega cai 39%. Esta proposta vem depois do pacote mecânico: aplique o pacote primeiro. Nada muda no comportamento até você assinar. Assinatura só depois do merge deste PR: `bash scripts/aprovar.sh skills-consolidadas-12-11 "<motivo>"`, no terminal, sem `!`.

## Hoje, 11/11 (proposta chat lote 4)

Proposta sobre `origin/main` `c1a190c6`, com registro (987). A `chat-lote4-09-11` junta editar e reenviar, ramos, Parar, Continuar, feedback, contexto, atalhos e tema claro. Não aplicada; a assinatura é do Humano. Parar só corta o stream de verdade com o gateway real, depois de `chat-stream-verificar-depois-09-11`. Não medido: gateway real, lixeira com ramos no navegador, contraste da paleta clara.

## Hoje, 09/11 (proposta chat protege conversas)

Proposta sobre `origin/main`, com registro (985). A `chat-protege-conversas-09-11` faz apagar virar mover para a lixeira, exige cabeçalho do painel para escrever conversa, registra cada escrita sem conteúdo e preserva a origem ao salvar. Não aplicada; a assinatura é do Humano. Pendência: decidir a regra de origem (403 sem cabeçalho) e a purga manual por item.

## Hoje, 09/11 (proposta chat lote 3)

Proposta sobre `origin/main`, com registro (982). A `chat-lote3-09-11` junta busca nas conversas, pastas, fixar, arquivar, marcadores, exportar e importar sem duplicar, e conversa temporária. Não aplicada; a assinatura é do Humano. Link público de compartilhamento fica de fora até decisão de segurança do Humano. Busca com muitas conversas e fluxo no navegador não medidos.

## Hoje, 09/11 (proposta chat lote 2)

PR publicada sobre `origin/main`, com registro (979). A proposta `chat-lote2-09-11` junta falhas silenciosas do chat, seletor de modelo e exibição do modelo real. Não aplicada; a assinatura é do Humano. O gateway real com `X-Modelo-Real` não foi medido.

## Hoje, 09/11 (aplicação do painel unificado)

**Aplicação local validada:** `painel-unificado-07-11`. Assinatura P-8 confirmada, diff aplicado em worktree própria e CI local `TUDO OK`. A aplicação segue para PR; o Humano decide se junta. Registro em MEMÓRIAS (973).

## Hoje, 09/11 (proposta núcleo de desenvolvimento)

PR #951 refeita sobre `origin/main` atual, com C11b no diff e registro (974). A CI local foi executada; assinatura e aplicação do diff aguardam o Humano. O restante da fila está sendo processado um PR por vez.

## Hoje, 09/11 (proposta OpenCode no terminal)

PR #948 atualizada sobre `main`, com registro (975). A proposta troca o atalho de terminal e o membro da equipe para OpenCode; a CI local passou. A proposta de documentação #949 declara dependência desta e segue depois.

## Hoje, 09/11 (proposta docs OpenCode)

PR #949 atualizada como segunda parte da troca, com registro (976). O diff contém apenas os deltas de documentação, configuração e skills; o registro da decisão fica no diff da primeira proposta para não duplicar. A CI local passou.

## Hoje, 09/11 (proposta origem preservada)

PR #947 atualizada sobre `main`, com registro (977). O diff propõe preservar origem dos dados ao salvar conversas; suíte do painel e CI local passaram. Armazenamento real e conversas acima de 8000 caracteres não foram validados.

## Hoje, 09/11 (proposta retirar LibreChat dos atalhos)

PR #946 atualizada sobre `main`, com registro (978). O diff retira a subida/parada do LibreChat dos atalhos e seus nomes da checagem P-9. Cobertura de serviços, testes e CI local passaram. O patch não foi aplicado.

## Hoje, 06/11 (aplicação teto do Conselho)

**Aplicado:** `sem-teto-conselho-20261106`. O pedido ao Conselho Remoto não tem mais teto de tamanho (`scripts/conselho_remoto.py`, 4 linhas removidas). Assinado pelo Humano e verificado com `p8_verificar` (PODE APLICAR). Registro em MEMÓRIAS (971).

## Hoje, 06/11 (aplicação agência de pesquisa)

**Aplicado:** `agencia-pesquisa-20261106`. Três pesquisadores de leitura em `.claude/agents/` (`agata-pesq-rea`, `agata-pesq-painel`, `agata-pesq-processo`). Assinado pelo Humano e verificado com `p8_verificar` (PODE APLICAR). Valem numa sessão nova. Registro em MEMÓRIAS (970).

## Estado em 06/11/2026 17:40 (correção por entrada nova)

Esta entrada corrige o que as entradas de 03 a 06/11 dizem sobre pendências. Não edita nada acima. Atualizado em 06/11/2026 17:40 (UTC-3). Base: `origin/main` eb1c40a4.

Resumo: cinco propostas já estão aplicadas; quatro estão superadas e não devem ser assinadas; o PR 927 (aplicação do rea-herdr) está pronto para você juntar.

**Medido**

Aplicadas (APROVADO em `propostas/aplicadas/`):
- `APROVADO-m2c-acervo-parcial-20261106`
- `APROVADO-m2b-acervo-egress-20261106`
- `APROVADO-agata-robustez-codeql-medicoes-v2-20261103` (a v1 saiu do main em `af37554c`)
- `APROVADO-cabecalho-modelo-real-20261020`
- lote4: aplicada pelo PR 925 (mesclado às 16:20)

Superadas (não assinar, não aplicar):
- `lote2-processo-20261106` → substituída por `lote2b-processo-20261106` (o header do arquivo manda não assinar a v1).
- `lote2b-processo-20261106` → substituída por `lote3-processo-20261106` (header da lote3). `git apply --check` contra o main de hoje falha: o diff cria arquivos que já existem (ex.: `.claude/agents/agata-ci.md`).
- `lote3-processo-20261106` → substituída por `lote4-processo-20261106` (aplicada). Entrada 356 do cache do Conselho: "Não assinar a lote3".
- `m2-acervo-egress-20261106` v1 → substituída por `m2b-acervo-egress-20261106`. A v1 entrou no main em `29b3231b` e saiu em `1412a897`; hoje não está no main nem no checkout vivo.

Sem aplicação:
- `APROVADO-lote2b-processo-20261106` existe só na raiz do checkout vivo (não rastreado, 06/11 14:18). É um APROVADO sem aplicação.

PRs:
- PR 925 (aplicação lote4): mesclado às 16:20 (UTC-3).
- PR 926 (proposta rea-herdr-integracao-20261106): mesclado às 17:20 (UTC-3).
- PR 927 (aplicação rea-herdr-integracao-20261106, head `3768443`): OPEN, sem conflito (CLEAN). Checks verdes: CodeQL (actions, javascript-typescript, python, rust) e CodeQL; fiscal-p8; suite-adversarial; sdd.
- PR 923 (spec da nova versão, head `7f68458`): OPEN, em conflito com o main (DIRTY). Nesse head não há check `suite-adversarial` nem `sdd`; os checks que existem estão verdes. A frase anterior, "segue vermelha nos critérios de painel de chaves e reversão", não corresponde a esse estado medido e fica substituída por esta entrada.

**Decisão do Humano pendente**
- Juntar o PR 927. Pela AGENTS.md, o PR de aplicação fica com você.
- Arquivar as propostas superadas (lote2, lote2b, lote3, m2 v1) e o `APROVADO-lote2b-processo-20261106` da raiz. A decisão final de arquivar é sua.
- Destino do PR 923: está em conflito e sem suite-adversarial nem sdd no head.
- Não conferido nesta rodada: os outros itens de "Esperando você" das entradas de 03 a 06/11 (branches, D1–D13, P-9/P-16/P-17/P-24, allowlist do Acervo, conciliação do Experimento 2, conferência da tela do Acervo no navegador).

## Hoje, 06/11 (aplicação REA)

**Aplicado:** `rea-herdr-integracao-20261106`. O REA entra em leitura, com allowlist de 14 subcomandos e wrapper `scripts/rea_leitura.sh`. O Herdr fica como está. Assinado pelo Humano.

**Pendente:** a linha da skill em `.agents/skills/INDICE.md` (caminho protegido, precisa de proposta própria).

## Hoje, 06/11 (aplicação lote4)

**Aplicado:** `lote4-processo-20261106` (aviso D3 antes da chamada, multicast bloqueado, skill de processo, portões mecanizados). Assinado pelo Humano e verificado com `p8_verificar` (PODE APLICAR). Próximo: PR de aplicação e CI verde.

**Para o Humano:** o time `agata-*` (em `.claude/agents/`) só fica ativo numa sessão nova. A spec da nova versão (PR 923) segue vermelha nos critérios de painel de chaves e reversão, sem teste.

## Hoje, 06/11 (proposta m2c)

**Esperando você:** assinar `m2c-acervo-parcial-20261106`. É só um teste novo para o estado `parcial` do Acervo, achado pelo ciclo SDD da M2b. O código não muda.

## Hoje, 06/11 (proposta lote3)

**Esperando você:** assinar `lote3-processo-20261106`. Substitui a lote2b, que foi assinada com um diff que traz registros e não aplica. A v3 é só código e aplica limpa. Traz a regra do D3 (aviso antes da chamada) e a camada 2 do Rust com IPs pinados.

## Hoje, 06/11 (proposta lote2b)

**Esperando você:** assinar `lote2b-processo-20261106` (substitui a v1). Traz a correção de segurança do Rust egress, o filtro do CI, a skill de processo e o time de inovação. Duas perguntas: merge de PR de aplicação (AGENTS.md diz que fica com você) e a ordem do aviso D3.

## Hoje, 06/11 (proposta lote2)

**Esperando você:** assinar `lote2-processo-20261106`. Traz a skill do processo de lote, quatro agentes especializados em `.claude/agents` (valem em sessão nova), a página de frentes, o chat com stream e a regra D3 no Conselho. O CI local passa.

## Hoje, 06/11 (aplicação)

**Acervo (M2b):** assinada pelo Humano e aplicada em PR próprio. O Acervo mostra estados explícitos e o egress recusa URL com usuário ou senha. Falta conferir a tela no navegador.

## Hoje, 06/11 (atualização)

**Acervo e egress, v2:** a proposta `m2b-acervo-egress-20261106` substitui a v1 (`m2-acervo-egress-20261106`). Não assine a v1. A v2 corrige os achados da revisão: tela sem contradição, KPIs ocultos em erro, teste sem rede. Os testes passam numa cópia limpa do main.

**Esperando você:** assinar `m2b-acervo-egress-20261106` depois do merge. Decidir D1–D13 (conciliação v2 no Experimento 2, seção 8).

## Hoje, 06/11 (início do dia)

**Acervo e egress (proposta pronta, falta sua assinatura):** o Acervo deixa de mostrar erro como lista vazia; arquivo que não se lê vira contagem visível; URL com usuário ou senha deixa de sair. Os testes passam numa cópia limpa do main. Uma falha do painel (projeto externo do SDD) já existia antes desta mudança.

**Experimento 2:** a conciliação das sete palavras está em `Área de trabalho/Experimento 2/conciliacao-sete-palavras.md`. Esperando você confirmar ou corrigir.

**Esperando você:** assinar `m2-acervo-egress-20261106` depois que o PR chegar ao main. Decidir a allowlist por destinatário e o conflito de saída externa de dados pessoais.

## Hoje, 03/11

**SDD (spec-driven):** o ciclo está no ar e passa na CI: `anchor`, `cycle` e `proposal` em `redesign/sdd_flow/`, com os componentes `sdd_flow`, `project_kit`, `review_mesh`, `evidence_ledger` e `painel_operacional` ancorados (spec com critérios ligados a testes). Cada implementação agora é uma proposta e uma assinatura.

**Painel:** menu em submenus (Sistema, Memória e conhecimento, Qualidade); abas novas SDD e Qualidade de LLM, com botões de medição (dois cliques para confirmar). Skill `agata-llm-fundamentos` com a pesquisa e o mapa falha por mecanismo.

**Medido nesta Máquina:** busca por texto recall@1 70%, @5 100% (consultas de palavras raras); busca por sentido com as mesmas consultas recall@10 22,5%; `qwen3.5-9b-64k` e `qwen3:4b` acham um fato escondido em 3 de 3 até 32 mil tokens, e o 9b até 61 mil (só recuperação simples).

**Codex:** offline até segunda ordem. Marcado ausente na Equipe, vigia dele fora do atalho `seth` (`config/equipe-ausentes.txt`); arquivos locais dele em `~/.cache/agata/sincronia/arquivo-codex-20261103/`.

**Esperando você:** assinar `economia-contexto-24-11` (carga conforme a tarefa + economia de tokens permanente; 3 arquivos canônicos; CI local passou nos passos do lote; comando: `bash scripts/aprovar.sh economia-contexto-24-11`). Assinar `agata-robustez-codeql-medicoes-20261103` (5 alertas do CodeQL, fallback do pytest, escriba sem `cryptography`, medição de vários fatos e da busca por sentido). Assinar `ferramentas-unificadas-26-11` (fonte única de ferramentas para todos os modelos do Conselho + skill de arranque universal; CI 95/95, revisão 4 altos + 2 médios corrigidos; comando: `bash scripts/aprovar.sh ferramentas-unificadas-26-11`). Decidir na assinatura entre E (`permissions.ask` global + `permissions.allow` em `~/agata`) ou C (desinstalar extensão Chrome) para R4 do claude-in-chrome — opção B original não funciona (deny vence allow). Apagar 512 branches remotos já mesclados (lista na pasta da Área de trabalho) e decidir sobre 12 não mesclados. Decisões de doutrina: P-9 sob demanda, P-16 contra P-17, escalada do P-24.

## Hoje, 22 e 23/10

**Já valendo (assinado e aplicado):**
- A Seth responde pela cascata com a memória completa. Dados pessoais deixaram de bloquear a saída externa; só segredo continua bloqueado.
- A escrita em MEMÓRIAS pelo LibreChat exige sua aprovação, e foi comprovada uma vez. O diário saiu do chat.
- O escriba exige token por projeto e recusa segredo antes de gravar.
- O migrador de história e o gerador do mapa do PROJETO entraram (pacote 2a).
- O mapa do PROJETO na hidratação (pacote 2b). Medido em cópia: a hidratação caiu de 124 mil para 88 mil caracteres.
- A suíte de testes roda em paralelo, até 4 casos ao mesmo tempo. Antes levava cerca de 205 segundos; agora, cerca de 56 segundos, medido duas vezes com os 58 casos passando.

**Esperando você:**
- Assinar as propostas em conjunto, quando estiverem prontas. Hoje, uma: a correção da entrada 817 do MEMÓRIAS.
- Lista de nomes de projeto: não é necessária para a Seth funcionar. Só faz sentido se houver nome que não deva sair para a nuvem.

**Com o Codex:**
- As pastas reports, research_notes e o arquivo sh são do Codex. Serão sanitizadas quando o trabalho dele estiver concluído. Até lá, não são movidas.
- Propostas antigas: cinco não se aplicam mais ao main e não serão assinadas. Uma (cabecalho-modelo-real) ainda se aplica e será conferida antes de qualquer assinatura.

**Em espera:**
- Backfill das 11 tags dos chunks frios: depois de 29/10.
- Roteamento por capacidade: próxima frente, depois da correção da 817.

**Fechado:**
- Sombra em segundo plano (PR 474).
