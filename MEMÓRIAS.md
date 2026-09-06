# MEMÓRIAS.md — Sistema Agata

**Você está lendo o arquivo de história. É append-only: nada se apaga, nada se edita — só se acrescenta.**
Desde a entrada (271) (26/08/2026), entrada nova entra logo abaixo do marcador `ENTRADAS-NOVAS` abaixo — mais recente primeiro, pra ler o estado herdado sem varrer a história inteira. Antes de (271) a ordem era o oposto (mais antiga primeiro, mais recente acrescentada no fim físico); motivo, autorização do Humano e portão das três perguntas cumprido: ver a própria entrada (271), logo abaixo do marcador. Correção nunca é edição — é entrada nova apontando a que corrige. Para o estado atual (não o histórico), leia PROJETO.md.

## Como ler este arquivo (para modelos)
- **Não leia tudo.** Leia o TOPO, logo abaixo do marcador — é o estado herdado mais recente. O resto é lastro, consultável por busca quando um número de entrada for citado.
- **Entrada citada por número** — `(n)` — pode ser buscada diretamente **a partir de (49)**. Toda regra e todo bug remetem a um número; é assim que se checa se algo é fato ou lembrança.
- **Cópia recebida pode estar atrás do canon.** Antes de escrever qualquer entrada nova, confira o TOPO do remoto (logo abaixo do marcador — não o fim físico, que agora é a história mais antiga). Se não puder conferir, diga até onde a sua cópia vai e não numere nada.
- **Grafias antigas do nome** (com acento, com "h") aparecem na história migrada. Não se corrigem: história não se edita. A grafia canônica hoje é **Agata**.

## Os quatro tipos de bloco
- `(n) DIÁRIO` — fato coletivo, comum a todos.
- `(n) CONSELHO` — entrada, saída ou discordância de modelo, mais o veredito do Humano.
- `(n) MOD <modelo>` — memória pessoal. **Silo:** cada modelo deveria receber só os MODs com o seu `modelo-alvo`. Consentimento de publicação é por trecho, com data; o default é privado.
  *Hoje o silo é norma, não mecanismo: a hidratação é arquivo único e sem filtro. Recebeu MOD alheio, diga em uma linha e não use o conteúdo.*
- `(n) CORREÇÃO` — corrige uma entrada anterior sem editá-la; aponta o número que corrige.

**Correção sobre este preâmbulo (MEMÓRIAS (109)): a numeração NÃO é única globalmente antes de (49).** História migrada de mais de uma origem reinicia número por número — "(2)" sozinho aparece pelo menos 4 vezes, em datas diferentes. A partir de (49) a numeração é única e contínua; antes disso, cite por número **e data**. O bloco migrado (mais antigo, no fim físico deste arquivo) segue colado verbatim, sem editar uma vírgula — isso não muda; o que mudou nesta migração foi só a posição do corpo (49)+ e a direção de leitura.

---

<!-- ENTRADAS-NOVAS:AQUI -- não editar esta linha à mão; ancora o controle P-5 em scripts/perimetro.sh; entrada nova sempre logo abaixo dela, nunca acima) -->
(356) DIÁRIO — 06/09/2026 · Discordância sintética (item 2 do backlog reordenado em (355)): checagem mecânica do relógio de 4 semanas (P-13) implementada + convenção `SINTÉTICO: true` documentada em REGRAS.md — achado, no caminho, que uma estimativa anterior de urgência estava errada

**Pedido do Humano:** "Autorizado, vai." — depois de "varredura primeiro" e do portão das três perguntas cumprido (Reversibilidade: `git revert` limpo; Alcance: um script novo + uma chamada nova em `scripts/perimetro.sh` + um parágrafo em REGRAS.md; Silêncio: não é silencioso, o aviso aparece em toda corrida de `perimetro.sh`). Escopo confirmado como só mecânico — "como provocar uma discordância" fica de fora, julgamento editorial, não automatizado hoje.

