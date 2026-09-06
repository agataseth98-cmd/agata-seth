# MEMORIAS-FRIO-2026-09-06-4.md — camada fria do sistema Agata (selada, imutável)

Congelado por scripts/migrar_periodo.py. Selado com scripts/selar.sh — SHA-256 registrado em SELOS.txt, tag de git aponta pro commit deste selamento. Depois de selado, este arquivo nunca mais recebe escrita — garantia é `scripts/selar.sh --check`, não mais P-5.

---

(204) DIÁRIO — 17/08/2026 · P-7 HABILITADO no pre-commit — crase vira exemplo protegido, segundo número no mesmo parêntese passa a ser validado, taxa de (203) recontextualizada como amostra pequena; esta própria entrada é o "verde uma vez" exigido antes de ligar

**As duas correções pedidas, implementadas e testadas isoladas antes de tocar no real:**

1. **Citação dentro de crases é EXEMPLO, pulada sem alarme.** `checar_citacao.sh` agora acha todo span entre crases no texto e ignora qualquer citação cujo intervalo inteiro caia dentro de um span — registrado também em REGRAS.md, "Citação de MEMÓRIAS — primeira referência". Teste positivo (citação errada, dentro de crases) → não marcou, `pulados_exemplo=1`. Teste negativo (a MESMA citação errada, sem crases) → marcou `SUSPEITO` normalmente — crase não é escudo universal, só de exemplo real de formato.

2. **Segundo número no mesmo parêntese passa a ser validado.** Síntese composta (`(194 - ...; 196 - ...)`) agora divide em `; ` só quando seguido de outro `N - `, e valida cada par separado contra sua própria entrada. Teste com dois pares válidos + um número inexistente no meio → achou os dois válidos limpos, marcou só o inexistente, `total_citacoes=4`.

**Correção sobre a própria motivação do pedido — não escondida:** a citação-exemplo achada dentro de (162 - hora obrigatória no cabeçalho e formato de citação com síntese, ordem direta do Humano) **não está entre crases** no texto real (é uma transcrição entre aspas duplas da fala do Humano, não formatação de código) — conferido de novo, linha 2359 de MEMÓRIAS.md. A exceção de crase, portanto, **não protege essa instância específica** se ela fosse rescaneada. Isto não invalida a correção: o motivo estrutural continua de pé (uma entrada que MOSTRA uma citação-exemplo — como esta própria, como (203 - P-7 implementado e testado, taxa de falso positivo 1 em 5 contra o corpus real) — precisa poder fazer isso sem alarme, e (203)/REGRAS.md realmente usam crase pra isso). O que resolve (162) na prática é outra coisa, já verdadeira desde o desenho original: **P-7 em produção só olha o que o commit ACRESCENTA a MEMÓRIAS.md (`git diff --cached`), nunca reaudita o arquivo inteiro** — (162) é história congelada, nenhum commit futuro a rescaneia, com ou sem crase. A auditoria de (203) contra o corpus inteiro foi um modo especial, manual, não o modo de produção.

**Ponto 3, sem mudança de código, registrado como pedido:** o limite da palavra genérica (uma palavra comum compartilhada deixa passar citação de assunto errado, achado em (203)) fica como está. Checador generoso é a escolha certa — travar um commit honesto é pior que deixar passar uma citação rara.

**Ponto 5, a taxa recontextualizada — números exatos, não a aproximação:** a "taxa 1/5" de (203) vem só das **5 citações reais do corpus** (o formato `(n - síntese)` só existe desde (162), corpus pequeno por desenho, não por amostragem reduzida). Somando os testes sintéticos que exercitaram o checador na mesma sessão — 3 citações no arquivo de teste positivo, 3 no negativo — o total de citações que passaram pelo checador até agora é **11** (5 reais + 6 fabricadas para teste), não as ~15 lembradas. Mais da metade é caso de teste, não produção real. **Registrado como está: o checador nunca foi exercitado contra volume real de commits — a prova real começa a partir de agora, com P-7 no hook.**

**HABILITADO:** `perimetro.sh` ganha P-7 (função `p7_citacao`, entre P-5 e P-6), chamando `checar_citacao` contra só as linhas que o commit acrescenta a MEMÓRIAS.md. `.githooks/pre-commit` já roda `perimetro.sh` inteiro — nenhuma mudança no hook em si, P-7 entra automaticamente por já fazer parte do script que o hook chama.

**O "verde uma vez" exigido antes de ligar é esta própria entrada:** ela mesma carrega citação real de (162) e (203), com síntese, fora de crase — o par que P-7 tem de validar contra o conteúdo de verdade de cada entrada, não contra texto sintético — mais os exemplos de formato entre crases (`(194 - ...; 196 - ...)`) que P-7 tem de pular. Comitar esta entrada com P-7 já ativo, e passar limpo nas duas coisas ao mesmo tempo, é o teste verde exigido antes de ligar.

Modelo: Claude Sonnet 5 · vetor: (162) relido linha a linha antes de afirmar se tem ou não crase — não assumido pela lembrança da entrada (203); os dois testes (crase protege/crase não é escudo universal, multi-citação com número inexistente) rodados isolados antes de tocar em `perimetro.sh`; `perimetro.sh` rodado contra o repositório real sem nada staged pra confirmar que P-7 não quebra com `MEMÓRIAS.md` vazio de diff (retorna OK, `total_citacoes=0`); contagem de 11 citações exercitadas recontada a partir dos dois arquivos de teste reais, não estimada. Turno desta sessão: t=2 (contado no contexto).

(203) DIÁRIO — 17/08/2026 · P-7 (checagem de citação) implementado e testado, NÃO habilitado no hook — taxa de falso positivo medida contra o corpus real: 1 em 5 citações no formato `(n - síntese)`, achado explicado, não é defeito do canon

**Decisão do Humano que baliza tudo aqui:** não trocar a arquitetura de hidratação; fechar só a falha específica que a expedição RLM achou — a única fabricação confirmada em 240 respostas foi uma citação errada (atribuiu a (143) um erro que estava na (157)), e checar só existência não pega isso, as duas entradas existem de verdade. Desde (162) toda citação carrega uma síntese junto do número, e é essa síntese que dá o que checar. **Explicitamente NÃO decidido aqui se habilita:** ordem foi implementar, testar, rodar contra o corpus, reportar a taxa — propor, não decidir sozinho (Regra 3).

**Implementado:** `scripts/checar_citacao.sh`, função `checar_citacao <arquivo> [MEMÓRIAS.md]`, sourceável e standalone como os outros. Indexa toda entrada `(n) DIÁRIO/CONSELHO/CORREÇÃO/MOD` de MEMÓRIAS.md (só a partir de (49), mesma fronteira que o resto do canon já usa — antes disso o formato é `### `, história migrada, ambígua por desenho). Extrai citações no formato `(n - síntese)` do texto de entrada, e pra cada uma: entrada existe? alguma palavra significativa da síntese (≥4 letras, lista curta de palavras comuns descartada, comparação por prefixo de 5 caracteres pra tolerar flexão) aparece no corpo real de (n)? Nenhuma checagem de `(n)` sozinho — fora do escopo do P-7 (é outra regra, primeira referência).

**Dois desenhos de teste positivo/negativo, isolados, antes de tocar no corpus real:**
- Citações inventadas (`(9999 - entrada que não existe)`, `(108 - migração para Kubernetes)`, real assunto de (108) é publicação/checagem de segredo) → 2 de 3 marcadas `SUSPEITO`, a terceira (`(198 - correção de bug de VRAM na GPU do Predator)`) **passou por engano** — achado real, não escondido: a palavra "correção" aparece de verdade no corpo de (198) por coincidência temática (198 fala de "correção" absorvida/não absorvida pelo Seth), então uma palavra comum genérica basta pra "generoso" deixar passar uma citação de assunto errado. Tradeoff aceito por desenho — o pedido foi generosidade contra falso positivo, não detecção perfeita.
- Citações reais e coerentes (`(198 - achado sobre o Seth)`, `(196 - achado que motivou a página de onde estamos)`, `(194 - mecanismo root do P-2)`) → 3 de 3 passaram limpo, `exit=0`.

**Rodado contra o corpus real (MEMÓRIAS.md inteiro, ~197 entradas), como ordenado — a taxa:**
Primeira rodada achou 14 "citações", 7 suspeitas — **maioria falso positivo do próprio regex**, não do julgamento de conteúdo: `(2026-07-02)`, `(45-97% de utilização...)`, `(6-7)` são datas e faixas numéricas, não citações — o padrão `\(\d+\s*-\s*...\)` casava com qualquer hífen entre parênteses. **Corrigido:** citação real sempre tem espaço dos dois lados do hífen (`(101 - síntese)`); data/faixa nunca tem (`2026-07-02`, `45-97%`). Regex trocado pra `\((\d+) - ([^()]+)\)`, exigindo os espaços. Re-rodado: **5 citações reais no formato `(n - síntese)` existem hoje no corpus inteiro** (a convenção só vale desde (162), corpus pequeno por isso, não é amostra artificialmente reduzida) — **1 suspeita, taxa 1/5 (20%)**.

**A 1 suspeita, examinada — não é defeito do canon:** `(101 - Investigação de Crashes locais)`, dentro do corpo de (162), não é uma citação real da entrada (101) — é o **exemplo ilustrativo** dentro da ordem literal do Humano que criou a própria convenção de síntese ("... ex: (101 - Investigação de crashes locais), adaptado para o contexto"), citada em (162) como transcrição direta do pedido. O conteúdo real de (101) é outra coisa (mitigações de (99) reaplicadas). **Achado, registrado como limitação conhecida, não corrigido:** o checador não distingue "citação real" de "exemplo de formato dentro de uma instrução citada" — isto reprova um trecho do canon que está certo, exatamente o caso que a doutrina de defesa proporcional avisa ("se isto reprovar o próprio canon, a checagem está errada, não o canon").

**Lacuna adicional, não corrigida:** uma síntese composta cita mais de um número dentro do mesmo par de parênteses (`(194 - Parte A: ...; 196 - Fase 1 instalada e confirmada real)`, entrada (201)) — o checador valida (194) contra a síntese inteira, mas não extrai nem valida (196) separadamente. Passou sem alarme porque as palavras de (194) já bastam; cobertura de (196) nesse caso é `lacuna`.

**Proposta ao Humano, não decisão:** a taxa medida (20%, n pequeno) tem UMA causa entendida (exemplo ilustrativo dentro de citação) e ZERO causa por julgamento errado de conteúdo genuíno — as 4 citações reais passaram limpo, e o teste sintético mostrou que o lado gracioso funciona (não bloqueia paráfrase legítima) e tem o limite esperado (uma palavra genérica compartilhada deixa passar erro grosseiro). **Não habilitado em `perimetro.sh`/pre-commit nesta entrada** — decisão de habilitar, e se antes disso vale tratar o caso do exemplo ilustrativo, fica com o Humano.

Modelo: Claude Sonnet 5 · vetor: cada match do regex conferido contra o texto-fonte real antes de aceitar como citação (não assumido pelo achado do script); os 7 falsos positivos da primeira rodada abertos um a um pra achar a causa raiz (espaço no hífen), não descartados como "ruído"; a 1 suspeita da rodada final rastreada até (162) e comparada linha a linha contra o texto de origem antes de declarar "não é defeito do canon" — não aceito por leitura corrida. Turno desta sessão: t=2 (contado no contexto).

(202) DIÁRIO — 17/08/2026 · Três avisos confusos de (196) corrigidos — as três propostas apresentadas ao Humano nesta sessão, aprovadas com acréscimo dele; princípio novo registrado — todo alarme diz o que aconteceu, por que importa, o que fazer

**As três, aprovadas, testadas positivo/negativo em repositório descartável antes de tocar no real, depois checadas ao vivo contra o repositório de verdade (só leitura, nenhum controle desligado pra testar):**

