# PROJETO.md — Agata (estado corrente)

Este arquivo é o **agora**. É editável e trocável sem mexer nas REGRAS.
Se algo aqui contradisser MEMÓRIAS, MEMÓRIAS ganha: lá está o que aconteceu, aqui está o que vale hoje.
Se algo aqui contradisser a Máquina, a Máquina ganha — e a correção vira entrada nova em MEMÓRIAS.

<!-- ANCORA-SHA:INICIO (gerado por .githooks/pre-commit -- não editar as linhas abaixo à mão, o resto do arquivo é livre) -->
  SHA do commit ANTERIOR a este arquivo (limite conhecido: normalmente 1 commit atrasado; se o hook que grava esta linha falhar, pode ser mais -- ver a nota logo abaixo deste bloco, e PROJETO.md, "Memória e hidratação"): 58e611e4be9848ab6086e352fab185f5ca4300a2
  Escrito em: 03/10/2026 18:51 -03
  URLs raw pinadas neste SHA (preferir estas -- imutáveis, sem risco de cache velho; mesma defasagem máxima do SHA acima):
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/58e611e4be9848ab6086e352fab185f5ca4300a2/REGRAS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/58e611e4be9848ab6086e352fab185f5ca4300a2/PROTOCOLOS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/58e611e4be9848ab6086e352fab185f5ca4300a2/FALHAS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/58e611e4be9848ab6086e352fab185f5ca4300a2/PROJETO.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/58e611e4be9848ab6086e352fab185f5ca4300a2/MEMÓRIAS.md
<!-- ANCORA-SHA:FIM -->
<!-- Bloco de máquina (MEMÓRIAS (378)): SHA do commit anterior + URLs raw pinadas. Um leitor OFFLINE compara este SHA entre REGRAS.md, PROJETO.md e MEMÓRIAS.md -- se os três não baterem, a cópia é inconsistente (arquivos de commits diferentes). Numa interface que renderiza markdown estes comentários somem. Limite: normalmente 1 commit atrasado (auto-referência); mais se o hook falhar. -->


Como ler: cada seção diz **o que vale hoje** e **onde está a fonte viva** (script, config, Máquina). A história de como se chegou aqui está em MEMÓRIAS, citada entre parênteses no fim da frase. O texto anterior a 02/10/2026 está verbatim em `extras/arquivo/PROJETO-ate-2026-10-02.md`.

## O que é
Nome do sistema: Agata

Fonte única do nome falado (Fase 2, plano de replicabilidade, 25/09/2026 — parecer do
laboratório-nuvem "Ensaio"). Todo lugar onde `{{NOME_SISTEMA}}` aparece (REGRAS.md,
PROMPT_CARREGAMENTO.md, `.agents/skills/*/SKILL.md`) resolve pra este campo — inclusive
lendo o arquivo cru, sem script nenhum: a regra de resolução está escrita junto do token em
cada um desses arquivos. Campo ausente (clone com PROJETO.md ainda vazio) = usa "Agata".
Nunca edite os caminhos internos (`~/.config/agata/`, nomes de serviço) por causa deste
campo — só o nome falado muda.

Assistente pessoal do Orusoua, local-first e grátis por padrão.
Agata = **espinha determinística (git + `scripts/` + `perimetro.sh`)** + governança canônica
(REGRAS / PROTOCOLOS / FALHAS / PROJETO / MEMÓRIAS) + Conselho Federado de modelos.
- **Executor do loop:** grafo LangGraph + OmniRoute (redesenho mergeado na Fase 8, 03/09/2026 — (310)/(311)). Os modelos são trabalhadores substituíveis; nenhuma ferramenta É o sistema.
- **Frentes:** LibreChat (conversa, aponta no `seth_gateway` `:20126`), Goose (agente/código) e voz (piper-tts). Ver "Interface".
- **Acesso remoto:** LibreChat por `tailscale serve --bg 3080` (só tailnet, nunca `funnel`), hostname do tailnet em `~/librechat/.env` (`DOMAIN_CLIENT`/`DOMAIN_SERVER`, `TRUST_PROXY=1`) (350). Aviso conhecido do `tailscale status`, não bloqueante: `systemd-resolved` e `NetworkManager` "wired together incorrectly" — MagicDNS pode falhar; hostname completo e IP funcionam.

Grafia canônica do nome: **Agata** — sem acento, sem "h". A história migrada usa grafias antigas; não se corrige história.

## Máquinas
- **Predator** (master — CachyOS, fish, i7-13650HX, 40GB RAM, RTX 4060 8GB): grafo + OmniRoute, LibreChat, Ollama, git, Obsidian, web.
  - **Boot:** GRUB é o bootloader ativo (Limine saiu na recuperação de 17/09/2026); `mkinitcpio` com `lvm2` logo após `block` (raiz em LVM sobre 2 NVMe, Btrfs); kernel de reserva `linux-cachyos-lts` com preset e `initramfs` (435).
  - **Suspensão:** S3 (`deep`) por `/etc/systemd/sleep.conf.d/10-agata-deep.conf` (`MemorySleepMode=deep`), com driver NVIDIA 615 open (`NVreg_UseKernelSuspendNotifiers=1`). O GRUB ainda tem `mem_sleep_default=s2idle` e não tem `nowatchdog` (101), mas o arquivo do systemd vence na suspensão. Desfazer: `sudo rm /etc/systemd/sleep.conf.d/10-agata-deep.conf` (540).
  - **Vigiar:** suspender e acordar em loop (124); se voltar, procedimento em `PROCEDIMENTO_LOGIN.md`. Ruído conhecido: o teclado USB externo (`1-10.3`) reconecta sozinho no resume. A contenção antiga `predator-suspend-inhibit.service` está desabilitada (540).
  - **Discos:** SMART `PASSED` nas duas NVMe (24/09/2026); `Unsafe Shutdowns` altos são o padrão de desligamento não-limpo deste hardware (539). Causa raiz desse padrão: não fechada.
  - `/etc/default/grub.bak.20260812-155431`: rede de segurança das mitigações de GRUB; não apagar sem boot limpo confirmado (101).
