# PROJETO.md — Agata (estado corrente)

Este arquivo é o **agora**. É editável e trocável sem mexer nas REGRAS.
Se algo aqui contradisser MEMÓRIAS, MEMÓRIAS ganha: lá está o que aconteceu, aqui está o que vale hoje.
Se algo aqui contradisser a Máquina, a Máquina ganha — e a correção vira entrada nova em MEMÓRIAS.

## O que é
Assistente pessoal do Orusoua, local-first e grátis por padrão.
Agata = **espinha determinística (git + `scripts/` + `perimetro.sh`)** + governança canônica
(REGRAS / PROJETO / MEMÓRIAS) + Conselho Federado de modelos.
**Redesenho concluído no branch `redesign`, mergeado na Fase 8 (2026-09-03, MEMÓRIAS (310)/(311)).**
O executor do loop passou a ser **grafo LangGraph + OmniRoute** (não mais o Hermes). Os modelos
são trabalhadores substituíveis; nenhuma ferramenta É o sistema. Hermes-gateway saiu do loop
(desabilitado); **LibreChat** (lane de conversa, aponta no `seth_gateway` `:20126`) e a voz
(kokoro-tts) seguem como frontends à parte. Acesso multi-dispositivo por LibreChat sobre
Tailscale serve, nunca internet pública. (Open WebUI foi trocado por LibreChat em
2026-09-03, MEMÓRIAS (313).) **Tailscale não está instalado nesta Máquina (achado
05/09/2026, MEMÓRIAS (340), conferido com `which`/`pacman -Qi`/`systemctl status`, os três
negativos) — o texto acima descreve o desenho pretendido, não um mecanismo ativo hoje.
Mesma classe de lacuna que (126) já corrigiu uma vez para a autenticação; desta vez é sobre
existência do programa.** `lacuna`: instalar/configurar fica pro Humano decidir.

Grafia canônica do nome: **Agata** — sem acento, sem "h". A história migrada usa grafias antigas; não se corrige história.

## Máquinas
- **Predator** (master — CachyOS, fish, i7-13650HX, 40GB RAM, RTX 4060 8GB): grafo + OmniRoute, LibreChat, Ollama, git, Obsidian, web. _(Hermes removido por inteiro em 2026-09-03, MEMÓRIAS (312) — linha corrigida 04/09/2026, achado de auditoria: citava Hermes como se ainda estivesse na lista, contradizendo a seção "Riscos conhecidos" mais abaixo neste mesmo arquivo.)_
  **Estabilidade, 12/08/2026 — reclassificado em (124):** 3 eventos sem shutdown limpo no dia, **1 com causa própria confirmada, 2 sem causa determinada.** O 2º tem evidência independente real — GPU presa em resume, `systemd-logind` falhando por watchdog próprio e entrando em loop de 51 reinícios (MEMÓRIAS (99)) — não é ausência de shutdown limpo, é mecanismo capturado em ato; não reclassificado. O 1º (`nowatchdog` mascarou tudo, sem nenhum rastro) e o 3º (só corte abrupto no journal, coincide no tempo com tentativa de GRUB do próprio Humano, MEMÓRIAS (100)) têm, desde (124), uma explicação adicional possível — desligamento forçado por bug de login (ver linha de 13/08 abaixo) — ao lado das já registradas; nenhuma decidida. Mitigações aplicadas — `nowatchdog` removido, `mem_sleep_default=s2idle` (MEMÓRIAS (101)) — continuam justificadas pelo 2º evento sozinho, e reforçadas pela recorrência de 13/08 (suspend/resume seguem não confiáveis neste hardware, mudou a manifestação, não sumiu). `/etc/default/grub.bak.20260812-155431` é a rede de segurança até um boot limpo confirmar efeito; não apagar antes.
  **13/08/2026 — bug de login recorrente, mecanismo achado ao vivo (MEMÓRIAS (124)/(125)):** a máquina trava a senha correta em loop porque **suspende e acorda sozinha repetidamente** (s2idle, `org_kde_powerde` re-suspendendo a cada resume — 91 ciclos numa madrugada). Cada resume falha em recuperar o teclado USB de verdade (`PM: failed to resume async`, desconecta/reconecta), a GPU (`NVRM: Failed to handle ACPI D-Notifier`) e a EEPROM da RAM — sem derrubar o sistema. Efeito na tela: teclas perdidas durante a digitação da senha + `pam_unix: conversation failed` repetido, que `pam_faillock` acumula até travar a conta. Esperar não resolve porque o ciclo de suspend/resume não para sozinho. Boot da madrugada de 13/08 termina abruptamente às 08:08:33, ~3 min depois do travamento de conta (08:05:56) — muito provavelmente o desligamento forçado pelo Humano descrito nesta sessão, não travamento espontâneo novo (não confirmado por Máquina que foi literalmente o botão). **Procedimento completo para a próxima ocorrência:** `PROCEDIMENTO_LOGIN.md`, raiz do repositório. Journal do boot: `journalctl --verify` achou corrupção num segmento arquivado (`user-1000@...journal~`, 52%) — o de (111) já rotacionou e sumiu antes disso, este é achado novo.
- **Orusoua** (réplica Windows 11, leitura/failover) — *planejado*.

## Ambiente Operacional
- **Shell do Humano:** `fish` (Fish Shell) no CachyOS. **Restrição de sintaxe confirmada ao vivo (MEMÓRIAS (149)):** fish rejeita heredoc POSIX (`cat <<'EOF'`) — `fish: Esperava a string, mas achou a redirection`. Para escrita em arquivo via terminal nesse shell: `printf ... | tee`/`sudo tee`, ou delegar a execução para `bash -c '...'` / scripts `.sh`.
- **Shell de execução do Claude Code nesta Máquina:** `zsh`, não `fish` — heredoc funciona normalmente nesse caminho (confirmado, MEMÓRIAS (149)). A restrição acima vale pro shell interativo do Humano e para qualquer executor que herde `fish` como shell de login, não universalmente para todo executor do Agata.

## Cérebro
- **Principal, sob regime de auditoria desde MEMÓRIAS (140): `qwen3.5-9b-64k` local** (Ollama, `custom:qwen-local-ctx-override`) — **não** a tag oficial `qwen3.5:9b`, que reproduz o bug de (121)/#16814. Promovido por decisão do Humano, risco assumido por escrito (mesma cláusula de (102)): cada resposta é auditada pelo Humano; o objetivo é medir o modelo sob a exposição mais alta, não confiar nele. Duas travas cumpridas antes da promoção: ferramenta `memory` testada isolada e confirmada honesta (MEMÓRIAS (139) — a anomalia de (138) era fabricação do modelo, não bug do mecanismo); `num_ctx` confirmado íntegro pelo caminho default, sem override de CLI (`KvSize:65536`, zero truncamento, `prompt_tokens=38.048`). Monitoramento contínuo de VRAM em `~/agata_vram_producao_*.log`, fora do scratchpad de sessão. **Critério de saída do regime, respondido em (141): até o Humano pedir o contrário — evento, não prazo nem contagem.**
- **Fallback: `gemini-2.5-flash`** (Google API, grátis) — papel invertido do histórico: era principal até (140), agora é o alívio quando o Qwen local falha ou não completa. Teto do free tier ~20 requisições/dia — estourar gera 429 (agora do lado do fallback, não do principal). **Circuit breaker ativo** (plugin `gemini_quota_guard`, hook `pre_api_request`): conta requisições reais e avisa a partir da 15ª do dia, sem bloquear nem rerotear (MEMÓRIAS (122)).
- **Roteamento por complexidade — aprovado, NÃO implementado** (MEMÓRIAS (64)): proposta original pressupunha Gemini como principal; com a inversão de (140), o sentido do roteamento precisa ser revisto antes de implementar, não só a implementação em si.
- **Último recurso manual:** `llama3.1:8b` — sem tool-calling, fora da cadeia.
- **Barreira dura:** o Hermes exige contexto ≥64k (constante de produto, não derivada do payload). Skills 12 ativas / 56 off; tools 12 de 18 documentado (13 medidos em ambiente CLI headless, (138) — `lacuna` de paridade exata com o ambiente do gateway); payload ~12,6k tokens.
- **[FECHADO] Histórico de avaliação do `qwen3.5-9b-64k`/`qwen3.5:9b`, que embasou a promoção.** Veredito: aprovado com ressalva — tool-calling correto sob payload real com `num_ctx=65536`, e **2 casos de fabricação deliberada** nos quais admitiu a ausência, errando a autoidentificação num deles. Histórico: MEMÓRIAS (119)/(120), (138), (139); a causa do truncamento tem item próprio abaixo. **Estado corrente, não histórico:** VRAM de pico medida em uso real 89-92% dos 8.188 MiB da placa — produção contínua é mais pesada que teste pontual. **Sem variante text-only na biblioteca do Ollama** (64 tags checadas, todas multimodais) — o encoder de visão é permanente *nessa biblioteca*, confirmado via `/api/show` (27 blocos de atenção de visão). **Fora dela, variantes text-only da família existem**: `alphaXiv/rlm-sft-Qwen3.5-9B-text-v1` tem `model_type: qwen3_5_text` e `Qwen3_5ForCausalLM` **sem `vision_config`**, confirmado por A/B contra o irmão multimodal `-v1` (`Qwen3_5ForConditionalGeneration`, com `vision_config`). A frase anterior afirmava inexistência absoluta; o escopo real é a biblioteca do Ollama. Correção registrada em MEMÓRIAS (162).
- **Padrão de alucinação** documentado é do antecessor `qwen2.5-14b-64k` (inventava entradas e datas) — não do `qwen3.5-9b-64k`, que tem incidentes próprios registrados ((120), (138), (139)) sob rótulo de fabricação, não do mesmo padrão antigo.

