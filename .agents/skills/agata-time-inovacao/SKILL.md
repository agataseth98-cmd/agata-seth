---
name: agata-time-inovacao
description: >-
  Como o time de inovação do Agata propõe uma melhoria com SDD: pesquisa com fonte, entrevista do Humano, spec
  com revisão independente, decisão humana e só então proposta P-8. Inclui o método elefante e peixinhos
  dourados (contexto para desenhar, revisão sem contexto, drift depois). Use ao propor uma melhoria nova ou ao
  avaliar uma ideia já registrada no backlog.
---

# Time de inovação (SDD)

Por quê: ideia sem evidência vira retrabalho, e ideia sem revisão vira alucinação com cara de plano. O time transforma uma melhoria em artefato de SDD antes de qualquer código. Uma ideia por vez.

## 1. Método

- **Elefante:** modelo com contexto do sistema, usuários, restrições e histórico. Conduz a descoberta e escreve a proposta.
- **Peixinhos dourados:** revisores independentes que recebem só a proposta, o código necessário e a pergunta de revisão. Não recebem a conversa nem as justificativas do elefante.
- **Humano:** escolhe trade-offs, aprova a especificação e autoriza a mudança.
- Não afirme que existe plugin oficial instalado sem prova local. Este método é adaptação operacional.
- Explique ao Humano em termos de decisão: objetivo, risco evitado, opções, custo e decisão pendente. Ele deve poder responder "entra", "não entra" ou "revisar". A aprovação da spec não substitui a assinatura nem os gates de P-8.
- Pare e peça decisão quando houver requisito conflitante, dependência não medida, risco sem reversão, revisão independente ausente, ou drift sem classificação baseada em evidência.

## 2. Papéis (agentes em `.claude/agents/`)

- `agata-inov-pesquisa`: bootstrap. Estado da arte e problema real do Agata, com fonte e evidência.
- `agata-inov-arquiteto`: draft. Escreve brainstorm e spec mínima (critério com teste, reversão, código a tocar).
- `agata-inov-critico`: revisão independente. Procura reuso, falha de governança, critério sem teste, custo.
- Auditoria do processo: a mesma pessoa que audita o lote, com o checklist de `agata-aplicar-proposta`.

## 3. Ciclo (uma ideia por vez)

1. **Pesquisa.** A ideia tem problema com evidência do Agata e fonte externa. Sem as duas, fica "não verificado" e não avança.
2. **Entrevista (11/11).** Antes da spec de ideia nova de comportamento, o orquestrador, que fala com o Humano, faz até 5 perguntas de múltipla escolha. Usa a ferramenta de pergunta se houver; senão, lista numerada no texto. Cada resposta vai para `decision.md` na pasta de trabalho, com a pergunta e a opção escolhida. Sem resposta do Humano, a spec não começa. Base: code.claude.com/docs/en/best-practices, "Interview me until you could write the spec". Manutenção sem ideia nova não passa aqui.
3. **Draft.** O arquiteto lê `decision.md` e escreve brainstorm e spec fora do repositório, por partes: jornadas críticas; contrato e critérios de aceite; desenho e alternativas; implementação, testes, migração e reversão; riscos e dependências. Nada de código ainda. Perguntas do brainstorm: quem usa, qual estado muda, o que não pode quebrar, erros, concorrência, migração, observabilidade, reversão, sucesso.
4. **Revisão independente.** O crítico avalia a spec sem a conversa: já existe capacidade equivalente? há caminho mais simples? o que quebra sob carga, repetição ou dado antigo? a spec é implementável sem adivinhação? o aceite prova comportamento real? Se recomendar reduzir escopo ou arquivar, o time segue ou registra por que não segue.
5. **Consolidação.** Preserve as divergências, responda aos achados e deixe o Humano decidir conflitos. Não reescreva a revisão para ela concordar.
6. **Decisão.** O Humano decide avançar, reduzir ou arquivar. O time nunca decide.
7. **Proposta P-8.** Se avançar, a implementação entra como lote, pelo processo de `agata-aplicar-proposta`. Uma proposta, uma assinatura.
8. **Drift.** Depois da aplicação, compare a spec aprovada com o código e o comportamento observado, item por item. Cada diferença sai como intencional registrada, defeito, requisito mudado ou spec desatualizada. Cada critério passa, falha ou não roda.

Artefatos mínimos: bootstrap, concept brief, spec, relatórios independentes, consolidação, decisão humana e drift report. Em área protegida, o artefato acompanha a proposta, sem substituir o `.diff` e o `APROVADO-<nome>` assinado.

## 4. Backlog

Ideias ficam num backlog de trabalho fora do repositório (pasta de inovação do Experimento 2), com: id, problema, evidência, hipótese, estado (pesquisada, spec, revisada, decidida, proposta, aplicada, arquivada), decisão do Humano e data. Ideia arquivada também fica registrada, com o motivo.

## 5. Regras

- Não recomende código que o reuso já cobre. O crítico confere com grep antes.
- Todo critério tem teste ou é marcado como lacuna.
- Medição de custo e cota: "não medido" quando não tiver medição.
- Subagente só quando a sessão permitir e o Humano pedir.
- Nenhum agente do time assina, aplica ou junta PR.
- Experimento (rodada com critério prévio, splits, registro append-only) está em `agata-llm-fundamentos`, seção "Rodar um experimento".