1. **Alarme de segredo (P-1) passa a nomear o arquivo.** Antes processava o diff staged inteiro concatenado; agora itera arquivo por arquivo (`git diff --cached --name-only`), então cada `SUSPEITO (padrão: ...)` carrega `em <arquivo>`. Teste positivo (dois arquivos staged, só um com chave falsa): nomeou o arquivo certo, não confundiu com o limpo. Teste negativo (nenhum segredo staged): silencioso, exit 0.

2. **PARCIAL do P-4 ganha explicação e ação, acréscimo do Humano.** Antes só imprimia a palavra `PARCIAL`. Agora, sempre que roda sem root: `PARCIAL: rodando sem privilégio de administrador, não enxergo todos os processos -- não é falha, é o controle enxergando menos do que deveria. Para ver completo: rode de novo com sudo.` Testado isolado (positivo, sem root) e ao vivo contra o repositório real — apareceu antes de `veredito: PARCIAL`, na ordem certa.

3. **SUSPEITO do P-5 repete o motivo e ganha ação, acréscimo do Humano.** As duas variantes (arquivo encolheu, byte mudou) agora dizem `(P-5, nunca se apaga história)` na própria linha, e terminam com o que fazer — `Alguma linha foi removida. Restaure o arquivo antes de comitar.` (encolheu) ou `Um trecho antigo foi alterado. Restaure o arquivo antes de comitar.` (byte mudou, texto de ação não estava no pedido original, estendido aqui pra cobrir a segunda variante do mesmo controle, mesma lógica). Testado isolado, as duas variantes, mais o caso negativo (append real, só acrescenta) — silencioso, exit 0.

**Princípio do Humano, registrado como comentário no topo de `perimetro.sh`, junto às outras convenções de desenho do arquivo (SKIP/PARCIAL, sem correção automática):** todo alarme diz três coisas, nesta ordem — o que aconteceu, por que importa, o que fazer. As três propostas originais de (196) consertavam as duas primeiras; nenhuma trazia a terceira — é essa lacuna que o acréscimo do Humano fecha nas três, e que o comentário deixa como regra pra qualquer alarme futuro no mesmo arquivo.

**Fecha um dos três itens que `ONDE_ESTAMOS.md` (197) registrou como esperando o Humano.** Atualizado no mesmo commit.

Modelo: Claude Sonnet 5 · vetor: mensagem literal de cada alarme lida no código-fonte antes de propor qualquer redação (não hipotetizada); as três mudanças testadas positivo e negativo num repositório git descartável (`/tmp`, git próprio, apagado ao fim), nunca no repositório real; depois disso, `perimetro.sh` rodado contra o repositório de verdade em modo só-leitura (nenhum `git add`/commit alterando estado antes da checagem) pra confirmar que P-4 mostra a explicação nova sem quebrar nada — resultado 5 OK/1 PARCIAL/0 FALHA, igual ao estado conhecido antes da mudança. Turno desta sessão: t=2 (contado no contexto).

(201) DIÁRIO — 17/08/2026 · Doutrina de defesa proporcional, ADOTADA — texto curto no PROJETO (não em REGRAS); formato de pedido de decisão explicitamente NÃO canonizado ainda

**Decisão do Humano:** adotar a doutrina, cinco frases, em PROJETO.md — não em REGRAS.md, por ser critério de julgamento situacional (Regra 3: Humano decide), não regra universal de identidade/registro/hidratação como as sete regras existentes.

**Texto adotado, literal, PROJETO.md, nova seção "Doutrina de defesa proporcional":**
- Incidente é o que passa ao lado de um controle que o sistema declarou. O resto é risco de fundo: registra e segue.
- Defesa só entra se for mecânica e no limite. Vigilância humana permanente decai; mecanismo instalado não.
- Risco residual declarado é mais seguro que estado "seguro" não declarado.
- Fecha a classe, não o caso.
- Nenhuma checagem entra em hook antes de passar verde uma vez.

**Precedente concreto que já seguia esta doutrina antes dela existir por escrito:** a escolha da opção D sobre a A no mecanismo root de sudoers (194 - Parte A: P-2 lê status root em vez de tentar sudo -n -l; 196 - Fase 1 instalada e confirmada real) — recusou timer systemd permanente por desproporção, preferiu mecanismo orientado a evento. A doutrina nomeia agora o critério que já orientou aquela escolha.

**Explicitamente NÃO decidido aqui:** o formato de "pedido de decisão" (a estrutura desta própria conversa — itens numerados, marcador de aguardando, ordem de execução) não é canonizado. Roda informalmente mais algumas vezes; canoniza-se a versão que sobreviver ao uso, não a que foi inventada agora.

Modelo: Claude Sonnet 5 · vetor: PROJETO.md lido inteiro antes de escolher onde inserir (não REGRAS, por instrução direta); conferido que (194)/(196) descrevem de fato uma escolha por desproporção antes de citá-las como precedente, não citação decorativa. Turno desta sessão: t=2 (contado no contexto).

(200) DIÁRIO — 17/08/2026 · Convenção de data no título de entrada, resolvida — data do COMMIT, não de escrita; lacuna aberta em (178) fechada por decisão do Humano

**Decisão do Humano, registrada literal:** "o título de entrada usa a DATA DO COMMIT, não a data de escrita [...] é a única data que a Máquina prova; a de escrita é o que alguém digitou. E não exige julgamento quando a sessão vira a meia-noite." Escolhe a opção 2 das três propostas em (178 - divergência de data no título de (177), lacuna de convenção aberta, três opções sem escolha).

**Aplicado:** REGRAS.md, "Carregar e formatos", uma linha nova logo após o bloco de formato de cabeçalho — título de entrada de MEMÓRIAS usa a data do commit que a introduz no canon (`git log`), nunca a data de início da escrita. **Vale a partir da próxima entrada em diante** — a numeração desta mesma sessão, (198)/(199), já foi escrita hoje e comitada hoje, então não diverge; (200) é a primeira formalmente sob a regra escrita. **Título de entrada antiga não se reescreve** — (177) permanece como está, Regra 4 proíbe editar.

Modelo: Claude Sonnet 5 · vetor: REGRAS.md lido inteiro antes de editar, pra confirmar onde a lacuna vivia (nenhuma linha cobria título de entrada, só cabeçalho de resposta — (162) resolveu um problema adjacente, não este); edição direta de "Carregar e formatos"; verificação pós-push de hash de REGRAS.md, ver rodapé desta resposta. Turno desta sessão: t=2 (contado no contexto).

(199) DIÁRIO — 17/08/2026 · Levantamento do vazamento antigo de `memoria/USER.md`/`memoria/MEMORY.md` (só leitura, sem proposta de ação) — 0 forks agora, rastreado publicamente 01/07 a 15/08/2026 (45 dias), conteúdo descrito em uma linha por arquivo

**Ordem do Humano: levantar e reportar, sem propor ação — ele decide.**

**Forks, via API do GitHub, agora:** `gh api repos/agataseth98-cmd/agata-seth` → `forks_count: 0`, `network_count: 0`, lista de forks vazia (os dois números batem). Repositório público desde a criação (`created_at: 2026-04-20T13:41:37Z`).

**Janela de rastreamento público, via `git log --follow` cruzado com `git show --stat`:** `memoria/USER.md` e `memoria/MEMORY.md` entraram no rastreamento no commit `dcdbc9c` ("Fase 3 (parte 1): memória nativa do Hermes via symlink + .hermes.md auto-gerado"), 2026-07-01 20:32:39 -03. Saíram no commit `ec99a0b` (189 - Passo 2 do saneamento: memória nativa do Hermes sai do rastreamento público), 2026-08-15 19:02:19 -03 — diff do próprio commit confirma remoção real, não edição: `memoria/MEMORY.md | 19 -`, `memoria/USER.md | 9 -`, `.gitignore | 4 +`. **45 dias públicos.** Hoje, `git ls-files` confirma os dois fora do rastreamento atual.

**Conteúdo, uma linha cada, sem colar o texto — dado pessoal do Humano, ele já sabe o que é:**
- `memoria/USER.md` (9 linhas na última versão rastreada): preferências pessoais triviais, interesses técnicos ligados a modelos de IA, e uma nota de configuração sobre o formato de cabeçalho do Seth.
- `memoria/MEMORY.md` (19 linhas na última versão rastreada): trocas de boas-vindas entre GLM-5 e a identidade Ágata sobre a criação do sistema, mais anotações técnicas de verificação (achado real vs. alegação sobre "RETOMADA"/"ESTADO") e uma nota de avaliação de modelo.

**Sem proposta de ação, como pedido.** Fato registrado; 0 forks é foto de agora, não garantia permanente (mesma ressalva já em PROJETO.md, "Riscos conhecidos"). PROJETO.md e `ONDE_ESTAMOS.md` atualizados no mesmo commit com estes números.

Modelo: Claude Sonnet 5 · vetor: `gh api repos/.../forks_count` cruzado com `gh api .../forks` (lista vazia, bate com o contador); `git log --all --oneline --follow` para os dois caminhos, cruzado contra `git show --stat` do commit de saída pra confirmar remoção real; `git ls-files` hoje confirma ausência atual; conteúdo lido do commit pai de `ec99a0b` só pra escrever a descrição de uma linha, nunca colado nem persistido fora do disco local. Turno desta sessão: t=2 (contado no contexto).

(198) DIÁRIO — 17/08/2026 · Achado sobre o Seth (qwen3.5-9b-64k), relatado pelo Humano: absorve correção de forma/complexidade, não absorve correção de fato nem de formato do pedido — quatro respostas seguidas em produção, 16/08/2026

**Registrado como fato observado, sem juízo de valor sobre o modelo — ordem do Humano.** Busquei antes de escrever: nenhuma transcrição da sessão de produção de 16/08 com o Seth está em disco (`~/agata`, `memoria/missoes/`, pasta de relay no Desktop) — não é o mesmo material da expedição RLM ((163)-(187), (195 - análise pós-expedição: trace diffing, custo/resposta, hesitação)), que é outro contexto. **Este achado é relato direto do Humano, não confirmado por Máquina** — registrado como tal, sem alegar verificação que não fiz.

**O relatado, quatro respostas seguidas, 16/08/2026:**
- Corrigido sobre COMPLEXIDADE ("sem parsing, só rode os comandos") → absorveu: sumiram o parsing, a lógica quebrada e os erros de sintaxe.
- Corrigido sobre um FATO — `git ls-remote origin/main` não funciona, com a saída literal `fatal: 'origin/main' does not appear to be a git repository` mostrada a ela → não absorveu, manteve o comando errado nas respostas seguintes.
- Pedido explícito de FORMATO — "responda só com as três linhas de comando, sem Python, sem explicação" → não absorveu, respondeu com Python.

**Leitura proposta pelo Humano, não veredito:** correção de FORMA é absorvida; correção de FATO e de FORMATO DO PEDIDO, não. Consequência prática para delegação: pedir simplificação funciona; corrigir uma crença dela, não. Parente do achado B.3(a) da expedição (195 - análise pós-expedição RLM) — achar a prova e não concluir; aqui é receber a resposta e não usar.

Modelo: Claude Sonnet 5 · vetor: busca em `~/agata` (repositório e `memoria/missoes/`) e em `/home/orusoua/Área de trabalho/` por transcrição da sessão citada, nenhuma achada — achado registrado como relato do Humano, não como verificação própria; nenhum comando testado de novo nem repetido. Turno desta sessão: t=2 (contado no contexto).

(197) DIÁRIO — 16/08/2026 · `ONDE_ESTAMOS.md` criado, aprovado pelo Humano na primeira versão ("Perfeito", sem pergunta) e oficializado no canon — nome adotado: "Onde Estamos"; Regra 4 (REGRAS) e "Memória e hidratação" (PROJETO) passam a exigir que ele seja atualizado no mesmo commit de qualquer entrada de MEMÓRIAS que mude o estado

**Origem, direto do achado de (196):** a bateria de legibilidade não conseguiu veredito por controle porque faltava uma página que devolvesse contexto ao Humano em menos de um minuto. Este arquivo é a resposta a esse achado — não implementado por conta própria, o Humano pediu depois de ver o achado.

