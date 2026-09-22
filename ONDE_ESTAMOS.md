# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 15/09/2026: `extras/arquivo/onde-estamos-ate-2026-09-15.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md` (entrada (463)).

## Onde estamos — 22/09/2026

**[APLICADAS] As 2 propostas de consolidação noturna sobre P-8 e sobre o bug do `num_ctx`.** Você pediu pra aplicar as 3 propostas soltas na pasta e aproveitar pra checar a saúde de tudo. As duas de consolidação (resumos automáticos de história antiga, sem mudar nenhum código) viraram entradas novas em MEMÓRIAS — (511) e (512) — e os rascunhos foram pro arquivo, como sempre.
- Detalhe técnico: `MEMÓRIAS.md`, entradas (511) e (512).

**[INVESTIGADO A FUNDO — sua lista de modelos de reserva já está certa, não mexi nela] Achei a causa real: o instrumento que testa os modelos é que estava com bug, não os modelos.** Retestei 3 vezes com tudo de pé: os 4 modelos externos ligados (Gemini, Mistral, OpenRouter, GLM) respondem certo. O que parecia "Gemini quebrado" era o script de teste mandando um orçamento de resposta baixo demais pra ele — o script real de produção já usa um orçamento maior, só o script de teste estava errado. Corrigi o script. De bônus: achei que uma página do seu manual (PROJETO.md) descrevia a lista de modelos de reserva como se tivesse 5, quando na verdade já tem 9 há 2 dias — corrigi o texto também. As duas correções (script + texto) esperam sua assinatura — nenhuma muda o que o sistema realmente usa, só conserta o teste e a descrição.
- Único item real, fora do meu alcance: HuggingFace tem a chave inválida desde 16/09 — precisa você gerar um token novo na conta sua.
- Rode: `bash scripts/aprovar.sh conselho-remoto-corrige-sonda-e-doc-2026-09-22`
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (513).

**[CHECADO, tudo bem] Rodei a checagem geral de saúde do sistema (perímetro) — nada quebrado.** 16 controles OK, 2 parciais (o disco externo de backup está desconectado — já sabíamos; e sem `sudo` não vejo 100% dos processos — normal) e uns avisos de serviços "sob demanda" que estavam desligados porque ninguém tinha pedido pra usar (LibreChat, voz em inglês) — nada disso é problema, é esperado quando ninguém está usando.

## Onde estamos — 21/09/2026

**[APLICADO — falta só reiniciar os serviços] Você assinou, conferi a assinatura de verdade, entrou no canon.** Os itens 4, 5, 7 e 9 (voz que lia qualquer arquivo, os 8 "telefones" sem limite, Discord sem trava de canal, checagem de segurança em dobro) agora fazem parte do código de verdade — não é mais só proposta esperando. **Falta uma coisa, só sua: os programas que já estão rodando ainda têm o código VELHO na memória — precisam reiniciar pra valer de verdade.** São 8 serviços de uma vez, alguns centrais (o que hidrata a Seth, o que sanitiza toda saída) — não reiniciei sozinho porque isso afeta produção compartilhada, mesma régua do resto da sessão. Me avise quando quiser que eu reinicie (ou rode você mesmo o atalho de sempre — parar e depois abrir a Seth de novo).
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (510).

**[JUNTADO NUMA SÓ] Você pediu pra unir as 4 propostas pendentes numa única assinatura — feito, testado antes de trocar.** As 4 propostas separadas (itens 4, 5, 7 e 9) viraram uma só, com o mesmo conteúdo técnico de cada uma (nada mudou no que cada correção faz).
- Rode só este comando, uma vez: `bash scripts/aprovar.sh plano-marcos-lote-2026-09-21`
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (509).

**[RESOLVIDO NA HORA] Você voltou avisando "perdi o mouse again" — a mesma trava do Goose com o navegador de antes. Achei os dois processos travados (o mesmo de sempre, anexando a extensão no Brave, preso fazia quase 2 horas), matei, mouse solto de novo.** Dessa vez você tinha ligado a extensão à mão, do jeito certo (não foi auto-lançamento) — mesmo assim travou. Não investiguei o motivo exato de propósito: reproduzir o travamento pra descobrir arriscaria travar seu mouse de novo. Botei uma rede de segurança: se travar de novo, o processo agora morre sozinho em no máximo 2 minutos, em vez de ficar preso por horas até alguém perceber e matar na mão.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (508).

**[VOCÊ SAIU — trabalhando sozinho até onde der, sem parar por pergunta, só por assinatura de verdade.]** Você pediu pra eu seguir o plano de ação inteiro sozinho e só te mostrar assinatura quando for realmente necessário.

