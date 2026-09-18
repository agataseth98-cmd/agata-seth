# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 15/09/2026: `extras/arquivo/onde-estamos-ate-2026-09-15.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md` (entrada (452)).

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

**[FECHADO] Auditoria externa do Marcos — os 12 pontos, todos respondidos.** Você pediu essa auditoria antes do incidente de boot. Achados reais: o navegador da Seth podia visitar qualquer endereço sem checar pra onde ia, os serviços internos confiavam uns nos outros só por convenção, uma função de escrita no canon podia deixar arquivo alterado mesmo com o `git commit` falhando, e o serviço que escreve no canon tinha menos proteção do sistema que o menos exposto. Nada disso era "alguém já invadiu" — era "isto pode ficar mais sólido", e agora ficou: 9 pontos com correção real, testada e em produção; 1 fechado na parte que é nossa (o resto depende de um produto de terceiro, sem código nosso); 2 auditados e registrados como "nada pra fazer de verdade" — nenhum ficou em silêncio. No meio do caminho achei e consertei, de brinde: um bug de 12 dias no seu robô de horário, um bug real na própria ferramenta de teste do sistema (parado desde 06/09, nunca notado), e um buraco na trava de aprovação que cobria só metade dos arquivos que deveriam precisar da sua assinatura.
- Único resto pendente, fora do meu alcance: criar `.github/workflows/perimetro.yml` direto no site do GitHub (o token de acesso daqui não tem permissão) — conteúdo já pronto, só falta colar. Sem isso a segunda checagem automática (Fase D) fica só no seu disco, não no GitHub.
- Detalhe técnico completo, passo a passo: `MEMÓRIAS.md`, entradas (437) até (452).

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
