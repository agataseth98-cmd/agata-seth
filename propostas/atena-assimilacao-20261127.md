# Proposta Atena — assimilação do Reversa

Classe: Comportamento

## Objetivo

Assimilar ao Agata o framework Reversa como Atena, preparado para o harness do Agata e para todos os harnesses já contemplados pelo sistema: Agata, Claude Code, Codex, Cursor, Gemini CLI, OpenCode e Seth. A integração cobre descoberta, engenharia reversa, SDD, migração, documentação, revisão, depuração e qualidade. A própria Atena também deve ser atualizada pelo Reversa: `npx reversa update` para a ferramenta e `reversa-sync` para convergir as specs após evoluções. A integração preserva as regras do Agata e bloqueia edição do legado por padrão.

## Escopo do diff

- `AGENTS.md`: entrada do Reversa e política de escrita segura.
- `.agents/skills/`: skills Reversa e Impeccable instaladas pelo pacote `reversa@1.3.6`; índice atualizado.
- `.reversa/`: configuração reutilizável, templates, hooks, manifestos e versão.
- `.reversa/_config/manifest.yaml`: matriz explícita de harnesses suportados, sem acoplar o fluxo a uma ferramenta específica.
- `AGENTS.md`: procedimento de atualização da Atena pelo Reversa, sempre em worktree e sob P-8.

Não entram: `_reversa_sdd/` (resultado específico desta análise), `state.json`, `plan.md`, `config.toml` do projeto de ensaio, `config.user.toml` ou `redesign/nova_versao/spec/evidence.json` gerado pelo CI.

## Segurança e limites

- `allowLegacyEdits=false` permanece ativo.
- O núcleo comum usa instruções e arquivos portáveis; capacidades opcionais de cada harness são detectadas no ambiente e não são presumidas.
- Claude Code mantém o hook de bloqueio disponível; Codex, Gemini CLI, Cursor, OpenCode, Agata e Seth seguem a mesma política por instrução e pelos gates do Agata.
- A lista de harnesses é declarativa e extensível: adicionar um harness futuro exige apenas uma atualização controlada da matriz e teste correspondente, sem reescrever as skills.
- A atualização da própria Atena não é automática: `npx reversa update` prepara o novo pacote e `reversa-sync` preserva o histórico das specs; ambos passam por revisão, CI, assinatura e aplicação do Agata.
- Atena escreve apenas em pastas próprias até decisão explícita e proposta posterior.
- Nenhum segredo foi lido.
- Nenhuma aplicação foi feita no checkout principal.

## Verificação medida

- `pytest 9.2.0`.
- Primeiro CI: 2 falhas esperadas pela assimilação: índice de skills incompleto e placeholder XML no `reversa-debugger`.
- Correções na worktree: teste do índice `1 passed`; `qualidade_llm.py` retornou `bad_skills []`.
- Segundo CI: `CI LOCAL: TUDO OK`, 95/95 passos; 1.551 testes, 1 skip e 568 subtestes aprovados.
- `git diff --check`: sem erro.
- Diff anterior: 342 arquivos; SHA-256 anterior `bace6685e57a532b3fa046b68b6c2776cc6658430d16587104a3e7b3613f9368`.
- `p8_verificar`: ainda não aplicável; o par assinado não existe.

## Verificação adicional

O diff com `--binary` aplica em cópia limpa baseada no mesmo `HEAD` (`git apply --check`: OK). SHA-256 atual: `48e231eeffe33672c09bf1c4f3fbdd964b171b8b3420b656e46adb073d2c7f25`.

## Reversão

Em uma aplicação assinada, reverter com o diff reverso do lote e repetir CI/P-8. Não remover arquivos manualmente; preservar cópias e registros conforme a skill `agata-aplicar-proposta`.

## Comando de assinatura

O Humano deverá assinar somente após a proposta chegar ao checkout principal e o CI do PR estar verde:

```bash
bash scripts/aprovar.sh atena-assimilacao-20261127
```
