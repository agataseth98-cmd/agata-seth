# Handoff para o executor — nova versão do Agata

**Preparado em:** 04/11/2026  
**Direção do Humano:** esta arquitetura será a nova versão do Agata; Alexandria é um subsistema.  
**Estado:** documentação consolidada; nenhum componente novo foi implantado.

## Mandato

Transformar a arquitetura aprovada em entregas incrementais verificáveis no Agata real. Comece por validar o estado atual do repositório e converter a especificação em um plano técnico de piloto. Preserve componentes existentes que já atendem ao requisito; proponha a menor integração que permita medir o valor da nova arquitetura.

## Ordem de leitura

1. `AGENTS.md` e o fluxo vigente do Agata para sessão, equipe e mudanças protegidas.
2. `conclusoes.md`, especialmente as entradas 077–080, como memória do experimento e decisões humanas.
3. `LEIA-ME.md`, para precedência e mapa dos artefatos.
4. `proposta-tecnica-alexandria-editorial.md`, fonte do desenho integrado.
5. `proposta-implementacao-buracos-experimento.md`, fonte das métricas e critérios de avanço.
6. `contrato-do-agata-rascunho.md` e `proposta-tecnica-metacognicao-llm.md`, para autoridade e ciclo operacional.
7. `inventario-servicos-agata-2026-11-04.md`, `matriz-redundancia-agata-2026-11-04.md` e `auditoria-2026-11-04/relatorio.md`, como fotografia e evidência datadas, não como estado atual.

O snapshot de 04/11/2026 não substitui uma nova medição. Confirme HEAD, sync, alterações locais, propostas abertas, sessão da Equipe, serviços, capacidades e arquivos envolvidos no início do trabalho. Não conclua que um serviço ou modelo segue disponível com base no inventário histórico.

## Primeira entrega obrigatória: plano delimitado

Antes de editar o Agata real, entregue um plano curto que contenha:

- requisito de usuário e fluxo atual correspondente;
- componentes existentes a reutilizar e lacunas observadas no código atual;
- escopo mínimo do piloto em sombra, localização isolada e dados de teste permitidos;
- contratos de entrada e saída, estados, proveniência, permissões, concorrência, cancelamento e falha;
- baseline, casos reservados, métricas por dimensão e orçamento máximo proposto;
- arquivos e interfaces que seriam alterados, dependências e plano de retorno;
- riscos, questões sem evidência e decisões que precisam do Humano.

Não iniciar inferência paga, aquisição de acervo, gravação em memória/cânone, instalação de skill, alteração de serviço ou mudança protegida sem a autorização específica aplicável. A aprovação da direção do produto não substitui orçamento, consentimento para efeitos externos nem assinatura P-8.

## Sequência de implementação proposta

### F0 — especificação de execução

Confrontar esta documentação com o código e com o estado medido naquele momento. Resolver ambiguidades do piloto e propor critérios de aceite. Aproveitar os harnesses e mecanismos existentes; não criar um segundo cache, indexador, roteador ou sistema de avaliação sem justificar a lacuna.

### F1 — piloto em sombra

Após escopo e orçamento autorizados, implementar em área isolada, com corpus permitido e versão fixada. O piloto consulta cópias e produz registros auditáveis sem comandar respostas ou ações de produção. Toda saída aponta para objeto, trecho, versão e condição de acesso. Incluir baseline lexical/local, fluxo externo apenas quando permitido e falhas explícitas para indisponibilidade, conflito e contexto obsoleto.

### F2 — avaliação

Separar desenvolvimento, calibração e teste reservado. Comparar condições pareadas; medir suporte, recuperação, seleção, qualidade de tarefa, abstenção, falha operacional, latência, custo completo, privacidade e restauração. Repetições não contam como novas tarefas independentes. Publicar denominadores, incerteza, dados ausentes e resultados negativos; não reduzir a conclusão a um percentual de “compreensão”.

### F3 — integração protegida

Só depois de resultado útil e sem regressão crítica, preparar mudança em fluxo protegido, com diff, testes pertinentes, revisão e assinatura humana conforme as regras atuais do Agata. Alexandria não recebe autoridade normativa própria. O Humano decide avanço, redução de escopo ou encerramento.

## Invariantes de arquitetura

- Cânone, permissões, silos e autoridade humana precedem descoberta e roteamento.
- `conclusoes.md` é memória append-only do experimento; retificações entram como novos registros.
- Alexandria organiza conhecimento e pesquisa. Não substitui o cânone nem torna todo resultado catalogado verdadeiro.
- Pesos continuam contribuindo à geração. Memória externa não garante reprodução do comportamento após troca de modelo.
- A recusa documentada a vector store/GraphRAG como memória primária permanece. Qualquer revisão exige evidência nova e fluxo protegido.
- Skills são procedimentos; livros e fontes são conteúdo. Encontrar um documento não executa uma skill.
- Remoção é transição opcional. Estados editoriais, de execução e de saúde não se confundem.
- Paralelismo respeita orçamento e recursos compartilhados; consolidação usa versão e escrita idempotente.
- Catálogo, health check, acesso, inferência real e fila ativa são medições diferentes.
- Ausência na busca significa “não encontrado nesta busca”, não inexistência.

## Critérios para encerrar o handoff

O executor está pronto para propor o primeiro PR quando houver um plano delimitado, estado atual medido, arquivos identificados, critérios de aceite mensuráveis, plano de retorno e nenhuma contradição aberta com o cânone. O primeiro PR deve seguir o fluxo vigente para propostas; código de integração pertence a uma etapa posterior e separada.

## Referências

- [Especificação Alexandria](proposta-tecnica-alexandria-editorial.md)
- [Protocolo de avaliação](proposta-implementacao-buracos-experimento.md)
- [Contrato experimental](contrato-do-agata-rascunho.md)
- [Relatório e evidências da auditoria](auditoria-2026-11-04/relatorio.md)
- [Índice da pasta](LEIA-ME.md)
