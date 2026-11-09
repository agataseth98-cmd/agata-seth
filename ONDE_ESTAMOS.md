# Onde estamos

Atualizado em 03/11/2026.

Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 22/10/2026: `extras/arquivo/onde-estamos-ate-2026-10-22.md`; 28 e 29/10: `extras/arquivo/onde-estamos-ate-2026-10-29.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md`.

## Hoje, 09/11 (aplicação do painel unificado)

**Aplicação local validada:** `painel-unificado-07-11`. Assinatura P-8 confirmada, diff aplicado em worktree própria e CI local `TUDO OK`. A aplicação segue para PR; o Humano decide se junta. Registro em MEMÓRIAS (973).

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

**Esperando você:** assinar `agata-robustez-codeql-medicoes-20261103` (5 alertas do CodeQL, fallback do pytest, escriba sem `cryptography`, medição de vários fatos e da busca por sentido). Apagar 512 branches remotos já mesclados (lista na pasta da Área de trabalho) e decidir sobre 12 não mesclados. Decisões de doutrina: P-9 sob demanda, P-16 contra P-17, escalada do P-24.

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
