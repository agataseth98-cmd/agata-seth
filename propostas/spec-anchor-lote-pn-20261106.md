# Proposta spec-anchor — inclui no dono de cada componente os arquivos novos do lote

**Nome para assinatura:** `spec-anchor-lote-pn-20261106`
**Motivo:** o CI (job `sdd`, passo de âncora) acusou cinco arquivos novos do lote `lote-pn-20261106` sem dono na spec da própria pasta. Esta proposta só acrescenta esses arquivos à seção "Código" de três specs.

## Mudança (7 linhas em 3 arquivos)
- `redesign/painel_operacional/spec/spec.md`: `chat_stream.py`, `test_chat_stream.py`, `test_chat_stream_rota.py`.
- `redesign/nova_versao/spec/spec.md`: `conselho.py`.
- `redesign/sentidos/spec/spec.md`: `falha_segura.py`.

## Aplicação
Depois do merge da aplicação do lote (PR #917). O `.diff` foi gerado contra o estado que contém o lote.

## Evidência
- Na árvore com o lote aplicado: `anchor.py` passa para `redesign/painel_operacional`, `redesign/nova_versao` e `redesign/sentidos`.
- Ciclo SDD de `redesign/nova_versao`: gates OK, âncora OK.
