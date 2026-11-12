---
name: agata-aplicar-proposta
description: >-
  Criar, verificar, propor e aplicar um lote de mudança protegida no Agata (proposta P-8): worktree, CI local,
  âncora de specs, uma assinatura por lote, PR de proposta e de aplicação, registro em MEMÓRIAS. O Humano assina;
  o modelo nunca assina nem roda aprovar.sh. Use antes de qualquer proposta P-8 ou aplicação.
---

# Proposta P-8 e lote: criar, verificar, aplicar

Por quê: os lotes de 06/11/2026 quebraram em pontos recorrentes (testes que o CI roda e nós não rodamos, comando que falhou em silêncio por causa de `| tail`, arquivo gerado no commit, conflito de âncora, diff assinado com registro). Esta skill é a lista do que já quebrou. Siga na ordem.

Escopo: o repositório `/home/orusoua/agata`. Caminhos de worktree são sempre absolutos. Quem tem o papel de cada passo está em `agata-equipe`. O que é protegido está em `propostas/README.md`.

## Classe da tarefa (P4, 11/11)

Antes do passo 1, escolha uma classe e registre: linha "Classe:" em `propostas/<lote>.md`; na tarefa sem proposta, na entrada de MEMÓRIAS. Se a classe mudar, registre a troca. Classe errada pula revisão.

- **Operacional**: nada que muda comportamento nem arquivo protegido. Faça e registre no DIÁRIO.
- **Comportamento**: código, teste ou script que muda o que um componente faz. Spec com `acceptance.json` antes do código (papel `agata-spec`); depois proposta P-8, revisada pelo `agata-revisor` no modo "contra a spec".
- **Canon**: `REGRAS.md`, `PROTOCOLOS.md`, `FALHAS.md`, `PROJETO.md`, `AGENTS.md`, `CLAUDE.md`. Spec mínima (o que muda, como medir, reversão) e proposta P-8, com a mesma revisão de comportamento.

## Regras que não se negociam

1. Um lote = uma proposta = uma assinatura do Humano. Nunca rode `scripts/aprovar.sh`. Exceção: mudança em `redesign/*/spec/spec.md` exige proposta própria, assinada à parte (armadilha "Spec é P-8", caso de 06/11: `spec-anchor-lote-pn-20261106`).
2. Código protegido só entra no `main` por proposta assinada. O hook P-8 recusa commit direto; não contorne. A lista é a do `AGENTS.md`: `redesign/*`, `scripts/*`, `config/*`, `.githooks/*`, `REGRAS.md`, `PROTOCOLOS.md`, `FALHAS.md`, `PROJETO.md`, `MEMÓRIAS.md`, `AGENTS.md`, `CLAUDE.md`. `.agents/` e `.claude/` não aparecem nessa lista; tratá-los como protegidos é precaução (não verificado no P-8).
   Exceções a "só por proposta assinada", e só estas:
   - (a) Registro da proposta: `propostas/<lote>.diff`, `propostas/<lote>.md`, a entrada de proposta em `MEMÓRIAS.md` e a atualização de `ONDE_ESTAMOS.md` entram no PR de proposta, sem assinatura. Registro não tem quarentena (`propostas/README.md`, "SEM quarentena").
   - (b) Entrada de aplicação: a entrada de registro da aplicação (passo 10) entra no PR de aplicação, fora do diff assinado.
3. Não edite o checkout vivo `/home/orusoua/agata` para trabalho de lote. Trabalhe em worktree a partir de `origin/main`. `scripts/p8_verificar.sh` é só leitura (usa um diretório temporário que apaga ao sair), então rodá-lo no checkout vivo não é edição.
4. Permissão negada pelo classificador é decisão do Humano. Pare, explique o que tentou e por que precisa, e espere. Não recrie a ação por outro caminho.
5. Destruir ou restaurar só com ordem explícita do Humano nesta conversa: remover worktree com alteração, apagar dado, remover ou restaurar arquivo gerado, apagar cópia de `APROVADO`. Sem ordem, pergunte.

