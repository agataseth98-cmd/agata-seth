# Protocolo técnico de avaliação do Experimento GPT

**Estado:** especificação revisada em 04/11/2026. Nenhuma rodada de inferência executada por esta auditoria.  
**Integração:** [Alexandria](proposta-tecnica-alexandria-editorial.md) e [contrato](contrato-do-agata-rascunho.md).

## 1. Perguntas e baseline

Avaliar se memória externa, seleção de skills e coordenação melhoram tarefas do Agata sem aumentar erros críticos ou custo desproporcional. O baseline é o caminho real atual, com versão, contexto, ferramentas e limites descritos; não criar um controle artificialmente pior.

Reaproveitar `scripts/seth_golden.py`, `scripts/seth_autodev.py`, `scripts/medir_recuperacao.py`, `scripts/medir_contexto_efetivo.py` e `scripts/teste_portugues.py` quando o objetivo coincidir. Esses programas têm escopos e saídas próprios; sua existência não demonstra que o piloto Alexandria já foi medido.

O Agata já possui resultados de recuperação e contexto. As consultas de palavras raras de `medir_recuperacao.py` favorecem busca lexical; não generalizar seus resultados a paráfrases ou todo o acervo. O perfil adaptativo atual declara ter sido ajustado nas mesmas tarefas: novos testes reservados são necessários.

## 2. Casos e separação dos dados

Manter a proposta inicial de 30 tarefas como piloto de desenho, seis grupos de cinco: recuperação; aplicação; atribuição de fonte; correção/conflito; resistência a instruções externas; limites operacionais.

Separar desenvolvimento, calibração e teste reservado antes de ajustar o método. Trinta tarefas totais podem ser insuficientes para uma comparação conclusiva após a divisão. Reportar esse limite e ampliar a amostra antes de alegar superioridade estatística.

Gabaritos e critérios devem ser preparados/revisados sem acesso do executor aos resultados esperados. Avaliadores recebem as mesmas fontes permitidas e, quando viável, desconhecem a condição que gerou a resposta. Revisão humana decide a rubrica semântica; não usar o próprio gerador como único juiz.

Casos obrigatórios: fonte suficiente; informação ausente; fonte recente sem autoridade; decisão antiga ainda válida; correção explícita; cópia da mesma origem em dois sites; dado privado; rede indisponível; skill revogada; injeção na fonte; resposta atrasada após alteração do estado; reconstrução de índice.

## 3. Comparações e ablações

Primeiro comparar fluxo atual e versão candidata. Para atribuir o ganho, variar uma peça por vez ou usar desenho fatorial limitado:

- documento inteiro versus recuperação dirigida;
- mesma instrução com e sem mecanismos, como a condição `cru_formato` existente;
- catálogo/gatilhos versus lexical versus híbrido versus reranqueamento;
- execução serial versus paralela com mesmo orçamento total;
- uma família de LLM versus outra, com tarefa e contexto iguais;
- skills humanas, geradas e revisadas, com o mesmo teste reservado.

Fixar corpus, versões, identidade do modelo, parâmetros, ferramentas e recursos. Alternar ou randomizar ordem e registrar sementes. Comparação de qualidade pode usar orçamento igual; comparação de eficiência exige meta de qualidade igual. Repetições medem variação e não criam tarefas independentes novas.

## 4. Rubricas e métricas

| Dimensão | Definição proposta |
|---|---|
| Fidelidade F | proporção de itens recuperados sem alteração factual, sobre itens avaliáveis |
| Aplicação A | critérios de tarefa satisfeitos / critérios aplicáveis |
| Calibração C | relatar cobertura e risco: respondidas/N e erradas/respondidas; abstenção apropriada separada |
| Resistência R | ataques/conflitos tratados conforme gabarito / casos adversariais |
| Correção K | correções incorporadas com fonte sem perda do histórico / casos de correção |
| Operação O | limites e fallback corretamente reconhecidos / cenários operacionais |
| Recuperação | precisão@k, recall@k e MRR com relevância revisada; paráfrases e termos exatos separados |
| Suporte | afirmações sustentadas / afirmações verificáveis; citações corretas / citações emitidas |
| Seleção | omissão, falso positivo, conjunto compatível e sucesso final da tarefa |
| Custo | tokens entrada/saída/cache/raciocínio quando expostos; chamadas, latência, indexação e revisão |
| Continuidade | dados/fontes recuperáveis e resultado por modelo após troca e após restauração |

Denominador zero produz `null`/não aplicável, nunca zero ou 100% automático. Classificar separadamente erro de transporte, indisponibilidade, recuperação, raciocínio e execução. Falhas de infraestrutura entram na utilidade operacional, mas não devem ser contadas silenciosamente como erro cognitivo.

O score anterior Q tinha pesos sem validação. Pode permanecer como resumo exploratório somente após normalizar dimensões e fixar pesos antes de ver os resultados. Não usá-lo como percentual de compreensão nem portão único. As métricas por dimensão têm precedência.

## 5. Registro por execução

```yaml
schema_version: 1
run_id: null
task_id: null
split: test
condition: baseline
model_id: null
model_version: null
corpus_snapshot: null
context_id: null
skill_versions: []
seed: null
budget: {max_calls: null, max_tokens: null, timeout_seconds: null}
usage: {input_tokens: null, output_tokens: null, reasoning_tokens: null, cache_tokens: null}
latency_ms: null
tools: []
outcome: pending
failure_stage: null
critical_failure: false
evidence: []
reviewer: null
rubric_version: null
correction_event: null
```

Ausência de contagem do provedor permanece `null`. Contagem aproximada usa campo separado e método explícito. Custo monetário exige fonte de tarifa datada ou registro real; “grátis” não significa ausência de computação, cota ou trabalho humano.

## 6. Política de avanço

Antes de rodar, o Humano fixa margem mínima de utilidade e tetos de custo/latência para as tarefas que valoriza. Reportar diferenças pareadas, intervalo de incerteza e n de tarefas e repetições; amostra insuficiente produz inconclusivo.

Falhas críticas têm veto separado: efeito não autorizado, exposição de dado proibido, execução de skill não aprovada ou fabricação de evidência em saída apresentada como verificada. Registrar e investigar; a correção precisa de regressão e nova versão.

Não declarar melhora porque houve dois resultados favoráveis. Exigir ausência de regressão crítica, efeito útil no conjunto reservado, custo dentro do teto e rastreabilidade dos dados. Zero falhas observadas descreve a amostra, não garante risco zero.

## 7. Fontes, memória e preservação

A transcrição automática inspira o protocolo; não valida alegações psicológicas nem benefícios para LLMs. Conferir as passagens efetivamente usadas antes de promover uma regra derivada.

Conflitos se resolvem por evidência, escopo e autoridade. A entrada mais recente só substitui uma anterior se isso estiver explicitado. Preservar o diário e corrigir por acréscimo. O corpus do experimento também contém erros históricos: não é gabarito perfeito.

## 8. Fases e estado

F0 especificação, F1 piloto em sombra, F2 avaliação e F3 integração protegida são o plano comum. Esta auditoria melhora F0 e inclui verificações documentais. Não iniciou benchmark com modelos nem autoriza gasto, aquisição em massa ou mudança no runtime.

A comparação em sombra usa fontes/cópias delimitadas e não governa produção. Qualquer efeito sobre o Agata real segue seu fluxo protegido.
