# STATUS — redesenho do sistema local Agata

FASE ATUAL: **Fase 0 — rede de segurança e sistema de tarefas** (em montagem)
ATUALIZADO: 2026-09-01 ~16:40 -03 · por: sessão Claude (Claude Code, na Máquina)
HEAD (redesign): ver `git log -1 --oneline redesign`
BASE: `main` @ 4aa90bd (MEMÓRIAS (309))

## Quadro de posse

_(nenhuma tarefa EM ANDAMENTO)_

Formato: `EM ANDAMENTO: <tarefa> · <executor> · <AAAA-MM-DD HH:MM -03>` enquanto trabalha;
`FEITO: <tarefa> · <executor> · <data>` ao terminar.

## Feito

- Branch `redesign` criado a partir de `main` @ 4aa90bd.
- Scaffolding do workspace: `README.md` (estado de exceção + invariantes),
  `CONTINUIDADE.md` (briefing dos executores fallback Codex e Qwen Coder),
  `ROADMAP.md` (9 fases), `PESQUISA.md` (estado da arte + 8 correções), `STATUS.md`,
  `LOG.md`.

## Próximo (Fase 0, sem bloqueio)

- **P0-01** — `git tag pre-redesign` em `main`; backup restic inicial (`~/.hermes`, `config/`,
  `~/.config/agata/`, lista de modelos); primeiro `models/manifest.json` (nome, sha256,
  origem, Modelfile de cada GGUF em `ollama list`).
- **P0-02** — servidor **FastMCP 3.0** das ferramentas de Máquina:
  `git_sync`, `run_perimetro`, `check_citation`, `lint_header`, `query_canon`, `commit_entry`.
  Cada tool é um wrapper fino do script existente. Aceite: MCP e script dão o mesmo resultado.
- **P0-03** — escrever os arquivos-tarefa das Fases 1 e 2 em `redesign/tasks/` no schema fixo.

## Bloqueios

_(nenhum)_

## Notas de handoff

- Executor primário: sessão Claude. Fallback 1: Codex (OpenAI, plano gratuito). Fallback 2:
  Qwen Coder (plano gratuito). Ambos com integração nativa ao GitHub `agataseth98-cmd/agata-seth`.
- Nenhum executor tem shell local. O Humano (Orusoua) roda os blocos fish e cola a saída.
- Gates de governança suspensos no branch `redesign` (autorização escrita do Humano,
  01/09/2026, risco assumido). Invariantes de proteção mantidos — ver `README.md`.
