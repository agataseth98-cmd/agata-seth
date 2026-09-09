# Plano — reorg do código de `redesign/` pra um lar permanente (B6)

> **Não é canon. Rascunho pra decisão do Humano antes de qualquer `.diff`.**
> REGRAS, "Mudança estrutural": item grande em PROJETO/scripts exige **segunda
> opinião de outro modelo OU o Humano assumir o risco por escrito** antes de
> tocar canon. Este plano é pra revisão; nada foi movido.
>
> Origem: `propostas/backlog.md` B6, ordem do Humano 08/09/2026 — "'redesign'
> descreve um processo terminado, não o que o código É; mover melhora coerência,
> rastreabilidade e compreensão".

---

## 1. O que move

`redesign/{grafo, router, librechat, mcp, igpu, obsidian, systemd, fase7-hd}` +
os soltos `redesign/{ACESSO-GRADUADO.md, LOG.md, README.md}` e
`redesign/propostas/` (2 arquivos).

**Decisão pendente do Humano — nome do lar novo:**
- (a) `runtime/` na raiz — um diretório só, agrupa tudo que "roda o sistema".
- (b) promover cada subdir pra raiz (`grafo/`, `router/`, `librechat/`, …) — mais
  itens na raiz, mas cada um autodescreve.
- (c) outro nome (`sistema/`, `stack/`, `app/`…).

Recomendação: **(a) `runtime/`** — a raiz já tem 20+ itens; um agrupador a mais é
mais legível que 8 subdirs novos soltos. Mas é escolha sua.

## 2. Inventário de referências a corrigir (levantado 09/09/2026)

### 2a. Máquina — quebra se não corrigir junto
- **12 units systemd INSTALADAS** em `~/.config/systemd/user/` com `ExecStart=`,
  `Documentation=`, `WorkingDirectory=`, `EnvironmentFile=` ou dropin apontando
  pra `%h/agata/redesign/…`: `agata-drain`, `agata-consolidacao`, `discord-mcp`,
  `navegador-mcp`, `openvino-whisper`, `openvino-embeddings`, `omniroute-sanitizer`,
  `obsidian-ro-proxy`, `piper-tts`, `seth-gateway`, `seth-escriba`, `llamacpp-agata`.
  Precisam de novo `cp` da fonte + `systemctl --user daemon-reload`.
- **`~/.local/bin/agata`** — wrapper que chama `~/agata/redesign/grafo/cli.py`.
- **`~/librechat/`** (deploy) — `librechat.yaml` e `data/mcp/canon-mcp.mjs`
  copiados da fonte; o atalho `seth` re-sincroniza desde (401), mas a 1ª cópia
  pós-move é manual.
- **dropins** `redesign/systemd/dropin-*.conf` (instalados como `*.d/override.conf`).

### 2b. Repo — fonte versionada, entra no(s) `.diff`
- `scripts/perimetro.sh` — padrões P-8 (`_p8_eh_comportamento`:
  `redesign/router/*|redesign/mcp/*|redesign/librechat/*.mjs|…|redesign/systemd/*`),
  comentários P-9, P-10 (lista de `gerar_obsidian.py`), P-12 (`redesign/fase7-hd/`).
- `scripts/gerar_obsidian.py` — lista hard-coded de caminhos.
- `scripts/busca_semantica.py` — ref a `redesign/`.
- `redesign/librechat/canon-mcp.mjs` — `CANON.ACESSO_GRADUADO = "redesign/ACESSO-GRADUADO.md"`
  (2 chaves) + o guard `p.startsWith("redesign/")` na resolução de caminho.
  Nota: a chave `ROADMAP: "ROADMAP.md"` já está quebrada (arquivo não existe na
  raiz — foi pra `extras/arquivo-redesign/`); consertar de passagem ou anotar.
- `redesign/librechat/librechat.yaml` + `docker-compose.yml` — comandos de MCP server.
- `redesign/systemd/{seth, seth-parar, seth-agente, agata-jogo}` — atalhos com
  `~/agata/redesign/…` embutido.
- Todos os `*.service` fonte em `redesign/systemd/` — `ExecStart`, `Documentation`.
- `PROJETO.md` — **19 ocorrências**.
- `config/modelos-gratuitos.md`, `CHAVES.md`, `ONDE_ESTAMOS.md`,
  `PROCEDIMENTO_LOGIN.md`.
