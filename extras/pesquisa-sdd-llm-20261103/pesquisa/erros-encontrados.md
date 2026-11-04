# Erros encontrados no caminho (03/11/2026)

Autor: Claude Sonnet 5.5 (Claude Code). Levantado ao longo da sessão de 03/11/2026 (13:47 a 16:37, medido com `date`). Cada item diz como foi verificado e o estado. Rascunho para o Humano; nada aqui é canônico.

Estados: **corrigido** (com PR), **tratado** (ação local, sem PR), **aberto** (nada feito), **estrutural** (por desenho).

## A. Defeitos e riscos do sistema

| # | Erro | Como foi visto | Estado |
|---|---|---|---|
| 1 | O selftest do `seth_gateway` estourava o timeout de 10 s na CI: o primeiro pedido espera o `estado_para_eco.sh`, que faz `git ls-remote` com timeout de 8 s. Falhou 3 vezes e passou na 4ª no PR #824 | Log da CI; reproduzido localmente com remoto bloqueado (11,4 s) | **corrigido** no PR #826 (4,4 s com remoto bloqueado). Estabilidade em várias execuções: não medida |
| 2 | `test_complete_requires_gates_and_records_completion` (sdd_flow) falha onde `pytest` não está no PATH, porque o runner usa `--pytest-bin pytest` por padrão | Rodei os testes com o Python do sistema e falhou 1 de 24; com o PATH ajustado, 24 de 24 | **aberto** |
| 3 | `scripts/testar_trava_escriba.py` falha com o Python do sistema: falta o módulo `cryptography`, que ninguém declara; passa com o Python do venv do MCP | Bateria offline: 27 de 28 | **aberto** |
| 4 | P-10 (vault derivado) FALHOU no início da sessão e passou depois do `git pull`. A causa provável é o checkout atrasado, mas não confirmei | Perímetro às 13:47 e às 16:30 | **resolvido por sincronizar**; causa não confirmada |
| 5 | `sync: FALHA` no início: HEAD local 4 commits atrás do remoto | Hook de início de sessão | **corrigido** com `git pull --ff-only` |
| 6 | O `seth_gateway` lista como "assinadas, falta aplicar" qualquer `.diff` com `APROVADO-` e não lê `propostas/SUBSTITUIDAS.txt`; uma proposta substituída pode aparecer como pendente para a Seth | Leitura de `redesign/router/seth_gateway.py` (função `_linha_propostas`) | **aberto** |
| 7 | 5 alertas de segurança do CodeQL abertos na `main`: `py/path-injection` em `redesign/obsidian/ro_proxy.py` (4) e `py/command-line-injection` em `redesign/router/seth_verificador.py:374` | `gh api` de alertas de code scanning | **aberto** (não são desta sessão) |
| 8 | P-24: `MEMÓRIAS.md` com 130.216 caracteres contra orçamento de 25.000; a escalada para FALHA ainda não existe | Perímetro | **aberto** |
| 9 | P-17: o controle P-16 está em SKIP há 470 corridas seguidas, ou seja, na prática desligado | Perímetro | **aberto** |
| 10 | P-9: 13 unidades e portas declaradas aparecem inativas, porque o sistema agora sobe sob demanda (decisão de 29/10). O aviso vira ruído permanente e esconde o que cair de verdade | Perímetro e `/api/lacunas` | **aberto** (decisão de 29/10 contra o P-9) |
| 11 | Sessão conjunta da Equipe parada na base `6fc87db` desde 28/10, com Codex "presente" desde então, e `DERIVA` em relação ao `origin/main` | `equipe.py status` | **tratado**: Codex marcado ausente; a sessão em si continua |
| 12 | `INDICE.md` de skills diz que as cópias de terceiros estão em `.agents/skills` e `.claude/skills`, mas 5 delas estão fora do git (`.git/info/exclude`); um clone limpo e a CI veem 13 skills e não 18 | `git ls-files` contra `ls` | **aberto** (inconsistência de documentação) |
| 13 | `design-taste-frontend`: corpo com 528 linhas, acima da recomendação de 500 | `qualidade_llm.py` | **aberto** (cópia de terceiros, fixa) |
| 14 | P-15: nenhuma família do roster remoto do Conselho com sucesso nas últimas 24 h | Perímetro | **aviso**, pode ser só falta de uso |
| 15 | P-4 PARCIAL: sem privilégio de administrador não enxergo todos os processos | Perímetro | **estrutural** |
| 16 | Servidor MCP `agata-navegador` com ECONNREFUSED no início da sessão | Aviso da ferramenta | **por desenho** (serviço sob demanda parado) |
| 17 | 140 worktrees registrados, 166 branches locais `proposta/*` e `aplica/*` e 583 branches remotos; a maioria vem do Codex e de sessões anteriores | `git worktree list`, `git branch` | **aberto** (removi só o que criei) |
| 18 | O CodeQL só roda de verdade no PR de aplicação: o PR da proposta só tem o `.diff`. Um alerta só aparece depois da assinatura | PR #830 | **aberto** (processo) |
| 19 | `ONDE_ESTAMOS.md` desatualizado: última entrada de 29/10 | Leitura do arquivo | **aberto** |

