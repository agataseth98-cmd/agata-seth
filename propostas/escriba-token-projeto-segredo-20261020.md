# Proposta: token por projeto e bloqueio de segredo no Escriba

Base de decisão: `propostas/desenho-modo-projeto-20261020.md`, seção 10. O diff exige raiz ativa explícita, deriva um identificador não secreto da raiz e lê o token correspondente em `~/.config/agata/projetos/<sha256-da-raiz>.token`. Recusa tokens ausentes/inválidos e arquivos que não sejam regulares, do usuário, sem links extras e sem permissões para grupo/outros.

Antes de aceitar capability, o Escriba examina título, corpo e diário com os mesmos padrões de `scripts/varredura_segredo.sh`; erro na leitura/execução da régua bloqueia a escrita, e a resposta não repete o texto suspeito. O token é esperado em `X-Agata-Project-Token`.

**Pendente de integração antes de aplicar:** provisionar o token e encaminhar o header pelo executor MCP; o serviço de cada projeto precisa receber porta própria em `SETH_ESCRIBA_BIND`. Esta proposta altera o executor HTTP (`seth_escriba.py`) e inclui contraprovas, mas não muda unidade systemd, compose nem cliente MCP.
