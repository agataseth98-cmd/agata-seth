# Estado de fundo do Agata (prosa de estado)

Saiu do PROJETO.md em 12/11/2026 (decisão do Humano, entradas 521 e 522 do cache do Conselho): o PROJETO vira índice, e a prosa de estado mora aqui. Os números vivos (portas, serviços, modelos que responderam, propostas) estão no `ESTADO.md`, gerado pela Máquina. Este arquivo não é canon; o histórico por número está em `MEMÓRIAS.md` e o texto anterior inteiro em `extras/arquivo/projeto-ate-2026-11-12.md`.

## O que é (estado de fundo)

- **Frentes:** LibreChat (conversa, aponta no `seth_gateway` `:20126`; **em substituição** pelo chat do painel, sai do sistema depois da entrega medida — decisão do Humano, 07/11/2026), OpenCode (agente/código, no lugar do Goose por decisão do Humano de 07/11/2026; integração ainda não medida) e voz (piper-tts). Ver "Interface".

- **Acesso remoto:** LibreChat (em substituição, ver "Frentes") por `tailscale serve --bg 3080` (só tailnet, nunca `funnel`), hostname do tailnet em `~/librechat/.env` (`DOMAIN_CLIENT`/`DOMAIN_SERVER`, `TRUST_PROXY=1`) (350). Aviso conhecido do `tailscale status`, não bloqueante: `systemd-resolved` e `NetworkManager` "wired together incorrectly" — MagicDNS pode falhar; hostname completo e IP funcionam.

## Máquinas

- **Predator** (master — CachyOS, fish, i7-13650HX, 40GB RAM, RTX 4060 8GB): grafo + OmniRoute, LibreChat, Ollama, git, Obsidian, web.
  - **Boot:** GRUB é o bootloader ativo (Limine saiu na recuperação de 17/09/2026); `mkinitcpio` com `lvm2` logo após `block` (raiz em LVM sobre 2 NVMe, Btrfs); kernel de reserva `linux-cachyos-lts` com preset e `initramfs` (435). **Fora do boot:** `agata.target` (sob demanda desde 29/10/2026) e `ollama.service` (desde 07/11/2026, decisão do Humano; medido `disabled`). Os atalhos não ligam nem param o Ollama; `seth-parar` só descarrega os modelos.
  - **Suspensão:** S3 (`deep`) por `/etc/systemd/sleep.conf.d/10-agata-deep.conf` (`MemorySleepMode=deep`), com driver NVIDIA 615 open (`NVreg_UseKernelSuspendNotifiers=1`). O GRUB ainda tem `mem_sleep_default=s2idle` e não tem `nowatchdog` (101), mas o arquivo do systemd vence na suspensão. Desfazer: `sudo rm /etc/systemd/sleep.conf.d/10-agata-deep.conf` (540).
  - **Vigiar:** suspender e acordar em loop (124); se voltar, procedimento em `PROCEDIMENTO_LOGIN.md`. Ruído conhecido: o teclado USB externo (`1-10.3`) reconecta sozinho no resume. A contenção antiga `predator-suspend-inhibit.service` está desabilitada (540).
  - **Discos:** SMART `PASSED` nas duas NVMe (24/09/2026); `Unsafe Shutdowns` altos são o padrão de desligamento não-limpo deste hardware (539). Causa raiz desse padrão: não fechada.
  - `/etc/default/grub.bak.20260812-155431`: rede de segurança das mitigações de GRUB; não apagar sem boot limpo confirmado (101).
- **Orusoua** (réplica Windows 11, leitura/failover) — *planejado*.

## Cérebro

