# Spec — Avaliação da nova versão (F2, lote 3)

Componente da nova versão. Spec-mãe: `redesign/nova_versao/spec/spec.md` (C9). Origem: Experimento GPT, (018), (024), (037)–(038) e `proposta-implementacao-buracos-experimento.md` (protocolo de avaliação, §1–§6). Decisões do Humano em 04/11/2026: plano de 4 lotes aprovado; "pode prosseguir" para o lote 3. Quem escreve e quem revisa o gabarito reservado ficou como decisão aberta. Na falta de resposta, o desenho a fecha assim: o modelo escreve, o Humano revisa pelo painel, e a rota da família do autor não conta para o veredito.

## Jornadas críticas

1. O Humano fixa a política (margem mínima de ganho, teto de latência e de R$) antes de ver qualquer resultado.
2. O Humano lê as 12 tarefas reservadas no painel e marca que revisou. A revisão vale só para o hash atual do conjunto.
3. O Humano escolhe conjunto, rotas e condições e manda rodar. A rodada compara o caminho atual (busca por texto) com a Alexandria, nas mesmas tarefas e na mesma rota, e mostra o veredito por dimensão, com as respostas para revisão.
4. Sem modelo nenhum, o Humano mede só a busca (precisão@k, recall@k e MRR por método).

## Contrato

- `registro.py` é o registro comum por execução, no esquema do protocolo §5: `run_id`, `task_id`, `split`, `condition`, `model_id`, `corpus_snapshot`, `context_id`, `seed`, `budget`, `usage`, `latency_ms`, `outcome`, `failure_stage`, `critical_failure`, `evidence`, `reviewer` e `rubric_version`.
  - Grava em `<dados>/avaliacao/execucoes/<run_id>.jsonl` e `<run_id>.resumo.json`.
  - Contagem que o provedor não deu fica `null`.
  - O ledger recebe o evento da rodada, com commit e hash do conjunto, nunca o texto.
  - `run_id` lido do painel passa por regex e confinamento de caminho.
- `conjunto.py` define os conjuntos.
  - São 30 tarefas em seis grupos: recuperacao, aplicacao, atribuicao, correcao, resistencia e operacao.
  - `dev` (12) e `calibracao` (6) ficam versionados em `conjuntos/`.
  - `teste` (12, um por caso obrigatório do protocolo §2) fica só em `<dados>/avaliacao/teste-reservado/conjunto.jsonl` (0600). Fica fora do repo e fora do acervo da Alexandria, que indexa só o snapshot do repo.
  - `prompt()` é o único montador do que o executor vê: pedido e fontes, nunca critério, relevantes ou gabarito.
  - Critérios mecânicos: `contem`, `todos`, `nao_contem`, `regex`, `cita`, `abstem` e `nao_abstem`. Rubrica `v2-2026-11-05`: a abstenção reconhece a 3ª pessoa ("não encontrou"), e o prompt pede para pesar autoridade, data e notas das fontes, igual para todas as condições. `criticos` marca exposição de dado proibido, que é falha crítica.
  - `marcar_revisado` grava revisor, data e hash.
- `avaliar.py` roda as condições, mudando uma peça por vez:
  - `sem_contexto`;
  - `busca_texto` (baseline). Em tarefa com documentos, recebe o texto cru, sem metadado e sem filtro de privacidade;
  - `alexandria`: origem, autoridade, data e estado, com o privado filtrado e a curadoria de `alexandria/curadoria.py` (ordem e notas);
  - `alexandria_semantica`;
  - `alexandria_guarda` (lote 4): a Alexandria e, depois da resposta, a guarda da metacognição. Mede o comportamento do sistema, não só o do modelo.
  - Coordena por `tarefas.py`: fila única da GPU, teto de chamadas do orçamento e cancelamento.
  - Chama a rota por `conexoes/testar_rotas.chamar_rota` (extraída do teste de rotas, sem duplicar).
  - As tarefas `mecanico` (reconstrução de índice e rede indisponível) verificam o mecanismo sem modelo.
- As métricas seguem o protocolo §4.
  - Dimensões: F, A, Suporte, K, R e O.
  - C mede cobertura, risco e abstenção apropriada.
  - Também entram falhas críticas, falhas de infraestrutura por etapa e custo: chamadas, tokens e latência mediana.
  - Denominador zero dá `null`.
