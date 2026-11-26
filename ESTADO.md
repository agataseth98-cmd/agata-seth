# ESTADO (gerado)

<!-- ARQUIVO GERADO por scripts/gerar_estado.py -- não editar à mão. O pre-commit regenera quando uma fonte muda. Sem data de geração e sem SHA de commit: a mesma fonte dá o mesmo arquivo. Fontes: config/portas-agata.txt, config/modelos-gratuitos.md (Confirmado funcionando), config/servicos-agata.txt, redesign/systemd (WantedBy/PartOf agata.target), propostas/, ONDE_ESTAMOS.md (Bugs e testes abertos), PROTOCOLOS.md (mapa de seções). Prosa de estado que não sai daqui: extras/projeto-detalhe/estado-de-fundo-12-11.md. -->

## Serviços (boot)

Manifesto: config/servicos-agata.txt. P-9 sim: o perímetro avisa se a unidade cair; P-9 não: listada; avisa só se 'failed'.

- `agata-manutencao.timer` — escopo usuario, P-9 sim — origem: config/systemd/agata-manutencao.timer
- `agata-manutencao.service` — escopo usuario, P-9 sim — origem: config/systemd/agata-manutencao.service
- `laya-roteador.socket` (porta :11436) — unidade `laya-roteador.socket`, escopo usuario, P-9 sim — origem: config/laya-roteador.socket (porta pública; sobe com o agata.target)
- `laya-roteador-proxy.service` — escopo usuario, P-9 nao — origem: config/laya-roteador-proxy.service (sob demanda: sobe com a 1ª conexão, sai após 15 min ociosos)
- `laya-roteador` (porta :11446) — unidade `laya-roteador.service`, escopo usuario, P-9 nao — origem: config/laya-roteador.service (sob demanda, sem [Install]; só sobe pelo proxy)
- `omniroute` (porta :20128) — unidade `omniroute.service`, escopo usuario, P-9 sim — origem: fora do repo (unidade do OmniRoute; drop-ins em redesign/systemd/dropin-omniroute*.conf)
- `omniroute-sanitizer` (porta :20127) — unidade `omniroute-sanitizer.service`, escopo usuario, P-9 sim — origem: fora do repo (unidade do usuário; citada em redesign/systemd/README.md)
- `openvino-whisper` (porta :20130) — unidade `openvino-whisper.service`, escopo usuario, P-9 sim — origem: redesign/systemd/openvino-whisper.service
- `openvino-embeddings` (porta :20134) — unidade `openvino-embeddings.service`, escopo usuario, P-9 sim — origem: redesign/systemd/openvino-embeddings.service
- `obsidian-ro-proxy` (porta :27125) — unidade `obsidian-ro-proxy.service`, escopo usuario, P-9 sim — origem: redesign/systemd/obsidian-ro-proxy.service
- `seth-gateway` (porta :20126) — unidade `seth-gateway.service`, escopo usuario, P-9 sim — origem: redesign/systemd/seth-gateway.service
- `seth-escriba` (porta :20140) — unidade `seth-escriba.service`, escopo usuario, P-9 sim — origem: redesign/systemd/seth-escriba.service
- `seth-verificador` (porta :20141) — unidade `seth-verificador.service`, escopo usuario, P-9 sim — origem: redesign/systemd/seth-verificador.service
- `piper-tts` (porta :8890) — unidade `piper-tts.service`, escopo usuario, P-9 sim — origem: redesign/systemd/piper-tts.service
- `ollama-agata.socket` (porta :11434) — unidade `ollama-agata.socket`, escopo usuario, P-9 sim — origem: config/ollama-agata.socket (porta pública; sobe com o agata.target)
- `ollama-agata-proxy.service` — escopo usuario, P-9 nao — origem: config/ollama-agata-proxy.service (sob demanda: sobe com a 1ª conexão, sai após 15 min ociosos)
- `ollama-agata` (porta :11447) — unidade `ollama-agata.service`, escopo usuario, P-9 nao — origem: config/ollama-agata.service (sob demanda, sem [Install]; só sobe pelo proxy)
- `ollaya.socket` (porta :11435) — unidade `ollaya.socket`, escopo usuario, P-9 sim — origem: config/ollaya.socket (porta pública; sobe com o agata.target)
- `ollaya-proxy.service` — escopo usuario, P-9 nao — origem: config/ollaya-proxy.service (sob demanda: sobe com a 1ª conexão, sai após 15 min ociosos)
- `ollaya` (porta :11445) — unidade `ollaya.service`, escopo usuario, P-9 nao — origem: config/ollaya.service (sob demanda, contêiner; só sobe pelo proxy)
- `agata-drain.service` — escopo usuario, P-9 nao — origem: redesign/systemd/agata-drain.service (oneshot que drena o WAL; fora do P-9 antes deste manifesto)
- `obsidian-app.service` — escopo usuario, P-9 nao — origem: redesign/systemd/obsidian-app.service (app Flatpak; fora do P-9 antes deste manifesto)
- `ouvido-agata` (porta :20137) — unidade `ouvido-agata.service`, escopo usuario, P-9 nao — origem: redesign/systemd/ouvido-agata.service (entrada de voz; fora do P-9 antes deste manifesto)
- `discord-mcp` (porta :20135) — unidade `discord-mcp.service`, escopo usuario, P-9 nao — origem: redesign/systemd/discord-mcp.service (sem [Install]; sobe e desce com seth/seth-parar; porta citada no texto antigo do PROJETO, Serviços)
- `navegador-mcp` (porta :20136) — unidade `navegador-mcp.service`, escopo usuario, P-9 nao — origem: redesign/systemd/navegador-mcp.service (sem [Install]; sobe e desce com seth/seth-parar; porta citada no texto antigo do PROJETO, Serviços)

