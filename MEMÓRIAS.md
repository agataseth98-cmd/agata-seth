# MEMÓRIAS.md — Sistema Agata

**Você está lendo o arquivo de história. É append-only: nada se apaga, nada se edita — só se acrescenta.**
Desde a entrada (271) (26/08/2026), entrada nova entra logo abaixo do marcador `ENTRADAS-NOVAS` abaixo — mais recente primeiro, pra ler o estado herdado sem varrer a história inteira. Antes de (271) a ordem era o oposto (mais antiga primeiro, mais recente acrescentada no fim físico); motivo, autorização do Humano e portão das três perguntas cumprido: ver a própria entrada (271), logo abaixo do marcador. Correção nunca é edição — é entrada nova apontando a que corrige. Para o estado atual (não o histórico), leia PROJETO.md.

## Como ler este arquivo (para modelos)
- **Não leia tudo.** Leia o TOPO, logo abaixo do marcador — é o estado herdado mais recente. O resto é lastro, consultável por busca quando um número de entrada for citado.
- **Entrada citada por número** — `(n)` — pode ser buscada diretamente **a partir de (49)**. Toda regra e todo bug remetem a um número; é assim que se checa se algo é fato ou lembrança.
- **Cópia recebida pode estar atrás do canon.** Antes de escrever qualquer entrada nova, confira o TOPO do remoto (logo abaixo do marcador — não o fim físico, que agora é a história mais antiga). Se não puder conferir, diga até onde a sua cópia vai e não numere nada.
- **Grafias antigas do nome** (com acento, com "h") aparecem na história migrada. Não se corrigem: história não se edita. A grafia canônica hoje é **Agata**.

**MEMÓRIAS por período (Fase 4, desde MEMÓRIAS (357), 06/09/2026): este arquivo é só a camada QUENTE.** Uma entrada `(n)` citada aqui e não encontrada abaixo do marcador não sumiu — migrou pra uma camada mais fria, conforme envelhece, sempre pelo mesmo mecanismo (`scripts/migrar_periodo.py`), nunca editada, só realocada (prova byte a byte: `scripts/verificar_migracao_periodo.py`). Três camadas, mesmo número global, arquivo muda:
- **Quente = este arquivo.** Entradas recentes, mesma janela de custo que a hidratação já usa (25.000 chars a partir do topo).
- **Morno = `MEMORIAS-MORNO.md`.** Entradas que saíram de quente, ainda mutável, mesma disciplina de topo/append-only (P-5 protege as duas).
- **Frio = `MEMORIAS-FRIO-<data>[-N].md`.** Chunks de ~500 linhas, selados (`scripts/selar.sh` + `git tag`) assim que fecham — imutáveis depois disso (P-14, não mais P-5).

**Período de aderência: até 04/10/2026 (4 semanas a partir de (357)).** Ferramentas derivadas (índices, vault Obsidian, busca semântica) que ainda assumem "MEMÓRIAS.md = história inteira" são atualizadas dentro desta janela — listadas na própria entrada (357). Até lá, um resultado desatualizado dessas ferramentas é lacuna conhecida, não achado novo; depois, é bug a corrigir. O que já protege a garantia mais forte (P-5, P-7, P-14) foi atualizado no mesmo commit que criou as camadas — não espera a janela.

## Os quatro tipos de bloco
- `(n) DIÁRIO` — fato coletivo, comum a todos.
- `(n) CONSELHO` — entrada, saída ou discordância de modelo, mais o veredito do Humano.
- `(n) MOD <modelo>` — memória pessoal. **Silo:** cada modelo deveria receber só os MODs com o seu `modelo-alvo`. Consentimento de publicação é por trecho, com data; o default é privado.
  *Hoje o silo é norma, não mecanismo: a hidratação é arquivo único e sem filtro. Recebeu MOD alheio, diga em uma linha e não use o conteúdo.*
- `(n) CORREÇÃO` — corrige uma entrada anterior sem editá-la; aponta o número que corrige.

**Correção sobre este preâmbulo (MEMÓRIAS (109)): a numeração NÃO é única globalmente antes de (49).** História migrada de mais de uma origem reinicia número por número — "(2)" sozinho aparece pelo menos 4 vezes, em datas diferentes. A partir de (49) a numeração é única e contínua; antes disso, cite por número **e data**. O bloco migrado (mais antigo, no fim físico deste arquivo) segue colado verbatim, sem editar uma vírgula — isso não muda; o que mudou nesta migração foi só a posição do corpo (49)+ e a direção de leitura.

