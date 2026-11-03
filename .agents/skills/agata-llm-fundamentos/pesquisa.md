# Como uma LLM funciona e como mitigar suas falhas: revisão de fontes para o sistema Agata

Autor da síntese: Claude Sonnet 5.5 (Claude Code). Data: 03/11/2026. Estado: rascunho para revisão do Humano; nada aqui é canônico.

## Resumo

Esta revisão parte de um vídeo de divulgação (Léo Lamera, 30/10/2026) que lista pegadinhas de uso de LLMs e as confronta com fontes primárias: documentação oficial da Anthropic, a especificação do MCP e artigos do arXiv. O resultado central é que nenhuma técnica sozinha elimina a alucinação, que a janela de contexto declarada superestima a janela efetiva, que o número de skills e módulos importa menos do que a curadoria, e que parte dos números que circulam em blogs não aparece nas fontes primárias. A seção final traduz os achados em hipóteses de trabalho para o Agata, todas ainda por medir.

## Método e níveis de evidência

Cada afirmação carrega um nível:

- **N1**: li a fonte primária inteira ou a seção citada (documentação oficial, texto completo do artigo).
- **N2**: li só o resumo (abstract) do artigo; método e conclusão geral valem, números do corpo não.
- **N3**: fonte secundária (blog, lista, resumo de terceiros).
- **Inferência**: conclusão minha, não escrita na fonte.

A leitura das fontes foi feita por agentes auxiliares com a ferramenta de leitura de páginas; onde o relatório disse "resumo extraído", o trecho veio resumido por modelo e não literal, e está marcado. Nenhum número abaixo foi recalculado por mim. A página da OpenAI sobre o artigo de alucinação respondeu 403 e não foi lida; o artigo em si foi lido no arXiv.

## 1. Como uma LLM funciona

- A arquitetura dominante é o Transformer, baseada só em atenção (Vaswani et al., 2017, N2). O custo da atenção cresce com o quadrado do comprimento da sequência (conhecimento geral, não está no resumo).
- O texto é dividido em subpalavras. O método de byte pair encoding para tokenização (Sennrich et al., 2016, N2) permite tratar palavras raras como combinação de pedaços.
- O desempenho segue leis de potência em tamanho do modelo, dados e computação (Kaplan et al., 2020, N2). Para um orçamento fixo de computação, parâmetros e tokens devem crescer juntos (Hoffmann et al., 2022, "Chinchilla", N2).
- O alinhamento a instruções usa feedback humano: um modelo de 1,3 bilhão de parâmetros ajustado foi preferido a um GPT-3 de 175 bilhões (Ouyang et al., 2022, N2); o próprio resumo diz que o modelo ainda comete erros simples.
- Raciocínio em tempo de resposta: gastar computação na inferência, de forma adaptativa, pode superar um modelo 14 vezes maior em problemas onde o modelo-base já acerta algumas vezes (Snell et al., 2024, N2). O resumo também diz que boa parte do trabalho anterior dá resultados negativos.
- Geração de imagem e vídeo usa difusão: parte do ruído e o remove em passos (Ho et al., 2020, N2).

A frase do vídeo "escolhe o provável, não o verdadeiro" é consistente com o objetivo de treino de prever o próximo token, mas o argumento rigoroso está no item 2.

## 2. Alucinação

**Causa.** Kalai et al. (2025, arXiv 2509.04664, texto lido, mas parte das seções via resumo extraído) argumentam que a alucinação nasce do treino estatístico e é mantida pela avaliação: em 9 de 10 benchmarks analisados a pontuação é binária e só um deles dá crédito parcial a "não sei" (Tabela 2, resumo extraído). Exemplo do texto: se 20% dos fatos de aniversário aparecem uma única vez no pré-treino, espera-se errar cerca de 20% deles.

