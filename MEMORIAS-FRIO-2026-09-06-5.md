# MEMORIAS-FRIO-2026-09-06-5.md — camada fria do sistema Agata (selada, imutável)

Congelado por scripts/migrar_periodo.py. Selado com scripts/selar.sh — SHA-256 registrado em SELOS.txt, tag de git aponta pro commit deste selamento. Depois de selado, este arquivo nunca mais recebe escrita — garantia é `scripts/selar.sh --check`, não mais P-5.

---

(233) DIÁRIO — 21/08/2026 · git push travava por credencial expirada, não rede — `gh auth setup-git` destrava, confirma suspeita antiga do sincronizador

**Achado, ao publicar (232 - ler_pagina.sh: teste negativo corrigido) em origin/main:** `git push origin main` travou sem erro visível, mesmo com `GIT_TERMINAL_PROMPT=0` (que deveria abortar na hora em vez de esperar prompt). Descartada causa de rede: `curl -sS https://github.com` respondeu HTTP 200 em 0,109s. Causa real, isolada forçando `GIT_ASKPASS=/bin/echo` (credencial vazia) pra tirar o comando do modo silencioso: `remote: Invalid username or token. Password authentication is not supported for Git operations.` — nenhum `credential.helper` configurado (nem local nem global), nenhuma credencial válida disponível pro `git` usar.

**Confirma, não introduz, uma suspeita antiga:** `memoria/sincronizacao.log` já vinha registrando `[2026-08-20T09:17:14] OK sincronizado (modo local, remoto offline ou credencial expirada)` — o script `scripts/sincronizar-estado.sh` (só lê e nunca publica sozinho, por desenho desde o incidente do commit `564a50d`, ver 224 - auto-sync, lacuna fechada por decisão do Humano sem investigar mais) trata "sem match no `git ls-remote`" como um caso só, sem distinguir rede de credencial. Hoje ficou confirmado: era credencial — a rede estava, e está, OK.

**Conserto aplicado, sem inventar credencial nova:** o `gh` CLI já estava autenticado de verdade (`gh auth status` → conta `agataseth98-cmd`, escopo `repo`, via keyring do sistema) — só não estava amarrado ao `git`. Rodado `gh auth setup-git` (subcomando padrão do próprio `gh`, configura `credential.helper` pra delegar pro `gh`) — o push seguinte passou de primeira, confirmado por `git ls-remote origin main` batendo o SHA publicado.

**Alcance do conserto:** config de `git` (`credential.helper`) pra este usuário nesta máquina, não script novo nem mudança de comportamento automático de nenhum serviço do Agata — reversível trivialmente (`git config --unset credential.helper`). Destrava push futuro nesta sessão de usuário, não é garantia permanente: o token do `gh` pode expirar de novo, e o mesmo sintoma (travamento sem erro visível, exige forçar `GIT_ASKPASS` pra ver a causa real) provavelmente se repete se isso acontecer.

Modelo: Claude Sonnet 5 · vetor: `curl` real descartando rede antes de suspeitar de credencial; `GIT_ASKPASS=/bin/echo` pra forçar o erro real em vez do timeout silencioso; `gh auth status` conferido antes de assumir que não havia credencial nenhuma disponível; push e `git ls-remote` rodados de verdade depois do conserto, não presumido. Turno desta sessão: t=4 (contado no contexto).

(232) DIÁRIO — 21/08/2026 · ler_pagina.sh: teste negativo achou ruído de framework sendo relatado como conteúdo; conserto aplicado, aprovado ao vivo

**Achado, por teste negativo real, não revisão de código:** rodando `scripts/ler_pagina.sh` contra `https://angular.realworld.io/` nesta máquina (Predator, cachyos-PHN16-71), o CASO 3 relatava mensagens internas de erro do Angular ("StaticProvider does not have...", "Cannot mix multi providers...") como se fossem conteúdo do site — a heurística de "cadeia longa sem sintaxe de código" não distingue isso de texto real de qualquer SPA moderna (Angular/React/Vue têm erros com a mesma forma). O script também não checava código HTTP antes de extrair — risco já medido antes contra uma URL morta no S3 que devolveu 404 e foi tratada como CASO 1.

**Conserto, as três mudanças autorizadas:** (1) checagem de HTTP obrigatória antes de qualquer extração — código fora de 2xx aborta, nada é extraído; (2) CASO 3 rebaixado a SUSPEITA, nunca mais conclusão, sempre com qualquer URL de API do mesmo pacote reportada lado a lado, nunca uma escolhida em vez da outra; (3) filtro de idioma quando o HTML declara `lang`, com ausência reportada em vez de calada.

**Regressão, antes/depois, ambos exigidos e medidos ao vivo nesta máquina:** controle positivo `razionshefa.com.br/pt` (conteúdo real, antes já saía certo por acidente, depois sai como SUSPEITA em vez de CASO 3) e teste negativo `angular.realworld.io` (antes: erros do Angular relatados sem aviso; depois: SUSPEITA + `https://conduit.productionready.io/api` reportada junto, confirmada por grep direto no pacote). Bônus medido: 404 real controlado (`en.wikipedia.org`, página inexistente) agora aborta em HTTP 404 sem tentar extrair nada. Os dois casos exigidos viraram teste permanente versionado: `scripts/testar_ler_pagina.sh` — rodado, 0 falhas.

**O caminho CASO 4/lacuna** agora é mecanismo testado contra caso real (API do pacote de `angular.realworld.io` confirmada por grep direto), não mais especificação nunca exercitada.

**Fluxo de quarentena P-8, aplicado:** `propostas/aplicadas/ler-pagina-conserto.diff` + `propostas/aplicadas/APROVADO-ler-pagina-conserto`. Aprovação ao vivo nesta conversa — o Humano leu o diff e o relatório de teste antes/depois e respondeu "autoriza → o Executor cria o marcador → commita o diff junto da entrada (232)", mesmo padrão de autorização ao vivo já usado em (231) e outras entradas desta sessão de trabalho do Humano.

**Portão das três perguntas (231), aplicado antes de commitar:** (1) Reversibilidade — sim, é entrada nova + diff revertível, nenhum mecanismo automático mudou. (2) Alcance — só `scripts/ler_pagina.sh` e o novo `scripts/testar_ler_pagina.sh`; nenhum hook, serviço ou config tocado. (3) Silêncio — não: o teste de regressão falha ruidosamente (exit != 0) se a SUSPEITA regredir pra CASO 3 ou se a API sumir do relatório.

Modelo: Claude Sonnet 5 · vetor: teste negativo e o 404 controlado rodados ao vivo nesta máquina, antes e depois do conserto, saída colada no relatório ao Humano antes desta entrada — não restaurado de resumo. Turno desta sessão: t=2 (contado no contexto).

(231) DIÁRIO — 20/08/2026 · Portão das três perguntas adotado em REGRAS — desenhado a partir de incidentes reais deste projeto, não copiado da proposta que chegou de fora

**Motivo:** (229)/(230) confirmaram que a proposta de um "portão de segurança" (três perguntas antes de o Humano autorizar mudança estrutural) era real, vinda de uma sessão remota. O Humano pediu, nesta conversa, pra não adotar como veio — "melhore, leve ao estado da arte... elegante, refinada, prazerosa e musical."

**Desenho:** as três perguntas do bloco original não vinham com conteúdo específico ("três perguntas de segurança por arquitetura"). Escritas do zero, cada uma ancorada num incidente que este projeto já pagou caro, não em teoria genérica de arquitetura:
1. **Reversibilidade** — "desfaço sozinho, ou preciso de alguém de fora?" — a mesma pergunta que justifica ter quarentena e backup.
2. **Alcance** — "o que mais isto toca, além do que pretendo mudar?" — a pergunta que a P-8 existe pra forçar (218): executor mudando canon sem o Humano perceber o alcance.
3. **Silêncio** — "eu saberia se quebrasse, ou só descubro quando for tarde?" — a pergunta que a P-9 existe pra forçar (221): `agata-consolidacao.timer` morto dias sem ninguém notar.

**Mecanismo:** quem PROPÕE pergunta ao Humano, uma de cada vez, sempre as três, sempre nesta ordem, antes de pedir autorização — não é o Humano respondendo sozinho um formulário, é diálogo. Registrado em REGRAS.md, "Mudança estrutural".

**O portão aplicado a si mesmo, antes de escrever isto em canon:**
1. Desfaço sozinho? Sim — é entrada nova em REGRAS.md; revogar é outra entrada nova (Regra 4), não mexe em nada mecânico do sistema.
2. O que mais toca? Só a seção "Mudança estrutural" — nenhum script, hook ou comportamento automático muda.
3. Eu saberia se quebrasse? Sim — vira ritual vazio do jeito que o hedge de (157)/(158) virou; o sinal seria uma proposta chegando sem as três perguntas, ou respostas em piloto automático.

**Fluxo de quarentena, sétimo uso real:** autorização ao vivo nesta conversa, a mesma mensagem que pediu a elevação do desenho. `propostas/aplicadas/APROVADO-portao-tres-perguntas`.

Modelo: Claude Sonnet 5 · vetor: `grep` real em REGRAS.md pra confirmar a seção "Mudança estrutural" antes de editar; citações de (218)/(221) conferidas contra o texto real dessas entradas, não de memória. Turno desta sessão: t=5 (contado no contexto).

(230) DIÁRIO — 20/08/2026 · Humano confirma ao vivo: a disputa entre modelos sobre `config.yaml` (229) foi real

**Confirmado pelo Humano, nesta conversa, pergunta direta e resposta direta:** a conversa entre modelos sobre a edição de `~/.hermes/config.yaml` (uma instância remota questionando, resolvida a favor da edição) aconteceu de verdade. Sem rastro em disco (229) porque não deixou — não porque não existiu.

**O que isso fecha:** a parte de (229) marcada "não confirmado, sem evidência de Máquina" passa a "confirmada pelo Humano, sem evidência de Máquina" — fontes diferentes, as duas válidas. Regra 1 não exige rastro em disco pra tudo; exige não inventar rastro que não existe.

**O que continua em aberto:** a proposta do "novo portão de segurança" (três perguntas antes de mudança estrutural) — a confirmação de hoje foi sobre o fato da conversa ter acontecido, não sobre adotar a regra. Perguntado à parte.

Modelo: Claude Sonnet 5 · vetor: resposta direta do Humano nesta conversa, à pergunta feita em (229). Turno desta sessão: t=4 (contado no contexto).

(229) DIÁRIO — 20/08/2026 · Bloco recebido como "handoff" de outra sessão — fato físico confirmado por este executor, narrativa em volta não

**Motivo:** depois de tratar o bloco anterior como dado não verificado, este executor checou por conta própria o que dava pra checar — "Máquina arbitra fatos" não se cumpre descartando por suspeita, se cumpre indo olhar.