## Papéis e coordenação (06/11/2026)

- Quem coordena um lote não é o revisor dele. Quem implementa não revisa o que implementou.
- Nenhum agente, nem o coordenador, executa sozinho passo mecânico (aplicação, commit, reindex, montagem de diff). Passo mecânico vai para `agata-ci` ou `agata-dev`. A conferência da saída (log, `git status --short`, `grep '^diff --git'`) é do `agata-ci`. Saída não colada não conta.
- A coordenação rotaciona entre lotes.
- Em proposta, refaça o lote sobre a base atual (`origin/main`), sem reescrever o commit já publicado.
- `APROVADO-*` só entra no git por aplicação, com ordem do Humano.
- Remover worktree: `git -C <worktree> status --porcelain` tem de sair vazio antes; sem `--force`; só com ordem do Humano.
- Restaurar arquivo gerado: só com ordem do Humano, arquivo por arquivo (regra 5).

**Quem faz cada passo mecânico.**
- Passos 1 e 3 (worktree, CI local): `agata-dev` cria a worktree; `agata-ci` roda o CI local.
- Passo 2 (teste da âncora no worktree da proposta): `agata-ci` roda `anchor.py` e cola a saída.
- Passo 4 (diff e conferência em cópia limpa): `agata-ci`.
- Passo 5 (PR de proposta): `agata-ci` abre o PR e confere o `headSha` dos checks, colando a saída. O coordenador decide a junção (padrão 692); `agata-ci` executa a junção e o `git pull`, com ordem do coordenador e `headSha` verde.
- Passos 6 e 7 (verificação de assinatura, aplicação em worktree própria): `agata-ci`, com checagem por passo.
- Passos 8 e 9 (mover o par, `git add`): `agata-ci`. Passo 10 (registro em `MEMÓRIAS.md` e `ONDE_ESTAMOS.md`): `agata-dev` grava, nomeado; `agata-ci` confere `git status --short` depois. O coordenador não grava o registro.
- Passo 11 (PR de aplicação): `agata-ci` abre; a junção é do Humano.
- Passo 12 (remover worktrees): `agata-ci`, só com `git status` vazio e ordem do Humano.
- Reindex: `agata-ci` roda `reindexar` e cola a saída.

**Pauta do auditor (antes de cada lote).** Papel contínuo; se não houver arquivo do papel em `.claude/agents/`, diga isso ao Humano e não finja que o auditor passou.
1. Premissa: a base da proposta está aplicada no `main` ou só como proposta?
2. Worktree: caminho, e `git status --porcelain` de cada uma que será removida.
3. Diff: `grep '^diff --git'` só com código; nenhum registro, nenhum `APROVADO-*`.
4. CI local: log com `CI LOCAL: TUDO OK` e a versão do pytest na própria saída.
5. Passos mecânicos: quem executou, com a saída colada.
6. Checks obrigatórios por `headSha`; `mergeStateStatus` sem `DIRTY`.
7. Ordens do Humano: quais ações de assinatura, destruição ou versionamento de `APROVADO-*` estão pendentes, e quais têm ordem registrada nesta conversa.

**Veredito do auditor (fim do lote).** Uma linha por item: `conforme`, `desvio` (com arquivo, log ou comando) ou `não medido`. Fecha com "lote conforme" ou "lote com N desvios", e manda os desvios ao Humano. O auditor não grava, não aprova, não junta.

## Passo a passo

