# Proposta: hidratação selecionada por AGATA_PROJETO_RAIZ

Base: decisão aprovada pelo Humano em `propostas/desenho-modo-projeto-20261020.md`, seção 11. O diff aborta quando a variável está ausente, inválida ou aponta para uma instância sem `PROJETO.md` e `extras/projeto-detalhe/`; não usa fallback. A raiz é canonizada e passa a ser o diretório de trabalho do gerador. O conteúdo Markdown de `extras/projeto-detalhe/` é incluído após `PROJETO.md` na hidratação.

Antes de aplicar em qualquer instalação, configurar `AGATA_PROJETO_RAIZ` no ambiente que chama o hook. O teste aqui é `bash -n` e `git apply --check`; comportamento integrado requer teste em cópia de instância com e sem a variável.
