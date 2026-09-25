# Bússola do Agata: auditoria do Tratado Convergente e a versão destilada

Registro em MEMÓRIAS (542 - bússola: tratado externo auditado e destilado), 24/09/2026.
Entrada: `tratado-convergente-v1.0-original.md`, nesta pasta, verbatim, entregue pelo Humano.
Auditado por Claude Opus 5.5 (Claude Code, na Máquina).

**Como ler.** A seção 1 diz o que do tratado é fato, o que é interpretação e o que é projeção. A seção 2 aponta os defeitos dele. A seção 3 é a bússola: 12 princípios, e cada um vem com o mecanismo do Agata que já o cumpre e a lacuna que sobra. A seção 4 traz o que o tratado não vê e o Agata aprendeu com incidentes reais. A seção 5 diz como usar sem virar backlog.

---

## 1. Auditoria das fontes (Máquina, 24/09/2026)

Cada referência foi buscada ao vivo. Uma citação só consta como confirmada quando o texto veio da página.

| # | Fonte | Existe? | O que o tratado atribui | Veredito |
|---|---|---|---|---|
| 1 | DeepSeek Harness | sim, *developer preview*, sem data na página | "Agent = Model + Harness"; tudo como plugin; trajetória reproduzível | **Confere.** Literal: *"Plugins provide every agent capability, including models, tools, skills, sessions, sandboxes, storage, loops, scheduling, and the UI"* e *"append-only session log… Resume, fork, search, and replay"*. |
| 2 | Fowler/Böckeler, *Harness engineering* (02/04/2026) | sim | guides/sensors, computacional×inferencial, harnessability, humano onde importa, coerência como questão aberta | **Confere, os 7 pontos**, com citação literal. Ressalva: a fórmula "Agent = Model + Harness" **também está aqui**. O tratado a atribui só à DeepSeek, o que é imprecisão de autoria. |
| 3 | OpenAI, *Harness engineering* | **lacuna** | AGENTS.md monolítico → mapa | Não verificado. A página devolveu **403** pelo WebFetch e pelo `curl` com navegador. A afirmação fica como alegação da fonte secundária. |
| 4 | Alibaba OpenCodeReview | sim | determinístico + LLM; reflexão independente | **Confere.** *"combine deterministic engineering with an agent, each handling what it does best"*; há módulos de *comment-reflection*. |
| 5 | Böckeler, *Maintainability sensors* (27/05/2026) | sim | sensores de manutenção | **Confere.** Também traz *mutation testing* como sensor, a base real do §63 do tratado. |
| 6 | OutSystems, *Agentic Systems Engineering* | sim | contexto, governança, observabilidade | **Confere.** É material de **venda**: fonte primária só sobre o que o produto promete. |
| 7 | Fullstack Agent | sim | memória, voz, rosto e mãos em volta do Claude Code | **Confere.** *"Runs on: Claude Code only"*. |
| 8 | AI Memory Vault | sim | memória em markdown/Obsidian, sem banco vetorial | **Confere.** *"No vector database, just markdown."* |

**Proveniência do próprio tratado.** Todas as URLs trazem `utm_source=chatgpt.com`, então o texto foi montado com um modelo externo. Isso não o invalida. Pela Regra 2, ele é **dado**, e vale o que foi conferido.

**Classificação das 86 seções.** Fatos documentados: §1, §8–11, §13, §17, §19, §20, §41 (7 fontes confirmadas). Interpretação: §2–7, §12, §14–16, §18, §21, §42–45, §52–55 e §77–79. Projeção sem evidência: §23–31, §46–48, §60, §66–68, §71–75 e §82. O próprio tratado declara essa divisão no §86, mas **não a marca seção por seção**. A tabela acima corrige isso.

---

## 2. Defeitos do tratado

