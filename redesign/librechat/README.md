# LibreChat -- lane de conversa da Seth

Substituiu o Open WebUI em 03/09/2026 (MEMORIAS (313)). Frontend de conversa
informal, "estilo ChatGPT/Claude", apontado no `seth_gateway` (`:20126`).
Para agente/codigo continua o Goose (`seth-agente`).

## Forma (espelhos do sistema)

- **Enxuto**: so 3 contêineres -- `librechat`, `librechat-mongodb`, `librechat-meilisearch`.
- **SEM RAG por embedding**: `rag_api` e `pgvector` nao sao implantados. Respeita
  MEMORIAS (115)/(293) (busca semantica recusada; canon e grep + link por numero).
- **Memoria desligada** (`memory.disabled: true`): a hidratacao da Seth vem do
  `seth_gateway`, que injeta canon-em-git verificavel. Nada de auto-captura por LLM
  (MEMORIAS (312)).
- **Sob demanda**: `restart: "no"` em tudo. Sobe/para pelos atalhos `seth` / `Parar Seth`.
- **Loopback**: a app faz bind em `127.0.0.1:3080`. Acesso remoto e via Tailscale
  serve (nao expor porta).
- **Um endpoint** ("Seth") -> `http://127.0.0.1:20126/v1` (seth_gateway ->
  sanitizador -> OmniRoute). `ENDPOINTS=custom` esconde os embutidos.

## Layout

| Onde | O que |
|---|---|
| `~/librechat/` | runtime -- `.env` (segredos, 600), `librechat.yaml`, `docker-compose.yml`, `data/ images/ uploads/ logs/`, `PRIMEIRO-ACESSO.txt` |
| `~/agata/redesign/librechat/` | **fonte versionada** -- copias de `docker-compose.yml` e `librechat.yaml`, `env.exemplo` (placeholders), este README |
| `~/librechat/.env` | segredos reais: `CREDS_KEY`, `CREDS_IV`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `MEILI_MASTER_KEY`. Ver `CHAVES.md`. |

Editou `~/librechat/librechat.yaml` ou o compose? Copie a versao sem-segredo para
`redesign/librechat/` e commite.

## Rede

A app roda em `network_mode: host` para alcancar o `seth_gateway` em
`127.0.0.1:20126` -- mesmo padrao que o Open WebUI usava nesta maquina. Mongo e
Meili ficam numa bridge privada (`librechat`) e so publicam em `127.0.0.1`.

## Operacao

```
docker compose -f ~/librechat/docker-compose.yml up -d      # subir (o atalho `seth` faz isso)
docker compose -f ~/librechat/docker-compose.yml stop       # parar  (o atalho `Parar Seth`)
docker compose -f ~/librechat/docker-compose.yml logs -f librechat
```

Primeiro acesso: `http://127.0.0.1:3080`, credenciais em `~/librechat/PRIMEIRO-ACESSO.txt`.
Trocar a senha no menu (canto inferior esquerdo > Configuracoes > Conta) e apagar o arquivo.

Conta unica -- `ALLOW_REGISTRATION=false`. Recriar/trocar senha:

```
# gera o hash e grava direto no Mongo (o `npm run reset-password` do container e interativo e nao aceita pipe)
HASH=$(docker compose -f ~/librechat/docker-compose.yml exec -T librechat node -e 'console.log(require("bcryptjs").hashSync(process.argv[1],10))' 'NOVASENHA')
docker compose -f ~/librechat/docker-compose.yml exec -T librechat-mongodb mongosh LibreChat --quiet \
  --eval 'db.users.updateOne({email:"agata.seth98@gmail.com"},{$set:{password:"'"$HASH"'"}})'
```

## Voz

TTS pelo `kokoro-tts` (`:8880`, ja rodava; OpenAI-compat em `/v1/audio/speech`).
Configurado em `librechat.yaml` -> `speech.tts.openai`.

STT: **pendente**. O `openvino-whisper` (`:20130`) ainda nao expoe
`/v1/audio/transcriptions` estilo OpenAI (`/v1/models` responde `not_found`).
Quando expuser, e so acrescentar `speech.stt.openai.url` no `librechat.yaml`.

## Tailscale (passo do Humano -- precisa de sudo e login da conta)

O Tailscale nao esta instalado nesta maquina. Para acesso remoto:

```
sudo pacman -S tailscale
sudo systemctl enable --now tailscaled
sudo tailscale up
sudo tailscale set --operator=orusoua      # deixa o `tailscale serve` rodar sem sudo depois
tailscale serve --bg 3080                   # publica http://<nome-magicdns>. so no tailnet.
```

Depois: em `~/librechat/.env` trocar `DOMAIN_CLIENT` e `DOMAIN_SERVER` para
`https://<nome-magicdns>.<tailnet>.ts.net` e por `TRUST_PROXY=1`; recriar a app
(`docker compose -f ~/librechat/docker-compose.yml up -d --force-recreate librechat`).
**Nao** usar `tailscale funnel` (isso expoe pra internet).

## MCP

### canon (memoria local -- LIGADO)

`canon-mcp.mjs` -- servidor MCP stdio, zero dependencias (so `fetch` do Node,
que o container ja tem). Le o vault do Agata pelo proxy read-only `:27125`
(`obsidian-ro-proxy`, que injeta o bearer e bloqueia escrita).

- Runtime: `~/librechat/data/mcp/canon-mcp.mjs` (montado em `/app/data/mcp/`).
- Fonte versionada: `redesign/librechat/canon-mcp.mjs`.
- `librechat.yaml` -> `mcpServers.canon`, `startup: true` (excecao consciente a
  regra do "sob demanda": e read-only, ~40 MB, e a espinha da hidratacao -- a
  Seth precisa da tool ja na proxima mensagem, nao depois de um toggle na UI).
- Tools:
  - `query_canon { doc, grep?, contexto?, linhas? }` -- le REGRAS/PROJETO/MEMORIAS/
    ONDE_ESTAMOS/CHAVES/PROJETO_REFERENCIA/ROADMAP/PROMPT_CARREGAMENTO/INDICE_MEMORIAS
    direto da fonte. MEMORIAS sem grep/linhas devolve so a janela do topo.
  - `vault_consultar { caminho? }` -- le ou lista uma nota derivada sob
    `memoria/obsidian/` (estado, timeline, moc-*, entradas/, regras/, controles/).
- Trava: whitelist (so os docs nomeados + `memoria/obsidian/**`) + denylist de
  sufixos de segredo (`.secret .token .pass .key .gpg .env .pem`) + sem `..`.
- Editou o `.mjs` ou o bloco? `docker compose -f ~/librechat/docker-compose.yml restart librechat`.
- Nota: `auto/*` que roteia p/ modelo sem function-calling nao usa a tool naquele
  turno -- prefira `auto/chat` / `auto/claude-sonnet` p/ turnos que consultam canon.

### integracoes futuras (sob demanda)

browser-use -> Brave, Home Assistant, pontes Discord/WhatsApp: cada uma entra
como bloco em `librechat.yaml` -> `mcpServers`, com `startup: false` (so
inicializa quando o modelo pedir). Transporte recomendado: Streamable HTTP.
Ver o desenho da arquitetura da Seth.
