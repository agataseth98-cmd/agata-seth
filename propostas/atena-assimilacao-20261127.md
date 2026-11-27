# Proposta Atena — assimilação do Reversa

Classe: Comportamento

## Objetivo

Assimilar ao Agata o framework Reversa como Atena, com harness para Codex, descoberta, engenharia reversa, SDD, migração, documentação, revisão, depuração e qualidade. A integração preserva as regras do Agata e bloqueia edição do legado por padrão.

## Escopo do diff

- `AGENTS.md`: entrada do Reversa e política de escrita segura.
- `.agents/skills/`: skills Reversa e Impeccable instaladas pelo pacote `reversa@1.3.6`; índice atualizado.
- `.reversa/`: configuração reutilizável, templates, hooks, manifestos e versão.

Não entram: `_reversa_sdd/` (resultado específico desta análise), `state.json`, `plan.md`, `config.toml` do projeto de ensaio, `config.user.toml` ou `redesign/nova_versao/spec/evidence.json` gerado pelo CI.

## Segurança e limites

- `allowLegacyEdits=false` permanece ativo.
- Atena escreve apenas em pastas próprias até decisão explícita e proposta posterior.
- Nenhum segredo foi lido.
- Nenhuma aplicação foi feita no checkout principal.

## Verificação medida

- `pytest 9.2.0`.
- Primeiro CI: 2 falhas esperadas pela assimilação: índice de skills incompleto e placeholder XML no `reversa-debugger`.
- Correções na worktree: teste do índice `1 passed`; `qualidade_llm.py` retornou `bad_skills []`.
- Segundo CI: `CI LOCAL: TUDO OK`, 95/95 passos; 1.551 testes, 1 skip e 568 subtestes aprovados.
- `git diff --check`: sem erro.
- Diff: 342 arquivos; SHA-256 `708608126a1bd77b5e28b144fb5cac2fd85095353e54de74def250da9f43d596`.
- `p8_verificar`: ainda não aplicável; o par assinado não existe.

## Verificação adicional

O diff com `--binary` aplica em cópia limpa baseada no mesmo `HEAD` (`git apply --check`: OK). SHA-256 atual: `bace6685e57a532b3fa046b68b6c2776cc6658430d16587104a3e7b3613f9368`.

## Reversão

Em uma aplicação assinada, reverter com o diff reverso do lote e repetir CI/P-8. Não remover arquivos manualmente; preservar cópias e registros conforme a skill `agata-aplicar-proposta`.

## Comando de assinatura

O Humano deverá assinar somente após a proposta chegar ao checkout principal e o CI do PR estar verde:

```bash
bash scripts/aprovar.sh atena-assimilacao-20261127
```
