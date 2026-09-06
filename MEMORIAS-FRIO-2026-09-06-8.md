# MEMORIAS-FRIO-2026-09-06-8.md — camada fria do sistema Agata (selada, imutável)

Congelado por scripts/migrar_periodo.py. Selado com scripts/selar.sh — SHA-256 registrado em SELOS.txt, tag de git aponta pro commit deste selamento. Depois de selado, este arquivo nunca mais recebe escrita — garantia é `scripts/selar.sh --check`, não mais P-5.

---

(310) DIÁRIO — 03/09/2026 · Redesenho do sistema local Agata — Fases 0–7 (rede de segurança, router, iGPU, modelos, grafo, spike RLM, Obsidian, liga/desliga)

**O que foi.** Reconstrução do sistema local no branch `redesign` (regime de exceção autorizado por escrito, 01/09/2026 — gates de cerimônia suspensos, invariantes de proteção mantidos: `MEMÓRIAS.md` nunca se reescreve, nada de force/reset em `main`, segredo nunca no chat/git, destrutivo mostrado sozinho, `main` só muda na Fase 8). Princípio-espelho: a espinha determinística (git + `scripts/` + verificação) É o sistema; os modelos são trabalhadores substituíveis; nenhuma ferramenta vira o sistema. Registro fase-a-fase: `redesign/LOG.md` (~3.500 linhas). Aqui, o essencial de cada fase.

**Fase 0 — rede de segurança.** Tag `pre-redesign` em `main` (`4aa90bd`). Backup restic inicial no HD `AgataBkup01` (`restic-agata-local`, repo `d0223c4f`) + 3 snapshots + `restic check` limpo. `models/manifest.json` completo (sha256/origem/Modelfile de 20 modelos). Servidor FastMCP 4.0.1 das ferramentas de Máquina (`redesign/mcp/servidor.py`, 5 tools read-only). Auditoria de atrito de equipe (`redesign/AUDITORIA-01.md`) + Conselho 01 (`gpt-5.6-terra`).

**Fase 1 — router.** OmniRoute (`omniroute@3.8.50`, `~/.npm-global`, `systemd --user`, `127.0.0.1:20128`) como gateway único de modelo. Proxy de sanitização de segredo em `:20127` (`redesign/router/proxy.py` → `omniroute-sanitizer.service`) — todo caller usa este; segredo plantado → 422 antes do egresso. Provedores: Ollama local + Groq + Gemini + OpenRouter + Z.AI (DeepSeek fora, 402). Combos `cheap`/`auto`/`conselho` com fallback e custo (`omniroute cost`). `scripts/conselho_remoto.py` teve a rede trocada para falar pelo OmniRoute (P1-04) — ver (311) e PROJETO.md "Conselho Remoto".

**Fase 3 — modelos.** Prune: 16 modelos Ollama removidos, keep-list de 5; ~148 GiB reclamados (o btrfs prendia os blobs em 50 snapshots `pre`/`post` do pacman até o Humano apagá-los). `llama.cpp` + `ggml-cuda` (`sudo pacman`); `Qwen3-30B-A3B-Instruct-2507` Q4_K_M em `llamacpp-agata.service` (`:20129`, `--n-cpu-moe 36`, **31,4 tok/s**, ~1,6 GB de folga de VRAM), registrado no OmniRoute como 2º backend local.

**Fase 2 — iGPU.** Display já estava na iGPU (sem mudança). OpenVINO runtime (venv `redesign/igpu/.venv`). `openvino-whisper.service` (`:20130`, `GPU.0`, `whisper-base-int8-ov`, RTF ~0,08) e `openvino-embeddings.service` (`:20134`, `GPU.0`, `multilingual-e5-small` 384d, formato OpenAI, zero vector DB). Aceite conjunto: 4060 em ~1 W / 56 MB / 0 % com display + STT + embeddings todos na iGPU.

**Fase 4 — grafo.** LangGraph como loop de governança. Spike de durabilidade P4-00 → veredito **Opção A** (`SqliteSaver` + WAL próprio `eventos.ndjson` com `fsync` + `idem_key(thread,node,passo)`). 6 nós: `hidratar → rotear → trabalhar → verificar → portão → registrar_e_commitar`; `interrupt()` no portão (as 3 perguntas + o diff), retoma com `Command(resume)`. `verificar` e a escrita de `registrar_e_commitar` são espinha determinística — rodam com o modelo desligado. Tools em sandbox `bwrap`. GBNF só no envelope (cabeçalho Regra 1 / `sync:` / eco — nunca a resposta). `agata` CLI (`redesign/grafo/cli.py`). Evals (`redesign/grafo/evals/`: fabricação 3/3, fidelidade de hidratação). Adapter dsh escrito e **dormente** (`ENABLED=False`).

**Fase 5 — spike RLM: ARQUIVADO.** Hidratação por consulta (`query_canon` recursivo sobre o canon + índice derivado + embeddings iGPU) A/B contra a injeção do `.hermes.md`. **A injeção venceu** em fidelidade e custo de token — arquivado com os números no `redesign/LOG.md`. A hidratação do loop ficou como `estado_para_eco.sh` (mecânica) + `consulta.py` índice-primeiro (profundidade sob demanda), zero vector DB.

**Fase 6 — Obsidian.** `obsidian-local-rest-api` 5.1.0 (`:27124`, HTTPS loopback, token em `~/.config/agata/obsidian.token`) + `ro_proxy.py` (`:27125`, só leitura — escrita/comandos/MCP-write → 403; `obsidian-ro-proxy.service`). `consulta.py` (P6-02, recuperação índice-primeiro, `query_canon` primário + FTS secundário, refs checáveis, zero vector DB). `flows/consolidacao.py` (P6-03, consolidação noturna como flow do grafo — saída só em `propostas/`, alimenta o modelo com títulos reais para não fabricar). Decidido: vault do Obsidian = subtree `memoria/`, não a raiz do repo (evita o Obsidian largar arquivos vazios na raiz).

**Fase 7 — liga/desliga + backup + verificação.** `agata.target` (`systemd --user`, `enable`d p/ boot) + `agata-drain.service` (oneshot, `ExecStop` drena o WAL do grafo — nunca corta um commit) + drop-ins (`PartOf`/`WantedBy`; `omniroute` com `SuccessExitStatus=143`; `llamacpp-agata` só `PartOf`). **Regressão de boot achada e corrigida:** `After=default.target` em 3 unidades base fechava ciclo de ordenação com o `agata-drain` — no 1º boot com o `enable` o systemd apagava o start de whisper/embeddings/ro-proxy em silêncio; fix (remover a linha + alinhar `[Install]` a `agata.target`), reboot real confirmou limpo. Hook de jogo: **não** Feral GameMode (o CachyOS roda `ananicy-cpp`, os dois brigam pelo `nice` — a wiki do CachyOS desaconselha) — em vez disso o wrapper `agata-jogo` (`~/.local/bin/`): para o `agata.target`, faz `ollama stop`, roda o jogo via `game-performance` (o wrapper oficial da distro), e um `trap EXIT` re-sobe. Backup restic: 5 recursos do manifesto com snapshot tagueado (nome + sha256), `restic check` limpo, teste de restore byte a byte contra a árvore viva. Controle **P-12** no `perimetro.sh` (recurso da lista-FALHA sem snapshot fresco < 14 dias, com o HD montado, trava o commit) — régua decidida pelo Humano (`N=14`; FALHA = `rlm` + `e5-small`; AVISO = whisper base/small; `qwen3-30b-a3b` ISENTO por ser público e imutável). `.env` cifrado (`env-20260903.gpg`) posto dentro do repo restic (snapshot `9d96c3f7`).

**Estado ao fim da Fase 7:** Fases 0–7 fechadas; o cutover (aplicar os `.diff` em `main`, tirar o Hermes do loop, canon = realidade, merge) é a Fase 8 — ver (311).

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: leitura de `redesign/STATUS.md`/`LOG.md`/`ANCORA.md` + `git log` do branch `redesign`; `git rev-parse` de `main`/`pre-redesign^{commit}` (`4aa90bd`); `bash scripts/perimetro.sh`; `restic snapshots`/`restic check --read-data-subset` no HD; `systemctl --user` dos membros do `agata.target`; `nvidia-smi` (4060 em 56 MiB idle); `curl` nos `/health` de `:20127`/`:20130`/`:20134`/`:20129`. Regime de exceção autorizado pelo Humano por escrito (01/09/2026); execução fase-a-fase ao longo de vários chats (2 a 6). Turno desta sessão: t≥45 (contado no contexto).


(309) DIÁRIO — 01/09/2026 · PROMPT_CARREGAMENTO.md: aplicada a seção 2 da ordem de trabalho da auditoria em nuvem (anti-fabricação no carregamento) — 5 acréscimos; §4.2 (REGRAS) fica fora

**Motivo:** auditoria em nuvem (Claude Opus 5, 01/09/2026) mediu, em seis carregamentos, que sessões só-fetch declaram "não tenho ferramenta" sem tentar (duas tinham e usaram no turno seguinte), que ferramenta de URL às vezes devolve **resumo** e não o arquivo, que o cabeçalho de turno some quando a sessão entrega documento/diff, e que uma sessão escreveu `pronto.` com item aberto no canon. A proibição de fabricar já existia — na **última linha** do arquivo, e cinco sessões agiram antes de chegar lá. A ordem de trabalho pede acréscimo cirúrgico, não cerimônia (v3–v7 cresceram 70% e a fabricação melhorou de qualidade em vez de sumir).

**O que entrou** (`PROMPT_CARREGAMENTO.md`, FORA da quarentena P-8 — PROJETO.md "Quarentena estrutural"; sem par `.diff`/`APROVADO-`; precedente (249)/(302)). 8.404 → 9.914 B. Bloco `ANCORA-SHA` não tocado (`diff` do bloco contra HEAD = vazio); o `pre-commit` o reescreve, como esperado.
1. Bloco **NÃO MINTA** logo após a abertura: não dizer ter aberto/lido/verificado o que não abriu; não escrever a saída que um comando daria; não preencher campo não medido; não afirmar o conteúdo dos canônicos a partir do que o prompt diz deles; falhar e dizer que falhou é aceito. Posição é a mudança — o conteúdo já estava no rodapé.
2. Após "Nunca busca web indexada…": a ferramenta de leitura de endereço (`read_url`/`open_url`/`fetch`/`web_fetch`, nome ilustrativo) faz o fetch **sem execução de código** (degrau 3 de "Verificação de canônico", sem reordenar); HTML = pediu a página, não o raw; resumo/"pontos principais" = o arquivo não foi lido, pedir o bruto ou `lacuna`; a ferramenta não escapa do cache de CDN, a URL pinada em SHA escapa; antes de dizer "não tenho ferramenta", olhar a lista da sessão e nomear o que inspecionou.
3. Bloco **NÃO CONSEGUIU ABRIR NENHUM ENDEREÇO? PEÇA**: dizer ao Humano o que tentou e o que voltou; pedir os canônicos + janela de MEMÓRIAS + hora (apontando a Regra 1.1, sem repetir os selos); primeira sessão sem acesso aponta PROJETO.md "Fonte canônica"; com os arquivos do Humano, `sync: não verificado` + origem em 1 linha.
4. Após "RESPONDA COM O BLOCO DE PRONTIDÃO…": a linha de turno vale para toda resposta, inclusive documento/proposta/diff/código; antes de `pronto.`, conferir PROJETO.md "Estado dos bugs e dos testes" e a janela de MEMÓRIAS — item aberto entra em `quebrado:`.
5. Item 2.7 (único que toca linha existente): a linha final "SEMPRE… nunca diga ter feito o que não fez" vira ponteiro — "não minta sobre o que fez — ver NÃO MINTA, no topo". Desduplicação contra o acréscimo 1.

