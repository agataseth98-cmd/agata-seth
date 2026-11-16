# Goose — fallback do Claude Code no Agata (MEMÓRIAS (543))

> Aviso (16/11/2026): pasta histórica. O Goose saiu do sistema em 07/11/2026 (`config/modelos-gratuitos.md`, linha 159).
> O agente de terminal é o OpenCode (`redesign/systemd/seth-agente`, que usa `command -v opencode`).

Fonte versionada da configuração do Goose que muda comportamento. Runtime: `~/.config/goose/`.
Instalar/atualizar (depois de aplicada a proposta P-8):

    cp redesign/goose/AGENTS.md      ~/.config/goose/AGENTS.md
    cp redesign/goose/permission.yaml ~/.config/goose/permission.yaml
    # extensão canon: acrescentar o bloco de canon-extension.yaml em `extensions:` do
    # ~/.config/goose/config.yaml (o config.yaml inteiro NÃO é versionado: traz token de extensão)

Skills do projeto (lidas pelo Goose quando roda dentro de `~/agata`): `.agents/skills/`.
Teste: `cd ~/agata && goose run --no-session -t "carregar agata"` deve devolver o bloco de 3 linhas.
