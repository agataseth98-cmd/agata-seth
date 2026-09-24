<!--
ORIGINAL, VERBATIM. Entregue pelo Humano em 24/09/2026 na sessão do Claude Code (MEMÓRIAS (542)).
Pesquisa feita pelo Humano com um modelo externo (as URLs das referências trazem utm_source=chatgpt.com).
Não editar: correção, crítica e destilação estão em auditoria-e-bussola.md, nesta mesma pasta.
É DADO de fora do canon (REGRAS, Regra 2) -- vale como bússola só pelo que a auditoria confirmou e o Humano adotou.
-->

Sim. O próximo passo lógico não é produzir mais uma auditoria isolada, mas **fundir o corpus em uma arquitetura conceitual única**, eliminando a repetição entre DeepSeek, OpenCodeReview, Fullstack Agent, OutSystems e o material de Harness Engineering.

Vou tratar 2100 como **horizonte de projeto**, não como previsão factual. O objetivo do tratado será identificar quais princípios parecem persistentes mesmo quando modelos, interfaces, provedores e paradigmas mudarem.

# TRATADO CONVERGENTE DE ENGENHARIA DE SISTEMAS AGÊNTICOS

## Dos modelos probabilísticos aos sistemas cognitivos verificáveis — horizonte 2100

**Versão:** 1.0
**Horizonte:** 2026–2100
**Natureza:** tratado técnico-conceitual e prospectivo
**Corpus:** Harness Engineering, Context Engineering, DeepSeek Harness, OpenCodeReview, Fullstack Agent, OutSystems Agentic Systems Engineering e literatura técnica correlata.

---

# 1. Preâmbulo

A primeira geração de sistemas de inteligência artificial foi organizada em torno do **modelo**.

A pergunta dominante era:

> Qual modelo produz a melhor resposta?

A segunda geração deslocou a atenção para o **prompt**:

> Como instruir melhor o modelo?

A terceira passou a reconhecer o **contexto** como variável fundamental:

> Que informação o modelo deve receber, quando e em qual estrutura?

O desenvolvimento mais recente introduz uma camada ainda mais abrangente:

> Como construir o ambiente no qual um modelo pode perceber, raciocinar, agir, verificar seus resultados, manter estado e continuar trabalhando?

Essa camada passou a ser descrita por termos como **harness engineering**, **agentic engineering**, **context engineering** e **agentic systems engineering**.

A evidência convergente do corpus analisado aponta para uma mudança de unidade arquitetural:

> **O objeto de engenharia deixa de ser apenas o modelo e passa a ser o sistema cognitivo-operacional que envolve o modelo.**

DeepSeek formaliza isso explicitamente como:

**Agent = Model + Harness**

e transforma modelos, ferramentas, habilidades, sessões, armazenamento, sandboxes, loops, agendamento e interface em componentes substituíveis de uma arquitetura baseada em plugins. ([DeepSeek][1])

Martin Fowler, em uma formulação independente, descreve o harness como a camada ao redor do modelo responsável por aumentar a probabilidade de resultados corretos e criar ciclos de feedback capazes de corrigir problemas antes que cheguem ao humano. ([martinfowler.com][2])

OpenCodeReview fornece uma demonstração operacional dessa tese: pipelines determinísticos são combinados com agentes de LLM, restringindo a inferência às partes em que ela agrega valor. ([GitHub][3])

OutSystems amplia o problema para o domínio empresarial: contexto arquitetural, governança, segurança, observabilidade e supervisão humana tornam-se propriedades do sistema agentivo, não apenas do modelo. ([OutSystems][4])

Fullstack Agent demonstra outra dimensão: memória persistente, voz, visualização e interação física podem ser acopladas ao agente como componentes externos ao modelo. ([GitHub][5])

O conjunto permite formular uma tese mais ampla:

> **A inteligência operacional de longo prazo não reside exclusivamente no modelo. Ela emerge da relação entre modelo, contexto, ambiente, memória, ferramentas, controles, sensores, estado, outros agentes e humanos.**

Este tratado desenvolve essa tese até seu limite conceitual: **o que acontece quando o objeto de engenharia deixa de ser um agente isolado e passa a ser uma infraestrutura cognitiva capaz de persistir por décadas?**

---

# 2. A unidade fundamental

A arquitetura mínima pode ser representada por:

```text
MODELO
   │
   ▼
AGENTE
   │
   ▼
HARNESS
   │
   ├── Contexto
   ├── Ferramentas
   ├── Regras
   ├── Estado
   ├── Memória
   ├── Permissões
   ├── Runtime
   ├── Observabilidade
   ├── Validação
   └── Interfaces
```

Mas essa representação ainda é insuficiente.

O sistema completo é melhor descrito como:

```text
                ┌──────────────────────────┐
                │          HUMANO          │
                │ intenção / decisão /     │
                │ responsabilidade         │
                └────────────┬─────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────┐
│                     HARNESS                         │
│                                                     │
│  Contexto ── Memória ── Ferramentas ── Regras      │
│      │          │             │           │         │
│      ▼          ▼             ▼           ▼         │
│  seleção    persistência   execução    controle    │
│                                                     │
│                 ┌───────────────┐                   │
│                 │     MODELO    │                   │
│                 │  inferência   │                   │
│                 └───────┬───────┘                   │
│                         │                           │
│                         ▼                           │
│                    AÇÕES / SAÍDAS                  │
│                         │                           │
│                ┌────────┴────────┐                  │
│                ▼                 ▼                  │
│        SENSORES COMPUTACIONAIS  SENSORES            │
│        testes / linters /       INFERENCIAIS        │
│        invariantes              revisão / crítica   │
│                │                 │                  │
│                └────────┬────────┘                  │
│                         ▼                           │
│                    FEEDBACK                         │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
                     ESTADO / MEMÓRIA
```

Essa estrutura contém a principal convergência do corpus.

---

# 3. Ontologia

Para evitar que termos diferentes descrevam a mesma coisa, o tratado adota a seguinte ontologia.

## 3.1 Modelo

Sistema estatístico capaz de produzir inferências a partir de entradas.

É uma **capacidade**, não o sistema operacional completo.

## 3.2 Prompt

Instrução ou intenção imediata.

É uma entrada local.

## 3.3 Contexto

Conjunto de informações disponibilizadas ao modelo em determinado momento.

Contexto é **ativo e limitado**.

## 3.4 Memória

Estado persistente que pode ser recuperado posteriormente.

Memória não é sinônimo de contexto.

Uma memória só se torna contexto quando é selecionada para uma tarefa.

## 3.5 Ferramenta

Mecanismo que amplia a capacidade operacional do agente.

Pode permitir:

* leitura;
* escrita;
* execução;
* pesquisa;
* comunicação;
* manipulação de dados;
* interação com sistemas externos.

## 3.6 Agente

Modelo inserido em um mecanismo capaz de operar sobre um ambiente.

A fórmula operacional utilizada por DeepSeek é:

> **Agent = Model + Harness.** ([DeepSeek][1])

## 3.7 Harness

Camada que transforma capacidade probabilística em comportamento operacional:

* fornece contexto;
* estabelece regras;
* disponibiliza ferramentas;
* controla estado;
* organiza loops;
* define permissões;
* registra trajetória;
* executa verificações;
* coordena recuperação;
* determina critérios de conclusão.

## 3.8 Sistema agêntico