**Mitigação proposta.** Mudar a pontuação para penalizar o erro confiante: com limiar t, acerto vale 1, "não sei" vale 0 e erro vale −t/(1−t) (seção 4.2). Para t = 0,75 a penalidade é 3, conforme a fórmula. O artigo não traz experimento de mitigação, só teoria e auditoria de benchmarks. Limitação declarada: busca e RAG não resolvem sozinhos, porque a avaliação binária continua premiando o chute.

**Abstenção com garantia estatística.** Abbasi-Yadkori et al. (2024, arXiv 2405.01563) amostram várias respostas, medem a concordância entre elas e se abstêm abaixo de um limiar calibrado por controle conforme de risco. No melhor recorte relatado (Gemini Pro, Temporal Sequences, alfa 0,1), a perda foi 0,082 com abstenção de 11,7%, contra 0,084 e 21,9% da linha de base por log-probabilidade (números de tabelas, resumo extraído). Em TriviaQA a linha de base ficou melhor, o que o resumo chama de "comparável". Escopo: um modelo e dois conjuntos de dados.

**Cuidado com os resultados de treinamento por reforço.** Wu et al. (2025, arXiv 2512.19920) treinam um modelo pequeno com recompensas calibradas. O resumo afirma desempenho comparável a modelos de fronteira, mas os números das tabelas, segundo o relatório de leitura, mostram o método pior que dois deles em calibração no SimpleQA, e o texto diz que a variante com limiar no prompt falhou nos experimentos dos próprios autores (seção 3.2.1, literal). Usar apenas como indício, não como método a copiar.

**Levantamento.** Alansari e Luqman (2025-2026, arXiv 2510.06265) organizam as mitigações em quatro grupos: prompt, recuperação, raciocínio e treinamento. A conclusão do texto é que nenhuma abordagem sozinha elimina o problema e que híbridos são mais promissores. Os percentuais que cita vêm de outros trabalhos (N3 para fins de decisão).

**Síntese.** O estado da arte é uma pilha: ancorar em fonte com citação, permitir abstenção calibrada, verificar afirmação por afirmação e medir em produção. A peça mais barata de importar para o Agata é a política de pontuação: tratar "não medido" como resposta correta e o erro confiante como falha pior.

## 3. Contexto longo e "context rot"

- Chroma (Hong, Troynikov, Huber, 14/07/2025, N1 no texto integral): em 18 modelos, o desempenho cai com o comprimento da entrada em todos os experimentos; um distrator já prejudica e quatro agravam; no LongMemEval o prompt completo (cerca de 113 mil tokens) rende menos que a versão focada (cerca de 300 tokens). Os valores estão em gráficos, sem limiar numérico no texto, e não há seção de mitigação. Limitação: comprimento e dificuldade podem se confundir.
- RULER (Hsieh et al., COLM 2024, N1): de 17 modelos, só cerca de metade mantém desempenho satisfatório a 32 mil tokens. Exemplos de média em 13 tarefas de 4 mil para 128 mil tokens: GPT-4 de 96,6 para 81,2; Mistral-v0.2 de 93,6 para 13,8 (Tabela 3). O teste simples de agulha no palheiro fica perto de 100% e esconde a degradação. Recomendação: medir o comprimento efetivo, não o declarado.
- "Lost in the Middle" (Liu et al., TACL 2023, N1): curva em U, melhor no começo e no fim do contexto. Mitigações medidas: colocar o relevante nas pontas, recuperar menos documentos e repetir a consulta antes e depois do contexto (quase elimina a queda na tarefa de chave-valor, pouco muda no QA).
- Anthropic, engenharia de contexto (29/09/2025, N1): não traz medição própria. Recomenda compactação, anotações fora da janela, subagentes de contexto limpo e recuperação sob demanda. É orientação, não estudo.

**Síntese.** A janela de 1 milhão de tokens de que fala o vídeo é capacidade de leitura, não garantia de precisão. A mitigação com respaldo é reduzir e posicionar o contexto, e medir o comprimento efetivo de cada modelo usado.

## 4. Recuperação (RAG)

