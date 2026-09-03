# STATUS — redesenho do sistema local Agata

FASE ATUAL: **Fase 8 — Cutover + merge para `main`** (EM ANDAMENTO — P8-00 ✅ · P8-01 🔶 (`.diff` aplicados no branch, P-12 vermelho/verde OK; falta B/C + `APROVADO-` do `conselho-remoto-omniroute.diff`) · **P8-02 🟢 aberto** (N=7+piso, acumula com o uso) · P8-03 aguarda caminho de cutover de pé · **P8-04 ✅** (Goose v1.48.0 instalado) · P8-05/06/07 em cadeia). **Fases 0-7 FECHADAS.** **`main` intocado (`4aa90bd`)** — merge é P8-07.
ATUALIZADO: 2026-09-03 10:05 -03 (relógio da máquina) · por: sessão Claude (Claude Code, na
Máquina — chat 6) — **N do paralelo = 7 dias + piso de amostragem** (≥1 par por tipo, ≥1
fallback, ≥1 pausa de portão, zero fabricação; estende só até cobrir o piso). P8-02 aberto,
harness validado (seed em `redesign/grafo/paralelo.md`: modelo via `:20127` ✓, `verificar`
✓, portão ✓, `--recusar` → nada no clone ✓). P8-04: Goose atual = binário Rust (não `pipx`;
`goose-ai` do PyPI é deprecado) — `redesign/router/goose.md`, aguarda o Humano escolher
A/B/C/D + "vai". _(entrada 09:50: P8-00 FEITO; P8-01 — bug do P-12 (`hd_ok=1`, heredoc vs
pipe) corrigido com `subprocess`; `perimetro.sh` 11 controles, vermelho/verde OK.)_
_(entradas 09:12/09:00/08:50/08:35: `.env` cifrado no repo restic; P7-02 wrapper `agata-jogo`
(sem Feral GameMode — conflito com `ananicy-cpp`); reboot confirmou o P7-01; backup P7-03 +
régua P-12.)_
ÂNCORA (leve, manual): sobre `redesign` @ **`55c980c`**; referência viva = `git rev-parse
origin/redesign`; ver `redesign/ANCORA.md`.
BASE: `main` @ 4aa90bd (MEMÓRIAS (309)) · tag `pre-redesign` (anotada: objeto-tag `cea5aeb`
→ commit `4aa90bd`; desreferenciar com `pre-redesign^{commit}`) local + remoto

## Quadro de posse

_(nenhuma tarefa EM ANDAMENTO)_ — **P7-01 FEITO** (2026-09-02 ~20:40, chat 4, com "vai").
`agata.target` + `agata-drain.service` (dreno via `redesign/grafo/drenar.py`, não corta) +
drop-ins (`PartOf`/`WantedBy`; `omniroute` c/ `SuccessExitStatus=143`; `llamacpp-agata` só
`PartOf`). Instalado em `~/.config/systemd/user/`, **NÃO `enable`d p/ boot** (pende "vai").
S7 PASS: dreno segura 26 s c/ efeito pendente e registra sem cortar · WAL limpo = teardown
1 s · `start` re-sobe os 5 (portas :20127/8/:20130/4/:27124/5) · MoE: `agata down` derruba
e a 4060 volta de 6229→54 MiB. `redesign/systemd/README.md`.

