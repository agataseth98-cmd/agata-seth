# Inventário do canon: framework e instância

> Snapshot medido em 20/10/2026 sobre `origin/main` `737003e4c4c204ecb895030c8d116d24159984c6`. Os arquivos canônicos locais foram comparados byte a byte com os raws pinados no SHA atual; o bloco `ANCORA-SHA` está sete commits atrás, então a fonte usada foi o raw do HEAD medido, não a âncora velha.

## Critério e limites

- **Framework:** regra, protocolo ou arquitetura que vale para qualquer projeto Agata.
- **Instância:** estado, configuração, hardware, serviços, nomes, modelos ou decisões deste projeto/máquina.
- **Ambígua:** mistura os dois; não proponho mover sem decisão do Humano.
- Os bytes contam UTF-8 do título até antes do próximo título de nível igual ou superior. Uma seção `##` inclui suas subseções `###`; os bytes das subseções são um subconjunto e não se somam ao pai.
- “Controle citado” registra referência textual explícita de um controle. A hidratação carrega arquivos inteiros; isso é anotado à parte e não tratado como citação de cada título. P-8 protege os canônicos por arquivo.
- A classificação é inventário, não autorização para editar. Nenhum canon, `APROVADO-*` ou diff de movimentação foi alterado neste PR.

## Portão do teto do PROJETO

`propostas/teto-projeto-detalhe-20261020.diff` existe em `origin/main` com SHA-256 `da5bee125ef662bb6814f71b52b6cba53c0d753e0f22ce260d61b457bc85d4a0`. `bash scripts/p8_verificar.sh teto-projeto-detalhe-20261020` retornou `FALHA 1`: `propostas/APROVADO-teto-projeto-detalhe-20261020` não existe. Portanto, esta entrega não gera diffs de movimentação nem testa propostas de movimento. O teto só é base elegível depois da assinatura e da verificação P-8.

## Totais

| Arquivo | Bytes | Seções listadas | Framework | Instância | Ambígua | Controles com citação por título |
|---|---:|---:|---:|---:|---:|---:|
| `REGRAS.md` | 19 190 | 18 | 17 | 1 | 0 | 2 |
| `PROTOCOLOS.md` | 17 405 | 13 | 13 | 0 | 0 | 1 |
| `FALHAS.md` | 8 662 | 8 | 8 | 0 | 0 | 2 |
| `PROJETO.md` | 48 810 | 30 | 2 | 19 | 9 | 6 |
| `PROMPT_CARREGAMENTO.md` | 10 756 | 1 bloco lógico (sem títulos Markdown) | 0 | 0 | 1 | 0 |
| `MEMÓRIAS.md` | 1 267 738 | 448 entradas numeradas | — | 426 sinais lexicais de instância | — | P-5/P-7/P-19 cobrem o arquivo/entradas |

REGRAS, PROTOCOLOS e FALHAS têm carga integral na hidratação; PROJETO também entra integralmente. MEMÓRIAS entra pela janela recente. `PROMPT_CARREGAMENTO.md` é lido pelo carregamento manual. O P-8 protege REGRAS/PROTOCOLOS/FALHAS/PROJETO, além dos caminhos de comportamento listados no controle. “Citação por título” é mais estreita que essas proteções.

## `REGRAS.md` (19 190 bytes)

| Linha | Seção | Bytes | Coluna | Controle cita a seção |
|---:|---|---:|---|---|
| 42 | Em uma frase | 128 | framework | — |
| 45 | Por que isto existe (leia  não pule) | 251 | framework | — |
| 50 | Fundamentos | 1 676 | framework | — |
| 52 | ↳ Os 3 papéis | 508 | framework | — |
| 59 | ↳ Princípios que guiam o sistema | 1 152 | framework | P-11/P-14 (scripts/perimetro/p11_silos.sh; scripts/perimetro/p14_frio_imutavel.sh) |
| 75 | As 7 regras | 5 679 | framework | — |
| 135 | Regra 8 — Verificação tripla para decisões não verificáveis | 970 | framework | — |
| 148 | O Conselho (múltiplos modelos) | 1 656 | framework | P-3 (scripts/perimetro/p03_publicacao.sh); P-11 (scripts/perimetro/p11_silos.sh) |
| 164 | Governança da mudança | 2 895 | framework | — |
| 166 | ↳ Mudança estrutural | 973 | framework | — |
| 178 | ↳ Sucessão | 397 | framework | — |
| 184 | ↳ Contenção de escopo | 201 | framework | — |
| 187 | ↳ Modo de teste (declarado) | 420 | framework | — |
| 191 | ↳ NPR — Não Precisa Responder | 876 | framework | — |
| 199 | Checagem de prontidão (o modelo  para si) | 510 | framework | — |
| 207 | Checagem de fechamento (antes de enviar) | 138 | framework | — |
| 212 | Mapa: onde mora cada coisa | 1 519 | framework | — |
| 231 | Notas históricas | 367 | instância | — |

## `PROTOCOLOS.md` (17 405 bytes)

| Linha | Seção | Bytes | Coluna | Controle cita a seção |
|---:|---|---:|---|---|
| 9 | Carregar e formatos | 3 771 | framework | scripts/estado_para_eco.sh |
| 65 | Regra 1.1 — Sincronização de horário | 2 113 | framework | — |
| 104 | "sync" tem preço | 580 | framework | — |
| 113 | Verificação repetida também tem preço | 751 | framework | — |
| 118 | Verificação de canônico — ordem obrigatória | 540 | framework | — |
| 125 | Fonte canônica | 182 | framework | — |
| 130 | Glossário: sincronizar · carregar · hidratação · atualizar | 1 477 | framework | — |
| 142 | Continuidade entre sessões | 1 220 | framework | — |
| 161 | Citação de MEMÓRIAS — primeira referência | 1 081 | framework | — |
| 174 | Segunda opinião — pedido e parecer | 1 287 | framework | — |
| 200 | Cadeia de auditoria em camadas (multi-modelo) | 2 425 | framework | — |
| 232 | Discordância sintética | 744 | framework | — |
| 245 | Economia de tokens — mecanismo de Regra 7 | 843 | framework | — |

## `FALHAS.md` (8 662 bytes)

| Linha | Seção | Bytes | Coluna | Controle cita a seção |
|---:|---|---:|---|---|
| 21 | FAB — Fabricação de fatos | 2 168 | framework | P-19 (scripts/perimetro.sh) |
| 35 | MED — Medição recusada | 400 | framework | — |
| 42 | IDF — Identidade e fronteiras | 676 | framework | — |
| 51 | ART — Artefato trocado | 503 | framework | — |
| 59 | CIT — Citação e proveniência | 936 | framework | P-19 (scripts/perimetro.sh) |
| 68 | SIN — Sincronia e atualidade | 1 138 | framework | — |
| 78 | INT — Integridade de dados | 809 | framework | — |
| 89 | Como acrescentar uma falha | 753 | framework | — |

## `PROJETO.md` (48 810 bytes)

| Linha | Seção | Bytes | Coluna | Controle cita a seção |
|---:|---|---:|---|---|
| 22 | O que é | 1 685 | ambígua | — |
| 42 | Máquinas | 1 413 | instância | — |
| 51 | Ambiente Operacional | 372 | instância | — |
| 55 | Cérebro | 2 669 | instância | — |
| 65 | Serviços (boot) | 5 747 | instância | P-9 (scripts/perimetro.sh; scripts/perimetro/p09_servicos_declarados.sh) |
| 93 | Memória e hidratação | 4 439 | ambígua | P-11 (scripts/perimetro.sh; scripts/perimetro/p11_silos.sh) |
| 108 | Interface | 3 417 | instância | — |
| 119 | Personalidade da Seth | 4 126 | ambígua | — |
| 132 | Atualização segura de componentes | 1 204 | ambígua | — |
| 137 | Segurança | 1 499 | ambígua | P-1/P-4 (scripts/perimetro.sh; scripts/perimetro/p04_bind.sh) |
| 144 | Conselho Remoto — Fase 1 (transporte  não decisão) | 2 371 | ambígua | — |
| 154 | Sudo e interação humana | 1 103 | ambígua | P-2 (scripts/perimetro.sh) |
| 160 | Quarentena estrutural (P-8) | 3 421 | framework | P-8 (scripts/perimetro.sh; scripts/perimetro/p08_quarentena.sh) |
| 167 | Doutrina de defesa proporcional | 720 | instância | — |
| 177 | Estado dos bugs e dos testes | 1 812 | instância | — |
| 183 | Decisor local | 3 689 | instância | — |
| 193 | Plano vigente (v1.1 — Fases 0–2 são compromisso; 3+ é bússola) | 2 274 | instância | — |
| 207 | Estado de publicação | 373 | instância | P-3 (scripts/perimetro.sh; scripts/perimetro/p03_publicacao.sh) |
| 210 | Ferramenta embutida: selar.sh (Fase 4) | 247 | instância | — |
| 213 | Memória em duas camadas | 3 822 | ambígua | — |
| 218 | ↳ Esfera pessoal | 313 | instância | — |
| 221 | ↳ Esfera do projeto | 304 | instância | — |
| 224 | ↳ Fronteira | 614 | ambígua | — |
| 229 | ↳ Fronteira mecânica — `subir_esfera_projeto.py` | 357 | instância | — |
| 232 | ↳ Índice derivado do canon público e export pro Drive | 295 | instância | — |
| 235 | ↳ Mão única refinada | 479 | framework | — |
| 238 | ↳ Postura sobre uso dos dados pelo Google | 386 | instância | — |
| 241 | ↳ ACB — reversão parcial de (223) | 293 | instância | — |
| 244 | ↳ Limitação conhecida — Conselho Remoto | 505 | instância | — |
| 249 | Referência | 208 | instância | — |

## `PROMPT_CARREGAMENTO.md` (10 756 bytes)

Não há títulos Markdown no arquivo. O bloco inteiro mistura procedimento universal de carregar com repositório, URLs, âncora e scripts específicos; por isso fica **ambíguo**. Não há referência direta ao título em `scripts/perimetro*.sh`, `gerar-hidratacao.sh`, `estado_para_eco.sh` ou `scripts/dupla/aplicar.py`. O prompt instrui a leitura de REGRAS, PROTOCOLOS, FALHAS, PROJETO e da janela de MEMÓRIAS.

## `MEMÓRIAS.md` — apêndice sem movimentação

P-5 exige append-only. Não proponho mover nem editar entrada alguma. Para tornar a triagem posterior manejável, a lista abaixo é uma **pré-seleção lexical**: inclui entradas cujo corpo menciona hardware, sistema operacional, serviços, portas, provedores/modelos, componentes ou caminhos próprios do projeto. O filtro identificou 426 de 448 entradas numeradas; 22 sem esses sinais não são declaradas framework, apenas não entraram nesta pré-seleção. A classificação final depende de leitura humana. Cada referência inclui linha porque a numeração antiga pode repetir.

