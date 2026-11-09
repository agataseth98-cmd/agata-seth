# Proposta: Fase F2 do Conselho, estudo como unidade (29/10/2026)

Depende da Fase F1 (`conselho-hidratacao-f1-20261029`). Aplicar a F1 antes.

O que muda em `conselho_rede.py`:
- **Tipo `estudo`:** a pergunta inteira vai a todos os participantes (2 a 9), de forma independente. Com nove, são nove aprovações individuais, como antes.
- **Síntese por estudo:** só roda quando todos os participantes terminam, e recebe todas as respostas de uma vez. Antes, a síntese saía por rodada e podia ignorar as outras.
- **Respostas limpas:** `limpa_resposta` remove linhas de raciocínio interno ("Thinking", "Trabalhou por", "Refletiu por" etc.) e corta cada resposta em 1.500 caracteres, marcando o corte. A resposta entra em outro prompt como dado, não como instrução.
- **Teto:** a síntese checa o tamanho com o contexto incluído.

Testes: 16 passam, incluindo `test_estudo_synthesis_waits_for_all_members_and_cleans_responses_f2`, que usa os nove provedores.

Não cobre ainda: visibilidade da aba e sanitização na extensão (F3), tela (F4), ferramentas (F5) e escrita (F6). Cada uma terá proposta própria.

Aplicação: depois da assinatura de F1 e de F2 (`bash scripts/aprovar.sh conselho-estudo-f2-20261029`).
