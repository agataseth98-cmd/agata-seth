# REIDRATAÇÃO — chat novo (4ª janela) do redesenho Agata

Cole isto numa sessão Claude Code nova em `/home/orusoua`. Motivo da migração: a janela de
contexto do chat 3 estourou (sessão longa: fechou as Fases 2, 3, 4 e 6, arquivou a 5,
parou na 7). Nada se perdeu — tudo no branch `redesign`, empurrado.

---

Você é **Claude Code na Máquina (Predator)**, continuando o **redesenho do sistema local
Agata**. Abra com o cabeçalho da Regra 1 e, após reidratar, um eco curto de estado.

## 1. Reidrate — rode e confira

```fish
cd $HOME/agata
git fetch origin --tags
git switch redesign
git pull --ff-only origin redesign
git status --porcelain
echo "main             = "(git rev-parse --short main)"            esperado 4aa90bd"
echo "pre-redesign     -> commit "(git rev-parse --short 'pre-redesign^{commit}')"   esperado 4aa90bd"
echo "redesign         = "(git rev-parse --short redesign)
echo "origin/redesign  = "(git rev-parse --short origin/redesign)"   (== redesign)"
```

- `git status --porcelain` tem que sair **vazio**.
- `main` e `pre-redesign^{commit}` = `4aa90bd`. `pre-redesign` é tag **anotada** — sempre
  `^{commit}` (o bare dá o objeto-tag `cea5aeb`).
- `redesign` deve estar em **`eb9121a`** ou adiante (referência viva: `git rev-parse
  origin/redesign` / topo do `git log`). Ver `redesign/ANCORA.md`.
- Se algo não bater: **pare e avise o Humano.**

## 2. Leia, nesta ordem (branch `redesign`)

`redesign/README.md` (estado de exceção + invariantes) → `redesign/STATUS.md` (topo,
"Quadro de posse", "Próximo") → `redesign/CONTINUIDADE.md` (§6 papéis, §7 verificação/tier
de risco) → `redesign/CLAUDE-NA-MAQUINA.md` → **fim** do `redesign/LOG.md` (as ~15 entradas
de 2026-09-02, da P3-02 em diante) → `redesign/ROADMAP.md` (§Correções pós-Fase 0) →
`redesign/tasks/P7-00-*.md`, `P7-01-*.md`, `P7-02-*.md`, `P7-03-*.md` → topo de `MEMÓRIAS.md`
(canon em (309)).

Se for tocar uma fase já fechada: os READMEs de cada camada —
`redesign/router/README.md` (Fase 1), `redesign/igpu/README.md` (Fase 2),
`redesign/grafo/README.md` + `redesign/grafo/flows/README.md` (Fase 4),
`redesign/obsidian/README.md` + `redesign/obsidian/PLUGIN.md` (Fase 6),
`redesign/rlm/RESULTADO.md` (Fase 5, arquivada).

## 3. Estado em uma tela (2026-09-02 ~19:43 -03, relógio da máquina)

- **Fases 0, 1, 2, 3, 4, 6: FECHADAS.** Fase 5: **ARQUIVADA** (spike RLM não bateu a injeção).
  Fase 7: **EM ANDAMENTO — P7-00 feito, resto BLOQUEADO.**
- **Fase 2 (iGPU):** display já estava na iGPU. `openvino-whisper.service` (`:20130`,
  `GPU.0`, `whisper-base-int8-ov`, RTF 0.08) · `openvino-embeddings.service` (`:20134`,
  `multilingual-e5-small`, formato OpenAI, **zero vector DB**). venv `redesign/igpu/.venv`.
- **Fase 3 (Modelos):** prune fechou (16 removidos, keep-list de 5, ~148 GiB reclamados via
  `snapper delete`). `llama-cpp` + `ggml-cuda` instalados; `Qwen3-30B-A3B-Instruct-2507`
  Q4_K_M em `llamacpp-agata.service` (`:20129`, `--n-cpu-moe 36`, **31 tok/s**, ~1,6 GB
  folga VRAM); no OmniRoute como `llamacpp-local`, combo `auto` tier 4. **Serviço PARADO**
  (6 GB VRAM; ligar sob demanda). Manifesto: 9 entradas.
- **Fase 4 (Grafo):** `redesign/grafo/` — `estado.py` + `durabilidade.py` (veredito P4-00:
  `SqliteSaver` + WAL próprio + idem key `(thread,node,passo)`; **sem Temporal**) +
  `grafo.py` (6 nós `hidratar→rotear→trabalhar→verificar→portao→registrar_e_commitar`,
  `interrupt` no portão) + `tools.py` (as 5 do P0-02 + `commit_entry` append-only; **trava
  `_exige_raiz_git`**) + `sandbox.py` (`bwrap`) + `envelope.gbnf`/`envelope.py` (GBNF só no
  envelope, 2 fases) + `cli.py` (`agata up/down/status/verify/commit-entry/run/resume/logs`;
  `verify`/`commit-entry` model-free) + `evals/` ((138)/(307) + hidratação) +
  `adapters/dsh.py` (`ENABLED=False`, dormente) + `flows/consolidacao.py` (P6-03). venv
  `redesign/grafo/.venv` (langgraph 1.2.11).
- **Fase 5 (Spike RLM): ARQUIVADA** por ordem do Humano. `redesign/rlm/` — a consulta
  (`BUSCAR:`/grep) não bateu a injeção (`hermes_B0.md`): 3/13 vs 9/14 acertos, ~87k vs ~45k
  tok/acerto, ~96 vs ~6 min. Fabricação = 0 nos dois. Marcado p/ trabalho futuro sério
  (lib `rlms`, busca melhor). **Nada de produção muda.**