**Achado que corrige uma varredura anterior, antes de publicar como fato.** Uma checagem de texto (`grep`) rodada antes desta entrada, no mesmo dia, tinha achado (85)/(109) — 11/08 e 12/08/2026 — como a última entrada CONSELHO relevante, e daí 25-26 dias decorridos, "faltando 2 dias" pro relógio de 4 semanas. Escrevendo o script de verdade contra o corpo inteiro das entradas (não só o título), achei (276) CONSELHO — 27/08/2026: Modelo B, ali, "discorda de 'não há divergência canônica real'" — uma discordância real, registrada, mais recente que a que a varredura anterior tinha achado. Consequência: hoje são **10 dias** decorridos desde a última discordância real, não 25-26 — o relógio não estava perto de disparar, e eu quase teria registrado essa falsa urgência como se fosse achado de Máquina. Corrigido antes de virar entrada, não depois.

**`scripts/checar_discordancia.sh` (novo).** Mesmo padrão de `checar_citacao.sh` (Python embutido via heredoc, sourceável sem executar): varre entradas rotuladas `CONSELHO` em MEMÓRIAS.md, filtra as que contêm a raiz `discord` no corpo (cobre discordância/discorda/discordou; não colide com `concorda`/`concordância`, que não contêm `discord`), pega a de maior número (mais recente), calcula dias desde a data no título. Silencioso se < 28 dias; se ≥ 28, imprime um `AVISO` nas três partes exigidas (o que aconteceu, por que importa, o que fazer) e sai 1 — mas o chamador em `perimetro.sh` trata como AVISO SÓ, nunca falha, mesma doutrina de P-6/P-9. Bootstrap (nenhuma discordância real jamais registrada) sai silencioso, mesma lógica do bootstrap de P-10.

**Testado nos dois sentidos antes de considerar pronto.** Contra MEMÓRIAS.md real: silencioso, exit 0 (10 dias). Contra um arquivo sintético com uma entrada CONSELHO datada de 67 dias atrás contendo "discorda": disparou o `AVISO`, exit 1, texto conferido item a item contra o formato exigido.

**REGRAS.md, convenção nova perto do item 4 do Conselho:** campo estrutural `SINTÉTICO: true`, numa linha própria perto do bloco de fechamento `Modelo: ... vetor: ...`, obrigatório em qualquer entrada de discordância provocada de propósito pelo relógio de P-13 — nunca em discordância espontânea, e nunca marcado numa discordância espontânea só pra "contar" pro relógio (inverteria o propósito: fricção real virando teatro de fricção). Texto completo em REGRAS.md, "O Conselho", logo após o parágrafo da Fase 2.

**Verificação:** `bash scripts/checar_discordancia.sh` isolado, dos dois lados (silencioso contra o real, `AVISO` contra o sintético) — `exit $?` conferido nos dois casos, não só a saída impressa. `bash scripts/perimetro.sh` inteiro, antes e depois de source-ar o script novo → `RESULTADO GERAL: OK`, P-13 aparece com `veredito: AVISO SÓ (nunca falha)`, silencioso (10 dias reais, não os 25-26 estimados antes). Recontagem manual de `(276)` linha por linha, corpo completo lido, antes de aceitar como o candidato certo — não só a saída do script.

Três arquivos sob quarentena P-8: `REGRAS.md`, `scripts/perimetro.sh`, `scripts/checar_discordancia.sh` (novo). Par `.diff`/`APROVADO-` em `propostas/aplicadas/discordancia-sintetica` — `.diff` preparado por mim; `APROVADO-` criado pelo Humano, não por mim, confirmado no disco (`ls -la`) antes de eu prosseguir.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: leitura do corpo completo de `checar_citacao.sh` antes de escrever o script novo no mesmo estilo; teste isolado do script nos dois sentidos (real e sintético), `exit $?` conferido, não só a saída; `bash scripts/perimetro.sh` real antes e depois; recontagem manual do corpo de (276) antes de aceitar como a entrada certa, corrigindo a varredura anterior em vez de repetir o erro dela. Autorização: Humano, "Autorizado, vai." Turno desta sessão: retomado após compactação de contexto — contagem de turno não confiável a partir daqui, não registrada por número.

