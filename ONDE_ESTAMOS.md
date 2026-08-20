# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos.

## Onde estamos agora
A limpeza de segurança que estava em aberto terminou.
Uma regra antiga e perigosa foi removida do sistema.
Um teste grande com IA terminou. Deu resultado, mas ninguém escolheu
ainda o que fazer com ele.
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

## Esperando você
- Escolher o que fazer com o resultado do teste grande de IA.
- Revisar e mandar (ou não) o pedido de recursos pro Marcos —
  `memoria/missoes/rlm-3caminhos/PEDIDO_RECURSOS_VM_MARCOS.md`.
- Marcar uma sessão só pra rodar o teste grande com os modelos
  candidatos — leva umas 6 horas de GPU, por isso ficou de fora de
  hoje.
- Confirmar se a conversa entre modelos sobre a edição do
  `config.yaml` foi real, e se quer adotar a regra das três perguntas
  antes de mudança estrutural.

## Rodando agora
Nada rodando.

## Quebrado
Nada quebrado.

## Última atualização
20/08/2026, 19:59.
