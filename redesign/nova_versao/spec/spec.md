# Spec — Nova versão do Agata (Experimento GPT)

Spec-mãe. Fonte do desenho: `~/Área de trabalho/Experimento GPT/` (diário `conclusoes.md` 001–080 e os documentos derivados), lido inteiro em 04/11/2026. Direção aprovada pelo Humano em (077): "Essa será a nova versão do agata ok". Esta spec não é assinatura P-8; a assinatura é a do par `propostas/nova-versao-piloto-20261104`.

## Jornadas críticas

1. O Humano abre o painel, grupo "Nova versão", e vê o estado real de cada componente; o que não foi medido aparece como não medido.
2. Um modelo pergunta algo sobre o sistema e recebe um pacote de evidência com objeto, trecho, linha, commit e sha, ou "não encontrado nesta busca".
3. O gateway, com a sombra ligada, registra o que a nova versão teria feito com cada pedido, sem o texto e sem mudar a resposta, para a avaliação comparar.
4. O Humano decide no painel quais provedores a nova versão pode usar e com qual teto; cada mudança fica no ledger.

## Contrato

**Tese ((066)).** Os pesos dão a capacidade; o Agata dá memória, contexto, corpo, ferramentas, seleção de skills, papéis, redundância, sincronização, metacognição, auditoria e autoridade. A unidade vem do estado comum, das fontes rastreáveis e da decisão humana, não de uma LLM.

**Nove componentes e o que cada um reaproveita:**

| # | Componente | Reaproveita | Código novo (lote) |
|---|---|---|---|
| C1 | Governança e contrato | canon, P-8, `propostas/`, `scripts/equipe/aplicar.py`, `redesign/mcp/capability.py` | nenhum; seção em `PROJETO_REFERENCIA.md` (1) |
| C2 | Memória em camadas | hidratação do gateway, MEMÓRIAS quente/morna/fria, vault, `cache_conselho.py`, `memoria_semanal.py`, `vault_importar_inbox.py` | nenhum; mapa abaixo; teste de troca de LLM (3) |
| C3 | Alexandria | `busca_texto.py`, `busca_semantica.py`, `cita` do vault, `gerar_indice_derivado.py`, `evidence_ledger` | `redesign/alexandria/` (1) |
| C4 | Seleção de skills | `.agents/skills/INDICE.md`, `ferramentas/ferramentas.py` (quarentena), `qualidade_llm.py` | `redesign/alexandria/skills.py` (1) |
| C5 | Metacognição | `_classificar_rota` do gateway, `auditoria_turno.py`, `sombra_capacidade.py`, `detector_estado_sem_prova.py` | `redesign/metacognicao/`, `redesign/router/sombra_nova_versao.py` (1) |
| C6 | Corpo operacional | `estado_para_eco.sh`, `perimetro.sh`, `coletar_evidencias.py` da auditoria, `config/portas-*.txt` | `redesign/corpo/` (1) |
| C7 | Redundância e conexões | combos OmniRoute, Conselho em Rede (`relay_catalog.py`), `sanitizar.py`, `teste_portugues.py` | `redesign/conexoes/` (2): Claude e ChatGPT como exemplos nos três caminhos, teste por capacidade; painel de chaves (ver Painel de chaves) |
| C8 | Coordenação e papéis | `grafo/durabilidade.py` (WAL), `evidence_ledger`, `idempotency_key` do Conselho, semáforos das sombras | `redesign/nova_versao/tarefas.py` (2) |
| C9 | Avaliação | `medir_recuperacao.py`, `teste_portugues.py`, `seth_golden.py`, `seth_autodev.py`, `medir_contexto_efetivo.py` | registro por execução comum (3): `redesign/avaliacao/` |

**Mapa de memória (C2), camada → mecanismo existente:** autoridade = canon; memória de trabalho = hidratação (`seth_gateway.py`, `_hidratacao`); episódica = MEMÓRIAS e `memoria/` (quente, morna, fria); semântica derivada = vault e índices; operacional entre modelos = `cache_conselho.py`; procedural = skills e scripts; corporal = `redesign/corpo/`; acervo com proveniência = Alexandria. Nenhuma camada nova é criada para substituir outra.

**Pastas de trabalho** (decisão do Humano, 04/11): `AGATA_NV_DIR`, padrão `~/.local/share/agata/nova-versao/` (0700, fora do repo público), criadas por `redesign/alexandria/acervo.py iniciar`, com `LEIA-ME.md` gerado. Fluxo editorial (`recebido`, `quarentena`, `catalogado`, `revisado`, `contestado`, `restrito`, `arquivado`, `rejeitado`), ciclo de skills (`rascunho`, `quarentena`, `em-teste`, `elegivel`, `revogada`), `contextos/`, `metacognicao/`, `corpo/`, `redundancia/`, `coordenacao/`, `avaliacao/{dev,calibracao,teste-reservado,execucoes}`, `eventos/` e `config/`. Índice derivado em `AGATA_NV_CACHE` (padrão `~/.cache/agata/nova-versao/`).

