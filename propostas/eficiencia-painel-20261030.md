# Decreto: eficiência do painel (30/10/2026)

Origem: auditoria só de leitura de 30/10 (itens 6 e 7). Mudança em `redesign/painel_operacional/conselho_rede.py` e testes.

- Banco do Conselho: três índices (`actions(status)`, `actions(created)`, `events(action)`). Criados com `IF NOT EXISTS`; não alteram dados.
- Histórico antigo (`legacy`): o resultado já limpo fica em memória e só é lido de novo quando o arquivo muda (data de modificação ou tamanho). Antes, cada atualização do painel relia o arquivo inteiro.

Fica de fora, de propósito: a limpeza de eventos antigos. Os eventos são o registro de aprovações do Conselho, e a regra do projeto é não apagar registro. Se o banco crescer demais, proponho arquivar em vez de apagar, com a sua decisão.

Testes novos: índices presentes; histórico só relido quando o arquivo muda. Suíte do painel e do Conselho: 43 testes passam.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh eficiencia-painel-20261030 "aprovo: eficiência do painel"`.
