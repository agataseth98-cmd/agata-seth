# Brainstorm: transição do modo de trabalho para o núcleo de desenvolvimento

Status: rascunho do arquiteto SDD. Decisão: pendente (ver decision.md). Data: 07/11/2026. Base medida: origin/main 83334fde.
Rótulos: [medido] = comando ou busca com saída citada; [lido] = arquivo lido, sem execução; [inferido]; [não medido].

## Pedido

Decisão do Humano, 07/11/2026, como chegou ao arquiteto: "prepare a transição deste modelo de trabalho para fazer parte do núcleo de desenvolvimento do Agata, universalista e disponível a todos os membros do Conselho".
[medido] Essa decisão não está no canon de origin/main: busca por "universalista" em MEMÓRIAS.md, PROJETO.md, REGRAS.md, ONDE_ESTAMOS.md e propostas/ achou só a linha 363 de MEMÓRIAS.md, que é outra decisão (renomear "dupla" para "Equipe", também "universalista"); "núcleo de desenvolvimento" não apareceu em nenhum arquivo do repositório fora de memória restrita (busca com git grep). Prova só "não encontrado nesta busca". Pela lição i do lote, a decisão vira registro ou proposta antes de virar código.

## Problema medido

1. O processo de lote mora em skills e agentes que não chegam a todos os modelos.
   - [medido] `.agents/skills/INDICE.md` não tem linha para 5 de 20 pastas com SKILL.md: agata-disciplina, agata-engenharia-reversa, agata-processo-lote, agata-time-inovacao e elephant-goldfish-sdd. As duas skills de processo, agata-processo-lote e agata-time-inovacao, ficam de fora.
   - [lido] Os agentes em `.claude/agents/` usam o formato do Claude Code (campos name, description e tools). [não medido] Se Codex, Gemini ou Goose leem esse formato.
2. AGENTS.md, que o time pede que todo modelo leia, não aponta para o fluxo universal nem para o índice de skills.
   - [medido] Não há menção a agata-fluxo nem a INDICE em AGENTS.md. Há a regra de cache e o verificador (linha 21), a economia de tokens (linha 22) e a ordem de carregar PROMPT_CARREGAMENTO.md (linha 5).
   - [medido] AGENTS.md não tem "worktree" nem "CI local". [não medido] Quais CLIs carregam AGENTS.md por padrão.
3. `agata-fluxo` é o fluxo declarado para qualquer LLM ("Vale para qualquer modelo da Confederação", SKILL.md, e linha 10 do INDICE), mas não tem as regras que faltam.
   - [medido] Zero ocorrências de cache_conselho, "lote", "delega", "numer" (perguntas numeradas), "rm" e "mv" no arquivo.
4. A Seth, pelo gateway, recebe a doutrina fixa, o estado e o resumo do cache, mas não o processo de lote.
   - [lido] `_DOUTRINA_FIXA` tem 10734 bytes (seth_gateway.py, linha 103, medido com ast). Não há "worktree", "lote" nem "skill" nela (a constante vai da linha 103 à 253).
   - [lido] Skills só aparecem como sugestão, e só com SETH_SKILLS_SUGERE=1 (seth_gateway.py, linha 1174; redesign/alexandria/skills.py, linha 159: "nada foi carregado"). O padrão é desligado.
5. As lições medidas de 07/11 estão só na proposta do PR #944 (propostas/skill-processo-lessons-07-11.md, branch proposta/skill-processo-lessons-07-11). [medido] Não estão em origin/main.
6. Duas partes de `agata-fluxo` contradizem o próprio time.
   - §8 manda copiar as alterações para backup e depois rodar `git checkout --` nelas. Isso restaura sem ordem explícita, contra a regra de remoção e restauração do lote. [lido]
   - §6 diz "A Seth carrega esta skill pela hidratação". [lido] O código de injeção lido não confirma isso. [não medido] Se a Seth tem alguma ferramenta de leitura de skill.
7. Já existe um mecanismo universal de coordenação: agata-fluxo-equipe, para "qualquer membro do Conselho" (SKILL.md, linha 3, na descrição, e linha 12), e scripts/equipe/equipe.py (812 linhas, 47169 bytes) [medido]. A matriz de propriedade e a vigia já estão lá.