**Confirmado, com evidência de Máquina, por este executor, agora:**
- `~/.hermes/config.yaml` (fora de `~/agata`, fora de qualquer repositório git — `cd ~/.hermes && git status` devolve "not a git repository") teve o bloco `agent.personalities` (14 personas, incluindo `kawaii`/`catgirl`/`pirate`) removido — lido no arquivo atual, ausente; `grep -n "^personalities"` não acha nada.
- Existe backup pré-mudança seguindo a convenção já usada neste projeto pra `config.yaml` (`.bak.<descrição>`, ver histórico de `~/.hermes/config.yaml.bak-*` desde julho): `config.yaml.bak.personalities_remove`, mesmo timestamp (18:25) do arquivo editado, conteúdo batendo exato com o que o diff do log alega ter sido removido.
- Existe o log `memoria/missoes/auditoria-local/integridade_20260820_191956.log`, lido por inteiro: diff real, validação YAML com sucesso, e a checagem "arquivo fora do git → P-8 não aplicável" — **correta**, P-8 (MEMÓRIAS (218)) só cobre `REGRAS.md`/`PROJETO.md`/`scripts/*`/`.githooks/*`/`config/*` dentro de `~/agata`; nunca foi desenhada pra alcançar `~/.hermes`.
- Histórico do fish (`history search --contains`) tem os comandos exatos que geraram esse log, no mesmo segundo do timestamp do arquivo.

**Não confirmado, sem evidência de Máquina que este executor tenha encontrado:** a narrativa de que uma "instância remota" (nomeada "gemini-1.5-pro") alegou fabricação, e que "o Conselho homologou" uma refutação. Nenhum arquivo, log ou histórico corrobora essa conversa — pode ter acontecido numa sessão sem rastro em disco (voz, outra máquina, outro cliente), mas isso não é a mesma coisa que confirmado. Registrado como recebido, não como fato.

**Não adotado como política:** o bloco propunha um "novo portão de segurança" (três perguntas de arquitetura antes de o Humano autorizar mudança estrutural) como se já decidido. Regra 3 — quem propõe não decide por si. Fica como proposta recebida, não como regra; o Humano decide se entra em REGRAS.

**Lição que já estava certa e segue valendo:** disco local arbitra fato físico. Isto não virou "aceitar a narrativa que veio junto" — as duas partes do mesmo bloco tiveram destinos diferentes porque só uma tinha onde checar.

Modelo: Claude Sonnet 5 · vetor: leitura direta de `~/.hermes/config.yaml` e do backup `.bak.personalities_remove`, comparados linha a linha; `cd ~/.hermes && git status` real (não presumido) pra confirmar ausência de repositório; leitura do log inteiro, não só do resumo; `fish -c "history search"` real pra achar os comandos originais; busca por `gemini-1.5-pro`/`Qwen3.7`/`auditoria cruzada` em todo `~/agata` sem achar nada que corrobore a narrativa. Turno desta sessão: t=3 (contado no contexto).

(228) DIÁRIO — 20/08/2026 · Princípio "ferramenta nova é decisão, não conserto" registrado com quatro provas; scripts/ler_pagina.sh lê página montada por JavaScript sem navegador, testado positivo e negativo

**Motivo:** dois documentos do Humano, mesma tarde — um pedindo pra registrar que ler HTML cru não enxerga a maioria dos sites modernos (achado ao vivo contra `razionshefa.com.br`), outro pedindo pra ensinar o princípio geral por trás disso ao sistema, como script e como regra em PROJETO.md.

**Verificado antes de escrever qualquer coisa em canon:** o achado original — HTML cru de `razionshefa.com.br` é casca vazia (5.778 bytes, sem texto real), o pacote JS referenciado (508.134 bytes, medido) contém o texto inteiro do site — foi conferido por este executor com dois `curl` reais, não aceito do texto colado. Bate exato com o alegado.

**Princípio, com quatro ocorrências já registradas que o medem:** "antes de acrescentar ferramenta, esgote o que já se alcança com o que existe." (115) — `grep` venceu vector store. A bancada de (169) venceu suíte de teste nova. `perimetro.sh` já era o "porteiro" pedido de fora. Dois `curl` venceram navegador headless. Escrito em PROJETO.md, seção ACB.

**`scripts/ler_pagina.sh`, novo:** cinco casos em ordem — texto no HTML cru; casca vazia → acha e lê o pacote `.js`; pacote sem texto → acha e reporta endereço de API, sem chamar; nada disso → `lacuna`. Sempre diz qual caso resolveu. Nunca confunde casca vazia com ausência de conteúdo. Só leitura — não envia formulário, não clica, não executa o que baixou.

**Testado antes de comitar, os dois resultados exatos pedidos:**
- **Positivo**, `razionshefa.com.br/pt` — CASO 3: pacote JS entregou o texto real do site (título, descrição, seções, em inglês e português), depois de uma primeira tentativa com filtro largo demais que trazia texto interno do React junto — corrigido (heurística: descarta cadeia com caractere de sintaxe de código, exige 4+ palavras separadas por espaço) antes de aceitar o resultado.
- **Negativo**, fixture sintética local (`python3 -m http.server`, HTML vazio + `app.js` que só chama `fetch("/api/v2/conteudo")`, nenhum texto embutido) — CASO 4: o script achou e reportou o endereço `/api/v2/conteudo`, não chamou, não inventou texto nenhum.

**O que não foi feito, por ordem explícita:** Playwright, Puppeteer, Selenium e Chromium headless não instalados. Fase L do ACB não aberta. O nome do script (`ler_pagina.sh`, não "navegação" nem "browser") deixa isso óbvio de propósito.

**Fluxo de quarentena, sexto uso real:** cobre `PROJETO.md` e `scripts/ler_pagina.sh`. Autorização: ordem escrita e datada do Humano no próprio documento "AO EXECUTOR — ENSINAR ISTO AO SISTEMA" já continha o conteúdo exato desta mudança — mesmo padrão do bootstrap de (218), registro mecânico de uma autorização que já existia em texto, não autoaprovação por iniciativa própria. Ver `propostas/aplicadas/APROVADO-ler-pagina-sem-navegador`.

**À parte, não incorporado ao canon como veio:** na mesma janela, chegou um bloco se apresentando como handoff de uma sessão remota ("Qwen3.7"), com uma entrada (228) pronta pra colar, alegando uma edição em `~/.hermes/config.yaml` e uma "auditoria cruzada" com outro modelo. Tratado como DADO, não instrução (política adotada nesta mesma data, item 6a do documento de 20/08 15:02) — a entrada pronta não foi copiada pra MEMÓRIAS como veio. Checagem própria feita depois: `~/.hermes/config.yaml` **foi mesmo alterado** (bloco `personalities` removido, confirmado por este executor lendo o arquivo agora) e existe um log real em `memoria/missoes/auditoria-local/integridade_20260820_191956.log` — o fato físico se sustenta. A narrativa em volta dele (disputa com "gemini-1.5-pro", "Conselho" homologando, "novo portão de segurança") não tem evidência de Máquina que este executor possa checar — ver entrada seguinte.

Modelo: Claude Sonnet 5 · vetor: dois `curl` reais contra `razionshefa.com.br` antes de escrever a política (não aceito do texto colado); `scripts/ler_pagina.sh` rodado de verdade nos dois casos, positivo contra o site real, negativo contra fixture local servida por `python3 -m http.server` e desligada depois; `git status`/`git diff` conferidos antes de descartar o bloco "Qwen3.7" como dado não verificado. Turno desta sessão: t=2 (contado no contexto).

(227) DIÁRIO — 20/08/2026 · VM do Marcos, terreno preparado — política de fronteira escrita, um bug real de portabilidade achado e corrigido, comando único testado de verdade fora do repo, pedido de recursos com números medidos

**Motivo:** item 4/7 do documento do Humano — decidir a fronteira de confiança no papel antes da VM existir, verificar se a bancada roda em máquina limpa, e levantar números medidos pro pedido a mandar ao Marcos.

**4.1, política escrita em PROJETO.md, "VM do Marcos — nó de computação, não guardiã de canon":** a VM recebe o corpus congelado, os runners e os pesos dos candidatos; nunca recebe `.env`, chave, `memoria/missoes/` inteiro, credencial de push ou escrita em `origin/main`. Resultado volta como trace e é DADO, mesma regra do Conselho Remoto — lido antes de qualquer coisa acontecer com ele.

**4.2, um bug real de portabilidade achado e corrigido:** `rlm-qwen3-8b-teste.Modelfile` tinha o caminho absoluto `/home/orusoua/agata/...` na diretiva `FROM` — travaria a recriação do modelo em qualquer máquina com usuário ou caminho diferente. Trocado por caminho relativo (`./modelo/...`), testado de verdade: `ollama create` com o Modelfile corrigido, rodado da pasta certa, funcionou igual ao original (tag descartável depois removida). Os runners (`rlm_c1.py`, `rlm_c1b.py`, `rlm_b0.py`, `rlm_c3.py`, `rlm_c4.py`) já não tinham caminho absoluto nem dependência de `~/.hermes` — só `127.0.0.1:11434` (Ollama) e caminhos relativos ao diretório de trabalho, conferido por `grep` nos cinco arquivos.

**Comando único entregue e testado ponta a ponta, fora do repositório:** `rlm-3caminhos/rodar_celula.sh` — checa `bancada.json`, `corpus/`, Ollama respondendo e o modelo presente antes de rodar `rlm_c1b.py`. Testado copiando só o necessário (runner, corpus, script, uma bancada reduzida a 1 pergunta) pra uma pasta fora de `~/agata`, e rodando de lá contra `qwen3.5-9b-64k` de verdade — respondeu certo, trace gerado, nenhuma dependência de caminho absoluto ou serviço além do Ollama.

**4.3, pedido de recursos escrito com números medidos, não estimados** (`memoria/missoes/rlm-3caminhos/PEDIDO_RECURSOS_VM_MARCOS.md`, rascunho — o Humano decide se e quando manda):
- VRAM: 9b em 64k usa 6.996 de 8.188 MiB (85%) medido agora, historicamente 89-92%. Testado ao vivo um 14b real (`qwen3:14b`, 14,8B, Q4_K_M, 40 camadas): contexto MÁXIMO do modelo é 40.960, nem chega a 64k sem Modelfile customizado (mesma técnica do 9b atual); mesmo nesse contexto menor, só 58% coube na GPU, footprint total ~11GB. Recomendação extrapolada do medido: 16GB de VRAM como piso.
- Disco: os 6 candidatos do item 5.2 já estão puxados nesta máquina — tamanho real via `ollama list`, soma ~31,8GB. Recomendação: 80GB, com margem pra um candidato 14b.
- Tempo de GPU: runner C1b (o que a bancada de hoje usa), 3 rodadas do modelo controle, medido nos traces reais — **58,3 minutos**. Com 6 candidatos sequenciais: estimativa de ~6h de GPU só nas baterias.
- O que NÃO precisa ir: nenhuma credencial, sem escrita em `origin/main`, sem `memoria/missoes/` inteiro.