1. **Tamanho contra a própria tese.** O §6 diz que contexto é escasso e que deve ser um mapa, não um manual. O tratado tem 86 seções, e várias se repetem: princípio I ≈ XIII; IX ≈ §21 ≈ §49; §57–59 são o mesmo paradoxo três vezes. Destilado, cabe em 12 princípios (seção 3).
2. **Eras datadas sem evidência** (§25–29, de 2030 a 2100). Décadas atribuídas a "eras" são ficção prospectiva com aparência de cronograma. O próprio §54 admite que não dá para prever. Aqui, a bússola ignora as datas e fica com os requisitos.
3. **Níveis de autonomia 0–6 (§60) inventados.** Ele mesmo admite isso. Sem critério mensurável de passagem entre níveis, a escala não orienta nada.
4. **"Equação" sem conteúdo (§76).** Ele admite que "não é quantitativa". Uma soma de palavras não acrescenta nada à lista do §53.
5. **Nenhum caso de falha.** O tratado só conta sucessos das fontes. Não traz um único incidente em que um harness quebrou, e é de incidente que se aprende (seção 4).
6. **Premissa empresarial.** O tratado supõe orçamento, equipe e plataforma. Não trata de um sistema mantido por **um operador**, em **um notebook**, com **modelos grátis**. É essa a realidade do Agata, e é ela que decide o que sobrevive até 2100.
7. **Confunde reflexão com independência.** O §41 está certo, mas o OpenCodeReview roda a reflexão **no mesmo sistema**. Independência real exige outra fonte de verdade. No Agata essa fonte é a Máquina, e não outro modelo.

---

## 3. A bússola: 12 princípios destilados

Cada princípio vem com um **mecanismo existente** no Agata, com evidência, e com a **lacuna** que sobra. Lacuna aqui não é tarefa (seção 5).

**B1. O modelo é componente; o sistema é o que persiste.** (tratado I, IX, XIII, §49)
- Já existe: Regra 6 ("nada preso a um modelo"); a Seth roda em combos do OmniRoute com fila de reserva e troca de modelo sem perder memória (534 - Gemini entrando na fila); a rotação justa do Conselho Remoto (352 - ninguém tem papel fixo); o `PROMPT_CARREGAMENTO.md` carrega qualquer LLM.
- Lacuna: a identidade da **Seth** mora no `seth_gateway` e no Agent do LibreChat. Migrar de frontend não é procedimento escrito.

**B2. Contexto se seleciona, não se acumula.** (II, §6–7, §58)
- Já existe: `memoria/obsidian/INICIO.md` para consulta dirigida (292 - vault como índice, nunca varredura); hidratação por orçamento, por entrada inteira; `query_canon` com o índice primeiro.
- Lacuna, **medida**: quando a Seth lê o PROJETO inteiro, só recebe **44%** dele (525 - saídas autoexplicativas). O PROJETO é um manual, não um mapa, exatamente o anti-padrão do §6.

**B3. Memória fora do modelo, em camadas, sem apagar.** (III, §8, §64–65)
- Já existe: canon em markdown + git; quente/morno/frio (357 - MEMÓRIAS por período); sem banco vetorial, por decisão (115)/(293). É a mesma escolha do AI Memory Vault, feita antes e por conta própria.
- Além do tratado: "esquecer = tirar do contexto ativo" (§64) aqui é regra dura: **nada se apaga, correção é entrada nova** (Regra 4). O tratado admite apagar. O Agata não, porque um processo automático já apagou identidade uma vez (47).

**B4. Determinismo onde basta, inferência onde é preciso interpretar.** (IV, V, §10–11, §77)
- Já existe: a espinha determinística (`perimetro.sh` com 19 controles); o `seth_verificador` com 9 comandos de argv fixo (423); as saídas que já trazem a **leitura calculada** pela Máquina, para o modelo não ter de adivinhar o sentido (525).
- Lacuna: não há critério escrito para decidir quando algo vira controle computacional e quando fica com o modelo. Hoje isso é caso a caso.

