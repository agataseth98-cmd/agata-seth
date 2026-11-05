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
