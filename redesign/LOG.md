# LOG — redesenho do sistema local Agata (append-only)

Mais recente no fim. Cada entrada: data-hora `-03` · executor · o que foi feito · o que
falta · bloqueios · `HEAD` no fim.

---

## 2026-09-01 ~16:40 -03 · sessão Claude (Claude Code, na Máquina)

**Feito**
- Criado o branch `redesign` a partir de `main` @ `4aa90bd` (MEMÓRIAS (309)).
- Criado o scaffolding do workspace `redesign/`:
  - `README.md` — estado de exceção (gates de governança suspensos no branch por
    autorização escrita do Humano, 01/09/2026, risco assumido) + invariantes que
    continuam valendo (sem reescrita de história, sem force-push/reset em `main`,
    segredo nunca exposto, destrutivo mostrado sozinho, `main` só muda na Fase 8,
    Hermes/Ollama de produção intocados até a Fase 8).
  - `CONTINUIDADE.md` — briefing para o executor fallback (Codex / Qwen Coder):
    quem ele é (lê o GitHub, sem shell local, o Humano é mãos e olhos), o primeiro
    movimento obrigatório (sincronizar com o repo antes de propor), como entregar
    trabalho (blocos para o terminal fish, um por vez), regras de fish 4.8 vs bash,
    divisão entre executores (um de cada vez, linha de posse em STATUS.md), fim de
    sessão (STATUS + LOG + commit no branch).
  - `ROADMAP.md` — as 9 fases (0–8) com objetivo, entrega e critério de aceite,
    já com as 8 correções da pesquisa embutidas.
  - `PESQUISA.md` — estado da arte por ferramenta (set/2026) + as 8 correções
    (C1 MoE fora do Ollama, C2 iGPU é UHD não Arc, C3 grammar só no envelope,
    C4 FastMCP 3.0 traz OTel, C5 OTel sem dashboard, C6 restic não borg,
    C7 fallback shell = Goose, C8 LoRA exige `agata down`) + fontes.
  - `STATUS.md` — Fase 0 em montagem, quadro de posse vazio, próximos passos
    P0-01/P0-02/P0-03.
  - `LOG.md` — este arquivo.

**Não tocado**
- `main`, o canon (`REGRAS.md`/`PROJETO.md`/`MEMÓRIAS.md`), o Hermes, o Ollama, o
  `.hermes.md` de produção. Nada instalado, nada em `systemd`, nenhum modelo baixado
  ou removido.

**Contexto do handoff**
- O Humano conseguiu dois executores fallback de redundância: **Codex (OpenAI, plano
  gratuito)** e **Qwen Coder (plano gratuito)**, ambos com integração nativa ao GitHub
  `agataseth98-cmd/agata-seth` (`main` para leitura; `redesign` para trabalho). Eles
  assumem se a sessão Claude cair. O `CONTINUIDADE.md` é o ponto de entrada deles.

**Falta / próximo**
- P0-01: `git tag pre-redesign` + backup restic inicial + `models/manifest.json`.
- P0-02: servidor FastMCP 3.0 das ferramentas de Máquina.
- P0-03: arquivos-tarefa das Fases 1–2.
- Todos pedem o "vai" do Humano.

**HEAD (redesign) no fim:** ver `git log -1 --oneline redesign` após o commit desta entrada.

---

## 2026-09-01 ~17:10 -03 · sessão Claude (Claude Code, na Máquina)

**Contexto:** o Humano relayou (a) uma auditoria de `gpt-5.6-terra` (t=14) apontando 8
defeitos no plano da Fase 0 e propondo uma tarefa corretiva P0-00 antes de qualquer
execução, e (b) um relato de que um executor já tinha rodado P0-01 parcialmente (tag
criada, manifesto de 20 modelos gerado, `restic` v0.19.1 instalado, HD não montado) e
estava prestes a commitar.

**Verificado na Máquina:**
- Tag `pre-redesign` existe em `main` e no remoto, apontando `4aa90bd`. OK, é o ponto de
  congelamento correto — mantida.
- `models/manifest.json` estava **staged, não commitado**, na versão deficiente (só `id`
  do Ollama, 6 linhas de Modelfile, sem sha256 nem origem).