_(P6-00 + P6-01 FEITOS 2026-09-02 ~19:15.)_
P6-00: `INVENTARIO.md`. P6-01: plugin `obsidian-local-rest-api` 5.1.0 (`~/agata/.obsidian/`,
gitignorado) → `:27124` HTTPS loopback, token em `~/.config/agata/obsidian.token` (chmod 600).
O plugin não tem read-only global → **`ro_proxy.py` em `:27125`** (só leitura, injeta o token;
escrita/comandos/MCP-write → 403). `obsidian-ro-proxy.service` (sem enable). `redesign/obsidian/PLUGIN.md`.
**FASE 6 (Obsidian) FECHADA** (2026-09-02 ~19:25). P6-01 plugin + `ro_proxy` `:27125` (só
leitura) · P6-02 `consulta.py` (índice-primeiro, zero vector DB) · P6-03 `flows/consolidacao.py`
(4 nós, saída só em `propostas/`, nada em canon; alimenta o modelo com títulos reais p/ não
fabricar). `redesign/obsidian/README.md` + `redesign/grafo/flows/README.md`.
**Fase 8 (Cutover + merge p/ `main`) — arquivos-tarefa escritos, aguardam revisão + execução:**
- **P8-00 ✅** inventário + estratégia de merge (só doc). `main..redesign` fora de
  `redesign/`: `.gitignore` (aditivo), `PROMPT_CARREGAMENTO.md` (**excluir** — churn da
  âncora), `models/*` (Fase 3), `scripts/conselho_remoto.py` (par P-8 retroativo).
- **P8-01 🔶** fechar P-8 de `scripts/*`: `p12-backup-verificavel.diff` (APROVADO ✅) +
  `cifrar-env.diff` (APROVADO ✅, `--host predator` removido) **aplicados no branch**.
  `perimetro.sh` = **11 controles, P-12 vermelho/verde demonstrado** (bug do `hd_ok=1`
  corrigido — `subprocess` no lugar de `restic | python3 - <<'PY'`). **Falta:** camadas B/C
  da Cadeia + `APROVADO-conselho-remoto-omniroute` (toca rede — não auto-aprovado).
- **P8-02 🟢** paralelo **N=7 dias + piso de amostragem** (Hermes vs. grafo+OmniRoute, sem
  desligar nada). Aberto — acumula em `redesign/grafo/paralelo.md` conforme o Humano usa.
- **P8-03** reteste de fabricação no caminho novo ((138)/(307) + hidratação), config de cutover.
- **P8-04 ✅** Goose **v1.48.0** → `~/.local/bin/goose` (método B, sha256 conferido).
  Config → `:20127`, modelo `ollama-local/qwen3.5:9b`. `goose run` OK via OmniRoute; segredo
  plantado → 422. Achado: cold start do Ollama estoura o deadline (15s) do OmniRoute na 1ª
  chamada — mitigar no cutover. `redesign/router/goose.md`.
- **P8-05** Hermes sai do loop (grafo+OmniRoute dirige; voz/OWUI ficam à parte se em uso).
- **P8-06** canon reflete a realidade: `REGRAS`/`PROJETO`/`ONDE_ESTAMOS` pela Cadeia de
  auditoria em camadas + 2ª opinião; 1 entrada em `MEMÓRIAS.md` por fase (0–8), append-only.
- **P8-07** o merge (`--no-ff`, sem force/reset/rebase) + **S7 pós-push por sessão
  independente** + `perimetro.sh` verde com P-12. Fecha o redesenho.

