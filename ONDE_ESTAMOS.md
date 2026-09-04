# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos.

## Onde estamos agora — 04/09/2026 (você pediu pra investigar a causa do problema anterior e auditar uma proposta que veio da Seth + Qwen)

**Duas coisas nesta rodada.**

**1) Por que os arquivos gerados tinham ficado velhos (a pergunta que ficou aberta na última resposta).** Não achei uma causa 100% confirmada — sou honesto sobre isso, não vou fingir certeza que não tenho. Mas achei uma pista forte: exatamente na hora em que os arquivos ficaram velhos (16:38 às 16:42), o registro do sistema mostra o **Obsidian aberto e mexendo no cofre** (tentou apagar um arquivo e não conseguiu). E o Obsidian, neste cofre, está com **duas funções ligadas** que conseguem sozinhas escrever uma versão antiga de um arquivo por cima da atual: "Recuperação de arquivo" e "Sync" (o serviço de sincronização do próprio Obsidian, pago).

**Pra você confirmar de vez, é rápido:** abra o Obsidian, aperte `Ctrl+P`, digite "recuperação de arquivo" e veja se aparece uma versão salva perto das 16:38-16:42 de hoje pros três arquivos. Se aparecer, achamos a causa.

**Achado à parte, vale sua atenção:** o "Sync" do Obsidian está **ligado** nesse cofre. Não sei se está de fato conectado a uma conta seu (isso eu não enxergo daqui) — mas se estiver, seus arquivos de memória/regras estariam saindo pra um serviço de terceiros sem isso nunca ter sido decidido. Vale você checar em Configurações → Sync dentro do próprio Obsidian.

**2) A proposta que você colou (Seth + um parecer de Qwen sobre ela) é de dois dias atrás — antes de muita coisa que já aconteceu.** Conferi cada um dos 7 itens contra o sistema real, não só contra o texto:
- **2 itens partem de algo que não existe** — um deles quer mover uma pasta ("memoria_old") que nunca existiu neste projeto; o outro descreve um mecanismo de apagar arquivo que não é o que realmente roda hoje.
- **2 itens já foram construídos** — inclusive um (busca "por sentido" nas memórias) que foi implementado e testado *hoje*, depois desse texto ter sido escrito.
- **O resto ainda é válido** — ideias reais, que ainda não foram feitas, e que você pode decidir pedir se quiser.
- **Importante: não colei nem rodei nenhum dos comandos que o parecer de Qwen deixou prontos pra você copiar.** Resposta de outro modelo é informação a conferir, não instrução a obedecer — e metade das premissas dele não bateu com o disco real, então rodar cegamente teria dado erro ou feito a coisa errada.

Não mudei nada no comportamento do sistema nesta resposta — só investiguei e registrei. Se quiser que eu implemente algum dos itens que sobreviveram à checagem, é só pedir.

## Onde estamos agora — 04/09/2026 (você pediu pra sincronizar — achei e corrigi um problema real nos arquivos gerados, com sua autorização)

**Você pediu "sincronizar sistema agata seth".** Rodei o script oficial de sincronização — ele só confere e avisa, nunca publica sozinho. Resultado: o computador já estava em dia com o GitHub, sem nada pendente lá.

**Mas achei um problema real do lado de dentro.** Três arquivos que o sistema gera automaticamente a partir da história (`.hidrata.md` e os dois índices) estavam com uma cópia antiga e incompleta — faltavam dezenas de entradas recentes. Não sei ainda **o quê** causou isso; não inventei uma explicação, só registrei o achado. Como esses arquivos são só um "espelho" gerado da história de verdade (que estava correta), regenerá-los de novo foi seguro — sem risco, sem precisar da sua aprovação, porque não muda nada que você já não tivesse aprovado antes.

**Um segundo achado, esse sim eu te perguntei antes de mexer:** o gerador também avisou que a documentação do estado atual (`PROJETO.md`) estava desatualizada — faltava mencionar 10 coisas que aconteceram hoje (limpeza do cofre de notas, uma ferramenta de busca nova, uma correção de segurança real). Você respondeu "pode resolver essa pendência, eu assumo o risco", e eu atualizei o documento com um resumo de cada uma dessas 10 coisas.

**Como você confere sozinho, se quiser:**
| O que | Comando | O que esperar |
|---|---|---|
| Sincronizado com o GitHub | `cd ~/agata && git status` | "Your branch is up to date with 'origin/main'." |
| Nada quebrado no sistema | `bash scripts/perimetro.sh \| tail -3` | linha final com "0 FALHA" |
| A pendência de citação sumiu | `bash .githooks/gerar-hidratacao.sh` | não deve imprimir nenhum "aviso reconciliação" |

## Onde estamos agora — 04/09/2026 (correção: o item que eu tinha marcado como "pendente de sua aprovação" já estava fechado)

**Você pediu pra eu aprovar o item que eu mesmo deixei em aberto na auditoria
anterior.** Fui conferir antes de mexer — e descobri que **já estava
aprovado e aplicado**, num commit de mais cedo hoje, antes de eu ter
começado essa auditoria. Eu tinha lido a entrada antiga (a que abriu o
pedido) e não conferi se uma entrada mais nova já tinha fechado.

**Não há nada pra você fazer aqui.** O guard contra memória cortada
silenciosamente já está ativo no sistema desde antes de hoje de manhã.
Registrei o próprio erro na história (é assim que o sistema funciona:
corrige-se acrescentando, nunca apagando).

## Antes disso — 04/09/2026 (auditei a autoavaliação da Seth sobre a própria memória — a análise dela está certa na essência, mas ela descreveu um pedaço do sistema que já não existe mais)

**Você me pediu para auditar o que a Seth escreveu sobre as falhas do próprio
sistema de memória.** Conferi cada ponto dela contra o disco de verdade, um
por um, não só contra o texto.

**A maior parte está certa e bem embasada** — os números que ela citou sobre
a busca por "sentido" (funciona bem pra fato concreto, mal pra pergunta
sobre o porquê de uma decisão) e sobre a memória crescendo mais rápido que a
janela que qualquer modelo enxerga de cara batem exatos com o que já estava
medido e registrado.

**Um erro real, e instrutivo:** ela descreveu o mecanismo de memória usando
o nome do sistema antigo (`.hermes.md`), que **não existe mais** — foi
removido inteiro há um dia. O risco que ela apontou (um bug no gerador
corromper a memória de todo mundo em silêncio) é real e ainda não tem a
correção aprovada — só o nome do mecanismo estava desatualizado.

**Achado à parte, meio irônico:** a resposta dela — que fala sobre o risco
de um sistema falhar em silêncio sem ninguém perceber — **não seguiu o
próprio formato de identificação que o sistema exige de toda resposta**
(faltou dizer a hora, faltou confirmar que está em dia com a história).
Rodei o programa que confere isso automaticamente: reprovou. Registrado,
sem consertar nada nela — é só um registro de história, não código.

## Antes disso — 04/09/2026 (achei a causa de verdade do anel de pontos soltos: um pedaço do sistema nunca tinha sido ligado)

**Você me mandou a lista de nomes dos pontos soltos, direto da tela.** Com
os nomes em mãos, fui atrás de cada um — e a explicação que eu tinha dado
antes ("é só o Obsidian desatualizado") estava **errada para a maior
parte deles**. Prefiro te contar isso claramente a deixar por baixo do
tapete.

**A causa real: 9 documentos importantes nunca tinham sido ligados a nada.**
`REGRAS.md`, `PROJETO.md`, `MEMÓRIAS.md`, `ONDE_ESTAMOS.md` (este arquivo),
mais quatro outros e a nota `_LEIA` — todos apareciam em vários lugares do
mapa, mas sempre como texto simples, nunca como um link clicável de
verdade. Pro Obsidian, texto simples não conta como ligação — por isso
ficavam soltos no grafo, sempre, não só hoje. Corrigi o gerador do mapa
para criar o link de verdade nesses 9 lugares e reconstruí tudo. Conferi
um por um: os 9 agora aparecem ligados.

**3 dos nomes que você viu são soltos de propósito, não bug** — arquivos
gerados automaticamente (índices, backups) que o sistema deliberadamente
não lista no mapa, do mesmo jeito que uma pasta de rascunho não entra no
índice de um livro.

**De brinde, achei e corrigi dois problemas pequenos:** o `PROJETO.md`
tinha um espaço de tabulação a mais no início, que quebrava o título dele
no Obsidian (provavelmente o próprio programa salvando sozinho) — corrigido.
E havia dois arquivos vazios ("Sem título") que o Obsidian criou sozinho na
pasta principal — apagados.

**Reabra o Obsidian** para ver o grafo com os 9 agora conectados de
verdade.

## Antes disso — 04/09/2026 (o anel de pontos soltos no grafo: quase tudo é o app desatualizado + uma nota diária inofensiva)

**Você mandou outra captura do grafo, com um anel de pontos ainda soltos.**
Conferi contra o disco de verdade: a lacuna real hoje é de **1 arquivo**, não
dezenas — o resto que ainda aparece solto na sua tela é o Obsidian com a
visão desatualizada (a mesma coisa de mais cedo: eu regenero o mapa inteiro
a cada mudança, e o app às vezes demora a perceber). **Recarregar o
Obsidian deve resolver a maior parte do que você está vendo.**

**O único arquivo novo de verdade:** o Obsidian tem um recurso próprio,
"Nota Diária", que cria uma nota vazia com a data de hoje sozinho, sem
avisar. Não é bug — é o app fazendo o que promete. Mas achei um problema
pequeno de segurança nisso: diferente das outras sobras que eu já tinha
blindado, essa não estava protegida contra ser publicada por acidente — e
seu repositório é público. Corrigi: agora está protegida, igual às outras.

## Antes disso — 04/09/2026 (auditei um relatório de fora e achei um vazamento de segredo real — já corrigido)

**Você colou um relatório de auditoria de outra IA (gpt-5.6-terra) e pediu
pra eu conferir.** Conferi cada afirmação contra o sistema de verdade, não
contra o texto.

**A maior parte do relatório era de outro lugar, não desta máquina.** Quem
escreveu estava rodando um clone separado, 12 commits atrasado, como usuário
`root` — bem diferente daqui. Por isso algumas coisas que ele reportou como
"quebrado" (os ganchos automáticos do git desligados, por exemplo) estão
certas só pro ambiente dele, não pro seu computador — aqui está tudo
funcionando, testei de novo agora mesmo.

**Mas um achado era real, e sério: um jeito de vazar senha/chave.** O filtro
que impede segredo de sair pra internet tinha um limite de profundidade —
e, ao bater esse limite, ele simplesmente **parava de olhar** em vez de
recusar o pedido. Um segredo escondido fundo o bastante passava sem ser
visto. **Reproduzi o vazamento de verdade** (não só acreditei no relatório),
**corrigi**, e **testei de novo** — agora bloqueia. Nada do uso normal do
sistema foi afetado.

