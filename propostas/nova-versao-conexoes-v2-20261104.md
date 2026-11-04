# Proposta `nova-versao-conexoes-v2-20261104` — substitui `nova-versao-conexoes-20261104`

**O que é, em português comum:** é o mesmo lote 2 que você assinou, com uma correção de segurança. Na aplicação (PR #870), o CodeQL apontou 12 alertas altos de `py/path-injection` em `redesign/conexoes/segredos.py`, e o `aplicar.py` não fez o merge. Nada do lote 2 entrou no `main`. O `.diff` assinado não pode mudar, por isso esta proposta o substitui e precisa de nova assinatura.

**O que mudou em relação à anterior:**
- `segredos._arquivo` confina o caminho da chave à pasta do cofre: confere o id com `fullmatch`, normaliza com `os.path.normpath` e exige o prefixo `base + os.sep`. É o padrão que o CodeQL reconhece como proteção contra path injection.
- `nova_versao_painel.py`: em `gravar_chave`, `remover_chave` e `ajustar_conexao`, só o id que existe no catálogo segue para o cofre. O texto da requisição nunca vira caminho.
- `tests/test_conexoes.py`: ids maliciosos ("../fora", "a/b", "..", 60 caracteres, `None`) são recusados.

Todo o resto é idêntico. Descrição completa, evidência e limites estão em `propostas/nova-versao-conexoes-20261104.md`.

**Evidência (worktree, 04/11/2026):**
- 103 testes verdes nos componentes da nova versão, no painel e em ferramentas;
- âncora OK;
- depois de aplicar este `.diff` sobre `origin/main` (`7738ae2b`), 80 testes de conexões e do painel continuam verdes.

**Não medido:** o CodeQL não roda localmente, então só o PR de aplicação vai confirmar que os alertas fecharam.