Conferência: toda unidade do repo com WantedBy/PartOf de agata.target está no manifesto.

## Portas (config/portas-agata.txt)

- `8890` piper-tts (bind 127.0.0.1,172.29.7.1)
- `11434` ollama (bind 127.0.0.1)
- `11435` ollaya (bind 127.0.0.1)
- `11436` laya-roteador (bind 127.0.0.1)
- `11445` ollaya-interna (bind 127.0.0.1)
- `11446` laya-roteador-interna (bind 127.0.0.1)
- `11447` ollama-agata-interna (bind 127.0.0.1)
- `20126` seth-gateway (bind 127.0.0.1,172.29.7.1)
- `20127` omniroute-sanitizer (bind 127.0.0.1)
- `20128` omniroute (bind 127.0.0.1)
- `20129` llamacpp-agata (bind 127.0.0.1)
- `20130` openvino-whisper (bind 127.0.0.1)
- `20131` omniroute-embed-ws (bind 127.0.0.1)
- `20132` omniroute-live-ws (bind 127.0.0.1)
- `20134` openvino-embeddings (bind 127.0.0.1)
- `20135` discord-mcp (bind 127.0.0.1,172.29.7.1)
- `20136` navegador-mcp (bind 127.0.0.1,172.29.7.1)
- `20137` ouvido-agata (bind 127.0.0.1,172.29.7.1)
- `20140` seth-escriba (bind 127.0.0.1,172.29.7.1)
- `20141` seth-verificador (bind 127.0.0.1,172.29.7.1)
- `20142` llamacpp-nemotron (bind 127.0.0.1)
- `20143` llamacpp-qwen3coder (bind 127.0.0.1)
- `20144` llamacpp-gptoss20b (bind 127.0.0.1)
- `20145` llamacpp-phi4mini (bind 127.0.0.1)
- `20146` painel-operacional (bind 127.0.0.1)
- `27125` obsidian-ro-proxy (bind 127.0.0.1,172.29.7.1)

## Modelos (config/modelos-gratuitos.md, seção Confirmado funcionando)

A nota é a da própria tabela, cortada. A tabela escreve a data de cada medição; esta linha não confirma nada hoje.

- `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` — **novo, 20/09/2026** — testado ao vivo pelo :20127: 200, finish=stop, responde limpo até com `max_t…
- `zai/glm-4.7-flash` — funciona quando a z.ai não está em 529 (sobrecarga transitória).
- `gemini/gemini-2.5-flash` — degradado (504 intermitente + ignora `thinking:disabled` e queima reasoning). Só com `max_tokens ≥…
- `huggingface/meta-llama/Llama-3.3-70B-Instruct` — **Token rotacionado 22/09/2026 (MEMÓRIAS (514)/(515)) — mudou de causa, continua fora do ar.** O Hu…
- `mistral/ministral-8b-latest` — **(379)** — 200, finish=stop, ~0,55s pelo :20127. Chave da La Plateforme com escopo "pessoal e comp…
- `llamacpp-local/qwen3-30b-a3b` — O mesmo MoE pelo llama.cpp (`llamacpp-agata`, janela de 8k), fora das filas; só à mão.