<!-- ANCORA-SHA:INICIO (gerado por .githooks/pre-commit -- não editar as linhas abaixo à mão, o resto do arquivo é livre) -->
  SHA do commit ANTERIOR a este arquivo (limite conhecido: normalmente 1 commit atrasado; se o hook que grava esta linha falhar, pode ser mais -- ver a nota logo abaixo deste bloco, e PROJETO.md, "Memória e hidratação"): 656bd6f4f9c1ac7581bb1b08b823905515aca992
  Escrito em: 23/10/2026 14:41 -03
  URLs raw pinadas neste SHA (preferir estas -- imutáveis, sem risco de cache velho; mesma defasagem máxima do SHA acima):
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/656bd6f4f9c1ac7581bb1b08b823905515aca992/REGRAS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/656bd6f4f9c1ac7581bb1b08b823905515aca992/PROTOCOLOS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/656bd6f4f9c1ac7581bb1b08b823905515aca992/FALHAS.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/656bd6f4f9c1ac7581bb1b08b823905515aca992/PROJETO.md
    https://raw.githubusercontent.com/agataseth98-cmd/agata-seth/656bd6f4f9c1ac7581bb1b08b823905515aca992/MEMÓRIAS.md
<!-- ANCORA-SHA:FIM -->
<!-- Bloco de máquina (MEMÓRIAS (378)): SHA do commit anterior + URLs raw pinadas. Fica ACIMA do marcador ENTRADAS-NOVAS, que o P-5 não policia (só o corpo de entradas). Um leitor OFFLINE compara este SHA entre REGRAS.md, PROJETO.md e MEMÓRIAS.md -- se os três não baterem, a cópia é inconsistente. Numa interface que renderiza markdown estes comentários somem. Limite: normalmente 1 commit atrasado; mais se o hook falhar. -->

---

<!-- ENTRADAS-NOVAS:AQUI -- não editar esta linha à mão; ancora o controle P-5 em scripts/perimetro.sh; entrada nova sempre logo abaixo dela, nunca acima) -->
(824) DIÁRIO — 23/10/2026 · **Passo 1 do roteamento por capacidade aplicado: registro de capacidades em quatro camadas, sem mudar a rota. A doc do Laya foi corrigida: ele decide a rota desde 15/10.** As duas propostas foram assinadas pelo Humano em 23/10/2026 e são aplicadas juntas. (1) `capacidades-passo1-20261023`: `scripts/capivara_capacidades.py` grava `config/capivara/capacidades.json`. Cada modelo das filas tem `catalogo` (OmniRoute `/v1/models`), `declarado` (só documentação oficial), `medido` e `observado` (vazios até o passo 2, que exige proveniência completa). O selftest, com 13 casos, entra no CI. O gateway não lê o arquivo, então a rota não muda. A primeira leitura, às 13h41, deu 11 modelos: 8 com catálogo, 2 com documentação e 3 sem fonte. (2) `doc-laya-ativo-20261023`: em `config/modelos-gratuitos.md`, o texto de 13/10 ("roteador-sombra") fica riscado e a descrição do estado desde (718)/(719) é acrescentada: o Laya decide a rota e o Jev é a sombra. O roteamento entrou na V9 por decisão do Humano (V9, seção 35). A assinatura pelo `!` do chat não abre o pedido de senha, porque não há terminal interativo; ela foi feita no terminal do Humano.
Modelo: Claude Opus 5.5 (Claude Code, na Máquina) · vetor: clone com hooks (`scripts/clone_teste.sh`), selftest OK e `--conferir` OK; PRs 499 e 500 com CI verde · Autorização: Humano — "assinei as duas no terminal, aplique"

(823) DIÁRIO — 23/10/2026 · **Cabeçalho com o modelo real: `agata-seth · <modelo real>` só quando a resposta passa pelo gateway ou escriba da Seth; fora desse caminho, `agata · <modelo real>`.** Aplica `cabecalho-modelo-real-20261020`, assinado pelo Humano em 23/10/2026, às 13h23. O diff troca em `PROTOCOLOS.md` o parágrafo de 17/10 ("O nome no cabeçalho é `agata-seth`") pela regra de 20/10: o nome do modelo vem do indicador da interface ou da configuração medida da sessão, nunca da memória nem de outro modelo. Não duplica `cabecalho-agata-seth-20261017`: substitui o parágrafo que aquela proposta criou. Conferido antes da assinatura: `git apply --check` limpo sobre `2fceada`.
Modelo: Claude Opus 5.5 (Claude Code, na Máquina) · vetor: `git apply --check propostas/cabecalho-modelo-real-20261020.diff` · Autorização: Humano — "assinei, aplique"