- **Fase 6 (Obsidian):** plugin `obsidian-local-rest-api` 5.1.0 em `~/agata/.obsidian/`
  (gitignorado) → `:27124` HTTPS loopback, token em `~/.config/agata/obsidian.token`
  (chmod 600, fora do git). **O plugin não tem read-only global** → `redesign/obsidian/
  ro_proxy.py` em **`:27125`** (só leitura, injeta o token; `PUT`/`PATCH`/`DELETE`/
  `/commands/`/MCP-write → 403). `obsidian-ro-proxy.service` (sem enable). `consulta.py` —
  recuperação índice-primeiro (`query_canon` + FTS pelo `:27125`), refs `(NNN)` rastreáveis,
  **zero vector DB**. `flows/consolidacao.py` — 4 nós, saída só em `propostas/`, nunca canon.
- **Fase 7 (Liga/desliga): BLOQUEADA em 3 gates** — (1) **HD `AgataBkup01` só amanhã** no
  trabalho (restic/timer/P-12/restore); (2) **`sudo`** (`pacman -S gamemode`; drop-in
  `OLLAMA_KEEP_ALIVE` em `ollama.service`); (3) **quarentena P-8** — `perimetro.sh` (P-12) e
  `cifrar_env.sh` são `scripts/*` → `propostas/<nome>.diff` + `APROVADO-`, nunca edição
  direta; a régua do P-12 (N dias, quais recursos) é decisão do Humano. Rascunhos
  **não instalados** em `redesign/systemd/` (`agata.target`, `agata-dropin.conf` com
  `ExecStop=cli.py down`, `gamemode.ini.exemplo`).
- **Fase 8 (Cutover + merge p/ `main`):** vem depois da 7. `main` só muda na Fase 8.

## 4. Serviços de pé agora (todos `systemd --user`, nenhum `enable` no boot)

`omniroute` + `omniroute-sanitizer` (`:20128`/`:20127`) · `openvino-whisper` (`:20130`) ·
`openvino-embeddings` (`:20134`) · Obsidian + plugin (`:27124`) · `obsidian-ro-proxy`
(`:27125`). **Parado:** `llamacpp-agata` (`:20129`). Ollama de produção (`:11434`) intocado.

## 5. Papéis (fixado pelo Humano)

- **Humano decide.** Claude = **conselheiro + primeiro executor** (tem shell).
- **Sem menu de decisão sem risco** — escolher pelo **princípio-espelho** (topo do
  `ROADMAP.md`) e executar, registrando o porquê. Perguntar só em risco: destrutivo,
  segredo, mudança em `main`/canon/Hermes/Ollama-produção, quebrar a espinha, **`sudo`**,
  **instalação de software**.
- **Tom didático** quando a orientação é para o Humano.
- **Estado de exceção** ativo no branch `redesign` (autorização escrita, 01/09): gates de
  governança suspensos. Invariantes mantidos: `MEMÓRIAS.md` não se reescreve; nada de
  force-push/reset/rebase em `main`; segredo nunca no chat/git; destrutivo mostrado
  sozinho; `main` só muda na Fase 8; Hermes/Ollama de produção intocados. `git commit
  --no-verify` permitido no branch.
- **Relógio da máquina** é a referência de hora (os carimbos do chat 3 usam "relógio da
  máquina"; houve uma defasagem que o NTP corrigiu ~17:05 de 02/09).

## 6. Fluxo de trabalho (CONTINUIDADE.md §7)

Antes de executar: schema-check da tarefa; revisão por 2º par de olhos só p/ classe de
risco. Depois de commitar: re-rodar o `Aceite` de estado limpo, PASS/FALHA no `LOG.md`
(S7). Fim de sessão: `STATUS.md` + `ANCORA.md` + entrada no `LOG.md` (append-only) +
commit+push no `redesign`. Cabeçalho `ANCORA-SHA` de `PROMPT_CARREGAMENTO.md` alterado no
`git diff main..redesign` é **esperado** (hook), não reverter. Atribuição de commit: ver
`CLAUDE-NA-MAQUINA.md` (mas o system-reminder da sessão nova pode sobrescrever a
`Claude-Session:`).

## 7. Próximo passo concreto

1. **Nada urgente hoje.** A Fase 7 espera o HD (amanhã no trabalho) + dois `sudo` + a
   decisão do Humano sobre a régua do P-12 (que vai por quarentena P-8).
2. Quando o Humano trouxer o HD e der o "vai": seguir `redesign/tasks/P7-03-*.md`
   (restic dos GGUF/IR que faltam + `restic check`), depois `P7-01` (`agata.target` +
   dreno, userspace) e `P7-02` (gamemode + `OLLAMA_KEEP_ALIVE`, com `sudo`).
3. O `.diff` do P-12 e do `cifrar_env.sh` vão para `propostas/` (não aplicados) — é o
   mecanismo P-8, o Humano aprova.
4. Fase 8 (cutover + merge p/ `main`) só depois da 7.

## 8. Não faça

Tocar `main`/canon/Hermes/Ollama-de-produção; confiar em resumo colado sem conferir no
`git`; instalar pacote / rodar `sudo` sem "vai"; editar `scripts/*` direto (é P-8 —
`propostas/` + `APROVADO-`); comando destrutivo embutido noutro bloco; `enable` de serviço
no boot (isso é a Fase 7, com "vai").
