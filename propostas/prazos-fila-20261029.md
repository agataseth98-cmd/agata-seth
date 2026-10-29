# Proposta: prazos menores na fila do Conselho (29/10/2026)

Motivo: um item travado em `running` segurava a fila por 10 minutos (teste do Kimi, 29/10). A fila é sequencial, então nada novo andava.

Mudanças:
- `conselho_rede.py`: `EXPIRY` de 600 s para 300 s. Um item parado vira `unknown` em 5 minutos.
- `relay-extension-v2/background.js`: `TURN_MAX_WAIT_MS` de 240 s para 150 s, e `READY_TIMEOUT_MS` de 90 s para 60 s. Se a resposta não for lida em 2,5 minutos, o item vira `sem_leitura`.

Trade-off: respostas que levam mais de 2,5 minutos (raciocínio longo) passam a dar `sem_leitura`. O pior caso (página pronta em 60 s, resposta em 150 s) cabe nos 300 s de expiração.

Validado: 15 testes passam, e a sintaxe de `background.js` é válida.

Aplicação: depois da assinatura (`bash scripts/aprovar.sh prazos-fila-20261029`). Recarregar a extensão no Chromium do sistema.