(822) DIÁRIO — 23/10/2026 · **Primeira execução da migração de período (quente para morno e frio), em proposta consolidada.**

Decisão do Humano (23/10/2026): primeira execução agora; as próximas ficam para a janela de manutenção. Medido antes: quente com 478 entradas após o marcador (1.287.913 bytes) e morno com 3 entradas. Resultado: 40 entradas ficam no quente (24.638 caracteres); 438 vão para o morno, que fica com 412 entradas; 29 são congeladas no bloco frio `MEMORIAS-FRIO-2026-10-23.md`, com selo em `SELOS.txt` e elo em `SELOS.chain`. Conferido num clone antes: 787 entradas antes e depois, nenhuma perdida, nenhuma nova. A tag de git desse bloco ainda não foi criada: o selo só imprime a instrução.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(821) DIÁRIO — 23/10/2026 · **Hidratação com só a última entrada de MEMÓRIAS inteira.**

Assinado pelo Humano (`APROVADO-hidratacao-ultima-entrada-20261023`). Decisão do Humano: a hidratação carrega a última entrada de MEMÓRIAS inteira. As anteriores ficam em resumo de uma linha e são consultadas sob demanda pela busca do vault. Medido antes da aplicação: `.hidrata.md` de 91.907 para 66.647 bytes.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(820) DIÁRIO — 23/10/2026 · **Ajustes do aplicar.py: registro opcional, sem duplicar MEMÓRIAS, coautor correto.**

Assinado pelo Humano (`APROVADO-aplicar-ajustes-20261023`). A partir daqui, `--registro` é opcional. Quando o diff já mexe em MEMÓRIAS.md, o script recusa o `--registro`, para não duplicar a entrada. O coautor passa a ser configurável; o padrão para o agente claude é Claude Haiku 5.5.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(819) DIÁRIO — 23/10/2026 · **Correção da entrada (817): a medição da suíte paralela.**

A entrada (817) diz "Medido nesta aplicação: pendente do pre-commit". Essa frase ficou defasada. Medido depois, no `main` em 7e3d462: a suíte passou com 58/58 casos e 0 falhas, em 56,298 s (medição do Claude, em clones) e em 55,423 s (medição do Codex). As duas com saída 0. A aplicação da paralelização foi o PR 482, mesclado às 23h42 de 22/10. A suíte sem paralelização levava cerca de 205 s, medido antes na sessão. Esta entrada corrige só a frase de medição; o restante da (817) segue válido.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(818) DIÁRIO — 23/10/2026 · **Ajuste do P-8: merge de origin/main não é mudança nova.**

Assinado pelo Humano (`APROVADO-p8-merge-main-20261023`). O P-8 comparava o staged só com o HEAD do branch; num merge de origin/main, o conteúdo que vinha do main era recusado como mudança sem aprovação, embora já tivesse passado pela quarentena ao entrar no main. O ajuste aceita o staged idêntico ao blob do outro pai, só quando esse pai já é ancestral de origin/main. Qualquer outro staged segue o caminho normal (APROVADO-).

Medido antes da proposta: merge reproduzido do main no branch da proposta da correção da entrada (817) passou com 0 falhas; mudança sem aprovação em PROJETO.md continuou SUSPEITO (rc=1).

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(817) DIÁRIO — 22/10/2026 · **Paralelização da suíte de regressão dos controles (P-16).**

Assinado pelo Humano (`APROVADO-paralelo-suite-controles-20261022`). A suíte passa a rodar até 4 casos ao mesmo tempo, cada um num clone descartável; o repositório real não é tocado. Os agregados são impressos uma vez, no fim. O filtro serial por `FILTRO` continua igual. A confirmação de isolamento veio do Codex: suíte 58/58 com 0 falhas numa cópia isolada, e até 4 clones coexistindo. Esta aplicação só entrou depois dessa confirmação, como o Humano pediu. Medido nesta aplicação: pendente do pre-commit.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(816) DIÁRIO — 22/10/2026 · **Correção da documentação do importador do inbox (fila de revisão).**

Assinado pelo Humano (`APROVADO-docstring-inbox-revisao-20261022`). A aplicação anterior (PR 478) ficou em conflito depois que o pacote 2b entrou no main; foi fechada e reaplicada a partir do main atual, com o mesmo diff. Conteúdo: a documentação do importador passa a descrever a fila de revisão, e não a gravação direta em MEMÓRIAS. Medido: autoteste do importador 15/15 OK.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(815) DIÁRIO — 22/10/2026 · **Pacote 2b: mapa do PROJETO na hidratação (em vez do arquivo inteiro).**

