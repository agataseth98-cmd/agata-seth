# STATUS — redesenho do sistema local Agata

FASE ATUAL: **Fase 0 — rede de segurança e sistema de tarefas**
ATUALIZADO: 2026-09-01 ~23:02 -03 · por: sessão Claude (Claude Code, na Máquina)
ÂNCORA (leve, manual até H2): esta atualização foi escrita sobre `redesign` @ **`ca6f76d`**
e cria o commit seguinte. Referência viva para os pares = `git rev-parse origin/redesign`
(ou o topo do `git log` do branch no GitHub); esta linha dá só o piso conhecido, um commit
atrás — mesma defasagem da âncora-SHA do canon.
BASE: `main` @ 4aa90bd (MEMÓRIAS (309)) · tag `pre-redesign` (anotada: objeto-tag `cea5aeb`
→ commit `4aa90bd`; desreferenciar com `pre-redesign^{commit}`) local + remoto

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
- **P0-02 — servidor FastMCP das ferramentas de Máquina** ✅ (sessão Claude, 01/09;
  revisto pelo `gpt-5.6-terra` no Conselho 01). `redesign/mcp/servidor.py` +
  `requisitos.txt` (`fastmcp==4.0.1`, pin) + `README.md`. Venv isolado
  (`redesign/mcp/.venv`, gitignorado). 5 tools sem escrita em workspace/canon: `git_sync`
  (2 eixos: `canon_*` = `main` vs `origin/main`; `branch_*` = branch vs upstream; +
  `fetch_error`), `run_perimetro`, `check_citation` (adaptador de temp com `os.fdopen`),
  `lint_header`, `query_canon` (rejeita flags — defesa real é subprocess sem shell + args
  em lista; `--rebuild` inalcançável, índice não regenera). `_run` nunca levanta (124
  timeout / 127 binário ausente). Equivalência MCP↔script cru re-verificada em
  `run_perimetro`, `lint_header` (3 casos) e `check_citation` (real+suspeito); `git status`
  limpo depois. Tabela + 6 casos de borda em `redesign/mcp/README.md`. `commit_entry`
  continua fora (Fase 4).
- Scaffolding do workspace `redesign/` (branch criado de `main` @ 4aa90bd): README,
  CONTINUIDADE, ROADMAP, PESQUISA, STATUS, LOG, tasks/P0-00, P0-01, P0-02.
- **AUDITORIA-01** (sessão Claude, 01/09) — auditoria de atrito de equipe + delta de
  estado da arte. 8 pontos de atrito (A1 = sem verificação independente sob o estado de
  exceção, o mais grave). Delta: MCP virou stateless (spec 2026-07-28), FastMCP em 4.0 não
  3.x (E1); "checkpoint ≠ execução durável" agora é crítica mainstream, Fase 4 tem premissa
  não validada (E2). 4 decisões para o Humano (H1-H4), 4 mudanças de processo (T1/T4
  aplicáveis já; T2/T3 pendentes de parecer). Ver `redesign/AUDITORIA-01.md`.
- **CONSELHO-01** — pacote de relay para Codex / Qwen Coder / `gpt-5.6-terra`. Ver
  `redesign/CONSELHO-01-relay.md` (cópia em `~/Área de trabalho/`).
  - ✅ **`gpt-5.6-terra` respondeu** (P1/P2/P3), convergência forte com a auto-revisão do
    Claude, sem divergência. P1: achados de robustez aplicados em `servidor.py` +
    `README.md` (timeout no `_run`; `git_sync` em 2 eixos + `fetch_error`; `os.fdopen` no
    `check_citation`; frase errada sobre `memoria/missoes/` corrigida; pin do `fastmcp`).
    P2: T2 (tier de risco) e T3 (posse confirmada por commit remoto; TTL = recuperação de
    abandono) — convergência de 2 modelos. P3: E1 anotar não re-desenhar; E2 spike de
    durabilidade antes do desenho da Fase 4.
  - ⏳ **aguardando Codex e Qwen Coder** (P1 verificação + P2/P3).

## Próximo (Fase 0 — aguardando as decisões do Humano; ver PLANO reapresentado no chat, 01/09 ~23h)

- **Humano decide:** H1 (verificação sob exceção) · H2 (âncora de coordenação do branch) ·
  H3 (pointer em `main`) · H4 **retirada** (fallbacks só afinados — não há divergência
  entre executores a exercitar) · T1/T4 (aplicáveis já) · T2 (plano auditado, tier de
  risco) · T3 (posse — dormante com 1 executor ativo) · E1/E2 (linhas no ROADMAP + spike P4-00).
- **Depois do "vai":** aplicar T1/T4 + E1/E2 (docs); H2 se aprovado (hook + `ANCORA.md`);
  então **P0-03** (arquivos-tarefa das Fases 1-2).
- **Quando o HD montar:** P0-01 passos 3-4 (repo restic + 1º snapshot) + **P0-02 aceite de
  restore** (restore num scratch reproduz config — fecha o critério da Fase 0).
- **Fallbacks:** manter afinados (reidratar do branch a pedido do Humano). Não são gate.

## Bloqueios

- **P0-01 passos 3-4** — HD externo `AgataBkup01` não montado. Reavaliar em 02/09.

## Papéis (fixado pelo Humano, 01/09/2026)

- **Humano (Orusoua) decide.** Sozinho. Nenhum modelo co-decide.
- **Claude (esta sessão, na Máquina) = conselheiro + primeiro executor.** Aconselha (com
  recomendação explícita) e executa. Não decide doutrina.
- **Codex, Qwen Coder = executores de reserva, apenas AFINADOS.** Reidratam do branch
  quando o Humano pedir, ficam no HEAD do momento, conhecem o `CONTINUIDADE.md`. **Não**
  são conselheiros nem gate: não se espera parecer deles para o plano andar.
- **`gpt-5.6-terra` = ferramenta de auditoria pontual** que o Humano aciona (achou os 8
  defeitos de P0-00; achou o `git_sync` mal-desenhado no Conselho 01). Útil, não trava.

## Notas de handoff

- **Shell:** a sessão Claude Code roda na Máquina (Predator) e **tem shell** — executa os
  blocos direto e cola a saída. Os fallbacks (Codex, Qwen Coder) **não têm shell**: para
  eles o Humano (Orusoua) é mãos e olhos, roda os blocos fish e cola a saída (`CONTINUIDADE.md`).
- **Shell:** a sessão Claude Code roda na Máquina (Predator) e **tem shell** — executa os
  blocos direto e cola a saída. Os fallbacks (Codex, Qwen Coder) **não têm shell**: para
  eles o Humano (Orusoua) é mãos e olhos, roda os blocos fish e cola a saída (`CONTINUIDADE.md`).
- Gates de governança suspensos no branch `redesign` (autorização escrita do Humano,
  01/09/2026, risco assumido). Invariantes de proteção mantidos — ver `README.md`.
- **Migração de chat feita:** a conversa Claude anterior foi encerrada (falso positivo
  recorrente de classificador `[bio]` no harness) e retomada num chat novo, que reidratou
  de `STATUS.md` + `LOG.md` + `CONTINUIDADE.md` no branch `redesign` (4 refs conferidas:
  `main` 4aa90bd, `redesign`/`origin/redesign` 798d483, `pre-redesign` 4aa90bd).