- Contextual Retrieval (Anthropic, 19/09/2024, N1): a taxa de falha nos 20 primeiros trechos cai de 5,7% para 3,7% com embeddings contextuais, 2,9% com BM25 contextual somado, e 1,9% com reranking (reduções de 35%, 49% e 67%). Cada trecho ganha 50 a 100 tokens de contexto gerados por um modelo pequeno; custo hipotético de US$ 1,02 por milhão de tokens de documento com cache. Não nomeia benchmark; o domínio testado inclui código, ficção e artigos científicos. O texto avisa "sempre rode avaliações".
- Self-RAG (Asai et al., 2023), RAG corretivo (Yan et al., 2024) e RAGAS (Es et al., 2023) foram lidos só no resumo (N2): o primeiro treina o modelo para criticar trechos e respostas com fichas de reflexão; o segundo usa um avaliador de qualidade que dispara busca na web quando a base é insuficiente; o terceiro propõe avaliar RAG sem rótulo humano. Os nomes das métricas do RAGAS não foram confirmados.
- O RAG original (Lewis et al., NeurIPS 2020, N2) já aponta proveniência e atualização como problemas abertos.

**Síntese.** Um RAG com busca errada responde errado com cara de certo, como diz o vídeo, e a defesa com número é híbrido (semântico mais lexical), reranking e uma métrica de recuperação medida em conjunto próprio.

## 5. Custo, esforço de raciocínio e agentes

Preços e regras abaixo são da documentação oficial da Anthropic (N1; as páginas não trazem data):

- Claude Opus 5.5: US$ 4 por milhão de tokens de entrada e US$ 20 de saída; lote: US$ 2 e US$ 10; modo rápido: US$ 8 e US$ 40 (pré-visualização).
- Cache de prompt, Opus 5.5: escrita de 5 minutos US$ 5, escrita de 1 hora US$ 8, leitura US$ 0,20 (0,05 vezes o preço base); mínimo cacheável de 512 tokens; vida padrão de 5 minutos, renovada a cada uso.
- Modelos 4.7 e posteriores usam um tokenizador que gera cerca de 30% mais tokens para o mesmo texto, segundo a página de preços.
- Esforço: cinco níveis (low, medium, high, xhigh, max). Para o Opus 5.5 o padrão é medium e o raciocínio adaptativo fica sempre ligado (página de effort). Isso corrige fontes secundárias que apontavam high como padrão.
- Que o raciocínio é cobrado como saída: não está dito na página de preços. A página de effort diz que o limite de saída cobre "raciocínio mais texto de resposta", o que sugere cobrança como saída (inferência).
- Agentes gastam cerca de 4 vezes os tokens de um chat e sistemas multiagente cerca de 15 vezes; o sistema multiagente superou o agente único em 90,2% numa avaliação interna sem nome e sem metodologia detalhada (Anthropic, 13/06/2025, N1). São modelos da geração Claude 4.
- Roteamento (RouteLLM, Ong et al., 2024, N2): reduz custo em mais de 2 vezes "em certos casos" sem perder qualidade; números de 2024 não se transferem aos modelos atuais.

**Síntese.** As alavancas medidas pela própria fornecedora são: prefixo estável para acertar o cache, esforço proporcional à tarefa, lote para o que não é urgente e multiagente só quando o valor justifica 15 vezes o custo.

## 6. Prompt, exemplos e atualidade

- Documentação da Anthropic (N1, seção "Use examples effectively"): "3 a 5 exemplos"; exemplos relevantes, diversos para o modelo não captar padrões não intencionais, e envoltos em tags. Não há aviso explícito de que o exemplo vire regra; a frase mais próxima é a de "padrões não intencionais".
- Min et al. (EMNLP 2022, N2): trocar aleatoriamente os rótulos dos exemplos quase não prejudica; contam o espaço de rótulos, a distribuição do texto e o formato. Em termos práticos, o exemplo ensina formato e distribuição mais do que conteúdo, e por isso é fácil virar molde.
- Cadeia de pensamento (Wei et al., 2022, N2): ganho aparece em modelos suficientemente grandes.
- FreshLLMs (Vu et al., 2023, N2): o número e a ordem das evidências de busca afetam a correção, e pedir respostas concisas reduz alucinação; todos os modelos sofrem com conhecimento que muda rápido.