(355) DIÁRIO — 06/09/2026 · Item "GLM membro pleno" do Ponto Cego fechado sem implementar — superado pela própria decisão de (352); WhatsApp removido do backlog por ordem do Humano; ordem dos 5 itens restantes redefinida (MEMÓRIAS por período sobe uma posição)

**Pedido do Humano:** "removemos o whatsapp e faremos o restante, e subiremos memórias por periodo uma posição, vai" — confirmando também o fechamento do item GLM proposto na resposta anterior.

**GLM membro pleno — fechado por contradição doutrinária, não por falta de tempo.** O item original (Fase 3 do "Plano vigente", `PROJETO.md`) pedia promover GLM a membro pleno do Conselho — bloco MOD próprio, hidratação completa, entrando no contexto de outros modelos. A decisão registrada em (352) ("ninguém tem papel fixo... revogo GLM... rotação justa entre modelos grátis") vai na direção contrária: nenhum modelo específico é promovido, todos competem pela vez. Implementar "GLM membro pleno" agora contradiria a própria doutrina que o Humano acabou de fixar no mesmo dia — fechado sem implementar, `PROJETO.md` marcado `[SUPERADO]`, texto original riscado (não apagado — Regra 4), motivo registrado ali mesmo.

**WhatsApp removido do backlog, por ordem direta.** Não implementado, não fica mais como pendência — o achado do "Ponto Cego" sobre risco de ban de conta pessoal (sem API oficial gratuita, ao contrário do Discord) segue registrado ali como o motivo mais provável da remoção, não confirmado como causa explícita nesta mensagem do Humano — não presumo o porquê além do que foi dito.

**Ordem dos 5 itens restantes, atualizada:** discordância sintética → **MEMÓRIAS por período** (subiu de 4º pra 3º lugar) → Home Assistant → réplica Windows. Home Assistant desceu uma posição, réplica Windows continua por último.

**Verificação:** `bash scripts/perimetro.sh` → sem FALHA. Nenhuma verificação de Máquina aplicável além disso — é registro de decisão do Humano, não achado técnico.

Um arquivo sob quarentena P-8: `PROJETO.md`. Par `.diff`/`APROVADO-` em `propostas/aplicadas/fecha-glm-membro-pleno` — `APROVADO-` criado pelo Humano.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: nenhuma verificação técnica nesta entrada além do perímetro — é registro fiel de decisão do Humano, sem inferir motivo além do dito. Autorização: Humano, "vai" confirmando a proposta anterior + a reordenação nova. Turno desta sessão: t=34 (contado no contexto).

(354) DIÁRIO — 06/09/2026 · Item 2 do "Ponto Cego" fechado — §4.2 (item aberto desde (309)) redigido, mandado pra segunda opinião pela rotação nova, auditado antes de aceitar (achou erro real meu), aplicado em REGRAS.md com a emenda

**Pedido do Humano:** "manda" (o §4.2), depois "Aprovado, manda" (o texto que redigi), depois "Sim, aplica" (a emenda). Três autorizações distintas, cada uma sobre um artefato diferente — pedido do parecer, aceite do parecer, aplicação da emenda.

**Achado real antes de mandar: o texto do §4.2 não existe em lugar nenhum do repositório.** Procurado em REGRAS.md, `redesign/CANON-DELTA.md`, MEMÓRIAS, `extras/arquivo-redesign/AUDITORIA-01.md`, `redesign/LOG.md` — todo lugar só tem o PONTEIRO ("§4.2, armadilha de string do selo declarado pela interface, item aberto de (309)"), nunca o texto proposto de verdade. Ficou no documento externo da auditoria em nuvem de 01/09, nunca salvo no repo. Não mandei nada sem ter o texto — redigi um, com autorização explícita do Humano pra essa via específica.

