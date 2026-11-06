# Auditoria do Experimento GPT — 04/11/2026

**Revisor:** GPT-6.1-sol, identidade informada pelas instruções da sessão.  
**Parecer:** direção aproveitável, com correções técnicas necessárias aplicadas aos documentos; pronta para revisão do piloto, não para afirmar implantação ou eficácia.  
**Decisão humana incorporada:** esta arquitetura será a base da nova versão do Agata, mantendo Alexandria como subsistema.

## 1. Escopo e método

Foram lidos os 11 arquivos originais da pasta: diário, skill, briefing, transcrição, fundamentos, contrato, inventário, matriz e três propostas. A transcrição foi lida como texto; não foi comparada integralmente ao áudio.

Foram lidos PROMPT_CARREGAMENTO e os quatro documentos normativos REGRAS, PROTOCOLOS, FALHAS e PROJETO integralmente; a janela recente de MEMÓRIAS (linhas 40–70 na cópia) e trechos adicionais recuperados por busca. Consulta dirigida ao vault, índices e Fronteira de recusas precedeu o confronto com código. Não houve leitura integral de toda a memória histórica nem de todo o código do Agata.

A cópia medida iniciou em `ef5a08e`; o estado reportou sync PASS, hashes de REGRAS e MEMÓRIAS e HASH-ESTADO `79a169aa03f3`. A sessão antiga de Equipe apresenta deriva de base e o marcador Codex ausente; não foram alterados. A auditoria autorizada ocorre nesta pasta.

Leituras de runtime foram limitadas a metadados GET e estado de serviços/portas. Não houve geração por LLM, POST de teste, acesso ao arquivo de segredos ou alteração de serviços. A coleta e o arquivo de originais ficam no próprio experimento.

## 2. Achados e tratamento

Os documentos anteriores estão preservados em [originais.tar.gz](originais.tar.gz), com hashes em [evidencias-iniciais.json](evidencias-iniciais.json). O diário antigo permanece; as correções entram nas novas entradas.

| ID | Prioridade | Achado e evidência | Correção aplicada |
|---|---|---|---|
| A01 | alta | conclusões 044–046 e respostas chamavam flags do catálogo de modelos disponíveis; /api/models contém openrouter/auto | inventário distingue flag, rota, instalado, elegível, testado e em fila; não afirma 12 LLMs funcionais |
| A02 | alta | matriz propunha Groq e novos titulares apesar da retirada documentada em PROJETO, seção Cérebro | matriz preserva filas reais e trata demais opções como candidatas condicionadas |
| A03 | alta | fronteira dos pesos sugeria delegar toda memória exceto pesos e garantia de continuidade comportamental | explicita contribuição inevitável dos pesos, persistência externa e regressão após troca |
| A04 | alta | validação de frontmatter e busca por títulos foram apresentadas como coerência completa; proposta tinha dois títulos 18 e metacognição pulava 11 | revisão semântica dirigida, ordem/numeração corrigidas e alcance do verificador declarado |
| A05 | alta | alegações de falta de avaliação/memória integrada ignoravam peças existentes | mapeia medidores, autodev, teste_portugues, cache com lock/idempotência, memória semanal e fila de revisão |
| A06 | alta | recuperação vetorial/GraphRAG proposta como camada geral sem recusa vigente | Alexandria conserva baseline lexical e semântica secundária; mudança primária exige reabertura protegida |
| A07 | alta | protocolo priorizava entrada mais recente; biblioteconomia confundia controle de autoridade com poder normativo | sucessão exige escopo, autoridade e supersedes; nomes bibliográficos e autorização são distintos |
| A08 | alta | “estado comum” e memória entre todas as LLMs omitiam silos MOD e dados pessoais | contexto por acesso e destino; consulta externa minimizada; nada de broadcast irrestrito |
| A09 | média | sete palavras chamadas de máquina verificável sem transições concretas e Remoção obrigatória | tabela de transições, retornos e Remoção opcional; separa estado editorial, execução e saúde |
| A10 | alta | score sem rubricas/denominadores; A/B misturava várias intervenções e dados de ajuste/teste | protocolo pareado, ablações, split reservado, falhas por etapa, custo completo e incerteza |
| A11 | média | provedor diferente era condição suficiente de independência; repetição de script era auditoria independente | descreve dependências comuns e distingue repetibilidade de independência factual |
| A12 | média | preservação universal de qualquer fonte e autoaquisição conflitavam com direitos, sensibilidade e disciplina de memória | política de direitos/acesso antes de ingestão; candidatos em quarentena; retenção não universal |
| A13 | média | livro, conhecimento, skill e instrução estavam fundidos | tipos distintos, catálogo documental separado de capacidades e revisão antes de ativação |
| A14 | média | local-first parecia serial obrigatório e Internet paralela não limitava egresso | precedência lógica local e execução simultânea em atualidade, preservando privacidade e orçamento |
| A15 | média | “estado da arte mais eficaz” baseado em buscas/resumos, referências sem versões e rascunho FADGI tratado genericamente | registro de fontes com versão, nível de leitura e pendências; eficácia local passa a hipótese |
| A16 | média | funções distribuídas sem commits de estado, revogação e invalidação suficientemente definidos | escritor único, versão, idempotência, eventos de correção, dependências e skills revogáveis |

