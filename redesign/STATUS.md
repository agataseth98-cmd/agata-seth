# STATUS — redesenho do sistema local Agata

FASE ATUAL: **Fase 0 — rede de segurança e sistema de tarefas**
ATUALIZADO: 2026-09-01 ~21:55 -03 · por: sessão Claude (Claude Code, na Máquina)
BASE: `main` @ 4aa90bd (MEMÓRIAS (309)) · tag `pre-redesign` = 4aa90bd (local + remoto)

## Quadro de posse

_(nenhuma tarefa EM ANDAMENTO)_

Formato: `EM ANDAMENTO: <tarefa> · <executor> · <AAAA-MM-DD HH:MM -03>` enquanto trabalha;
`FEITO: <tarefa> · <executor> · <data>` ao terminar.

**Regra de coordenação (reforçada 01/09):** nenhuma tarefa é executada antes de estar
listada como autorizada aqui em "Próximo" **e** de o executor ter escrito a linha
`EM ANDAMENTO` acima. Auditoria e execução em paralelo sem posse causou retrabalho
nesta fase (ver LOG 01/09 ~17:10).

## Feito

- **P0-00 — correção do plano da Fase 0** ✅ (sessão Claude, 01/09). Auditoria de
  `gpt-5.6-terra` confirmada na Máquina (8/8 achados) e aplicada: `.gitignore` protege
  venv; `models/manifest.json` agora com `blob_sha256` + origem + Modelfile completo (20/20);
  `commit_entry` tirada da Fase 0 (vai p/ Fase 4); `query_canon` rejeita flags;
  `check_citation` com adaptador de temp especificado; rollbacks destrutivos isolados com
  aviso; `git log ... redesign` ambíguo corrigido no `CONTINUIDADE.md`; efeito da âncora
  registrado no `README.md`.
- **P0-01 — parcial:**
  - ✅ passo 1: tag `pre-redesign` criada em `main` e no remoto (@ 4aa90bd).
  - ✅ passo 2: `models/manifest.json` gerado (versão corrigida por P0-00 — 20 modelos,
    sha256 em 20/20).
  - ✅ passo 3: `restic` v0.19.1 instalado e verificado.
  - ⏸️ passos 3-4 (repo restic + 1º snapshot): **bloqueado** — HD `AgataBkup01` não
    montado (previsto para 02/09).
- **P0-02 — servidor FastMCP das ferramentas de Máquina** ✅ (sessão Claude, 01/09).
  `redesign/mcp/servidor.py` + `requisitos.txt` + `README.md`. **fastmcp 4.0.1** num venv
  isolado (`redesign/mcp/.venv`, gitignorado). 5 tools read-only: `git_sync`,
  `run_perimetro`, `check_citation` (adaptador de temp), `lint_header`, `query_canon`
  (rejeita flags — `--rebuild` barrado, índice não regenera). Equivalência MCP↔script cru
  verificada em `run_perimetro`, `lint_header` (ok+falha) e `check_citation` (ok+suspeito);
  `query_canon` aceita termos válidos e rejeita `--rebuild`, `git status` limpo depois.
  Tabela de equivalência em `redesign/mcp/README.md`. `commit_entry` continua fora (Fase 4).
- Scaffolding do workspace `redesign/` (branch criado de `main` @ 4aa90bd): README,
  CONTINUIDADE, ROADMAP, PESQUISA, STATUS, LOG, tasks/P0-00, P0-01, P0-02.

## Próximo (Fase 0, precisa do "vai" do Humano)

- **P0-01 passos 3-4** — inicializar o repo restic + 1º snapshot, quando o HD montar.
- **P0-03** — escrever os arquivos-tarefa das Fases 1 e 2.
- **P0-02 — aceite de restore** (parte do critério da Fase 0): restore do restic num
  scratch reproduz config — depende de P0-01 passos 3-4 (HD).

## Bloqueios

- **P0-01 passos 3-4** — HD externo `AgataBkup01` não montado. Reavaliar em 02/09.

## Notas de handoff

- Executor primário: sessão Claude. Fallback 1: Codex (OpenAI, plano gratuito). Fallback 2:
  Qwen Coder (plano gratuito). Ambos com integração nativa ao GitHub `agataseth98-cmd/agata-seth`.
- Auditor de plano ativo nesta fase: `gpt-5.6-terra` (achou os 8 defeitos de P0-00).
- **Shell:** a sessão Claude Code roda na Máquina (Predator) e **tem shell** — executa os
  blocos direto e cola a saída. Os fallbacks (Codex, Qwen Coder) **não têm shell**: para
  eles o Humano (Orusoua) é mãos e olhos, roda os blocos fish e cola a saída (`CONTINUIDADE.md`).
- Gates de governança suspensos no branch `redesign` (autorização escrita do Humano,
  01/09/2026, risco assumido). Invariantes de proteção mantidos — ver `README.md`.
- **Migração de chat feita:** a conversa Claude anterior foi encerrada (falso positivo
  recorrente de classificador `[bio]` no harness) e retomada num chat novo, que reidratou
  de `STATUS.md` + `LOG.md` + `CONTINUIDADE.md` no branch `redesign` (4 refs conferidas:
  `main` 4aa90bd, `redesign`/`origin/redesign` 798d483, `pre-redesign` 4aa90bd).
