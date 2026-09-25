# Goose — fallback do Claude Code no Agata (MEMÓRIAS (543))

Fonte versionada da configuração do Goose que muda comportamento. Runtime: `~/.config/goose/`.
Instalar/atualizar (depois de aplicada a proposta P-8):

    cp redesign/goose/AGENTS.md      ~/.config/goose/AGENTS.md
    cp redesign/goose/permission.yaml ~/.config/goose/permission.yaml
    # extensão canon: acrescentar o bloco de canon-extension.yaml em `extensions:` do
    # ~/.config/goose/config.yaml (o config.yaml inteiro NÃO é versionado: traz token de extensão)

Skills do projeto (lidas pelo Goose quando roda dentro de `~/agata`): `.agents/skills/`.
Teste: `cd ~/agata && goose run --no-session -t "carregar agata"` deve devolver o bloco de 3 linhas.
