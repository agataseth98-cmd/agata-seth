# P6-01 — instalar/configurar `obsidian-local-rest-api` + subir `:27124/mcp/`

**Status:** ⏳ **PENDE do "vai" do Humano** — INSTALA SOFTWARE (plugin `obsidian-local-rest-api`)
+ serviço de rede novo (`:27124/mcp/`). P6-00 fez o inventário e o desenho.

**Objetivo:** o vault derivado `memoria/obsidian/` servido por MCP nativo em
`https://127.0.0.1:27124/mcp/`, bearer token em store local, **read-only**.

**Pré-requisitos:** P6-00 FEITO. Obsidian instalado (flatpak, confirmado).

> **INSTALA SOFTWARE (plugin da comunidade) + serviço de rede novo.** Pede o "vai" do
> Humano. Revisão de plano antes. Sem `sudo` (plugin é userspace), mas é instalação.

**Arquivos:**
- config do plugin em `~/.var/app/md.obsidian.Obsidian/config/` (fora do git)
- token em `~/.config/agata/obsidian.token` (chmod 600, **fora do git**)
- `~/.config/systemd/user/obsidian-headless.service` (novo) — só se rodar o Obsidian headless
- `redesign/obsidian/PLUGIN.md` (novo) — o que foi instalado, como reverter
- `redesign/tasks/P6-01-*.md`

---

## Passos

### 1. Abrir o vault no Obsidian

O vault é **`~/agata/memoria/`** (INVENTARIO P6-00, "Solução"). O `.obsidian/` fica em
`~/agata/memoria/.obsidian/` — fora de `memoria/obsidian/` (que o `gerar_obsidian.py` apaga
e reescreve). **Acrescentar ao `.gitignore`:** `memoria/.obsidian/` (plugin + config = estado
local, nunca canon). **Não** abrir a raiz do repo como vault — faz o Obsidian largar `.md`
vazios na raiz (MEMÓRIAS (293)/(294)). O MCP serve o subtree `memoria/obsidian/`.

### 2. Instalar `obsidian-local-rest-api`

- Community plugins → procurar "Local REST API" (coddingtonbear) → instalar → habilitar.
- OU via BRAT / cópia manual do release em `memoria/.obsidian/plugins/`.
- **Confirmar a versão com MCP nativo** (≥ jul/2026 — serve `/mcp/`).

### 3. Configurar

- Bind **`127.0.0.1`** (nunca `0.0.0.0`). HTTPS na `27124` (o plugin gera cert self-signed).
- **Read-only:** desabilitar os endpoints de escrita (`PUT`/`POST`/`PATCH`/`DELETE` de
  arquivo). Se o plugin não separar, documentar que o token só é dado a clientes de leitura
  e o `gerar_obsidian.py` é a única via de escrita (a P-10 é o backstop).
- Token: gerar (`openssl rand -hex 32`), pôr em `~/.config/agata/obsidian.token` (chmod
  600), e no config do plugin. **Nunca no git, nunca no chat.**

### 4. Subir

- Se o Obsidian roda como app GUI: o plugin sobe junto. Boot = Fase 7.
- Se precisar headless: `obsidian-headless.service` (`flatpak run ... --headless` se
  suportar, senão xvfb). **Sem `enable`.**
- Teste: `curl -sk -H "Authorization: Bearer $(cat ~/.config/agata/obsidian.token)"
  https://127.0.0.1:27124/` → 200; `.../mcp/` responde ao handshake MCP.

### 5. `PLUGIN.md`

Registrar: versão do plugin, o que ficou habilitado/desabilitado, o caminho do token, o
comando de reversão (desabilitar plugin + `rm` do config).

---

## Aceite

- `curl` autenticado em `https://127.0.0.1:27124/` → 200; `/mcp/` faz handshake.
- Bind `127.0.0.1` (`ss -tlnp | grep 27124`).
- Endpoints de escrita **desabilitados** ou o token de leitura documentado como a única via.
- Token em `~/.config/agata/obsidian.token` (chmod 600), **não** no git (`git check-ignore` / `git status`).
- Plugin **não** habilitado no boot (Fase 7).

## Verificação independente

- **Quem:** Humano. **O quê:** que o serviço é loopback, que nenhum cliente com token pode
  escrever no vault (tentar um `PUT` → 403/405), que o token não vazou pro git/chat.
- **Como:** `curl` de escrita → negado; `git log -p` sem o token; `ss` mostra `127.0.0.1`.
- **Resultado:** no LOG.

## Rollback

Não destrutivo:
```fish
# Obsidian: desabilitar o plugin "Local REST API"
rm -rf ~/agata/memoria/obsidian/.obsidian/plugins/obsidian-local-rest-api
systemctl --user disable --now obsidian-headless.service 2>/dev/null; or true
rm -f ~/.config/systemd/user/obsidian-headless.service ~/.config/agata/obsidian.token
git checkout -- redesign/obsidian
```

## Registro

- `STATUS.md`: P6-01 → "Feito"; a versão do plugin, o bind, read-only sim/não.
- `LOG.md`: o `curl` autenticado, o teste de escrita negada, o `ss`, `HEAD`.