**Teste de aceite, como definido pelo Humano — ele lê, não o modelo:** primeira versão mostrada em texto, direto na conversa, antes de qualquer commit. Resposta: "Perfeito." Nenhuma pergunta de volta — passou de primeira, sem precisar de segunda rodada de redação.

**Nome oficial: "Onde Estamos"** — o Humano pediu pra eu escolher como chamar a página; adotado o próprio título do arquivo (`# Onde estamos`), sem inventar apelido novo — mais fácil de lembrar e de dizer em voz do que qualquer nome adicional teria sido.

**Regras de redação, como o Humano pediu, cumpridas na primeira versão:** português simples, frases curtas, uma tela, sem hash, sem caminho de arquivo, sem "conforme registrado em"/"verificado por"/"veredito", sem número de entrada como referência principal. Estrutura fixa: O que é isto · Onde estamos agora · Esperando você · Rodando agora · Quebrado · Última atualização.

**Oficializado no canon, dois lugares:**
- REGRAS.md, Regra 4: novo sub-item — toda entrada que muda o estado atualiza `ONDE_ESTAMOS.md` no mesmo commit, não como tarefa separada.
- PROJETO.md, "Memória e hidratação": registrado como quarto arquivo na raiz, explicitamente fora da hidratação (`.hermes.md` continua lendo só REGRAS + PROJETO + MEMÓRIAS, nenhuma mudança de código necessária — confirmado lendo `gerar-hermes-md.sh` antes de escrever isto, ele só cita os três arquivos por nome, não faz glob).

**Conteúdo desta primeira versão, resumido em si mesmo — não repetido aqui em detalhe pra não duplicar o arquivo:** limpeza de segurança concluída, regra sudo removida, expedição RLM concluída sem decisão de produção, teste de legibilidade concluído com o achado que gerou esta própria página. Três itens esperando o Humano: caminho de produção da expedição, as três propostas de redação de alarme de (196), e a decisão sobre a exposição antiga de `memoria/*.md`.

**Pergunta separada do Humano, respondida fora do canon, não uma decisão de projeto:** "Humanos são LLMs?" — musing genuíno, não pedido de pesquisa; ligado ao próprio achado desta entrada (o Humano perdendo contexto depois de dias de trabalho é o mesmo problema estrutural que hidratação/janela de contexto tentam resolver para um modelo). Não afirmado nem investigado aqui — comentário do executor na resposta à parte, não registro de fato do canon.

Modelo: Claude Sonnet 5 · vetor: `gerar-hermes-md.sh` lido de novo antes de escrever "nenhuma mudança de código necessária", não assumido; conteúdo da primeira versão mostrado ao Humano ANTES do commit, não commitado e apresentado depois como fato consumado — a ordem do próprio pedido ("mostre a ele" antes de "oficialize") seguida à risca. Turno desta sessão: t=19 (contado no contexto).

(196) DIÁRIO — 16/08/2026 · Fase 1 instalada pelo Humano (mecanismo root do P-2 ativo, `--` removido); Fase 2 (prova de legibilidade dos controles, Humano como instrumento) rodada — 6 de 8 itens dispararam de verdade, mas o achado não é por controle: o Humano não conseguiu dar veredito item por item depois de ler os seis blocos em sequência, achado maior que qualquer redação individual

**Fase 1, confirmada real, não alegada:** `checar-sudoers-root.sh` rodou como root, `veredito OK`, escreveu `/var/lib/agata/p2-status.json`. `perimetro.sh` rodado de novo (T5 "depois"): P-2 saiu de `SKIP` pra `OK` com timestamp real (`2026-08-16T11:59:58-03:00`) — a transição desenhada em (194) funciona contra o mecanismo instalado de verdade, não só contra mock. `~/agata/--` confirmado removido (`ls` -> "não existe"). Disparo do hook de pacman continua PENDENTE (T8) — nenhuma operação de pacote tocou `sudoers.d` ainda, não simulado.

**Fase 2, bateria de 8, documento completo em `memoria/missoes/prova-legibilidade-controles/PROVA_PRODUCAO.md` (commit local, mesma pasta):** T1 (segredo), T2 (P-3, `memoria/*.md` forçado), T3 (P-5, linha apagada do meio) e T6 (P-6, marcador forjado) dispararam como desenhado, em clone descartável (`git clone ~/agata /tmp/prova-agata`, restaurado entre cada item, apagado no fim). T4 (P-4 sem sudo vs. com sudo: `PARCIAL` -> `OK`, mesma seção, nada mais mudou) e T5 (P-2 antes/depois da Fase 1) confirmados no repositório real, só leitura.

**O ACHADO CENTRAL, palavras do Humano, sem suavizar:** depois de ler os seis blocos, "tinha perdido o fio do que estava sendo feito. Sem veredito individual." E, nomeando a causa: "as mensagens pressupõem contexto que o Humano não tem depois de dias de trabalho. O problema não é a redação de cada alarme — é a falta de uma página de 'onde estamos' em linguagem simples." **Isto redefine o que a bateria mediu:** a pergunta original era "cada alarme se explica sozinho", a resposta que veio foi sobre uma camada acima — não existe hoje um resumo em linguagem simples que deixe o Humano recuperar contexto ANTES de julgar um alarme técnico individual. Seis mensagens corretas no próprio controle viraram ilegíveis como lote, sem essa camada.

**Registrado como achado, não como alteração:** nenhuma "página de onde estamos" foi desenhada, proposta em formato de decisão ou implementada aqui. Fica pro Humano decidir se e como construir isso — fora do escopo desta entrada, que só registra o que foi encontrado.

**Três observações técnicas do executor, à parte do achado central, propostas de redação — não decisão:** T1 não nomeia o arquivo na linha `SUSPEITO` (só o número de linha); T4/PARCIAL não imprime nenhuma linha explicativa própria (só a palavra `PARCIAL`, diferente de T1/T2/T3 que explicam o achado antes do veredito); T3 (controle mais crítico) não repete "Regra 4/linha vermelha" na própria linha `SUSPEITO`, só no cabeçalho impresso segundos antes. Detalhe de cada uma no documento da missão.

**T7 (post-commit real, HD conectado):** avaliado no próprio commit desta entrada — saída literal registrada abaixo, no rodapé operacional, não neste corpo (a saída só existe depois que o commit acontece).

Modelo: Claude Sonnet 5 · vetor: T1-T3/T6 disparados de verdade em clone descartável, restaurado entre cada item (`git reset --hard` + remoção do arquivo de teste), nunca no repositório real; T4/T5 confirmados no repositório real só-leitura, sem desligar nenhum controle pra testar; identidade git local (`user.email`/`user.name`) configurada só dentro do clone, nunca `--global`, pra não tocar configuração do Humano; recusa de fabricar os vereditos item-por-item quando o Humano deu resposta global em vez disso — registrado como o achado é, não encaixado à força na tabela original. Turno desta sessão: t=16 (contado no contexto).

(195) DIÁRIO — 16/08/2026 · Parte B: análise pós-expedição sobre os traces já no disco (nenhuma célula rodada de novo) — documento em `memoria/missoes/rlm-3caminhos/ANALISE_POS_EXPEDICAO.md`, commit `a83bfaa` do repo local; achados de fato registrados aqui, leituras propostas ficam só no documento

**Escopo e regra:** bancada congelada, nenhuma pergunta mudou, nenhuma GPU. Script reproduzível `analise_pos_expedicao.py`, mesma pasta. Documento tem as 5 leituras propostas numeradas, sem veredito — não repetidas aqui (Regra: leitura mora na missão, fato mora no canon).

**B.1 (trace diffing, a dívida de (159)):** C1×C1b (mesmo modelo) convergem mais em SEQUÊNCIA de comandos (similaridade média 0,39) do que qualquer par com C4 (modelo diferente: 0,12 e 0,08) — mas em VOCABULÁRIO de comandos (verbos usados, sem importar ordem) C1×C1b compartilham 80%, contra 31%/27% dos pares com C4. C3 não entra na comparação de sequência — achado de instrumentação: o trace da biblioteca `recursive-llm` não grava comandos internos, só `n_eventos` (contagem).

**B.2 (custo por resposta certa, número que faltava):** tokens totais/3 rodadas — B0 1.404.465, C1 564.507, C1b 1.160.453, C4 261.587, **C3 não instrumentado** (schema não grava tokens, achado de lacuna, não custo zero). Latência total — B0 2.530,7s, C1 4.136,6s, C1b 3.502,3s, C4 507,9s, C3 3.624,9s (mas rodou com GPU compartilhada, não comparável 1:1, MEMÓRIAS (187) B.6). Custo/resposta-limpa em tokens (denominador = "limpos" já publicado em (186)/(187), não recalculado aqui): C1 20.908 · C1b 38.682 · B0 42.560 (46.816 líquido, retirando a 1 fabricação confirmada do denominador) · C4 43.598.

**B.3(a) (achou-mas-não-extraiu):** 3 casos em 45 combinações checadas (5 perguntas de prova literal × 3 células × 3 rodadas), todos a mesma célula/pergunta — **C1b, F1, as 3 rodadas**: evidência de ausência (busca literal por `(999)`) aparece na 3ª iteração, a célula segue buscando variações até a 12ª e nunca produz um "FINAL:" — esgota o teto sem concluir apesar da prova cedo.

**B.3(b) (hesitação):** 30 casos com gap>0 entre prova e conclusão, gap médio 2,7 iterações, máximo 9 (C1b/F1). **Nota que corrige a citação da ordem:** "prova na 4ª iteração" (F1/C1b) — meu critério (comando contendo o literal `(999)`, não a saída, porque a prova de F1 é negativa) achou a prova na **3ª** iteração, mais cedo que o citado; gap real medido é **9**, não 8. Divergência é do critério de detecção, registrada em vez de silenciada, e o padrão geral (F1/C1b é o caso mais extremo) se confirma de qualquer forma. C1 tem o mesmo padrão em F1 (prova na 3ª, conclusão na 10ª, gap 7) — achado novo, não estava na ordem.

Modelo: Claude Sonnet 5 · vetor: schema de cada trace lido linha a linha antes de escrever qualquer extrator, não assumido igual entre células (achando ao vivo que C3 tem schema próprio, sem tokens nem sequência de comando); heurística de "prova suficiente" corrigida ao validar contra o caso citado na ordem (F1/C1b) ANTES de generalizar — a primeira tentativa (achar termo na SAÍDA) não achava nada em F1 porque a prova ali é ausência, não presença, e só apareceu depois de comparar contra o caso conhecido; checagem de robustez de "não-resposta" trocada de string "SEM RESPOSTA" (que não existe no trace) para "último `llm` não começa com FINAL:", validada rodando contra as 9 rodadas de C1/C1b/C4 antes de aceitar. Turno desta sessão: t=12 (contado no contexto).

(194) DIÁRIO — 16/08/2026 · Parte A: P-2 do `perimetro.sh` deixa de tentar `sudo -n -l` (SKIP estrutural sempre) e passa a ler status escrito por mecanismo root separado, orientado a evento (opção D do Humano — hook de pacman); dois artefatos preparados e testados isolados, instalação pendente do Humano (exige root); `--` reportado de novo, ainda não removido

**Decisão do Humano: opção D, hook de pacman.** B descartada (reabre a classe de (192); NOPASSWD sobre o próprio `/usr/bin/sudo` é primitivo de escalação desaconselhado pela documentação do sudo). A descartada por desproporção (timer permanente com privilégio pra vigiar condição que só muda quando um humano roda sudo).

**A.1(a) — `scripts/checar-sudoers-root.sh`, material de origem, testado isolado (positivo e negativo, mock de `sudo -l`, mesmo método de (181)/(190)/(191)):**
```
TESTE POSITIVO (sudo -l limpo, só "(ALL) ALL"):
  veredito OK, exit 0, status.json: {"veredito":"OK","detalhe":"","inspecionado":[]}
TESTE NEGATIVO (regra órfã mockada, mesmo padrão de (181)/(192)):
  veredito FALHOU, exit 1
  status.json: {"veredito":"FALHOU",
    "detalhe":"regra aponta pra caminho INEXISTENTE: /home/orusoua/acer-predator-turbo-and-rgb-keyboard-linux-module/keyboard.py",
    "inspecionado":["/usr/bin/python","/home/orusoua/..."]}
```
JSON validado com `json.load` real, não inspeção visual. **AUTOCONTIDO de propósito** — não faz `source` de nada em `~/agata`: um script que roda como root não pode depender de arquivo gravável por `orusoua`, seria recriar a classe fechada em (192). A lógica de inspeção é cópia pequena (~15 linhas) da mesma de `checar_sudoers` — duplicação deliberada pela fronteira de segurança, não descuido. SÓ LÊ E REPORTA, nunca edita sudoers. Destino final, instalação do Humano: `/usr/local/lib/agata/checar-sudoers-root.sh` (root:root, 0755).

