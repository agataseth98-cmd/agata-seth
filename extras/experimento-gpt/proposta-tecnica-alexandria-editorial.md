# Alexandria — especificação técnica da nova versão do Agata

**Revisão:** auditoria de 04/11/2026 · GPT-6.1-sol  
**Direção:** aprovada pelo Humano nesta conversa: esta arquitetura será a nova versão do Agata.  
**Estado técnico:** especificação revisada; implementação e eficácia ainda por demonstrar.  
**Escopo:** Alexandria é subsistema de conhecimento do Agata; a governança continua no Agata.

## 1. Propósito e fronteiras

Alexandria reúne catálogo, recuperação, aquisição seletiva, curadoria e produção de procedimentos. Reaproveita a memória do Agata e oferece acesso a conhecimento com origem, versão, direitos e contexto. LLMs atuam como processadores substituíveis; agentes são papéis atribuídos conforme a tarefa.

O acordo inicial do experimento permanece: `conclusoes.md` é a primeira memória consultada sobre este experimento, preservada por acréscimo. Essa disciplina é o protótipo manual. Sua existência não prova qualidade de recuperação, cumprimento perfeito nem aprendizagem dos pesos.

O Agata real já implementa partes desse ciclo. [Mapa de evidências](auditoria-2026-11-04/relatorio.md) documenta o estado observado e os limites. A nova versão integra e avalia essas peças sem criar uma segunda autoridade normativa.

## 2. Requisitos e não inferências

- Pesos continuam contribuindo conhecimento e padrões para toda geração. Memória externa pode ser centralizada no Agata; não é possível garantir por prompt que o modelo ignore o que aprendeu.
- Em modo estritamente documental, toda afirmação sobre a coleção exige trecho de suporte ou abstenção. Essa é uma política de saída verificável, não isolamento dos pesos.
- Contexto, ativações e KV cache são estados computacionais. Armazenar ou reutilizar cache não o transforma em fonte validada.
- Trocar de LLM deve preservar objetos, fontes e permissões; o comportamento e a qualidade podem mudar e precisam de regressão.
- Aplicações e provedores podem manter histórico, caches ou funções próprias de memória. Exclusividade da memória de aplicação exige adaptadores e configurações verificadas; Alexandria não controla por instrução a retenção interna de terceiros.
- Auto-observação operacional significa telemetria, avaliação e ajuste autorizado. As analogias com cérebro e memória humana são funcionais.
- Integridade criptográfica demonstra conservação de bytes em relação a uma referência. Não demonstra verdade do conteúdo, completude, licença nem autoria real.

## 3. Reaproveitamento do Agata

| Função | Peça existente inspecionada | Limite e ação proposta |
|---|---|---|
| Governança e história | `REGRAS.md`, `PROTOCOLOS.md`, `MEMÓRIAS.md` | preservar autoridade e fluxo de registro |
| Contexto | `scripts/estado_para_eco.sh`, gateway e hidratação | medir atualidade e respeitar silos; o gateway estava inativo na fotografia |
| Recuperação lexical | vault, índices, `scripts/busca_texto.py` | baseline inicial |
| Recuperação semântica | `scripts/busca_semantica.py`, endpoint local e5 | secundária, sob demanda; serviço inativo na fotografia |
| Memória compartilhada | `redesign/router/cache_conselho.py` | cache não canônico, com lock, encadeamento e limites |
| Consolidação | `scripts/memoria_semanal.py` | prepara proposta; checagem lexical não prova suporte semântico |
| Revisão de notas | `scripts/vault_importar_inbox.py` | copia para fila humana; não grava automaticamente no cânone |
| Avaliação | `seth_golden.py`, `seth_autodev.py`, `medir_recuperacao.py`, `teste_portugues.py` em `scripts/` | adaptar casos, separar treino de avaliação e evitar duplicar harness |
| Roteamento | gateway, Laya/Jev, combos OmniRoute | roteiam tarefas/modelos; não equivalem ao seletor de skills proposto |
| Autorização | P-8 e `redesign/mcp/capability.py` | assinatura e permissão de chamada têm finalidades distintas |
| Observação | manifestos, estado, painel | incorporar indicadores sem reiniciar serviços durante a auditoria |

GraphRAG e vector store como memória primária têm recusa documentada em `PROJETO_REFERENCIA.md`, seção Fronteira de recusas. Busca semântica secundária tem autorização própria. A nova versão conserva esse limite: grafos de relações derivados e experiências de recuperação são opcionais; qualquer mudança da política primária requer reabertura explícita com dado novo e fluxo protegido.