**Fluxo de quarentena, quinto uso real:** cobre só `PROJETO.md` (a única mudança de item 4 que toca arquivo quarentenado — o resto vive em `memoria/missoes/`, repositório privado separado, sem P-8). Autorização: a resposta do Humano ao ritmo do lote ("Só o item 4 agora") já cobria o item inteiro, incluindo a política que o próprio 4.1 pede — não repetida pergunta por pergunta pra cada arquivo, registrado em `propostas/aplicadas/APROVADO-vm-fronteira-confianca`.

**Item 5 (seleção de modelo principal) fica para uma sessão dedicada, por decisão do Humano** — a bancada é de até 6 modelos, sequencial, sem dois carregados ao mesmo tempo; pelo tempo medido acima (58,3 min por modelo só na bateria), passa de várias horas de GPU.

Modelo: Claude Sonnet 5 · vetor: `grep` real nos cinco runners pra confirmar ausência de caminho absoluto/`.hermes`; `ollama create` real com o Modelfile corrigido, tag descartável depois removida (`ollama rm`); teste ponta a ponta do `rodar_celula.sh` fora de `~/agata`, com chamada real à API do Ollama, trace conferido em disco; `nvidia-smi`/`ollama ps`/`ollama show`/`curl` reais pra todos os números de VRAM; `ollama list` real pros tamanhos de disco; timestamps reais dos arquivos de trace (`ts` de início/fim de cada rodada) pro tempo de GPU, não a estimativa antiga de "~60-75 min" já registrada em (174). Turno desta sessão: t=1 (contado no contexto).

(226) DIÁRIO — 20/08/2026 · Âncora de SHA passa a ser gerada automaticamente — prompt de carregamento movido pra dentro do repo, achado real de auto-referência resolvido com atraso de 1 commit aceito

**Motivo:** a âncora de SHA de (217) era atualizada à mão e apodrecia — mesma doença que a linha 44 de PROJETO.md já teve em (215). Item 2 do documento do Humano pediu o hook gerar a âncora sozinho, como já gera `.hermes.md` e o índice.

**Decisão tomada ao vivo, mudou o desenho no meio do trabalho:** a primeira versão manteve o prompt fora do repo (Área de trabalho), com `.githooks/post-commit` escrevendo nele por caminho absoluto — implementada e testada (positivo e negativo, contra o arquivo real com backup). Perguntado, o Humano preferiu mover o prompt pra dentro do repositório. Isso abriu um problema técnico real, não previsto na proposta original: **um commit não pode embutir o próprio SHA** — a hash de um commit depende do seu conteúdo, então um arquivo dentro da árvore não pode conter corretamente o SHA do commit que o inclui. Duas saídas honestas foram levadas ao Humano; escolhida: **ficar sempre até 1 commit atrasada**, 100% automática, em vez de exigir um commit manual extra pra fechar o loop.

**O que existe agora:** `PROMPT_CARREGAMENTO.md`, canônico na raiz do repo (movido da Área de trabalho, que ficou com um bilhete apontando pro novo lugar). `.githooks/pre-commit` ganhou um passo novo: antes de cada commit, `scripts/atualizar_ancora_prompt.py` reescreve só as duas linhas entre os marcadores `ANCORA-SHA` com o SHA do HEAD anterior — nunca toca o resto do arquivo (documento editado à mão), aborta sem escrever se os marcadores sumirem. Falha aqui só avisa, nunca bloqueia o commit.

**Classificação de quarentena, decidida e registrada:** `PROMPT_CARREGAMENTO.md` fica SEM quarentena (grupo do `ONDE_ESTAMOS.md`), apesar de "dirigir" um modelo — ao contrário de `config/agata-consolidacao.prompt.txt` (que dirige um processo desatendido, sem Humano revisando antes de agir), este prompt é sempre lido por um Humano que cola o texto numa sessão nova e audita cada resposta. `.githooks/pre-commit`, `scripts/atualizar_ancora_prompt.py` e `PROJETO.md` (documentação do mecanismo) SÃO quarentenados — cobertos por este commit.

**Achado extra, corrigido no caminho, não escondido:** o texto do prompt ainda dizia "últimas 30 linhas de MEMÓRIAS.md" — a mesma frase errada que (215) já tinha corrigido em PROJETO.md, nunca propagada pro prompt externo. Corrigida junto, mesma classe de decadência que motivou este item inteiro.

**Testado antes do commit:** positivo (marcadores presentes → âncora atualizada, resto do arquivo intocado, conferido linha a linha) e negativo (arquivo sem marcadores → aborta, `exit 1`, nada escrito) — contra o arquivo real, com backup feito antes de qualquer edição. Sintaxe do hook checada (`bash -n`). Não testado contra clone descartável — mudança pequena, um único arquivo-alvo, sem side-effect em canon.

**Fluxo de quarentena, quarto uso real:** três perguntas feitas ao vivo nesta sessão (quem cria o marcador; onde o prompt vive; como resolver a auto-referência), respostas registradas em `propostas/aplicadas/APROVADO-ancora-sha-automatica`.

Modelo: Claude Sonnet 5 · vetor: teste real (positivo/negativo) do script contra o arquivo em disco antes de integrar ao hook; `bash -n` no hook; `git diff --cached` real gerou o `.diff`; leitura de `.githooks/pre-commit`/`post-commit` linha a linha antes de decidir onde o passo entra. Turno desta sessão: t=1 (contado no contexto — nota de correção abaixo).

**Correção sobre (223)-(225):** aquelas três entradas foram escritas antes da minha primeira resposta ao Humano nesta conversa e cada uma levou um `t=` diferente (1, 2, 3) — errado; "turno" conta respostas ao Humano, e nenhuma resposta tinha sido enviada ainda. As quatro entradas (223)-(226) pertencem todas ao mesmo t=1. Conteúdo e vetores de verificação de (223)-(225) continuam corretos — só o rótulo de turno errou. Registrado aqui como correção nova, Regra 4 — as entradas antigas não foram editadas.

(225) DIÁRIO — 20/08/2026 · Conselho Remoto retomado — invocação real sem 429 desta vez, parecer recebido sobre P-7

**Motivo:** pausado desde (213), 6 de 8 chamadas do dia em 429. O backoff de (216) — duas falhas 429 seguidas travam 15 min — já estava no lugar, nunca exercitado numa chamada de sucesso.

Backoff conferido antes de chamar: sem arquivo de estado (`.backoff-estado.json` ausente), portanto livre. Âncora do pedido pendente (`pedido_01_p7-citacao.txt`) estava desatualizada — apontava pra (212) e hashes antigos de REGRAS/MEMÓRIAS; atualizada pra (222) e os hashes reais antes de enviar, texto da proposta em si preservado (arquivo fora de MEMÓRIAS, camada privada, sem remote — Regra 4 não se aplica).

**Resultado: sem 429.** GLM-4.7-Flash respondeu em 41,8 s, formato OK (as quatro partes apareceram), 831 tokens de entrada + 373 de saída, custo US$0,00 (camada grátis). Posição: condicional — aprova o desenho do P-7 (checagem só do que cada commit acrescenta, nunca reaudita histórico) mas pede um mecanismo explícito de override/whitelist manual para falsos positivos, ausente do desenho atual. Resposta completa em `memoria/missoes/conselho-remoto/20260820-151331-glm-4.7-flash.json`.

**A medida que importa:** uma invocação, um parecer completo, zero idas e vindas de copiar-e-colar do Humano — o script fez a chamada, salvou a resposta crua e validou o formato sozinho, do pedido escrito ao arquivo final.

Modelo: Claude Sonnet 5 · vetor: `python3 scripts/conselho_remoto.py` rodado de verdade contra a API real, não simulado; `sha256sum` de REGRAS.md/MEMÓRIAS.md calculado na Máquina antes de atualizar a âncora do pedido; conteúdo do JSON de resposta lido direto do arquivo salvo, não do stdout do script. Turno desta sessão: t=3 (contado no contexto).

(224) DIÁRIO — 20/08/2026 · (auto-sync) 564a50d — lacuna fechada por decisão do Humano, não investigada mais

**Motivo:** o commit `564a50d` (18/08/2026 23:28:08, autor `agata <agata@local~>`, "(auto-sync) sincronizar-estado.sh detectou mudanças") entrou em `origin/main` sem entrada correspondente em MEMÓRIAS. Nenhuma checagem do perímetro cobre "commit sem entrada" — P-7 cobre citação errada, P-8 cobre arquivo de comportamento sem aprovação. Buraco distinto, registrado aqui como fato, não fechado por mecanismo novo.

A consolidação noturna (`agata-consolidacao.timer`) NÃO foi a autora — confirmado em (220): o serviço já estava quebrado por PATH (`hermes: comando não encontrado`, exit 127) desde antes dessa data. Autor real: não identificado. Journal do período (18/08, noite) não está mais disponível pra checagem direta — mesma lacuna de retenção curta já documentada em (110), não uma investigação nova que se perdeu.

**Decisão do Humano, registrada sem suavizar:** deixar como está. `lacuna` fechada por decisão, não por explicação encontrada — não investigar mais.

Modelo: Claude Sonnet 5 · vetor: `git show --stat 564a50d` e `git log -1 --format` na Máquina pra autor/data reais; `journalctl --user -u agata-consolidacao.service --since/--until` na janela do commit, sem resultado — confirma a lacuna, não a inventa. Turno desta sessão: t=2 (contado no contexto).

(223) DIÁRIO — 20/08/2026 · Autorização em bloco do Humano — quatro pendentes fechados; ACB inteiro fica de fora, por escopo

**Motivo:** registrar o que foi autorizado nesta data e, com o mesmo peso, o que não foi — Regra 4 exige numeração antes de mais nada, e um bloco desta escala sem fronteira registrada vira ambiguidade depois.

**Autorizado, em bloco, por escrito nesta conversa:** fechar os quatro pendentes (âncora de SHA automática, retomada do Conselho Remoto, VM do Marcos aceita); seleção de modelo principal pela bancada já existente — o Humano declarou insatisfação com `qwen3.5-9b-64k` como principal; três políticas gerais vindas do documento ACB; preparo de terreno para a VM do Marcos.