Assinado pelo Humano (`APROVADO-pacote2b-mapa-hidratacao-20261022`, PR 458 mesclado). Depende do 2a, já aplicado (PR 476). Medido pelo Codex em cópia: hidratação de 124.718 para 88.325 caracteres; tokens reais do modelo local de 40.321 para 28.623; geração repetida dá o mesmo hash.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(814) DIÁRIO — 22/10/2026 · **Proposta para alinhar a documentação do importador do inbox ao comportamento atual.**

O cabeçalho ainda dizia que o script enviava POST para o escriba e gravava em MEMÓRIAS; a implementação atual copia notas para a fila de revisão humana. O diff proposto corrige essa descrição. Em cópia descartável limpa: selftest 15/15. A aplicação depende de assinatura P-8.

Modelo: Codex (na Máquina) · vetor: selftest local do importador · Autorização: Humano — "corrija por favor".

(813) DIÁRIO — 22/10/2026 · **Pacote 2a aplicado: migrador de história (modo historia) e gerador reprodutível do mapa do PROJETO.**

Assinado pelo Humano (`APROVADO-pacote2a-migrador-mapa-20261022`, PR 457 mesclado). Aplicado pelo fluxo padrão, sozinho. Medido pelo Codex em cópia: 7/7 testes; MEMÓRIAS.md com o mesmo SHA-256 antes e depois da cópia; mapa de 10.233 caracteres, abaixo do teto de 25.000. Não liga o mapa na hidratação (isso é o pacote 2b, PR 458, que depende deste).

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).


(812) DIÁRIO — 22/10/2026 · **Proposta para paralelizar a suíte de perímetro por controle.**

Proposta `paralelo-suite-controles-20261022.diff`, ainda sem aplicação. Em worktree baseada em `60d5367`, a suíte serial de referência levou 205,047 s (58 verificações, 0 falhas); com até quatro workers, cada controle em clone próprio e agregados uma vez, levou 58,414 s (58 verificações, 0 falhas), redução medida de 71,5%. Filtros explícitos seguem no caminho serial. `scripts/perimetro/p16_testes_dos_controles.sh` e a chamada do pré-commit não foram alterados; P-16 continua chamando `bash scripts/testar_perimetro.sh`.

Modelo: Codex (na Máquina).

(811) DIÁRIO — 22/10/2026 · **canon-mcp sem diario_anotar no chat, com o teste do escriba em memoria_acrescentar (par).**

Assinados pelo Humano (`APROVADO-canon-sem-diario-chat-20261022` e `APROVADO-teste-escriba-memoria-20261022`; PRs 471 e 472 mesclados). A aplicação anterior da proposta do canon falhou na suíte: o teste chamava diario_anotar, que a proposta tira do chat. O teste passa a usar memoria_acrescentar, que exercita o mesmo caminho do token. Medido: node scripts/testar_escriba_cliente.mjs PASS.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(810) DIÁRIO — 22/10/2026 · **Servidor canon do LibreChat recebe AGATA_PROJECT_TOKEN_FILE=/run/a.**

Assinado pelo Humano (`APROVADO-canon-token-env-20261022`, PR 469 mesclado). Causa encontrada no teste de gravação pela cascata: o servidor canon não recebia a variável, o cliente caía no caminho padrão e recusava a escrita ("token do projeto ausente ou inseguro"). Uma linha no bloco env do servidor canon. Medido: o token dentro do container passa todas as checagens do cliente.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(809) DIÁRIO — 22/10/2026 · **Escriba fase A: token por projeto, recusa de segredo antes de gravar, provas HTTP/MCP; token montado em /run/a.**

Assinado pelo Humano (`APROVADO-escriba-fase-a-20261022`, PR 466 mesclado). Diff feito pelo Codex na worktree fase-a-escriba-20261021 e revisado pelo Claude. Ajuste de falso positivo do P-1: caminho do token encurtado para /run/a (função preservada). Medido numa cópia com o diff aplicado: testar_capability OK; testar_net02_compose PASS; testar_escriba_http PASSOU. Exige token provisionado no host. Reinício do serviço seth-escriba a combinar.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(808) DIÁRIO — 22/10/2026 · **6 skills do Agata no modelo LLM-first (confederação).**

Assinado pelo Humano (`APROVADO-skills-llm-first-confederacao-20261022`, PR 464 mesclado). Diff feito pelo Codex na worktree agata-skills-utility e revisado pelo Claude; aplicou limpo no main 19c899d. Só texto de skill (agata-aplicar-proposta, agata-carregar, agata-conversar-com-seth, agata-fluxo-dupla, agata-fluxo, agata-mudanca-segura). Não altera código nem serviço.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(807) DIÁRIO — 22/10/2026 · **Saída externa volta a varrer só segredo; 422 passa a registrar a categoria do padrão no log.**