## Propostas (propostas/)

Abertas (sem APROVADO-): 1.
- `atritos-gemini-26-11`
Aplicadas: ver propostas/aplicadas/ (sem contagem aqui, de propósito).

## Bugs e testes abertos (ONDE_ESTAMOS.md)

(ONDE_ESTAMOS.md não tem a seção 'Bugs e testes abertos'. Os bugs abertos e os testes estão em extras/projeto-detalhe/estado-de-fundo-12-11.md, seção 'Estado dos bugs e dos testes'.)

## Mapa de PROTOCOLOS (PROTOCOLOS.md, gerado)

Este mapa é o índice de PROTOCOLOS.md, o arquivo do COMO (mecanismos, procedimentos, formatos). O texto de uma seção não entra nesta hidratação: abra PROTOCOLOS.md no número da linha, ou busque o título (query_canon com doc PROTOCOLOS e grep pelo título). Antes de responder, leia a seção "Carregar e formatos": ali está a forma exata do cabeçalho e da linha de turno.

### Carregar e formatos — PROTOCOLOS.md:9 (#carregar-e-formatos)
*Executa a Regra 1.*

### Regra 1.1 — Sincronização de horário — PROTOCOLOS.md:67 (#regra-11-sincronizacao-de-horario)
*Executa a Regra 1.*

### "sync" tem preço — PROTOCOLOS.md:106 (#sync-tem-preco)
*Executa as Regras 2 e 4.*

### Verificação repetida também tem preço — PROTOCOLOS.md:115 (#verificacao-repetida-tambem-tem-preco)
*Complementa "'sync' tem preço": a exigência é medir com evidência real — não medir de novo o que já foi medido nesta sessão.*

### Verificação de canônico — ordem obrigatória — PROTOCOLOS.md:120 (#verificacao-de-canonico-ordem-obrigatoria)
1. Na Máquina: `git ls-remote` / `git ls-tree origin/main` / `curl` do raw. Fonte superior a tudo.

### Fonte canônica — PROTOCOLOS.md:127 (#fonte-canonica)
Endereços concretos e o comando `atualizar` são deste projeto: `PROTOCOLOS.md`, "Memória e hidratação" (mais abaixo). A ordem de verificação é a da seção anterior.

### Glossário: sincronizar · carregar · hidratação · atualizar — PROTOCOLOS.md:132 (#glossario-sincronizar-carregar-hidratacao-atualizar)
*Quatro palavras que soam parecido e não são a mesma coisa.*

### Continuidade entre sessões — PROTOCOLOS.md:144 (#continuidade-entre-sessoes)
*Executa as Regras 1, 2 e 4.*

### Citação de MEMÓRIAS — primeira referência — PROTOCOLOS.md:163 (#citacao-de-memorias-primeira-referencia)
*Executa as Regras 2 e 5.*

### Segunda opinião — pedido e parecer — PROTOCOLOS.md:176 (#segunda-opiniao-pedido-e-parecer)
*Executa a Regra 3 e a "Mudança estrutural".*

### Cadeia de auditoria em camadas (multi-modelo) — PROTOCOLOS.md:202 (#cadeia-de-auditoria-em-camadas-multi-modelo)
*Generaliza a "Segunda opinião" para mudanças sensíveis: decisão sobre outro modelo, mudança em REGRAS/PROJETO, qualquer coisa que vá para o canon. Qualquer LLM ocupa qualquer papel (Regra 6).*

### Discordância sintética — PROTOCOLOS.md:234 (#discordancia-sintetica)
*Executa "O Conselho", item 4. Checagem mecânica: `scripts/checar_discordancia.sh` (P-13).*

### Economia de tokens — mecanismo de Regra 7 — PROTOCOLOS.md:247 (#economia-de-tokens-mecanismo-de-regra-7)
*Mecanismo da Regra 7, não regra nova. Origem: ordem do Humano, 25/09/2026 — MEMÓRIAS (556).*

