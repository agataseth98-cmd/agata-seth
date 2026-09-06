# MEMORIAS-MORNO.md — camada morna do sistema Agata

Gerado por scripts/migrar_periodo.py a partir de MEMÓRIAS.md (quente) quando entradas saem do orçamento de hidratação. Mesma garantia de MEMÓRIAS.md (Regra 4, append-only) — só muda ONDE a entrada mora, nunca o conteúdo dela. Ver REGRAS.md, "Como ler este arquivo".

---

<!-- ENTRADAS-NOVAS:AQUI -- não editar esta linha à mão) -->
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

