# PROJETO.md — Agata (estado corrente)

Este arquivo é o **agora**. É editável e trocável sem mexer nas REGRAS.
Se algo aqui contradisser MEMÓRIAS, MEMÓRIAS ganha: lá está o que aconteceu, aqui está o que vale hoje.
Se algo aqui contradisser a Máquina, a Máquina ganha — e a correção vira entrada nova em MEMÓRIAS.

## O que é
Assistente pessoal do Orusoua, local-first e grátis por padrão, sobre **Hermes Agent** (Nous Research).
Agata = Hermes + governança canônica (REGRAS / PROJETO / MEMÓRIAS) + Conselho Federado de modelos.
Acesso multi-dispositivo por Open WebUI sobre Tailscale, nunca internet pública.

Grafia canônica do nome: **Agata** — sem acento, sem "h". A história migrada usa grafias antigas; não se corrige história.

## Máquinas
- **Predator** (master — CachyOS, fish, i7-13650HX, 40GB RAM, RTX 4060 8GB): Hermes, Ollama, git, Obsidian, web.
  **Estabilidade, 12/08/2026 — reclassificado em (124):** 3 eventos sem shutdown limpo no dia, **1 com causa própria confirmada, 2 sem causa determinada.** O 2º tem evidência independente real — GPU presa em resume, `systemd-logind` falhando por watchdog próprio e entrando em loop de 51 reinícios (MEMÓRIAS (99)) — não é ausência de shutdown limpo, é mecanismo capturado em ato; não reclassificado. O 1º (`nowatchdog` mascarou tudo, sem nenhum rastro) e o 3º (só corte abrupto no journal, coincide no tempo com tentativa de GRUB do próprio Humano, MEMÓRIAS (100)) têm, desde (124), uma explicação adicional possível — desligamento forçado por bug de login (ver linha de 13/08 abaixo) — ao lado das já registradas; nenhuma decidida. Mitigações aplicadas — `nowatchdog` removido, `mem_sleep_default=s2idle` (MEMÓRIAS (101)) — continuam justificadas pelo 2º evento sozinho, e reforçadas pela recorrência de 13/08 (suspend/resume seguem não confiáveis neste hardware, mudou a manifestação, não sumiu). `/etc/default/grub.bak.20260812-155431` é a rede de segurança até um boot limpo confirmar efeito; não apagar antes.
  **13/08/2026 — bug de login recorrente, mecanismo achado ao vivo (MEMÓRIAS (124)/(125)):** a máquina trava a senha correta em loop porque **suspende e acorda sozinha repetidamente** (s2idle, `org_kde_powerde` re-suspendendo a cada resume — 91 ciclos numa madrugada). Cada resume falha em recuperar o teclado USB de verdade (`PM: failed to resume async`, desconecta/reconecta), a GPU (`NVRM: Failed to handle ACPI D-Notifier`) e a EEPROM da RAM — sem derrubar o sistema. Efeito na tela: teclas perdidas durante a digitação da senha + `pam_unix: conversation failed` repetido, que `pam_faillock` acumula até travar a conta. Esperar não resolve porque o ciclo de suspend/resume não para sozinho. Boot da madrugada de 13/08 termina abruptamente às 08:08:33, ~3 min depois do travamento de conta (08:05:56) — muito provavelmente o desligamento forçado pelo Humano descrito nesta sessão, não travamento espontâneo novo (não confirmado por Máquina que foi literalmente o botão). **Procedimento completo para a próxima ocorrência:** `PROCEDIMENTO_LOGIN.md`, raiz do repositório. Journal do boot: `journalctl --verify` achou corrupção num segmento arquivado (`user-1000@...journal~`, 52%) — o de (111) já rotacionou e sumiu antes disso, este é achado novo.
- **Orusoua** (réplica Windows 11, leitura/failover) — *planejado*.