## Serviços (boot)
**Pós-redesenho (Fase 8, 2026-09-03):** `agata.target` (`systemd --user`, `enable`d p/ boot)
puxa `omniroute` (`:20128`) · `omniroute-sanitizer` (`:20127`, os callers usam este — sanitiza
segredo antes do egresso) · `openvino-whisper` (`:20130`, STT na iGPU) · `openvino-embeddings`
(`:20134`, embeddings na iGPU) · `obsidian-ro-proxy` (`:27125`, só leitura) · `agata-drain`
(oneshot, drena o WAL do grafo no stop, nunca corta um commit). `llamacpp-agata` (`:20129`, MoE
Qwen3-30B-A3B, `--n-cpu-moe 36`, ~31 tok/s) sobe **sob demanda** (`PartOf` sem `WantedBy`).
`agata-warmup.service` (manual) pré-aquece o modelo local. `agata-jogo` (`~/.local/bin/`, wrapper
para lançar jogo com o Agata fora da RTX 4060 — **não** Feral GameMode, que briga com o
`ananicy-cpp` do CachyOS; usa o `game-performance` da distro).
**Sob demanda** (`seth`/`Parar Seth`): `seth-gateway.service` (`:20126`) · a stack Docker do
**LibreChat** (`librechat` em `network_mode: host` bind `127.0.0.1:3080`, + `librechat-mongodb`
e `librechat-meilisearch` numa bridge privada; `restart: "no"` em tudo; compose em
`~/librechat/`, fonte versionada em `redesign/librechat/`) + `kokoro-tts` (`:8880`).
Ainda de pé no boot: `ollama.service` (produção, `:11434`, intocado) · `agata-consolidacao.timer`.
**Hermes removido por inteiro (2026-09-03, MEMÓRIAS (312)):** `~/.hermes/` apagado (~1,5 GB),
a unit `hermes-gateway.service` não existe mais, `SOUL.md` removido. Segredos movidos para
`~/.config/agata/.env` (o OmniRoute não os lê em runtime — ver `CHAVES.md`).

**`agata-consolidacao.timer` (MEMÓRIAS (220); repontado na Fase 8, MEMÓRIAS (311)).** Roda
23:00 diário. `ExecStart` = `redesign/grafo/flows/consolidacao.py` (flow do grafo — LangGraph,
saída só em `propostas/consolidacao-<data>.md` com entrada `(a numerar)`, nunca toca canon).
Sob `ProtectSystem=strict` + `ProtectHome=read-only` + `ReadWritePaths` = `propostas/` +
`~/.cache/agata/` (checkpoint/WAL) — a contenção é do kernel, não só do prompt. O `hermes
chat` antigo já estava quebrado (sem diretório temporário) quando foi trocado. **`lacuna`
carregada:** o resumo de 1 linha do log já alegou sucesso sem o arquivo existir — confira
`propostas/`, nunca só o log.

**P-9 (MEMÓRIAS (221); lista atualizada na Fase 8, MEMÓRIAS (311)):** `scripts/perimetro.sh`
avisa (nunca falha) se `ollama.service`, `agata-consolidacao.timer`, os 5 membros do
`agata.target` (`omniroute`, `omniroute-sanitizer`, `openvino-whisper`, `openvino-embeddings`,
`obsidian-ro-proxy`) ou os containers do LibreChat (`librechat`, `librechat-mongodb`,
`librechat-meilisearch`) e `kokoro-tts` estiverem `failed`, `disabled`/`masked`, ou
(containers) fora do ar. `hermes-gateway.service` saiu da lista (Fase 8).
Motivo do controle: foi a ausência desse aviso que deixou a consolidação morta sem ninguém notar.

Leftovers pré-Hermes — **não recriar**. `agata.service` e `agatha.service` confirmados ausentes (`systemctl status` → "could not be found"). **`agata-rest.service` ainda existe, mas está `disabled`** (`systemctl status` confirma, MEMÓRIAS (107)). Remoção da unit (com sudo) está na fila, mas não é impeditivo. As duas mitigações de GRUB (`nowatchdog` removido, `mem_sleep_default=s2idle`) foram aplicadas e **confirmadas no kernel via `/proc/cmdline`** (lido diretamente, sem restrição — `mem_sleep_default=s2idle` presente, `nowatchdog` ausente).

## Memória e hidratação
- Canônicos em `~/agata`. O repositório git é também o cofre Obsidian. Memória nativa do Hermes symlinkada em `~/agata/memoria/` — o arquivo real é o canônico; quem é link é o lado do Hermes.
- **Vault Obsidian derivado (MEMÓRIAS (290)):** `memoria/obsidian/` — gerado por `scripts/gerar_obsidian.py` a cada commit (passo `post-commit`, pasta gitignorada). Representa TODO o sistema como notas religadas por wikilinks: uma por entrada de MEMÓRIAS, por regra, por seção de PROJETO/PROJETO_REFERENCIA, por script, por controle P-N, por proposta aplicada, mais MOCs e um painel de estado. **Fonte da verdade continua sendo o canon** — isto é camada de leitura, como o `.hidrata.md`. Modelo com acesso à Máquina (Seth) navega a partir de `memoria/obsidian/INICIO.md`; não editar (a geração apaga e reescreve — correção é entrada nova em MEMÓRIAS).
- **Quando a Seth usa o vault (MEMÓRIAS (292)):** consulta dirigida, nunca varredura. Serve para história além da janela do `.hidrata.md`, para os backlinks de uma entrada/regra/proposta, ou para "o que faz o script X" sem abrir o arquivo inteiro — abrir a nota específica em `memoria/obsidian/`, chegando por `INICIO.md` ou pelos `moc-*`. São centenas de notas: não varrer o vault nem o `MEMÓRIAS.md` cru, o custo é de contexto.
- **MEMÓRIAS.md** é o terceiro canônico: DIÁRIO coletivo + blocos MOD por modelo + registro do Conselho, tudo append-only num arquivo só.
- **Hidratação — pós-redesenho (Fase 8):** o **loop de governança** (grafo LangGraph) hidrata
  pelo nó `hidratar` = `scripts/estado_para_eco.sh` (fatos de Máquina: HEAD, topo de MEMÓRIAS,
  `sync`, `HASH-ESTADO`) + `query_canon` / `redesign/grafo/flows` (`consulta.py`, índice-primeiro,
  zero vector DB) para profundidade sob demanda. O **`.hidrata.md`** continua sendo gerado pelo
  `pre-commit` (`.githooks/gerar-hidratacao.sh`) como **referência** — não é mais a hidratação
  primária do loop. Sessões em nuvem seguem carregando por `PROMPT_CARREGAMENTO.md` + canon.
  Fora do loop não há contador mecânico de turno — conta-se a própria resposta no contexto
  (REGRAS Regra 1). A escolha "consulta vs. injeção" foi decidida na Fase 5 (spike RLM
  **arquivado** — injeção venceu em fidelidade/custo; números no `redesign/LOG.md`).
