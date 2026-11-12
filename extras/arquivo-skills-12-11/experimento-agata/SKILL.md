---
name: experimento-agata
description: Planejar, executar, analisar e registrar experimentos semânticos e avaliações de confiabilidade interna do Agata no Experimento 2. Use para tarefas desta pasta; não autoriza alterações no runtime.
---

# Experimento Agata

Use esta skill para conduzir rodadas da pasta Experimento 2 e incorporar aprendizados comprovados sem transformar uma observação isolada em regra geral.

## Fontes locais

Antes de desenhar ou executar uma rodada, leia apenas as partes necessárias de:

- `protocolo.md` (documento do Experimento 2, fora do repositório) para famílias semânticas, métricas e separação dos conjuntos;
- `direcao-e-confiabilidade.md` (documento do Experimento 2, fora do repositório) para a trilha de confiabilidade do sistema;
- `templates/registro-execucao.yaml` (documento do Experimento 2, fora do repositório) para registrar cada execução;
- o diário do Experimento 2 (fora do repositório) (documento do Experimento 2, fora do repositório) para decisões, resultados e correções anteriores.

A bateria semântica e os gates de confiabilidade são avaliações diferentes. Não combine resultados em uma nota única.

## Antes da rodada

1. Defina pergunta, baseline, tarefas, split, condição, versão do modelo, prompt, ferramentas, avaliador, métrica, denominador, orçamento e regra de parada antes de observar resultados.
2. Se algum critério essencial estiver aberto, trate o trabalho como desenho ou exploração; não chame o resultado de aprovado.
3. Separe desenvolvimento, calibração e teste reservado. Não use o reservado para ajustar prompt, rubrica ou seleção de modelo; preserve o sigilo do conjunto reservado.
4. Não inicie inferência paga, chamada externa, coleta de dados ou efeito no runtime sem escopo e autorização próprios.

## Executar e registrar

- Atribua `experiment_id`, `run_id` e `task_id`; registre condição, versões, parâmetros, orçamento, uso, ferramentas, saída, hash, avaliador e falha por etapa no template.
- Preserve saídas e registros originais quando permitido; remova segredo e dado pessoal. Hash confirma integridade dos bytes, não correção semântica.
- Rotule cada caso `pass`, `fail`, `inconclusive` ou `not run`, sempre junto da evidência e do critério prévio. Se o gabarito ou a execução falhar, não converta isso em acerto do modelo.
- Em revisão de código, diferencie análise estática, reprodução isolada de função e validação ponta a ponta. Uma reprodução local confirma apenas o caminho reproduzido; não prova comportamento do navegador, serviço ou produção.
- Use revisão independente quando agregar valor: forneça ao revisor a pergunta e o código necessário, sem a resposta esperada. Preserve divergências e confira alegações no código ou na medição.
- Se o Humano já estiver executando uma suíte, não a interrompa nem duplique; faça análise estática ou diagnóstico isolado e declare o que ficou sem medir.

## Aprender com acertos

- Chame um resultado de **acerto** somente quando o critério foi fixado antes da rodada e a evidência satisfaz esse critério. Sem isso, registre uma observação exploratória.
- Depois de cada acerto, acrescente a o diário do Experimento 2 (fora do repositório) uma entrada nova com escopo, evidência, condições, denominador, limites e próxima decisão. Não reescreva entradas antigas; correções são novas entradas.
- Atualize esta skill somente quando o acerto sustentar uma regra reutilizável. Registre a regra de forma curta, com link/data da evidência e limites de aplicação. Um sucesso isolado pode gerar um resultado local, mas não uma regra universal.
- Não transforme concordância entre modelos em prova. Use-a como revisão; confirme o ponto com critério, fonte ou reprodução.

## Lições de método desta pasta

- Uma reprodução isolada de função é útil para localizar uma causa, mas não substitui uma validação ponta a ponta.
- Revisores independentes podem revelar uma decisão de política ainda não definida; resolva a semântica antes de afirmar que o sistema cumpre a regra.
- Em investigação de sistema, verifique qual branch/worktree e qual checkout o serviço realmente usa; um estado de desenvolvimento antigo pode não representar o runtime medido.

## Limites de mudança

Esta skill é um artefato local da pasta Experimento 2; não está instalada no menu do Agata. Para disponibilizá-la no sistema ou alterar código, configuração ou skills protegidas do Agata, siga a proposta P-8 assinada e o fluxo oficial. Esta skill não concede permissão para executar ações, mudar limites ou aprovar resultados.