**Proveniência.** Todo objeto do acervo tem `object_id`, caminho, commit do snapshot, `sha256`, classificação de acesso (`public`, `project`, `private`), estado editorial e verificação (`identidade`, `integridade`, `suporte factual`) como dimensões separadas. Hash prova conservação de bytes, não verdade.

**Estados separados.** Editorial (acima); execução (`criada`, `em_execucao`, `em_revisao`, `concluida`, `falhou`, `cancelada`, `aguardando_humano`, lote 2, só os estados que uma jornada consome); saúde (`normal`, `pressionado`, `degradado`, `isolado`, `indisponivel`, lote 5, critério de entrada e saída a definir); saída do turno (`apto`, `parcial`, `inconclusivo`, `bloqueado`, `aguardando_humano`, lote 5).

**Sete palavras.** Apresentação → Compreensão → Assimilação → Simbiose → Transição → Aprimoramento, com Remoção opcional e retornos da tabela da proposta Alexandria §11. `eventos.transicao()` grava estado anterior e seguinte, evidência, autorização e retorno; recusa salto fora da tabela e Remoção sem autorização. É registro, não máquina autônoma.

**Permissões.** Consulta pública não vê `private`; a sombra grava hash, nunca o texto; nenhuma peça lê `~/.config/agata/.env`; nada escreve no canon; skill selecionada não é carregada nem executada; a fotografia só faz GET e comandos de leitura.

**Concorrência e falha.** Trava única: `flock` do ledger (`redesign/evidence_ledger`), com timeout e chave idempotente; a fila de GPU é a única outra fila. Eventos (`eventos.py`) são camada fina sobre o ledger, sem log próprio. Ordem entre ação e registro: a intenção é gravada antes, a ação roda, a confirmação é gravada depois; `nv.py sincronizar` reconcilia intenções sem confirmação. Índice reconstruído em arquivo temporário no mesmo sistema de arquivos e trocado atomicamente. Sombra pula o pedido quando a fila está ocupada e conta o pulo. Busca semântica fora do ar (timeout ou erro, definido no lote 5) degrada para léxico com aviso. Falha de um componente da sombra vira campo `erros`, nunca exceção no gateway.

**Orçamento** (decisão do Humano, 04/11: "tudo que estiver disponivel configuravel pelo painel"; decisão do Humano, 06/11: valores equilibrados aplicados). `redesign/nova_versao/orcamento.py`: quatro categorias de provedor, `local`, `gratuito`, `assinatura` (cota do plano do usuário, sem R$) e `pago`, mais tetos de chamadas, tokens, tempo e R$. Padrão de fábrica: só `local` ligado; `pago` desligado com teto de R$ 0, portanto não gasta. Valores aplicados: 200 chamadas, 2 milhões de tokens, 120 s por chamada, R$ 0. Justificativa medida: uma chamada do Conselho Remoto usou 11.292 tokens e 19,6 s (`memoria/missoes/conselho-remoto/20261106-142748-glm-4.7-flash.json`); 200 chamadas × ~11 mil tokens ≈ 2,2 milhões, então 2 milhões é o teto coerente com o cap de chamadas. Existe um escopo para turno, tarefa e global, no mesmo módulo; `orcamento_turno.py` deixa de existir como módulo separado. Cada mudança vira evento. No lote 1 nada consome inferência.

**Invariantes (handoff do executor).** Canon, permissões, silos e autoridade humana vêm antes de descoberta e roteamento. Alexandria não é cânone paralelo. A recusa de vetor/GraphRAG como camada primária ((115)) permanece; a semântica é secundária ((327)). Skill é procedimento; livro é conteúdo. Catálogo, health check, inferência real e fila ativa são medições diferentes. Ausência na busca é "não encontrado nesta busca".

**Fases.** F0 spec e F1 sombra no lote 1 (`nova-versao-piloto-20261104`, aplicado, (939)); C7 e C8 no lote 2 (`nova-versao-conexoes-20261104`); F2 avaliação no lote 3 (30 tarefas, split reservado, gabarito revisado pelo Humano, métricas por dimensão com `null` em denominador zero); F3 integração protegida no lote 4, cada item em proposta própria e só com ganho medido sem regressão crítica.

## Critérios de aceite

- [ ] a chave idempotente não grava duas vezes
- [ ] escritas concorrentes no ledger preservam a cadeia
- [ ] a transição recusa salto fora da tabela e Remoção sem autorização
- [ ] o orçamento padrão é só local e pago sem teto não gasta
- [ ] a GPU local tem fila única e o teto de chamadas da tarefa vale
- [ ] cancelar impede novos itens e contexto mudado manda o resultado para revisão
- [ ] nomes vindos de fora só entram dentro da pasta-base, e symlink para fora é recusado
- [ ] papel só recebe rota que passou na prova e de família diferente do sintetizador
- [ ] o ensaio de retorno usa a rota alternativa quando a principal cai
- [ ] o orçamento do turno esgota por rodadas, chamadas ou prazo
- [ ] as sete palavras andam só pelos passos previstos e não repetem o registro
- [ ] o orçamento padrão tem 200 chamadas, 2 milhões de tokens, 120 s e R$ 0, e `orcamento.py` usa as mesmas quatro categorias da spec
- [ ] o painel de chaves grava a chave sem devolvê-la, e o valor não aparece em resposta HTTP, log ou ledger
- [ ] a reversão não apaga `AGATA_NV_DIR`; só remove o cache