**Texto redigido, revisado pelo Humano antes de sair.** Baseado no que os ponteiros descreviam: a "armadilha" é presença OU ausência da string retirada (`declarado pela interface, não verificável de dentro`) sendo lida como sinal de cuidado — nos dois sentidos, os dois são engano.

**Pedido formal montado no formato exato que REGRAS "Segunda opinião" exige** — proposta em itens, ponteiro pra objeções conhecidas (nenhuma registrada, primeira formalização), âncora de versão (última MEMÓRIAS lida + sha256 real de REGRAS.md no momento do pedido).

**A rotação de (352)/(353) travou de verdade, duas vezes seguidas — mesmo bug de (340), reproduzido, não hipotético.** Escolheu Gemini as duas vezes (contagem empatada, ordem do roster) e as duas vezes bateu no teto de 15s do OmniRoute (`RATE_LIMIT_EXECUTION_TIMEOUT`, HTTP 504) — o mesmo achado já registrado, agora confirmando que não foi acaso daquela vez. **Contornado manualmente, transparente, sem mudar a lógica de rotação nem penalizar o Gemini** (a falha dele não é culpa de ninguém — é o teto de infraestrutura) — chamei `openrouter/minimax/minimax-m3:free` direto, fora do fluxo automático do script, documentado como bypass manual no próprio registro `.json` salvo.

**Parecer recebido de MiniMax-M3 — auditado antes de aceitar, não aceito por confiança.** "Concorda com ressalva": os 3 pontos centrais da proposta validados (não revive a exigência; identifica o risco nos dois sentidos; ancora identidade onde Regra 1 já ancora). **A ressalva achou um erro real meu:** eu tinha escrito "centenas de entradas históricas" sem contar — `grep -c` real: **87 ocorrências**, não centenas. O modelo remoto pegou uma alegação minha não verificada antes de eu mesmo checar. Emenda proposta ("um volume substancial" em vez de "centenas") aceita depois de confirmar o erro, não antes.

**Aplicado em REGRAS.md**, logo após o parágrafo *Motivo* de Regra 1 — mesmo lugar sugerido na proposta original, com a ressalva do próprio MiniMax sobre "onde exatamente" respondida citando o parágrafo específico.

**Verificação:** busca real em 5 lugares do repositório antes de declarar o texto do §4.2 ausente; formato do pedido conferido contra REGRAS "Segunda opinião" linha a linha antes de mandar; `grep -c` real antes de aceitar a emenda, não confiado no parecer nem na própria memória; `bash scripts/perimetro.sh` → sem FALHA.

Um arquivo sob quarentena P-8: `REGRAS.md`. Par `.diff`/`APROVADO-` em `propostas/aplicadas/secao-4-2-armadilha-selo` — `APROVADO-` criado pelo Humano.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: busca real em 5 arquivos antes de declarar o §4.2 ausente, não assumido; pedido formal montado seguindo REGRAS "Segunda opinião" linha a linha, não de memória; `grep -c` real antes de aceitar a emenda do parecer — a ressalva dele só virou mudança depois de eu confirmar que ele tinha razão, não porque veio de fora. Autorização: Humano, três confirmações distintas ao longo do processo, citadas no topo desta entrada. Turno desta sessão: t=33 (contado no contexto).

(353) DIÁRIO — 06/09/2026 · Groq confirmado com free tier real (`WebSearch`, não memória de treino) e somado ao roster do Conselho Remoto — 4 modelos na rotação, não 3

**Pedido do Humano, depois de esclarecer que era "Groq" e não "Grok" (xAI):** "confirme Groq e de um acesso a ele."