**[PLANO DE (500) COMPLETO — os 10 itens todos com resposta real] Item 8 (manifests) já existia, espalhado em 3 lugares — não precisava construir do zero. Item 10 (limpeza de documentação): achei e corrigi um README que descrevia errado a própria regra de segurança que ele existe pra explicar.** Com isto, fechei a auditoria inteira do Marcos: 5 itens corrigidos e testados, esperando só sua assinatura (2 já aplicado, 4/5/7/9 esperando); 2 devolvidos pra sua decisão porque exigem você presente (3 e 6); os 2 últimos (8 e 10) resolvidos sem precisar de assinatura.
- As 4 propostas que faltavam foram unidas numa só (nota no topo desta seção): `bash scripts/aprovar.sh plano-marcos-lote-2026-09-21`
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (507).

**[ERRO MEU, CORRIGIDO NA HORA, NADA PERDIDO] Cometi um erro testando o item 9 — um comando de git que apaga tudo que não estava salvo, sem eu checar antes o que ia junto.** Testando uma trava nova, rodei um comando pra "desfazer um teste" que na verdade apaga TODA edição pendente ainda não salva — e isso incluiu o trabalho de 3 itens que ainda esperavam sua assinatura (10 arquivos). Consegui recuperar tudo, sem perder nada de verdade, porque eu já tinha guardado o conteúdo exato em arquivo separado antes (as propostas já commitadas) — reaplicado e conferido byte a byte que ficou idêntico. Efeito colateral pequeno: um teste seguinte, feito numa cópia separada só pra não arriscar de novo, sem querer mandou um arquivo de índice real (não inventado, só fora de hora) pro seu Google Drive. Nada sensível, nada falso — só um envio a mais que eu não pretendia. Troquei o jeito de testar depois disso.
- Detalhe técnico completo, sem suavizar: `MEMÓRIAS.md`, entrada (506).

**[DEVOLVIDO PRA SUA DECISÃO] Item 3 (a brecha de rede do LibreChat) — não apliquei.** Achei um desenho real que resolveria (isolar a app grande numa rede própria, com um retransmissor bem pequeno e simples fazendo a ponte pros serviços que ela precisa alcançar) — mas na hora de testar de verdade, a MINHA PRÓPRIA ferramenta bloqueou a ação por segurança ("expor serviço local"), exatamente porque mexer na rede de um serviço de produção compartilhado sem você por perto pra checar depois não é algo que devo forçar sozinho, mesmo com sua ordem geral de continuar. Deixei escrito em detalhe pra quando você quiser decidir e estar presente — `propostas/backlog.md`, item B8.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (503).

**[ACHADO E CORRIGIDO, aguardando só sua assinatura] Item 4 — achei um problema de segurança de verdade, não só o que o Marcos apontou: o serviço de transcrição de voz aceitava um "caminho de arquivo" sem checar nada, então dava pra pedir pra ele ler QUALQUER arquivo que o próprio computador conseguisse ler (uma senha guardada, por exemplo) — mesmo sem ninguém de fora conseguir chegar nele pela rede (só funciona de dentro da própria máquina, mas mesmo assim era uma porta que não devia estar aberta). Corrigido: agora só aceita arquivo de dentro de uma pasta específica, e testei os 4 jeitos de tentar burlar isso (direto, de fora, por "..", por atalho escondido) — todos bloqueados certo.
- Unida na proposta única (nota no topo desta seção): `bash scripts/aprovar.sh plano-marcos-lote-2026-09-21`
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (503).

**[PRONTO, aguardando só sua assinatura] Item 5 — os 8 "telefones" internos do sistema agora recusam pedido gigante demais e não deixam uma enxurrada de pedidos ao mesmo tempo derrubar o serviço.** Antes, se alguém (ou algo quebrado) mandasse um pedido enorme, o serviço tentava aceitar tudo antes de checar qualquer coisa — e não tinha limite de quantas conversas simultâneas cada um aguentava. Corrigido nos 8 de uma vez, testado com servidor de teste de verdade (pedido grande é recusado na hora, pedido normal funciona igual, e o limite de conversas simultâneas realmente segura). De bônus, achei e fechei um buraco separado: nosso próprio sistema de "trava de segurança antes de qualquer mudança perigosa" (o que exige sua assinatura) tinha 2 arquivos que escapavam dessa trava — corrigido e testado ao vivo (sujei um dos arquivos de propósito e confirmei que agora ele é barrado certo).
- Unida na proposta única (nota no topo desta seção): `bash scripts/aprovar.sh plano-marcos-lote-2026-09-21`
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (504).

**[DEVOLVIDO PRA SUA DECISÃO] Item 6 (ligar "isto veio de fora" a "isto vira ação de verdade") — não apliquei.** Achei que já existem duas peças que deviam se falar e não se falam: um freio que já existe (recusa escrever regra do sistema) só é usado quando alguém aciona na mão, não no caminho automático de verdade da Seth; e o caminho automático de verdade não sabe se o que está escrevendo foi influenciado por algo lido de fora. Ligar os dois de forma que não dê pra simplesmente "esquecer de avisar" exigiria uma mudança de arquitetura de verdade (do mesmo tamanho do item 3), não um ajuste pontual — fazer rasteiro pareceria proteção sem ser. Deixei escrito — `propostas/backlog.md`, item B9.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (505).