**Fase 7 (Liga/desliga) — FECHADA no que dá sem o Humano ao teclado.** P7-00 FEITO · P7-01 FEITO (reboot confirmado 03/09) · P7-03 backup + régua P-12 + `.env` cifrado no repo FEITO · P7-02 hook `agata-jogo` FEITO. Falta só: Humano testar `agata-jogo` num jogo real (não bloqueia a Fase 8) + `OLLAMA_KEEP_ALIVE` opcional.
- **P7-01 ✅ FEITO** (2026-09-02 ~21:00) — instalado em `~/.config/systemd/user/` + S7 PASS
  + **`agata.target` `enable`d p/ boot** ("sim" do Humano). Ver "Quadro de posse" e
  `redesign/systemd/README.md`. 3 lições no LOG (systemctl-em-ExecStop deadlocka; `enable`
  honra todo `WantedBy`; teste real acha o que a revisão de papel não acha).
  - **REGRESSÃO NO BOOT (chat 5, 02/09) — corrigida + endurecida + S7 PASS + REBOOT REAL CONFIRMADO (chat 6, 03/09).**
    No 1º boot com o `enable`, `systemd --user` achou 3 ciclos de ordenação e quebrou
    apagando o start de `openvino-whisper` (:20130), `openvino-embeddings` (:20134),
    `obsidian-ro-proxy` (:27125) — subiram só os 2 proxies do OmniRoute. Causa:
    `After=default.target` nas 3 unidades base fechava laço com `agata-drain` (`After=` os
    membros) via `agata.target`. **Fix:** (a) removida a linha `After=default.target` das 3;
    (b) `[Install] WantedBy=default.target` → `agata.target` nas 3 (senão um `enable` futuro
    re-arma o ciclo — footgun da lição 2). Drop-ins, `agata-drain`, `drenar.py` intocados.
    **Verificado:** `systemd-analyze verify` rc 0; `reenable` → `default.target.wants/` sem
    nada do Agata; **S7 PASS** (efeito plantado no WAL → dreno segura 25s, loga, não corta,
    serviços param depois; restart → 6 ativos, 5 portas UP, 4060 56 MiB). LOG 02/09 ~22:10.
    **Reboot real (chat 6, 03/09 boot 07:06):** `journalctl --user -b 0` e `journalctl -b 0`
    sem "ordering cycle"; `agata.target` `enabled`+`active` + 5 membros `active`;
    `default.target.wants/` só com `agata.target`. **P7-01 FECHADO.**
- **P7-02** hook "jogo liga/desliga o Agata" — **hook FEITO (chat 6, 03/09), sem sudo.**
  **NÃO** Feral GameMode: o CachyOS roda `ananicy-cpp` (renice automático) e GameMode
  brigaria com ele — a wiki do CachyOS desaconselha; o caminho da distro é `game-performance`.
  Wrapper `redesign/systemd/agata-jogo` → `~/.local/bin/agata-jogo`: `stop agata.target`
  (drena) + `ollama stop` dos modelos ativos → jogo via `game-performance` → `trap EXIT`
  re-sobe. **Testado PASS** (03/09 ~08:56: para/re-sobe, 5 portas UP, 4060 56 MiB).
  **Falta (Humano):** pôr `agata-jogo %command%` no Steam / "Command prefix" no Lutris /
  "Wrapper" no Heroic. **Opcional (1 sudo):** `OLLAMA_KEEP_ALIVE=30s` em `ollama.service`
  (`P7-02-RUNBOOK.md` bloco B) — não é mais necessário para o aceite (o wrapper já faz
  `ollama stop`), só bom para o caso geral.