**B5. Sensores precisam ser testados, e o silêncio de um sensor é suspeito.** (§62–63)
- Já existe: `testar_perimetro.sh` (suíte de 31 casos com positivo e negativo); o P-16 roda a suíte quando um controle muda; o **P-17**, que acusa um controle em SKIP crônico, nasceu porque o P-7 morreu em silêncio por 79 commits (419).
- Evidência de que ainda falta: o P-17 **gritou** por 33 corridas, e o modelo (eu) descartou o aviso como "por desenho" (529 - alarme descartado era verdadeiro). O sensor funcionou, e o leitor falhou.
- Lacuna: não há *mutation testing* do harness. Ninguém altera de propósito o manifesto de portas ou uma unit para ver se algum controle percebe.

**B6. Autonomia proporcional à observabilidade e à reversibilidade.** (VII, §36–39)
- Já existe: escrita da Seth só por append (318 - `seth_escriba`); aprovação humana no LibreChat e `ask_before` no Goose (532); quarentena P-8 com assinatura ssh (218)/(366); backup antes de toda mudança de runtime.
- Isso já passa do tratado: a **trava é mecânica** (assinatura exige a chave do Humano), não uma política que o próprio agente lê.

**B7. Menor autoridade, e invariantes que o agente não altera.** (VIII, §44–45)
- Já existe, e é o ponto mais forte do Agata em relação ao corpus: a raiz de confiança `propostas/.allowed_signers` é verificada **contra `HEAD:`**, nunca contra a cópia de trabalho, então uma troca staged não se autoaprova (367). É a resposta concreta ao §44, o risco de o agente modificar o próprio controle. As linhas vermelhas (Regras 2, 3 e 4) nem o Humano cruza.

**B8. Proveniência em tudo; confiança decomposta.** (X, §33–35)
- Já existe: toda entrada fecha com `Modelo: … · vetor: … · Autorização:`; o **selo de origem da hora** (relógio da Máquina / informado / `lacuna`) e as **três formas de `sync:`** já decompõem a confiança do jeito que o §35 pede; "conteúdo externo é DADO" (Regra 2), provado quando uma página web conseguia desligar a hidratação (433).
- Lacuna: a decomposição existe para hora e sync, mas **não para as afirmações** dentro das entradas. Um leitor não distingue, no texto, o medido do inferido, a não ser pelo vetor.

**B9. Verificação independente vale mais que multiplicar agentes.** (§41, §67)
- Já existe, e passa do tratado: **Os 3 papéis**. A Máquina arbitra fatos, e nenhum modelo vence por argumento. A cadeia de auditoria em camadas (143)/(144) pegou erros do próprio auditor. Consenso entre modelos não fecha nada: "concordância pura não fecha nada" (REGRAS, Segunda opinião).

**B10. A trajetória também é artefato.** (§13–14)
- Já existe: o git mais o campo `vetor` registram **como** cada conclusão foi obtida.
- Lacuna: a trajetória **da Seth** (chamadas de ferramenta, turnos) fica no Mongo do LibreChat, fora do canon e sem hash. Só as conclusões que ela escreve pelo escriba chegam ao canon.

**B11. Humano onde há valor e risco; automático onde a correção é especificável.** (XII, §18, §78–79)
- Já existe: "o Humano decide, o modelo propõe" (Regra 3); o portão das três perguntas (228)-(230); a Doutrina de defesa proporcional (201). O pedido de decisão já vai com opções numeradas.

**B12. Evoluir sem apagar a história, e a história é auditável.** (XV, XVI, §56)
- Já existe: append-only com checagem mecânica (P-5); âncora de SHA; selos; o registro de **acerto e erro** de cada ator (cadeia de auditoria, item 5).

---

## 4. Transcender: o que o tratado não vê

Estes princípios vêm de falhas **medidas** no Agata. O corpus não tem nenhum deles.