- `restic` v0.19.1 instalado. HD `AgataBkup01` não montado.
- Os 8 achados da auditoria: **todos confirmados** (incl. `consultar_indice.py --rebuild`
  escreve; `checar_citacao.sh` recebe caminho, não stdin; `git log ... redesign` ambíguo,
  que já tinha falhado nesta sessão).

**Feito (P0-00 — correção do plano, aplicada direto na Máquina):**
1. `.gitignore` — linhas explícitas para `redesign/**/.venv/`, `__pycache__`, `*.pyc`
   (`.venv/` já era coberto; reforço). Verificado com `git check-ignore`.
2. `models/manifest.json` — regenerado com `blob_sha256` (64 hex), `blob_path`, `origem`
   e Modelfile completo. 20 modelos, sha256 em 20/20. Substitui a versão staged deficiente.
3. `redesign/tasks/P0-02` — `commit_entry` removida (vai p/ Fase 4); `query_canon` passa a
   rejeitar qualquer argumento com `-` (barra `--rebuild`); `check_citation` ganha o
   adaptador de temp especificado com código; aceite atualizado; tools 6→5.
4. `redesign/tasks/P0-01` — gerador de manifesto reescrito no próprio arquivo-tarefa;
   rollbacks: parte não destrutiva separada, `rm -rf` isolado com `⚠️ DESTRUTIVO`.
5. `redesign/CONTINUIDADE.md` — `git log --oneline -12 redesign` → `... HEAD --`.
6. `redesign/README.md` — seção "Efeito automático esperado nos commits deste branch"
   (âncora SHA + derivados do post-commit).
7. `redesign/tasks/P0-00-correcao-do-plano.md` — criado, registrando os 8 achados e as
   correções, marcado FEITO.
8. `STATUS.md` — P0-00 FEITO; P0-01 parcial (tag ✅, manifesto ✅ corrigido, restic ✅,
   repo restic ⏸ HD); regra de coordenação reforçada (posse antes de executar).

**Não tocado:** `main`, canon, Hermes, Ollama, `.hermes.md` de produção.

**Coordenação:** houve auditoria e execução em paralelo sem linha de posse em `STATUS.md`.
A regra "posse antes de executar" foi reforçada no `STATUS.md` e no `CONTINUIDADE.md`.

**Migração de chat:** esta conversa Claude será encerrada e o trabalho continua num chat
novo (falso positivo recorrente de classificador `[bio]` no harness — conhecimento
registrado na memória do Claude Code). O chat novo retoma de `STATUS.md` + `LOG.md` +
`CONTINUIDADE.md` no branch `redesign`.

**Falta / próximo:** P0-01 passos 3-4 (repo restic, quando o HD montar); P0-02 (servidor
FastMCP, já corrigido); P0-03 (tarefas das Fases 1-2). Todos pedem o "vai" do Humano.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.

---

## 2026-09-01 ~21:55 -03 · sessão Claude (Claude Code, na Máquina — chat novo pós-migração)

**Contexto:** chat novo, reidratado do repositório (a conversa anterior foi encerrada por
falso positivo recorrente do classificador `[bio]` no harness). Reidratação conferida:
`git status` limpo; 4 refs batem — `main` 4aa90bd, `redesign` = `origin/redesign` = 798d483,
tag `pre-redesign` = 4aa90bd. `git diff main..redesign` em `PROMPT_CARREGAMENTO.md` = só o
bloco `ANCORA-SHA` (máquina, `pre-commit`), esperado, não revertido. Lidos, na ordem:
`README.md` → `STATUS.md` → `LOG.md` → `CONTINUIDADE.md` → `ROADMAP.md` + `PESQUISA.md` →
topo de `MEMÓRIAS.md` (canon em (309)).

**Direção do Humano:** "sem escolhas, em estado de exceção, você prevê meu comportamento e
apresenta só as opções que amadurecem o sistema. Prossiga." → executei a próxima tarefa
não bloqueada de maior valor de maturidade: **P0-02**. (P0-01 passos 3-4 seguem bloqueados
pelo HD; P0-03 é o próximo alvo.)