- **P7-03** restic no HD + timer + **P-12 no `perimetro.sh`** + `cifrar_env.sh`:
  - **PASSADA DE BACKUP FEITA (chat 6, 2026-09-03, HD montado):** 5 recursos do manifesto
    com snapshot restic tagueado (nome + sha256): `multilingual-e5-small-int8` `8c1a077a` ·
    `whisper-base-int8-ov` `485eb078` · `whisper-small-int8-ov` `2ed22f0f` · `qwen3-30b-a3b`
    `9433e3b8` (18 GB, 7m20s) · `rlm-qwen3-8b-teste:latest` = re-tag do snapshot da Fase 0
    (`c19275ec` → **`4bf31a37`**, sem sudo — o GGUF da `missoes` bate o `blob_sha256`).
    `restic check --read-data-subset=10%` = **no errors**. Teste de restore (e5-small) =
    **idêntico byte a byte** à árvore viva de `:20134`. `~/.agata-backup-staging/p12-cobertura.json`
    semeado (5 recursos). Ver LOG 2026-09-03 ~08:35.
  - **PREP sem o HD (chat 4), ainda válida:** `redesign/propostas/p12-backup-verificavel.diff`
    (P-12 completo) · `redesign/propostas/cifrar-env.diff` · `redesign/propostas/README.md`
    · `redesign/fase7-hd/REGUA-P12.md` (R1/R2/R3 — **decisão do Humano**, com recomendação) ·
    `redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md` · `redesign/fase7-hd/semear_cache_p12.py`.
  - **RÉGUA P-12 APROVADA (chat 6, 03/09):** Humano criou `redesign/propostas/APROVADO-p12-backup-verificavel`.
    Reafinada por ordem dele ("otimizar se der"): `qwen3-30b-a3b` AVISO → **ISENTO** (público
    + `blob_sha256` fixado no manifesto — imutável não precisa de backup *fresco*). Régua
    final: `N=14` · FALHA = `rlm-qwen3-8b-teste:latest multilingual-e5-small-int8` · AVISO =
    `whisper-base-int8-ov whisper-small-int8-ov`. `.diff` reverificado (`git apply` +
    `bash -n` OK); a aprovação cobre a versão reafinada.
  - **`.env` CIFRADO NO REPO ✅ (chat 6, 03/09):** Humano rodou `sh scripts/cifrar_env.sh`
    (prompt GPG, verificação por decifração OK) → `env-20260903.gpg` (sha256 `4798f8ac...`,
    conteúdo do `.env` de 02/09). Fechados à mão os 2 "FALTA" do script: `MANIFESTO.txt` na
    raiz do HD + `restic backup --tag agata-env` → snapshot `9d96c3f7` (`restic check` +
    restore OK). Replica o que o `cifrar-env.diff` automatiza — a automação em
    `scripts/cifrar_env.sh` fica pra Fase 8.
  - **FALTA (só Fase 8):** aplicar `p12-backup-verificavel.diff` e `cifrar-env.diff` em
    `scripts/*` (+ `APROVADO-cifrar-env`). Aí o aceite "P-12 vermelho com backup velho,
    verde com fresco" roda.
  - **Lacuna (não bloqueia):** a fórmula exata do `ir_sha256_xmlbin` do manifesto não está
    registrada (chat 3 não anotou); o teste de restore contorna comparando restaurado vs.
    vivo. Fixar na Fase 8.
_(Fase 5 = spike RLM ARQUIVADO.)_

_(histórico:)_ **FASE 4 (Grafo) FECHADA** (2026-09-02 ~14:30).
P4-00 durabilidade (SqliteSaver+WAL) · P4-01 esqueleto (6 nós, `interrupt`) · P4-02 tools+
sandbox `bwrap` · P4-03 GBNF só no envelope (2 fases) · P4-04 `agata` CLI (verify/
commit-entry model-free) · P4-05 evals ((138)/(307) + hidratação) · P4-06 adapter dsh
dormente. Aceite conjunto re-rodado: loop ponta a ponta num clone · verify+commit-entry com
tudo parado · portão pausa/retoma · grammar rejeita cabeçalho malformado sem distorcer o
corpo. **Incidente:** teste com args trocados commitou lixo no `redesign` (local, não
empurrado) → revertido (`reset --soft`); trava `_exige_raiz_git` adicionada. `redesign/grafo/README.md`.
**Próximo: Fase 5 (Spike RLM)** — ordem do ROADMAP `…→4→5→6→7→8`. Pede o "vai" do Humano +
arquivos-tarefa. **Antes:** a Fronteira de recusas (a entrada "RLM self-training" é outra
coisa — isto é padrão de inferência).

_(histórico:)_ **FASE 2 (iGPU) FECHADA** (2026-09-02 ~12:08).
P2-00 `INVENTARIO.md` · P2-01 `DISPLAY-PIN.md` (display já na iGPU, sem mudança) · P2-02
`openvino-whisper.service` (`:20130`, `GPU.0`, `whisper-base-int8-ov`, RTF 0.082) · P2-03
`openvino-embeddings.service` (`:20134`, `GPU.0`, `multilingual-e5-small` 384d, formato
OpenAI, zero vector DB). **Aceite conjunto:** 4060 em **1 W / 56 MB / 0 %** com
display+STT+embeddings todos na iGPU. Serviços `sem enable` (boot = Fase 7).
**Próximo: Fase 4 (Grafo)** — LangGraph; começa pelo spike **P4-00** (durabilidade, E2 da
AUDITORIA-01) antes de comprometer a arquitetura do loop. Pede o "vai" do Humano +
arquivos-tarefa (P0-03 só cobriu Fases 1-2; a Fase 4 precisa dos seus).