1. **Worktree do lote.** Todas as worktrees deste processo ficam em `/home/orusoua/agata/.claude/worktrees/`, excluídas pelo `.git/info/exclude` local (verificado com `git check-ignore`). Comando: `git fetch -q origin && git worktree add -b proposta/<lote> /home/orusoua/agata/.claude/worktrees/<lote> origin/main`. Worktrees antigas fora dessa pasta não são removidas por este processo.
2. **Código e spec juntos.** Todo arquivo de código novo (`.py`, `.sh`, `.js`, `.html`) em componente ancorado precisa estar na seção `## Código` do `spec.md` daquele componente, senão a âncora falha (`código órfão`). Teste a âncora no worktree da proposta.
3. **CI local antes de propor:** `bash scripts/ci_sdd_local.sh`. Só siga com `CI LOCAL: TUDO OK`. Falha que já existia no `origin/main` pode seguir só se estiver registrada em `propostas/<lote>.md` e informada ao Humano. Para comparar, use a mesma árvore limpa, numa worktree a partir de `origin/main`. Rodar `anchor.py` num componente não substitui este passo: o CI roda todos os escopos do `sdd.yml`.
4. **Diff único.**
   - `git status` e `git diff --cached --name-only` primeiro. Depois `git add <caminhos explícitos>`. Nunca `git add -A` numa worktree com mudanças alheias.
   - `git diff --cached origin/main > propostas/<lote>.diff`. Arquivo novo entra com `git add -N <arq>` antes do `git diff`.
   - Teste o efeito numa cópia descartável (`git worktree add --detach <dir> HEAD`), nunca só lendo o diff.
   - Obrigatório: `grep '^diff --git' propostas/<lote>.diff` e conferir que só há caminhos de código. Se aparecer `MEMÓRIAS.md`, `ONDE_ESTAMOS.md`, `INDICE_MEMORIAS*.md`, `.hidrata.md`, `PROMPT_CARREGAMENTO.md`, qualquer coisa em `propostas/`, ou linha dentro de bloco `ANCORA-SHA`, pare e refaça o diff. Registro entra no PR de proposta, nunca no diff assinado (caso de 06/11).
   - Conferir em cópia limpa: `git worktree add --detach /home/orusoua/agata/.claude/worktrees/check-<lote> origin/main`. Depois, dentro de um `if`: `git -C /home/orusoua/agata/.claude/worktrees/check-<lote> apply --check /home/orusoua/agata/.claude/worktrees/<lote>/propostas/<lote>.diff`.
5. **PR de proposta: só diff e registro.** O PR traz `propostas/<lote>.diff`, `propostas/<lote>.md` (resumo, limites, comando de assinatura), a entrada de proposta em `MEMÓRIAS.md` e a atualização de `ONDE_ESTAMOS.md` (página de estado para o Humano, não para modelos; `propostas/README.md`, item 0). O código não vai como arquivo no PR: só dentro do `.diff`. Antes de propor, confira a premissa (regra da pauta, item 1). Espere o CI do commit (seção "CI é por commit"). Vermelho ou ausente: não junte, avise o Humano. Depois entregue o comando de assinatura, `bash scripts/aprovar.sh <lote>`, que o Humano roda.
6. **Depois da assinatura:** `bash scripts/p8_verificar.sh <lote>` no checkout vivo, onde está o `APROVADO-<lote>`. O script usa a raiz de confiança do HEAD (`git show HEAD:propostas/.allowed_signers`); confirme antes que `git rev-parse HEAD` é `origin/main`. Só se der `PODE APLICAR`, siga.
7. **Aplicação em worktree própria:** `/home/orusoua/agata/.claude/worktrees/aplica-<lote>`, a partir do `origin/main` atual. O diff já vem do `origin/main` (entrou pelo PR do passo 5). Copie só o `propostas/APROVADO-<lote>` para ela. Rode `p8_verificar.sh <lote>` lá também e aplique com checagem por passo:
   ```
   if git apply propostas/<lote>.diff; then echo OK; else echo FALHOU; exit 1; fi
   ```
   Nunca encadeie verificação com `| tail -1 &&`: o `tail` devolve 0 e o `git apply` roda mesmo com a verificação falha. Já aconteceu. Vale também para qualquer teste ou script de verificação.
   Se a mudança vale fora do repo (unit em `~/.config/systemd/user`, compose em `~/librechat`, config do OpenCode), siga a regra de runtime em `agata-fluxo`, seção 4: backup, copie, `cmp`, recarregue e prove pelo caminho real.