Assinado pelo Humano (`APROVADO-relaxa-pessoal-log-categoria-20261022`, PR 454 mesclado). Motivo: desde 11h23, pedidos ao seth-rapido com e-mail, telefone ou CPF no texto recebiam 422 do sanitizador. Decisão do Humano: relaxar. Só proxy.py muda. O log registra a categoria, nunca o trecho. Medido na proposta: autoteste do proxy e do sanitizador OK.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(806) DIÁRIO — 22/10/2026 · **Devolutiva final para CODE: seção 8 da skill agata-fluxo-dupla.**

Assinado pelo Humano (`APROVADO-devolutiva-code-final-20261022`, PR 461 mesclado). Diff elaborado pelo Codex em worktree própria e revisado pelo Claude. Só texto de skill: diferencia proposta, diff, assinatura, aplicação e merge. Não altera código nem serviço.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(805) DIÁRIO — 22/10/2026 · **Script preparar_assinatura.sh: confere checks, mescla o PR, atualiza o main e verifica o .diff; não assina.**

Assinado pelo Humano (`APROVADO-preparar-assinatura-20261022`, PR 455 mesclado). Motivo: a assinatura falhou quatro vezes em 22/10 pela mesma causa (o .diff ainda estava só no PR, e o comando era entregue antes do merge). A regra também está na memória. O script só mescla PR com checks verdes e nunca executa aprovar.sh.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(804) DIÁRIO — 22/10/2026 · **Importador do inbox grava na fila de revisão, não em MEMÓRIAS.**

Assinado pelo Humano (`APROVADO-fila-inbox-revisao-20261022`, PR 452 mesclado). O POST direto ao escriba exigia capability assinada, que o script não enviava (achado do Codex, 22/10, auditoria pré-trabalho). A gravação automática em MEMÓRIAS também não tinha par P-8. Agora a nota vai para `memoria/obsidian-fila-revisao/` e o original sai do inbox só depois da cópia. O timer `agata-vault-inbox` está parado pelo Humano desde 22/10. Medido: autoteste do importador 15/15 OK na worktree.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(803) DIÁRIO — 22/10/2026 · **Sanitizador amplia para dados pessoais e nomes de projeto; cascata seth-livre volta COM hidratação (decisão do Humano).**

Assinado pelo Humano (`APROVADO-sanitizador-cascata-20261022`, `p8_verificar` = PODE APLICAR), PR 450. Decisão do Humano, com o risco declarado: o contexto da hidratação, inclusive a janela de memória, pode sair da Máquina pela rota `seth-livre`. A proteção por padrão é: segredo, e-mail, CPF, CNPJ, telefone e nomes da lista privada (`~/.config/agata/nomes-projeto.txt`, quando existir; sem ela vale só a régua de padrões). A revisão do Codex (22/10, 09:54 e 10:17) está registrada no PR e na V9 (seção 27); o Humano decidiu seguir. Pendente, não bloqueia: conflito de governança do `vault_importar_inbox.py` (POST /memoria sem autorização) e CodeQL fora da branch protection.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(802) DIÁRIO — 22/10/2026 · **Teto do PROJETO.md: parágrafo do escriba movido para extras, sem perda.**

Assinado pelo Humano (`APROVADO-teto-projeto-detalhe-20261020`, `p8_verificar` = PODE APLICAR). O parágrafo de segurança do escriba (1.101 bytes) foi movido, byte a byte, para `extras/projeto-detalhe/servicos-e-interface.md`; o PROJETO.md ficou com um ponteiro. Revisão cruzada do Codex no canal (22/10, 09:02): OK; conferida pelo Claude na mesma data. Efeito: PROJETO.md fica abaixo do teto de 48.000 bytes. Reversível por `git revert` do merge.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(801) DIÁRIO — 21/10/2026 · **Pacote F1+F2 aplicado junto com a correção P-16 (P-24 e P-26 em SEM_TESTE).**

Assinados pelo Humano: `APROVADO-pacote-f1-f2-20261021` e `APROVADO-pacote-f1-f2-testes-20261021` (PR 444, mesclado). A primeira tentativa de aplicar só o pacote foi barrada pelo P-16: P-24 e P-26 emitem só AVISO e não tinham caso nem justificativa em `scripts/testar_perimetro.sh`. Medidos isolados em 21/10/2026: MEMÓRIAS.md com 1.242.050 caracteres contra orçamento de 25.000; 11 chunks frios sem tag. Governança apenas: não altera hidratação, leitura de modelos nem serviços. Reversível por `git revert` do merge.