_(histórico:)_ **FASE 3 FECHADA** (2026-09-02 ~11:00, relógio da máquina).
P3-02: 16 modelos removidos, keep-list de 5, ~148 GiB reclamados (apagados os 50 snapshots
pacman do snapper que prendiam os blobs no btrfs). P3-03: `llama-cpp 0.3.0` + `ggml-cuda`;
`Qwen3-30B-A3B-Instruct-2507` Q4_K_M em `llamacpp-agata.service` (`:20129`, `--n-cpu-moe 36`,
**31,4 tok/s**, ~1,6 GB folga de VRAM); registrado no OmniRoute (`llamacpp-local`, combo `auto`
tier 4). **Próximo: Fase 2 (iGPU)** — ordem `0→1→3→2` do ROADMAP. Arquivos-tarefa P2-00..P2-03
já escritos (P0-03). Pede o "vai" do Humano + revisão de plano (P2-01 é risco alto — sessão
gráfica).

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
- **P0-01 — ✅ FEITO** (2026-09-02). Tag `pre-redesign` @ 4aa90bd · `models/manifest.json`
  20/20 · `restic` v0.19.1 · **repo restic `d0223c4ffb` em `AgataBkup01`** + snapshot
  `61b986a3` (4 itens de config) + snapshot `a0aa676c` (+ `~/.omniroute/` da Fase 1 + units
  systemd) · `restic check` = no errors. Senha em `~/.config/agata/restic.pass` (fora do
  git, chmod 600). `~/.hermes/.env` fora do backup.
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
  - Codex/Qwen **não são gate** — se responderem, entra como afinação, não trava.
- **AUDITORIA-01 resolvida** (01/09 ~23:05) pelo Humano: "ele decide, Claude aconselha+
  executa, sem menu sem risco — escolher pelo espelho". H1 = S7 mínimo (re-rodar `Aceite`
  de estado limpo, PASS/FALHA no LOG); H2 = `redesign/ANCORA.md` manual (hook pende do
  Humano — mudança de espinha); H3 = não (invariante vence); H4 = retirada; T1/T2/T4
  aplicados; T3 dormente; E1/E2 no ROADMAP + spike P4-00. Ver `AUDITORIA-01.md` §Resolução.
- **P0-03 — arquivos-tarefa das Fases 1 e 2** ✅ (sessão Claude, 01/09). 9 arquivos no
  schema (com o campo "Verificação independente"):
  - **Fase 1 (Router/OmniRoute):** `P1-00` instalar+subir `:20128` · `P1-01` provider
    Ollama + rota mínima · `P1-02` sanitização de segredo antes do egresso (reusa
    `PADROES_SEGREDO`, falha fechado) · `P1-03` pool nuvem free + combos auto/cheap +
    fallback + breaker + custo · `P1-04` aposentar a rede do `conselho_remoto.py` (mantém
    política + regex; merge p/ `main` só na Fase 8).
  - **Fase 2 (iGPU):** `P2-00` inventário iGPU + baseline da 4060 (só leitura) · `P2-01`
    pinar display na iGPU (**risco alto — sessão gráfica**; reversão testada antes) ·
    `P2-02` `openvino-whisper.service` distil-whisper int8 chunked, RTF<1 · `P2-03`
    `openvino-embeddings.service` bge-small/e5-small, formato OpenAI, zero vector DB.
