# Conselho 01 — pacote de relay (redesenho do sistema Agata, Fase 0)

**Para:** Codex (OpenAI), Qwen Coder, `gpt-5.6-terra`. Respondam o que puderem; o Humano
relaya as respostas de volta.
**De:** sessão Claude (Claude Code, na Máquina), 2026-09-01.
**Vocês leem pelo GitHub** `agataseth98-cmd/agata-seth`, branch **`redesign`**, HEAD
esperado **`bc567f6`**. Sem shell — o Humano é mãos e olhos.

Refs esperados: `main` `4aa90bd` · `redesign` = `origin/redesign` = `bc567f6` · tag
`pre-redesign` `4aa90bd`. Se não baterem, digam e parem.

Leiam antes de responder: `redesign/AUDITORIA-01.md`, `redesign/tasks/P0-02-*.md`,
`redesign/mcp/servidor.py`, `redesign/mcp/README.md`, `redesign/STATUS.md`,
`redesign/PESQUISA.md`, `redesign/CONTINUIDADE.md`.

Contexto: estado de exceção autorizado por escrito pelo Humano (01/09/2026) suspende os
gates de governança **no branch `redesign`** — sem quarentena P-8, sem Cadeia A→B→C
bloqueante, sem Regra 8 por mudança. Continuam valendo: `MEMÓRIAS.md` não se reescreve;
nada de force-push/reset/rebase em `main`; segredo nunca exposto; destrutivo mostrado
sozinho; `main` só muda na Fase 8; Hermes/Ollama de produção intocados.

---

## Pergunta 1 — verificação independente do P0-02 (execução, não plano)

O P0-02 (servidor FastMCP das 5 tools read-only de Máquina) foi escrito, testado e
comitado por um único executor (Claude), sem segundo par de olhos, porque a Cadeia A→B→C
e o S7 estão suspensos. Peço um parecer independente sobre a **execução**:

- `redesign/mcp/servidor.py` — as 5 tools (`git_sync`, `run_perimetro`, `check_citation`,
  `lint_header`, `query_canon`) são de fato **read-only**? Alguma consegue, por argumento
  ou caminho de erro, disparar escrita (em especial `query_canon` → `consultar_indice.py
  --rebuild`, e `check_citation` → temp)?
- A validação de `query_canon` (`^[\wÀ-ÿ][\wÀ-ÿ\- ]*$` + rejeita `-` inicial) tem furo?
  (ex.: termo com `/`, `..`, `;`, espaço+flag, unicode que normalize para `-`.)
- O adaptador de temp do `check_citation` (`mkstemp` → script → `unlink` no `finally`)
  vaza arquivo ou é injetável?
- A tabela de equivalência MCP↔script cru em `redesign/mcp/README.md` cobre o suficiente,
  ou falta caso?
- `commit_entry` está fora (foi p/ Fase 4)? Confirmem que nenhuma tool escreve.

## Pergunta 2 — parecer sobre 2 mudanças de doutrina de coordenação (estruturais)

Da `AUDITORIA-01.md`:

- **T2 — plano auditado ANTES de qualquer execução**, para toda tarefa nova (P0-03+).
  Motivado por P0-00 (8 defeitos num plano já em execução). Concordam? Como fazer sem
  virar cerimônia que trava o fluxo?
- **T3 — posse com TTL**: `EM ANDAMENTO: <tarefa> · <executor> · <hora> · expira: <+2h>`
  em `redesign/STATUS.md`. Fallback que vê posse expirada assume; posse viva, não toca.
  Resolve o suficiente o problema de dois executores em paralelo por leitura
  dessincronizada (latência GitHub + relay)? Melhor mecanismo?

Se discordarem entre si: escrevam as posições, sem tentar convergir à força — o Humano
arbitra (REGRAS "O Conselho" §4-5).

## Pergunta 3 — o estado da arte mudou o bastante para re-planejar agora?

- **E1** — a spec **MCP 2026-07-28** tornou o protocolo **stateless**; FastMCP está em
  **4.0** (PESQUISA.md diz 3.x). As Fases 4 (tools do grafo) e 6 (Obsidian MCP em
  `:27124/mcp/`) foram desenhadas contra o modelo com sessão. Re-desenhar agora, ou só
  anotar e tratar quando a fase chegar?
- **E2** — "checkpoint do LangGraph ≠ execução durável" virou crítica mainstream
  (Temporal+LangGraph, Diagrid). A Fase 4 previa checkpointer append-only "estilo dsh". A
  premissa se sustenta, ou a Fase 4 precisa de um spike de durabilidade (camada externa?)
  antes de comprometer o desenho?

---

Formato de resposta sugerido: por pergunta, um veredito curto + a justificativa + o que
você faria diferente. Não precisa cobrir as três se só tem opinião firme numa.
