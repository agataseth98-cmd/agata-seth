# Proposta agencia-pesquisa-20261106: três pesquisadores de leitura

Autor: agata-ci (Claude Haiku 5.5). Base: origin/main eb1c40a4.

**O que entra:** três subagentes em `.claude/agents/`, só leitura, cada um para uma pergunta fechada:
- `agata-pesq-rea`: frente REA e Herdr. Lê a allowlist da proposta rea-herdr-integracao-20261106 e diz o que falta medir antes de usar o REA em paralelo com o LibreChat.
- `agata-pesq-painel`: painel operacional. Diz quais páginas e rotas não têm teste de navegador e quais violam a CSP de estilo, por leitura.
- `agata-pesq-processo`: skill agata-processo-lote. Diz quais regras têm verificação mecânica e quais não.

Os três não decidem, não propõem código e não gravam nem commitam. Ferramentas: Read, Grep, Glob e Bash (leitura).

**Divergências do revisor (medidas no origin/main):**
1. `scripts/rea_leitura.sh` não está no main. Ele entra com a proposta rea-herdr-integracao-20261106, cuja aplicação é o PR 927 (aberto). O agente `agata-pesq-rea` lê a allowlist direto no diff da proposta. Junto com o script, `.agents/skills/agata-engenharia-reversa/SKILL.md` também só existe no PR 927.
2. A skill `agata-equipe` não existe no main. A equivalente é `.agents/skills/agata-fluxo-equipe/SKILL.md`. O agente `agata-pesq-processo` usa essa e registra a troca no relatório. Nenhuma skill foi criada nem renomeada.

**Conferência:** `propostas/agencia-pesquisa-20261106.diff` tem 116 linhas e cria só os três arquivos acima. `git apply -R --check` contra os arquivos da worktree passa.

**Aplicação:** esta proposta só abre o registro. Aplicar exige a assinatura do Humano (`APROVADO-agencia-pesquisa-20261106`).
