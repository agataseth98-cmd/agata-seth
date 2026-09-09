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

## O que falta

- **Reorganizar a pasta do código (a antiga "redesign")** — o nome
  descreve um trabalho que já terminou, não o que o código é hoje. É a
  mudança grande que sobrou; o plano está pronto e o levantamento
  também. **Deixei para depois desta trava de segurança de propósito:**
  são 102 arquivos mudando de lugar de uma vez, e mover arquivo era
  justamente o buraco que acabei de tapar.
- **Dois atalhos no seu computador estão atrás do que está guardado** —
  os comandos `seth` e `seth-parar` receberam melhorias que nunca foram
  instaladas. A lista de tarefas dá esse item como concluído, mas o
  mecanismo que ele descreve nunca chegou a rodar.
- **Uma lista de inconsistências no texto do projeto**, achadas na mesma
  auditoria e ainda não corrigidas: dois documentos se contradizem sobre
  o acesso remoto, uma seção de segurança descreve um programa que não
  existe mais, e o índice do sistema oferece um documento que nunca
  existiu.

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