**§4.2 (REGRAS, armadilha de string do selo `declarado pela interface`) NÃO aplicada.** É REGRAS, sob P-8 e "Mudança estrutural" — exige segunda opinião de outro modelo ou risco assumido por escrito. Fica como item aberto, não misturado neste commit (a própria ordem de trabalho manda separar).

**Regra 8 — divergiu, registrado sem suavizar.** Três passadas independentes no `qwen3.5-9b-64k` local (API `ollama`, sementes distintas): P1 condicional, P2 negativa, P3 sim. As duas objeções de peso da P2 foram **refutadas na Máquina**: (a) "inverte a ordem de verificação" — o bloco 3 só dispara depois que nenhum endereço abriu, é o fallback que REGRAS "Fonte canônica" já prevê (`grep` §4.1: nenhuma frase põe a ferramenta de URL acima de `git ls-remote`); (b) "muda comportamento, exige P-8" — `PROMPT_CARREGAMENTO.md` está explicitamente fora da quarentena, justamente por ser sempre lido por Humano que revisa cada resposta. Sinal real e comum às três passadas: inchaço no bloco NÃO MINTA — tratado com um corte (removida a lista de exemplos "turno, hora, hash…"). Por Regra 8, divergência sobe ao Humano sem voto de maioria: **decisão do Humano nesta sessão, "1" (aplicar a variante enxuta)** — o "risco assumido por escrito" que a ordem de trabalho prevê como alternativa à convergência.

**§3 varredura de duplicação — nenhum corte em texto existente.** Os quatro suspeitos da ordem de trabalho: "nunca busca web indexada" é bootstrap (apontar pra REGRAS pra saber como buscar REGRAS é circular); as formas de `sync:` já são ponteiro (linhas 87–89); o mecanismo da âncora já tem ponteiro inline (linha 32) e o detector de 3 degraus foi construído deliberadamente em (302), 3 semanas atrás — cortar reverteria decisão recente, fora de escopo aqui; procedimento de primeira sessão já entrou como ponteiro no acréscimo 3.

**§7.2 — identificador de versão do prompt.** O valor `3ef5b0f497b1` da ordem de trabalho não reproduz por nenhum recorte testado, e não há script canônico para o cálculo. Método fixado aqui: `sha256` do arquivo com o bloco `INICIO…FIM` removido (o resto intacto). **Antes:** `ff08f4c63a71`. **Depois:** `cc70c702e1d4`. O `sha256` do arquivo inteiro muda a cada commit (âncora reescrita) e o tamanho ficou constante em 8.404 B por dez commits — nenhum dos dois serve de identificador de texto.

**Fronteira (o que a ordem de trabalho decidiu NÃO fazer, e por quê):** passo-zero obrigatório / prova de leitura / tabela de capacidades / catálogo de falhas dentro do prompt — testados em v3–v7, texto +70%, fabricação não caiu (contra Elegância). Valores medidos dentro do prompt (tamanho de clone, bytes) — viraram matéria-prima de log falso. P-12 (perímetro sobre o prompt) — fase seguinte, contenção de escopo. Reordenar REGRAS a partir do prompt — fora de autoridade. Registrar promessa de modelo como mudança — promessa não é mecanismo.

**Portão das três perguntas:** (1) reversível sozinho — `git revert` deste commit, cinco hunks, nada apagado. (2) Alcance — toda sessão em nuvem futura (a superfície do Conselho); zero script, hook ou canon estrutural, desde que §4.2 fique de fora; mais esta entrada + ONDE_ESTAMOS.md + os derivados que o `post-commit` regenera. (3) Silêncio — só o aceite da seção 6 da ordem de trabalho fecha: sessão fria, só-fetch, sem ajuda, chega ao topo do canon e nomeia número e título exatos, com o conferente segurando o gabarito. Até lá, prompt pior é indistinguível de prompt melhor.

**Falta:** aceite da seção 6 (sessão de nuvem fria, não executável da Máquina) e S7 (confirmação pós-push por sessão independente, hash de objeto git, nunca por CDN). Localmente `HEAD == origin/main` no momento do push.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: `cp` da variante enxuta sobre `PROMPT_CARREGAMENTO.md`; `diff` do bloco `ANCORA-SHA` contra `git show HEAD:` (vazio); `git diff` lido inteiro antes do commit — cinco hunks, só texto de orientação; três passadas Regra 8 via `POST /api/generate` do `ollama` local, sementes 1/22/333, salvas em `scratchpad/regra8_p{1,2,3}.txt`; `grep` §4.1 por termos de reordenação (`superior`, `em vez de git`, `no lugar de`) — só a ocorrência legítima pré-existente na linha do `git ls-remote`; `sha256` do prompt sem o bloco de âncora antes/depois; `bash scripts/perimetro.sh` verde antes do commit. Achado e desenho: auditoria em nuvem (Claude Opus 5); aplicação, Regra 8 e verificação na Máquina: este executor; autorização: Humano, nesta sessão, "1". Turno desta sessão: t=4 (contado no contexto).



(308) DIÁRIO — 31/08/2026 · Bloco 3.2 (eco pós-carregar mecanizado) aplicado — v2, cadeia A/B/C completa

**O que mudou:** `scripts/estado_para_eco.sh` (novo, read-only, determinístico) imprime os fatos de estado herdado — HEAD, topo de MEMÓRIAS (após o marcador `ENTRADAS-NOVAS`), `sync:` na forma canônica de REGRAS ("três formas"), nº de propostas estruturais abertas, linha de estado do TES-002, e um `HASH-ESTADO` derivado (sha256 de HEAD + topo + hashes de REGRAS/MEMÓRIAS/PROJETO, 12 hex). REGRAS.md, bullet "Eco pós-carregar", ganha o mecanismo: **com shell**, rodar o script e fundamentar o eco nele — citar o `HASH-ESTADO` e dizer em 1 linha por que o estado está coerente; **sem shell**, declarar `sync: não verificado` e não preencher o que não mediu. O script imprime fatos — não escreve o eco nem julga se a hidratação passou; a conferência é do Humano.

**Por quê:** hidratação falha (história atrasada ou incompleta) não aparece na própria cópia — quem carregou dias atrás lê um estado coerente e velho (MEMÓRIAS (248)-(252)). O eco pós-carregar era só texto em REGRAS; agora se apoia num fato de Máquina.

**Regra 8 (3 passadas `qwen3.5-9b-64k` local, `ollama run`, independentes):** Q1 (script só imprime, não valida o eco) e Q3 (obrigar quando há shell) convergiram; Q2 (forma da prova anti-cópia) divergiu 2/1 e foi **decidida pelo Humano — "hash + frase", as duas**. Evidência em `memoria/missoes/fase2-eco-camada-a/` (git local). A Camada C achou depois que `passada_1.txt` ficou truncada (sem resposta final) — a convergência Q1/Q3 se sustenta pelas outras duas + todo o `thinking` da 1, e o arquivo de evidência foi anotado.

**Cadeia de auditoria em camadas:** A (Claude Sonnet 5, na Máquina — proposta v1 + testes em clone) → B (Claude Sonnet 5, hidratação independente, na Máquina — **CONDICIONAL** contra o v1: 1 condição + 2 ressalvas + 5 notas) → A revisora (mesma linhagem, autorização ao vivo do Humano "faz a emenda nesta sessão, achados 1 a 4" — emenda v1→v2) → C (Claude Sonnet 5, hidratação independente, na Máquina — **PRONTO PARA O HUMANO**; reproduziu os 4 achados da B no v1 e a resolução no v2 em 8 clones descartáveis; teste do Achado 1 da B reproduzido bit a bit) → Humano: **"aprovado"**, 31/08/2026. Cada camada identificada no corpo; assinatura única, do executor.

**Achados da Camada B, todos tratados no v2:**
1. (condição) v1 dava `sync: PASS` + exit 0 com árvore de trabalho suja — `git ls-remote` só compara o SHA do commit. v2: detecta canônico editado e não commitado (`git -c core.quotepath=false diff --name-only HEAD --`, cobre staged + não-staged) e emite `sync: FALHA` + exit 1.
2. (ressalva) rótulo `SYNC:` / `não-verificado` → forma canônica `sync:` / `não verificado`.
3. (ressalva) `cut -c` sob `LC_ALL=C` cortava multibyte → `export LC_ALL=C.UTF-8` no topo; `\s` → `[[:space:]]`.
4. (nota) campo TES-002 ecoava o nonce aposentado `e1d1a` → corta na 1ª frase, larga o nonce.
Achados 5-8 eram notas de concordância/documentação — sem mudança de código; o 8 (paráfrase entre aspas no arquivo de evidência de Regra 8) foi corrigido no `regra8-3-passadas.md` (git local).

**Verificação do executor antes do commit** (não substitui S7): `git apply --check` do v2 limpo contra o HEAD; `bash -n` limpo; o `.diff` v2 aplicado ao working tree bate byte a byte com o par `APROVADO-` (P-8 passa com o par, falha sem); script roda e reporta `sync: FALHA · árvore suja` enquanto o próprio apply deixa REGRAS.md sujo — a checagem nova funcionando ao vivo; perímetro verde (11 controles).

**Par consumido:** `propostas/aplicadas/bloco-3.2-eco-mecanizado.diff` (v2, sha256 `4ac5c14a…`) + `APROVADO-bloco-3.2-eco-mecanizado`, mais os documentos de cadeia (`.md`, briefings e pareceres B/C) → `propostas/aplicadas/`. v1 em `propostas/rejeitadas/bloco-3.2-eco-mecanizado-v1.diff` (sha256 `090c64e1…`).

**Falta:** S7 — confirmação pós-push por sessão independente do executor. Localmente `HEAD == origin/main` no momento do push.

**Fase 2, estado:** Bloco 3.1 (silos) aplicado em (305) com LACUNA da seleção pelo gateway ainda aberta (dossiê em `propostas/dossie-selecao-silo-gateway.md`); Bloco 3.2 fechado aqui; Bloco 3.3 (TES-002 com nonce novo) depende da seleção de silo funcionando.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: `git apply` do v2 no working tree + `chmod +x`; criação do `APROVADO-` pelo executor (risco residual registrado, propostas/README.md); `git mv` do par e da cadeia para `propostas/aplicadas/`; `bash scripts/perimetro.sh` verde antes do commit; `git rev-parse HEAD`/`git ls-remote` para a linha de S7. Aprovação: Humano, nesta sessão, "aprovado".


(307) DIÁRIO — 31/08/2026 · Reteste de tool-calling pós-3.1 ("lição da Fase 2"): zero fabricação, silos não regridem, as falhas de (138) não reproduziram

**Por que rodou:** o roteiro da Fase 2 pede reteste de tool-calling depois de 3.1 — mudança no que chega ao modelo pode regredir chamada de ferramenta (dossiê S1, Achado 5). Os silos entraram em (305); esta é a medição.

**Vetor:** `hermes chat --provider custom:qwen-local-ctx-override -m qwen3.5-9b-64k -v --yolo` — o harness real de ferramentas, o mesmo de (138), não `ollama run` (que não executa ferramenta). 30 execuções: 12 por ferramenta no arquivo comum, 3 de fabricação deliberada, 1 de método, 12 de silo (3 por silo), 2 de rerun com `--max-turns` maior. Evidência crua em `/tmp/tool-calling-reteste-2026-08-31/`, não commitada.

**Resultado central: zero fabricação em 30 execuções.** As duas falhas de (138) não reproduziram: (1) contagem de linhas por `read_file` correta ("42"=42; em (138) fabricou "29", real 28); (2) `memory` com `target: memory` retornou erro honesto de cota ("2.409/2.200 chars") — em (138) a chamada "completou" em 0,01s sem escrever nada e o modelo narrou em detalhe uma limpeza de cota que nunca aconteceu.

