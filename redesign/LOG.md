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
