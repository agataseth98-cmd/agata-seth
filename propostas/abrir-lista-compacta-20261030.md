# Decreto: lista Abrir visível na barra lateral (30/10/2026)

Motivo: os botões de abrir estavam no fim da barra lateral, abaixo da altura da tela. Por isso pareciam não funcionar pelo menu: o clique estava fora da tela e o aviso também.

Mudança (só `prototipo.css`): a lista Abrir passa a duas colunas, com botões menores. Ela cabe na tela de 900 px de altura.

Validado: os testes do painel passam. Medido numa cópia: a lista ocupa de 695 a 898 px, dentro da tela.

Aplicação: depois da assinatura (`bash scripts/aprovar.sh abrir-lista-compacta-20261030 "aprovo: lista Abrir visível"`). Depois de aplicar, reiniciar o painel.