## Cérebro
- **Principal:** `gemini-2.5-flash` (Google API, grátis). Teto do free tier ~20 requisições/dia — estourar gera 429. **Circuit breaker ativo** (plugin `gemini_quota_guard`, hook `pre_api_request`): conta requisições reais e avisa a partir da 15ª do dia, sem bloquear nem rerotear (MEMÓRIAS (122)).
- **Fallback:** `qwen3-14b-64k` local (Ollama). Contexto 64k por override durável em `custom_providers`; tool-calling **e** raciocínio visível. Adotado exatamente por expor o raciocínio, o que permite pegar fabricação antes da ação em vez de auditar depois. **Desligado desde (112)** (`fallback_model` comentado em `config.yaml`) — confirmado ao vivo em (118): sem ele, 429 do Gemini vira erro limpo pro Humano ("API call failed after 3 retries"), não travamento.
- **Roteamento por complexidade — aprovado, NÃO implementado** (MEMÓRIAS (64)): o Hermes estima a complexidade antes de escolher cérebro; tarefa simples resolve no qwen local, só escala para o Gemini acima do limite. `lacuna`: limite não definido nem medido. Executor: Claude Code na Máquina, com prova antes/depois.
- **Último recurso manual:** `llama3.1:8b` — sem tool-calling, fora da cadeia.
- **Barreira dura:** o Hermes exige contexto ≥64k (constante de produto, não derivada do payload). Skills 12 ativas / 56 off; tools 12 de 18; payload ~12,6k tokens.
- **Padrão de alucinação** documentado é do antecessor `qwen2.5-14b-64k` (inventava entradas e datas). O qwen3 não tem incidente registrado. A suspensão de MOD é do **papel** "fallback", não da versão — o contador de sessões limpas conta a partir da troca para o qwen3.
- **Candidato avaliado, não adotado: `qwen3.5:9b`** (nome parecido com `qwen3-14b-64k` acima, modelo diferente — checar sempre qual dos dois, ver MEMÓRIAS (114)). Testado (MEMÓRIAS (119)/(120)): tool-calling correto sob payload real com `num_ctx=65536`, mas **VRAM de pico maior que o fallback atual** (91,3% contra 83,8% dos 8.188 MiB da placa) — o argumento original de "libera VRAM" está refutado por medição; se adotado, é por offload/velocidade (30/33 camadas na GPU contra 23/41), não por folga. Um incidente de fabricação registrado sob contexto degradado (truncamento do teste, não do modelo em uso normal) — o `thinking` visível foi o que expôs. **Testado pelo caminho real de produção em (121): reprovou o pipeline, não o modelo** — contexto cortado pra 4096 tokens apesar de `context_length: 65536` configurado; mecanismo mapeado em (122) (não é regressão de código: o `hermes-agent` local está byte-idêntico desde 06/07/2026), causa exata ainda `lacuna`. Não instalado como fallback. **Sem variante text-only na biblioteca oficial** (64 tags checadas, todas multimodais) — o encoder de visão é permanente nesta família de modelo, confirmado via `/api/show` (27 blocos de atenção de visão), medição isolada: 6.494 MiB de VRAM com `num_ctx=4096` só-texto (MEMÓRIAS (123)).

## Serviços (boot)
`ollama.service` · Docker `open-webui` + `kokoro-tts` · `hermes-gateway.service` (user unit, linger, porta 8642) · `agata-consolidacao.timer`.
Leftovers pré-Hermes — **não recriar**. `agata.service` e `agatha.service` confirmados ausentes (`systemctl status` → "could not be found"). **`agata-rest.service` ainda existe, mas está `disabled`** (`systemctl status` confirma, MEMÓRIAS (107)). Remoção da unit (com sudo) está na fila, mas não é impeditivo. As duas mitigações de GRUB (`nowatchdog` removido, `mem_sleep_default=s2idle`) foram aplicadas e **confirmadas no kernel via `/proc/cmdline`** (lido diretamente, sem restrição — `mem_sleep_default=s2idle` presente, `nowatchdog` ausente).

