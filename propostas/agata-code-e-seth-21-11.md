# Proposta agata-code-e-seth-21-11 — lote único da manhã de 21/11 (uma assinatura)

Ordem do Humano, 21/11 11:39: "avance o máximo e me apresente apenas uma assinatura ao final".

**1. Medição do modelo do Agata Code** (`redesign/rotas/spec/medicao-agata-code-21-11.md`, novo). Pelo OpenCode, N=5, duas tarefas (contar .js de uma pasta; número da entrada mais recente de MEMÓRIAS). Só duas portas são permitidas pela política para código do repo (classe pessoal): `seth-livre` e modelo local pelo nome.
- seth-livre (atual): tarefa a 0/5 (escreve "próximo passo: usar glob" em texto, sem chamar), tarefa b 4/5.
- qwen3-30b local: a 2/5, b 1/5; com a regra "nunca responda sem ferramenta", a 3/5, b 5/5, mas 95–150 s por resposta.
- qwen3.5-9b local: respostas vazias, 4 min cada.
- **Decisão: nenhum chega a 4/5 nas duas; o modelo do Agata Code NÃO muda e a regra não entra no agente.** O selo NÃO VERIFICADO (aplicado hoje) continua sendo a proteção.

**2. Lições de voz nas instruções da Seth** (PROTOCOLOS.md, bloco SETH-GATEWAY, um parágrafo): frase cortada → pedir o resto; frase embaralhada → hipótese e "é isso?"; nomes trocados pela transcrição; nunca ficar muda; visitante sem jargão; repetir quando pedem; decisão por voz vai ao cache. Decisão do Humano de 20/11 (cache 697): as lições valem para todos os modelos.

**Fora do repo, sem assinatura:** organograma da Área de trabalho atualizado com 20 e 21/11 (antes/depois em ~/agata-arquivo/organograma-21-11/).

**Hipótese para o próximo lote (não implementada):** o seth-livre hidrata o Agata Code com a doutrina da Seth (cabeçalho, "resultado/evidência/próximo passo"), e o modelo responde no formato da Seth em vez de chamar a ferramenta. Teste: o gateway reconhecer o Agata Code e mandar doutrina de agente de código.

**Medido:** CI local TUDO OK (agente, com a medição); bruto em ~/agata-arquivo/agata-code-medicao-21-11/. **Reversão:** git revert. **Modelo:** Sonnet 5.5 (medição), Opus 5.5 (revisão, texto da Seth).
