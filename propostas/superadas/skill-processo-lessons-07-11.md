# Proposta skill-processo-lessons-07-11 — lições medidas na skill de processo de lote

**Nome para assinatura:** `skill-processo-lessons-07-11`
**Arquivo afetado:** `.agents/skills/agata-processo-lote/SKILL.md` (1 arquivo, +35 linhas, nada removido).
**Motivo:** a rodada de 07/11/2026 deixou lições que faltavam na skill de processo. Esta proposta só acrescenta a seção "Lições medidas em 07/11/2026" ao fim da skill. As regras existentes não mudam.
**Quarentena:** `.agents/*` está na lista de comportamento do P-8 (`scripts/perimetro/p08_quarentena.sh`, grep em 07/11), então a aplicação precisa do par assinado.

**Diff:** `propostas/skill-processo-lessons-07-11.diff`
**sha256 do diff:** `06aae4d614186fc4cf46b9519ea9fc5de786a8046e3360d2a81128e108add660`

## Conferência (medida em 07/11/2026)
- `git apply --check` do diff numa worktree destacada em `origin/main` (83334fde): passou.
- CI local, com `PYTEST=/home/orusoua/.cache/uv/archive-v0/0obnOoJtclHllQl_/bin/pytest scripts/ci_sdd_local.sh` (pytest 9.2.0, rodada das 13h15 às 13h17): `CI LOCAL: TUDO OK`, 33 passos OK, nenhum FALHA.
- Lint da skill (`python3 -I redesign/painel_operacional/qualidade_llm.py`): `agata-processo-lote` com `problemas: []` e `avisos: []`; zero problemas em todas as skills.
- `python3 -I ferramentas/ferramentas.py reindexar`: nenhum índice mudou (o resumo da skill vem da descrição, que não mudou).
- Caminhos citados na seção nova existem: `.githooks/pre-commit`, `.hidrata.md`, `scripts/ci_sdd_local.sh`, `~/agata-documentacao`, `/home/orusoua/agata/.claude/worktrees/`.
- Efeito do CI local na árvore da worktree (não entra nesta proposta): `redesign/nova_versao/spec/criterion-drift.md` e `evidence.json` foram regravados (estão modificados), e `redesign/sdd_flow/spec/criterion-drift.md` e `evidence.json` apareceram como não rastreados. São saídas do ciclo SDD; não foram commitadas nem restauradas.

## Lições (regra em uma frase; fonte em uma linha)
- **a.** Ler código não é medição; risco só lido se rotula "lido". Fonte: regra da rodada, sem caso específico informado.
- **b.** Defeito de código já medido se corrige numa proposta na mesma rodada; a assinatura é do Humano. Fonte: regra da rodada, sem caso específico informado.
- **c.** Migração, importação e teste de escrita rodam sobre cópia, com manifesto de hashes. Fonte: migração das conversas do LibreChat (relato, não conferido).
- **d.** Teste de navegador e de HTTP só com GET. Fonte: POST para /api/abrir por teste com origem errada colocou conselheiros na fila; clique na seção Conselho também disparou POST (relato, não conferido).
- **e.** Nunca rm (nem -f, -r), nem em temporário ou pasta da mesma tarefa; usar mv; remover só com ordem do Humano, por nome. Fonte: três agentes rodaram rm -rf ou rm -f em scratch; um comando foi negado pelo classificador (relato, não conferido).
- **f.** Trabalho durável não fica em /tmp (tmpfs); usar `/home/orusoua/agata/.claude/worktrees/` ou `~/agata-documentacao`. Fonte: worktrees perdidas em 07/11 (relato: 22). Medido: `findmnt -T /tmp` mostra tmpfs; `git worktree list` mostra 20 entradas prunable, não 22. Journal e fsck não medidos.
- **g.** Canon não se commita antes da assinatura: gerar diff, conferir `git apply --check` numa cópia de origin/main, reverter a edição na worktree. Fonte: correção do PROJETO.md revertida antes do commit (relato, não conferido). Lido em `.githooks/pre-commit`: o hook faz `git add` da âncora em REGRAS.md, PROJETO.md e MEMÓRIAS.md e recusa o commit se o staged ganhou conteúdo fora da âncora.
- **h.** O pre-commit regrava a âncora de PROMPT_CARREGAMENTO.md e, quando o canon entra no commit, a de REGRAS.md, PROJETO.md e MEMÓRIAS.md, além de `.hidrata.md` e INDICE_MEMORIAS.md; o corpo do PR declara o que o hook alterou. Fonte: PRs #934, #941, #942, #943 (relato). Trecho lido em `.githooks/pre-commit`. O efeito real está na seção "Efeito do hook" do PR desta proposta.
- **i.** Decisão do Humano que só existe em mensagem não é tratada como decidida; vira proposta P-8 ou registro. Fonte: desativação do Ollama no boot e substituição do LibreChat (relato). Medido: grep em MEMÓRIAS.md por Ollama com boot/desativ, e por LibreChat com substitu/troca, sem resultado (prova só "não encontrado nesta busca").
- **j.** Antes de remover serviço ou dado: inventário sem conteúdo, cópia com hash, importação idempotente, contagem igual nos dois lados; remover só com ordem explícita. Fonte: migração do LibreChat (relato, não conferido).
- **k.** Limiar de corte pela quebra medida na distribuição, não por chute. Fonte: limiar de 20 mensagens com quebra entre 18 e 22 (relato, não conferido).
- **l.** Número sai com rótulo (medido, inferido ou não medido). Fonte: regra da rodada, sem caso específico informado.
- **m.** Perguntas ao Humano numeradas, na ordem da mensagem. Fonte: preferência explícita do Humano (relato).
- **n.** Sem sudo pelo modelo; comando de sistema vai ao Humano como comando pronto, com caminho absoluto, sem o prefixo `!`. Fonte: o `!` do chat não mostrou o prompt de senha (registro de 23/10); `sudo -n` falha e a senha não é do modelo (registro de 17/10). **Desvio da tarefa:** a tarefa pedia "com o prefixo !"; o registro de 23/10 mostra que o `!` não serve para o prompt de senha. Escrevi sem o `!`.
- **o.** Antes de afirmar estado (serviço, container, branch, PR), consultar com systemctl, docker inspect, git ls-remote ou gh pr view e citar a saída. Fonte: divergências entre relatório de agente e estado medido (relato, não conferido).

