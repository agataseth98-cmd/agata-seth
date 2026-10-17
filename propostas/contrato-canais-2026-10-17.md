# Contrato comum dos módulos de canal (C13) — RASCUNHO, sem código

**Estado:** rascunho de desenho para o Humano e o Codex revisarem. Nada aqui está implementado, instalado ou ligado. Autor: Claude Code (Sonnet 5.5), 17/10/2026. Origem: Decisão 1 do Humano (15/10/2026): canais "prontos para configurar", habilitados por projeto; resposta de 16/10: só gratuitos (Discord, Telegram, e-mail, Mastodon, Bluesky, Signal com aviso), sem WhatsApp nem redes pagas, aprovação por item (Decisão 6). Depende do cofre G-C (`propostas/desenho-cofre-chaves-2026-10-16.md`): nenhum canal com chave sobe antes do F3.

## 1. Molde: o que o `discord-mcp` já cumpre (fonte: `redesign/mcp/discord/servidor.py`, docstring)
O contrato é a generalização do que existe e funciona; nada novo é inventado.
1. **Poll, nunca push.** O servidor só responde quando uma ferramenta é chamada numa sessão que o Humano iniciou; sem websocket nem escuta em segundo plano (Regra 3).
2. **Egresso sanitizado.** Todo envio passa por `sanitizar.varrer` antes de sair; achou segredo, bloqueia.
3. **Ingresso rotulado como dado.** Mensagem de terceiro volta como campo `mensagens`, nunca como texto solto que pareça instrução (Regra 2).
4. **Allowlist mecânica, vazia por padrão.** Arquivo em `~/.config/agata/<canal>-permitidos.txt`, um identificador por linha; ausente ou vazio = nenhum permitido; só o Humano edita, nunca por chat. Vale para LEITURA também (conversa de terceiro).
5. **Token fora do código e do log.** Hoje em `~/.config/agata/.env`; com o cofre, entregue por `systemd-creds`.
6. **Erro estruturado.** Rede ou HTTP falhando vira campo `erro`, nunca exceção que derruba.
7. **Manifesto de portas.** Porta só em `127.0.0.1` e `172.29.7.1`, declarada em `config/portas-agata.txt` (P-4).

## 2. O que o contrato acrescenta (cada item é uma exigência para um canal novo entrar)
- **Desligado por padrão.** Sem unit habilitada, sem entrada no `librechat.yaml`, sem chave: "não configurado". Habilitar é ato do Humano por projeto.
- **Um serviço por canal**, uma credencial por serviço (nunca compartilhada), `LoadCredentialEncrypted=` quando o cofre F3 existir.
- **Aprovação por item** para toda ação que age fora do sistema (enviar, responder, publicar, seguir): o servidor devolve um RASCUNHO e a ferramenta de envio fica na lista de aprovação do LibreChat (fora do `allow`). Leitura de canal na allowlist pode ficar sem aprovação ((716)).
- **Conteúdo de terceiro fica privado.** Mensagens lidas vão para `memoria/missoes/` (sem remote); no canon só decisão, hash e referência (Decisão 5; P-20).
- **Limite de taxa e teto diário** por canal, em arquivo de configuração, com falha fechada (acima do teto, recusa).
- **Registro de auditoria** local (`~/.cache/agata/<canal>-log.jsonl`): quem pediu, o que, resultado, sem conteúdo de terceiro.
- **Selftest offline** (sem rede, sem token): allowlist vazia bloqueia, segredo no texto bloqueia o envio, ingresso vem rotulado, erro de rede não derruba.
- **Parada rápida:** um arquivo `~/.config/agata/<canal>.parar` faz o servidor recusar tudo.

## 3. Canais, um por vez (ordem sugerida: menor risco primeiro)
| Canal | Papel mínimo | Pontos a verificar na fonte oficial ANTES de desenhar (não medidos aqui) |
|---|---|---|
| Discord | já existe | só adequar ao contrato (teto, parada, rascunho) |
| Telegram | bot por poll de atualizações | termos do Bot API, limites de taxa, privacidade do bot em grupos |
| E-mail | leitura (IMAP) e rascunho; envio só com aprovação | provedor e senha de aplicativo; risco de enviar a lista errada; anexos como dado |
| Mastodon | ler linha do tempo, rascunhar posts | instância usada e regras dela; token por escopo mínimo |
| Bluesky | idem | autenticação por senha de aplicativo; limites |
| Signal | **com aviso**: exige número de telefone e cliente não oficial (signal-cli) | licença, estabilidade e se cabe em "gratuito e aberto" (Decisão 2) |
Fora: WhatsApp e qualquer rede paga ou fechada (decisão do Humano, 16/10).

## 4. Portão de cada canal (nenhum pula)
1. Ficha do canal com as fontes oficiais lidas e datadas (F0) e o que não foi medido.
2. Portão das três perguntas ao Humano, com fatos.
3. Proposta P-8 (`scripts/`, `config/`, `redesign/mcp/<canal>/`), selftest verde, revisão cruzada com o Codex.
4. Teste de falha fechada (sem credencial não sobe com segredo vazio) e de vazamento (segredo sintético não sai).
5. Habilitação pelo Humano; primeira semana só leitura.

## 5. Perguntas para o Humano
1. A ordem de canais acima serve, ou algum é prioridade (por exemplo e-mail primeiro)?
2. Para e-mail, qual provedor e qual conta (a do projeto, `agata.seth98@gmail.com`, ou outra)? Só o Humano cria a senha de aplicativo.
3. Teto diário padrão de envios por canal (sugestão: 0 até o Humano subir; leitura livre na allowlist).