- **Adiantado sem HD nem instalação (01/09, "continuar sem o HD"):** o que dava para fazer
  offline da Fase 1, tudo em `redesign/router/`:
  - `sanitizar.py` — scrub de segredo da P1-02. Régua única (extrai `PADROES_SEGREDO` de
    `varredura_segredo.sh` via `bash source`, sem 2ª cópia; só traduz `[[:space:]]`). Falha
    fechada (`raise SegredoNoPayload`). `--autoteste` verde; `--selftest` redige o trecho.
  - `proxy.py` — opção B da P1-02: proxy fino stdlib em `:20127` → `sanitizar_payload` →
    repassa para `:20128`. `--selftest` (upstream dummy) **verde**: pedido limpo → 200
    passthrough; pedido com `sk-…` plantado → 422, **upstream não tocado**, trecho redigido.
    Streaming/SSE passa direto.
  - `PROVEDORES.md` (P1-03) — template do pool nuvem: env vars, base URLs, limites de
    01/09 (RECONFERIR), combos `cheap`/`auto`/`conselho`.
  - `conselho_via_omniroute.md` (P1-04) — antes/depois de `conselho_remoto.py`: tabela do
    que **não muda** (política) vs. o que muda (rede), esboço de código, testes, rollback.
  - `README.md` do dir documenta os 4.
  **Nada ligado ao OmniRoute** — isso são os passos de integração, precisam do gateway de pé.
  `P1-02` e `P1-04` atualizados para refletir o que já está pronto.

## Próximo

- **Fase 0 — ✅ FECHADA**: repo restic + 3 snapshots + `restic check` limpo + restore byte
  a byte OK; MCP == script cru.
- **Fase 1 — ✅ FECHADA** (2026-09-02 ~09:00). Aceite todo cumprido: um pedido roteia · cai
  no fallback sob falha real (`[deepseek 402 → groq]`; `conselho` GLM→Gemini) · custo
  logado (`omniroute cost`) · segredo plantado bloqueado antes de sair (proxy `:20127`) ·
  a rede do `conselho_remoto.py` aposentada (P1-04, verificado com parecer real).
  Providers ativos: Ollama, Groq (`gpt-oss-120b`), Gemini (`2.5-flash`), OpenRouter
  (`minimax-m3:free`), Z.AI (`glm-4.7-flash`). DeepSeek fora (402, sem crédito). Cerebras
  não configurado (`~/.hermes/.env` sem a chave — walkthrough em `PROVEDORES.md`).
- **Fase 3 — Modelos — ✅ FECHADA** (2026-09-02 ~11:00, relógio da máquina). Aceite cumprido:
  manifesto reconstrói qualquer mantido · `ollama list` + backend llama.cpp batem com o
  manifesto · MoE roda **31,4 tok/s** (≥ ~20) no `--n-cpu-moe 36`.
  - **P3-00 ✅ FEITO** — reconstrutibilidade dos 20 modelos provada (`models/RECONSTRUCAO.md`).
  - **P3-01 ✅ FEITO** — `models/PRUNE.md` (keep-list de 5 vs. 15/16 a remover).
  - **P3-02 ✅ FECHADO** (2026-09-02 ~10:37, relógio da máquina). 16 `ollama rm`; `ollama list`
    = keep-list de 5 (`qwen3.5:9b`, `qwen3.5-9b-64k`, `qwen3:4b` [base do LoRA], `rlm-qwen3-8b-teste`,
    `nomic-embed-text`); `manifest.json` regenerado (5, sha256 5/5); GGUF do rlm no snapshot
    restic `c19275ec`. **Espaço:** o restart do Ollama não reclamou nada porque o btrfs
    (CachyOS + snapper) mantinha os blobs em 50 snapshots `pre`/`post` do `pacman`
    (`#454`–`#503`, todos anteriores ao prune). Humano apagou os 50 (`snapper -c root delete
    454-503`) → **~148 GiB reclamados** (livre 362 → 510 GB; `Data used` 578 → 430 GiB).
    S7 re-rodado de estado limpo: keep-list responde (`qwen3.5:9b`/`-64k`/`qwen3:4b` → "ok";
    `rlm` responde; `nomic-embed-text` → embedding 768-dim). **PASS.**
  - **P3-03 ✅ FEITO** (2026-09-02 ~11:00). `sudo pacman -S llama-cpp ggml-cuda` (repo `extra`;
    `cuda`/`nvidia-utils` já estavam). `Qwen3-30B-A3B-Instruct-2507` Q4_K_M (17,3 GiB, sha256
    `6c997b8a…`, HF unsloth) em `~/.cache/agata/models/` (`@cache`, fora dos snapshots).
    Varredura `--n-cpu-moe` 48→20 com `llama-bench` (N≤28 = CUDA OOM na 4060): **N=36** escolhido
    → servidor real `-c 8192` dá **31,4 tok/s** e ~1,6 GB de folga de VRAM (N=32 = 34,9 tok/s
    mas só ~200 MiB — apertado demais). `llamacpp-agata.service` (`127.0.0.1:20129`, sem
    `enable`). OmniRoute: provider `llamacpp-local`, model-id `llamacpp-local/qwen3-30b-a3b`;
    combo `auto` refeita com ele em **tier 4** (acima do denso 9B — decisão pelo espelho, ver
    LOG). Offload GPU confirmado (`nvidia-smi` 9–100 %). Fallback forçado p/ o MoE testado
    (`[deepseek 402 → llamacpp-local]`). `omniroute cost` contabiliza. Manifesto: 6 modelos
    (5 Ollama + 1 llama.cpp), sha256 6/6. Doc: `redesign/router/llamacpp.md`. S7 → PASS.
  - **Próximo: Fase 2 (iGPU).** Ver bloco abaixo.