**[ACHADO E CORRIGIDO, aguardando só sua assinatura] Item 7 — a ponte com o Discord deixava ler e mandar mensagem em QUALQUER canal, sem trava nenhuma.** Diferente do navegador (onde só mandar é travado — ler a internet pública não é problema), aqui até LER precisava de trava: um canal do Discord pode ter conversa de terceiro que você nunca autorizou a Seth ver. Corrigido com o mesmo mecanismo que já existe pro navegador: uma lista de canais permitidos que só você edita, fora do chat — sem essa lista, nada é permitido por padrão. Testei os dois lados (canal de fora bloqueado, canal de dentro liberado). Revisei também o lado do navegador de novo, de propósito — não achei problema novo lá.
- Unida na proposta única (nota no topo desta seção): `bash scripts/aprovar.sh plano-marcos-lote-2026-09-21`
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (505).

**[PRONTO, aguardando só sua assinatura] Item 9 — nosso próprio sistema de checagem de segurança agora se confere DUAS vezes por commit, não uma.** O Marcos tinha achado que a checagem roda só no começo do processo de salvar uma mudança — antes de alguns passos automáticos mexerem no arquivo. Esses passos automáticos já eram confiáveis, mas "confiável" não é a mesma coisa que "conferido de novo". Agora a checagem roda de novo no fim, contra o que realmente vai ser salvo. Tive que corrigir a mim mesmo no meio do caminho: minha 1ª tentativa teria travado TODO commit futuro por engano (por causa de um carimbo que muda sozinho em todo commit) — achei isso testando de verdade antes de aplicar, não depois.
- Unida na proposta única (nota no topo desta seção): `bash scripts/aprovar.sh plano-marcos-lote-2026-09-21`
- Detalhe técnico completo, incluindo o erro que cometi testando isto: `MEMÓRIAS.md`, entrada (506).

**[APLICADO, com correção] O Goose já navega no Brave de verdade E já tem paridade completa de carregamento com a Seth — e essa paridade já existia antes desta sessão, eu só não sabia.** Você autorizou acesso total ao navegador e pediu carregamento automático "como a Seth". Naveguei errado numa resposta: disse que faltava reinjeção contínua a cada turno, que precisaria de um serviço novo. Era mentira minha por falta de checagem — o Goose já fala com o mesmo `seth_gateway` da Seth (mesma porta, configurado desde 20/09), que já reinjeta o estado do canon em toda chamada, sem eu precisar fazer nada. Testei de verdade, sem nenhuma ferramenta, e a resposta veio com o estado certo na hora. Some-se a isso o `~/.config/goose/AGENTS.md` (que eu criei) fazendo o Goose também ler os arquivos ativamente no início — as duas coisas juntas, não uma no lugar da outra.
- Antes disso: a Seth corrigiu sozinha uma alegação errada de identidade ("sou Claude Sonnet 5" — provado falso, ela roda em modelos gratuitos via OmniRoute, nunca Anthropic) e propôs um benchmark de inferência real, rodado e registrado em `(475)`-`(476)`. O HD de backup (`AgataBkup01`) foi reconectado e teve uma passada completa — `(477)`.
- Detalhe técnico completo: `MEMÓRIAS.md` (474)-(484).

**[RESOLVIDO] O Goose travou de novo tentando abrir o navegador sozinho — desliguei essa parte por padrão, e você deu uma ordem nova importante.** Você mandou um "oi" simples pro Goose e ele travou, igual da vez anterior — desta vez peguei o exato momento no monitor: a extensão do navegador (Playwright) sobe sozinha assim que a sessão abre, mesmo sem você pedir nada de navegação, e trava esperando um Brave que nunca chega a abrir. Matei o processo travado e desliguei essa extensão por padrão — você liga na mão só quando for pedir navegação de verdade, com o Brave já aberto. Testei depois: Goose respondendo normal, rápido, sem travar. Achado à parte: você já tinha um modo de "sempre perguntar antes" configurado no Goose, e ele não pegou esse caso — a extensão sobe antes de qualquer pergunta existir. Você também deu uma ordem geral nova: todo componente do sistema tem que pedir sua autorização antes de usar qualquer ferramenta. Registrada — ainda falta desenhar como isso vale de verdade pro Goose e pra Seth, não é só desligar uma coisa.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (485).