A proposta metacognitiva também deixou de chamar toda a camada de determinística: classificação semântica e verificação de suporte são sujeitas a erro. Falha de auditor lexical não autoriza afirmar verdade completa.

## 3. Confronto com mecanismos reais

| Evidência consultada | O que sustenta |
|---|---|
| `PROJETO.md`, seções Cérebro, Memória e hidratação e Memória em duas camadas | modelos substituíveis, memória e índices, privacidade, estado declarado |
| `PROJETO_REFERENCIA.md`, linhas 62–80 | recusa de vetor/GraphRAG primário e autorização semântica secundária |
| `redesign/router/auditoria_turno.py`, linhas 1–35 e CLI a partir de 1519 | predicados mecânicos e leitura de stdin; não verifica toda afirmação falsa nova |
| `redesign/router/cache_conselho.py`, início e função anotar | cache não canônico com lock, encadeamento, filtragem e idempotência |
| `scripts/vault_importar_inbox.py`, linhas 1–45 | fila de revisão, sem escrita automática no cânone |
| `scripts/memoria_semanal.py`, linhas 1–100 | síntese em proposta, com checagem mecânica parcial |
| `scripts/medir_recuperacao.py`, linhas 1–42 | benchmark lexical e modo semântico; viés de consulta declarado |
| `scripts/teste_portugues.py`, linhas 1–100; `config/capacidades_modelos.json` | quatro condições e perfis diferentes; contaminação do perfil pelo mesmo conjunto explicitada |
| `redesign/obsidian/consulta.py`, início | índice primeiro; via canon e via MCP, sem vector DB |
| `redesign/mcp/capability.py`, início | autorização efêmera ligada a chamada, argumentos e nonce |
| APIs locais e unidades em evidencias-iniciais.json | fotografia observada, sem equivaler a teste funcional |

Na fotografia de 13:55:30: Ollama retornou 7 tags (6 generativas, 1 embedding); OmniRoute 15 registros de catálogo (12 flags true, incluindo uma rota auto), 311 registros expostos e os combos reais. Gateway, verificador, embeddings e Laya estavam inativos. Esses fatos têm escopo temporal e não diagnosticam defeito por si.

A API resumida não é roster completo: Ministral 14B aparece nos combos sem constar entre os 15 registros. A contagem de rotas variou de 313 para 311; não é contagem de capacidades independentes.

## 4. O que foi preservado e melhorado

A direção central permanece: memória externa, consulta local, Internet para atualidade/lacuna, curadoria, procedimentos derivados e modelos substituíveis, sob governança humana.

A revisão consolidou a especificação em Alexandria e separou responsabilidades dos demais documentos. Acrescentou índice de leitura, registro de fontes e evidências estruturadas. A skill ficou menor, com instruções decisivas e referências sob demanda, conforme a skill de criação consultada.

A única memória de conclusões continua sendo conclusoes.md. Documentos de arquitetura são projeções revisáveis; a cópia anterior permite comparar exatamente o que mudou.

## 5. Falhas e custos desta própria auditoria

Leituras agrupadas geraram truncamento de saída em algumas chamadas. Trechos necessários foram relidos em blocos menores; isso consumiu contexto adicional. O custo exato de tokens e valor monetário não foi medido.

Uma busca tentou o caminho errado de consulta.py e foi corrigida por inventário para redesign/obsidian/consulta.py. A leitura web de PREMIS falhou duas vezes; a MDPI respondeu 429. A auditoria não tratou essas falhas como leitura concluída.

A primeira execução do verificador apontou um link para verificacao.json antes de esse próprio relatório ser gerado. O arquivo foi produzido ao final da execução; a verificação seguinte inclui sua existência e validade JSON. A falha inicial não foi tratada como sucesso.

Este parecer usa o histórico da mesma conversa e foi redigido pelo modelo que aplicou as emendas. Não é revisão cega, sessão independente ou aprovação canônica. A independência de avaliação futura permanece necessária conforme o fluxo do Agata.

## 6. Verificação e pendências

O [verificador da pasta](verificar_pasta.py) confere preservação do prefixo histórico, bytes da transcrição, hashes do arquivo de cópia, links locais, sequências de títulos e JSON. O resultado fica em [verificacao.json](verificacao.json). Sua aprovação cobre esses predicados, não todas as relações semânticas.

A skill passa também pelo quick_validate. O relatório e a resposta final passam pelo auditor mecânico do Agata; achados lexicais precisam ser interpretados. Não executar uma suíte de produção inteira para validar uma revisão documental.

Permanecem para o piloto: implementar os contratos, reservar casos novos, avaliar suporte semântico, medir qualidade/custo por rota, testar restauração e revogação e confirmar acesso às LLMs pagas. A aquisição de “principais livros” exige seleção do acervo e permissões por edição.

## 7. Conclusão

O desenho é aproveitável como base da nova versão. Os documentos anteriores superestimavam o grau de verificação e misturavam capacidades catalogadas, políticas e implementação. A versão revisada oferece uma especificação mais concreta e um caminho comum: F0 especificação, F1 sombra, F2 avaliação, F3 integração protegida. O ganho operacional ainda deve ser demonstrado.