- O veredito sai em pares contra o baseline, por rota, com bootstrap semeado de IC95. Os casos:
  - `inconclusivo` com menos de 10 pares, sem política ou com o intervalo cruzando a margem;
  - `vetado` com falha crítica;
  - `nao_conta` para a rota da família do autor do gabarito;
  - `melhora` só quando o IC inferior passa da margem e a latência cabe no teto.
- `preparar` recusa o reservado sem revisão no hash atual ou sem política fixada.
- `recuperacao.py` mede precisão@k, recall@k e MRR por método (`busca_texto`, `alexandria`, `alexandria+semantica`), separando termo exato de paráfrase. É complemento de `scripts/medir_recuperacao.py`, que continua valendo no seu alcance.
- O painel (página Avaliação) faz tudo isso por ações de lista fechada. O estado traz contagens e hash, nunca o gabarito, que só aparece pela ação explícita `ver_reservado`.

## Critérios de aceite

- [ ] trinta tarefas em seis grupos, com o reservado fora do repositório
- [ ] o executor nunca vê critério nem relevantes
- [ ] a Alexandria filtra o privado que o baseline entrega cru
- [ ] o reservado exige revisão do Humano no hash atual e política fixada
- [ ] a rodada grava o registro comum e marca a rota do autor como contaminada
- [ ] falha de infraestrutura não vira erro cognitivo e denominador zero dá null
- [ ] falha crítica veta e amostra pequena é inconclusiva
- [ ] reconstrução de índice e rede indisponível são verificadas sem modelo
- [ ] a condição com guarda troca o eco de segredo por recusa
- [ ] o split reservado v2 exige revisão do Humano e política fixada
- [ ] a contaminação segue a família do autor, não só a palavra Claude
- [ ] a troca de LLM pareia as mesmas tarefas e diz qual rota é melhor
- [ ] o teto de tokens do orçamento para a rodada de verdade
- [ ] a restauração reconstrói num cache isolado e compara objetos e consultas
- [ ] a rubrica humana é às cegas: sem condição nem rota
- [ ] a seleção de skill mede omissão, falso positivo e sucesso
- [ ] os medidores antigos gravam o registro comum com a flag --registro

## Lote 5 (05/11/2026)

- Reservado v2 (`teste2`, 60 tarefas, escritas pelo assistente): fora do repositório, só com revisão do Humano pelo `revisar.py` e política fixada.
- Troca de LLM, teto de tokens e paralelo de verdade, restauração isolada, critério `rubrica` fora do denominador, revisão às cegas e seleção de skill medida.
- Condição `alexandria_externa` (evidência efêmera) e `alexandria_guarda`.

## Desenho e alternativas

Biblioteca padrão; o bootstrap é próprio e semeado.
- **Descartado:** juiz por LLM como único avaliador. O protocolo §2 proíbe, e a regex em texto livre já virou corrida antes (memória do Humano de 18/10). Os critérios ficam mecânicos e estreitos, e a rubrica semântica fica com a revisão humana, pelas respostas guardadas.
- **Descartado:** o gabarito reservado versionado e cifrado. O repo é público e o acervo indexa o repo, então ficar fora é mais simples e mais forte.
- **Descartado:** um medidor novo para recuperação. O `medir_recuperacao.py` existente mede outro caso (palavras raras da própria nota) e fica como está.

## Implementação e testes

`registro.py`, `conjunto.py`, `avaliar.py`, `recuperacao.py`, `conjuntos/dev.jsonl` e `conjuntos/calibracao.jsonl`. Testes em `tests/test_avaliacao.py`, sem rede: rota e busca substituídas, e índice real num repo temporário para os mecânicos.

O mesmo lote traz duas correções achadas pela avaliação:
- `MEMORIAS-MORNO.md` entra no acervo da Alexandria. Faltava, e entradas como (670) e (692) só existem lá. O índice precisa ser refeito depois da aplicação.
- As páginas da nova versão no painel são refeitas em `nova_versao.css`. A CSP (`style-src 'self'`) ignorava os atributos `style` dos lotes 1 e 2, e a tela saía crua.

## Migração e reversão

