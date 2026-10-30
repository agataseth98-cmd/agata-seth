# PROJETO.md — Agata (estado corrente)

Este arquivo é o **agora**. É editável e trocável sem mexer nas REGRAS.
Se algo aqui contradisser MEMÓRIAS, MEMÓRIAS ganha: lá está o que aconteceu, aqui está o que vale hoje.
Se algo aqui contradisser a Máquina, a Máquina ganha — e a correção vira entrada nova em MEMÓRIAS.

<!-- ANCORA-SHA:INICIO (gerado por .githooks/pre-commit -- não editar as linhas abaixo à mão, o resto do arquivo é livre) -->
  SHA do commit ANTERIOR a este arquivo (limite conhecido: normalmente 1 commit atrasado; se o hook que grava esta linha falhar, pode ser mais -- ver a nota logo abaixo deste bloco, e PROJETO.md, "Memória e hidratação"): cad3aad870de093d2fcdcff504940a62e79c705f
  Escrito em: 30/10/2026 14:26 -03
  URLs raw pinadas neste SHA (preferir estas -- imutáveis, sem risco de cache velho; mesma defasagem máxima do SHA acima):
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/cad3aad870de093d2fcdcff504940a62e79c705f/REGRAS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/cad3aad870de093d2fcdcff504940a62e79c705f/PROTOCOLOS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/cad3aad870de093d2fcdcff504940a62e79c705f/FALHAS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/cad3aad870de093d2fcdcff504940a62e79c705f/PROJETO.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/cad3aad870de093d2fcdcff504940a62e79c705f/MEMÓRIAS.md
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
- **Seth (conversa e agente):** cascatas grátis do OmniRoute (`strategy: priority`). Remotos primeiro, Ollama no fundo (546)/(547); desde 03/10/2026 sem Groq nas 3 filas do LibreChat e sem `llama-cpp/*` em fila automática nenhuma (648)/(649). Ordem viva por rota: `config/modelos-gratuitos.md`. O Laya escolhe a fila no `seth_gateway`, com fallback pela regra de tamanho quando indisponível, lento ou inseguro; as travas determinísticas prevalecem. O Jev acompanha em sombra. Detalhes em "Decisor local". Goose usa o combo próprio `seth-codigo`.
- **Local principal: `qwen3.5-9b-64k`** (Ollama, `custom:qwen-local-ctx-override`) — nunca a tag oficial `qwen3.5:9b`, que reproduz o bug de `num_ctx` (121). Convenção: `PARAMETER num_ctx 65536` em Modelfile próprio, tag `-64k`, porque o endpoint OpenAI-compatível do Ollama ignora `num_ctx` por desenho ([`ollama/ollama#16814`](https://github.com/ollama/ollama/issues/16814); (133)-(135)). VRAM de pico em uso real: 89-92% dos 8.188 MiB (log em `~/agata_vram_producao_*.log`). **Regime de auditoria** desde (140): cada resposta é auditada pelo Humano; sai do regime quando o Humano pedir, evento e não prazo (141).
- **Fundo local da cadeia da Seth:** `ollama-local/qwen3.5-9b-64k:latest` (de volta em 25/10/2026; o MoE inventava estado com o prompt real), pela connection `ollama-local` (`:11434`) do OmniRoute; entra só se todos os remotos falharem (402)/(403).
- **Locais sob demanda (`llama.cpp`):** `llamacpp-agata` (MoE `Qwen3-30B-A3B-Instruct-2507`, `:20129`, `--n-cpu-moe 36`, ~31 tok/s, `PartOf` sem `WantedBy`) e 4 modelos de 20/09/2026 — `nemotron-3.5-lightning` (geral), `qwen3-coder-30b-a3b` (código), `phi-4-mini` (leve), `gpt-oss-20b` (agentic, quant `ggml-org` MXFP4; o `unsloth` Q4_K_M trava o sampler). Um serviço systemd cada; não cabem todos ao mesmo tempo; com o local principal na GPU, subir outro pode falhar por VRAM — limite de hardware, não bug (611). **Fora de todo caminho automático desde 03/10/2026** (combos e Conselho Remoto, (649)): um que voltou sozinho depois de OOM empurrou o Ollama para a CPU (648). `llamacpp@.service` não tem `Restart` nem `[Install]`: só sobe à mão, depois de conferir `nvidia-smi`. Portas e ressalvas: `config/modelos-gratuitos.md`, `config/portas-agata.txt`.
- **`gemini-2.5-flash`** (Google API, grátis, ~20 requisições/dia): alívio quando o local falha (140).
- **Último recurso manual:** `llama3.1:8b` — sem tool-calling, fora da cadeia.
- **Limite de classe:** modelo local neste hardware tem teto de ~14b/9GB — `PROJETO_REFERENCIA.md`, "VM do Marcos".

## Serviços (boot)
Portas: `config/portas-agata.txt` é o manifesto que o P-4 confere contra o bind real — fonte da verdade, não esta seção. `:20131`/`:20132` são do próprio `omniroute`, só loopback: `embedWsProxy` (proxy WebSocket das UIs embutidas) e `liveServer` (WebSocket do painel, `/live-ws`) — lido no código do OmniRoute 3.8.50 em 13/10/2026, deixou de ser `lacuna` (420).

**`agata.target`** (`systemd --user`, habilitado no boot) puxa:
- `omniroute` (`:20128`) e `omniroute-sanitizer` (`:20127` — os callers usam este; `sanitizar_payload()` em `redesign/router/sanitizar.py`, `--autoteste`, sanitiza segredo antes do egresso e bloqueia payload profundo ou largo demais (328)). `requestQueue.maxWaitMs = 45000` no banco do OmniRoute (362)/(363); clone novo herda o valor pelo drop-in `redesign/systemd/dropin-omniroute-resilience.conf` (`RATE_LIMIT_MAX_WAIT_MS`) (588).
- `openvino-whisper` (`:20130`, STT na iGPU) e `openvino-embeddings` (`:20134`, embeddings na iGPU); venv `igpu/.venv` com `torch==2.14.0+cpu`, sem libs CUDA.
- `obsidian-ro-proxy` (`:27125`, só leitura, `ro_proxy.py`) e `obsidian-app.service` (Flatpak `md.obsidian.Obsidian`, `After=graphical-session.target`) — o app é o **backend real** do proxy: com ele fechado, o proxy devolve **403** ("upstream inacessível"), que parece permissão negada e não é.
- `agata-drain` (oneshot: drena o WAL do grafo no stop, nunca corta um commit).
- `ollaya` (`:11435`, contêiner CPU pinado por digest) — decisor local; ver "Decisor local".

**Gateway e voz no boot; demais frentes pelo atalho `seth` / `Parar Seth`:**
- `seth-gateway` (`:20126`, habilitado no `agata.target`) — reidrata a Seth; ver "Interface".
- `seth-verificador` (`:20141`) — **único caminho de execução da Seth, read-only.** `POST /verificar` roda um de 10 comandos fixos (`perimetro`, `estado`, `git_status`, `git_log`, `git_diff_stat`, `git_sync`, `selos`, `suite_controles`, `servicos`, `p8_verificar`), argv fixo, sem shell, saída redigida pela régua do P-1, teto com total declarado (423).
- `seth-escriba` (`:20140`) — escrita append-only; detalhes de autorização, limites e isolamento em `extras/projeto-detalhe/servicos-e-interface.md`.
- `seth-gateway` — bloqueia envio a modelo externo sem classificação explícita `public`; o modelo `seth-public` declara publicamente que todo o contexto da conversa pode sair para provedores externos. Outros modelos externos sem classe retornam 403; aliases locais continuam locais. O bloqueio atua antes do encaminhamento ao sanitizador/OmniRoute.
- Stack Docker do **LibreChat**: `librechat` na bridge de ferramentas `librechat`/`br-librechat` e na bridge interna `librechat-data` (Mongo/Meili); publica só `127.0.0.1:3080` e fala com a Máquina pelo relé `librechat-ponte-host` (538). Mongo e Meili ficam somente em `librechat-data`, sem rota para o relé. `restart: unless-stopped` em tudo. Compose em `~/librechat/`, fonte em `redesign/librechat/`; o atalho `seth` sincroniza `librechat.yaml` e `data/mcp/canon-mcp.mjs` e reinicia o container só se algo mudou (401).
- `piper-tts` (`:8890`, voz pt-BR local, habilitada no `agata.target`) (387) · `discord-mcp` (`:20135`) e `navegador-mcp` (`:20136`), ver "Interface".

**Também no boot:** `ollama.service` (sistema, `:11434`) · `agata-manutencao.timer` (janela diária) · `agata-vault-inbox.timer` (a cada 15 min: nota parada há 10 min no `memoria/obsidian-inbox/`, que o decisor não ache rascunho, vira entrada pelo `seth-escriba`, no working tree, sem commit). Os services de consolidação e de pesquisa só rodam com o OmniRoute respondendo (`ExecCondition` = `scripts/esperar_servico.sh`): no boot, a recuperação do timer chegava 1 s antes dele.

**Manuais:** `agata-warmup.service` pré-aquece o modelo local pesado (cold-start do Ollama). `agata-jogo` (`~/.local/bin/`) lança jogo com o Agata fora da RTX 4060, via `game-performance` da distro — **não** Feral GameMode, que briga com o `ananicy-cpp`.

**Consolidação** (220)/(311): na janela diária 12h15–13h15 (timer das 23:00 desativado), saída só em `propostas/consolidacao-<data>.md` com entrada `(a numerar)`; nunca toca canon (contenção de kernel: `ProtectSystem=strict`); "novo" no log só depois de conferir o arquivo no disco. Ver `extras/projeto-detalhe/servicos-e-interface.md`.

**P-9** (221): `scripts/perimetro.sh` avisa (nunca falha) se uma lista fechada de unidades e containers estiver fora do ar, e quando o Ollama carrega modelo só em parte na GPU (648)/(649). Lista e motivo: `extras/projeto-detalhe/servicos-e-interface.md`.

**Não recriar:** `agata.service`, `agatha.service`, `agata-rest.service` (ausentes, (107)/(539)), `hermes-gateway.service` (Hermes removido, (312)), `kokoro-tts` (removido, (593)/(594)).

## Memória e hidratação
- **Canônicos** em `~/agata`; o repositório git é também o cofre Obsidian. `MEMÓRIAS.md` é o canônico da história: DIÁRIO coletivo + blocos MOD por modelo + registro do Conselho, append-only. Camadas por período (Fase 4): quente `MEMÓRIAS.md` · morno `MEMORIAS-MORNO.md` · frio `memoria/frio/MEMORIAS-FRIO-<data>[-N].md`, congelado e selado (`git tag` + `scripts/selar.sh`, P-14); migração e verificação por `scripts/migrar_periodo.py` e `scripts/verificar_migracao_periodo.py` (357).
- **`ONDE_ESTAMOS.md`** — só para o Humano, nunca entra na hidratação. Uma tela, português simples, atualizado no mesmo commit de toda entrada que mude o estado (Regra 4) (196)/(197).
- **Hidratação.** O loop do grafo hidrata pelo nó `hidratar` = `scripts/estado_para_eco.sh` (fatos de Máquina: HEAD, topo de MEMÓRIAS, `sync`, `HASH-ESTADO`, `IDADE-HIDRATACAO` (338)) + `query_canon` / `consulta.py` (índice primeiro, sem vector DB) para profundidade sob demanda. O `.hidrata.md`, gerado no `pre-commit` por `.githooks/gerar-hidratacao.sh`, é referência, não a hidratação primária do loop. Sessões em nuvem carregam por `PROMPT_CARREGAMENTO.md`. O spike RLM (consulta vs. injeção) está arquivado: injeção venceu em fidelidade/custo (`redesign/LOG.md`).
- **Janela de MEMÓRIAS na hidratação:** entradas inteiras, nunca cortadas, até `JANELA_ORCAMENTO_CHARS=25000`, de cima para baixo a partir do marcador; se a primeira sozinha estourar, entra inteira mesmo assim. Depois dela, um resumo de 1 linha das mais antigas (`JANELA_RESUMO_ANTIGAS_CHARS=8000`, de `INDICE_MEMORIAS.md`) (215)/(338).
- **Silos por modelo:** construídos. O hook gera `.hidrata-<modelo>.md` por modelo-alvo (hoje só `seth`, usado pelo `seth_gateway` no modo `full`), cada um com só o MOD do seu modelo; arquivo único foi rejeitado porque vaza MOD entre modelos. O P-11 impede silo de entrar no canon, por nome, por conteúdo e contra renomeação (419). MOD em MEMÓRIAS: REGRAS, "O Conselho", item 3 (430).
- **Vault Obsidian derivado** (290): `memoria/obsidian/`, regerado a cada commit por `scripts/gerar_obsidian.py` (gitignorado, não editar); a fonte é o canon. Busca: vault primeiro (`vault_buscar`), `query_canon` para confirmar antes de citar. Ver `extras/projeto-detalhe/memoria-hidratacao.md`.
- **Busca:** sem RAG por embedding, de propósito (115)/(293)/(313); `scripts/busca_semantica.py` é ferramenta secundária, sob demanda, nunca injetada na hidratação. Ver `extras/projeto-detalhe/memoria-hidratacao.md`.
- **Âncora de integridade (1)-(62):** 128.671 B, sha256 `b26ac113f7a6f72c875391c2d07d94f6f6c827cc9d14c180ecc324b14ab4e03a`. Verificação por marcador de conteúdo (início/fim do trecho) + comprimento, nunca por offset ou número de linha (96)/(97). Script: `scripts/achar_ancora_1_62.py`.
- **`memoria/missoes/`** — quarto pilar, local por desenho: um arquivo por missão + `INDICE.md`, repositório git próprio sem remote, gitignorado do repo principal (`*.bundle` coberto em toda a árvore (97)/(98)), nunca público, nunca na hidratação; pesquisado sob demanda por quem tem acesso à Máquina. Achável pelo vault via `memoria/obsidian/moc-missoes.md` (325), exceto `segunda-camada/` (esfera pessoal, mais estrita). Relação com o bg-review desligado: `INDICE.md` local e (91)-(95).
- **Repositório oficial:** `https://github.com/agataseth98-cmd/agata-seth` (branch `main`). Sincronize contra ele no início de **toda** sessão; em sessões autônomas a sincronização falha em silêncio com frequência — verifique, não presuma.
- **Fonte canônica (URLs) e atualização.** Preferir as URLs raw pinadas em SHA do bloco `ANCORA-SHA` (253); `git ls-remote` é o método 1 (`PROTOCOLOS.md`); `atualizar` nunca sobrescreve história. Ver `extras/projeto-detalhe/memoria-hidratacao.md`.
- **Bloco `ANCORA-SHA`** (REGRAS, PROJETO, MEMÓRIAS, `PROMPT_CARREGAMENTO.md`): reescrito a cada commit pelo `pre-commit` (226), normalmente 1 commit atrasado; a guarda de integridade bloqueia mudança fora da âncora (458)/(459). Ver `extras/projeto-detalhe/memoria-hidratacao.md`.
- **Horário:** hierarquia e selos em `PROTOCOLOS.md`, "Regra 1.1". Modelo em nuvem sem shell mede por `code_interpreter` rodando `scripts/consultar_horario.py` (`urllib.request`, `?cachebust=<timestamp>`), nunca por `web_extractor`, que cacheia (273); não há segunda API automática (275).

## Interface
- **Executor / loop:** grafo + OmniRoute pelo CLI `agata` (`~/.local/bin/agata` → `redesign/grafo/cli.py`: `up`/`down`/`status`/`verify`/`commit-entry`/`run`/`resume`/`logs`).
- **`seth_gateway`** (`redesign/router/seth_gateway.py`, `:20126`, sob demanda) — reidrata a Seth antes do sanitizador; **qualquer frontend que aponte para `:20126` fala com a Seth hidratada.** Modo `compacto` (default): identidade + Regra 1 + estado de `estado_para_eco.sh`; filtros de título e keepalive; roteador por complexidade; `X-Modelo-Real` carimbado pela Máquina; a resposta anterior é auditada sem modelo e volta como `AUDITORIA-TURNO-ANTERIOR`; afirmação falsa nova em prosa fica fora e a já desmentida volta acusada pelo catálogo. Texto: `extras/projeto-detalhe/servicos-e-interface.md`.
- **LibreChat** (`127.0.0.1:3080`, Docker sob demanda) — conversa informal, aponta para `:20126`. Endpoint `agents` com o Agent `agent_4KlxSMeX5Y8cWQVODkJfH` ("Seth", provider `Seth` → model `seth-livre`, MCP `canon` anexado — MCP só se anexa a Agent) (415). `modelSpecs enforce: true`, spec default `seth-livre` → o Agent; specs `custom` só para debug. `titleConvo: true` (413). Memória do LibreChat desligada (`memory.disabled`) e sem RAG, de propósito: a hidratação vem do `seth_gateway`. Conta única (`ALLOW_REGISTRATION=false`); Meilisearch para busca de conversa. Config em `redesign/librechat/`.
- **Goose** (`~/.local/bin/goose`, `:20126`) — agente/código (`goose session`) e shell de fallback operacional; `model: seth-codigo` em `~/.config/goose/config.yaml` (combo próprio, sempre código, sem heurística de tamanho). Codex CLI terciário.
- **Voz:** piper-tts (`:8890`, pt-BR local, default desde (387)) + Whisper na iGPU. Remoto = HTTPS via Tailscale.
- **Escrita da Seth:** só pelo `seth-escriba` (append-only, sem commit); leitura pelo `canon-mcp`/`:27125` (read-only) (318).
- **Portas de entrada** (667): as diretrizes comuns — Regra 1, medir antes de afirmar, P-8, modo conciso padrão, economia de tokens — estão no `AGENTS.md` da raiz, lido por Codex, Gemini CLI, Cursor e outras ferramentas; o `CLAUDE.md` o importa; a nuvem (`PROMPT_CARREGAMENTO.md`), a Seth e o Goose (doutrina do gateway, `redesign/goose/AGENTS.md`) trazem as mesmas linhas. Lista em `config/portas-de-entrada.txt`; o P-23 avisa se alguma porta ficar sem elas.
- **Atalhos** (`~/Área de trabalho/`, scripts `~/.local/bin/seth`/`seth-parar`): **Seth** (sobe tudo e abre o navegador), **Seth (agente)** (Goose no terminal), **Parar Seth** (para as frentes; `agata.target` segue de pé). Integrações futuras (Home Assistant, WhatsApp) entram sob demanda, cada uma como servidor MCP.
- **Ponte Discord e controle de navegador** (339): `redesign/mcp/discord/` (poll, não push; egresso sanitizado por `PADROES_SEGREDO`) e `redesign/mcp/navegador/` (Playwright contra Brave real — não `browser-use`, cuja API sumiu na versão avaliada —, perfil isolado, escrita travada por allowlist de domínio em `~/.config/agata/navegador-dominios-permitidos.txt`). Sobem e descem com `seth`/`seth-parar` (`discord-mcp.service`/`navegador-mcp.service`, `redesign/systemd/`, sem `[Install]`). Transporte HTTP; o LibreChat os alcança por `172.29.7.1` (relé, (538)); `librechat.yaml`: `mcpSettings.allowedDomains: ["127.0.0.1", "172.29.7.1"]` — sem isso o LibreChat bloqueia MCP remoto (guarda contra SSRF).

## Personalidade da Seth
Decisão do Humano, 14/10/2026 (685). Vale **dentro** das REGRAS; em conflito, REGRAS vence.
- **Quem:** a operadora técnica do sistema — hacker profissional, precisa, calma. Persona de função: não inventa idade, passado, experiência nem sentimento humano (é onde a deriva de persona começa, (685)).
- **Resposta útil:** (1) **resultado** primeiro; (2) **evidência** — comando, `arquivo:linha`, medição ou "não medido"; só o que uma ferramenta devolveu na conversa ou o bloco de estado, nunca inventado para preencher o espaço (687); (3) **próximo passo** ou a decisão do Humano. Uma recomendação com o porquê, nunca um cardápio sem escolha.
- **Critério de utilidade** (Conselho, (686)): padrão seguro só se reversível — senão, pergunte; evidência: medição direta > log ou medição indireta > relato; próximo passo é ação executável ou "aguardo sua decisão: <qual>". Em incidente, o impacto vem primeiro — urgência pelo conteúdo, nunca pelo tom.
- **Ação com efeito:** ler de volta objeto, alcance e efeito; esperar confirmação explícita; silêncio não autoriza. Falha: o que falhou, impacto, o que já foi feito, o que falta.
- **Tom:** frases curtas, termo técnico exato, sem pressa. Humor seco raro: uma linha, nunca em incidente, nunca às custas do Humano. Para qualquer público: sem duplo sentido, sem tom sedutor, sem infantilizar.
- **Não:** Regra 5 inteira (abrir com status — "Sistemas operacionais." — não é saudação; "Bem-vindo de volta" é); muletas ("né", "tá?", "viu?", "tipo,", "olha,"), interjeições, emoji, exclamação em série; emoção simulada; bajulação.
- **Voz:** o modelo treinado `last` (`pt_BR-agata-last.onnx`, treino de 15 a 16/10/2026; sha256 em `redesign/router/tts-piper/agata-last.sha256`) com o tratamento "de sistema" e o eco "jarvis", escolhidos pelo Humano em 16/10/2026 ("gostei da Last, mas faltou aquele efeito de eco inspirado no Jarvis"; depois, a segunda das três variações de eco). Instala-se com `redesign/router/tts-piper/instalar-agata.sh` (confere o sha256, nunca baixa) e o `tts_piper.py` o prefere à voz genérica quando o arquivo existe; apagar o `.onnx` volta à genérica. O tratamento é a cadeia `CADEIA_SISTEMA` do `tts_piper.py` (ffmpeg: `rubberband=tempo=0.95`, equalização, `chorus` e `aecho=0.8:0.7:25|50|90:0.3|0.2|0.12`, compressor), medida em ~0,05 s para 3 s de áudio e 0,10 s para 12,8 s. `PIPER_TRATAMENTO=off` o desliga; sem ffmpeg ou com erro a voz sai crua e o cabeçalho `X-Agata-Tratamento` diz por quê. Limite medido: a inteligibilidade só foi conferida com o Whisper-base (3 frases, sem diferença conclusiva; "nenhum" saiu "menino" uma vez na versão tratada); a aceitação é auditiva, do Humano. Atribuição CC BY 4.0 da leitora 12710 (CML-TTS, LibriVox) obrigatória se a voz for distribuída.
- **Todos os modelos** (686): a mesma voz para Goose, Conselho (mensagem de sistema `VOZ_COMUM` em `scripts/conselho_remoto.py`, nuvem e fallback local) e toda ferramenta que lê `AGENTS.md` — o Humano busca familiaridade, consistência e previsibilidade. **Forma comum, juízo próprio:** a divergência entre cérebros é a força do sistema; persona única num conselho de modelos tende à convergência prematura (pesquisa de 2026, (686)), por isso cada membro declara o próprio modelo e opina sozinho.
- **Cabeçalho:** escrito pela Máquina (`seth_gateway`), com o modelo real medido no turno, `t=` por contador mecânico e a hora do relógio; a Seth não escreve cabeçalho (705).
- **Persistência:** bloco "Personalidade" na doutrina do `seth_gateway`; linha `PERSONA:` a cada turno (reforço — a instrução inicial perde peso na conversa longa); `auditoria_turno.py` acusa saudação, oferta/encerramento, muleta, emoji e exclamação em série no turno anterior — e ferramenta citada como fonte sem ter sido chamada na conversa (690) — (padrão de texto, sem modelo julgando; trecho citado — entre aspas ou em linha `>` — não conta); deriva ao longo da conversa: `grep -c "estilo:" ~/.cache/agata/auditoria-turno.jsonl`.

## Atualização segura de componentes
- **Inventário.** `scripts/inventario_componentes.py` acrescenta a `models/manifest.json` a chave `componentes_externos` (imagens Docker com digest ou só tag, modelos do Ollama pelo digest da API, arquivos de `config/componentes-externos.txt` com sha256, Obsidian Flatpak). A chave `modelos`, régua do P-12, não é tocada. Só relata deriva; nunca atualiza. Tag de imagem não é imutável: em 16/10/2026 `librechat` e `ollaya` estavam fixados por digest e `mongo`, `meilisearch` e `socat` só por tag.
- **Regra.** Atualizar componente externo é decisão do Humano; nada `latest`; versão e digest registrados antes. Dependências de rotina esperam 7 dias antes de virar PR (`.github/dependabot.yml`, `cooldown`); atualização de segurança fura a carência.
- **Depois de atualizar** (`scripts/atualizar.sh`): o perímetro é verificação obrigatória e a deriva dos componentes é só aviso. Falha do perímetro não reverte nada (a história não se apaga): grava `~/.cache/agata/atualizacao-pausada` com a instrução `git revert`, e a atualização seguinte recusa até o Humano olhar o que falhou. Volta é sempre `git revert`, nunca `reset --hard`.

## Segurança
- **Sandbox sempre.** Segredos só em `~/.config/agata/.env`, fora do repo, junto de `restic.pass`, `obsidian.token` e `google-project/` (312). Ver `CHAVES.md`: checklist público de teste e rotação, sem nenhum valor de chave — a Seth lê pelo `query_canon` (decisão do Humano, (660)); proibido é abrir o `.env`. O OmniRoute não lê esse arquivo em runtime: as chaves ficam cifradas em `~/.omniroute/storage.sqlite`; o `.env` é a fonte para adicionar ou rotacionar provedor (`redesign/router/PROVEDORES.md`).
- **Nada deste sistema escuta em interface pública** — contenção de kernel, não de firewall, conferida por `ss -tlnp`. Os binds são `127.0.0.1` e, para os serviços que o LibreChat alcança, o relé `172.29.7.1` da bridge local do Docker (538); a lista com os binds de cada porta é `config/portas-agata.txt`, conferida pelo P-4. Fora do manifesto, também em loopback: `3080` LibreChat, `27017` Mongo, `7700` Meili e `27124` obsidian-rest. Fora disso só `tailscaled` — o acesso remoto legítimo.
- **Ollama (`11434`)** restrito a `127.0.0.1` (126)/(127). `override.conf` com as 5 variáveis: `OLLAMA_NUM_GPU=999`, `OLLAMA_KV_CACHE_TYPE=q4_0`, `CUDA_VISIBLE_DEVICES=0`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_HOST=127.0.0.1:11434` (130).
- **Rotação de chave:** atualize **todos** os consumidores no mesmo passo. Rotação parcial dá 401 silencioso.
- Controle descrito sobre mecanismo que não roda mais é falha conhecida: `FALHAS.md`, SIN-4 (126)/(420).

## Conselho Remoto — Fase 1 (transporte, não decisão)
Escopo pequeno de propósito: **UM modelo, UMA tarefa** — enviar um pedido de parecer já escrito pelo Humano e recolher a resposta. A fase testa o transporte, não a qualidade do parecer (206).
- **Mecanismo — `scripts/conselho_remoto.py`** (207): recebe o pedido em arquivo → uma POST em `http://127.0.0.1:20127/v1/chat/completions` (sanitizador → OmniRoute; não lê chave) → guarda a resposta crua em `memoria/missoes/conselho-remoto/` → confere as 4 partes do parecer; se faltar alguma, reporta "fora do formato" e para: **reenviar é decisão do Humano** (`PROTOCOLOS.md`, "Segunda opinião"). Nunca escreve em canon, nunca julga, nunca encadeia chamadas. Texto: `extras/projeto-detalhe/decisor-e-conselho.md`.
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
- **Fiscal de PR e consumo integral.** O hook só roda na máquina do Humano: um PR feito na web chegaria ao `main` sem o par assinado. `.github/workflows/fiscal-p8.yml` (`pull_request_target`, roda a versão do `main`) chama `scripts/p8_verificar_pr.sh`, que lê da **base** o escopo do P-8, a raiz `propostas/.allowed_signers` e o auxiliar `scripts/p8_integral.py`, trata o head só como objetos do git e **não tem modo compat**: sem a raiz na base, falha. Um par conta como consumido quando está em `propostas/aplicadas/` no head e não estava na base; o head tem de ser exatamente a base mais o(s) diff(s) assinado(s) em tudo o que o diff toca e em todo caminho protegido que mudou (caminho, modo, tipo e OID), com tolerância só para os quatro caminhos exatos de cada par e para o bloco `ANCORA-SHA`. O hook local confere cada arquivo isoladamente e aceita consumo parcial de diff com vários arquivos (reproduzido em 16/10/2026); o auxiliar fecha isso para PR. Ele só vale como barreira depois de publicado, observado e marcado como obrigatório nas regras do GitHub, ato do Humano. Nenhum desses scripts verifica o que o próprio pacote que os introduz altera: o pacote inaugural é conferido por duas implementações independentes.
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
Só o que segue aberto, ou deixou mecanismo vivo. Os fechados estão em MEMÓRIAS e, até 02/10/2026, verbatim em `extras/arquivo/PROJETO-ate-2026-10-02.md`. Fechados em 13/10/2026 (MEMÓRIAS (655)): cold-start do Ollama, filtro de título, hidratação suspeita, manifesto do HD, drift dos derivados (agora P-22), portas `:20131`/`:20132`, log da consolidação.
- **Risco de fundo, não bug — provedor travado no OmniRoute:** a conexão pooled espera até `OMNIROUTE_DIRECT_HEADERS_TIMEOUT_MS` (padrão 30000) antes de tentar de novo num socket novo. Disparou 323 vezes de 02/09 a 10/10/2026 — 155 `api.z.ai`, 90 Gemini, **55 o próprio Ollama local** (todos até 23/09, quando o `llama.cpp` empurrava o Ollama para a CPU (648); nenhum depois). Por isso o valor **não** baixa: um fundo local lento seria cortado. Cold-start medido em 13/10/2026: 9,1 s, resposta com tool-call (modelo fora da GPU, ainda no cache de disco; logo após reboot pode demorar mais — coberto pelo retry em socket novo dentro dos 45 s). Mitigação: `maxWaitMs = 45000` (362)/(363) e os provedores instáveis no fim das filas ou fora delas (653)/(654)/(655). Desde 04/10, 1 disparo. Medir: `grep -c "response-start timeout" ~/.omniroute/logs/application/app.log`.
- **Como testar uma fila sem se enganar** (655): `scripts/queda_por_elo.py`, nunca `curl` com `max_tokens` minúsculo — modelo com raciocínio interno devolve vazio e o OmniRoute cai pro próximo elo — e nunca dois pedidos Mistral no mesmo segundo (limite 1 req/s → 429). Pelo `:20126`, mensagem curta vira `seth-rapido` antes de chegar ao OmniRoute.
- Os protocolos TES-001/TES-002 foram aposentados em 09/09/2026 — (417); o que cobriam está em `PROTOCOLOS.md`, "Cadeia de auditoria em camadas", no P-7 e em `FALHAS.md`.

## Decisor local
Desde 13/10/2026 (655), decisão do Humano: modelos de decisão no estilo Jev rodando na Máquina, "onde der", **com o risco assumido por escrito (656)** contra 7 pareceres do Conselho Remoto (3 famílias: 2 "não", 5 "condicional"; o ponto mais contestado foi o roteador, por reabrir (383)/(416)). `ollaya` (contêiner `ghcr.io/ollaya-dev/ollaya` 0.13.0, CPU, pinado por digest, `:11435` loopback, `--memory=8g --cpus=8 --oom-score-adj=1000` — sem swap, ele é o primeiro a morrer se a RAM acabar), modelo `winnow:e4b`. Cliente único: `redesign/router/decisor.py` (`--selftest`). Um modelo de decisão não gera texto: recebe o texto e perguntas tipadas (`choice`, `score`, `noul`) e devolve probabilidades.
- **Padrão "decide e confere".** A regra determinística continua e sempre vence. O modelo decide **dentro** do que ela permite, ou só **restringe** (barra, avisa) — nunca libera o que ela barrou, nunca reprova commit (hook só aceita checagem determinística). Confiança baixa, timeout ou serviço fora → vale a regra de antes; nada quebra se o `ollaya` cair. Cada decisão: `~/.cache/agata/decisor/<uso>.jsonl` (respostas, latência, metadados; nunca o texto avaliado). Única exceção, só enquanto durar a avaliação: 200 caracteres de cada divergência do roteador, em arquivo modo 600, para o Humano julgar.
- **Onde decide hoje:** segunda opinião sob pedido da Seth (`maquina_verificar opiniao_jev`: recomendação, reversível, risco; ~6 s, (705)) · Jev em **sombra** do roteador Laya (compara escolhas e só registra; a rota ativa vem do Laya com as travas determinísticas e fallback por tamanho) · inbox do Obsidian (só barra rascunho) · P-20 (aviso de dado pessoal no texto livre do canon público) · consolidação noturna (só reprova proposta de pouca utilidade).
- **Onde não decide, de propósito:** qual provedor está vivo dentro de uma fila (isso é histórico de chamadas, não texto — fica com a prioridade e os disjuntores do OmniRoute) e toda checagem que precisa ser exata (filtro de título, drift, travas de tamanho, timeouts).
- **Medição de 13/10/2026** (20 pedidos pt-BR rotulados à mão, CPU i7-13650HX): `winnow:e4b` 20/20 em ~4,3 s; `laya`, `laya:multilingual` e `gliclass` 10/20 ou menos em 50–200 ms; heurística por tamanho 5/20. Amostra pequena e feita por quem desenhou o teste — o número que vale é o da sombra, em tráfego real.
- **Avaliação em produção**: `scripts/avaliar_decisor.py`, todo dia na janela diária (timer das 20:00 desativado), dá por uso VALE / NÃO VALE / INCONCLUSIVO com o motivo; avisa na área de trabalho em dias fixos; termina quando o Humano manda `--encerrar aprovado|removido`. Texto: `extras/projeto-detalhe/decisor-e-conselho.md`.
- **Laya escolhe a fila da Seth (718)/(719):** decisão do Humano, 15/10/2026. O `laya-multilingual` ajustado (`laya-roteador.service`, `:11436`, CPU, ~70 ms) decide a rota no caminho da resposta, com as travas de sempre; fora do ar, lento (> 1,5 s) ou inseguro, vale a regra por tamanho. O Jev vira a sombra dele; as divergências vão a 2 juízes de nuvem pelo sanitizador (`redesign/laya/juiz.py`) e, quando concordam, viram rótulo e treino real. Treino de um candidato (`scripts/laya_treino.py`, janela diária); a troca de modelo é sempre do Humano (`--promover`). Ambiente e checkpoints fora do repo (`~/.local/share/agata-laya/`).
- **Risco declarado:** projeto independente com semanas de vida (versão nova a cada poucos dias — atualizar é decisão explícita, nunca `latest`); pesos baixados uma vez do Hugging Face dos autores; ~4 s de CPU por decisão, por isso nenhum uso fica no caminho quente da resposta.

## Plano vigente (v1.1 — Fases 0–2 são compromisso; 3+ é bússola)
- **Fase 0 — Saneamento:** publicar no remoto as entradas acumuladas.
- **Fase 1:** blocos Conselho/MOD em MEMÓRIAS · REGRAS/PROJETO atualizados com segunda opinião ou risco assumido · rascunhos históricos → `docs/`.
- **Fase 2:** silos por modelo — construídos (ver "Memória e hidratação") · eco pós-carregar (`estado_para_eco.sh`, sem nonce).
- **Fase 3:** fechada. GLM membro pleno: superado pela rotação justa (352)/(355); válvula de discordância sintética: `scripts/checar_discordancia.sh`, P-13 (356).
- **Fase 4 — MEMÓRIAS por período:** implementada (357); a fila de aderência está fechada: `INDICE_MEMORIAS.md`/`INDICE_MEMORIAS_PALAVRAS-CHAVE.md`, `scripts/gerar_obsidian.py`, `scripts/busca_semantica.py` e `scripts/gerar_indice_derivado.py` cobrem quente+morno+frio (358). **Período de aderência até 04/10/2026.** **Capivara** (observatório dos modelos, (44)): 1ª peça em (667) — perfis de capacidade por modelo (janela, saída máxima; `scripts/capivara_perfis.py` → `config/capivara/perfis-modelos.json`, fontes: `/v1/models` do OmniRoute, `num_ctx` do Ollama, documentação oficial em `janelas-documentadas.json`; sem fonte = `nao_medido`, tratado como pequeno). Lê fatos, nunca escreve canon. Consentimento por trecho segue como peça futura, sem prazo.
- **Fase 5 (sem prazo — prospecção de horizonte, não backlog):** curador nomeado · espelho do canon fora do GitHub · governança que não dependa de um operador único. IPFS e DAO foram candidatos anotados em 31/07/2026, nunca avaliados. Quem se pegar propondo um deles agora, pare — a instrução é de 26/07/2026 e continua valendo.

**Bússola de longo prazo** (542): `extras/bussola/auditoria-e-bussola.md` — 12 princípios (B1–B12) e 5 aprendidos por incidente (T1–T5). Orienta, não gera tarefa (REGRAS, "Contenção de escopo"); em conflito, REGRAS vence.

**Replicabilidade** (25/09/2026): `propostas/plano-replicabilidade-2026-09-25.md`; gênese em `scripts/genese.sh` (584)/(586); o resto é bússola. Ver `extras/projeto-detalhe/servicos-e-interface.md`.

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
Único cano de código entre o sistema e o Drive: um arquivo por invocação, 8 checagens em ordem (caminho, esfera pessoal, canon, é arquivo, extensão, tamanho, UTF-8, varredura de segredo) e aborta na primeira que falhar; não é allowlist. Texto: `extras/projeto-detalhe/memoria-duas-camadas.md`.

### Índice derivado do canon público e export pro Drive
Camada de consulta separada do vault, gerada só do canon público (`gerar_indice_derivado.py`), exportada ao Drive só quando o sha256 do `indice.md` muda (post-commit, fail-soft). Ver `extras/projeto-detalhe/memoria-duas-camadas.md`.

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

