# PROPOSTA — Agata Voz: continuidade intelectual e confirmação falada
Data da decisão oral: 13/10/2026 (America/Sao_Paulo)
Estado: PROPOSTA para revisão; NÃO é registro canônico em MEMÓRIAS.md.
Origem: interação vocal com o Humano; trechos abaixo são sínteses, não transcrição literal integral.

## Decisão expressa pelo Humano
O Humano solicitou canonizar a interação vocal e, em seguida, especificou que a implementação e a validação deveriam ocorrer por voz, para testar segurança, detectar falhas e preservar o tom, a cadência e a velocidade de fala considerados adequados. A autorização não elimina os portões de verificação, a checagem contra o cânone nem a necessidade de comprovação por Máquina.

## Princípio proposto
Continuidade intelectual verificável exige preservar **informação + origem + razões + evidências + incerteza**. Um sucessor não deve apenas repetir uma narrativa coerente: deve conseguir justificar decisões, localizar suas fontes e distinguir fato de hipótese.

## Protocolo experimental por voz
1. Captar a fala, registrar o texto reconhecido e indicar confiança quando o módulo oferecer essa informação. Nunca fingir certeza sobre áudio ambíguo.
2. Interpretar intenção e distinguir conversa, registro, proposta e execução.
3. Antes de ação com efeitos persistentes, ler de volta em português simples **o objeto exato, o alcance e o efeito**; solicitar confirmação explícita em turno separado. Silêncio não autoriza.
4. Executar apenas pela interface já permitida e com privilégios mínimos. Não converter comando de voz diretamente em shell ou operação Git de escrita.
5. Confirmar a execução por evidência de Máquina: commit, diff, teste, arquivo ou resposta do serviço; alegação de modelo não é prova.
6. Preservar trilha auditável: data/hora de Máquina, identificador da tarefa, texto reconhecido corrigível, decisão, confirmação, resultado, erro e referência à evidência. Redigir segredos e dados pessoais; não publicar áudio bruto nem conversas privadas no repositório público.
7. Suportar interrupção e retomada sem executar a frase incompleta. Permitir correção do reconhecimento antes da confirmação.
8. Manter rota alternativa textual quando STT, TTS, gateway ou rede falharem.
9. Verificar a continuidade em modelo diferente, com um registro mínimo, sem entregar a transcrição toda: pedir razões, evidências e lacunas. Registrar divergência sem inventar consenso.
10. Medir: erros de transcrição, comandos indevidos, confirmações incorretas, latência, taxa de retomada correta, custo de tokens e integridade dos registros.

## Estilo falado aprovado para teste
Português brasileiro natural, calor humano sem simulação de intimidade; frases curtas, ritmo conversável, pausas significativas, velocidade moderada e adaptável, precisão sem pedantismo, beleza sem excesso. Não fixar alteração de timbre, que depende do motor TTS e não foi verificada. Sem imitar identidade vocal humana. Nome provisório: Agata Flow Vanilla.

## Critérios de aceite
- Ao menos 10 casos, incluindo: áudio ambíguo; comando parcial; interrupção; negativa de confirmação; replay/duplicação; ação destrutiva; falha da rede; falha de TTS; correção de STT; reconstrução por outro modelo.
- Zero alteração persistente não autorizada nos casos de teste.
- Evidências de execução e limites conhecidos relatados separadamente.
- Comparação com o comportamento atual sem alterar os componentes estáveis antes do aceite.

## Preservação do cânone
- REGRAS.md: Humano decide; Máquina verifica; Modelo propõe. Histórico não é reescrito.
- Mudança de padrão transversal requer segunda opinião independente, ou assunção formal de risco pelo Humano, e portão das três perguntas, uma por vez.
- MEMÓRIAS.md: consultar topo remoto antes de numerar; acrescentar entrada nova, sem editar antigas, junto de ONDE_ESTAMOS.md no mesmo commit quando a decisão mudar estado.
- Esta proposta não declara `sync: PASS` nem implementação funcional do pipeline. A consulta do conteúdo atual de MEMÓRIAS.md permaneceu incompleta nesta sessão.
- Não distribuir MOD privado entre famílias nem publicar dados pessoais.

## Próximo passo
Revisão confederada independente e teste de uma ordem não destrutiva integralmente por voz, com confirmação e evidência. Somente após os portões aplicáveis registrar a decisão no cânone.
