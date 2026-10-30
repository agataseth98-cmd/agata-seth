# Decreto: Conselho dentro do painel geral (30/10/2026)

**O que muda:** a tela do Conselho deixa de ser uma página separada. Ela abre dentro do painel, com a mesma barra lateral e a mesma barra superior dos outros painéis. Ao clicar em "Conselho de Modelos em Rede", a página muda sem trocar de janela.

**Mudanças (só a casca do painel):**
- `prototipo.html`: a seção do Conselho passa a conter o conteúdo da tela do Conselho; o script do Conselho é carregado pelo painel.
- `prototipo.css`: o estilo da tela do Conselho é incluído, escopado para não mudar o restante do painel.
- `prototipo.js`: o clique no Conselho não redireciona mais para `/conselho-rede`.

**O que não muda:** os envios, a fila de aprovação, os debates e as ferramentas do Conselho continuam iguais. A página antiga `/conselho-rede` continua existindo.

**Validado:** os 22 testes do painel passam, e o CSS e o HTML têm estrutura balanceada.

**Não validado visualmente:** a tela do Conselho dentro do painel precisa de um teste com você olhando, depois da aplicação.

**Aplicação:** depois da assinatura (`bash scripts/aprovar.sh conselho-na-casca-20261030 "aprovo: Conselho dentro do painel"`). Depois de aplicar, reiniciar o painel.
