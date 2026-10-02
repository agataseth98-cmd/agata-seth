# Onde estamos

## O que é isto
Agata é o seu sistema. Ele guarda memória e regras que nunca se apagam.
Modelos de IA trabalham nele seguindo o que está escrito aqui.
Esta página é só para você — não para os modelos. Teto: uma tela.
Histórico até 27/09/2026: `extras/arquivo/onde-estamos-ate-2026-09-27.md`.
O registro completo e permanente de tudo é `MEMÓRIAS.md` (entrada (625)).

## Onde estamos — 02/10/2026 (consolidado, pra retomar rápido se a sessão cortar)

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