**A.1(b) — `scripts/agata-sudoers.hook`, material de origem:** `[Trigger] Type = Path, Target = etc/sudoers.d/*, Operation = Install/Upgrade/Remove` · `[Action] When = PostTransaction, Exec = /usr/local/lib/agata/checar-sudoers-root.sh`. Destino final: `/etc/pacman.d/hooks/agata-sudoers.hook`.

**A.1(c) — `/var/lib/agata/p2-status.json`:** escrito pelo script acima a cada disparo — `timestamp` (ISO 8601), `veredito`, `detalhe`, `inspecionado`. Dono root, legível por `orusoua`, não gravável por ele (`chmod 0644`, `chown root:root` na escrita real como root).

**A.2 — `checar_sudoers` (P-2) reescrita, testada nos três estados possíveis, isolado, antes de rodar contra o repositório real:**
```
status ausente          -> SKIP, exit 0, PERIMETRO_ESTADO=SKIP
status presente, OK     -> OK,   exit 0, PERIMETRO_ESTADO="" (OK de verdade, não skip)
status presente, FALHOU -> FALHOU, exit 1, imprime o "detalhe" literal
```
**Semântica de idade, aplicada como pedido:** veredito positivo conta como OK **independente de quando foi escrito** — se nada tocou `sudoers.d` desde a última checagem, o resultado continua válido. Nenhum alerta por idade implementado. `perimetro.sh` rodado contra o repositório real, agora, sem o mecanismo instalado ainda: `4 OK · 1 SKIP · 1 PARCIAL · 0 FALHA` (P-2 ainda SKIP — `/var/lib/agata/p2-status.json` não existe nesta máquina até o Humano instalar).

**A.3 — cobertura que o hook não tem, registrada como runbook em PROJETO.md, "Sudo e interação humana":** edição manual via `visudo` não dispara pacman — `sudo /usr/local/lib/agata/checar-sudoers-root.sh` depois de qualquer `visudo`, sem maquinário novo.

**A.4 — `~/agata/--`, reportado de novo (mesmo achado de (193), ainda não resolvido):** `sudo rm ./--` (barra obrigatória), de dentro de `~/agata`. Nenhum irmão (já confirmado em (193), não re-testado agora — nada mudou na árvore desde então que justificasse repetir).

**A.5 — ACEITE, honestamente parcial nesta entrada:** instalação exige root, que o executor não tem — os dois artefatos estão prontos e testados isolados, não instalados. **Não afirmado como fechado.** Pendente do Humano: `sudo mkdir -p /usr/local/lib/agata && sudo install -o root -g root -m 0755 ~/agata/scripts/checar-sudoers-root.sh /usr/local/lib/agata/checar-sudoers-root.sh` · `sudo install -o root -g root -m 0644 ~/agata/scripts/agata-sudoers.hook /etc/pacman.d/hooks/agata-sudoers.hook` · rodar `sudo /usr/local/lib/agata/checar-sudoers-root.sh` uma vez pra semear o status.json (mesmo comando do runbook A.3) · disparo real do hook por pacman fica pendente de confirmação numa próxima operação de pacote (`pacman -Syu` de rotina serve, não é garantido que toque `sudoers.d` nesta rodada especificamente) — **isto não foi verificado nesta entrada porque não pode ser, sem root.**

Modelo: Claude Sonnet 5 · vetor: teste isolado positivo/negativo do script root ANTES de instalar no repo, com JSON validado por `json.load` real, não leitura visual; teste isolado dos três estados de `checar_sudoers` (ausente/OK/FALHOU) contra arquivos `.json` reais em `/tmp`, não assumido pela leitura do código; `perimetro.sh` rodado contra o repositório real depois da troca, confirmando SKIP continua (mecanismo não instalado), não alegado OK por engano. Turno desta sessão: t=11 (contado no contexto).

(193) DIÁRIO — 16/08/2026 · Três correções pós-saneamento, ordem do Humano: SKIP/PARCIAL vira terceiro/quarto estado no `perimetro.sh` (nunca somado a OK), auditoria dos 6 controles achou um segundo caso real (P-4 cego pra processos de UID alheio sem root); arquivo de dono root `~/agata/--` achado e reportado, não removido; PROJETO.md reconciliado com (183)-(192), zero aviso de reconciliação

**1.1 — SKIP e PARCIAL, terceiro e quarto estado, nunca somados a OK:** `perimetro.sh` agora imprime `veredito: SKIP` (checagem não rodou de verdade) ou `veredito: PARCIAL` (rodou, mas com visibilidade incompleta sem root) em vez de disfarçar os dois de OK — "verde que ninguém questiona é pior que checagem ausente" (ordem do Humano). Placar novo no resultado geral: `N OK · N SKIP · N PARCIAL · N FALHA`. Nenhum dos dois falha o hook — exigir root pra todo commit seria pior que a lacuna que sinalizam. Mecanismo: `PERIMETRO_ESTADO` (variável global, resetada antes de cada checagem, setada pela própria checagem quando não é OK de verdade), lido só por um ponto central (`_perimetro_veredito()`) que decide o texto e soma o contador — nenhuma chamada individual em `main()` decide isso sozinha.

**1.2 — auditoria dos 6 pelo critério "degrada em silêncio sem root?", rodada contra o repositório real:**
- **P-1** (segredo em staged diff) e **P-3** (`git ls-files`) e **P-5** (`git show`/diff de bytes) e **P-6** (marcador em `$HOME`): nenhum depende de privilégio, nenhum degrada. OK real.
- **P-2** (sudoers): já sabido, SKIP estrutural sempre que falta `sudo -n` não-interativo — nunca vai deixar de acontecer no hook normal.
- **P-4** (bind hermes/ollama): **achado novo, confirmado ao vivo, não suposto.** `ss -tulpn` sem root só atribui nome de processo a sockets do PRÓPRIO uid. `hermes-gateway` roda como `orusoua` (user unit) — visível. `ollama.service` roda como usuário de sistema dedicado `ollama` — **testado ao vivo:** a linha do `ss` pra `127.0.0.1:11434` (porta do Ollama) sai com endereço e porta, mas **nenhum texto de processo**, e o `grep -qiE "hermes|ollama"` do script nunca casa essa linha. Se o Ollama algum dia binder em `0.0.0.0` — exatamente o que P-4 existe pra pegar — rodando sem root o script não veria, porque a linha nunca entra no filtro. Corrigido: `p4_bind` marca `PERIMETRO_ESTADO="PARCIAL"` sempre que `id -u` ≠ 0, incondicional, porque não dá pra provar que nenhuma linha oculta era hermes/ollama sem o privilégio pra ver.
- **Rodado contra o repositório real, agora:** `4 OK · 1 SKIP · 1 PARCIAL · 0 FALHA` — P-1/P-3/P-5/P-6 OK, P-2 SKIP, P-4 PARCIAL.

**1.3 — fechamento pleno do P-2 (rodar em contexto root) é ALTERAÇÃO DE SISTEMA, proposta ao Humano separadamente, não implementada aqui** — formato de pedido de decisão completo, entregue fora deste registro (esta entrada só aponta que a proposta foi feita, não decide). Armadilha nomeada na proposta: um timer systemd como root executando código de dentro de `~/agata` (gravável por `orusoua`) reabriria a MESMA classe fechada em (192) — root executando script gravável pela conta do usuário. Se a proposta for aceita por essa via, o mecanismo tem que viver em caminho de sistema, dono root, não-gravável pelo usuário — nunca `~/agata/scripts/`.

**2 — arquivo de dono root `~/agata/--`:** achado ao checar `git status` desta sessão (não novo hoje — mtime 09:32, mesmo horário da tentativa de Passo 4 desta manhã). Conteúdo idêntico ao comentário que `passo4_editor_automatico.fish` escreve — leitura mais provável: teste manual do editor automático com argumento literal `--`, que o `printf ... > $argv[1]` tomou como nome de arquivo de saída. Risco nomeado pelo Humano: nome perigoso pra qualquer script que faça glob no repositório e passe nomes adiante (`--` vira terminador de opções pro próximo comando, silenciosamente). `find ~/agata -maxdepth 2 ! -user orusoua -not -path '*/.git/*'` rodado: **nenhum irmão**, só este arquivo. **Não removido — achado é achado, não faxina.** Reportado ao Humano com o comando exato (`sudo rm ./--`, barra obrigatória).

**3 — PROJETO.md reconciliado com MEMÓRIAS (183)-(192), zero edição em MEMÓRIAS (Regra 7, estado; Regra 4 intocada):**
- **Novo, "Sudo e interação humana":** fechamento da regra órfã (192) com decisão e opção 4 registradas; nota de que P-2 é estruturalmente SKIP (193).
- **Reescrito, "Riscos conhecidos" item da memória nativa do Hermes:** de descrição de risco de fundo pra **[PARCIAL]** — bypass fechado (189), exposição passada explicitamente **não** desfeita, `git rm --cached` interrompe só pra frente.
- **Reescrito, "Riscos conhecidos" item da expedição RLM:** de leitura intermediária pra **[FECHADO — EXPERIMENTO]** com os números exatos de (186)/(187) (5 células, 240 respostas, 1 fabricação) e citação de (184)/(185) — **cuidado aplicado:** o experimento fecha, a decisão de produção fica explicitamente ABERTA, as 5 leituras continuam PROPOSTAS, nada convertido em veredito.
- **Novo, "Riscos conhecidos":** item **[FECHADO]** do saneamento em 5 passos, citando (188)-(193).
- **Aceite mecânico, rodado de verdade:** `bash .githooks/gerar-hermes-md.sh` → **0 avisos de reconciliação** (era 10). Medida antes/depois: `.hermes.md` 96.302 B → **98.100 B** (+1.798) · `PROJETO.md` 26.949 B → **28.994 B** (+2.045, ~7,6%) · itens `[FECHADO]` 3 → **6** (uma variante `[FECHADO — EXPERIMENTO]`) · `[PARCIAL]` 1 → **2**. Crescimento vem só dos ponteiros novos exigidos pela reconciliação, não de detalhe histórico reinserido — cada item aponta pra MEMÓRIAS em vez de recontar.

Modelo: Claude Sonnet 5 · vetor: `ss -tulpn` rodado ao vivo, comparando a linha do hermes (mesmo uid, completa) contra a do ollama (uid diferente, sem processo) antes de aceitar a hipótese do Humano como achado, não só concordando com o texto da ordem; `find` real por donos ≠ orusoua antes de declarar "nenhum irmão"; `gerar-hermes-md.sh` rodado depois de cada edição em PROJETO.md, não só uma vez no fim, pra saber exatamente qual edição zerava qual aviso. Turno desta sessão: t=9 (contado no contexto).

(192) DIÁRIO — 16/08/2026 · Passo 4 (saneamento) FECHADO: regra sudo NOPASSWD órfã removida de `/etc/sudoers.d/facer` por decisão e execução do Humano; achado extra no caminho — permissão pré-existente errada (644) fazendo `visudo -c` reprovar, diagnosticado antes de qualquer conserto, ramo cosmético confirmado, resolvido com `install` atômico em 0440 root:root; `perimetro.sh` fechou 6/6 e foi amarrado ao pre-commit no mesmo commit desta entrada

