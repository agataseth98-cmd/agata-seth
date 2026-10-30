# Skills do Agata: índice para o Conselho

Para qualquer modelo que trabalhe no Agata (Claude, Codex, Seth ou outro). Cada skill tem um dono e um escopo; quem vai mexer em algo lê a skill certa antes.

## Skills próprias do Agata (`agata-*`)

| Skill | Use quando | Dono de fato |
|---|---|---|
| `agata-carregar` | abrir uma sessão ou quando o bloco de estado não aparecer | Claude |
| `agata-fluxo` | qualquer trabalho que mude o sistema, para qualquer modelo | Codex (doutrina) |
| `agata-fluxo-equipe` | trabalhar em Equipe, qualquer membro do Conselho (partida, fila, propriedade) | Claude |
| `agata-conselho-memoria` | cache do Conselho, canal MSG, auditoria antes de afirmar | Claude |
| `agata-aplicar-proposta` | criar, verificar e aplicar uma proposta P-8 | Claude |
| `agata-mudanca-segura` | antes de mexer em serviço, container, firewall ou config que roda | Claude |
| `agata-painel` | painel operacional (porta 20146): textos, cores, popups, medições | Claude |
| `agata-conversar-com-seth` | conversar com a Seth ou ler a conversa dela | Claude |
| `agata-relay-provedores` | adaptadores de chats web no RelayCouncil | Codex |
| `agata-ferramentas` | achar skill ou agente por tema (testes, segurança, revisão, banco, frontend) | Claude |

## Skills de terceiros (cópias fixas, não editar aqui)
- `defuddle`, `json-canvas`, `obsidian-bases`, `obsidian-cli`, `obsidian-markdown`: presentes em `.agents/skills` e em `.claude/skills`. São cópias do mesmo conteúdo; a fonte de atualização é externa.

## Regras de manutenção
1. Cada skill cita só caminhos que existem. Antes de salvar, confira: `python3 -c` com `os.path.exists` sobre os caminhos entre crases.
2. Uma skill por assunto. Se um assunto já tem skill, acrescente à skill, não crie outra.
3. Mudança em skill do repositório passa por proposta P-8 (é arquivo versionado).
4. Medido vai com comando e data. Sem medição, a frase começa com "não medido".
