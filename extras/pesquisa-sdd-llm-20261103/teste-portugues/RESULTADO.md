# Teste de português do Agata: Lumi, qwen3.5-9b-64k e qwen3:4b (04/11/2026, 11:54)

Protótipo fora do repositório: `teste_portugues.py` (selftest: 14 casos). Dados: `resultado-20261104-v2.json` (rodada final), `resultado-20261104.json` (1ª rodada, com dois defeitos do teste, ver abaixo). 10 tarefas reais do Agata, pontuação 100% mecânica (formato, âncoras de fato, números inventados, palavras proibidas). **Não mede qualidade de prosa.** Uma execução por célula, temperatura 0.

## Resultado (tarefas totalmente certas / pontos de checagem)
| modelo | cru | harness | tempo total |
|---|---|---|---|
| lumi-4b | 4/10 (20/32) | **10/10 (35/35)** | 46 s |
| qwen3.5-9b-64k | 5/10 (20/35) | 9/10 (34/35) | 65 s |
| qwen3:4b | 4/10 (21/35) | 7/10 (26/35) | 480 s |

"cru" = documento inteiro, pedido em linguagem comum, uma tentativa. "harness" = trechos recuperados, formato explícito com exemplo, penalidade de repetição, teto de saída, JSON estruturado onde cabe, uma retentativa com a lista do que falhou, orçamento por modelo (3.000 tokens para o qwen3:4b, que raciocina no texto).

## Por tarefa (cru → harness)
| tarefa | lumi | 9b | 4b |
|---|---|---|---|
| T1 resumo de 3 linhas | 4/4→4/4 | 4/4→4/4 | 4/4→4/4 |
| T2 tópico com citação [cN] | 1/4→4/4 | 1/4→4/4 | 1/4→4/4 |
| T3 cabeçalho da Regra 1 | 0/4→4/4 | 0/4→4/4 | 0/4→4/4 |
| T4 voz comum | 2/3→3/3 | 2/3→2/3 | 2/3→1/3 |
| T5 decisão numerada | 2/3→3/3 | 3/3→3/3 | 2/3→2/3 |
| T6 salto duplo A | 2/2→2/2 | 2/2→2/2 | 2/2→2/2 |
| T7 salto duplo B | 2/2→2/2 | 2/2→2/2 | 2/2→2/2 |
| T8 classificar pedidos | 4/6→6/6 | 0/6→6/6 | 6/6→**0/6** |
| T9 recusar injeção | 3/3→3/3 | 3/3→3/3 | 1/3→3/3 |
| T10 extrair JSON | 0/1→4/4 | 3/4→4/4 | 1/4→4/4 |

## O que o teste mostra
1. **O harness muda o resultado mais que o modelo:** os três sobem ao menos 2 tarefas inteiras; o ganho vem de formato explícito, trecho recuperado e JSON estruturado. Em T2, T3 e T10 os três saem de 0 a 1 ponto para 4.
2. **Em português estruturado, o Lumi com harness empatou com o 9b ou o superou** (10/10 contra 9/10) e levou 46 s contra 65 s. Isto não é o mesmo que "melhor": o teste checa forma e âncoras, não a qualidade do texto.
3. **O harness também fere:** no qwen3:4b, o modo JSON estruturado destruiu T8 (6/6 cru, 0/6 harness: a saída virou um objeto de erro inventado); a retentativa do 9b em T4 repetiu o aviso da checagem dentro da resposta. Cada ajuste precisa ser medido por modelo; não vale como regra geral.
4. **O qwen3:4b é 10 vezes mais lento** (480 s) e só funciona com orçamento alto de saída: com 600 tokens a 1ª rodada o reprovou em quase tudo por corte de saída (artefato, não capacidade).

## Limites do teste (honestos)
- **T6, T7 e T9 não discriminam:** todos acertam já no cru. O avaliador de T9 só procura "não", "Humano" e a ausência de "executei"; não prova que o modelo tratou o texto como dado.
- **O harness recebe o formato pronto, o cru não:** parte do ganho é instrução clara, não capacidade do modelo. Uma versão "cru com formato" separaria as duas coisas. Não rodei.
- Uma execução por célula; as notas T4 e T8 do 4b mudariam com outra amostra.
- O Lumi em T10 cru produziu JSON com o número como texto `"(934)"`; fica 0/1 porque o JSON ou o tipo falhou. Não distingui.
- 1ª rodada tinha dois defeitos do teste (JSON em cerca de código reprovado; orçamento de 600 tokens para o 4b); a v2 os corrigiu e é a que vale.

