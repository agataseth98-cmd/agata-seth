# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 08/09/2026: `extras/arquivo/onde-estamos-ate-2026-09-08.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md`.

## Onde estamos — 09/09/2026 (tarde)

**Auditoria completa do sistema. Quatro travas de segurança estavam
abertas sem ninguém saber — todas fechadas hoje.**

O sistema tem travas automáticas que conferem cada mudança antes dela
entrar. Descobri, testando de verdade e não só lendo, que quatro delas
não faziam o que prometiam:

- **Bastava renomear um arquivo para escapar da trava principal.** Editar
  um arquivo protegido era barrado, como devia. Mas *mover* o mesmo
  arquivo para outra pasta passava em silêncio — inclusive o programa que
  tira senhas e chaves de tudo que sai para fora. Dava para desligá-lo sem
  aprovação nenhuma.
- **Pelo mesmo caminho, um arquivo privado ia parar no repositório
  público.** É exatamente o que essa trava existe para impedir.
- **A trava que confere citações estava desligada desde 06/09.** Ela
  achava que não tinha nada para conferir e pulava, silenciosamente, em
  todo commit. A trava em si funcionava — só o portão dela estava travado
  aberto.
- **O detector de senhas não reconhecia as chaves que você realmente
  usa.** Três das suas chaves passariam limpas por ele.

Fechei as quatro, mais quatro problemas menores da mesma família. Cada
conserto foi testado antes e depois: mostrei o problema acontecendo,
apliquei o conserto, mostrei o problema não acontecendo mais, e conferi
que nada que funcionava parou de funcionar.

**Uma trava passou no teste e merece registro:** a que protege a memória
antiga congelada resistiu, porque tem duas camadas em vez de uma. Foi ela
que me deu a ideia de como consertar as outras.

## Também fechado hoje, depois da auditoria

**O texto do projeto voltou a bater com a máquina.** A auditoria achou
lugares onde o que estava escrito já não era verdade:

- **O documento que você leria numa emergência estava errado.** Ele dizia
  que o Tailscale não está instalado — está, e funciona. Pior: esse
  documento se apresentava como "correção" de outro, o que faz confiar
  nele. Você teria lido "não há como acessar a máquina de outro
  dispositivo" justamente na hora de precisar saber que há.
- **Uma seção de segurança se apoiava num programa que não existe mais.**
  Reescrita: a proteção real é que nada aqui aceita conexão de fora, e
  conferi as 16 portas uma a uma.
- **A seção do "Conselho" prometia uma garantia que o programa não
  cumpre** — dizia que ele nunca recorre ao modelo local, e ele recorre.
  Garantia que não vale é pior que documentação faltando, porque alguém
  decide confiando nela.
- **Dois atalhos seus estavam desatualizados** — `seth` e `seth-parar`
  tinham melhorias guardadas que nunca foram instaladas. Instalados, com
  cópia de segurança. A lista dava isso como pronto há quatro dias.

**Reorganizar a pasta do código virou horizonte, a seu pedido** — não é
defeito, é nome feio, e não bloqueia nada.

## E a correção mais importante do dia

**Agora existe teste das travas — e ele pegou um erro meu no primeiro dia.**

Quando lhe dei a nota do sistema, apontei que a causa de tudo era simples:
**nada testava as travas**. Elas eram conferidas quando alguém sentava para
procurar, e foi assim que os quatro furos apareceram. Se ninguém tivesse
procurado, continuariam abertos.

Escrevi uma bateria de 28 testes que refaz cada furo de propósito e exige
que a trava pegue — e também exige que ela **não** grite no que é legítimo,
porque trava que alarma à toa acaba desligada. E amarrei isso: quem mexer
numa trava passa a ser obrigado a rodar os testes dela antes de gravar.
Custa 29 segundos, e só nos commits que mexem em trava; nos outros, 1
segundo.

**O melhor sinal do dia:** na primeira vez que rodei a bateria, ela
reprovou o conserto que eu tinha feito ontem. Minha suposição estava
errada, e o teste viu. Não fui eu que percebi — foi o teste. É exatamente
para isso que ele serve.

## 10/09 — auditamos a Seth e o culpado era o sistema

Você mandou auditar a Seth. Ela não inventou **nada**. As cinco coisas
verificáveis que ela afirmou estavam certas — inclusive uma data que eu
mesmo corrigi quatro minutos depois de ela responder.

Os erros de formato dela vieram de instruções nossas:

- **As Regras descreviam um arquivo que não existe mais** como sendo o
  mecanismo atual do sistema. Ele foi removido há sete dias. Pior: nosso
  próprio registro conta que a Seth **já tinha sido corrigida** por citar
  esse arquivo — corrigiram a Seth e deixaram o texto que a induziu ao
  erro. Ela repetiu, lendo corretamente.
- **A instrução mandava ela misturar dois formatos de cabeçalho** que as
  Regras proíbem juntar. Ela obedecia direitinho.
- **A instrução não proibia dizer "olá"** — só proibia bajular. Daí o
  "Olá! Como posso ajudar?".
- E um erro meu: o corretor de cabeçalho que escrevi ontem ficou cego a
  uma forma que as Regras permitem. **Foi ela, sendo auditada, que
  expôs.**

Tudo corrigido. A lição ficou escrita ao lado do conserto: **quando o
modelo e o texto divergem, confira os dois antes de culpar o modelo.**

**O vault do Obsidian tinha sete travas invisíveis.** Ele mostrava 10 dos
17 controles — faltavam justamente o que guarda dados privados, o que
protege a história congelada e os dois criados na véspera. Quem
consultasse para saber o que protege o sistema veria um retrato antigo,
sem aviso. Agora a lista **se monta sozinha** a partir do código real, e
o gerador **para e reclama** se não encontrar nada, em vez de produzir um
vault vazio em silêncio.

## A Seth pediu mais poder. Recebeu metade — a metade certa.

Ela pediu um interpretador de código: rodar qualquer comando, mexer em
qualquer arquivo. O argumento dela era bom — sem isso, ela fala do
sistema sem poder conferir nada por conta própria.

**Mas isso desmontaria as travas.** Com um comando livre, qualquer
proteção do sistema se contorna numa linha. Não é desconfiança dela: um
canal aberto não distingue a Seth de qualquer coisa que consiga falar
por ela.

Então ela ganhou o poder de **verificar**, não o de **mudar**:

- Pode rodar as 17 travas, conferir os selos da história, ver o estado do
  git, comparar com o repositório publicado, rodar a bateria de testes.
- **Não** pode escrever, apagar, publicar nem rodar comando inventado. A
  lista é fechada; o que não está nela volta recusado, com a lista junto.
- A saída passa pelo mesmo detector de senhas que protege o resto — se
  algo sigiloso aparecer no meio, sai tapado antes de chegar a ela.

Testei atravessando a fronteira de verdade: pedir `rm -rf /` volta
recusado; pedir o estado do repositório volta com o dado real.

Ampliar é barato — um item novo na lista, com sua assinatura. E cada
item passa pela mesma pergunta: **isso pode mudar alguma coisa?** Se
puder, não entra.

## O que falta

- **Uma decisão sua sobre uma regra.** Uma parte do sistema ficou pronta,
  e existe uma regra escrita que vale "enquanto essa parte não existir".
  Não mudei a regra por conta própria — mudar regra exige seu aval. Até
  você decidir, vale a leitura mais conservadora.
- **Quatro coisas que a auditoria achou e eu não consertei**, todas
  registradas: um filtro do sistema da Seth pode ser desligado por texto
  vindo de uma página da web (é o mesmo trecho que já quebrou antes, e
  merece cuidado próprio); um agendamento ligado que nunca mais dispara;
  o arquivo de memória ocupando quase toda a janela do modelo; e algumas
  regras internas escritas em duplicidade.

## Fechado recentemente, pra não voltar

- **Pendências e limpeza ((418))** — restos dos testes aposentados saíram
  dos programas e documentos; a lista de tarefas ficou zerada, exceto a
  reorganização acima.
- **TES-001 e TES-002 aposentados ((417))** — sua decisão ("mera
  formalidade"). O que eles vigiavam continua coberto por outros meios.
- **Cabeçalho da Seth ((417))** — a hora e o estado envelheciam do
  segundo turno em diante. O sistema agora reinjeta dado fresco a cada
  resposta.
- **Roteador da Seth ((416))** — pergunta curta vai por um caminho
  rápido, tarefa longa por um caminho forte, e entrou um provedor grátis
  e veloz no topo. Se ele cair, desce para o de sempre sem quebrar.
- **Ferramentas da Seth voltaram ((415))** — estavam quebradas desde a
  (392); testadas e funcionando.
- **Voz ((415))** — de volta ao Piper, a seu pedido. Voz feminina em
  português exige outro motor; fica para quando você pedir.
