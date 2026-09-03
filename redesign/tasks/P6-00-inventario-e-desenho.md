# P6-00 — inventário Obsidian + desenho da superfície de leitura

**Status:** ✅ **FEITO — 2026-09-02 ~19:00 (relógio da máquina).** `redesign/obsidian/
INVENTARIO.md`: Obsidian = flatpak 1.13.7 (instalado); vault `memoria/obsidian/` gitignorado,
regenerado (apaga+reescreve) no post-commit; plugin não instalado. **Conflito achado:** o
`.obsidian/` do plugin não pode morar dentro de `memoria/obsidian/` → vault root = `~/agata`.
4 invariantes fixados. Ver `LOG.md`.

**Objetivo:** saber o estado do Obsidian e do vault derivado, e fixar o desenho da Fase 6
(MCP de leitura + recuperação índice-primeiro + consolidação como flow), respeitando os
invariantes.

**Pré-requisitos:** Fase 5 FECHADA. "vai" da Fase 6.

**Arquivos:** `redesign/obsidian/INVENTARIO.md` (novo) · este arquivo-tarefa.

Só leitura. Nada instalado, nada de systemd.

---

## Inventário (2026-09-02)

- **Obsidian:** flatpak `md.obsidian.Obsidian 1.13.7` (flathub), config em
  `~/.var/app/md.obsidian.Obsidian/`. **Já instalado.**
- **`obsidian-local-rest-api`** (github.com/coddingtonbear/obsidian-local-rest-api): plugin
  da comunidade, serve **MCP nativo** em `https://127.0.0.1:27124/mcp/` desde jul/2026,
  bearer token. Não instalado ainda.
- **Vault derivado `memoria/obsidian/`:** 438 arquivos, gerado pelo `scripts/gerar_obsidian.py`
  no `post-commit` (P-10 confere byte a byte contra HEAD). Estrutura: `canon/`, `entradas/`,
  `controles/`, MOCs (`moc-*.md`), `INICIO.md`, `_LEIA.md`, `estado.md`. É **derivado** — a
  fonte é o canon; editar o vault à mão é o que a P-10 pega.

## Invariantes da Fase 6 (do ROADMAP / E1)

1. **Read-only para modelos.** A geração (canon → `gerar_obsidian.py`) é dona da escrita. O
   MCP serve **consulta**, nunca escrita.
2. **O loop local continua lendo os `.md` direto do disco** — não depende do Obsidian estar
   aberto nem do plugin. O MCP é uma *superfície adicional*, não a única via.
3. **Zero vector DB.** Recuperação índice-primeiro: devolve refs rastreáveis (nº de entrada
   + arquivo + linha), não um vetor nem um "resultado semântico" opaco. (O `multilingual-e5-small`
   da P2-03 existe, mas a Fase 6 **não** o transforma num índice vetorial — invariante.)
4. **MCP é stateless** (spec 2026-07-28, E1). Nenhum estado de autorização/continuidade mora
   numa sessão MCP — mora no cliente / no grafo / no store local. O token bearer é config
   local, não sessão.

## Desenho das tarefas

- **P6-01** — instalar + configurar o plugin: vault apontando para `memoria/obsidian/`,
  bearer token num store local (fora do git, como o `restic.pass`), serviço em
  `:27124/mcp/`. **INSTALA SOFTWARE** (plugin) + serviço de rede novo → pede o "vai".
- **P6-02** — recuperação índice-primeiro: um cliente/ferramenta que consulta o vault via
  `:27124/mcp/` **e** por leitura direta de disco (fallback), devolvendo refs rastreáveis
  (`(NNN)` + arquivo + linha). Zero vector DB. Reusa `query_canon` (P4-02) como o motor de
  busca; o MCP é a superfície.
- **P6-03** — consolidação noturna como flow do grafo (Fase 4): `orientar → juntar →
  consolidar → podar`, escrevendo **proposta** em `propostas/` (nunca canon direto, como a
  `agata-consolidacao.service` já faz). Reusa o `grafo.py` + o portão.

## Aceite (P6-00)

- `redesign/obsidian/INVENTARIO.md` responde: Obsidian instalado? vault onde e como gerado?
  os 4 invariantes; o desenho de P6-01..P6-03.
- Nada instalado.

## Registro

- `STATUS.md`: P6-00 → "Feito".
- `LOG.md`: o inventário + o desenho; próximo = P6-01 (pede "vai" — instala plugin).