8. **Mova o par** para `propostas/aplicadas/` (só com aplicação ordenada pelo Humano; nenhum agente arquiva por conta própria). O diff vai com `git mv`, porque já está versionado pelo PR do passo 5. O `APROVADO-<lote>` vai com `mv`, porque é arquivo local, fora do commit de código. Depois prove com `git apply --check -R propostas/aplicadas/<lote>.diff`. Essa prova só mostra que os hunks do diff estão presentes na árvore; não prova que a árvore é exatamente o estado assinado.
9. **Adicione explicitamente:** `git add <caminhos explícitos>` com os caminhos de código do diff. Confira com `git diff --cached --name-only` que aparecem todos os caminhos do `grep '^diff --git'` (já aconteceu de esquecer arquivo modificado, e o CI pegou). O `APROVADO-<lote>` não entra no commit de código. Histórico: 562 arquivos `APROVADO-*` estão versionados em `propostas/aplicadas/` no `origin/main` (contagem de 06/11). Em qual commit entram não foi verificado; pergunte ao Humano antes de versionar um.
10. **Registro.** Entrada nova no `MEMÓRIAS.md` logo abaixo do marcador `ENTRADAS-NOVAS:AQUI`, número = topo + 1, no formato das entradas de topo. Nunca edite entrada antiga; correção é entrada nova. Atualize `ONDE_ESTAMOS.md` se o estado mudou. Antes do commit, rode `git status --short` e `git diff origin/main --stat`. A lista tem de ser só: caminhos do diff, `propostas/aplicadas/<lote>.diff`, `MEMÓRIAS.md` e `ONDE_ESTAMOS.md` (se mudou). Quando o commit mexe no canon, o pre-commit regenera `ANCORA-SHA`, `.hidrata.md` e `INDICE_MEMORIAS*.md`: eles entram pelo hook, não à mão. Qualquer outro caminho: pare.
11. **PR de aplicação:** abra contra `main` e confira os checks (seção "CI é por commit"). Junção: decisão do Humano. Se `mergeStateStatus` for `BEHIND` ou `DIRTY`, o branch precisa estar atualizado com `main` (a proteção tem `strict: true`): faça `git merge origin/main` no branch. Depois de qualquer merge de `main`, repita `bash scripts/p8_verificar.sh <lote>` e `git apply --check -R propostas/aplicadas/<lote>.diff` na worktree, e espere o run do novo `headSha`. Conflito em arquivo assinado (`propostas/<lote>.diff`, `APROVADO-*`, `propostas/aplicadas/*`): pare e peça ao Humano; não resolva à mão. Conflito de âncora: armadilha "Conflito de âncora". `BLOCKED`: espere os checks obrigatórios.
12. **Depois do merge:** não remova sem ordem as worktrees deste lote (`aplica-<lote>` e `check-<lote>`). Cópias de `APROVADO-<lote>` no checkout vivo não são apagadas pelo processo.

**Diga ao Humano o comando exato, sem ponto no fim:** `bash scripts/aprovar.sh <nome>`.

## CI é por commit

- Obrigatórios no `main` (verificado em 06/11 com `gh api repos/agataseth98-cmd/agata-seth/branches/main/protection`): `suite-adversarial`, `fiscal-p8` e `CodeQL`, com `strict: true`. Reconfira antes de juntar, porque a proteção pode mudar.
- Quem dispara em PR para `main`:
  - `suite-adversarial` (`.github/workflows/perimetro.yml`, evento `pull_request`) e `fiscal-p8` (`.github/workflows/fiscal-p8.yml`, evento `pull_request_target`) rodam em todo PR de proposta e de aplicação.
  - `sdd` (`.github/workflows/sdd.yml`) roda só se o PR tocar os `paths` dele, por exemplo `.agents/skills/**`, `ferramentas/**`, `redesign/painel_operacional/**`. Não é obrigatório no GitHub.
  - `CodeQL`: a origem do workflow não foi encontrada em `.github/workflows` (não verificado).