- **`ONDE_ESTAMOS.md` (16/08/2026) é um quarto arquivo na raiz, só para o Humano — nunca entra na hidratação.** Uma tela, português simples, sem jargão de canon. Mantido atualizado no mesmo commit de qualquer entrada de MEMÓRIAS que mude o estado (REGRAS, Regra 4). MEMÓRIAS (196)/(197).
- **[FECHADO] Teto de entrega do carregador do `hermes-agent`.** Veredito: `agent/prompt_builder.py` truncava `.hermes.md` antes de injetar — piso dinâmico de 20.000 chars vindo de `model.context_length: 65536`, e **o PROJETO.md inteiro nunca chegava a nenhum modelo**. Corrigido com `context_file_max_chars: 100000` explícito no `config.yaml`, escopo estreito, verificado rodando o carregador real e não só lendo a config. `lacuna` que permanece: efeito de `model.context_length` sobre a compressão de histórico de conversa, não medido. Histórico: MEMÓRIAS (103)-(105).
- Silos por modelo (Fase 2, ainda NÃO construídos): o hook `gerar-hidratacao.sh` gera `.hidrata-<modelo>.md` por modelo-alvo (hoje só `seth`, que o `seth_gateway` usa no modo `full`); cada um filtra só o MOD do modelo-alvo. Arquivo único foi rejeitado em auditoria (vaza MOD entre modelos). Silo do Conselho (REGRAS, "O Conselho" item 3): norma.
- **Item C1.1 (05/09/2026, MEMÓRIAS (338)): `scripts/estado_para_eco.sh` reporta `IDADE-HIDRATACAO`** — há quanto tempo `.hidrata.md` foi gerado, distinto de `sync:` (que só mede HEAD local vs. remoto). `redesign/router/seth_gateway.py` já repassa esse campo pro contexto compacto da Seth.
- **Item B1.1 (05/09/2026, MEMÓRIAS (338)): a janela de `.hidrata.md` ganhou um resumo de 1 linha das entradas mais antigas que a janela cheia** — aditivo, mesmo orçamento de `JANELA_ORCAMENTO_CHARS` sem mudar, mais `JANELA_RESUMO_ANTIGAS_CHARS=8000` à parte, reaproveitando `INDICE_MEMORIAS.md`. Não muda o algoritmo de acúmulo por orçamento abaixo, só estende o alcance depois dele.
- **A janela de injeção é por ENTRADA INTEIRA, não por linha crua.** `.githooks/gerar-hidratacao.sh` acumula entradas completas até um orçamento de `JANELA_ORCAMENTO_CHARS=25000` caracteres — desde MEMÓRIAS (271), de cima pra baixo a partir do marcador `ENTRADAS-NOVAS` (mais recente primeiro); nas entradas migradas de antes de (271), o mecanismo original (de trás pra frente, a partir do fim físico) continua documentado como fallback para HEADs sem o marcador. Nunca corta uma entrada no meio — se a primeira sozinha já estourar o orçamento, entra inteira mesmo assim. Medido ao vivo em 20/08/2026 (antes da migração): o `.hidrata.md` (então `.hermes.md`) publicado carregava 9 entradas completas, (205)-(213), nenhuma cortada, 16.713 palavras no arquivo todo. A frase anterior a essa medição ("janela de 30 linhas") vinha de um desenho anterior ao hook atual e nunca foi atualizada quando o mecanismo mudou — corrigida em (215), sem apagar a entrada de MEMÓRIAS que registra o achado.
- **Âncora de integridade (1)-(62):** 128.671 B, sha256 `b26ac113f7a6f72c875391c2d07d94f6f6c827cc9d14c180ecc324b14ab4e03a`. Verificação por marcador de conteúdo (início/fim do trecho) + comprimento — nunca por offset fixo ou número de linha, que se deslocam a cada edição de preâmbulo (MEMÓRIAS (96) achou isso; (97) corrigiu: o offset registrado em (96) é foto, não âncora durável). Script: `scripts/achar_ancora_1_62.py`.
- **[FECHADO por (313)]** RAG só no Open WebUI e só em sessões Gemini. Sem objeto: o Open WebUI
  saiu (03/09/2026) e o LibreChat foi implantado **sem** RAG por embedding de propósito
  (`rag_api`/`pgvector` não subidos) — respeita MEMÓRIAS (115)/(293). Janela grande hoje vem
  do modelo (`auto/*` do OmniRoute), não de recorte por vetor.
- **`memoria/missoes/` (renomeado de `memoria/projetos/` em 12/08/2026) é um quarto pilar, LOCAL por desenho.** Um arquivo editável por missão, mais `INDICE.md`. Repositório git próprio, sem remote — gitignorado do repo principal (`.gitignore` cobre `*.bundle` em qualquer lugar da árvore, não só a pasta — endurecido depois de um bundle quase vazar um nível acima, MEMÓRIAS (97)/(98)), nunca público, nunca em hidratação. Pesquisado sob demanda por qualquer modelo com acesso à Máquina, não injetado automaticamente. **Desde 04/09/2026 (MEMÓRIAS (325)), achável pelo grafo do Obsidian** — `memoria/obsidian/moc-missoes.md`, linkado do `INICIO.md`, lista os arquivos de `memoria/missoes/` (exceto `segunda-camada/`, ver abaixo) como wikilink pro arquivo real. Isso muda achabilidade, não a fronteira: continua fora de `.hidrata.md` (não é empurrado a nenhum modelo), continua gitignorado do repo principal, continua nunca público. `segunda-camada/` (esfera pessoal, "Memória em duas camadas" abaixo) fica de fora do MOC de propósito — "modelos em nuvem não veem" é mais estrito que "sob demanda". Propósito próximo do bg-review desligado, mecanismo distinto em três pontos nomeados — ver `INDICE.md` local e MEMÓRIAS (91)-(95). Ordem do Humano.
- **Repositório oficial:** `https://github.com/agataseth98-cmd/agata-seth` (branch `main`) — sincronizar contra ele no início de toda sessão, não só na primeira. Achado recorrente com sessões autônomas na nuvem (sem Humano revisando cada resposta): a sincronização falha silenciosamente com frequência — não presuma feita, verifique.
- **Fonte canônica (URLs) e atualização:** `https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/main/{REGRAS,PROJETO,MEMÓRIAS}.md`. Primeira sessão: o Humano envia os 3. Depois: o modelo busca das URLs, seguindo a ordem de verificação de REGRAS.md. `atualizar <REGRAS|PROJETO|MEMÓRIAS|TUDO>` = git pull + regenerar hidratação. Nunca sobrescreve história; conflito → para e avisa.
  **Caveat medido, MEMÓRIAS (156):** `raw.githubusercontent.com` é servido por CDN (Fastly) e pode ficar em cache por alguns minutos após um push, mesmo com cache-busting na query string — confirmado ao vivo, ~1-2 min de defasagem. `git ls-remote`/`git ls-tree` (na Máquina) não sofrem disso, por isso são o método 1 em "Verificação de canônico", superior ao raw. Uma sessão só-HTTP (sem Máquina) verificando *logo depois* de um push pode pegar conteúdo stale sem ter como saber — não é falha de sincronização do modelo, é da fonte.
  **Âncora de SHA no prompt de carregamento, 20/08/2026 (item 4 do documento do Humano, sugestão do Marcos, MEMÓRIAS (217); geração automática item 2, 20/08/2026, MEMÓRIAS (226)).** O prompt de carregamento usado por sessões só-HTTP (sem Máquina) carrega o SHA de commit esperado no momento em que foi escrito. Uma sessão só-HTTP pode consultar `https://api.github.com/repos/agataseth98-cmd/agata-seth/commits/main` (endpoint da API do GitHub, não o CDN do raw) e comparar o campo `sha` contra o valor impresso no prompt — divergência é sinal de que o prompt está desatualizado ou o raw pode estar em cache, não prova sozinha de nenhum dos dois. Testado ao vivo em 20/08/2026: o endpoint respondeu com o SHA correto do HEAD no momento da checagem. **Não substitui `git ls-remote`/`git ls-tree` onde a Máquina existe** — esses continuam método 1, superior. **Limite achado em 25/08/2026 (MEMÓRIAS (250)-(254)):** `api.github.com` bloqueia por bot-detection em pelo menos uma interface de nuvem real testada — essa sessão não teve como rodar esta comparação. Não é universal.
  **URLs raw pinadas em SHA, 25/08/2026 (MEMÓRIAS (253), achado de "Ágata Opus").** Preferir estas sobre as URLs em `/main/` acima: `https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/<SHA>/{REGRAS,PROJETO,MEMÓRIAS}.md`, geradas automaticamente dentro do próprio bloco ANCORA-SHA (mesmo SHA, mesma defasagem: normalmente 1 commit, mais se o hook de âncora falhar). Conteúdo endereçado por hash é imutável — elimina o risco de cache velho sem precisar do endpoint da API, que pode estar bloqueado (ver limite acima). As URLs em `/main/` continuam como alternativa/fallback.
  **Mecanismo, desde 20/08/2026:** o prompt agora é canônico dentro do repo (`PROMPT_CARREGAMENTO.md`, movido da Área de trabalho — ver "Quarentena estrutural" pra classificação SEM quarentena). `.githooks/pre-commit` reescreve as duas linhas entre os marcadores `ANCORA-SHA` a cada commit, via `scripts/atualizar_ancora_prompt.py` — nunca toca o resto do arquivo, aborta sem escrever se os marcadores sumirem. **Limite conhecido, não escondido:** um commit não pode embutir o próprio SHA (auto-referência) — o valor escrito é sempre o do HEAD ANTERIOR ao commit, então fica normalmente 1 commit atrasado. O passo que grava a âncora no `pre-commit` é fail-soft: se falhar, imprime um AVISO em stderr e o commit segue mesmo assim, e a defasagem pode ficar maior que 1 commit sem que quem lê o prompt seja avisado (achado MEMÓRIAS (277)). Mitigação sem custo, já no arquivo: o campo `Escrito em:` do bloco, comparável com a hora medida na abertura da sessão. Decisão do Humano: aceitar esse atraso em troca de 100% automático, em vez de exigir um commit manual extra pra fechar o loop.

### Medição de horário para modelos em nuvem (adicionado 26/08/2026)

**Problema:** Modelos em nuvem (GPT, Claude, Gemini via API) não têm acesso a `date` do shell local e não podem medir horário de forma confiável usando `web_extractor` (cacheia respostas — confirmado com timeapi.io retornando timestamp de ~6h atrás, MEMÓRIAS (273)).

**Solução canônica:** Usar `code_interpreter` para executar Python puro via `urllib.request`, que faz requisição HTTP direta sem cache intermediário. Script disponível em `scripts/consultar_horario.py`:
- Consulta timeapi.io com cache-busting (`?cachebust=<timestamp>`) pra forçar nova requisição
- Converte timestamp Unix para horário de Brasília (-03)
- **Sem fallback automático de segunda API.** worldtimeapi.org foi cotado originalmente, mas o serviço foi descontinuado pelo mantenedor e, mesmo no ar, devolvia o timestamp numa chave diferente da esperada — o fallback nunca teria funcionado. Corrigido em MEMÓRIAS (275). Sem um segundo provedor testado e vivo, o fallback real é o item 3 da hierarquia abaixo, não uma segunda API automática.

