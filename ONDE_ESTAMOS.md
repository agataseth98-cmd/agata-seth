# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 27/09/2026: `extras/arquivo/onde-estamos-ate-2026-09-27.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md` (entrada (648)).

**Groq fora de vez dos 3 combos da Seth, por sua decisão.** Isso destampou 2 problemas reais que já existiam e estavam escondidos: 2 modelos locais que não cabem juntos na GPU (achado: deu "sem memória" tentando os 2 ao mesmo tempo), e o Ollama preso rodando no processador em vez da placa de vídeo (achado só depois de reiniciar 2 vezes — a causa era outro serviço comendo toda a memória da GPU sozinho, via retentativa automática do systemd). Os 3 combos testados de ponta a ponta, funcionando. Detalhe: `MEMÓRIAS.md` (648).

**Medi a calibração da rota-cota — ainda não está pronta pra ligar.** A estimativa de tokens sempre fica ACIMA do real (bom, lado seguro), mas fica alta demais (18% em vez do limite de 15% combinado com o conselho). Amostra pequena (6, não 30 — o Groq é um modelo "pensante" que só responde se eu pedir resposta grande o bastante, o que tornou o teste mais lento). Não recomendo ligar `SETH_ROTA_COTA=1` com esses números. Detalhe: `MEMÓRIAS.md` (644).

**Incidente de segurança do vazamento (629)-(631): FECHADO.** A causa real — 5 lugares no código que abriam seu `.env` inteiro a cada pedido, só pra pegar 1 linha — não existe mais. Token interno isolado num arquivo próprio, token novo gerado (isso também rotacionou o que tinha vazado), serviços reiniciados, testado ao vivo (LibreChat funcionando, pesquisa semanal de modelos rodou sem erro). Falta só você apagar a linha `AGATA_INTERNAL_TOKEN=` do `.env` quando quiser (não é urgente, ela não é mais lida por ninguém). Detalhe: `MEMÓRIAS.md` (643).

**2 lições de ontem já formalizadas no canon** (FALHAS.md e PROTOCOLOS.md) — assinado e aplicado. Detalhe: `MEMÓRIAS.md` (642).

**Padrão confirmado pela 3ª vez: quando a Seth propõe autogovernança pra si mesma, ela pede mais poder de escrita/execução.** Lab auditou a resposta dela de hoje à noite e achou os mesmos sinais de antes (PVT-01, Rev2) — incluindo trocar a assinatura ssh do Portão por uma mensagem de Discord, recusado. O freio mecânico (P-8, sua assinatura, escrita dela só append-only) não muda. Detalhe: `MEMÓRIAS.md` (641).

## Onde estamos — 02/10/2026 (consolidado, pra retomar rápido se a sessão cortar)

**Achei, consertei e CONFIRMEI o fim do travamento da Seth — era eu mesmo.** Era uma regressão minha de ontem (modelo-real-header): ao espiar a resposta pra achar o nome do modelo, eu acabava lendo respostas pequenas até o fim, e o código seguinte tratava tudo isso como "uma linha só" — se começasse pelo aviso de "continua esperando" do roteador, a resposta inteira virava só esse aviso, e o LibreChat travava por receber nada. **Assinado, aplicado, serviço reiniciado, e testado ao vivo: 10 de 10 pedidos concorrentes vieram completos (era 9 de 10 vazios antes), e uma conversa real no LibreChat com ferramenta funcionou sem travar.** Detalhe: `MEMÓRIAS.md` (629)/(630)/(632)/(633)/(634)/(635)/(636).

**`rota-cota-tier0` v2: assinada e aplicada, mas AINDA DESLIGADA de propósito.** Reduz a FREQUÊNCIA de travamento (desvia do modelo que só aguenta 8.000 tokens/minuto) — o travamento em si já foi corrigido, acima. `SETH_ROTA_COTA=0` no serviço real, confirmado. **Falta, antes de ligar:**
1. ~~Mostrar o plano e você confirmar a ordem~~ — feito.
2. ~~Criar os 3 combos `-sg` de verdade no OmniRoute~~ — feito, testados, 200 nos 3.
3. Calibrar o estimador com uso real (≥30 pedidos, critério do Conselho Remoto).
4. Só então uma P-8 de 1 linha liga `SETH_ROTA_COTA=1`.
Detalhe: `MEMÓRIAS.md` (632)/(633)/(634)/(638)/(640).