## 7. MCP, skills e seleção de skills

- Especificação do MCP, página de boas práticas de segurança (a versão publicada mais recente parece ser 2026-07-28, inferência, pois a página não traz data; N1): servidores não devem aceitar tokens não emitidos para eles; proxies precisam de consentimento por cliente; clientes devem bloquear faixas privadas contra SSRF e rejeitar esquemas como javascript e file. **Não há seção sobre envenenamento de ferramentas** (descrições maliciosas).
- Envenenamento de ferramentas (Invariant Labs, 01/04/2025, N3 por ser de fornecedor): instruções ocultas na descrição, visíveis ao modelo e invisíveis ao usuário; variantes de troca posterior e de sombreamento entre servidores. Mitigações sugeridas: fixar versão com hash da descrição, controle de fluxo entre servidores e interface que mostre o que o modelo vê. Sem avaliação quantitativa.
- Skills (Anthropic, 16/10/2025, N1): três níveis de revelação progressiva: nome e descrição sempre carregados; corpo quando relevante; arquivos extras sob demanda. O artigo não dá número de tokens para os metadados; o "cerca de 100 tokens" do vídeo não consta nas fontes primárias lidas. Limites da documentação: nome até 64 caracteres, descrição até 1.024, corpo do SKILL.md abaixo de 500 linhas.
- SkillsBench (Li et al., arXiv 2602.12670, fev/2026, revisado jun/2026; resumo e parte do texto, N1/N2): 87 tarefas, 18 configurações de modelo e ambiente, 3 repetições. A média passa de 33,9% sem skills para 50,5% com skills curadas (+16,6 pontos). Skills focadas, com no máximo três módulos, superam pacotes grandes. Skills geradas pelo próprio modelo ficaram abaixo da linha de base nas três configurações testadas (por exemplo, Opus 4.7 com Claude Code: 43,0 sem skill, 34,9 gerada, 61,2 curada; valores de resumo extraído). Ressalvas: o benchmark é mantido pelo mesmo grupo que o executa, "curada" aqui significa o pacote específico da tarefa, e o placar do site usa outra agregação.

## 8. Discrepâncias encontradas entre o vídeo, blogs e as fontes

| Afirmação | Verificação |
|---|---|
| Tarifas do Opus 5.5 | US$ 4 e US$ 20 por milhão (N1) |
| Esforço padrão do Opus 5.5 | medium (N1); blogs diziam high |
| "Skill custa 100 tokens até ser usada" | sem número nas fontes primárias lidas; mecanismo de três níveis confirmado |
| Agentes 4x e multiagente 15x | confirmado (N1), dados de 2025 com modelos Claude 4 |
| Contexto de 1 milhão de tokens | declarado; RULER e Chroma mostram queda antes disso (N1) |
| Mitigação do envenenamento de ferramentas na spec do MCP | não existe na página de segurança lida |
| "Raciocínio cobrado como saída" | plausível, não escrito na página de preços |

## 9. Hipóteses de trabalho para o Agata (a medir, não a assumir)

