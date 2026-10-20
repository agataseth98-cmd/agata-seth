# Proposta: manter PROJETO.md abaixo do teto

Medição na base anterior ao PR 405 (`b4fdc20^`): 47.703 bytes. HEAD antes da proposta (`bbfb561`): 48.810 bytes, aumento líquido de 1.107 bytes. O parágrafo de segurança do `seth-escriba` ocupa 1.101 bytes; movê-lo integralmente para `extras/projeto-detalhe/servicos-e-interface.md` e deixar um ponteiro reduz PROJETO.md para 47.862 bytes, 138 bytes abaixo do teto de 48.000.

A proposta preserva o texto integral, muda apenas sua localização e o ponteiro no canon.