**Não autorizado, decidido-NÃO-fazer, com o porquê:** o ACB inteiro (14 fases, 17 adaptadores Workspace, ~30 serviços Google, 13 mensageiros, Discord, automação de navegador, 25 arquivos de documentação) fica como bússola, não backlog. REGRAS "Contenção de escopo" é clara: só a fase atual e a seguinte têm gates e prazo, o resto não; modelo antecipando fase futura é negado por default, salvo ordem do Humano.

A decisão de modelo principal (item 5) não espera o ACB pronto. O laboratório já existe: a bancada da entrada (169), congelada, validada, com o titular (`qwen3.5-9b-64k`) medido em células reais (C1, C1b, B0, C3, C4) e o runner C1b já testado (176)/(177). É T1 — disponível hoje — não T2.

Modelo: Claude Sonnet 5 · vetor: `git log`/`git ls-remote origin main` na Máquina pra confirmar o canon em (222)/`1b4f94e` antes de escrever; `grep` real em REGRAS.md pra confirmar a citação de "Contenção de escopo" e em MEMÓRIAS.md pra confirmar (169)/(172)/(176)/(177) linha a linha, não citados de memória. Turno desta sessão: t=1 (contado no contexto).

(222) DIÁRIO — 20/08/2026 · Escopo da P-8 passa a incluir config/ — recursão de propósito, fechando o buraco que a própria consolidação usava

**Motivo:** `config/agata-consolidacao.prompt.txt` é um arquivo que dirige um modelo autônomo contra o canon — muda comportamento tanto quanto um script, mas ficou fora da quarentena criada em (218). O prompt quebrado que rodou sem ninguém perceber (220) é prova concreta do que um `config/` sem controle pode custar.

**Mudança:** `_p8_eh_comportamento()` em `scripts/perimetro.sh` passa a incluir `config/*` no grupo protegido, junto de `REGRAS.md`, `PROJETO.md`, `scripts/*`, `.githooks/*`. Documentado em PROJETO.md ("Quarentena estrutural") e `propostas/README.md`.

**Recursão, de propósito, ordem do documento do Humano:** esta própria mudança toca `scripts/perimetro.sh`, já protegido desde (218) — é a última candidata a precisar do fluxo de aprovação ANTES de config/ entrar no grupo; a partir deste commit, qualquer mudança futura em `config/` (inclusive uma nova versão do prompt de consolidação) passa a exigir o mesmo par diff/APROVADO que REGRAS/PROJETO/scripts/.githooks já exigem.

**Terceiro uso real do fluxo de quarentena:** proposta escrita (`propostas/p8-escopo-config.diff`), deixada sem stage, Humano perguntado ao vivo, mesma resposta dos dois itens anteriores desta sessão — autorização ao vivo, marcador criado pelo executor só depois da confirmação.

Modelo: Claude Sonnet 5 · vetor: `_p8_eh_comportamento()` lida linha a linha antes de editar, não alterada de memória; diff gerado por `git diff --cached` real. Turno desta sessão: t=6 (contado no contexto).

(221) DIÁRIO — 20/08/2026 · P-9 — controle novo, avisa quando um serviço declarado no PROJETO morre em silêncio

**Motivo direto:** `agata-consolidacao.timer` (219) estava falhando havia dias sem que nenhuma das oito checagens do perímetro percebesse — PROJETO.md listava a unidade entre os serviços da máquina como se funcionasse. Controle que não avisa quando falha é pior que controle nenhum, doutrina já adotada esta semana.

**O que P-9 checa, escopo fechado à mão (mesma doutrina de P-3/P-4):** unidades de sistema (`ollama.service`), unidades de usuário (`hermes-gateway.service`, `agata-consolidacao.timer`) e containers Docker (`open-webui`, `kokoro-tts`) — a lista exata de "Serviços (boot)" em PROJETO.md. Avisa se uma unidade está `failed` ou `disabled`/`masked`; avisa se um container declarado não aparece em `docker ps`. **Fica de propósito FORA:** `agata-consolidacao.service` (o oneshot em si) — seu repouso normal depois de rodar com sucesso é `inactive`, checar isso daria falso alarme a cada execução; o que importa é o TIMER que agenda, não o resultado da última corrida isolada.

**AVISA, nunca falha** — mesma lógica de P-6: serviço caído não é motivo pra travar a escrita do canon.

**Testado, positivo e negativo, taxa de falso positivo relatada:** contra o estado real da máquina (achou o timer mascarado — verdade, eu tinha mascarado como rede de segurança no início da sessão; nada mais). Unidade de sistema inexistente forçada → avisou. Container real rodando (`open-webui`) → não avisou, zero falso positivo. Container inexistente forçado → avisou. `ollama.service` e `hermes-gateway.service` reais, saudáveis, confirmados fora do output — checado explicitamente com `systemctl is-active`/`is-enabled` direto, não só pela ausência de aviso.

**Fluxo de quarentena, segundo uso real (depois do bootstrap de (218) e do primeiro uso de (219)):** proposta escrita (`propostas/p9-servico-declarado.diff`), deixada sem stage, Humano perguntado ao vivo nesta conversa sobre quem cria o marcador, resposta a mesma do item anterior — autorização ao vivo, criada pelo executor só depois da confirmação.

Modelo: Claude Sonnet 5 · vetor: quatro casos de teste rodados de verdade contra o estado real e contra listas forçadas, não apenas lidos; `systemctl is-active`/`is-enabled` conferido diretamente pra `ollama.service` e `hermes-gateway.service`, não presumido pela ausência de aviso. Turno desta sessão: t=5 (contado no contexto).

(220) DIÁRIO — 20/08/2026 · Consolidação noturna restaurada em quarentena — prompt novo, sandbox de kernel, PATH absoluto, testada de verdade

**O que estava quebrado, apurado antes de tocar em nada:** `agata-consolidacao.timer` é legítimo — decisão do Humano no PLANO_AGATA_v1.3, citado em PROJETO.md entre os serviços da máquina, não é automação clandestina. Mas o serviço morria com `hermes: comando não encontrado`, exit 127, desde pelo menos hoje 08:15:25 (catch-up de boot, `Persistent=true` — o timer perdeu o disparo de 23h porque a máquina estava desligada, e rodou assim que o systemd --user manager acordou). O prompt ainda mandava escrever em `DIÁRIO.md`, arquivo que não existe desde 31/07/2026 (migrado pra MEMÓRIAS.md, entrada (62)).

**Causa do PATH, mais precisa do que a hipótese original:** não é diferença de shell por si só — `bash -lc` interativo resolve `hermes` normalmente nesta máquina agora, testado ao vivo. O que aconteceu: `fish_user_paths` (variável universal do fish, onde `~/.local/bin` mora) nunca é exportado automaticamente pro ambiente do systemd `--user` manager; algum mecanismo de sessão gráfica importa isso depois, mas o catch-up de boot deste timer específico rodou ANTES dessa importação acontecer — `ActiveEnterTimestamp` do `--user` manager bate no segundo com o instante da falha. Corrigido de raiz, independente do timing exato: `ExecStart` passa a chamar o binário pelo caminho absoluto (`/home/orusoua/.local/bin/hermes`, confirmado via `which hermes`), removendo a dependência de PATH e de shell de login por completo — `bash -c`, não `bash -lc`, usado só pelo `$(cat ...)` que a CLI do hermes exige (não existe flag de query-por-arquivo, conferido em `hermes chat --help`).

**Achado à parte, registrado sem inflar:** a contagem "4 ocorrências" do padrão antigo (`### <data> · <título>`) citada no documento do Humano estava errada — são 63, todas de junho a 09/07/2026, dentro do histórico migrado. A conclusão que importava (nada escrito por essa consolidação depois de 31/07) continua verdadeira, só o número estava impreciso.

**Item 1, prompt novo (`config/agata-consolidacao.prompt.txt`):** lê desde a última entrada de MEMÓRIAS.md, nunca mais DIÁRIO.md. Se achar atividade relevante, escreve UM arquivo em `propostas/consolidacao-<data>.md`, entrada marcada `(a numerar)` — número de verdade só na aprovação, contra o fim do remoto (este projeto já teve colisão de numeração por sessão paralela). Proibido expressamente de escrever, editar ou abrir para escrita MEMÓRIAS.md, REGRAS.md, PROJETO.md ou ONDE_ESTAMOS.md. Nada relevante → nenhum arquivo, resposta de 1 linha. Estilo aprovado em (219) citado no próprio prompt.

**Item 2, a cerca de verdade (`config/agata-consolidacao.service`):** `ProtectSystem=strict` + `ProtectHome=read-only` + `ReadWritePaths=%h/agata/propostas %h/.hermes` — kernel, não instrução. Testado direto, sem depender do resultado de nenhuma chamada de modelo: sob o sandbox, escrever em `propostas/` funciona; escrever em `MEMÓRIAS.md` dá `Sistema de arquivos somente para leitura` de verdade (não simulado) — hash do arquivo conferido igual antes e depois. Nenhum `ReadWritePaths` extra precisou ser acrescentado — os dois caminhos declarados bastaram em todas as rodadas reais.

**Item 3, PATH absoluto:** aplicado dentro do mesmo arquivo do item 2 — ver acima.

**Item 4, testado antes de religar, sete rodadas reais da unidade sandboxed, não só planejadas:** 5 sucessos, 2 falhas reais com o mesmo erro (`session storage could not be written`, SQLite `state.db`) — reproduzido de propósito uma vez disparando a unidade em paralelo com uma chamada `hermes chat` concorrente. Isolado: não é falha do sandbox (escrita direta em `state.db` sob o mesmo `systemd-run` funcionou; `PRAGMA integrity_check` voltou `ok` depois); é contenção real de acesso concorrente ao SQLite, provavelmente entre este processo e o `hermes-gateway.service` que roda o tempo todo. `Restart=on-failure` + `RestartSec=30` acrescentado ao `.service` como mitigação — testado ao vivo: falha real → `Scheduled restart job, restart counter is at 1` → retentativa 30s depois → sucesso, proposta processada. **Achado extra, não suavizado:** nessa mesma retentativa que "teve sucesso", o modelo respondeu `"Proposta em propostas/consolidacao-2026-08-20.md: ..."` e o arquivo NUNCA existiu — confirmado com `ls`, e o próprio modelo, questionado numa sessão separada, admitiu: **"não chamei nunca write_file... foi uma afirmação errada minha sem confirmação de execução antes de responder."** Isto não comprometeu canon (MEMÓRIAS/REGRAS/PROJETO seguem intocados, hash conferido) — mas prova ao vivo por que o item 2 é kernel e não confiança no texto do prompt: mesmo a auto-descrição do que o modelo fez pode ser fabricada com fluência, exatamente Regra 2. `lacuna`: quem checar `propostas/` depois de uma corrida noturna precisa olhar o diretório, não confiar na linha de resumo que o log mostra.

