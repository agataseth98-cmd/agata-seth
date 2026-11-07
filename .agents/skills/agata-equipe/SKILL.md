---
name: agata-equipe
description: Papéis da equipe de agentes do Agata (spec, dev, revisor, ci, time de inovação e auditor), com o que cada um pode e não pode fazer, quem revisa quem, como passar trabalho entre papéis sem a conversa e o que só o Humano decide (assinatura, junção de aplicação, arquivar, apagar). Use antes de abrir lote com mais de um agente ou ao passar trabalho entre papéis.
---

# Equipe de agentes no Agata

Por quê: os erros de 06/11 estão no diário de `agata-processo-lote` (diff assinado com registro, relatório de subagente dado como prova, passo mecânico feito à mão). Esta skill fixa quem faz o quê. O passo a passo do lote é `agata-processo-lote`.

Princípio de papel:
- O papel é uma função, não um modelo.
- A garantia vem do script e da checagem, não da fala do agente.
- O Humano decide o que é decisão do Humano.

Os nomes são os de `.claude/agents/`. Um papel sem arquivo ali é descrito, não instalado: não diga que ele rodou.

## Papéis

| Papel | Função | Pode | Não pode | Quem revisa |
|---|---|---|---|---|
| coordenador (sessão que abre o lote) | Abre o lote e reparte a tarefa. Decide só o próximo passo do próprio lote | Montar pacote, rodar comandos de leitura, abrir PR de proposta, decidir a junção de proposta (padrão 692), com a saída de checks por `headSha` colada pelo `agata-ci` | Executar sozinho passo mecânico; assinar; aprovar; juntar aplicação; aceitar relatório sem saída colada; as proibições de git abaixo | Revisor diferente do que implementou; o Humano |
| `agata-spec` | Escreve a spec SDD (`spec.md`, `acceptance.json`, `brainstorm.md`, `decision.md`) e confere a âncora | Editar só `redesign/<componente>/spec/` na worktree; rodar `anchor.py` | Commitar; pôr `DECISAO: aceita` sem decisão do Humano; spec entra só por proposta própria (P-8); as proibições de git abaixo | `agata-revisor` (não o autor) |
| `agata-dev` | Implementa código e teste numa worktree de lote | Editar só os arquivos da tarefa (inclui o registro do passo 10, se a tarefa listar); rodar testes e colar a saída | Commit, push, sudo, instalar pacote, ler `.env`, citar `memoria/missoes`, chamar provedor real; as proibições de git abaixo | `agata-revisor` (não o próprio dev) |
| `agata-revisor` | Revisão independente de diff ou proposta | Ler diff, spec, log; rodar só comandos de leitura | Editar, commitar, aplicar; dizer "aprovado" (quem decide é o Humano); as proibições de git da lista única | O Humano, com o veredito |
| `agata-ci` | Responsável único pela conferência de passo mecânico: CI local, diagnóstico de falha, mecânica de aplicação, commit, push e PR quando o coordenador ordena | Rodar `ci_sdd_local.sh`, `git status`, `git apply` em worktree de aplicação, commit com caminhos explícitos, abrir PR, conferir a saída de todo passo mecânico; testar a âncora no worktree da proposta (passo 2); conferir o `headSha` dos checks (passo 5); executar a junção de proposta, com ordem do coordenador e headSha verde; rodar `reindexar` (passo mecânico) | Editar código e o registro (`MEMÓRIAS.md`, `ONDE_ESTAMOS.md`); assinar; juntar aplicação; as proibições de git abaixo | O Humano, pela saída colada |
| `agata-inov-pesquisa` | Estado da arte e problemas reais do Agata, com fonte | Ler, buscar, pesquisar na web | Editar, commitar, decidir a ideia | `agata-inov-critico` |
| `agata-inov-arquiteto` | Transforma ideia em brainstorm e spec mínima, num diretório fora do repositório | Escrever no diretório que a tarefa indicar | Escrever em `redesign/`, `scripts/`, `config/` ou `.agents/` (isso é P-8); implementar; citar `memoria/missoes` | `agata-inov-critico` |
| `agata-inov-critico` | Crítica de ideia e spec contra governança e evidência | Ler, buscar, rodar leitura | Editar, commitar, aplicar; decidir (entrega só a recomendação ao Humano) | O Humano |
| `agata-auditor` (função contínua) | Audita o processo e a conduta do coordenador; cobra com evidência | Ler logs, diffs, PRs e saídas; reportar ao Humano | Gravar, aprovar, juntar, assinar, dar ordem de destruição; as proibições de git da lista única | O Humano. Sem arquivo de definição no `origin/main` (06/11, `git ls-tree`) |

Quem coordena um lote não é o revisor dele. Quem implementa não revisa o que implementou.

## Barreiras
- A barreira é a permissão da sessão e o classificador, não o frontmatter. A linha `tools:` de cada arquivo em `.claude/agents/` declara o que o papel usa; não impede nada por si só.
- O registro (`MEMÓRIAS.md`, `ONDE_ESTAMOS.md`) é gravado pelo `agata-dev`, nomeado, e conferido pelo `agata-ci`. O coordenador não grava o registro, mesmo que a sessão lhe dê Edit ou Write: passo mecânico não é dele. Quem só tem Bash, como o `agata-ci`, também não grava.

