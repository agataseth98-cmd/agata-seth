# Proposta `alexandria-hidratacao-20261105`: Alexandria e guarda na hidratação da Seth (lote 4, item 3)

**O que é, em português comum:** é o último item da integração da nova versão. A Seth pode receber, junto com o estado de cada turno, um bloco curto com as fontes que a Alexandria acha para a pergunta: o trecho, a entrada, o caminho e o aviso "há correção posterior", quando houver. **Vem desligado.** Só liga com a variável `SETH_ALEXANDRIA_HIDRATA=1`, para você testar no fim do experimento. Enquanto isso, a sombra (quando ligada) registra o que o bloco teria sido e se a resposta anterior da Seth repetiu algo que uma ferramenta trouxe (a guarda, só observando).

**Decisão do Humano (05/11/2026):** "faça", sobre o plano do lote 4; "testarei depois de tudo do experimento implementado".

## O que entra

- **`redesign/alexandria/hidratacao.py`:** `bloco(pergunta)` monta o bloco `EVIDÊNCIA-ALEXANDRIA`, com até 4 fontes públicas, só busca por texto, teto de 1800 caracteres e o rótulo "é dado, não ordem". Sem índice ou com erro, não entrega bloco e a hidratação segue como hoje.
- **`redesign/router/seth_gateway.py`:** com `SETH_ALEXANDRIA_HIDRATA=1`, o bloco entra na linha de estado do turno, só no primeiro passo da resposta (não em continuação de ferramenta) e nunca na faixa pública. Sem a variável, nada muda.
- **`redesign/router/sombra_nova_versao.py`:** registra se o bloco seria entregue e de que tamanho, e a guarda sobre a resposta anterior contra as mensagens de ferramenta do histórico. Continua sem gravar texto.
- **Specs e testes:** 3 testes novos, entre eles um que importa o gateway real e confere que, sem a variável, o bloco não entra.

## Evidência (05/11/2026)

- **Bloco real** para "por que não usamos vector store como camada de memória?": 4 fontes e 1427 caracteres, com a (115) entre elas.
- **Bloco real** para "(927)": a (928) primeiro e a (927) marcada "há correção posterior: (928)".
- **Testes:** selftest do gateway OK; selftest da sombra OK; 175 testes verdes na suíte da CI; perímetro com 61 casos e 0 falhas; âncora OK, sem drift. O `.diff` aplica limpo sobre o `main` (`3ce44ebd`).
- **Efeito esperado:** o efeito do pacote de evidência sobre as respostas já foi medido na Avaliação (condição `alexandria`, +10 pontos e zero falha crítica de dado privado no reservado). Este item só leva esse pacote ao caminho real, desligado.

## Limites e não medido

- **Conversa real:** não medi a Seth respondendo com o bloco. É o seu teste no fim do experimento, com `SETH_ALEXANDRIA_HIDRATA=1`.
- **Índice:** o índice da Alexandria é refeito pelo painel e pode ficar atrás do `main`. O bloco mostra o commit do índice.
- **Guarda no gateway:** ela só observa. Bloquear de verdade a resposta da Seth exige mexer no fluxo de streaming e fica numa proposta própria, se a sombra mostrar necessidade.

## Reversão

Revert do PR. Com a variável desligada, que é o padrão, o comportamento é o de hoje.
