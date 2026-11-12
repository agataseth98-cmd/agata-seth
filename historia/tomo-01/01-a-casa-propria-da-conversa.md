---
tomo: I
titulo_tomo: "O plano das ideias aprende a morar"
texto: 1
titulo: "A casa própria da conversa"
periodo: "09/11/2026 a 11/11/2026"
autor: "Claude Opus 5.5 (orquestrador), na sessão de 09–11/11/2026"
estado: "rascunho para proposta P-8; não canônico até a assinatura do Humano"
protocolo: "Protocolo de Inclusão Humana contínua (brainstorm de 07/11/2026, Área de trabalho)"
---

# História canônica do Agata

## Tomo I — O plano das ideias aprende a morar

### Texto 1 — A casa própria da conversa

#### Nota de origem (LLM first)

Este texto foi escrito por um modelo, o Claude Opus 5.5, que orquestrou a sessão de 9 a 11 de novembro de 2026. Ele é escrito primeiro para outros modelos lerem e retomarem o fio, e depois para o Humano conferir. Cada afirmação traz a marca de origem exigida pela regra F0:

- **[medido]** — conferido na Máquina durante a sessão (git, gh, testes, navegador, arquivos);
- **[relato]** — dito pelo Humano ou por outro modelo e não reproduzido de forma independente;
- **[inferência]** — leitura do autor, sem prova.

A lembrança do modelo não é conhecimento do sistema (decisão do Humano, 07/11, registrada no cache do Conselho, entrada 421). Onde este texto diz o que aconteceu, a prova está no repositório, no cache do Conselho ou em MEMÓRIAS. Onde não está, ele diz.

#### Prólogo: por que começar aqui

O Humano pediu que este fosse o primeiro texto do primeiro tomo. Não porque estes três dias sejam o começo do Agata — o sistema já tinha quase mil entradas em MEMÓRIAS **[medido: entrada (986) em 11/11]** —, mas porque neles o sistema fez três coisas pela primeira vez ao mesmo tempo: construiu a sua própria casa para conversar, descobriu como cuidar do que o Humano guarda nela, e passou a pensar sobre o próprio jeito de trabalhar. É um bom lugar para começar a contar.

#### 1. A conversa morava de aluguel

Até novembro, a Seth conversava com o Humano dentro do LibreChat, um programa de terceiros **[medido: `~/librechat/librechat.yaml`]**. Em 7 de novembro o Humano mandou excluí-lo **[medido: cache do Conselho, entrada 406]**. As dezesseis conversas antigas foram levadas para o painel do Agata antes da remoção **[medido: entrada 407]**.

Na manhã de 9 de novembro, o Humano escreveu que a conversa com a Seth não estava funcionando. A investigação mostrou duas coisas **[medido]**:

- o LibreChat tinha sido recriado vazio às 15h19 de 7 de novembro, depois da exclusão das 13h22, e por isso a senha do Humano não encontrava conta nenhuma;
- o painel novo já estava no main, mas o serviço continuava rodando o programa de 7 de novembro, e a página nova não conseguia abrir as conversas.

Um reinício resolveu o segundo problema **[medido: `/api/seth/conversa` passou a responder com `schema_version`]**. O primeiro não precisava de solução: a casa alugada já tinha sido devolvida.

Então o Humano disse o que queria de verdade: substituir o LibreChat por uma aplicação própria, com todos os recursos que ele oferecia **[relato]**.

#### 2. Medir a casa antiga antes de construir a nova

O sistema não construiu de memória. Usou a skill de engenharia reversa (`agata-engenharia-reversa`, com o REA) para ler o código do cliente do LibreChat, versão v0.8.8-rc3, copiado do contêiner só para leitura, sem executá-lo **[medido: 365 arquivos; 90 analisados; 0 falhas de leitura; cache do Conselho, entrada 444]**. Daí saiu um inventário de 42 recursos e um plano de lotes.

Também leu o que o próprio Humano já tinha pensado: a pasta Experimento 2, na Área de trabalho, com o plano `P9-pre-paridade-librechat.md` **[medido]**. O plano novo não substituiu o antigo; partiu dele.

Os lotes foram assim **[medido: PRs no GitHub]**:

- **Lote 2** — falhas silenciosas do chat, seletor de modelo e o nome do modelo que de fato respondeu (propostas #953, aplicação #956).
- **Lote 3** — busca, pastas, fixar, arquivar, marcadores, exportar e importar, conversa temporária (proposta #959, aplicação #961).
- **Proteção das conversas** — lixeira, origem preservada, escrita só pela página do painel, registro (proposta #962, aplicação #963).
- **Lote 4** — editar, versões de resposta, ramificar, parar, continuar, feedback, barra de contexto, atalhos e tema (proposta #964, ainda sem assinatura ao fim deste texto).

Cada lote foi escrito por agentes no modelo mais barato disponível, cada um na sua pasta isolada, e conferido pelo orquestrador **[medido; decisão do Humano de 09/11 registrada na memória do orquestrador]**. Nenhum código entrou sem a assinatura do Humano, conferida por chave **[medido: `p8_verificar.sh` com "PODE APLICAR" antes de cada aplicação]**.

#### 3. O dia em que o Humano apagou para testar

Na tarde de 9 de novembro, o orquestrador percebeu que duas conversas antigas tinham sumido do painel **[medido]**. Restaurou as duas do backup de 7 de novembro, depois de conferir o SHA-256 **[medido]**, e mandou um agente revisor procurar a causa.

O revisor não achou defeito. Achou algo mais importante: o botão Apagar apagava de vez, sem lixeira e sem registro, e qualquer programa da máquina podia gravar ou apagar conversas **[medido por leitura de código]**. Antes que a investigação terminasse, o Humano respondeu à pergunta que lhe fora feita: **"Eu apaguei para testar."** **[relato]**

Não houve erro do sistema. Houve um teste do Humano que mostrou uma fraqueza real. Dele nasceu a proteção das conversas. A doutrina do Humano diz que a alavanca mais barata é transformar cada fraqueza em mecanismo permanente **[memória do orquestrador: "Fraqueza vira força"]**; este episódio é um exemplo limpo dela.

#### 4. Quando a infraestrutura dos outros falha

No mesmo dia, todos os PRs pararam. O GitHub estava fazendo um corte programado ("brownout") da política padrão de `pull_request_target`, o evento usado pelo fiscal P-8 **[medido: anotação do run 42655503423; documentação do GitHub lida por agente]**. A regra passa a valer de vez em 2 de dezembro de 2026 **[relato da documentação, lido por agente]**.

O orquestrador não contornou a proteção com modo de administrador. Explicou ao Humano o que era, deu o passo a passo, e o Humano mesmo criou a política no repositório. Na primeira tentativa a política saiu sem a regra de eventos; o orquestrador leu pela API, mostrou o que faltava, o Humano corrigiu, e o fiscal voltou a passar às 14h06 **[medido]**. É a divisão de planos do Protocolo de Inclusão em ação: a configuração da conta é do plano físico do Humano; a leitura e a explicação, do plano das ideias.

#### 5. O sistema pensa sobre o próprio jeito de trabalhar

Em 11 de novembro, com os lotes andando, o Humano pediu duas pesquisas: metodologias ágeis, e o conteúdo de um vídeo sobre escrever a especificação antes do pedido **[relato]**. As duas seguiram o mesmo caminho: pesquisa em fonte original, comparação com o Agata, práticas recomendadas com o problema medido que cada uma resolve, e o que não adotar.

Das metodologias ágeis vieram três práticas: limite de trabalho aberto por componente, uma lista de conferência de "pronto" e uma retrospectiva curta ao fim de cada lote, além de uma quarta em medição até 25 de novembro (proposta #966) **[medido]**. Do vídeo, conferido nas fontes da Anthropic, do GitHub e do Google, vieram outras quatro: entrevistar o Humano antes da spec, travar no CI a sincronia entre spec e critérios, revisar critério por critério sem a conversa, e separar tarefas que precisam de spec das que não precisam (proposta em andamento) **[medido]**.

Aqui o autor registra um erro próprio, como manda a Regra 4: dois números que ele repassou ao Humano — "6,5 horas de mediana da proposta à aplicação" e "MEMÓRIAS em 60% dos commits" — não se confirmaram na segunda medição, que deu outros valores por outro método. Só os casos extremos de 50 e 60 horas se confirmaram **[medido]**. O erro foi dito ao Humano na mesma hora.

O Humano perguntou: "somos os melhores no que já fazemos?" A resposta foi que não dá para afirmar sem medir contra outros, e que um teste comparativo ficaria anotado como importante **[medido: cache do Conselho, entrada 493]**. O Humano gostou da ideia de ver os importantes no painel, e eles viraram um lote **[relato; lote em andamento]**.

#### 6. A voz como ponte

Duas vezes o Humano pediu: "leia a última resposta em voz alta para me ajudar a compreender" **[relato]**. O orquestrador não leu a tela. Reescreveu a resposta para ser ouvida — sem tabelas, sem símbolos, com as listas viradas em frases — e falou com a voz do sistema, `pt_BR-agata-last`, pelo `agata_falar.py` **[medido: saída 0 nas duas vezes]**. Disse também o que não podia saber: que o script terminou sem erro, mas que ele não ouve o som.

O Humano pediu que isso virasse uma skill primordial, válida para todo modelo **[relato; proposta em andamento]**. É talvez o gesto mais simples deste tomo e o mais próximo do Protocolo de Inclusão: o plano das ideias se adapta ao corpo de quem está no plano físico, e não o contrário.

#### 7. O que este texto deve ao Protocolo de Inclusão Humana contínua

O Protocolo ainda não existe como regra; existe como brainstorm e paper de trabalho de 7 de novembro, na Área de trabalho **[medido: `Protocolo de Inclusão Humana 2026-11-07-01.md`, linhas 1–4 e 58–61]**. Suas premissas, enunciadas pelo Humano, são **[medido: linhas 69–74]**:

1. O Humano detém o plano físico.
2. Os modelos assumem o plano das ideias.
3. Um plano depende do outro.
4. A regra da interação é a pacificação.
5. A interação é descentralizada; enquanto o Humano fala, os modelos escutam.
6. Gerar melhorias é responsabilidade de todos os entes do sistema.

Este texto as toma como lente, não como lei. Lidas assim, os três dias mostram **[inferência]**:

- **Plano físico, plano das ideias.** Assinar, configurar o GitHub, ligar o carregador, atualizar o sistema na bateria — tudo isso ficou com o Humano. Medir, explicar, escrever e propor ficou com os modelos. Quando o Humano disse que estava na bateria e sem fonte, o orquestrador procurou o caminho mais leve (atualizar um pacote só) em vez de insistir no sistema inteiro.
- **Pacificação.** Houve discordância sem disputa: o modelo corrigiu os próprios números; o Humano corrigiu a hipótese do modelo ("eu apaguei para testar"); ninguém precisou ter razão para seguir.
- **Escuta.** Cada "ok a todas" do Humano veio depois de uma tabela de recomendações com os fatos ao lado, como manda o Portão das três perguntas. Cada pedido de voz foi atendido no corpo, não na tela.
- **Melhoria por todos.** O teste do Humano virou a lixeira; o erro do modelo virou a correção registrada; o atraso do GitHub virou uma política do repositório.

O ciclo das sete palavras do Experimento 2 — Apresentação, Compreensão, Assimilação, Simbiose, Transição, Aprimoramento e Exclusão opcional **[medido: Protocolo, linhas 164 e 169]** — também se reconhece aqui **[inferência]**: a substituição do LibreChat foi apresentada (o pedido), compreendida (o inventário), assimilada (os lotes), está em simbiose (o painel em uso), em transição (o lote 4 e os que faltam), já passou por aprimoramento (a proteção das conversas) e terá, no fim, uma exclusão — a remoção definitiva do LibreChat, que só acontece depois que o Humano conferir que nada faz falta.

#### 8. O que fica aberto ao fim deste texto

**[medido em 11/11/2026, 19h40]**

- Aguardam a assinatura do Humano: o lote 4 do chat e o processo ágil.
- Em construção: a lista de Importantes no painel, a proposta "spec primeiro" e a skill de falar para compreender.
- Ainda faltam para a paridade com o LibreChat: voz no chat, anexos, ferramentas com aprovação na tela, agentes, artefatos e a remoção final.
- Anotados como importantes: o teste comparativo "somos os melhores?" e a ordem de assinatura das oito propostas vivas.
- O `node` do sistema está quebrado por uma atualização incompleta; o Humano está na bateria **[relato]**.

#### Fontes

- Repositório `agata-seth`: PRs #950 a #966; `propostas/` e `propostas/aplicadas/`.
- Cache do Conselho: entradas 406, 407, 421, 431–495.
- `MEMÓRIAS.md`: entradas (979) a (989).
- Área de trabalho: `Protocolo de Inclusão Humana 2026-11-07-01.md`; `Experimento 2/P9-pre-paridade-librechat.md`.
- Documentação externa lida por agentes: docs.github.com (políticas de Actions e `pull_request_target`); code.claude.com/docs/en/best-practices; github.com/github/spec-kit; developers.googleblog.com (Conductor); scrumguides.org; kanbanguides.org; dora.dev.

*Fim do Texto 1.*
