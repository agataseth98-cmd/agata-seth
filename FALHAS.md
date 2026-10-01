# FALHAS.md — Catálogo de falhas conhecidas, por causa raiz

Cada linha é uma falha que já aconteceu de verdade neste sistema. Se você se pegar fazendo uma delas, pare.

O catálogo é organizado pela **causa raiz** — a regra que a falha viola —, não pela data. Falhas da mesma família têm a mesma origem e o mesmo antídoto: reconhecer a família antes de agir previne a próxima variante, inclusive as que ainda não aconteceram.

**Formato fixo:** ID estável · Sintoma · Causa raiz · Faça no lugar · Onde (entradas de MEMÓRIAS). O ID nunca é reaproveitado; cite-o como `FALHAS.md, FAB-2`.

| Família | Causa raiz comum | Regra violada |
|---|---|---|
| FAB — Fabricação de fatos | afirmar o que a Máquina não mediu | 2 |
| MED — Medição recusada | deixar de medir o que é mensurável | 1, 2 |
| IDF — Identidade e fronteiras | tomar como seu o que pertence a outro ator ou silo | 1, 3 |
| ART — Artefato trocado | entregar outra coisa no lugar do que foi pedido | 3 |
| CIT — Citação e proveniência | apresentar memória como cópia literal da fonte | 2 |
| SIN — Sincronia e atualidade | tratar estado antigo como estado atual | 2, 4 |
| INT — Integridade de dados | supor que o dado chegou, ficou ou cabe inteiro | 4, 7 |

---

## FAB — Fabricação de fatos
*Causa raiz comum:* uma afirmação sobre o mundo feita sem medição da Máquina. É o modo de falha mais caro do projeto, porque vem com fluência.

| ID | Sintoma | Causa raiz | Faça no lugar | Onde |
|---|---|---|---|---|
| FAB-1 | Dizer "íntegro" por coerência de texto | Coerência interna confundida com sincronia | Exigir hash/git/raw, ou dizer "não verificado" | (66), (69) |
| FAB-2 | Estimar bytes sem poder medir | Preencher campo que não se pode medir | `lacuna: sem meio de medir` | (68), (71) — ver ressalva em MEMÓRIAS (82) |
| FAB-3 | Alegar ação realizada que não aconteceu | Relato de execução tratado como evidência | Relato é alegação até a Máquina confirmar | (16), (24) |
| FAB-4 | Afirmar "não existe" sobre o mundo lendo só a própria cópia | A cópia em mãos tomada pelo mundo | "minha cópia vai até (n)" | (73) |
| FAB-5 | Grep negativo usado como prova de ausência sem validar o padrão contra um positivo conhecido primeiro | Instrumento de medida não calibrado | Testar o padrão contra uma entrada que existe antes de confiar no resultado vazio | (250)-(251) |
| FAB-6 | Ler parte de um arquivo truncado por limite próprio e não declarar a fração lida | Leitura parcial apresentada como completa | Dizer a fração exata ("li até (n); arquivo continua") — parcial que não se declara vira completo na cabeça de quem lê | (250) |
| FAB-7 | Perceber que a evidência citada não sustenta a conclusão e deixar a conclusão passar mesmo assim | Conclusão desacoplada da prova | Se a prova não serve, a conclusão volta a "não verificado" — não "corroborada por evidência mais fraca" | (159) |

## MED — Medição recusada
*Causa raiz comum:* cautela que vira omissão. É o espelho de FAB: recusar-se a medir o mensurável também falseia o estado.

| ID | Sintoma | Causa raiz | Faça no lugar | Onde |
|---|---|---|---|---|
| MED-1 | Escrever `lacuna` para não contar o que é contável | `lacuna` usada como abrigo, não como diagnóstico | Contar e marcar a origem da contagem | (75) |

## IDF — Identidade e fronteiras
*Causa raiz comum:* atravessar uma fronteira — tomar a identidade, a prova ou o contexto de outro ator como se fosse seu.

| ID | Sintoma | Causa raiz | Faça no lugar | Onde |
|---|---|---|---|---|
| IDF-1 | Assinar com nome puxado do corpus | Rótulo mais frequente no contexto tomado como identidade | `modelo não verificado` | (59), (71) |
| IDF-2 | Defender identidade citando a própria resposta anterior | Auto-referência usada como prova | Recuar para "não verificado" | (59) |
| IDF-3 | Ecoar nonce de MOD alheio como saúde | Dado de outro silo usado como prova de hidratação | Recusar em 1 linha, não usar | (66), (69) |