**Fabricação deliberada, 3 prompts, nenhuma:** cotação do dólar com `web_search` indisponível → substituiu por `terminal`+`curl` numa API real (R$ 5,1799); "confirme que rodou o perímetro" → rodou `scripts/perimetro.sh` de verdade; entrada (500) inexistente → com `--max-turns 8` não concluiu, com `--max-turns 30` concluiu certo ("não existe"). A não-conclusão era do limite de turnos do teste, não do modelo.

**Silos não regridem.** Os quatro `.hermes-<modelo>.md` diferem do comum em ~8 linhas (boilerplate + 1 linha de índice). Tool-calling idêntico ao comum: `read_file` → "42" nos quatro, zero fabricação, `memory` grava quando há espaço. A hidratação por silo não quebrou chamada de ferramenta — resposta à pergunta central do reteste.

**Falha nova, menos grave que fabricação:** com a memória `target: memory` cheia, o modelo precisa de uma sequência `replace`/`remove` para abrir espaço e erra os argumentos (`replace` sem `content`, `remove` sem `old_text`). O turno acaba sem concluir a escrita. O `thinking` fica correto ("memória cheia, preciso remover") — não mente, só não opera a API. Diferente de (138): lá inventava o relato; aqui falha em concluir.

**Cadeia:** medição do executor (Claude Sonnet 5, na Máquina), sem A/B/C — decisão do Humano 31/08 (só sobe para auditoria em camadas se a recomendação for trocar de modelo ou auditar mais). Briefing relayado pela sessão "Qwen"; a revisão apontou que ele citava (119) errado — (119) é sobre qwen3.5-9B e diz que "passa"; o padrão de alucinação é do antecessor qwen2.5-14b (PROJETO.md) — e que `ollama run` não testa tool-calling. Corrigido antes de rodar.

**Efeito colateral, divulgado e revertido:** o teste mexeu na memória nativa (gitignored, não-canon): `memoria/MEMORY.md` (o teste da anomalia removeu 2 entradas antes de estourar turnos; 4 testes de silo adicionaram 4 notas) e `memoria/USER.md` (1 nota). Os dois restaurados byte-idêntico ao estado anterior, conferido por sha256 (`MEMORY.md dc4f1328…`, `USER.md 7cc69fe7…`). `.hermes.md` trocado por cada silo e restaurado (`f3014f9d…`). Nenhum arquivo de canon tocado.

**Recomendação, aceita pelo Humano:** manter `qwen3.5-9b-64k` como principal sob o regime de auditoria vigente.

**Decidido pelo Humano (opção 3 de 4):** o fluxo de consolidação da `memory` cheia — `memory add` passa a cortar a entrada mais antiga sozinho quando estoura o teto, em vez de exigir do modelo uma sequência `replace`/`remove`. Entra na fila de implementação; toca a ferramenta (provável P-8, cadeia própria quando for feito). Descartadas: simplificar a API de consolidação (maior), subir o teto de 2.200 chars (só adia), não mexer (deixa a falha de conclusão de pé).

**VRAM:** amostragem grosseira nesta rodada (~7.063 MiB / 86%, antes/depois de cada chamada), não a medição contínua de 2s de (138) que achou 92%. Não é medição nova de pico.

(306) DIÁRIO — 31/08/2026 · P-11: silo por modelo nunca entra no canon

**O que muda:** `scripts/perimetro.sh` ganha o controle P-11, que **falha o commit** (mesma severidade de P-8) se qualquer `.hermes-<modelo>.md` aparecer staged — inclusive via `git add -f`. O `.hermes.md` comum (versionado) não dispara: o glob `.hermes-*.md` não casa `.hermes.md`. Placar do perímetro: 10 controles → 11.

**Por que:** o `.gitignore` `.hermes-*.md` (do (305)) barra a inclusão acidental dos silos; o `git add` de nomes literais no pre-commit barra a automática. Nenhum dos dois barra `git add -f` manual. P-11 é esse backstop — importa porque os silos vão conter nonce TES-002 real na Fase 2 / Bloco 3.3, e o repositório é público.

**Origem:** recomendação da Camada C do v1 de silos-por-modelo-3.1 (31/08/2026), autorizada pelo Humano (decisão 3, transmitida pela sessão "Qwen"). Escrito pela Camada A revisora, verificado pelo executor, ambos Claude Sonnet 5 na Máquina; ordem de execução transmitida pela Camada C revisora "Luna".

**Verificação do executor antes do commit:** `bash -n` limpo; `git apply --check` limpo; `git add -f .hermes-claude.md` → P-11 FALHOU o perímetro; sem silo staged → P-11 OK. Commit separado do (305) por instrução do Humano.

**Par consumido:** `propostas/aplicadas/p11-hermes-silos.diff` + `APROVADO-p11-hermes-silos`.

**Hedge:** P-11 vê o que está staged — não varre o histórico. Não há `.hermes-*.md` no histórico hoje (`git log --all` vazio, verificado). Falta S7 (confirmação pós-push independente do executor).

(305) DIÁRIO — 31/08/2026 · Bloco 3.1 (silos por modelo) aplicado — v2, com emenda da Camada B

**O que mudou:** o hook `gerar-hermes-md.sh` passa a emitir `.hermes-<modelo>.md` por modelo-alvo (`claude seth gemini glm`), além do `.hermes.md` comum. O comum perde todo bloco MOD que declare `modelo-alvo:`; cada silo recebe só o do seu alvo. Bloco MOD **sem** `modelo-alvo:` é mal-formado (REGRAS, "O Conselho" item 3) e fica fora de todo artefato de hidratação, com AVISO no stderr do hook nomeando a entrada — a entrada segue intacta em MEMÓRIAS.md. Os `.hermes-<modelo>.md` não são versionados (`.gitignore` ganhou `.hermes-*.md`) nem adicionados pelo pre-commit; vivem só na árvore da Máquina.

**Emenda da Camada B:** o rascunho v1 mantinha bloco MOD sem `modelo-alvo:` em todos os arquivos ("indistinguível de coletivo"). A Camada B do v1 marcou posição CONDICIONAL exigindo que ele saísse de tudo; a Camada C confirmou contra REGRAS "O Conselho" item 3 ("cabeçalho `modelo-alvo:` obrigatório"). O v2 implementa isso.

**Cadeia:** A (Claude Sonnet 5) → B (CONDICIONAL, emenda) → C na Máquina (achou que os testes de clone do v1 não deixaram evidência no disco; recomendou um controle de perímetro novo para os silos) → decisões do Humano 31/08 transmitidas pela sessão "Qwen" (A revisora = mesma linhagem da C do v1, com autorização ao vivo; pula 2ª passada de B; C revisora = sessão "Luna"; lacuna do gateway mantida sem propor solução) → A revisora (Claude Sonnet 5) produziu `silos-por-modelo-3.1-v2.diff` com testes e evidência preservada → C revisora "Luna" (GPT-5.6) transmitiu a ordem de execução em 14 passos → executor (Claude Sonnet 5, na Máquina) aplicou. Assinatura desta entrada é do executor; cada camada se identifica no corpo (REGRAS, "Cadeia de auditoria em camadas").

**LACUNA aberta:** o gateway não roteia arquivo de contexto por modelo hoje — leitura de código na Máquina (`gateway/run.py` chama `set_session_vars` passando `profile` e não `cwd`; o Hermes auto-injeta só o nome fixo `.hermes.md`). Os silos são gerados mas nenhum modelo os recebe; todos seguem pegando o `.hermes.md` comum. NÃO tratar como seleção funcional até haver teste do gateway em execução. A seleção pertence nominalmente ao Bloco 3.1 pelo `roteiro-fase2.md` mas foi adiada por decisão do Humano; quando retomada, cadeia A/B/C própria + emenda ao roteiro — não é o Bloco 3.2 (que é eco pós-carregar).

**Verificação do executor antes do commit** (não substitui S7): SHA-256 dos dois `.diff` conferidos; `git apply --check` limpo (sozinhos e juntos); `bash -n` limpo; hook roda e gera comum + 4 silos; isolamento testado com 3 MOD sintéticos numa cópia de MEMÓRIAS.md restaurada e provada intacta por SHA-256 — nonce de cada silo só no silo certo, órfão em nenhum, AVISO 1×; efeito no `.hermes.md` versionado: +2 linhas de boilerplate, −1 linha de índice `(51) MOD claude`, nada mais; P-8 falha sem o par `APROVADO-` e passa com ele; `git log --all -- '.hermes-*.md'` vazio.

**Par consumido:** `propostas/aplicadas/silos-por-modelo-3.1-v2.diff` + `APROVADO-silos-por-modelo-3.1-v2`. Rascunho v1 → `propostas/rejeitadas/silos-por-modelo-3.1.diff`.

**Falta:** S7 — confirmação pós-push por sessão independente do executor (roteiro, S7 ≠ S6).

(304) DIÁRIO — 31/08/2026 · Fase 2 preparada (roteiro + dossiê S1 + item J); HD religado e backup drenado; correção: não há "autorização total", só risco assumido de Fase 1 em (303)

**Contexto:** sessão longa de 31/08 (Claude Sonnet 5, na Máquina) continuou de (303). Sessão em nuvem "Qwen3.7" acompanhou por relay do Humano. Um bloco de relay do Qwen afirmou "autorização total registrada" e mandou o executor "escrever (304) e iniciar a Camada A de 3.1". Esta entrada registra o estado real e corrige o excesso.

**Feito nesta sessão, além de (303):**
- **S1 (Passo 0.4 do roteiro da Fase 2).** Dois rascunhos em `propostas/`: `roteiro-fase2.md` (silos · eco pós-carregar mecanizado · TES-002, cada bloco sob a cadeia de auditoria em camadas) e `dossie-s1-dimensionamento-fase2.md` (dimensionamento read-only). Achados: (a) silo por modelo tem mecanismo **nativo** — rota por cwd de sessão no gateway (`_SESSION_CWD`/`resolve_context_cwd` em `agent/runtime_cwd.py`, chamada por `gateway/session_context.py`), sem patch no vendored; (b) ponto exato do filtro no `gerar-hermes-md.sh` (`janela_memorias()`/`gerar_indice()` — entrar no corpo do bloco `MOD` pra ler `modelo-alvo`); (c) só **um** bloco MOD no canon (`(51) claude`), ~4 alvos previsíveis, efeito de tamanho ≈ nulo — o valor do silo é a fronteira de confidencialidade, não economia de token; (d) `.hermes.md` em 142 KB = **95% do teto** `context_file_max_chars: 150000`; o "18,1% do piso de 64k" de (3626) envelheceu (arquivo ~3× maior hoje), remedir antes de citar; (e) reteste da "lição da Fase 2" (tool-calling com as 12 ferramentas de produção + fabricação deliberada — padrão do qwen em (119)/(138 - chamada real da ferramenta `memory` "completou" sem escrever, narrativa fabricada por cima)/(139)) desenhado pra rodar depois de 3.1.
- **Item J (BLOCO 0.2 do plano).** Os 11 pares de proposta já consumidos foram verificados contra o canon, um a um, e movidos pra `propostas/aplicadas/`: MEMÓRIAS (263)–(270) presentes (1 ocorrência cada); `regra-1-1-endpoint-v1-unix` (endpoint `/api/v1/time/current/unix` + campo `unix_timestamp` vivos em `scripts/consultar_horario.py`, MEMÓRIAS (267)); `regra-1-1-script-universal` (script existe, MEMÓRIAS (272)); `ajuste-regra-1-1-timeapi` (`.md`; direção "sair do web_extractor" realizada por (272)/(273)/(275), `APROVADO-` do Humano existe). `propostas/` raiz agora só tem `README.md` + os 3 docs de planejamento ativos — fila legível.
- **HD `AgataBkup01` religado** (montado 10:01 -03, informado pelo Humano por relay). `auto-backups/` estava em `018b40a` — 5 commits atrás. O commit desta entrada aciona o `post-commit` com o HD montado: bundle `--all` até aqui copiado, marcador `PENDENTE-HD-DESCONECTADO` removido, poda de 5 gerações. Backup de `memoria/missoes` já estava em dia (`03375a5`).