## Proibições de git (lista única)
Vale para todo papel com Bash: coordenador, `agata-spec`, `agata-dev`, `agata-ci`, `agata-revisor`, `agata-inov-pesquisa`, `agata-inov-arquiteto`, `agata-inov-critico` e `agata-auditor` (quando tiver arquivo). Sem exceção, salvo a linha marcada.
- `git reset --hard`
- `rm -rf`
- `git checkout --`
- `git add -A` (use caminhos explícitos)
- `--force` (inclusive em `git worktree remove` e em push)
- `--amend` em commit de proposta (refaça sobre a base atual, `origin/main`)
- `git clean`
- `git rm -f` (linha marcada: só com ordem do Humano nesta conversa, arquivo por arquivo; armadilha de `agata-processo-lote`)

Restaurar arquivo gerado ou apagar qualquer coisa é decisão do Humano (item 5 de `agata-processo-lote`).

## Pacote de passagem (sem a conversa)

Trabalho passa de um papel para outro por arquivo de texto num diretório de trabalho da tarefa (fora do repositório, ou no scratchpad). Conteúdo mínimo:
1. Caminho absoluto da worktree e nome da branch.
2. Objetivo em até três linhas.
3. Arquivos que o papel pode editar. Em revisão, escreva "somente leitura".
4. Comandos a rodar e o que a saída deve mostrar.
5. Critérios de aceite, cada um com o nome do teste que o prova.
6. Proibições do papel: a lista de git acima e as da tabela.
7. Formato da resposta: texto, com `arquivo:linha` e a saída real colada.

Não entra no pacote: a conversa do coordenador, opiniões não registradas, segredos, caminhos de `memoria/missoes`, e o raciocínio de quem implementou. O revisor recebe o diff, a descrição e os critérios. Para revisão SDD oficial, `redesign/review_mesh/mesh.py prepare <spec> <pasta>` gera o pacote e `consolidate` junta os pareceres.

## Retorno e conferência
- Relatório é alegação. Quem recebe confere o código e roda o teste ou o comando por conta própria. "Passou" sem saída colada não conta.
- Conferência de passo mecânico: sempre `agata-ci`. O coordenador decide só o próximo passo do próprio lote.
- Trabalho em paralelo só com arquivos disjuntos. Cada agente recebe a sua lista; duas edições no mesmo arquivo viram conflito que ninguém vê.
- Relatório sem caminhos de arquivo não é conferível: devolva.
- Criação de arquivo encadeada com `||` pode sair vazia (caso `test_conjunto_dev.py`, diário de `agata-processo-lote`, 06/11): confira tamanho e conteúdo depois.

## Crescimento da equipe (por demanda)

A equipe cresce quando o trabalho exige mais do que os papéis atuais cobrem.
- Gatilho: (a) uma frente de trabalho não tem dono capaz de executá-la; (b) um papel está sobrecarregado, isto é, mais de um lote simultâneo, ou passo mecânico feito pelo coordenador. O gatilho precisa de evidência medida.
- Medição em log antes de propor: o log, o comando que gerou a contagem e a data. Contagem informada por alguém não é prova. Sem a medição, não há proposta.
- Quem propõe: `agata-auditor`, quando existir. Enquanto não existir (06/11, sem arquivo no `origin/main`), quem propõe é o coordenador, com a medição; o Humano decide. Nenhum agente cria papel por conta própria.
- A proposta diz: nome, função, o que pode e o que não pode fazer, quem revisa, quem confere a saída, e a evidência medida que motivou.
- Papel novo entra como arquivo em `.claude/agents/`, por proposta assinada. Sem arquivo, o papel não existe. Tipo novo só é reconhecido em sessão nova.
- Nenhum caso nesta proposta. O candidato com mais peso (passos mecânicos feitos pelo coordenador) ainda não tem medição em log; entra em proposta própria depois de medido.

## O que só o Humano decide
- Assinatura: `scripts/aprovar.sh <lote>` roda só o Humano. O agente entrega o comando exato e o motivo, e para.
- Junção de aplicação: o PR de aplicação é juntado pelo Humano. A junção de proposta segue o padrão 692: o coordenador decide, com a saída de checks por `headSha` colada pelo `agata-ci`.
- Arquivar: ideia, lote, worktree ou `APROVADO-*`. Nenhum agente arquiva por conta própria.
- Apagar ou restaurar: worktree com alteração, arquivo gerado, cópia de `APROVADO-*`, dado. Só com ordem explícita do Humano nesta conversa (item 5 de `agata-processo-lote`), arquivo por arquivo.
- Versionar `APROVADO-*` no git: só com ordem do Humano.
- Criar papel novo ou mudar esta skill: o Humano decide, e entra como proposta, não como edição direta no main.

## Quando parar e pedir
- Permissão negada pelo classificador: pare, explique o que tentou e espere (item 4 de `agata-processo-lote`). Não recrie a ação por outro caminho.
- Check obrigatório vermelho, ausente no `headSha` atual, ou conflito `DIRTY`.
- Ordem destrutiva sem ordem registrada nesta conversa.
- Agente que não é reconhecido na sessão (`Agent type not found`): tipos são lidos na inicialização. Usar o papel com a mesma instrução só se o Humano aceitar, e dizer que foi assim (diário de `agata-processo-lote`).
- Pedido de passo mecânico para o coordenador executar sozinho: devolva ao papel certo (tabela "Quem faz cada passo mecânico" em `agata-processo-lote`).
