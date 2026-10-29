# Proposta: seth e seth-parar sob demanda (29/10/2026)

**Pedido do Humano (29/10/2026):** clicar em Seth abre o sistema inteiro (agata.target, LibreChat, painel, Obsidian) e o navegador do projeto com as 9 LLMs do Conselho e o LibreChat, já logados; clicar em parar Seth derruba só o que é do sistema.

## O que muda

- `redesign/systemd/seth`
  - sobe `obsidian-app.service` junto da espinha;
  - troca o `xdg-open` do LibreChat por um navegador do perfil do projeto (`~/.config/agata/relay-profile`), com as 9 LLMs, `/conselho-rede` e `http://127.0.0.1:3080` em uma janela;
  - se o perfil já estiver aberto (SingletonLock de um processo deste perfil), não abre outro.
- `redesign/systemd/seth-parar`
  - fecha o Obsidian com `flatpak kill md.obsidian.Obsidian` (o escopo Flatpak não para com o serviço);
  - fecha só o processo do perfil do projeto, achado pelo SingletonLock e confirmado pelo `--user-data-dir` no cmdline. O navegador pessoal não é tocado;
  - depois segue o fluxo atual (LibreChat, painel, gateway, MCPs, voz, `agata.target`).

## Fora desta proposta

- **Boot:** `agata.target` continua `enabled` e `obsidian-app` continua com `WantedBy=agata.target`. Desligar o boot é decisão do Humano e vai em proposta própria (muda unit, não script).
- **Logins:** o perfil tem cookies dos 9 provedores, mas cookie não prova login. Cada LLM precisa ser verificada aberta antes de dizer que está logada.

## Pontos não medidos

- O navegador do perfil do projeto não foi identificado com certeza. O script assume `brave` (`AGATA_NAVEGADOR`, padrão `brave`); confirmar antes de aplicar.
- Não houve teste ao vivo: não abri o navegador nem fechei o existente. Validado: `bash -n` nos dois arquivos e `git apply --check` do diff no `main`.
- `seth-parar` manda SIGTERM ao navegador do projeto. Abas com texto não enviado podem perder o rascunho.

## Aplicação

Depois da assinatura (`bash scripts/aprovar.sh seth-sob-demanda-20261029`), o PR de aplicação copia os dois arquivos para `redesign/systemd/` e para `~/.local/bin/`, e registra a entrada em MEMÓRIAS no mesmo commit.