## Achados em regras existentes (não alterados)
1. **Regra 2 da skill:** "`.agents/` ... não verificado no P-8". Está verificado: `scripts/perimetro/p08_quarentena.sh` tem `.agents/*|.claude/*|redesign/goose/*` (grep em 07/11). A frase está desatualizada.
2. **Regra 2 da skill:** "A lista é a do AGENTS.md" e "O hook P-8 recusa commit direto". A lista do AGENTS.md cobre `redesign/*` inteiro; `p08_quarentena.sh` cobre só caminhos específicos de redesign (router, mcp, librechat, goose, obsidian, igpu, grafo, systemd, fase7-hd). Não medi se `redesign/*/spec/spec.md` tem outro controle: grep por `spec` em `p08_quarentena.sh` e `scripts/perimetro.sh` não achou nada.
3. **Passo 3 da skill (CI local):** não avisa que `scripts/ci_sdd_local.sh` regrava arquivos rastreados (`criterion-drift.md`, `evidence.json` de `redesign/nova_versao/spec`) e cria os do `redesign/sdd_flow/spec` (medido em 07/11). A armadilha "Mudança na worktree" cobre parte disso, mas o passo 3 deveria dizer.
4. **Conflito com a lição e nos scripts do repo (não alterado):** `scripts/ci_sdd_local.sh` (`trap 'rm -rf "$TMP"'`) e `.githooks/pre-commit` (`rm -f /tmp/agata-perimetro-2a-passada.log`, que também grava em /tmp) usam rm e /tmp. Ambos estão em quarentena (`scripts/*`, `.githooks/*`); a mudança fica para proposta própria.
5. **CI é por commit (confirmado, não é achado):** `gh api repos/agataseth98-cmd/agata-seth/branches/main/protection` em 07/11 devolve `suite-adversarial`, `fiscal-p8`, `CodeQL`, igual ao texto da skill.

## Pendências desta proposta
- Não inclui a entrada em `MEMÓRIAS.md` nem a atualização de `ONDE_ESTAMOS.md`, que `propostas/README.md` (item 0) e o passo 5 da skill pedem. Ficaram de fora porque a tarefa mandou commitar só os dois arquivos de propostas. Falta incluir antes da assinatura.
- Número de worktrees da lição f: a tarefa dizia 22; medido hoje, 20.

## Assinatura e aplicação
- Depois do merge do PR de proposta, o Humano assina: `bash scripts/aprovar.sh skill-processo-lessons-07-11`. Quem propõe não roda isso.
- A aplicação segue o passo 7 em diante da skill, numa worktree `aplica-skill-processo-lessons-07-11`.
