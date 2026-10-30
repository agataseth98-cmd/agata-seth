# Decreto: serviços na barra lateral e modelos dentro do Conselho (30/10/2026)

Motivo: o botão de abrir os modelos ficava na barra lateral, fora da tela, e não abria. Os modelos pertencem ao Conselho, e os serviços do sistema devem abrir em janela própria.

Mudança:
- Barra lateral "Serviços": Obsidian, LibreChat e OmniRoute (interface em 127.0.0.1:20128), cada um em janela própria.
- Dentro da tela do Conselho: os nove modelos como botões. Eles pedem a janela pelo mesmo caminho dos serviços e não usam links externos (o painel proíbe links que abrem em nova aba).
- Servidor: lista fixa com os serviços e os modelos. Cada pedido de abrir vira janela própria.
- Extensão: pedido de janela cria uma janela normal com a página.

Validado: os testes do painel e do Conselho passam.

Pendência conhecida (anotada): ao clicar, a janela pode não abrir se a extensão não tiver sido recarregada. Precisa de teste ao vivo.

Aplicação: depois da assinatura (`bash scripts/aprovar.sh servicos-e-modelos-20261030 "aprovo: serviços e modelos"`). Depois de aplicar, recarregar a extensão e reiniciar o painel.