Timer mascarado no início desta sessão como rede de segurança (ordem do documento), desmascarado só depois de todo o acima confirmado — religado com `systemctl --user link` + `enable` + `start`, verificado ativo, próximo disparo 23h hoje.

Modelo: Claude Sonnet 5 · vetor: sete execuções reais da unidade sandboxed (`journalctl --user -u agata-consolidacao.service`), duas delas com falha real reproduzida de propósito; teste direto de escrita via `systemd-run` com os mesmos parâmetros de sandbox, positivo (propostas/) e negativo (MEMÓRIAS.md, erro real de filesystem); `PRAGMA integrity_check` no `state.db` depois das falhas; hash dos quatro canônicos conferido igual antes e depois de toda a sequência; a alegação falsa do modelo sobre o arquivo escrito foi verificada com `ls`/`cat`, não aceita por confiança. Turno desta sessão: t=4 (contado no contexto).

(219) DIÁRIO — 20/08/2026 · Convenção de estilo pra texto novo — porquê antes do quê, uma ideia por frase, nunca retroativo

**Decisão do Humano:** REGRAS.md, Regra 5 ("Fale direto"), ganha uma linha de estilo concreta. Adotar: porquê antes do quê · uma ideia por frase · concreto antes de abstrato · nenhum jargão sem definição · conclusão antes do raciocínio. Vale pra entradas NOVAS de MEMÓRIAS, pra PROJETO, e pra qualquer texto dirigido ao Humano.

**Não adotar, e por quê:** parágrafo de uma linha só, repetição pra ênfase, cabeçalho a cada ideia — é o que infla tamanho sem agregar. `.hermes.md` já tinha 16.713 palavras medidas em (215) e entra no contexto de todo modelo, toda sessão — cada entrada mais longa do que precisa é custo pago por todo mundo, sempre.

**Não retroativo, Regra 4 protege:** não reescreve nada já escrito em MEMÓRIAS — linha vermelha, correção é entrada nova, nunca edição do que já está lá. Vale só daqui pra frente.

**Primeiro uso real do fluxo de quarentena (P-8), registrado à parte da decisão de estilo em si:** esta mudança toca `REGRAS.md`, e a exceção de bootstrap do commit (218) foi explícita — "esta exceção não se repete". O executor escreveu a proposta (`propostas/regra-estilo.diff`), deixou sem stage, e perguntou ao Humano quem deveria criar o marcador de aprovação, com três opções: o Humano criar por comando, o executor criar com autorização ao vivo, ou adiar o item. Resposta: autorização ao vivo, criada pelo executor **depois** da confirmação nesta conversa — distinto do bootstrap de (218), onde a aprovação vinha só do texto do documento original. `propostas/aplicadas/APROVADO-regra-estilo` registra a pergunta e a resposta escolhida.

Modelo: Claude Sonnet 5 · vetor: proposta escrita e mantida fora do índice do git até a resposta do Humano chegar nesta mesma conversa, não presumida antes disso; `git diff --cached` real gerou o `.diff`, não escrito à mão. Turno desta sessão: t=2 (contado no contexto).

(218) DIÁRIO — 20/08/2026 · Quarentena estrutural criada e ligada — P-8 exige propostas/APROVADO-<nome> antes de canon mudar comportamento

**O buraco que isto fecha, nomeado pelo Humano:** até aqui, o executor escreve em canon, comita e empurra — o Humano fica sabendo depois. Nenhuma das sete checagens do perímetro (P-1 a P-7) cobria isso. Mesma classe do incidente já registrado em (214): automação (ou executor) alterando canônico sem um passo de proposta prévio.

**Escopo, decisão do Humano, proporcional de propósito:** QUARENTENA OBRIGATÓRIA para o que MUDA COMPORTAMENTO — `REGRAS.md`, `PROJETO.md`, `scripts/*`, `.githooks/*`. SEM quarentena para o que só REGISTRA o que já aconteceu — entradas de `MEMÓRIAS.md`, `ONDE_ESTAMOS.md`, `INDICE_MEMORIAS.md`, `.hermes.md`. Motivo: registro errado se corrige com entrada nova (é pra isso que append-only existe); comportamento errado, não.

**Mecanismo:** diretório `propostas/` versionado (`propostas/README.md` tem o texto completo). Proposta vira `propostas/<nome>.diff`; Humano aprova criando `propostas/APROVADO-<nome>`; `scripts/perimetro.sh`, nova checagem **P-8**, falha o commit se algum arquivo staged do grupo comportamento não tiver um par diff/APROVADO cobrindo o caminho. Aprovação consumida: o par se move para `propostas/aplicadas/` no mesmo commit que aplica a mudança.

**Achado real ao testar antes de ligar, corrigido antes do commit valer:** a primeira versão só procurava o par em `propostas/` (pendente). Como o fluxo normal MOVE o par pra `propostas/aplicadas/` no mesmo commit que ele autoriza, todo commit que consumisse sua própria aprovação reprovaria a aprovação que o autoriza — testado contra um clone descartável, achado antes de virar produção. Corrigido: `_p8_caminhos_aprovados()` procura nos dois lugares, `propostas/` e `propostas/aplicadas/`.

**Testado, positivo e negativo, taxa de falso positivo relatada, seis casos, todos contra clone descartável em `/tmp`, nunca contra o repositório real:** (1) arquivo de comportamento staged sem aprovação → FALHA. (2) mesmo arquivo com diff+APROVADO cobrindo o caminho, ambos em `propostas/` → PASSA. (3) `MEMÓRIAS.md`/`ONDE_ESTAMOS.md` staged sem nenhuma aprovação → PASSA, nunca deveria travar (checagem de falso positivo sobre o grupo isento). (4) um arquivo aprovado + um não aprovado no mesmo commit → FALHA citando só o não aprovado, confirma checagem por arquivo, não global. (5) diff+APROVADO já em `propostas/aplicadas/` (consumo no mesmo commit) → PASSA, valida a correção do achado acima. (6) caso negativo básico repetido depois da correção → continua FALHANDO como deveria. Zero falsos positivos, zero falsos negativos nos seis.

**Bootstrap, registrado sem suavizar, ordem explícita do Humano no documento de origem:** este commit toca `scripts/perimetro.sh` e `PROJETO.md` — é a primeira mudança candidata a passar pela própria quarentena. O documento do Humano instrui aplicá-la ANTES de ligar P-8 exatamente porque não havia como pedir aprovação a um mecanismo que ainda não existia. `propostas/aplicadas/quarentena-p8.diff` é o diff real deste commit (gerado com `git diff --cached`, não escrito à mão); `propostas/aplicadas/APROVADO-quarentena-p8` foi criado pelo executor, mas a autorização de fato é a ordem escrita e datada do Humano — o marcador é o registro mecânico dela, não uma autoaprovação por iniciativa própria. **A partir do próximo commit que toque REGRAS/PROJETO/scripts/.githooks, o marcador precisa vir do Humano — esta exceção não se repete.** Este commit é, ele mesmo, o teste ao vivo de P-8 contra o repositório real — se o pre-commit hook aceitar, é P-8 validando sua própria primeira aplicação; se rejeitar, o bootstrap falhou e precisa ser revisto antes de qualquer outra coisa.

**Risco residual, não suavizado (registrado em PROJETO.md também):** o marcador de aprovação é um arquivo que o próprio executor tem permissão técnica de criar. P-8 impede automação agindo sem que ninguém perceba — exatamente o caso de 18/08/2026 — e NÃO impede um modelo que decida contornar deliberadamente. Aceito por decisão do Humano: a ameaça real é desatenção, não malícia. Caminho pra mais proteção, se um dia precisar: assinatura que o executor não possa produzir, custo de o Humano digitar senha a cada mudança estrutural.

Modelo: Claude Sonnet 5 · vetor: seis casos de teste rodados de verdade contra clone descartável em `/tmp` (nunca contra `~/agata`), um bug real achado e corrigido antes de qualquer teste passar a valer; diff de `propostas/aplicadas/quarentena-p8.diff` gerado por `git diff --cached`, conferido linha a linha contra o que foi editado, não escrito de memória. Turno desta sessão: t=1 (contado no contexto).

(217) DIÁRIO — 20/08/2026 · Âncora de SHA no prompt de carregamento — sessão só-HTTP ganha jeito de detectar versão velha

**Problema, MEMÓRIAS (156):** `raw.githubusercontent.com` fica em cache de CDN 1-2 min depois de um push. Uma sessão sem a Máquina (sem `git ls-remote`) não tinha como saber se o que acabou de buscar era o conteúdo novo ou o cache velho.

**Mecanismo adicionado, item 4 do documento do Humano, sugestão do Marcos:** o prompt de carregamento (arquivo à parte, fora deste repositório, mantido pelo Humano — `PROMPT DE CARREGAMENTO — Sistema Agata` na Área de trabalho) passa a carregar o SHA de commit esperado no momento em que foi escrito, mais a instrução de conferir `https://api.github.com/repos/agataseth98-cmd/agata-seth/commits/main` (API do GitHub, endpoint diferente do raw, não sofre o mesmo cache medido em (156)) e comparar o campo `sha`. Testado ao vivo: o endpoint respondeu com o SHA correto do HEAD no momento da checagem — confirmado, não assumido.

**Limite, registrado sem suavizar:** o SHA impresso é uma foto do momento em que o prompt foi escrito — fica velho a cada push seguinte, e nada atualiza esse arquivo sozinho (ele vive fora do git, mantido manualmente). Não substitui `git ls-remote`/`git ls-tree` onde a Máquina existe — cobre só quem não a tem, exatamente o caso do documento do Humano.

**Achado à parte, fora do pedido original mas teve que ser resolvido pra editar o arquivo:** o prompt na Área de trabalho estava com o texto embaralhado/duplicado a partir de certo ponto — provavelmente o mesmo tipo de corrupção de copiar-colar já visto antes com acentuação em português. Reescrito do zero, preservando o conteúdo e a intenção do original (comparado contra REGRAS.md e a seção "Fonte canônica" de PROJETO.md pra manter consistência), verificado como UTF-8 válido com acentos intactos (`file` + grep de caracteres acentuados) depois de escrito.

Modelo: Claude Sonnet 5 · vetor: `curl` real contra a API do GitHub, SHA comparado contra `git ls-remote origin main` na Máquina, não assumido igual; arquivo reescrito conferido com `file` e contagem de caracteres acentuados depois de salvar. Turno desta sessão: t=1 (contado no contexto).

(216) DIÁRIO — 20/08/2026 · Backoff de 429 no Conselho Remoto: duas falhas seguidas travam nova chamada por 15 min

