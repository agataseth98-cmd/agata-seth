---
name: agata-equipe
description: >-
  Trabalhar com a equipe de agentes do Agata: papéis (spec, dev, revisor, ci, inovação, auditor) e o que cada um
  pode e não pode fazer; partida conjunta, canal MSG, vigia sem timer, fila, fallback quando um membro cai,
  economia de cota e o que só o Humano decide. Use ao abrir ou retomar sessão conjunta, antes de abrir lote com
  mais de um agente, ao passar trabalho entre papéis ou quando um membro some.
---

# Equipe no Agata

Por quê: em 16/10/2026 a dupla Claude × Codex entregou cerca de 20 mudanças assinadas num dia, e gastou cota e errou nas fronteiras que não modelava (MEMÓRIAS (732): timer de 2 min, mensagens de estado, crase executada pelo shell, número (729) repetido 14 vezes, vigia vencido). As ferramentas moram em `scripts/equipe/`; o estado fica fora do repo, em `~/.cache/agata/sincronia/equipe/`.

Princípios:
- O papel é uma função, não um modelo.
- A garantia vem do script e da checagem, não da fala do agente.
- O Humano decide o que é decisão do Humano.

Membro = nome curto em minúsculas (`claude`, `codex`, `gemini`, `opencode`, `seth`...). Nenhum nome é fixo no código: quem chega entra com `--agente <nome>`; `iniciar --com a,b,c` diz quem a partida espera (sem a lista, quaisquer dois abrem). Linha nova na matriz só entra com o aceite de todos os outros presentes.

Os nomes de papel são os de `.claude/agents/`. Papel sem arquivo ali é descrito, não instalado: não diga que ele rodou. O passo a passo do lote está em `agata-aplicar-proposta`. O painel está em `agata-painel`.

## 0. Antes de tudo

- Cabeçalho da Regra 1 em toda resposta, mesmo em NPR (`PROTOCOLOS.md`, "Carregar e formatos" e "Regra 1.1"). Não crie formato próprio para o fluxo em equipe.
- Texto longo para o canal vai por arquivo: `equipe.py dizer ... --texto "$(cat arq.txt)"`. Nunca crase dentro de aspas duplas: crase em texto de argumento executa comando.
- Você nunca roda `scripts/aprovar.sh`, nunca usa `sudo`, nunca abre segredo. Só o Humano assina.

## 1. Partida e retomada

1. `python3 scripts/equipe/equipe.py status`. Se "divergente" ou "aguardando": `iniciar --agente <eu> --nova-base --aceitar-matriz <hash da matriz>`.
2. `python3 scripts/painel_estado.py` mostra HEAD, serviços, propostas sem assinatura válida e o comando de assinatura. Fila: `~/.cache/agata/sincronia/fila.md`.
3. `equipe.py estado --agente <eu> --item <nome> --estado <em_andamento|em_revisao|pronto|bloqueado>` mantém o quadro. Dois itens ativos por agente.
4. Presença e canal: `equipe.py presente --agente <eu>`; ler com `equipe.py ler --agente <eu>` (mostra só o novo); responder com `equipe.py dizer --agente <eu> --assunto "..." --resposta-a <id> --estado <estado> --proximo <agente> --texto "..."`.
5. Ler o canal inteiro: arquivo `~/.cache/agata/sincronia/conversa.md` (por exemplo, `sed` a partir da última linha `## `). `scripts/equipe/inicio.sh <eu>` mostra só o resumo da última entrada.
6. Protocolo MSG: "MSG" no fim de uma mensagem do Humano significa ler o canal, responder e terminar o texto de devolução com `MSG`.
7. Deriva (base diferente de `origin/main`) não se corrige sozinha: é decisão do Humano (`iniciar --nova-base`).
8. Matriz congelada: `aceitar-linha` **altera** a matriz. Confirme com o Humano antes. Em 28/10/2026 a matriz foi trocada sem decisão prévia dele; foi registrada no canal, e o Humano decidiu manter a nova.

## 2. Esperar sem gastar: vigia sem timer