**Feito (P0-02 — servidor FastMCP das ferramentas de Máquina):**
- `redesign/mcp/.venv` — venv isolado, **fastmcp 4.0.1** (`fastmcp>=3.2` satisfeito; API
  `@mcp.tool` / `mcp.run()` estável de 3.x a 4.x). Gitignorado (`.gitignore:54`,
  `redesign/mcp/.venv/`), confirmado com `git check-ignore`.
- `redesign/mcp/servidor.py` — 5 tools read-only, cada uma wrapper fino de um script de
  `~/agata/scripts/` com `cwd=~/agata`, sem shell:
  - `git_sync` — `git fetch` + `git ls-remote origin refs/heads/main`; `{head, origin_head,
    em_dia}`. Testado: `head` 798d483 (redesign), `origin_head` 4aa90bd (main), `em_dia:false`.
  - `run_perimetro` — `bash scripts/perimetro.sh`; `{exit_code, resumo, linhas}`.
  - `check_citation` — adaptador de temp (`mkstemp` → script recebe caminho → `unlink`);
    `{exit_code, resumo, suspeitos}`.
  - `lint_header` — `verificar_cabecalho.py` por stdin; `{ok, motivo}`.
  - `query_canon` — `consultar_indice.py`; valida cada termo contra `^[\wÀ-ÿ][\wÀ-ÿ\- ]*$`,
    **rejeita** qualquer termo com `-` inicial (barra `--rebuild`); `{exit_code, trechos, erro}`.
  - Modo `--selftest <tool>` para rodar cada tool fora do protocolo MCP.
- `redesign/mcp/requisitos.txt`, `redesign/mcp/README.md` (com a tabela de equivalência).

**Equivalência MCP ↔ script cru (verificada):**
- `run_perimetro`: script exit 0 · `RESULTADO GERAL: OK — 10 OK · 0 SKIP · 1 PARCIAL · 0
  FALHA`; MCP idêntico (mesmo placar, mesmo exit).
- `lint_header`: cabeçalho válido → `OK`/exit 0 ↔ `{ok:true}`; cabeçalho sem `t=`/sem
  citação → 2 linhas `FALHA:`/exit 1 ↔ mesmas 2 linhas/`ok:false`/exit 1.
- `check_citation`: `(302 - ...)` real → `suspeitos=0`/exit 0 ↔ `suspeitos:[]`; `(99999 -
  ...)` inexistente → `SUSPEITO (P-7)`/exit 1 ↔ mesma linha em `suspeitos[]`/exit 1.
- `query_canon`: `["--rebuild","x"]` (e `["--","--rebuild"...]`) → erro de validação/exit 3,
  **índice não regenerado**; `["hidratação","âncora"]` → 8 seções de REGRAS + títulos/exit 0.
- `git status` limpo depois de tudo (fora as mudanças intencionais); `.venv` e `__pycache__`
  não aparecem (`!!` ignorado).

**Aceite P0-02:** servidor sobe e lista **5** tools (`mcp.list_tools()`); resultado por MCP
= resultado do script cru em `run_perimetro`/`check_citation`/`lint_header`; `query_canon`
rejeita `--rebuild` e aceita termos válidos sem regenerar índice; `.venv` fora do git. ✅
O outro item do critério da Fase 0 ("restore do restic num scratch reproduz config")
depende de P0-01 passos 3-4 (HD) — anotado em `STATUS.md` como "aceite de restore".

**Não tocado:** `main`, canon (`REGRAS.md`/`PROJETO.md`/`MEMÓRIAS.md`), Hermes, Ollama,
`.hermes.md` de produção, `scripts/` (só lidos e chamados, nunca editados), índice derivado.

**Nota de fato:** esta sessão Claude Code roda na Máquina e **tem shell** — executou os
blocos direto. Os fallbacks (Codex/Qwen) continuam sem shell. `STATUS.md` "Notas de
handoff" atualizado para refletir isso e para registrar a migração de chat como feita.

**Falta / próximo:** P0-01 passos 3-4 (HD); P0-03 (arquivos-tarefa das Fases 1-2);
aceite de restore do P0-02 (com HD). Pedem o "vai" do Humano.

**HEAD (redesign) no fim:** ver `git log -1 --oneline HEAD --` após o commit desta entrada.