## B. Erros meus nesta sessão

| # | Erro | Estado |
|---|---|---|
| 20 | Escrevi num arquivo a hora "15:58" sem medir; a medida era 15:54 | **corrigido** (agora "15:55, medido com `date`") |
| 21 | Usei um regex sobre HTML no meu teste `test_qualidade_llm.py`; o CodeQL acusou `py/bad-tag-filter` e bloqueou o PR #830. Custou uma assinatura a mais e um PR fechado sem merge | **corrigido** na v2 (`HTMLParser`) |
| 22 | Relatei a primeira rodada de testes do `sdd_flow` como "1 falhou" antes de separar que a causa era o PATH do meu shell | **corrigido** na mesma resposta seguinte |
| 23 | Duas buscas minhas com glob sem aspas e um alias do zsh falharam, e uma busca vinda de bibliotecas de terceiros (`.venv`) poluiu o resultado | **corrigido** (busca refeita excluindo `.venv`) |
| 24 | No mapa, "18 skills" não distinguia as versionadas (13) das cópias locais | **corrigido** na cópia da skill; a cópia solta nesta pasta ainda traz a frase antiga |
| 25 | Chamei de "flaky" a falha da CI antes de ter prova; a causa exata na CI não foi medida | **hipótese** apenas |

## C. Divergências entre fontes (do vídeo e dos blogs)

| # | Divergência | Verificação |
|---|---|---|
| 26 | A colagem da transcrição perdeu os valores com `$` (tarifas e o preço final) | Descrição do vídeo confirmou R$ 1 e R$ 28,82/mês; tarifas vieram da documentação oficial |
| 27 | Blogs davam esforço padrão `high` para o Opus 5.5; a documentação oficial diz `medium` | Página de effort (N1) |
| 28 | O "cerca de 100 tokens por skill" do vídeo não consta nas fontes primárias lidas | Post da Anthropic de 16/10/2025 e documentação de skills |
| 29 | Paper da OpenAI: o resumo diz penalidade 2 para t = 0,75; a fórmula da seção 4.2 dá 3 | Relatório de leitura; usei a fórmula |
| 30 | Paper de RL calibrado (arXiv 2512.19920): o resumo afirma desempenho comparável a modelos de fronteira, mas as tabelas, segundo o relatório, mostram pior calibração que dois deles | Relatório de leitura; tratado como indício |
| 31 | A página da OpenAI sobre o paper respondeu 403 | Não lida; o artigo foi lido no arXiv |
| 32 | A Anthropic diz que raciocínio é limitado por `max_tokens` junto da resposta, mas não diz que é cobrado como saída | Inferência marcada como tal |

---

# Atualização de 03/11/2026, 19:00 (medido com `date`)

Esta seção só acrescenta; a lista acima fica como foi escrita. Primeiro, o que mudou de estado.

## Mudanças de estado

