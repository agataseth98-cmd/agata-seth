# Decisão — nova versão (Experimento GPT)

- **Direção do produto:** Humano, (077), "Essa será a nova versão do agata ok".
- **Plano:** aprovado pelo Humano em 04/11/2026 (plano de 4 lotes, mais o lote 0 de verificação).
- **Acervo do piloto:** só o que já está no repositório; a Alexandria tem estrutura própria de pastas de trabalho (Humano, 04/11).
- **Orçamento:** "tudo que estiver disponivel configuravel pelo painel" (Humano, 04/11). Padrão de fábrica só local até o Humano mudar no painel.
- **Assinatura:** F0 e F1 num lote só (Humano, 04/11; regra "uma assinatura por implementação").
- **Escolhas técnicas deste lote:** SQLite FTS5 (medido: disponível no SQLite 3.54.0 da Máquina) como índice léxico derivado; `evidence_ledger` como diário único; sombra no gateway desligada por padrão; nenhum serviço novo, nenhuma porta nova, nenhum timer novo.

DECISAO: aceita — plano aprovado pelo Humano nesta sessão (04/11/2026), em modo de plano; a assinatura P-8 da aplicação continua sendo dele.