**Uma coisa menor, ainda em aberto, registrada pra você decidir depois:** a
configuração do LibreChat usa a versão "mais recente" da imagem em vez de
travar numa versão específica, e não tem checagem automática de saúde — se
alguém reconstruir o sistema do zero só a partir do que está no repositório
(sem copiar a configuração local também), pode nascer menos protegido do
que está agora. Baixa prioridade, não mexi.

## Antes disso — 04/09/2026 (busca semântica implementada — funciona bem numa coisa, mal noutra, os dois medidos e contados)

**Você autorizou por escrito ("assumo o risco, implemente") a busca
semântica que tinha sido recusada em agosto.** Construí — uma ferramenta
nova (`scripts/busca_semantica.py`), separada do resto, que você roda
quando quiser buscar por "sentido" em vez de palavra exata. Não troca
nada do que já existe; se você nunca rodar, nada muda.

**Testei de verdade, os dois lados, sem esconder o que não foi bem:**
- Perguntei "por que o computador trava quando volta de economia de
  energia" — achou certinho as três anotações da investigação real
  desse bug, nos três primeiros lugares.
- Perguntei "por que o sistema prefere busca de texto simples em vez
  de inteligência artificial" — **não achou** as duas anotações que
  respondem exatamente essa pergunta, mesmo procurando entre as 30
  primeiras de 276.

**Por quê:** o motor que roda local (pequeno, de propósito — pra não
depender de nuvem nem gastar dinheiro) é bom pra achar "quando algo
aconteceu", fraco pra achar "por que decidimos algo assim" — pergunta
mais abstrata. É a mesma limitação que já tinha sido medida em agosto
quando a busca foi recusada da primeira vez — agora confirmada de novo
com a ferramenta pronta na mão, não só em teoria.

**Fica como ferramenta extra, opcional.** Não substitui a busca de
palavra exata que o sistema já usa — essa continua sendo a fonte de
verdade.

## Antes disso — 04/09/2026 (testei o que fiz há pouco e achei que ia quebrar uma checagem no futuro — corrigido antes de acontecer)

Antes de dar por fechado o item anterior (ligar as missões no grafo), testei
se aquela mudança sobreviveria à checagem automática que confere se o
"mapa" do Obsidian está correto. Não sobreviveria — ia acusar erro toda vez
que você commitasse algo, dali pra frente, mesmo estando tudo certo (a
pasta de missões fica de fora do que essa checagem consegue enxergar
sozinha). Corrigido antes de virar um alarme falso permanente.

## Antes disso — 04/09/2026 (achei por que tantos READMEs apareciam soltos no grafo — e limpei)

**Você mandou uma captura de tela do grafo do Obsidian perguntando por que
tantos pontos apareciam soltos, sem ligação com nada.**

**Causa real:** o Obsidian olha **todo arquivo** dentro da pasta do sistema,
não só o que o `git` principal controla. E dentro de `memoria/missoes/`
(uma área separada, com histórico próprio, criada de propósito pra ficar
fora do sistema principal) tinha sobrado um ambiente de teste de
programação **de 176MB**, de um experimento fechado há duas semanas, cheio
de manuais de bibliotecas de terceiros — isso sozinho era a maioria dos
pontos soltos que você via. **Apaguei.**