**Hierarquia de fontes de horário (Regra 1.1 em REGRAS.md):**
1. Modelos com shell local → `date` (fonte primária)
2. Modelos sem shell (nuvem) → `code_interpreter` + `scripts/consultar_horario.py`
3. Fallback → horário informado pelo Humano (apenas se script falhar)

**Proibido:** `web_extractor` para medição de horário, herdar hora de resposta anterior, inventar horário.

**Selo de auditoria:** `(API externa via script)` quando usar code_interpreter + script.

## Interface
**Pós-redesenho + remoção do Hermes (2026-09-03, MEMÓRIAS (310)–(312)):**
- **Executor / loop:** grafo + OmniRoute, via o `agata` CLI (`~/.local/bin/agata` →
  `redesign/grafo/cli.py`: `up`/`down`/`status`/`verify`/`commit-entry`/`run`/`resume`/`logs`).
- **`seth_gateway`** (`redesign/router/seth_gateway.py`, `:20126`, `seth-gateway.service`
  **sob demanda**) — reidrata a **Seth** antes do sanitizador. Modo `compacto` (default):
  cabeçalho curto (identidade + Regra 1 + ponteiro p/ `query_canon`) + estado atual de
  `estado_para_eco.sh`. Modo `full` (o `.hidrata-seth.md` inteiro) só sob configuração —
  ~45k tokens estouram o `maxWaitMs` do OmniRoute. **Qualquer frontend que aponte para
  `:20126` fala com a Seth hidratada.**
- **LibreChat** (`127.0.0.1:3080`, stack Docker sob demanda) — frente de **conversa** informal,
  aponta para `:20126`. Endpoint único "Seth" (`ENDPOINTS=custom`), `fetch` dos modelos `auto/*`
  do OmniRoute. **Memória desligada** (`memory.disabled`) e **sem RAG** de propósito — a
  hidratação vem do `seth_gateway`. Conta única (`ALLOW_REGISTRATION=false`). Meilisearch para
  busca de conversa. Substituiu o Open WebUI em 2026-09-03 (MEMÓRIAS (313); config em
  `redesign/librechat/`).
- **Goose** (`~/.local/bin/goose` v1.48.0, `:20126`) — frentE de **agente / código**
  (`goose session`); também é o shell de fallback operacional. Codex CLI terciário.
- **Voz:** kokoro-tts (`:8880`, `--restart=no`) + Whisper na iGPU. Remoto = HTTPS via Tailscale.
- **Atalhos** (`~/Área de trabalho/`, ícone `~/Imagens/Ágatha Seth.png`): **Seth** (chat —
  sobe tudo + abre o navegador), **Seth (agente)** (Goose no terminal), **Parar Seth**
  (para os frentes; a espinha `agata.target` segue de pé). Skills/integrações futuras
  (Home Assistant, ponte WhatsApp) entram **sob demanda**, cada uma como servidor MCP (ver
  desenho da arquitetura da Seth). **Ponte Discord e controle de navegador — implementados
  05/09/2026, MEMÓRIAS (339):** `redesign/mcp/discord/` (poll, não push; egresso sanitizado
  por `PADROES_SEGREDO`) e `redesign/mcp/navegador/` (Playwright direto contra Brave real —
  não `browser-use`, cuja API de classes sumiu na versão avaliada; perfil isolado; escrita
  travada por allowlist mecânica de domínio, `~/.config/agata/navegador-dominios-permitidos.txt`).
  Os dois sobem/descem sob demanda via `discord-mcp.service`/`navegador-mcp.service`
  (`redesign/systemd/`, sem `[Install]`), amarrados ao ciclo de `~/.local/bin/seth`/`seth-parar`.
  Transporte HTTP (não stdio, diferente do `canon-mcp.mjs`) — os dois rodam no host (Brave
  real, API do Discord), o LibreChat alcança via `127.0.0.1` porque o container usa
  `network_mode: host`. `librechat.yaml` ganhou `mcpSettings.allowedDomains: ["127.0.0.1"]`
  (sem isso o próprio LibreChat bloqueia servidor MCP remoto, guarda contra SSRF).