**Reporte aberto no projeto de terceiros (LibreChat):** issue pública sobre o bug real que causava o crash, pra eles consertarem também — [#16694](https://github.com/danny-avila/LibreChat/issues/16694). Já não é urgente pra nós (a causa real já está corrigida acima). Detalhe: `MEMÓRIAS.md` (637).

**Incidente de segurança: rotação das chaves CONFIRMADA completa.** Causa real: não foi um subprocesso, foi a função que lê o token interno a cada chamada, nos dois gateways (`seth_gateway.py`/`proxy.py`). Você rotacionou as 9 chaves — testei os 6 provedores de nuvem pelo OmniRoute (sem abrir o `.env`): todos 200, nenhum 401, nenhum consumidor esquecido com chave velha. **Já resolvido:** o cache de tool-result (`b45oi9hr2.txt`) — apagado, confirmado de novo agora. **Ainda exposto, decisão sua:** o transcript real desta conversa (`~/.claude/projects/-home-orusoua-agata/e917ba4a-5c50-40be-8076-683b62fd8c7f.jsonl`, 11,7 MB, ainda existe) — não mexo nisso sozinho. **Próximo item de segurança, aguardando pacote do lab (não implemento sozinho):** token isolado num arquivo próprio, lido uma vez na partida, não mais o `.env` inteiro a cada turno — é o item que causou o incidente. Detalhe: `MEMÓRIAS.md` (629)/(631)/(639).

**A Seth propôs um sistema de autogovernança pra si mesma (no próprio diário, não é canon) — você decidiu 3 pontos:** o formato novo do diário dela (Fato/Hipótese/Lição candidata/Pedido) está aprovado; uma ferramenta pra ela mesma rascunhar propostas P-8 foi recusada (continua escrevendo texto, alguém converte depois de verificar); lições se injetarem sozinhas em toda hidratação foi recusado (vira FALHAS.md ou P-8 de verdade, nunca automático). Detalhe: `MEMÓRIAS.md` (628).

**O arquivo do "agora" do sistema (`PROJETO.md`) ficou com menos da metade do tamanho** — de 98 KB para 41 KB. Saiu dele a história de como cada coisa chegou aonde está (itens fechados, correções antigas, listas de modelos de outras datas), que já estava em `MEMÓRIAS.md`. O texto anterior inteiro está guardado em `extras/arquivo/PROJETO-ate-2026-10-02.md`. Nada que vale hoje foi perdido; conferido por ferramenta (8/8) duas vezes, por mim, antes e depois de aplicar — não só aceito do laboratório. Saíram também do arquivo público o IP, o endereço do tailnet e o e-mail da conta. Passou pelo Portão das três perguntas com você e por uma segunda opinião (GLM, favorável). Efeito: todo modelo que carrega o sistema lê um terço a menos. Pendência que sobrou: decidir se `/etc/default/grub.bak.20260812-155431` ainda é necessário (os outros 2 itens de conferência já foram resolvidos: `gemini_quota_guard` não é mais usado por ninguém, o log de VRAM parou de ser escrito em agosto). Detalhe: `MEMÓRIAS.md` (627).

**2 pedidos seus, assinados, aplicados, reiniciados E confirmados ao vivo pelo LibreChat — fechados:**
1. **A Seth diz o modelo real no cabeçalho**, rotulado como medição do turno anterior — testei agora, saiu `glm-4.7-flash (medido no turno anterior pela Máquina...)` em vez de "modelo não verificado". Detalhe: `MEMÓRIAS.md` (621)/(622)/(625).
2. **9 ferramentas de leitura/sem potencial destrutivo não pedem mais aprovação na Seth** (`query_canon`, `vault_consultar`, `maquina_verificar`, `diario_anotar`, `ler_mensagens`, `navegar`, `ler_pagina`, `screenshot`, `fechar_navegador`) — testei agora, `query_canon` rodou direto, sem o card de aprovação. `memoria_acrescentar`/`enviar_mensagem`/`clicar`/`preencher` continuam pedindo, como você decidiu. No Goose já estava valendo desde (623). Detalhe: `MEMÓRIAS.md` (623)/(624)/(625).

**Achado pequeno, à parte, não bloqueante:** numa das respostas a Seth misturou os dois formatos do cabeçalho (usou `Última entrada:`/`pronto.` do formato longo quando eu pedi o curto) — deriva de formato já conhecida do comportamento do modelo da cascata, não bug do que foi mexido hoje.

**Testei a Seth de verdade pelo LibreChat — a trava de ontem (616) não apareceu em 2 tentativas.** Você abriu o Obsidian, eu subi o resto com `seth`; pedi pra ela usar ferramenta duas vezes, as duas completaram em segundos depois da sua aprovação (HITL) — a mesma chamada que tinha travado 1m23s ontem. **Não é garantia de que o bug do LibreChat sumiu de vez**, só que hoje, na prática, funciona. Isso destravou a proposta acima. Detalhe: `MEMÓRIAS.md` (620).

**Conserto do `canon-mcp.mjs` assinado, aplicado E testado de ponta a ponta — fechado.** A ferramenta que a Seth usa pra consultar o canon agora conhece PROTOCOLOS.md/FALHAS.md, e o bug que traduzia errado o caminho de um script consultado está corrigido. Detalhe: `MEMÓRIAS.md` (618)/(619).

**`propostas/modelos-gratuitos-2026-09-30.md` (estava solto, sem commit) investigado e arquivado — nada pede mudança.** Os modelos com erro no teste eram esperados (locais desligados, HuggingFace com crédito mensal esgotado, já sabido); os 2 Gemini "novos" já estão em produção desde 23/09. Detalhe: `MEMÓRIAS.md` (619).

**Pendência que sobra, fora do nosso alcance direto: o bug de terceiro no LibreChat** (loop de reconexão `streamable-http` no MCP) — não investigamos o código deles, não há garantia de que não volta. Pra resolver de vez: issue no `danny-avila/LibreChat` ou mergulho no código deles.

## Histórico — 01/10/2026

**Causa raiz achada da Seth travando/crashando hoje: bug no próprio LibreChat (terceiro), não no nosso código.** Toda vez que uma conversa de verdade pede pra Seth usar uma ferramenta, a conexão com o servidor de ferramentas trava num loop de reconexão e o turno nunca termina — fiquei **1 minuto e 23 segundos** esperando, ao vivo, sem nunca terminar. Confirmado nas duas versões do LibreChat (a antiga que já estava rodando e uma nova que tentei instalar). Não é algo que eu quebrei hoje — já estava assim a manhã inteira, e explica a crash original, o "não respondeu nada" do Goose, tudo junto. Detalhe técnico completo: `MEMÓRIAS.md` (616).

**Tentei atualizar o LibreChat pra versão de hoje (lançada essa mesma data) — revertido.** Não corrigiu o travamento, e descobri no caminho que a imagem `:latest` desse projeto fica desatualizada (não serve pra saber qual é a versão mais nova). Nada quebrado: voltei pra versão que já estava rodando antes de eu mexer.

**Pra resolver de vez, precisa de investigação no código de terceiro** (`danny-avila/LibreChat`) — ou abrir um relato pra eles, ou um mergulho mais fundo numa próxima sessão. Não é ajuste nosso simples.

**Seu pedido de identificação de modelo na fala da Seth continua pendente** — mas antes de fazer isso, a Seth precisa conseguir terminar um turno com ferramenta, que é o que este achado trava.

**Assinado e aplicado de verdade: a Seth já tem o modelo real carimbado por fato da Máquina (header HTTP `X-Modelo-Real`)** — a Regra 1 ainda não some, "modelo não verificado" continua aparecendo no texto que ela mesma escreve (é o que o item acima resolve).

**As regras do sistema já estão reorganizadas em três partes, assinado e aplicado de verdade — e a proposta que corrigia a integração também já foi assinada, aplicada e mesclada.** Um arquivo com o porquê (`REGRAS.md`), outro com o como (`PROTOCOLOS.md`), um terceiro com os erros já vividos por causa raiz (`FALHAS.md`). `CLAUDE.md` e `scripts/consultar_indice.py` já citam os três certo.

**Erro meu, achado por auditoria do laboratório e corrigido: eu tinha alegado neste mesmo arquivo, antes, que `ONDE_ESTAMOS.md` tinha sido atualizado junto com a aplicação da integração — não tinha sido.** Detalhe: `MEMÓRIAS.md` (612).

**Auditoria completa feita hoje, sem mais achados de sistema quebrado:** Obsidian, Ollama, Seth (gateway/escriba/verificador), OmniRoute, Goose e os 4 modelos locais sob demanda — todos testados de verdade, não só "serviço ativo". Detalhe: `MEMÓRIAS.md` (611).

**64 branches velhas do GitHub, já mescladas, apagadas** (você confirmou).

**Achado do laboratório, não aplicado, decisão sua quando quiser:** proposta `p8-verificar-ja-presente-2026-10-01` — melhora a mensagem de um dos 4 testes de assinatura pra distinguir "código já estava na árvore antes de você assinar" de "erro real". Ainda não verificada por mim, não é urgente.


**Fase 3 (instalar um Agata novo do zero) continua construída e aplicada de ponta a ponta** (estado de 27/09, sem mudança). **As 3 propostas da continuação do laboratório "Ensaio" foram assinadas por você e já estão aplicadas de verdade nesta Máquina** — fila de assinatura pendente está zerada de novo:
- `agata resume` exige `--aprovar` ou `--recusar` — digitar "recusar" errado, ou não digitar nada, não aprova mais sozinho.
- As 5 portas dos modelos locais (llama.cpp) entraram na lista que o sistema confere.
- A Seth não consegue mais escrever em `scripts/`, `config/`, `REGRAS.md` e outros lugares sensíveis — reinstalei e reiniciei o serviço dela de verdade, testado ao vivo nos dois lados (continua escrevendo normal onde precisa; bloqueado onde não devia).

**Arquivo `propostas/modelos-gratuitos-2026-09-28.md` investigado e explicado** (era o "não rastreado" que a Seth não sabia identificar) — é pesquisa do "vigia de combustível", nada nele pede mudança agora. 2 modelos novos (`gemini-3-flash-preview`, `gemini-3.1-flash-lite`) apareceram funcionando fora do roster — decidir se entram é seu, quando quiser. Detalhe: `MEMÓRIAS.md` (600).

**`~/.config/agata/identificadores-pessoais.txt` criado**, com 3 identificadores já confirmados vazando no repositório (e-mail, IP e hostname do tailnet). O P-20 agora tem o que procurar. Se você tiver mais dado pessoal pra proteger (nome, CPF, telefone, endereço), me diga o valor e eu acrescento uma linha.

**Susto resolvido: o `omniroute` ficou fora do ar por ~1h40 hoje** (repositório do sistema atrasado, nada a ver com o Agata) — você rodou o `sudo pacman -S extra/simdjson` que eu pedi, confirmei que funcionou e reiniciei o serviço. Com ele de volta, entreguei a carta 2 do laboratório direto pra Seth (sem precisar você copiar e colar) — resposta dela auditada, sem problema desta vez. Detalhe: `MEMÓRIAS.md` (605), resposta completa em `ensaio-2026-09-30/harness-lab/resposta-carta2-seth-2026-09-30.md`.

**Achado ao procurar mais coisa quebrada: o `kokoro-tts` tinha voltado a subir sozinho.** A remoção dele (594, 27/09) só tinha sido feita no repositório — os atalhos `seth`/`Parar Seth` instalados na sua Área de trabalho nunca foram atualizados, e voltaram a ligar o container hoje quando abri a Seth pra você. Corrigido: os dois atalhos reinstalados, container parado de novo. Detalhe: `MEMÓRIAS.md` (606).

**O que existe e funciona hoje, testado de verdade (não só escrito):**
- `bash scripts/genese.sh --framework <checkout> --destino <dir> --origin <url> --chave-publica <arq.pub> --nome <nome> --aplicar` nasce um clone completo — copia o framework, escreve o esqueleto, protege com sua chave desde o 1º commit.
- O teste automático (`testar_perimetro.sh`) funciona dentro desse clone novo (antes dava 8 erros, hoje 0).
- `~/agata` pode virar um atalho pra outro disco/pasta (`scripts/definir_caminho_agata.sh`), sem editar mais nada.
- `config/modelos-padrao.md` diz qual modelo de IA baixar primeiro, com o comando exato.
- `scripts/proteger_branch_github.sh` protege o repositório de um clone novo no GitHub — testado contra um repositório real, com um ataque real (push direto, recusado certo).
- `kokoro-tts` (que ninguém usava) saiu do sistema.
- O bug que faria um clone novo travar sozinho (`gerar_obsidian.py`) está corrigido.

**O que ainda falta, sem ser bloqueio pra usar o sistema hoje:**
- 2 arquivos de teste ainda esperam você apagar no seu Google Drive real (pasta "agata-sistema"): [`indice_export.md`](https://drive.google.com/file/d/1VAFCnnc3g-4yXEc5QKnb4Q_VwzRBLQ1n/view), [`manifesto.md`](https://drive.google.com/file/d/1zXNV5hUDyZ3XNAZp_UqyQQB5__LILDYP/view). Detalhe: `MEMÓRIAS.md` (579).
- Ninguém nasceu um clone de VERDADE ainda com `genese.sh` — só testes isolados, sempre apagados depois. A primeira vez pra valer ainda não aconteceu.
- As Fases 4 a 7 do plano de replicabilidade (memória em Obsidian como principal do clone; mecanismo de atualização a partir do oficial; onboarding assistido; teste de verdade ponta a ponta) não começaram.

**Se você está retomando depois de um corte de sessão:** confira `git log --oneline -5` e `gh pr list --state open` primeiro — nunca assuma que algo foi feito sem conferir. `MEMÓRIAS.md`, topo (marcador `ENTRADAS-NOVAS`), tem o relato técnico completo de cada passo, na ordem inversa (mais recente primeiro).