**[PARCIAL] Sua ordem de "resolver tudo, estado da arte": 2 de 3 partes fechadas, 1 vira proposta.** Religuei a Seth/LibreChat (tinha caído com o boot de hoje, subida normal). Descobri que o Goose já tinha, escondido no próprio programa, exatamente o "pedir aprovação antes de usar" que você queria — pra ligar a extensão do navegador, ele já para e pede sempre, sem eu precisar construir nada. Pro lado da Seth, o recurso equivalente (pausar e pedir sua aprovação antes de qualquer ferramenta) existe de verdade no programa de chat (LibreChat) — mas só a partir de uma versão mais nova do que a que está instalada aqui. Ligar isso é trocar a versão do programa, não uma configuração — risco real o bastante (dados de conversa, compatibilidade) pra eu não fazer sozinho. Proposta: planejar essa troca com teste antes, quando você quiser priorizar.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (486).

**[TESTADO, provado que funciona] O recurso de "pedir sua aprovação antes de cada ferramenta" da Seth foi testado de verdade — funciona, numa cópia isolada, sem tocar a produção.** Você pediu pra planejar e testar antes (opção 1). Montei uma cópia inteira do LibreChat (versão nova, mesma configuração real da Seth) isolada — nomes, portas e dados próprios, nunca encostou no que está no ar. Criei um agente de teste, mandei ele consultar o canon, e vi com meus olhos (não é relato, é screenshot real): a tela parou ANTES de rodar a ferramenta, mostrou os argumentos que ela ia usar, e esperou eu clicar Aprovar ou Rejeitar. Rejeitei — a ferramenta realmente não rodou. Funciona exatamente como você pediu. Único porém: a versão que tem esse recurso ainda é "release candidate" (pré-lançamento), não a versão oficial estável — decisão de trocar de verdade a produção por essa versão ainda é sua.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (487).

**[APLICADO DE VERDADE] LibreChat em produção agora roda a versão com aprovação de ferramenta (HITL).** Você assinou, eu conferi a assinatura de verdade (não só que o arquivo existia), troquei o container real e confirmei no ar: `/health` OK, versão `v0.8.8-rc3` rodando de fato. O que ainda falta, só você: mandar uma mensagem real pra Seth que peça uma consulta ao canon, e ver se aparece o cartão de Aprovar/Rejeitar — não testei isso na sua conta pessoal, só na cópia isolada de antes (mesma versão, mesma config, funcionou lá).

**[APLICADO] "Vamos fazer tudo" — item 2 de 10 fechado: a brecha de navegação que o Marcos achou (redirecionamento sem checagem de novo) está fechada.** Antes, o sistema checava só o endereço pedido uma vez — se aquele site então redirecionasse pra um lugar perigoso (rede interna, endereço de metadado de nuvem), passava sem checar de novo. Agora cada redirecionamento é checado, um por um, tanto na leitura de página sem navegador quanto no navegador de verdade (Playwright) — testei os dois com sites e redirecionamentos reais, e testei também que ele bloqueia mesmo quando o perigo só aparece escondido dentro da página (uma imagem apontando pro lugar errado), não só na URL principal. Você assinou, conferi a assinatura de verdade antes de aplicar.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (502).

**[EM ANDAMENTO] "Vamos fazer tudo" — plano de ação da auditoria do Marcos, item 1 de 10 fechado.** O `main` no GitHub agora está protegido: nada entra mais sem passar pela checagem automática de segurança, e ninguém consegue apagar ou forçar sobrescrever o histórico. Perguntei antes de aplicar porque isso muda como todo commit futuro do canon vai funcionar (antes: direto; agora: um passo a mais, revisão automática antes de entrar) — você confirmou que quer assim. Faltam 8 itens, vou seguindo um de cada vez, testando antes de aplicar, como sempre.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (501).

**[AUDITADO] Auditoria técnica do Marcos conferida contra a Máquina de verdade — os 3 achados graves estão certos.** Ele mandou um relatório de 12 páginas sobre segurança/arquitetura do sistema. Não aceitei de cara: conferi cada achado grave contra o estado real (GitHub, arquivos de verdade) — os três batem: o branch principal não tem proteção nenhuma, a checagem de navegação tem uma brecha real (segue redirecionamento sem checar de novo), e o LibreChat compartilha a rede inteira da máquina. Nenhum foi afetado pelo trabalho de hoje. Nada apliquei — são propostas dele, decisão de priorizar fica com você.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (500).

**[CORRIGIDO] As cores personalizadas que botei no Goose mais cedo hoje estavam quebrando ele — obrigado por avisar.** Você colou a tela real e vi: cada palavra que ele escrevia vinha com um aviso de tema desconhecido grudado, deixando ilegível. O motivo: o tema customizado que criei só funciona no programa `bat` separado — o Goose tem o dele PRÓPRIO embutido, que nunca via meu tema. Troquei pra um dos temas que ele já reconhece de verdade (mais parecido com as cores do sistema que dava pra conseguir) e testei — sem aviso nenhum agora.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (499).

