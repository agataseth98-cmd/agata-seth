# Locais do llama-cpp no benchmark e no gateway, e correção do roteiro de sob-demanda (`competicao-locais-18-11`)

Classe: Mudança (runtime: `redesign/router/seth_gateway.py`, `scripts/benchmark_roteamento.py`; CI: `scripts/ci_sdd_local.sh`) e correção de roteiro (`propostas/sob-demanda-17-11.md`). Base: `origin/main` (ae4e0ec1).

## O que muda

1. `scripts/benchmark_roteamento.py`: `LOCAIS` passa a incluir `llama-cpp/` e `llamacpp-` (antes só `ollama-local/`, `llamacpp-local/`, `local/`). Efeito: o anexo privado do canon vai para modelos llama-cpp; antes o nemotron pulava esses itens como se fosse remoto. O `--via-gateway` também recusa só remotos, e não os locais llama-cpp.
2. `redesign/router/seth_gateway.py`: `_ROTAS_LOCAIS` usa a mesma lista (`ollama-local/`, `llamacpp-`, `llama-cpp/`, `local/`). `llamacpp-local/` deixa de ser o prefixo exato e passa a ser coberto por `llamacpp-`. Efeito: um pedido `llama-cpp/...` sem classificação deixa de receber 403 (ramo de dados externos) e passa como local; um pedido classificado como público recebe hidratação e ferramentas como o `ollama-local/`, e não cai na faixa pública.
3. `scripts/ci_sdd_local.sh`: passo novo `benchmark: locais e privacidade (testes)`, que roda `scripts/testar_benchmark_roteamento.py` (14 testes, sem rede). Os testes garantem que as duas listas continuam iguais.
4. `redesign/router/test_seth_base.py`: teste 21e (llama-cpp/ e llamacpp- entram no ramo local; nuvem sem classe continua bloqueada).

## Correção do roteiro de sob-demanda-17-11

O roteiro `propostas/sob-demanda-17-11.md` (linha 37) relinka só `laya-roteador.socket`, `laya-roteador-proxy.service`, `ollaya.socket` e `ollaya-proxy.service`. Falta relinkar os backends `laya-roteador.service` e `ollaya.service`:

    ln -sfn ~/agata/config/laya-roteador.service ~/.config/systemd/user/laya-roteador.service
    ln -sfn ~/agata/config/ollaya.service ~/.config/systemd/user/ollaya.service

Motivo: `config/laya-roteador-proxy.service` e `config/ollaya-proxy.service` declaram `Requires=`/`After=` do backend; sem o unit do backend carregável, o proxy de socket não sobe. O desvio foi registrado em `CHECKPOINT.md` em 18/11 (`disable` removeu os links, depois foram refeitos). Medido agora (read-only): os dois links existem em `~/.config/systemd/user/`, apontando para `config/`, criados 18/11 09:02.

Autorização do Humano para esta correção: "tem autorização para consertar tudo mesmo que mexa na produção".

## Medido

Na worktree `trabalho/competicao-locais-18-11b` (base `ae4e0ec1`), com a alteração aplicada:

- `pytest redesign/router -q`: 107 passed, 10 subtests passed.
- `python3 redesign/router/seth_gateway.py --selftest`: SELFTEST OK (inclui `21e`: llama-cpp/ e llamacpp- entram no ramo local; nuvem sem classe continua bloqueada).
- `python3 -I scripts/testar_benchmark_roteamento.py`: Ran 14 tests, OK.
- `python3 -I scripts/benchmark_roteamento.py --selftest`: SELFTEST OK.
- `git apply --3way` do WIP (base `8b4b806d`) sobre `ae4e0ec1`: aplicou sem conflito; os padrões `_refazer = False` e `_verificar = False` em `_Handler` e o código de verificar-e-refazer continuam no arquivo.
- `git apply --check` do `.diff` sobre `origin/main` (`ae4e0ec1`): APLICA.

## Não medido

- Requisição real a um `llama-cpp/...` pelo gateway, com o servidor no ar. Só o selftest e os testes sem rede.
- Comportamento do passo novo do CI em runner limpo (só rodou local).

## Reversão

`git apply -R propostas/aplicadas/competicao-locais-18-11.diff`, ou reverter o PR de aplicação. A correção do roteiro é só documentação e não tem reversão.

## Comando de assinatura

bash scripts/aprovar.sh competicao-locais-18-11

## Modelos

Claude Haiku 5.5 (agente do Claude Code), orquestrado pelo Claude Opus 5.5. Implementou, testou e mediu a partir do WIP guardado em `~/agata-arquivo/roteador-capacidade-17-11/competicao-locais-wip.diff`.