## Alternativas

A. Texto inteiro do processo em AGENTS.md.
B. Skill-guia nova, com ponteiro em AGENTS.md e entrega das regras pelo cache do Conselho.
C. Módulo de código com função de guia (por exemplo, guia.py que imprime o guia) que cada modelo chama.
D. Reaproveitar o que existe: agata-fluxo vira o guia curto, as duas skills de processo entram no seu roteiro e no índice, AGENTS.md ganha um ponteiro para agata-fluxo, e o gateway recebe um ponteiro de uma linha só se o Humano decidir.

Avaliação:
- A. Descartada. AGENTS.md já tem 7193 bytes [medido]. O texto do processo de lote tem 22305 bytes [medido]. A regra de economia de tokens (AGENTS.md, linha 22) veda carregar isso em toda sessão. O gateway não lê AGENTS.md: "AGENTS" não aparece em seth_gateway.py [medido]. Só alcançaria os CLIs que leem AGENTS.md.
- B. Descartada como mecanismo novo. Criaria um terceiro fluxo ao lado de agata-fluxo, que já é o universal. O cache é um registro append-only, e o gateway injeta só as 3 últimas entradas, de até 160 caracteres (cache_conselho.py, `resumo_hidratacao`) [lido]. Não serve de canal de doutrina. Fica o uso que AGENTS.md já prevê: o cache guarda fato e pendência.
- C. Descartada agora. É código novo com testes e P-8 para entregar um texto que a leitura de um arquivo já entrega. Não resolve a lacuna de conteúdo (problema 3) e não chega ao gateway sem mais código. Fica de reserva se a regra precisar de estado calculado, como o quadro da Equipe.
- D. Escolhida. É o menor mecanismo que resolve. Não cria serviço, nem módulo de produto, nem fluxo novo: muda texto e índice, e ganha testes de regressão. Corrige os problemas 1, 2, 3, 5 e 6. O problema 4 depende de uma decisão do Humano (gateway). O problema 7 vira o ponto de entrada do mesmo fluxo.

Ponteiro para o gateway, se for aprovado: pelo canal de estado de `_injeta` (seth_gateway.py, linhas 1132 e 1160), e não pela doutrina. [lido] `MARCADOR` é o hash de `_DOUTRINA_FIXA` (linha 255), e o próprio código avisa que mudar a doutrina faz conversas em andamento serem reidratadas (comentário logo acima da linha 103). [inferido, não testado] Uma linha no bloco de estado não muda o hash.

## Escolha

D. O resultado é um guia curto (agata-fluxo, com um resumo de regras de lote) mais um roteiro completo (agata-processo-lote), uma entrada no índice para cada skill de processo, um ponteiro no AGENTS.md e testes que travam esses pontos. Nenhum modelo recebe regra diferente: a regra é a mesma para todos.

## Usuários

- Humano: decide, assina e lê a devolutiva em poucas linhas.
- Orquestrador (hoje, Claude Code): coordena e delega operação a agentes. Não faz a operação.
- Operários: agentes com arquivos próprios. Subagente sem permissão de escrita devolve texto, e quem coordena grava e confere (armadilha do lote, 06/11).
- Membros da Equipe (Codex, Gemini, Goose, Seth e quem entrar): entram por agata-fluxo-equipe e por equipe.py [medido]. [não medido] Quais leem AGENTS.md.
- Conselho Remoto: usa o CLI do cache (docstring de cache_conselho.py) [lido].
- Faixa pública (seth-public): fica de fora por desenho. O gateway tira o sistema e o histórico oculto antes de enviar (`_preparar_payload_publico`, seth_gateway.py, linhas 567 a 580, e 1294 a 1295) [lido].

## Estado que muda