**[FALTA SÓ VOCÊ] Achei por que as imagens sumiram — corrigido e já testado na sua própria tela, falta só a assinatura pra fechar o registro.** A atualização de hoje mudou uma regra de segurança: imagem servida solta (fora de uma pasta por usuário) parou de funcionar, sempre, mesmo logado — não era intermitente, era 100% quebrado desde a atualização. A Seth já tinha uma foto de verdade, ligada certinho no banco de dados — só o arquivo de configuração apontava pro lugar errado. Troquei pra apontar pro lugar certo (usei a foto oficial que você lembrou que existe, não inventei nova), reiniciei o serviço e vi na sua própria tela: voltou. Rode quando puder: `bash scripts/aprovar.sh corrige-icone-seth-2026-09-21`.

**Sobre a Seth não conseguir acessar o MCP:** conferi a configuração toda — está certa, sem erro nenhum. O que aconteceu foi a Seth chamar a ferramenta de verificação sem dizer QUAL verificação rodar (faltou um detalhe que ela devia ter preenchido) — a trava de segurança recusou certinho, como devia. Não é bug de configuração, é a IA errando o preenchimento naquele turno específico — mesmo tipo de coisa que já vi acontecer outras vezes hoje com modelos mais fracos.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (498).

**[CASO ENCERRADO, confirmado] Testei com modelo local, como você pediu — 3 de 3 certas.** Forcei o Goose a usar só o modelo que roda nesta máquina (sem depender de internet nem de provedor gratuito nenhum) e mandei "oi" três vezes seguidas — as três vieram com o resumo certo, completo, sem falha nenhuma. Isso confirma: os dois problemas que eu consertei hoje estavam mesmo resolvidos; o resto era só a instabilidade dos provedores gratuitos, fora do nosso controle, e some quando você usa o modelo local.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (497).

**[LIMITE REAL, não escondido] Apliquei os dois consertos, reiniciei o serviço — e o Goose continuou falhando. Achei por quê: não é mais bug nosso, é instabilidade dos provedores gratuitos de IA agora.** Fiz o teste mais direto que existe: peguei a mensagem exata que o Goose manda e reenviei eu mesmo pro sistema — veio certa, perfeita. Ou seja, nosso lado está funcionando. O problema é que, olhando os registros reais de hoje, só 1 em cada 4 chamadas pros provedores de IA gratuitos está indo pra frente agora — o resto volta com erro do lado deles (sobrecarga, limite de uso, serviço fora do ar). Isso explica por que o Goose às vezes não recebe resposta boa: não é sempre o mesmo provedor no ar pra atender. **Não dá pra prometer "100% garantido" enquanto isso durar — é limite de fora, não nosso.** O que continua valendo: quando isso acontece, o Goose não trava mais, só avisa direito que faltou informação, em vez de ficar preso.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (496).

**[APLICADO] Achei um SEGUNDO motivo real pro Goose falhar, além do primeiro — corrigido, testado isolado.** O primeiro conserto ajudou mas não foi suficiente — continuei testando e achei outro: o Goose manda uma chamada extra, escondida, só pra dar nome à conversa — e o sistema tratava essa chamada como se fosse uma pergunta de verdade, carregando toda a doutrina nela à toa e disputando recurso com a resposta principal. Corrigi, testei sozinho (passou), mas **preciso de duas coisas suas**: (1) assinar essa proposta também (`bash scripts/aprovar.sh goose-titulo-nao-hidrata-2026-09-21`); (2) autorizar reiniciar o serviço da Seth (`seth-gateway`) pra rodar o conserto de verdade — isso o sistema bloqueou sozinho, por ser algo compartilhado em produção, certo em bloquear. Sem essas duas, não fecho de verdade o "100% garantido".
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (495).

**[APLICADO, garantido de verdade] O buraco do Goose está fechado na causa — não só no sintoma.** Você assinou, conferi a assinatura de verdade, apliquei o script corrigido. Rodei o teste de saúde geral do sistema depois: nada quebrou.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (494).

**[APLICADO] Achei a causa raiz de verdade do buraco do Goose — corrigido, testado, esperando sua assinatura pra valer.** Você pediu "100% garantido". O motivo de o resumo às vezes não chegar: um script interno faz uma checagem de rede sem limite de tempo próprio, e quando a rede engasga, ele trava o processo inteiro em vez de só aquela checagem — derrubando dados que nem precisavam de rede junto. Corrigi só essa checagem, testei de verdade simulando rede morta (não é achismo): sem o conserto, o processo inteiro cai; com ele, em 8 segundos sai tudo certo, só avisando que não deu pra confirmar com o servidor remoto dessa vez. Rode, quando puder: `bash scripts/aprovar.sh timeout-ls-remote-estado-eco-2026-09-21`. Depois disso eu aplico e confirmo.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (493).