**Confirmado de verdade, não de memória de treino — achado que valia a pena checar.** Meu corte de conhecimento é janeiro/2026; "hoje" é setembro/2026, 8 meses de distância — tempo o bastante pra uma política de free tier mudar. Rodei `WebSearch` (não assumi do que já sabia): Groq **tem free tier real, sem cartão** — 30 requisições/minuto, 6.000 tokens/minuto, 14.400 requisições/dia por organização, cobre **todos** os modelos suportados, incluindo `gpt-oss-120b` (o que já está registrado no OmniRoute desde P1-03). Fontes: eesel.ai/blog/groq-pricing, cloudzero.com/blog/groq-pricing, tokenmix.ai/blog/groq-api-pricing.

**Somado ao roster de (352).** `ROSTER` em `scripts/conselho_remoto.py` ganhou `groq/openai/gpt-oss-120b`, quarta entrada. Testado offline, 5 chamadas seguidas num estado temporário: os 4 modelos passam uma vez cada (round-robin correto), o 5º volta pro primeiro do roster — mesmo comportamento de (352), agora com 4 em vez de 3.

**`PROJETO.md` atualizado no mesmo lugar da entrada anterior** — a nota "Groq considerado, free tier não confirmado" virou "Groq confirmado 06/09/2026 via WebSearch real... fontes em MEMÓRIAS (353)".

**Sobre reaproveitar a aprovação de (352):** o `.diff` que o Humano tinha aprovado (`propostas/APROVADO-rotacao-conselho-remoto`) foi escrito ANTES desta adição — o conteúdo do par mudou depois do `touch`. Não tratei o marcador antigo como cobrindo a mudança nova por conta própria: regenerei o `.diff` com o conteúdo atual (rotação de 3 + Groq juntos, ainda não commitados desde (352)) e pedi confirmação de novo, mesmo nome de marcador — proporcional ao risco (mesma mecânica já aprovada, um item a mais no roster), não uma dança de portão nova do zero, mas também não uma reaprovação silenciosa.

**Verificação:** `WebSearch` real, 3 fontes cruzadas, não uma só; teste offline da rotação com 4 entradas, 5 chamadas, resultado conferido linha a linha.

Dois arquivos sob quarentena P-8, mesmo par de (352) ainda pendente: `scripts/conselho_remoto.py`, `PROJETO.md`. `.diff` regenerado em `propostas/rotacao-conselho-remoto.diff`; `APROVADO-` pedido de novo ao Humano antes de commitar.

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: `WebSearch` real em vez de responder da memória de treino, justificado pela distância real entre o corte de conhecimento e a data de hoje; teste offline real da rotação de 4 antes de considerar pronto; decisão explícita de não reaproveitar uma aprovação cujo conteúdo mudou, registrada como tal. Autorização: Humano, "confirme Groq e de um acesso a ele" — a confirmação em si (WebSearch) não precisava de portão (é investigação, não mudança); a mudança de código pede reconfirmação do `APROVADO-`. Turno desta sessão: t=32 (contado no contexto).

(352) DIÁRIO — 06/09/2026 · GLM revogado como modelo fixo do Conselho Remoto — ordem doutrinária do Humano ("ninguém tem papel fixo, o sistema tem razão"); `scripts/conselho_remoto.py` agora escolhe por rotação justa entre 3 modelos grátis confirmados, testado com pedido real

**Pedido do Humano, que começou como resposta ao item 2 do Ponto Cego (§4.2) e virou decisão maior:** "ninguém tem papel fixo, o sistema tem razão, revogo GLM" — depois, especificando: "deve ser decidido entre modelos gratuitos sob um regime de regras justas de rotatividade."

**A decisão aplica o próprio princípio-espelho do sistema a si mesma.** `redesign/ROADMAP.md` já dizia, desde a Fase 0 do redesenho: "os modelos são trabalhadores substituíveis; nenhuma ferramenta É o sistema." Até agora isso valia pra Hermes (removido em (312)), pra Open WebUI (trocado em (313)) — mas o GLM, como modelo do Conselho Remoto, tinha um papel fixo desde (182)/(206), nunca revisto sob esse princípio. O Humano fechou a lacuna.