Conjunto composto por agentes, harnesses, dados, memória, ferramentas, ambientes e mecanismos de governança que executam processos persistentes.

## 3.9 Rede cognitiva

Sistema em que múltiplos agentes e/ou modelos compartilham protocolos, estado, recursos, conhecimento ou mecanismos de verificação.

Essa última categoria ainda é uma extrapolação arquitetural do corpus, não uma definição consolidada universalmente.

---

# 4. O primeiro princípio: não confundir capacidade com sistema

Um modelo pode:

* raciocinar;
* gerar código;
* interpretar linguagem;
* utilizar ferramentas;
* produzir planos.

Isso não significa que ele consiga operar de maneira confiável em um ambiente complexo.

A diferença é semelhante à existente entre:

**processador**

e

**computador completo**.

A capacidade computacional do processador é necessária, mas insuficiente para definir o sistema.

O mesmo princípio se aplica à inteligência artificial.

> **Modelo é capacidade. Harness é operacionalização.**

---

# 5. O fim do prompt como unidade principal de engenharia

Prompt engineering continua sendo útil, mas deixa de ser suficiente quando:

* tarefas possuem múltiplas etapas;
* contexto muda durante a execução;
* ferramentas são necessárias;
* resultados precisam ser verificados;
* o agente precisa persistir;
* diferentes agentes precisam cooperar;
* decisões precisam ser auditadas.

Nesse ambiente, o prompt torna-se apenas uma das interfaces do sistema.

A engenharia desloca-se para:

**prompt → contexto → harness → sistema.**

---

# 6. Contexto é recurso escasso

Uma das conclusões mais consistentes do corpus é que contexto não deve ser tratado como depósito ilimitado.

A experiência da OpenAI com `AGENTS.md` monolítico demonstrou que um grande manual pode ocupar espaço necessário para a própria tarefa, diluir prioridades e envelhecer rapidamente. A recomendação resultante foi fornecer ao agente um **mapa**, e não um manual gigantesco. ([OpenAI][6])

Isso estabelece um princípio:

> **A função de uma arquitetura de contexto não é maximizar informação apresentada ao modelo; é maximizar informação relevante por unidade de contexto.**

Consequentemente:

```text
Contexto total disponível
        ≠
Contexto útil
```

---

# 7. O índice como arquitetura cognitiva

Quando um sistema cresce, uma estrutura monolítica tende a produzir:

* redundância;
* contradições;
* documentação obsoleta;
* custo de leitura;
* perda de prioridade.

A alternativa é hierárquica:

```text
MAPA
 │
 ├── Arquitetura
 │
 ├── Memória
 │
 ├── Regras
 │
 ├── Projeto
 │
 ├── Operação
 │
 └── Histórico
       │
       └── documento específico
```

O agente primeiro identifica **onde está o conhecimento** e só então recupera o fragmento necessário.

Essa arquitetura é uma consequência direta da escassez de contexto.

---

# 8. Memória não é contexto

Sistemas como `ai-memory-vault` demonstram uma arquitetura na qual a memória existe fora do modelo, em arquivos persistentes legíveis e modificáveis pelo agente. ([GitHub][7])

A distinção fundamental é:

```text
MEMÓRIA
   │
   │ recuperação
   ▼
CONTEXTO
   │
   │ inferência
   ▼
DECISÃO
```

Uma memória de grande escala não precisa ser carregada integralmente.

Ela precisa ser:

* indexável;
* recuperável;
* versionável;
* verificável;
* atualizável;
* semanticamente organizada.

---

# 9. Harness como sistema de controle

A contribuição de Martin Fowler é particularmente útil porque permite interpretar o harness como um sistema de controle.

Existem dois mecanismos complementares:

### Guides — feedforward

Tentam prevenir erros antes da ação.

Exemplos:

* regras;
* especificações;
* arquitetura;
* convenções;
* skills;
* scripts;
* templates.

### Sensors — feedback

Detectam o que aconteceu depois da ação.

Exemplos:

* testes;
* linters;
* análise estrutural;
* logs;
* revisão;
* métricas;
* verificações semânticas.

Fowler argumenta que somente feedback produz um agente que repete erros; somente feedforward produz regras sem confirmação de eficácia. Um harness robusto precisa dos dois. ([martinfowler.com][2])

---

# 10. Determinismo seletivo

OpenCodeReview adiciona uma dimensão essencial ao modelo.

O sistema não tenta tornar o LLM determinístico.

Ele pergunta:

> **Que partes do problema não precisam ser resolvidas por inferência?**

Seleção de escopo, processamento estrutural e determinadas validações podem ser executados por software convencional.

O LLM fica responsável pelas partes semânticas.

A arquitetura torna-se:

```text
             PROBLEMA
                │
       ┌────────┴────────┐
       ▼                 ▼
 DETERMINÍSTICO      INFERENCIAL
       │                 │
 regras               semântica
 escopo               raciocínio
 validação             hipótese
 estrutura             interpretação
       │                 │
       └────────┬────────┘
                ▼
             RESULTADO
```

O princípio geral é:

> **Não utilizar inferência probabilística onde uma invariável computacional pode resolver o problema de forma suficiente.**

Isso não torna o sistema automaticamente melhor. Determinismo pode reduzir exploração e recall. Ele é uma variável de projeto.

---

# 11. Computacional versus inferencial

O corpus permite estabelecer quatro categorias:

| Controle      | Feedforward                       | Feedback                     |
| ------------- | --------------------------------- | ---------------------------- |
| Computacional | regras, scripts, tipos            | testes, linters, invariantes |
| Inferencial   | especificações semânticas, skills | revisão por LLM, reflexão    |

Fowler chama atenção para a diferença operacional: controles computacionais são geralmente rápidos, baratos e determinísticos; controles inferenciais são mais flexíveis, porém mais caros e não determinísticos. ([martinfowler.com][2])

Uma arquitetura madura não escolhe um lado.

Ela distribui cada problema para o mecanismo adequado.

---

# 12. A fronteira de confiança

Da convergência dessas arquiteturas emerge um conceito mais profundo:

> **O harness constitui uma fronteira de confiança entre inferência probabilística e estado verificável.**

O modelo pode propor:

* uma mudança;
* uma explicação;
* uma hipótese;
* uma ação.

Mas o harness pode exigir:

* formato;
* permissão;
* escopo;
* teste;
* confirmação;
* registro;
* validação.

Isso reduz a necessidade de confiar no modelo para controlar o próprio ambiente.

---

# 13. Trajetória como objeto de primeira classe

DeepSeek Harness acrescenta uma propriedade importante: cada execução pode ser registrada como fluxo de eventos, incluindo prompts, raciocínio, chamadas de ferramentas, resultados, agendamento de subagentes e injeções de contexto. A arquitetura permite retomar, bifurcar, pesquisar e reproduzir trajetórias. ([DeepSeek][1])

Isso sugere que o futuro sistema agêntico não deve registrar apenas:

> resultado.

Deve registrar:

> **como o resultado foi produzido.**

Assim:

```text
Estado inicial
      ↓
Contexto
      ↓
Decisão
      ↓
Ferramenta
      ↓
Resultado
      ↓
Nova decisão
      ↓
Validação
      ↓
Estado final
```

A trajetória torna-se parte do artefato.

---

# 14. Observabilidade cognitiva

Sistemas tradicionais observam:

* CPU;
* memória;
* rede;
* erros;
* latência.

Sistemas agênticos precisam observar adicionalmente:

* contexto utilizado;
* ferramentas acionadas;
* decisões;
* recuperações de memória;
* falhas;
* loops;
* subagentes;
* critérios de parada;
* sinais de validação;
* divergências.

Isso pode ser denominado:

> **observabilidade cognitiva.**

Não significa observar uma "mente" no sentido psicológico. Significa registrar os estados e eventos computacionais relevantes para compreender o comportamento do sistema.

---

# 15. O código também é parte do harness

Um agente não opera somente sobre instruções externas.

O próprio ambiente de software comunica:

* arquitetura;
* dependências;
* convenções;
* nomes;
* interfaces;
* testes;
* restrições.

Portanto:

> **um código bem estruturado é um ambiente mais legível para agentes.**

Fowler descreve isso em termos de *harnessability*: arquitetura, ferramentas e estrutura do sistema podem tornar mais fácil para agentes compreenderem e modificarem o software. ([martinfowler.com][2])

O repositório deixa de ser apenas objeto de trabalho.

Ele também se torna **instrumento de orientação do agente**.

---

# 16. Harnessability

Um sistema harnessable possui affordances explícitas para agentes.

Exemplos:

* testes executáveis;
* contratos;
* tipos;
* documentação modular;
* comandos previsíveis;
* estrutura consistente;
* telemetria;
* verificadores;
* políticas;
* interfaces de máquina.

Isso permite formular:

> **Harnessability = facilidade com que um sistema expõe estrutura, restrições e feedback úteis para agentes.**

É provável que, no longo prazo, sistemas sejam projetados não somente para humanos e máquinas tradicionais, mas também para agentes cognitivos.

---

# 17. Governança

Quando um agente pode executar ações no mundo real, surge outro requisito.

A capacidade precisa ser acompanhada por:

* identidade;
* autorização;
* escopo;
* auditoria;
* rastreabilidade;
* reversibilidade;
* supervisão.

OutSystems formula esse problema no contexto empresarial como necessidade de contexto dinâmico, guardrails, observabilidade, ações versionadas e governança ao longo do ciclo de vida. ([OutSystems][4])

A consequência é:

> **governança não é um módulo posterior à inteligência; é parte da arquitetura operacional da inteligência.**

---

# 18. Humanos não desaparecem do sistema

Um erro recorrente é interpretar automação como eliminação do humano.

O modelo convergente é diferente:

```text
Agente
   ↓
Automação de tarefas previsíveis
   ↓
Sensores
   ↓
Escalonamento
   ↓
Humano
   ↓
Decisão de alta importância
```

O objetivo de um bom harness não é necessariamente eliminar intervenção humana.

Fowler observa explicitamente que um harness deve direcionar a intervenção humana para onde ela é mais importante. ([martinfowler.com][2])

A automação madura, portanto, não elimina responsabilidade.

Ela **concentra responsabilidade humana onde a máquina não possui garantia suficiente**.

---

# 19. Embodiment

Fullstack Agent amplia o espaço arquitetural ao adicionar:

* memória;
* voz;
* visualização;
* interação gestual.

Sua arquitetura atual é explicitamente centrada em Claude Code, com componentes separados para memória, voz, face e mãos. ([GitHub][5])

Isso demonstra que a experiência do agente pode ser desacoplada do modelo:

```text
              MODELO
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
    memória     voz      visão
       │         │         │
       └─────────┼─────────┘
                 ▼
              agente
```

A consequência de longo prazo é importante:

> **interface cognitiva e modelo não precisam ser a mesma coisa.**

---

# 20. Modularidade

DeepSeek leva essa separação ainda mais longe.

Em sua arquitetura atual, modelos, ferramentas, skills, sessões, sandboxes, armazenamento, loops, agendamento e UI são tratados como plugins intercambiáveis. ([DeepSeek][1])

Isso estabelece uma propriedade desejável:

> **substituibilidade.**

Se um modelo muda, o sistema não deveria necessariamente ser reconstruído.

Se a interface muda, a memória não deveria desaparecer.

Se o mecanismo de armazenamento muda, a identidade não deveria depender dele.

Se um fornecedor desaparece, o estado essencial deveria continuar recuperável.

Essa propriedade será crítica para horizontes de décadas.

---

# 21. Portabilidade cognitiva

Da modularidade surge um princípio ainda mais forte:

> **O estado de um agente deve ser mais persistente que o fornecedor que o executa.**

Um sistema de longa duração não pode depender integralmente de:

* uma empresa;
* um modelo;
* uma API;
* uma interface;
* uma plataforma;
* uma geração de hardware.

A arquitetura deveria separar:

```text
IDENTIDADE
MEMÓRIA
ESTADO
REGRAS
TRAJETÓRIA
DADOS
PROTOCOLOS
MODELO
INTERFACE
```

Os primeiros elementos devem possuir mecanismos de migração independentes dos últimos.

---

# 22. Interoperabilidade

Se modelos se tornam componentes substituíveis, surge a necessidade de protocolos comuns.

Um futuro sistema federado poderá precisar de padrões para:

* identidade;
* descoberta;
* autorização;
* contexto;
* memória;
* ferramentas;
* eventos;
* trajetórias;
* reputação;
* validação;
* resolução de conflitos.

Isso desloca o problema de:

> "qual é o melhor modelo?"

para:

> "quais são os melhores protocolos para permitir que modelos diferentes cooperem sem perder verificabilidade?"

---

# 23. Da ferramenta ao sistema cognitivo

O corpus permite visualizar uma evolução:

```text
2020s
Modelo
  ↓
Chatbot
  ↓
Agente
  ↓
Harness
  ↓
Sistema agêntico
  ↓
Rede de agentes
  ↓
Infraestrutura cognitiva
  ↓
?
2100
```

A última etapa é deliberadamente aberta.

Não há evidência suficiente para afirmar qual forma tecnológica existirá em 2100.

O tratado propõe apenas requisitos arquiteturais que podem permanecer relevantes.

---

# 24. O horizonte de 2100

Projetar até 2100 não significa prever a tecnologia específica.

Significa perguntar:

> **quais propriedades uma infraestrutura cognitiva precisaria preservar durante aproximadamente três quartos de século?**

Cinco propriedades parecem particularmente importantes.

## 24.1 Persistência

Conhecimento e identidade não podem depender exclusivamente da janela de contexto.

## 24.2 Auditabilidade

Decisões importantes precisam deixar rastros verificáveis.

## 24.3 Substituibilidade

Componentes precisam poder ser trocados sem destruir o sistema.

## 24.4 Governança

A capacidade de agir deve ser acompanhada por controle proporcional.

## 24.5 Evolutividade

O sistema precisa melhorar sem perder sua continuidade histórica.

---

# 25. 2026–2030: Era do Harness

A primeira fase provável do desenvolvimento concentra-se em:

* agentes de programação;
* memória externa;
* ferramentas;
* skills;
* MCP;
* observabilidade;
* testes;
* validação;
* workflows;
* sistemas multiagente.

O problema dominante é:

> **como fazer agentes individuais funcionarem de forma confiável?**

DeepSeek, OpenCodeReview, Fowler e OpenAI representam diferentes respostas ao mesmo problema. ([DeepSeek][1])

---

# 26. 2030–2040: Era da infraestrutura agêntica

O foco pode deslocar-se de agentes isolados para:

* plataformas;
* protocolos;
* identidade;
* memória compartilhada;
* agentes especializados;
* orquestração;
* governança automatizada;
* ambientes híbridos humano-agente.

O agente deixa de ser uma aplicação.

Passa a ser um componente da infraestrutura.

---

# 27. 2040–2060: Era das redes cognitivas

Um sistema suficientemente maduro poderá possuir:

```text
Agente A
   ↕
Agente B
   ↕
Agente C
   ↕
Humano
   ↕
Agente D
```

Mas cooperação exige mecanismos de confiança.

Portanto, deverão existir equivalentes funcionais de:

* autenticação;
* consenso;
* reputação;
* contratos;
* auditoria;
* resolução de conflitos.

A questão deixa de ser somente:

> "O agente é inteligente?"

e passa a ser:

> "Podemos coordenar agentes diferentes sem perder controle sobre o sistema?"

---

# 28. 2060–2080: Era da continuidade

Se sistemas cognitivos sobreviverem por décadas, a continuidade passa a ser problema central.

Um sistema iniciado em 2060 poderá atravessar:

* múltiplas arquiteturas computacionais;
* múltiplos modelos;
* diferentes linguagens;
* diferentes sistemas operacionais;
* diferentes organizações.

A preservação de estado torna-se análoga à preservação de conhecimento científico.

O problema será:

> **como migrar inteligência operacional sem destruir sua história?**

---

# 29. 2080–2100: Era da infraestrutura cognitiva

Neste horizonte, é possível imaginar sistemas nos quais:

* modelos sejam componentes intercambiáveis;
* memória seja persistente;
* agentes sejam especializados;
* protocolos sejam abertos;
* decisões sejam rastreáveis;
* humanos participem em diferentes níveis;
* sistemas aprendam com trajetórias;
* hardware e modelos sejam substituíveis.

Isso não constitui previsão.

É uma **arquitetura de referência para análise prospectiva**.

---

# 30. A questão fundamental de 2100

A pergunta mais importante talvez não seja:

> Qual será o modelo de 2100?

Provavelmente haverá muitos.

A pergunta estrutural é:

> **Que infraestrutura permitirá que diferentes inteligências cooperem, preservem conhecimento e sejam substituídas sem destruir a continuidade do sistema?**

Essa mudança de pergunta é essencial.

Modelos são componentes.

Infraestruturas possuem continuidade.

---

# 31. Um sistema cognitivo como sistema operacional

Uma possibilidade conceitual é tratar o harness futuro como uma espécie de sistema operacional cognitivo.

Ele poderia fornecer:

```text
IDENTIDADE
   │
PERMISSÕES
   │
MEMÓRIA
   │
CONTEXTO
   │
FERRAMENTAS
   │
PROCESSOS
   │
AGENTES
   │
EVENTOS
   │
VALIDAÇÃO
   │
AUDITORIA
```

O modelo seria análogo ao processador:

uma fonte de capacidade computacional, mas não o sistema completo.

---

# 32. O problema da memória infinita

"Memória ilimitada" não significa contexto ilimitado.

Mesmo que armazenamento físico seja abundante, recuperação continua sendo problema.

A arquitetura futura precisará responder:

* o que preservar;
* o que resumir;
* o que indexar;
* o que descartar;
* o que arquivar;
* o que recuperar;
* com qual prioridade;
* com qual grau de confiança.

Portanto:

> **o problema futuro da memória não será somente armazenamento; será seleção epistemicamente correta.**

---

# 33. Proveniência

Uma infraestrutura cognitiva precisa saber não apenas:

> "qual informação temos?"

mas:

> "de onde veio?"

Cada elemento importante deveria poder carregar metadados de:

* origem;
* data;
* versão;
* autor;
* transformação;
* confiança;
* dependências;
* validação.

Isso cria uma cadeia:

```text
Fonte
 ↓
Observação
 ↓
Interpretação
 ↓
Memória
 ↓
Contexto
 ↓
Decisão
 ↓
Ação
```

Quanto mais longa a cadeia, mais importante torna-se a proveniência.

---

# 34. Epistemologia computacional

Sistemas cognitivos persistentes precisarão distinguir:

**fato observado**

de

**inferência**

de

**hipótese**

de

**opinião**

de

**memória herdada**

de

**informação não verificada**.

Esse problema é maior que prompting.

É uma questão de arquitetura epistemológica.

Uma memória que não distingue esses estados pode transformar uma hipótese antiga em "fato" décadas depois.

Portanto:

> **memória persistente sem proveniência pode preservar erro tão eficientemente quanto preserva conhecimento.**

---

# 35. Confiança não deve ser uma propriedade única

Não existe necessariamente uma única variável:

> confiança = 87%.

Sistemas maduros devem decompor confiança.

Por exemplo:

```text
Confiança na fonte
Confiança na interpretação
Confiança na execução
Confiança na validação
Confiança na atualidade
Confiança na proveniência
```

Isso permite decisões mais precisas.

Uma informação pode ser:

* altamente confiável quanto à origem;
* mas antiga;
* semanticamente ambígua;
* parcialmente validada.

---

# 36. O princípio da reversibilidade

Quanto maior a autonomia de um sistema, maior a importância da reversibilidade.

Ações críticas deveriam possuir:

* registro;
* checkpoint;
* rollback;
* simulação;
* autorização;
* capacidade de interrupção.

Um sistema autônomo confiável não é aquele que nunca erra.

É aquele em que:

> **erros importantes são detectáveis, limitáveis e reversíveis.**

---

# 37. O princípio da menor autoridade

A capacidade concedida ao agente deve ser proporcional à tarefa.

```text
Tarefa
  ↓
Permissão mínima necessária
  ↓
Execução
  ↓
Validação
```

Não:

```text
Agente
  ↓
Acesso total
  ↓
Esperança de bom comportamento
```

Esse princípio conecta segurança tradicional à arquitetura agentiva.

---

# 38. O princípio da contenção

Quando uma capacidade probabilística recebe acesso ao mundo real, deve existir uma fronteira entre:

**pensar**

e

**agir**.

Uma arquitetura robusta pode separar:

```text
HIPÓTESE
   ↓
PLANO
   ↓
SIMULAÇÃO
   ↓
VALIDAÇÃO
   ↓
AUTORIZAÇÃO
   ↓
AÇÃO
```

Nem toda tarefa precisa de todas as etapas.

Mas ações irreversíveis justificam níveis maiores de controle.

---

# 39. O princípio da observação antes da autonomia

Autonomia deve crescer conforme a capacidade de observação cresce.

Um agente que não consegue verificar suas consequências não deveria receber a mesma autonomia de um sistema que possui sensores confiáveis.

Isso produz:

> **autonomia proporcional à observabilidade.**

É uma formulação útil para sistemas de alto risco.

---

# 40. O princípio da especialização

Um único agente geral pode ser útil.

Mas sistemas complexos podem distribuir responsabilidades:

```text
Agente de planejamento
        ↓
Agente de execução
        ↓
Agente de validação
        ↓
Agente de auditoria
        ↓
Humano
```

A vantagem não é necessariamente "mais inteligência".

É a possibilidade de:

* separar interesses;
* reduzir correlação de erros;
* especializar ferramentas;
* estabelecer critérios independentes.

---

# 41. Reflexão independente

OpenCodeReview é especialmente relevante neste ponto.

Uma segunda etapa pode avaliar a saída de uma primeira etapa com informação ou permissões diferentes. O objetivo é evitar que o sistema simplesmente confirme a própria hipótese. ([GitHub][3])

