# Rotas: ficha e placar de modelos

## Contrato

1. A ficha (`config/rotas-ficha.json`) é validada por `ficha.py` contra D2 (dado pessoal só em rota local) e D3 (cota gratuita compartilhada com aviso). Não chama provedor.
2. O placar (`placar.py`, 19/11/2026) agrega, por modelo e tipo de pedido (conversa, codigo, json, ferramenta, contexto), o que já foi medido: nota (a lógica de `scripts/porta_entrada.py`, importada, não duplicada), p50/p95, n, data, protocolo (`neutro` ou `prompt_real`, este quando o item termina em `_mcp_canon`), custo, confiança do provedor (`local`, `pago_sem_treino`, `gratuito`) e estado no painel (última decisão em `decisoes.jsonl`; standby, aposentado e vetado tiram o modelo).
3. `placar.py gerar` grava `placar.json` com modo 0600. `placar.py melhores --tipo T --classe publico|pessoal` devolve os modelos elegíveis em ordem: publico aceita qualquer confiança, pessoal só `local`, segredo nenhum.
4. Amostra pequena (n < 6) entra com aviso e peso menor (nota puxada para 0,5); nenhum modelo some por amostra pequena. De várias execuções vale a mais recente do par modelo × tipo.
5. O placar só lê arquivos; não chama provedor, não altera o gateway. Tarifa e confiança `pago_sem_treino` só entram por `tarifas.json` na pasta do placar (a tarifa do cofre não é lida aqui). Nota mecânica não é juízo de qualidade; o conteúdo entra pelo item 6.
6. Qualidade de conteúdo (19/11/2026): por modelo, o pior de três sinais já existentes: bloqueios do gateway (journal `bloqueio_turno ... served_by=`, via `--bloqueios`; 5 bloqueios zeram o sinal, ou taxa x4 se houver `turnos`), vereditos manuais (`vereditos-manuais.jsonl`) e experimento de escrita longa (`experimento-*.jsonl`). `nota_final` = 0,5 x nota mecânica ajustada + 0,5 x conteúdo; conteúdo < 0,5 é `ruim` e nunca fica à frente de modelo não ruim em `melhores`. Sem sinal: `conteúdo não medido` e `nota_final` limitada a 0,9. Sinal com nome que não casa com modelo do placar vira aviso.

## Critérios de aceite

- [ ] dado pessoal fora de rota local é erro na ficha (`tests/test_ficha.py`)
- [ ] o placar agrega por modelo e tipo com n, p50 e p95, e grava 0600 (`tests/test_placar.py`)
- [ ] classe pessoal só devolve modelo local; segredo devolve lista vazia
- [ ] standby no painel tira o modelo; a decisão mais recente vence
- [ ] amostra pequena traz aviso e peso menor, sem descartar o modelo
- [ ] fonte ausente ou resumo ilegível vira aviso, não falha
- [ ] modelo com nota mecânica 1.00 e bloqueios frequentes cai e fica marcado `ruim` (`tests/test_placar.py`)
- [ ] modelo sem dado de conteúdo aparece `conteúdo não medido`, nunca 1.00

## Código

- `ficha.py`
- `placar.py`
- `tests/`