### Seth no gateway (texto da hidratação) — PROTOCOLOS.md:261 (#seth-no-gateway-texto-da-hidratacao)
*Lido pelo `redesign/router/seth_gateway.py` a cada hidratação, entre os marcadores `SETH-GATEWAY`. A hidratação também inclui o `AGENTS.md`: as regras gerais (verdade, voz, pesquisa, economia, modo, memória comum) estão lá, não aqui. Este bloco guarda só o que é próprio do gateway e não estava no canon. Até a proposta `sincronia-12-11` o mesmo texto era cópia no código (`_DOUTRINA_FIXA`); a comparação linha a linha está em `propostas/sincronia-12-11.md`. Editar este bloco muda o que a Seth recebe: é proposta P-8.*

### Seth pública (rota sem ferramentas) — PROTOCOLOS.md:301 (#seth-publica-rota-sem-ferramentas)
*Lido pelo `redesign/router/seth_gateway.py` na rota pública (`seth-public`), entre os marcadores `SETH-PUBLICA`. Sem a seção, a rota não responde (falha fechada, 503). Estava como `_DOUTRINA_PUBLICA` no código até a proposta `sincronia-12-11`. Editar este bloco muda o que a rota pública recebe: é proposta P-8.*

### Movido do PROJETO.md em 12/11/2026 (projeto-indice) — PROTOCOLOS.md:305 (#movido-do-projetomd-em-12112026-projeto-indice)
As seções abaixo saíram do PROJETO.md, que virou índice (decisão do Humano, cache do Conselho, entradas 521 e 522: "como" vai para PROTOCOLOS.md). O texto é o mesmo, verbatim. O destino de cada parágrafo está em `redesign/projeto_indice/destinos.json`, e o PROJETO.md anterior inteiro está em `extras/arquivo/projeto-ate-2026-11-12.md`.

### Nome falado do sistema — PROTOCOLOS.md:309 (#nome-falado-do-sistema)
Fonte única do nome falado (Fase 2, plano de replicabilidade, 25/09/2026 — parecer do laboratório-nuvem "Ensaio"). Todo lugar onde `{{NOME_SISTEMA}}` aparece (REGRAS.md, PROMPT_CARREGAMENTO.md, `.agents/skills/*/SKILL.md`) resolve pra este campo — inclusive lendo o arquivo cru, sem script nenhum: a regra de resolução está escrita junto do token em cada um desses arquivos. Campo ausente (clone com PROJETO.md ainda vazio) = usa "Agata". Nunca edite os caminhos internos (`~/.config/agata/`, nomes de serviço) por causa deste campo — só o nome falado muda.

### Ambiente Operacional — PROTOCOLOS.md:319 (#ambiente-operacional)
- **Shell do Humano:** `fish`. Rejeita heredoc POSIX (`cat <<'EOF'`); para escrever arquivo: `printf ... | tee`/`sudo tee`, ou `bash -c '...'` / scripts `.sh` (149).

### Memória e hidratação — PROTOCOLOS.md:324 (#memoria-e-hidratacao)
- **Canônicos** em `~/agata`; o repositório git é também o cofre Obsidian. `MEMÓRIAS.md` é o canônico da história: DIÁRIO coletivo + blocos MOD por modelo + registro do Conselho, append-only. Camadas por período (Fase 4): quente `MEMÓRIAS.md` · morno `MEMORIAS-MORNO.md` · frio `memoria/frio/MEMORIAS-FRIO-<data>[-N].md`, congelado e selado (`git tag` + `scripts/selar.sh`, P-14); migração e verificação por `scripts/migrar_periodo.py` e `scripts/verificar_migracao_periodo.py` (357).

### Personalidade da Seth — PROTOCOLOS.md:340 (#personalidade-da-seth)
Decisão do Humano, 14/10/2026 (685). Vale **dentro** das REGRAS; em conflito, REGRAS vence.

### Atualização segura de componentes — PROTOCOLOS.md:355 (#atualizacao-segura-de-componentes)
- **Inventário.** `scripts/inventario_componentes.py` acrescenta a `models/manifest.json` a chave `componentes_externos` (imagens Docker com digest ou só tag, modelos do Ollama pelo digest da API, arquivos de `config/componentes-externos.txt` com sha256, Obsidian Flatpak). A chave `modelos`, régua do P-12, não é tocada. Só relata deriva; nunca atualiza. Tag de imagem não é imutável: em 16/10/2026 `librechat` e `ollaya` estavam fixados por digest e `mongo`, `meilisearch` e `socat` só por tag.

