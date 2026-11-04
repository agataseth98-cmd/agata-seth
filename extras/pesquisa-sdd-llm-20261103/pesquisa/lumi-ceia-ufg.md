# CEIA Lumi: história, estado e possibilidades para o Agata

Autor: Claude Sonnet 5.5 (Claude Code). 04/11/2026, 10:40 (`date`). Nota de estudo, não canônica. Níveis: **N1** página primária lida (via agente de leitura), **N3** notícia, **Medido** na Máquina, **Inferência** minha.

## 1. História
- **CEIA-UFG:** criado em 2019, no Instituto de Informática da UFG, em Goiânia (N3, A Redação, 28/10/2026). O governo de Goiás investiu cerca de R$ 91 milhões, em dois convênios (R$ 13 mi e R$ 78 mi); o centro reúne mais de mil pesquisadores e atende mais de 100 clientes (N3, Convergência Digital, 29/10/2026). Esses números são do centro, não do Lumi.
- **Antecessor, Gaia (2025):** `CEIA-UFG/Gemma-3-Gaia-PT-BR-4b-it`, do Gemma 3 4B com pré-treino contínuo de cerca de 13 bilhões de tokens em português, parceiros ABRIA, Nama, Amadeus AI e Google DeepMind, licença Gemma (N3, buscas; cartão não lido por mim).
- **Lumi, 28/10/2026:** apresentado no AI Brasil Experience, em São Paulo. A Redação o chama "o primeiro modelo open source do CEIA". Responsáveis citados: Arlindo Galvão e o time de processamento de linguagem natural; diretora Telma Soares (N3). A organização no Hugging Face (`ceia-br`) tem 3 membros e 1 modelo, sem datasets públicos (N1).

## 2. O que o modelo é (N1: cartão `ceia-br/lumi-4b` e página `HyperScale/lumi-4b-GGUF`)
- 4B parâmetros, BF16, safetensors, arquitetura **`nemotron_h`**: híbrida Mamba-2 e atenção, família Nemotron-H da NVIDIA (artigo arXiv 2504.03624, N1 por resultado de busca; a NVIDIA lista um 4B base de 8K de contexto, de uma só página de documentação). **Modelo de origem do Lumi: não consta** em nenhuma página.
- **Licença: não consta.** O cartão diz que não documenta licença; a notícia diz "open source" sem nomear licença. Contradição aberta.
- Tokens de treino, dados, contexto máximo e template: não constam no cartão. A cifra "mais de 100 bilhões de tokens" vem de um veículo; outro diz "100 bilhões de palavras" (unidades inconsistentes). Não confirmada por fonte primária.
- Benchmarks do cartão (sem versão, harness nem intervalo de confiança): MMLU PT ensino médio 45,72%, graduação 48,80%, Global MMLU PT 59,36%, MMLU-ProX PT 36,28%, IFEval PT 33,83%; média 44,80%, "2º entre 9 modelos". Em Q4_K_M a HyperScale mediu 57,88% no Global MMLU PT.
- GGUF de terceiros: só Q4_K_M (2,7 GB), uso recomendado com `--repeat-penalty 1.1`; o greedy entrou em loop em 2 de 15 casos. "Thinking" vem ligado no template.
- A Redação o descreve como modelo-base (para continuar treino); o cartão marca "conversational". Não sei se é base ou ajustado para instruções.

## 3. Medido na Máquina (04/11/2026, Ollama 0.32.11, `lumi-4b` Q4_K_M, GGUF da HyperScale)
Importa e roda no Ollama (arquitetura `nemotron_h`, contexto declarado 1.048.576, capacidades: completion, tools, thinking). Tokens reais são ~10% menores que o alvo (3.686 para alvo 4.096).

| Teste | Resultado |
|---|---|
| Agulha, sem raciocínio, 4k, 16k, 32k, 64k, 128k (alvo) | **3/3 em todos** |
| Rastreio de variáveis, sem raciocínio, 4k e 16k | 0/3 (lista só o 1º elo; sem a penalidade de repetição dá o mesmo) |
| Rastreio, com raciocínio, 4k e 16k | 1/3 em ambos (um corte por tamanho de saída em 16k) |
| Comparação: `qwen3.5-9b-64k` com raciocínio | **3/3** em 4k e 16k (sem raciocínio: 0/5 tamanhos) |
| Comparação: `qwen3:4b` rastreio | 3/3 em 2k, 8k, 16k, 32k |

Leitura: recuperação de um fato em contexto muito longo é forte (compatível com a arquitetura Mamba híbrida, **inferência**); encadear fatos é fraco. Não medi agregação, qualidade em português, ferramentas, velocidade nem memória. Resultados com 3 tentativas por ponto, um modelo quantizado de terceiros.

