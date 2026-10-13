# redesign/obsidian/PLUGIN.md — o que o P6-01 instalou

**Não é canon.** Branch `redesign`, Fase 6. 2026-09-02.

## Instalado

- **Plugin `obsidian-local-rest-api` v5.1.0** ("Local REST API with MCP", Adam Coddington),
  em `~/agata/.obsidian/plugins/obsidian-local-rest-api/` (`main.js` + `manifest.json` +
  `styles.css`, baixados do release do GitHub). **Gitignorado** (`.gitignore`:
  `.obsidian/plugins/`, `.obsidian/community-plugins.json`, `.obsidian/**/data.json`).
- Habilitado em `~/agata/.obsidian/community-plugins.json` (`["obsidian-local-rest-api"]`).
- **Vault:** `~/agata` (o vault que o Humano já tinha registrado; `obsidian.json` do
  flatpak). O MCP serve o subtree `memoria/obsidian/`.

## Config do plugin (`~/agata/.obsidian/plugins/obsidian-local-rest-api/data.json`)

```json
{
  "bindingHost": "127.0.0.1",   // NUNCA 0.0.0.0
  "port": 27124,                 // HTTPS (cert self-signed gerado pelo plugin)
  "enableSecureServer": true,
  "enableInsecureServer": false, // sem HTTP
  "subjectAltNames": "127.0.0.1"
}
```
- `apiKey` (64 hex) e `crypto` (cert) foram gerados pelo plugin no 1º start. O `apiKey`
  está copiado em **`~/.config/agata/obsidian.token`** (chmod 600, fora do repo, nunca no
  chat). O `data.json` também contém o `apiKey` — por isso é **gitignorado**.

## Read-only — a trava (o plugin 5.1.0 não tem toggle global)

Confirmado no `main.js`: só anotações `readOnlyHint` por tool MCP, sem "disable all writes".
Teste ao vivo: `PUT /vault/...` com o token → **HTTP 204, arquivo criado**. Então:

**`redesign/obsidian/ro_proxy.py` — proxy read-only em `127.0.0.1:27125`:**

```
cliente  →  :27125 (ro_proxy, SÓ leitura, sem token)  →  :27124 (plugin, token injetado)
```

- `GET`/`HEAD`/`OPTIONS` → repassa.
- `POST /mcp/` → repassa só se o JSON-RPC for método de leitura (`initialize`, `tools/list`,
  `resources/read`, …) **ou** `tools/call` cujo `name` não contém
  `put|patch|append|delete|post|create|write|execute|command|move|rename|trash|insert|replace`.
- `PUT`/`PATCH`/`DELETE` → **403**. `/commands/` (executa comando do Obsidian) → **403**.
- Injeta o Bearer do `:27124` — **o cliente do `:27125` não precisa do segredo**.

`obsidian-ro-proxy.service` (`systemd --user`, **sem `enable`** — boot é Fase 7).
`ro_proxy.py --selftest`: GET 200 · PUT 403 · MCP-write 403 → **OK**.

**Regra:** clientes (P6-02, o loop, sessões) usam **`:27125`**. `:27124` fica atrás do
proxy. `gerar_obsidian.py` continua a única via de escrita no vault; **P-10** é o backstop
(pega edição à mão).

## Como sobe

- **`:27124`:** o plugin roda dentro do Obsidian → sobe quando o Obsidian está aberto
  (`flatpak run md.obsidian.Obsidian ~/agata`). Boot-persistente / headless = **Fase 7**.
- **`:27125`:** `systemctl --user start obsidian-ro-proxy.service` (feito; sem `enable`).

## Verificação (aceite P6-01)

| critério | resultado |
|---|---|
| `curl` autenticado em `https://127.0.0.1:27124/` → 200 | ✅ `{"status":"OK","authenticated":true}` |
| sem token → 401 | ✅ |
| `/mcp/` handshake | ✅ `initialize` → `serverInfo`, protocol `2025-11-25` |
| bind `127.0.0.1` | ✅ `ss`: `127.0.0.1:27124` e `127.0.0.1:27125` |
| escrita negada **na superfície de cliente** (`:27125`) | ✅ `PUT` → 403, `/commands/` → 403, MCP write-tool → 403; arquivo não criado |
| token em `~/.config/agata/obsidian.token` chmod 600, **fora do git** | ✅ (`.obsidian/**/data.json` gitignorado; `git grep` do prefixo do token = vazio) |
| plugin **não** habilitado no boot | ✅ (Fase 7); `obsidian-ro-proxy.service` `disabled` |

## Rollback

```fish
systemctl --user stop obsidian-ro-proxy.service
rm -f ~/.config/systemd/user/obsidian-ro-proxy.service
systemctl --user daemon-reload
# Obsidian: desabilitar/remover o plugin
rm -rf ~/agata/.obsidian/plugins/obsidian-local-rest-api
printf '[]' > ~/agata/.obsidian/community-plugins.json
rm -f ~/.config/agata/obsidian.token
git checkout -- redesign/obsidian .gitignore
```

## Cérebro — Brain Atlas (MEMÓRIAS (670))

Segundo plugin de comunidade, pedido do Humano em 13/10/2026 ("gráfico em 3D com visual inspirado no cérebro humano"). Escolha dele entre Brain Atlas e Brain Graph.

| item | valor |
|---|---|
| plugin | `colorpulse6/brain-atlas` **0.2.2** (MIT), versão fixa |
| sha256 `main.js` | `9b137a59e6088ceab2af1d432da2abdfb1be0b37ee0007a087b793b11543de88` |
| sha256 `manifest.json` | `ef837563693ec9d742d872469bb01f6f50f9f86a9d3462a0596ca0a0923ee27a` |
| sha256 `styles.css` | `ab63af3bacb08a58159c9b0a91a7db3e16facad205eb94ff6b1b712b71908543` |
| origem | atestação do GitHub conferida (`gh attestation verify`) |
| rede | nenhuma: `main.js` sem `fetch`/`XMLHttpRequest`/`WebSocket`/`requestUrl`; lê só metadados (caminho, propriedades, tags, links) |
| instala | `bash redesign/obsidian/instalar_cerebro.sh` (confere tudo de novo; `--conferir` só confere) |
| configuração | `redesign/obsidian/brain-atlas.json` → `.obsidian/plugins/brain-atlas/data.json` (preserva neurônios fixados) |

**Regiões:** o gerador do vault escreve `brain_region` e `kind` em cada nota (`config/agata-identidade.json`): memória → temporal, decisão → frontal, ferramentas → parietal, correção → cerebelo, o que vem de fora → occipital, roteamento → tronco. **Cores:** o plugin só tem paletas prontas; "Aurora" é a mais próxima da identidade da Agata, e o `kind` escolhe dentro dela o tom de cada região. Cor exata da Agata vai no tema do Obsidian (`.obsidian/snippets/agata.css`) e nos grupos de cor do grafo 2D.

**Recusados (estado da arte medido, out/2026):** InfraNodus (manda o texto para servidores deles e para a OpenAI); Smart Connections (duplica o embedding local que já existe e grava cache dentro do repo — os recursos dele vêm do nosso índice: `parecidas`, trechos `#^bN`, `scripts/agata_busca.sh`).

**Rollback:** `rm -rf ~/agata/.obsidian/plugins/brain-atlas` e tirar `"brain-atlas"` de `.obsidian/community-plugins.json`.
