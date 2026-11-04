# Adaptar o que varia, recusar o que identifica, declarar o que fez: a saída de áudio do Agata como caso de projeto

Autor da síntese: Claude Sonnet 5.5 (Claude Code). Data: 03/11/2026, 22:48 (medido com `date`). Nota de estudo para o Humano; não é canônica. Níveis de evidência como em `pesquisa-llm-agata.md`: **N1** fonte primária lida, **N3** fonte secundária, **Inferência** minha.

## Resumo

Em 03/11/2026 o Humano estabeleceu como regra, depois de uma leitura em voz alta que saiu pelo alto-falante porque os fones estavam carregando: "essa é a regra a partir de agora, adaptação". Esta nota explica por que a regra é boa engenharia, onde ela deixa de ser, e como o Agata a separa em duas partes: **o que pode variar** (por onde o som sai), em que o sistema se adapta sem perguntar, e **o que identifica** (a voz `pt_BR-agata-last`), em que ele recusa a adaptação. A tese é que adaptação segura exige três coisas: classificar o que é variável e o que é invariante, impor limites de segurança à parte variável, e declarar ao Humano o que foi feito.

## 1. O caso (medido na sessão)

| Hora | Fato | Evidência |
|---|---|---|
| 19:19 | Leitura do t=29 pelos fones TWS (saída padrão Bluetooth) | `date`, `mpv` saída 0 |
| 21:05 | Nenhum fone conectado; só o alto-falante do notebook (150%) e três HDMI | `pactl list sinks short`, `bluetoothctl devices Connected` vazio |
| 21:2x | TWS reconectado a pedido; canais esquerdo e direito já iguais (90%); baixei a 50%; ao final marcava 65% sem ação minha | `pactl get-sink-volume` |
| 22:43 | Leitura do t=37 tocou no alto-falante a 150%, porque o TWS estava fora e o PipeWire voltou a saída padrão | `pactl get-default-sink` e volume lidos depois do comando |
| 22:45 | Humano: a execução foi perfeita; fones carregando; "o sistema se adaptou"; adaptação é a regra | mensagem do Humano |

Duas leituras do mesmo episódio, que a regra precisa separar: o sistema se adaptou à saída (acerto, na avaliação do Humano) e eu não verifiquei o limite de volume antes de falar (falha minha, antes de a regra existir).

## 2. Fundamentação

**Computação autonômica (laço MAPE-K).** Kephart e Chess (IEEE Computer, 2003) propõem sistemas que se gerenciam a partir de objetivos de alto nível; fontes secundárias descrevem o laço Monitorar, Analisar, Planejar e Executar sobre uma base de conhecimento compartilhada, com sensores e atuadores (N3: não li o artigo). O caso se encaixa: monitorar é ler a saída padrão do sistema de som; analisar é conferir se a voz do sistema está disponível; planejar e executar é gerar e tocar o áudio; a base de conhecimento é a regra do Humano.

**Consciência de contexto.** Dey (Personal and Ubiquitous Computing, 2001) define que um sistema é sensível ao contexto se usa contexto para dar informação ou serviço relevante à tarefa do usuário (N3, via resumos). Aqui o contexto é "quais saídas existem agora".

**Princípio da robustez.** A RFC 1122, seção 1.2.2 (N1), diz "Be liberal in what you accept, and conservative in what you send" e pede que o software não quebre diante de um caso não definido. É a base clássica de "tolerar o ambiente".

**A crítica ao excesso de tolerância.** A RFC 9413, "Maintaining Robust Protocols" (Thomson e Schinazi, jun/2023, N1), separa a robustez a defeitos de software, a ataques e ao inesperado. Sobre o terceiro ponto afirma que tolerar entrada inesperada "is no longer considered best practice in all scenarios" (seção 2). Nas seções 2.1 e 4 sustenta que ignorar entrada defeituosa ou ambígua é "almost always the incorrect solution", e que a tolerância gera decaimento do protocolo e efeitos de ecossistema. Propõe a **intolerância virtuosa**: tratar como erro fatal o que a especificação não prevê (seção 5.1). Na seção 6 avisa que esconder variações encobre bugs.

