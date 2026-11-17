# Spec-mãe descreve o cofre de chaves que o código usa (`spec-mae-cofre-17-11`)

Classe: Comportamento (spec).

Proposta P-8 de `spec-mae-cofre-17-11`. Diff: `propostas/spec-mae-cofre-17-11.diff` (4 arquivos, 202 linhas). Base: `origin/main` (d5301fa2). O diff não traz registro nem `ONDE_ESTAMOS.md`; esses entram no PR de proposta, fora do diff assinado.

Decisão do Humano (17/11/2026, 08:24): "inventarie, audite e atualize o sistema e depois aplique tudo que vc sugeriu para o painel a luz do que for encontrado".

## O que muda

1. `redesign/nova_versao/spec/spec.md`: a seção de chaves de provedor passa a descrever o cofre `~/.config/agata/conexoes/<id>.chave`, que é o que `redesign/conexoes/segredos.py` grava: pasta 0700, arquivo 0600, gravação atômica. O `~/.config/agata/.env` não é tocado.
2. `redesign/nova_versao/spec/spec.md`: a exceção "só essa rotina lê `.env`" sai do texto. Entra o critério marcado "a chave de provedor vai para o cofre próprio com permissão 0600 e nunca volta; o .env não é tocado".
3. `redesign/nova_versao/spec/acceptance.json`: critério novo com o comando `pytest -q redesign/conexoes/tests/test_conexoes.py::CofreTests::test_chave_vai_para_o_cofre_0600_e_nunca_volta`.
4. `redesign/nova_versao/spec/criterion-drift.md` e `redesign/nova_versao/spec/evidence.json`: regerados pelo ciclo SDD da nova versão, sem edição à mão.

## Por que não entrou no pacote anterior

O verificador de sincronia recusa mudança só de texto numa spec. Com um critério novo, o drift muda de verdade e o verificador aceita, sem mexer nele.

## Medido (17/11/2026)

- CI local (`scripts/ci_sdd_local.sh`, com `PYTEST=/home/orusoua/.cache/uv/archive-v0/0obnOoJtclHllQl_/bin/pytest`; `pytest 9.2.0` confirmado por `--version` antes da rodada, porque a saída do script não imprime a versão): `CI LOCAL: TUDO OK`, 88 linhas `OK`, 0 `FALHA`, rc=0. Log: `/home/orusoua/agata-arquivo/atualiza-17-11/spec-mae/ci-local.log`.
- Teste do cofre, na cópia limpa com o diff aplicado (pytest 9.2.0): `1 passed`, rc=0.
- Cópia limpa `check-spec-mae-cofre-17-11`, a partir de `origin/main`: `git apply --check` = APLICA; `git apply` = APLICADO.
- Na cópia com o diff aplicado: `scripts/gate_spec_sync.py`: rc=0, 16 componentes, 0 falha, 1 aviso (`alexandria`: 5 critérios do acceptance.json sem linha no spec.md; componente sem mudança neste diff). `redesign/sdd_flow/anchor.py . redesign/nova_versao`: `ANCHOR: OK`, rc=0.
- `grep '^diff --git'` no diff: 4 caminhos, todos em `redesign/nova_versao/spec/`.

## Não medido

- Se o texto novo descreve o código além do que o teste prova. O teste cobre permissão 0600 e o não retorno da chave; a leitura de `segredos.py` não foi repetida neste pacote.
- Se o aviso de `alexandria` existe também em `origin/main` puro (não medido separadamente).
- Run verde no GitHub no `headSha` do PR (fica no registro do PR).

## Reversão

`git apply -R propostas/aplicadas/spec-mae-cofre-17-11.diff` numa worktree a partir do `main`, por proposta. O diff inclui `criterion-drift.md` e `evidence.json`, que voltam junto.

## Comando de assinatura

Depois do merge deste PR, no terminal, sem `!`:

bash scripts/aprovar.sh spec-mae-cofre-17-11

## Modelos

Claude Opus 5.5 coordenou; agente Claude Haiku 5.5 rodou o CI local, o diff, o registro e o PR.

## Definição de pronto (R3)

- [x] CI local com `CI LOCAL: TUDO OK` (log acima)
- [ ] run verde no GitHub no `headSha` do PR (fica no registro do PR)
- [x] captura de tela: não se aplica (sem interface)
- [x] sem emoji no `.md` (conferido com grep depois de escrever)
- [x] testes medidos, o que não foi medido e a reversão (acima)
- [x] nenhuma falha pré-existente sem dono e data (nenhuma falha no CI local; o aviso de `alexandria` fica registrado)
- [x] texto da entrada de MEMÓRIAS sem citação `caminho:número` (conferido com grep depois de escrever)
