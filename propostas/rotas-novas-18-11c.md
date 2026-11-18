# Proposta rotas-novas-18-11c — idêntica a rotas-novas-18-11b, sem ESTADO.md

O diff assinado de `rotas-novas-18-11b` incluiu `ESTADO.md`. O pre-commit regenera esse arquivo em todo commit, e ele lista as propostas abertas, inclusive a própria. Por isso o head da aplicação nunca casa com o diff assinado, e o fiscal P-8 reprova (PR #1051, "divergente: ESTADO.md"). Esta versão tem os mesmos 15 arquivos e as mesmas linhas, sem o `ESTADO.md`, que o hook gera na aplicação.

Conteúdo, medição e reversão: ver `propostas/rotas-novas-18-11b.md`. Não assinar `rotas-novas-18-11` nem reaplicar a `-18-11b`.

Lição: diff de proposta não leva arquivo gerado pelo hook (`ESTADO.md`, `.hidrata.md`, índices).

**Modelo:** Opus 5.5.