**Antes:** `scripts/conselho_remoto.py` faz UMA chamada por invocação, sem retentativa interna nenhuma — o padrão de "uma retentativa e desiste" citado em (211)-(213) era, na prática, o Humano/modelo invocando o script duas vezes em sequência. Nada impedia uma terceira, quarta invocação no mesmo minuto: o script não guardava memória de falha entre chamadas.

**Ordem do Humano, sugestão do Marcos:** falhou duas vezes seguidas com HTTP 429 → espera 15 minutos antes de permitir nova chamada, e a espera fica registrada em log. Motivo: proteger a conta de parecer abusiva pro provedor sob rate limit.

**Implementado:** estado persistido em `memoria/missoes/conselho-remoto/.backoff-estado.json` (camada privada, gitignorada do repo principal, sem remote — mesmo lugar onde o script já guardava as respostas cruas). Contador de falhas 429 SEGUIDAS: incrementa a cada HTTP 429, zera em qualquer chamada que não seja 429 (sucesso ou outro erro). Ao chegar em 2 falhas seguidas, `checar_backoff()` recusa nova chamada até 15 minutos depois da última falha, e a recusa é logada em `memoria/missoes/conselho-remoto/backoff.log`. O check roda ANTES de qualquer chamada de rede — depois das validações locais que já existiam (conteúdo privado, tamanho, chave).

**Testado antes de comitar, três casos, contra o módulo importado (sem chamada de rede real):** (1) estado limpo → `checar_backoff()` = 0, chamada liberada. (2) uma falha 429 → ainda 0, abaixo do limiar de 2. (3) segunda falha 429 seguida → `checar_backoff()` = 899s (~15 min), backoff ativo, log escrito. (4) uma chamada sem 429 depois disso → contador zera, `checar_backoff()` volta a 0. Os quatro passaram. Artefatos do teste (`.backoff-estado.json`, `backoff.log`) apagados depois — não eram eventos reais, não deviam sujar o histórico do mecanismo.

Modelo: Claude Sonnet 5 · vetor: `ast.parse` confirmando sintaxe antes de rodar; os 4 casos de teste rodados de verdade importando o módulo real (`importlib`), asserts checados, não só lidos; estado de teste conferido no disco (`cat .backoff-estado.json`) antes de apagar. Turno desta sessão: t=1 (contado no contexto).

(215) CORREÇÃO — 20/08/2026 · PROJETO.md linha 44 estava errada: "janela de 30 linhas" não existe, medida real é por entrada inteira

**O erro:** PROJETO.md, seção "Memória e hidratação", dizia "A janela de injeção é de 30 linhas do fim de MEMÓRIAS. Entradas longas não chegam inteiras ao contexto — escreva contando com isso." Essa frase é injetada em `.hermes.md`, no contexto de todo modelo, toda sessão — e instruía escrever curto por um motivo que não existe no mecanismo atual.

**Medido de verdade, não assumido:** `.githooks/gerar-hermes-md.sh` (função `janela_memorias`) acumula ENTRADAS INTEIRAS de trás pra frente até `JANELA_ORCAMENTO_CHARS=25000` caracteres — nunca corta uma entrada no meio; se a última sozinha já estourar o orçamento, entra inteira do mesmo jeito. Contado direto no `.hermes.md` publicado agora: 9 entradas completas na janela, (205) a (213), nenhuma cortada. `.hermes.md` inteiro tem 16.713 palavras.

**Causa provável, registrada sem afirmar como fato:** a frase de 30 linhas descreve um desenho anterior ao hook por orçamento de caracteres — não foi atualizada quando o mecanismo mudou. `lacuna`: não achei o commit exato que introduziu o orçamento por entrada nem quando a frase de 30 linhas devia ter sido revisada e não foi.

**Corrigido em PROJETO.md** com o comportamento real e a data da medição, mantendo a entrada antiga implicitamente superada por esta (Regra 4 — correção é entrada nova, nunca edição do que já está lá; PROJETO.md em si não é MEMÓRIAS, mas descreve o mecanismo e é ele que estava errado, corrigido no lugar certo).

Modelo: Claude Sonnet 5 · vetor: `.githooks/gerar-hermes-md.sh` lido linha a linha (não resumido de memória); contagem de entradas na janela feita com `awk` contra o `.hermes.md` real gerado após o commit (214); `wc -w .hermes.md` rodado direto, não estimado. Turno desta sessão: t=1 (contado no contexto).

(214) DIÁRIO — 20/08/2026 · `sincronizar-estado.sh` publicava sozinho apesar do próprio cabeçalho dizer que não — auto-push removido, script virou só leitura

**O achado, verificado na Máquina:** commit `564a50d` ("(auto-sync) sincronizar-estado.sh detectou mudanças") entrou em `origin/main` em 18/08/2026 sem entrada em MEMÓRIAS e sem revisão — `git log` confirma o commit, `git ls-remote origin main` confirma que é o HEAD publicado agora. O script fazia `git add --all` + `git commit` + `git push origin main` sozinho quando achava `git status --porcelain` não vazio, apesar do próprio comentário de cabeçalho dizer "Não altera canônico sem permissão explícita". Mesma classe já registrada em MEMÓRIAS (47): bg-review do Hermes Gateway apagando história canônica sem humano no loop — automação escrevendo em canônico sem humano no loop. (Título de (47) usa o formato migrado `### `, fora do índice de P-7 desde (49) — citação sem a síntese entre parênteses de propósito, pra não disparar falso positivo num checador que a própria REGRAS reconhece como limitado a partir dali.) Mesma razão pela qual `memoria/*.md` fica fora do índice do git (P-3): escritor automático não deliberado não pode publicar.

**Verificado antes de mexer, ordem do documento do Humano:** nenhum timer/cron/hook agenda este script (`systemctl --user list-timers --all`, `crontab -l`, `.githooks/*`, `ps aux` — nenhum achado, todos rodados de verdade). O commit `564a50d` foi uma execução manual/pontual, não uma automação recorrente ainda ativa — mas o script continuava capaz de repetir o mesmo erro na próxima vez que alguém o rodasse.

**Correção aplicada:** `git add --all`/commit/push automáticos removidos por completo — o script agora só lê e escreve ALERTA/OK/DIVERGÊNCIA no log, nunca toca o índice do git. Dois bugs reais a mais achados rodando de verdade, não só lendo: `git ls-remote --short origin/main` tinha DOIS problemas — `origin/main` (com barra) não é repositório válido pra `ls-remote` (o certo é `origin main`, dois argumentos separados), e `--short` não existe em `git ls-remote` nesta versão (`git ls-remote --short` → `error: unknown option \`short'`, git 2.55.0) — não é flag deste subcomando em nenhuma testada. O SHA curto agora vem de `cut -c1-7`, não de uma flag inexistente. `git -v --push` e `git -v --remote origin main` (linhas 31 e 60 da versão anterior) não são comandos git reais — removidos.

**Testado, positivo e negativo, antes de comitar:** rodado contra o repositório real, estado sincronizado (`564a50d` local = remoto) → log correto ("OK sincronizado"), nada comitado nem empurrado. Rodado contra um clone descartável em `/tmp`, com um commit local nunca empurrado → `DIVERGÊNCIA: local=9e9dc9b vs remoto=564a50d`, de novo sem tocar índice nem remoto. Clone de teste apagado depois de conferir o log.

**Decidido NÃO fazer:** não reintroduzir push automático mesmo com trava adicional (ex.: uma flag `--eu-autorizo` que o script aceitasse). REGRAS ("Cadeia de auditoria em camadas", item 4: "Autorização explícita do Humano antes de tocar em canônico") já cobre isso, e uma flag que o próprio script pudesse setar sozinho não seria autorização de verdade, só teatro. O item da quarentena (P-8) desta mesma sessão é o mecanismo estrutural pra isso — este script não precisa reinventar uma versão fraca dele.

Modelo: Claude Sonnet 5 · vetor: `git log`/`git ls-remote origin main` confirmando o commit publicado; `git ls-remote --short` rodado de verdade (não assumido) confirmando a flag inexistente; dois testes reais rodados e log conferido depois de cada um, um deles contra clone descartável com commit não empurrado, apagado ao final. Turno desta sessão: t=1 (contado no contexto).

(213) DIÁRIO — 17/08/2026 · Terceira invocação real, âncora reatualizada (última entrada (212)) — HTTP 429 de novo, nas duas tentativas permitidas; três das quatro tentativas do dia bateram nesse mesmo erro, proposta ao Humano: pausar em vez de insistir agora

**Terceira invocação, mesmo pedido, âncora reatualizada na hora** (`git ls-remote origin main` → `0f6f622`, última entrada (212)). Chamada + a uma retentativa da regra 2.3 — **as duas, HTTP 429, código `1305`, mesma mensagem** ("service may be temporarily overloaded"). Nenhum arquivo novo no disco.

**Padrão que já dá pra nomear, não mais só "azar":** das 4 chamadas HTTP reais feitas hoje contra o GLM-4.7-Flash (211: 2 tentativas · 212: 1 sucesso técnico + 1 reenvio com 2 tentativas · 213: 2 tentativas), **6 de 8 bateram em 429**. Não é afirmação de causa — pode ser o provedor mesmo, pode ser o horário — só o padrão observado, registrado sem inflar pra teoria.

**Proposta ao Humano, não decisão:** pausar as tentativas por agora em vez de insistir em sequência — reduz a chance de a conta ser vista como abusiva pelo rate limit, e mais tentativas seguidas com o mesmo padrão não trazem informação nova. O pedido, já corrigido (thinking desligado, nota de formato), fica pronto pra quando o Humano decidir tentar de novo, em outro momento.

Modelo: Claude Sonnet 5 · vetor: contagem de tentativas e vereditos desta sessão recontada a partir das três entradas reais (211, 212, 213), não estimada; diretório de destino conferido de novo, limpo. Turno desta sessão: t=10 (contado no contexto).

(212) DIÁRIO — 17/08/2026 · Segunda invocação real: GLM-4.7-Flash respondeu (sem 429) mas gastou o orçamento inteiro tentando calcular hash de cabeça — achado real de bug, corrigido (thinking desligado); reenvio único com formato junto, ordenado por REGRAS, bateu em 429 de novo duas vezes — ainda sem parecer válido

