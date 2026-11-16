# Higiene 16/11: CI local com a suíte adversarial e texto vivo sem o chat antigo nem o Goose (`higiene-16-11`)

Classe: Canon (toca AGENTS.md) e Comportamento (`scripts/ci_sdd_local.sh` e `scripts/testar_sem_goose_ativo.py`; configuração e READMEs de pastas históricas).

Proposta P-8 de `higiene-16-11`. Diff: `propostas/higiene-16-11.diff` (6 arquivos). Base: `origin/main` (3711870a). O diff não traz registro, derivados nem `ONDE_ESTAMOS.md`; esses entram no PR de proposta, fora do diff assinado.

Decisão do Humano (16/11/2026, 14:46), em resposta à lista de pendências numerada: "1-faça, 2-faça, 3-faça, 4-faça".

## O que muda

1. `scripts/ci_sdd_local.sh` passa a rodar os 29 passos do job `suite-adversarial` (o perímetro e 28 scripts), com o Python do sistema. Os dois passos de YAML deixam de depender de variável: o script escolhe `/usr/bin/python3` quando ele tem PyYAML. Total: de 59 para 88 passos.
2. `AGENTS.md`: deixa de dizer que a Seth fala pelo chat antigo; a frase passa a dizer que ela fala pelo painel.
3. `redesign/librechat/README.md` e `redesign/goose/README.md` ganham aviso de pasta histórica, com a data de saída de 07/11/2026.
4. `config/portas-de-entrada.txt`: só a coluna de descrição de três linhas muda. A coluna lida por máquina fica igual, e a cobertura do P-23 não muda.
5. `scripts/testar_sem_goose_ativo.py`: a lista de exceções acompanha as contagens novas. `config/portas-de-entrada.txt` cai de 3 para 1; entra `scripts/ci_sdd_local.sh`, com 1.

## Por que

Em 16/11 a proposta `painel-funcional-16-11` passou no CI local e foi reprovada pela suíte adversarial no PR de aplicação, o que custou uma segunda assinatura. Esta proposta fecha essa lacuna no CI local e tira do texto vivo as referências a dois sistemas que saíram em 07/11/2026: o chat antigo e o Goose.

## Medido (16/11/2026)

- CI local com o Python do sistema: a última linha do log é `CI LOCAL: TUDO OK`. No log `/home/orusoua/agata-arquivo/auditoria-conceito-16-11/ci-local-higiene-final.log`: 88 linhas `OK`, 0 `FALHA`, 29 passos da suíte adversarial.
- Cópia limpa de `origin/main` (worktree `check-higiene-16-11`): `git apply --check` retorna APLICA; `git apply` do `.diff` roda sem erro.
- Testes de ausência, antes (cópia limpa em `origin/main`) e depois (com o `.diff` aplicado):
  - `scripts/testar_sem_goose_ativo.py`: 6 testes, OK nos dois casos.
  - `scripts/testar_tira_librechat.py`: 5 testes, OK nos dois casos.
- `bash -n scripts/ci_sdd_local.sh`: rc=0.

## Não medido

- Os 29 passos da suíte adversarial sob isolamento de rede. Não reproduzido aqui.
- Se algum passo tenta ler o token interno. O caminho foi desviado para um arquivo inexistente dentro de `$TMP` (variável `AGATA_TOKEN_INTERNO_PATH`), mas não medi se algum passo tenta abri-lo.
- Run verde no GitHub no `headSha` do PR de proposta (fica no registro do PR).
- Horas de agente: estimativa de cerca de 1 hora, não medida.

## Fora do pacote, com motivo

- Divergência de texto entre a spec-mãe e a spec de conexões. O gate de sincronia recusa mudança só de prosa na spec, e spec é P-8. Patch guardado em `/home/orusoua/agata-arquivo/auditoria-conceito-16-11/b5-nova-versao-spec.patch`; precisa de proposta própria.
- A frase equivalente em `redesign/goose/AGENTS.md` (arquivo histórico do Goose). Fica até a decisão de remoção.
- O perfil da Capivara de 25/10. Regenera com `scripts/capivara_capacidades.py`, que consulta o OmniRoute; não rodado.
- Arquivos gerados pelo ciclo, sem restauração (sem ordem do Humano): `redesign/nova_versao/spec/evidence.json` (modificado) e `redesign/sdd_flow/spec/criterion-drift.md` e `evidence.json` (não rastreados).

## Apetite

6 arquivos. Cerca de 1 hora de agente (estimativa, não medida).

## Reversão

`git apply -R propostas/aplicadas/higiene-16-11.diff` numa worktree, por proposta. Não exige reinício de serviço: o pacote muda scripts de teste, configuração e textos.

## Comando de assinatura

Depois do merge deste PR, no terminal, sem `!`:

bash scripts/aprovar.sh higiene-16-11

## Modelos

Claude Fable 5.2 coordenou; agentes Claude Haiku 5.5 implementaram e montaram a proposta.

## Definição de pronto (R3)

- [x] CI local com `CI LOCAL: TUDO OK` (log acima)
- [ ] run verde no GitHub no `headSha` do PR (fica no registro do PR)
- [x] sem interface: captura de tela não se aplica
- [x] sem emoji
- [x] testes medidos, o que não foi medido e a reversão (acima)
- [ ] nenhuma falha pré-existente sem dono e data: as pendências fora do pacote têm motivo; dono e data a definir pelo Humano
- [x] texto de MEMÓRIAS sem citação `caminho:número` (conferido com grep depois de escrever)
