# LibreChat -- lane de conversa da Seth

Substituiu o Open WebUI em 03/09/2026 (MEMORIAS (313)). Frontend de conversa
informal, "estilo ChatGPT/Claude", apontado no `seth_gateway` (`:20126`).
Para agente/codigo continua o Goose (`seth-agente`).

## Fork Agata

O container da Agata é uma derivação versionada da imagem v0.8.8-rc3, fixada
por digest no `Dockerfile`. O patch em `fork/agata-capabilities.patch` se aplica
ao commit upstream `1df448481075d37484f11c4751dc3f60314ee651`; o build falha se o
patch não casar com a imagem-base. Ele instala o emissor no caminho real de
aprovação/resume e injeta a capability somente na chamada MCP executada. O teste
Node cobre emissão, rejeição, edição de argumentos e colisão de IDs por conversa.
O build ainda não foi aplicado à instância em execução.

## Forma (espelhos do sistema)

- **Enxuto**: três serviços da aplicação/dados (`librechat`, Mongo, Meili) e um relay `socat` mínimo em host networking.
- **SEM RAG por embedding**: `rag_api` e `pgvector` nao sao implantados. Respeita
  MEMORIAS (115)/(293) (busca semantica recusada; canon e grep + link por numero).
- **Memoria desligada** (`memory.disabled: true`): a hidratacao da Seth vem do
  `seth_gateway`, que injeta canon-em-git verificavel. Nada de auto-captura por LLM
  (MEMORIAS (312)).
- **Recuperação**: `restart: unless-stopped` nos contêineres; o atalho `Parar Seth` para manualmente e deixa-os parados.
- **Loopback**: a app faz bind em `127.0.0.1:3080`. Acesso remoto e via Tailscale
  serve (nao expor porta).
- **Um endpoint** ("Seth") -> `http://127.0.0.1:20126/v1` (seth_gateway ->
  sanitizador -> OmniRoute). `ENDPOINTS=custom` esconde os embutidos.
- **Dados externos**: o proxy bloqueia qualquer POST sem classificação `public`, em
  todos os caminhos e tipos de conteúdo. Na UI, `Seth pública · sem ferramentas` é
  um endpoint custom dedicado com cabeçalho público fixo; as rotas cloud do Agent
  comum continuam bloqueadas. O alias local `ollama-local/*` segue local.
  Chamadores HTTP diretos podem declarar `X-Agata-Data-Classification: public`.

## Layout

| Onde | O que |
|---|---|
| `~/librechat/` | runtime -- `.env` (segredos, 600), `librechat.yaml`, `docker-compose.yml`, `data/ images/ uploads/ logs/`, `PRIMEIRO-ACESSO.txt` |
| `~/agata/redesign/librechat/` | **fonte versionada** -- copias de `docker-compose.yml` e `librechat.yaml`, `env.exemplo` (placeholders), este README |
| `~/librechat/.env` | segredos reais: `CREDS_KEY`, `CREDS_IV`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `MEILI_MASTER_KEY`. Ver `CHAVES.md`. |

Editou `~/librechat/librechat.yaml` ou o compose? Copie a versao sem-segredo para
`redesign/librechat/` e commite.

## Rede

Desde MEMÓRIAS (538) (B8 / ISO-05) a app NAO usa `network_mode: host`: fica na
bridge `librechat` (172.29.7.0/24, interface `br-librechat`) e publica so
`127.0.0.1:3080`. Para falar com a Maquina, passa pelo `librechat-ponte-host`
(socat em modo host) que repassa SO 7 portas a partir de `172.29.7.1`: 20126
seth_gateway · 8890 piper · 27125 canon · 20135 discord · 20136 navegador ·
20140 escriba · 20141 verificador. O ufw da Maquina precisa liberar essas 7
portas na `br-librechat` (regra instalada com sudo, uma vez). Porta nova =
compose + `librechat.yaml` + regra do ufw, juntos. Mongo e Meili: pelo nome do
serviço, na rede interna `librechat-data` (172.29.8.0/24), sem rota para o
relé. A aplicação entra nas duas redes: alcança as ferramentas pela bridge
`librechat` e os bancos pela rede de dados. Os bancos não compartilham a bridge
que alcança as portas de ferramentas.

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
  --eval 'db.users.updateOne({email:"SEU-EMAIL-DE-LOGIN@dominio.com"},{$set:{password:"'"$HASH"'"}})'