**4.1 — o que saiu, texto literal (Regra 4):**
```
orusoua ALL=(ALL) NOPASSWD: /usr/bin/python /home/orusoua/acer-predator-turbo-and-rgb-keyboard-linux-module/keyboard.py
```
Arquivo: `/etc/sudoers.d/facer` — até esta entrada, o canon só conhecia a regra pelo conteúdo, nunca pelo nome do arquivo. `mtime` original 25/mai/2026 (bem antes da existência da Agata), sem pacote dono (`pacman -Qo`: "Nenhum pacote possui") — não volta sozinho num update.

**4.2 — decisão do Humano e motivo:** opção 1, remover. Não era poder novo — `orusoua` já tem `(ALL) ALL` padrão, que dá root com senha de qualquer forma. Era fricção removida de um caminho que o próprio controle declarado ("o executor pausa e pede sudo ao Humano", PROJETO "Sudo e interação humana") deveria pedagiar: o arquivo apontava pra um caminho sob `/home/orusoua/`, gravável pela mesma conta que roda o executor — quem escrevesse um arquivo ali virava root sem senha e sem prompt, contornando o controle sem precisar quebrá-lo.

**4.3 — opção 4, registrada como caminho seguro se o teclado RGB Acer voltar a ser usado:** instalar o script em `/usr/local/bin` (dono root, não gravável por `orusoua`), e só então recriar uma regra NOPASSWD apontando pra esse caminho fixo — nunca reintroduzir o primitivo de escrita em diretório do usuário.

**4.4 — achado extra, não previsto na ordem original: permissão pré-existente errada.** `stat` mostrou `/etc/sudoers.d/facer` em `644 root:root` (comparado a `10-installer`, no mesmo diretório, corretamente em `0440`/`r--r-----`). Ramo avaliado: dono root, sem bit de escrita pra grupo/outros → **cosmético**, não escalado como achado maior (o ramo grave seria modo com 2/6 no segundo/terceiro dígito ou dono ≠ root). `visudo -c` reprovava por causa dessa permissão, não por conteúdo malformado.

**4.5 — por que o primeiro `visudo -f` deu "sem alteração":** `visudo` só lê `SUDO_EDITOR`/`VISUAL`/`EDITOR` se `env_editor` estiver habilitado em `/etc/sudoers` — `grep -n env_editor /etc/sudoers` voltou vazio, ou seja a diretiva nem aparece (ausente = desligado, o padrão do sudo). Sem ela, `visudo` ignora as três variáveis e abre o `vi` compilado por padrão, que saiu sem tocar em nada — daí "sem alteração", e nada foi corrompido nisso: `visudo` aborta a instalação inteira quando detecta o arquivo temporário inalterado. O script determinístico de 15/08 (`passo4_remover_regra_sudo_orfa.fish`) não tinha bug de lógica — tinha uma suposição errada sobre qual variável de ambiente o `visudo` lê.

**4.6 — conserto, sem editor:** conteúdo novo montado fora de `/etc/sudoers.d/` (`/root/facer.new`, um comentário explicando a remoção, sintaxe válida, zero regra ativa), validado com `visudo -c -f` antes de instalar, instalado com `install -o root -g root -m 0440` (atômico, permissão correta desde a criação, sem passar por um estado intermediário errado). Confirmado depois: `visudo -c` limpo nos três arquivos do diretório (`/etc/sudoers`, `10-installer`, `facer`); `sudo -n -l -U orusoua` — rodado como root, listando o usuário certo, depois de uma primeira tentativa `sudo -n -l` simples ter mostrado por engano os privilégios de *root*, não os de `orusoua` — sem a regra órfã, só `(ALL) ALL` padrão, exige senha.

**4.7 — lição de classe, não incidente: backup dentro do próprio diretório de sudoers.** O script de 15/08 fez `sudo cp` do arquivo original pra um `.bak-passo4-<timestamp>` DENTRO de `/etc/sudoers.d/` — `sudo` lê todos os arquivos desse diretório por padrão. Só não reativou a regra porque o `#includedir` do sudo pula, por convenção, nomes com ponto ou terminados em `~` (proteção padrão contra arquivo de backup virar regra ativa sem querer). Ficou correto por essa convenção, não por desenho do script — vale lembrar em qualquer regra futura que precise de backup em `/etc/sudoers.d/`: nomear o backup fora do diretório, nunca confiar em sorte.

**4.8 — histórico de tentativas, registrado porque tentativa que falha também é história:** trabalho de 15/08 20:51–22:34 (5 capturas de conteúdo, os 2 scripts) não chegou ao canon antes da queda de energia da madrugada de 16/08 — achado só na retomada desta sessão (relatório de integridade pós-queda). Duas tentativas manuais via `nano` falharam por confusão de tecla antes da versão determinística. Artefatos movidos pra `memoria/missoes/passo4-sudoers-facer/` e commitados nesse repo local (commit `2e1c93d`) — ferramenta de uso único, o que é durável é o achado, registrado aqui, não o script.

**4.9 — decidido NÃO fazer, e por quê:** não versionar as ferramentas de uso único no repo público (superfície sem fechar classe nova — a classe já fecha com P-2 do `perimetro.sh`); não fazer varredura ampla de todo `/etc/sudoers.d/` além do que P-2 já cobre; não mexer em grupos do usuário. Sem incidente que motive qualquer um dos três, o custo de atenção não se paga agora.

**4.10 — perímetro, depois do fechamento, rodado de verdade contra o repositório real:**
```
P-1  Segredos só em ~/.hermes/.env, fora do repo — OK
P-2  O executor pausa e pede sudo ao Humano — OK
P-3  Publicação é decisão deliberada, consentimento por trecho — OK
P-4  api_server contido · Ollama restrito a 127.0.0.1 — OK
P-5  Registre e nunca apague — OK
P-6  Cópia da história fora desta máquina — AVISO SÓ (nada pendente agora)
RESULTADO GERAL: OK — 6/6
```
**Precisão que importa, pra não confundir skip com verificação:** o P-2 desta execução deu OK por *pular* a checagem — o shell do executor, nesta rodada, não tinha `sudo -n -l` não-interativo disponível ("sem acesso não-interativo agora"), e o desenho de (190) trata isso como aviso, não falha, pra não travar commit por incapacidade de checar. A confirmação real de que a regra sumiu **não veio deste run do `perimetro.sh`**, veio do `sudo -n -l -U orusoua` do item 4.6, rodado pelo Humano como root. Os 6/6 valem para amarrar no hook (o desenho de skip-não-falha já era decisão tomada em (190)/(191), não nova), mas quem fechou o Passo 4 de fato foi a checagem direta, não este script.

Amarrado ao `.githooks/pre-commit` no mesmo commit que registra este verde — princípio aplicado, decidido nesta sessão porque generaliza: nenhuma checagem entra em hook antes de passar verde uma vez. Portão que nasce vermelho ensina a ser contornado, e o contorno vira hábito.

Modelo: Claude Sonnet 5 · vetor: diagnóstico só-leitura antes de qualquer conserto (`stat`/`cat`/`ls`/`grep`/`pacman`, todos rodados pelo Humano, saída conferida por mim antes de ramificar entre cosmético e grave); reconhecimento em tempo real de que o primeiro `sudo -n -l` pós-conserto mostrou o usuário errado (root, não orusoua) e pedido de correção antes de aceitar como fechado; `perimetro.sh` rodado de novo contra o repositório real depois do conserto, não assumido 6/6 pela lógica — achando, ao rodar, que o P-2 desta vez passou por skip, não por reverificação, e registrando essa distinção em vez de deixar "6 OK" parecer mais forte do que é. Turno desta sessão: t=7 (contado no contexto).

(191) DIÁRIO — 15/08/2026 · Passo 5 (saneamento): `scripts/perimetro.sh`, 6 controles declarados, cada um testado com caso positivo e negativo em repo isolado — 2 bugs reais achados e corrigidos no processo (ARG_MAX estourado, `trap RETURN` vazando pra função seguinte). Primeira execução completa: 5 OK, 1 FALHOU (P-2, esperado — Passo 4 ainda não concluído pelo Humano)

**Desenho:** um script só, `scripts/perimetro.sh`, sourceável sem executar (mesmo padrão `BASH_SOURCE` guard de `varredura_segredo.sh`) — P-1 e P-2 importados de lá (`checar_segredo`, `checar_sudoers`, já testados em (190)), P-3 a P-6 novos. Cada checagem imprime o controle que defende e a fonte, como pedido. P-1 a P-5 falham (exit≠0); P-6 só avisa.

**Bug 1, achado ao rodar contra o repo real, não a bancada de teste:** `p5_append_only` passava o conteúdo inteiro do `MEMÓRIAS.md` (500 KB+) como argumento de linha de comando pro `python3` — estourou `ARG_MAX` ("Lista de argumentos muito longa"). Corrigido: escreve os dois lados em arquivo temporário, python lê do arquivo, só o caminho (curto) vira `argv`.

**Bug 2, achado na mesma rodada de correção:** `trap ... RETURN` dentro de `p5_append_only` não fica escopado só a ela — bash não limita isso por chamada de função, e o trap disparava de novo no retorno da função SEGUINTE (`cabecalho`, `p6_backup_pendente`), quando as variáveis temporárias já tinham saído de escopo, estourando "variável não associada" sob `set -u`. Corrigido: limpeza explícita em cada ponto de saída da função, sem `trap`.

**Testes isolados, positivo e negativo, cada controle novo (repo `/tmp` descartável, apagado depois):**
- **P-3:** negativo (`.gitignore` correto, nada rastreado) → OK. Positivo (`git add -f memoria/USER.md`) → FALHOU, aponta o arquivo exato.
- **P-4:** negativo (linhas `ss` sintéticas com hermes/ollama em `127.0.0.1`) → OK. Positivo (mesma linha, hermes em `0.0.0.0`) → FALHOU, aponta a linha exata.
- **P-5:** negativo (só append) → OK. Positivo 1 (byte antigo mudou) → FALHOU, aponta o offset e os dois trechos. Positivo 2 (arquivo encolheu) → FALHOU, aponta os dois tamanhos.
- **P-6:** negativo (marcador com timestamp de agora, 0 commits de distância) → sem aviso. Positivo A (marcador de 5h atrás) → avisa. Positivo B (marcador a 5 commits de distância, timestamp recente) → avisa. Limiar usado, sem número já declarado no canon pra isto: **mais de 3 commits OU mais de 2 horas**, documentado no próprio script — decisão de implementação desta sessão, não ordem explícita de número.

**Primeira execução completa, contra o repositório real, agora:**
```
P-1  Segredos só em ~/.hermes/.env, fora do repo — OK
P-2  O executor pausa e pede sudo ao Humano — FALHOU
     (regra órfã de (181)/(190), Passo 4 ainda não concluído pelo Humano
      no momento desta execução — esperado, não é achado novo)
P-3  Publicação é decisão deliberada, consentimento por trecho — OK
P-4  api_server contido · Ollama restrito a 127.0.0.1 — OK
P-5  Registre e nunca apague — OK
P-6  Cópia da história fora desta máquina — AVISO SÓ (nada pendente agora)
RESULTADO GERAL: FALHOU (por causa só de P-2)
```

**Não habilitado no pre-commit ainda — mesma tensão já registrada em (190):** como P-2 está DE VERDADE falhando agora (não é falso positivo), ligar `perimetro.sh` no `.githooks/pre-commit` neste exato momento bloquearia todo commit, incluindo o que registra esta entrada. Falta a palavra do Humano sobre quando ligar (depois do Passo 4 fechar, ou agora mesmo aceitando a trava) — mesma pergunta de (190), agora valendo pros 6 controles juntos, não só sudoers.

Modelo: Claude Sonnet 5 · vetor: rodar contra o repositório real ANTES de aceitar qualquer coisa, achando os 2 bugs de verdade rodando, não lendo o script; testes isolados positivo/negativo pra cada um dos 4 controles novos, em repo `/tmp` descartável, mesmo método de (181)/(190); verificação de que P-2 ainda falha de verdade (não fechado pelo Passo 4) antes de escrever esta entrada, não assumido. Turno desta sessão: t=1 (contado no contexto).