Modelo: Claude Haiku 5.5 (Claude Code, na Máquina).

(800) DIÁRIO — 21/10/2026 · **A aplicação só junta com CodeQL verde, além de fiscal-p8 e suite-adversarial.** Assinada pelo Humano (aplicar-exige-codeql-20261021). CodeQL em skipping também bloqueia (escolha rígida).
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: p8_verificar = PODE APLICAR · Autorização: Humano — assinatura de aplicar-exige-codeql-20261021; "ok"

(799) DIÁRIO — 21/10/2026 · **Auditoria do escriba deixa de imprimir o padrão de segredo (alerta CodeQL alto).** Assinada pelo Humano (auditoria-escriba-sem-vazamento-20261021). Registra só arquivo e contagem.
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: p8_verificar = PODE APLICAR · Autorização: Humano — assinatura de auditoria-escriba-sem-vazamento-20261021; "ok"

(798) DIÁRIO — 21/10/2026 · **Auditoria rígida do escriba ativa (somente leitura): remoções só com exceção aprovada a partir do marco, numeração, segredo, registro por PR e cópia igual ao origin.** Assinada pelo Humano (auditoria-escriba-rigida-20261021). Dívida histórica (6 commits anteriores) reportada e não conta.
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: p8_verificar = PODE APLICAR; caso limpo passou · Autorização: Humano — assinatura de auditoria-escriba-rigida-20261021; "assinado e autorizado"

(797) DIÁRIO — 21/10/2026 · **Escriba passa a poder levar entradas ao histórico por PR de registro (branch próprio), desligado por padrão (SETH_ESCRIBA_GIT=1 liga).** Assinado pelo Humano (escriba-commit-registro-20261021). A gravação local é mantida se o registro falhar. Ativar exige a variável no unit, em proposta à parte.
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: p8_verificar = PODE APLICAR · Autorização: Humano — assinatura de escriba-commit-registro-20261021; "pode"

(796) DIÁRIO — 21/10/2026 · **Comandos padrão da skill agata-fluxo (§8) aplicados: atualizar a checkout guardando alterações antes, e assinar proposta.** Assinado pelo Humano (skill-agata-fluxo-comandos-20261021). Todo modelo passa a entregar esses comandos no mesmo formato.
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: p8_verificar = PODE APLICAR · Autorização: Humano — assinatura de skill-agata-fluxo-comandos-20261021

(795) DIÁRIO — 21/10/2026 · **Início de sessão da dupla mecanizado: scripts/dupla/inicio.sh, uma leitura do canal, saída vazia sem novidade.** Assinado pelo Humano (inicio-dupla-20261021). Substitui a leitura manual do canal no começo de cada sessão, para economia de tokens.
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: p8_verificar = PODE APLICAR; aplicação pelo fluxo padrão · Autorização: Humano — assinatura de inicio-dupla-20261021

(794) DIÁRIO — 21/10/2026 · **Skill agata-fluxo aplicada (universal, para qualquer LLM e para a Seth).** Assinada pelo Humano (skill-agata-fluxo-20261021). Substitui a divisão ad hoc entre Claude e Codex por um fluxo único: medir, canal, divisão de execução e auditoria, mudança protegida só por proposta, afirmar com prova.
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: p8_verificar = PODE APLICAR; aplicação pelo fluxo padrão · Autorização: Humano — assinatura de skill-agata-fluxo-20261021

(793) DIÁRIO — 21/10/2026 · **Auditoria de turno passa a incluir o detector de estado sem prova (aplicado após assinatura do Humano).** Acrescenta uma linha em `_conteudo` que importa `detector_estado_sem_prova` e soma os achados (estado sem prova, confiança numérica, componente removido no presente). Selftest da auditoria e 6 casos do detector passam.
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: p8_verificar = PODE APLICAR; `auditoria_turno.py --selftest` = SELFTEST OK · Autorização: Humano — assinatura de ligar-detector-auditoria-20261021

(792) DIÁRIO — 21/10/2026 · **Detector de estado sem prova aplicado (M1-M4): achados de afirmação sem prova, confiança numérica e componente removido citado no presente.** Assinado pelo Humano (detector-estado-sem-prova-20261021). Sem modelo: regex, 6 casos fixos derivados da conversa auditada (scripts/testar_detector_estado.py).
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: p8_verificar = PODE APLICAR; testes do detector 6/6 · Autorização: Humano — assinatura de detector-estado-sem-prova-20261021; "pode"

