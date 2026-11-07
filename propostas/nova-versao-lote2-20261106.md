# Proposta nova-versao-lote2-20261106

## Resumo
Novo subcomando `nv.py reverter [dest]`, em `redesign/nova_versao/nv.py`. Ele faz duas coisas:
- remove só o cache, que é derivado: `AGATA_NV_CACHE`, ou o padrão `~/.cache/agata/nova-versao`;
- arquiva `AGATA_NV_DIR` (ledger, eventos e execuções) num `.tar.gz` datado, sem apagar os dados.

O destino padrão é `<pai dos dados>/nova-versao-arquivo`. O pacote abre com `x:gz` e nunca sobrescreve um pacote que já exista. O revert do commit é um passo à parte.

Diff (`git diff --stat`): nv.py +54, tests/test_nova_versao.py +106. Só inserções.

## Recusas
Antes de tocar em qualquer coisa, o subcomando recusa com ValueError nestes casos:
- variáveis vazias (`AGATA_NV_DIR` ou `AGATA_NV_CACHE` com valor vazio);
- cache igual a `/` ou à home;
- cache igual aos dados, dentro deles ou que os contenha;
- cache que contém o diretório atual ou o repositório;
- cache fora de `~/.cache` ou sem "nova-versao" no nome;
- destino dentro dos dados ou do cache.

## Testes
- Resultado: 14 testes passam, com home falsa por mock e nenhum toque no `~/.cache` real.
- Esse resultado vem do coordenador; não rodei os testes para este registro.
- No diff, o arquivo de teste acrescenta 10 funções `def test_`. Não verifiquei como elas chegam a 14 testes.

## Revisão
O agata-revisor aprovou na rodada 3. Antes, foram corrigidos 2 achados ALTA, 1 MÉDIA e 3 BAIXA. Isso vem do coordenador.

## Fora deste lote
- Painel de chaves: parado, porque a exceção do `.env` espera o Humano.
- Entradas do `acceptance.json`: vão na v2 da spec, depois deste lote. O alvo do critério (c) é `test_nova_versao.py::ReversaoTests::test_reversao_nao_apaga_dados_so_remove_cache`.

## Limites
- Proposta não aplicada.
- Sem APROVADO.

## Assinatura (só o Humano)
```
bash scripts/aprovar.sh nova-versao-lote2-20261106
```
