---
name: elephant-goldfish-sdd
description: "Orientar o Humano e os modelos a aplicar SDD 2.0 em funcionalidades grandes ou arriscadas: contexto profundo para desenhar, revisão independente com contexto mínimo e verificação de drift depois da implementação."
---

# Elephant–Goldfish SDD para Agata

Use quando uma mudança exigir decisões de arquitetura, afetar vários componentes, tiver alto custo de erro ou precisar de critérios de aceite explícitos. Não use para correções pequenas, locais e claras.

## Conceito

Desenhe com o elefante, revise com peixinhos dourados e decida como Humano.

- **Elefante:** modelo com contexto do sistema, usuários, restrições e histórico. Conduz descoberta e escreve a proposta.
- **Peixinhos dourados:** revisores independentes que recebem só a proposta, o código necessário e a pergunta de revisão. Não recebem a conversa nem as justificativas do elefante.
- **Humano:** escolhe trade-offs, aprova a especificação e autoriza a mudança.

Esta é uma adaptação operacional da transcrição fornecida. Não afirmar que existe um plugin oficial instalado sem prova local.

## Orientação didática ao Humano

Explique em termos de decisão: objetivo, risco evitado, opções, custo e decisão pendente. O Humano deve poder responder “entra”, “não entra” ou “revisar”. A aprovação da especificação não substitui a assinatura nem os gates de P-8.

## Ciclo

1. **Bootstrap:** mapear diretórios, contratos, usuários, invariantes, serviços, testes, fronteiras de segurança e mudanças recentes. Registrar fontes e separar fato medido, inferência e “não medido”.
2. **Brainstorm:** perguntar quem usa, qual estado muda, o que não pode quebrar, erros, concorrência, migração, observabilidade, reversão e sucesso. Gerar concept brief com alternativas e trade-offs.
3. **Draft:** escrever e aprovar por partes: jornadas críticas; contrato e critérios de aceite; desenho e alternativas; implementação, testes, migração e reversão; riscos e dependências.
4. **Review independente:** distribuir perguntas a revisores sem contexto da conversa: já existe capacidade equivalente? há caminho mais simples? o que quebra sob carga, repetição ou dados antigos? a spec é implementável sem adivinhação? o aceite prova comportamento real?
5. **Consolidação:** preservar divergências, responder aos achados e deixar o Humano decidir conflitos. Não reescrever a revisão para fazê-la concordar.
6. **Implementação:** somente após decisão humana; em Agata, manter worktree própria e separar proposta de aplicação.
7. **Drift report:** comparar a spec aprovada com código e comportamento observado, item por item. Classificar cada diferença como intencional registrada, defeito, requisito mudado ou spec desatualizada.

## Artefatos mínimos

`bootstrap`, `concept brief`, `spec`, relatórios independentes, consolidação, decisão humana e `drift report`. Em áreas protegidas, acompanhar a proposta, sem substituir `.diff` e `APROVADO-<nome>` assinado.

## Pare

Peça decisão quando houver requisito conflitante, dependência não medida, risco sem reversão, revisão independente ausente ou drift sem classificação baseada em evidência.
