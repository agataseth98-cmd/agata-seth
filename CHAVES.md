# CHAVES — onde ficam os segredos

**Todos os segredos vivem em `~/.config/agata/`, fora do repositório.** Nada de chave no
git, no chat, nem em `PROJETO.md`/`MEMÓRIAS.md`. Permissão `600`.

| arquivo | o quê |
|---|---|
| `~/.config/agata/.env` | chaves de API dos provedores de modelo (`GROQ_API_KEY`, `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`/`GEMINI_API_KEY`, `ZHIPU_API_KEY`, `CEREBRAS_API_KEY`, …). Era `~/.hermes/.env` até a remoção do Hermes (03/09/2026, MEMÓRIAS (312)). |
| `~/.config/agata/restic.pass` | senha do repo restic no HD `AgataBkup01` |
| `~/.config/agata/obsidian.token` | bearer do plugin `obsidian-local-rest-api` (`:27124`) |
| `~/.config/agata/google-project/` | credencial OAuth da conta do projeto (`agata.seth98@gmail.com`, escopo `drive.file`) para o índice → Drive/NotebookLM |
| `~/.omniroute/.env` | `STORAGE_ENCRYPTION_KEY` do OmniRoute (cifra o `storage.sqlite`) |

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

## Backup

`scripts/cifrar_env.sh` cifra `~/.config/agata/.env` com GPG simétrico (AES256) e põe o
`.gpg` dentro do repo restic (tag `agata-env`) + cópia solta no HD. Rodar após qualquer
mudança de chave.