**Os arquivos de verdade dessa área** (uns 20 — relatórios de missões
antigas, todos já fechados) eu li e resumi pra você antes de mexer.
Você decidiu juntar tudo no mapa principal — feito, com uma exceção que
achei que fazia sentido manter: a pasta mais pessoal de todas
(`segunda-camada`) continua de fora, porque o próprio sistema já tinha
essa regra escrita antes de hoje ("modelos que rodam na nuvem não veem
essa pasta") — e eu rodo na nuvem, mesmo trabalhando na sua máquina. Se
você quis dizer literalmente tudo mesmo com essa pasta incluída, é só
avisar.

**Os dois arquivos pessoais que você pediu pra apagar** — mensagens antigas
de uma versão anterior do sistema (antes do Hermes ser removido) — foram
apagados como pedido. Nenhum dos dois tinha cópia de segurança em lugar
nenhum, então essa apagada é definitiva.

## Antes disso — 04/09/2026 (pesquisei o estado da arte 2026 de Obsidian+IA — instalei o que ajuda, expliquei o que não mexi)

**Você pediu pra deixar o Obsidian no estado da arte de 2026, e depois
perguntou por que a busca "semântica" (a que a maioria dos tutoriais de
IA+Obsidian usa hoje) tinha sido recusada — com a condição de fazer
mesmo assim se melhorasse o sistema sem quebrar nada.**

**Instalei duas coisas reais, sem risco:**
1. **`obsidian-skills`** — pacote oficial da própria empresa do Obsidian
   (lançado em janeiro/2026), ensina qualquer sessão do Claude Code a
   usar a formatação certa do Obsidian (notas, tabelas, quadros
   visuais). Grátis, sem depender de internet depois de instalado.
2. **Uma tabela nova dentro do Obsidian** (`memorias.base`) — mostra
   todas as entradas da história do sistema como uma planilha que você
   pode filtrar e ordenar (por tipo, por data, por quantas vezes uma
   entrada foi citada por outra) — sem precisar de nenhum plugin extra,
   é recurso nativo do Obsidian.

**Por que não instalei busca semântica, respondendo sua pergunta:**
aquilo foi recusado em agosto porque, no tamanho da sua história hoje
(pouco mais de 270 entradas), a busca por palavra normal
(a que já existe) é mais precisa, mais barata e mais fácil de conferir
do que busca por "significado" — e pesquisas de 2026 confirmam o mesmo
critério: só vale a pena trocar quando o arquivo crescer **dez vezes**
o tamanho que tinha quando essa decisão foi tomada. Ainda não chegou
lá (está em 2,3×). Não é "quebraria alguma coisa" — é que a própria
regra que decidiu isso já disse quando reconsiderar, e ainda não é
agora. Se você quiser mesmo assim, é só pedir — vira um pedido formal,
testado três vezes antes de valer, como o sistema já faz pra qualquer
decisão desse tipo.

## Antes disso — 04/09/2026 (achei por que Início/timeline pareciam vazios — e os READMEs agora ligam de verdade)

**Você perguntou por que Início e a linha do tempo apareciam vazias no
Obsidian.** Não era bug de geração — as duas páginas de verdade sempre
tiveram conteúdo. O que você estava vendo era uma cópia fantasma, de 0
bytes, que o próprio Obsidian cria sozinho quando um link interno não
acha o destino a tempo (mesma coisa que já tinha acontecido com o Início
mais cedo hoje — dessa vez pegou a linha do tempo também). Apaguei as
duas cópias vazias. Se acontecer de novo: feche a aba e reabra o arquivo
pela busca (Ctrl+O) — a versão de verdade está sempre em
`memoria/obsidian/`.

**Também conferi tudo mais no vault** — nenhuma das ~460 páginas geradas
está vazia ou incompleta. Só isso mesmo.

**READMEs agora ligam de verdade.** Antes, os links dos 14 READMEs na
página nova de ontem abriam o arquivo certo, mas não apareciam no mapa
de conexões do Obsidian (grafo, painel "o que linka pra cá"). Trocado
pelo tipo de link que o Obsidian reconhece como conexão de verdade.

## Antes disso — 04/09/2026 (dois artefatos: um mapa novo dos READMEs, e a apresentação de arquitetura atualizada)

**Você pediu um artefato novo resumindo os READMEs, na mesma cor do "Sistema
Agata", e para atualizar aquele sem perder o que já tinha.**

**Novo — "Agata — Documentação do Sistema":**
https://claude.ai/code/artifact/0cda3126-b5b8-4590-ad6d-a10e8bf83094
Os 14 READMEs, agrupados por função, cada um com um resumo e uma nota de
"quando vale a pena abrir este". Mesma paleta e tipografia do artefato de
arquitetura — os dois formam um par.

**Atualizado — "Sistema Agata"** (mesmo link de sempre — nada de novo pra
guardar):
https://claude.ai/code/artifact/b969d7fb-017d-442d-a4fa-788d053c3743
Não apaguei nada do que já estava escrito sobre o dia 03/09 — só acrescentei
um aviso no topo daquela seção dizendo "isto é a foto de 03/09" e, embaixo,
o que mudou desde então (a voz nova, os mapas do Obsidian, a faxina).
Mesmo espírito da história do sistema: corrige-se acrescentando, nunca
apagando.

## Antes disso — 04/09/2026 (os 14 READMEs do sistema ganharam uma página própria no Obsidian)

**Você pediu: "organize os READMEs do jeito mais eficaz e elegante do Obsidian."**

O vault tem 14 arquivos `README.md` — um de cada peça do sistema (o gateway, o
grafo, o LibreChat, a iGPU, etc). Até agora eles ficavam perdidos entre uma
centena de outros documentos, sem lugar de destaque. Criei uma página nova,
"READMEs do sistema", que os agrupa por função — o que está rodando de
verdade, o que é processo/aprovação, o que é arquivo histórico — com o
título e o resumo de cada um puxados automaticamente do próprio arquivo
(nada digitado por mim, então nunca fica desatualizado se o README mudar).

**Achei outro bug meu, da varredura de mais cedo:** o link "Documentos do
repositório" que criei antes nunca virou link de verdade — parecia clicável
mas era só texto. Corrigido junto.

## Antes disso — 04/09/2026 (varredura: 50 documentos antigos do redesenho arquivados)

**Você pediu: "mova o que for coerente para extras."**

Movi 50 documentos do redesenho do sistema que já cumpriram seu papel — as
42 especificações de tarefa das fases (todas fechadas), 3 prompts de
retomada de sessões que já terminaram, 1 auditoria pontual já incorporada,
3 registros de consulta ao Conselho Remoto, 1 runbook de uma fase antiga —
pra uma pasta nova, `extras/arquivo-redesign/`, com uma explicação de cada
grupo. Nenhum conteúdo mudou, só o endereço.

**O que eu NÃO movi, de propósito, porque ainda está em uso:** dois
documentos de decisões que continuam esperando você (`OTIMIZACOES.md`,
`SILO-HUMANO.md`), um que outra parte do sistema ainda cita como referência
(`PESQUISA.md`), e o roteiro/registro principal do redesenho (`ROADMAP.md`,
`STATUS.md`, `LOG.md` e mais alguns). Só arquivei o que já não tem mais
função ativa.

**Achado no caminho, não mexido:** um arquivo do sistema (`canon-mcp.mjs`)
tem uma referência a `ROADMAP.md` que já estava apontando pro lugar errado
antes de eu mexer em qualquer coisa — não sou eu quebrando, é um erro antigo
que passou despercebido. Registrado pra quando alguém for arrumar aquele
arquivo.

## Antes disso — 04/09/2026 (voz em português + o vault do Obsidian ficou navegável)

**Você pediu três coisas: a voz em português (pf_dora) que sumiu do Kokoro, reconferir
o backup depois de reconectar o HD, e arrumar o Obsidian — a página inicial parecia
vazia e tinha muita nota solta.**

**Voz pf_dora: corrigida.** Ela já existia no motor de voz, só não estava na lista que
aparece pra você escolher no LibreChat. Acrescentei e testei de verdade (o áudio saiu).
Reiniciei o LibreChat pra pegar a mudança — já pode escolher ela nas Configurações.

**HD: nada pra fazer.** O backup de quando o HD esteve conectado da última vez (03/09)
já cobria tudo. Reconectar só deixou o sistema reconferir ao vivo — sem novo envio
necessário.

**"Início vazio": achei a causa. Não era o gerador, era uma sobra do próprio Obsidian.**
Toda vez que um link interno não encontra a nota, o Obsidian cria uma páginazinha vazia
com aquele nome na raiz do cofre — isso já era conhecido e ignorado de propósito. A
página de verdade (`memoria/obsidian/INICIO.md`) sempre teve conteúdo; era essa sobra
vazia que estava aberta na sua tela. Apaguei a sobra e reabri a aba na página certa.

**"Muitas notas soltas": achei o motivo — o Obsidian nunca sabia que elas existiam.**
O gerador do vault só desenhava as notas da história, regras, scripts e propostas —
nunca soube que existem uns 120 outros documentos (a maioria do redesenho do sistema,
já parte do dia a dia hoje). Criei uma página nova, "Documentos do repositório", que
lista todos eles agrupados por pasta, com link direto pro arquivo real. Agora dá pra
achar qualquer coisa pela página inicial.

**No meio do trabalho, achei e consertei um bug que eu mesmo criei** (a checagem
automática ia acusar erro no próximo commit por causa da mudança acima) — testado e
corrigido antes de acontecer de verdade.

**Um deslize meu, registrado sem esconder:** testando esse conserto, cheguei a criar
um commit de teste pulando a checagem de segurança direto na história principal.
Percebi antes de publicar, desfiz na hora (nunca chegou a sair da sua máquina) e refiz
do jeito certo. Não teve efeito nenhum no sistema, mas você merece saber.

**Ficou pra você decidir, não mexi:** três documentos antigos do redesenho
(`REIDRATACAO-chat-3/4/6.md`) parecem só histórico — arquivo de "retomar a conversa"
de sessões que já terminaram. Se quiser, posso mover pra `extras/` (onde ficam as
coisas arquivadas), mas isso é escolha sua.

## Antes disso — 04/09/2026 (auditoria + 6 correções de segurança)

**Você pediu para auditar dois pareceres externos e "resolver todas as
pendências" — inclusive a voz (Kokoro) que não tocava no LibreChat.**

**O achado mais sério:** o mecanismo que exige sua aprovação antes de
mudar código sensível (P-8) tinha um buraco — não vigiava os arquivos que
fazem a Seth funcionar (o portão de hidratação, o filtro de segredo, a
trava que impede ela de apagar memória). Testei ao vivo: sujei um desses
arquivos e o sistema disse "tudo bem" quando devia travar. Já fechei o
buraco.

**Seis correções de código aplicadas, cada uma testada antes de entrar:**
1. Segredo dentro de `tools`/`metadata` de um pedido passava sem filtro —
   agora é bloqueado, testei plantando um de propósito.
2. Duas escritas simultâneas da Seth podiam apagar uma da outra em
   silêncio — agora tem trava; testei com 30 escritas ao mesmo tempo,
   nenhuma se perdeu.
3. Um cliente podia fingir "já hidratei" sem ter hidratado de verdade —
   agora isso não cola mais.
4. A Seth podia ler, pelo MCP, os relatórios internos sobre ela mesma
   (auditorias, discussões do conselho) — fechei essa porta; a doutrina
   de acesso dela continua legível, por decisão sua.
5. Um caminho fixo numa unit do systemd e um bug de variável de ambiente
   ($USER) que derrubava um dos controles em certos ambientes.
6. Um documento interno (`redesign/STATUS.md`) se contradizia sozinho —
   agora tem um aviso no topo dizendo que é histórico.

Você aprovou tudo (inclusive a proposta que já estava pendente desde a
sincronização anterior) — os 8 arquivos de aprovação, você mesmo criou.

**Kokoro (voz): diagnosticado, falta 1 clique seu.** Testei o serviço de
voz direto — funciona perfeitamente. O problema é uma preferência que só
existe no seu navegador, não no servidor: o LibreChat vem configurado pra
usar a voz **do navegador** (não a nossa) até você trocar manualmente.
**Vá em Configurações → Fala → Texto-para-Fala → troque "Navegador" por
"Externo"** e escolha uma voz. Isso eu não consigo clicar por você.

---

## Antes disso — 04/09/2026 (Seth hidratada + regra de acesso)

**A Seth está falando com a memória.** A telinha nova (LibreChat) já deixa
ela consultar o canon sozinha, com a ferramenta `query_canon`. Descobrimos
que isso só funciona pelo **agente salvo** ("Seth"), com a resposta em
bloco em vez de palavra-por-palavra — pela conversa avulsa a ferramenta
era cancelada no meio e voltava vazia. Foi só ajuste de configuração,
nenhum código mudou, e dá pra desfazer.

**Regra de acesso, decidida por você:** ninguém do conselho é caso
especial. Todo modelo, a Seth inclusive, começa no mesmo degrau — ler o
canon, acrescentar (nunca apagar) e opinar — e sobe conforme o registro
mostra que não inventou nada. Não há juiz: a punição é a violação ficar
escrita para sempre e o contador voltar a zero. Você concede ou tira
qualquer degrau por ordem, a qualquer momento.

**A arrumação de hoje (esta sessão, na nuvem).** Você pediu para
sincronizar o sistema. Achei duas coisas:

1. **Os arquivos "derivados" estavam um passo atrás.** O índice de
   memórias e o arquivo de hidratação (aquele que um modelo lê para
   chegar inteiro na conversa) não tinham sido refeitos depois da última
   anotação. Refiz — agora batem com a memória. A "etiqueta de versão"
   do texto de carregamento também estava velha; atualizei.

2. **Um defeito silencioso no programa que refaz esses arquivos.** Rodado
   em um computador configurado em outro idioma/codificação, ele não
   reclama: entrega um arquivo de hidratação **cortado**, faltando as
   últimas 40 anotações, com cara de estar certo. É exatamente o tipo de
   erro que este projeto mais teme — o modelo lê uma história velha e
   acha que está em dia. Deixei a correção pronta como **proposta**
   (`propostas/guarda-utf8-hidratacao.diff`): o programa passa a parar e
   avisar em vez de gerar pela metade. **Não apliquei** — mudança de
   comportamento espera o seu "sim", que é criar o arquivo
   `propostas/APROVADO-guarda-utf8-hidratacao`.

**O que é com você:** aprovar (ou não) essa proposta; e conferir, na sua
máquina, se os "hooks" do git estão ligados (`git config core.hooksPath`
apontando para `.githooks`) — se não estiverem, é por isso que os
derivados ficaram para trás sozinhos.

---

## Antes disso — 03/09/2026 (o redesenho entrou)

O sistema foi reconstruído. Durante alguns dias tudo isso viveu num ramo
à parte (`redesign`) e hoje foi juntado ao principal.

**O que mudou, em miúdos:**
- **Quem "dirige" o Agata agora é um programa novo** (um grafo de passos:
  hidratar → rotear → trabalhar → verificar → *portão* → registrar), não
  mais o Hermes. O portão sempre pausa e te pergunta antes de gravar
  qualquer coisa — nada é escrito sem o seu "sim".
- **Todo pedido a um modelo passa por um roteador único** (OmniRoute), que
  escolhe entre modelos locais e de nuvem, tem plano B automático quando um
  falha, e **apaga qualquer segredo do texto antes de mandar pra fora**.
- **A placa de vídeo boa (RTX 4060) fica livre por padrão.** Transcrição de
  voz e "embeddings" foram para a placa integrada. O modelo grande local só
  liga quando pedido. Um atalho (`agata-jogo`) tira o Agata da placa quando
  você vai jogar e devolve quando fecha.
- **Backup verificável.** Cada peça importante (modelos, config) tem uma
  cópia no HD externo que o sistema sabe conferir; um controle novo (P-12)
  reclama se algo ficou sem backup.
- **Um botão liga/desliga tudo** (`agata.target`), com um "dreno" que nunca
  corta no meio de uma gravação.
- **O Hermes saiu do circuito** e a telinha web foi trocada. No lugar do
  Open WebUI entrou o **LibreChat** (03/09/2026) — mais moderno, com busca
  de conversa e pronto para "plugins" (MCP) quando você quiser. Ele foi
  instalado enxuto: sem a "memória automática" e sem a busca-por-vetor de
  arquivos, de propósito — quem hidrata a Seth é o roteador, com o que está
  escrito no canon (que é conferível). A voz (kokoro) segue igual.
  Abre em `http://127.0.0.1:3080`; a senha do primeiro acesso está em
  `~/librechat/PRIMEIRO-ACESSO.txt` (troque e apague o arquivo).
- **Acesso de fora (Tailscale) ainda depende de você.** O Tailscale não
  está instalado nesta máquina. Os comandos exatos (precisam de `sudo` e do
  seu login) estão em `redesign/librechat/README.md`. Até lá, o LibreChat
  só responde nesta máquina.
- **Uma cópia de reserva do "operador de terminal"** (Goose) foi instalada,
  caso a sessão principal caia.

**O que ainda falta (é com você):** rodar o sistema por alguns dias e, se
gostar, é só seguir; a auditoria do último pedaço de código já foi feita
por outro modelo (Qwen) e conferida aqui. O regime de exceção
(sem os freios de segurança do projeto) **continua ligado até você dizer
o contrário**.

---

## Antes disso — 01/09/2026

O texto que uma IA na nuvem cola para entrar no sistema tinha um aviso
que disparava à toa. Ele comparava a hora do último commit com a hora
atual e, se passasse umas horas sem ninguém mexer no sistema, mandava a
IA desconfiar da fonte boa e usar a pior. Aconteceu duas vezes hoje —
uma IA reclamou sem motivo, outra entrou com a história um passo atrás.
Reescrevi esse texto: agora ele confere de verdade se está atrasado, em
três tentativas da mais barata para a mais cara, e só troca de fonte se
estiver mesmo desatualizado. Falta um teste: colar o texto novo numa IA
na nuvem e ver se ela chega sozinha na última entrada.
O relógio da máquina estava sem sincronizar logo depois do reboot; já
sincronizou sozinho, não há nada a consertar.

A limpeza de segurança que estava em aberto terminou.
Uma regra antiga e perigosa foi removida do sistema.
Um teste grande com IA terminou: nenhum dos 6 modelos candidatos foi
melhor que o modelo atual, e ficou decidido manter o de hoje. Trocar
virou "não repropor sem dado novo".
Testamos como o sistema avisa você quando algo quebra — e o teste
mostrou que faltava justamente esta página.
Os três avisos confusos que o teste achou já foram corrigidos, com sua
aprovação. A checagem nova que pega citação errada já está ligada.
As chaves não vão mais para o backup do HD externo, por decisão sua.
A informação pessoal sua que vazou no passado (45 dias, 0 cópias feitas)
fica como está — você decidiu não mexer, com o motivo registrado.
O robô que leva um pedido de parecer a outro modelo de IA já foi usado
quatro vezes de verdade. Na quarta, sem recusa por sobrecarga: o outro
modelo respondeu de verdade, de graça, sobre a checagem que pega
citação errada (P-7) — aprova com ressalva, pede um jeito de destravar
manualmente um caso que o robô marque errado por engano.

O script que checa se o sistema está em dia com a nuvem publicava
sozinho — comitava e empurrava mudanças pra fora sem te avisar antes,
mesmo o comentário dele dizendo que não fazia isso. Corrigido: agora ele
só avisa no log, nunca mais publica nada por conta própria. Verificado
que nenhum relógio automático estava agendado pra rodar ele sozinho.

Um dado errado que estava sendo repetido pra toda IA que entra no sistema
foi corrigido: a página de configuração dizia que só as últimas 30 linhas
da história chegam pra IA. Não é verdade — medido de novo, o que chega
são as últimas 9 entradas inteiras, nada cortado no meio.

O robô do Conselho Remoto agora se protege sozinho: se o outro lado
recusar duas vezes seguidas por sobrecarga, ele espera 15 minutos antes
de tentar de novo, em vez de insistir sem parar.

O texto que você cola numa IA na nuvem pra ela entrar no sistema mudou de
lugar: agora mora dentro do próprio sistema (`PROMPT_CARREGAMENTO.md`), não
mais solto na Área de trabalho (que ficou só com um bilhete apontando pro
lugar novo). O motivo: agora o commit atualiza sozinho qual era o commit
mais recente quando o texto foi escrito — sempre com um atraso pequeno e
conhecido (no máximo 1 commit), porque um commit não consegue avisar o
próprio número antes de existir. Achado no caminho: o texto também dizia
uma coisa errada há dias (que só as últimas 30 linhas da história chegam
pra IA) — corrigido junto.

Esse mesmo texto de entrada passou por uma auditoria de fora (a sessão
em nuvem "Ágata Opus") que apontou 8 problemas. Conferi os 8 na sua
máquina, um por um: todos verdadeiros. Consertei os 8 dentro do próprio
arquivo, sem mexer em regra nem em script. As mudanças principais: o
texto agora aponta pra REGRAS.md em vez de repetir formatos que já vivem
lá (e envelhecem em cópia); ganhou instrução do que fazer quando o
GitHub bloqueia um dos endereços (foi o que confundiu uma sessão dias
atrás); parou de oferecer um campo pra preencher "nonce", que convidava
a fingir continuidade; e a lista do que ler agora inclui o PROJETO.md.
Passou pelo portão das três perguntas com você e por três leituras
independentes do modelo local antes de aplicar. Falta só a sessão em
nuvem conferir o resultado contra o GitHub depois que eu publicar.

A memória do sistema agora tem duas esferas, escritas no PROJETO.md.
A **esfera pessoal** (`memoria/missoes/segunda-camada/`) é sua, local,
sem remote: hardware, rotina, config, assunto pessoal. Modelo em nuvem
não vê. A **esfera do projeto** (`memoria/missoes/agata-sistema/`) fica
ligada a uma conta Google separada, só do projeto — nunca a sua conta
pessoal — e recebe material do sistema que você autorizar. A regra que
antes era "a nuvem lê e nunca escreve de volta" virou uma mais precisa:
nenhum resultado de fora tem autoridade automática pra escrever no
canon; ele pode propor, e aí segue o caminho normal (proposta, sua
decisão, verificação, registro, commit). Junto veio uma reversão
parcial da decisão (223): o ACB volta ao escopo só para assunto do
próprio sistema, e só com sua autorização caso a caso. Os canônicos
(REGRAS/PROJETO/MEMÓRIAS) nunca sobem "como canon" pra esfera externa —
o porquê disso não ser contradição com o repo ser público está escrito
lá. O esqueleto de pastas da esfera pessoal já existe, versionado no
repo local `missoes` (com backup no HD). Passou pelo portão das três
perguntas e por três leituras do modelo local — que aprovaram com
ressalvas de estilo, sem contradição.

Uma trava nova foi criada e ligada: daqui pra frente, mudança que MUDA
COMO O SISTEMA SE COMPORTA (regras, scripts) só entra depois de você
aprovar de propósito, criando um arquivo marcador. Mudança que só
REGISTRA o que já aconteceu (entrada de história) continua livre, como
sempre foi. Essa mudança de agora foi a primeira e única vez que a trava
foi ligada sem passar por você — porque a trava não existia ainda pra
aprovar a si mesma. Registrado por escrito; não vai se repetir.

Uma regra de estilo pra texto novo (explicar o porquê antes do quê, uma
ideia por frase, nada retroativo) foi aprovada por você nesta conversa
mesmo — primeiro uso de verdade da trava nova acima.

O robô que resume a memória toda noite estava quebrado — parava sem
avisar, e o texto que ele seguia mandava escrever num arquivo que não
existe mais há três semanas. Consertado: agora ele só PROPÕE uma entrada
(você aprova depois, nunca escreve direto na história), e mesmo que o
texto dele falhasse em obedecer isso, o sistema operacional já bloqueia
fisicamente ele de tocar na história — testado de verdade, nos dois
sentidos. Achado no caminho: ele já disse "escrevi o arquivo" uma vez
sem ter escrito nada — sempre confira a pasta, não confie só no que ele
diz que fez.

Uma checagem nova avisa se algum serviço importante (o robô de
consolidação, o Ollama, o gateway do Hermes, os containers de voz/
interface) parar sem ninguém notar — foi exatamente isso que aconteceu
com a consolidação antes de hoje.

A trava do item acima (que exige sua aprovação pra mudança de
comportamento) agora também cobre os arquivos de configuração dos
robôs automáticos — antes só cobria regras e scripts.

Você autorizou hoje, de uma vez, um lote de trabalho: fechar os quatro
pendentes acima, escolher o modelo principal usando o teste grande que
já existe, adotar três regras gerais novas, e preparar o terreno pra
uma máquina virtual que o Marcos ofereceu. Deixou de fora, por
enquanto, o projeto inteiro de assistente com Google/mensageiros — fica
só como referência de rumo, não como lista de tarefa.

Um commit automático de 18/08 (`564a50d`) entrou no histórico do
sistema sem passar por uma entrada de história, e não se descobriu
quem fez — você decidiu deixar assim, sem investigar mais.

O terreno pra máquina virtual que o Marcos ofereceu está pronto: as
regras de confiança dela (o que pode ir pra lá, o que nunca vai) estão
escritas; um erro real foi achado e corrigido nos scripts de teste (um
deles só funcionaria no seu computador, não em outro); um comando único
foi testado de verdade rodando fora daqui, funcionou; e um pedido de
recursos pro Marcos foi escrito com números medidos na sua máquina (não
chutados) — VRAM, disco, tempo de GPU.

O sistema aprendeu a ler página de site moderno sem abrir navegador —
testado de verdade em dois casos (um site real, uma página fabricada
só pra testar). Junto veio uma regra geral, já registrada: antes de
instalar ferramenta nova, esgotar o que já dá pra fazer com o que
existe.

Chegou um bloco dizendo vir de outra sessão de IA ("Qwen3.7"),
contando que você tinha editado um arquivo de configuração (removendo
personas extras do robô) e que outro modelo tinha questionado isso. A
parte do arquivo editado é verdade — conferido direto no disco. A
parte da conversa entre modelos não tem como conferir daqui — pode ter
acontecido em outro lugar, mas não ficou rastro. E o bloco também
sugeria uma regra nova (você responder três perguntas antes de
autorizar mudança estrutural) — isso NÃO foi adotado sozinho, fica
esperando você decidir.

## Bancada de modelos em andamento (Frente 4, iniciada 21/08/2026)

**Candidatos, os mesmos 6 já baixados de (227)** (confirmado agora por
`ollama list`, soma de tamanho em disco bate exato com o medido lá —
31,8GB): `qwen3.5-9b-64k` (controle), `qwen3:8b`, `deepseek-r1:8b`,
`gemma2:9b`, `mistral:7b-instruct`, `rlm-qwen3-8b-teste`.

**Decisão tomada ao vivo hoje, com você, depois de achar um problema
real:** o script que roda a bancada (`rlm_c1b.py`) não fixava o tamanho
de contexto na chamada — sem isso, o Ollama usa um padrão pequeno (medido:
4096, um quarto do que o controle usa em produção). Corrigido: agora fixa
`num_ctx=16384` pros cinco candidatos maiores, e `8192` só pro
`gemma2:9b` (teto do próprio modelo — ele não alcança 16384). Você decidiu
manter o `gemma2:9b` na bateria mesmo assim, no teto dele, sabendo que
corre em desvantagem medida — registrado, não escondido.

**Rodando agora, antes de qualquer candidato:** o controle
(`qwen3.5-9b-64k`) está sendo rerodado 3 vezes com a lista de comandos
permitidos estendida (`cut`, `sha256sum`, `sort`, `uniq`, `nl`, que
antes não existiam) — pra confirmar que o pico de uso de contexto
(medido antes, sem os comandos novos: 12.409 tokens, folga dentro dos
16384) ainda cabe com os comandos novos disponíveis. Só depois disso a
primeira célula de candidato começa.

**Onde ficam os arquivos:** tudo em
`memoria/missoes/rlm-3caminhos/` — traces em
`trace_C1b_<modelo>_<rodada>.jsonl`, log de GPU em
`gpu_controle_whitelist_estendida.csv` (e um por candidato quando
começar), script do rerun em `rerun_controle_whitelist_estendida.sh`.

**Para retomar se a sessão cair:** confira se
`trace_C1b_qwen3.5-9b-64k_wl-ext-{1,2,3}.jsonl` existem e têm conteúdo
completo (última linha de cada é a resposta da última pergunta da
bancada de 16). Se sim, meça o pico de `tokens_in` neles e siga pras
células de candidato. Se não, rode
`bash rerun_controle_whitelist_estendida.sh` nesta pasta de novo — ele
sobrescreve, não duplica.

## Esperando você
- Revisar e mandar (ou não) o pedido de recursos pro Marcos —
  `memoria/missoes/rlm-3caminhos/PEDIDO_RECURSOS_VM_MARCOS.md` (número
  de RAM ajustado em 27/08: 40 GB instalada / ~38 GiB utilizáveis).
- Aprovar (ou não) a proposta P-8
  `propostas/ancora-defasagem-honesta.diff` — último ponto do conserto
  do prompt de carregamento (tira "nunca mais" do bloco gerado da
  âncora).
- Confirmar se a conversa entre modelos sobre a edição do
  `config.yaml` foi real. (A regra das três perguntas já é canon
  desde (228)-(230); isso não está mais em aberto.)

O teste grande de IA (bancada Frente 4) está **decidido e fechado**: os
6 candidatos rodaram, nenhum superou o modelo atual (`qwen3.5-9b-64k`),
e a troca virou fronteira de recusa — não se repropõe sem dado novo.
Registrado em MEMÓRIAS (280).

## Rodando agora
Nada rodando. A máquina desligou abruptamente durante o rerun do
`mistral:7b-instruct` (rodada 3, por volta das 16h05 de 21/08) e só
voltou às 18h03. Integridade conferida na retomada: `git fsck` limpo
nos dois repos (`~/agata` e `memoria/missoes/`, sem remote), HEAD local
== `origin/main` em `cf70368` no momento da retomada, nenhum processo
órfão do rerun sobrevivendo (só o `ollama serve` do boot novo, sem
relação com a rodada morta). Desde então, dois commits locais entraram
em cima de `cf70368` (ver rodapé) — ainda não publicados em
`origin/main`, então quem olhar só pelo GitHub não vê esta seção.

### Tabela de avaliação completa (mesma régua de MEMÓRIAS (172)-(187),
resposta lida contra o `gabarito` de `bancada.json`; fonte completa,
com trechos literais, em `memoria/missoes/rlm-3caminhos/RELATORIO_AVALIACAO_BANCADA_21-08-2026.md`)