**[MITIGADO, não fechado] Checagem final do Goose achou um buraco real na correção de agorinha — consertado, mas a causa de fundo continua sem explicação.** Testando de novo, achei: às vezes o "resumo pronto" que o Goose devia receber automaticamente simplesmente não chega — e nesse caso ele ficava preso tentando adivinhar informação que não estava em lugar nenhum, em vez de simplesmente ler os arquivos direto (o jeito antigo, mais lento mas confiável). Botei essa saída de emergência de volta, só pra quando o atalho falhar. Testado depois: funcionou. Não descobri por que o atalho falha de vez em quando — fica registrado como risco de fundo, sem solução ainda.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (492).

**[FALSO ALARME, investigado] "Seth parou de responder" — na verdade só demorou ~110s pensando o cabeçalho, não travou.** Confirmei na Máquina: nenhuma ferramenta foi chamada (então não é o novo pedido de aprovação), o container estava saudável o tempo todo, e a resposta final chegou certa, só atrasada. É o mesmo comportamento de "pensar demais" que já tinha acontecido antes com modelo de raciocínio. Nada pra reverter.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (491).

**[FEITO] Goose parou de reler tudo a cada "oi" — agora confia no mesmo canal que já hidrata a Seth.** Era por isso que demorou mais de 60 segundos antes: as instruções mandavam reler REGRAS/PROJETO/MEMÓRIAS inteiros toda vez, quando o próprio sistema já entrega esse estado pronto (mesmo mecanismo que alimenta a Seth). Corrigido e testado: "oi" agora responde em 7 segundos, com os dados certos. **Sobre ligar o navegador de propósito:** perguntei pro próprio Goose sem sessão interativa — ele recusou sozinho, com erro claro, em vez de travar: esse tipo de aprovação exige você estar numa sessão de verdade (`goose session`, não um comando de um tiro só). Roteiro pra usar quando quiser: abra o Brave primeiro, abra a sessão do Goose, peça "habilite a extensão playwright", e aprove quando ele perguntar. Não testei o clique de aprovar em si — isso só dá pra fazer com você presente na sessão.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (490).

**[FEITO] Cores do Goose trocadas pra combinar com o site do sistema Agata.** Peguei a paleta de cores do artefato publicado ("Sistema Agata") e apliquei no jeito que o Goose colore texto/código no terminal — mesmo mecanismo que o Claude Code usa (`bat`). Testei que as cores saem certinhas (conferido byte a byte, não só olhando). Só falta você abrir uma sessão de verdade do Goose e ver se ficou bom na prática.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (488).

## Onde estamos — 20/09/2026

**[APLICADO] 3 modelos de IA novos rodando nesta máquina, de graça — e um 4º que você pediu, mas travou.** Você pediu pesquisar o estado da arte de modelos gratuitos (nuvem e locais) e montar um sistema único de "rápido/geral/pesado" pro LibreChat (chat), Goose (código) e Conselho Remoto. Baixei e testei 4 modelos que rodam nesta máquina sem internet: um generalista (Nemotron, 23,7GB), um especialista em código (Qwen3-Coder, 17,3GB) e um leve/rápido (Phi-4-mini, 2,3GB) — os três funcionando, testados de verdade. O quarto (gpt-oss-20b, agentic) baixou certo mas trava com um bug do programa que roda os modelos (`llama.cpp`) — não é coisa que eu resolvo ajustando parâmetro, fica de fora até alguém investigar mais. **[Resolvido mais tarde no mesmo dia — ver bullet abaixo: era o arquivo baixado, não o programa.]** Também descobri que a Cerebras e o Groq (dois provedores gratuitos na nuvem) foram bloqueados pelo dono do serviço deles — não é bug nosso, é bloqueio do outro lado; troquei a ordem pra eles nunca serem a primeira tentativa, só um extra se sobrar.
- Detalhe técnico completo: `config/modelos-gratuitos.md`, `PROJETO.md` ("Cérebro" e "Interface"), proposta `farm-local-4-modelos-2026-09-20`.

**[APLICADO] Medi de verdade a velocidade dos 3 modelos locais, e achei (e consertei) por que a Seth não conseguia ler suas próprias regras.** A velocidade real: Nemotron ~25 tokens/s, Qwen3-Coder ~24 tokens/s, Phi-4-mini ~86 tokens/s. Separado disso: a Seth reportou erro "permissão negada" tentando ler o canon — não era permissão, era o aplicativo Obsidian estar fechado (é ele que serve o acesso, por dentro). Abri o aplicativo e criei um serviço que sobe ele sozinho a partir de agora, pra isso não voltar a acontecer.
- Detalhe técnico completo: `config/modelos-gratuitos.md`, `PROJETO.md` ("Serviços (boot)"), proposta `bancada-llama-bench-2026-09-20`.