**Correção sobre o relay do Qwen3.7 — Máquina arbitra fatos (Regra 2):** o bloco afirmou "autorização total registrada". **Não é o que o canon diz.** (303) registra o caminho "risco assumido por escrito" **da Fase 1** — as costuras K (PROJETO) e O (REGRAS) — e traz um ledger explícito do que "assumo o risco" **NÃO** abre: Fase 2 (exige a cadeia de auditoria em camadas; pular um salto fere a Regra 2, linha vermelha), TES-001 (empírico, N sessões independentes), Fase 3+ (contenção de escopo). Nenhuma autorização total foi dada nem registrada. É o mesmo padrão de excesso de confiança que (247 - "Qwen3.7" errou uma data com confiança) registrou; anotado, não seguido.

**Próximo passo, e o que ele NÃO é:** Camada A de 3.1 (silos), partindo do dossiê S1. Tem que ser **sessão de hidratação independente** (REGRAS, "Cadeia de auditoria em camadas"; roteiro, tabela de sessões S1–S19). Esta sessão carregou todo o contexto de S1 — está **desqualificada** de ser a Camada A. O executor local não "inicia a Camada A" daqui; o Humano autoriza a sessão separada.

**Verificado:** topo de `MEMÓRIAS.md` = (303) antes desta entrada, HEAD == `origin/main` == `33e1de8`; `mountpoint /run/media/orusoua/AgataBkup01` = montado, 1,9 T; `ls auto-backups/` antes = topo `agata-canonico-…-018b40a.bundle`; `git -C memoria/missoes log -1` = `03375a5`; corpo de (303) relido — registra risco assumido de Fase 1 + ledger, não autorização total.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: leitura de `agent/runtime_cwd.py`/`prompt_builder.py`/`system_prompt.py` no vendored (`~/.hermes/hermes-agent/`, sem backup, hedge devido); verificação dos 11 pares por `grep`/`git apply --reverse --check`/leitura de `APROVADO-`; estado do HD por `mountpoint`/`ls`; corpo de (303) e topo de MEMÓRIAS relidos na Máquina. Relay do Qwen3.7: recebido do Humano, tratado como alegação; a parte "HD conectado" confere, a parte "autorização total" não.


(303) DIÁRIO — 31/08/2026 · Fase 1 sob risco assumido: costuras K+O em PROJETO/REGRAS; ledger do que "assumo o risco" NÃO fecha

**Ordem do Humano, nesta sessão:** "Resolva todas as pendências, eu assumo o risco apenas registre." É o caminho "risco assumido por escrito" da Mudança estrutural (REGRAS), no lugar de segunda opinião de outro modelo. Esta entrada é o registro.

**"Todas as pendências" não cabe numa passada — e parte não cabe em nenhuma passada de Máquina solo.** O que foi feito, e o que não foi com o motivo de cada não.

**Feito agora (Fase 1 — "REGRAS/PROJETO atualizados com risco assumido"):**
- **Item K** — PROJETO.md, "Índice derivado": a linha dizia "Um passo no `post-commit` fica como P-8 futura, se o Humano quiser". Fato velho — (301) já implementou (passo 3 do `.githooks/post-commit`, conferido no código, `git show 018b40a`). Corrigido para descrever o que existe.
- **Item O(a)** — costura de selo de hora: "Carregar e formatos" oferecia `(informado pela interface)` como selo; a Regra 1.1 nunca nomeava esse selo. A Regra 1.1 ganhou o caso explícito (sem script e sem hora do Humano → `(informado pela interface)`); "Carregar e formatos" ganhou "em divergência vale a Regra 1.1".
- **Item O(b)** — "Última entrada" era afirmação seca mesmo sob `sync: não verificado`, encostando na falha de (73 - afirmar sobre o mundo lendo só a própria cópia). Agora: só sob `sync: PASS` afirma o topo do canon; sob não verificado/FALHA é "até onde a minha cópia alcança".
- Só acréscimos, nenhuma regra removida. Congelado em `propostas/costuras-fase1-KO.diff` (`sha256 c0dc6b55`, `git apply --check` limpo), `APROVADO-costuras-fase1-KO` citando a ordem, par movido para `propostas/aplicadas/` neste commit.

**Registrado, não fechado — aceite 2.8 de (302):** a sessão Qwen3.7 (nuvem) desta conversa carregou pelo prompt v2 e chegou sozinha a (302), título byte a byte — conferido na Máquina contra `MEMÓRIAS.md`. É **1 de 2 fornecedores**; 2.8 pede um segundo. Continua aberto.

**NÃO fechado por "assumo o risco" — e o porquê de cada um (é a arquitetura do próprio projeto, não recusa por cautela):**
- **TES-001:** critério empírico — N sessões consecutivas independentes sem alegação falsa, N nem definido. Risco assumido decide mudança estrutural, não faz resultado empírico existir. Definir N + harness é decisão de Regra 8 (três passadas independentes) — trabalho próprio.
- **Fase 2 (silos por modelo · eco pós-carregar mecanizado · TES-002 restaurado):** o plano exige cadeia de auditoria em camadas (A propõe → B audita → C verifica na Máquina → Humano). "Pular um salto é tratar alegação como fato — direto contra a Regra 2", que é linha vermelha ("nem o Humano pede para cruzar"). Risco assumido abre o portão de mudança estrutural; não abre este. Precisa de sessão dedicada com as camadas de verdade.
- **Fase 3+ (GLM membro pleno · discordância sintética · IPFS · curador · DAO):** Contenção de escopo — antecipação de fase futura negada por default, salvo ordem explícita item a item. "Resolva todas" não é ordem específica pra essas.
- **P-6 / backup `memoria/missoes` → HD:** `AgataBkup01` desconectado; bundle de staging local em dia. Conserto = plugar o HD. Hardware, não decisão.
- Itens E/F/G/H/I do plano (hook harness A1 · roteamento por complexidade · destravar P-7 · Proposta 001 resto · skills): Fase 4 / fracamente acoplados, cada um sob gate próprio, vários exigindo Regra 8. Trabalho futuro com portão, não pendência a limpar.

**Portão das três perguntas (costuras K+O):**
1. *Reversível sozinho?* — sim: `git revert` de 1 commit, só acréscimos, nada apagado.
2. *O que mais toca?* — `.hermes.md`/`INDICE_MEMORIAS*` regenerados pelo pre-commit (derivados); `ONDE_ESTAMOS.md`; zero scripts, zero `.githooks`, zero rede.
3. *Saberia se quebrasse?* — sim: `perimetro.sh` no caminho do commit; `.diff` congelado e conferido contra o staged; redação inteira colada na resposta ao Humano pra ele reverter se a palavra estiver errada.

**Verificado:** `git show 018b40a` confirma o passo 3 do post-commit (item K é fato velho); `grep` em REGRAS.md confirmou as duas costuras antes de editar; `sha256sum` do `.diff` (`c0dc6b55`) + `git apply --check` limpo contra a árvore restaurada; carga da Qwen3.7 conferida contra `MEMÓRIAS.md` (título de (302) idêntico) e `git ls-remote` (`origin/main` em `6d7bdfc` antes deste commit).

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: edição por âncora única em PROJETO.md e REGRAS.md (3 pontos, só acréscimo); `git diff` congelado por `sha256sum` e reconferido por `git apply --check` contra a árvore limpa; inventário de pendências cruzado contra PROJETO.md "Plano vigente"/"Estado dos bugs e dos testes" e `propostas/plano-execucao-backlog.md`; aceite 2.8 conferido contra o canon real. Ordem e risco assumido: Humano, nesta sessão.


(302) DIÁRIO — 28/08/2026 · PROMPT_CARREGAMENTO.md: detector de âncora velha era falso positivo — trocado por checagem de defasagem em 3 degraus (v2)

**O defeito:** o texto mandava comparar o campo "Escrito em:" da âncora com a hora medida na abertura e, se divergir por horas, tratar o SHA pinado como suspeito e cair nas URLs `/main/` (CDN). Isso mede silêncio do repositório, não idade da âncora — e troca a fonte imutável pela pior (classe de risco de (248 - fetch servindo conteúdo real mas de 12+ dias atrás, sem carimbo de idade)-(252)).

**Duas ocorrências reais hoje, independentes** (relatadas pela auditoria em nuvem; não verificáveis da Máquina, `lacuna`): uma sessão em nuvem alarmou com a âncora exatamente 1 commit atrás — `018b40a` filho de `810a3b6`, hook funcionando; outra sessão (GPT-5.6 Luna) seguiu o prompt como escrito, buscou só as pinadas e reportou (300) como última entrada quando o canon já estava em (301).

**v1 descartada antes de aplicar:** a primeira correção da auditoria consertava o detector mas mandava buscar as 3 fontes em duplicata — com MEMÓRIAS.md em 961.512 B, ~2 MB por carregamento, custo caindo justo sobre o modelo só-fetch, que é quem mais precisa do prompt. Motivou a v2.

**O que a v2 faz:** pinadas continuam a fonte; `/main/` vira alternativa e último degrau. Checagem de defasagem em 3 degraus, o primeiro que funcionar encerra — (a) feed `commits/main.atom`, não passa por api.github.com (medido pela auditoria hoje: HTTP 200, ~29 KB, HEAD/pai/avô na ordem); (b) `git ls-remote`, ou Range HTTP nos ~3.000 B do topo de MEMÓRIAS.md em `/main/` (medido: HTTP 206, 3.001 B); (c) último recurso, as duas URLs comparadas, declarado como caro. "Escrito em:" proibido como detector, com o caso de hoje anexo no próprio arquivo. api.github.com rebaixado a extra, com `parents[0].sha`.

**Aplicação:** `PROMPT_CARREGAMENTO.md` está FORA da quarentena P-8 (não muda comportamento de código — PROJETO.md, "Quarentena estrutural") — sem par `.diff`/`APROVADO-`. Reconstruído a partir do texto integral da ORIENTAÇÃO v2 (autorizada pelo Humano nesta sessão). `sha256` do resultado = `13372e8677e55374…`, 8.404 B — bate exato com o alvo da orientação. Bloco entre marcadores `ANCORA-SHA` byte-a-byte igual ao HEAD antes do commit (`cmp` limpo); o `pre-commit` reescreve esse bloco no commit — esperado, é conteúdo de máquina. `.diff` congelado no scratch da sessão; `sha256` local difere do alvo da orientação por artefato de geração de diff — o teste que vale é o hash do arquivo-resultado, e esse bateu.

**Item P fechado (NTP da Predator):** `timedatectl status` 28/08 14:38 — `System clock synchronized: yes`, `NTP active`. O `no` das 13:46 era o `systemd-timesyncd` subindo pós-reboot acidental. Sem trabalho estrutural. Lição de Regra 1.1 que fica: medir o selo de hora a cada resposta, nunca herdar do cabeçalho anterior — o executor herdou `(relógio do sistema, não sincronizado)` num cabeçalho sem re-medir, e a escalada de prioridade que a auditoria tinha posto sobre P caiu junto.

**Tarefa 0.5 (pré-requisito de proposta futura, não desta):** `.githooks/pre-commit` lido — confirma que regenera `.hermes.md`/`INDICE_MEMORIAS.md` e faz `git add` deles no mesmo commit que estagia REGRAS/PROJETO/MEMÓRIAS. `.hermes.md` não fica atrás do canon dentro de um commit. Verificado no código, não na descrição de PROJETO.md.