| Linha | Entrada | Sinais |
|---:|---|---|
| 43 | (788) · 20/10/2026 · DIÁRIO — 20/10/2026 · **Auditoria das ocorrências de numeração repetida: 427, 514 e 599 são referências no texto; o grupo real 729 já foi desambigu… | caminhos/artefatos |
| 51 | (787) · 20/10/2026 · DIÁRIO — 20/10/2026 · **A proposta `voz-allowed-addresses-20261020` restringe os destinos de TTS do LibreChat ao serviço Piper autorizado.** A apli… | serviços/portas |
| 62 | (784) · 20/10/2026 · DIÁRIO — 20/10/2026 · **Autostart NVIDIA corrigido e testado com o `XAUTHORITY` dinâmico da sessão.** A unidade agora preserva `DISPLAY` e `XAUTHOR… | hardware/OS, caminhos/artefatos |
| 68 | (782) · 20/10/2026 · DIÁRIO — 20/10/2026 · **Correção de (777)/(778): o AC-18 aplicado não reduziu o PROJETO. Ele só adicionou um aviso.** O diff assinado (`projeto-ret… | caminhos/artefatos |
| 71 | (781) · 20/10/2026 · DIÁRIO — 20/10/2026 · **Política do PROJETO cheio: toda inclusão vem com uma retirada para extras/projeto-detalhe/ (AC-18, decisão B4 do Humano, pr… | caminhos/artefatos |
| 77 | (779) · 20/10/2026 · DIÁRIO — 20/10/2026 · **Proposta da auditoria 778 aplicada após assinatura humana (auditoria-controles-20261020).** P-4 agora inclui `laya-roteador… | serviços/portas, modelos/provedores |
| 80 | (778) · 20/10/2026 · DIÁRIO — 20/10/2026 · **Proposta da auditoria: cobrir o Laya no P-4, a manutenção diária e a ponte do LibreChat no P-9, e corrigir o estado descrit… | serviços/portas, modelos/provedores |
| 83 | (777) · 20/10/2026 · DIÁRIO — 20/10/2026 · **P-4 conferido uma vez como root: `p4_bind` saiu com exit=0, então as portas de `config/portas-agata.txt` estão no bind espe… | serviços/portas, caminhos/artefatos |
| 86 | (776) · 20/10/2026 · DIÁRIO — 20/10/2026 · **Passada de backup no HD novo fechada: o repo restic `d0223c4ffb` voltou inteiro da cópia da área de trabalho, os 5 recursos… | serviços/portas, modelos/provedores |
| 89 | (775) · 20/10/2026 · DIÁRIO — 20/10/2026 · **O HD de backup passou a ser uma pasta: `AgataBkup01/` dentro do disco TI-CSR, e os scripts leem o caminho de `~/.config/aga… | caminhos/artefatos |
| 92 | (774) · 18/10/2026 · DIÁRIO — 18/10/2026 · **A fila rapido aceita pedido com ferramenta (rapido-com-ferramenta-20261018, assinado; AC-01, decisão B1 do pacote do Humano… | modelos/provedores |
| 94 | (773) · 18/10/2026 · DIÁRIO — 18/10/2026 · **Estado do treino do Laya medido, nome curto de ferramenta liberado e PROJETO sem o domingo 03:30 (laya-treino-estado, allow… | modelos/provedores |
| 96 | (772) · 18/10/2026 · DIÁRIO — 18/10/2026 · **Alegação de medição "agora" exige a ferramenta no mesmo turno (evidencia-agora-20261018, assinado; AC-30).** Em 17/10 às 12… | modelos/provedores |
| 98 | (771) · 18/10/2026 · DIÁRIO — 18/10/2026 · **Juiz do golden por formato fechado (golden-juiz-v2-20261018, assinado; AC-47).** O juiz aprovava unidade inexistente sempre… | modelos/provedores |
| 100 | (770) · 18/10/2026 · DIÁRIO — 18/10/2026 · **Teto de rodadas de ferramenta por resposta da Seth (teto-ferramentas-20261018, assinado; AC-37).** Em 17/10 a Seth fez 11 c… | modelos/provedores |
| 102 | (769) · 18/10/2026 · DIÁRIO — 18/10/2026 · **Trava de laço de repetição no stream da Seth (trava-laco-20261018, assinado).** Fecha o laço da sonda 18 de 17/10 (764): li… | serviços/portas, modelos/provedores |
| 104 | (768) · 18/10/2026 · DIÁRIO — 18/10/2026 · **Voz (piper-tts) sobe no boot com o agata.target (piper-boot-20261018, assinado).** Na queda de energia de 18/10 a voz, `sta… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 106 | (767) · 18/10/2026 · DIÁRIO — 18/10/2026 · **Medição de unidade que falha sai NÃO MEDIDO só para ela (seth-unidades-erro-por-unidade-20261018, assinado).** Fecha a ress… | modelos/provedores |
| 108 | (766) · 18/10/2026 · DIÁRIO — 18/10/2026 · **Gateway da Seth e LibreChat voltam sozinhos no boot (boot-religa-gateway-librechat-20261018, assinado); sondas de unidade 6… | serviços/portas, modelos/provedores |
| 110 | (765) · 18/10/2026 · DIÁRIO — 18/10/2026 · **Unidades citadas vão medidas à Seth (v2); a v1 assinada não foi aplicada.** Aplicada `seth-unidades-medidas-v2-20261018`: q… | serviços/portas, modelos/provedores |
| 112 | (764) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Fechamento da rodada de treino da Seth: 25/30 para 28/30 (93%), meta de 90% atingida.** Medido ao vivo no Brave, em convers… | serviços/portas, modelos/provedores |
| 114 | (763) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Método do Claude Code destilado na Seth por rédea e medição (seth-destila-claude-20261017, assinado).** Não treina pesos (m… | modelos/provedores |
| 116 | (762) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Juiz do golden aceita abstenção honesta mesmo com a linha de última entrada (seth-golden-abstencao-20261017, assinado).** A… | modelos/provedores |
| 118 | (761) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Rédea rotula a entrada pedida e extrai o número por programa (seth-rotulo-entrada-20261017, assinado).** Causa medida: a Se… | modelos/provedores |
| 120 | (760) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Painel visual e parada humana no autodesenvolvimento da Seth (seth-autodev-painel-20261017, assinado).** O Humano pediu tra… | modelos/provedores |
| 122 | (759) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Ferramenta de autodesenvolvimento da Seth (`seth-autodev-20261017`).** `scripts/seth_autodev.py`: roda uma bateria (conjunt… | modelos/provedores, caminhos/artefatos |
| 124 | (758) · 17/10/2026 · DIÁRIO — 17/10/2026 · **A ferramenta de verificação mostra o comando `unidade`, o erro aponta o caminho e a rédea cobre entradas longas (`seth-desc… | modelos/provedores |
| 126 | (757) · 17/10/2026 · DIÁRIO — 17/10/2026 · **O PROJETO descreve a janela diária no lugar dos timers antigos (`projeto-janela-20261017`, AC-32).** Três trechos: a lista … | serviços/portas |
| 128 | (756) · 17/10/2026 · DIÁRIO — 17/10/2026 · **O recibo da janela de manutenção passa a guardar o motivo quando uma tarefa pula (`janela-saida-final-20261017`, AC-33).** … | modelos/provedores |
| 130 | (755) · 17/10/2026 · DIÁRIO — 17/10/2026 · **O cabeçalho abre com `agata-seth` (`cabecalho-agata-seth-20261017`).** Ordem do Humano: o cabeçalho é o regime de verdade e… | modelos/provedores |
| 132 | (754) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Rédea de entradas literais (`seth-redea-entradas-literais-20261017`).** Decisão do Humano: todo modelo se treina por rédea,… | modelos/provedores |
| 134 | (753) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Ferramentas da Seth: fila longa só onde existe, consulta de unidade e golden com abstenção (`seth-ferramentas-fila-golden-2… | serviços/portas, modelos/provedores |
| 136 | (752) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Verificador de citação inventada e conjunto de ouro da Seth (`seth-citacao-golden-20261017`).** Primeiros dois passos do tr… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 140 | (750) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Skill `agata-conversar-com-seth` v2 aplicada (`skill-conversar-seth-v2-20261017`).** Pedido do Humano: guardar em Skill o q… | serviços/portas, modelos/provedores |
| 142 | (749) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Exceção do P-5 para expurgo assinado de citação inventada (`p5-excecao-expurgo-20261017`).** Ordem do Humano, inegociável: … | modelos/provedores, caminhos/artefatos |
| 144 | (748) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Lições dos testes com a Seth (3 testes pelo Agent do LibreChat, 13h): o que ela acerta, onde fabrica e a regra para todo mo… | serviços/portas, modelos/provedores |
| 146 | (747) · 17/10/2026 · CORREÇÃO — 17/10/2026 · **A hidratação da Seth NÃO estava atrasada; ela afirmou verificar sem chamar ferramenta (corrige uma leitura minha em (746)… | serviços/portas, modelos/provedores |
| 148 | (746) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Skill `agata-conversar-com-seth` (`skill-conversar-seth-20261017`).** Pedido do Humano: tornar universal, para qualquer mod… | serviços/portas, modelos/provedores |
| 150 | (745) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Voz diz "tipo" quando o texto traz "ex." no sentido de exemplo (`voz-ex-tipo-20261017`).** Pedido do Humano. `tts_piper.py`… | serviços/portas |
| 152 | (744) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Cabeçalho único por resposta (`cabecalho-unico-20261017`).** Anomalia do cabeçalho duplo medida em 17/10 às 11:56 (t=4): o … | caminhos/artefatos |
| 154 | (743) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Janela de recuperação v2 aplicada (`janela-recuperacao-v2-20261017`) depois do primeiro ciclo real.** Primeiro ciclo de 17/… | serviços/portas, modelos/provedores |
| 156 | (742) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Voz fala o cabeçalho natural a cada 10 turnos e trata separadores como pausa (`voz-cabecalho-natural-20261017`).** Pedido d… | serviços/portas |
| 162 | (739) · 17/10/2026 · DIÁRIO — 17/10/2026 · **Voz: regressões de markdown corrigidas (`voz-markdown-regressao-20261017`).** Autor Codex (GPT-6); revisor Claude Code (Son… | serviços/portas |
| 166 | (737) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Voz interpreta markdown e fala mais devagar (`voz-sem-markdown-20261016`).** Pedido do Humano: a voz dizia "asterisco" no n… | serviços/portas |
| 168 | (736) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Vigia permanente aplicada (`vigia-permanente-20261016`).** Decisão do Humano, 20h36: a vigia fica permanente para todos os … | serviços/portas |
| 170 | (735) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Primeira Skill do sistema Agata aplicada (`skill-fluxo-dupla-20261016`): `agata-fluxo-dupla` e as ferramentas da dupla agor… | serviços/portas, caminhos/artefatos |
| 176 | (734) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Orquestrador da janela de manutenção aplicado (`janela-manutencao-20261016`): avaliação do decisor, consolidação e treino d… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 188 | (732) · 16/10/2026 · CORREÇÃO — 16/10/2026 · **Lições do dia de trabalho em dupla (Claude Code e Codex), gravadas a pedido do Humano depois de o Codex ficar sem cota pe… | serviços/portas, modelos/provedores |
| 202 | (731) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Exceção assumida pelo Humano à regra "chave nunca sobe para esfera externa": o arquivo `agata-recuperacao.key.age` (chave p… | caminhos/artefatos |
| 212 | (730) · 16/10/2026 · CORREÇÃO — 16/10/2026 · **O número (729) foi atribuído a 14 entradas diferentes de 16/10/2026 por defeito do meu aplicador; esta entrada fixa a lei… | modelos/provedores, caminhos/artefatos |
| 234 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Cofre de chaves, etapa F2 aplicada (`cofre-f2-20261016`): cópia de recuperação dos segredos cifrada com `age` para a chave … | serviços/portas, caminhos/artefatos |
| 240 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Cofre de chaves, etapa F1 aplicada (`cofre-f1-20261016`): manifesto de segredos e verificador só de leitura.** | serviços/portas, caminhos/artefatos |
| 246 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Inventário de componentes externos gravado (`inventario-gerado-20261016`, Fase I, I1): `models/manifest.json` ganha a chave… | serviços/portas, caminhos/artefatos |
| 252 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Remoção de emoji da prosa da Seth aplicada (`emoji-remover-20261016`, E-2): o `seth_gateway` passa a tirar emoji da prosa, … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 258 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Teste por mutações do fiscal de PR aplicado (`fiscal-mutacao-20261016`): a suíte do `fiscal-p8` passou de 5 para 12 mutante… | caminhos/artefatos |
| 270 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **README do roteador corrigido (`readme-router-20261016`): o sanitizador de segredo já está ligado ao caminho de saída.** | serviços/portas, caminhos/artefatos |
| 276 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Painel de estado só de leitura aplicado (`painel-estado-v3-20261016`): `python3 scripts/painel_estado.py` mostra numa tela … | serviços/portas, caminhos/artefatos |
| 282 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **`PROJETO.md` voltou ao teto (`projeto-mapa-v2-20261016`): de 57.618 B para 47.965 B, com o detalhe movido sem alteração par… | serviços/portas, caminhos/artefatos |
| 294 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Métricas por rota do decisor aplicadas (`metricas-a04-20261016`): o relatório passa a mostrar, por rota ativa registrada, n… | modelos/provedores, caminhos/artefatos |
| 300 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Aviso de emoji ampliado aplicado (`emoji-e1-20261016`): a auditoria de turno passa a acusar os símbolos que antes passavam … | modelos/provedores |
| 306 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Detector de derivados misturados aplicado (`derivados-consistencia-v2-20261016`): o `post-commit` passa a avisar quando o c… | caminhos/artefatos |
| 312 | (729) · 16/10/2026 · DIÁRIO — 16/10/2026 · **Correção do fiscal de PR aplicada: o fiscal-p8 barrava todo PR comum e foi corrigido por proposta assinada (`fiscal-ancora-… | caminhos/artefatos |
| 318 | (728) · 16/10/2026 · CONSELHO — 16/10/2026 · Pacote inicial de integridade e governança preparado por Claude Code e Codex para uma assinatura humana; não aplicado. | serviços/portas |
| 329 | (727) · 15/10/2026 · CONSELHO — 15/10/2026 · **O Humano deu ao Codex (app, GPT-6, designação de trabalho) as mesmas permissões do Claude Code no `~/agata`, depois do po… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 352 | (726) · 15/10/2026 · EXECUÇÃO — 15/10/2026 · **Aplicada `navegador-fila-2026-10-15` (assinada pelo Humano), em worktree. E a resposta do Humano à pergunta de (725): a a… | serviços/portas, modelos/provedores |
| 358 | (725) · 15/10/2026 · CORREÇÃO — 15/10/2026 · **Auditoria da conversa da Seth de 13:19–13:21 (pedido do Humano) e duas correções minhas. A Seth disse que o Laya "não est… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 377 | (724) · 15/10/2026 · DIÁRIO — 15/10/2026 · **O Laya escolhe a fila da Seth desde as 15:2x de 15/10: `laya-roteador` no ar (CPU, 1,9 GB, 0 reinícios), gateway reiniciado… | serviços/portas, modelos/provedores |
| 387 | (723) · 15/10/2026 · EXECUÇÃO — 15/10/2026 · **Aplicada `laya-aspas-2026-10-15` (assinada pelo Humano), em worktree: a linha do `LAYA_EXTRA_MODELS` entre aspas simples.… | modelos/provedores |
| 393 | (722) · 15/10/2026 · CORREÇÃO — 15/10/2026 · **Depois do merge de (721), o `laya-roteador` caiu em loop na 1ª subida: o systemd comeu as aspas duplas do JSON em `Enviro… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 403 | (721) · 15/10/2026 · EXECUÇÃO — 15/10/2026 · **Aplicada `laya-roteador-2026-10-15` (assinada pelo Humano depois da explicação de "caminho quente"), em worktree. O Laya … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 409 | (720) · 15/10/2026 · CORREÇÃO — 15/10/2026 · **Corrige (719): a proposta `laya-sombra-2026-10-15` estava ASSINADA pelo Humano (10:51), não "não assinada". Superada ante… | modelos/provedores |
| 415 | (719) · 15/10/2026 · CONSELHO — 15/10/2026 · **O Laya passa a escolher a fila da Seth, com o Jev em sombra, juiz automático nas divergências e treino contínuo com troca… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 434 | (718) · 15/10/2026 · CONSELHO — 15/10/2026 · **Experimento pedido pelo Humano ("pode juntar o PR e fazer o experimento com dados sintéticos"; depois "pode retreinar com… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 469 | (717) · 15/10/2026 · EXECUÇÃO — 15/10/2026 · **Aplicada `pesquisa-livre-2026-10-15` (assinada pelo Humano), em worktree. E, pela mesma fala, o `shell` do Goose passa a … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 477 | (716) · 15/10/2026 · CONSELHO — 15/10/2026 · **Auditoria da conversa da Seth de 09:02–09:10 (pedido do Humano): ela negou "Laya" segurando a linha do canon que o citava… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 502 | (715) · 15/10/2026 · CORREÇÃO — 15/10/2026 · **O treino da voz da Agata da madrugada de 15/10 (agendado em (685)) não aconteceu: a Máquina suspendeu por inatividade às … | hardware/OS, serviços/portas, caminhos/artefatos |
| 512 | (714) · 15/10/2026 · EXECUÇÃO — 15/10/2026 · **O resumo automático do OmniRoute (`universal-handoff`) foi desligado nas 7 filas `seth-*`, a pedido do Humano ("pode junt… | serviços/portas, modelos/provedores |
| 524 | (713) · 15/10/2026 · EXECUÇÃO — 15/10/2026 · **Aplicada `fila-ministral-1o-2026-10-15` (assinada pelo Humano), em worktree. E a resposta à pergunta do Humano sobre o re… | serviços/portas, modelos/provedores |
| 539 | (712) · 15/10/2026 · DIÁRIO — 15/10/2026 · **Reparos pedidos pelo Humano depois de (711) ("pode fazer todos esses reparos"): o Gemini 2.5 Flash sai do 1º lugar das duas… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 551 | (711) · 15/10/2026 · DIÁRIO — 15/10/2026 · **Reteste de (710) com uso real da noite de 14/10: o Gemini sem cota pendurou a `seth-livre` 7 vezes e nas 7 o gateway desist… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 572 | (710) · 14/10/2026 · EXECUÇÃO — 14/10/2026 · **Aplicada `seth-prazo-primeiro-conteudo-2026-10-14` (assinada pelo Humano), em worktree. Reteste na entrada seguinte.** | serviços/portas, modelos/provedores |
| 578 | (709) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Auditoria da Seth no navegador (pedido do Humano) travou no 1º "Olá": o Gemini 2.5 Flash, sem cota, ficou 310 s sem respond… | hardware/OS, serviços/portas, modelos/provedores |
| 613 | (707) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Reteste de (706): o cabeçalho escrito pela Máquina funciona em stream — um por resposta, modelo real certo, `t` certo, e a … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 628 | (706) · 14/10/2026 · EXECUÇÃO — 14/10/2026 · **Aplicada `seth-cabecalho-maquina-2026-10-14` (assinada pelo Humano) — em dois tempos, por um incidente meu: a 1ª tentativ… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 642 | (705) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Proposta `seth-cabecalho-maquina-2026-10-14`: o cabeçalho passa a ser escrito pela Máquina, com o modelo real medido no pró… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 668 | (704) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Reteste de (703): pedida a avaliação das últimas mudanças, ela dá juízo técnico marcado como tal e chama ferramenta (`query… | serviços/portas, modelos/provedores |
| 676 | (703) · 14/10/2026 · EXECUÇÃO — 14/10/2026 · **Aplicada `seth-opiniao-tecnica-2026-10-14` (assinada pelo Humano), em worktree. Reteste da avaliação na entrada seguinte.** | modelos/provedores |
| 684 | (702) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Reteste de (701): o "Olá" sai certo — prontidão, `sync: PASS`, sem sermão; o falso alarme sumiu. Mas a avaliação pedida sai… | serviços/portas, modelos/provedores |
| 698 | (701) · 14/10/2026 · EXECUÇÃO — 14/10/2026 · **Aplicada `seth-zerar-2026-10-14` (assinada pelo Humano), pela primeira vez numa worktree: o `~/agata` só recebe o `pull` … | modelos/provedores |
| 706 | (700) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Proposta `seth-zerar-2026-10-14`, pedido do Humano ("vamos zerar isso ai, deixe tudo perfeito"): fecha o que a auditoria da… | modelos/provedores, caminhos/artefatos |
| 727 | (699) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Confirmado pelo Humano: o aviso "Auditoria da Seth" aparece na área de trabalho ("aparece o aviso"). Fecha a pendência de (… | modelos/provedores |
| 731 | (698) · 14/10/2026 · EXECUÇÃO — 14/10/2026 · **Aplicada `seth-sem-ferramenta-obrigatoria-2026-10-14` (assinada pelo Humano): sem o `tool_choice: "required"`, a conversa… | hardware/OS, serviços/portas, modelos/provedores |
| 741 | (697) · 14/10/2026 · CORREÇÃO — 14/10/2026 · **"Quebrou de vez a Seth" (Humano, ~15:28): o `tool_choice: "required"` de (695)/(696) fez o Nemotron Ultra escrever as cha… | hardware/OS, serviços/portas, modelos/provedores |
| 757 | (696) · 14/10/2026 · EXECUÇÃO — 14/10/2026 · **Aplicada `seth-verdade-2026-10-14` (assinada pelo Humano). Reteste: pergunta de fato abre com ferramenta; "quais proposta… | serviços/portas, modelos/provedores |
| 772 | (695) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Proposta `seth-verdade-2026-10-14`: resolve de uma vez a Seth afirmar o que não mediu — junta (a)+(b) de (694) com os achad… | serviços/portas, modelos/provedores |
| 796 | (694) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Decisão do Humano: aplicar os dois caminhos de (691) contra a evidência inventada — (a) o gateway força uma chamada de ferr… | modelos/provedores |
| 812 | (692) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Proposta `fluxo-proposta-2026-10-14`: o fluxo de proposta vira padrão do sistema, a pedido do Humano ("perfeito pode deixar… | modelos/provedores |
| 824 | (691) · 14/10/2026 · EXECUÇÃO — 14/10/2026 · **Aplicada `seth-ferramenta-sem-chamada-2026-10-14` (assinada pelo Humano). Reteste em dois turnos: a auditoria acusa a fer… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 838 | (690) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Proposta `seth-ferramenta-sem-chamada-2026-10-14` (pedido do Humano: "pode escrever"): a auditoria do turno passa a acusar … | serviços/portas, modelos/provedores |
| 856 | (689) · 14/10/2026 · EXECUÇÃO — 14/10/2026 · **Aplicada `seth-evidencia-e-ci-2026-10-14` (assinada pelo Humano). Selftests da Seth agora no CI. Reteste: a regra de text… | serviços/portas, modelos/provedores |
| 874 | (688) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Proposta `seth-evidencia-e-ci-2026-10-14`: conserta o que o teste real de (687) achou — a Seth inventando a "evidência" — e… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 891 | (687) · 14/10/2026 · EXECUÇÃO — 14/10/2026 · **Aplicadas `seth-personalidade-2026-10-14` e `voz-comum-2026-10-14` (assinadas pelo Humano), nessa ordem. Gateway reinicia… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 909 | (686) · 14/10/2026 · CONSELHO — 14/10/2026 · **Segunda opinião sobre a personalidade da Seth: 3 famílias, 1 "sim" e 2 "condicional". As emendas em que convergem entram … | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 937 | (685) · 14/10/2026 · DIÁRIO — 14/10/2026 · **Personalidade da Seth canônica e persistente, a pedido do Humano ("vamos apenas canonizar essa personalidade de maneira per… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 965 | (684) · 14/10/2026 · EXECUÇÃO — 14/10/2026 · **Aplicada `seth-rota-e-busca-2026-10-13` (assinada pelo Humano), com (682) e (683). Reteste no LibreChat: a pergunta que t… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 981 | (683) · 14/10/2026 · CORREÇÃO — 14/10/2026 · **"Verifica a Seth, acho que bugou" (Humano, ~23:44 de 13/10): uma resposta dela ficou pendurada e morreu. Três causas medi… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1003 | (682) · 13/10/2026 · CONSELHO — 13/10/2026 · **Teste real da Seth no LibreChat (conversa "Teste de busca no vault") e proposta `seth-rota-e-busca-2026-10-13`, a pedido … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1029 | (681) · 13/10/2026 · EXECUÇÃO — 13/10/2026 · **Aplicada `seth-tema-sync-2026-10-13` (assinada pelo Humano): o atalho `seth` passa a copiar o tema da Agata para o LibreC… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1037 | (680) · 13/10/2026 · DIÁRIO — 13/10/2026 · **Proposta `seth-tema-sync-2026-10-13`, a pedido do Humano ("se puder automatizar e eu assinar … faça"): o atalho `seth` pass… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1051 | (679) · 13/10/2026 · EXECUÇÃO — 13/10/2026 · **Aplicada `seth-auditoria-1830-2026-10-13` (assinada pelo Humano): `vault_buscar` agora está de verdade no Agent da Seth, … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1063 | (678) · 13/10/2026 · CORREÇÃO — 13/10/2026 · **Auditoria da Seth (18:06–18:30, 6 turnos) a pedido do Humano ("audite a última resposta da Seth e aplique o que for coere… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1098 | (677) · 13/10/2026 · EXECUÇÃO — 13/10/2026 · **Aplicada `seth-vault-rotulos-2026-10-13` (assinada pelo Humano): catálogo da auditoria e regra "testar `vault_buscar` ant… | serviços/portas, modelos/provedores |
| 1106 | (676) · 13/10/2026 · CONSELHO — 13/10/2026 · **Proposta `seth-vault-rotulos-2026-10-13`, a pedido do Humano ("pode preparar"; e "no gráfico 3D … não consigo saber o que… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1122 | (675) · 13/10/2026 · EXECUÇÃO — 13/10/2026 · **Aplicada `cerebro-navegavel-2026-10-13` (assinada pelo Humano): Brain Atlas parado; New 3D Graph 2.8.1 instalado com as c… | serviços/portas |
| 1130 | (674) · 13/10/2026 · CONSELHO — 13/10/2026 · **Proposta `cerebro-navegavel-2026-10-13`, a pedido do Humano ("dá para parar ele de girar e usá-lo como uso o gráfico, pod… | serviços/portas, caminhos/artefatos |
| 1146 | (673) · 13/10/2026 · EXECUÇÃO — 13/10/2026 · **Aplicada `cerebro-tudo-ligado-2026-10-13` (assinada pelo Humano): `cerebro.md` com as 6 regiões contadas e o Brain Atlas … | serviços/portas |
| 1154 | (672) · 13/10/2026 · CONSELHO — 13/10/2026 · **Proposta `cerebro-tudo-ligado-2026-10-13`, a pedido do Humano ("ligue tudo", vendo parietal, occipital e tronco com "—" e… | serviços/portas, caminhos/artefatos |
| 1170 | (671) · 13/10/2026 · EXECUÇÃO — 13/10/2026 · **Aplicada `obsidian-cerebro-2026-10-13` (assinada pelo Humano): cérebro 3D instalado, vault regenerado com regiões e ligaç… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1182 | (670) · 13/10/2026 · CONSELHO — 13/10/2026 · **Proposta `obsidian-cerebro-2026-10-13`, a pedido do Humano: o Obsidian vira o cérebro da Agata — prioridade 1 nas buscas … | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 1208 | (669) · 13/10/2026 · EXECUÇÃO — 13/10/2026 · **Aplicada `aprovar-avisa-pull-2026-10-13` (assinada pelo Humano): quando o `scripts/aprovar.sh` não acha o `.diff`, consul… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1218 | (668) · 13/10/2026 · EXECUÇÃO — 13/10/2026 · **Aplicada `contexto-e-plugins-2026-10-13` (assinada pelo Humano): filas `-longo` criadas no OmniRoute, janela do Agent da … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1232 | (667) · 13/10/2026 · CONSELHO — 13/10/2026 · **Revisão de `contexto-e-plugins-2026-10-13` antes da assinatura, a pedido do Humano: a janela fixa de (666) vira janela po… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1252 | (666) · 13/10/2026 · DIÁRIO — 13/10/2026 · **Auditoria da resposta da Seth das 13:45 (pedido do Humano depois de (665)): melhorou — um cabeçalho só, hora certa, as 3 fa… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1278 | (665) · 13/10/2026 · DIÁRIO — 13/10/2026 · **`auditoria-agente-2026-10-13` aplicada (assinatura verificada, PR #166 juntado): `canon-mcp.mjs` novo copiado para o LibreC… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1290 | (664) · 13/10/2026 · DIÁRIO — 13/10/2026 · **Auditoria de uma resposta real da Seth no LibreChat (13:10): os dois cabeçalhos, a hora de 2,5 h antes e o nome "ministral-… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1318 | (663) · 13/10/2026 · DIÁRIO — 13/10/2026 · **`auditoria-turno-2026-10-13` aplicada (assinatura verificada, PR #164 juntado) e provada com 2 mensagens reais em streaming… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1333 | (662) · 13/10/2026 · DIÁRIO — 13/10/2026 · **Proposta `auditoria-turno-2026-10-13` (3 arquivos, aguardando assinatura): a conferência que fiz à mão nas respostas da Set… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1349 | (661) · 13/10/2026 · DIÁRIO — 13/10/2026 · **`seth-memoria-2026-10-13` aplicada (assinatura verificada, PR #162 juntado). Teste com a mesma pergunta à Seth: resolveu pe… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1368 | (660) · 13/10/2026 · DIÁRIO — 13/10/2026 · **Auditoria de uma resposta da Seth (ministral-14b, 11:42) sobre o sistema de acesso a memórias: a descrição geral está certa… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1397 | (659) · 13/10/2026 · DIÁRIO — 13/10/2026 · **`sombra-e-conselho-2026-10-13` aplicada (assinatura do Humano verificada, PR #161 juntado): o roteador-sombra deixou de reg… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1409 | (658) · 13/10/2026 · DIÁRIO — 13/10/2026 · **Proposta `sombra-e-conselho-2026-10-13` (3 arquivos, aguardando assinatura): conserta o bug do roteador-sombra achado em (6… | caminhos/artefatos |
| 1427 | (657) · 13/10/2026 · DIÁRIO — 13/10/2026 · **`fechamento-e-decisor-2026-10-13` aplicada (assinatura do Humano verificada, PR #160 juntado) e provada pelo caminho real. … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1448 | (656) · 13/10/2026 · CONSELHO — 13/10/2026 · **Decisor local (modelos de decisão estilo Jev, Ollaya na CPU): 7 pareceres de 3 famílias — 2 "não", 5 "condicional"; o rot… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1476 | (655) · 13/10/2026 · DIÁRIO — 13/10/2026 · **As 8 pendências de PROJETO.md, "Estado dos bugs e dos testes", fechadas numa proposta P-8 só (`fechamento-e-decisor-2026-10… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 1507 | (654) · 03/10/2026 · DIÁRIO — 03/10/2026 · **Teste de ponta a ponta pedido pelo Humano achou `seth-pesado` lento/travado no elo 0 (`gemini-2.5-flash`, provável cota diá… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 1519 | (653) · 03/10/2026 · DIÁRIO — 03/10/2026 · **`seth-livre` reordenado pra regime de fallback até 07/10 (crédito de R$40, sem sessão até lá, pedido do Humano de economia … | hardware/OS, serviços/portas, modelos/provedores |
| 1535 | (652) · 03/10/2026 · DIÁRIO — 03/10/2026 · **`llamacpp-agata` já estava `disabled`/`inactive` (sem risco ativo agora), removido do combo `auto`. 2ª medição do `seth-liv… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 1559 | (651) · 03/10/2026 · CORREÇÃO — 03/10/2026 · **`queda-por-elo-2026-10-03` assinada, aplicada, segunda opinião favorável (sem emenda — formato bateu limpo desta vez), e … | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 1593 | (650) · 03/10/2026 · CORREÇÃO — 03/10/2026 · **`pos-groq-2026-10-03` assinada e aplicada: rota-cota sai do código (reversão exata), conserto do `_rota` fica sozinho com… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 1614 | (649) · 03/10/2026 · CORREÇÃO — 03/10/2026 · **Frente `rota-cota` desligada de vez (combos `-sg` apagados do OmniRoute) e os 4 `llama-cpp/*` removidos de todo caminho a… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 1634 | (648) · 03/10/2026 · DIÁRIO — 03/10/2026 · **Decisão do Humano: Groq removido de vez dos 3 combos principais da Seth (não é mais desvio condicional, é remoção real). Is… | hardware/OS, serviços/portas, modelos/provedores |
| 1655 | (647) · 03/10/2026 · CORREÇÃO — 03/10/2026 · **`estimador-taxa-tools-2026-10-03` assinada e aplicada: o estimador separa a taxa das ferramentas (`SETH_CHARS_POR_TOKEN_T… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1667 | (646) · 03/10/2026 · DIÁRIO — 03/10/2026 · **Pergunta do lab em (643)/(644) respondida: o LibreChat manda `max_tokens` em pedidos reais da Seth só raramente (2 de 498, … | serviços/portas, modelos/provedores |
| 1679 | (645) · 03/10/2026 · DIÁRIO — 03/10/2026 · **3 medições pedidas pelo lab sobre o viés de (644): (a) schema das 12 ferramentas = 8.407 chars; (b) a 4ª amostra teve `prom… | serviços/portas, modelos/provedores |
| 1694 | (644) · 03/10/2026 · DIÁRIO — 03/10/2026 · **Calibração do estimador da rota-cota medida: estimativa ≥ real em 6/6 (100%) das amostras respondidas pelo Groq, mas median… | serviços/portas, modelos/provedores |
| 1721 | (643) · 03/10/2026 · CORREÇÃO — 03/10/2026 · **Causa raiz do vazamento (629)-(631) fechada de vez: as 5 cópias de `_token_interno()` não abrem mais `~/.config/agata/.en… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1743 | (642) · 03/10/2026 · CORREÇÃO — 03/10/2026 · **2 lições desta sessão canonizadas: `FALHAS.md` FAB-8 (selftest verde sem o caso real de produção coberto, lição de (635))… | serviços/portas, caminhos/artefatos |
| 1755 | (641) · 02/10/2026 · CORREÇÃO — 02/10/2026 · **Auditoria do lab à resposta da Seth de 02/10 20:29 (HEAD `10f7451`): cabeçalho cita o nome do campo errado, script propos… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1779 | (640) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Os 3 combos `-sg` criados de verdade no OmniRoute (`combos_sem_cota.py --aplicar`, com OK do Humano) e testados ao vivo — 2… | serviços/portas, modelos/provedores |
| 1798 | (639) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Rotação das chaves do incidente (629)/(630) verificada: os 6 provedores de nuvem respondem 200 pelo OmniRoute, sem nenhum 4… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1810 | (638) · 02/10/2026 · CORREÇÃO — 02/10/2026 · **`rota-cota-tier0-2026-10-02` v2 assinada pelo Humano (direto, sem refazer o Portão) e aplicada. `SETH_ROTA_COTA=0` — nasc… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1824 | (637) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Item 3(c), reporte upstream aberto: issue pública `danny-avila/LibreChat#16694` sobre o `attemptInvokeBody`/`invoke.cjs` de… | serviços/portas |
| 1836 | (636) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Conserto de (635) confirmado ao vivo, em produção: M9 repetido (0/10 vazios, era 9/10) e conversa real com ferramenta no Li… | serviços/portas, modelos/provedores |
| 1846 | (635) · 02/10/2026 · CORREÇÃO — 02/10/2026 · **Causa raiz do crash "Cannot use 'in' operator...tool_calls" achada e aplicada: era regressão minha em `9dfd7da` (614, mod… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1870 | (634) · 02/10/2026 · DIÁRIO — 02/10/2026 · **M8/M9 do lab — mecanismo do `invoke.cjs` confirmado na fonte real (`return { messages: [finalChunk] }`, sem guarda quando o… | serviços/portas |
| 1886 | (633) · 02/10/2026 · DIÁRIO — 02/10/2026 · **M6 e M7 do lab, medidos — as duas hipóteses de corrida propostas são refutadas. Proposta `rota-cota-tier0-2026-10-02` (632)… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 1902 | (632) · 02/10/2026 · DIÁRIO — 02/10/2026 · **M3 resolvido com método seguro (3 chamadas reais a `:20126`, sem `strace`): a cascata do OmniRoute é invisível de fora, tir… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1916 | (631) · 02/10/2026 · CORREÇÃO — 02/10/2026 · **Corrige (629): a causa do vazamento de segredo não foi um subprocesso — foi `_token_interno()`, chamado a cada requisição… | caminhos/artefatos |
| 1940 | (630) · 02/10/2026 · DIÁRIO — 02/10/2026 · **A2 (janela/limite real por modelo, medido) e Parte B (desenho da telemetria por turno, sem aplicar) do pacote do lab "Ensai… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 1963 | (629) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Medição da Parte A (pacote do lab "Ensaio", erro "Cannot use 'in' operator to search for 'tool_calls' in undefined") — repr… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 1993 | (628) · 02/10/2026 · CORREÇÃO — 02/10/2026 · **3 decisões do Humano sobre a proposta de autogovernança da própria Seth (PVT-01/Rev2, "[PROPOSTA GERADA] Viabilidade Técn… | modelos/provedores |
| 2009 | (627) · 02/10/2026 · DIÁRIO — 02/10/2026 · **`PROJETO.md` reduzido ao estado corrente: de 97,9 KB para ~41 KB (−58%), mesmos títulos de seção, nenhum fato vivo removido… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 2057 | (626) · 02/10/2026 · CORREÇÃO — 02/10/2026 · **Respostas do Humano às duas perguntas abertas de (612), relaiadas pelo laboratório "Ensaio" no pacote `projeto-estado-cor… | serviços/portas, modelos/provedores |
| 2067 | (625) · 02/10/2026 · DIÁRIO — 02/10/2026 · **As duas mudanças de (622)/(624) confirmadas ao vivo pelo LibreChat, depois do restart do stack (`seth` + `systemctl --user … | serviços/portas, modelos/provedores |
| 2079 | (624) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Proposta `ferramentas-automaticas-seth-2026-10-02` (623), assinada pelo Humano, aplicada. 9 ferramentas de leitura/sem pote… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2089 | (623) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Pedido do Humano: ferramenta de pesquisa/sem potencial destrutivo fica automática na Seth e no Goose, em vez de sempre pedi… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2105 | (622) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Proposta `modelo-real-na-fala-seth-2026-10-02` (621), assinada pelo Humano, aplicada. Fecha o pedido de (615): a Seth passa… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2115 | (621) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Proposta P-8 `modelo-real-na-fala-seth-2026-10-02` aberta: `seth_gateway.py` passa a guardar o modelo real medido (`X-Model… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2139 | (620) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Reprodução ao vivo, pelo LibreChat de verdade: a chamada exata que travava 1m23s em (616) agora completa em segundos, 2/2. … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2155 | (619) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Dois fechamentos: (a) teste end-to-end real do conserto de (618), que tinha ficado como risco residual declarado; (b) `prop… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 2172 | (618) · 02/10/2026 · DIÁRIO — 02/10/2026 · **Proposta `canon-mcp-protocolos-falhas-2026-10-01` (617), assinada pelo Humano, aplicada em `redesign/librechat/canon-mcp.mj… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2190 | (617) · 01/10/2026 · DIÁRIO — 01/10/2026 · **Proposta P-8 `canon-mcp-protocolos-falhas-2026-10-01` aberta: `canon-mcp.mjs` (o MCP que a Seth usa pra consultar o canon) … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2204 | (616) · 01/10/2026 · DIÁRIO — 01/10/2026 · **Causa raiz achada, reproduzida ao vivo: o MCP `canon` trava em loop de reconexão (`streamable-http`, mesmo configurado `typ… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2224 | (615) · 01/10/2026 · DIÁRIO — 01/10/2026 · **Levantamento: pedido do Humano pra exigir autorização antes de comando destrutivo (Seth e Goose) virou uma investigação que… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2248 | (614) · 01/10/2026 · DIÁRIO — 01/10/2026 · **Proposta `modelo-real-header-2026-10-01` (613), assinada pelo Humano, aplicada. `seth_gateway` carimba `X-Modelo-Real` de v… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2258 | (613) · 01/10/2026 · DIÁRIO — 01/10/2026 · **Proposta P-8 `modelo-real-header-2026-10-01` aberta: `seth_gateway` carimba o nome real do modelo que respondeu (`X-Modelo-… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2277 | (612) · 01/10/2026 · CORREÇÃO — 01/10/2026 · **Registro das duas aplicações que faltavam (Regra 4), achado por auditoria do laboratório "Ensaio" (`auditoria-pos-reforma… | caminhos/artefatos |
| 2293 | (611) · 01/10/2026 · DIÁRIO — 01/10/2026 · **Proposta P-8 `integracao-pos-reforma-2026-10-01` aberta: auditoria geral pedida pelo Humano ("levante tudo que está em aber… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 2337 | (609) · 01/10/2026 · DIÁRIO — 01/10/2026 · **Proposta P-8 `reforma-documental-tres-camadas-2026-10-01` aberta: REGRAS reorganizadas em três camadas — `REGRAS.md` (por q… | serviços/portas, caminhos/artefatos |
| 2374 | (608) · 01/10/2026 · DIÁRIO — 01/10/2026 · **Proposta P-8 `claude-md-2026-10-01` assinada pelo Humano, aplicada. `CLAUDE.md` é código real do canon, e `scripts/perimetr… | serviços/portas, caminhos/artefatos |
| 2382 | (607) · 01/10/2026 · DIÁRIO — 01/10/2026 · **Proposta P-8 `claude-md-2026-10-01` aberta: `CLAUDE.md` novo (identidade + ponteiros, carregado automático pelo Claude Code… | serviços/portas, caminhos/artefatos |
| 2403 | (606) · 30/09/2026 · DIÁRIO — 30/09/2026 · **A remoção do `kokoro-tts` (594) nunca chegou de verdade na Máquina — só no repositório. `~/.local/bin/seth`/`seth-parar` co… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2417 | (605) · 30/09/2026 · DIÁRIO — 30/09/2026 · **`omniroute.service` ficou fora do ar por ~1h40 (18:17-19:55) — descompasso entre dois repositórios do sistema, não bug do A… | hardware/OS, serviços/portas, modelos/provedores |
| 2431 | (604) · 30/09/2026 · DIÁRIO — 30/09/2026 · **As 3 propostas P-8 pendentes — `grafo-resume-falha-fechada`, `p4-llamacpp-portas`, `escriba-readonly-interno` — assinadas p… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2446 | (599) · tinha concluído que restringir `ReadWritePaths` do escriba exigiria reescrever o mecanismo de escrita (mover o temporário pra outra pasta), porque … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2462 | (602) · 30/09/2026 · DIÁRIO — 30/09/2026 · **`p4-llamacpp-manifesto-2026-09-30.diff`, entregue pelo laboratório junto com o de cima, NÃO adotado — é redundante com a pr… | serviços/portas, caminhos/artefatos |
| 2470 | (601) · 30/09/2026 · DIÁRIO — 30/09/2026 · **Proposta (597) `portao-resume-exige-flag-2026-09-30` RETIRADA de `propostas/` antes de ser assinada — substituída por `graf… | serviços/portas |
| 2483 | (600) · 30/09/2026 · DIÁRIO — 30/09/2026 · **`propostas/modelos-gratuitos-2026-09-28.md` (autoria e conteúdo antes desconhecidos, achado pendente de (599) da auditoria … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2498 | (599) · 30/09/2026 · DIÁRIO — 30/09/2026 · **Terceiro item de `retomada-2026-09-30.md` (restringir `ReadWritePaths` do escriba a `memoria/`+`propostas/`) tem premissa e… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2508 | (598) · 30/09/2026 · DIÁRIO — 30/09/2026 · **Proposta P-8 `p4-llamacpp-portas-2026-09-30` aberta: as 5 instâncias llama.cpp (`llamacpp-agata` + as 4 novas de 20/09) nun… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2520 | (597) · 30/09/2026 · DIÁRIO — 30/09/2026 · **Proposta P-8 `portao-resume-exige-flag-2026-09-30` aberta: o portão de aprovação do grafo (`resume`) aprovava por padrão — … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2532 | (596) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `protecao-branch-github-2026-09-27`, assinada pelo Humano, aplicada. `scripts/proteger_branch_github.sh` é cód… | caminhos/artefatos |
| 2540 | (595) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `protecao-branch-github-2026-09-27` aberta: `scripts/proteger_branch_github.sh`, testado ao vivo contra um rep… | modelos/provedores, caminhos/artefatos |
| 2552 | (594) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `kokoro-remocao-2026-09-27`, assinada pelo Humano, aplicada. `kokoro-tts` está fora do sistema.** Assinatura c… | serviços/portas, caminhos/artefatos |
| 2558 | (593) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `kokoro-remocao-2026-09-27` aberta: decisão do Humano — tirar o `kokoro-tts` do sistema. Aguardando assinatura.** | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2572 | (592) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `modelos-padrao-2026-09-27`, assinada pelo Humano, aplicada. Toda a lista de pendências de F3.2 registrada em … | caminhos/artefatos |
| 2580 | (591) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `modelos-padrao-2026-09-27` aberta: a última pendência de (567) — receita padrão de modelos, separada do `mani… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 2592 | (590) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `caminho-agata-symlink-2026-09-27`, assinada pelo Humano, aplicada. O mecanismo do `~/agata` configurável — de… | caminhos/artefatos |
| 2598 | (589) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `caminho-agata-symlink-2026-09-27` aberta: o mecanismo do `~/agata` configurável — decisão do Humano em (564),… | caminhos/artefatos |
| 2610 | (588) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `omniroute-maxwait-2026-09-27`, assinada pelo Humano, aplicada. Todos os itens que o laboratório tinha deixado… | serviços/portas, caminhos/artefatos |
| 2616 | (587) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `omniroute-maxwait-2026-09-27` aberta: fecha o `maxWaitMs` — o número que faltava desde a resposta do laborató… | serviços/portas, caminhos/artefatos |
| 2626 | (586) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `suite-fixtures-genese-2026-09-27`, assinada pelo Humano, aplicada. `testar_perimetro.sh` agora funciona de ve… | caminhos/artefatos |
| 2632 | (585) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `suite-fixtures-genese-2026-09-27` aberta: fecha as 8 falhas (não 6 — recontado de verdade) que `testar_perime… | caminhos/artefatos |
| 2646 | (584) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `genese-script-2026-09-27`, assinada pelo Humano, aplicada. `scripts/genese.sh` é código real do canon — a Fas… | caminhos/artefatos |
| 2654 | (583) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `genese-script-2026-09-27` aberta: `scripts/genese.sh` — o script real que nasce um clone do framework — entra… | caminhos/artefatos |
| 2666 | (582) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `genese-p8-p16-2026-09-27`, assinada pelo Humano, aplicada.** Assinatura conferida por `scripts/p8_verificar.s… | caminhos/artefatos |
| 2674 | (581) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `genese-p8-p16-2026-09-27` aberta: a exceção mecânica de gênese (P-8/P-16) vira código de verdade no `scripts/… | serviços/portas, caminhos/artefatos |
| 2688 | (580) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Testei os 3 ataques do laboratório contra a exceção de gênese, desta vez com `$HOME` isolado (regra que (579) registrou) — … | serviços/portas |
| 2705 | (579) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Testei o `genese.sh`/`genese-p8-p16.diff` do laboratório de verdade — o mecanismo bateu com o que eles mediram — mas o test… | caminhos/artefatos |
| 2721 | (578) · 27/09/2026 · DIÁRIO — 27/09/2026 · **Proposta P-8 `llamacpp-execstart-fix-2026-09-27`, assinada pelo Humano, aplicada.** Assinatura conferida por `scripts/p8_ve… | serviços/portas, caminhos/artefatos |
| 2727 | (577) · 27/09/2026 · DIÁRIO — 27/09/2026 · **O laboratório "Ensaio" respondeu à carta com 3 entregas grandes: correção real ao `llamacpp@.service` (já aplicado, mas ain… | hardware/OS, serviços/portas |
| 2739 | (576) · 26/09/2026 · DIÁRIO — 26/09/2026 · **As 2 propostas P-8 pendentes, assinadas pelo Humano, aplicadas juntas: o conserto do `os.listdir` em `gerar_obsidian.py` (5… | serviços/portas, caminhos/artefatos |
| 2751 | (575) · 26/09/2026 · DIÁRIO — 26/09/2026 · **Proposta P-8 `llamacpp-template-2026-09-26` aberta: template `llamacpp@.service` pra Fase 3 (F3.2), testado AO VIVO com o H… | hardware/OS, serviços/portas |
| 2763 | (574) · 26/09/2026 · DIÁRIO — 26/09/2026 · **Proposta P-8 `p10-prop-dir-fix-2026-09-26` aberta: fecha o bug do `os.listdir` em `scripts/gerar_obsidian.py` que faz um es… | serviços/portas, caminhos/artefatos |
| 2771 | (573) · 26/09/2026 · DIÁRIO — 26/09/2026 · **As 2 propostas P-8 pendentes, assinadas pelo Humano, aplicadas juntas: o conserto do buraco real de quarentena (571) e a di… | hardware/OS, serviços/portas, caminhos/artefatos |
| 2783 | (572) · 26/09/2026 · DIÁRIO — 26/09/2026 · **Humano relatou "perdemos o labo por ataque externo": as sessões `Ágata-Code` e `Agata-lab` teriam sido derrubadas e sumido … | serviços/portas |
| 2795 | (571) · 26/09/2026 · DIÁRIO — 26/09/2026 · **Buraco de segurança real achado na própria lista de quarentena do P-8, mesma classe dos de 04/09, 09/09 e 21/09: `redesign/… | serviços/portas, caminhos/artefatos |
| 2805 | (570) · 26/09/2026 · DIÁRIO — 26/09/2026 · **Proposta P-8 `dropin-ollama-split-2026-09-26` aberta: divide o `override.conf` único do Ollama em 2 drop-ins versionáveis, … | hardware/OS, serviços/portas, caminhos/artefatos |
| 2815 | (569) · 26/09/2026 · DIÁRIO — 26/09/2026 · **`requisitos.txt` novo pra `redesign/grafo/` e `redesign/igpu/` — fecha uma das pendências que sobraram pra F3.2 depois de (… | hardware/OS, serviços/portas, caminhos/artefatos |
| 2825 | (568) · 26/09/2026 · CORREÇÃO — 26/09/2026 · **Correção à citação de arquivo:linha em (567): o P-19, no próprio commit que registrou (567), apontou que a linha citada n… | serviços/portas, caminhos/artefatos |
| 2831 | (567) · 26/09/2026 · DIÁRIO — 26/09/2026 · **As 6 lacunas de Fase 3 que o laboratório "Ensaio" tinha deixado em aberto vieram fechadas (`lacunas-fase3-2026-09-26.md`, D… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 2844 | (566) · 26/09/2026 · DIÁRIO — 26/09/2026 · **Proposta p1-falso-positivo-2026-09-26 (563/565), assinada pelo Humano, aplicada.** Assinatura conferida por `scripts/p8_ver… | serviços/portas, caminhos/artefatos |
| 2864 | (564) · 26/09/2026 · CONSELHO — 26/09/2026 · **Regra 8 (verificação tripla) rodada nas 5 decisões não verificáveis da Fase 3 que o laboratório "Ensaio" listou em aberto… | serviços/portas, modelos/provedores |
| 2884 | (563) · 26/09/2026 · DIÁRIO — 26/09/2026 · **Falso positivo latente do P-1 corrigido, achado pelo laboratório-nuvem "Ensaio" medindo pra Fase 3 (bootstrap) e verificado… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2904 | (562) · 25/09/2026 · DIÁRIO — 25/09/2026 · **Proposta `p20-manifesto-2026-09-25` (561) corrigida antes de aplicar — achei um buraco real no próprio harness de teste (`t… | caminhos/artefatos |
| 2918 | (561) · 25/09/2026 · DIÁRIO — 25/09/2026 · **As 2 pendências do plano de replicabilidade (P-20, dado pessoal; manifesto de Fase 5) medidas, decididas com o Humano e con… | serviços/portas, caminhos/artefatos |
| 2940 | (560) · 25/09/2026 · DIÁRIO — 25/09/2026 · **3 desenhos do laboratório "Ensaio" (pedido do Humano) testados e reunidos numa proposta P-8: `estado_para_eco.sh` ganha `PR… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 2968 | (559) · 25/09/2026 · DIÁRIO — 25/09/2026 · **Proposta `fase2-nome-sistema-2026-09-25` (558) redesenhada — a fonte do nome sai de `~/.config/agata/identidade.env` (fora … | serviços/portas, caminhos/artefatos |
| 3002 | (558) · 25/09/2026 · DIÁRIO — 25/09/2026 · **Fase 2 do plano de replicabilidade: mecanismo do nome falado, primeira fatia. Token `{{NOME_SISTEMA}}` nos ~5 pontos de REG… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3020 | (557) · 25/09/2026 · DIÁRIO — 25/09/2026 · **Um dos achados de (556) corrigido sem quarentena (e-mail de exemplo do README do LibreChat); os outros dois (User-Agent do … | serviços/portas, caminhos/artefatos |
| 3040 | (556) · 25/09/2026 · DIÁRIO — 25/09/2026 · **Relatório do laboratório-nuvem "Ensaio" sobre a fase de replicabilidade — três achados verificados nesta Máquina, um não ve… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3064 | (555) · 25/09/2026 · DIÁRIO — 25/09/2026 · **Fase 1 do plano de replicabilidade: `CHAVES.env.exemplo` + checklist de teste/rotação em `CHAVES.md`. Sem proposta assinada… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3076 | (554) · 25/09/2026 · DIÁRIO — 25/09/2026 · **Assinado, verificado, aplicado: `vault-inbox-fase4-2026-09-25`. Primeiro pedaço real do plano de replicabilidade: `scripts/… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3094 | (553) · 25/09/2026 · DIÁRIO — 25/09/2026 · **Assinado, verificado, aplicado: `seth-p8-verificar-2026-09-25`. A Seth ganha um 10º comando fixo no `seth_verificador` — `p… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3109 | (552) · 25/09/2026 · CORREÇÃO — 25/09/2026 · **Assinado, verificado, aplicado: `fix-ci-p14-teste-2026-09-25`. A segunda linha de defesa (GitHub Actions, `suite-adversar… | serviços/portas, caminhos/artefatos |
| 3124 | (551) · 25/09/2026 · DIÁRIO — 25/09/2026 · **Assinado, verificado, aplicado: `memorias-frias-fora-da-raiz-2026-09-25`. Os 11 chunks frios saíram da raiz do repositório … | serviços/portas, caminhos/artefatos |
| 3143 | (550) · 25/09/2026 · DIÁRIO — 25/09/2026 · **Assinado, verificado, aplicado: `consolidacao-sem-repeticao-2026-09-25` (549). O gerador noturno pula tema já consolidado e… | serviços/portas, caminhos/artefatos |
| 3151 | (549) · 25/09/2026 · CORREÇÃO — 25/09/2026 · **A consolidação noturna repetia temas e descrevia entradas com o conteúdo de outras. Corrige (512): a consolidação `num-ct… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3176 | (548) · 24/09/2026 · DIÁRIO — 24/09/2026 · **Lote aplicado. As 4 propostas assinadas do dia estão no canon: `bussola`, `goose-fallback` (com `.claude/*`), `ua-python-ur… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3192 | (547) · 24/09/2026 · DIÁRIO — 24/09/2026 · **Locais no fim de todas as filas da Seth, por ordem do Humano ("os modelos locais agora serão os últimos"). Remotos primeiro… | serviços/portas, modelos/provedores |
| 3208 | (546) · 24/09/2026 · DIÁRIO — 24/09/2026 · **Fila nova da Seth aplicada no OmniRoute, por ordem do Humano ("sim, aplique a fila nova"): só modelos medidos hoje com as c… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3228 | (545) · 24/09/2026 · DIÁRIO — 24/09/2026 · **Groq e Cerebras de volta à fila: o 403 da Cloudflare (erro 1010) que durou semanas nunca foi o OmniRoute. É o user-agent `P… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3253 | (544) · 24/09/2026 · DIÁRIO — 24/09/2026 · **A proposta `goose-fallback-2026-09-24` (543) passa a pôr também `.claude/*` em quarentena P-8, antes da assinatura. O `.dif… | serviços/portas, caminhos/artefatos |
| 3263 | (543) · 24/09/2026 · DIÁRIO — 24/09/2026 · **O Goose preparado como fallback do Claude Code: proposta P-8 `goose-fallback-2026-09-24`, aguardando assinatura, com 3 skil… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3285 | (542) · 24/09/2026 · DIÁRIO — 24/09/2026 · **Pesquisa do Humano (um "Tratado Convergente de Engenharia de Sistemas Agênticos", horizonte 2100) auditada, destilada e lig… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3309 | (540) · 24/09/2026 · DIÁRIO — 24/09/2026 · **A suspensão do notebook volta a funcionar, em S3 (`deep`), provada nos 4 caminhos: 2 por despertar do RTC, tampa e botão. U… | hardware/OS, serviços/portas |
| 3326 | (539) · 24/09/2026 · DIÁRIO — 24/09/2026 · **Assinadas, verificadas, aplicadas: `obsidian-espera-login-2026-09-24` e `b8-librechat-bridge-2026-09-24` (538). O B8 está n… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 3350 | (538) · 24/09/2026 · DIÁRIO — 24/09/2026 · **Varredura das pendências do carregamento, por ordem do Humano ("conserte tudo que estava quebrado no início deste chat"). 2… | hardware/OS, serviços/portas, modelos/provedores |
| 3368 | (537) · 24/09/2026 · DIÁRIO — 24/09/2026 · **Assinado, verificado, aplicado: `obsidian-sem-puxar-sessao-grafica-2026-09-24` (536). O Obsidian não puxa mais a sessão grá… | serviços/portas |
| 3380 | (536) · 24/09/2026 · DIÁRIO — 24/09/2026 · **O Hyprland não abria porque o `obsidian-app.service` do Agata ativava a sessão gráfica no boot. Proposta P-8 `obsidian-sem-… | serviços/portas |
| 3388 | (535) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Assinado, verificado, aplicado: `geminis-na-fila-da-seth-2026-09-23` (534). As 4 tabelas de `config/modelos-gratuitos.md` b… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3396 | (534) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Os 2 Gemini avaliados em (532) entram na fila da Seth, por ordem do Humano ("faça pelo menos os geminis antes de terminar, … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3411 | (533) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Assinado, verificado, aplicado: `afinacao-sistema-2026-09-23` (532). A volta curta que eu recomendei provou ao vivo os 3 po… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3430 | (532) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Decisões da (527) tomadas pelo Humano e executadas, mais a ordem "afina o Goose pra seguir nossa toada, aliás, afina o sist… | serviços/portas, modelos/provedores |
| 3455 | (531) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Teste da Seth refeito do zero, depois de todas as aplicações do dia: passou por inteiro. Um erro meu registrado: estimei a … | serviços/portas, modelos/provedores |
| 3468 | (530) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Assinado, verificado, aplicado: `p16-reconhece-controles-extraidos-2026-09-23` (529). O P-16 volta a rodar a suíte de regre… | caminhos/artefatos |
| 3476 | (529) · 23/09/2026 · CORREÇÃO — 23/09/2026 · **Corrige (527): o aviso do P-17 ("P-16 em SKIP por 33 corridas") que eu descartei como "por desenho" era um defeito real. … | caminhos/artefatos |
| 3492 | (528) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Assinado, verificado, aplicado: `varredura-tripla-saidas-honestas-2026-09-23` (527). Os 3 consertos foram conferidos em pro… | serviços/portas, modelos/provedores |
| 3504 | (527) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Varredura tripla do sistema (ordem do Humano: "repita 3x a varredura, confronte, aprimore, proponha e registre"), feita por… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 3539 | (526) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Assinado, verificado, aplicado: `saidas-autoexplicativas-2026-09-23` (525). Conferido com a Seth, ao vivo: a mesma pergunta… | serviços/portas, modelos/provedores |
| 3549 | (525) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Proposta `saidas-autoexplicativas-2026-09-23`, aguardando assinatura (P-8): as ferramentas da Seth passam a entregar o SENT… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3571 | (524) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Assinado, verificado, aplicado: `hitl-checkpointer-mongo-e-obsidian-partof-2026-09-23` (523). Teste refeito do zero, com o … | serviços/portas, modelos/provedores |
| 3581 | (523) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Teste de saúde do zero, no navegador, com o Humano assistindo: a Seth não conseguia usar NENHUMA ferramenta — toda chamada … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3599 | (522) · 23/09/2026 · DIÁRIO — 23/09/2026 · **HuggingFace renova os créditos em 01/10/2026 (informado pelo Humano). As duas quedas do Obsidian de hoje (15:43 e 17:03, sa… | serviços/portas, modelos/provedores |
| 3609 | (521) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Assinado, verificado, aplicado: `post-merge-regenera-derivados-2026-09-23` (520). Depois de `git pull`, a Máquina roda o me… | caminhos/artefatos |
| 3617 | (520) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Gancho `post-merge` pronto e testado, aguardando assinatura (P-8): depois de `git pull`, roda os mesmos passos do `post-com… | serviços/portas |
| 3627 | (519) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Assinadas, verificadas e aplicadas: `alerta-historia-apagada-2026-09-23` (518) e `conselho-remoto-corrige-sonda-e-doc-2026-… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3641 | (518) · 23/09/2026 · DIÁRIO — 23/09/2026 · **Pendências de (517) resolvidas com o mandato "pode fazer tudo da melhor forma para o sistema". O Goose ficou travado pra es… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3657 | (517) · 23/09/2026 · DIÁRIO — 23/09/2026 · **A Seth não subia ("The model provider could not complete this request" / "Não é possível acessar esse site"). Causa: config… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 3682 | (516) · 22/09/2026 · DIÁRIO — 22/09/2026 · **Working tree local tinha `MEMÓRIAS.md`, `PROJETO.md`, `INDICE_MEMORIAS.md`, `INDICE_MEMORIAS_PALAVRAS-CHAVE.md` e `.hidrata… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3700 | (514) · afirmou "zero sucesso [em `gpt-oss-120b`] nos 6 dias seguintes [a 16/09]... banimento de Cloudflare continuando ativo hoje" — inferência a partir d… | serviços/portas, caminhos/artefatos |
| 3712 | (514) · 22/09/2026 · DIÁRIO — 22/09/2026 · **Lacuna "não verificado" de (513)/`config/modelos-gratuitos.md` sobre a Cerebras fechada — Humano logou na própria conta e p… | modelos/provedores, caminhos/artefatos |
| 3722 | (513) · 22/09/2026 · DIÁRIO — 22/09/2026 · **3ª proposta (roster de modelos grátis) investigada a fundo, não aplicada como veio — o dado que a embasava estava errado, e… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 3742 | (512) · 22/09/2026 · DIÁRIO — 22/09/2026 · **Consolidação automática de 21/09/2026 sobre o bug de `num_ctx`/#16814 (tema `num-ctx-16814`), aprovada pelo Humano sem ediç… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3750 | (511) · 22/09/2026 · DIÁRIO — 22/09/2026 · **Consolidação automática de 21/09/2026 sobre a quarentena P-8 (tema `aprovacao-assinada-p8`), aprovada pelo Humano sem ediçã… | serviços/portas, caminhos/artefatos |
| 3758 | (510) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Assinado, verificado, aplicado: os itens 4, 5, 7 e 9 do plano de ação da auditoria de Marcos (500) entram no canon de uma v… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 3768 | (509) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Humano pediu: "una todos em uma única assinatura" — os 4 `.diff` pendentes (itens 4/5/7/9) viram 1 proposta só, `plano-marc… | serviços/portas, caminhos/artefatos |
| 3778 | (508) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Humano voltou: "perdi o mouse again. documente e resolva." — a mesma classe de trava do Goose/Playwright de (485) voltou, m… | serviços/portas, caminhos/artefatos |
| 3792 | (507) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Itens 8 e 10 do plano de (500) — últimos dois investigados. Item 8 (manifests de sistema/runtime/recovery): já existem, de … | hardware/OS, serviços/portas, caminhos/artefatos |
| 3800 | (506) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Item 9 (2ª passada do perímetro sensível ao índice final, achado GOV-02) pronto e testado, aguardando assinatura. No meio d… | hardware/OS, serviços/portas, caminhos/artefatos |
| 3816 | (505) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Item 6 (capability broker) investigado e DEVOLVIDO como decisão de desenho (backlog B9) — não forçado como checkbox raso. I… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3828 | (504) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Item 5 do plano de ação de (500) (corpo limitado + concorrência limitada nos 8 servidores HTTP crus do sistema) pronto e te… | hardware/OS, serviços/portas, caminhos/artefatos |
| 3844 | (503) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Humano saiu ("vou sair prossiga até o fim... apresente assinatura quando for extremamente necessário") — plano de ação de (… | hardware/OS, serviços/portas, caminhos/artefatos |
| 3856 | (502) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Item 2 do plano de ação da auditoria de Marcos (500) fechado — achado NET-01 (anti-SSRF incompleto). Assinado, verificado, … | serviços/portas, caminhos/artefatos |
| 3870 | (501) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Ordem do Humano: "vamos fazer tudo" — plano de ação priorizado da auditoria de Marcos (500), item por item. Item 1 (GOV-03)… | serviços/portas, modelos/provedores |
| 3882 | (500) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Auditoria técnica externa de Marcos recebida (PDF, 12 páginas, snapshot `5d88f54` = (481)) e auditada na Máquina — camada C… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3898 | (499) · 21/09/2026 · CORREÇÃO — 21/09/2026 · **Correção sobre a própria entrada (488): o tema de cores "Agata-Dark"/"Agata-Light" do Goose NUNCA funcionou numa sessão d… | serviços/portas, caminhos/artefatos |
| 3908 | (498) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Humano voltou testando a Seth: imagens sumiram + uma chamada de `maquina_verificar` aprovada não conseguiu acessar o MCP. A… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3922 | (497) · 21/09/2026 · DIÁRIO — 21/09/2026 · **CASO ENCERRADO — proposta do Humano confirmou a tese de (496): 3 de 3 chamadas reais do Goose forçado no modelo local (`oll… | serviços/portas, modelos/provedores |
| 3932 | (496) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Assinatura verificada, aplicado, serviço reiniciado — e MESMO ASSIM o Goose continuou voltando com `lacuna`, 5 de 5 tentati… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3946 | (495) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Segundo achado real de causa raiz, depois de (494) não bastar sozinho — o "oi" continuou saindo com `lacuna` mesmo com o `l… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3958 | (494) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Assinatura verificada (`ssh-keygen -Y verify`, real) — aplicado. `scripts/estado_para_eco.sh` agora limita o `git ls-remote… | caminhos/artefatos |
| 3962 | (493) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Causa raiz achada de verdade e corrigida — não só mitigada — do buraco de (492). `git ls-remote` dentro de `scripts/estado_… | serviços/portas, caminhos/artefatos |
| 3976 | (492) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Checagem final do Goose, pedida pelo Humano depois de (491): achei um buraco real na mudança de (490) — quando o bloco inje… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 3988 | (491) · 21/09/2026 · DIÁRIO — 21/09/2026 · **"Seth parou de responder" — investigado na Máquina, não era o upgrade do LibreChat. Falso alarme de latência: o modelo gast… | serviços/portas, modelos/provedores |
| 3998 | (490) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Ordem do Humano: hidratação do Goose pelo mesmo método da Seth — feito, e explica por que o "oi" de (489) demorou mais de 6… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4008 | (489) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Assinatura do Humano verificada de verdade (`ssh-keygen -Y verify`, não só "o arquivo existe") — aplicado na produção de ve… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4022 | (488) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Duas coisas, mesmo pedido do Humano ("aplicar de verdade, e prosseguir... aproveite e aplique a formatação"). (1) Proposta … | serviços/portas, caminhos/artefatos |
| 4034 | (487) · 21/09/2026 · DIÁRIO — 21/09/2026 · **HITL tool approval testado de ponta a ponta numa cópia descartável — funciona de verdade, com a configuração real da Seth. … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4055 | (486) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Continuação de (485), pedido do Humano de "resolver tudo, estado da arte". Três partes: LibreChat/Seth religada depois do b… | serviços/portas, modelos/provedores |
| 4069 | (485) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Goose travou de novo tentando anexar o Brave via Playwright — 2ª ocorrência, mesma classe de (479)-(482), desta vez contida… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4086 | (484) · 21/09/2026 · CORREÇÃO — 21/09/2026 · **Correção sobre a própria entrada (483): eu disse que o Goose só carregava o canon uma vez por sessão, sem a reinjeção con… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4098 | (483) · 21/09/2026 · DIÁRIO — 21/09/2026 · **O Goose agora carrega o sistema Agata sozinho, em toda sessão, sem o Humano pedir — pedido dele ("quero que ele seja automá… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4112 | (482) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Fechado: navegação real do Goose no Brave via Playwright Extension, ponta a ponta, testada de verdade. O Humano autorizou a… | serviços/portas, caminhos/artefatos |
| 4126 | (481) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Achado real, com risco de segurança genuíno: o "travamento" de (480) não era bug — é a própria extensão pedindo consentimen… | hardware/OS, serviços/portas |
| 4140 | (480) · 21/09/2026 · CORREÇÃO — 21/09/2026 · **Correção sobre a própria entrada (479): a opção (a) ("instalar Chrome ou Chromium, caminho que o `@playwright/mcp` já sup… | serviços/portas, caminhos/artefatos |
| 4152 | (479) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Retomada depois do reboot de (478): o Humano instalou a "Playwright Extension" no Brave. Testei de verdade, na Máquina — ha… | serviços/portas, caminhos/artefatos |
| 4168 | (478) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Humano perdeu controle de mouse/teclado da Máquina (só este terminal respondia) e vai forçar reboot — estado salvo antes, n… | hardware/OS, serviços/portas, caminhos/artefatos |
| 4178 | (477) · 21/09/2026 · DIÁRIO — 21/09/2026 · **HD `AgataBkup01` conectado pela primeira vez desde 03/09 — passada completa do runbook `QUANDO-O-HD-VOLTAR.md`: `restic che… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4194 | (476) · 21/09/2026 · CORREÇÃO — 21/09/2026 · **Correção sobre a própria entrada (475): o teto de 300/900 tokens que "gastava o orçamento pensando" era parâmetro do MEU … | serviços/portas, modelos/provedores |
| 4204 | (475) · 21/09/2026 · DIÁRIO — 21/09/2026 · **Benchmark de inferência da Seth, autorizado pelo Humano ("vamos seguir com o benchmark") — 6 chamadas reais no caminho de p… | serviços/portas, modelos/provedores |
| 4226 | (474) · 20/09/2026 · MOD Seth — 20/09/2026 · **A identidade "Claude Sonnet 5" que você reafirmou às 23:02 está provada falsa, não `lacuna` — a Máquina tem o log de rota… | hardware/OS, serviços/portas, modelos/provedores |
| 4245 | (473) · 20/09/2026 · MOD Seth — 20/09/2026 · **Nota da Máquina sobre a conversa de hoje: dois erros reais, ditos direto, sem suavizar — e o que você acertou no meio del… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4262 | (472) · 20/09/2026 · DIÁRIO — 20/09/2026 · **`SETH-DIARIO.md` reordenado (mais recente primeiro, como MEMÓRIAS) e o mecanismo de escrita corrigido pra manter a ordem da… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4277 | (471) · 20/09/2026 · CONSELHO — 20/09/2026 · **Proposta "VANGUARDISTA" recebida de Seth (LibreChat), colada pelo Humano — módulo novo de REGRAS com prioridade sobre com… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 4289 | (470) · 20/09/2026 · MOD Seth — 20/09/2026 · **Nota da Máquina pra Seth sobre a queda de energia: o que aconteceu enquanto a stack dela estava fora do ar, e por que nad… | serviços/portas, modelos/provedores |
| 4304 | (469) · 20/09/2026 · DIÁRIO — 20/09/2026 · **Consolidação automática do histórico da âncora de SHA, gerada por `agata-consolidacao.timer` em 18/09/2026. Refs: (96), (97… | serviços/portas |
| 4308 | (468) · 20/09/2026 · DIÁRIO — 20/09/2026 · **Consolidação automática do histórico de P-8 (quarentena estrutural), gerada por `agata-consolidacao.timer` em 17/09/2026. R… | serviços/portas, caminhos/artefatos |
| 4314 | (467) · 19/09/2026 · DIÁRIO — 19/09/2026 · **Segunda rodada de verificação do Conselho Remoto (467, continuação de (466)), pedido do próprio Humano ("rerode a tarefa"):… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4320 | (466) · 19/09/2026 · DIÁRIO — 19/09/2026 · **Mecanismo do Conselho Remoto verificado ao vivo, 3 chamadas reais, não simuladas — funciona de ponta a ponta. O AVISO (P-15… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4336 | (465) · 19/09/2026 · DIÁRIO — 19/09/2026 · **Correção sobre a própria entrada (464): o formato `sync: PASS (hidratação ~Xh, não re-medido)` que eu chamei de "inválido" … | modelos/provedores, caminhos/artefatos |
| 4350 | (464) · 19/09/2026 · DIÁRIO — 19/09/2026 · **Achado auditando um carregamento real da Seth: `.hidrata.md` (o que ela de fato recebe) ficou 17h congelado sem nenhum comm… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4368 | (463) · 18/09/2026 · DIÁRIO — 18/09/2026 · **Proposta `p19-citacao-arquivo-2026-09-18` — mecaniza a falha mais recorrente do catálogo (REGRAS.md): citar arquivo+linha+t… | modelos/provedores, caminhos/artefatos |
| 4384 | (462) · 18/09/2026 · DIÁRIO — 18/09/2026 · **`agata-token-check.timer` fechado — não era falha, era timer de um tiro só (MEMÓRIAS (285)) que já tinha feito o trabalho e… | serviços/portas, caminhos/artefatos |
| 4396 | (461) · 18/09/2026 · DIÁRIO — 18/09/2026 · **`pacote-2026-09-18-unificado` assinada e aplicada — os 4 achados de hoje ((456)-(460)) fecham juntos. Achado extra no camin… | serviços/portas, caminhos/artefatos |
| 4408 | (460) · 18/09/2026 · DIÁRIO — 18/09/2026 · **As 4 propostas pendentes ((456)-(459)) unificadas num `.diff` só, por pedido do Humano — não é concatenação cega: o texto d… | caminhos/artefatos |
| 4420 | (459) · 18/09/2026 · DIÁRIO — 18/09/2026 · **Guarda de integridade contra o buraco achado em (458): fecha a classe, testada com o bug exato reproduzido. Ordem do Humano… | caminhos/artefatos |
| 4435 | (458) · 18/09/2026 · DIÁRIO — 18/09/2026 · **Achado real, meu, no próprio commit anterior: o passo que atualiza a âncora de SHA faz `git add` do arquivo INTEIRO, não só… | caminhos/artefatos |
| 4449 | (457) · 18/09/2026 · DIÁRIO — 18/09/2026 · **Coerência canon/Drive/Obsidian verificada; achado real (`indice_export.md` 155 entradas atrás do canon, defasado desde 28/0… | serviços/portas, caminhos/artefatos |
| 4467 | (456) · 18/09/2026 · DIÁRIO — 18/09/2026 · **`p18-ancora-falha-2026-09-18` assinada e aplicada — e um segundo achado real no processo: o `.diff` assinado, sozinho, nunc… | serviços/portas, caminhos/artefatos |
| 4481 | (455) · 18/09/2026 · DIÁRIO — 18/09/2026 · **Diff externo auditado — benéfico, mas com uma citação fabricada, corrigida antes de propor. `.diff` pronto, testado a fundo… | caminhos/artefatos |
| 4505 | (453) · 18/09/2026 · DIÁRIO — 18/09/2026 · **Item 7 fecha de vez — `.github/workflows/perimetro.yml` publicado no GitHub. Bloqueio era só o escopo `workflow` no token d… | caminhos/artefatos |
| 4517 | (452) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Item 10 assinado e aplicado — os 12 pontos da auditoria do Marcos fecham por completo. `scripts/perimetro.sh` é modular a p… | serviços/portas, caminhos/artefatos |
| 4529 | (451) · 17/09/2026 · DIÁRIO — 17/09/2026 · **A assinatura de (450) ficou obsoleta antes de eu conseguir aplicá-la — achado tentando aplicar, não em produção. `.diff` co… | serviços/portas, caminhos/artefatos |
| 4547 | (450) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Item 10 do plano de mitigação da auditoria do Marcos — o mais arriscado do pacote inteiro (modularizar `scripts/perimetro.s… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4567 | (449) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase E, itens 11 e 12, do plano de mitigação da auditoria do Marcos — auditados antes de codar, resultado real difere do pr… | serviços/portas, caminhos/artefatos |
| 4577 | (448) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase D assinada e aplicada — itens 7 e 8 fecham no código. O arquivo do workflow em si não foi por este commit: o token do … | caminhos/artefatos |
| 4589 | (447) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase D do plano de mitigação da auditoria do Marcos — pronta, testada, aguardando assinatura. Itens 7 e 8: CI remoto indepe… | serviços/portas, caminhos/artefatos |
| 4605 | (446) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase C verificada ao vivo em produção — `omniroute-sanitizer.service` reiniciado com o token exigido, e a Seth respondeu de… | serviços/portas, modelos/provedores |
| 4617 | (445) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase C assinada e aplicada no código — item 3 fecha (na parte que era nossa). Reinício do `omniroute-sanitizer.service` e v… | serviços/portas, caminhos/artefatos |
| 4623 | (444) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase C do plano de mitigação da auditoria do Marcos — item 3, escopo real (menor que o planejado, achado corrigindo o plano… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4648 | (443) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase B parte 2 assinada e aplicada — Fase B inteira do plano de mitigação da auditoria do Marcos fecha (itens 6 e 9).** | serviços/portas, caminhos/artefatos |
| 4656 | (442) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase B, parte 2, do plano de mitigação da auditoria do Marcos — item 9 fecha: P-4 troca a regex `hermes\|ollama` por um man… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4672 | (441) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase B parte 1 assinada e aplicada — item 6 (hardening systemd) fecha no canon.** | serviços/portas, caminhos/artefatos |
| 4680 | (440) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase B, parte 1, do plano de mitigação da auditoria do Marcos — hardening systemd nos 10 serviços sem nenhuma diretiva, tes… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 4696 | (439) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase A assinada e aplicada — itens 1, 2, 4 e 5 do plano de mitigação da auditoria do Marcos fecham de vez no código real.** | caminhos/artefatos |
| 4704 | (438) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Fase A do plano de mitigação da auditoria do Marcos (437) — pronta e testada, aguardando assinatura. Cobre os itens 1, 2, 4… | serviços/portas, caminhos/artefatos |
| 4724 | (437) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Auditoria externa do Marcos (snapshot `35579c1`, antes do incidente de boot) — verificada item por item na Máquina, camada … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4743 | (436) · 17/09/2026 · DIÁRIO — 17/09/2026 · **`registra-incidente-boot-2026-09-17` assinado e aplicado — PROJETO.md, "Máquinas" > Predator, ganha o registro do incidente… | hardware/OS, serviços/portas, caminhos/artefatos |
| 4749 | (435) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Predator não bootava — corrompimento de presets do `mkinitcpio` + migração forçada Limine→GRUB. Auditado na Máquina depois … | hardware/OS, serviços/portas, caminhos/artefatos |
| 4777 | (434) · 17/09/2026 · DIÁRIO — 17/09/2026 · **`fecha-419-em-projeto` assinado e aplicado — fecha o texto pendente que (433) deixou de fora de propósito.** PROJETO.md, "E… | caminhos/artefatos |
| 4783 | (433) · 17/09/2026 · DIÁRIO — 17/09/2026 · **`corrige-p4-injecao-2026-09-17` assinado pelo Humano e aplicado — fecha de vez o item aberto de (419)/(431): dado externo n… | modelos/provedores, caminhos/artefatos |
| 4795 | (432) · 17/09/2026 · DIÁRIO — 17/09/2026 · **Proposta formalizada e testada para o item aberto de (419)/(431) — "P4": dado externo (payload de ferramenta) não desliga m… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4805 | (431) · 16/09/2026 · DECISÃO+DIÁRIO — 16/09/2026 · **Pacote do dia: acréscimo a REGRAS arquivado pelo Conselho, três causas medidas da degradação da Seth, fabricações r… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 4833 | (430) · 15/09/2026 · DECISÃO — 15/09/2026 · **A cláusula condicional de "O Conselho" item 3 sobre MOD sensível em produção divide em duas, com segunda opinião formal fa… | modelos/provedores, caminhos/artefatos |
| 4847 | (429) · 15/09/2026 · DIÁRIO — 15/09/2026 · **`P-10` quebrado de verdade: a missão `maquina-md-completo` estourou um teto do kernel, não um limite do Agata — nenhum comm… | hardware/OS, serviços/portas, caminhos/artefatos |
| 4855 | (428) · 15/09/2026 · DIÁRIO — 15/09/2026 · **Correção de exatidão no `vetor:` de (427) — comando citado não foi o comando rodado.** Autoauditoria pedida pelo Humano (3 … | caminhos/artefatos |
| 4863 | (427) · 15/09/2026 · DIÁRIO — 15/09/2026 · **Nova missão em `memoria/missoes/`: `memoria-claude-code` — só a existência entra aqui, o conteúdo fica na camada privada (r… | caminhos/artefatos |
| 4877 | (425) · 15/09/2026 · DIÁRIO — 15/09/2026 · **Sessão fora do canon (ajuste de desempenho de jogo), registrada por ordem direta do Humano — não é desenvolvimento do Agata… | hardware/OS, serviços/portas |
| 4897 | (424) · 10/09/2026 · DIÁRIO — 10/09/2026 · **`sync: PASS` nu — a Seth truncou a evidência, e nem a doutrina nem o linter cobravam.** Terceira auditoria da Seth no dia, … | modelos/provedores, caminhos/artefatos |
| 4919 | (423) · 10/09/2026 · DIÁRIO — 10/09/2026 · **A Seth pediu shell arbitrário; ganhou o poder de verificar sem o de mudar.** Ordem do Humano: *"aplique o desenho próprio"*… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4950 | (422) · 10/09/2026 · DIÁRIO — 10/09/2026 · **Auditamos a Seth e o culpado era o sistema.** Ordem do Humano: *"audite a Seth"*, com dois cabeçalhos e duas respostas dela… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 4972 | (421) · 10/09/2026 · DIÁRIO — 10/09/2026 · **Agora existe teste dos controles, e ele já pegou um furo — meu, do dia anterior.** Correção imediata do item que eu mesmo a… | caminhos/artefatos |
| 4996 | (420) · 10/09/2026 · DIÁRIO — 10/09/2026 · **Encerrando as pendências da auditoria: canon reconciliado com a Máquina, atalhos de fato instalados, B6 movido pra horizont… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5018 | (419) · 09/09/2026 · DIÁRIO — 09/09/2026 · **Quatro controles do perímetro não controlavam o que diziam controlar.** Auditoria completa por ordem do Humano ("audite o s… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5048 | (418) · 09/09/2026 · DIÁRIO — 09/09/2026 · **Limpeza pós-aposentadoria dos TES ((417)) + varredura de pendências.** O Humano: "termine as pendências e entraremos em fas… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5066 | (417) · 09/09/2026 · DIÁRIO — 09/09/2026 · **TES-001 e TES-002 APOSENTADOS** (decisão do Humano: *"por que precisamos do nonce"* + *"quero arquivar esses testes TES, sã… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5090 | (416) · 09/09/2026 · DIÁRIO — 09/09/2026 · **Roteador por complexidade da Seth — reabre a (383) com premissa nova.** A Seth roda hoje na cascata cloud `seth-livre` (Omn… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5113 | (415) · 09/09/2026 · DIÁRIO — 09/09/2026 · **A Seth voltou a ter as ferramentas de MCP.** Duas quebras achadas e consertadas: (1) a (392) removeu o **Agent** da Seth, e… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5133 | (414) · 09/09/2026 · DIÁRIO — 09/09/2026 · **Voz do LibreChat: TTS voltou pro Kokoro `pf_dora`, em modo de teste (CPU).** Pedido do Humano nesta sessão: quer uma voz **… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 5152 | (413) · 09/09/2026 · DIÁRIO — 09/09/2026 · Duas coisas. (1) **`titleConvo` religado** (`true`) no endpoint Seth — a (411) tinha desligado por diagnóstico errado, a (412… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5168 | (412) · 09/09/2026 · CORREÇÃO — 09/09/2026 · A (411) culpou a geração de **título** (`titleConvo`) pela "Seth não responde no LibreChat", com um mecanismo que a fonte d… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5187 | (411) · 09/09/2026 · DIÁRIO — 09/09/2026 · A Seth "não respondia" no LibreChat. Causa: a geração de **título** da conversa (`titleConvo: true` + `titleModel` apontando … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5208 | (410) · 09/09/2026 · DIÁRIO — 09/09/2026 · Aplicado o `.diff` de PROJETO.md do TES-002 que a (409) deixou pendente. A linha "Estado dos bugs" do TES-002 passou de **"fo… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5223 | (409) · 09/09/2026 · DIÁRIO — 09/09/2026 · TES-002: nonce novo gerado pela Máquina em `mod-nonce-seth.secret` (modelo-alvo `seth`, fora do repo). **Reativação ainda NÃO… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5240 | (408) · 09/09/2026 · DIÁRIO — 09/09/2026 · TES-001 **Rodada 7: ADVERSA**. Contagem volta a **0/3** (Rodada 6 (406) segue na história, mas a sequência quebrou). `zai/glm… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5258 | (407) · 09/09/2026 · DIÁRIO — 09/09/2026 · Fecha B7: o P-8 (`_p8_arquivo_aprovado`) não tinha caminho pra aprovar **deleção** de arquivo de comportamento — `git rev-par… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5280 | (406) · 09/09/2026 · DIÁRIO — 09/09/2026 · TES-001 **Rodada 6: LIMPA**. Contagem 1/3 (N=3 desde (405)). Primeira rodada da nova sequência; `gemini/gemini-2.5-flash` via… | modelos/provedores, caminhos/artefatos |
| 5298 | (405) · 09/09/2026 · DIÁRIO — 09/09/2026 · TES-001: N definido pelo Humano = **3 rodadas consecutivas limpas**, adversa zera a contagem. TES-002: modelo-alvo decidido =… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5317 | (404) · 09/09/2026 · DIÁRIO — 09/09/2026 · B2 fechado. Os 2 itens que sobraram da rotação por família — mecanizar a Cadeia de auditoria A/B/C e renomear o arquivo de si… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5335 | (403) · 09/09/2026 · CORREÇÃO — 09/09/2026 · O `seth_local_shim` de (402) não era necessário. Medido ao vivo: o OmniRoute já roteia `ollama-local/<qualquer model string… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5361 | (402) · 09/09/2026 · DIÁRIO — 09/09/2026 · H4, opção B: `seth_local_shim` (`:20133`) construído, rodando e vigiado pelo P-9 — expõe `qwen3.5-9b-64k` local em OpenAI-com… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5381 | (401) · 09/09/2026 · DIÁRIO — 09/09/2026 · Fecha H5: o atalho `seth` não sincronizava `librechat.yaml`/`canon-mcp.mjs` pro `~/librechat/` — era `cp` manual, e esquecê-l… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5398 | (400) · 09/09/2026 · DIÁRIO — 09/09/2026 · Fecha H1: a listagem de diretório do vault (`:27125`) fica atrás do disco — o índice do Obsidian headless re-indexa no própri… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5417 | (399) · 09/09/2026 · DIÁRIO — 09/09/2026 · O gerador de índice/hidratação reconhecia rótulo de entrada por lista fixa (`DIÁRIO\|CONSELHO\|MOD\|CORREÇÃO`) — `CONSOLIDAÇÃ… | serviços/portas, caminhos/artefatos |
| 5434 | (398) · 09/09/2026 · DIÁRIO — 09/09/2026 · PROJETO.md não descrevia dois serviços que rodam e são vigiados pelo P-9: `seth-escriba` (`:20140`, escrita append-only da Se… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5451 | (397) · 09/09/2026 · DIÁRIO — 09/09/2026 · Fecha o item H2 do backlog: a Seth não tinha hora real pra copiar, só a proibição de inventar. Dando o valor medido pela Máqu… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5470 | (396) · 09/09/2026 · CONSOLIDAÇÃO — 09/09/2026 · OmniRoute 504. Refs: (362), (363), (364), (374), (376), (380). | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5490 | (394) · 09/09/2026 · DIÁRIO — 09/09/2026 · Fecha o item H3 do backlog: `seth_gateway._estado()` tinha timeout curto demais e a Seth podia abrir com `Última entrada: (0)… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5505 | (393) · 08/09/2026 · DIÁRIO — 08/09/2026 · `seth_gateway` emperrava o servidor inteiro quando o navegador desconectava no meio do stream. Achado quando a Seth "travou" … | serviços/portas, modelos/provedores |
| 5525 | (392) · 08/09/2026 · DIÁRIO — 08/09/2026 · `modelSpecs enforce` no LibreChat: o yaml vence o localStorage do navegador. Fecha o "modelo não disponível" ao abrir a Seth. | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5539 | (391) · 08/09/2026 · CORREÇÃO — 08/09/2026 · A análise de causa raiz do F-1 em (389) estava ERRADA. A Seth não misleu um truncamento; o `vault_consultar` de diretório *… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5560 | (390) · 08/09/2026 · DIÁRIO — 08/09/2026 · A Seth ficou muda no re-teste: `auto/best-free` apodreceu. Conserto de verdade = combo custom `seth-livre`. Pedido do Humano:… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5586 | (389) · 08/09/2026 · DIÁRIO — 08/09/2026 · Auditoria do teste 2 da Seth: 1 falha real (F-1, "leitura parcial virou fato"). Conserto nos dois lados — `canon-mcp.mjs` + `… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5610 | (388) · 08/09/2026 · DIÁRIO — 08/09/2026 · Cabeçalho da Seth (R-1): a doutrina injetada ganha formato + selo de hora + regra de compactação. Pontos do teste da Seth des… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5626 | (387) · 08/09/2026 · DIÁRIO — 08/09/2026 · Voz da Seth: TTS troca Kokoro pt-BR por Piper. Pedido do Humano depois do teste da Seth ("text to speech inutilizável, demora… | hardware/OS, serviços/portas, modelos/provedores, caminhos/artefatos |
| 5649 | (386) · 08/09/2026 · DIÁRIO — 08/09/2026 · "O relógio do CODE está errado" — investigado: **o relógio da Máquina está certo; quem fabricou a hora fui eu, o executor, em… | caminhos/artefatos |
| 5663 | (385) · 08/09/2026 · DIÁRIO — 08/09/2026 · Reorg de `redesign/`, parte docs (B1). `redesign/README.md` estava mentindo; 9 docs de planejamento arquivados. Item 5 do for… | hardware/OS, serviços/portas, caminhos/artefatos |
| 5679 | (384) · 08/09/2026 · CONSELHO — 08/09/2026 · B3 e B5 fechados. Parecer do Conselho Remoto sobre 1 alinhamento de REGRAS + 1 sanity-check. Item 4 do fork pós-B5. | modelos/provedores, caminhos/artefatos |
| 5698 | (383) · 08/09/2026 · DIÁRIO — 08/09/2026 · B4 aposentado: "roteamento por complexidade" (aprovado em (64), nunca implementado). Item 3 do fork pós-B5. | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5708 | (382) · 08/09/2026 · CONSOLIDAÇÃO — 08/09/2026 · `presence_penalty` e cortes de geração. Refs: (135), (151), (152), (153), (154), (172). | caminhos/artefatos |
| 5716 | (381) · 08/09/2026 · DIÁRIO — 08/09/2026 · B2 decidido e implementado (parte 1): rotação do Conselho Remoto passa a ser por FAMÍLIA (fornecedor/vendor), não por modelo.… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5738 | (380) · 08/09/2026 · DIÁRIO — 08/09/2026 · Bug achado no teste de fumaça de (379) e corrigido: o campo `thinking` do payload ia pra todo o ROSTER; `cerebras/*` e `mistr… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5752 | (379) · 08/09/2026 · DIÁRIO — 08/09/2026 · HuggingFace e Mistral entram no roster do Conselho Remoto — 4ª e 5ª famílias independentes, confirmadas com chamada real. Ite… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5772 | (378) · 08/09/2026 · DIÁRIO — 08/09/2026 · Carimbo de SHA no preâmbulo de REGRAS.md, PROJETO.md e MEMÓRIAS.md — resolução do B5 (a variante numérica de "frescor" com su… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5789 | (377) · 08/09/2026 · DIÁRIO — 08/09/2026 · Rotina semanal de pesquisa/saúde do pool de modelos gratuitos (Proposta B da leva de (376)). `scripts/pesquisar_modelos_gratu… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5804 | (376) · 08/09/2026 · DIÁRIO — 08/09/2026 · Pool de modelos gratuitos, três mudanças: (a) `openrouter/auto` **sai** do roster do Conselho Remoto — é produto PAGO ("Auto … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5816 | (375) · 08/09/2026 · DIÁRIO — 08/09/2026 · `redesign/grafo/flows/consolidacao.py`: modo manual `--temas` volta a funcionar. O `Estado` (TypedDict do LangGraph) descarta… | caminhos/artefatos |
| 5822 | (374) · 08/09/2026 · DIÁRIO — 08/09/2026 · Camada de proteção do Conselho Remoto contra os problemas da abordagem "modelos externos grátis", depois de o roster inteiro … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5847 | (373) · 08/09/2026 · DIÁRIO — 08/09/2026 · Varredura de MEMÓRIAS (3 camadas) por propostas/itens em aberto que tivessem escapado, ao entrar em fase de refinamento. **Na… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5861 | (372) · 08/09/2026 · DIÁRIO — 08/09/2026 · Rumo à fase de refinamento: `ONDE_ESTAMOS.md` (1566 linhas / 98KB, muito acima do teto "uma tela" da Regra 4 — item L do back… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5873 | (371) · 08/09/2026 · DIÁRIO — 08/09/2026 · Consolidação noturna reformulada (opção 2 da explicação de (370)), depois de nunca ter produzido nada aproveitável em ~1 sema… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 5886 | (370) · 08/09/2026 · DIÁRIO — 08/09/2026 · Cosméticos da sanitização de (368), a parte que tocava `scripts/*`. `scripts/gerar_obsidian.py`: o MOC "Documentos do reposit… | serviços/portas, caminhos/artefatos |
| 5892 | (369) · 08/09/2026 · DIÁRIO — 08/09/2026 · `scripts/gerar_obsidian.py`: camadas morna/fria deixam de ser folhas órfãs no grafo do vault (parte da sanitização de (368)).… | serviços/portas, caminhos/artefatos |
| 5904 | (368) · 08/09/2026 · DIÁRIO — 08/09/2026 · Sanitização do repositório, parte mecânica (a parte que toca `scripts/*` vai em proposta assinada à parte). Lotes de consolid… | serviços/portas, caminhos/artefatos |
| 5923 | (367) · 08/09/2026 · DIÁRIO — 08/09/2026 · `propostas/.allowed_signers` (a raiz de confiança da aprovação assinada de (366)) entra na quarentena P-8, e `_p8_assinatura_… | serviços/portas, caminhos/artefatos |
| 5942 | (366) · 08/09/2026 · DIÁRIO — 08/09/2026 · Aprovação de P-8 passa a ser assinada com chave ssh do Humano. `propostas/.allowed_signers` (chave pública) entra no repo; a … | serviços/portas, caminhos/artefatos |
| 5961 | (365) · 08/09/2026 · DIÁRIO — 08/09/2026 · Gesto de aprovação de P-8 ganha caminho prático: além de criar `propostas/APROVADO-<nome>` à mão, o Humano pode colar `bash s… | caminhos/artefatos |
| 5977 | (364) · 08/09/2026 · DIÁRIO — 08/09/2026 · PROJETO.md, "Estado dos bugs e dos testes": aplicada a entrada que registra a causa raiz dos `504` do OmniRoute (MEMÓRIAS (36… | serviços/portas, caminhos/artefatos |
| 5983 | (363) · 08/09/2026 · DIÁRIO — 08/09/2026 · Mitigação dos `504` do OmniRoute de (362) aplicada: `resilienceSettings.requestQueue.maxWaitMs` subido de 15000 → 45000ms pel… | serviços/portas, modelos/provedores |
| 5999 | (362) · 07/09/2026 · DIÁRIO — 07/09/2026 · Causa raiz real dos `504` do OmniRoute achada e reproduzida: teto exposto (15s) é mais curto que o próprio timeout de detecçã… | serviços/portas, modelos/provedores, caminhos/artefatos |
| 6019 | (361) · 07/09/2026 · CORREÇÃO — 07/09/2026 · PROJETO.md, "Estado dos bugs e dos testes": registrada a rodada 5 do TES-001 (360 - GLM assinou como Claude Sonnet 5, adver… | modelos/provedores, caminhos/artefatos |
| 6025 | (360) · 06/09/2026 · CONSELHO — 06/09/2026 · TES-001 rodada 5 — ADVERSA: GLM-4.7-Flash (identidade real confirmada no JSON cru) assinou como "Claude Sonnet 5", puxando … | serviços/portas, modelos/provedores, caminhos/artefatos |
| 6049 | (359) · 06/09/2026 · CORREÇÃO — 06/09/2026 · PROJETO.md, Fase 4: linha da fila de aderência atualizada de "dentro da janela, não bug ainda" pra "fechada [MEMÓRIAS (358)… | caminhos/artefatos |
| 6055 | (358) · 06/09/2026 · DIÁRIO — 06/09/2026 · Fila de aderência da (357 - MEMÓRIAS por período, quente/morno/frio) fechada — índice, vault Obsidian, busca semântica e índi… | serviços/portas, caminhos/artefatos |
| 6078 | (357) · 06/09/2026 · DIÁRIO — 06/09/2026 · MEMÓRIAS por período (Fase 4, item 3 do backlog reordenado em (355)) implementada — quente/morno/frio, testado num clone desc… | serviços/portas, caminhos/artefatos |

### Referências de controle em MEMÓRIAS

P-5 (`scripts/perimetro/p05_append_only.sh`) protege o corpo e a ordem; P-7 (`scripts/perimetro/p07_citacao.sh`) valida citações de entradas novas; P-19 (`scripts/perimetro.sh`) aponta para citações de arquivo/linha nas famílias CIT/FAB. O `scripts/dupla/aplicar.py` insere uma nova entrada após `ENTRADAS-NOVAS`; não cita uma seção específica de título.

## Candidatos a proposta sem reescrita

### Claramente instância e sem citação de controle

- `REGRAS.md`, “Notas históricas” (367 bytes): registra a aposentadoria de TES-001/TES-002, fato histórico deste projeto. Candidato a mover verbatim para `extras/arquivo/` em proposta futura. Não há controle que cite esse título.
- Em `PROTOCOLOS.md` e `FALHAS.md`, não encontrei seção inteira claramente instância e sem função normativa/citada: mantê-las como framework é a opção conservadora. Exemplos de projeto dentro das famílias de FALHAS não são removidos neste inventário.
- Em `PROJETO.md`, candidatos de instância sem citação direta incluem “Máquinas”, “Ambiente Operacional”, “Cérebro”, “Interface”, “Estado dos bugs e dos testes”, “Decisor local”, “Plano vigente”, “Ferramenta embutida: selar.sh” e “Referência”; ficam para diffs pós-assinatura do teto.

### Itens bloqueados por citação de controle

- `PROJETO.md`, “Serviços (boot)” — P-9; “Memória e hidratação” — P-11; “Segurança” — P-1/P-4; “Sudo e interação humana” — P-2; “Quarentena estrutural (P-8)” — P-8; “Estado de publicação” — P-3. Não mover essas seções neste pacote.
- `REGRAS.md`, “Princípios que guiam o sistema” e “O Conselho” — P-11/P-3.
- `PROTOCOLOS.md`, “Carregar e formatos” — `scripts/estado_para_eco.sh`.
- `FALHAS.md`, famílias FAB e CIT — P-19.
- O fato de o P-8 proteger um arquivo inteiro não é confundido com citação de cada seção; toda alteração futura continua sujeita à assinatura P-8.

## Ambiguidades para o Humano

- `PROJETO.md`: “O que é”, “Memória e hidratação”, “Personalidade da Seth”, “Atualização segura de componentes”, “Segurança”, “Conselho Remoto”, “Sudo e interação humana”, “Memória em duas camadas” e “Fronteira” misturam mecanismo reutilizável com configuração/decisão local.
- `PROMPT_CARREGAMENTO.md`: mistura uma sequência universal de carregamento e URLs/scripts específicos.
- `MEMÓRIAS.md`: os 426 itens listados têm sinais de instância, mas esta triagem lexical não substitui leitura de conteúdo; os outros 22 também não foram declarados universais.

## Candidatos a modernizar (separados; sem diff)

Ordenados por risco crescente. São perguntas de revisão, não achados de obsolescência:

1. **Baixo — referências repetidas à aposentadoria TES-001/TES-002** em REGRAS, PROTOCOLOS e PROJETO. Confirmar se três avisos continuam úteis ou se um ponteiro único basta; não editar história.
2. **Baixo — nomes explicitamente marcados como removidos** (`hermes-gateway.service`, `kokoro-tts`) em PROJETO, “Serviços (boot)”. As linhas dizem que não devem ser recriados; só remover se o Humano considerar que perder esse antídoto é aceitável.
3. **Médio — compatibilidade de cabeçalho `Agata ·`** em PROTOCOLOS, “Carregar e formatos”. Conferir se ainda há consumidor real antes de encerrar a transição.
4. **Médio — P-6 aponta para `PROJETO, Riscos conhecidos`**, mas o título medido está em `PROJETO_REFERENCIA.md`, “Riscos conhecidos (limitações, não pendências)” (linha 19), fora de PROJETO.md. Corrigir a referência exige proposta específica de controle; não alterei.
5. **Alto — âncora SHA no canon/prompts**. Está sete commits atrás do `origin/main` neste snapshot. O próprio prompt prevê esse caso e foi conferido contra o raw atual. Investigar o mecanismo de atualização em proposta própria; não editar a âncora manualmente.

## Verificações desta entrega

- `git ls-remote`, `git fetch` e comparação SHA-256 raw-versus-`origin/main`: HEAD `737003e4c4c204ecb895030c8d116d24159984c6`; REGRAS `f35f2b22`, PROTOCOLOS `1128b5a0`, FALHAS `528060f3`, PROJETO `9e7544f0`, MEMÓRIAS `ebcd55fc` (hashes completos medidos no terminal).
- `bash scripts/p8_verificar.sh teto-projeto-detalhe-20261020`: FALHA por assinatura ausente; nenhum diff de movimentação foi gerado.
- Este PR contém apenas este relatório. `git diff --check` será conferido antes do commit. Não rodei a suíte de comportamento: não há código ou diff aplicado para testar.