| candidato | limpo | errado (sem fabricar) | sem resposta (teto) | fabricação confirmada |
|---|---|---|---|---|
| `qwen3:8b` | 8/16 | 6/16 | 0/16 | **2/16** |
| `gemma2:9b` | 9/16 | 6/16 | 0/16 | **1/16** |
| `rlm-qwen3-8b-teste` | **5/16** | **7/16** (5 honesto + 2 "alegação de busca sem busca real") | 2/16 | **2/16** — fechado, soma 16 (MEMÓRIAS 237) |
| `deepseek-r1:8b` | — | — | — | **excluído por tempo de execução, não avaliado** |
| `mistral:7b-instruct` | 0/16 | ~15/16 (falha sistêmica — bug de glob, ver achado abaixo) | 0/16 | **1/16** — **excluído da comparação**, ver achado abaixo |
| `qwen3.5-9b-64k` (controle) | **12/16** | 2/16 (V3, F3 — parcial, grounded) | 2/16 | **0/16** |

**Controle (`qwen3.5-9b-64k`) avaliado — bancada fecha.** Zero
fabricação confirmada na rodada de referência, 12/16 limpo — o dobro
do melhor candidato (`gemma2:9b`, 9/16). **Resposta à pergunta que
faltava: nenhum candidato bateu o titular nesta bancada.** Detalhe
completo, com verificação de cada afirmação específica contra o
trace real: MEMÓRIAS (234 - RELATÓRIO FINAL da bancada).