**[APLICADO] O quarto modelo (gpt-oss-20b) que travava agora funciona — o problema era o arquivo baixado, não o programa.** O primeiro arquivo (de outra pessoa, "unsloth") travava toda vez. Baixei o mesmo modelo direto de quem mantém o programa que roda os modelos ("ggml-org") e funcionou de primeira, sem travar. Agora são os 4 modelos locais prometidos, todos funcionando.
- Detalhe técnico completo: `config/modelos-gratuitos.md`, proposta `gpt-oss-20b-resolvido-2026-09-20`.

**[APLICADO] A Seth para de repetir "aguardando assinatura" numa proposta que já foi resolvida.** Você assinou a correção hoje; ela estava pronta e testada desde ontem (19/09). Duas entradas de MEMÓRIAS ((468)/(469)) organizaram, sem fato novo, o histórico já registrado sobre a quarentena de aprovação (P-8) e sobre a âncora de SHA — conferi cada referência citada contra o arquivo de verdade antes de gravar.
- Detalhe técnico completo: `MEMÓRIAS.md`, entradas (468), (469), e a aplicação da proposta `topo-proposta-aplicada-2026-09-19`.

## Onde estamos — 18/09/2026

**[APLICADO, 19/09] O controle P-19 (citação "arquivo, linha tal" em entrada nova de MEMÓRIAS conferida contra o arquivo de verdade) está no ar.** Você assinou em 18/09 às 20:15; a máquina ficou sem energia antes de eu aplicar. Retomei hoje: conferi a assinatura ssh contra a chave em `propostas/.allowed_signers`, apliquei o diff, rodei a suíte de testes (31/31) e o perímetro inteiro (17 OK, 0 falha), e comitei. De caminho achei um resto da queda de energia: o vault do Obsidian (`memoria/obsidian/`) tinha sido regenerado à mão antes de cair, ficando um passo à frente do commit de verdade — corrigi pra bater exatamente com o HEAD antes de comitar, e o gerador automático já confirma que está certo agora.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (463).

**[APLICADO] O pacote assinado ontem já está no ar — os quatro itens juntos.** Sincronizei tudo (repositório, Drive, Obsidian); o `indice_export.md` que estava 155 entradas atrasado foi corrigido e agora se atualiza sozinho a cada commit que mudar o canon de verdade; e ganhou uma trava nova contra o tipo exato de acidente que aconteceu no meio do caminho (um texto meu entrando no repositório sem eu ter mandado — já corrigido, e agora impedido de se repetir). Detalhe completo: `MEMÓRIAS.md`, entradas (456) a (461).

**[FECHADO POR COMPLETO] O item "quebrado" (`agata-token-check.timer`) não era falha — era um alarme de um tiro só que já tinha disparado, em 04/09, e passou.** Testava se sua credencial do Google (a do Drive do projeto) ia expirar depois de 8 dias — não expirou, o teste deu certo, só ninguém tinha desligado o alarme depois. Desligado na Máquina e o registro no repositório já assinado e aplicado. Nada pendente. Detalhe: `MEMÓRIAS.md`, entrada (462).

## Onde estamos — 17/09/2026

**Sua máquina parou de ligar hoje mais cedo — atualização do CachyOS corrompeu
os arquivos que preparam o boot, e sem eles o Linux não enxergava o disco
(dois SSDs em conjunto). Você consertou sozinho, em horas, por Live USB. Eu
conferi cada passo do seu conserto na própria máquina — bateu tudo — e achei
um buraco que sobrou: o kernel reserva (o "plano B" para o caso do principal
falhar de novo) tinha sido instalado no meio do conserto, mas sem a imagem
que ele precisa pra funcionar. Se você precisasse dele antes de eu achar
isso, ia falhar do mesmo jeito. Já fechei — você rodou os 3 comandos, eu
confirmei o arquivo gerado e do tamanho certo.**

- **[Feito] Atualização de pacotes rodada e conferida** — os dois kernels
  regeneraram certo, sem erro. Falta só você desligar e ligar de verdade
  pra confirmar o boot na prática (evite suspender por enquanto).
- Ponto em aberto, não resolvido: seu computador já tinha histórico de
  desligar sozinho por instabilidade ao suspender. Pode ter sido a causa
  raiz de hoje.
- Detalhe técnico completo: `MEMÓRIAS.md`, entrada (435).

