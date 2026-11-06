# Fundamentos LLM — revisão experimental

**Estado:** proposta revisada em 04/11/2026; aplicação conceitual da skill real `agata-llm-fundamentos`.  
**Referência de integração:** [Alexandria](proposta-tecnica-alexandria-editorial.md).  
**Método:** [avaliação](proposta-implementacao-buracos-experimento.md).

## Modelo e memória

Uma LLM autorregressiva gera tokens condicionada aos pesos e à entrada. Os pesos codificam padrões aprendidos, inclusive conhecimento e vieses. Durante inferência usual eles não mudam a cada conversa. Estado transitório inclui contexto, ativações e caches; a aplicação pode persistir histórico e reutilizar estado.

É possível manter a memória persistente do produto no Agata. Isso não desliga o conhecimento paramétrico: o modelo continuará usando os pesos. A política documental deve exigir suporte em fontes para afirmações sobre a coleção, com abstenção quando faltar evidência.

A memória preservada pode ser entregue a outra LLM; identidade de respostas e fidelidade não são garantidas. O teste de substituição mede recuperação, aplicação das regras, suporte e custo para cada modelo.

## Metacognição operacional

Antes: delimitar tarefa, autorização, privacidade, risco e recursos; recuperar apenas o necessário e selecionar procedimento. Durante: observar saídas, ferramentas, erros e consumo. Depois: comparar com o pedido, testar quando cabível, revisar suporte e registrar correção por entrada nova.

Esses controles observam comportamento e evidências; não dão acesso confiável aos mecanismos internos do raciocínio. Explicações da própria LLM também são saídas sujeitas a erro.

| Falha | Reaproveitar no Agata | Limite |
|---|---|---|
| Estado inventado | comandos fixos, gateway e auditoria de turno | auditoria mecânica não julga toda prosa |
| Recuperação inadequada | vault, busca lexical, semântica secundária | medir por tipo de consulta; similaridade não prova suporte |
| Contexto excessivo | hidratação limitada e consulta sob demanda | janela declarada não equivale a raciocínio efetivo |
| Formato inadequado | harness e perfil por modelo | JSON estruturado pode ajudar um modelo e prejudicar outro |
| Skill inadequada | catálogo e gatilhos; seleção híbrida candidata | leitura integral do SKILL selecionado, referências sob demanda |
| Erro de fonte | trecho, origem, versão e qualificação | hash e consenso não demonstram verdade |
| Pressão material | telemetria e fila de recursos | coleta proporcional; dado ausente vira não medido |

A skill real contém pesquisas e lacunas datadas. A revisão encontrou métricas já disponíveis em `scripts/medir_recuperacao.py`, `scripts/medir_contexto_efetivo.py` e `scripts/teste_portugues.py`; não repetir alegações antigas de ausência sem conferir a versão.

## Skills, agentes e execução

Primeiro aplicar autorização e limites; depois selecionar candidatos por pedido explícito e gatilhos. Recuperação híbrida e reranqueamento são hipóteses para aumentar precisão em catálogos grandes, sujeitas a comparação local. Indexar o corpo pode ajudar a busca sem carregar toda a biblioteca no contexto.

Papéis podem ser implementados por código ou por LLM. Hashes, filtros, filas e metadados exatos cabem em código. Revisão semântica pode exigir modelo e Humano. Paralelismo é seletivo; todos os agentes não recebem todos os dados, pois há escopo, acesso e silos.

## Continuidade e evolução

`conclusoes.md` é o protótipo manual de continuidade. Correções explícitas evitam priorizar erro recente só pela data. Registros provisórios podem preservar hipóteses rotuladas; promoção normativa exige o fluxo correspondente.

As sete palavras orientam o ciclo com retornos e Remoção opcional, conforme a máquina especificada em Alexandria. Consciência operacional descreve um modelo verificável do estado; as analogias humanas não constituem evidência de experiência subjetiva.
