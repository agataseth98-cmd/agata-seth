# Proposta — critério de orçamento da spec v2 (refeita)

**Nome para assinatura:** `nova-versao-spec-v2-refeita-07-11`
**Base:** `origin/main` (e99f029c)
**sha256 do `.diff`:** `bb3e6a1360fe4d696e2fdb8357e4283c8012655727a19713ecf00eed692bd418`
**Origem:** as alterações de `acceptance.json` e de `test_nova_versao.py` do critério de orçamento se perderam numa limpeza de /tmp (registro 386 do cache do Conselho). Esta proposta refaz o critério a partir do código, sem replay de transcrição. Referência lida antes de escrever: `origin/proposta/nova-versao-spec-v2-20261106-diff` (commit 7f68458), que não tem o critério em `acceptance.json` nem em `test_nova_versao.py`.

## O que muda

- `redesign/nova_versao/spec/acceptance.json`: +1 critério (9 linhas), no formato dos outros, com o comando `pytest` do teste novo. Fica logo após o critério "o orçamento padrão é só local e pago sem teto não gasta".
- `redesign/nova_versao/tests/test_nova_versao.py`: teste novo `OrcamentoTests::test_valores_de_fabrica_e_quatro_categorias_da_spec` (+7 linhas). Confere as quatro categorias (`local`, `gratuito`, `assinatura`, `pago`), o padrão (só `local` ligado), os valores 200 chamadas, 2.000.000 tokens, 120 s e R$ 0, e que `permite()` deixa passar só `local`.
- `redesign/nova_versao/spec/spec.md`: +1 checkbox na seção "Critérios de aceite", com o mesmo texto do critério. O drift por critério lê os checkboxes, então sem esta linha o critério ficaria fora da spec.

## Valores de fábrica (conferidos no código)

Lidos em `redesign/nova_versao/orcamento.py` (`PADRAO`, em e99f029c), não de memória:

- `provedores`: `local` ligado; `gratuito`, `assinatura` e `pago` desligados.
- `max_chamadas`: 200. `max_tokens`: 2000000. `timeout_s`: 120. `teto_reais`: 0.0.
- `PROVEDORES` = `("local", "gratuito", "assinatura", "pago")`.

## Fora desta proposta

- Critérios de painel de chaves e de reversão da spec v2: sem teste, não entram aqui.
- Demais mudanças da spec v2 (texto de Orçamento, Código, lotes 5 e 6, cofre de chaves, reversão): não entram aqui.
- `redesign/nova_versao/spec/evidence.json` e `criterion-drift.md` (rastreados, de execução anterior): não regenerados.

## Evidência

- `runner.py proposal` (base `origin/main`): `git apply --check`, `git apply` num checkout limpo e `git diff --check` passaram. Registro no estado do runner com o mesmo sha256.
- Testes do componente `nova_versao` (`unittest discover`): 41 OK, na worktree e num checkout limpo de origin/main com o diff aplicado.
- Teste novo com mutação (`max_chamadas` 201 numa cópia): falha em `(201, 2000000, 120, 0.0) != (200, 2000000, 120, 0.0)`. Sem mutação: passa.
- `redesign/sdd_flow/anchor.py` com o escopo do CI: `ANCHOR: OK`.
- `redesign/sdd_flow/spec_gate.py check` na spec: `SPEC GATES: OK`.
- Checkboxes de `spec.md` e critérios de `acceptance.json`: 12 e 12, mesmo texto e mesma ordem.

## Não medido

- `pytest` não está instalado nesta máquina e não foi instalado. Por isso `acceptance_runner.py` e o `cycle` (que chamam `pytest` pelo nome) não rodaram. O comando declarado no critério não foi executado pelo `pytest`; o teste foi executado pelo `unittest`.
- Drift por critério (`criterion_drift.py`) não rodou com evidência de execução. Só foi conferida a correspondência de texto entre checkbox e critério.

## Assinatura

Depois do merge do PR de proposta, o Humano assina com `bash scripts/aprovar.sh nova-versao-spec-v2-refeita-07-11`. A assinatura fica amarrada ao sha256 acima.