Fonte viva da ordem dos modelos: o próprio OmniRoute (`/api/combos`) e `config/modelos-gratuitos.md` — não este texto.
- **Seth (conversa e agente):** cascatas grátis do OmniRoute (`strategy: priority`). Remotos primeiro, Ollama no fundo (546)/(547); desde 03/10/2026 sem Groq nas 3 filas do LibreChat e sem `llama-cpp/*` em fila automática nenhuma (648)/(649). Ordem viva por rota: `config/modelos-gratuitos.md`. O Laya escolhe a fila no `seth_gateway`, com fallback pela regra de tamanho quando indisponível, lento ou inseguro; as travas determinísticas prevalecem. O Jev acompanha em sombra. Detalhes em "Decisor local". O combo próprio `seth-codigo` era do Goose; o OpenCode ainda não tem consumidor medido.
- **Local principal: `qwen3.5-9b-64k`** (Ollama, `custom:qwen-local-ctx-override`) — nunca a tag oficial `qwen3.5:9b`, que reproduz o bug de `num_ctx` (121). Convenção: `PARAMETER num_ctx 65536` em Modelfile próprio, tag `-64k`, porque o endpoint OpenAI-compatível do Ollama ignora `num_ctx` por desenho ([`ollama/ollama#16814`](https://github.com/ollama/ollama/issues/16814); (133)-(135)). VRAM de pico em uso real: 89-92% dos 8.188 MiB (log em `~/agata_vram_producao_*.log`). **Regime de auditoria** desde (140): cada resposta é auditada pelo Humano; sai do regime quando o Humano pedir, evento e não prazo (141).
- **Fundo local da cadeia da Seth:** `ollama-local/qwen3.5-9b-64k:latest` (de volta em 25/10/2026; o MoE inventava estado com o prompt real), pela connection `ollama-local` (`:11434`) do OmniRoute; entra só se todos os remotos falharem (402)/(403).
- **Locais sob demanda (`llama.cpp`):** `llamacpp-agata` (MoE `Qwen3-30B-A3B-Instruct-2507`, `:20129`, `--n-cpu-moe 36`, ~31 tok/s, `PartOf` sem `WantedBy`) e 4 modelos de 20/09/2026 — `nemotron-3.5-lightning` (geral), `qwen3-coder-30b-a3b` (código), `phi-4-mini` (leve), `gpt-oss-20b` (agentic, quant `ggml-org` MXFP4; o `unsloth` Q4_K_M trava o sampler). Um serviço systemd cada; não cabem todos ao mesmo tempo; com o local principal na GPU, subir outro pode falhar por VRAM — limite de hardware, não bug (611). **Fora de todo caminho automático desde 03/10/2026** (combos e Conselho Remoto, (649)): um que voltou sozinho depois de OOM empurrou o Ollama para a CPU (648). `llamacpp@.service` não tem `Restart` nem `[Install]`: só sobe à mão, depois de conferir `nvidia-smi`. Portas e ressalvas: `config/modelos-gratuitos.md`, `config/portas-agata.txt`.
- **`gemini-2.5-flash`** (Google API, grátis, ~20 requisições/dia): alívio quando o local falha (140).
- **Último recurso manual:** `llama3.1:8b` — sem tool-calling, fora da cadeia.
- **Limite de classe:** modelo local neste hardware tem teto de ~14b/9GB — `PROJETO_REFERENCIA.md`, "VM do Marcos".

## Serviços (boot)

Portas: `config/portas-agata.txt` é o manifesto que o P-4 confere contra o bind real — fonte da verdade, não esta seção. `:20131`/`:20132` são do próprio `omniroute`, só loopback: `embedWsProxy` (proxy WebSocket das UIs embutidas) e `liveServer` (WebSocket do painel, `/live-ws`) — lido no código do OmniRoute 3.8.50 em 13/10/2026, deixou de ser `lacuna` (420).

**`agata.target`** (`systemd --user`, sob demanda desde 29/10/2026: não sobe no boot; o atalho `seth` liga, `Parar Seth` desliga) puxa:
- `omniroute` (`:20128`) e `omniroute-sanitizer` (`:20127` — os callers usam este; `sanitizar_payload()` em `redesign/router/sanitizar.py`, `--autoteste`, sanitiza segredo antes do egresso e bloqueia payload profundo ou largo demais (328)). `requestQueue.maxWaitMs = 45000` no banco do OmniRoute (362)/(363); clone novo herda o valor pelo drop-in `redesign/systemd/dropin-omniroute-resilience.conf` (`RATE_LIMIT_MAX_WAIT_MS`) (588).
- `openvino-whisper` (`:20130`, STT na iGPU) e `openvino-embeddings` (`:20134`, embeddings na iGPU); venv `igpu/.venv` com `torch==2.14.0+cpu`, sem libs CUDA.
- `obsidian-ro-proxy` (`:27125`, só leitura, `ro_proxy.py`) e `obsidian-app.service` (Flatpak `md.obsidian.Obsidian`, `After=graphical-session.target`) — o app é o **backend real** do proxy: com ele fechado, o proxy devolve **403** ("upstream inacessível"), que parece permissão negada e não é.
- `agata-drain` (oneshot: drena o WAL do grafo no stop, nunca corta um commit).
- `ollaya` (`:11435`, contêiner CPU pinado por digest) — decisor local; ver "Decisor local".

**Gateway e voz sobem com o `agata.target` (sob demanda, não no boot); demais frentes pelo atalho `seth` / `Parar Seth`:**
- `seth-gateway` (`:20126`, habilitado no `agata.target`) — reidrata a Seth; ver "Interface".
- `seth-verificador` (`:20141`) — **único caminho de execução da Seth, read-only.** `POST /verificar` roda um de 10 comandos fixos (`perimetro`, `estado`, `git_status`, `git_log`, `git_diff_stat`, `git_sync`, `selos`, `suite_controles`, `servicos`, `p8_verificar`), argv fixo, sem shell, saída redigida pela régua do P-1, teto com total declarado (423).
- `seth-escriba` (`:20140`) — escrita append-only; detalhes de autorização, limites e isolamento em `extras/projeto-detalhe/servicos-e-interface.md`.
- `seth-gateway` — bloqueia envio a modelo externo sem classificação explícita `public`; o modelo `seth-public` declara publicamente que todo o contexto da conversa pode sair para provedores externos. Outros modelos externos sem classe retornam 403; aliases locais continuam locais. O bloqueio atua antes do encaminhamento ao sanitizador/OmniRoute.
- Stack Docker do **LibreChat**: `librechat` na bridge de ferramentas `librechat`/`br-librechat` e na bridge interna `librechat-data` (Mongo/Meili); publica só `127.0.0.1:3080` e fala com a Máquina pelo relé `librechat-ponte-host` (538). Mongo e Meili ficam somente em `librechat-data`, sem rota para o relé. **Em substituição** pelo chat do painel (decisão do Humano, 07/11/2026): sai do sistema depois que o substituto estiver no ar e medido. Desde 07/11/2026 os quatro contêineres estão com `restart=no` (medido com `docker inspect`, rodando), então nada do LibreChat sobe no boot; antes era `unless-stopped` em tudo. A fonte `redesign/librechat/docker-compose.yml` ainda diz `unless-stopped` (pendente: alinhar em proposta própria). Compose em `~/librechat/`, fonte em `redesign/librechat/`; o atalho `seth` sincroniza `librechat.yaml` e `data/mcp/canon-mcp.mjs` e reinicia o container só se algo mudou (401).
- `piper-tts` (`:8890`, voz pt-BR local, habilitada no `agata.target`) (387) · `discord-mcp` (`:20135`) e `navegador-mcp` (`:20136`), ver "Interface".

**Também no boot:** `agata-manutencao.timer` (janela diária) · `agata-vault-inbox.timer` (a cada 15 min: nota parada há 10 min no `memoria/obsidian-inbox/`, que o decisor não ache rascunho, vira entrada pelo `seth-escriba`, no working tree, sem commit). Os services de consolidação e de pesquisa só rodam com o OmniRoute respondendo (`ExecCondition` = `scripts/esperar_servico.sh`): no boot, a recuperação do timer chegava 1 s antes dele.

**Manuais:** `agata-warmup.service` pré-aquece o modelo local pesado (cold-start do Ollama). `agata-jogo` (`~/.local/bin/`) lança jogo com o Agata fora da RTX 4060, via `game-performance` da distro — **não** Feral GameMode, que briga com o `ananicy-cpp`.

**Consolidação** (220)/(311): na janela diária 12h15–13h15 (timer das 23:00 desativado), saída só em `propostas/consolidacao-<data>.md` com entrada `(a numerar)`; nunca toca canon (contenção de kernel: `ProtectSystem=strict`); "novo" no log só depois de conferir o arquivo no disco. Ver `extras/projeto-detalhe/servicos-e-interface.md`.

**P-9** (221): `scripts/perimetro.sh` avisa (nunca falha) se uma lista fechada de unidades e containers estiver fora do ar, e quando o Ollama carrega modelo só em parte na GPU (648)/(649). Lista e motivo: `extras/projeto-detalhe/servicos-e-interface.md`.

**Não recriar:** `agata.service`, `agatha.service`, `agata-rest.service` (ausentes, (107)/(539)), `hermes-gateway.service` (Hermes removido, (312)), `kokoro-tts` (removido, (593)/(594)).

## Interface

- **Executor / loop:** grafo + OmniRoute pelo CLI `agata` (`~/.local/bin/agata` → `redesign/grafo/cli.py`: `up`/`down`/`status`/`verify`/`commit-entry`/`run`/`resume`/`logs`).
- **`seth_gateway`** (`redesign/router/seth_gateway.py`, `:20126`, sob demanda) — reidrata a Seth antes do sanitizador; **qualquer frontend que aponte para `:20126` fala com a Seth hidratada.** Modo `compacto` (default): identidade + Regra 1 + estado de `estado_para_eco.sh`; filtros de título e keepalive; roteador por complexidade; `X-Modelo-Real` carimbado pela Máquina; a resposta anterior é auditada sem modelo e volta como `AUDITORIA-TURNO-ANTERIOR`; afirmação falsa nova em prosa fica fora e a já desmentida volta acusada pelo catálogo. Texto: `extras/projeto-detalhe/servicos-e-interface.md`.
- **LibreChat** (`127.0.0.1:3080`, Docker sob demanda) — conversa informal, aponta para `:20126`. **Em substituição** pelo chat do painel (decisão do Humano, 07/11/2026): sai do sistema depois da entrega medida; a descrição abaixo segue valendo até lá. Endpoint `agents` com o Agent `agent_4KlxSMeX5Y8cWQVODkJfH` ("Seth", provider `Seth` → model `seth-livre`, MCP `canon` anexado — MCP só se anexa a Agent) (415). `modelSpecs enforce: true`, spec default `seth-livre` → o Agent; specs `custom` só para debug. `titleConvo: true` (413). Memória do LibreChat desligada (`memory.disabled`) e sem RAG, de propósito: a hidratação vem do `seth_gateway`. Conta única (`ALLOW_REGISTRATION=false`); Meilisearch para busca de conversa. Config em `redesign/librechat/`.
- **OpenCode** (`~/.opencode/bin/opencode`, versão 1.0.180, fora do PATH e sem modelo configurado) — agente de terminal de primeira classe, no lugar do Goose (decisão do Humano de 07/11/2026). Provedor, gateway e payload ainda não medidos. O Goose sai do sistema; os dados dele ainda não foram removidos. Codex CLI terciário.
- **Voz:** piper-tts (`:8890`, pt-BR local, default desde (387)) + Whisper na iGPU. Remoto = HTTPS via Tailscale.
- **Escrita da Seth:** só pelo `seth-escriba` (append-only, sem commit); leitura pelo `canon-mcp`/`:27125` (read-only) (318).
- **Portas de entrada** (667): as diretrizes comuns — Regra 1, medir antes de afirmar, P-8, modo conciso padrão, economia de tokens — estão no `AGENTS.md` da raiz, lido por Codex, Gemini CLI, Cursor e outras ferramentas; o `CLAUDE.md` o importa; a nuvem (`PROMPT_CARREGAMENTO.md`), a Seth e o agente de terminal trazem as mesmas linhas (o OpenCode ainda não medido; a doutrina do gateway segue em `redesign/goose/AGENTS.md` até a remoção do diretório). Lista em `config/portas-de-entrada.txt`; o P-23 avisa se alguma porta ficar sem elas.
- **Atalhos** (`~/Área de trabalho/`, scripts `~/.local/bin/seth`/`seth-parar`): **Seth** (sobe tudo e abre o navegador), **Seth (agente)** (OpenCode no terminal, no lugar do Goose), **Parar Seth** (para as frentes e o `agata.target`, e libera a VRAM). Integrações futuras (Home Assistant, WhatsApp) entram sob demanda, cada uma como servidor MCP.
- **Ponte Discord e controle de navegador** (339): `redesign/mcp/discord/` (poll, não push; egresso sanitizado por `PADROES_SEGREDO`) e `redesign/mcp/navegador/` (Playwright contra Brave real — não `browser-use`, cuja API sumiu na versão avaliada —, perfil isolado, escrita travada por allowlist de domínio em `~/.config/agata/navegador-dominios-permitidos.txt`). Sobem e descem com `seth`/`seth-parar` (`discord-mcp.service`/`navegador-mcp.service`, `redesign/systemd/`, sem `[Install]`). Transporte HTTP; o LibreChat os alcança por `172.29.7.1` (relé, (538)); `librechat.yaml`: `mcpSettings.allowedDomains: ["127.0.0.1", "172.29.7.1"]` — sem isso o LibreChat bloqueia MCP remoto (guarda contra SSRF).

## Estado dos bugs e dos testes

Só o que segue aberto, ou deixou mecanismo vivo. Os fechados estão em MEMÓRIAS e, até 02/10/2026, verbatim em `extras/arquivo/PROJETO-ate-2026-10-02.md`. Fechados em 13/10/2026 (MEMÓRIAS (655)): cold-start do Ollama, filtro de título, hidratação suspeita, manifesto do HD, drift dos derivados (agora P-22), portas `:20131`/`:20132`, log da consolidação.
- **Risco de fundo, não bug — provedor travado no OmniRoute:** a conexão pooled espera até `OMNIROUTE_DIRECT_HEADERS_TIMEOUT_MS` (padrão 30000) antes de tentar de novo num socket novo. Disparou 323 vezes de 02/09 a 10/10/2026 — 155 `api.z.ai`, 90 Gemini, **55 o próprio Ollama local** (todos até 23/09, quando o `llama.cpp` empurrava o Ollama para a CPU (648); nenhum depois). Por isso o valor **não** baixa: um fundo local lento seria cortado. Cold-start medido em 13/10/2026: 9,1 s, resposta com tool-call (modelo fora da GPU, ainda no cache de disco; logo após reboot pode demorar mais — coberto pelo retry em socket novo dentro dos 45 s). Mitigação: `maxWaitMs = 45000` (362)/(363) e os provedores instáveis no fim das filas ou fora delas (653)/(654)/(655). Desde 04/10, 1 disparo. Medir: `grep -c "response-start timeout" ~/.omniroute/logs/application/app.log`.
- **Como testar uma fila sem se enganar** (655): `scripts/queda_por_elo.py`, nunca `curl` com `max_tokens` minúsculo — modelo com raciocínio interno devolve vazio e o OmniRoute cai pro próximo elo — e nunca dois pedidos Mistral no mesmo segundo (limite 1 req/s → 429). Pelo `:20126`, mensagem curta vira `seth-rapido` antes de chegar ao OmniRoute.
- Os protocolos TES-001/TES-002 foram aposentados em 09/09/2026 — (417); o que cobriam está em `PROTOCOLOS.md`, "Cadeia de auditoria em camadas", no P-7 e em `FALHAS.md`.

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