## 4. Modelo de informação

Separar entidades que antes estavam misturadas:

| Entidade | Conteúdo | Identidade e relações |
|---|---|---|
| Obra e edição | livro, artigo, manual; tradução/edição específica | `work_id`, `edition_id`, idioma e autoria declarada |
| Objeto | arquivo ou captura preservável | `object_id`, versão, URI, formato, hash |
| Afirmação | proposição delimitada sobre algo | `claim_id`, suporte, oposição, qualificação e escopo |
| Evento | aquisição, extração, revisão, correção ou decisão | `event_id`, instante, ator, entradas e saídas |
| Skill | procedimento potencialmente executável | `skill_id`, versão, gatilho, dependências, testes e permissões |
| Contexto | pacote entregue a um modelo | `context_id`, fontes/versões, orçamento, política e destino |
| Autorização | decisão do Humano aplicável ao efeito | referência ao escopo aprovado; nunca inferida da relevância |

Catalogar uma pessoa ou obra com vocabulário controlado é **controle de autoridade bibliográfico**. Isso não significa que a obra seja verdadeira ou que possua autoridade para comandar o sistema.

Exemplo de registro de fonte (campos ausentes ficam `null`):

```yaml
schema_version: 1
object_id: alex:source:0001
work_id: alex:work:0001
edition_id: null
version: 1
title: null
origin_uri: null
published_at: null
acquired_at: null
checked_at: null
content_sha256: null
media_type: null
language: pt
rights:
  status: unknown
  evidence: null
access:
  classification: local_only
  allowed_destinations: []
editorial_status: quarantined
verification:
  identity: not_checked
  integrity: not_checked
  factual_support: not_checked
  method: null
derived_from: []
supersedes: []
expires_at: null
reviewer: null
```

Fonte confiável pode conter afirmação errada. Objeto preservado pode estar contestado. Por isso estado editorial, acesso, integridade e suporte factual são dimensões separadas.

## 5. Persistência e recuperação inicial

O primeiro piloto usará arquivos já existentes em leitura e um catálogo derivado reconstruível. Um índice lexical simples é suficiente para a primeira comparação. SQLite/FTS5 é opção de implementação, condicionada à disponibilidade local; um banco vetorial ou servidor de grafo não é pré-requisito.

O catálogo mantém referências e pequenos metadados; documentos completos ficam em armazenamento de objetos/arquivos permitido. O histórico de eventos é append-only, com escritor único, transação e chave idempotente. Projeções para consulta podem ser reconstruídas a partir das fontes e do diário.

Tabelas candidatas: `objects`, `editions`, `claims`, `claim_evidence`, `relations`, `skills`, `events` e índice lexical. Esses nomes são desenho, não tabelas criadas por esta revisão.

Regras de correção:

- decisão nova só substitui outra quando tem escopo e autoridade compatíveis;
- uma data recente sozinha não revoga decisão antiga;
- usar `supersedes`, `supports`, `contradicts` e `derived_from` para relações explícitas;
- resumo, embedding e relação extraída são derivados; conservar ponteiro para a evidência;
- mudança de fonte invalida ou marca como pendentes os derivados afetados, por evento;
- revogação de skill impede uso futuro da versão retirada; registros passados permanecem.

## 6. Pesquisa local-first e atualidade

O primeiro passo lógico é consultar Alexandria e as regras. Em tarefa estável e suficientemente coberta, a resposta pode ficar local. Em pedido explícito de web, estado da arte ou fato volátil, a pesquisa externa pode iniciar ao mesmo tempo que a consulta local. A precedência local não impõe uma espera serial que prejudique atualidade.

Antes da busca, aplicar acesso e privacidade. Texto pessoal, segredo e MOD de outra família não podem vazar por pergunta, embedding, metadado ou resumo. A rota externa recebe apenas consulta pública minimizada e permitida; caso isso não seja possível, permanece local.

A suficiência é julgada por cobertura dos subproblemas, suporte em trechos, atualidade por domínio, contradições e risco. Similaridade alta não basta. Se a fonte local não sustenta a resposta, declarar a lacuna e buscar fora quando permitido. Sem rede, entregar resultado parcial com data, fontes e limites.

Recuperação proposta:

1. filtrar permissões e versões elegíveis;
2. consulta exata/lexical e relações catalogadas;
3. busca semântica secundária se disponível e útil no conjunto local;
4. fusão e reranqueamento somente quando a ablação medir ganho;
5. inspeção dos trechos e construção do pacote de evidência;
6. geração, validação de suporte e resposta.

Catálogo vazio significa resultado negativo naquela busca, nunca inexistência do conhecimento.

## 7. Aquisição e curadoria

A pesquisa pode sugerir novos itens; não obriga guardar cada página. Priorizar utilidade, cobertura de lacunas, diversidade, custo, direitos e possibilidade de recuperação.

`recebido → quarentena → catalogado → revisado → elegível para consulta`

Objetos podem seguir para `contestado`, `restrito`, `arquivado` ou `rejeitado`. Preservar um argumento contestado como documento não exige aceitá-lo como verdade.

Na quarentena: parser isolado, sem macros/scripts e sem execução dos arquivos adquiridos; registrar origem e direitos; conferir limites, sensibilidade, integridade, duplicação e sinais de instrução maliciosa. Detectores de prompt injection são imperfeitos. A defesa principal mantém o conteúdo sem capacidade de autorizar ações, inclusive após catalogado.

Licença desconhecida não autoriza copiar, redistribuir ou converter integralmente uma obra. Pode-se manter referência bibliográfica e localização permitida. Política de preservação de conteúdo sensível ou vedado deve ser decidida pelo Humano; não impor retenção universal desses bytes. O histórico protegido tem sua disciplina específica.

Obras consideradas importantes devem ser selecionadas por critérios explícitos, com pluralidade de idioma, região, época, posição e edição. Prestígio histórico não substitui avaliação da afirmação.

## 8. Livros operacionais e skills

Uma obra de referência e uma skill são tipos distintos. Alexandria pode derivar um procedimento de fontes autorizadas; não precisa transformar todo livro em instrução executável.

Cada skill candidata tem `SKILL.md` enxuto e referências detalhadas sob demanda. Incluir objetivo, gatilhos, contraindicações relevantes, dependências, ferramentas permitidas, fontes e casos de teste. Scripts só entram quando resolvem uma necessidade concreta.

`rascunho → quarentena → revisão de fontes → testes reservados → revisão humana → versão elegível`

Versão elegível para experimento não é aprovação para instalar no Agata. A instalação protegida segue P-8. Uma skill não se autoaprova, não amplia seus privilégios e não altera o roteador que a avalia.

## 9. Seleção de skills e modelos

Primeiro validar escopo e autorização. Menção explícita seleciona um candidato prioritário entre opções permitidas. Skills obrigatórias permanecem; ausência de skill adequada pode levar a fluxo genérico autorizado ou esclarecimento.

Separar dois índices: documentos informam; skills prescrevem um procedimento após seleção autorizada. Um resultado de busca documental não ativa automaticamente uma skill.

No início, usar catálogo pequeno com gatilhos e busca lexical. Introduzir recuperação semântica, indexação do corpo e reranqueamento por etapas avaliadas. O indexador pode usar o corpo completo sem injetá-lo inteiro em cada chamada. Após selecionar, o executor lê o `SKILL.md` inteiro; referências seguem a necessidade.

Registrar `disponível`, `selecionada`, `lida`, `aplicada`, `testada` e versão/hash. Uma skill lida em outro turno pode ter sido compactada ou alterada.

Escolher LLM por medição por tarefa, capacidade de ferramentas, privacidade, saída e custo. Catálogo de provedor não prova inferência disponível. Gratuito pode ter cota, custo computacional e restrições de uso. As duas LLMs pagas relatadas pelo Humano ainda precisam de adaptadores, identidade e limites confirmados antes de designação técnica.

## 10. Papéis, coordenação e execução

Hidrator, recuperador, classificador, catalogador, especialista, sintetizador, revisor, curador, editor, sincronizador e vigia são responsabilidades. Funções determinísticas cuidam de hashes, metadados, orçamento, acesso e transições. Uma LLM só é chamada onde interpretação agrega valor.

Tarefa simples pode exigir uma chamada; revisão adicional depende do risco ou regra vigente. Em decisão não verificável, respeitar a Regra 8 do Agata e suas condições locais. A arquitetura não revoga essa regra por economia.

Paralelismo requer subtarefas independentes e orçamento total, incluindo novas tentativas e síntese. Usar fila na GPU local compartilhada; duas tags instaladas não equivalem a dois recursos independentes.