(190) DIÁRIO — 15/08/2026 · Passo 3 (saneamento): varredura de segredo testada contra 20 commits reais (zero falso positivo) e checagem de sudoers acrescentada à mesma varredura — achado real ao testar: um falso positivo próprio (secure_path lido como caminho) corrigido antes de aceitar, e a checagem de sudoers, correta, bloquearia TODO commit a partir de agora até o Passo 4 decidir — não habilitado no pre-commit ainda, pergunta ao Humano no fim desta entrada; diff do patch do 429 versionado fora do vendorizado

**3.1 — varredura de segredo, testada contra os 20 commits reais mais recentes** (`scripts/testar_varredura_20_commits.sh`, reaproveita os mesmos padrões do script real contra `git show -U0` de cada commit, não staged fictício): **zero achados nos 20** — nenhum falso positivo. Verificado manualmente que o teste não estava vazio por engano: um dos commits sozinho tem 53 linhas adicionadas, incluindo menções reais a `sha256`/hash em prosa (ex: "N4 (`sha256sum`, 21/21)... `corpus/CORPUS.sha256`, que já tem o hash pronto") — o padrão genérico (`KEY=`/`TOKEN:` etc.) corretamente não confundiu isso com segredo, porque hash em prosa não tem a forma `VAR=valor`. Mesma checagem específica pra "nonce": as duas menções reais nos 20 commits são prosa ("nenhum nonce ativo"), não valor atribuído — zero falso positivo aí também.

**3.2 — checagem de sudoers, acrescentada ao mesmo script (`checar_sudoers()`), classe inteira, não só o caso de (181):** roda `sudo -n -l`, extrai caminhos da seção real de regras, falha se algum não existe ou é gravável por não-root; se `sudo -n -l` pede senha (sem acesso não-interativo no momento), pula com aviso — não trava commit por não conseguir checar. **Achado real ao testar antes de aceitar:** a primeira versão varria a saída inteira e confundia a linha `Defaults ... secure_path=/usr/local/sbin:/usr/local/bin:/usr/bin` (PATH de busca, não regra de comando) com um caminho inexistente — regex ganancioso engolindo os `:` escapados como um token só. **Corrigido:** a checagem agora só olha o bloco depois do cabeçalho "pode executar os seguintes comandos", onde ficam as regras de verdade. Reexecutado: **1 achado real, correto** — a mesma regra órfã de (181) (`/home/orusoua/acer-predator-turbo-and-rgb-keyboard-linux-module/keyboard.py`, caminho inexistente).

**Consequência operacional, achada ao testar, não antecipada no texto da ordem — reportando antes de agir:** habilitar esta checagem no `.githooks/pre-commit` AGORA bloquearia **todo commit futuro**, inclusive os que documentam o resto desta própria sessão, porque a regra órfã de (181) ainda existe e o Passo 4 (a decisão sobre ela) está explicitamente travado esperando o Humano. A ordem pede "fecha a classe inteira do passo 4" — o que a checagem faz corretamente — mas o efeito prático é travar a escrita do canon até o Passo 4 ser resolvido, não só sinalizar. **Não habilitado ainda.** Pergunta ao fim desta entrada.

**3.3 — diff do patch do 429, versionado fora do diretório vendorizado:** reconfirmado antes de gerar — `~/.hermes/hermes-agent` ainda no commit `1f8fdc7b`, `pyproject.toml` em `0.20.1`, único arquivo modificado (`run_agent.py`), patch idêntico ao lido em (181) (2 linhas, `response.read()` antes de `response.text`). Salvo em `docs/hermes-agent-429-patch-0.20.1.diff` + `docs/hermes-agent-429-patch-0.20.1.md` (contexto, base, procedimento de reaplicação e reverificação) — `docs/` no repositório principal, nunca dentro de `~/.hermes/hermes-agent`, que é exatamente o que o próximo `hermes update` sobrescreve. sha256 do `.diff`: `2cc4cd5555ace0581782a3795ae73b2e30e87559002105f38f6df16b5fd37594`.

**Pergunta ao Humano, decisão real, não retórica:** habilito a checagem de sudoers no pre-commit agora — aceitando que nenhum commit passa até o Passo 4 decidir — ou espero o Passo 4 primeiro e habilito as duas checagens juntas depois? A varredura de segredo (3.1) sozinha já pode ser habilitada sem esse efeito colateral, se preferir separar as duas.

Modelo: Claude Sonnet 5 · vetor: script de teste real contra os 20 commits, não amostra nem alegação; inspeção manual do conteúdo de pelo menos um commit pra confirmar que o teste não estava vazio por bug; teste isolado de `checar_sudoers()` antes de integrar ao script principal, achando o próprio falso positivo antes que virasse achado aceito; reconfirmação do estado do patch do 429 (commit, versão, diff) imediatamente antes de salvar a cópia, não reaproveitando a leitura de (181) sem checar de novo. Turno desta sessão: t=1 (contado no contexto).

(189) DIÁRIO — 15/08/2026 · Passo 2 (saneamento): memória nativa do Hermes (`memoria/USER.md`, `memoria/MEMORY.md`) sai do rastreamento do repositório público — bypass de controle, não risco de fundo; exposição passada permanece, 0 forks confirmados via API

**Fato confirmado antes de agir:** `git ls-tree -r HEAD --name-only | grep '^memoria/'` — só dois arquivos rastreados sob `memoria/` fora de `memoria/missoes/` (já gitignorado à parte): `memoria/MEMORY.md` e `memoria/USER.md`. Bate exato com o alegado pela sessão de nuvem.

**Reclassificação, não novo achado:** PROJETO.md item 108 já descrevia este vetor (memória nativa do Hermes, escrita por mecanismo automático, distinta do DIÁRIO coletivo). O que muda aqui é a classificação: não é mais "risco de fundo" registrado — é **bypass de controle confirmado**. O controle declarado do projeto é que publicação em MEMÓRIAS é deliberada, por trecho, com data e consentimento (REGRAS, "O Conselho", item 2). Estes dois arquivos nunca passaram por esse controle nenhuma vez — são escritos automaticamente pelo mecanismo de memória do Hermes e publicavam por padrão, sem decisão. Mesma classe de (47): escrita automática operando fora do controle que deveria governá-la.

**2.1 — `git rm --cached memoria/USER.md memoria/MEMORY.md`:** os dois saem do índice, permanecem no disco (`memoria/USER.md` 541 B, `memoria/MEMORY.md` 2.506 B, confirmados presentes depois do comando). O Hermes continua escrevendo neles normalmente; só deixam de ser publicados a partir daqui.

**2.2 — `.gitignore`, glob em vez dos dois nomes:**
```
# Memória nativa do Hermes — escrita automática pela Máquina, não por
# decisão deliberada; nunca pública (achado em 15/08/2026, PROJETO item 108)
memoria/*.md
```
Mesma lição da regra de `memoria/missoes/` (achado em (97)/(98)): protege a classe, não o caso — se o mecanismo do Hermes criar um terceiro arquivo amanhã, nasce protegido sem exigir edição nova aqui.

**2.3 — conferido antes de comitar:** `git status --short` mostrou só `.gitignore` modificado + os dois arquivos removidos do índice — nada mais saiu. `memoria/missoes/` confirmado ainda ignorado (`git check-ignore -v`), pela regra própria dele, sem depender da nova.

**2.4 — registrado sem suavizar, como pedido:**
- **A proteção vale daqui pra frente. A exposição passada NÃO desaparece.** O histórico git é público e permanente — `git rm --cached` remove rastreamento futuro, não desfaz commits antigos que já publicaram o conteúdo. Reescrever a história (rebase, filter-branch, force-push) para apagar isso do passado é a linha vermelha da Regra 4 — não cogitado, não proposto.
- **Forks, verificado via API do GitHub (`api.github.com/repos/agataseth98-cmd/agata-seth`), agora:** `forks_count: 0`, `network_count: 0`. Zero forks confirmados no momento desta checagem — mas isto é uma foto de agora, não uma garantia permanente; um fork feito a qualquer momento antes desta entrada já teria cópia do histórico, e isto não seria detectável por esta checagem.
- **O que fazer sobre a exposição já ocorrida — se algo — é decisão do Humano.** Não proposta aqui, por ordem explícita. Registrado o fato (o quê, desde quando prático de checar, quanto do histórico) e a fronteira (o que este passo alcança e o que não alcança), nada além disso.

Modelo: Claude Sonnet 5 · vetor: `git ls-tree` real antes de aceitar o fato alegado pela sessão de nuvem; `git status`/`git check-ignore` depois da mudança, não antes, pra confirmar que nada além do pedido saiu do índice; chamada real à API do GitHub pro número de forks, não estimativa; disciplina de registrar sem propor ação sobre o passado, seguindo a ordem à risca. Turno desta sessão: t=1 (contado no contexto).

(188) DIÁRIO — 15/08/2026 · Passo 1 (saneamento): backup externo da expedição inteira (161)-(187) confirmado por RESTAURAÇÃO real, não listagem — clone dos dois bundles, HEAD bate exato, marcadores de pendência removidos

**HD detectado mas não montado sozinho:** `lsblk` achou `/dev/sda1` (exFAT, label `AgataBkup01`) fisicamente conectado, mas sem ponto de montagem automático. Montado via `udisksctl mount -b /dev/sda1` (mídia removível do próprio usuário, sem sudo).

**1.1 — comando dos marcadores, rodado:**
- `cp agata-canonico.bundle → auto-backups/agata-canonico-20260815-162634-8fb285c.bundle`
- `cp agata-missoes.bundle → auto-backups/agata-missoes-20260815-152618-07b6fd1.bundle`
Confirmado antes de copiar: `07b6fd1` era de fato o HEAD atual de `memoria/missoes` (nenhum commit novo lá desde a última passada).

**1.2/1.3 — verificação por restauração, não listagem:**
- `git bundle verify` nos dois: **"is okay"**, **"records a complete history"**, canônico com 7 refs (main + origin/HEAD + origin/main + 3 tags históricas), missões com 2 refs (master + HEAD).
- Clone real em `/tmp/restaura-canonico` e `/tmp/restaura-missoes` (apagados depois de conferir).
- **Checagem decisiva:** `grep -c '^(187) DIÁRIO' MEMÓRIAS.md` no clone restaurado → **1**. `git log -1 --format=%H` → **`8fb285c11792f91c0f3ee20252d0c878243a4899`**, bate exato com o canon. Missões: `git log -1 --format=%H` no clone → **`07b6fd1af5655066f5a5890800b02b18ea557166`**, bate exato.
- Contagem total de entradas DIÁRIO/CONSELHO no MEMÓRIAS restaurado: **137**.

**1.4 — relatório:**
```
agata-canonico-20260815-162634-8fb285c.bundle
  1.490.599 bytes · sha256 e734a7790dc391c9be78bbdf877ee5c2f1ce573c986de07bdb271e46721088f3
  HEAD restaurado: 8fb285c11792f91c0f3ee20252d0c878243a4899
  entradas DIÁRIO/CONSELHO no MEMÓRIAS restaurado: 137

agata-missoes-20260815-152618-07b6fd1.bundle
  341.551 bytes · sha256 6550b1f10ed35fa0d66d46ebb02ad3138540020f188113a3ebcbbb666fdbd59d
  HEAD restaurado: 07b6fd1af5655066f5a5890800b02b18ea557166
```

**1.5 — marcadores removidos**, só depois de 1.3 passar: `~/.agata-backup-staging/PENDENTE-HD-DESCONECTADO` e `PENDENTE-HD-DESCONECTADO-MISSOES` apagados. A expedição inteira (161)-(187) agora tem cópia externa confirmada por restauração real, não só por commit local + GitHub.

Modelo: Claude Sonnet 5 · vetor: `git bundle verify` real nos dois arquivos antes de qualquer outra coisa; clone de teste de verdade em `/tmp`, não confiança na cópia; checagem decisiva rodada e conferida (grep + hash), não assumida; verificação prévia de que o HEAD de missões usado na cópia era o atual, não um stale. Turno desta sessão: t=1 (contado no contexto).

