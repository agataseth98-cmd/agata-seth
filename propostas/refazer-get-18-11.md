# Correção urgente: GET do gateway quebrado após verificar-refazer (`refazer-get-18-11`)

Classe: Correção (runtime: `seth_gateway.py`). Base: `origin/main` (8ba46dbd).

## Incidente (medido 18/11/2026 10:23)

Depois da aplicação de `verificar-refazer-18-11` (PR #1032) e do reinício do gateway às 10:22:52, todo GET (`/v1/models`, `/api/health`) responde sem corpo (curl 000): `AttributeError: '_Handler' object has no attribute '_refazer'` em `_passar`. Os atributos `_refazer` e `_verificar` só eram atribuídos em `do_POST`. POST respondeu (403 por política, sem o erro). Os testes do lote usavam só POST.

## O que muda

Valores padrão de classe `_refazer = False` e `_verificar = False` em `_Handler`, como já existe para `_rota`. Teste de regressão em `test_verificar_refazer.py`.

## Medido

`pytest redesign/router`: 105 passed. `seth_gateway.py --selftest`: SELFTEST OK. `git apply --check`: APLICA.

## Reversão

`git apply -R` do diff, ou reverter #1032.

## Comando de assinatura

bash scripts/aprovar.sh refazer-get-18-11

## Modelos

Claude Opus 5.5 diagnosticou (a partir do relato do agente Haiku que aplicou) e corrigiu.