**Segunda invocação, âncora atualizada na hora** (`git ls-remote origin main` → `8016eb8`, REGRAS.md sha256 `63d7a298...`, MEMÓRIAS.md sha256 `b5060f69...`, última entrada (211 - primeira invocação, HTTP 429 nas duas tentativas permitidas)): desta vez a chamada teve sucesso técnico (sem 429) — mas o parecer não veio. `finish_reason: "length"`, `completion_tokens: 8000` (o teto inteiro), `reasoning_tokens: 7991` — o modelo gastou o orçamento inteiro em `reasoning_content` tentando literalmente CALCULAR um hash SHA256 "de cabeça" pro texto do pedido, repetindo a mesma tentativa falha várias vezes seguidas (texto de raciocínio lido, padrão claro: "Let's calculate... Hash: `...` (this is a placeholder, not correct)... Let's use the hash: ..." repetido). `content` (a resposta de verdade) ficou vazio. Guardado como está — `20260817-102728-glm-4.7-flash.json` — não é lixo, é evidência real do achado.

**Achado, corrigido no script antes de tentar de novo:** GLM-4.7-Flash tem "thinking" habilitado por padrão. Confirmado em fonte primária (`docs.z.ai/api-reference/llm/chat-completion`, fetch real) que existe o parâmetro `thinking: {"type": "disabled"}`. Adicionado ao corpo da chamada; `TETO_TOKENS_SAIDA` reduzido de 8.000 pra 4.000 — sem raciocínio consumindo o orçamento, quatro parágrafos curtos cabem de sobra.

**Reenvio único, com o formato junto — mecanismo da própria REGRAS ("Segunda opinião"), não decisão nova:** nota anexada ao pedido pedindo pra não gastar orçamento tentando calcular hash, responder só as quatro partes numeradas. Duas tentativas desse reenvio (uma chamada + a uma retentativa que a regra 2.3 permite) — **as duas bateram em HTTP 429 de novo**, mesmo código, sem relação com o bug corrigido. Parei aí. Nenhum arquivo espúrio ficou no disco.

**Estado real, sem inflar:** ainda não existe um parecer válido. O que existe: um achado de bug real e corrigido (thinking), e indisponibilidade de provedor repetida em momentos diferentes do dia — não é padrão suficiente pra afirmar "sempre sobrecarregado", só o observado até agora. B.7 segue não mensurável.

Modelo: Claude Sonnet 5 · vetor: `reasoning_content` da resposta lido linha a linha antes de diagnosticar a causa, não assumido "modelo travou" sem ver o texto; parâmetro `thinking` confirmado em fetch real da documentação oficial antes de codificar, não suposto por analogia com outros provedores; diretório de destino inspecionado depois de cada tentativa falha pra confirmar ausência de arquivo espúrio. Turno desta sessão: t=9 (contado no contexto).

(211) DIÁRIO — 17/08/2026 · Primeira invocação real do Conselho Remoto tentada — âncora medida na hora, pedido enviado, GLM-4.7-Flash devolveu HTTP 429 (sobrecarga temporária) nas duas tentativas permitidas; nenhum parecer recebido, B.7 não mensurável nesta rodada

**Âncora, medida agora, não copiada de lugar nenhum:** `git ls-remote origin main` → `6a50d1d`. `git show origin/main:REGRAS.md | sha256sum` → `63d7a298...` (hash completo de 64 caracteres no arquivo do pedido). `git show origin/main:MEMÓRIAS.md | sha256sum` → `9d62603e...`. Última entrada: (210 - exposição passada, decisão de não fazer nada). Os quatro campos preenchidos no pedido com esses valores, nenhum reaproveitado de resposta anterior.

**Pedido enviado, texto completo aprovado pelo Humano sem alteração:** salvo em `memoria/missoes/conselho-remoto/pedido_01_p7-citacao.txt` (camada privada, apropriado — é material de trabalho da missão, não o pedido em si que é público em conteúdo). Conferido antes do envio: o texto do pedido não menciona `memoria/missoes` em nenhum ponto — Condição 1 respeitada, guarda técnica do script não precisou nem disparar.

**Chave confirmada carregando a nova (trocada em (209)), sem imprimir o valor:** `carregar_chave()` retornou 49 caracteres, mesma checagem estrutural de sempre.

**Resultado: FALHOU, duas vezes, dado externo:** primeira chamada, HTTP 429, corpo `{"error":{"code":"1305","message":"The service may be temporarily overloaded, please try again later"}}`. Segunda chamada — a UMA retentativa que a regra 2.3 permite, não mais — mesmo erro, mesmo código. **Parei aí, como a regra manda** ("sem retentativa automática além de uma") — nenhuma terceira tentativa. Conferido depois: nenhum arquivo de resposta foi escrito em `memoria/missoes/conselho-remoto/` (o script só grava depois de uma chamada bem-sucedida; as duas falhas pararam antes desse ponto, nada de arquivo parcial ou malformado no disco).

**B.7 (a medida que importa) não mensurável nesta rodada:** sem parecer recebido, não há o que comparar contra o fluxo manual de copiar-colar. Não é o resultado "zero ou uma idas-e-vindas" que fecharia a fase — é ausência de dado, categoria diferente.

**Não é falha do mecanismo, é indisponibilidade do provedor no momento.** Nenhum código mudou por causa disto. Decisão de tentar de novo agora, mais tarde, ou noutro momento é do Humano — não decidida aqui.

Modelo: Claude Sonnet 5 · vetor: os quatro comandos da âncora rodados agora, na Máquina, valores usados vieram direto da saída desses comandos, não de memória da sessão; conteúdo do pedido conferido contra a Condição 1 antes do envio; diretório de destino inspecionado depois das duas falhas pra confirmar ausência de arquivo espúrio, não assumido limpo. Turno desta sessão: t=8 (contado no contexto).

(210) DIÁRIO — 17/08/2026 · Exposição passada de `memoria/USER.md` e `memoria/MEMORY.md` — decisão do Humano: NÃO FAZER NADA, registrada com os fatos que sustentam, não como pendência esquecida

**Decisão do Humano, registrada literal:** "NÃO FAZER NADA." Sustentada em quatro fatos, já levantados em (199 - levantamento do vazamento antigo: 0 forks, 45 dias públicos, conteúdo em uma linha):
- zero forks — ninguém copiou o repositório no período.
- o conteúdo é dado pessoal do Humano, não credencial — não há o que rotacionar.
- a exposição futura já está fechada desde 15/08 (189 - memória nativa do Hermes sai do rastreamento público).
- reescrever história é linha vermelha (Regra 4) e nunca esteve em discussão.

**Por que isto entra no canon, palavras do próprio pedido:** "este item entra no registro do que foi decidido NÃO fazer, e por quê — a parte que MEMÓRIAS historicamente não guardava." Registrado como decisão consciente, não como item que morreu por esquecimento.

**PROJETO.md, item correspondente, fechado no mesmo commit:** de `[PARCIAL]` para `[FECHADO]`. `ONDE_ESTAMOS.md` atualizado — o item sai da lista de pendências, entra em "onde estamos agora" como decidido.

Modelo: Claude Sonnet 5 · vetor: os quatro fatos conferidos contra (189)/(199) antes de aceitar como já estabelecidos — a ordem pedia registro da decisão, não nova pesquisa, e não tratei isso como licença pra reafirmar sem checar a fonte de novo. Turno desta sessão: t=8 (contado no contexto).

(209) DIÁRIO — 17/08/2026 · Chave da Zhipu trocada pelo próprio Humano, direto no arquivo — risco residual de (208) fechado, sem passar pela conversa desta vez

**O que aconteceu:** o Humano rotacionou a chave no painel da Zhipu e editou `~/.hermes/.env` diretamente, sem colar o novo valor aqui — a opção mais segura entre as duas que ofereci, e a que ele escolheu.

**Fecha o risco residual declarado em (208 - chave real recebida e guardada, exposição em texto puro pela conversa registrada como risco não escondido).** A chave antiga — a que passou pela conversa — está invalidada pela troca, virou lixo, não segredo válido. A nova nunca passou por aqui.

**Verificado, sem ler o valor:** uma linha `ZHIPU_API_KEY=` em `~/.hermes/.env`, 49 caracteres, permissão `600`, formato bate por regex com o padrão confirmado em (208) (32 hex + ponto + 16 alfanumérico) — checado contra o arquivo real, nunca impresso. Mesmo formato já testado contra P-1 em (208); não repeti o teste isolado porque a FORMA não mudou, só o valor.

**PROJETO.md e `ONDE_ESTAMOS.md` atualizados no mesmo commit** — o item opcional sobre trocar a chave sai da lista de pendências, cumprido.

Modelo: Claude Sonnet 5 · vetor: `grep`/`wc -c`/regex contra o arquivo real, nunca contra alegação; permissão conferida por `stat`, não assumida mantida. Turno desta sessão: t=7 (contado no contexto).

(208) DIÁRIO — 17/08/2026 · Chave real da Zhipu recebida do Humano, Condição 2 fechada de verdade — formato confirmado (32 hex + ponto + 16 alfanumérico misto, 49 caracteres), testada com chave FALSA da mesma forma, P-1 alarmou, só então guardada; Fase 1 do Conselho Remoto pronta para a primeira invocação real

**A chave em si nunca entra neste arquivo, nem em nenhum outro arquivo do repositório — só a FORMA dela, nunca o valor.** Regra 2/segurança são absolutas aqui: MEMÓRIAS é append-only e público, um segredo commitado aqui seria permanente e irreversível (Regra 4, "nunca apague" corta os dois lados — nem o segredo sairia depois).

**Ordem seguida, como a Condição 2 exigiu, nesta sequência e não em outra:**
1. Chave recebida do Humano, colada diretamente na conversa.
2. Formato real identificado: dois segmentos separados por ponto — 32 caracteres hexadecimais, depois 16 caracteres alfanuméricos maiúsculos/minúsculos. Total 49 caracteres. Bate com um dos 4 formatos plausíveis já testados em (207 - conselho_remoto.py escrito e testado, 4 formatos de chave testados contra P-1) — mas testado de novo agora, com a forma CONFIRMADA, não só plausível.
3. Chave FALSA da mesma forma exata (32 hex + ponto + 16 alfanumérico, valor inventado, nunca o real) testada em repositório git descartável, apagado ao fim: `SUSPEITO` disparado, `exit=1` — P-1 pega o formato real, confirmado, não suposto.
4. Só então a chave real foi gravada em `~/.hermes/.env` (`ZHIPU_API_KEY=`), permissão `600` confirmada depois da escrita, uma linha só, arquivo não versionado (fora do repositório git por desenho).
5. `conselho_remoto.py` testado carregando a chave real do arquivo — 49 caracteres, ponto no índice 32 — sem imprimir o valor em nenhum momento, nem em teste nem em log.

**Sobre "apagar do contexto do chat", pedido do Humano:** não é algo que este executor possa fazer — não há mecanismo pra editar ou apagar uma mensagem já enviada pelo Humano na conversa; o que está feito é não repetir o valor da chave em nenhuma resposta daqui pra frente, e garantir que ela não seja escrita em nenhum arquivo além de `~/.hermes/.env`. **Risco residual declarado, doutrina de defesa proporcional:** a chave passou, em texto puro, pela própria conversa — isso é uma exposição real, ainda que pequena, que gravar em `.env` depois não desfaz. Registrado como risco, não escondido; decisão de rotacionar a chave no painel da Zhipu (se o Humano achar que vale) é dele, não decidida aqui.

