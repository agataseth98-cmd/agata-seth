# redesign/ — espinha de produção do sistema local Agata

**Este código está em `main` e É produção.** O redesenho (Fases 0–8) foi
mergeado em `main` em 03/09/2026 — MEMÓRIAS (310)/(311). O nome do diretório
é histórico; o conteúdo, não.

## Governança: os gates VALEM aqui (isto mudou)

Versões antigas deste README diziam que os gates estavam suspensos "no branch
`redesign`". **Não estão mais** — depois do merge em `main`, tudo aqui segue o
regime normal:

- **Quarentena P-8** cobre `redesign/router/*`, `redesign/mcp/*`,
  `redesign/librechat/*.mjs|*.yaml|*.yml`, `redesign/grafo/*.py|*.sh`,
  `redesign/systemd/*` (ver `scripts/perimetro.sh`, `_p8_eh_comportamento`).
  Mudar qualquer um exige `propostas/<nome>.diff` + `propostas/APROVADO-<nome>`
  assinado.
- Invariantes universais valem sem exceção: MEMÓRIAS nunca se reescreve
  (Regra 4); nada de `push --force`/`reset --hard` em `main`; segredo nunca
  sai; comando destrutivo mostrado sozinho.

## O que vive aqui

| Subdir | O que é | Serviço / ponto de entrada |
|---|---|---|
| `router/` | `seth_gateway.py` (hidratação da Seth), `sanitizar.py`/`proxy.py` (scrub de egresso), `seth_escriba.py` | `:20126` seth-gateway · `:20127` sanitizador · seth-escriba |
| `grafo/` | LangGraph da consolidação noturna (`flows/consolidacao.py`), `drenar.py`, sandbox, envelope | `agata-consolidacao.timer` · `agata-drain.service` |
| `librechat/` | `librechat.yaml` (config da Seth), `canon-mcp.mjs` (MCP read-only do vault), `docker-compose.yml` | LibreChat (runtime em `~/librechat/`) |
| `mcp/` | servidores MCP: `discord/servidor.py` (`:20135`), `navegador/servidor.py` (`:20136`) | discord-mcp · navegador-mcp |
| `igpu/` | `embeddings_server.py`, `whisper_server.py` (OpenVINO na iGPU Intel) | openvino-embeddings · openvino-whisper |
| `obsidian/` | `ro_proxy.py` (`:27125`, vault read-only), `consulta.py` | obsidian-ro-proxy.service |
| `systemd/` | **fonte** das units instaladas em `~/.config/systemd/user/` | — |
| `fase7-hd/` | `hash_ir.sh`, `semear_cache_p12.py` — régua do P-12 (backup restic verificável) | usado por `perimetro.sh` P-12 |
| `LOG.md` | histórico append-only do redesenho — **fica aqui** porque PROJETO.md e MEMÓRIAS.md citam este caminho (MEMÓRIAS não se edita) | — |
| `ACESSO-GRADUADO.md` | método de acesso graduado (R0–R3) — **fica aqui** porque `librechat/canon-mcp.mjs` (dict `CANON`, quarentena P-8) aponta pra este caminho | — |
| `propostas/` | os pares `.diff`/`APROVADO-` das Fases 0–8 | — |

## Docs de planejamento — arquivados

Os documentos de planejamento das fases (`ROADMAP`, `STATUS`, `PESQUISA`,
`CONTINUIDADE`, `CLAUDE-NA-MAQUINA`, `ANCORA`, `CANON-DELTA`, `OTIMIZACOES`,
`SILO-HUMANO`) cumpriram o papel e viraram história — movidos para
`extras/arquivo-redesign/` (MEMÓRIAS (385)). O que aconteceu de fato está nas
entradas de MEMÓRIAS que citam cada fase e em `LOG.md`. `ACESSO-GRADUADO.md`
ficou por causa da ref quarentenada em `canon-mcp.mjs` — vai junto quando essa
ref for corrigida (B6).

## Mudança futura registrada (backlog B6)

Promover as pastas de código para fora de `redesign/` (nome permanente, ex.
`runtime/` ou raiz), para coerência e rastreabilidade — "redesign" descreve um
processo terminado, não o que o código É. É migração grande: toca ~10 units
systemd (fonte + instaladas, com caminho de `.venv` no `ExecStart`),
`perimetro.sh` (padrões P-8 + lista P-9), `scripts/gerar_obsidian.py` (lista
hard-coded), `PROJETO.md` (18 refs), `config/modelos-gratuitos.md`. Precisa de
plano faseado próprio + aprovação assinada por peça. Ver `propostas/backlog.md`.