- **Permanente (decisão do Humano, 16/10/2026):** a vigia roda sempre para todos os modelos, como unit `agata-vigia@<agente>` (`config/systemd/agata-vigia@.service`). Eventos em `~/.cache/agata/sincronia/vigia-<agente>.log`. Quem tem Monitor só acompanha com `tail -n0 -F` nesse arquivo. Não precisa rearmar nem rodar `vigia.sh` à mão.
- Segundo plano (com Monitor): `bash scripts/equipe/vigia.sh <eu> 20`. Avisa mensagem de outro membro, `APROVADO-` novo, `main` andou e pedido parado ("DEVO RESPOSTA" a partir de 8 min; "SEM RESPOSTA: <membro>" a partir de 15 min).
- Bloqueante (quem não acorda por stdout): `bash scripts/equipe/vigia.sh <eu> 20 --uma 600`. Sai no primeiro evento ou imprime "SEM EVENTO em 600s". Chame de novo sem texto. Sem timer de 2 min.
- Monitores têm prazo (30 min): ao notificar a expiração, rearme.
- Mensagens: uma por ENTREGA ou BLOQUEIO, agrupada, com caminho e SHA. Nunca resposta só de estado. Não copie relatório para o canal.

## 3. Papéis

| Papel | Função | Pode | Não pode | Quem revisa |
|---|---|---|---|---|
| coordenador (sessão que abre o lote) | Abre o lote e reparte a tarefa. Decide só o próximo passo do próprio lote | Montar pacote, rodar comandos de leitura, abrir PR de proposta, decidir a junção de proposta (padrão 692), com a saída de checks por `headSha` colada pelo `agata-ci` | Executar sozinho passo mecânico; assinar; aprovar; juntar aplicação; aceitar relatório sem saída colada; as proibições de git da seção 4 | Revisor diferente do que implementou; o Humano |
| `agata-spec` | Escreve a spec SDD (`spec.md`, `acceptance.json`, `brainstorm.md`, `decision.md`) e confere a âncora | Editar só `redesign/<componente>/spec/` na worktree; rodar `anchor.py` | Commitar; pôr `DECISAO: aceita` sem decisão do Humano; spec entra só por proposta própria (P-8) | `agata-revisor` (não o autor) |
| `agata-dev` | Implementa código e teste numa worktree de lote | Editar só os arquivos da tarefa (inclui o registro do passo 10, se a tarefa listar); rodar testes e colar a saída | Commit, push, sudo, instalar pacote, ler `.env`, citar `memoria/missoes`, chamar provedor real | `agata-revisor` (não o próprio dev) |
| `agata-revisor` | Revisão independente de diff ou proposta | Ler diff, spec, log; rodar só comandos de leitura | Editar, commitar, aplicar; dizer "aprovado" (quem decide é o Humano) | O Humano, com o veredito |
| `agata-ci` | Conferência de passo mecânico: CI local, diagnóstico de falha, mecânica de aplicação, commit, push e PR quando o coordenador ordena | Rodar `ci_sdd_local.sh`, `git status`, `git apply` em worktree de aplicação, commit com caminhos explícitos, abrir PR; testar a âncora no worktree da proposta; conferir o `headSha` dos checks; executar a junção de proposta com ordem do coordenador e headSha verde; rodar `reindexar` | Editar código e o registro (`MEMÓRIAS.md`, `ONDE_ESTAMOS.md`); assinar; juntar aplicação | O Humano, pela saída colada |
| `agata-inov-pesquisa` | Estado da arte e problemas reais do Agata, com fonte | Ler, buscar, pesquisar na web | Editar, commitar, decidir a ideia | `agata-inov-critico` |
| `agata-inov-arquiteto` | Transforma ideia em brainstorm e spec mínima, num diretório fora do repositório | Escrever no diretório que a tarefa indicar | Escrever em `redesign/`, `scripts/`, `config/` ou `.agents/` (isso é P-8); implementar; citar `memoria/missoes` | `agata-inov-critico` |
| `agata-inov-critico` | Crítica de ideia e spec contra governança e evidência | Ler, buscar, rodar leitura | Editar, commitar, aplicar; decidir (entrega só a recomendação ao Humano) | O Humano |
| `agata-auditor` (função contínua) | Audita o processo e a conduta do coordenador; cobra com evidência | Ler logs, diffs, PRs e saídas; reportar ao Humano | Gravar, aprovar, juntar, assinar, dar ordem de destruição | O Humano. Sem arquivo de definição no `origin/main` (06/11, `git ls-tree`) |

Quem coordena um lote não é o revisor dele. Quem implementa não revisa o que implementou.

Barreira: a permissão da sessão e o classificador seguram, não o frontmatter. A linha `tools:` de cada arquivo em `.claude/agents/` declara o que o papel usa; não impede nada por si só. O registro (`MEMÓRIAS.md`, `ONDE_ESTAMOS.md`) é gravado pelo `agata-dev`, nomeado, e conferido pelo `agata-ci`. O coordenador não grava o registro, mesmo que a sessão lhe dê Edit ou Write: passo mecânico não é dele.

