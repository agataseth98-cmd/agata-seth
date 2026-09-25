# CHAVES — onde ficam os segredos

**Todos os segredos vivem em `~/.config/agata/`, fora do repositório.** Nada de chave no
git, no chat, nem em `PROJETO.md`/`MEMÓRIAS.md`. Permissão `600`.

**Modelo sem segredo, versionado:** `CHAVES.env.exemplo` (raiz do repo) —
mesmo padrão de `redesign/librechat/env.exemplo`. Documenta a FORMA de
`~/.config/agata/.env` (nome de cada variável + link de onde tirar a chave),
nunca um valor real. Fase 1 do plano de replicabilidade
(`propostas/plano-replicabilidade-2026-09-25.md`) — um clone novo copia este
arquivo pra `~/.config/agata/.env` e preenche, em vez de adivinhar o formato
lendo prosa espalhada.

| arquivo | o quê |
|---|---|
| `~/.config/agata/.env` | chaves de API dos provedores de modelo (`GROQ_API_KEY`, `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`/`GEMINI_API_KEY`, `ZHIPU_API_KEY`, `CEREBRAS_API_KEY`, …). Era `~/.hermes/.env` até a remoção do Hermes (03/09/2026, MEMÓRIAS (312)). |
| `~/.config/agata/restic.pass` | senha do repo restic no HD `AgataBkup01` |
| `~/.config/agata/obsidian.token` | bearer do plugin `obsidian-local-rest-api` (`:27124`) |
| `~/.config/agata/google-project/` | credencial OAuth da conta do projeto (`agata.seth98@gmail.com`, escopo `drive.file`) para o índice → Drive/NotebookLM |
| `~/.omniroute/.env` | `STORAGE_ENCRYPTION_KEY` do OmniRoute (cifra o `storage.sqlite`) |
| `~/librechat/.env` | segredos do LibreChat: `CREDS_KEY`, `CREDS_IV`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `MEILI_MASTER_KEY`. Fora do repo, `600`. Gerados na troca Open WebUI → LibreChat (03/09/2026, MEMÓRIAS (313)). Modelo sem-segredo: `redesign/librechat/env.exemplo`. |
| `~/librechat/PRIMEIRO-ACESSO.txt` | senha do primeiro login do LibreChat (`600`, apagar após trocar no app) |
| `~/.config/agata/.env` (`DISCORD_BOT_TOKEN`) | token do bot Discord da skill nova (05/09/2026, `redesign/mcp/discord/`). Sem ele, `ler_mensagens`/`enviar_mensagem` retornam erro estruturado, não levantam. Criar em `discord.com/developers/applications` → aplicação → Bot → Reset Token → convidar o bot no servidor/canal desejado (escopo `bot`, permissões `Read Messages`/`Send Messages`). |

## Como o OmniRoute usa as chaves

O OmniRoute **não lê `~/.config/agata/.env` em runtime.** Na Fase 1 as chaves foram lidas
desse arquivo e registradas nos provedores via `omniroute setup --add-provider`; desde
então ficam **cifradas em `~/.omniroute/storage.sqlite`** (`provider_connections`, campo
`api_key: enc:…`), decifradas com o `STORAGE_ENCRYPTION_KEY`.

`~/.config/agata/.env` é a **fonte** para adicionar um provedor novo ou rotacionar uma
chave:
1. editar `~/.config/agata/.env` (o Humano, direto — nunca pelo chat);
2. rodar os comandos de `redesign/router/PROVEDORES.md` para (re)registrar no OmniRoute;
3. `systemctl --user restart omniroute.service`.

## Checklist: testar que uma chave funcionou, e como rotacionar

Escrito porque hoje é prosa espalhada — vira executável. "Rotacionar" é
sempre: gerar/copiar a chave nova → repetir o teste da linha → só então
apagar a antiga.

| Segredo | Como testar que funcionou |
|---|---|
| Chave de provedor de modelo (Groq, OpenRouter, Google, Zhipu, Cerebras, DeepSeek, HuggingFace, Mistral) | `redesign/router/PROVEDORES.md` (registrar/atualizar no OmniRoute) → `python3 scripts/pesquisar_modelos_gratuitos.py` sonda o provedor de verdade; 200 com resposta real = funcionou, 401/403 = chave errada ou não propagada. |
| `DISCORD_BOT_TOKEN` | `ler_mensagens`/`enviar_mensagem` do MCP `discord` devolvem conteúdo real em vez do erro estruturado que aparece sem token. |
| `~/.config/agata/restic.pass` | `restic snapshots` (repo no HD `AgataBkup01`) lista sem pedir senha de novo nem falhar. |
| `~/.config/agata/obsidian.token` | `curl -H "Authorization: Bearer <token>" http://127.0.0.1:27124/` responde 200, não 401. |
| `~/.config/agata/google-project/` (OAuth) | `python3 scripts/subir_esfera_projeto.py <arquivo de teste pequeno>` sobe sem erro de credencial. |
| `~/.omniroute/.env` (`STORAGE_ENCRYPTION_KEY`) | `systemctl --user restart omniroute.service` sobe limpo — chave errada falha decifrando `storage.sqlite` no boot, erro aparece no log do serviço. |
| `~/librechat/.env` (`CREDS_KEY`/`JWT_*`/`MEILI_MASTER_KEY`) | `docker compose up -d` + `curl http://127.0.0.1:3080/health` → 200. |

## Backup

`scripts/cifrar_env.sh` cifra `~/.config/agata/.env` com GPG simétrico (AES256) e põe o
`.gpg` dentro do repo restic (tag `agata-env`) + cópia solta no HD. Rodar após qualquer
mudança de chave.