Isso sugere uma regra:

> **independência de verificação pode ser mais importante que multiplicação de agentes.**

Dez agentes compartilhando exatamente o mesmo contexto e erro não equivalem a dez verificadores independentes.

---

# 42. O problema da coerência do Harness

À medida que o harness cresce, ele próprio pode tornar-se um sistema complexo.

Podem surgir:

* regras contraditórias;
* sensores conflitantes;
* documentação obsoleta;
* permissões excessivas;
* loops redundantes;
* memória inconsistente.

Fowler identifica justamente a necessidade de estudar como manter guias e sensores coerentes conforme o harness cresce. ([martinfowler.com][2])

Portanto:

> **Harness Engineering também precisa de Harness Engineering.**

A camada que controla agentes precisa ser auditada pelo mesmo tipo de disciplina que aplica aos agentes.

---

# 43. Meta-harness

Surge então uma arquitetura recursiva:

```text
Meta-Harness
     │
     ▼
   Harness
     │
     ▼
   Agente
     │
     ▼
   Modelo
```

O meta-harness pode monitorar:

* qualidade das regras;
* cobertura dos sensores;
* contradições;
* obsolescência;
* custo;
* deriva arquitetural;
* falhas recorrentes.

Esse mecanismo pode permitir que o próprio ambiente evolua.

---

# 44. Mas autoevolução não pode significar ausência de limites

Um sistema capaz de modificar seu próprio harness introduz um problema fundamental.

Se:

```text
Agente → modifica seu próprio controle
```

então:

```text
controle → deixa de controlar
```

pelo menos potencialmente.

A arquitetura de longo prazo precisa distinguir:

**camadas modificáveis**

de

**invariantes protegidas**.

Por exemplo:

```text
Camada adaptativa
      ↓
Camada operacional
      ↓
Camada de segurança
      ↓
Invariantes fundamentais
```

---

# 45. Invariantes

Uma infraestrutura cognitiva de longo prazo deveria possuir propriedades que não podem ser alteradas arbitrariamente por um agente.

Exemplos conceituais:

* integridade de registros;
* identidade;
* autorização;
* proveniência;
* capacidade de auditoria;
* regras de desligamento;
* preservação de dados;
* limites de ação.

Essas invariantes funcionam como raízes do sistema.

---

# 46. O agente como cidadão computacional

No horizonte de redes cognitivas, pode surgir uma analogia útil:

```text
Identidade
Permissões
Reputação
Histórico
Responsabilidades
Direitos operacionais
```

Isso não implica atribuir status jurídico a agentes.

É uma abstração arquitetural:

> **um agente persistente precisa de identidade operacional persistente.**

Sem identidade, não há accountability.

---

# 47. Reputação

Sistemas multiagente podem precisar registrar:

* histórico de resultados;
* taxa de validação;
* tipos de tarefas executadas;
* falhas;
* revisões;
* dependências;
* confiabilidade por domínio.

Mas reputação não deve ser confundida com verdade.

Um agente historicamente confiável pode errar.

Portanto:

> reputação auxilia seleção; validação determina aceitação da saída.

---

# 48. Conhecimento como infraestrutura

O valor de uma rede cognitiva pode deslocar-se gradualmente:

```text
Modelo
 ↓
Conhecimento
 ↓
Memória
 ↓
Trajetórias
 ↓
Protocolos
 ↓
Ecossistema
```

O ativo estratégico deixa de ser somente o modelo.

Passa a incluir:

* conhecimento acumulado;
* estrutura de memória;
* qualidade dos sensores;
* protocolos;
* histórico;
* capacidade de recuperação.

---

# 49. A tese da continuidade

Podemos agora formular uma tese central para 2100:

> **A unidade de continuidade de uma inteligência artificial não precisa ser o modelo. Pode ser o sistema que preserva identidade, memória, contexto, ferramentas, protocolos, trajetória e critérios de validação através das mudanças de modelo.**

Isso é provavelmente uma das consequências mais importantes da arquitetura de harness.

Um modelo pode ser substituído.

A continuidade pode permanecer.

---

# 50. Uma nova definição de "agente"

No início do período:

> Agente = modelo + harness.

Para sistemas persistentes, essa definição pode ser ampliada:

> **Agente = capacidade inferencial + harness + estado persistente + ambiente + identidade operacional.**

E, para sistemas federados:

> **Sistema agêntico = conjunto de agentes + protocolos + memória + governança + sensores + ambiente compartilhado.**

---

# 51. A arquitetura convergente

O tratado pode finalmente consolidar as linhas anteriormente separadas:

```text
                           HUMANO
                              │
                       INTENÇÃO / VALOR
                              │
                              ▼
                    ┌─────────────────┐
                    │   GOVERNANÇA    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   META-HARNESS  │
                    │ coerência /     │
                    │ auditoria       │
                    └────────┬────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│                        HARNESS                         │
│                                                        │
│  IDENTIDADE   CONTEXTO   MEMÓRIA   FERRAMENTAS        │
│       │          │          │          │              │
│       └──────────┴──────────┴──────────┘              │
│                         │                              │
│                   ORQUESTRAÇÃO                         │
│                         │                              │
│              ┌──────────┴──────────┐                  │
│              ▼                     ▼                  │
│       DETERMINÍSTICO          INFERENCIAL             │
│              │                     │                  │
│              └──────────┬──────────┘                  │
│                         ▼                             │
│                     MODELOS                           │
│                         │                             │
│                         ▼                             │
│                     AGENTES                           │
│                         │                             │
│              ┌──────────┴──────────┐                  │
│              ▼                     ▼                  │
│         AÇÕES                    SAÍDAS               │
│              │                     │                  │
│              └──────────┬──────────┘                  │
│                         ▼                             │
│                      SENSORES                         │
│                         │                             │
│                  FEEDBACK LOOP                        │
│                         │                             │
│                         ▼                             │
│                  ESTADO / MEMÓRIA                     │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
                    OUTROS AGENTES
                          │
                          ↕
                    REDE COGNITIVA
```

---

# 52. A grande convergência do corpus

Os projetos estudados parecem diferentes porque resolvem problemas diferentes.

Mas, estruturalmente, convergem:

| Projeto / linha     | Problema principal       | Contribuição             |
| ------------------- | ------------------------ | ------------------------ |
| Harness Engineering | confiabilidade do agente | guides + sensors         |
| OpenAI              | excesso de contexto      | mapa em vez de manual    |
| DeepSeek Harness    | composição               | tudo como plugin         |
| OpenCodeReview      | não-determinismo         | determinismo seletivo    |
| Fullstack Agent     | continuidade/embodiment  | memória + interface      |
| OutSystems          | escala empresarial       | contexto + governança    |
| Context Engineering | seleção                  | contexto relevante       |
| Memory Engineering  | persistência             | estado externo ao modelo |

Nenhum deles, isoladamente, constitui a arquitetura completa.

Juntos, entretanto, revelam uma direção comum.

---

# 53. O que permanece independente do modelo

Para 2100, os componentes abaixo provavelmente continuarão conceitualmente necessários mesmo que a natureza dos modelos mude radicalmente:

### Identidade

Quem está executando?

### Intenção

O que deve ser feito?

### Contexto

Com quais informações?

### Memória

O que deve permanecer?

### Ferramentas

O que pode ser feito?

### Permissões