## 4. Proibições de git (lista única)

Vale para todo papel com Bash, sem exceção, salvo a linha marcada:
- `git reset --hard`
- `rm -rf`
- `git checkout --`
- `git add -A` (use caminhos explícitos)
- `--force` (inclusive em `git worktree remove` e em push)
- `--amend` em commit de proposta (refaça sobre a base atual, `origin/main`)
- `git clean`
- `git rm -f` (linha marcada: só com ordem do Humano nesta conversa, arquivo por arquivo; armadilha de `agata-aplicar-proposta`)

Restaurar arquivo gerado ou apagar qualquer coisa é decisão do Humano (regra 5 de `agata-aplicar-proposta`).

## 5. Pacote de passagem e conferência

Trabalho passa de um papel para outro por arquivo de texto num diretório de trabalho da tarefa (fora do repositório, ou no scratchpad). Conteúdo mínimo:
1. Caminho absoluto da worktree e nome da branch.
2. Objetivo em até três linhas.
3. Arquivos que o papel pode editar. Em revisão, escreva "somente leitura".
4. Comandos a rodar e o que a saída deve mostrar.
5. Critérios de aceite, cada um com o nome do teste que o prova.
6. Proibições do papel: a lista da seção 4 e as da tabela.
7. Formato da resposta: texto, com `arquivo:linha` e a saída real colada.

Não entra no pacote: a conversa do coordenador, opiniões não registradas, segredos, caminhos de `memoria/missoes`, e o raciocínio de quem implementou. O revisor recebe o diff, a descrição e os critérios. Para revisão SDD oficial, `redesign/review_mesh/mesh.py prepare <spec> <pasta>` gera o pacote e `consolidate` junta os pareceres.

- Relatório é alegação. Quem recebe confere o código e roda o teste ou o comando por conta própria. "Passou" sem saída colada não conta.
- Conferência de passo mecânico: sempre `agata-ci`. O coordenador decide só o próximo passo do próprio lote.
- Trabalho em paralelo só com arquivos disjuntos. Cada agente recebe a sua lista; duas edições no mesmo arquivo viram conflito que ninguém vê.
- Relatório sem caminhos de arquivo não é conferível: devolva.
- Criação de arquivo encadeada com `||` pode sair vazia (caso `test_conjunto_dev.py`, 06/11): confira tamanho e conteúdo depois.

## 6. Fallback e economia de cota

- `equipe.py ausente --agente <quem> --motivo ... [--ate HH:MM]` só com confirmação (do Humano ou do próprio agente). Silêncio não prova cota esgotada. `presente --agente <quem>` encerra.
- Ausente: os outros presentes cobrem trabalho independente na pista dele (aparece como ASSUMIDA em `equipe.py verificar`). O titular revisa ao voltar.
- Não cai no fallback: assinar, `aprovar.sh`, `sudo`, configuração do GitHub, instalar ou reiniciar serviço, abrir segredo.
- Economia de cota (regra do Humano: "sem desperdício"): despertar começa por checagem em shell (`git ls-remote origin main`, `ls propostas/APROVADO-*`, contagem de blocos novos). Sem mudança, encerre sem texto. Fila longa: itens de 10 min ou mais; terminou um, abra o próximo sem esperar mensagem. Não repetir prova verde.
- Trabalho caro em tokens vai para o modelo com mais folga; o relato volta pelo canal.

## 7. Crescimento da equipe (por demanda)

- Gatilho: (a) uma frente de trabalho não tem dono capaz de executá-la; (b) um papel está sobrecarregado (mais de um lote simultâneo, ou passo mecânico feito pelo coordenador). O gatilho precisa de evidência medida: o log, o comando que gerou a contagem e a data. Contagem informada por alguém não é prova.
- Quem propõe: `agata-auditor`, quando existir. Enquanto não existir, o coordenador propõe, com a medição; o Humano decide. Nenhum agente cria papel por conta própria.
- A proposta diz: nome, função, o que pode e o que não pode fazer, quem revisa, quem confere a saída, e a evidência medida.
- Papel novo entra como arquivo em `.claude/agents/`, por proposta assinada. Sem arquivo, o papel não existe. Tipo novo só é reconhecido em sessão nova.

## 8. O que só o Humano decide

