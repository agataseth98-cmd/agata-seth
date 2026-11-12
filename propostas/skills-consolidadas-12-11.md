# Skills consolidadas (12/11): 21 pastas viram 10 do Agata (`skills-consolidadas-12-11`)

Proposta P-8 de `skills-consolidadas-12-11`. Diff: `propostas/skills-consolidadas-12-11.diff` (1282 linhas, 122937 bytes; sha256 `f295b693ac29a08e368ac7591b6f53b240f5ed526d30ffbfff236b0acc07087f`). Base: `origin/main` `2ec04181` com `propostas/pacote-mecanico-12-11.diff` já aplicado (PR #978 mergeado; a aplicação do pacote é decisão do Humano). **Aplicar depois de pacote-mecanico-12-11.** Este diff foi refeito sobre essa base: o diff anterior (base `04bfe2e4`) não aplica mais. Assinatura do Humano, uma vez, depois do merge deste PR de proposta.

Pedido: diretriz do Humano em 12/11/2026 (cache do Conselho, entrada 518): "MENOS skills e MAIS qualidade, formato UNIVERSAL para todos os LLMs (Markdown simples, sem recursos exclusivos de um modelo), remover o óbvio, deixar só o que resolve problema real".

Critério aplicado (doc oficial de skills, citado no pedido): uma instrução fica só se (a) evita um erro que aconteceu (MEMÓRIAS, cache do Conselho ou FALHAS.md) ou (b) diz um comando, caminho ou regra próprio do Agata que o modelo não adivinha. Regra já garantida por mecanismo vira ponteiro de uma linha.

Classe (P4): Comportamento. Texto de skill dirige modelos, mas nenhum componente ancorado muda e nenhum `redesign/*/spec` é tocado. Nenhum arquivo de canon muda (REGRAS, PROTOCOLOS, FALHAS, PROJETO, MEMÓRIAS, AGENTS, CLAUDE ficam como estão).

## Em resumo (para o Humano)

- As skills próprias do Agata passam de 20 pastas para 10. Ninguém perde texto: os 11 SKILL.md originais estão byte a byte em `extras/arquivo-skills-12-11/`, e a tabela da seção 3 diz para onde foi cada bloco.
- Medido: a lista que todo modelo carrega (nome e descrição) cai de 5.969 para 3.626 caracteres (-39%). O corpo das skills cai de 1.183 para 890 linhas (-25%). Bytes das pastas: 150.733 para 123.737 (-18%).
- A regra "pacote mínimo para subagente" (decisão do Humano, 12/11, trazida pelo pacote-mecanico-12-11) não se perde: a seção 9 de `agata-fluxo-equipe` vai inteira para `agata-equipe`, sem mudança de texto. Os dois checks do pacote que leem essa seção (`scripts/testar_mecanismos.py` e `scripts/conselho_mecanismos.py`) passam a ler `agata-equipe`.
- O ganho em bytes é menor que em linhas de propósito: o processo de lote guarda a pauta do auditor, a tabela de quem faz cada passo e as 12 lições de 07/11, que têm fonte e não se repetem em outro lugar.
- A caixa de ferramentas ECC tem 314 peças. Nenhuma é referenciada por caminho ou crase nos arquivos vivos (seção 4). Mover para `extras/` fica como decisão separada do Humano: não está neste diff.
- `agents/openai.yaml` (arquivo de interface de um modelo) saiu de duas skills, por causa do formato universal. O arquivo está em `extras/`.
- Assinar só depois do merge deste PR: `bash scripts/aprovar.sh skills-consolidadas-12-11 "<motivo>"`.

## 1. Inventário antes (medido na base: `origin/main` 2ec04181 com o pacote-mecanico-12-11 aplicado)

Uso: MEM = menções em `MEMÓRIAS.md` (`grep -c -F`, substring; `fluxo` inclui `fluxo-equipe`); CACHE = menções em `cache_conselho.py ler --n 300` (150 entradas); PROP = arquivos em `propostas/` que citam o nome. São citações, não registro de carregamento: não existe log de quantas vezes um modelo leu cada skill (não medido).

| Skill | Bytes | Linhas | Desc. (chars) | Gatilho | O que resolve | MEM / CACHE / PROP | Sobreposição | Destino |
|---|---|---|---|---|---|---|---|---|
| agata-processo-lote | 36.138 | 213 | 265 | lote e P-8 | regras e erros de lote (06/11), lições (07/11) | 2 / 2 / 27 | aplicar-proposta, equipe, fluxo | fundida em `agata-aplicar-proposta` |
| agata-equipe | 9.950 | 93 | 360 | papéis da equipe | quem faz o quê; proibições de git | 2 / 0 / 4 | fluxo-equipe, processo | mantida; absorve fluxo-equipe |
| agata-relay-provedores | 9.342 | 53 | 237 | chats web (Relay) | estados e limites do Relay | 1 / 0 / 13 | nenhuma | mantida (um ponteiro trocado; sai `agents/openai.yaml`) |
| agata-conversar-com-seth | 7.406 | 49 | 375 | conversar com a Seth | caminhos A a D e limites | 1 / 0 / 16 | nenhuma | mantida (um bullet vira ponteiro) |
| agata-fluxo-equipe | 7.173 | 65 | 465 | equipe em partida, fila, vigia | partida, vigia, fallback, cota | 3 / 0 / 10 | equipe, fluxo, conselho | fundida em `agata-equipe` |
| agata-llm-fundamentos | 29.658 (3 arquivos) | 46 | 451 | falhas de LLM, custo, experimento | mecanismo do Agata por falha; lacunas | 1 / 0 / 16 | experimento | mantida; absorve experimento-agata |
| agata-engenharia-reversa | 5.693 | 93 | 506 | análise de app ou bundle (REA) | allowlist e destino de escrita | 1 / 0 / 8 | nenhuma | mantida (sem mudança) |
| agata-fluxo | 5.467 | 76 | 239 | entrada de qualquer tarefa | escolha da skill; registro; comandos | 10 / 0 / 30 | todas | reescrita como entrada única |
| agata-conselho-memoria | 3.287 | 38 | 296 | memória comum e canal MSG | cache, MSG, "antes de afirmar" | 1 / 0 / 6 | fluxo, equipe | fundida (fluxo seção 5; equipe seção 1) |
| agata-carregar | 2.671 | 37 | 216 | abrir sessão | estado, bloco de prontidão | 3 / 0 / 15 | fluxo | fundida em `agata-fluxo` seção 0 |
| agata-disciplina | 3.557 | 66 | 332 | conduta de qualquer modelo | cabeçalho, conciso, avisos, leitura | 0 / 0 / 8 | fluxo, PROTOCOLOS, AGENTS | fundida em `agata-fluxo` seção 1 |
| agata-ferramentas | 1.190 | 17 | 248 | achar skill por tema | tema para peça da caixa | 0 / 0 / 5 | fluxo | fundida em `agata-fluxo` seção 2 |
| agata-mudanca-segura | 2.605 | 38 | 231 | mudança no runtime da Máquina | três perguntas, acoplamentos | 1 / 0 / 13 | fluxo, aplicar | fundida em `agata-fluxo` seção 4 |
| agata-aplicar-proposta | 3.685 | 46 | 138 | proposta P-8 | criar, aplicar, registrar | 1 / 0 / 17 | processo-lote | fundida; nome mantido (citado em `PROJETO.md`) |
| agata-painel | 4.630 | 48 | 306 | painel na porta 20146 | regras de CSP, popup, medição | 1 / 0 / 17 | nenhuma | mantida (três armadilhas viram ponteiro) |
| agata-voz | 3.798 | 47 | 385 | falar, voz do sistema | piper, saídas, regras | 1 / 1 / 25 | morse | mantida; absorve morse |
| agata-time-inovacao | 3.068 | 36 | 218 | melhoria nova com SDD | papéis e ciclo do time | 0 / 0 / 9 | elephant | mantida; absorve elephant |
| elephant-goldfish-sdd | 3.567 (+ `openai.yaml`) | 40 | 212 | funcionalidade grande (SDD) | método elefante e peixinhos | 0 / 0 / 7 | time-inovacao | fundida em `agata-time-inovacao` |
| experimento-agata | 4.690 | 52 | 196 | rodada de experimento | critério prévio, registro | 0 / 0 / 3 | llm-fundamentos | fundida em `agata-llm-fundamentos` seção 5 |
| morse | 3.158 | 30 | 290 | conversa de voz e debate | escuta, turnos, handoff | 0 / 1 / 4 | voz | fundida em `agata-voz` seção 3 |

Fora da consolidação, sem mudança: `design-taste-frontend` (terceiro, 2.424.169 bytes, 39 arquivos, 528 linhas; o lint já avisa) e as cinco cópias de terceiros em `.claude/skills/`. O `INDICE.md` foi reescrito (seção 6).

## 2. Destino depois: 10 skills do Agata

| Skill | Conteúdo | Gatilho (descrição) |
|---|---|---|
| `agata-fluxo` | entrada única: medir o estado (seção 0), conduta (1), escolha da skill (2), divisão e proteção (3), runtime (4), afirmar com prova e registrar (5), parar (6), comandos padrão (7) | início de qualquer tarefa |
| `agata-aplicar-proposta` | ciclo P-8 e de lote: classes, regras, papéis, passo a passo, CI por commit, pacote, lições de 07/11, armadilhas | proposta ou aplicação protegida |
| `agata-equipe` | papéis, barreiras, proibições de git, passagem, pacote mínimo para subagente (seção 9), fallback e cota, vigia, canal MSG, mudança protegida em equipe, assinatura | trabalho com dois ou mais membros |
| `agata-painel` | painel operacional, porta 20146 | textos, cores, popups, medição do painel |
| `agata-voz` | voz do sistema, falar, conversa falada e debate | ler em voz alta, voz, TTS |
| `agata-conversar-com-seth` | caminhos A a D para falar com a Seth ou ler a conversa dela | conversar ou acompanhar a Seth |
| `agata-relay-provedores` | adaptadores de chats web no Relay | provedores web, rodadas do Relay |
| `agata-time-inovacao` | ciclo SDD do time e método elefante e peixinhos | melhoria nova com SDD |
| `agata-engenharia-reversa` | REA: allowlist e destino de escrita (sem mudança) | análise estática de app ou bundle |
| `agata-llm-fundamentos` | falhas de LLM, mecanismo do Agata, lacunas, experimento | custo, contexto, alucinação, experimento |

## 3. Linhas removidas, com motivo

Granularidade: bloco (seção ou item). Cada linha removida está no `.diff` com prefixo `-`. O texto integral de cada skill removida está em `extras/arquivo-skills-12-11/` (cópias byte a byte, conferidas contra `origin/main`: 12 de 12 arquivos iguais). Motivos: **óbvio** (o modelo já sabe, sem consequência no Agata); **duplicada** (o mesmo texto existe em outro lugar desta lista ou no canon); **canon** (o canon já diz, e a skill aponta); **mecanismo** (um script ou CI já confere); **ponteiro quebrado** (cita item que não existe); **vazio**; **formato** (arquivo de interface de um modelo).

**agata-processo-lote** (36.138 bytes):
- "Equipe e papéis": a lista de sete papéis: duplicada de `agata-equipe` (seção 3).
- "Regras de segurança": a lista de proibições de git: duplicada de `agata-equipe` seção 4.
- "Regras de segurança": "check obrigatório vale por head do PR": duplicada de "CI é por commit".
- "Regras de segurança": "restaurar arquivo gerado": duplicada da regra 5 e da armadilha "Arquivos gerados".
- Passo 2: "(armadilha 'Âncora SDD')": ponteiro quebrado; a armadilha não existe. A instrução de teste da âncora fica.
- Passo 5: "(armadilha 'Premissa de proposta')": ponteiro quebrado; a premissa está na pauta do auditor, item 1, mantida.
- Passo 7: parágrafo sobre mudança fora do repo: coberto por `agata-fluxo` seção 4 (ponteiro mantido).
- "Armadilhas": nada removido. Lições de 07/11 (a a o): mantidas integralmente.

**agata-aplicar-proposta** (3.685 bytes):
- "Criar uma proposta", passo 2: "desfaça a mudança com `git checkout <arquivos>`": proibição de git (`agata-equipe` seção 4) para este caso; o teste em cópia descartável (passo 4) fica.
- "Aplicar", passo 4 (runtime): coberto por `agata-fluxo` seção 4 (ponteiro mantido).
- Demais passos e armadilhas: duplicados do processo (passos 1 a 12), mantidos uma vez.

**agata-fluxo-equipe** (6.668 bytes):
- Lista de ponteiros para outras skills no início ("protocolo MSG, painel"): duplicada da tabela de escolha (`agata-fluxo` seção 2).
- Frase "conte o turno com o contador disponível": movida para `agata-fluxo` seção 1 (ainda no texto).
- Seção 9 ("pacote mínimo para subagente", trazida pelo pacote-mecanico-12-11): movida inteira para `agata-equipe` seção 9, sem mudança de texto. Os checks do pacote passam a ler `agata-equipe`.
- Demais seções (partida, vigia, fallback, cota, armadilhas, devolutiva, assinatura, mudança em equipe): mantidas em `agata-equipe` seções 1, 2, 6, 11, 12, 13, 14 (numeração deslocada por causa da seção 9).

**agata-conselho-memoria** (3.287 bytes):
- "No início da sessão": mantido em `agata-fluxo` seção 0.6 (sem o número "10").
- "Identidade de modelo": mantida em `agata-fluxo` seção 1, como ponteiro para `PROTOCOLOS.md`.
- "Proposta e aplicação (resumo)": duplicada de `AGENTS.md` (só o Humano roda `aprovar.sh`). A checagem de `APROVADO-` foi mantida em `agata-fluxo` seção 5.

**agata-carregar** (2.671 bytes):
- Passos 1 a 6 e o bloco de três linhas: canon (`PROTOCOLOS.md`, "Carregar e formatos", linhas 9 a 22). Resumo mantido em `agata-fluxo` seção 0.
- "Depois do carregar, a linha de turno": canon (`PROTOCOLOS.md`).
- "Contexto automático (28/10)": mantido em `agata-fluxo` seção 0.6.

**agata-disciplina** (3.557 bytes):
- Seção 1 (formato, selo, hora): canon (`PROTOCOLOS.md`, selo obrigatório). Regra "sem cabeçalho = resposta inválida": mantida. Verificação mecânica: `auditoria_turno.py` confere o cabeçalho.
- Seção 2 (modo conciso): canon (`REGRAS.md`, NPR).
- Seções 3 a 6 (aviso antes de ação externa, consulta antes de mexer em trabalho alheio, dependências antes de reiniciar, leitura declarada): mantidas em `agata-fluxo` seção 1.
- Seção 7 (verificação antes de entregar): mantida em `agata-fluxo` seção 5.
- "Teste da skill" (checklist de cinco itens): óbvio; repete as seções 1 a 7.

**agata-ferramentas** (1.190 bytes): passos e regras mantidos em `agata-fluxo` seção 2. Nada removido.

**agata-mudanca-segura** (2.605 bytes): intro, "por quê", portão das três perguntas, acoplamentos, prova pelo caminho real e registro mantidos em `agata-fluxo` seção 4. Nada removido.

**elephant-goldfish-sdd** (3.567 bytes):
- Conceito, orientação didática, ciclo de sete passos, artefatos mínimos, "pare" e a nota "não afirmar plugin oficial": mantidos em `agata-time-inovacao` seções 1 e 3.
- `agents/openai.yaml` (interface de um modelo): formato; arquivado em `extras/`.

**experimento-agata** (4.690 bytes):
- "Fontes locais" (quatro bullets sobre documentos do Experimento 2, fora do repo): resumido em uma frase em `agata-llm-fundamentos` seção 5; os nomes dos documentos ficam.
- Antes da rodada, executar e registrar, aprender com acertos, lições de método: mantidos em `agata-llm-fundamentos` seção 5.
- "Limites de mudança": resumido. Mudança na skill por P-8 está em `agata-llm-fundamentos` seção 4.

**morse** (3.158 bytes): princípio, ruído, handoff para a Seth, debate e métrica mantidos em `agata-voz` seção 3 (métrica marcada como "não medida").

**agata-llm-fundamentos** (SKILL.md, 3.666 bytes; `mapa.md` e `pesquisa.md` sem mudança):
- "O que vale sempre", item 3 (corte de treino): óbvio; a regra de atualidade continua na tabela da seção 1.
- Item 5 (exemplo vira molde): óbvio para qualquer LLM; a fonte continua em `pesquisa.md`.
- Item 6, trecho "no Opus 5.5 o padrão é medium e o raciocínio adaptativo fica ligado": dado de fornecedor que muda, sem medição nesta sessão; a fonte continua em `pesquisa.md`.
- Demais itens: mantidos em `agata-llm-fundamentos` seção 2.

**agata-equipe** (9.950 bytes): reescrita. "Por quê" encurtado, com os mesmos números. Tabela de papéis, barreiras, proibições, passagem, crescimento e "o que só o Humano decide" mantidos.

**agata-painel**: três armadilhas viram ponteiro por duplicidade (`pkill -f` em `agata-equipe` seção 11; `git stash` em `agata-fluxo` seção 3; `equipe.py aceitar-linha` em `agata-equipe` seção 1.8). Ponteiro para o conselho atualizado.

**agata-conversar-com-seth**: o bullet "Citação inventada se expurga" (texto longo) vira ponteiro curto para `agata-fluxo` seção 1. A regra continua inteira na skill do fluxo.

**agata-relay-provedores**: `agents/openai.yaml` (formato) arquivado em `extras/`. Ponteiro "agata-mudanca-segura" trocado por `agata-fluxo` seção 4.

**agata-time-inovacao**: "Diário de erros e acertos" (cabeçalho com instrução e nenhuma entrada): vazio desde a criação. Registro de rodadas vai para MEMÓRIAS por PR (`agata-fluxo` seção 5).

**agata-voz**: nada removido. Acrescentado: morse (seção 3) e "adaptar à saída de áudio disponível" (decisão do Humano de 03/11, antes só na memória).

**INDICE.md de skills**: reescrito. A frase antiga dizia que `defuddle`, `json-canvas`, `obsidian-bases`, `obsidian-cli` e `obsidian-markdown` estavam fora do git. `git ls-files` mostra que estão versionados em `.claude/skills/`. O texto novo não repete a frase (decisão 4 da seção 9).

**Não mudados de propósito:** `MEMÓRIAS.md` (append-only), `MEMORIAS-MORNO.md`, `SETH-DIARIO.md`, `propostas/aplicadas/` (história); `redesign/nova_versao/spec/brainstorm.md`, linha 25 (cita `agata-carregar`; é spec, que exige proposta própria; ver seção 8).

## 4. ECC: referências e proposta separada

Medido (arquivos vivos = todo o repo, menos `ferramentas/fontes/`, `extras/`, `propostas/`, `memoria/`, `historia/`, os índices gerados, `MEMÓRIAS.md`, `MEMORIAS-MORNO.md`, `SETH-DIARIO.md` e os `.diff`):
- Peças em `ferramentas/fontes/ecc/skills/`: 314 (`ls ... | wc -l`).
- Referenciadas por caminho `ecc/skills/<nome>` em arquivos vivos: 0. As únicas ocorrências estão em `propostas/aplicadas/*.diff` (história).
- Referenciadas por nome entre crases em arquivos vivos: 0.
- Nome exato (palavra inteira) em arquivos vivos: 3 peças aparecem em `ferramentas/test_ferramentas.py` (`unified-memory`, `continuous-learning-v2`, `agentic-os`), no teste de quarentena. Os demais casos são palavras comuns (`benchmark`, `council`, `taste`, `x-api`, `ck`, `continuous-learning` em `test_alexandria.py`), não a skill.
- `ferramentas/ferramentas.py` cita nomes para classificar (QUARENTENA e AJUSTES), o que é índice, não uso.
- Comando para repetir: `grep -rlwF -f <lista-de-314-nomes> .` com as exclusões acima; o resultado acima sai dele.

Contexto que o modelo carrega por padrão: só `ferramentas/INDICE.md` (lido por `agata-fluxo`); o corpo das 314 peças não entra no contexto. Por isso mover para `extras/` reduz o que o repositório guarda e indexa, não o que o modelo carrega (ganho de contexto: zero, medido pelo mecanismo, não por sessão).

Proposta (não incluída neste diff; decisão do Humano): arquivar as 314 peças em `extras/` e apontar `FONTES` de `ferramentas/ferramentas.py` para lá, com o teste de quarentena ajustado. É um lote próprio, porque altera o indexador e o teste.

## 5. Antes e depois (medido)

| Medida | Antes (`origin/main` 2ec04181 + pacote-mecanico-12-11) | Depois (este diff) | Como medido |
|---|---|---|---|
| Pastas de skill em `.agents/skills/` | 21 (mais `INDICE.md`) | 11 (10 do Agata e `design-taste-frontend`) | `ls`, `git ls-tree` |
| Skills próprias do Agata | 20 pastas | 10 | contagem do lint |
| Descrições carregadas sempre (caracteres) | 5.969 (20 skills) | 3.626 (10 skills), -39% | `desc_chars` de `qualidade_llm.py` |
| Linhas dos SKILL.md do Agata | 1.183 | 890 | leitura do frontmatter e do corpo |
| Bytes das pastas do Agata (todos os arquivos) | 150.733 | 123.737 | `git ls-tree -l` e `find` |
| Peças na caixa de ferramentas | 421 (tema `agata`: 21) | 411 (tema `agata`: 11) | `reindexar` |

Não medido: tokens por sessão (a medição é de bytes e caracteres); quantas vezes um modelo carrega cada skill; se um modelo acerta a skill certa pela tabela de `agata-fluxo` (não há teste de roteamento).

## 6. Testes e verificação

- Lint de skills: `python3 redesign/painel_operacional/qualidade_llm.py` gera `skills` com `11/11 sem problema; 1 com aviso`. O aviso é `design-taste-frontend`, 528 linhas, já existia. Nenhum aviso de caminho inexistente nas skills do Agata.
- CI local, no estado deste diff aplicado sobre `origin/main` 2ec04181 com o pacote-mecanico-12-11 aplicado: `uv run --offline --with pytest bash scripts/ci_sdd_local.sh` com `CI LOCAL: TUDO OK` (40 passos OK, 0 falhas, saída 0).
- Testes da caixa de ferramentas: `cd ferramentas && python3 -m unittest test_ferramentas` (como a CI roda): 5 testes OK. Rodar a partir da raiz do repo falha por colisão de nome do pacote `ferramentas` (não investigado em `origin/main`).
- Índice: `python3 -I ferramentas/ferramentas.py reindexar`: 421 para 411 peças.
- Aplicação: `git apply --cached --check` com índice temporário a partir de `origin/main` 2ec04181 com o pacote aplicado: OK.
- Arquivo: 12 de 12 cópias em `extras/arquivo-skills-12-11/` iguais aos originais de `origin/main`.
- Ponteiros mortos: busca de nomes removidos em arquivos vivos. Restam só: `redesign/nova_versao/spec/brainstorm.md` (linha 25, spec), e o histórico (`MEMÓRIAS.md`, `MEMORIAS-MORNO.md`, `propostas/aplicadas/`).

## 7. Não medido

- Se um modelo encontra a skill certa com a nova tabela de escolha (sem teste de roteamento).
- Tokens reais por sessão, e a diferença de contexto carregado por modelo (Goose e OpenCode também leem `.agents/skills/`: não medido neste diff).
- Horas de agente e tamanho de arquivo por proposta (apetite, R2): não medido.
- Se alguma sessão antiga ainda cita os nomes removidos de memória: não medido.

## 8. Dependências e conflitos

- Base: `origin/main` `2ec04181` com `propostas/pacote-mecanico-12-11.diff` aplicado. **Aplicar depois de pacote-mecanico-12-11.** Se o pacote não entrar antes, este diff não aplica (testado com `git apply --cached --check` sobre a base com o pacote).
- Arquivos que os dois diffs tocam (o pacote primeiro, este depois):
  - `.agents/skills/agata-fluxo-equipe/SKILL.md`: o pacote acrescenta a seção 9 (pacote mínimo); este diff remove o arquivo e move a seção 9 para `agata-equipe`, sem mudança de texto.
  - `.claude/agents/agata-dev.md` e `.claude/agents/agata-pesq-processo.md`: o pacote acrescenta a seção "Pacote mínimo" e os campos de modelo; este diff troca só o ponteiro de skill (`agata-processo-lote` para `agata-aplicar-proposta`, e `agata-fluxo-equipe` para `agata-equipe`).
  - `scripts/testar_mecanismos.py` e `scripts/conselho_mecanismos.py`: o pacote lê `agata-fluxo-equipe/SKILL.md`; este diff troca o caminho para `agata-equipe/SKILL.md` (quatro referências no total).
- Se outro lote tocar `.agents/skills/**`, `ferramentas/indice.json`, `ferramentas/INDICE.md`, `ferramentas/README.md`, `redesign/goose/AGENTS.md` ou os dois `.claude/agents/*.md` acima antes, este diff é refeito sobre o `main` novo. Uma proposta por vez contra HEAD.
- Sem alteração, de propósito, nos arquivos que apontam para skills que continuam: `scripts/rea_leitura.sh` (`agata-engenharia-reversa`), `scripts/equipe/inicio.sh` (`agata-fluxo` §0), `PROJETO.md` (`agata-aplicar-proposta`), `AGENTS.md` (`agata-voz`), `redesign/painel_operacional/qualidade_llm.py` (`agata-llm-fundamentos`).
- `redesign/nova_versao/spec/brainstorm.md`, linha 25, ainda cita `agata-carregar`. Spec é P-8 (`propostas/README.md`): a troca pede proposta própria.

## 9. Decisões para o Humano (não entram neste diff)

1. Arquivar as 314 peças do ECC em `extras/` (seção 4), em lote próprio.
2. Juízo de agrupamento: `experimento-agata` dentro de `agata-llm-fundamentos`; `elephant-goldfish-sdd` dentro de `agata-time-inovacao`; `morse` dentro de `agata-voz`. Separadas, a conta sobe para 13 skills.
3. Formato: aprovar a saída de `agents/openai.yaml` (Relay e elephant), arquivada em `extras/`.
4. Confirmar a correção do INDICE sobre os cinco terceiros de `.claude/skills/` (versionados, não fora do git).

## 10. Reversão

- Antes da assinatura: não assinar; o PR de proposta só tem registro e o `.diff` é inerte.
- Depois da aplicação (sobre a base com o pacote-mecanico-12-11): `git apply -R propostas/aplicadas/skills-consolidadas-12-11.diff` (o diff inclui as pastas novas em `extras/`, então a reversão as remove), depois `python3 -I ferramentas/ferramentas.py reindexar`. Ou revert do commit de aplicação. Sem perda: o texto antigo volta integral.

## 11. Comando de assinatura

Depois do merge deste PR de proposta (não antes), o Humano cola no terminal, sem `!`:

`bash scripts/aprovar.sh skills-consolidadas-12-11 "<motivo>"`

Antes, confirme que `propostas/skills-consolidadas-12-11.diff` existe (`ls propostas/skills-consolidadas-12-11.diff`). Assinatura, aplicação e junção do PR de aplicação são do Humano.