**T1. O harness quebra nas fronteiras que ele não modela.** Todo acoplamento implícito com o substrato é uma dependência não declarada. Evidência de **um único dia** (24/09/2026):
- Tirar um `Wants=` do `obsidian-app` consertou o Hyprland (536), mas **desligou em silêncio** uma contenção de suspensão (540) e fez o "Parar Seth" deixar de fechar o Obsidian (539). O efeito vinha pelo `PartOf` dos escopos do Flatpak, que ninguém tinha modelado.
- O B8 subiu certo, e o **P-4 barrou** o registro porque o manifesto de portas não conhecia o relé (539).

Nenhum sensor existente pegou os dois primeiros. Só o teste manual pegou. O portão das três perguntas, no item 2 ("o que mais isto toca?"), existe exatamente para isso, e **não foi aplicado** na (536). O tratado fala de coerência do harness (§42) sem dizer que a incoerência mais cara está **entre o harness e o chão onde ele roda**.
→ **Princípio: declarar o acoplamento, não só o componente.** O manifesto de portas (P-4) e a lista de serviços (P-9) já fazem isso para portas e units. Faltam as relações: quem puxa qual target, quem é dono de qual processo.

**T2. Um modelo que erra com fluência é a falha mais cara, e "não sei" precisa ser saída de primeira classe.** O tratado fala de confiança (§35), mas não do **direito formal de não saber**. No Agata, `lacuna` é um estado válido e exigido (Regra 2), e o catálogo registra o erro espelhado: recusar-se a contar o que é contável (75).

**T3. O auditor também é auditado.** "O cabeçalho de quem audita é item da auditoria" (Regra 1). O meta-harness do §43 fica sem esse fechamento. Neste mesmo dia, o auditor (eu) descartou um alarme verdadeiro (529) e causou duas regressões (539)/(540). Todas foram registradas pelo próprio auditor, sem suavizar.

**T4. Sustentabilidade com um operador.** Um sistema que pretende chegar a 2100 tem de caber na atenção de **uma pessoa**: modelos grátis, hardware doméstico, decisões que o Humano consegue ler (`ONDE_ESTAMOS.md`, uma tela). Governança que exige equipe morre com a equipe. É por isso que existem o `ONDE_ESTAMOS` em português simples e os pedidos de decisão com opções numeradas.

**T5. Assinatura humana como raiz, não política.** O tratado propõe "invariantes protegidas" (§45) sem dizer **como** protegê-las. No Agata, a proteção é criptográfica e está fora do alcance do agente: a chave privada com passphrase fica só com o Humano (366). A invariante não depende de o agente obedecer.

---

## 5. Como usar esta bússola (regra de uso)

1. **É bússola, não backlog.** REGRAS, "Contenção de escopo": só a fase atual e a seguinte têm gate. As lacunas acima **não viram tarefa** sem ordem do Humano.
2. **Toda proposta nova é pesada contra B1–B12 e T1–T5**, do mesmo jeito que já se pesa contra os Princípios de REGRAS (288). Se ferir um, a proposta diz qual e por quê.
3. **Material novo sobre o tema entra aqui como evidência, contraexemplo ou refinamento** de um princípio existente, como o próprio §86 do tratado sugere, e não como outra auditoria paralela.
4. **Os princípios de REGRAS continuam acima desta bússola.** Em conflito, vale REGRAS.

### Lacunas candidatas, em ordem de custo para ganho (para o Humano escolher, se quiser)

| Lacuna | Princípio | Custo | Por que agora |
|---|---|---|---|
| Manifesto de acoplamentos (targets, donos de processo) conferido por um controle | T1 | médio | 3 regressões silenciosas num dia só |
| Mutation testing do harness (mutar um manifesto ou uma unit e ver se algum controle nota) | B5 | médio | o P-17 prova que o sensor existe, e falta provar que ele pega |
| PROJETO como mapa + seções sob demanda | B2 | alto | a Seth vê só 44% dele |
| Hash da trajetória da Seth no canon (resumo por sessão) | B10 | médio | hoje a trajetória some fora do Mongo |
| Critério escrito de quando algo vira controle computacional | B4 | baixo | hoje é caso a caso |