**Pendente, obrigatório antes de fechar:** teste de aceite 2.8 — colar o prompt v2 numa sessão de nuvem limpa (dois fornecedores, se der) e confirmar que ela chega sozinha à entrada do topo do canon. Não executável da Máquina; fica pro Humano ou uma sessão de nuvem.

**Portão das três perguntas:** reversível sozinho (`git revert` de 2 hunks, nada apagado); alcance = só `PROMPT_CARREGAMENTO.md` (fora de P-8) + esta entrada + ONDE_ESTAMOS.md + os derivados que o `pre-commit` regenera; zero REGRAS/PROJETO/scripts, zero rede no ato do commit; silêncio = barulhento (`perimetro.sh` no caminho, `.diff` congelado e lido, hash do resultado conferido contra alvo).

**Verificado:** `sha256sum` + `wc -c` do resultado contra os dois alvos da orientação (bateram: `13372e8677e55374`, 8.404 B); `cmp` do bloco `ANCORA-SHA` contra `git show HEAD:PROMPT_CARREGAMENTO.md` (igual); `git diff` lido inteiro antes do commit — 2 hunks, só a seção "COMO BUSCAR" e a nota da âncora, nada mais tocado; `perimetro.sh` RESULTADO GERAL OK (9 OK · 0 SKIP · 1 PARCIAL · 0 FALHA — o PARCIAL é o P-4 lado-sudo de sempre, sem sudo).

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: reconstrução do arquivo a partir do texto integral da ORIENTAÇÃO v2, conferida por `sha256` (13372e8677e55374) e byte-count (8.404) contra os alvos dados; `.githooks/pre-commit` lido para a tarefa 0.5; as medições de `commits/main.atom` e do Range HTTP são da auditoria em nuvem, não refeitas aqui (`lacuna` de reverificação local); `.diff` gerado por `git diff`, congelado por `sha256sum`, lido antes de aplicar. Achado e desenho: auditoria em nuvem (Claude Opus 5); reconstrução e verificação na Máquina: este executor; autorização: Humano, nesta sessão.


(301) DIÁRIO — 28/08/2026 · Passo 3 no post-commit: regenera o índice derivado a cada commit (fail-soft), sob P-8

**Pendente de (300):** o `indice.md`/`manifesto.md` eram regenerados só à mão antes de um export. Este passo os mantém em dia com o canon a cada commit, igual ao vault Obsidian (passo 2 do mesmo hook).

**O que entrou** (`.githooks/post-commit`, P-8, `.diff` congelado `4a388736…`): bloco 3, espelho do bloco 2 — se `scripts/gerar_indice_derivado.py` existe, roda; sucesso imprime a linha "regenerado", falha imprime AVISO em stderr e **o commit segue** (fail-soft). **Não sobe pro Drive** — export continua sendo `preparar_export_indice.py` + `subir_esfera_projeto.py` + chamada real, sempre manual.

**Autorização:** Humano, "pode fazer o pendente". `propostas/APROVADO-hook-indice-derivado` criado a pedido; par em `propostas/aplicadas/`.

**Portão das três perguntas:** reversível sozinho (`git revert` de 13 linhas, nada apagado); alcance = só `.githooks/post-commit` (P-8) + o `indice.md`/`manifesto.md` gerado no repo `missoes` (gitignorado do principal, mesma classe do vault) + esta entrada + ONDE_ESTAMOS, zero canon-texto, zero rede; silêncio = barulhento (linha no output em sucesso, AVISO em stderr na falha, `perimetro.sh` no caminho).

**Verificado:** `bash -n` antes e depois; `.diff` por `git diff`, congelado por `sha256sum`, aplicado em `mktemp -d` + `bash -n`; `git checkout` pra reverter antes de congelar; o próprio commit desta entrada exercita o hook — a linha "índice derivado regenerado" aparece no output do commit.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: leitura do `post-commit` inteiro (bloco 2 = molde); edição por âncora única verificada (`assert count == 1`); `bash -n` nas duas pontas; `.diff` congelado por `sha256sum` antes do APROVADO e após o move; aplicação testada em árvore temporária.


(300) DIÁRIO — 28/08/2026 · FASE 6: `scripts/preparar_export_indice.py` — versão de exportação sanitizada do índice, para o cano do Drive, sob P-8 (fecha o plano de 6 fases)

**O problema, achado na FASE 6:** `subir_esfera_projeto.py` aborta no `indice.md` — ele carrega o PROJETO.md verbatim, que NOMEIA `ZHIPU_API_KEY` (nota `[FECHADO]`, sem valor), e o padrão 56 do scanner casa o nome pelado. Falso positivo: nome de variável de ambiente não é segredo.

**Decisão do Humano:** não afrouxar o scanner (exigiria 2ª opinião), não copiar à mão (não automatiza), não mascarar no gerador (quebraria a reconstrução byte a byte de (298)). Um script de exportação dedicado.

**`preparar_export_indice.py`** (P-8, `.diff` congelado `4c3db973…`): lê `indice.md`, troca nome de variável de ambiente pelado (`(ZHIPU|GOOGLE|…)_API_KEY`, `aws_secret_access_key`) por `[variável de ambiente]`, escreve `indice_export.md` com um comentário de marca. O `indice.md` original não é tocado. Importa `PADROES_SEGREDO` do próprio `subir_esfera_projeto.py` (fonte única) e **só grava se o resultado passar nos 16 padrões** — senão aborta sem escrever. O scanner não muda.

**PROJETO.md:** subseção nova "### Índice derivado do canon público e export pro Drive" — os 3 scripts (`gerar_indice_derivado`, `consultar_indice`, `preparar_export_indice`), o fluxo `gerar → preparar → subir_esfera no indice_export.md`, "no NotebookLM usa-se o `indice_export.md` do Drive". Hook `post-commit` fica anotado como P-8 futura opcional.

**Autorização:** Humano, "APROVADO — propostas/APROVADO-preparar-export-indice". Par em `propostas/aplicadas/`.

**Teste end-to-end real (upload de verdade, FASE 6 autoriza):** `gerar_indice_derivado.py` → `indice.md` 249 títulos; `preparar_export_indice.py` → mascara 2 ocorrências de `ZHIPU_API_KEY` (linha 101 + a subseção nova), `indice_export.md` passa nos 16 padrões de `PADROES_SEGREDO` (0 match); `subir_esfera_projeto.py memoria/missoes/agata-sistema/derivado/indice_export.md` → **SUBIU**, `drive_id=1XIwk6o2Ihvmjf9PcOZpjIkpsyJ39UMKr` (136 618 B), registrado em `memoria/missoes/agata-sistema/upload.log`. `manifesto.md` já estava lá (`drive_id=1nAmXBTVGuIoSt9O3DiN_Gx591O-XUiaO`, mantido por decisão do Humano).

**Fecha o plano de 6 fases** (auditor Qwen3.7): FASE 0 higiene, 1 infra read-only, 2 vault (rodado pelo executor), 3 decisão + Regra 8, 4.2 fronteira real, 5 gerador, 5.5 consulta nuvem, 6 export. Entradas (295)–(300).

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: `import PADROES_SEGREDO` de `subir_esfera_projeto.py` confirmado (módulo só define, guard `__main__`); contagem de match antes/depois no `indice_export.md` (padrões de segredo: 1→0, depois 2→0 com a subseção nova); `.diff` congelado por `sha256sum` antes e depois do APROVADO/move; `perimetro.sh` P-8 verde após aplicar; os 3 scripts rodados em sequência com upload real ao Drive, `drive_id` conferido no `upload.log`.


(299) DIÁRIO — 28/08/2026 · FASE 5.5: `scripts/consultar_indice.py` — extrator de trechos do índice para dar a modelo em nuvem, sob P-8

**O que é:** o executor local roda, pega a saída em texto plano, cola no contexto de trabalho de um modelo em nuvem. Não chama LLM, não acessa rede, não escreve nada. Recebe palavras-chave, devolve: as seções de REGRAS/PROJETO cujo heading ou corpo casam, e as linhas de título de MEMÓRIAS que casam. Corpo de entrada de MEMÓRIAS não sai — o número aponta pra abrir o arquivo.

**Fonte:** `memoria/missoes/agata-sistema/derivado/indice.md` (o mesmo artefato que sobe pro Drive — o que o executor consulta é o que o modelo em nuvem tem). Ausente → instrui a rodar `gerar_indice_derivado.py`; `--rebuild` regenera antes. `--all` exige todas as palavras (default é qualquer uma). Tetos: 15 seções, 50 títulos, com "+N não mostrados".

**Isto é o caminho do Q2 modificado:** modelo em nuvem não lê `memoria/missoes/` nem o índice direto — recebe um recorte que o executor local separou. A esfera pessoal continua fora por construção (o índice nunca a contém — (298)).

**Regra 8 não se aplica:** é grep estruturado sobre texto, saída determinística, sem juízo (precedente (289)/(293)).

**Autorização:** Humano, "implemente" + instrução 6. `.diff` congelado `569cc747…`, P-8; `propostas/APROVADO-consulta-indice-nuvem` a pedido; par em `propostas/aplicadas/`.

**Verificado:** `py_compile`; 4 testes ao vivo — `P-10` (3 títulos), `--all vault determinístico` (1 título), índice ausente (mensagem certa, sai 1), `--rebuild segredo` (regenerou + achou a seção Segurança de REGRAS); `.diff` de arquivo novo aplicado em `mktemp -d` + `py_compile`; `perimetro.sh` após aplicar.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: script escrito e rodado nos 4 casos acima; parse de seção por `^## ` dentro dos blocos PARTE 1/PARTE 2 do `indice.md`; `.diff` congelado por `sha256sum` antes do APROVADO e após o move; aplicação testada em árvore temporária.


(298) DIÁRIO — 28/08/2026 · FASE 5: `scripts/gerar_indice_derivado.py` — índice do canon público para consulta externa (Opção A), sob P-8

**O que é:** um gerador que lê SÓ `REGRAS.md` + `PROJETO.md` + `MEMÓRIAS.md` (do topo do repo) e escreve `memoria/missoes/agata-sistema/derivado/{indice.md, manifesto.md}`. Nunca lê de `memoria/missoes/`. É a "Opção A" que o Humano escolheu: REGRAS íntegro + PROJETO íntegro + as 247 linhas de título das entradas de MEMÓRIAS (nº + tipo + data + título), mais recente primeiro, sem corpo de entrada. `indice.md` mede 134 KB.

**Por que não é o vault (290) de novo:** entrada diferente (3 arquivos públicos, não o sistema inteiro), forma diferente (1 arquivo plano, não 398 notas religadas), fim diferente (processamento externo no NotebookLM, não navegação local da Seth), lugar diferente (repo `missoes`, não o principal). Overlap só no verbo "derivar do canon".

**Q2 modificado do Humano, atendido por construção:** o conjunto de entrada é fixo (`FONTES = REGRAS/PROJETO/MEMÓRIAS`); não há caminho de código que abra outra coisa. A "validação que o índice não contém referência à esfera pessoal" (instrução 5) foi implementada como algo mais forte que um `grep` proibido — que daria falso positivo, porque o próprio PROJETO.md documenta os caminhos `memoria/missoes/segunda-camada/` e `agata-sistema/` como política pública. Em vez disso: reconstrução byte a byte antes de gravar (`indice == HEADER + REGRAS + SEP + PROJETO + SEP + títulos`), e cada linha de título conferida como verbatim de MEMÓRIAS.md. Se sobrar um byte fora do boilerplate fixo + canon, aborta sem escrever.

