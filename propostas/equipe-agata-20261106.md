# Proposta equipe-agata-20261106

## Resumo
Muda duas skills de `.agents/`. Nenhum código de runtime.
- `agata-equipe` (novo): papéis e delegação. Tabela de papéis (o que cada um pode e não pode, quem revisa), lista única de proibições de git para todo papel com Bash, pacote de passagem sem a conversa, barreiras (permissão da sessão e classificador, não o frontmatter), crescimento da equipe por demanda com medição em log, e o que só o Humano decide.
- `agata-processo-lote` (ajustes): papéis com o nome do agente; conferência de passo mecânico é do `agata-ci`; mapa "Quem faz cada passo mecânico" com dono em cada passo, incluindo reindex; registro do passo 10 pelo `agata-dev`; `git rm -f` como exceção marcada; passo 8 só com aplicação ordenada pelo Humano; aviso na armadilha "Time de agentes", sem editar a linha antiga; entradas novas no diário.

## Limites
- Não aplicada. Sem `APROVADO-*`. Assinatura do Humano pendente.
- Ainda não rodaram: CI local (`scripts/ci_sdd_local.sh`), o `.diff` em `propostas/` (sai no passo 4 pelo `agata-ci`) e os checks do PR.
- Lint de skill limpo para as duas (`problemas` vazio). O único aviso do lint é de outra skill (`design-taste-frontend`, 528 linhas).
- Revisão: `agata-revisor`, rodada 4, aprovado para PR (relatado pelo coordenador).
- Residuais BAIXA do revisor ficaram fora: rotação de coordenador (linhas 14, 82, 97 e 118 da skill de processo, citadas pelo revisor).
- Contagem de `APROVADO-*` no histórico: a linha 562 foi mantida; a medição de hoje deu 563, registrada no diário.
- Só `.agents/` e este registro. Nada em `redesign/`, `scripts/`, `config/` ou `.githooks/`. `MEMÓRIAS.md` e `ONDE_ESTAMOS.md` não foram tocados.

## Ponto em aberto para o Humano
O padrão 692 diz que quem propõe junta. Esta proposta põe o `agata-ci` para executar a junção de proposta, com ordem do coordenador e `headSha` verde; o coordenador só decide. O Humano confirma essa regra ou pede o padrão 692 como estava.

## Arquivos alterados
- `.agents/skills/agata-equipe/SKILL.md` (novo)
- `.agents/skills/agata-processo-lote/SKILL.md`

## Comando de assinatura (só o Humano)
`bash scripts/aprovar.sh equipe-agata-20261106`