**Investigado antes de desenhar — o pool real do OmniRoute, não assumido.** `redesign/router/PROVEDORES.md` mostra que "Conselho" hoje é prioridade fixa (`zai/glm-4.7-flash → gemini/gemini-2.5-flash`, `strategy=priority`), não rotação — mudar de verdade exigia sair da combo, não só trocar um nome. Candidatos com free tier **confirmado** no canon: `zai/glm-4.7-flash`, `gemini/gemini-2.5-flash`, `openrouter/minimax/minimax-m3:free`. Groq (`groq/openai/gpt-oss-120b`) considerado e **deixado de fora** — free tier não confirmado explicitamente em `PROVEDORES.md`, perguntado ao Humano antes de incluir, não presumido.

**Desenho, autorizado depois do portão das três perguntas (reversibilidade/alcance/silêncio, todas respondidas antes do "autorizado"):** `scripts/conselho_remoto.py` ganhou `ROSTER` (os 3 modelos), `escolher_modelo()` (menos usos bem-sucedidos primeiro, empate por ordem fixa do roster — determinístico, nunca aleatório, auditável), `_registrar_sucesso()` (só conta ponto se a chamada realmente teve sucesso — falha não penaliza, pra não afundar um modelo bom por um erro de rede isolado). Estado em `memoria/missoes/conselho-remoto/rotacao-estado.json` (mesma pasta que já guarda o backoff, local, gitignorado). **Invariante do script preservado, não quebrado:** continua UMA chamada externa por invocação — se o escolhido falhar, aborta como sempre abortou, não laça pra outro sozinho.

**Testado em duas camadas, não só "deve funcionar":**
1. **Lógica isolada, offline:** 4 chamadas seguidas de `escolher_modelo()`/`_registrar_sucesso()` num estado temporário — confirmado round-robin correto (zero→zero→zero→GLM, depois pula pro próximo cada vez, empate volta pro início do roster).
2. **Chamada real, com pedido de verdade:** rodei o script com um pedido de teste real — escolheu GLM (todos zerados), chamou o OmniRoute de verdade (`zai/glm-4.7-flash` direto, não mais a combo), recebeu resposta real (51+9=60 tokens, US$0), gravou o estado real (`{"zai/glm-4.7-flash": 1, "gemini/...": 0, "openrouter/...": 0}`). O "FORA DO FORMATO" que saiu depois é esperado — o pedido de teste não tinha as 4 partes de um parecer de verdade, não é falha do mecanismo de rotação.

**`PROJETO.md` atualizado, história preservada, não editada.** O parágrafo "Modelo escolhido: GLM-4.7-Flash" de 17/08 continua ali, verbatim — é fato histórico de quando a escolha foi feita, Regra 4 não permite apagar. Um parágrafo novo, antes dele, explica que foi superado por esta decisão, com a ordem do Humano citada.

**O que fica em aberto, nomeado:** Groq entra no roster se/quando o Humano confirmar o free tier dele — item separado, não decidido aqui.

**Verificação:** `py_compile` real; teste isolado da lógica de rotação (4 chamadas, estado temporário, resultado conferido linha a linha); chamada real ao OmniRoute com pedido de teste, estado de rotação real inspecionado depois; `bash scripts/perimetro.sh` → sem FALHA.

Dois arquivos sob quarentena P-8: `scripts/conselho_remoto.py`, `PROJETO.md`. Par `.diff`/`APROVADO-` em `propostas/aplicadas/rotacao-conselho-remoto` — `APROVADO-` criado pelo Humano, terceiro caso desde (346).

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: leitura real de `redesign/router/PROVEDORES.md` antes de desenhar o roster, não assumido de memória; teste isolado da função de rotação antes de rodar contra o sistema real; chamada real ao OmniRoute (não simulada) com inspeção do estado de rotação real depois. Autorização: Humano, "ninguém tem papel fixo... revogo GLM" + "decidido entre modelos gratuitos sob regime de rotatividade justa" + "Autorizado, aplica" depois do portão. Turno desta sessão: t=31 (contado no contexto).