## 4. Possibilidades para o Agata (inferências, nenhuma feita)
1. **Leitura de contexto longo barata:** achar um fato em canon ou diário muito grandes com um 4B de 2,7 GB. Candidato a medir contra a busca por texto (recall@k).
2. **Português nativo:** testar em tarefas do próprio Agata (resumo de MEMÓRIAS, memória semanal, Regra 1) contra o `qwen3.5-9b-64k`. Não medido.
3. **Ajuste fino:** se a licença permitir, treinar com dados do Agata; hoje a licença é desconhecida, então **não usar em produto nem ajustar até o CEIA declarar** (pergunta ao CEIA: github.com/ceia-br).
4. **Cuidados:** conversão de terceiros; repetição em greedy; raciocínio ligado por padrão; Ollama aceita a arquitetura hoje, o que pode mudar em outra versão.
5. **Registro no sistema:** o modelo está só no Ollama local e em `~/.cache/agata/models/lumi-4b/`. Entrar em `models/manifest.json` e no backup (P-12) exige proposta assinada.

## Fontes
huggingface.co/ceia-br/lumi-4b · huggingface.co/HyperScale/lumi-4b-GGUF · huggingface.co/ceia-br · aredacao.com.br (28/10/2026) · convergenciadigital.com.br (29/10/2026) · research.nvidia.com/labs/adlr/nemotronh · arxiv.org/abs/2504.03624. A matéria do SpaceMoney deu HTTP 403 e não foi lida.

## Correção de 04/11/2026, 11:05 (entrada nova)
As medições do Lumi e do `qwen3.5-9b-64k` com raciocínio foram feitas por script avulso com **enchimento simples** (texto repetido). O medidor oficial usa o **texto do canon** como enchimento. Repetindo o 9b com raciocínio pelo caminho oficial: **1/3 em 4k e 1/3 em 16k** (antes: 3/3 com enchimento simples); as respostas de 4k inspecionadas eram erros reais, sem corte de saída. Logo, "o erro era só falta de raciocínio" não se sustenta: o resultado depende do enchimento. Os números do Lumi (agulha 3/3 até 128k; rastreio 0/3 e 1/3) valem para enchimento simples e **precisam ser refeitos pelo medidor oficial** quando a proposta `medicao-raciocinio-ligado-20261104` for aplicada.

## Medição oficial, 04/11/2026, 11:27 (entrada nova; vale no lugar da seção 3 e da correção acima)
Medidor oficial (enchimento = texto do canon, 3 tentativas por ponto, `lumi-4b` Q4_K_M, penalidade de repetição 1,1 do Modelfile, contexto até 140.000). Tokens reais são cerca de 9% menores que o alvo (119.745 no alvo de 131.072).

| Teste | Alvo em tokens | Acertos |
|---|---|---|
| Agulha | 4k / 16k / 32k / 64k / 128k | 3/3, 2/3, 3/3, 2/3, **0/3** |
| Rastreio, sem raciocínio | 4k / 16k | 0/3, 1/3 |
| Rastreio, com raciocínio | 4k / 16k | 1/3, 1/3 |

Leitura: com o enchimento do canon, a agulha **não** chega limpa a 128k, como o script avulso sugeria (3/3 em todos). Falha em 128k e oscila em 16k e 64k; pela regra do medidor (para no primeiro buraco), o contexto efetivo é 4.096, o que subestima (32k deu 3/3). A cifra de contexto de 1.048.576 que o Ollama exibe é a declarada pelo modelo, não medida. O rastreio continua fraco, com ou sem raciocínio. Não medi o porquê da diferença entre enchimentos.

---

## Atualização de 04/11/2026 15:06: licença e uso no sistema
- **Licença:** o Humano informou que os desenvolvedores (CEIA-UFG) autorizaram por escrito a alteração do modelo; o sistema NÃO leu o documento e não conferiu os termos. O manifesto (`models/manifest.json`, campo `licenca`) registra "risco assumido pelo Humano". Em aberto: se vale ajuste fino, redistribuição dos pesos ajustados, uso comercial e se exige atribuição.
- **Desempenho no teste de português** (rodada completa, 30 execuções por célula): cru 11, cru_formato 22, harness 26, adaptativo 26 tarefas totalmente certas. Estratégia no perfil: harness. Ver `teste-portugues/RESULTADO.md`.
- **Continua em aberto:** por que a agulha do Lumi falha em 128k pelo medidor oficial (0/3) e a diferença entre os dois enchimentos; o contexto declarado de 1.048.576 não foi medido; o Lumi está fora da lista de backup obrigatório do P-12 (decisão do Humano).