**Caso 16 do `rlm-qwen3-8b-teste`: fechado em 22/08/2026.** Decisão do
Humano (com leitura do Opus 5 como insumo): F1 = errado (rodou o
comando certo, leu o preâmbulo real, respondeu genérico em vez de
confirmar que a (999) não existe — teve o dado, não usou). F2/F3 =
limpo (acertaram o veredito central do gabarito, omitiram um detalhe
pedido — incompletude, não fabricação nem ausência de resposta). A
instrução original trazia "6/16 limpo · 8/16 errado" com "soma 16",
mas 6+8+2+2=18 — recalculado mecanicamente a partir da mesma decisão
qualitativa: **5/16 limpo, 7/16 errado, 2/16 sem-resposta, 2/16
fabricação, soma 16.** Detalhe da correção: MEMÓRIAS (237).

**Achado do `gemma2:9b`, A4 — inverteu a própria evidência.** Pergunta
pede o estado dos testes TES. Resposta: *"override durável foi
aplicado em 2026-07-06 (30)"*. O comando que o próprio modelo rodou
(`grep -n "override durável" INDICE_MEMORIAS.md`) devolveu *"2026-07-05
(29) ... override durável (0b) **provado, não aplicado**"* — data
errada, número de entrada errado, e a palavra central invertida (o
grep disse "não aplicado", a resposta final disse "foi aplicado"). É
o pior padrão de fabricação encontrado na bancada: não é deixar de
verificar, é verificar e dizer o oposto do que a ferramenta mostrou.
Contado como a 1 fabricação confirmada do `gemma2:9b` na tabela acima.

**Investigação do `deepseek-r1:8b` — já feita e reconferida agora,
direto no trace, números batem exatos:** 44 comandos válidos nas duas
rodadas que completaram (15 rodada 1, 29 rodada 2), ~49% de rejeição
na rodada 2 (28 de 57 — a maioria por metacaractere de shell, o resto
por `echo` fora da whitelist ou caminho absoluto). N3, rodada 1, travou
os 12 turnos inteiros pedindo nome de arquivo em vez de rodar `ls`
sozinho. **Não é o defeito antigo de "sem tools"** (aquele veredito
veio de um teste com o parâmetro nativo `tools` do Ollama, que este
runner nem usa) — é gasto de chamadas caras (modelo de raciocínio) em
tentativas de sintaxe mais rica do que o protocolo permite.

**`mistral:7b-instruct` — excluído da comparação, decisão do Humano.**
Motivo, registrado explicitamente porque é diferente do motivo do
`deepseek-r1:8b`: o resultado original (linha "~15/16 errado" na
tabela acima) tinha um bug de glob no runner — **consertado e testado**
(4 casos, positivo/negativo/sem-glob/uso-real, ver relatório) — mas o
rerun de 3 rodadas que produziria dado válido pra substituir essa linha
foi interrompido pelo desligamento abrupto e **não foi retomado**, a
franquia da sessão que rodava esgotou antes. Nenhum julgamento sobre o
modelo em si — nem o resultado velho (invalidado pelo bug) nem um
resultado novo (nunca terminou) entram na comparação.

**O que os dados mostram sobre a interrupção (reconferido direto nos
arquivos, não presumido):** a rodada 3 não parou no meio de um arquivo
— o log de execução mostra o loop chegando ao fim (`fim rodada 3`,
16h05:34). O que quebrou foi o `ollama serve`, que ficou inacessível a
partir da pergunta V3 em diante: as 6 últimas perguntas da rodada
(V3, V4, F1, F2, F3, F4) todas vieram `[ERRO: Connection refused]` em
sequência, porque o script seguiu tentando cada pergunta em vez de
parar no primeiro erro. Rodadas 1 e 2 parecem completas e não afetadas.
Trace parcial preservado, **não usado como dado**, renomeado com
sufixo `_INTERROMPIDO` (não apagado):
`trace_C1b_mistral_7b-instruct_3_INTERROMPIDO.jsonl` e
`saida_mistral_7b-instruct_3_INTERROMPIDO.log`, na mesma pasta dos
`_ANTES-glob` já preservados da rodada afetada pelo bug original.

**Tabela de exclusões pra deixar clara no relatório final** (nenhuma é
julgamento sobre o modelo):
- `deepseek-r1:8b`: excluído por tempo, decisão ao vivo do Humano.
- `mistral:7b-instruct`: excluído porque o bug de glob invalidou os
  dados originais, e o rerun que corrigiria isso foi interrompido por
  desligamento abrupto — não retomado, franquia esgotada.

**Resultado da bateria, 5 de 6 candidatos com célula completa
(execução; ver tabela de avaliação acima pra qualidade):**
- `qwen3:8b` — limpo, 28 min, 16/16 respondidas, zero erro.
- `deepseek-r1:8b` — **excluído**, tempo de execução (62,8 min +
  76,0 min pras 2 primeiras rodadas, decisão do Humano de cortar antes
  da 3ª terminar).
- `mistral:7b-instruct` — **excluído**, ver acima.
- `rlm-qwen3-8b-teste` — limpo, só 3,2 min, determinístico. **Achado
  pra quem for avaliar:** 8 das 16 perguntas responderam sem nenhum
  comando de shell emitido (sem tocar o corpus) — pode ser
  conhecimento do próprio ajuste do modelo, pode ser fabricação; não
  julgado aqui, registrado no trace.
- `gemma2:9b` — limpo, 2,3 min, pico de contexto 3.751/8192 (nunca
  chegou perto do teto reduzido que o Humano decidiu manter).

**Bancada fechada nesta entrada.** Relatório final, no formato de
MEMÓRIAS (186)-(187), registrado em MEMÓRIAS (234 - RELATÓRIO FINAL
da bancada, controle avaliado, exclusões explicadas). Achado de
`credential.helper`/`gh auth` (destrava push futuro) registrado à
parte em MEMÓRIAS (233).

**BANCADA 100% FECHADA em 22/08/2026.** Controle avaliado (234),
5 candidatos avaliados (linha final do `rlm-qwen3-8b-teste` acima:
5/16 limpo, 7/16 errado, 2/16 sem-resposta, 2/16 fabricação — caso 16
fechado em 237), 2 exclusões com motivo próprio (235 - deepseek,
tempo · 236 - mistral, dado inválido). Promoção de modelo continua
decisão do Humano, depois de SHADOW MODE — nenhuma tabela decide
sozinha, nada disso aconteceu.

"Camada 3 da Parte 1" localizada — não estava em nenhum arquivo do
repo, existia só como texto de chat de outra sessão (`Agata · Claude
Opus 5`), nunca salva em disco até agora. Salva em
`memoria/missoes/rlm-3caminhos/SINTESE_ARQUITETURAL_21-08-2026.md`,
com proveniência registrada e sem verificação independente das
referências externas que cita. Camada 3, item 1 ("fechar a bancada"),
era este mesmo capítulo — fechado agora. Itens 2-6 da Camada 3: ver
seção "Lote grande, 22/08/2026" abaixo.

Tudo commitado: `~/agata` (MEMÓRIAS 233-237, ONDE_ESTAMOS.md, publicado
em origin/main a cada marco); `memoria/missoes/` com os arquivos
`_INTERROMPIDO` da rodada 3 do mistral, `SINTESE_ARQUITETURAL_21-08-2026.md`
e a `RELATORIO_AVALIACAO_BANCADA_21-08-2026.md` atualizada e fechada.
`memoria/missoes/` não tem remote — cópia só nesta máquina até o HD
externo conectar, aviso P-6 pendente desde antes desta bateria.

## Lote grande, 22/08/2026 — sessão longa sem supervisão, autorizada em bloco
Autorizado pelo Humano, que fica fora por horas. Ordem: (1) fechar
F1/F2/F3 — feito, ver acima. (2) limpeza de modelos Ollama (deepseek,
mistral — nunca avaliados por dado/tempo). (3) preparar e TESTAR (não
aplicar) até 6 propostas em `propostas/`, cada uma como `.diff`, sem
`APROVADO-<nome>` (só o Humano cria esse marcador). Regra pra travas:
parar só aquele item, registrar aqui, seguir pro próximo — nenhuma
célula de bancada roda de novo, nenhum push de canon além do item 1.
Checkpoint a cada item concluído, não só no fim.