(791) DIÁRIO — 21/10/2026 · **Regra M7: conversa com a Seth é matéria-prima não verificada; só entra como base de regra o que tiver PR, commit ou medição anexada.** Ditado do Humano (21/10/2026), a partir da auditoria do export de conversa. Origem: 176 afirmações de "endereçado/fechado" e 139 de "confirmado" no export, sem prova ao lado; "5 de 7 riscos endereçados" era falso (medido: nenhum risco fechado por completo).
Aplicação: o relatório de achados (somente leitura, fora do repositório) e o detector de estado sem prova (proposta PR 420, sem assinatura) são as fontes de regra; a conversa não.
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: contagem literal do export (grep) e relatório de achados de 523 registros · Autorização: Humano — "autorizo suas propostas"

(790) DIÁRIO — 21/10/2026 · **Regra: o harness da Seth aprende com os registros, sem treinar pesos. Toda lição entra no canon só com aprovação humana e medição num conjunto fixo de casos.** Ditado do Humano em 20/10/2026 (fim do dia). Desenho completo em `~/Área de trabalho/HARNESS-SETH-aprendizado-sem-treino.md`.
Regras que valem daqui em diante: (a) matéria-prima = auditoria de turno, memórias quente/morna/fria, decisões do Humano e FALHAS.md; (b) a evidência bruta nunca é sobrescrita, a lição fica ao lado dela; (c) lição só entra se não piorar o conjunto de casos; (d) um erro isolado vira nota, só padrão repetido vira regra; (e) toda sessão recebe ficha de contexto gerada pelo sistema (onde, para quê, quando, com quê), igual para todos os modelos; (f) nenhum dado pessoal ou segredo entra na matéria-prima.
Fases: F1 relatório diário de achados (só leitura); F2 rascunhos de lição fora do canon; F3 ficha de contexto injetada (proposta de código, P-8); F4 gate de avaliação (proposta de código, P-8).
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: ditado do Humano em 20/10/2026; pesquisa: 3 fontes de 2026 listadas no desenho · Autorização: Humano — "vira regra… canonize"

(789) DIÁRIO — 21/10/2026 · **Ritmo de trabalho e substituição: só o Humano decide quando parar; o modelo que não se julgar apto pede substituição.** Ditado pelo Humano em 20/10/2026, ao final do dia: a sessão segue até o fim do dia por ordem do Humano, não por contagem de tarefas. Se o modelo não se julgar apto a continuar (erro de medição recorrente, afirmação sem prova, perda de contexto), ele diz isso e pede substituição, em vez de seguir com risco.
Motivo: em 20/10 houve afirmações não medidas em mais de um modelo (cabeçalho de identidade trocado, contagem refeita sem conferir, achado de auditoria dado como atual sem medir). O custo de errar em auditoria externa é maior que o de parar.
Como aplicar: antes de cada afirmação de estado, medir com a ferramenta do caso (comando, arquivo, PR). Sem medição, dizer "não medido". Ao identificar erro próprio, registrar em entrada nova, sem editar a anterior.
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: ditado do Humano em 20/10/2026 (fim do dia) · Autorização: Humano — "até o final do dia… só o humano decide quando é hora de parar… canonize isso"

(788) DIÁRIO — 20/10/2026 · **Auditoria das ocorrências de numeração repetida: 427, 514 e 599 são referências no texto; o grupo real 729 já foi desambiguado em (730).**

Vetor: `grep -nE '^\([0-9]+\) '` com nome do arquivo (`grep -nH -E`) em `MEMÓRIAS.md`, `MEMORIAS-MORNO.md` e `memoria/frio/MEMORIAS-FRIO-*.md`; conferência adicional dos cabeçalhos formais `^\([0-9]+\) \S+ — ` em todas essas camadas, no HEAD `a96fb7b`. Os números (427), (514) e (599) aparecem duas vezes no grep literal, sempre em `MEMÓRIAS.md`: uma ocorrência é uma referência numa correção posterior (linhas 4841, 3684 e 2430, respectivamente), e a outra é a única entrada formal correspondente (linhas 4847, 3696 e 2482). Não se renumeram nem se editam essas entradas. O número (729), sim, identifica 14 cabeçalhos formais em `MEMÓRIAS.md` (linhas 218 a 296, de seis em seis); a entrada (730) já atribuiu os identificadores de citação (729a) a (729n), do mais antigo ao mais novo, e enumera os títulos. As camadas morna e fria não acrescentam outro grupo formal repetido.

Numeração futura medida: os PRs 409 e 411, ainda abertos nesta auditoria, trazem respectivamente (786) e (787); este registro recebe (788), e o próximo número livre após ele é (789), preservadas essas duas entradas pendentes. Nenhuma entrada histórica foi alterada.