## Lote 5 (05/11/2026)

- `caminhos.py`: confinamento de nomes vindos de fora (usado por cadastro, upload, revisões e reservado v2).
- `papeis.py` + `config/papeis.json`: papel → rota, só com capacidade provada e independência do sintetizador. Sem serviço por papel.
- `redundancia.py`: escolha de rota alternativa e ensaio de falha com injeção (sem parar serviço).
- Turno em `orcamento.py` (escopo `turno`): rodadas, chamadas e prazo; o `posterior` marca `parcial` quando esgota. Sem módulo separado.
- `nv.py sincronizar`: as sete palavras ligadas a propostas reais (apresentação, assinatura, aplicação), pelo ledger, com chave idempotente. Remoção nunca é automática.

## Painel de chaves (lote 2, decisão do Humano, 06/11)

O Humano cadastra e troca chaves de provedor pelo painel, com segurança: campo só de escrita, por provedor.

- Ao salvar, a chave vai para `~/.config/agata/.env`, linha do nome do provedor, com permissão 0600; a gravação é atômica.
- A única peça que lê esse arquivo é a rotina de gravação, e só para trocar a linha daquele nome. Nada devolve o valor: a resposta diz só "configurada, alterada em DATA".
- O ledger registra "chave NOME alterada", nunca o valor. Log não recebe o valor.
- Modelos, pedidos e a sombra não leem o arquivo. Nada disso entra no repo nem no canon.
- Exceção à regra "nenhuma peça lê `.env`": só essa rotina, por escrita. Essa exceção precisa ser aprovada pelo Humano na assinatura, porque a regra atual não a prevê.

## Lotes seguintes (decisão do Humano, 06/11: "contanto que seja implementado tudo")

Nada sai do escopo. Estes itens saem do lote atual e entram no lote 6, cada um com critérios escritos antes do código:

- `redesign/metacognicao/` (C5): sem critério ainda.
- `redesign/corpo/` (C6): sem critério ainda.
- `redesign/alexandria/skills.py` (C4): ciclo de skills, sem jornada ainda; fica fora de `acervo`, porque skill é procedimento.
- `conselho.py`: sem critério ainda.

## Desenho e alternativas

Ver `brainstorm.md` e `decision.md`. Alternativas descartadas: um serviço por papel (039–040: custo e pontos de falha sem ganho medido); banco vetorial como base (recusa (115)); terceiro log de eventos (o `evidence_ledger` já cobre); dados dentro do repo (remote público).

## Implementação e testes

`eventos.py`, `orcamento.py` (categorias `local`, `gratuito`, `assinatura` e `pago`), `tarefas.py` (coordenação: `task_id`, versão de contexto, prazo, teto de chamadas, cancelamento, fila de GPU, escritor único) e `nv.py` (CLI e selftest). Testes em `tests/`; cada critério aponta o teste em `acceptance.json`.

## Migração e reversão

Sem migração de dados do canon. Reversão: revert do commit de aplicação e remoção de `AGATA_NV_CACHE` (derivado). `AGATA_NV_DIR` (ledger, `eventos/` e execuções) é arquivado num pacote datado fora do repo e nunca apagado automaticamente; apagar só quando o Humano decidir que não é mais necessário (decisão do Humano, 06/11). A sombra já nasce desligada.

## Riscos e dependências

O pré-voo é regex: erra (falso positivo de "efeito", por exemplo) e só serve em sombra até o lote 3 medir. O acervo do piloto é só o repo (decisão de 04/11); o vault fica fora porque é derivado e está fora do git. A nota de `PROJETO_REFERENCIA.md` que diz que o vault "não tem embedding" está defasada pela (670): fica registrada como achado, sem mudança neste lote.

## Código

- `eventos.py` (camada fina sobre o ledger, lote 1)
- `orcamento.py` (lote 1; escopos turno, tarefa e global)
- `nv.py`
- `tarefas.py` (lote 2)
- `tests/`
- `caminhos.py` (lote 5)
- `papeis.py` (lote 5)
- `redundancia.py` (lote 5)
- `conselho.py` (existente; critério no lote 6)
- `orcamento_turno.py` (existente; sai no lote 5, em favor do escopo turno de `orcamento.py`)
- Painel de chaves (lote 2, junto ao painel; sem crase até existir)
- Lote 6, sem crase até existir: metacognição, corpo, skills da Alexandria