## Segurança
Sandbox sempre. Segredos só em `~/.config/agata/.env`, fora do repo (era `~/.hermes/.env` —
movido na remoção do Hermes, 2026-09-03, MEMÓRIAS (312); junto de `restic.pass`,
`obsidian.token`, `google-project/` no mesmo diretório). O OmniRoute não lê esse arquivo em
runtime — as chaves ficam cifradas no `~/.omniroute/storage.sqlite`; `~/.config/agata/.env`
é a fonte para adicionar/rotacionar provedor (ver `redesign/router/PROVEDORES.md`).
**O api_server executa terminal: nunca expor sem contenção.** Auditado em MEMÓRIAS (126) — a frase antiga desta seção descrevia Tailscale com dupla autenticação, mecanismo que **não existe nesta máquina** (achado em (125)). O mecanismo real, confirmado por `ss -tlnp`: `api_server` compartilha a porta do `hermes-gateway` (8642), e o bind é **`127.0.0.1`** — contenção de kernel, não de firewall. LibreChat (`network_mode: host`, bind `127.0.0.1:3080`), Mongo/Meili (publicados só em `127.0.0.1`) e Kokoro TTS (8880, publicado pelo Docker) também só em loopback. Mesmo efeito de contenção do texto antigo, mecanismo diferente do descrito — corrigido aqui pra não sustentar um controle de segurança em algo que não roda.
**Ollama (`11434`):** restrito a `127.0.0.1` desde MEMÓRIAS (126)/(127), confirmado no bind real (`ss -tlnp`) e no ambiente do processo. `override.conf` completo com as 5 variáveis (`OLLAMA_NUM_GPU=999`, `OLLAMA_KV_CACHE_TYPE=q4_0`, `CUDA_VISIBLE_DEVICES=0`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_HOST=127.0.0.1:11434`) — o efeito colateral de (127) (`OLLAMA_NUM_GPU`/`CUDA_VISIBLE_DEVICES`/`OLLAMA_FLASH_ATTENTION` apagados por um `tee` destrutivo) foi corrigido, confirmado em MEMÓRIAS (130). Efeito sobre estabilidade de VRAM não medido nesta correção — restaurar a variável não é o mesmo que testar carga.
Ao rotacionar chave, atualize **todos** os consumidores no mesmo passo. Rotação parcial dá 401 silencioso.

## Conselho Remoto — Fase 1 (transporte, não decisão)
Aprovado em princípio, escopo pequeno de propósito: UM modelo, UMA tarefa — enviar um pedido de parecer já escrito pelo Humano, recolher a resposta. Fase 1 testa o TRANSPORTE, não a qualidade do parecer (ordem do Humano, MEMÓRIAS (206)).

**Modelo escolhido: GLM-4.7-Flash (Zhipu), grátis.** Grátis é a escolha certa aqui — remove a hesitação de custo, que é justamente o que a fase mede. `model` na API: `glm-4.7-flash`. Endpoint compatível OpenAI: `https://api.z.ai/api/paas/v4/chat/completions`. Escolhido contra os 5 provedores de MEMÓRIAS (182), nesta ordem de critério: já participou do Conselho de verdade (auditor ativo desde (44)) · custo baixo o bastante pra não pensar (free tier real, não só barato) · sem histórico de 429 (o GPT foi descartado desse papel por cota — MEMÓRIAS linha 917 — GLM nunca teve o mesmo problema).

**Mecanismo, `scripts/conselho_remoto.py` (MEMÓRIAS (207)):** recebe um arquivo de texto com o pedido (escrito pelo Humano) → envia UMA vez a UM modelo → guarda a resposta CRUA em `memoria/missoes/conselho-remoto/` (data, modelo, tokens, custo) → confere as 4 partes do parecer (Origem/Posição/Fundamentação/Emenda); se faltar, reporta "fora do formato" e para — REGRAS ("Segunda opinião") manda devolver o pedido uma vez com o formato junto, decisão de reenviar é do Humano, não do script. Nunca escreve em MEMÓRIAS/PROJETO/REGRAS, nunca interpreta ou julga a resposta, nunca encadeia chamadas, nunca decide nada.

**Segurança, o ponto que esta fase introduz:** hoje um Humano lê todo texto entre modelos antes dele influenciar outro modelo; automatizar o transporte remove esse filtro. **A resposta de um modelo remoto é DADO NÃO CONFIÁVEL** — nunca executada, nunca interpretada como instrução, guardada em arquivo, nunca injetada automaticamente no contexto de outro modelo nem na hidratação (`.hidrata*.md`). O Humano lê antes de qualquer coisa acontecer com ela.

**Condição 1 (MEMÓRIAS (206)), tecnicamente forçada no script (MEMÓRIAS (207)):** só material já no repositório PÚBLICO pode ir no texto do pedido — nunca `memoria/missoes/`. `conselho_remoto.py` recusa enviar se o texto do pedido mencionar `memoria/missoes` (barra ou contrabarra), antes de qualquer chamada de rede. Reforçado porque **os termos de treino da Zhipu sobre dado enviado pela camada grátis não foram confirmados em fonte primária** (`z.ai/privacy-policy`, `z.ai/legal-agreement`, `docs.z.ai/api-reference/introduction` — 404 ou sem a cláusula) — tratado como se pudesse treinar sobre o enviado, até prova em contrário.

**[FECHADO] Condição 2, ordem obrigatória da chave, cumprida 17/08/2026 (MEMÓRIAS (208)).** Formato real confirmado: 32 caracteres hexadecimais + ponto + 16 alfanuméricos mistos, 49 caracteres — um dos 4 formatos plausíveis já testados em (207), reconfirmado com a forma EXATA antes de guardar. Chave falsa dessa forma testada de novo em repositório descartável: P-1 alarmou. Chave real está em `~/.config/agata/.env` (`ZHIPU_API_KEY=`; era `~/.hermes/.env` até 03/09), permissão `600`. **Risco residual de (208) fechado (MEMÓRIAS (209)):** a primeira chave passou em texto puro pela conversa; o Humano rotacionou no painel da Zhipu e editou `~/.hermes/.env` direto, sem colar o valor novo aqui — a chave exposta está invalidada, a atual nunca passou pela conversa. Verificado sem ler o valor: mesma forma, 49 caracteres, permissão `600`.

**Custo:** `max_tokens` no pedido limita a saída (teto atual: 8.000 tokens); pedido acima de 60.000 caracteres é recusado antes do envio. Preço US$0/token nesta camada — fórmula de custo em dólar já no script, pronta pra quando não for mais grátis.

**Como saber se valeu (B.7, MEMÓRIAS (206)):** na primeira utilização real, contar quantas idas e vindas de copiar-colar o Humano deixou de fazer. Zero ou uma = fase 1 não se pagou — resultado legítimo, registra e para, não expande pra dois modelos.

**Estado, atualizado 20/08/2026 (MEMÓRIAS (225)):** quarta invocação real, sem 429 — parecer completo recebido, formato OK, custo US$0. GLM aprovou o desenho do checador de citação (P-7) com ressalva: falta um jeito de destravar manualmente um caso marcado errado por engano. O backoff de (216) ficou pronto (2 falhas 429 seguidas travam 15 min) mas nunca precisou entrar em ação nesta chamada. Histórico completo, incluindo as três tentativas anteriores que bateram em 429: MEMÓRIAS (206)-(208), (211)-(213), (216), (225).

**Backoff de 429, 20/08/2026 (item 3 do documento do Humano, sugestão do Marcos, MEMÓRIAS (216)).** Antes: uma retentativa (duas invocações manuais em sequência) e desiste, sem memória entre invocações. Agora: `conselho_remoto.py` guarda em `memoria/missoes/conselho-remoto/.backoff-estado.json` (camada privada, sem remote) quantas falhas HTTP 429 aconteceram SEGUIDAS entre invocações; na segunda falha seguida, a próxima chamada é recusada por 15 minutos, com a espera registrada em `memoria/missoes/conselho-remoto/backoff.log`. Uma chamada sem 429 (sucesso ou erro de outro tipo) zera o contador. Testado isolado: 1 falha não trava, 2 falhas seguidas travam por ~900s, sucesso depois reseta — os três casos rodados de verdade contra o módulo importado, sem chamada de rede real.

**Pós-redesenho (Fase 1 do `redesign`, P1-04; mergeado na Fase 8, MEMÓRIAS (310)/(311)):**
`conselho_remoto.py` **não lê mais chave nenhuma** e não faz backoff próprio — a chamada externa
sai por **UMA POST em `http://127.0.0.1:20127/v1/chat/completions`** (o proxy de sanitização
P1-02) → OmniRoute, combo `conselho` (`zai/glm-4.7-flash → gemini-2.5-flash`, `strategy=priority`,
**sem tier local** — verificado em `storage.sqlite`). Backoff/breaker/cota agora são do OmniRoute.
**Ganho:** o pedido do Conselho passa pela sanitização de segredo. **Invariantes preservados:**
só material público sai (`checar_conteudo_privado` byte a byte igual), teto de tamanho, UMA
chamada, aborta se os externos esgotarem (não cai pro local), formato do parecer, resposta crua.
O `.json` de saída passou a gravar `provider` (derivado do modelo) — rastreabilidade, já que a
combo é config. Cadeia de auditoria A→B→C cumprida (B=Qwen; C=Máquina); `redesign/propostas/
conselho-remoto-omniroute.diff` + `APROVADO-`.

## Sudo e interação humana
Quando uma operação na Máquina exigir `sudo`, o executor (Claude Code ou similar) pausa o processo em curso e pede ao Humano para rodar o comando (ex: via prefixo `!` no Claude Code). Não armazenar senha, não simular autenticação, não tentar contornar. Confirmado na prática em MEMÓRIAS (110): sudo sem sessão interativa já foi um bloqueio real, não hipotético.

**[FECHADO] Regra sudo NOPASSWD órfã (`/etc/sudoers.d/facer`) removida 16/08/2026** — apontava pra caminho inexistente sob `/home/orusoua/`, gravável pela mesma conta do executor, contornando este controle sem quebrá-lo. Decisão do Humano: opção 1 (remover); opção 4 registrada como caminho seguro se o teclado RGB Acer voltar — script em `/usr/local/bin`, dono root, só então a regra. MEMÓRIAS (192).

**[FECHADO] Verificação root-side de sudoers, orientada a evento (opção D, decisão do Humano 16/08/2026).** `scripts/perimetro.sh` P-2 não chama mais `sudo -n -l` diretamente (era SKIP estrutural sempre — o executor nunca tem sudo não-interativo, é o controle funcionando, não uma falha a contornar). Passa a **ler** `/var/lib/agata/p2-status.json`, escrito por um mecanismo separado que roda como root: `/usr/local/lib/agata/checar-sudoers-root.sh` (autocontido, dono root, não-gravável por `orusoua` — depender de código gravável pelo usuário recriaria a classe fechada em (192)), disparado por `/etc/pacman.d/hooks/agata-sudoers.hook` sempre que uma operação de pacote tocar `etc/sudoers.d/*` — o vetor mais provável de como `facer` apareceu. Três estados: status ausente = SKIP (mecanismo nunca rodou, não bloqueia); veredito negativo = FALHOU; veredito positivo = OK **com a data da última verificação — idade não é alarme**, só ausência ou veredito negativo. Opções alternativas descartadas: A (timer systemd permanente) por desproporção — vigiar uma condição que só muda quando um humano roda sudo não justifica privilégio permanente; B (NOPASSWD estreito pro próprio `sudo`) por reabrir a classe de (192) e ser primitivo de escalação desaconselhado pela documentação do `sudo`. **Instalado e confirmado real 16/08/2026** (não só testado com mock): P-2 transicionou de `SKIP` pra `OK` com timestamp real contra o mecanismo instalado. Disparo do hook pelo pacman em si segue pendente (nenhuma operação de pacote tocou `sudoers.d` ainda). MEMÓRIAS (196).

**Cobertura que o hook não tem, coberta por runbook, não por maquinário:** edição manual via `visudo` não dispara pacman. **Depois de qualquer `visudo`, rodar `sudo /usr/local/lib/agata/checar-sudoers-root.sh`** pra atualizar o status manualmente. Material de origem dos dois artefatos (script + hook), versionado: `scripts/checar-sudoers-root.sh`, `scripts/agata-sudoers.hook`. MEMÓRIAS (194).

## Quarentena estrutural (P-8)
**O buraco, 20/08/2026 (item 6 do documento do Humano, proposta do Marcos, MEMÓRIAS (218)).** Até aqui, o executor escreve em canon, comita e empurra — o Humano fica sabendo depois. Nenhuma das sete checagens do perímetro cobria isso, e é a mesma classe do incidente registrado em MEMÓRIAS (214) (`sincronizar-estado.sh` publicando sozinho apesar do próprio cabeçalho dizer que não).

**Escopo, proporcional de propósito.** QUARENTENA OBRIGATÓRIA — o que MUDA COMPORTAMENTO: `REGRAS.md`, `PROJETO.md`, `scripts/*`, `.githooks/*`, `config/*` (`config/` incluído em 20/08/2026, MEMÓRIAS (222) — um prompt que dirige um modelo autônomo contra o canon muda comportamento tanto quanto um script). SEM quarentena — o que só REGISTRA o que já aconteceu: entradas de `MEMÓRIAS.md`, `ONDE_ESTAMOS.md`, `INDICE_MEMORIAS.md`, `.hidrata.md` (gerado), `PROMPT_CARREGAMENTO.md` (movido pra dentro do repo em 20/08/2026, item 2 do documento do Humano). Motivo da linha: registro errado se corrige com entrada nova — é pra isso que append-only existe. Comportamento errado, não. `PROMPT_CARREGAMENTO.md` fica fora da quarentena apesar de "dirigir" um modelo, ao contrário de um prompt que dirige um processo DESATENDIDO (systemd timer sem Humano revisando antes de agir — o `config/agata-consolidacao.prompt.txt` era desse tipo, removido em (312) quando a consolidação virou flow do grafo): o prompt de carregamento é sempre lido por um Humano que cola o texto numa sessão nova e revisa cada resposta — mais perto de `ONDE_ESTAMOS.md` (registro pro Humano) do que de um script autônomo.

**Mecanismo — ver `propostas/README.md` para o texto completo.** Diretório `propostas/` na raiz, versionado. A mudança proposta vira `propostas/<nome>.diff` (cabeçalhos `--- a/` / `+++ b/` de verdade). O Humano aprova criando `propostas/APROVADO-<nome>`. `scripts/perimetro.sh`, checagem **P-8**: FALHA o commit se algum arquivo staged do grupo "muda comportamento" não estiver coberto por um par `.diff`/`APROVADO-` presente em `propostas/` — procura tanto em `propostas/` (pendente) quanto em `propostas/aplicadas/` (já consumido), porque a aprovação consumida NO MESMO commit que aplica a mudança já não está mais no lugar pendente quando o hook roda; sem checar as duas, todo commit que consome sua própria aprovação reprovaria a aprovação que o autoriza — achado testando antes de comitar de verdade, corrigido antes de ligar o controle. Aprovação consumida: ao entrar no canon, quem aplica move o par para `propostas/aplicadas/` no mesmo commit.

**Testado, positivo e negativo, taxa de falso positivo relatada antes de habilitar (MEMÓRIAS (218)):** 6 casos rodados contra um clone descartável antes do commit real — arquivo de comportamento staged sem aprovação (falha), com aprovação cobrindo o caminho (passa), arquivo de registro (MEMÓRIAS/ONDE_ESTAMOS) sem aprovação nenhuma (passa, nunca deveria travar), mistura de um aprovado + um não aprovado no mesmo commit (falha citando só o não aprovado), aprovação já movida pra `aplicadas/` no mesmo commit que ela autoriza (passa), e o caso negativo básico repetido depois da correção (falha). Zero falsos positivos e zero falsos negativos nos 6 casos.

**Bootstrap, registrado sem suavizar.** Esta própria mudança toca `scripts/perimetro.sh` e `PROJETO.md` — ordem do Humano, ela é a primeira candidata a passar pela própria quarentena, depois de P-8 existir, aplicada antes de ligar P-8 (não havia como pedir aprovação a um mecanismo que ainda não existia). O par `propostas/aplicadas/quarentena-p8.diff` / `propostas/aplicadas/APROVADO-quarentena-p8` deste commit foi criado pelo próprio executor, sob ordem escrita direta e datada do Humano no documento de 20/08/2026 — não é o executor se autoaprovando por conta própria; a aprovação já existia em texto, este é só o registro mecânico dela. **A partir do próximo commit que toque REGRAS/PROJETO/scripts/.githooks, o marcador precisa ser criado pelo Humano — esta exceção não se repete.**

**Risco residual, não suavizado.** O marcador de aprovação é um arquivo que o próprio executor TEM PERMISSÃO técnica de criar. P-8 impede automação agindo sem que ninguém perceba — que foi exatamente o caso de 18/08/2026 — e NÃO impede um modelo que decida contornar deliberadamente. Aceito por decisão do Humano: a ameaça real aqui é desatenção, não malícia. Se um dia for preciso mais, o caminho é assinatura que o executor não possa produzir, com o custo de o Humano digitar uma senha a cada mudança estrutural.

## Doutrina de defesa proporcional
Adotada pelo Humano, 17/08/2026 (MEMÓRIAS (201)). Critério de julgamento pra decidir se e como reagir a um achado de segurança/robustez — não regra universal de REGRAS.md, é ferramenta de decisão situacional do Humano (Regra 3).
- Incidente é o que passa ao lado de um controle que o sistema declarou. O resto é risco de fundo: registra e segue.
- Defesa só entra se for mecânica e no limite. Vigilância humana permanente decai; mecanismo instalado não.
- Risco residual declarado é mais seguro que estado "seguro" não declarado.
- Fecha a classe, não o caso.
- Nenhuma checagem entra em hook antes de passar verde uma vez.

**Formato de "pedido de decisão" (itens numerados, marcador de aguardando, ordem de execução) não é canonizado.** Roda informalmente mais algumas vezes; canoniza-se a versão que sobreviver ao uso.

## Estado dos bugs e dos testes
- **[FASE 8 / redesenho, 2026-09-03 — MEMÓRIAS (310)/(311)]** O redesenho (branch `redesign`,
  Fases 0–8) foi mergeado em `main`. Detalhe granular: `redesign/LOG.md`. **Achados desta fase:**
  - **P-12 (`perimetro.sh`) — bug corrigido:** o caminho `hd_ok=1` fazia
    `restic ... | python3 - <<'PY'` — a redireção do heredoc vence o pipe, `json.load(sys.stdin)`
    nunca via o JSON do restic, e todo recurso da lista-FALHA virava SUSPEITO → **P-12 travava
    todo commit com o HD montado**. A verificação original só exercitou `hd_ok=0`. Fix: o python
    chama `restic snapshots` por `subprocess`. Vermelho/verde demonstrado.
  - **OmniRoute vs. cold-start do Ollama:** a 1ª chamada a um modelo Ollama não carregado (~30s
    de load) estoura o `resilienceSettings.requestQueue.maxWaitMs=15000` (15s, default de código)
    → **504**; o modelo carrega mesmo assim e a 2ª chamada responde em ~0,5s. Mitigação:
    `agata-warmup.service` (manual — `systemctl --user start agata-warmup.service` antes de usar
    o modelo local pesado).
  - **`ir_sha256_xmlbin` do manifesto:** a fórmula original não está registrada e não reproduz.
    `redesign/fase7-hd/hash_ir.sh` fixa uma fórmula reproduzível daqui pra frente; o teste de
    restore do restic (`diff -rq` restaurado vs. vivo) é a garantia real.
  - **`agata-consolidacao` (via `hermes chat`) já estava quebrado** (journal 03/09 07:06:
    "ferramentas read_file/terminal falhando — sem diretório temporário no ambiente do Hermes").
    Repontado para `redesign/grafo/flows/consolidacao.py` (grafo, sob o mesmo sandbox).
  - **`igpu/.venv`** tinha ~5 GB de libs CUDA (torch-CUDA + nvidia-* + triton) inúteis para o
    runtime OpenVINO na iGPU Intel — trocado por `torch==2.14.0+cpu` (6,2 GB → 1,8 GB).
- **[04/09/2026 — MEMÓRIAS (323)-(332)] Manutenção do vault Obsidian + auditorias, mesma sessão.** Achados reais, cada um verificado na Máquina antes de reportado, não só lidos:
  - **(323)** `INICIO.md`/`timeline.md` vazios na raiz eram artefato órfão do Obsidian (mesmo mecanismo já registrado em (319)) — removidos; `.gitignore` ganhou `/estado.md`, `/timeline.md`, `/_LEIA.md` (só `/INICIO.md`/`/moc-*.md` estavam cobertos). Links markdown pros READMEs (o Obsidian não conta como aresta do grafo) viraram `[[wikilink]]` real.
  - **(324)** `obsidian-skills` oficial (kepano/Obsidian) instalado + `memoria/obsidian/memorias.base` (Obsidian Bases nativo) criado. Busca semântica **segue recusada** — o gatilho de reabertura da própria (115) (corpus crescer uma ordem de grandeza) não foi atingido: hoje 2,3×, não 10×.
  - **(325)** Causa real dos READMEs órfãos no grafo: `memoria/missoes/` é um repositório git separado, invisível pro gerador do vault — corrigido (`moc-missoes.md` novo, 18 arquivos linkados; `segunda-camada/` deliberadamente fora, esfera mais estrita). Venv órfão de 176MB apagado; 2 arquivos pessoais pré-redesenho (não rastreados por nenhum git) apagados sob ordem direta do Humano.
  - **(326)** Bugfix pré-emptivo: o `moc-missoes.md` de (325) quebraria o controle **P-10** em todo commit futuro (a sandbox do P-10 não enxerga `memoria/missoes/`, repo separado) — corrigido antes do dano acontecer, `perimetro.sh` repassa a lista de arquivos por variável de ambiente.
  - **(327)** `scripts/busca_semantica.py` implementado sob autorização direta do Humano ("assumo o risco por escrito") — ferramenta **secundária**, sob demanda, nunca injetada em hidratação. Medida ao vivo nos dois lados: boa pra tema concreto, fraca pra pergunta abstrata sobre o próprio sistema (rank real 116º/150º de 276 pros casos que deveriam ser o topo).
  - **(328)** Auditoria de parecer externo achou bug real e reproduzível em `redesign/router/sanitizar.py`: payload muito profundo (>12 níveis) ou muito largo (>20.000 nós) escapava da varredura de segredo sem bloquear (falha aberta, contradizendo o próprio contrato do módulo). Corrigido e testado antes/depois: os dois ataques agora bloqueiam, payload normal continua passando limpo.
  - **(329)** Anel de "pontos soltos" do grafo era quase todo Nota Diária + arquivo gerado por desenho, não bug. Achado de segurança pequeno corrigido: a Nota Diária do Obsidian (`AAAA-MM-DD.md`) não estava no `.gitignore` — um `git add -A` descuidado teria publicado rascunho pessoal no repositório público.
  - **(330)** Achado real por trás do anel: os 9 canônicos da raiz (`REGRAS.md` … `_LEIA.md`) nunca tiveram `[[wikilink]]` de verdade em lugar nenhum do vault, só texto em `código` — corrigido em `gerar_obsidian.py`, sob par `.diff`/`APROVADO-`.
  - **(331)/(332)** Auditoria da autoavaliação da Seth sobre o próprio sistema de memória: substância majoritariamente confirmada; um ponto estava desatualizado (citava `.hermes.md`, removido em (312) — o mecanismo real hoje é `.hidrata.md`/`estado_para_eco.sh`); a própria resposta da Seth reprovou no linter de Regra 1 do projeto. **(332)** corrige **(331)**: a proposta `guarda-utf8-hidratacao` que (331) descreveu como pendente já estava aprovada e aplicada em (318), antes da auditoria começar — nenhuma ação pendente para o Humano nesse ponto.
- **[04/09-05/09/2026 — MEMÓRIAS (333)-(340)] Sincronização, autoauditoria da Seth e correção de dois bugs reais, sessão seguinte.**
  - **(333)** Drift real achado nos 3 arquivos derivados de hidratação (voltaram a um estado velho, causa raiz não confirmada — hipótese: Obsidian "Recuperação de arquivo"/"Sync", `lacuna` até o Humano checar dentro do app) + reconciliação de (323)-(332) em PROJETO.md.
  - **(334)/(335)** Auditoria de uma proposta de 7 itens da Seth com parecer de Qwen: 2 itens partiam de premissa falsa (pasta inexistente, mecanismo mal diagnosticado), 2 já estavam implementados. **(335)** corrige **(334)**: datar a proposta pelo HEAD que ela cita prova só o conteúdo descrito, não o momento da redação — os 10 veredictos técnicos não mudaram.
  - **(336)** Síntese de capacidades da Seth: acerta quando repete número já medido, erra quando afirma existência/estado sem checar (mesmo padrão em 2 incidentes de formato de cabeçalho). Orientação escrita entregue a ela.
  - **(337)** A Seth reproduziu o padrão descrito em (336) na resposta seguinte (citação de entrada inexistente, termos sem referente), depois se autocorrigiu com precisão real (linha exata, contagem exata) — confirmado item a item, não aceito por confiança.
  - **(338)** Dos 4 pendentes de (334), 2 já estavam feitos (B3.1, A3-médio — erro meu não ter checado antes de listar); implementados e testados os 2 reais: **C1.1**/**B1.1**, ver "Memória e hidratação" acima.
  - **(340)** Causa raiz real do `HTTPError` da consolidação noturna corrigida (`max_tokens` baixo pro reasoning do Gemini + teto de 15s do OmniRoute em overload do provedor principal) — (338) tinha concluído "transitório", incompleto. Tailscale conferido: não instalado nesta Máquina, ver "O que é" acima.
- **[FECHADO por (312)] Gemini 429 ("perdi a conexão").** Causa raiz, mecanismo (`_summarize_api_error`/`run_agent.py:2146`) e verificação histórica: MEMÓRIAS (38)-(40), (150). O risco residual citado aqui ("patch vive no `hermes-agent` vendored, sem backup") **não tem mais objeto** — o Hermes foi removido por inteiro em (312), 03/09/2026; não há mais patch vendored pra reverificar.
- **`carregar` no fallback:** nenhum bug confirmado com esse nome na história real. Não carregar adiante como fato. Se reaparecer, o protocolo é: curl na 8642 forçando fallback com `carregar`, capturar o system prompt efetivo no Ollama, e testar em ordem — (a) hidratação não injetada, (b) injetada mas truncada, (c) recebida e ignorada.
- **[FECHADO] `num_ctx` ignorado pelo endpoint compatível com OpenAI do Ollama.** Veredito: **não é bug do `hermes-agent`** — o pedido sempre saiu correto (`HERMES_DUMP_REQUESTS=1` capturou `options.num_ctx: 65536` no `api_kwargs` real), e o endpoint `/v1/chat/completions` do Ollama não suporta `num_ctx` **por desenho**, declarado pelo mantenedor em [`ollama/ollama#16814`](https://github.com/ollama/ollama/issues/16814). Conserto permanente: `PARAMETER num_ctx 65536` embutido em Modelfile próprio, convenção de tag `-64k`. Custo medido: 89,7% de VRAM de pico, 29/33 camadas na GPU. Histórico, inclusive a hipótese do merge raso testada e **refutada**: MEMÓRIAS (121), (122), (133)-(135).
- **TES-001:** não fechado. Três rodadas executadas com resultado adverso documentado (MEMÓRIAS (66), (69), (73)). Exige sessões genuinamente independentes.
  **Hipótese em aberto, não afirmada como causa (MEMÓRIAS (106)):** o teto de truncamento do carregador ((103)/(104)) esteve ativo durante essas três rodadas — os modelos testados podem ter sido avaliados contra REGRAS que nunca chegaram inteiras. Não é reafirmação de causalidade, é motivo pra rerodar TES-001 depois da correção de (104) e comparar.
  **Rodada 4, 25/08/2026 (MEMÓRIAS (243)):** primeira passagem limpa da história do teste — GLM-4.7-Flash via `conselho_remoto.py`, testado com pedido de fidelidade de relato (não parecer sobre proposta), auditado item a item contra o catálogo de falhas conhecidas de REGRAS.md, nenhuma violação achada. **Não fecha o teste sozinho** — REGRAS.md exige N sessões consecutivas sem alegação falsa, uma rodada é o primeiro dado positivo depois de três adversos, não o critério cumprido.
- **[OBSOLETO, achado 05/09/2026 ao tentar implementar] Asserção byte a byte de entrega (harness A1).** Especificação original: hashear o payload no hook `pre_api_request` do `hermes-agent` (`agent/conversation_loop.py:2645-2702`) e comparar contra o selo de `selar.sh`. **O Hermes foi removido por inteiro em (312), 03/09/2026** — `agent/conversation_loop.py` e o hook `pre_api_request` não existem mais em lugar nenhum do sistema; confirmado por `grep` real, zero ocorrência. A especificação inteira dependia de um ponto de gancho que não existe mais na arquitetura atual (grafo + OmniRoute). **Não implementado como especificado — implementá-lo seria pendurar um hook em nada.** Se a preocupação original (o que chega ao provedor bate com o que devia) ainda vale na arquitetura nova, o ponto de fronteira equivalente hoje é `redesign/router/sanitizar.py`, `sanitizar_payload()` — chamado antes de toda saída pelo `:20127`, já testado (`--autoteste`) — mas hashear-e-comparar-contra-selo ali seria um item NOVO, não uma retomada deste, e não foi pedido. Histórico: MEMÓRIAS (103)-(105), (159).
- **TES-002:** **formalmente inativo até existir silo (Fase 2).** Nonce `e1d1a` aposentado (MEMÓRIAS (90)) — não deve ser ecoado por ninguém. Sucessor existe, gerado pela Máquina, guardado fora do canônico, nunca commitado, nunca em hidratação — entregue à mão pelo Humano, uma vez, só ao modelo-alvo, quando ele decidir reabrir o teste. Até lá: nenhum nonce ativo, dizer isso em vez de fingir. Protocolo completo em REGRAS.md, "Continuidade mecânica". Ver MEMÓRIAS (70), (90).
- **[FECHADO] Segunda opinião sobre a regra 3X.** Pendente desde MEMÓRIAS (68) — o executor designado devolveu eco do texto do proponente, não parecer. **Resolvido 25/08/2026:** pedido formal refeito, parecer real recebido e auditado (MEMÓRIAS (246)/(247)), resultado virou REGRAS.md, "Regra 8 — Verificação tripla para decisões não verificáveis".

## Plano vigente (v1.1 — Fases 0–2 são compromisso; 3+ é bússola)
- **Fase 0 — Saneamento (agora):** publicar no remoto as entradas acumuladas · fechar TES-001 · (o patch do 429 do Hermes deixou de existir — Hermes removido em (312)).
- **Fase 1:** blocos Conselho/MOD em MEMÓRIAS · REGRAS/PROJETO atualizados com segunda opinião ou risco assumido · rascunhos históricos → `docs/`.
- **Fase 2:** hook com silos por modelo · eco pós-carregar · TES-002 restaurado com nonce novo.
- **Fase 3:** GLM membro pleno (MOD-002) · válvula de discordância sintética.
- **Fase 4:** MEMÓRIAS por período (hot/warm/cold) · congelar a ~500 linhas com `git tag` + SHA-256 · `selar.sh --check` · Capivara com consentimento por trecho.
- **Fase 5 (sem prazo):** espelho IPFS, curador nomeado, DAO.

**Curador da sucessão:** `lacuna` — enquanto vago, o Humano operador local. Regras de curador nas REGRAS.

## Estado de publicação
O remoto público (`agataseth98-cmd/agata-seth`) está **em dia** — publicado em `main`, confirmado por `git fetch` sem divergência em nenhum sentido (MEMÓRIAS (85)). Se voltar a ficar atrás por acúmulo de sessões sem Máquina, o executor trabalha com os arquivos entregues pelo Humano, não com o GitHub, e declara a origem, como manda a seção de segunda opinião nas REGRAS.
Repositório **é público** por decisão registrada do Humano. Isso é o que queimou o nonce; não é acidente, é consequência conhecida.

## Ferramenta embutida: selar.sh (Fase 4)
Testado nesta sessão de verdade (não só lido): `--check` sem `SELOS.txt` dá exit 1 com mensagem clara; selar um arquivo e checar dá exit 0; adulterar o arquivo depois de selado dá exit 1 com "VIOLADO". Script em `scripts/selar.sh` (sha256 `154dfa55f1bfb3f571a338d2b305d60922cbb245b6a6edb4865f7f06afae4745`), não mais inline aqui — extraído por sessão de reconciliação, ver MEMÓRIAS.

## Memória em duas camadas

**Camada local** — Obsidian sobre o próprio repositório git: offline, privada, é **FATO**.
**Camada nuvem** — NotebookLM e afins: processamento de fonte bruta, é **RELATO/projeção**. Nunca recebe canon e nunca vira cérebro do sistema.

### Esfera pessoal
`memoria/missoes/segunda-camada/` é a esfera local e privada do Humano. Sem remote, não sobe para serviço externo nenhum. Pode conter o que só existe nesta Máquina: hardware, rotina, configuração local, assunto pessoal. Modelos locais consultam sob demanda; modelos em nuvem não veem.

### Esfera do projeto
`memoria/missoes/agata-sistema/` é a esfera de trabalho do sistema, vinculada a uma conta Google Workspace **dedicada ao projeto** — nunca a conta pessoal do Humano. Recebe material do sistema que o Humano autorize, e pode ser consultada por modelos externos sob autorização.

### Fronteira
Só o não-sensível sobe. Conteúdo público sobre o sistema pode ser usado na esfera do projeto; os arquivos canônicos (`REGRAS.md`, `PROJETO.md`, `MEMÓRIAS.md`) não sobem como canon. Dado que só existe nesta Máquina, ou que pertence ao domínio pessoal, fica na esfera pessoal. Segredo, chave e credencial nunca sobem para esfera externa nenhuma.

**Por que "canon nunca sobe" não é contradição com o repositório ser público:** o canon já está no GitHub, aberto. A proibição não é sobre sigilo do texto — é sobre duas outras coisas. Primeira: nenhuma esfera externa adquire autoridade para escrever fato no canon. Segunda: material derivado do canon que ainda não é público não sobe. Sem esse motivo escrito, a regra parece absurda na primeira leitura e é ignorada em silêncio.

### Fronteira mecânica — `subir_esfera_projeto.py`
O único cano de código entre o sistema e o Drive. Um arquivo por invocação, não encadeia, não escreve em canon, não decide nada. Aborta na primeira checagem que falhar, nesta ordem:
1. **Caminho** — `realpath` do alvo tem que estar dentro de `memoria/missoes/agata-sistema/` (o próprio diretório ou abaixo dele). Symlink apontando pra fora é resolvido e barrado.
2. **Esfera pessoal** — se o `realpath` tocar `memoria/missoes/segunda-camada/`, aborta.
3. **Canon** — basename em `{REGRAS.md, PROJETO.md, MEMÓRIAS.md, PROJETO_REFERENCIA.md}` aborta, mesmo que seja cópia.
4. **É arquivo** — não diretório.
5. **Extensão** — só `.md .txt .csv .json .yaml .yml .log`.
6. **Tamanho** — acima de 10 MiB aborta; 0 byte aborta.
7. **UTF-8** — o conteúdo tem que decodificar como UTF-8; binário aborta.
8. **Varredura de segredo** — ~16 padrões (client_secret Google, refresh/access token OAuth, chave PEM, AWS key id, `sk-…`, token GitHub/Slack, connection string com senha, header `Authorization`, par chave/valor genérico, nomes de `*_API_KEY` conhecidos, CPF, CNPJ). Um match aborta — **nada é enviado**.

Só depois das 8: `refresh_token` → access token → cria ou reusa a pasta `agata-sistema` no Drive (escopo `drive.file`) → upload multipart → registra `[carimbo] nome drive_id=… tamanho <- caminho` em `memoria/missoes/agata-sistema/upload.log`.

**Não é allowlist.** Não há arquivo de permissão por caminho — a fronteira é a lista de checagens acima. Se um dia for preciso liberar só certos arquivos de `agata-sistema/`, isso entra como P-8 separada; não existe hoje. Limitação assumida (MEMÓRIAS (286)): formato de segredo que nenhum padrão pega, num arquivo posto em `agata-sistema/` de propósito e com o script rodado à mão — fecham a colocação deliberada, o `upload.log` auditável e a revisão do Humano. A varredura é rede contra acidente, não classificador.

### Índice derivado do canon público e export pro Drive
MEMÓRIAS (296)/(298)/(299)/(300). Camada de consulta sobre o canon, separada do vault Obsidian: gerada só de `REGRAS.md` + `PROJETO.md` + `MEMÓRIAS.md`, nunca de `memoria/missoes/`.
- `scripts/gerar_indice_derivado.py` → `memoria/missoes/agata-sistema/derivado/{indice.md, manifesto.md}`. `indice.md` = REGRAS + PROJETO na íntegra + os títulos das entradas de MEMÓRIAS (sem corpo), mais recente primeiro. Reconstrução byte a byte antes de gravar — se sobrar um byte fora do boilerplate fixo + canon, aborta. `manifesto.md` traz o sha256 das 3 fontes. Determinístico (carimbo de commit).
- `scripts/consultar_indice.py <palavras>` extrai trechos do `indice.md` em texto plano. É como o executor local entrega recorte pra um modelo em nuvem — o modelo não lê o índice nem `memoria/missoes/` direto.
- **Export pro Drive:** o `indice.md` não sobe pelo cano — contém o PROJETO.md verbatim, que nomeia variáveis de ambiente (`ZHIPU_API_KEY` etc.), e a varredura de segredo aborta no nome pelado (falso positivo; o scanner não se afrouxa). `scripts/preparar_export_indice.py` lê o `indice.md` e escreve `indice_export.md` com esses nomes mascarados como `[variável de ambiente]`; o original fica intacto, e o script só grava se o resultado passar em todos os padrões de `PADROES_SEGREDO`. Fluxo: `gerar_indice_derivado.py` → `preparar_export_indice.py` → `subir_esfera_projeto.py memoria/missoes/agata-sistema/derivado/indice_export.md`. No NotebookLM, usa-se o `indice_export.md` baixado do Drive; `manifesto.md` também sobe, como carimbo de proveniência.
- Regeneração automática: `.githooks/post-commit` (passo 3, MEMÓRIAS (301)) refaz `indice.md`/`manifesto.md` a cada commit, fail-soft, sob P-8 — espelho do passo 2 (vault Obsidian). Regeneração sob demanda antes de um export segue disponível (`gerar_indice_derivado.py` direto). O upload pro Drive nunca é automático.

### Mão única refinada
A política deixa de ser "lê, nunca escreve fato de volta" e passa a ser: **nenhum resultado externo tem autoridade automática para escrever no canon.** A esfera do projeto pode produzir síntese, análise ou proposta. Nada disso é escrita de fato. Nenhum resultado retorna automaticamente a `REGRAS.md`, `PROJETO.md` ou `MEMÓRIAS.md`.

Resultado processado só influencia o canon pelo fluxo normal: proposta explícita, decisão do Humano, verificação pela Máquina quando aplicável, registro em MEMÓRIAS, commit. A autorização do Humano permite a incorporação; não dispensa verificação nem registro.

### Postura sobre uso dos dados pelo Google
O Humano autoriza o uso dos dados da esfera do projeto nos serviços Google escolhidos, incluindo eventual uso para melhoria ou treinamento **quando os termos daquele serviço assim previrem**. Isto é postura declarada do Humano, não alegação sobre o que a Google faz — o comportamento do fornecedor não foi medido aqui. Dados da esfera pessoal nunca são usados para isso, porque nunca sobem.

### ACB — reversão parcial de (223)
(223) manteve o ACB inteiro fora de escopo. A partir de 27/08/2026, essa decisão fica limitada aos assuntos pessoais e às partes do ACB desnecessárias ao sistema. Assunto do próprio sistema pode voltar ao escopo mediante autorização explícita do Humano e o mesmo controle de proposta, verificação e registro das demais mudanças.

### Limitação conhecida — Conselho Remoto
A esfera do projeto mora em `memoria/missoes/`, que casa com o regex da Condição 1 em `scripts/conselho_remoto.py`. Por mecanismo, ela não pode ser discutida com o Conselho Remoto hoje. Não é defeito: é a proteção funcionando. Mudar isso exige allowlist explícita ou mover a esfera para fora de `memoria/missoes/`, e qualquer das duas é decisão do Humano.

**Sem auto-captura de fatos.** (Histórico: o `bg-review` do Hermes reescrevia sozinho o MEMORY.md nativo e chegou a apagar identidade e história para caber num teto — ficou desligado, e o Hermes foi removido em (312).) A memória muda só por edição deliberada, por entrada em MEMÓRIAS, ou sob comando explícito — o portão do grafo garante isso agora.


## Referência
Seções de consulta (VM do Marcos, riscos conhecidos, ACB, fronteira de recusas, diagnóstico) movidas para `PROJETO_REFERENCIA.md` — não injetadas na hidratação, disponíveis sob demanda.