- Texto: uma linha em AGENTS.md; uma seção nova em agata-fluxo/SKILL.md, e a correção de §6 e §8; cinco linhas em .agents/skills/INDICE.md.
- Gerado: ferramentas/indice.json e ferramentas/INDICE.md, só se a descrição de alguma skill mudar (armadilha "Índice derivado" do lote).
- Testes e CI: pasta nova de testes; a mesma lista de pytest em scripts/ci_sdd_local.sh e em .github/workflows/sdd.yml [medido: as duas listas hoje são iguais e precisam continuar iguais].
- Gateway, só se D2 for aprovada: uma função de ponteiro e uma linha em `_injeta`.
- Não muda: formato e dados do cache; scripts/equipe/equipe.py; REGRAS.md; PROJETO.md; agata-processo-lote, exceto a aplicação do PR #944, que é outro lote.
- Registro: .diff e .md em propostas/ (PR de proposta), e entrada de decisão em MEMÓRIAS.md (lição i).

## Erros e concorrência

- Duas mudanças no mesmo arquivo (agata-fluxo/SKILL.md ou INDICE.md) em propostas diferentes: aplicar uma de cada vez, em sequência. Não há mudança concorrente no mesmo arquivo hoje [medido: só o PR #944 toca agata-processo-lote].
- Ponteiro para arquivo que não existe: pegado pelos testes C1 e C6 no CI.
- Resumo que cita uma lição inexistente: pego pelo teste C9 (ids). Conteúdo errado dentro de uma lição existente não é pego por teste: lacuna L2, revisão cruzada.
- Modelo que não lê AGENTS.md nem o índice: não recebe o ponteiro. [não medido] Quantos.
- Cache: escrita com trava (fcntl.flock, cache_conselho.py, linha 118), fsync e cadeia de hash. Segredo é recusado com saída 2. Dado pessoal vira marca.
- Gateway (D2): a linha de estado não muda MARCADOR. [não medido] Se o cliente descarta mensagens de sistema, a linha volta a cada turno: custo de contexto.
- Remoção ou restauração destrutiva: fica fora do fluxo, pelo teste C4.

## Migração

- Não há migração de dados.
- Conversas em andamento: não são afetadas se o ponteiro do gateway for pelo canal de estado (D2). Se fosse pela doutrina, seriam reidratadas (linhas 100 a 103 de seth_gateway.py).
- Lições de 07/11: o resumo do fluxo só pode citar as lições (ids a a o) depois que skill-processo-lessons-07-11 estiver assinada e aplicada. Antes disso, o teste C9 fica vermelho. Ou se junta a proposta, ou se espera.
- Decisão de 07/11: entrada de registro em MEMÓRIAS.md por PR, com número na junção.

## Observabilidade

- CI: os testes rodam no run do commit (regra "CI é por commit" do lote).
- Gateway (D2): hoje não há sinal de que o ponteiro foi injetado. [inferido] Pode seguir o padrão dos registradores que já existem em seth_gateway.py (linhas 1696 a 1760), mas isso é código novo e não está decidido.
- Adoção, isto é, quem leu o ponteiro: [não medido]. A proposta não cria telemetria de leitura (lacuna L1).
- Verificador: `python3 redesign/router/auditoria_turno.py --verificar < arquivo` já aponta caminho inexistente em texto de modelo (auditoria_turno.py, linha 1531) [lido].

## Reversão

- Ponteiro em AGENTS.md: nova proposta que remove a linha. Correção é entrada nova; não se reescreve histórico (Regra 4).
- Gateway (D2): `SETH_PROCESSO_HIDRATA=0` desliga sem código, no mesmo padrão de SETH_CACHE_CONSELHO_HIDRATA (seth_gateway.py, linha 1160). Aplicar a variável exige reiniciar o serviço: ordem do Humano.
- Seção nova em agata-fluxo: revertida por proposta. O comando destrutivo de §8 não volta: a remoção do bloco é parte do desenho.
- Testes e CI: saem da lista na mesma proposta.
- Arquivos: nenhum é apagado. Se for preciso tirar algo do caminho, usa-se mv para uma pasta de arquivo, com ordem do Humano.

## Sucesso

- Medido agora: testes C1 a C11 verdes no CI do commit; índice com 20 de 20 pastas de skill.
- Medido na próxima rodada de lote: cada proposta passa pelo resumo do fluxo, sem violação de rm, de restauração sem ordem, de assinatura feita por modelo. [não medido] Hoje não há contagem.
- Não é sucesso: "todo modelo recebeu o guia" sem medição de leitura (lacuna L1).