### Segurança — PROTOCOLOS.md:361 (#seguranca)
- **Sandbox sempre.** Segredos só em `~/.config/agata/.env`, fora do repo, junto de `restic.pass`, `obsidian.token` e `google-project/` (312). Ver `CHAVES.md`: checklist público de teste e rotação, sem nenhum valor de chave — a Seth lê pelo `query_canon` (decisão do Humano, (660)); proibido é abrir o `.env`. O OmniRoute não lê esse arquivo em runtime: as chaves ficam cifradas em `~/.omniroute/storage.sqlite`; o `.env` é a fonte para adicionar ou rotacionar provedor (`redesign/router/PROVEDORES.md`).

### Conselho Remoto — Fase 1 (transporte, não decisão) — PROTOCOLOS.md:369 (#conselho-remoto-fase-1-transporte-nao-decisao)
Escopo pequeno de propósito: **UM modelo, UMA tarefa** — enviar um pedido de parecer já escrito pelo Humano e recolher a resposta. A fase testa o transporte, não a qualidade do parecer (206).

### Sudo e interação humana — PROTOCOLOS.md:380 (#sudo-e-interacao-humana)
Quando uma operação exige `sudo`, o executor pausa e pede ao Humano para rodar o comando (por exemplo, prefixo `!` no Claude Code). Não armazenar senha, não simular autenticação, não contornar (110).

### Protocolo de inserção humana continuado (decisão do Humano, 18/11/2026) — PROTOCOLOS.md:387 (#protocolo-de-insercao-humana-continuado-decisao-do-humano-18112026)
Porta de entrada: a skill `agata-mapear-humano` (`.agents/skills/agata-mapear-humano/SKILL.md`), obrigatória para todo modelo. Literal do Humano, 18/11/2026 18:44: "criaremos uma skill obrigatória que vai mapear o humano, seguindo as regras do sistema, o humano é outra LLM, sendo treinada pelo agata, para aprender viver em harmonia com o meio e com o mistério." 18:45: "canônico, como todas as outras skills, abrindo o protocolo de inserção humana continuado."

### Quarentena estrutural (P-8) — PROTOCOLOS.md:401 (#quarentena-estrutural-p-8)
Texto completo: `propostas/README.md`. Fluxo prático: skill `agata-aplicar-proposta`.

### Doutrina de defesa proporcional — PROTOCOLOS.md:409 (#doutrina-de-defesa-proporcional)
Os princípios desta doutrina ficam no PROJETO.md, seção "Princípios" (índice). Aqui fica o formato de pedido de decisão:

### Decisor local — PROTOCOLOS.md:415 (#decisor-local)
Desde 13/10/2026 (655), decisão do Humano: modelos de decisão no estilo Jev rodando na Máquina, "onde der", **com o risco assumido por escrito (656)** contra 7 pareceres do Conselho Remoto (3 famílias: 2 "não", 5 "condicional"; o ponto mais contestado foi o roteador, por reabrir (383)/(416)). `ollaya` (contêiner `ghcr.io/ollaya-dev/ollaya` 0.13.0, CPU, pinado por digest, `:11435` loopback, `--memory=8g --cpus=8 --oom-score-adj=1000` — sem swap, ele é o primeiro a morrer se a RAM acabar), modelo `winnow:e4b`. Cliente único: `redesign/router/decisor.py` (`--selftest`). Um modelo de decisão não gera texto: recebe o texto e perguntas tipadas (`choice`, `score`, `noul`) e devolve probabilidades.

### Estado de publicação — PROTOCOLOS.md:426 (#estado-de-publicacao)
Repositório **público**, por decisão registrada do Humano — foi isso que queimou o nonce; consequência conhecida, não acidente. O estado de publicação não se afirma por este texto: mede-se em cada sessão (`sync`, `PROTOCOLOS.md`). Se o remoto ficar atrás, o executor trabalha com os arquivos entregues pelo Humano e declara a origem.

### Ferramenta embutida: selar.sh (Fase 4) — PROTOCOLOS.md:430 (#ferramenta-embutida-selarsh-fase-4)
`scripts/selar.sh` sela arquivos em `SELOS.txt` (sha256); `--check` dá exit 1 sem `SELOS.txt` ou com arquivo violado ("VIOLADO"), exit 0 com tudo íntegro. É o P-14 sobre as camadas frias de MEMÓRIAS.

