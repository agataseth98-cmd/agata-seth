# Onde estamos

Atualizado em 03/11/2026.

Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 22/10/2026: `extras/arquivo/onde-estamos-ate-2026-10-22.md`; 28 e 29/10: `extras/arquivo/onde-estamos-ate-2026-10-29.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md`.

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
