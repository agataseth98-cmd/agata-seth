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
