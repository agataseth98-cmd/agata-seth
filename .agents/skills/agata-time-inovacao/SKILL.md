---
name: agata-time-inovacao
description: Como o time de inovação do Agata propõe melhorias com SDD: pesquisa, spec, revisão independente, decisão humana e só então proposta P-8. Use ao propor uma melhoria nova ou ao avaliar uma ideia já registrada no backlog.
---

# Time de inovação (SDD)

Por quê: ideia sem evidência vira retrabalho, e ideia sem revisão vira alucinação com cara de plano. O time transforma uma melhoria em artefato de SDD antes de qualquer código.

## Papéis (agentes em .claude/agents)
- agata-inov-pesquisa: bootstrap. Busca estado da arte e problema real do Agata, com fonte e evidência.
- agata-inov-arquiteto: draft. Escreve brainstorm e spec mínima (critério com teste, reversão, código a tocar).
- agata-inov-critico: review independente. Procura reuso, falha de governança, critério sem teste, custo.
- Auditoria do processo: a mesma pessoa que audita o lote, com o checklist de agata-processo-lote.

## Ciclo (uma ideia por vez)
1. Pesquisa: a ideia tem problema com evidência do Agata e fonte externa. Sem as duas, fica "não verificado" e não avança.
2. Entrevista (P1, 11/11): antes da spec de ideia nova de comportamento, o orquestrador, que fala com o Humano, faz até 5 perguntas de múltipla escolha. Usa AskUserQuestion quando houver; senão, lista numerada no texto. Cada resposta vai para `decision.md` na pasta de trabalho, com a pergunta e a opção escolhida. Sem resposta do Humano, a spec não começa. Base: code.claude.com/docs/en/best-practices, "Interview me until you could write the spec". Manutenção sem ideia nova não passa por aqui.
3. Spec: o arquiteto lê `decision.md` e escreve brainstorm e spec fora do repositório. Nada de código ainda.
4. Revisão: o crítico avalia a spec. Se o crítico recomendar reduzir escopo ou arquivar, o time segue a recomendação ou registra por que não segue.
5. Decisão: o Humano decide avançar, reduzir ou arquivar. O time nunca decide.
6. Proposta P-8: se avançar, a implementação entra como lote, pelo processo de agata-processo-lote. Uma proposta, uma assinatura.
7. Implementação e drift: depois da aplicação, roda-se o ciclo SDD da spec e o relatório de drift (cada critério passa, falha ou não roda).

## Backlog
Ideias ficam num backlog de trabalho fora do repositório (Área de trabalho, pasta de inovação do Experimento 2), com: id, problema, evidência, hipótese, estado (pesquisada, spec, revisada, decidida, proposta, aplicada, arquivada), decisão do Humano e data. Ideia arquivada também fica registrada, com o motivo.

## Regras
- Não recomende código que o reuso já cobre. O crítico confere com grep antes.
- Todo critério tem teste ou é marcado como lacuna.
- Medição de custo e cota: diga "não medido" quando não tiver medição.
- Subagente só quando a sessão permitir e o Humano pedir (ver agata-processo-lote).
- Nenhum agente do time assina, aplica ou junta PR.

## Diário de erros e acertos
(Acrescente uma linha por rodada: o que funcionou, o que o crítico derrubou, o que virou regra.)