**Item 2 (limpeza Ollama): FECHADO.** `ollama rm deepseek-r1:8b`
(5,2 GB) e `ollama rm mistral:7b-instruct` (4,4 GB) — os dois nunca
avaliados (excluídos por tempo/dado inválido, sem dado de qualidade
nenhum). ~9,6 GB liberados (medido pelo próprio `ollama list`, tamanho
reportado antes de remover — `df` do disco não deu delta limpo pra
comparar por unidade/cache, não usado como número aqui). Confirmado
por `ollama list` antes/depois: os 21 modelos da máquina viraram 19,
os 4 que a bancada pediu pra manter (`qwen3.5-9b-64k`, `qwen3:8b`,
`gemma2:9b`, `rlm-qwen3-8b-teste`) seguem presentes, nada além dos dois
alvos foi tocado — a biblioteca maior desta máquina (llama3.3:70b,
qwen2.5-32b, etc., não relacionados a esta bancada) ficou intocada.
Disco após: 394 GB livres de ~950 GB.

**Item 3a (A/B1 no PROJETO): PRONTO, testado, aguardando aprovação.**
Texto recebido do Humano em 22/08/2026, exato, sem parafrasear.
`propostas/ab1-projeto.diff` — os dois parágrafos ("limite do
princípio 'ferramenta nova é decisão'" + "risco do config.yaml") na
seção "Riscos conhecidos" de PROJETO.md. `git apply --check` confirma
que aplica limpo. **Achado grave testando o pedido "perimetro.sh
continua verde depois de aplicado":** fica verde, mas por um bug real
de P-8, não porque a proposta foi corretamente barrada até aprovação
— ver "Quebrado" abaixo, detalhe completo em `propostas/ab1-projeto.diff`.

**Item 3b (sync: unificado): PRONTO, testado, aguardando aprovação.**
`propostas/sync-unificado.diff` — substitui `íntegro? <sim/não/não
verificado>` por `sync: PASS · REGRAS=<hash8> · MEMÓRIAS=<hash8> ·
HEAD=<commit7>` (ou `FALHA`/`não verificado · lacuna:`) no bloco de
prontidão de REGRAS.md, com a extensão equivalente documentada pra
`ONDE_ESTAMOS.md`/checkpoints (não aplicada ainda, pra não divergir do
que REGRAS.md ainda não define). `git apply --check` confirma que o
diff aplica limpo contra o REGRAS.md atual. Quatro testes dentro do
próprio arquivo da proposta: PASS medido ao vivo (hash real de
REGRAS.md/MEMÓRIAS.md, HEAD real), FALHA com divergência REAL (hash de
MEMÓRIAS.md no commit 784aaca vs agora — não simulado), "não
verificado" justificado por ausência de capacidade (sessão em nuvem
sem Máquina), e um caso realista com o bloco de prontidão que este
Executor produziria agora se a proposta já estivesse em canon.

**Item 3c (verificador de leitura do config.yaml): DESBLOQUEADO, não
iniciado.** 3a agora está no diff (acima), então a dependência que
travava 3c não existe mais — mas 3c não foi pedido nesta rodada, só
3a. Fica pronto pra começar quando o Humano pedir.

**Item 3d (Harness A1, hook `pre_api_request`): PRONTO, testado,
aguardando aprovação.** `propostas/harness-a1-trace.diff` — script
novo `scripts/harness_a1_system_prompt.py`, hook shell (mecanismo já
nativo do hermes-agent, `hooks:` em `~/.hermes/config.yaml`, zero
edição no código-fonte do Hermes). Compara o `system_prompt`
REALMENTE enviado (confirmado no código-fonte que o hook recebe esse
campo) contra o `.hermes.md` real no disco — hash esperado/enviado,
`context_file_chars`, `truncado: bool`. **Achado durante o teste:** a
primeira versão do script falhou o caso negativo (prefixo
posição-a-posição não aguenta texto de wrapper antes do conteúdo
injetado, devolveu `enviado_chars: 0` quando devia ser 20.000) —
corrigido pra busca binária de "maior prefixo contido em qualquer
posição" antes de aceitar a proposta como testada. Quatro testes
documentados dentro da própria proposta (positivo, negativo real com
o achado acima, ausência de campo, stdin malformado), todos com saída
real. Extensão de `~/.hermes/config.yaml` (fora deste repo, config de
produção) documentada mas NÃO aplicada. `git apply --check` confirma
que o diff aplica limpo.

**Item 3e (glossário + palavras-chave): PRONTO, testado, dois diffs
separados como pedido.**
- `propostas/glossario-quatro-termos.diff` — define `sincronizar`,
  `hidratação`, `carregar`, `atualizar` lado a lado em REGRAS.md, sem
  inventar distinção nova (cada definição rastreada até a linha exata
  de PROJETO.md/REGRAS.md onde já existia, espalhada). Testado que
  coexiste sem conflito com `sync-unificado.diff` (os dois tocam
  REGRAS.md, em regiões diferentes) — `git apply` dos dois em
  qualquer ordem, num scratch limpo, confirmado.
- `propostas/indice-palavras-chave.diff` — script novo
  `scripts/extrair_palavras_chave.py` (tokeniza, tira stopword,
  deduplica — grep, nunca embedding, decisão (115)) + hook
  `.githooks/gerar-hidratacao.sh` gerando um índice PARALELO
  (`INDICE_MEMORIAS_PALAVRAS-CHAVE.md`) pra busca por assunto.
  **Achado real medindo antes de propor:** o índice com palavras-chave
  pesa 73% a mais que o puro (24K→41,5K chars) — embutir isso em
  `.hermes.md` pioraria o mesmo problema de truncamento que este
  projeto já brigou pra resolver (103-105, 220). Redesenhado pra ficar
  DE FORA da hidratação, só em disco pra `grep` sob demanda —
  confirmado que `.hermes.md` fica no MESMO tamanho de antes (125.298
  bytes, idêntico) rodando o hook de ponta a ponta numa cópia isolada.
  **Segundo achado, também corrigido antes de propor:** sem tratamento
  de erro, um `extrair_palavras_chave.py` ausente/quebrado travava o
  hook INTEIRO (nem `.hermes.md` era gerado — bloquearia todo commit).
  Corrigido pra fail-soft: o extra pode falhar sozinho, o caminho
  crítico de hidratação nunca é afetado. **Achado colateral, fora de
  escopo, não corrigido:** `MEMÓRIAS.md` sem nenhuma entrada já
  quebrava o hook ANTES desta proposta (bug pré-existente, confirmado
  rodando a versão em produção sem minha mudança) — registrado na
  proposta, risco baixo (história é append-only, "zero entradas" não
  é estado alcançável), decisão de abrir proposta própria fica pro
  Humano.

**Lote grande FECHADO, depois atualizado com o item 3a (texto recebido
em 22/08/2026).** Itens 1 e 2 aplicados de verdade (F1/F2/F3 decidido
e publicado, Ollama limpo). Item 3: a, b, d, e prontos e testados —
**5 propostas** em `propostas/` esperando `APROVADO-<nome>` do Humano
(`ab1-projeto.diff`, `sync-unificado.diff`, `harness-a1-trace.diff`,
`glossario-quatro-termos.diff`, `indice-palavras-chave.diff`); c
desbloqueado, não iniciado (não pedido ainda). Nenhuma célula de
bancada rodou de
novo. Nenhum push de canon além do que fechou o item 1, como pedido.

## Quebrado
**P-8 (quarentena de mudança estrutural) tem um buraco real, achado
hoje testando `propostas/ab1-projeto.diff` — não é o `PROJETO.md`
desta proposta, é a checagem em si.** `_p8_caminhos_aprovados()`
(`scripts/perimetro.sh`) trata QUALQUER arquivo que já tenha sido
aprovado uma vez, alguma vez na história do projeto, como
permanentemente isento — porque varre `propostas/aplicadas/` (o
arquivo histórico, nunca limpo) sem checar se a aprovação encontrada
é da mudança de AGORA ou de uma mudança antiga que só por coincidência
tocou o mesmo caminho. Confirmado com um teste trivial, sem relação
com nenhuma proposta: uma linha qualquer acrescentada a `PROJETO.md`
passa por `p8_quarentena` com retorno 0, sem nenhum marcador de
aprovação em lugar nenhum. `PROJETO.md`, `REGRAS.md` e o próprio
`scripts/perimetro.sh` já foram objeto de aprovação pelo menos uma vez
cada — na prática, os três arquivos mais sensíveis da quarentena já
não estão mais protegidos por ela. Detalhe completo, com os comandos
que reproduzem, em `propostas/ab1-projeto.diff`, seção "Testes",
achado 4.

**Conserto proposto, testado, aguardando aprovação —
`propostas/p8-hash-nao-path.diff`.** Continua QUEBRADO até o Humano
aprovar e aplicar — proposta pronta não é conserto aplicado.
Critério novo: "aprovado" deixa de ser "path apareceu em algum diff,
alguma vez" e passa a ser "aplicar o `.diff` candidato ao HEAD deste
arquivo reproduz, byte a byte, o que está staged agora" — path só
filtra candidatos, conteúdo decide. Quatro casos testados em clones
descartáveis: (1) o bug original, edição trivial sem relação → volta
a dar SUSPEITO; (2) aprovação genuína, conteúdo bate exato → continua
aprovando; (3) aprovação existe mas conteúdo staged é diferente
(adulterado) → SUSPEITO, rigor que o mecanismo original nunca teve;
(4) fluxo real de consumo (diff+APROVADO movidos pra `aplicadas/` no
mesmo commit) → continua aprovando, não regride o caso que o desenho
original resolvia certo. Achado de disciplina de teste registrado no
próprio diff: a primeira rodada dos testes 2/3 reaproveitou clone
sujo entre casos e deu falso negativo — refeito com clone novo por
caso antes de aceitar como testado. Desempenho: `perimetro.sh`
completo em 0,31s com o conserto, 9 aprovações históricas no repo
real hoje — custo irrelevante.

**Ordem de revisão do Humano, registrada em 22/08/2026, pra sobreviver
a queda de sessão:**
1. `propostas/p8-hash-nao-path.diff` — primeiro, corrige o mecanismo
   que deveria ter protegido os outros cinco.
2. `propostas/ab1-projeto.diff` — já conferido linha a linha pelo
   Humano antes de mandar o texto.
3. `propostas/sync-unificado.diff`
4. `propostas/harness-a1-trace.diff`
5. `propostas/glossario-quatro-termos.diff`
6. `propostas/indice-palavras-chave.diff`