(351) DIÁRIO — 06/09/2026 · Item 1 do "Ponto Cego" fechado — lacunas de P-8 em `redesign/grafo/*.py`/`*.sh` e `redesign/librechat/*.yml` cobertas, varredura real mostrou 17 arquivos afetados, nenhum trava retroativo

**Pedido do Humano:** primeira das 8 decisões de expansão, na ordem que o próprio Ponto Cego recomendou. "Varredura primeiro" — pedido antes de qualquer mudança.

**Achado corrigindo a própria proposta, antes de aplicar.** Minha primeira ideia (`redesign/grafo/*` inteiro) pegaria 22 arquivos, 5 deles documentação (`README.md`, `DURABILIDADE.md`, `dsh.md`, `paralelo.md`, `evals/README.md`) — exatamente o risco de "commit legítimo travado sem aviso" que o próprio Ponto Cego nomeou pra este item. Testado de verdade (`case` do bash casa `/` dentro de `*`, confirmado com teste isolado antes de propor): `redesign/grafo/*.py`/`*.sh` cobre subpasta (`flows/consolidacao.py` bate) sem pegar `.md`/`.gbnf`.

**Varredura real, mostrada ao Humano antes de qualquer edição:** 17 arquivos passariam a exigir aprovação (16 `.py`/`.sh` em `redesign/grafo/`, 1 `.yml` em `redesign/librechat/`) — nenhum com par `.diff`/`APROVADO-` prévio, confirmado um a um, então nenhum trava retroativamente commits já feitos.

**Aplicado, testado, aprovado pelo Humano — regime normal cumprido do início ao fim.** `_p8_eh_comportamento()` em `scripts/perimetro.sh` ganhou o padrão novo. Testado antes de pedir aprovação: `redesign/grafo/flows/consolidacao.py`/`rodar_par.sh`/`redesign/librechat/docker-compose.yml` → "EXIGE aprovação"; `redesign/grafo/README.md`/`envelope.gbnf` → "livre" — os dois lados confirmados, não só o caminho feliz. `.diff` preparado por mim; `APROVADO-fecha-lacunas-p8` criado pelo Humano (confirmado no disco antes de eu prosseguir, dois "pode"/"vai" do Humano não foram aceitos como equivalente ao arquivo até o arquivo existir de verdade).

**Verificação:** `git ls-files` real pra listar os 22 vs. os 17; teste isolado do `case` do bash antes de propor o padrão; `_p8_eh_comportamento` chamada real (fonte da função, não reimplementação) pra confirmar os dois lados depois de aplicar; `ls -la` real no marcador antes de seguir, duas vezes (a primeira ainda não existia). `bash scripts/perimetro.sh` → sem FALHA.

Um arquivo sob quarentena P-8: `scripts/perimetro.sh`. Par `.diff`/`APROVADO-` em `propostas/aplicadas/fecha-lacunas-p8` — `APROVADO-` criado pelo Humano, segundo caso desde (346) (o primeiro foi o Tailscale, (350)).

Modelo: Claude Sonnet 5 (Claude Code, na Máquina) · vetor: `git ls-files` real com os dois padrões antes de decidir qual propor; teste isolado do padrão bash antes de aplicar no arquivo real; chamada real da função (via `source` do trecho, não reescrita) pra confirmar os dois lados do comportamento; `ls -la` real no marcador, sem aceitar "pode"/"vai" como substituto do arquivo. Autorização: Humano, "Autorizado, pode aplicar" seguido do `APROVADO-` real. Turno desta sessão: t=30 (contado no contexto).