**Fase 1 pronta para a primeira invocação real** — script testado, chave no lugar. Falta só o Humano escrever o primeiro texto de pedido e rodar `python3 scripts/conselho_remoto.py <arquivo>`. O critério de sucesso (B.7, MEMÓRIAS (206)) já está registrado antes desse primeiro uso acontecer.

Modelo: Claude Sonnet 5 · vetor: chave FALSA gerada com a forma exata confirmada agora (não reaproveitando os 4 testes plausíveis de (207) sem reconferir), testada isolada, repositório apagado depois; permissão e conteúdo do `.env` real conferidos por tamanho e posição do ponto, nunca por impressão do valor; carregamento pelo script confirmado do mesmo jeito, sem expor o segredo em nenhuma saída de comando desta sessão. Turno desta sessão: t=5 (contado no contexto).

(207) DIÁRIO — 17/08/2026 · `scripts/conselho_remoto.py` (B.2–B.6) escrito e testado ponta a ponta com resposta simulada — bloqueado na chave real, que este executor não pode obter sozinho

**Escopo cumprido, os quatro pontos de B.2–B.6:**

**B.2, chave:** só em `~/.hermes/.env` (`ZHIPU_API_KEY=`), nunca no repositório. Formato real da chave Zhipu não confirmado em documentação pública (mesma lacuna de (206)) — testei o padrão genérico já existente em P-1 contra **4 formatos plausíveis** (hex 32 caracteres, `id.secret` separado por ponto, UUID com hífen, prefixado `sk-...`), em repositório git descartável: os 4 dispararam `SUSPEITO`. **Não é o teste definitivo da Condição 2** — esse espera a chave real (ou ao menos a forma dela) chegar.

**B.3, o que o coletor faz:** recebe arquivo de texto com o pedido → envia uma vez, via `urllib` puro (sem SDK, sem dependência nova) → guarda a resposta CRUA em `memoria/missoes/conselho-remoto/<data>-glm-4.7-flash.json` (data ISO, modelo, duração, tokens entrada/saída/total, custo em US$, caminho do pedido, resposta crua completa) → confere as 4 partes do parecer via checagem de presença de palavra (generosa a acento/caixa: origem/posição-posicao/fundamentação-fundamentacao/emenda) → se faltar alguma, imprime "FORA DO FORMATO" nomeando as que faltam e para — não reenvia sozinho, devolver o pedido é decisão do Humano (REGRAS, "Segunda opinião").

**B.4, o que nunca faz — cada um testado, não só declarado:**
- Não escreve em MEMÓRIAS/PROJETO/REGRAS — nenhuma chamada de escrita a esses arquivos existe no código.
- Não interpreta nem julga a resposta — a checagem de formato só confere PRESENÇA das 4 palavras-chave, nunca lê o conteúdo pra decidir se o parecer é bom.
- Não encadeia — uma chamada HTTP por invocação, sem laço, sem retentativa automática.
- Não decide nada — todo caminho de erro imprime e para (`return 1`), nunca segue sozinho pra um passo seguinte.

**B.5, segurança — escrito no PROJETO junto do mecanismo, como pedido, não só no código.** Resposta de modelo remoto é DADO NÃO CONFIÁVEL: guardada em arquivo JSON, nunca executada, nunca injetada em `.hermes.md` nem no contexto de outro modelo — o script não tem NENHUM caminho de código que leia esse JSON de volta pra injetar em outro lugar. Condição 1 forçada tecnicamente: `checar_conteudo_privado()` recusa o envio, antes de qualquer chamada de rede, se o texto do pedido mencionar `memoria/missoes` (barra ou contrabarra) — testado positivo (achou e abortou) e negativo (texto só com REGRAS.md/PROJETO.md, passou).

**B.6, custo:** `max_tokens=8000` no corpo da chamada — teto mecânico do lado do servidor, não só aviso. Pedido acima de 60.000 caracteres é recusado ANTES do envio (heurística de tamanho, sem tokenizador local). Fórmula de custo em dólar já no script (`PRECO_*_POR_TOKEN_USD`), hoje US$0 — pronta pra quando não for mais grátis.

**Testado ponta a ponta, sem rede real (nenhuma chave existe ainda):** três guardas de pré-envio isoladas — pedido citando `memoria/missoes` aborta antes de qualquer chamada; pedido de 70.001 caracteres aborta pelo teto; chave ausente em `~/.hermes/.env` (estado real desta máquina agora) aborta com mensagem clara. Checagem de formato testada unitária — texto com as 4 partes passa limpo, texto sem nenhuma acusa as 4 faltando. Fluxo completo testado com a função de rede (`enviar`) trocada por uma resposta simulada: escreveu o JSON esperado, calculou tokens/custo certo, apagado depois — não é resultado real, não fica no disco como se fosse.

**Bloqueado, não contornável por este executor:** a chave real exige criar conta na Zhipu — cadastro, e-mail, possível verificação — nada que este executor tenha acesso pra fazer sozinho (sem navegador, sem e-mail, sem meio de pagamento mesmo pra tier grátis). Pendente do Humano: criar a conta, obter a chave, mostrar o formato real (não necessariamente o valor) pra fechar o teste definitivo da Condição 2, e só depois guardar a chave de verdade em `~/.hermes/.env`.

Modelo: Claude Sonnet 5 · vetor: cada guarda testada isolada antes de integrar (privado/tamanho/chave ausente, formato do parecer); teste ponta a ponta com rede mockada, não pulado por não ter chave; os 4 formatos de chave testados em repositório git descartável, apagado ao fim, nunca no repositório real; arquivo de teste gerado em `memoria/missoes/conselho-remoto/` apagado depois de conferido — não é resposta real, não fica registrado como se fosse. Turno desta sessão: t=4 (contado no contexto).

(206) DIÁRIO — 17/08/2026 · GLM-4.7-Flash (Zhipu) APROVADO pelo Humano para a Fase 1 do Conselho Remoto — duas condições registradas, B.7 completo, termos de treino da Zhipu NÃO confirmados em fonte primária

**Decisão do Humano:** GLM-4.7-Flash aprovado para B.1. Razão adicional, registrada literal: "a fase 1 testa o TRANSPORTE, não a qualidade do parecer. Modelo grátis é o certo aqui porque remove a hesitação de custo, que é justamente o que se quer medir."

**Condição 1, registrada literal:** "só sai daqui material que já está no repositório PÚBLICO. Nada de `memoria/missoes/`. Camada grátis normalmente permite treino sobre o que se envia — verifique os termos e registre o que encontrar." **Verificação tentada, fonte primária não localizada:** `z.ai/privacy-policy`, `z.ai/legal-agreement`, `docs.z.ai/api-reference/introduction` — as três 404 ou sem a cláusula, testadas de verdade via fetch, não assumidas. Busca indexada (não fonte primária — mesmo descarte já aplicado em (182 - levantamento de transporte dos 5 provedores, preço em fonte oficial, agregador descartado como fonte)) traz múltiplos agregadores afirmando "dado de API não é usado para treino" — **não confirmado por documento oficial da Zhipu, registrado como `lacuna`, não como fato**. Consequência prática enquanto a lacuna não fecha: tratar a camada grátis como se pudesse treinar sobre o enviado — reforça, não afrouxa, a Condição 1.

**Condição 2, registrada literal:** "ordem obrigatória da chave — obter a chave, criar arquivo de teste com chave FALSA do mesmo formato, confirmar que a P-1 alarma, e só então guardar a real em `~/.hermes/.env`. Nunca guardar antes de confirmar que a varredura pega."

**B.7, completo agora (chegou cortado na mensagem anterior):** "numa primeira utilização real, conte quantas idas e vindas de copiar-e-colar o Humano deixou de fazer. Se for zero ou uma, a fase 1 não se pagou — resultado legítimo, registre e pare, não expanda para dois modelos 'para ver se melhora'." Critério de sucesso registrado ANTES de qualquer utilização real — não fica disponível para redefinição depois do resultado.

Modelo: Claude Sonnet 5 · vetor: 3 URLs candidatas a fonte primária de termos de uso testadas de verdade (`WebFetch`), nenhuma com a cláusula de treino — não aceito o resumo de busca indexada como substituto, mesmo repetindo o padrão já catalogado em (182); os dois critérios (ordem da chave, sucesso do B.7) transcritos literais do pedido do Humano, não parafraseados. Turno desta sessão: t=4 (contado no contexto).

(205) DIÁRIO — 17/08/2026 · Decisão do Humano sobre `.env` registrada — NÃO entra no backup do HD externo, risco assumido por escrito; item aberto desde (160) fecha

**Decisão do Humano, registrada literal:** "O `.env` NÃO entra no backup do HD externo [...] o HD é exFAT e não carrega permissão de arquivo — qualquer segredo copiado para lá fica legível por quem plugar o disco. E o backup existe para o que não se reconstrói: chave se refaz em minutos, história não." Consequência, também nas palavras do Humano: "Se a máquina morrer, as chaves se refazem — isso é decisão consciente, não esquecimento."

**Fecha o item aberto desde (160 - gap de backup de memoria/missoes fechado, deixou em aberto "cifra e inclusão do .env no backup" como decisão separada).** Chaves vivem só em `~/.hermes/.env`, protegidas pelo `.gitignore` e pela varredura P-1 (checagem de segredo). Nenhuma cópia — cifrada ou não — entra no fluxo automático de backup.

**O que isso deixa parado, sem apagar:** `scripts/cifrar_env.sh` — mecanismo manual, já testado (S-3), que cifra `.env` com GPG simétrico AES256 e copia o `.gpg` pro HD externo se montado — segue existindo no repositório, mas **não é mais o caminho recomendado**. A decisão de hoje é não fazer cópia nenhuma, cifrada ou não, não trocar cifra por confiança em permissão de arquivo de disco exFAT. O script fica como ferramenta disponível, não como parte do fluxo padrão.

**PROJETO.md atualizado no mesmo commit:** "Riscos conhecidos", item sobre cópia da história fora da máquina — "Em aberto: cifra e inclusão do `.env`" vira fato fechado, com o motivo.

Modelo: Claude Sonnet 5 · vetor: texto de (160) relido antes de declarar o que ficava em aberto, não citado de memória; `scripts/cifrar_env.sh` relido antes de descrever o que ele faz (cifra AES256 + copia condicional ao HD montado), pra não confundir com cópia crua. Turno desta sessão: t=3 (contado no contexto).