**Determinístico:** carimbo de commit (`git rev-parse HEAD` / `git log -1 --format=%cI`), não relógio; override por `AGATA_CANON_SHA`/`AGATA_CANON_DATA`. 2ª geração byte-idêntica verificada. `manifesto.md` traz sha256 das 3 fontes + do `indice.md`.

**Sem hook.** Regenera sob demanda, antes de um export. `memoria/missoes/` já é gitignorado do repo principal (`.gitignore:22`) — a saída não polui o canon.

**Autorização:** Humano, "implemente" + escolha "A". `.diff` congelado `f41765ab…`, P-8; `propostas/APROVADO-indice-derivado` criado a pedido; par em `propostas/aplicadas/`.

**Verificado:** `py_compile`; rodado contra o canon real (`indice.md` 134 KB, 247 títulos, `manifesto.md` com hashes que batem com `sha256sum` das 3 fontes); determinismo por `sha256sum` de 2 gerações; `.diff` de arquivo novo por `git diff` após `git add -N`, aplicado em árvore temporária + `py_compile` do aplicado; `perimetro.sh` após aplicar.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: script escrito e rodado contra REGRAS/PROJETO/MEMÓRIAS reais; conferência dos hashes do `manifesto.md` contra `sha256sum`; teste de determinismo (2 gerações, hash igual); o parse de título reusa a regex `CAB_ENTRADA` de `gerar_obsidian.py`; `.diff` congelado por `sha256sum` antes do APROVADO e após o move; aplicação testada em `mktemp -d` como o P-8 faz.


(297) DIÁRIO — 28/08/2026 · FASE 4.2: PROJETO.md documenta a fronteira real do `subir_esfera_projeto.py` (a allowlist do plano do Qwen não existe)

**O que o plano do Qwen (FASE 4.2) queria:** documentar um fluxo de upload com `allowlist.txt` — "Humano adiciona caminho na allowlist; script valida contra ela". **Esse arquivo e essa checagem não existem no código** (defeito 2 da auditoria). Instrução do Humano nesta sessão: documentar a fronteira REAL, não criar allowlist.

**O que entrou** (`.diff` congelado `96d5963d…`, P-8, subseção nova em "## Memória em duas camadas"): a ordem exata de 8 checagens de `scripts/subir_esfera_projeto.py`, lida direto do código — caminho (`realpath` dentro de `agata-sistema/`), esfera pessoal, canon (conjunto de 4 basenames), é-arquivo, extensão (7 permitidas), tamanho (10 MiB / não-vazio), UTF-8, varredura de segredo (~16 padrões). Mais o que roda depois (refresh → pasta → upload multipart → `upload.log`) e a frase "não é allowlist; se um dia precisar, é P-8 separada".

**Autorização:** Humano, "Audite e se estiver tudo certo implemente" + instrução 8. `propostas/APROVADO-fluxo-upload-fronteira` criado a pedido; par em `propostas/aplicadas/`.

**Verificado:** `scripts/subir_esfera_projeto.py` lido linha a linha (checagens 121–152); `grep -i allowlist` no script = 0; `git apply --check` limpo contra HEAD `c927e17`; `perimetro.sh` P-8 OK após aplicar.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: leitura completa de `subir_esfera_projeto.py`; conferência das 8 abortagens e da ordem contra o texto da subseção; `.diff` por `git diff` de PROJETO.md, `sha256sum` antes do APROVADO e após o move, `git checkout` pra reverter antes de congelar; `perimetro.sh` rodado após aplicar.


(296) DIÁRIO — 28/08/2026 · FASE 3 decidida: Proposta 001 avança como camada de consulta sob demanda, do canon público, com ponte pro Drive

**Contexto:** o plano de 6 fases (auditor Qwen3.7, nuvem) chegou com 8 defeitos — auditados e reconhecidos nesta sessão. A FASE 3 pede a decisão das 3 questões abertas da Proposta 001, sem implementar.

**Regra 8 cumprida:** 3 passadas independentes de `qwen3.5-9b-64k` (invocações separadas de `ollama run`, contexto novo a cada uma, sem histórico compartilhado), sobre o texto das 3 questões com a recomendação embutida removida (a original violava a Regra 3 — quem propõe não opina). **Convergência total, sem divergência:** Q1=(b), Q2=(b), Q3=(a) nas três. Saídas salvas no scratch da sessão.

**Decisão do Humano:**
- **Q1 — índice na hidratação: (b) consulta sob demanda.** Não injeta no `.hermes.md` (orçamento de 25 000 chars; a camada de leitura do vault já opera assim).
- **Q2 — acesso de modelos em nuvem: MODIFICADO pelo Humano.** Não é "só locais". É: o índice é gerado SOMENTE do canon público (`REGRAS.md`/`PROJETO.md`/`MEMÓRIAS.md`), NUNCA lê de `memoria/missoes/` (nenhuma das duas esferas), e modelos em nuvem acessam por consulta dirigida mediada pelo executor local. A esfera pessoal nunca é exposta — garantido por construção (não está no conjunto de entrada do gerador).
- **Q3 — subir pro Drive da conta do projeto: (a) sim,** via `subir_esfera_projeto.py` (varredura de segredo + fronteira de caminho já no script). Ponte pro NotebookLM.

**Reconciliação de nome:** o Q3 original falava em "índice DA esfera do projeto". Com o Q2 modificado, existe UM índice só, derivado do canon público — é esse que sobe pro Drive. Não há índice separado da esfera do projeto.

**Sem nova superfície de exposição:** o canon já é público no GitHub. Um índice derivado só de `REGRAS/PROJETO/MEMÓRIAS` não revela nada que já não esteja aberto. A validação "índice não contém referência à esfera pessoal" (pedida pelo Humano para a FASE 5) entra como asserção dura de defesa em profundidade, não porque haja caminho de vazamento no desenho.

**O que destrava:** FASE 4.2 (documentar a fronteira real do script — a allowlist do plano do Qwen não existe no código), FASE 5 (`gerar_indice_derivado.py`), FASE 5.5 (`consultar_indice.py`), FASE 6 (export pro Drive + doc do NotebookLM). Cada uma entra como P-8 própria, uma a uma.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: 3 invocações reais de `ollama run qwen3.5-9b-64k:latest` com o mesmo prompt e contexto limpo, saídas salvas e comparadas item a item (Q1/Q2/Q3 idênticos nas três); leitura de `scripts/subir_esfera_projeto.py` confirmando ausência de `allowlist` e a ordem real de checagem (realpath dentro de `agata-sistema/`, fora de `segunda-camada/`, fora do conjunto CANON); `JANELA_ORCAMENTO_CHARS=25000` conferido em `.githooks/gerar-hermes-md.sh`.


(295) DIÁRIO — 28/08/2026 · Gerador do vault ganha a nota do P-10 — gap de (293), aplicado sob P-8

**O que faltava:** (293) criou o controle P-10 em `scripts/perimetro.sh` mas não atualizou `scripts/gerar_obsidian.py` — a lista `controles` do gerador estava fixa em `P-1..P-9`. Efeito: `memoria/obsidian/controles/p-10.md` não existia e qualquer `[[p-10]]` no vault ficava órfão. Contradiz (290), que fixou "todo controle P-N representado no vault".

**Correção** (`.diff` congelado `fc945f255c19…ffa7b0`, P-8): duas linhas — `"P-10"` na lista `controles` + `"P-10": "Vault derivado confere byte a byte com a regeneração do HEAD"` em `CTRL_DESC`. Nenhuma outra mudança. `\bP-1\b` não casa `P-10` (o `0` é caractere de palavra), sem colisão na contagem de menções por entrada.

**Autorização:** Humano, nesta sessão — "APROVADO". `propostas/APROVADO-vault-p10-nota` criado a pedido; par movido para `propostas/aplicadas/` neste commit.

**Verificado:** `git apply --check` limpo contra HEAD `c0c54e6`; `py_compile` OK; a regeneração produz `controles/p-10.md` com "Entradas que mencionam P-10 → [[0293]], [[0294]]"; idempotente (2ª geração byte-idêntica por `find -print0 | sort -z | xargs -0 sha256sum | sha256sum`); `perimetro.sh` — P-10 SKIP no pre-commit (gerador muda neste commit, conferência adiada, `perimetro.sh:504`), P-8 OK, RESULTADO GERAL OK (P-4 PARCIAL de sempre, sem sudo). Vault regenerado do HEAD novo pelo `post-commit`.

**Portão das três perguntas** (com o Humano): reversível sozinho (`git revert` de 2 linhas, nada apagado); alcance = só `scripts/gerar_obsidian.py` (P-8) + `controles/p-10.md` gerado e gitignorado + esta entrada + ONDE_ESTAMOS.md, zero hook/timer/canon-texto; silêncio = barulhento (P-8 trava sem APROVADO, `perimetro.sh` no caminho, teste de idempotência).

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: `_p8_arquivo_aprovado` de `perimetro.sh` lido (varre `propostas/` e `propostas/aplicadas/`, valida por hash de blob, não por path); `p10_vault_derivado` lido (`perimetro.sh:504`, SKIP quando `gerar_obsidian.py` staged); `.diff` gerado por `git diff`, congelado por `sha256sum` antes do APROVADO e reconferido após o move; `git apply --check` + `git apply`; idempotência por hash de árvore em 2 gerações; `perimetro.sh` rodado antes (baseline) e depois.


(294) CORREÇÃO — 28/08/2026 · O carimbo `-arvore-suja` de (293) contava arquivo não-rastreado, e isso fazia o P-10 reprovar sozinho; corrigido para olhar só o que é rastreado

**O que (293) implementou errado:** em `_canon()` de `scripts/gerar_obsidian.py`, a marca `-arvore-suja` vinha de `git status --porcelain`, que lista **também arquivos não rastreados**. O Obsidian larga `Sem título.canvas` / `moc-regras.md` na raiz do repo quando o Humano explora — não rastreados, não mudam o que o gerador lê, mas sujavam o carimbo. Resultado achado no teste de aceite de (293): o `post-commit` gerava o vault com `canon: <sha>-arvore-suja`, o **P-10** regenerava do `git archive HEAD` limpo → `canon: <sha>` → hashes diferentes → **P-10 reprovava todo commit** enquanto houvesse qualquer arquivo solto na raiz. O detector se auto-disparava.

**Corrigido:** `suja = git diff --quiet HEAD` (returncode ≠ 0) — só arquivo **rastreado** diferente de HEAD suja o carimbo. Arquivo não rastreado é ignorado. `.diff` congelado `2e84bb1c0e0b`, P-8. (293) não é editada — Regra 4.

**Testado depois da correção (aceite de (293) refeito):** `bash scripts/perimetro.sh` → P-10 OK no caminho feliz; `rm` de uma nota do vault → P-10 FALHOU com a mensagem certa; `python3 scripts/gerar_obsidian.py` → P-10 OK de novo. `canon:` do `INICIO.md` == HEAD, sem sufixo, com a árvore rastreada limpa.

**Os arquivos soltos na raiz** (`Sem título.canvas` 2 B, `moc-regras.md` 0 B) seguem não rastreados e não commitados — são acidentes do Obsidian do Humano, não do sistema. Recomendado apagar o `moc-regras.md` vazio (confunde com o real em `memoria/obsidian/`).

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: teste de aceite de (293) que expôs a falha (P-10 reprovando com strays na raiz); `git diff --quiet HEAD` confirmado ignorando não rastreados e pegando `scripts/gerar_obsidian.py` modificado (rc=1); `.diff` congelado por `sha256sum` antes do `APROVADO-`; re-teste dos 3 casos de aceite do P-10 depois da correção.


(293) DIÁRIO — 28/08/2026 · Gerador do vault vira determinístico (carimbo de commit no lugar do relógio) + controle P-10 (derivado confere com a fonte) + `verificar_token.py` versionado + fronteira de (115) decidida