Cada tarefa recebe `task_id`, versão de contexto, prazo e limite de chamadas. Resultados levam fontes e a versão lida. Escritor único consolida com comparação de versão. Resultado atrasado ou contexto alterado volta à validação. Chave idempotente evita dupla aplicação; cancelamento impede novos efeitos e conserva o registro dos efeitos já ocorridos.

O estado de execução é separado do editorial:
`criada → em_execucao → em_revisao → concluida`, com `falhou`, `cancelada` e `aguardando_humano` como saídas explícitas.

Independência tem dimensões: fonte, autor original, treinamento, modelo, contexto, provedor e infraestrutura. Provedor diferente reduz algumas dependências; não garante verdade nem ausência de viés correlacionado. Reexecução do mesmo script prova repetibilidade, não verificação independente da lógica.

## 11. Sete palavras como ciclo de evolução

As sete palavras são a estrutura conceitual da evolução. Para automatizar, cada objeto precisa de transições explícitas:

| Estado | Evidência para sair | Destino normal | Retorno ou parada |
|---|---|---|---|
| Apresentação | pergunta, objeto, escopo e acesso definidos | Compreensão | pedir delimitação |
| Compreensão | fontes, lacunas, dependências e riscos descritos | Assimilação | pesquisar ou declarar inconclusivo |
| Assimilação | interpretação revisada, origem e versão preservadas | Simbiose | voltar a Compreensão |
| Simbiose | responsabilidades, interfaces e orçamento definidos | Transição | reduzir escopo ou resolver conflito |
| Transição | teste, versão e autorização compatível | Aprimoramento ou Remoção | voltar a Simbiose; aguardar Humano |
| Remoção | alvo exato, efeito, autorização e recuperação definidos | Aprimoramento | não remover se faltar condição |
| Aprimoramento | comparação com baseline e regressões avaliadas | novo ciclo ou encerramento | voltar ao estado que falhou |

Remoção é opcional. Uma melhoria pode conservar todos os componentes. Registro inclui estado anterior/posterior, evidência, responsável, verificador exigido, autorização, orçamento, retorno e resultado. Essa tabela é especificação, não máquina já executada.

## 12. Avaliação e critérios

[Protocolo de avaliação](proposta-implementacao-buracos-experimento.md) é a fonte do método. Separar falha de infraestrutura, recuperação, seleção, raciocínio, citação e execução.

Comparar baseline atual com alternativas pareadas, mantendo corpus, versões, tarefa, recursos e parâmetros registrados. Separar dados de desenvolvimento, calibração e teste reservado. Repetições medem variação; não substituem diversidade de tarefas. Custos incluem indexação, ingestão, revisão, novas tentativas e manutenção.

O piloto deve testar: resposta local suficiente; pergunta volátil com consulta externa; fonte conflitante; duas fontes copiadas da mesma origem; tarefa privada; indisponibilidade da busca semântica; troca de LLM; retirada de skill; resultado concorrente obsoleto; e restauração da coleção/índice.

Não declarar um único “percentual de compreensão”. Publicar métricas por dimensão, amostra e incerteza. Zero incidentes num piloto não é prova de ausência de risco.

## 13. Plano comum de entrega

Todos os documentos usam as mesmas fases, sem autorização automática de uma para outra:

| Fase | Entrega | Condição de avanço |
|---|---|---|
| F0 — especificação | escopo, contratos, corpus público permitido, rubricas e orçamento | revisão dos requisitos e decisão humana |
| F1 — piloto em sombra | catálogo derivado e recuperação sobre cópias, sem controlar produção | trilha de origem reconstruível |
| F2 — avaliação | comparação pareada, falhas, custo e restauração | ganho relevante sem regressão crítica |
| F3 — integração protegida | diff, testes, revisão e assinatura | fluxo P-8 e autorização de aplicação |

Editorial automático e grafos avançados são extensões condicionadas aos resultados, não pré-requisitos do piloto. Toda interface futura deve aparecer no painel conforme a diretriz existente, com fases e status reais.

## 14. Referências e decisão

[Registro de fontes verificadas](auditoria-2026-11-04/fontes.md) identifica versão e nível de leitura. Os resultados externos orientam hipóteses; não são métricas do Agata.

A direção da nova versão está aprovada pelo Humano. Esta revisão entrega documentação e instrumentos de auditoria. Execução de avaliações com modelos, aquisição de acervo, instalação de skills e integração protegida dependem dos respectivos escopos e orçamentos aprovados.
