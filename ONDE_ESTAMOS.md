# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 15/09/2026: `extras/arquivo/onde-estamos-ate-2026-09-15.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md` (entrada (440)).

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

**Auditoria externa do Marcos, pedida por você antes do incidente — conferi cada achado checável na própria máquina.** Ele estava certo nos sete pontos que dão pra checar sem rodar nada ao vivo: o navegador da Seth pode visitar qualquer endereço sem checar pra onde vai (inclusive endereços internos do próprio sistema), o jeito como os serviços conversam entre si depende de convenção, não de trava técnica, uma função de escrita no canon pode deixar arquivo alterado mesmo quando o `git commit` falha, e dois dos serviços mais expostos da Seth têm menos proteção do sistema do que o menos exposto. Nada disso é "alguém já invadiu" — é "isto pode ser mais sólido". Você aprovou um plano de 5 fases pra fechar os 12 pontos do relatório, um `.diff` assinado por vez.

**[Feito] Fase A assinada e aplicada** — fechou 4 dos 12 pontos. Detalhe: `MEMÓRIAS.md`, entradas (438)/(439).

**Fase B, parte 1, pronta e testada de verdade, esperando sua assinatura** — os dois serviços mais expostos da Seth (o que vê todo o tráfego, e o único que escreve no canon) tinham ZERO proteção do sistema operacional; agora têm a mesma que o mais protegido já tinha. Testei cada um dos 10 serviços ao vivo, não só "parece certo no papel": gerei um áudio de verdade, gerei um vetor de embedding de verdade na placa de vídeo, escrevi (e desfiz) uma linha de teste real no diário da Seth. Nada quebrou, nada ficou em estado de erro. Arquivo: `propostas/fase-b-hardening-systemd-2026-09-17.diff`. Detalhe: `MEMÓRIAS.md`, entrada (440).

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