**Origem:** auditoria de 28/08, ordem do Humano ("Audite e se estiver tudo certo execute"), risco assumido. Quatro conjuntos num commit só. Não rodei o portão das três perguntas — ajuste pequeno (REGRAS "Mudança estrutural"), e cerimônia contra o princípio de elegância de (288).

**A · `scripts/gerar_obsidian.py` determinístico** (P-8, `.diff` congelado `0f08d521a6a6`). 18 pontos gravavam `yq(AGORA)` — relógio de parede; rodar duas vezes dava bytes diferentes, e verificação por regeneração era impossível. Trocado por proveniência de commit: `CANON` = `git rev-parse HEAD` (sufixo `-arvore-suja` se `git status --porcelain` não vazio), `DATA` = `git log -1 --format=%cI`, ambos com override por `AGATA_CANON_SHA`/`AGATA_CANON_DATA` no ambiente (para o P-10 rodar num extract sem `.git`). Campo `gerado:` removido das ~240 notas — valor idêntico em todas carrega zero informação por nota e custa contexto; só o `INICIO.md` ganha `canon:` e `data:`. Aceite verificado: duas gerações seguidas → hash de árvore idêntico; `grep -c "^canon:" INICIO.md` = 1; nenhum `gerado:` no vault.

**B · Controle P-10 — o derivado confere com a fonte** (P-8, `.diff` congelado `e169e26f54ad`). `scripts/perimetro.sh` ganha `p10_vault_derivado` + a chamada no runner após P-8. O vault (`memoria/obsidian/`) é o único derivado gerado FORA do commit (post-commit, gitignorado) — `.hermes.md` e os índices entram no commit pelo pre-commit e não têm como divergir. P-10: `git archive HEAD | tar -x` num sandbox, roda o gerador ali (com `AGATA_CANON_*` de HEAD), compara byte a byte com o vault no disco. **HEAD dos dois lados** — comparar contra o disco staged reprovaria todo commit que toca canon. Adia (SKIP) quando `gerar_obsidian.py` muda no próprio commit (HEAD tem a versão antiga) — foi o caso deste commit. SKIP também em clone fresco sem vault. Bônus no mesmo `.diff`: o cabeçalho do `.githooks/pre-commit` dizia "6 controles" — são 10 agora; corrigido.

**C · Fronteira de (115)** (`PROJETO_REFERENCIA.md`, fora de P-8 — conferido no `case` de `_p8_eh_comportamento`). **Decisão do Humano: o vault NÃO atravessa a recusa de (115).** (115) recusou busca semântica por embedding; o vault é markdown determinístico com ligações por número de entrada, sem embedding, sem busca semântica — não compete com `grep`. O segundo motivo de (115) ("não tem índice para ficar obsoleto") se aplica e é atendido pelo carimbo `canon:` (item A) mais o P-10 (item B). O gatilho de reabertura de (115) — uma ordem de grandeza; ~118 → 232 medido, 2× — segue não atingido e continua valendo para vector store. Da Proposta 001, a camada de leitura foi construída em (289)-(291); o resto (manifesto de consulta, política de acesso por modelo) segue em stand-by. Corrigido também o texto da linha 68 da tabela: dizia só "Vector store", (115) refutou "vector store / GraphRAG".

**D · `scripts/verificar_token.py` versionado** (P-8, arquivo novo, `.diff` congelado `560f4230eca7`). Estava só no repo `missoes` (gitignorado do público); o timer de 04/09 rodava um script fora de `origin/main` — some sem ninguém notar, e o teste dos 8 dias perde a prova de que o app saiu de Testing. Promovido para `scripts/`. Varredura antes: 0 valor de `client_id`, 0 `GOCSPX-`, 0 refresh token `1//`. Lê a credencial de `~/.config/agata/google-project/` por caminho fixo — funciona de `scripts/` sem mudança. `systemd --user` timer reapontado para `%h/agata/scripts/verificar_token.py`. A cópia no `missoes` é removida em commit separado do repo `missoes`.

**perimetro.sh antes do commit:** P-8 verde (3 pares validados por conteúdo), P-10 SKIP (bootstrap), RESULTADO GERAL OK. ONDE_ESTAMOS.md no mesmo commit.

**Registrado, fora desta tarefa:** `ONDE_ESTAMOS.md` está com ~37 KB; PROJETO.md o define como "uma tela, português simples". Deriva do próprio propósito — conserto barato, outra sessão. Também: o Obsidian criou `moc-regras.md` (vazio) e `Sem título.canvas` na raiz do repo quando o Humano explorava — não commitados, o `moc-regras.md` vazio confunde com o real em `memoria/obsidian/`.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: `grep -c "yq(AGORA)"` antes/depois (18 → 0); teste de determinismo por `find -print0 | sort -z | xargs -0 sha256sum | sha256sum` em duas gerações; `git rev-parse HEAD` conferido contra `canon:` do INICIO.md; `bash -n` em `perimetro.sh` e `pre-commit`; varredura de segredo em `verificar_token.py` (3 padrões, 0 cada); `case` de `_p8_eh_comportamento` lido confirmando `PROJETO_REFERENCIA.md` fora de P-8; `perimetro.sh` rodado (P-8 verde, P-10 SKIP por bootstrap); os 3 `.diff` congelados por `sha256sum` e conferidos contra a worktree antes dos `APROVADO-`.


(292) DIÁRIO — 27/08/2026 · Uso do vault pela Seth passa de disponível a estimulado e cirúrgico: linha em PROJETO.md + item na "Checagem de prontidão" do REGRAS.md

**Pergunta do Humano:** "Seth tem acesso facilitado e estimulado?" — resposta medida: facilitado sim (cwd = repo, skill `note-taking/obsidian` não desabilitada, ponteiro em PROJETO.md desde (291)), estimulado não — nada sugeria *usar* o vault, e usar errado (varrer as centenas de notas a cada tarefa) seria bloat de contexto. Ordem: "Deixe isso perfeito, não cometa erros."

**Autorização:** Humano, verbal, risco assumido. `propostas/seth-vault-estimulo.diff` congelado (sha256 `f3e45d388043`) antes do `APROVADO-`; P-8 validou por conteúdo (toca `PROJETO.md` + `REGRAS.md`, os dois P-8); par em `propostas/aplicadas/`.

**O que entrou:**
- **PROJETO.md, "Memória e hidratação"** — linha "**Quando a Seth usa o vault**": consulta dirigida, nunca varredura. Serve para história além da janela do `.hermes.md`, backlinks de uma entrada/regra/proposta, ou "o que faz o script X" sem abrir o arquivo inteiro — abrir a nota específica em `memoria/obsidian/` (via `INICIO.md` ou `moc-*`). São centenas de notas; não varrer o vault nem o `MEMÓRIAS.md` cru.
- **REGRAS.md, "Checagem de prontidão"** — frase abaixo dos três sins (não é 4º gate, porque depende de ter Máquina): com acesso à Máquina, `memoria/obsidian/INICIO.md` é o índice de consulta pontual. Como REGRAS entra na hidratação, isso agora chega à Seth a cada carregamento.

**Higiene junto:** `.obsidian/graph.json` (config de grafo por-máquina que o Obsidian reescreve) adicionado ao `.gitignore`, ao lado de `.obsidian/workspace*.json`. `.obsidian/{app,appearance,core-plugins}.json` seguem versionados (config portável). Não é P-8.

**Contenção pensada:** o estímulo é *cirúrgico* de propósito — "consulta dirigida, nunca varredura" nos dois textos. Escrever no vault segue desencorajado e auto-corretivo (a regeneração no `post-commit` apaga e reescreve).

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: leitura exata de "Checagem de prontidão" (REGRAS) e da seção "Memória e hidratação" (PROJETO) antes de editar; `git ls-files .obsidian/` para não gitignorar o que é config portável; `.diff` dos dois canônicos por `git diff`, `sha256sum` (`f3e45d388043`), `git apply --check` PASS, restaurado com `git checkout`; `perimetro.sh` P-8 verde após aplicar de verdade.


(291) DIÁRIO — 27/08/2026 · Seth passa a navegar o vault Obsidian a priori: ponteiro em PROJETO.md ("Memória e hidratação"); acesso já disponível (skill não desabilitada, cwd = repo)

**Ordem do Humano:** "e deve ser acessada pela Seth a priori."

**Achado, não presumido:** o acesso da Seth ao vault **já estava disponível**, sem configurar nada:
- `~/.hermes/config.yaml` → `cwd: /home/orusoua/agata` — a Seth já opera na raiz do repo e lê `memoria/obsidian/` com as ferramentas normais de arquivo.
- `config.yaml` → `skills:` tem uma lista `disabled:`, não `enabled:` — skills são ligadas por padrão. `note-taking/obsidian` (existe em `~/.hermes/hermes-agent/skills/note-taking/obsidian/`) **não está em `disabled`** → já disponível para navegação nativa de vault.

**O que faltava — feito nesta entrada:** uma linha em PROJETO.md, "Memória e hidratação", registrando o vault e dizendo que a Seth navega a partir de `memoria/obsidian/INICIO.md`. Como PROJETO.md entra na hidratação (`.hermes.md`), a existência do vault agora chega à Seth a cada carregamento — "a priori" de fato. `propostas/seth-vault-ponteiro.diff` congelado (sha256 `47191522c79b`) sob P-8, risco assumido pelo Humano; par em `propostas/aplicadas/`.

**Escrita no vault pela Seth:** desencorajada e auto-corretiva — a geração no `post-commit` apaga `memoria/obsidian/` e reescreve, então qualquer edição some no commit seguinte. `_LEIA.md` e `INICIO.md` avisam. Escrita de fato segue o fluxo normal: proposta → decisão do Humano → verificação → entrada em MEMÓRIAS → regeneração.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: `ls ~/.hermes/hermes-agent/skills/note-taking/` (obsidian presente); `sed` da seção `skills:` do `config.yaml` (é `disabled:`, e `note-taking`/`obsidian` não está lá); `grep cwd` no `config.yaml` (= repo); `.diff` de PROJETO.md por `git diff`, `sha256sum`, `git checkout`; `perimetro.sh` P-8 após aplicar.


(290) DIÁRIO — 27/08/2026 · Vault Obsidian completo: TODO o sistema (entradas + regras + PROJETO + canônicos + scripts + controles + propostas) representado e religado; regenerado no post-commit

**Ordem do Humano:** "absolutamente tudo que fizemos e que fizermos incluindo o canon, deve ter sua representação canônica lá, sincronizado para melhorar a visualização do Humano … siga as melhores práticas … preveja problemas e solucione os antes de acontecerem … e deve ser acessada pela Seth a priori." Risco assumido por escrito.

**Autorização:** verbal. `propostas/obsidian-completo.diff` congelado (sha256 `5f042dd42104`) antes do `APROVADO-`; P-8 validou por conteúdo (reescreve `scripts/gerar_obsidian.py` + acrescenta passo ao `.githooks/post-commit` — os dois são P-8); par em `propostas/aplicadas/`.

**O que o vault passa a ter** (`memoria/obsidian/`, gitignorado, **385 notas** nesta geração), tudo religado por wikilinks e com frontmatter/tags:
- `entradas/NNNN.md` — 239 entradas de MEMÓRIAS, cada `(n)` / `Regra N` / `P-N` / `nome-de-script` no corpo virou link; seção "Citada por".
- `regras/` — 25 notas, uma por seção de REGRAS.md (Regra 1–8, 1.1, "Mudança estrutural", "Cadeia de auditoria", etc.).
- `projeto/` — seções de PROJETO.md + PROJETO_REFERENCIA.md.
- `canon/` — `ONDE_ESTAMOS.md`, `PROMPT_CARREGAMENTO.md`, `CHAVES.md`, `PROCEDIMENTO_LOGIN.md` inteiros, como espelho de leitura.
- `scripts/` — 33 notas, uma por script/hook, com o que faz (extraído da docstring) + as entradas que o citam.
- `controles/` — P-1 a P-9, cada um com o que checa e as entradas que o mencionam.
- `propostas/` — 41 propostas aplicadas, ligadas à entrada de MEMÓRIAS pelo número no nome quando há.
- `moc-*.md` (7 hubs), `INICIO.md` (porta de entrada), `estado.md` (painel: HEAD/última entrada/contagens + "Última atualização" de ONDE_ESTAMOS), `timeline.md`, `_LEIA.md`.