- `.gitignore` — padrões sob `redesign/` (`.venv`, `voices/`, etc.).

### 2c. NÃO tocar (histórico / gerado)
- `extras/arquivo-redesign/**` e `extras/arquivo/**` — descrevem o processo
  passado; Regra 4 no espírito.
- `propostas/aplicadas/**` — registro histórico de propostas já consumidas.
- `MEMÓRIAS.md` e camadas frias/morno, `INDICE_MEMORIAS*` — história; a entrada
  nova de MEMÓRIAS explica o move, as antigas ficam como estão.
- `.hidrata.md`, `memoria/obsidian/**` — gerados, o pre/post-commit regenera.

## 3. Como mover — big-bang, não faseado

`git mv` preserva história. **Um único commit** (ou 2-3 no máximo), não faseado
por subdir: um estado meio-movido é um sistema quebrado (unit apontando pra
caminho que não existe mais). O "por peça" do backlog se traduz em **revisão por
peça dentro de um `.diff` só**, não em commits parciais que deixam o sistema no ar.

Sequência dentro do commit:
1. `git mv redesign/<sub> runtime/<sub>` pra cada subdir + soltos.
2. `sed`/edição dos refs de 2b (um passe, com uma lista de substituição fixa
   `redesign/ → runtime/` só nos arquivos de 2b, nunca em 2c).
3. Regenerar nada à mão — o pre-commit refaz `.hidrata.md`/índices/vault.
4. Pós-commit, FORA do `.diff` (passos de Máquina, no apply):
   - `cp runtime/systemd/*.service ~/.config/systemd/user/` + dropins + `daemon-reload`.
   - `cp` novo do `~/.local/bin/agata` (ou editar a 1 linha).
   - `cp runtime/librechat/{librechat.yaml,canon-mcp.mjs}` pro `~/librechat/` + `docker restart librechat`.
5. Teste (seção 4).

## 4. Teste de aceite (antes de dizer que fechou)
- `bash -n` em todo `.sh`; `py_compile` em todo `.py` movido; `node --check` no `.mjs`.
- `systemctl --user daemon-reload` sem erro; `system-analyze --user verify` nas 12 units.
- `systemctl --user restart agata.target` → todos os membros `active`.
- Atalho `seth` completo → LibreChat 200, `:20126` responde, `canon_consultar` no LibreChat lê um canônico.
- `~/.local/bin/agata status` → OK.
- `bash scripts/perimetro.sh` → sem FALHA nova (P-8 tem que reconhecer os caminhos novos).
- `seth-parar` → frentes param limpo.
- 1 commit de teste (trivial) depois do move → pre-commit/post-commit (hidratação, vault, índice derivado, bundle) rodam sem erro.

## 5. Portão das três perguntas
1. **Desfaço sozinho?** — `git revert` do commit + re-`cp` das units antigas.
   Reversível, mas com uma janela de serviço quebrado se algo escapar.
2. **O que mais toca?** — toda a seção 2. O maior risco são as 12 units
   instaladas (fora do repo) ficarem dessincronizadas da fonte.
3. **Eu saberia se quebrasse?** — P-9 pega unit `failed`; o teste da seção 4
   exercita o caminho todo. Risco residual: erro de path que só aparece num
   **reboot** (unit que só roda no boot). Mitigar: `systemctl --user restart`
   de cada uma no apply, não só `daemon-reload`.

## 6. O que este plano precisa antes de virar `.diff`
1. **Decisão de nome** (seção 1) — só sua.
2. **Segunda opinião** (REGRAS "Mudança estrutural") — Conselho Remoto sobre
   este plano, OU você assume o risco por escrito em MEMÓRIAS.
3. **Sessão dedicada** — não a cauda de uma sessão longa. É mecânico mas amplo;
   merece foco e o teste da seção 4 rodado com calma.

## 7. Recomendação
Aprovar o **plano** (nome + "faço em sessão dedicada com 2ª opinião"), não a
execução agora. B6 é coerência/rastreabilidade, não urgência — o custo de fazer
com pressa (unit quebrada num reboot dias depois) é maior que o de esperar uma
sessão própria.