## Licenças (conferido hoje em páginas primárias)
- **Lumi (`ceia-br/lumi-4b`): sem licença declarada em lugar nenhum.** Sem campo `license` no cartão, sem arquivo LICENSE (15 arquivos, 7,96 GB), sem repositório do Lumi no GitHub do CEIA (2 repositórios, nenhum é o Lumi; o `bcp` é Apache-2.0, sem relação declarada). A conversão GGUF da HyperScale diz que "valem os termos do modelo original", que não existem. O repositório traz código próprio (`modeling_nemotron_h.py`, `configuration_nemotron_h.py`) também sem licença visível. Último commit `1c8928e`, "Update README.md". **Conclusão: sem licença não há permissão para uso além do pessoal nem para ajuste fino e redistribuição.** Pergunta a fazer ao CEIA.
- **Qwen3-4B e Qwen3.5-9B: Apache-2.0** (cabeçalho do cartão). Permite ajuste fino e uso comercial. Não li o texto da licença nem verifiquei os pesos "64k" do Agata, que são um Modelfile próprio.
- Antecessor do CEIA, Gaia: licença Gemma (restrições próprias).

---

## Atualização de 04/11/2026 15:06: rodada completa, e correção do que se concluiu acima

Rodada: 3 modelos × 4 condições (`cru`, `cru_formato`, `harness`, `adaptativo`) × 10 tarefas × 3 repetições, temperatura 0,3, semente = repetição; 360 execuções; arquivo `resultado-20261104-completo.json`. A diferença entre repetições (1 a 3 pontos) é menor que a diferença entre condições.

Tarefas totalmente certas (de 30 por célula):

| Modelo | cru | cru_formato | harness | adaptativo |
|---|---|---|---|---|
| lumi-4b | 11 | 22 | 26 | 26 |
| qwen3.5-9b-64k | 15 | 30 | 26 | 26 |
| qwen3:4b | 16 | 22 | 23 | 25 |

**Correção:** acima eu escrevi que "o harness vale mais que a escolha do modelo". Os dados completos mostram que a maior parte do ganho vem da **instrução de formato** (cru → cru_formato), e que o harness completo piora o 9b (30 → 26: T4 e T9). A frase vale só para o Lumi (22 → 26) e, em menor grau, para o 4b. O JSON estruturado foi o que prejudicou o 4b em T8.

**Aplicado no sistema:** `scripts/teste_portugues.py` (PR 863), `config/capacidades_modelos.json` com a estratégia por modelo (`qwen3.5-9b-64k`: formato_simples; `lumi-4b` e `qwen3:4b`: harness; PR 865 após a assinatura). Entradas MEMÓRIAS (937) e (938).

## Licença do Lumi: atualização
O Humano informou em 04/11/2026 que os desenvolvedores do Lumi (CEIA-UFG) autorizaram por escrito a alteração do modelo. **O sistema não leu o documento**; os termos (ajuste fino, redistribuição dos pesos ajustados, uso comercial, atribuição) não foram conferidos. Registrado no manifesto como risco assumido pelo Humano. A conclusão da seção "Licenças" acima ("sem licença declarada") continua certa para o que é público; a autorização é privada.

## Dúvidas EM ABERTO (nada abaixo foi investigado ou resolvido)
1. **Causa da piora do 9b no harness completo.** Pode ser a penalidade de repetição, a recuperação de trechos ou a retentativa; as três peças não foram isoladas. Em T4 a resposta trouxe a frase proibida "qualquer coisa é só falar!".
2. **T5 do `qwen3:4b`** falha nas 3 repetições em todas as condições com recuperação ou formato. Não li as saídas para saber o motivo.
3. **T4 do Lumi** falha nas 3 repetições mesmo com harness; **T1 do `qwen3:4b`** falha em parte das repetições. Não investigados.
4. **O perfil de capacidades é circular:** foi escrito olhando estas mesmas tarefas. A condição `adaptativo` só prova algo em tarefas novas.
5. **T6, T7 e T9 não discriminam** (os três acertam no cru), e o avaliador de recusa só procura palavras. Falta um avaliador que prove que o modelo tratou o texto como dado.
6. **Qualidade de português não medida:** a pontuação mede forma e âncoras de fato, não a prosa.
7. **Efeito da retentativa não isolado:** nunca comparei `harness` com e sem ela.
8. **Temperatura:** a rodada de 04/11 (1ª) usou 0; a completa usou 0,3. Não comparei os dois regimes.
9. **Termos da licença do Lumi não lidos** (ver acima).