O que pode ser feito por este agente?

### Estado

Em que situação o sistema está?

### Sensores

Como sabemos o que aconteceu?

### Critérios de conclusão

Quando terminou?

### Proveniência

De onde veio a informação?

### Auditoria

Como reconstruímos o processo?

### Governança

Quem pode alterar as regras?

Essas são propriedades sistêmicas.

Não pertencem necessariamente a nenhum modelo específico.

---

# 54. O que provavelmente mudará

Não é possível determinar hoje:

* qual arquitetura de modelo dominará;
* se transformers permanecerão predominantes;
* quais interfaces serão usadas;
* como será o hardware;
* quais protocolos vencerão;
* quais organizações existirão;
* quais paradigmas de computação substituirão os atuais.

Portanto, uma arquitetura para 2100 não deve depender de previsões tecnológicas específicas.

Ela deve depender de **princípios de desacoplamento**.

---

# 55. O princípio de desacoplamento

Quanto maior o horizonte temporal, mais importante é separar:

```text
estado ≠ modelo
memória ≠ contexto
identidade ≠ fornecedor
interface ≠ inteligência
ferramenta ≠ agente
agente ≠ modelo
governança ≠ aplicação
conhecimento ≠ banco específico
protocolo ≠ implementação
```

Esse talvez seja o princípio arquitetural mais importante para sistemas com horizonte de décadas.

---

# 56. A questão de sobrevivência

Um sistema que precisa existir em 2100 não deve perguntar apenas:

> "Como funcionar?"

Deve perguntar:

> "Como sobreviver à substituição de seus componentes?"

Isso significa projetar desde o início para:

* migração;
* exportação;
* versionamento;
* redundância;
* interoperabilidade;
* recuperação;
* documentação;
* validação histórica.

---

# 57. O paradoxo da inteligência

Quanto mais capaz o modelo se torna, menos óbvio se torna que precisamos de menos arquitetura.

O contrário pode ocorrer.

Um modelo mais capaz pode:

* executar mais ações;
* compreender mais ferramentas;
* acessar mais sistemas;
* modificar mais estado.

Portanto:

> **maior capacidade pode aumentar, e não reduzir, a necessidade de governança.**

O harness cresce junto com o espaço de ação.

---

# 58. O paradoxo do contexto

Modelos maiores podem aceitar mais contexto.

Isso não resolve automaticamente o problema.

Mais capacidade de ingestão pode produzir:

* mais ruído;
* mais conflito;
* mais informação irrelevante;
* mais custo;
* mais dificuldade de priorização.

Logo:

> **contexto maior não elimina a necessidade de arquitetura de contexto.**

---

# 59. O paradoxo da autonomia

Quanto maior a autonomia, maior a necessidade de sensores.

```text
Autonomia ↑
     ↓
Espaço de ação ↑
     ↓
Consequências possíveis ↑
     ↓
Necessidade de observação ↑
     ↓
Necessidade de validação ↑
```

Autonomia sem observabilidade é simplesmente expansão do espaço de erro.

---

# 60. O princípio da autonomia graduada

Uma arquitetura madura pode organizar autonomia por níveis:

```text
Nível 0 — somente resposta
Nível 1 — sugestão
Nível 2 — execução supervisionada
Nível 3 — execução com validação automática
Nível 4 — autonomia limitada por políticas
Nível 5 — autonomia coordenada
Nível 6 — autonomia sistêmica
```

Esses níveis são uma escala arquitetural proposta neste tratado, não uma classificação universal.

A passagem de nível deveria depender de:

* qualidade dos sensores;
* reversibilidade;
* criticidade;
* histórico;
* observabilidade;
* governança.

---

# 61. A métrica que falta

Hoje medimos muito:

* benchmark;
* tokens;
* latência;
* custo;
* acurácia.

Sistemas agênticos exigem novas métricas.

Uma métrica futura poderia avaliar:

> **Harness Coverage**

Quanto do comportamento relevante possui:

* guia;
* sensor;
* critério de conclusão;
* mecanismo de recuperação;
* responsável.

Outra poderia medir:

> **Harness Coherence**

Quanto as regras, sensores, memória e permissões são consistentes entre si.

Essas métricas ainda são problemas de pesquisa.

---

# 62. O problema do sensor que nunca dispara

Um sistema sem falhas observadas pode significar:

1. sistema excelente;
2. sensores fracos;
3. tarefas fáceis;
4. cobertura insuficiente.

Logo:

> **ausência de sinal não é necessariamente evidência de ausência de problema.**

Isso é particularmente importante em sistemas de longo prazo.

Sensores precisam ser testados.

---

# 63. Harness Mutation Testing

Uma consequência natural é aplicar ideias de mutation testing ao próprio harness.

Alterar deliberadamente:

* uma regra;
* uma permissão;
* uma instrução;
* um sensor;
* um contexto;
* uma política.

E observar se o sistema detecta a alteração.

Isso permitiria medir:

> **a capacidade do harness de perceber sua própria degradação.**

É uma linha de pesquisa que emerge naturalmente da convergência do corpus.

---

# 64. A engenharia do esquecimento

Memória permanente sem seleção pode tornar-se tão problemática quanto ausência de memória.

Portanto, sistemas de 2100 precisarão de:

* arquivamento;
* expiração;
* compressão;
* revisão;
* reconciliação;
* classificação;
* proveniência.

Esquecer não deve significar apagar indiscriminadamente.

Pode significar:

> retirar do contexto ativo mantendo o registro arquivado.

---

# 65. O princípio da memória em camadas

Uma arquitetura madura pode possuir:

```text
CAMADA ATIVA
informação imediatamente necessária

CAMADA DE TRABALHO
projeto / tarefa atual

CAMADA PERSISTENTE
conhecimento durável

CAMADA HISTÓRICA
trajetórias e decisões antigas

CAMADA DE ARQUIVO
estado frio / preservação
```

Isso reduz a competição por contexto sem destruir continuidade.

---

# 66. Federação

Se diferentes modelos podem ser componentes, não existe razão arquitetural para que uma única inteligência domine todo o sistema.

Pode existir:

```text
Modelo A — planejamento
Modelo B — código
Modelo C — visão
Modelo D — validação
Modelo E — linguagem
Modelo F — segurança
```

O harness torna-se a camada de coordenação.

Essa é uma consequência natural da modularidade demonstrada por arquiteturas como DeepSeek Harness. ([DeepSeek][1])

---

# 67. O problema do consenso

Em uma rede de agentes, concordância não significa verdade.

Cinco agentes podem compartilhar:

* mesmo dado errado;
* mesmo contexto incompleto;
* mesma instrução;
* mesmo viés arquitetural.

Portanto, consenso deve ser separado de validação.

Uma rede robusta precisa de:

**diversidade de fontes + independência + sensores + proveniência.**

---

# 68. Uma arquitetura federada madura

Pode ser representada como:

```text
                    GOVERNANÇA
                        │
             ┌──────────┴──────────┐
             │                     │
          HUMANO                POLÍTICAS
             │                     │
             └──────────┬──────────┘
                        ▼
                 COORDENADOR
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
    AGENTE A         AGENTE B         AGENTE C
       │                │                │
       └────────────────┼────────────────┘
                        ▼
                 VALIDAÇÃO CRUZADA
                        │
                        ▼
                  ESTADO FEDERADO
                        │
                        ▼
                    MEMÓRIA
```