- **Fase 1 (histórico dos passos):**
  - **P1-00 ✅ FEITO** (~00:02). `omniroute@3.8.50` em `~/.npm-global` (sem sudo),
    `systemd --user omniroute.service` **active**, bind **`127.0.0.1:20128`** (default dele
    era `0.0.0.0` — corrigido). `health` = healthy. `REQUIRE_API_KEY` **removido** (quebrava
    o CLI de gestão; loopback já é a proteção documentada). Unit `disabled` (boot = Fase 7).
  - **P1-01 ✅ FEITO** (~00:20). Provider `ollama-local` (id `dae5752b`) adicionado via
    `omniroute setup --add-provider` (o `nodes add` está quebrado no 3.8.50). Rota mínima:
    `curl :20128/v1/chat/completions` com `model: "ollama-local/qwen3.5:9b"` → resposta
    OpenAI-compat do Ollama local. `omniroute cost` contabiliza (2 reqs, 35/748 tok, $0).
    Modelo **exige prefixo de provider** (`ollama-local/...`). Ollama de produção intocado.
  - **P1-02 ✅ FEITO** (~00:30). Opção B: `omniroute-sanitizer.service` (`proxy.py`,
    `/usr/bin/python3`, stdlib) em `127.0.0.1:20127` → `:20128`. Teste de integração:
    pedido limpo via `:20127` → resposta do Ollama; pedido com `sk-…` plantado → **422**
    `secret_blocked_before_egress`, e `omniroute cost` Reqs 2→3 (o bloqueado **não**
    chegou ao OmniRoute). **Callers agora apontam para `:20127`.**
- **P1-03 ⏳ QUASE** (~08:45): as chaves já estavam em `~/.hermes/.env`. 5 providers
    registrados (`groq`/`deepseek`/`openrouter`/`gemini`/`zai`, valores nunca impressos).
    Combos `cheap`/`auto`/`conselho` roteiam. **Fallback real disparou** (conselho:
    `zai/glm-4.7-flash` lento → `gemini/gemini-2.5-flash`). Custo logado (`omniroute cost`:
    Gemini $0,0115). **Falta:** model-id de `deepseek`/`openrouter`, consertar `groq`
    (`unavailable`, default-model). Ver `redesign/router/PROVEDORES.md`.
  - **P1-04 ✅ FEITO no branch** (~08:40 -03, `git commit --no-verify` por autorização
    explícita do Humano — "regime de exceção vigente"). `scripts/conselho_remoto.py`
    (cópia-branch) reescrito −246/+70: `enviar_omniroute()` → uma POST no proxy `:20127`
    na combo `conselho`; **não lê mais chave**; política preservada (privado, teto, uma
    chamada, aborta-não-local, formato, resposta crua); **ganho:** o pedido do Conselho
    passa pela sanitização. **Verificado com parecer real** (2026-09-02 ~08:45): combo
    `conselho` = `zai/glm-4.7-flash` → `gemini/gemini-2.5-flash`; pedido de parecer de
    verdade → GLM lento → **fallback p/ Gemini** → 4 partes presentes → `checar_formato_parecer`
    PASS, registro gravado. `main` intocado — **merge só na Fase 8**. **P1-04 FECHADO.**