- **Orusoua** (réplica Windows 11, leitura/failover) — *planejado*.

## Ambiente Operacional
- **Shell do Humano:** `fish`. Rejeita heredoc POSIX (`cat <<'EOF'`); para escrever arquivo: `printf ... | tee`/`sudo tee`, ou `bash -c '...'` / scripts `.sh` (149).
- **Shell do Claude Code nesta Máquina:** `zsh` — heredoc funciona. A restrição acima vale para o shell interativo do Humano e para executor que herde `fish` como login (149).

## Cérebro
Fonte viva da ordem dos modelos: o próprio OmniRoute (`/api/combos`) e `config/modelos-gratuitos.md` — não este texto.
- **Seth (conversa e agente):** cascatas grátis do OmniRoute (`strategy: priority`). Remotos primeiro, Ollama no fundo (546)/(547); desde 03/10/2026 sem Groq nas 3 filas do LibreChat e sem `llama-cpp/*` em fila automática nenhuma (648)/(649). Ordem viva por rota: `config/modelos-gratuitos.md`. Classificador heurístico no `seth_gateway` (só regras, ~µs) reescreve `model` **só** quando o Agent pede `seth-livre`: `seth-rapido` (<400 chars, sem tools, ≤2 msgs do usuário) · `seth-livre` (normal) · `seth-pesado` (>6000 chars, código ou >10 msgs). Todas as rotas terminam nos mesmos modelos confiáveis — rotear errado degrada, nunca quebra (416). Goose usa o combo próprio `seth-codigo`.
- **Local principal: `qwen3.5-9b-64k`** (Ollama, `custom:qwen-local-ctx-override`) — nunca a tag oficial `qwen3.5:9b`, que reproduz o bug de `num_ctx` (121). Convenção: `PARAMETER num_ctx 65536` em Modelfile próprio, tag `-64k`, porque o endpoint OpenAI-compatível do Ollama ignora `num_ctx` por desenho ([`ollama/ollama#16814`](https://github.com/ollama/ollama/issues/16814); (133)-(135)). VRAM de pico em uso real: 89-92% dos 8.188 MiB (log em `~/agata_vram_producao_*.log`). **Regime de auditoria** desde (140): cada resposta é auditada pelo Humano; sai do regime quando o Humano pedir, evento e não prazo (141).
- **Fundo local da cadeia da Seth:** `ollama-local/qwen3.5-9b-64k:latest`, pela connection `ollama-local` (`:11434`) do OmniRoute; entra só se todos os remotos falharem (402)/(403).
- **Locais sob demanda (`llama.cpp`):** `llamacpp-agata` (MoE `Qwen3-30B-A3B-Instruct-2507`, `:20129`, `--n-cpu-moe 36`, ~31 tok/s, `PartOf` sem `WantedBy`) e 4 modelos de 20/09/2026 — `nemotron-3.5-lightning` (geral), `qwen3-coder-30b-a3b` (código), `phi-4-mini` (leve), `gpt-oss-20b` (agentic, quant `ggml-org` MXFP4; o `unsloth` Q4_K_M trava o sampler). Um serviço systemd cada; não cabem todos ao mesmo tempo; com o local principal na GPU, subir outro pode falhar por VRAM — limite de hardware, não bug (611). **Fora de todo caminho automático desde 03/10/2026** (combos e Conselho Remoto, (649)): um que voltou sozinho depois de OOM empurrou o Ollama para a CPU (648). `llamacpp@.service` não tem `Restart` nem `[Install]`: só sobe à mão, depois de conferir `nvidia-smi`. Portas e ressalvas: `config/modelos-gratuitos.md`, `config/portas-agata.txt`.
- **`gemini-2.5-flash`** (Google API, grátis, ~20 requisições/dia): alívio quando o local falha (140).
- **Último recurso manual:** `llama3.1:8b` — sem tool-calling, fora da cadeia.
- **Limite de classe:** modelo local neste hardware tem teto de ~14b/9GB — `PROJETO_REFERENCIA.md`, "VM do Marcos".

## Serviços (boot)
Portas: `config/portas-agata.txt` é o manifesto que o P-4 confere contra o bind real — fonte da verdade, não esta seção. `:20131`/`:20132` pertencem ao próprio `omniroute` (426 e 404): `lacuna`, função não determinada (420).

**`agata.target`** (`systemd --user`, habilitado no boot) puxa:
- `omniroute` (`:20128`) e `omniroute-sanitizer` (`:20127` — os callers usam este; `sanitizar_payload()` em `redesign/router/sanitizar.py`, `--autoteste`, sanitiza segredo antes do egresso e bloqueia payload profundo ou largo demais (328)). `requestQueue.maxWaitMs = 45000` no banco do OmniRoute (362)/(363); clone novo herda o valor pelo drop-in `redesign/systemd/dropin-omniroute-resilience.conf` (`RATE_LIMIT_MAX_WAIT_MS`) (588).
- `openvino-whisper` (`:20130`, STT na iGPU) e `openvino-embeddings` (`:20134`, embeddings na iGPU); venv `igpu/.venv` com `torch==2.14.0+cpu`, sem libs CUDA.
- `obsidian-ro-proxy` (`:27125`, só leitura, `ro_proxy.py`) e `obsidian-app.service` (Flatpak `md.obsidian.Obsidian`, `After=graphical-session.target`) — o app é o **backend real** do proxy: com ele fechado, o proxy devolve **403** ("upstream inacessível"), que parece permissão negada e não é.
- `agata-drain` (oneshot: drena o WAL do grafo no stop, nunca corta um commit).

**Sob demanda pelo atalho `seth` / `Parar Seth`:**
- `seth-gateway` (`:20126`) — reidrata a Seth; ver "Interface".
- `seth-verificador` (`:20141`) — **único caminho de execução da Seth, read-only.** `POST /verificar` roda um de 10 comandos fixos (`perimetro`, `estado`, `git_status`, `git_log`, `git_diff_stat`, `git_sync`, `selos`, `suite_controles`, `servicos`, `p8_verificar`), argv fixo, sem shell, saída redigida pela régua do P-1, teto com total declarado (423).
- `seth-escriba` (`:20140`) — **único caminho de escrita da Seth, append-only.** `POST /memoria` insere abaixo do marcador `ENTRADAS-NOVAS` (número e data vêm do relógio da Máquina); `POST /diario` anexa a `SETH-DIARIO.md`; aborta com 409 se a operação não for insert/append puro; sem `PUT`/`PATCH`/`DELETE`, sem `git`, sem segredo; `fcntl.flock` + `os.replace`; fonte `redesign/router/seth_escriba.py` (318).
- Stack Docker do **LibreChat**: `librechat` na bridge `librechat`/`br-librechat`, publica só `127.0.0.1:3080` e fala com a Máquina pelo relé `librechat-ponte-host` (538); `librechat-mongodb` e `librechat-meilisearch` numa bridge privada; `restart: "no"` em tudo. Compose em `~/librechat/`, fonte em `redesign/librechat/`; o atalho `seth` sincroniza `librechat.yaml` e `data/mcp/canon-mcp.mjs` e reinicia o container só se algo mudou (401).
- `piper-tts` (`:8890`, voz pt-BR local) (387) · `discord-mcp` (`:20135`) e `navegador-mcp` (`:20136`), ver "Interface".

**Também no boot:** `ollama.service` (sistema, `:11434`) · `agata-consolidacao.timer`.

**Manuais:** `agata-warmup.service` pré-aquece o modelo local pesado (cold-start do Ollama). `agata-jogo` (`~/.local/bin/`) lança jogo com o Agata fora da RTX 4060, via `game-performance` da distro — **não** Feral GameMode, que briga com o `ananicy-cpp`.

**`agata-consolidacao.timer`** (220)/(311): 23:00 diário, `ExecStart` = `redesign/grafo/flows/consolidacao.py`. Saída só em `propostas/consolidacao-<data>.md` com entrada `(a numerar)`; nunca toca canon. Sob `ProtectSystem=strict` + `ProtectHome=read-only` + `ReadWritePaths` = `propostas/` + `~/.cache/agata/` — contenção de kernel, não de prompt. **`lacuna` carregada:** o resumo de 1 linha do log já alegou sucesso sem o arquivo existir — confira `propostas/`, nunca só o log.

**P-9** (221): `scripts/perimetro.sh` avisa (nunca falha) se estiverem `failed`, `disabled`/`masked` ou, no caso de container, fora do ar: `ollama.service`, `agata-consolidacao.timer`, `agata-pesquisa-modelos.timer`, os 5 membros do `agata.target` (`omniroute`, `omniroute-sanitizer`, `openvino-whisper`, `openvino-embeddings`, `obsidian-ro-proxy`), `seth-gateway.service`, `seth-escriba.service`, `piper-tts.service` e os containers `librechat`, `librechat-mongodb`, `librechat-meilisearch`. Motivo: foi a falta desse aviso que deixou a consolidação morta sem ninguém notar. Avisa também quando o Ollama tem modelo carregado só em parte na GPU (`/api/ps`, `size_vram < size`) e diz quem ocupa a VRAM (648)/(649) — todas as unidades estavam `active` enquanto a Seth rodava a 6,3 tok/s.

**Não recriar:** `agata.service`, `agatha.service`, `agata-rest.service` (ausentes, (107)/(539)), `hermes-gateway.service` (Hermes removido, (312)), `kokoro-tts` (removido, (593)/(594)).

## Memória e hidratação
- **Canônicos** em `~/agata`; o repositório git é também o cofre Obsidian. `MEMÓRIAS.md` é o canônico da história: DIÁRIO coletivo + blocos MOD por modelo + registro do Conselho, append-only. Camadas por período (Fase 4): quente `MEMÓRIAS.md` · morno `MEMORIAS-MORNO.md` · frio `memoria/frio/MEMORIAS-FRIO-<data>[-N].md`, congelado e selado (`git tag` + `scripts/selar.sh`, P-14); migração e verificação por `scripts/migrar_periodo.py` e `scripts/verificar_migracao_periodo.py` (357).
- **`ONDE_ESTAMOS.md`** — só para o Humano, nunca entra na hidratação. Uma tela, português simples, atualizado no mesmo commit de toda entrada que mude o estado (Regra 4) (196)/(197).
- **Hidratação.** O loop do grafo hidrata pelo nó `hidratar` = `scripts/estado_para_eco.sh` (fatos de Máquina: HEAD, topo de MEMÓRIAS, `sync`, `HASH-ESTADO`, `IDADE-HIDRATACAO` (338)) + `query_canon` / `consulta.py` (índice primeiro, sem vector DB) para profundidade sob demanda. O `.hidrata.md`, gerado no `pre-commit` por `.githooks/gerar-hidratacao.sh`, é referência, não a hidratação primária do loop. Sessões em nuvem carregam por `PROMPT_CARREGAMENTO.md`. O spike RLM (consulta vs. injeção) está arquivado: injeção venceu em fidelidade/custo (`redesign/LOG.md`).
- **Janela de MEMÓRIAS na hidratação:** entradas inteiras, nunca cortadas, até `JANELA_ORCAMENTO_CHARS=25000`, de cima para baixo a partir do marcador; se a primeira sozinha estourar, entra inteira mesmo assim. Depois dela, um resumo de 1 linha das mais antigas (`JANELA_RESUMO_ANTIGAS_CHARS=8000`, de `INDICE_MEMORIAS.md`) (215)/(338).
- **Silos por modelo:** construídos. O hook gera `.hidrata-<modelo>.md` por modelo-alvo (hoje só `seth`, usado pelo `seth_gateway` no modo `full`), cada um com só o MOD do seu modelo; arquivo único foi rejeitado porque vaza MOD entre modelos. O P-11 impede silo de entrar no canon, por nome, por conteúdo e contra renomeação (419). MOD em MEMÓRIAS: REGRAS, "O Conselho", item 3 (430).
- **Vault Obsidian derivado** (290): `memoria/obsidian/`, regerado por `scripts/gerar_obsidian.py` a cada commit (`post-commit`, gitignorado) — uma nota por entrada, regra, seção, script, controle P-N e proposta aplicada, mais MOCs e painel. Camada de leitura; a fonte é o canon. Não editar. Também: `obsidian-skills` oficial e `memoria/obsidian/memorias.base` (Obsidian Bases) (324); a Nota Diária do Obsidian (`AAAA-MM-DD.md`) é gitignorada para nunca publicar rascunho pessoal (329). Uso pela Seth (292): consulta dirigida a partir de `memoria/obsidian/INICIO.md` ou dos `moc-*`, nunca varredura. A listagem de diretório do `:27125` fica atrás do disco: para saber se uma entrada recente existe, **ler o arquivo** (`query_canon`), nunca concluir pela listagem — doutrina fixa do `seth_gateway`, `_DOUTRINA_FIXA` (391)/(400).
- **Busca:** sem RAG por embedding, de propósito — `rag_api`/`pgvector` não sobem (115)/(293)/(313). `scripts/busca_semantica.py` é ferramenta secundária, sob demanda, nunca injetada: boa para tema concreto, fraca para pergunta abstrata sobre o próprio sistema (327).
- **Âncora de integridade (1)-(62):** 128.671 B, sha256 `b26ac113f7a6f72c875391c2d07d94f6f6c827cc9d14c180ecc324b14ab4e03a`. Verificação por marcador de conteúdo (início/fim do trecho) + comprimento, nunca por offset ou número de linha (96)/(97). Script: `scripts/achar_ancora_1_62.py`.
- **`memoria/missoes/`** — quarto pilar, local por desenho: um arquivo por missão + `INDICE.md`, repositório git próprio sem remote, gitignorado do repo principal (`*.bundle` coberto em toda a árvore (97)/(98)), nunca público, nunca na hidratação; pesquisado sob demanda por quem tem acesso à Máquina. Achável pelo vault via `memoria/obsidian/moc-missoes.md` (325), exceto `segunda-camada/` (esfera pessoal, mais estrita). Relação com o bg-review desligado: `INDICE.md` local e (91)-(95).
- **Repositório oficial:** `https://github.com/agataseth98-cmd/agata-seth` (branch `main`). Sincronize contra ele no início de **toda** sessão; em sessões autônomas a sincronização falha em silêncio com frequência — verifique, não presuma.
- **Fonte canônica (URLs) e atualização.** Preferir as URLs raw **pinadas em SHA** que o bloco `ANCORA-SHA` traz (conteúdo endereçado por hash, sem cache velho) (253); `https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/main/<arquivo>` é fallback — o CDN pode servir conteúdo de 1-2 min atrás logo depois de um push (156). Onde há Máquina, `git ls-remote`/`git ls-tree` é o método 1 (`PROTOCOLOS.md`, "Verificação de canônico"). Comparar o SHA do prompt com `https://api.github.com/repos/agataseth98-cmd/agata-seth/commits/main` funciona, mas há interface de nuvem que bloqueia esse endpoint (217)/(250)-(254). `atualizar <REGRAS|PROJETO|MEMÓRIAS|TUDO>` = git pull + regenerar hidratação; nunca sobrescreve história; conflito → para e avisa.
- **Bloco `ANCORA-SHA`** (REGRAS, PROJETO, MEMÓRIAS, `PROMPT_CARREGAMENTO.md`): reescrito a cada commit por `scripts/atualizar_ancora_prompt.py` via `pre-commit` (226). Limite conhecido: um commit não embute o próprio SHA, então o valor é o do commit **anterior** — normalmente 1 atrasado; mais se o passo fail-soft falhar sem ninguém ver (277). Mitigação: o campo `Escrito em:`, comparável com a hora medida. Decisão do Humano: aceitar o atraso em troca de 100% automático. **Guarda de integridade:** o `pre-commit` compara o sha256 staged de cada canon (sem a âncora) antes e depois do laço; se mudar fora da âncora, desfaz o stage e bloqueia o commit (458)/(459).
- **Horário:** hierarquia e selos em `PROTOCOLOS.md`, "Regra 1.1". Modelo em nuvem sem shell mede por `code_interpreter` rodando `scripts/consultar_horario.py` (`urllib.request`, `?cachebust=<timestamp>`), nunca por `web_extractor`, que cacheia (273); não há segunda API automática (275).

## Interface
- **Executor / loop:** grafo + OmniRoute pelo CLI `agata` (`~/.local/bin/agata` → `redesign/grafo/cli.py`: `up`/`down`/`status`/`verify`/`commit-entry`/`run`/`resume`/`logs`).
- **`seth_gateway`** (`redesign/router/seth_gateway.py`, `:20126`, sob demanda) — reidrata a Seth antes do sanitizador; **qualquer frontend que aponte para `:20126` fala com a Seth hidratada.** Modo `compacto` (default): cabeçalho curto (identidade + Regra 1 + ponteiro para `query_canon`) + estado de `estado_para_eco.sh`. Modo `full` (o `.hidrata-seth.md` inteiro) só por configuração — ~45k tokens estouram o `maxWaitMs`. No request: filtro de chamada de título (411)/(433), roteador por complexidade (416), `ESTADO-ATUAL` fresco a cada turno (417). Na resposta: filtro de keepalive SSE (415) e o header `X-Modelo-Real`, carimbado pela Máquina a partir do `model` que o OmniRoute devolve (614).
- **LibreChat** (`127.0.0.1:3080`, Docker sob demanda) — conversa informal, aponta para `:20126`. Endpoint `agents` com o Agent `agent_4KlxSMeX5Y8cWQVODkJfH` ("Seth", provider `Seth` → model `seth-livre`, MCP `canon` anexado — MCP só se anexa a Agent) (415). `modelSpecs enforce: true`, spec default `seth-livre` → o Agent; specs `custom` só para debug. `titleConvo: true` (413). Memória do LibreChat desligada (`memory.disabled`) e sem RAG, de propósito: a hidratação vem do `seth_gateway`. Conta única (`ALLOW_REGISTRATION=false`); Meilisearch para busca de conversa. Config em `redesign/librechat/`.
- **Goose** (`~/.local/bin/goose`, `:20126`) — agente/código (`goose session`) e shell de fallback operacional; `model: seth-codigo` em `~/.config/goose/config.yaml` (combo próprio, sempre código, sem heurística de tamanho). Codex CLI terciário.
- **Voz:** piper-tts (`:8890`, pt-BR local, default desde (387)) + Whisper na iGPU. Remoto = HTTPS via Tailscale.
- **Escrita da Seth:** só pelo `seth-escriba` (append-only, sem commit); leitura pelo `canon-mcp`/`:27125` (read-only) (318).
- **Atalhos** (`~/Área de trabalho/`, scripts `~/.local/bin/seth`/`seth-parar`): **Seth** (sobe tudo e abre o navegador), **Seth (agente)** (Goose no terminal), **Parar Seth** (para as frentes; `agata.target` segue de pé). Integrações futuras (Home Assistant, WhatsApp) entram sob demanda, cada uma como servidor MCP.
- **Ponte Discord e controle de navegador** (339): `redesign/mcp/discord/` (poll, não push; egresso sanitizado por `PADROES_SEGREDO`) e `redesign/mcp/navegador/` (Playwright contra Brave real — não `browser-use`, cuja API sumiu na versão avaliada —, perfil isolado, escrita travada por allowlist de domínio em `~/.config/agata/navegador-dominios-permitidos.txt`). Sobem e descem com `seth`/`seth-parar` (`discord-mcp.service`/`navegador-mcp.service`, `redesign/systemd/`, sem `[Install]`). Transporte HTTP; o LibreChat os alcança por `172.29.7.1` (relé, (538)); `librechat.yaml`: `mcpSettings.allowedDomains: ["127.0.0.1", "172.29.7.1"]` — sem isso o LibreChat bloqueia MCP remoto (guarda contra SSRF).

## Segurança
- **Sandbox sempre.** Segredos só em `~/.config/agata/.env`, fora do repo, junto de `restic.pass`, `obsidian.token` e `google-project/` (312). Ver `CHAVES.md` (só o Humano abre). O OmniRoute não lê esse arquivo em runtime: as chaves ficam cifradas em `~/.omniroute/storage.sqlite`; o `.env` é a fonte para adicionar ou rotacionar provedor (`redesign/router/PROVEDORES.md`).
- **Nada deste sistema escuta em interface pública** — contenção de kernel, não de firewall, conferida por `ss -tlnp`. Os binds são `127.0.0.1` e, para os serviços que o LibreChat alcança, o relé `172.29.7.1` da bridge local do Docker (538); a lista com os binds de cada porta é `config/portas-agata.txt`, conferida pelo P-4. Fora do manifesto, também em loopback: `3080` LibreChat, `27017` Mongo, `7700` Meili e `27124` obsidian-rest. Fora disso só `tailscaled` — o acesso remoto legítimo.
- **Ollama (`11434`)** restrito a `127.0.0.1` (126)/(127). `override.conf` com as 5 variáveis: `OLLAMA_NUM_GPU=999`, `OLLAMA_KV_CACHE_TYPE=q4_0`, `CUDA_VISIBLE_DEVICES=0`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_HOST=127.0.0.1:11434` (130).
- **Rotação de chave:** atualize **todos** os consumidores no mesmo passo. Rotação parcial dá 401 silencioso.
- Controle descrito sobre mecanismo que não roda mais é falha conhecida: `FALHAS.md`, SIN-4 (126)/(420).

## Conselho Remoto — Fase 1 (transporte, não decisão)
Escopo pequeno de propósito: **UM modelo, UMA tarefa** — enviar um pedido de parecer já escrito pelo Humano e recolher a resposta. A fase testa o transporte, não a qualidade do parecer (206).
- **Mecanismo — `scripts/conselho_remoto.py`** (207): recebe o pedido em arquivo → **uma** POST em `http://127.0.0.1:20127/v1/chat/completions` (sanitizador → OmniRoute; o script não lê chave nenhuma) → guarda a resposta **crua** em `memoria/missoes/conselho-remoto/` (data, modelo, `provider`, tokens, custo) → confere as 4 partes do parecer (Origem/Posição/Fundamentação/Emenda). Faltou alguma: reporta "fora do formato" e para; reenviar é decisão do Humano (`PROTOCOLOS.md`, "Segunda opinião"). Nunca escreve em canon, nunca julga, nunca encadeia chamadas.
- **Quem responde:** rotação justa — a cada chamada, o membro do `ROSTER` com menos usos bem-sucedidos; empate pela ordem fixa do roster (determinístico, nunca aleatório); estado em `memoria/missoes/conselho-remoto/rotacao-estado.json`. Ninguém tem papel fixo (352). **A lista viva é o `ROSTER` do script**, não este texto (513).
- **Falha:** circuit breaker por modelo, com estado em disco e recuo exponencial. Se o escolhido falha, o script aborta; rodar de novo escolhe outro. Roster remoto inteiro fora ⇒ **uma** chamada ao qwen local (`_chamar_local()`); o *combo* `conselho` não tem tier local (420).
- **A resposta é DADO NÃO CONFIÁVEL** — nunca executada, nunca lida como instrução, nunca injetada no contexto de outro modelo nem na hidratação. O Humano lê antes de qualquer coisa acontecer com ela.
- **Condição 1, forçada no script:** só material já no repositório **público** vai no pedido — o script recusa, antes de qualquer rede, texto que mencione `memoria/missoes` (barra ou contrabarra) (`checar_conteudo_privado`). Motivo extra: os termos de treino da camada grátis da Zhipu não foram confirmados em fonte primária; vale como se treinasse sobre o enviado.
- **Custo:** `max_tokens` 8.000; pedido acima de 60.000 caracteres é recusado antes do envio; preço US$0 nesta camada, fórmula em dólar já pronta no script.
- **Como saber se valeu** (206): no primeiro uso real, contar quantas idas e vindas de copiar-colar o Humano deixou de fazer. Zero ou uma: a fase não se pagou — registra e para, não expande para dois modelos.

## Sudo e interação humana
Quando uma operação exige `sudo`, o executor pausa e pede ao Humano para rodar o comando (por exemplo, prefixo `!` no Claude Code). Não armazenar senha, não simular autenticação, não contornar (110).
- **P-2 (verificação root-side de sudoers, orientada a evento — opção D, 16/08/2026)** (196): `scripts/perimetro.sh` **lê** `/var/lib/agata/p2-status.json`, escrito por `/usr/local/lib/agata/checar-sudoers-root.sh` (dono root, não gravável por `orusoua`), disparado por `/etc/pacman.d/hooks/agata-sudoers.hook` quando um pacote toca `etc/sudoers.d/*`. Status ausente = SKIP; veredito negativo = FALHOU; positivo = OK com a data — idade não é alarme. Fonte versionada: `scripts/checar-sudoers-root.sh`, `scripts/agata-sudoers.hook`.
- **Lacuna coberta por runbook:** `visudo` à mão não dispara o pacman. Depois de qualquer `visudo`, rode `sudo /usr/local/lib/agata/checar-sudoers-root.sh` (194).
- Regra NOPASSWD órfã `/etc/sudoers.d/facer`: removida (192). Se o teclado RGB Acer voltar: script em `/usr/local/bin`, dono root, e só então a regra.

## Quarentena estrutural (P-8)
Texto completo: `propostas/README.md`. Fluxo prático: skill `agata-aplicar-proposta`.
- **Escopo, proporcional de propósito.** Sob quarentena — o que **muda comportamento**: a lista de `_p8_eh_comportamento` em `scripts/perimetro/p08_quarentena.sh` (canon normativo `REGRAS.md`, `PROTOCOLOS.md`, `FALHAS.md`, `PROJETO.md`, `CLAUDE.md`; `scripts/`, `.githooks/`, `config/`; o código de `redesign/`; `.agents/`, `.claude/`; a raiz de confiança `propostas/.allowed_signers`) (218)/(222). Sem quarentena — o que só **registra**: entradas de `MEMÓRIAS.md`, `ONDE_ESTAMOS.md`, `INDICE_MEMORIAS.md`, `.hidrata.md` (gerado) e `PROMPT_CARREGAMENTO.md`, que dirige um modelo mas sempre com um Humano colando e lendo a resposta. Motivo da linha: registro errado se corrige com entrada nova; comportamento errado, não.
- **Mecanismo.** A mudança vira `propostas/<nome>.diff`. O Humano lê e assina com `bash scripts/aprovar.sh <nome>`, que (`bash scripts/aprovar.sh <nome> ["motivo"]`) grava em `propostas/APROVADO-<nome>` a linha `diff-sha256:` e a assinatura ssh de `"<sha256 do .diff>  <nome>"` (namespace `agata-aprovacao-p8`, chave `~/.config/agata/aprovacao_ed25519` com passphrase, fora do repo) (365)/(366). **O executor nunca roda `scripts/aprovar.sh`.** Verificar não precisa da passphrase (`ssh-keygen -Y verify`). O P-8 falha o commit se um arquivo staged do escopo não tiver par `.diff`/`APROVADO-` assinado e batendo byte a byte; procura em `propostas/` e em `propostas/aplicadas/`, porque quem aplica move o par para `aplicadas/` no mesmo commit. A verificação usa sempre `HEAD:propostas/.allowed_signers`, nunca a cópia de trabalho — uma troca staged não autoaprova a própria troca; rotação de chave assina-se com a chave atual (367). Antes de aplicar: `scripts/p8_verificar.sh <nome>` (543).
- **Risco residual aceito, não suavizado:** (i) o Humano aprovar às cegas um `.diff` malicioso, inclusive de rotação de chave; (ii) chave privada mal guardada. P-8 impede automação agindo sem ninguém perceber — a ameaça real é desatenção, não malícia. Custo do ganho: a passphrase a cada mudança estrutural.

## Doutrina de defesa proporcional
Adotada pelo Humano, 17/08/2026 (201). Ferramenta de decisão situacional do Humano (Regra 3), não regra universal:
- Incidente é o que passa ao lado de um controle que o sistema declarou. O resto é risco de fundo: registra e segue.
- Defesa só entra se for mecânica e no limite. Vigilância humana permanente decai; mecanismo instalado não.
- Risco residual declarado é mais seguro que estado "seguro" não declarado.
- Fecha a classe, não o caso.
- Nenhuma checagem entra em hook antes de passar verde uma vez.

O formato de "pedido de decisão" (itens numerados, marcador de aguardando, ordem de execução) não é canonizado: canoniza-se a versão que sobreviver ao uso.

## Estado dos bugs e dos testes
Só o que segue aberto, ou deixou mecanismo vivo. Os fechados estão em MEMÓRIAS e, até 02/10/2026, verbatim em `extras/arquivo/PROJETO-ate-2026-10-02.md`.
- **OmniRoute lento sob provedor travado:** a conexão pooled para o provedor trava ~30s, fora do nosso controle. `maxWaitMs = 45000` só dá folga para a auto-recuperação terminar em vez de estourar `504`. Efeito residual: chamada isolada lenta (~45s), não falha; combos com fallback sofrem menos (362)/(363).
- **Cold-start do Ollama:** a 1ª chamada a modelo não carregado (~30s de load) pode estourar a fila; a 2ª responde em ~0,5s. Mitigação: `systemctl --user start agata-warmup.service` antes de usar o modelo local pesado.
- **Filtro de título do `seth_gateway`** (433): o sinal forte é o *schema* que o `@librechat/agents` exige (`response_format`/`tools` com propriedade `"title"`). Sem esse sinal, vale só o fallback: `messages[-1]`, `role in ("user","system")` e `len(messages) <= 2`. **Risco residual:** a string-gatilho como primeira mensagem de uma conversa nova ainda casa a condição de fallback — mesma classe de qualquer detector por conteúdo.
- **Hidratação suspeita na Seth** (sem bug confirmado com esse nome): `curl` no `:20126` forçando o caminho suspeito, capturar o payload que sai (o `--selftest` do gateway mostra o que `_injeta` monta) e testar em ordem: (a) não injetada, (b) injetada mas truncada, (c) recebida e ignorada (420).
- **Manifesto do HD:** a fórmula original de `ir_sha256_xmlbin` não reproduz. `redesign/fase7-hd/hash_ir.sh` fixa uma fórmula reproduzível daqui para frente; a garantia real é o teste de restore do restic (`diff -rq` restaurado vs. vivo).
- **Drift dos derivados de hidratação** (333): três arquivos derivados já voltaram a um estado velho; causa raiz não confirmada (hipótese: "Recuperação de arquivo"/"Sync" do Obsidian) — `lacuna` até o Humano checar dentro do app.
- Os protocolos TES-001/TES-002 foram aposentados em 09/09/2026 — (417); o que cobriam está em `PROTOCOLOS.md`, "Cadeia de auditoria em camadas", no P-7 e em `FALHAS.md`.

## Plano vigente (v1.1 — Fases 0–2 são compromisso; 3+ é bússola)
- **Fase 0 — Saneamento:** publicar no remoto as entradas acumuladas.
- **Fase 1:** blocos Conselho/MOD em MEMÓRIAS · REGRAS/PROJETO atualizados com segunda opinião ou risco assumido · rascunhos históricos → `docs/`.
- **Fase 2:** silos por modelo — construídos (ver "Memória e hidratação") · eco pós-carregar (`estado_para_eco.sh`, sem nonce).
- **Fase 3:** fechada. GLM membro pleno: superado pela rotação justa (352)/(355); válvula de discordância sintética: `scripts/checar_discordancia.sh`, P-13 (356).
- **Fase 4 — MEMÓRIAS por período:** implementada (357); a fila de aderência está fechada: `INDICE_MEMORIAS.md`/`INDICE_MEMORIAS_PALAVRAS-CHAVE.md`, `scripts/gerar_obsidian.py`, `scripts/busca_semantica.py` e `scripts/gerar_indice_derivado.py` cobrem quente+morno+frio (358). **Período de aderência até 04/10/2026.** Capivara com consentimento por trecho: não implementado — projeto externo, item novo depois da janela.
- **Fase 5 (sem prazo — prospecção de horizonte, não backlog):** curador nomeado · espelho do canon fora do GitHub · governança que não dependa de um operador único. IPFS e DAO foram candidatos anotados em 31/07/2026, nunca avaliados. Quem se pegar propondo um deles agora, pare — a instrução é de 26/07/2026 e continua valendo.

**Bússola de longo prazo** (542): `extras/bussola/auditoria-e-bussola.md` — 12 princípios (B1–B12) e 5 aprendidos por incidente (T1–T5). Orienta, não gera tarefa (REGRAS, "Contenção de escopo"); em conflito, REGRAS vence.

**Replicabilidade** (25/09/2026): `propostas/plano-replicabilidade-2026-09-25.md` separa framework (vai para o clone) de instância (nunca vai). A gênese existe e foi testada de ponta a ponta: `scripts/genese.sh` (584)/(586). `scripts/vault_importar_inbox.py` (nota de `memoria/obsidian-inbox/` → entrada em MEMÓRIAS pelo `POST /memoria` do `seth_escriba`) está pronto e não ligado a fluxo automático nesta instância. O resto do plano é bússola.

**Curador da sucessão:** `lacuna` — enquanto vago, o Humano operador local. Regras de curador nas REGRAS.

## Estado de publicação
Repositório **público**, por decisão registrada do Humano — foi isso que queimou o nonce; consequência conhecida, não acidente. O estado de publicação não se afirma por este texto: mede-se em cada sessão (`sync`, `PROTOCOLOS.md`). Se o remoto ficar atrás, o executor trabalha com os arquivos entregues pelo Humano e declara a origem.

## Ferramenta embutida: selar.sh (Fase 4)
`scripts/selar.sh` sela arquivos em `SELOS.txt` (sha256); `--check` dá exit 1 sem `SELOS.txt` ou com arquivo violado ("VIOLADO"), exit 0 com tudo íntegro. É o P-14 sobre as camadas frias de MEMÓRIAS.

## Memória em duas camadas

**Camada local** — Obsidian sobre o próprio repositório git: offline, privada, é **FATO**.
**Camada nuvem** — NotebookLM e afins: processamento de fonte bruta, é **RELATO/projeção**. Nunca recebe canon e nunca vira cérebro do sistema.

### Esfera pessoal
`memoria/missoes/segunda-camada/` é a esfera local e privada do Humano. Sem remote, não sobe para serviço externo nenhum. Pode conter o que só existe nesta Máquina: hardware, rotina, configuração local, assunto pessoal. Modelos locais consultam sob demanda; modelos em nuvem não veem.

### Esfera do projeto
`memoria/missoes/agata-sistema/` é a esfera de trabalho do sistema, vinculada a uma conta Google Workspace **dedicada ao projeto** — nunca a conta pessoal do Humano. Recebe material do sistema que o Humano autorize, e pode ser consultada por modelos externos sob autorização.

### Fronteira
Só o não-sensível sobe. Conteúdo público sobre o sistema pode ser usado na esfera do projeto; os arquivos canônicos não sobem como canon. Dado que só existe nesta Máquina, ou que pertence ao domínio pessoal, fica na esfera pessoal. Segredo, chave e credencial nunca sobem para esfera externa nenhuma.

**Por que "canon nunca sobe" não contradiz o repositório ser público:** a proibição não é sobre sigilo do texto. É sobre duas outras coisas: nenhuma esfera externa adquire autoridade para escrever fato no canon; e material derivado do canon que ainda não é público não sobe.

### Fronteira mecânica — `subir_esfera_projeto.py`
O único cano de código entre o sistema e o Drive. Um arquivo por invocação; não encadeia, não escreve em canon, não decide nada. Aborta na primeira checagem que falhar, nesta ordem:
1. **Caminho** — `realpath` do alvo dentro de `memoria/missoes/agata-sistema/`; symlink para fora é resolvido e barrado.
2. **Esfera pessoal** — `realpath` que toque `memoria/missoes/segunda-camada/` aborta.
3. **Canon** — basename em `{REGRAS.md, PROJETO.md, MEMÓRIAS.md, PROJETO_REFERENCIA.md}` aborta, mesmo sendo cópia.
4. **É arquivo** — não diretório.
5. **Extensão** — só `.md .txt .csv .json .yaml .yml .log`.
6. **Tamanho** — acima de 10 MiB ou 0 byte aborta.
7. **UTF-8** — binário aborta.
8. **Varredura de segredo** — ~16 padrões (credenciais Google/OAuth, PEM, AWS, `sk-…`, tokens GitHub/Slack, connection string com senha, header `Authorization`, par chave/valor genérico, nomes de `*_API_KEY` conhecidos, CPF, CNPJ). Um match aborta — **nada é enviado**.

Só depois das 8: `refresh_token` → access token → pasta `agata-sistema` no Drive (escopo `drive.file`) → upload multipart → `[carimbo] nome drive_id=… tamanho <- caminho` em `memoria/missoes/agata-sistema/upload.log`. **Não é allowlist**; liberar só certos arquivos seria P-8 separada. Limitação assumida (286): formato de segredo que nenhum padrão pega, posto em `agata-sistema/` de propósito e enviado à mão — a varredura é rede contra acidente, não classificador.

### Índice derivado do canon público e export pro Drive
(296)/(298)/(299)/(300). Camada de consulta separada do vault, gerada só do canon público (`REGRAS.md`, `PROTOCOLOS.md`, `FALHAS.md`, `PROJETO.md` e as camadas de MEMÓRIAS), nunca de `memoria/missoes/`.
- `scripts/gerar_indice_derivado.py` → `memoria/missoes/agata-sistema/derivado/{indice.md, manifesto.md}`: as camadas normativas e o PROJETO na íntegra + os títulos das entradas de MEMÓRIAS, mais recente primeiro. Reconstrução byte a byte antes de gravar — um byte fora do boilerplate + canon aborta. `manifesto.md` traz o sha256 das fontes; determinístico (carimbo de commit).
- `scripts/consultar_indice.py <palavras>` extrai trechos do `indice.md` em texto plano, rotulados pela fonte certa (611) — é como o executor local entrega recorte a um modelo em nuvem.
- **Export:** `scripts/preparar_export_indice.py` mascara nomes de variável de ambiente como `[variável de ambiente]` (a varredura de segredo abortaria no nome pelado; o scanner não se afrouxa) e só grava se o resultado passar em todos os padrões de `PADROES_SEGREDO`. Fluxo: `gerar_indice_derivado.py` → `preparar_export_indice.py` → `subir_esfera_projeto.py memoria/missoes/agata-sistema/derivado/indice_export.md` (+ `manifesto.md` como carimbo de proveniência).
- **Automático:** o `.githooks/post-commit` refaz `indice.md`/`manifesto.md` a cada commit (301) e envia ao Drive só quando o sha256 do `indice.md` muda — marcador em `~/.cache/agata/indice-export-ultimo-sha` (457). Fail-soft: falha vira `AVISO`, nunca bloqueia o commit.

### Mão única refinada
**Nenhum resultado externo tem autoridade automática para escrever no canon.** A esfera do projeto pode produzir síntese, análise ou proposta; nada disso é escrita de fato. Resultado processado só influencia o canon pelo fluxo normal: proposta explícita, decisão do Humano, verificação pela Máquina quando aplicável, registro em MEMÓRIAS, commit. A autorização do Humano permite a incorporação; não dispensa verificação nem registro.

### Postura sobre uso dos dados pelo Google
O Humano autoriza o uso dos dados da esfera do projeto nos serviços Google escolhidos, incluindo eventual uso para melhoria ou treinamento **quando os termos daquele serviço assim previrem**. É postura declarada do Humano, não alegação sobre o que a Google faz. Dados da esfera pessoal nunca são usados para isso, porque nunca sobem.

### ACB — reversão parcial de (223)
Desde 27/08/2026, a exclusão do ACB vale só para assuntos pessoais e partes desnecessárias ao sistema. Assunto do próprio sistema pode voltar ao escopo com autorização explícita do Humano e o mesmo controle de proposta, verificação e registro.

### Limitação conhecida — Conselho Remoto
A esfera do projeto mora em `memoria/missoes/`, que casa com a Condição 1 do `scripts/conselho_remoto.py`: por mecanismo, não pode ser discutida com o Conselho Remoto. É a proteção funcionando. Mudar exige allowlist explícita ou mover a esfera — decisão do Humano.

**Sem auto-captura de fatos.** A memória muda só por edição deliberada, por entrada em MEMÓRIAS ou sob comando explícito; o portão do grafo garante isso (`FALHAS.md`, INT-3).

## Referência
Seções de consulta (VM do Marcos, riscos conhecidos, ACB, fronteira de recusas, diagnóstico) estão em `PROJETO_REFERENCIA.md` — não injetadas na hidratação, disponíveis sob demanda.

## Notas históricas
- Até 02/10/2026 este arquivo também guardava a história de cada item (fechados, superados, correções e rosters antigos). O texto verbatim está em `extras/arquivo/PROJETO-ate-2026-10-02.md`; o que saiu e por quê, na entrada de MEMÓRIAS que registra esta reorganização.
- Hermes (`hermes-gateway`, `.hermes.md`, plugins e hooks como `pre_api_request`) foi removido por inteiro em 03/09/2026 — (312). Nenhuma seção ativa depende dele.
