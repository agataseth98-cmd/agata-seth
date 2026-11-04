# Oportunidades no que ainda está em aberto (04/11/2026, 08:35, medido com `date`)

Autor: Claude Sonnet 5.5 (Claude Code). Cada item traz o dado que o sustenta e o que depende de quem. Nada aqui foi aplicado.

## 1. O orçamento de memória (P-24) não cabe no ritmo de escrita

Medido em `MEMÓRIAS.md` (150 entradas, 127.438 caracteres nas entradas): **25% do texto tem até 7 dias, 71% tem de 8 a 14 dias, 4% de 15 a 30 e nada passa de 30 dias.** Ou seja, a camada quente guarda duas semanas e escreve cerca de 9 mil caracteres por dia. O orçamento de 25.000 caracteres equivale a menos de 3 dias. Não há como cumprir o orçamento só migrando entradas mais velhas, porque as velhas já saíram.

Oportunidade: decidir entre (a) subir o orçamento para o tamanho que a janela de 14 dias realmente ocupa, (b) encurtar a janela quente para 3 dias e mover o resto para o morno, ou (c) comprimir entradas longas. A (b) usa a ferramenta que já existe (`scripts/migrar_periodo.py`). Depende do Humano: é doutrina da hidratação.

## 2. A causa dos 544 branches remotos é uma opção do GitHub

O repositório mescla com `--delete-branch=false` por convenção, e nada apaga o branch depois. Medido: 526 dos 544 remotos já estão contidos na `main`. Oportunidade: ligar no GitHub "apagar automaticamente o branch ao mesclar" mantém o problema resolvido para sempre. É configuração do repositório, então depende de você. Para o estoque atual, os 31 branches não mesclados já foram arquivados em tags `arquivo/20261104/*` (30 no remoto), então apagar não perde commit.

## 3. Pré-checagem do CodeQL antes da assinatura

Em um dia, dois PRs de aplicação (830 e 842) foram barrados por alertas novos que só aparecem depois da assinatura. Oportunidade: uma checagem local barata dos padrões que o CodeQL acusou (regex montado com variável, caminho vindo de pedido, comando com dado do pedido) dentro do comando `runner.py proposal`, antes de gerar o diff. Custa um módulo pequeno e evita uma assinatura perdida por incidente. Instalar a CLI do CodeQL seria mais fiel, mas exige download e sua aprovação.

## 4. Custo e esforço: faltam dados, não código

O gateway não guarda uso de tokens. O `registro_pedidos.py` guarda texto, não tokens, e vem desligado. Oportunidade: capturar o campo `usage` das respostas dos provedores no gateway (só números, sem texto) em um arquivo fora do repositório. É o pré-requisito para medir cache de prompt, custo por modelo e esforço por tarefa. Depende de proposta P-8 em `redesign/router/`.

## 5. Conjunto de ouro com abstenção graduada

Hoje são 7 casos e 1 aceita abstenção. A regra do artigo da OpenAI (erro confiante custa mais que "não sei") pede um tipo novo de caso, em que a resposta certa é "não medido" e o erro confiante pontua negativo. Depende do Humano autorizar mexer nos casos reservados.

## 6. Medição de contexto: agregação e rastreio

O medidor cobre recuperação de um fato e de vários fatos parecidos. Faltam as duas tarefas do RULER que degradam primeiro (agregação e rastreio de variáveis). Oportunidade: acrescentar as duas ao `medir_contexto_efetivo.py` e rodar no `qwen3.5-9b-64k`. Não depende de ninguém.

## 7. SDD com projeto real

O ciclo declarativo está aplicado e provado em projeto de teste, e a aba SDD lista projetos em `config/sdd/`, mas não há nenhum registrado. Depende do Humano dizer qual projeto vem primeiro.

## 8. Sessão da Equipe e canal do Codex

A sessão da Equipe parou na base `6fc87db`, de 28/10, e o Codex reporta o sistema de arquivos como somente leitura, então não consegue gravar no canal. Oportunidade: com o Codex de volta, renovar a base (`equipe.py iniciar --nova-base`) e dar a ele escrita só em `~/.cache/agata/sincronia/`. Depende do Humano.

## 9. A proposta semanal de memória

`memoria-semanal-2026-11-03` é a única pendência de assinatura. Oportunidade: o nome da próxima chega sozinho toda semana; vale um aviso no painel quando houver proposta aguardando você.

## 10. Dúvidas em aberto do teste de português e do harness adaptativo (marcadas em 04/11/2026 15:06)
Nenhuma foi investigada. Detalhe em `teste-portugues/RESULTADO.md`, seção "Dúvidas EM ABERTO". Resumo: (1) causa da piora do 9b no harness completo; (2) T5 do `qwen3:4b`; (3) T4 do Lumi e T1 do 4b; (4) perfil circular, falta conjunto de tarefas novas; (5) T6, T7, T9 não discriminam e o avaliador de recusa é por palavras; (6) qualidade de português não medida; (7) efeito isolado da retentativa; (8) temperatura 0 contra 0,3; (9) termos da licença do Lumi não lidos.

## 11. O roteador ainda não lê o perfil de capacidades
`config/capacidades_modelos.json` existe e só o `teste_portugues.py` o usa. Oportunidade: o roteador Laya e o gateway escolherem a estratégia por modelo (formato simples ou harness) a partir dele. Depende de proposta P-8 em `redesign/router/`.