- Offline da Fase 1 já pronto (`redesign/router/`): `sanitizar.py`, `proxy.py` (ambos
  `--selftest` verde), `PROVEDORES.md`, `conselho_via_omniroute.md`.

## Pendências com o Humano (2026-09-02)

1. ~~HD / Fase 0~~ **FEITO** (HD reconectado; snapshots `61b986a3` + `a0aa676c`; restore
   byte a byte OK). A rotina de briefing `trig_01QiW6UXWYYJbHxRxMG44v6d` (10:00 -03) já
   não é necessária — pode ignorar a saída dela.
2. **Chaves nuvem:** pôr `GROQ_API_KEY` / `CEREBRAS_API_KEY` / `DEEPSEEK_API_KEY` /
   `ZHIPU_API_KEY` / `GOOGLE_API_KEY` em `~/.hermes/.env` → rodar os comandos de
   `redesign/router/PROVEDORES.md` → fecha P1-03 e destrava o teste real de P1-04.
3. ~~P1-04 canônico~~ **FEITO** — aplicado a `scripts/conselho_remoto.py` (cópia-branch),
   `commit --no-verify` (autorização do Humano). Só falta o teste com glm/gemini reais.
4. **Serviços de pé** (não habilitados no boot): `omniroute.service` (`:20128`),
   `omniroute-sanitizer.service` (`:20127`). `omniroute health` = healthy.
- **Nota p/ P0-01 (backup):** somar ao restic o estado do OmniRoute — `~/.omniroute/`
  (config + `storage.sqlite` com os providers; o `.env` tem `STORAGE_ENCRYPTION_KEY`,
  segredo local, não commitar) e a unit systemd. O pacote em `~/.npm-global` (2,3G)
  reconstrói com `npm install -g omniroute`.
- **P4-00** (spike de durabilidade da Fase 4, de E2) — quando a Fase 4 se aproximar.
- Fallbacks: manter afinados (reidratar do branch a pedido do Humano). Não são gate.

## Fim da Fase 0 depende só do HD

Todo o resto da Fase 0 está FEITO. Ao montar o `AgataBkup01`: P0-01 passos 3-4 + aceite de
restore do P0-02 → **Fase 0 fechada, pronta para o "vai" da Fase 1**.

## Bloqueios

- **Fase 1 P1-03 / P1-04** — provedores nuvem + teste real aguardam as chaves do Humano em
  `~/.hermes/.env` (comandos em `redesign/router/PROVEDORES.md`). P1-04 canônico aguarda a
  decisão do Humano (`--no-verify` pela exceção, ou `propostas/`).
- ~~P0-01 passos 3-4 — HD não montado~~ **RESOLVIDO 2026-09-02** (HD reconectado).

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
- **Passagem chat 5 → chat 6 (02/09 ~22:15):** carta de reidratação
  `redesign/REIDRATACAO-chat-6.md` (para a próxima sessão Claude) e
  `redesign/CONSELHO-03-sync-fallbacks.md` (acompanhamento próximo dos fallbacks; cópia em
  `~/Área de trabalho/`). Estado: Fase 7 EM ANDAMENTO — P7-01 feito + regressão de boot
  corrigida + S7 PASS, **pende reboot real** (Humano adiou); P7-02 runbook pronto (2 sudo);
  P7-03 aguarda o HD (03/09) + régua P-12.