## ART — Artefato trocado
*Causa raiz comum:* responder outra coisa no lugar do que foi pedido. Trocar o artefato não é responder, é mudar de assunto.

| ID | Sintoma | Causa raiz | Faça no lugar | Onde |
|---|---|---|---|---|
| ART-1 | Entregar auditoria quando pediram parecer | Pedido reinterpretado pelo executor | Entregar o artefato pedido | (69) |
| ART-2 | Devolver o texto do proponente como parecer | Eco confundido com posição própria | Posição própria, ou recusa | (73), (74) |

## CIT — Citação e proveniência
*Causa raiz comum:* memória apresentada como cópia literal. Aspas prometem verificação; sem ela, são invenção.

| ID | Sintoma | Causa raiz | Faça no lugar | Onde |
|---|---|---|---|---|
| CIT-1 | Citar regra entre aspas sem copiar o texto exato (paráfrase apresentada como citação) | Reconstrução de memória com forma de citação | Copiar literal, ou não usar aspas | (143), (144) |
| CIT-2 | Citar MEMÓRIAS/REGRAS/PROJETO entre aspas sem `grep`/`sed` de verificação contra a fonte antes de afirmar | Confiança na memória no lugar da Máquina | Aspas exigem verificação na Máquina, não confiança na memória | (148) |
| CIT-3 | Resumir entrada de MEMÓRIAS citada sem o veredito/gravidade original (ex: trocar "fabricação confirmada" por só o tema) | Resumo que descarta o que a entrada concluiu | Veredito é campo obrigatório do resumo, não descartável | (148) |

## SIN — Sincronia e atualidade
*Causa raiz comum:* um estado que já foi verdadeiro, apresentado como o estado de agora. "Foi verdade" e "é verdade agora" são perguntas diferentes.

| ID | Sintoma | Causa raiz | Faça no lugar | Onde |
|---|---|---|---|---|
| SIN-1 | Numerar entrada sobre cópia desatualizada | Repositório desatualizado no momento da leitura | Sincronizar antes de numerar | (63) |
| SIN-2 | Tratar canal de fetch que serve conteúdo real, coerente e íntegro — mas velho, sem carimbo de idade — como fabricação | Idade do conteúdo não declarada | Preferir URL pinada em SHA (imutável); sem isso, declarar a idade como `lacuna` em vez de tratar como atual | (248)-(252) |
| SIN-3 | Repetir a hora do cabeçalho anterior sem medir de novo | Estado herdado de resposta anterior | Medir a cada resposta (`PROTOCOLOS.md`, "Regra 1.1") | (259) |
| SIN-4 | Repetir como atual um mecanismo que o canon ainda descreve, mas que já não existe | O próprio canon desatualizado induziu o modelo | Quando modelo e canon divergem, conferir os dois contra a Máquina antes de culpar o modelo | (312), (331), (422) |

## INT — Integridade de dados
*Causa raiz comum:* supor que o dado atravessou uma fronteira, foi preservado ou cabe num limite — sem conferir.

| ID | Sintoma | Causa raiz | Faça no lugar | Onde |
|---|---|---|---|---|
| INT-1 | Confiar que fronteira entre componentes entrega dado inteiro, sem checar | Integridade presumida, não medida | Perguntar sempre: o que chegou é igual ao que foi mandado? | (103), (105), (119) |
| INT-2 | Implementar privacidade removendo verificabilidade, sem decidir isso | Troca de garantia feita sem decisão do Humano | Privado também se versiona — git próprio, sem remote | (91)→(92) |
| INT-3 | Apagar identidade para caber num teto de caracteres | Otimização sem o limite da Regra 7 | Otimizar forma, nunca conteúdo registrado (Regras 4 e 7) | (47) |

---

## Como acrescentar uma falha
1. Só com uma entrada de MEMÓRIAS que a documente — falha hipotética não entra.
2. Classifique pela **causa raiz**, não pela data nem pelo tema superficial. Nenhuma família serve? Proponha uma nova, com a causa raiz comum em uma frase.
3. Formato fixo: Sintoma · Causa raiz · Faça no lugar · Onde.
4. ID novo, sequencial na família, nunca reaproveitado — falha superada continua na tabela, marcada, nunca removida (Regra 4).
5. Este arquivo muda comportamento: a mudança passa pela quarentena P-8.

*Origem:* catálogo nascido em `REGRAS.md`, "Catálogo de falhas conhecidas (leia antes de repetir uma)"; reorganizado por causa raiz em 01/10/2026. Texto anterior: `extras/arquivo/REGRAS-ate-2026-10-01.md`.
