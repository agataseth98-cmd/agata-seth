# Proposta M2c — teste do estado parcial do Acervo

**Nome para assinatura:** `m2c-acervo-parcial-20261106`
**Motivo:** o ciclo SDD da M2b (drift, 06/11/2026) encontrou o estado `parcial` sem teste direto. O código existe em `redesign/painel_operacional/nova_versao_painel.py` (regra `parcial` se há ilegíveis); o teste não estava na árvore aplicada.

## Mudança
- `redesign/painel_operacional/test_nova_versao_painel.py`: um teste novo, `test_acervo_com_registro_ilegivel_diz_parcial_e_conta`. Ele cria um cadastro legível e um arquivo ilegível e confere estado `parcial`, `ilegiveis == 1` e um item.
- Nenhuma mudança de código.

## Evidência
- Passa no `origin/main` (código já presente).
- Teste de mutação: trocar `parcial` por `ok` na regra faz o teste falhar; com a regra original, passa. O teste prende o comportamento.
- Suíte do painel de nova versão (`test_nova_versao_painel.py`): OK.