**Degradação graciosa e falha silenciosa.** Textos de prática (N3, blogs e glossários, não revisados por pares) convergem: degradar mantendo o serviço é bom, mas **o fallback silencioso é um antipadrão**; a degradação deve ser planejada, testada, monitorada e visível, e há tensão entre falhar aberto (disponibilidade) e falhar fechado (controle e segurança).

## 3. Análise

1. **Adaptar não é tolerar tudo.** A RFC 9413 critica aceitar entrada **inesperada** de outro agente; o caso do áudio é outra coisa: a saída de áudio **varia legitimamente** (fones carregam, o alto-falante existe). Adaptar-se a isso é robustez no sentido da RFC 1122, sem o dano que a RFC 9413 descreve.
2. **O invariante recebe intolerância virtuosa.** O Agata já aplica isso: `scripts/agata_falar.py` recusa falar se o piper carregou o modelo de reserva (`pt_BR-faber-medium`) e diz "NÃO falei". O som pode sair por qualquer lugar; a voz não pode ser outra. É a mesma divisão da RFC 9413 §5.1 aplicada a um problema de interface.
3. **A parte variável precisa de limites.** Falhar aberto na saída de áudio (tocar onde houver) é seguro se houver um teto de segurança. O episódio das 22:43 mostra o custo da ausência: o alto-falante a 150% é o estado que o Humano escolheu, mas o sistema não tem como saber se é seguro. A regra do Humano resolve isso por decisão (adaptar sem perguntar); o desenho continua devendo uma salvaguarda que não dependa de perguntar.
4. **Adaptação tem de ser declarada.** As fontes de prática e a seção 6 da RFC 9413 convergem em que adaptação silenciosa esconde defeito. **Lacuna concreta do Agata (medida):** o `agata_falar.py` hoje não diz por qual saída falou nem a que volume. A regra "adaptar" está cumprida; a regra "declarar" não.

**Tese:** adaptar o que varia, recusar o que identifica, declarar o que fez. Os dois primeiros itens já estão no sistema; o terceiro não.

## 4. Hipóteses testáveis

- **H1 (declaração):** se o script diz a saída e o volume depois de falar, o Humano deixa de ser surpreendido por fala no lugar errado. Medida: ocorrências de surpresa relatadas por semana (hoje: 1 em 2 leituras sem declaração).
- **H2 (telemetria do fallback):** registrar quantas leituras caíram em cada saída mostra se o alto-falante vira o caminho normal sem ninguém notar (o sinal que as fontes de prática recomendam).
- **H3 (teto):** um aviso quando o volume da saída passa de 100% captura o caso das 22:43 sem voltar a perguntar antes de falar.

## 5. Limites

Um caso, um usuário, avaliação subjetiva ("perfeita"). Kephart e Chess e Dey foram lidos só por resumos de terceiros. As fontes de degradação graciosa são de prática, não de pesquisa revisada. Não medi volume percebido nem latência. A inferência de que o alto-falante a 150% é uma escolha do Humano vem do fato de o ajuste já existir quando comecei, e não de confirmação.

## 6. O que o Agata pode fazer com isso (propostas, não feitas)

1. O `agata_falar.py` passa a imprimir, depois de falar, a saída usada e o volume (declaração, H1).
2. Opcional: contador local de saídas usadas (H2) e aviso de volume acima de 100% sem bloquear (H3).
3. A regra de adaptação entra na skill `agata-voz` como parágrafo curto, com a distinção entre o variável e o invariante.

Qualquer uma passa por proposta P-8 e uma assinatura.

## Referências

- Kephart, J. O.; Chess, D. M. The Vision of Autonomic Computing. IEEE Computer 36(1), 41-50, jan/2003. (N3)
- Dey, A. K. Understanding and Using Context. Personal and Ubiquitous Computing 5, 4-7, 2001. (N3)
- Braden, R. (ed.). RFC 1122, Requirements for Internet Hosts, out/1989, seção 1.2.2. rfc-editor.org/rfc/rfc1122. (N1)
- Thomson, M.; Schinazi, D. RFC 9413, Maintaining Robust Protocols, jun/2023, seções 2, 2.1, 4, 5.1 e 6. rfc-editor.org/rfc/rfc9413. (N1)
- Textos de prática sobre degradação graciosa e falha silenciosa (blogs e glossários de engenharia de confiabilidade). (N3)
- Registros desta sessão: notas 296 do cache do Conselho; `pactl` e `bluetoothctl` em 03/11/2026.