1. **Abstenção como política medida.** Adotar a regra de pontuação com penalidade para erro confiante nas auditorias de resposta, com "não medido" como resposta válida. Medir quantas respostas da Seth trazem afirmação verificável sem fonte.
2. **Prefixo estável para o cache.** A leitura de cache custa 0,05 vezes a entrada no Opus 5.5. Hipótese: manter instruções fixas no começo e variáveis no fim reduz custo. Medir a taxa de acerto de cache real antes de mexer.
3. **Esforço por tarefa.** Medir qual nível basta para cada classe de tarefa do Agata e fixar uma tabela, em vez do padrão.
4. **Comprimento efetivo dos modelos do Agata.** Rodar um teste no estilo RULER nos modelos locais (por exemplo, os de 64 mil de contexto) antes de confiar no valor declarado.
5. **Recuperação medida.** Construir um conjunto de perguntas com resposta conhecida sobre o acervo do Agata (vault e canon) e medir 1 menos recall@20 das buscas que existem hoje; só então testar contexto por trecho, busca lexical somada e reranking.
6. **Descrições de ferramentas fixadas por hash.** Como a spec não cobre envenenamento, um controle local de hash das descrições de ferramentas MCP seria uma defesa própria.
7. **Seleção de skills por A/B.** Replicar o método do SkillsBench em escala pequena: cada skill candidata roda nas tarefas do Agata com e sem skill, com 3 repetições; só entra o que ganha. Preferir módulos focados (até três), curados por humano e não gerados pelo modelo.
8. **Exemplos diversos e avaliados.** Para prompts com exemplos, exigir diversidade e testar se a saída copia o molde.

## Limites desta revisão

- Muitos artigos foram lidos só no resumo (N2); números de tabelas citados vêm de resumos extraídos e precisam de conferência na fonte antes de uso em material publicado.
- As fontes sobre skills populares de 2026 (listas de blogs) não foram usadas como evidência.
- Não pesquisei ainda literatura sobre verificação automática de afirmações em tempo de resposta além do que o levantamento de 2025 cita, nem benchmarks de skills de verificação de fatos; a lacuna foi encontrada na primeira rodada de busca.
- O que o Agata já faz para cada item é a hipótese da seção 9; não foi conferido item a item no código nesta rodada.

## Referências

- Kalai, Nachum, Vempala, Zhang. Why Language Models Hallucinate. arXiv:2509.04664, 2025.
- Abbasi-Yadkori et al. Mitigating LLM Hallucinations via Conformal Abstention. arXiv:2405.01563, 2024.
- Alansari, Luqman. Large Language Models Hallucination: A Comprehensive Survey. arXiv:2510.06265.
- Wu et al. Mitigating LLM Hallucination via Behaviorally Calibrated RL. arXiv:2512.19920.
- Hong, Troynikov, Huber. Context Rot. Chroma, 14/07/2025.
- Hsieh et al. RULER. arXiv:2404.06654, COLM 2024.
- Liu et al. Lost in the Middle. arXiv:2307.03172, TACL 2023.
- Anthropic. Effective context engineering for AI agents. 29/09/2025.
- Anthropic. Introducing Contextual Retrieval. 19/09/2024.
- Asai et al. Self-RAG. arXiv:2310.11511. Yan et al. Corrective RAG. arXiv:2401.15884. Es et al. RAGAS. arXiv:2309.15217. Lewis et al. RAG. arXiv:2005.11401.
- Anthropic. Documentação de preços, prompt caching e effort (platform.claude.com/docs). Sem data na página.
- Anthropic. How we built our multi-agent research system. 13/06/2025.
- Ong et al. RouteLLM. arXiv:2406.18665.
- Anthropic. Equipping agents for the real world with Agent Skills. 16/10/2025. Skill authoring best practices.
- Li et al. SkillsBench. arXiv:2602.12670.
- Model Context Protocol. Security best practices, versão 2026-07-28 (inferida).
- Beurer-Kellner, Fischer. MCP Security Notification: Tool Poisoning Attacks. Invariant Labs, 01/04/2025.
- Min et al. Rethinking the Role of Demonstrations. arXiv:2202.12837. Brown et al. arXiv:2005.14165. Wei et al. arXiv:2201.11903. Vu et al. FreshLLMs. arXiv:2310.03214.
- Vaswani et al. arXiv:1706.03762. Sennrich et al. arXiv:1508.07909. Kaplan et al. arXiv:2001.08361. Hoffmann et al. arXiv:2203.15556. Ouyang et al. arXiv:2203.02155. Snell et al. arXiv:2408.03314. Ho et al. arXiv:2006.11239.
- Lamera, L. Explicando tudo sobre IA em 15 minutos. YouTube, 30/10/2026.