## Memória e hidratação
- Canônicos em `~/agata`. O repositório git é também o cofre Obsidian. Memória nativa do Hermes symlinkada em `~/agata/memoria/` — o arquivo real é o canônico; quem é link é o lado do Hermes.
- **MEMÓRIAS.md** é o terceiro canônico: DIÁRIO coletivo + blocos MOD por modelo + registro do Conselho, tudo append-only num arquivo só.
- **Hidratação real hoje:** `.hermes.md` único, gerado por hook pre-commit (`.githooks/gerar-hermes-md.sh`), sem filtro por modelo. Injeta REGRAS + PROJETO + fim de MEMÓRIAS no system prompt. Fora do Hermes (outro executor/cliente lendo o canon) não há contador mecânico de turno — conta-se a própria resposta no contexto, como manda REGRAS Regra 1.
- **Teto de entrega do carregador do `hermes-agent`, achado e corrigido nesta sessão:** o carregador de arquivo de contexto (`agent/prompt_builder.py`) trunca `.hermes.md` antes de injetar — piso dinâmico de 20.000 caracteres, vindo de `model.context_length: 65536` em `~/.hermes/config.yaml` (a mesma variável, não distinção por provedor ativo). Cortava a partir do char ~14.000, cabeça+cauda de 20.000 — **PROJETO.md inteiro (começava no char 16.353) nunca chegava a nenhum modelo.** Corrigido com `context_file_max_chars: 100000` explícito no `config.yaml`, escopo estreito (não toca `model.context_length`, que também governa compressão de histórico de conversa — `lacuna: efeito lá, não medido`). Verificado rodando o carregador real, não só lendo a config. Ver MEMÓRIAS (103).
- Silos por modelo (Fase 2, ainda NÃO construídos): o hook passará a gerar `.hermes-<modelo>.md`, cada um com REGRAS + PROJETO + fim de MEMÓRIAS filtrando só o MOD do modelo-alvo. Arquivo único foi rejeitado em auditoria: vaza MOD entre modelos via system prompt. Até lá, silo do Conselho (REGRAS, "O Conselho" item 3) é **norma, não mecanismo**.
- **A janela de injeção é de 30 linhas** do fim de MEMÓRIAS. Entradas longas não chegam inteiras ao contexto — escreva contando com isso.
- **Âncora de integridade (1)-(62):** 128.671 B, sha256 `b26ac113f7a6f72c875391c2d07d94f6f6c827cc9d14c180ecc324b14ab4e03a`. Verificação por marcador de conteúdo (início/fim do trecho) + comprimento — nunca por offset fixo ou número de linha, que se deslocam a cada edição de preâmbulo (MEMÓRIAS (96) achou isso; (97) corrigiu: o offset registrado em (96) é foto, não âncora durável). Script: `scripts/achar_ancora_1_62.py`.
- RAG só no Open WebUI e só em sessões Gemini — mantido por prudência (janela maior), não pela justificativa antiga de "qwen 32k estoura", que está desatualizada.
- **`memoria/missoes/` (renomeado de `memoria/projetos/` em 12/08/2026) é um quarto pilar, LOCAL por desenho.** Um arquivo editável por missão, mais `INDICE.md`. Repositório git próprio, sem remote — gitignorado do repo principal (`.gitignore` cobre `*.bundle` em qualquer lugar da árvore, não só a pasta — endurecido depois de um bundle quase vazar um nível acima, MEMÓRIAS (97)/(98)), nunca público, nunca em hidratação. Pesquisado sob demanda por qualquer modelo com acesso à Máquina, não injetado automaticamente. Propósito próximo do bg-review desligado, mecanismo distinto em três pontos nomeados — ver `INDICE.md` local e MEMÓRIAS (91)-(95). Ordem do Humano.
- **Fonte canônica (URLs) e atualização:** `https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/main/{REGRAS,PROJETO,MEMÓRIAS}.md`. Primeira sessão: o Humano envia os 3. Depois: o modelo busca das URLs, seguindo a ordem de verificação de REGRAS.md. `atualizar <REGRAS|PROJETO|MEMÓRIAS|TUDO>` = git pull + regenerar hidratação. Nunca sobrescreve história; conflito → para e avisa.