- Assinatura: `scripts/aprovar.sh <lote>` roda só o Humano. O agente entrega o comando exato e o motivo, e para.
- Junção de aplicação: o PR de aplicação é juntado pelo Humano. A junção de proposta segue o padrão 692: o coordenador decide, com a saída de checks por `headSha` colada pelo `agata-ci`.
- Arquivar: ideia, lote, worktree ou `APROVADO-*`. Nenhum agente arquiva por conta própria.
- Apagar ou restaurar: worktree com alteração, arquivo gerado, cópia de `APROVADO-*`, dado. Só com ordem explícita do Humano nesta conversa, arquivo por arquivo.
- Versionar `APROVADO-*` no git: só com ordem do Humano.
- Criar papel novo ou mudar esta skill: o Humano decide, e entra como proposta, não como edição direta no `main`.

## 9. Pacote mínimo para subagente (decisão do Humano, 12/11/2026)
- Quem delega passa ao subagente só: objetivo, arquivos, critérios de pronto, as regras que se aplicam e o turno do pai (`t=<n>.sub`). Nunca a conversa inteira.
- O subagente segue AGENTS.md, que ele carrega sozinho: pelo CLAUDE.md (Claude Code) ou lendo AGENTS.md na partida (Codex, OpenCode). Não copie AGENTS.md no prompt.
- O que faltar para a tarefa volta como lacuna em uma linha. Contexto completo "por garantia" não entra.

## 10. Quando parar e pedir

- Permissão negada pelo classificador: pare, explique o que tentou e espere. Não recrie a ação por outro caminho.
- Check obrigatório vermelho, ausente no `headSha` atual, ou conflito `DIRTY`.
- Ordem destrutiva sem ordem registrada nesta conversa.
- Agente que não é reconhecido na sessão (`Agent type not found`): tipos são lidos na inicialização. Usar o papel com a mesma instrução só se o Humano aceitar, e dizer que foi assim.
- Pedido de passo mecânico para o coordenador executar sozinho: devolva ao papel certo (tabela "Quem faz cada passo mecânico" em `agata-aplicar-proposta`).
- Um modelo que não se julga apto (erro de medição recorrente, afirmação sem prova, perda de contexto) diz isso e pede substituição (entrada 789).

## 11. Armadilhas já pagas

- Crase em texto de argumento executa comando.
- `pkill -f` com o padrão na própria linha mata o seu shell. Liste com `ps` e mate por PID.
- Número de MEMÓRIAS: `aplicar.py` aceita qualquer palavra após o número.
- Comando de assinatura antes de a proposta chegar ao `main`.
- `fiscal-p8` obrigatório sem testar com o hook ligado barrou todo PR.
- Afirmar comportamento de código só pela descrição da unit.
- Hora herdada do cabeçalho anterior.

## 12. Mudança protegida em equipe

Use `agata-aplicar-proposta` para o ciclo P-8. Esta seção acrescenta a coordenação entre modelos:
1. Autor e revisor são modelos diferentes; não editam o mesmo arquivo ao mesmo tempo.
2. O revisor escolhe e registra os casos antes de ver os resultados, executa-os e devolve o parecer no formato de quatro partes.
3. O autor abre a proposta contra `origin/main` e só a junta após os checks exigidos passarem. O Humano assina depois que a proposta estiver no `main`.
4. A aplicação é um PR separado, em worktree própria; um PR de aplicação por vez. O Humano junta esse PR.
5. Na divergência ou no conflito, pare e reporte evidência. Não force merge nem refaça a assinatura.

## 13. Comando de assinatura (Humano, Fish, uma linha)

Gere pelo painel (`python3 scripts/painel_estado.py`) ou monte uma linha que confira o hash de cada proposta antes de assinar qualquer uma. A bandeira `ok` tem de ser usada dentro do `for`: um `false` seria sobrescrito. A igualdade tem de ser positiva: arquivo ausente conta como divergência. Antes de entregar, confirme que a proposta está em `origin/main` (`ls propostas/`) e tire o hash do arquivo, nunca da memória.

## 14. Devolutiva final

- Toda resposta final de entrega termina com `Devolutiva para CODE` e a skill mais indicada para a continuação.
- Seja sucinta sem perder o necessário para retomar: resultado e estado; arquivos, PR e SHA quando houver; testes e placar; pendências, limites e confirmação humana exigida.
- Diferencie proposta, diff, assinatura, aplicação e merge. Não diga que algo foi publicado ou aplicado quando não foi.
- A devolutiva é texto no fim da resposta; não envie mensagem para outro agente ou serviço sem autorização explícita.