(187) DIÁRIO — 15/08/2026 · Correções ao C-5 (186), por ordem do Humano — entrada nova, (186) não editada. Linha do B0 refeita com granularidade real, denominador exato (240, não "~80"), variável do C4 redescrita com honestidade (não isola treino), 12 falhas do C4 decompostas, ressalva da exclusão de C4/V1 movida pra dentro da mesma frase do número de fabricação

**B.1 — linha do B0, refeita a partir de (173), sem arredondar:** 11 limpos (N1, N3, A1, A3, V1, V3, V4, F1, F3, F4, F2) · 1 parcial (A4 — correto em TES-001/TES-002, mas acrescenta seção fora de escopo, não fabricada) · 2 recusas corretas (N2, N4 — resultado ANTECIPADO pelo pré-registro `fora_do_payload`, não crédito nem falha) · 1 estouro de orçamento de raciocínio (A2, `tokens_out=4000`, `content` vazio, ~208s, 3/3 rodadas) · 1 fabricação confirmada (V2). **Soma: 11+1+2+1+1 = 16.** A linha anterior em (186) colapsava isso em "~4 sem-resp/erro" — impreciso, substituído aqui.

**B.2 — denominador exato:** onde (186) dizia "~80 respostas", o correto é **240 respostas** (5 células × 16 perguntas × 3 rodadas). Uma fabricação confirmada em 240, não em ~80 — a tese fica mais forte com o número certo, não mais fraca.

**B.3 — variável do C4, redescrita com honestidade:** `rlm-qwen3-8b-teste` não difere de `qwen3.5-9b-64k` só por ser "outro modelo" — difere em geração de base, tamanho, janela de contexto (32.768 medido como teto real vs 65.536 de produção) **e** em ser (ou não) treinado para o laço de busca que a bancada testa. **A célula C4 NÃO isola a variável "treino pra RLM"** — isola "modelo A vs modelo B", um pacote de diferenças, não uma variável controlada só. Onde (186) dizia "MODELO trocado" como se fosse uma troca limpa, o certo é registrar as quatro diferenças reais.

**B.4 — as 12 falhas do C4 (180), decompostas, pro confundidor de whitelist não engolir o achado real:**
- **2 por vocabulário fora da whitelist** — N3 (`cut` em pipeline, 36/36 tentativas recusadas nas 3 rodadas) e N4 (`sha256sum`, 21/21) — mesma classe de atrito que motivou o C1b inteiro, não neutralizada aqui. N4 tinha caminho válido DENTRO da própria whitelist (`cat`/`grep` em `corpus/CORPUS.sha256`, que já tem o hash pronto) — o modelo nunca tentou esse caminho.
- **6 por responder sem acionar ferramenta nenhuma** — N1, A2, V1, V2, V4, F4 (F2, sétima pergunta do mesmo padrão, não entra aqui porque foi contada como parcial, não falha).
- **4, o resto (A1, A3, A4, F1) — não convergência**, no sentido largo de "tentou e não chegou", não estritamente estouro de teto de iteração (só A4 bateu o teto de 12; A1/A3/F1 responderam errado com poucas iterações).
- **Total: 2+6+4 = 12,** bate com o placar de (180).
**O achado que sobrevive a essa decomposição, destacado:** das 16 perguntas, **7 foram respondidas na 1ª chamada sem nenhum comando** (as mesmas 7, nas 3 rodadas — N1, A2, V1, V2, V4, F2, F4), **6 delas erradas.** Um checkpoint chamado `rlm-qwen3-8b`, presumivelmente relacionado a treino pra busca recursiva, não buscou em quase metade das perguntas — isso é achado sobre o checkpoint, não sobre a whitelist do runner.

**B.5 — a ressalva da exclusão de C4/V1 entra na mesma frase do número de fabricação, não separada:** "**1 fabricação confirmada em 240 respostas** — mais um caso (C4/V1) excluído por critério, não por ausência: erro confiante, sem fonte, invertendo o veredito do gabarito, idêntico nas 3 rodadas, sem o padrão de citação verificável (número de entrada falso e checável) que o critério estrito exige." Sem essa ressalva junto, o número "1" lê como ausência de risco quando na verdade é exclusão criteriosa de um caso limítrofe real.

**B.6 — condições de execução, não comparáveis entre si:** C4 rodou com a máquina dedicada (nada em paralelo, ordem explícita). C3 rodou com `qwen3.5-9b-64k` já carregado em produção, `19%/81% CPU/GPU` — configuração de produção normal, não mexida, mas partilhando GPU com outro processo residente. **Latência entre C4 e C3 não é comparável.** Não afeta o achado de não-convergência do C3 (que é sobre iterações batendo o teto, não sobre tempo de parede).

**C — confirmado, nada mudou:** os 5 pontos de leitura de (186) seguem válidos, seguem PROPOSTA. Nenhuma célula nova rodada. Bancada seguiu congelada — todas as correções acima são de texto/rótulo, os números-fonte em (173)/(180)/(185) não mudaram.

Modelo: Claude Sonnet 5 · vetor: releitura completa de (173) antes de reescrever a linha do B0, conferindo a soma bate 16; recontagem das 12 falhas do C4 direto da tabela R1 de (180), campo "1ª chamada sem comando?" cruzado com o placar categórico; verificação aritmética de 240 = 5×16×3 antes de trocar o denominador. Turno desta sessão: t=1 (contado no contexto).

(186) DIÁRIO — 15/08/2026 · C-5, RELATÓRIO FINAL do experimento "RLM em 3 caminhos" — 5 células rodadas (B0, C1, C1b, C4, C3), UMA fabricação confirmada no experimento inteiro, leituras propostas sem veredito — decisão do Humano

**Encerra o experimento aberto em (163).** Todas as células planejadas ou substituídas por decisão explícita do Humano já rodaram: B0 (173), C1 (172), C1b (174)-(177), C4 (178)-(180, redesenhada de "harness do C2" pra "runner do C1b × modelo diferente", ordem 15/08), C3 (181)-(185, rodada por último, portões verificados ao vivo antes de rodar). Esta entrada só consolida — nenhum dado novo é gerado aqui.

**Tabela células × métricas, tudo medido, nada estimado:**
```
célula  variável testada          modelo               limpos  parciais  sem-resp/erro  fabricação  determinístico  3 rodadas
B0      injeção total (sem tool)  qwen3.5-9b-64k        11       0          ~4          1 (V2)      NÃO (achado em 173)   n/d
C1      busca sob demanda,        qwen3.5-9b-64k         9       2          5           0           n/d                 n/d
        pipe proibido
C1b     busca sob demanda,        qwen3.5-9b-64k        10       1 (misto)  5           0           n/d                 n/d
        pipe até 3 estágios
C4      = runner do C1b,          rlm-qwen3-8b-teste     2       2          12          0*          SIM (180)           8m28s
        MODELO trocado
C3      biblioteca recursive-llm  qwen3.5-9b-64k         1       0**        14+1***     0           SIM (185)           1h00m30s
        (REPL/string, sub-call
        off, max_depth=0)
```
`*` C4/V1: erro confiante sem fonte, mesma classe de risco da fabricação, NÃO elevado a "confirmada" pelo critério estrito (sem citação de entrada falsa) — ver (180) R6.
`**` C3/N4: investigado a fundo, NÃO é fabricação — citação real e verbatim do corpus, só desatualizada (histórico de hash de REGRAS.md), sem ressalva — ver (185) R3.
`***` conta separada de N4 (errado-mas-grounded) somada às 14 sem-convergência = 15 não-acertos de 16 em C3.

VRAM/GPU medidos onde a célula rodou nesta sessão: C4 100% GPU, 6.555-6.710 MiB (32768 ctx, teto real medido — 40960 não coube); C3 7.099-7.223 MiB (produção, 19-81% CPU/GPU, config não mexida). B0/C1/C1b não têm medição de GPU desta sessão (rodaram em sessão anterior, 14/08).

**Obrigatório 1 — fabricação, contagem absoluta, FORA de qualquer média: UMA (1) fabricação confirmada em todo o experimento — 5 células, ~80 respostas-questão-rodada somadas.** É de B0 (173), célula de injeção total: perguntada sobre a própria história do projeto, atribuiu com confiança um erro de (157) à entrada errada (143), **idêntica nas 3 rodadas**, verificada linha a linha contra o corpus antes do registro. Trecho literal (V2, B0): a resposta atribuía o erro a "(143)" quando a entrada correta era outra — ver (173) pro texto completo da resposta e da verificação. Nenhuma outra célula produziu fabricação sob o mesmo critério estrito (citação de entrada/número falsa, verificável e confirmada) — os dois candidatos que pareciam fabricação à primeira vista (C4/V1, C3/N4) foram investigados a fundo e não se qualificam (ver notas `*`/`**` acima).

**Obrigatório 2 — faixa `fora_do_payload` (N2, N4), rotulada como resultado ANTECIPADO, não como ponto a favor de ninguém:** células com acesso a arquivo real (C1, C1b, C4 quando não travava por whitelist) acertam N2/N4 quase de graça — a informação está no disco, fora do `.hermes.md` injetado mas dentro do alcance do `grep`. B0 (só injeção, sem ferramenta) **corretamente não acertou N2 nem N4** — não está na lista de "11 acertos limpos" de (173) — isso é o desenho funcionando como esperado, não uma falha de B0. C3 (contexto em string, sem sistema de arquivos) errou os dois por motivo estrutural (N4: `CORPUS.sha256` nunca entrou no `context` que montei) — também não é falha de capacidade, é fronteira de desenho. Nenhuma célula ganha ou perde pontos por esta faixa; ela mede alcance de ferramenta, não qualidade de raciocínio.

**Obrigatório 3 — faixa decisiva `so_no_indice` vale como 5 sondas, não 6:** A2 falhou em **todas as 5 células, por 5 causas diferentes** (C1: pipe recusado · B0: orçamento de raciocínio esgotado · C1b: busca sem convergência, zero rejeição · C4: resposta vazia, zero tentativa · C3: loop de repetição de regex) — é propriedade da pergunta, não sinal comparável entre células. As 5 sondas restantes da faixa (A1, A3, V2, V4, F2, minus A2) são o que efetivamente diferencia os caminhos.

**Obrigatório 4 — o que o C1b mediu, com precisão, sem simplificar:** a variável do C1b não foi "liberar pipe" — foi o tratamento do caractere `|`, de banido cru em qualquer posição da string, para reconhecido como separador de estágio só fora de aspas. Essa mudança resolveu dois problemas textualmente distintos ao mesmo tempo: pipe de verdade (V1, V4, A2, A3 tinham tentativas reais de composição) E alternação de regex mal-interpretada como metacaractere (F4 — 18 de 18 rejeições eram alternação, zero pipe real, achado em (176)). Tratar como "C1b libera pipe" apaga essa distinção — 32% das rejeições do C1 nunca foram sobre pipe.

**Leituras, propostas — o Humano decide, nenhuma abaixo é veredito:**
1. **Busca sob demanda com pipe (C1b) é o caminho de melhor equilíbrio honesto:** maior contagem de acertos limpos entre as células com zero fabricação confirmada (10/16), mesmo sem superar o placar bruto de B0.
2. **B0 continua com o melhor placar bruto (11 limpos), mas é a única célula com fabricação confirmada e com não-determinismo documentado (173)** — troca explícita entre exatidão aparente e um risco real e medido, não hipotético.
3. **Nem modelo treinado (C4) nem biblioteca RLM externa (C3) superaram os caminhos próprios (C1/C1b) neste corpus e nesta bancada.** Isto pode ser específico deste checkpoint (`rlm-qwen3-8b-v0.1`, achado real: responde sem tentar ferramenta em quase metade das perguntas) e deste desenho de corpus (C3 sofreu de um gap real de construção — `CORPUS.sha256` fora do contexto), não uma afirmação geral sobre "modelo treinado" ou "RLM via REPL" como classes — outro checkpoint ou outro desenho de corpus poderia performar diferente.
4. **Nenhum caminho testado resolve o núcleo do gargalo:** A2 falha nas 5 células, V4/F4 falham na maioria — a leitura "nenhum caminho bate B0 nem resolve o que B0 também não resolve" é conclusão legítima do experimento, não fracasso dele.
5. **Se algum caminho vira produção, ou se o amálgama (ex: C1b como ferramenta, com o cuidado de B0 pra perguntas dentro da janela) é a resposta, é decisão do Humano** — o experimento entrega dado comparável, não recomendação.

