# Decreto: correção do Conselho dentro do painel (30/10/2026)

Motivo: ao abrir o Conselho dentro do painel, o script do Conselho procurava um indicador de status que não existia no painel. Sem ele, a atualização parava e a fila e os provedores não apareciam.

Mudança: um indicador de status dentro da tela do Conselho (`prototipo.html`).

Validado: os 22 testes do painel passam.

Aplicação: depois da assinatura (`bash scripts/aprovar.sh conselho-casca-status-20261030 "aprovo: status do Conselho dentro do painel"`). Depois de aplicar, reiniciar o painel.