- Só vale o run do commit atual. Confira com `gh run list --branch <b> --json headSha`. Se o run não aparecer para o seu HEAD (ou o `sdd` não aparecer quando o PR toca os paths), registre e avise o Humano. Não junte.
- Check vermelho ou ausente no `headSha` atual, ou conflito `DIRTY`: não junta, avisa o Humano.
- `gh pr view <n> --json mergeStateStatus,statusCheckRollup` mostra o estado por check. `gh pr checks` às vezes lista só parte.

## Fluxo e pronto (ágil, 11/11)

Decisão do Humano em 11/11/2026 ("ok a todas"). Vale para todo lote novo. A regra R2 fica em medição de 14 dias, até 25/11/2026.

- **R1 Limite de trabalho aberto.** No máximo 2 propostas abertas (sem aplicação) por componente. Antes de abrir a 3ª, aplique, supere ou feche uma. Base: Kanban Guide, edição 2025 (v2025.5, https://kanbanguides.org/english/), controle de WIP; Lei de Little (L = λ·W, teoria de filas) explica por que fila maior alonga o tempo de ciclo. O guia não cita a lei pelo nome.
- **R3 Definição de pronto do lote.** O relatório do agente preenche este checklist. Item sem marca: o lote não está pronto.
  - [ ] CI local com `CI LOCAL: TUDO OK` (saída colada)
  - [ ] run verde no GitHub no `headSha` do PR (`gh run list --branch <b> --json headSha`)
  - [ ] captura de tela quando há interface
  - [ ] sem emoji (E-2, decisão de 16/10)
  - [ ] `.md` da proposta com testes medidos, o que não foi medido e a reversão
  - [ ] nenhuma falha "pré-existente" sem dono e data
  - [ ] texto da entrada de MEMÓRIAS sem citação `caminho:número` (P-19 só avisa; não falha)
  Base: Scrum Guide 2020, Definition of Done.
- **R5 Retrospectiva de 3 linhas ao fechar cada lote.** Anote no cache do Conselho (`agata-fluxo`, seção 5): gargalo com número; regra que mudou; o que saiu do WIP. Base: Manifesto Ágil, princípio 12.
- **R2 Apetite (medição até 25/11/2026).** Cada proposta declara o apetite: máximo de arquivos e de horas de agente. Quando passar do limite, o `.md` registra isso. Nada é cortado automaticamente nesse período.

## Pacote de assinatura (11/11)

Decisão do Humano em 11/11/2026 ("me apresente apenas uma assinatura"). Memória "uma assinatura por implementação" (03/11).
- Propostas prontas no mesmo período que tocam arquivos em comum se juntam num pacote único, com uma só assinatura.
- O `.md` do pacote lista cada parte, a ordem de aplicação e cada conflito e como foi resolvido.
- O pacote é testado inteiro antes de propor: unittest do painel, `scripts/ci_sdd_local.sh`, gate de spec e lint de skills.
- As propostas parciais vão para `propostas/superadas/` quando o pacote entra, com a linha "incluída em <pacote>" no `propostas/superadas/LEIA-ME.md`.

## Registro em MEMÓRIAS

- Formato: `(<n>) DIÁRIO — dd/mm/aaaa · **<conclusão em 1-2 frases>**`, corpo curto, e fecho `Modelo: <nome> (<cliente>, na Máquina) · vetor: <o que foi medido> · Autorização: Humano — "<citação>"`. Um `aplicar.py --registro` lê o arquivo: a entrada começa exatamente com `(<n>) DIÁRIO — data · **título.**`, ou o P-5 falha.
- Pelo MCP `canon` → `memoria_acrescentar` (append-only, o escriba numera); ou, no shell, script python que insere após o marcador. **Nunca** `write` ou `edit` no arquivo (já apagou a história, (516)).
- `ONDE_ESTAMOS.md`: bloco novo no topo da data, português simples, sem jargão, no mesmo commit.

## Armadilhas já pagas

- **CI local diferente do CI real:** o job `sdd` roda `pytest` (9.2.0, fixado em `sdd.yml`) nos diretórios listados no workflow, depois anchor e ciclos. Unittest passa e pytest falha, ou o contrário. Use o script.
- **pytest:** se não estiver no PATH, use o binário do cache do uv: `PYTEST=$(ls /home/orusoua/.cache/uv/archive-v0/*/bin/pytest | head -1)`. Antes de usar, rode `"$PYTEST" --version`. Tem de mostrar `pytest 9.2.0` (em 06/11 foi esse o resultado). Se a saída estiver vazia, pare. Se a versão for outra, pare e avise. Depois: `PYTEST="$PYTEST" bash scripts/ci_sdd_local.sh`. Não instale sem ordem.
- **Índice derivado:** `ferramentas/indice.json` e `ferramentas/INDICE.md` são gerados por `python3 -I ferramentas/ferramentas.py reindexar`, que lê só skills versionadas. Depois de criar ou mudar skill: `git add` da skill, rode `reindexar` e adicione os dois arquivos gerados.
- **Arquivos gerados pelo ciclo SDD:** o `cycle` escreve na pasta do spec passado (`criterion-drift.md`, `evidence.json`). Antes de qualquer restauração, confira `git diff -- <arquivo>`: deve mostrar só a saída do ciclo. Se houver alteração sua, copie-a para fora da árvore e peça ordem. Restaurar arquivo gerado exige ordem do Humano, arquivo por arquivo. Nunca `rm -rf`.
- **Testes que parecem isolados:** confira `AGATA_NV_DIR` antes de confiar num teste que grava. Um teste de revisão que imprime "Humano" não é prova de gravação real.
- **Conflito de âncora:** os blocos `ANCORA-SHA` (em `REGRAS.md`, `PROJETO.md`, `MEMÓRIAS.md` e `PROMPT_CARREGAMENTO.md`) são de máquina, gerados pelo `.githooks/pre-commit` com `scripts/atualizar_ancora_prompt.py`. `.hidrata.md` e `INDICE_MEMORIAS*.md` são regenerados pelo mesmo hook (`.githooks/gerar-hidratacao.sh`). Não use `git checkout --theirs`: ele troca o arquivo inteiro e apaga as entradas do lote. No conflito:
  1. separe o bloco `ANCORA-SHA` (de `<!-- ANCORA-SHA:INICIO` até `<!-- ANCORA-SHA:FIM -->`) e deixe-o com a versão do `origin/main`; não edite à mão;
  2. regere: deixe o pre-commit fazer no commit, ou rode `python3 scripts/atualizar_ancora_prompt.py <arquivo> <SHA do HEAD anterior> <data-hora>` (uso no cabeçalho do script);
  3. reinsira as entradas do lote em `MEMÓRIAS.md` logo abaixo de `ENTRADAS-NOVAS:AQUI`, sem tocar entradas antigas;
  4. antes de concluir, confira com `git diff origin/main -- MEMÓRIAS.md` que nenhuma entrada antiga foi removida (a única linha removida aceitável é do bloco `ANCORA-SHA`) e com `git diff` de cada arquivo conflitado que só há o que o lote muda.
- **Spec é P-8:** mudar `redesign/*/spec/spec.md` exige proposta própria, mesmo que seja só uma linha. Por isso o lote precisa já conter a spec certa.
- **P-8 confere uma proposta por vez contra HEAD.** Duas propostas no mesmo arquivo = dois commits, ou aplicação em sequência (539).
- **Worktrees de outros:** não toque nas worktrees do Codex (`~/.codex/worktrees/`). Remova só as worktrees que você criou neste lote.
- **Subagente que diz "passou":** confira o código e rode o teste você mesmo. Relatório de subagente é alegação.
- **Subagente não grava arquivo:** nesta sessão, subagente não gravou arquivo (causa não verificada). Peça que o relatório venha como texto na resposta e grave você mesmo, depois de conferir.
- **O hook pode rodar a suíte de controles** (P-16, 1 a 2 min): não mate o commit por timeout.
- **Um controle que barra o commit** (P-4, P-8, P-10) está certo até prova em contrário: leia o SUSPEITO.

## Lições medidas em 07/11/2026

Cada lição tem a regra em uma frase e a fonte em uma linha. Quando a fonte é relato da rodada que não foi conferido, a linha diz "relato, não conferido". Medido e lido aparecem rotulados. As letras são as da proposta `skill-processo-lessons-07-11`; as lições que repetiam esta skill não entram.

- **a. Medir antes de afirmar.** Ler código não é medição: risco só lido se escreve "lido", e só vira "confirmado" depois de teste ou comando.
  Fonte: regra da rodada de 07/11, sem caso específico informado.
- **b. Risco medido se resolve na mesma rodada, por proposta.** Defeito de código já medido se corrige numa proposta, sem pedir permissão antes; a assinatura continua sendo do Humano.
  Fonte: regra da rodada de 07/11, sem caso específico informado.
- **c. Teste com cópia dos dados.** Migração, importação e teste de escrita rodam sobre cópia, com manifesto de hashes antes de importar; nunca sobre o armazenamento real.
  Fonte: a migração das conversas do LibreChat usou uma cópia e um manifesto de hashes antes de importar (relato, não conferido).
- **d. Em teste de navegador e de HTTP, só GET.** Antes de rodar, confira a origem: um POST dispara ação real.
  Fonte: um POST para /api/abrir, disparado por teste com origem errada, colocou conselheiros na fila; um clique na seção Conselho também disparou POST (relato, não conferido).
- **f. Trabalho durável não fica em /tmp.** Use `/home/orusoua/agata/.claude/worktrees/` ou `~/agata-documentacao`; /tmp é memória e some num reinício sujo.
  Fonte: 22 worktrees perdidas em 07/11, com causa apontada como journal, fsck e tmpfs (relato). Medido: `findmnt -T /tmp` mostra tmpfs, e `git worktree list` mostra 20 entradas prunable (não 22). Journal e fsck não medidos.
- **i. Decisão do Humano fora do repo vira proposta ou registro.** Uma decisão que existe só em mensagem não é tratada como decidida: antes, vira proposta P-8 ou entrada de registro.
  Fonte: a desativação do Ollama no boot e a substituição do LibreChat existiam só em mensagem (relato, não conferido). Medido: grep em MEMÓRIAS.md por Ollama com boot ou desativ, e por LibreChat com substitu ou troca, não achou nada; isso prova só "não encontrado nesta busca".
- **j. Antes de remover serviço ou dado, verifique a cópia.** Faça inventário sem conteúdo, cópia de segurança com hash, importação idempotente e contagem igual nos dois lados; só então remova, com ordem explícita do Humano.
  Fonte: a migração das conversas do LibreChat seguiu essa ordem (relato, não conferido).
- **k. Limiar de corte pela quebra medida.** Escolha o limiar pela quebra observada na distribuição, não por chute, e anote a distribuição junto.
  Fonte: limiar de 20 mensagens, com quebra entre 18 e 22 (relato, não conferido).
- **l. Número com rótulo.** Todo número sai marcado como medido, inferido ou não medido; número sem rótulo é defeito.
  Fonte: regra da rodada de 07/11, sem caso específico informado.
- **m. Perguntas numeradas.** Perguntas ao Humano vão numeradas, na ordem em que aparecem na mensagem.
  Fonte: preferência explícita do Humano (relato, não conferido).
- **n. Sem sudo pelo modelo.** O modelo não usa sudo; comando de sistema que exige sudo vai ao Humano como comando pronto, com caminho absoluto, para colar no terminal dele, sem o prefixo `!`.
  Fonte: o `!` do chat não mostrou o prompt de senha (registro de 23/10); `sudo -n` falha e a senha não é do modelo (registro de 17/10).
- **o. Estado real antes de afirmar.** Antes de dizer que um serviço, container, branch ou PR está em certo estado, consulte com systemctl, docker inspect, git ls-remote ou gh pr view e cite a saída.
  Fonte: divergências entre o relatório de um agente e o estado medido (relato, não conferido).