```

## Voz

TTS pelo `piper-tts.service` (`:8890`, pt-BR local, shim OpenAI-compat stdlib, MEMÓRIAS (387)).
Configurado em `librechat.yaml` -> `speech.tts.openai`. Documentação corrigida 27/09/2026
(MEMÓRIAS (593)) -- este texto ainda descrevia o `kokoro-tts` (removido), desatualizado desde
a troca pro Piper.

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
- Tools de LEITURA:
  - `query_canon { doc, grep?, contexto?, linhas? }` -- le REGRAS/PROJETO/MEMORIAS/
    ONDE_ESTAMOS/CHAVES/PROJETO_REFERENCIA/ROADMAP/PROMPT_CARREGAMENTO/INDICE_MEMORIAS
    direto da fonte. MEMORIAS sem grep/linhas devolve so a janela do topo.
  - `vault_consultar { caminho? }` -- le ou lista uma nota derivada sob
    `memoria/obsidian/` (estado, timeline, moc-*, entradas/, regras/, controles/),
    ou `SETH-DIARIO.md`.
- Tools de ESCRITA (APPEND-ONLY -- nunca apagam, ver seth_escriba abaixo):
  - `memoria_acrescentar { titulo, corpo }` -- insere uma entrada nova em
    MEMORIAS.md logo abaixo do marcador ENTRADAS-NOVAS. (NNN) e data sao da
    Maquina. NAO commita -- fica no working tree.
  - `diario_anotar { texto }` -- anexa ao fim de SETH-DIARIO.md.
- Trava de leitura: whitelist (docs nomeados + `memoria/obsidian/**` + `SETH-DIARIO.md`)
  + denylist de sufixos de segredo (`.secret .token .pass .key .gpg .env .pem`) + sem `..`.
- `SETH_ESCRIBA` (default `http://127.0.0.1:20140`) -- onde as tools de escrita batem.
Cada escrita exige uma capability Ed25519 de uso único, emitida após aprovação
humana no LibreChat e vinculada ao executor, à ferramenta e aos argumentos.
A chave privada (`~/.config/agata/approval-capability-private.pem`) fica no host
como `root:59999`, modo 0440, e é montada somente no container emissor, como
`/run/secrets/agata-approval-private.pem`, em leitura. O container usa UID
1000/GID 59999; o emissor também valida owner root, GID, modo, tipo e link único.
Depois de criar o par, o Humano deve executar:

```sh
sudo chown root:59999 ~/.config/agata/approval-capability-private.pem
sudo chmod 0440 ~/.config/agata/approval-capability-private.pem
```

Os executores locais recebem só a chave pública
(`approval-capability-public.pem`) e consomem cada nonce no banco local
`~/.cache/agata/approval-capabilities/used.sqlite3`; esse banco não é montado no
container do LibreChat. O UID/GID numérico do container é 1000:59999 nesta
Máquina. `python3
scripts/criar_chave_capability.py` cria o par sem exibir conteúdo. Sem token
válido, Escriba, Discord e ações de escrita do navegador recusam chamadas diretas.
Esta barreira não protege contra processos com acesso ao daemon Docker (o usuário
local pertence ao grupo `docker`); esse principal pode inspecionar o container e
ler a chave. A eficácia em runtime depende da homologação controlada.

**Uso obrigatorio pela Seth:** a tool `query_canon` SO FUNCIONA pela lane de **agente
SALVO** ("Seth", endpoint `agents`) com **`disableStreaming: true`** nos parametros do
modelo. Pelo agente efemero (endpoint + modelo + MCP no menu "+") a tool volta "Cancelado"
— bug de parser de stream: os `arguments` da tool-call chegam no mesmo chunk SSE que o
`finish_reason`, e o LibreChat v0.8.7 descarta esse chunk ao fechar a tool. Ver
MEMORIAS (316).

### seth_escriba (:20140) -- canal de escrita append-only da Seth

`redesign/router/seth_escriba.py`, unit `seth-escriba.service` (sob demanda,
sobe pelo atalho `seth` junto do gateway). O UNICO caminho de escrita da Seth,
e so acrescenta:

- `POST /memoria {titulo, corpo}` -- insere bloco novo em MEMORIAS.md abaixo do
  marcador. Verificacao byte a byte pos-escrita: `depois` == `antes` com
  exatamente um bloco inserido no offset do marcador; qualquer outra diferenca
  -> 409, nao grava. (NNN) e data do relogio da Maquina.
- `POST /diario {texto}` -- append puro ao fim de SETH-DIARIO.md; verifica que
  `antes` e' prefixo exato de `depois`.
- SEM PUT/PATCH/DELETE (405). Nao commita, nao faz `git add`. O Humano revisa
  com `git diff` e commita (ou descarta com `git checkout`).

Autorizado pelo Humano em 03/09/2026 ("corte os acessos dela, menos a memoria e
obsidian; append only... assumo o risco") depois de duas tentativas da
Seth-com-tools-de-leitura confabularem a saida (pegas pela camada C).
`SETH-DIARIO.md` fica na raiz do repo, tracked, NAO derivado, fora do P-10.
- Editou o `.mjs` ou o bloco? `docker compose -f ~/librechat/docker-compose.yml restart librechat`.
- Nota: `auto/*` que roteia p/ modelo sem function-calling nao usa a tool naquele
  turno -- prefira `auto/chat` / `auto/claude-sonnet` p/ turnos que consultam canon.

### integracoes futuras (sob demanda)

browser-use -> Brave, Home Assistant, pontes Discord/WhatsApp: cada uma entra
como bloco em `librechat.yaml` -> `mcpServers`, com `startup: false` (so
inicializa quando o modelo pedir). Transporte recomendado: Streamable HTTP.
Ver o desenho da arquitetura da Seth.

## (670) Tema da Agata e `vault_buscar`

- **Tema:** `agata-tema.css` (paleta de `config/agata-identidade.json`) montado em `/app/client/dist/assets/`; o `command` do serviço no `docker-compose.yml` põe o `<link>` no `index.html` antes de subir (idempotente) — o LibreChat v0.8.8 ainda não lê `interface.theme`. Aplicar: copiar `docker-compose.yml` e `agata-tema.css` para `~/librechat/` e `docker compose up -d librechat`. Navegador aberto: Ctrl+Shift+R uma vez (o service worker guarda o shell antigo).
- **`vault_buscar`** (canon-mcp): busca por sentido e por texto no vault, via `seth_verificador` (`busca_semantica`, `busca_texto`). Prioridade 1 para achar; `query_canon` confirma antes de citar.