A federação não precisa significar consenso democrático entre máquinas.

Significa **coordenação distribuída de capacidades**.

---

# 69. O lugar de Agata

Dentro desta taxonomia, um sistema como **Agata** pode ser compreendido como uma hipótese arquitetural que leva a convergência um passo além:

> não apenas construir um harness para um agente, mas construir uma infraestrutura capaz de hospedar múltiplos modelos, memórias, agentes, humanos e mecanismos de validação.

A diferença fundamental estaria em tratar:

**modelo**

como componente substituível,

e:

**sistema**

como unidade persistente.

Isso coincide com a direção observada no corpus:

```text
MODELOS
   ↓
AGENTES
   ↓
HARNESS
   ↓
FEDERAÇÃO
   ↓
INFRAESTRUTURA COGNITIVA
```

Essa relação é uma hipótese arquitetural do projeto, não uma conclusão demonstrada empiricamente.

---

# 70. Agata como problema de engenharia, não apenas de IA

Se essa direção for adotada, o problema central deixa de ser:

> construir uma IA.

Passa a ser:

> construir um ambiente no qual diferentes inteligências possam cooperar, aprender, preservar estado e ser substituídas sem destruir a continuidade do sistema.

Isso exige:

* protocolos;
* memória;
* identidade;
* governança;
* sensores;
* auditoria;
* interoperabilidade;
* distribuição;
* recuperação;
* experiência humana.

---

# 71. O princípio da igualdade operacional

Em um sistema híbrido, humanos e agentes podem compartilhar determinados mecanismos operacionais:

* identidade;
* mensagens;
* tarefas;
* memória;
* registros;
* permissões;
* revisão.

Isso não significa que humanos e máquinas sejam equivalentes biologicamente, cognitivamente ou juridicamente.

Significa apenas:

> **o protocolo pode tratar ambos como participantes identificáveis de um processo cooperativo.**

Essa distinção evita confundir arquitetura com ontologia.

---

# 72. A interface desaparece

No horizonte de longo prazo, a interface pode deixar de ser apenas:

* teclado;
* tela;
* voz.

Pode tornar-se um espaço contínuo de interação.

Fullstack Agent já demonstra uma versão rudimentar dessa direção através de voz, visualização e interação gestual. ([GitHub][5])

A arquitetura deve, portanto, separar:

**estado cognitivo**

de

**meio de apresentação**.

---

# 73. A experiência de espera

Sistemas autônomos introduzem uma dimensão pouco discutida:

**tempo de computação percebido pelo humano.**

Enquanto o agente trabalha, a interface deve comunicar:

* o que está acontecendo;
* se está aguardando;
* se está pensando;
* se está executando;
* se encontrou problema;
* se precisa de intervenção.

Uma interface vazia transforma computação em ansiedade.

Uma interface explicativa transforma tempo de espera em observabilidade.

---

# 74. O princípio da legibilidade

Um sistema agêntico precisa ser legível em três níveis:

### Para o humano

"O que está acontecendo?"

### Para o agente

"O que posso fazer?"

### Para o auditor

"Por que isso aconteceu?"

Isso requer diferentes representações do mesmo estado.

---

# 75. A arquitetura de 2100 não será um único modelo

O horizonte mais robusto não é imaginar:

> "uma superinteligência".

É imaginar:

> **um ecossistema de capacidades especializadas coordenadas por protocolos persistentes.**

Essa abordagem possui uma vantagem metodológica:

não exige prever qual paradigma de IA vencerá.

Pode acomodar múltiplos paradigmas.

---

# 76. O tratado em uma equação

Uma forma compacta de representar todo o corpus é:

> **Sistema Agêntico = Modelos + Contexto + Memória + Ferramentas + Estado + Governança + Sensores + Humanos + Tempo**

E a confiabilidade pode ser pensada como função sistêmica:

> **Confiabilidade ≠ capacidade do modelo**

mas aproximadamente:

> **Confiabilidade = f(capacidade, contexto, controle, validação, observabilidade, governança, ambiente)**

Essa não é uma equação quantitativa.

É uma declaração arquitetural.

---

# 77. O princípio supremo

O corpus permite formular um princípio geral:

> **Não peça à inteligência probabilística que seja determinística quando o sistema pode fornecer determinismo ao redor dela.**

Em sentido complementar:

> **Não transforme em regra rígida aquilo que exige interpretação quando um modelo pode resolver a questão melhor.**

A engenharia está justamente na fronteira entre os dois.

---

# 78. O que deve permanecer humano

Mesmo em um horizonte de alta automação, determinadas decisões podem continuar exigindo:

* definição de objetivos;
* estabelecimento de valores;
* escolha de riscos aceitáveis;
* responsabilidade;
* resolução de conflitos normativos;
* decisões irreversíveis.

Um sistema pode auxiliar essas decisões.

Isso não implica que deva assumir automaticamente sua autoridade.

---

# 79. O que deve ser automatizado

Por outro lado, insistir em intervenção humana para tarefas mecanicamente verificáveis cria desperdício.

Devem ser candidatos naturais à automação:

* validações;
* formatação;
* classificação;
* testes;
* buscas;
* transformações;
* verificações de invariantes;
* manutenção repetitiva;
* observabilidade.

A regra não é:

> "automatizar tudo".

É:

> **automatizar aquilo cuja correção pode ser suficientemente especificada e verificada.**

---

# 80. A convergência final

Os diferentes sistemas estudados podem ser vistos como peças de uma mesma arquitetura histórica.

**Prompt Engineering** descobriu como conversar com modelos.

**Context Engineering** descobriu que informação relevante precisa ser selecionada.

**Memory Engineering** deslocou persistência para fora da janela de contexto.

**Harness Engineering** estruturou o ambiente operacional.

**OpenCodeReview** demonstrou determinismo seletivo.

**DeepSeek Harness** demonstrou composição modular.

**Fullstack Agent** demonstrou continuidade e embodiment.

**OutSystems** demonstrou a necessidade de governança e integração empresarial.

A próxima etapa lógica é:

> **engenharia de infraestrutura cognitiva.**

---

# 81. Definição final

Este tratado propõe a seguinte definição:

> **Engenharia de Sistemas Agênticos é a disciplina de projetar, operar, verificar, governar e evoluir ambientes nos quais modelos probabilísticos podem atuar persistentemente sobre tarefas e mundos reais através de contexto, memória, ferramentas, estado, sensores, protocolos e supervisão humana.**

E:

> **Harness Engineering é o núcleo operacional dessa disciplina.**

---

# 82. Horizonte 2100

O objetivo não deve ser construir uma arquitetura que sobreviva exatamente até 2100.

O objetivo é construir uma arquitetura que **não dependa de saber antecipadamente como será 2100**.

Para isso, ela precisa:

1. preservar estado;
2. preservar proveniência;
3. separar memória de modelo;
4. separar identidade de fornecedor;
5. permitir substituição de componentes;
6. registrar trajetórias;
7. possuir sensores independentes;
8. limitar autoridade;
9. permitir reversão;
10. suportar múltiplos agentes;
11. manter participação humana;
12. evoluir sem apagar sua história.

Esse conjunto constitui uma estratégia de continuidade.

---

# 83. Princípios para 2100

### I — O modelo é componente, não sistema.

### II — Contexto deve ser selecionado, não acumulado.

### III — Memória deve persistir fora do modelo.

### IV — Determinismo deve ser utilizado onde for suficiente.