## Interface
Hermes CLI/TUI na Máquina. Open WebUI como frontend puro: tools, memória e search nativos desligados — o executor e a memória são únicos, e são do Hermes.
Voz: Kokoro-FastAPI (`pf_dora`, CPU) + Whisper STT. Remoto exige HTTPS via Tailscale.

## Segurança
Sandbox sempre. Segredos só em `~/.hermes/.env`, fora do repo.
**O api_server executa terminal: nunca expor sem contenção.** Auditado em MEMÓRIAS (126) — a frase antiga desta seção descrevia Tailscale com dupla autenticação, mecanismo que **não existe nesta máquina** (achado em (125)). O mecanismo real, confirmado por `ss -tlnp`: `api_server` compartilha a porta do `hermes-gateway` (8642), e o bind é **`127.0.0.1`** — contenção de kernel, não de firewall. Open WebUI (8080, `network_mode: host`) e Kokoro TTS (8880, publicado pelo Docker) também só em loopback. Mesmo efeito de contenção do texto antigo, mecanismo diferente do descrito — corrigido aqui pra não sustentar um controle de segurança em algo que não roda.
**Ollama (`11434`):** restrito a `127.0.0.1` desde MEMÓRIAS (126)/(127), confirmado no bind real (`ss -tlnp`) e no ambiente do processo. `override.conf` completo com as 5 variáveis (`OLLAMA_NUM_GPU=999`, `OLLAMA_KV_CACHE_TYPE=q4_0`, `CUDA_VISIBLE_DEVICES=0`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_HOST=127.0.0.1:11434`) — o efeito colateral de (127) (`OLLAMA_NUM_GPU`/`CUDA_VISIBLE_DEVICES`/`OLLAMA_FLASH_ATTENTION` apagados por um `tee` destrutivo) foi corrigido, confirmado em MEMÓRIAS (130). Efeito sobre estabilidade de VRAM não medido nesta correção — restaurar a variável não é o mesmo que testar carga.
Ao rotacionar chave, atualize **todos** os consumidores no mesmo passo. Rotação parcial dá 401 silencioso.

## Estado dos bugs e dos testes
- **Gemini 429 ("perdi a conexão"):** corrigido. Causa raiz, mecanismo (`_summarize_api_error`/`run_agent.py:2146`) e verificação: MEMÓRIAS (38)-(40).
  **Risco residual, não bug ativo:** o patch vive no `hermes-agent` vendored, fora do repo canônico, sem backup. Um `hermes update` pode descartá-lo em silêncio. **Reverificar após qualquer atualização do Hermes.**
- **`carregar` no fallback:** nenhum bug confirmado com esse nome na história real. Não carregar adiante como fato. Se reaparecer, o protocolo é: curl na 8642 forçando fallback com `carregar`, capturar o system prompt efetivo no Ollama, e testar em ordem — (a) hidratação não injetada, (b) injetada mas truncada, (c) recebida e ignorada.
- **Truncamento silencioso de `num_ctx` no caminho de produção do fallback, achado em (121), bug diferente do item acima:** com o fallback reativado temporariamente pra testar `qwen3.5:9b`, a chamada real via `hermes-agent` pediu só 4096 tokens ao Ollama apesar de `context_length: 65536` configurado em `custom_providers` — prompt de ~37-38k tokens cortado, resposta ilegível. Mecanismo mapeado em (122): não é regressão de código do `hermes-agent` (byte-idêntico desde 06/07/2026, confirmado por `mtime` e `git log` do checkout local), nem cache de `context_length` (arquivo checado, sem entrada pro modelo). Hipótese líder, não fechada: merge raso em `agent/transports/chat_completions.py:566-573` pode substituir inteiro o `extra_body["options"]` do perfil de provedor, apagando o `num_ctx` sem aviso. Causa exata segue `lacuna`. **Não afeta o `qwen3-14b-64k` em produção**, que pediu `num_ctx=65536` corretamente em (110) — mesmo mecanismo, resultado diferente, motivo ainda não determinado.
- **TES-001:** não fechado. Três rodadas executadas com resultado adverso documentado (MEMÓRIAS (66), (69), (73)). Exige sessões genuinamente independentes.
  **Hipótese em aberto, não afirmada como causa (MEMÓRIAS (106)):** o teto de truncamento do carregador ((103)/(104)) esteve ativo durante essas três rodadas — os modelos testados podem ter sido avaliados contra REGRAS que nunca chegaram inteiras. Não é reafirmação de causalidade, é motivo pra rerodar TES-001 depois da correção de (104) e comparar.
- **Item especificado, não implementado — asserção byte a byte de entrega (harness A1, quando vier):** verificar que o que o carregador entrega é byte-idêntico ao que deveria (não só ao que o arquivo contém) — teste permanente, não conserto único, motivado por (103)-(105) ter achado um teto silencioso que já existia sem ninguém saber. `lacuna`: numeração/escopo de "A1" fora do que este registro conhece — só a especificação do item, não o harness inteiro.
- **TES-002:** **formalmente inativo até existir silo (Fase 2).** Nonce `e1d1a` aposentado (MEMÓRIAS (90)) — não deve ser ecoado por ninguém. Sucessor existe, gerado pela Máquina, guardado fora do canônico, nunca commitado, nunca em hidratação — entregue à mão pelo Humano, uma vez, só ao modelo-alvo, quando ele decidir reabrir o teste. Até lá: nenhum nonce ativo, dizer isso em vez de fingir. Protocolo completo em REGRAS.md, "Continuidade mecânica". Ver MEMÓRIAS (70), (90).
- **Segunda opinião sobre a regra 3X:** pendente desde MEMÓRIAS (68). O executor designado devolveu eco do texto do proponente, não parecer. Encaminhamento recomendado: GLM, auditor ativo desde (44).

## Plano vigente (v1.1 — Fases 0–2 são compromisso; 3+ é bússola)
- **Fase 0 — Saneamento (agora):** publicar no remoto as entradas acumuladas · fechar TES-001 · reverificar o patch do 429 após qualquer `hermes update`.
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
**Camada nuvem** — NotebookLM e afins, pesquisa em andamento: cruzamento de dados, é **RELATO/projeção**. Mão única: lê, nunca escreve fato de volta. Só o não-sensível sobe; segredo, chave e canon nunca.

**bg-review do Hermes Gateway está desligado** (`nudge_interval: 0` em `~/.hermes/config.yaml`, fora do repo). Era um mecanismo que reescrevia sozinho o MEMORY.md nativo — mesmo inode do canônico — e chegou a **apagar identidade e história** para caber num teto de caracteres, sem humano no loop. Consequência aceita: sem auto-captura de fatos; a memória muda só por edição deliberada, por MEMÓRIAS, ou sob comando explícito.

## Riscos conhecidos (limitações, não pendências)
- O Gemini pode deixar de ser grátis. Plano B: pesquisar alternativas gratuitas quando doer.
- Silo é disciplina, não mecanismo, até a Fase 2.
- O patch do handler de 429 vive em repositório vendored sem backup — reverificar após todo `hermes update`.
- Desconfiança permanente tem custo. O overhead é campo opcional em MEMÓRIAS, sem automação; silêncio também é dado.
- Modelo local como classe é limitado neste hardware: o teto é ~14b/9GB. Assunto encerrado sem hardware novo.
- Fricções entre modelos de fornecedores diferentes são característica do período; registram-se quando surgem, não se resolvem por regra.
- **Sucessão do operador Humano é ponto único de falha.** O sistema trata sucessão de modelo com cuidado (Regra 6, silos, MOD), mas não tem plano pra sucessão do operador — só aparece em Fase 5, sem prazo. Se o Humano ficar indisponível, não há segundo operador definido.
- **Exposição do conteúdo do próprio DIÁRIO, não só do nonce.** A avaliação de risco do repositório público (MEMÓRIAS (62)/(70)) cobriu o nonce queimado, nunca o conteúdo do DIÁRIO coletivo em si — que já registra hábitos, hardware e rotina do Humano, e é público por decisão. Vale revisão futura sobre o que mover pra camada privada, sem editar história existente.
- **Memória nativa do Hermes (`memoria/USER.md`, `memoria/MEMORY.md`) é vetor distinto do DIÁRIO.** Já rastreada no repo público antes desta sessão, expõe dado pessoal e narrativa afetiva endereçando o Humano por nome. Diferente do item acima: este conteúdo é escrito pela Máquina (mecanismo de memória do Hermes), não por decisão deliberada do Humano ou do Modelo — o mesmo tipo de escrita automática que já apagou identidade em (47). Vetor de risco próprio, não subitem do risco do DIÁRIO.
- **Primeira cópia da história fora desta máquina, feita.** HD externo `AgataBkup01` (1,9T, exFAT) — duas passadas manuais completas em 12/08/2026 (MEMÓRIAS (116)/(117)), verificadas por restauração (`git bundle verify` + clone de teste real pra `/tmp`, não só listagem). Decidido pelo Humano: conteúdo = tudo (`~/agata` inteiro + `memoria/missoes/`, mais o diff isolado do patch do 429) · método = `git bundle` pros dois repositórios, cópia simples pro resto (`rsync` descartado — destino exFAT sem POSIX/symlink) · frequência = manual, por ora, sem timer. **Em aberto:** timer/gancho de repetição automática (proposta registrada em (117), não implementada) · cifra e inclusão do `.env` (decisão separada, ainda não tomada).
- **Alcance retroativo do bug de `grep -oE` achado em (105), não auditado.** O `grep` real desta máquina truncava matches de `-oE` com `[^\n]*`/similar em UTF-8 multibyte (português é acentuado; MEMÓRIAS inteiro é português). Não há como saber, sem auditoria manual, se alguma verificação de sessão anterior a (105) que tenha usado `grep -oE` sobre conteúdo acentuado produziu resultado incorreto registrado como confirmado. Não afirmado que algo caiu — registrado como possibilidade não descartada.

## Fronteira de recusas (propostas já decididas — não repropor)
Não é deliberação registrada aqui por hábito — é decisão. Sem esta tabela, cada modelo novo que lê um levantamento externo repropõe o que já foi recusado, com toda a razão de sua parte, porque o canon não carregava a objeção.

| Recusado | Motivo | Onde |
|---|---|---|
| Descarte de fatos por valor | Regra 4, absoluta | MEMÓRIAS (113) |
| Reconsolidação por reescrita | Já existe como entrada nova | MEMÓRIAS (113) |
| Reflections agendadas escrevendo memória | Mecanismo do bg-review, (47)/(48) | MEMÓRIAS (113) |
| Vector store como camada de memória | Refutado por medição nesta escala | MEMÓRIAS (115) |
| MEMÓRIAS em repo sem remote como cópia única | Privado também se versiona — git próprio, sem remote | (91)→(92) |
| RLM como auto-treino sem humano no loop | Regra 3 | MEMÓRIAS (114) |
| Conformidade com EU AI Act | Fora de escopo: pessoal, operador único, Brasil | — |

## Diagnóstico
`hermes doctor` / `hermes status`. Prontidão da Agata: definida nas REGRAS.