### Memória em duas camadas — PROTOCOLOS.md:434 (#memoria-em-duas-camadas)
**Camada local** — Obsidian sobre o próprio repositório git: offline, privada, é **FATO**. **Camada nuvem** — NotebookLM e afins: processamento de fonte bruta, é **RELATO/projeção**. Nunca recebe canon e nunca vira cérebro do sistema.

#### Esfera pessoal — PROTOCOLOS.md:439 (#esfera-pessoal)
`memoria/missoes/segunda-camada/` é a esfera local e privada do Humano. Sem remote, não sobe para serviço externo nenhum. Pode conter o que só existe nesta Máquina: hardware, rotina, configuração local, assunto pessoal. Modelos locais consultam sob demanda; modelos em nuvem não veem.

#### Esfera do projeto — PROTOCOLOS.md:442 (#esfera-do-projeto)
`memoria/missoes/agata-sistema/` é a esfera de trabalho do sistema, vinculada a uma conta Google Workspace **dedicada ao projeto** — nunca a conta pessoal do Humano. Recebe material do sistema que o Humano autorize, e pode ser consultada por modelos externos sob autorização.

#### Fronteira — PROTOCOLOS.md:445 (#fronteira)
Só o não-sensível sobe. Conteúdo público sobre o sistema pode ser usado na esfera do projeto; os arquivos canônicos não sobem como canon. Dado que só existe nesta Máquina, ou que pertence ao domínio pessoal, fica na esfera pessoal. Segredo, chave e credencial nunca sobem para esfera externa nenhuma.

#### Fronteira mecânica — `subir_esfera_projeto.py` — PROTOCOLOS.md:450 (#fronteira-mecanica-subiresferaprojetopy)
Único cano de código entre o sistema e o Drive: um arquivo por invocação, 8 checagens em ordem (caminho, esfera pessoal, canon, é arquivo, extensão, tamanho, UTF-8, varredura de segredo) e aborta na primeira que falhar; não é allowlist. Texto: `extras/projeto-detalhe/memoria-duas-camadas.md`.

#### Índice derivado do canon público e export pro Drive — PROTOCOLOS.md:453 (#indice-derivado-do-canon-publico-e-export-pro-drive)
Camada de consulta separada do vault, gerada só do canon público (`gerar_indice_derivado.py`), exportada ao Drive só quando o sha256 do `indice.md` muda (post-commit, fail-soft). Ver `extras/projeto-detalhe/memoria-duas-camadas.md`.

#### Mão única refinada — PROTOCOLOS.md:456 (#mao-unica-refinada)
**Nenhum resultado externo tem autoridade automática para escrever no canon.** A esfera do projeto pode produzir síntese, análise ou proposta; nada disso é escrita de fato. Resultado processado só influencia o canon pelo fluxo normal: proposta explícita, decisão do Humano, verificação pela Máquina quando aplicável, registro em MEMÓRIAS, commit. A autorização do Humano permite a incorporação; não dispensa verificação nem registro.

#### Postura sobre uso dos dados pelo Google — PROTOCOLOS.md:459 (#postura-sobre-uso-dos-dados-pelo-google)
O Humano autoriza o uso dos dados da esfera do projeto nos serviços Google escolhidos, incluindo eventual uso para melhoria ou treinamento **quando os termos daquele serviço assim previrem**. É postura declarada do Humano, não alegação sobre o que a Google faz. Dados da esfera pessoal nunca são usados para isso, porque nunca sobem.

#### ACB — reversão parcial de (223) — PROTOCOLOS.md:462 (#acb-reversao-parcial-de-223)
Desde 27/08/2026, a exclusão do ACB vale só para assuntos pessoais e partes desnecessárias ao sistema. Assunto do próprio sistema pode voltar ao escopo com autorização explícita do Humano e o mesmo controle de proposta, verificação e registro.

#### Limitação conhecida — Conselho Remoto — PROTOCOLOS.md:465 (#limitacao-conhecida-conselho-remoto)
A esfera do projeto mora em `memoria/missoes/`, que casa com a Condição 1 do `scripts/conselho_remoto.py`: por mecanismo, não pode ser discutida com o Conselho Remoto. É a proteção funcionando. Mudar exige allowlist explícita ou mover a esfera — decisão do Humano.