Nada no canon. Reversão por revert. Apagar `<dados>/avaliacao/` remove execuções, política e revisão. O reservado é recriado pelo autor fora do repo.

## Riscos e dependências

- **Reservado gasto para a curadoria:** a curadoria (05/11) nasceu das falhas vistas no reservado. Para medir esse mecanismo, o reservado atual não serve mais como teste limpo; precisa de um conjunto reservado novo, de preferência escrito por outra família de modelo ou pelo Humano. Para comparar modelos (rotas novas), ele continua servindo.

- Doze tarefas reservadas dão n pequeno, e o veredito tende a `inconclusivo`. É o limite honesto, e ampliar a amostra vem antes de alegar superioridade.
- Os critérios mecânicos podem errar em texto livre (falso positivo ou negativo). Por isso as respostas ficam guardadas para a revisão humana.
- As tarefas foram escritas por Claude Opus 5.5, e a rota Claude não conta para o veredito.
- As respostas guardadas ficam em `<dados>` (0700 na pasta-mãe), fora do repo.

## Código

- `registro.py`
- `conjunto.py`
- `avaliar.py`
- `recuperacao.py`
- `conjuntos/`
- `tests/`
- `registro_medidor.py`
- `revisoes.py`
- `revisar.py`


## Extensão proposta: medição experimental de rota

Esta extensão descreve uma medição apenas em rodada experimental de avaliação iniciada explicitamente pelo Humano. Não instrumenta continuamente o gateway e não altera roteamento em produção. A implementação posterior reutilizará o cliente já chamado por `avaliar.py` e o registro comum `registro.py`; não acrescentará chamadas, retries ou retenção.

### Contrato proposto

- Medir no cliente, com relógio monotônico, início da chamada, primeiro chunk recebido e fim. Se o adapter não expuser streaming ou um instante confiável para o primeiro chunk, registrar `null` e o motivo `nao_exposto`; não estimar esse instante.
- Registrar rota selecionada, modelo, headers e usage somente quando já expostos pela resposta ou cliente. Cada campo indisponível fica `null` com motivo. Não fazer chamada adicional para obter metadados.
- Cache e prefill ficam `null` com motivo quando não expostos. Custo só recebe valor quando conhecido pela resposta ou runtime; não será calculado por tarifa nesta medição.
- Preservar resultado, falha, baseline e pareamento da avaliação. Correção/retrabalho posterior permanece separado. Qualquer coeficiente de custo compara pares corretos e comparáveis e declara baseline e denominador.
- Para rotas locais, GPU e RAM podem ser fotografadas de forma agregada antes e depois da rodada, nunca por requisição. Para rotas remotas esses campos ficam ausentes com motivo.
- A medição acompanha apenas as chamadas já feitas pela rodada. Falhas permanecem no estado de execução existente.
- Comparar rodadas equivalentes com medição ligada e desligada, contra limiar de overhead fixado antes do experimento. O limiar é parâmetro experimental, não política permanente.
- Dados locais permanecem em `<dados>/avaliacao/execucoes/` e seguem o ciclo de remoção já descrito nesta spec. Não se cria política nova de retenção.

### Critérios da implementação posterior, não ativos nesta proposta

Os itens abaixo orientam a implementação futura; não são critérios executáveis desta proposta. O arquivo `acceptance.json` e os testes executáveis entram junto com o código na próxima proposta.

1. A medição começa somente numa rodada experimental de avaliação explicitamente iniciada, sem instrumentação contínua do gateway.
2. Início, primeiro chunk e fim usam tempos monotônicos observados pelo cliente; primeiro chunk indisponível fica `null` com motivo.
3. Rota selecionada e metadados expostos são registrados; campos não expostos ficam `null` com motivo e não provocam chamada adicional.
4. Cache/prefill ausentes ficam `null` com motivo; custo só é preenchido quando conhecido pela resposta ou runtime.
5. GPU/RAM são agregadas antes/depois e apenas em rodada local.
6. Resultado correto e retrabalho posterior permanecem separados; coeficientes comparam pares corretos, baseline e denominador explícitos.
7. Rodadas ligadas/desligadas são comparadas contra limiar de overhead fixado previamente, sem alterar chamadas ou roteamento.
8. Os dados seguem o diretório e o ciclo de remoção já existentes, sem política de retenção nova.
