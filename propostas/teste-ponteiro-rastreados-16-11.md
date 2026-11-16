# Teste de ponteiros lê só arquivos rastreados (`teste-ponteiro-rastreados-16-11`)

Proposta P-8 de `teste-ponteiro-rastreados-16-11`. Diff: `propostas/teste-ponteiro-rastreados-16-11.diff` (1 arquivo: `redesign/projeto_indice/tests/test_projeto_indice.py`; sha256 `574b4112c99083805ef458b38b391e1a7b4b0b0364b23fb2fc212b99b2f43c87`). Base: `origin/main` (65815eef).

Pedido desta sessão (894c2006, 16/11/2026): o teste `test_nenhum_ponteiro_vivo_para_secao_que_saiu` percorre o disco com `os.walk`. No `~/agata` vivo ele falha por causa de arquivos fora do git (ex.: `logs/incidente-corrupcao-memorias-2026-09-22/diff-completo.patch`). Essa falha veio do pedido e não foi reproduzida aqui.

O que muda (só o arquivo de teste):
1. Novo `_arquivos_do_repo()`: lista os arquivos com `git -C <RAIZ> ls-files -z`. Sem git, ou fora de um repositório, volta ao `os.walk` de antes.
2. Os filtros continuam iguais: diretórios podados (`.git`, `__pycache__`, `worktrees`, `.pytest_cache`), `pular_exato`, `pular_prefixo` e as extensões ignoradas.
3. O laço do teste passa a iterar essa lista; o corpo do laço perde um nível de indentação.
4. `ESTADO.md` entra no commit porque o pre-commit o regenera em todo commit. A única mudança é a linha `teste-ponteiro-rastreados-16-11` na seção Propostas.

Medido em 16/11/2026 (worktree a partir de origin/main):
- `pytest -q redesign/projeto_indice/tests/`: 24 passed antes da mudança; 24 passed com ela.
- Arquivo solto fora do git (`logs/teste-fora-do-git-16-11/ruido.patch`, com um ponteiro para seção inexistente): a lista com git não o inclui, e o teste passa com ele presente.
- Sem git (`subprocess.run` trocado por um que levanta `FileNotFoundError`): o fallback inclui o arquivo solto (3198 itens, contra 3196 com git) e nenhum caminho `.git/`.
- `scripts/ci_sdd_local.sh` com `PATH` e `PYTEST` apontando para `~/.local/share/agata-pytest/bin`: `CI LOCAL: TUDO OK` (58 OK).

Não medido:
- A falha no `~/agata` vivo e o efeito da mudança nele (o checkout vivo não foi tocado).
- A versão antiga do teste com o arquivo solto presente (não rodada aqui).
- O CI do PR no GitHub (fica no registro do PR).

Nota de ambiente: sem o binário no `PATH`, `ci_sdd_local.sh` falha no passo de painel, porque `acceptance_runner.py` chama `pytest` pelo nome (`FileNotFoundError`). O CI local precisa de `PATH` com `~/.local/share/agata-pytest/bin`, além de `PYTEST=`.

Aplicação: só depois da assinatura do Humano (`bash scripts/aprovar.sh teste-ponteiro-rastreados-16-11`). Esta PR só abre a proposta; o `main` não muda com ela.

Reversão: `git revert` do commit de aplicação, quando houver. Até lá, nada muda no código.