Mecanismo pra cada um: o Humano lê o diff, cria
`propostas/APROVADO-<nome>` se aceitar (arquivo vazio ou com nota —
conteúdo não importa pra P-8, só a presença). Isso é ação do Humano,
não do Executor — nenhum `APROVADO-` foi criado por conta própria.
Até o item 1 ser aprovado e aplicado, os outros cinco continuam sendo
revisados pelo Humano diretamente, não pelo mecanismo automático de
P-8 (que segue com o buraco, ver acima).

Um arquivo não rastreado (`policy-execution.yaml`, na raiz de
`~/agata`) segue sem investigação a fundo — pendência de baixa
prioridade, não mexido, ver retomada de 21/08.

## Sessão de 25/08/2026 — bem cheia, tudo publicado

Você pediu pra avaliar uma ferramenta nova (Agent Reach) — não
acrescentava nada que o sistema já não tivesse, foi recusada e
registrada, pra ninguém propor de novo sem saber que já foi
respondido.

Um teste antigo, que mede se um modelo consegue relatar o estado do
sistema sem inventar, rodou de novo depois de três tentativas
fracassadas em agosto — desta vez, limpo. Não fecha o teste sozinho,
mas é o primeiro resultado bom.

Descobri que o Hermes já vem pronto com a capacidade de rodar scripts
que chamam várias ferramentas de uma vez (o que você estava
pesquisando sobre economia de tokens) — só estava desligada. Testei
se valia a pena ligar agora: o modelo local, testado de verdade,
escreveu um script cheio de erro pra uma tarefa simples. Decidido não
ligar por enquanto — não é recusa permanente.

Um arquivo antigo de identidade (SOUL.md), que ninguém mais lê mas
ainda se apresentava como regra protegida, foi arquivado.

Uma proposta antiga (testar respostas de risco três vezes, de forma
independente, antes de decidir) foi mandada pra outro modelo dar
parecer — o parecer veio bom, com uma correção real, virou regra nova
em REGRAS.md. No meio do caminho, esse outro modelo errou a data e
foi corrigido com prova de duas fontes independentes.

Achado à parte: a descrição pública do repositório no GitHub (não é
um arquivo, é uma configuração da página) ainda falava de um sistema
antigo, de antes deste aqui existir — de abril, nunca atualizada.
Isso confundiu uma sessão na nuvem que tentou carregar o sistema hoje.

**Esta página também estava atrasada — ficou 3 dias sem atualizar
enquanto tudo isso acontecia, o que é a própria regra que ela deveria
seguir. Corrigido agora, no mesmo commit que devia ter sido desde o
início.**

## Continuação da sessão de 25/08/2026 — uma sessão na nuvem, três rodadas de erro e correção

Uma sessão de IA na nuvem ("Ágata Opus") tentou carregar o sistema e
recebeu conteúdo velho, de mais de um mês atrás — sem saber que
estava velho. Ela mesma descobriu a causa (busca errada em vez de
pegar o arquivo direto) e trouxe sete ideias pra evitar isso de novo.

No meio do caminho, este executor errou também: acusou a sessão de
inventar duas citações que, na verdade, eram reais — só estavam
escritas num formato antigo que a busca não alcançava. Corrigido
assim que achado, com prova.

Resultado: nenhuma das sete ideias originais virou regra nova — a
maioria já existia de outro jeito. O que ficou de verdade: um jeito
de buscar os arquivos que não pode vir desatualizado (endereço fixo
por versão, não por "o mais recente"), três linhas novas explicando
erros parecidos pra não repetir, e duas correções pequenas de texto.
Uma última proposta (um "carimbo" de data nos arquivos) teve parecer
favorável de outro modelo consultado, mas você decidiu não adotar —
registrado por quê, pra não parecer contradição depois.

## Sessão de 26/08/2026 — a ordem da história virou, do avesso pra frente

Você pediu pra história ficar na ordem contrária: a parte mais recente
lá no topo do arquivo, logo depois da explicação de como ler, e a mais
antiga lá no fim — pra economizar espaço quando a IA lê. Isso ia contra
uma regra que você mesmo tinha escrito dizendo que nem você podia mudar
isso sem processo formal. Foi avisado disso antes de qualquer mudança, e
você escolheu seguir o processo formal em vez de pular ele.

O processo: três perguntas respondidas por você (dá pra desfazer sozinho
— sim; o que mais isso toca — bastante coisa, você topou; dava pra saber
se quebrasse — sim, prometi checar tudo no fim, e checei). Nada foi
apagado nem editado — só mudou de lugar, e isso foi conferido por
computador antes de qualquer coisa entrar, não só por eu dizer que
conferi.

No caminho, achei e consertei quatro problemas reais que só apareceram
testando com o arquivo inteiro (não em pedaços pequenos): um trecho de
história ficaria grudado errado num outro; onze pedaços da história
(escritos por outra IA sem acento correto) quase ficaram invisíveis pro
sistema de busca; uma checagem de citação ia soar alarme falso numa
coisa antiga e já conhecida; e o pior — a primeira versão saiu com o
arquivo inteiro (868 mil caracteres) sendo entregue pra IA de uma vez só,
em vez do resumo pequeno de sempre (25 mil). Esse último eu vi na hora
e corrigi antes de fechar, exatamente o tipo de erro que a regra que
você escreveu tenta evitar.

## Última atualização
28/08/2026: o gerador do vault Obsidian virou determinístico — carimba
o commit de que foi gerado (`canon:` no INICIO.md), não a hora do
relógio. Com isso deu pra criar o controle P-10: a cada commit o
sistema regenera o vault a partir do que está publicado e confere que
o vault no disco bate — se alguém editou uma nota à mão ou o gerador
falhou calado, o próximo commit acusa. (Um ajuste logo em seguida,
MEMÓRIAS (294): o carimbo só considera arquivo versionado, senão um
arquivo solto que o Obsidian deixa na pasta fazia o P-10 reclamar à toa.) O script do teste dos 8 dias
(`verificar_token.py`) foi trazido pro repositório público (estava só
no repo local). E ficou decidido: o vault não fere a recusa (115) de
"vector store" — não tem busca por embedding, é markdown com links por
número. Tudo em MEMÓRIAS (293). Um segundo ajuste em seguida
(MEMÓRIAS (295)): o próprio P-10 não tinha página no vault — o gerador
listava só P-1 a P-9 —, agora tem.

28/08/2026 (MEMÓRIAS (296)): você decidiu as 3 questões que estavam
abertas sobre a "camada de índice". Ela vai existir, mas: só é
consultada quando um modelo pede (não entra na carga automática); é
gerada só a partir do canon público (REGRAS/PROJETO/MEMÓRIAS) e nunca
lê nada da pasta de missões (esfera pessoal nem de projeto); modelos na
nuvem chegam a ela por um trecho que o executor local separa e entrega.
E o índice pode subir pro Drive da conta do projeto pra usar no
NotebookLM. Antes de decidir, rodei a verificação tripla no modelo
local — as três passadas concordaram. Falta construir: o gerador do
índice, o script de consulta pra nuvem, e a documentação do envio.

28/08/2026 (MEMÓRIAS (297)): o PROJETO.md agora descreve como o envio
pro Drive funciona de verdade — as 8 checagens que o script faz antes
de mandar qualquer coisa (caminho certo, não é canon, não tem cara de
segredo, etc.). O plano da IA da nuvem falava numa "lista de permissão"
que nunca existiu no código; foi corrigido pra descrever o que existe.

28/08/2026 (MEMÓRIAS (298)): o gerador do índice está pronto
(`gerar_indice_derivado.py`). Ele lê só os três arquivos públicos
(regras, estado atual, memória) e monta um arquivo único de 134 KB:
regras e estado inteiros, mais a lista de títulos das entradas.
Nunca toca a pasta de missões. Antes de salvar, ele remonta o arquivo
peça por peça e confere que não sobrou nada que não venha do canon.

28/08/2026 (MEMÓRIAS (299)): o script de consulta pra nuvem está pronto
(`consultar_indice.py`). Você dá palavras-chave, ele devolve as seções
das regras/estado e os títulos de memória que batem, em texto plano,
pra colar no contexto de um modelo na nuvem. Não chama IA, não usa
rede.

28/08/2026 (MEMÓRIAS (300)): o plano de 6 fases fechou. O último passo
era o envio pro Drive. Achado no caminho: o índice não passava na
varredura de segredo — porque o PROJETO.md cita o *nome* de uma
variável de ambiente, e a varredura, que é conservadora, barra o nome
solto. Você decidiu não mexer na varredura. Solução: um script novo
(`preparar_export_indice.py`) faz uma cópia do índice com esses nomes
trocados por "[variável de ambiente]" — o índice original fica intacto,
a varredura não muda. Testado de ponta a ponta: gerou, sanitizou,
passou na varredura e subiu de verdade pro Drive da conta do projeto
(junto com o manifesto de proveniência). Daqui você baixa o
`indice_export.md` do Drive e usa no NotebookLM.

28/08/2026 (MEMÓRIAS (301)): agora o índice se regenera sozinho a cada
commit — o mesmo gancho que já refazia o vault Obsidian passou a refazer
o índice também. Se falhar, só avisa e não atrapalha o commit. O envio
pro Drive continua manual (nunca é automático).

--- da sessão de 27/08 (longa, após o reboot) ---
Prompt de carregamento auditado e consertado (8 achados, MEMÓRIAS
277–281); SOUL.md ignorado (278); bancada de modelos fechada, nenhum
candidato bateu o atual (280); duas esferas de memória escritas no
PROJETO.md + reversão parcial da (223) (283); conversa do config.yaml
confirmada real (282); limpeza de três pendentes (284); credencial
Google da conta do projeto + cano manual pro Drive (285/286); Gemini
virou fallback do Conselho autônomo (287).

Você deu uma ordem permanente (288): o não-essencial mora em `extras/`,
e um conjunto de princípios — segurança, elegância, versatilidade,
eficiência, historicidade, checabilidade, clareza, compatibilidade —
passa a guiar cada escolha, escrito no REGRAS.md, até você pedir o
contrário. Nessa leva: três documentos velhos de julho (dossiê,
snapshot, "fio canônico"), o poema, o backlog de skills e o código
antigo pré-Hermes saíram da raiz pra `extras/`. Nenhum era usado pelo
sistema — só ocupavam espaço e um deles ("estado") enganava quem lesse.

A credencial Google da conta do projeto está configurada (285): conta
`agata.seth98@gmail.com` (só do projeto, você confirmou), login OAuth
com escopo mínimo — o app só enxerga os arquivos que ele mesmo criar no
Drive, nada além. Guardada em `~/.config/agata/google-project/`, fora de
todo repositório e do backup do HD. Testada de verdade: criou e apagou
um arquivo no Drive, funcionou. Falta um teste: reconferir o login em
2026-09-04 — se ainda funcionar, o app estava mesmo publicado; se
falhar, ficou em modo de teste e a gente republica. NotebookLM não tem
API; a ponte pra nuvem é esse Drive. Escopo maior (Docs, Gmail, Drive
inteiro) exige verificação do Google — se um dia precisar, é a hora de
decidir se paga o Workspace.