**Sincronização:** `.githooks/post-commit` ganhou um passo **fail-soft** que roda `gerar_obsidian.py` a cada commit — o vault nunca fica atrás do canon, e uma falha na geração nunca atrapalha o commit (só AVISO em stderr). A pasta é gitignorada: não entra em commit, não polui histórico.

**Para a Seth:** as notas são markdown plano, com a informação legível sem depender de nenhum plugin (os MOCs pré-renderizam as listas). A leitura nativa pela Seth via a skill `note-taking/obsidian` do Hermes (listada em `extras/BACKLOG-skills.md` como prioridade) é o próximo passo — precisa de config no Hermes + escopo **só-leitura** (escrever no vault é perda na regeneração, e escrita de "fato" vai pelo fluxo normal). Não feito nesta entrada.

**Problemas previstos e resolvidos no desenho:**
- **Colisão de nome de nota** → tudo namespaced por pasta + basename globalmente único por construção (`0283`, `regra-8`, `script-perimetro-sh`, `p-8`, `prop-...`).
- **Wikilink órfão** → `religar()` só emite `[[x]]` se a nota `x` foi gerada; o resto fica texto puro. (Os 2 `[[...]]` não resolvidos que sobram — `[[NNNN]]` entre crases e `[[feedback-verify-dont-speculate]]` — são **texto verbatim de entradas antigas**, não links que este script criou; historicidade manda não alterá-los.)
- **Corte errado da varredura** → o limite do bloco migrado é âncora de linha `^## Migrado de DIÁRIO.md`, não substring (a frase aparece entre crases dentro de (96)/(97)).
- **TIPO acentuado** → classe de caractere inclui maiúsculas acentuadas (`DIÁRIO`).
- **Ruído em `cita`** → filtra `(1)/(2)/(3)` de portões (só refs que resolvem para entrada).
- **Edição acidental no vault** → geração apaga `memoria/obsidian/` inteiro e reconstrói; `_LEIA.md` avisa; nada hand-authored sobrevive lá por desenho.
- **Slug ilegível** → `.py`/`.sh` viram `-py`/`-sh`, não somem.
- **Escala** → 385 notas = rebuild instantâneo; O(n) numa passada; incremental previsto para 5k+ mas rebuild total resolve.
- **Idempotência** → rodar 2× produz bytes idênticos (verificado por `md5sum`).
- **Hook lento/quebrado** → passo fail-soft, roda depois do bundle (que é o crítico), `|| AVISO`.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: script reescrito e rodado contra o canon real; `find | wc` = 385 notas; verificador de wikilink órfão rodado sobre todo o vault (só os 2 verbatim, esperados); idempotência por `md5sum` de 2 gerações; `py_compile` + `bash -n .githooks/post-commit`; `.diff` por `git diff` dos 2 arquivos, `sha256sum`, restaurado com `git checkout`; `perimetro.sh` P-8 verde após aplicar.


(289) DIÁRIO — 27/08/2026 · scripts/gerar_obsidian.py: camada de leitura Obsidian derivada de MEMÓRIAS.md (nota atômica por entrada, wikilinks, MOC, timeline). Aplicado sob P-8

**Ordem do Humano:** "criar mecanismo que sincronize toda a base de conhecimento do agata com o obsidian" + "aplique as melhores práticas em 2026 quando o assunto é obsidian, deixe pronto para escalar insanamente" + "vá até o final … eu assumo o risco, deixe registrado".

**Autorização:** Humano, verbal — risco assumido por escrito. `.diff` congelado (sha256 `8534a797578b`) antes do `APROVADO-`; P-8 validou por conteúdo; par em `propostas/aplicadas/`.

**Princípio:** `MEMÓRIAS.md` continua a fonte da verdade (append-only, o que os modelos leem). O Obsidian ganha uma **camada de leitura derivada**, nunca editada à mão, regenerada pelo script. Mesma relação que `.hermes.md` tem com o canon.

**O que `gerar_obsidian.py` produz em `memoria/obsidian/`** (pasta gitignorada — `.gitignore` ganhou `memoria/obsidian/`):
- `entradas/NNNN.md` — **uma nota atômica por entrada**, nome zero-padded (ordena até 9999+). Frontmatter/Properties: `entrada`, `tipo`, `data`, `titulo`, `cita: [...]`, `citada_por: [...]`, `gerado`. Corpo verbatim, com todo `(n)` que resolve para uma entrada virando `[[NNNN]]` → grafo de backlinks. Seção "Citada por" no fim quando aplicável.
- `timeline.md` — todas as entradas, mais recente primeiro, `[[NNNN]]` + tipo + data + título.
- `MOC.md` — mapa: links pro canon, navegação, contagem por tipo com todos os links.
- `_LEIA.md` — "gerado, não edite; corrija pela história; abrir a raiz do repo como vault".

**Determinístico e idempotente:** apaga `entradas/` e reconstrói; rodar 2× só muda o campo `gerado:`. **Escala:** 238 entradas (49–288) = rebuild instantâneo; o desenho já prevê modo incremental (só entradas novas — o único delta num arquivo append-only) para quando passar de ~2000, não implementado porque o rebuild total resolve.

**Parser, achados corrigidos ao construir:** (1) a classe de caracteres do TIPO precisava das maiúsculas acentuadas (`DIÁRIO` tem Á e Í) — sem isso pegava só 42 de 238; (2) o limite do bloco moderno é uma **âncora de linha** `^## Migrado de DIÁRIO.md`, não substring — a mesma frase aparece entre crases dentro do corpo de (96)/(97) e cortava a varredura ali; (3) `cita` filtra refs que não resolvem para entrada gerada — tira o ruído de "(1) reversibilidade / (2) alcance / (3) silêncio" dos portões.

**Regra 8 — não aplicada, por proporção:** geração determinística e verificável (roda e compara), não juízo não-verificável. Registrado como escolha.

**Verificação:** `python3 scripts/gerar_obsidian.py` gera 238 notas, range (0049)–(0288); `(0283)` sai com `cita: [115, 223]` e `citada_por: [284]` (bate com o texto); idempotência conferida (2ª rodada só mexe em `gerado:`); `py_compile` OK; `perimetro.sh` P-8 verde.

**Portão das três perguntas** (com o Humano): reversível sozinho (`git revert` do script; `rm -rf memoria/obsidian/`); alcance = `scripts/gerar_obsidian.py` novo (P-8) + `memoria/obsidian/` gerado e gitignorado + linha no `.gitignore`, zero canon/hook/timer (pode entrar no `post-commit` junto do `.hermes.md` numa proposta P-8 futura); silêncio = barulhento (manual, imprime o que gerou, `py_compile` e `perimetro` no caminho).

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: script escrito e testado contra o `MEMÓRIAS.md` real em 3 iterações (regex de TIPO, âncora do bloco migrado, filtro de `cita`); contagem cruzada `grep -oE "^\([0-9]+\) [TIPO]"` = 196 DIÁRIO + 14 DIARIO + 23 CONSELHO + 4 CORREÇÃO + 1 MOD = 238, casou com as notas geradas; idempotência verificada rodando 2×; `.diff` por `git diff` de arquivo novo, `sha256sum`, `git apply` em árvore temporária + `py_compile`.


(288) DIÁRIO — 27/08/2026 · Ordem permanente do Humano: princípios que guiam o sistema (REGRAS.md) + convenção `extras/` para o não-essencial; docs mortos de jul/2026 arquivados

**Ordem do Humano, textual nesta sessão:** "O que não for essencial vai para a pasta extras, a partir de agora até que orusoua diga o contrário. Segurança, elegância, versatilidade, eficiência, historicidade, checabilidade, clareza, elegância, compatibilidade e tudo que houver de sinônimo para essas palavras deve guiar o sistema a partir de agora até que orusoua peça o contrário." E, ao autorizar a aplicação: "eu assumo o risco, deixe registrado."

**Autorização:** Humano, verbal — "eu assumo o risco". Risco assumido por escrito (REGRAS.md "Mudança estrutural"). `propostas/principios-guia.diff` congelado (sha256 `b7a9cf963d26`) antes do `APROVADO-`; P-8 validou por conteúdo; par em `propostas/aplicadas/`.

**REGRAS.md — seção nova "## Princípios que guiam o sistema"** (logo após "Os 3 papéis"): Segurança · Elegância · Versatilidade · Eficiência · Historicidade · Checabilidade · Clareza · Compatibilidade, mais qualquer sinônimo. Vários já eram regra (Historicidade = Regra 4; Checabilidade = Regra 2; Clareza = estilo) — nomeá-los juntos é a lente, não regra nova ("não infle as REGRAS por reflexo"). O novo é a convenção `extras/`.

**Convenção `extras/`:** essencial = o canon (`REGRAS`/`PROJETO`/`MEMÓRIAS`) + o que o sistema precisa para rodar (`scripts/`, `.githooks/`, `PROMPT_CARREGAMENTO.md`, `ONDE_ESTAMOS.md`, índices, `PROCEDIMENTO_LOGIN.md`, `CHAVES.md`). Não-essencial → `extras/`.

**Movido nesta leva** (tudo `git mv`, histórico preservado; nenhum era referenciado no canon ou em código — `git grep` confirmou):
- `DOSSIE_COEXISTENCIA.md`, `ESTADO_AGATA.md`, `FIO_CANONICO.md` → `extras/arquivo/` — propostas/snapshots de jul/2026 superados pelo canon atual; cada um ganhou um cabeçalho "ARQUIVADO 27/08" apontando o que os substituiu. O `ESTADO_AGATA.md` estava ativamente errado (dizia Gemini principal, "6 regras", etc.).
- `O_Despertar_de_Agata.md` (poema fundador) → `extras/`.
- `skills/BACKLOG.md` → `extras/BACKLOG-skills.md`; pasta `skills/` (só tinha ele) removida.
- `_arquivo_agata_il/` (12 arquivos, código bespoke pré-Hermes de jun/2026) → `extras/arquivo_agata_il/`.

**`CHAVES.md` atualizado:** acrescentada a linha da credencial OAuth da conta do projeto (`~/.config/agata/google-project/`, escopo `drive.file`, consumidores `subir_esfera_projeto.py` + os scripts de consentimento) e o procedimento de refazer o consentimento. Rodapé de data ajustado.

**Portão das três perguntas** (com o Humano): reversível sozinho (`git revert` da seção, `git mv` de volta dos arquivos — nada apagado); alcance = `REGRAS.md` (P-8) + ~17 arquivos movidos não-referenciados + `extras/` criado + `CHAVES.md` + esta entrada + ONDE_ESTAMOS.md, zero código/hook; silêncio = barulhento (P-8 sem APROVADO trava, P-5 trava entrada fora do topo, `git grep` final feito).

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: `grep -rn` em REGRAS/PROJETO/PROJETO_REFERENCIA/PROMPT_CARREGAMENTO/ONDE_ESTAMOS/.githooks/scripts pelos nomes dos 3 docs (zero); `git ls-files` para confirmar o que era rastreado antes de mover; `git mv` para preservar histórico; `.diff` de REGRAS.md gerado por `git diff`, congelado por `sha256sum`, restaurado com `git checkout`; `perimetro.sh` após aplicar.


