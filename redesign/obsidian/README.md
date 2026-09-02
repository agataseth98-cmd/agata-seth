# redesign/obsidian/ — superfície de leitura do vault (Fase 6)

**Não é canon.** Branch `redesign`.

## Estado (2026-09-02)

| tarefa | estado |
|---|---|
| **P6-00** inventário | ✅ `INVENTARIO.md` |
| **P6-01** plugin + proxy read-only | ✅ `obsidian-local-rest-api` 5.1.0 (`:27124`) + `ro_proxy.py` (`:27125`) — ver `PLUGIN.md` |
| **P6-02** recuperação índice-primeiro | ✅ `consulta.py` |
| P6-03 consolidação como flow | ⏳ |

## Arquitetura

```
loop / P6-02 / sessões  →  :27125  (ro_proxy.py, SÓ leitura, injeta o token)
                             │
                             ▼
                           :27124  (plugin obsidian-local-rest-api, dentro do Obsidian)
                             │  serve o vault ~/agata (subtree memoria/obsidian/)
                             ▼
                        MEMÓRIAS.md / REGRAS.md / PROJETO.md / memoria/obsidian/*
```

- **`:27124`** — plugin, HTTPS loopback, bearer token (`~/.config/agata/obsidian.token`).
  Roda quando o Obsidian está aberto. Boot/headless = **Fase 7**.
- **`:27125`** — `ro_proxy.py`. `GET`/`HEAD`/`OPTIONS` repassam; `POST /mcp/` só métodos de
  leitura ou `tools/call` não-escrita; `POST /search/…` (FTS, leitura) repassa;
  `PUT`/`PATCH`/`DELETE`/`/commands/` → **403**. Injeta o token — clientes do `:27125` não
  precisam do segredo. `obsidian-ro-proxy.service` (`systemd --user`, sem `enable`).

## `consulta.py` — P6-02 (índice-primeiro, zero vector DB)

`consultar(termos, via="ambos"|"canon"|"mcp")` — duas vias, **mesmo formato de hit**
`{ref, arquivo, offset|linha, trecho}`:

- **`query_canon`** (P4-02, PRIMÁRIA — o loop não depende do Obsidian): o índice derivado.
  MEMÓRIAS vem como título com `(NNN)`; REGRAS/PROJETO como seção (`arquivo › seção`).
- **MCP/FTS** (SECUNDÁRIA, pelo `:27125/search/simple/`): busca de texto completa em todo o
  vault, filtrada para canon + `memoria/obsidian/`. `ref` derivada de `entradas/NNNN.md`.
- `score` do plugin = BM25 de texto (só ordena). **Nenhum vetor, nenhum store** —
  `_sem_vector_db()` confirma que faiss/chroma/qdrant/etc. não estão carregados;
  `pip list` do venv idem.

### Verificação (aceite P6-02) — 5 consultas com gabarito no canon

| termos | `query_canon` | MCP/FTS | refs em comum |
|---|---|---|---|
| `presence_penalty` | `(151)–(154)` | `(151)–(154)` + `(135)(172)` | **`(151)(152)(153)(154)`** ✓ |
| `TES-002 nonce` | REGRAS §§ + `(70)(89)(90)` | 114 hits, refs `(104)…` + `(70)(89)(90)` | **`(70)(89)(90)`** ✓ |
| `16814` | PROJETO §§ Cérebro / bugs | `(133)(134)(179)(180)…` | — (complementares) |
| `context_file_max_chars` | PROJETO § Memória e hidratação | `(103)(104)(106)(107)(304)` | — (complementares) |
| `api_server 8642` | PROJETO §§ Serviços / Segurança | `(121)(126)(142)(181)…` | — (complementares) |

**Convergência é parcial e esperada:** `query_canon` é **seção/título** sobre o índice
derivado; o FTS do plugin é **texto completo** de cada arquivo. Onde indexam a mesma
granularidade, batem. Onde não, são **complementares** — `query_canon` aponta a seção do
PROJETO.md onde o valor *está*; o FTS aponta as entradas de MEMÓRIAS que o *discutem*. Todo
hit dos dois carrega uma ref checável (`(NNN)` ou `arquivo › seção`). **Zero vector DB.**

## Rollback

Ver `PLUGIN.md` (plugin + proxy). `git checkout -- redesign/obsidian`.