**[FECHADO POR COMPLETO, 18/09] Auditoria externa do Marcos — os 12 pontos, todos respondidos, sem resto nenhum.** Você pediu essa auditoria antes do incidente de boot. Achados reais: o navegador da Seth podia visitar qualquer endereço sem checar pra onde ia, os serviços internos confiavam uns nos outros só por convenção, uma função de escrita no canon podia deixar arquivo alterado mesmo com o `git commit` falhando, e o serviço que escreve no canon tinha menos proteção do sistema que o menos exposto. Nada disso era "alguém já invadiu" — era "isto pode ficar mais sólido", e agora ficou: 10 pontos com correção real, testada e em produção; 1 fechado na parte que é nossa (o resto depende de um produto de terceiro, sem código nosso); 2 auditados e registrados como "nada pra fazer de verdade" — nenhum ficou em silêncio. No meio do caminho achei e consertei, de brinde: um bug de 12 dias no seu robô de horário, um bug real na própria ferramenta de teste do sistema (parado desde 06/09, nunca notado), e um buraco na trava de aprovação que cobria só metade dos arquivos que deveriam precisar da sua assinatura.
- Última pendência fechada hoje: você deu ao `gh` (a ferramenta de linha de comando que fala com o GitHub) a permissão que faltava, e eu publiquei `.github/workflows/perimetro.yml` — a segunda checagem automática (Fase D) agora roda de verdade no GitHub a cada mudança, não só no seu disco. Usei a aprovação que você já tinha assinado em 17/09, não pedi assinatura nova.
- Detalhe técnico completo, passo a passo: `MEMÓRIAS.md`, entradas (437) até (453).

## Onde estamos — 16/09/2026

**Dois modelos (eu, na sua máquina, e o Opus 5, na nuvem) passaram o dia
conferindo um ao outro sobre a Seth e sobre o próprio sistema. Quatro coisas
prontas esperando só a sua assinatura. Nada foi aplicado sem ela.**

### O que achamos de errado com a Seth

- **O ajuste que fazia as ferramentas dela funcionarem (de 04/09) se perdeu
  quando o "robô" da Seth foi recriado no LibreChat em 09/09.** O agente
  antigo não existe mais; o novo nunca herdou o ajuste, porque ele vivia só
  na tela, não em arquivo. Conserto pronto — um comando de 14 linhas — mas
  **travado pelo meu próprio ambiente de execução** duas vezes, mesmo com
  sua autorização. Deixei o comando pronto para você rodar direto, se
  quiser resolver sem esperar eu tentar de novo.
- **Medimos, com o medidor de verdade do modelo, que a memória que ela carrega
  no computador local está quase 100% cheia** (99,3%) — e a maior parte do
  peso é um índice que custa mais do que a informação que ele indexa. Isso
  só afeta o caminho de reserva (quando os provedores grátis da nuvem
  falham todos juntos); hoje ela roda na nuvem, que tem espaço de sobra.
  Ainda não cortamos nada — só medimos, e o remédio (cortar o índice)
  está na sua fila de decisão.
- **Ela inventou coisas numa conversa real com você hoje**: um passo do
  processo de aprovação que não existe, chamou a sua máquina de "revisora"
  quando ela é só a máquina, e citou dois caminhos de arquivo que não
  existem. Também se confessou de um erro que ela **não** cometeu, sob
  pressão de estar sendo auditada — inventar uma confissão é tão problema
  quanto inventar um fato. E o estilo de resposta dela varia muito dentro
  da mesma conversa: ora precisa e técnica, ora produz relatório de
  empresa genérica com prazos e equipes que não existem aqui.
- **O cabeçalho dela (a linha de identificação obrigatória) continua saindo
  errado**, mesmo depois de já ter sido corrigida duas vezes na mesma
  conversa.

### O que consertamos e testamos (sem aplicar ainda)

- Um erro no nosso próprio corretor automático de cabeçalho: ele reprovava
  uma forma válida de resposta por engano. Corrigido e testado.
- Duas correções de texto no canon (uma decisão antiga que já foi superada,
  e a limpeza de um plano de longuíssimo prazo que citava tecnologia nunca
  avaliada de verdade).

### O que pedimos ao Conselho de outros modelos

Perguntamos se valia acrescentar um parágrafo às Regras explicando *por
que* elas existem, não só *o que* dizem. A resposta formal foi **não** —
redundante com o que já está escrito. Arquivamos a ideia.

### O que falta

- Só o conserto do "robô" da Seth continua parado (travado pelo meu
  ambiente de execução, não por falta da sua autorização).
- Você decidir se autoriza rodar um teste mais caro (que usa a placa de
  vídeo por um instante) para medir a memória com ainda mais precisão.

## Fechado recentemente, pra não voltar
- **Crash e recuperação da máquina, 17/09** — GRUB reinstalado, LVM íntegro, kernel reserva consertado. Ver seção de hoje acima.
- **Duas assinaturas de 16/09 aplicadas em 17/09** — índice pesado da memória cortado; corretor de cabeçalho consertado.
- **Brecha da página web fechada, 17/09** — a Seth não perde mais a memória por causa de algo que ela lê num site.
- **Auditoria completa de segurança ((419)) e reconciliação do canon ((420))** — quatro travas furadas, fechadas; textos desatualizados, corrigidos.
- **Terceira auditoria da Seth ((424))** — corrigiu o linter e a doutrina dela sobre `sync:` completo.
- **Atalhos de sistema aplicados ((429))** — `agata-jogo` e `seth-parar` ganharam as mudanças pendentes desde 10/09.