| # | Item | Novo estado |
|---|---|---|
| 6 | O gateway não lia `SUBSTITUIDAS.txt` | **corrigido** (PR #837, selftest novo) |
| 9 | P-17: P-16 em SKIP "crônico" | **corrigido** (PR #841): o SKIP de "não se aplica" passa a ser isento |
| 10 | P-9: 13 avisos permanentes com o sistema sob demanda | **corrigido** (PR #841): com `agata.target` e `seth-gateway` inativos vira uma linha; `failed`, timers, subida parcial e target ativo continuam avisando. Conferido no perímetro real |
| 1 a 3, 7, 12 | Selftest do gateway, `pytest` fora do PATH, `cryptography`, 5 alertas do CodeQL e índice de skills | **proposta pronta, aguardando assinatura** (`agata-robustez-codeql-medicoes-20261103`); o resultado do CodeQL só aparece depois, no PR de aplicação |
| 17 | Worktrees e branches | **parcial**: 87 worktrees e 164 branches locais removidos; 512 branches remotos aguardam você; 12 não mesclados aguardam decisão |
| 11 | Equipe com Codex "presente" | **tratado** e mantido: Codex ausente, vigia fora do atalho `seth` |

## Erros novos, achados depois da primeira lista

| # | Erro | Como foi visto | Estado |
|---|---|---|---|
| 33 | O selftest do `redesign/obsidian/ro_proxy.py` dá `SELFTEST FALHA` até na `main`: ele espera o plugin do Obsidian no ar (`GET /` deveria dar 200 e dá 403 "upstream inacessível"). Não é autocontido | Rodei antes e depois da minha mudança, via `git stash`; as checagens de caminho (`GET lista nova`, `../`) dão o mesmo resultado nas duas versões | **aberto** |
| 34 | Mudar código protegido não deixa testar o CodeQL antes da assinatura: o hook P-8 bloqueou o commit de teste, como deve. Minha tentativa deixou um branch remoto vazio, `precheck/codeql-lote4-20261103`, que apaguei | Saída do hook; `git push :branch` | **tratado**; a limitação do processo segue (item 18) |
| 35 | A exclusão em lote de branches remotos foi negada pelo classificador de permissão (escopo não verificável). Antes disso, meu laço em zsh falhou 13 vezes por não separar os argumentos, e um branch já mesclado (`aplica/abrir-janela-existente-20261030`) foi apagado no teste de diagnóstico | Mensagem de negação; contagem de remotos 525 | **aberto**; a lista está nesta pasta |
| 36 | P-9, minha primeira versão: eu definia "sistema desligado" por nenhum serviço de usuário no ar, e isso falhou na prática porque o `seth-escriba` fica sempre ligado, então o aviso continuou | Rodei o perímetro real antes de entregar a proposta | **corrigido** antes da assinatura (o critério passou a ser o `seth-gateway`) |
| 37 | Na primeira medição de contexto o modelo deu 0 de 3 em todos os comprimentos: o limite de saída de 48 tokens cortava a resposta, porque o `qwen3:4b` raciocina no próprio texto e o `think:false` é ignorado. Erro meu de desenho | Depurei a resposta crua; subi para 400 e repeti | **corrigido** |
| 38 | Na cadeia de aplicação, a falta do arquivo de assinatura interrompeu o comando no meio: o diff foi aplicado mas o par não foi movido. Aconteceu hoje com `agata-robustez-codeql-medicoes-20261103`, que não está assinada | Erro de `cp` e de `mv` | **tratado**: descartei a worktree sem commitar; falta a sua assinatura |
| 39 | A busca por sentido acha pouco quando a consulta são palavras raras: recall@1 10% e recall@10 22,5%, contra 70% e 100% da busca por texto. Não é defeito comprovado, porque esse tipo de consulta favorece a busca léxica; paráfrase continua não medida | `medir_recuperacao.py --semantico` | **observação** |
| 40 | O P-17 acusa o P-10 em SKIP em qualquer worktree sem o vault derivado (`memoria/obsidian/`), o que confunde medição feita fora do checkout oficial | Perímetro na worktree de teste | **observação** |
| 41 | A cada commit que muda o canon, um hook envia o índice ao Drive ("índice exportado e enviado ao Drive"). É envio automático para fora da Máquina | Saída do `post-commit` | **observação** para você confirmar que é intencional |
| 42 | O Codex deixou alterações não commitadas em `.agents/skills/agata-relay-provedores`, e 53 worktrees dele ou de sessões antigas seguem registradas (alteração solta ou commit não mesclado) | `git status`, `git worktree list` | **aberto**; não toquei |

---

# Atualização de 03/11/2026, 19:15 (medido com `date`)

## Erros novos

| # | Erro | Como foi visto | Estado |
|---|---|---|---|
| 43 | Meu selftest do medidor de contexto montava um regex com dado do pedido no servidor falso, e o CodeQL acusou `py/regex-injection` (alerta 16) no PR de aplicação #842. Erro meu, o segundo do mesmo tipo hoje (o primeiro foi o regex sobre HTML, item 21). Custou uma segunda assinatura da mesma proposta | CodeQL do PR #842; `gh api` de alertas do PR | **corrigido** na v2 (`agata-robustez-codeql-medicoes-v2-20261103`), com busca literal no lugar do regex dinâmico |
| 44 | O CodeQL só avisa no PR de aplicação, depois da assinatura (item 18). Aconteceu duas vezes hoje: PR #830 e PR #842 | PRs fechados sem merge | **aberto** (processo): vale uma checagem de padrões de risco (regex montado com variável, caminho vindo de pedido) no meu próprio desenho antes de gerar o diff |

## Boa notícia medida

Os 5 alertas antigos (`path-injection` do `ro_proxy.py` e `command-line-injection` do `seth_verificador.py`) **não aparecem** na lista de alertas do PR #842. Só aparece o alerta novo 16. Isso indica que os guardas funcionaram, mas a confirmação final é o merge e o novo escaneamento da `main`.

## Estado das propostas ao fim desta rodada

- Aplicadas: `agata-perimetro-sob-demanda-20261103` (PR #841).
- Substituída, sem merge: `agata-robustez-codeql-medicoes-20261103` (PR #842 fechado).
- Aguardando assinatura: `agata-robustez-codeql-medicoes-v2-20261103`.

---

# Atualização de 03/11/2026, 19:52 (medido com `date`)

## Mudanças de estado

| # | Item | Novo estado |
|---|---|---|
| 1 a 3, 12 | Selftest do gateway, `pytest` fora do PATH, `cryptography`, índice de skills | **corrigidos** (robustez v2, PR 845) |
| 7 | 5 alertas do CodeQL | **3 fecharam** na `main` (1, 3 e 4); **seguem abertos o 2 e o novo 17** (`path-injection` do `ro_proxy.py`, em `os.path.isdir` e `os.listdir`) e o **5** (`command-line-injection` do `seth_verificador.py`) |
| 43 | Regex dinâmico no selftest do medidor | **corrigido** na v2 |

## Erros novos

| # | Erro | Como foi visto | Estado |
|---|---|---|---|
| 45 | Duas propostas assinadas (voz e robustez) **conflitavam no contexto do `INDICE.md` de skills**: cada uma mexia numa região a menos de 3 linhas da outra, e `git apply` recusa a segunda. Não dá para aplicar em sequência nem em ordem inversa. Custou refazer a voz (mais uma assinatura) | `git apply --check` nas duas ordens | **corrigido**: robustez aplicada primeiro, voz refeita em cima. Lição: propostas do mesmo dia que tocam o mesmo arquivo devem ir no mesmo lote |
| 46 | O `scripts/equipe/aplicar.py` não foi usado nesta aplicação: você interrompeu a tentativa (eu a lançara com `nohup` em segundo plano), então apliquei à mão. A entrada de MEMÓRIAS segue pendente e vem com a voz v2 | Interrupção da ferramenta | **aberto** até a assinatura da voz v2 |
| 47 | O hook reescreve as âncoras de SHA de `REGRAS`, `PROJETO`, `PROMPT_CARREGAMENTO` e `MEMÓRIAS` em **todo commit**; qualquer PR de proposta fica com conflito assim que a `main` anda. Aconteceu com o PR 847, refeito como 848 | `gh pr merge`: "has merge conflicts" | **aberto** (processo): é o motivo de o `aplicar.py` refazer branches |
| 48 | Erro meu no desenho do diff do `ro_proxy`: um `replace` pegou duas linhas parecidas do `sdd.yml` e acrescentou `redesign/obsidian` na linha da âncora, que quebraria a CI (o obsidian não tem spec). Achei antes de qualquer merge | Reli o diff; regenerei | **corrigido** |
| 49 | Depois do merge do PR da proposta do `ro_proxy` falhar por conflito, limpei a worktree e a branch local antes de conferir o resultado do `merge`. A branch remota salvou o trabalho, mas foi descuido meu | Mensagem "merge conflicts" | **corrigido**; passo passa a conferir o `merge` antes de limpar |
| 50 | O alerta 5 do CodeQL (`command-line-injection`, `seth_verificador.py`) **não fecha só com código**: o texto livre da consulta tem de ir como argumento dos comandos. Os guardas de lista, tamanho e `--` já existem | Alerta continuou aberto depois do PR 845 | **aguarda sua decisão**: dispensar com justificativa ou mudar a interface dos comandos |

## Estado das propostas (aguardando assinatura)

- `agata-voz-do-sistema-v2-20261103` (PR 846 mergeado): skill de voz, `scripts/agata_falar.py`, regra no `AGENTS.md` e entrada de MEMÓRIAS.
- `agata-ro-proxy-guarda-20261103` (PR 848 mergeado): fecha os 2 alertas de `path-injection` do `ro_proxy.py`.

---

# Atualização de 03/11/2026, 22:40 (medido com `date`)

## Mudanças de estado

| # | Item | Novo estado |
|---|---|---|
| 7 | Alertas do CodeQL | **4 dos 5 fecharam** e o alerta novo (17) também: restam **1 aberto**, o 5 (`command-line-injection` em `seth_verificador.py`). Os dois `path-injection` do `ro_proxy.py` fecharam com o PR 851 (conferido em `gh api`, 100 s depois do merge) |
| 45 | Conflito de contexto entre as propostas da voz e do `ro_proxy` | **resolvido** (voz PR 849, ro_proxy refeito PR 851) |
| 46 | Entrada de MEMÓRIAS dos lotes do dia | **registrada** (entrada 932, com a voz) |

## Erro novo

| # | Erro | Estado |
|---|---|---|
| 51 | A assinatura do `ro_proxy v2` ficou faltando duas vezes: o `aprovar.sh` não gravou o arquivo na primeira tentativa (21:26) e só existiu na segunda. A causa não foi medida; o mesmo aconteceu com a robustez. Não sei se é a frase-senha digitada errada ou o comando interrompido | **aberto**: se voltar a acontecer, vale ver a mensagem de erro do `aprovar.sh` |

## Estado final

- Aplicado hoje e confirmado na `main`: ciclo SDD, skill de fundamentos de LLM, SDD no painel, menu em submenus, medições, perímetro sob demanda, robustez, voz do sistema e `ro_proxy`.
- Aguardando você: decisão do alerta 5, os 512 branches remotos e os 12 não mesclados.

---

# Atualização de 04/11/2026, 08:36

| # | Erro | Estado |
|---|---|---|
| 52 | Ao conferir a entrega ao Codex, rodei `equipe.py ler --agente codex`, que moveu o marcador de leitura dele para o fim do canal: ele não veria o meu alinhamento | **corrigido** (marcador restaurado para o início da minha mensagem) |
| 53 | Tentei mover para `propostas/aplicadas/` um par assinado cujo conteúdo já estava na `main` por outro caminho. O `fiscal-p8` recusou: só aceita consumir par quando o diff aplica sobre a base | **corrigido** (o par ficou em `propostas/` e foi marcado em `SUBSTITUIDAS.txt`) |
| 54 | O classificador de permissão negou duas vezes a exclusão em lote de branches remotos, e uma vez a remoção forçada de worktrees com alteração solta | **aberto**: as listas e os comandos estão nesta pasta; o estado delas foi arquivado antes |
| 55 | O aviso "propostas abertas: 4" do Codex me lembrou que eu havia dito "nenhuma pendente de assinatura" sem contar a proposta semanal de memória | **corrigido** na resposta; ver `oportunidades-em-aberto.md` |