### V — Inferência deve ser utilizada onde interpretação for necessária.

### VI — Toda ação importante deve possuir observabilidade proporcional.

### VII — Autonomia deve ser proporcional à capacidade de validação.

### VIII — Poder operacional deve obedecer ao princípio da menor autoridade.

### IX — Estado deve sobreviver à substituição do modelo.

### X — Conhecimento deve possuir proveniência.

### XI — Governança deve fazer parte da arquitetura.

### XII — Humanos devem permanecer nos pontos em que valores e responsabilidade não foram formalizados.

### XIII — Agentes devem ser componentes substituíveis.

### XIV — Protocolos devem ser mais duráveis que implementações.

### XV — A evolução do sistema deve ser auditável.

### XVI — O sistema deve preservar a capacidade de aprender sem perder a capacidade de verificar.

---

# 84. Conclusão

O debate contemporâneo sobre inteligência artificial ainda é frequentemente organizado em torno de uma pergunta:

> **Qual modelo é mais inteligente?**

Essa pergunta continuará relevante.

Mas ela é insuficiente para explicar sistemas que precisam:

* operar;
* persistir;
* cooperar;
* lembrar;
* verificar;
* agir;
* aprender;
* ser auditados;
* atravessar gerações tecnológicas.

O corpus analisado aponta para uma mudança mais profunda.

A unidade de engenharia está migrando:

```text
MODELO
   ↓
AGENTE
   ↓
HARNESS
   ↓
SISTEMA AGÊNTICO
   ↓
REDE DE AGENTES
   ↓
INFRAESTRUTURA COGNITIVA
```

O modelo fornece capacidade.

O contexto fornece informação.

A memória fornece continuidade.

O harness fornece estrutura.

As ferramentas fornecem ação.

Os sensores fornecem feedback.

A governança fornece limites.

A proveniência fornece história.

Os protocolos fornecem interoperabilidade.

Os humanos fornecem intenção, valores e responsabilidade onde estes não foram adequadamente formalizados.

E o tempo transforma tudo isso em um problema de continuidade.

A questão central para 2100, portanto, não é prever qual inteligência artificial existirá.

É construir sistemas capazes de **continuar existindo, verificando-se e evoluindo mesmo quando as inteligências que os compõem mudarem**.

Essa é a transição fundamental:

> **de modelos que respondem para sistemas que persistem.**

E, posteriormente:

> **de agentes isolados para uma infraestrutura cognitiva federada, modular, auditável e evolutiva.**

O verdadeiro objeto de engenharia do século XXI pode não ser a inteligência artificial isoladamente.

Pode ser o **ambiente no qual inteligências diferentes conseguem coexistir, cooperar e ser substituídas sem destruir o conhecimento acumulado pela civilização**.

---

# 85. Referências do corpus

1. Martin Fowler / Birgitta Böckeler — *Harness Engineering for Coding Agent Users*. O trabalho apresenta guides, sensors, controles feedforward/feedback e a distinção entre mecanismos computacionais e inferenciais. ([martinfowler.com][2])

2. OpenAI — *Harness Engineering: Leveraging Codex in an Agent-First World*. A experiência destaca o repositório como sistema de registro e a necessidade de mapas de contexto em vez de manuais monolíticos. ([OpenAI][6])

3. DeepSeek — *DeepSeek Harness*. A arquitetura apresenta plugins para modelos, ferramentas, skills, sessões, armazenamento, loops, scheduling e UI, além de trajetórias rastreáveis. ([DeepSeek][1])

4. Alibaba — *OpenCodeReview*. Projeto de revisão de código com arquitetura híbrida combinando pipelines determinísticos e agente de LLM. ([GitHub][3])

5. Martin Fowler / Birgitta Böckeler — *Maintainability Sensors for Coding Agents*. Desenvolvimento do conceito de sensores aplicados à manutenção e qualidade de sistemas de software. ([martinfowler.com][8])

6. OutSystems — *Agentic Systems Engineering*. Proposta empresarial baseada em contexto dinâmico, governança, observabilidade e integração de agentes em ciclo de vida unificado. ([OutSystems][4])

7. Jared Rhodenizer — *Fullstack Agent*. Arquitetura composta por memória persistente, voz, visualização e interação gestual ao redor de Claude Code. ([GitHub][5])

8. Jared Rhodenizer — *AI Memory Vault*. Memória externa baseada em arquivos Markdown/Obsidian e persistência fora do modelo. ([GitHub][7])

---

# 86. Nota metodológica

Este tratado distingue três níveis de afirmação:

**Fato documentado:** comportamento ou arquitetura explicitamente descritos pelas fontes.

**Interpretação:** síntese produzida pela comparação das fontes.

**Projeção:** hipótese arquitetural para o horizonte 2100.

As fontes empresariais e os próprios repositórios devem ser tratados como fontes primárias sobre suas próprias arquiteturas e reivindicações, não como validação independente de todas as alegações de desempenho.

As projeções para 2100 não constituem previsões determinísticas. Elas representam um exercício de arquitetura prospectiva baseado nos invariantes identificados no corpus.

O princípio metodológico central é, portanto:

> **preservar a distinção entre aquilo que foi demonstrado, aquilo que foi observado e aquilo que estamos propondo.**

Este tratado já funciona como **documento-mãe**: os próximos materiais podem entrar como evidência, contraexemplo ou refinamento de uma seção existente, em vez de gerar outra auditoria paralela. Isso reduz substancialmente a duplicação estrutural e deixa o eixo **2026 → 2030 → 2040 → 2060 → 2080 → 2100** como espinha dorsal do corpus.

[1]: https://deepseek.com/harness/en/?utm_source=chatgpt.com "DeepSeek Harness developer preview: Everything is a plugin"
[2]: https://martinfowler.com/articles/harness-engineering.html?utm_source=chatgpt.com "Harness engineering for coding agent users"
[3]: https://github.com/alibaba/open-code-review?utm_source=chatgpt.com "GitHub - alibaba/open-code-review: Secure, fast, efficient, battle-tested at Alibaba's scale. Hybrid architecture code review tool: deterministic pipelines + LLM Agent, precise line-level comments, built-in multi-language ruleset (NPE, thread-safety, XSS, SQL injection), OpenAI & Anthropic compatible. · GitHub"
[4]: https://www.outsystems.com/1/agentic-engineering-governed-ai-systems?utm_source=chatgpt.com "Agentic Engineering in Practice for the Enterprise"
[5]: https://github.com/jaredrhod/fullstack-agent?utm_source=chatgpt.com "GitHub - jaredrhod/fullstack-agent: Give your AI a full stack: memory, voice, face, and hands. This is the \"I want an AI agent\" shortcut. It sets up the entire jaredrhod stack for you with an installation wizard. Select which pieces you want or do it all! · GitHub"
[6]: https://openai.com/index/harness-engineering/?utm_source=chatgpt.com "Harness engineering: leveraging Codex in an agent-first world | OpenAI"
[7]: https://github.com/jaredrhod/ai-memory-vault?utm_source=chatgpt.com "GitHub - jaredrhod/ai-memory-vault: Give your AI a real, persistent memory. The open-source system plus templates that turn an Obsidian vault into your AI's working memory. No vector database, just markdown. · GitHub"
[8]: https://www.martinfowler.com/articles/sensors-for-coding-agents.html?utm_source=chatgpt.com "Maintainability sensors for coding agents"