**Nada em produção mudou por este relatório.** `qwen3.5-9b-64k` segue sob regime de auditoria como já estava; `rlm-qwen3-8b-teste` e `recursive-llm` (venv isolado) são artefatos de experimento, não candidatos automáticos a produção.

Modelo: Claude Sonnet 5 · vetor: releitura de (172)/(173)/(177)/(180)/(185) linha a linha pra montar a tabela sem reinventar números; checagem cruzada de que N2/N4 realmente não estão na lista de acertos de B0 antes de rotular como "anticipado, não falha"; contagem literal de fabricação (1, não taxa) contra as 5 entradas de resultado; releitura de (176) pra não simplificar o que o C1b mediu de fato. Turno desta sessão: t=1 (contado no contexto).

(185) DIÁRIO — 15/08/2026 · C3 completo, 3 rodadas — 100% determinístico (idêntico nas 3), placar 1 acerto bem fundamentado, 1 erro real (não fabricação — investigado a fundo antes de rotular), 14 sem convergência; A2 falha pela QUINTA vez, quinta causa diferente

**R1 — placar (3 rodadas idênticas, `temperature=0`, zero variação):**
```
pergunta  resultado                          eventos  causa
N1-N3     [SEM RESPOSTA: teto de iterações]  40       não convergiu
N4        errado, mas grounded (ver R3)      37       citação real, desatualizada
A1-A4     [SEM RESPOSTA: teto de iterações]  40       não convergiu
V1-V4     [SEM RESPOSTA: teto de iterações]  40       não convergiu
F1,F2,F4  [SEM RESPOSTA: teto de iterações]  40       não convergiu
F3        CORRETO, bem fundamentado          22       busca real convergiu
```
14 de 16 nunca convergiram, sempre nas 3 rodadas idênticas — pior placar bruto da comparação inteira (pior que C4, que ao menos teve 2 limpos + 2 parciais).

**R2 — F3, único acerto limpo:** "Não, a citação com aspas literais não existe no arquivo. O texto 'O papel de auditor é item da auditoria' aparece duas vezes sem aspas, mas não há ocorrência com aspas circundantes." — bate o veredito e o mecanismo do gabarito (Kimi fundiu duas frases separadas como se fosse uma citação única). 22 eventos, busca real dentro do REPL, não resposta de primeira tentativa.

**R3 — N4, investigado a fundo ANTES de rotular como fabricação — não é. Achado mais interessante da célula.** Resposta: `658d704e39b3d9bee9388205ec889c49941a46c1325095cf6c5b09c71863db13` — bate com o gabarito atual (`7cecb171a8...`)? **Não.** Primeira leitura pareceria fabricação (hash de 64 caracteres, confiante, errado). **Investigado o processo passo a passo** (`investigar_c3_n4.py`, `capture_trajectory_content=True`): o modelo rodou `re.findall(r'[a-f0-9]{64}', context)`, achou múltiplos hashes reais de REGRAS.md espalhados pelo histórico de MEMÓRIAS (o arquivo foi editado e re-hasheado várias vezes ao longo do projeto), filtrou por proximidade textual com "REGRAS.md" + "sha256", e extraiu o PRIMEIRO casamento por ordem de aparição no texto — `658d704e...`. **Confirmado por `grep` real:** essa string existe *verbatim* em `corpus/MEMÓRIAS.md:1281` — `"REGRAS.md: sha256 \`658d704e...\`, 15.446 B."` — um valor histórico real, de um REGRAS.md mais antigo, não o do corpus congelado hoje. **Não é conteúdo inventado — é uma citação real, verbatim, só desatualizada, apresentada sem nenhuma ressalva de que podia não ser a versão atual.** Achado adicional: `corpus/CORPUS.sha256` (onde vive o hash correto e atual) nunca fez parte do `context` que montei para o C3 — no paradigma RLM o corpus vira uma string só, e eu concatenei só os 3 `.md`, não o `.sha256`. **N4 era estruturalmente irrespondível certo neste desenho do C3**, gap meu de construção de corpus, não do modelo — registrado, não escondido.

**R4 — A2 falha pela QUINTA vez, quinta causa diferente em cinco arquiteturas diferentes:** C1 (pipe recusado) · B0 (orçamento de raciocínio esgotado) · C1b (busca sem convergência, zero rejeição) · C4 (resposta vazia, zero tentativa de comando) · **C3 (agora): loop de repetição — investigado o processo (`investigar_c3_n4.py` reaproveitado pra A2), o modelo achou material real relevante (`entrada (143)... confirmado depois pelo próprio Kim...`) na iteração 7, mas em vez de ler mais ou declarar `FINAL`, ficou re-rodando a MESMA regex (ou uma variação trivial dela) por mais 5 iterações, sempre com a mesma saída, até estourar o teto sem nunca comitar.** Reforça "propriedade da pergunta" pela quinta vez, cinco causas nunca repetidas — faixa decisiva `so_no_indice` continua valendo como 5 sondas.

**R5 — GPU/tempo, medido (`gpu_C3.csv`, 247 amostras a cada 15s):** VRAM 7.099-7.223 MiB (média 7.187,7) — `qwen3.5-9b-64k` já estava carregado em produção com `19%/81% CPU/GPU` (não 100% GPU, config normal de produção com `num_ctx=65536`, não mexida). Utilização de GPU média 48,6% (min 0, max 100). **3 rodadas completas em 1h00m30s** (14:17:02-15:17:32) — bem abaixo do teto superior estimado de ~3,2h, porque a maioria das falhas bateu o teto de 12 iterações rápido, não o timeout de 240s por chamada.

**Determinismo total, achado à parte:** as 3 rodadas produziram exatamente as mesmas 16 respostas, char por char, incluindo o mesmo hash "errado" em N4 nas 3 vezes — `temperature=0` aqui produziu reprodutibilidade completa, diferente do não-determinismo observado no B0 (173) sob a mesma configuração nominal de temperatura.

**Modelo descarregado ao fim** (`ollama stop`), `gpu_C3.csv` parado. Nada em produção mudou.

Modelo: Claude Sonnet 5 · vetor: investigação completa do processo (não só do resultado) antes de rotular N4 como fabricação — `grep` real confirmando que a string existe verbatim no corpus, evitando um falso positivo de fabricação; mesmo tratamento pra A2, achando a quinta causa real em vez de assumir repetição do padrão já visto; leitura de `gpu_C3.csv` completo, não amostra; cálculo de duração real via os timestamps do próprio log, não estimativa. Turno desta sessão: t=1 (contado no contexto).

(184) DIÁRIO — 15/08/2026 · C3, portões confirmados AO VIVO (não só lidos) — os dois liberam a célula; 2 smoke tests rodados, achado real de bug de corpus corrigido no processo, bateria completa de 3×16 NÃO lançada — custo estimado de horas pra uma célula que a própria ordem já tratava como menor valor esperado, decisão de continuar ou fechar aqui é do Humano

**Instalação, autorizada pelo Humano depois de bloqueio do classificador (183):** `uv pip install "recursive-llm @ git+..."` no venv isolado — `recursive-llm==0.3.1` (módulo real `rlm`), commit `6462053`. `pip global` nunca usado.

**Portão 1 (rede), verificado rodando, não só lendo o README:** `REPLExecutor` real, tentativas de `import socket` (com `.connect(('8.8.8.8', 53))`), `import urllib.request`, `import os`, `import subprocess`, `__import__` direto — **todas bloqueadas** (`Import of 'X' is not allowed` ou erro de compilação pro `__import__`). Controle positivo (`import json`, permitido) funcionou normal, confirmando que o bloqueio é seletivo, não uma falha genérica do executor. **Portão 1 libera a célula.** Script: `teste_c3_portao1.py`.

**Portão 2 (sub-chamadas), verificado rodando contra `qwen3.5-9b-64k` real, com prompt adversarial pedindo `llm_query(...)` explicitamente:** 34 eventos capturados via `event_handler` ao vivo (não só o resultado final — `MaxIterationsError` não carrega trajetória), **profundidade nunca saiu de 0 em nenhum dos 34**. Lido no código-fonte instalado (`rlm/core.py:900`, `_build_repl_env`): com `max_depth=0`, as chaves `llm_query`/`rlm_query`/`recursive_llm` **nunca são adicionadas** ao ambiente do REPL — não é recusa em runtime, o nome simplesmente não existe pro código gerado tentar chamar. **Portão 2 libera a célula.** Script: `teste_c3_portao2.py`.

**Achado real, corpus com bug de fronteira, corrigido antes de rodar a bancada — mesma disciplina de (175)/(176) (achar bug de script antes de condenar o modelo):** primeiro smoke test (V1, célula-núcleo `C2 × qwen3.5-9b-64k`) não convergiu em 12 iterações (128,4s). Segundo smoke test (N2, com captura de trajetória completa) mostrou a causa: o corpus é passado como uma string só (paradigma RLM — o modelo nunca vê o texto inteiro, só manipula por fatiamento Python dentro do REPL), e minha concatenação de REGRAS+PROJETO+MEMÓRIAS **sem delimitador** fazia `context.find('MEMÓRIAS.md')` casar com uma MENÇÃO do nome do arquivo dentro do próprio texto de REGRAS.md ("...está em MEMÓRIAS.md..."), não com o início real do arquivo. Corrigido com delimitador explícito (`===INÍCIO_ARQUIVO:MEMÓRIAS.md===`) em `rlm_c3.py`. **Refeito o mesmo smoke test (N2) depois do conserto: o problema persiste** — `.find('MEMÓRIAS.md')` ainda casa com a mesma menção textual antes de chegar no delimitador real, porque o nome do arquivo aparece várias vezes no corpo de REGRAS/PROJETO (é um sistema que fala sobre si mesmo o tempo todo). Nenhuma instrução foi dada ao modelo sobre a convenção do delimitador — ensinar isso mudaria o desenho do teste.

**Padrão qualitativo, nos dois smoke tests, mesma classe de achado do C4 (180):** o modelo nunca tentou uma estratégia direcionada (contar delimitadores, usar `re.search` com âncora mais específica, ou simplesmente `context.count('\n')` sobre a fatia certa). Em vez disso, expandiu a janela de leitura repetidas vezes a partir da mesma âncora errada (`[1300:1450]` → `[1300:2500]` → `[1300:5000]` → `[1300:8000]` → `[1300:20000]` → `[1300:50000]`), sem nunca declarar resposta final dentro do teto de 12 iterações.

**Custo medido, não estimado:** 2 smoke tests, ~60-130s cada, contra 1 pergunta cada. Bateria completa é 16 perguntas × 3 rodadas = 48 chamadas RLM, cada uma podendo gastar até `max_elapsed_seconds=240` antes de desistir — **teto superior de ~3,2h**, muito acima do que C1/C1b/C4 levaram inteiros. **Não lançada.** A própria ordem já registrava C3 como menor valor esperado da fila ("roda porque o Humano quer os três caminhos na mesa, não porque a expectativa é alta") — decisão de pagar esse custo, ou fechar aqui com os dois portões confirmados e os dois smoke tests como sinal, é do Humano, não decidida nesta entrada.

**Nada em produção.** `qwen3.5-9b-64k` foi usado só para os dois smoke tests e os dois testes de portão — mesmo modelo já em regime de auditoria, nenhuma mudança de configuração ou papel.

Modelo: Claude Sonnet 5 · vetor: dois portões testados rodando código real contra a Máquina, não aceitos por leitura de README; captura de trajetória completa via `event_handler` pra não depender do retorno de `complete_result` (que não carrega dado quando estoura iteração); leitura do código-fonte instalado (`core.py:900`) pra confirmar o mecanismo do portão 2, não só o comportamento observado; reprodução do smoke test depois do conserto do delimitador antes de aceitar que o conserto bastava. Turno desta sessão: t=1 (contado no contexto).