Modelo: GPT-6 · vetor: `grep` literal e agrupamento independente dos cabeçalhos formais nas camadas de memória, mais conferência dos PRs 409 e 411 · autorização: pedido do Humano, 20/10/2026.

(787) DIÁRIO — 20/10/2026 · **A proposta `voz-allowed-addresses-20261020` restringe os destinos de TTS do LibreChat ao serviço Piper autorizado.** A aplicação move o par assinado para `propostas/aplicadas/` e registra a mudança neste commit.
Modelo: GPT-6 (Codex, na Máquina) · vetor: P-8 confirmou assinatura e hash do diff; CI do PR de aplicação será verificado antes do merge · Autorização: Humano — assinatura P-8 e ordem para aplicar em 20/10/2026


(786) DIÁRIO — 20/10/2026 · **Aplicada a condição de janela de manutenção** (`manutencao-fora-da-janela-20261020`). Fonte versionada alterada e par assinado consumido no PR de aplicação; a unidade de runtime será verificada depois do merge.
Modelo: GPT-6 (Codex) · vetor: P-8 `PODE APLICAR`; `suite-adversarial` após atualizar a branch · Autorização: Humano — tarefa assinada de 20/10/2026


(785) DIÁRIO — 20/10/2026 · **Controles verificáveis de autorização e execução externa aplicados (`auditoria-seguranca-reducoes-verificaveis-20261020`).** O pacote endurece a capability por chamada, autentica os executores e restringe escrita do Escriba e dados externos/egress. Suíte offline: 58/58; perímetro: 19 OK, 2 SKIP, 2 PARCIAL, 0 FALHA. A eficácia no runtime ainda depende de homologação controlada com privilégios; P-4 permanece parcial sem root.
Modelo: GPT-6.1-sol (Codex, na Máquina) · vetor: suíte offline e perímetro em checkout descartável; `p8_verificar.sh` confirmou assinatura, hash e aplicabilidade · Autorização: Humano — "feito" (assinatura de auditoria-seguranca-reducoes-verificaveis-20261020)

(784) DIÁRIO — 20/10/2026 · **Autostart NVIDIA corrigido e testado com o `XAUTHORITY` dinâmico da sessão.** A unidade agora preserva `DISPLAY` e `XAUTHORITY` em `sudo`; a execução real terminou com `Result=success`, e `nvidia-settings` confirmou offsets `250`/`1750`. Reversão local: restaurar `~/.config/autostart/apply-nvidia-oc.desktop.codex-bak-20261020` e zerar os offsets.
Modelo: GPT-6 (Codex, na Máquina) · vetor: `systemctl --user restart` + journal da unidade + consulta de offsets · Autorização: Humano — "Audite e resolva", "Aceito esse alcance", "Aceito essa detecção e esses limites"; comando privilegiado executado pelo Humano.

(783) DIÁRIO — 20/10/2026 · **Correção de numeração em (782): as entradas dos dois itens são (780) = AC-09 (consolidação) e (781) = AC-18 (retirada no PROJETO). (777) é o P-4 com sudo; (778) e (779) são da auditoria do Codex.** Medido em `grep -nE '^\((77[5-9]|78[0-2])\) ' MEMÓRIAS.md`. Não edito (782) (append-only).
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: `grep` de MEMÓRIAS.md, linhas 43-64 · Autorização: Humano — "faça"

(782) DIÁRIO — 20/10/2026 · **Correção de (777)/(778): o AC-18 aplicado não reduziu o PROJETO. Ele só adicionou um aviso.** O diff assinado (`projeto-retirada-20261018`, aplicado em `2a371ca`) mudou `scripts/perimetro.sh` e acrescentou `PROJETO_FOLGA_BYTES` (padrão 500): o aviso sai quando o PROJETO cresce em relação ao HEAD e fica a menos de 500 bytes do teto. Não tirou nenhum texto do PROJETO. Medido agora: `PROJETO.md` = 47.703 bytes, folga de 297 bytes. A retirada real de conteúdo para `extras/projeto-detalhe/` continua por fazer, e precisa de proposta assinada com a escolha do que sai. As entradas (777)/(778) descreveram a política como feita; esta entrada corrige isso. Não edito o texto delas (append-only).
Modelo: Claude Haiku 5.5 (Claude Code, na Máquina) · vetor: `git show 2a371ca^2 --stat` e leitura do `.diff` aplicado (sem `+` de retirada de texto); `wc -c PROJETO.md` = 47703 · Autorização: Humano — "faça"