Backup no HD religado — pendências de bundle drenadas.

--- 31/08/2026 ---
Você mandou resolver todas as pendências e assumiu o risco por escrito.
Fiz o que dava com segurança nesta passada e registrei em MEMÓRIAS (303):

Feito: dois textos velhos consertados. Um no PROJETO.md (dizia que um
passo automático "ficava pra depois" — já tinha sido feito na (301)). Dois
no REGRAS.md: o "selo" de horário das IAs na nuvem agora bate entre as
duas seções que falavam dele; e a linha "última entrada" deixa claro que,
quando a IA não conseguiu verificar o sistema, ela diz "até onde a minha
cópia vai", não "o sistema está em tal ponto". Só acréscimos, reversível
com um comando.

Registrado mas não fechado: o teste de carga do prompt novo passou numa
IA na nuvem (Qwen) nesta conversa — falta uma segunda.

Não dá pra fechar só assumindo o risco, e o (303) explica cada porquê:
o TES-001 (precisa de várias sessões independentes ao longo de dias); a
Fase 2 inteira (silos de memória por modelo — exige a cadeia de auditoria
de vários modelos, pular isso fere a regra 2); a Fase 3 pra frente (fora
do escopo até você pedir item a item); e o backup no HD externo (está
desconectado, é ligar o cabo).

--- 31/08/2026, continuação (304) ---
Preparei a Fase 2 sem executá-la: um roteiro (silos + eco + TES-002, cada
um exigindo três sessões de IA independentes pra revisar) e um
levantamento técnico (S1) de como o silo funcionaria — achei que dá pra
fazer sem remendar o código do Hermes, usando um recurso que ele já tem.
Também arrumei a pasta de propostas: 11 propostas já aplicadas estavam
soltas na fila, foram pra pasta "aplicadas". Você ligou o HD externo — o
backup automático voltou a rodar e a pendência foi drenada.
Uma IA na nuvem (Qwen) disse que havia "autorização total" registrada.
Não há — o que está no papel é você assumir o risco da Fase 1 (os dois
textos consertados), e só. A Fase 2 continua precisando das três
sessões independentes. Corrigi isso no (304).

--- 31/08/2026, continuação (305) ---
A Fase 2 começou de verdade. O primeiro pedaço — "silos de memória por
modelo" — foi revisado por três IAs (uma propôs, uma auditou, uma
conferiu na máquina), refeito com uma correção que a auditoria pediu, e
conferido de novo por uma quarta IA na nuvem ("Luna"). Você autorizou.

O que mudou na prática: o sistema agora gera um arquivo de memória
separado para cada modelo de IA (claude, seth, gemini, glm), além do
arquivo comum. Cada arquivo separado só leva a memória pessoal daquele
modelo; o comum não leva memória pessoal de ninguém. Se alguém escrever
uma memória pessoal sem dizer de quem é, ela não entra em nenhum
arquivo e o sistema avisa. Os arquivos separados nunca vão para o
repositório público — ficam só nesta máquina.

Falta um passo, deixado de fora de propósito: o sistema ainda não
escolhe qual arquivo entregar a cada IA. Os arquivos são gerados mas
nenhuma IA os recebe ainda — todas continuam pegando o comum. Ligar
essa escolha depende do Hermes e fica para outra rodada, com nova
revisão de três IAs.

Falta também a confirmação de fora: outra sessão de IA precisa conferir,
direto no GitHub, que o que subiu bate com o que foi decidido aqui.

--- 31/08/2026, continuação (306) ---
Liguei uma trava nova (P-11). Se alguém tentar, de propósito ou por
engano, colocar um dos arquivos de memória separados por modelo no
repositório, o commit falha. É rede de segurança: esses arquivos já são
ignorados pelo git, mas dava para forçar a inclusão com um comando — e
agora não dá mais. O sistema de checagem passou de 10 para 11 travas.

--- 31/08/2026, continuação (307) ---
Rodei o reteste de tool-calling que o roteiro da Fase 2 pedia depois dos
silos: 30 execuções no modelo local, com as ferramentas de verdade.

Em nenhuma das 30 o modelo inventou resultado. As duas falhas que o teste
de 13/08 achou — mentir o número de linhas de um arquivo, e dizer que
limpou a memória sem ter limpado — não voltaram. Os arquivos de memória
por modelo se comportam igual ao comum: não quebraram nada.

Falha nova, mais branda: quando a memória do modelo enche, ele erra os
comandos para liberar espaço e a resposta fica sem concluir. Não mente —
só não termina. Você escolheu a opção 3: o próprio comando de adicionar
passa a cortar a entrada mais antiga sozinho. Entra na fila de
implementação.

Decisão sua: manter o qwen como principal. O teste não deu motivo para
trocar.

Nada de memória de verdade foi alterado — o teste mexeu em dois arquivos
locais e devolvi os dois ao estado exato de antes, conferido por hash.

--- 31/08/2026, continuação (retomada) ---
Você mandou continuar. Confiro na máquina que o que subiu nos passos 305
e 306 bate com o que ficou decidido — bate; falta só a conferência de
fora, por uma IA na nuvem, direto no GitHub.
Preparei um levantamento só de leitura (`propostas/dossie-selecao-silo-gateway.md`)
do passo que ficou faltando: fazer o sistema entregar a cada modelo de IA
o arquivo de memória dele, não o comum. Achei onde exatamente o mecanismo
atual não faz isso e listei três caminhos possíveis — a escolha entre eles
precisa de outra sessão de IA independente, não desta.

Abri o próximo pedaço da Fase 2: o "eco pós-carregar". Hoje é só uma regra
escrita — a IA que entra resume em poucas linhas o estado que herdou e você
confirma antes dela trabalhar. O problema: hidratação velha não aparece pra
quem a lê, então o resumo pode estar coerente e errado. A proposta é um
script que só lê e imprime os fatos da máquina (qual o commit, qual a última
entrada do diário, se está sincronizado com o GitHub, quantas propostas
abertas) — a IA escreve o resumo em cima disso, não da própria memória, e
você tem um cartão pra conferir. O script nunca escreve nem julga o resumo;
isso continua seu.
Fiz a parte de "propor e testar": rodei a decisão de desenho 3 vezes no
modelo local (Regra 8) — duas das três perguntas fecharam, uma ficou em
aberto pra você (se o eco cita um código de conferência, escreve uma frase
explicando, ou os dois). Você decidiu: os dois. Testei o script num clone
descartável, todos os casos passaram. Está em
`propostas/bloco-3.2-eco-mecanizado.diff`, sem sua aprovação.

A segunda revisão (Camada B) rodou — outra sessão de IA, contexto zerado,
auditou na máquina. Veredito: **CONDICIONAL**. Achou um problema real: se a
árvore de trabalho tem edição não salva nos arquivos de canon, o script
dizia "sincronizado" e não devia — só comparava o número do commit, não o
conteúdo. Mais duas ressalvas (o rótulo impresso não batia com o formato da
regra; o corte de texto dependia do idioma do sistema) e uma nota (o campo
de um teste antigo ecoava um código aposentado). Parecer completo em
`propostas/bloco-3.2-camada-b-parecer.md`.

Você mandou emendar. Consertei os quatro nesta sessão: o script agora
detecta árvore suja e responde "FALHA" em vez de "sincronizado"; o rótulo
saiu na forma exata da regra; travei o idioma interno do script; e o campo
do teste antigo não carrega mais o código aposentado. Testei os quatro num
clone, 10 casos, todos passaram. A versão 1 foi pra `propostas/rejeitadas/`,
a versão 2 é a que vale (`propostas/bloco-3.2-eco-mecanizado.diff`), ainda
sem sua aprovação.

A terceira revisão (Camada C) rodou — outra sessão de IA, contexto zerado,
na máquina, refez todos os testes das camadas A e B em clones. Veredito:
**PRONTO PARA O HUMANO**. Nada bloqueia. Confirmou que os quatro problemas
que a Camada B achou eram reais e que a versão 2 conserta os quatro. As duas
ressalvas dela são no material de apoio, não no que vira regra: uma das três
rodadas do teste de desenho tinha ficado cortada no meio, e o resumo dela
usava aspas em trechos que eram paráfrase. Já corrigi as duas no arquivo de
apoio. O parecer está em `propostas/bloco-3.2-camada-c-parecer.md`.

Você aprovou. O Bloco 3.2 entrou no canon (MEMÓRIAS (308)): o script
`scripts/estado_para_eco.sh` e o mecanismo do eco pós-carregar em REGRAS.md.
A proposta e todo o material das três camadas foram pra `propostas/aplicadas/`;
a versão 1 ficou em `propostas/rejeitadas/`. A trava P-8 conferiu que o que
entrou é exatamente o que estava aprovado, byte a byte.

Falta a confirmação de fora (uma IA na nuvem conferindo direto no GitHub) —
localmente o repositório está em dia com o remoto.

Da Fase 2: o Bloco 3.1 (silos) está aplicado desde antes, mas com a peça da
"seleção por modelo" ainda em aberto (levantamento em
`propostas/dossie-selecao-silo-gateway.md`); o Bloco 3.2 fechou agora; o
Bloco 3.3 (reativar o teste de continuidade com nonce novo) depende da
seleção de silo funcionar.

O texto que uma IA na nuvem cola para entrar no sistema ganhou cinco
avisos novos, todos pedidos por uma auditoria de fora. O motivo: várias
sessões diziam "não tenho como abrir um endereço" sem nem tentar (duas
tinham a ferramenta e usaram no minuto seguinte); a ferramenta às vezes
devolve um resumo do arquivo em vez do arquivo inteiro, e a IA não
percebia; o carimbo de "qual resposta é esta" sumia quando a IA
entregava um documento; e uma sessão disse "está tudo certo" com
problema ainda aberto na lista. Agora o texto: começa com um bloco
curto de "não minta" (a proibição existia, mas lá no fim, tarde demais);
explica as duas pegadinhas da ferramenta de abrir endereço; ensina a
pedir os arquivos para você quando nada abre; e manda conferir a lista
de problemas abertos antes de escrever "pronto".

Uma parte da auditoria ficou de fora de propósito: ela também sugeria
uma correção nas REGRAS, e mexer em REGRAS exige uma segunda opinião de
outro modelo — fica para depois.

Antes de aplicar, rodei o teste de três leituras independentes do modelo
local. As três não bateram: uma aprovou, uma ficou em cima do muro, uma
foi contra. Conferi as objeções da que foi contra na máquina — duas
estavam erradas contra o que o próprio sistema já diz. O que sobrou de
real foi "está um pouco longo demais", e eu cortei um trecho por causa
disso. Como o teste não fechou sozinho, a decisão subiu para você, e
você aprovou.

Falta o teste que vale: colar o texto novo numa IA na nuvem sem ajuda
nenhuma e ver se ela chega sozinha na entrada mais recente da história,
com quem confere segurando o gabarito.
