# Pacote mecânico 12/11: a verificação passa a valer para todo modelo (`pacote-mecanico-12-11`)

Proposta P-8 de `pacote-mecanico-12-11`. Diff: `propostas/pacote-mecanico-12-11.diff` (31 arquivos: 20 alterados e 11 novos; sha256 `d9345d130bdc113105b91e9b7aef4fcbac0f61d70fe58b7c39eb5f0840a7b533`). Base: `origin/main` `04bfe2e4` (já tem o PR #976, com pacote-12-11 e chat-voz-11-11 aplicados). Executado por Claude Haiku 5.5, agente de proposta, a pedido do coordenador, a partir das decisões do Humano de 12/11/2026. Assinatura do Humano, uma vez, depois do merge deste PR de proposta.

Classe (P4): Comportamento e canon. Canon: `AGENTS.md`, `REGRAS.md`, `PROTOCOLOS.md`, `PROMPT_CARREGAMENTO.md` e a skill `agata-fluxo-equipe`. Comportamento: `.claude/settings.json`, `.claude/agents/*.md`, `scripts/*`, `redesign/router/*`, `config/cli/*`, `.github/workflows/sdd.yml`. Spec: `redesign/router/spec/` (52 critérios; 27 deles são deste pacote).

## Em uma frase

O que o Agata desenvolve passa a valer para todo modelo do Conselho por mecanismo da Máquina: contador de turno, aviso de fim de turno sem bloqueio, negação de leitura do `.env`, pontos de entrada que apontam para o mesmo `AGENTS.md`, e subagentes com modelo barato e pacote mínimo.

## Em resumo (para o Humano)

- Junta quatro partes em uma assinatura: turno mecânico (proposta que estava em outro worktree, sem PR, absorvida inteira aqui); aviso de fim de turno que só avisa; negação de leitura de `~/.config/agata/.env`; subagentes com modelo barato, limite de turnos e pacote mínimo.
- Cada CLI lê `AGENTS.md`: Claude Code por `@AGENTS.md` em `CLAUDE.md`; Gemini CLI por `@AGENTS.md` em `GEMINI.md`; Codex e OpenCode pelo próprio nome; Seth pela hidratação compacta do gateway, que agora inclui o arquivo. Nenhuma cópia nova: os dois ponteiros têm no máximo 500 bytes, e o verificador falha se um virar cópia ou se perder o import.
- `scripts/conselho_mecanismos.py --verificar` mostra, por modelo, o que é mecânico e o que é disciplina, e sai 1 se algum ponteiro se perder.
- Medido nesta Máquina: CI local com `CI LOCAL: TUDO OK` (40 passos); 41 testes do turno; 28 testes dos mecanismos; 52 de 52 critérios da spec do roteador passam; gate de spec sem falha; lint de skills sem problema; verificador com 0 falha.
- Não medido (lista adiante): o disparo real dos ganchos numa sessão aberta; Codex, Gemini CLI e OpenCode rodando o pacote (só a doc pública foi lida, e nenhum binário foi executado); a run no GitHub no headSha.
- Assinar, depois do merge: `bash scripts/aprovar.sh pacote-mecanico-12-11 "<motivo>"`.

## Decisões do Humano que este pacote cumpre

Relatadas pelo coordenador, que as tirou do cache do Conselho; o agente não leu o cache (fica fora do repositório):

1. Turno é a resposta que devolve o controle ao Humano; chamadas de ferramenta e subagentes não contam. Contador mecânico na Máquina, por sessão. Subagente herda o turno do pai (`t=<n>.sub`). Divergência entre cabeçalho e contador só avisa (entrevista P1, 12/11/2026 09:15).
2. Diretriz de 12/11 (entrada 518 do cache): o que o Agata desenvolve vale para todos os modelos do Conselho de forma mecânica, por mecanismo da Máquina, não por instrução.
3. Decisão de 12/11, 09:40 (a última): (A) todo modelo de LLM do Agata tem acesso ao sistema e age segundo ele e segundo o que já foi decidido; (B) agentes e subagentes recebem só o necessário para a tarefa (pacote mínimo), não o contexto completo.
4. Fim de turno: a Máquina confere a resposta e só avisa, sem bloquear.
5. Negação de leitura de `~/.config/agata/.env` em `permissions.deny` do Claude Code, com equivalentes em `config/cli/` para as outras CLIs.

## Matriz modelo × mecanismo

Estados: `ok-mecanico` (verificado nesta Máquina, pelo arquivo do repo ou por teste); `ok-doc` (depende de comportamento nativo da CLI, segundo a doc pública, não rodado aqui); `passo-humano` (exemplo em `config/cli/`, que o Humano copia para fora do repo); `disciplina` (depende de o modelo cumprir a instrução); `nao-medido`.

| Modelo | Ponto de entrada → AGENTS.md | Fim de turno (só aviso) | Negar leitura do .env | Contador de turno | Subagentes |
|---|---|---|---|---|---|
| Claude Code | `CLAUDE.md` importa `@AGENTS.md`: `ok-mecanico`. Doc: https://code.claude.com/docs/en/memory | Gancho `Stop` → `scripts/auditoria_stop.py`: `ok-mecanico` no `settings.json`; disparo numa sessão `nao-medido`. Doc: https://code.claude.com/docs/en/hooks | `permissions.deny` com `Read(~/.config/agata/.env)`: `ok-mecanico`. Cobre Read, Grep, Glob e `cat`, `head`, `tail` (doc), não cobre subprocesso (`python3 -c`). Doc: https://code.claude.com/docs/en/permissions | Gancho `UserPromptSubmit` → `turno.py hook`: `ok-mecanico` | `model: haiku`, `maxTurns` e `tools` sem Bash nos de leitura: `ok-mecanico`. Doc: https://code.claude.com/docs/en/sub-agents |
| Codex | `AGENTS.md` lido nativamente (8.066 bytes; limite 32 KiB; sem `AGENTS.override.md`): `ok-mecanico`. Doc: https://learn.chatgpt.com/docs/agent-configuration/agents-md | `[[hooks.Stop]]` em `config/cli/codex/config.toml.exemplo`: `passo-humano` (o Humano roda `/hooks` para confiar). Doc: https://learn.chatgpt.com/docs/hooks | `permissions.<nome>.filesystem` = `"deny"`: `passo-humano`; expansão de `~` `nao-medido`. Doc: https://learn.chatgpt.com/docs/config-file/config-reference | `disciplina`: `turno.py proximo` no início de cada resposta, por instrução do AGENTS.md | `disciplina` (a skill de equipe tem a regra) |
| Gemini CLI | `GEMINI.md` importa `@AGENTS.md`: `ok-mecanico`. Doc: https://geminicli.com/docs/cli/gemini-md/ | `AfterAgent` (campo `prompt_response`) em `config/cli/gemini/settings.json.exemplo`: `passo-humano`. Doc: https://geminicli.com/docs/hooks/reference/ | `BeforeTool` com `config/cli/gemini/bloquear_env.py` (exit 2): `passo-humano`; nome do campo do caminho em `tool_input` `nao-medido`. Doc: https://geminicli.com/docs/hooks/ | `disciplina`. A doc lista o evento `BeforeAgent`, que poderia tornar isso mecânico; não feito (payload não medido) | `disciplina` |
| OpenCode | `AGENTS.md` na raiz, lido pelo OpenCode: `ok-doc`. Doc: https://opencode.ai/docs/rules/ | `nao-medido`: a doc pública consultada não confirma evento de fim de turno com o texto da resposta | `permissions` na sintaxe V2 (`action`, `resource`, `effect`) em `config/cli/opencode/opencode.json.exemplo`: `passo-humano`; cobertura de `~/.config/agata/.env` `nao-medido`. Doc: https://opencode.ai/docs/permissions/ | `disciplina` | `disciplina` |
| Seth (gateway) | `_diretrizes_agents()` inclui o texto de AGENTS.md na hidratação compacta: `ok-mecanico` (teste). Código: `redesign/router/seth_gateway.py` | Já existe: `verificar_resposta_atual` no stream da resposta: `ok-mecanico` (código existente) | `nao-medido`: o gateway não expõe leitura de arquivo do usuário, mas não conferi todas as ferramentas | `t=<n> (contador mecânico)` calculado pela contagem de turnos da conversa, com o mesmo rótulo do contador: `ok-mecanico` (teste) | não se aplica |

Decisões (canon e cache), por modelo: a cadeia `AGENTS.md` → `PROMPT_CARREGAMENTO.md` → `REGRAS.md`, `PROTOCOLOS.md`, `FALHAS.md`, `MEMÓRIAS.md`, `PROJETO.md` é conferida por texto (`ok-mecanico`) em Claude Code, Codex, Gemini CLI e OpenCode. O AGENTS.md também manda ler o cache do Conselho (`cache_conselho.py ler`), e o arquivo existe. Seth recebe o resumo do cache a cada resposta (`resumo_hidratacao`) e tem `query_canon`. Ler de fato é disciplina em todos.

## O que ficou como disciplina, e por quê

- Ler o canon e o cache do Conselho no começo. O ponteiro é verificado; o ato de ler é do modelo. Nenhuma CLI deste pacote tem gancho de início de turno confirmado que injete essa leitura. Mecânico possível: o Claude Code já tem `SessionStart` (hoje roda `sessao_claude_contexto.sh`); o Gemini CLI lista `BeforeAgent` na doc.
- Contador de turno fora do Claude Code: sem gancho de início confirmado. Depende de o modelo rodar `turno.py proximo`.
- Pacote mínimo: o que o orquestrador passa a um subagente é decisão dele. O verificador confere que a regra está escrita (nos agentes e na skill), não o que foi passado.
- Fim de turno no OpenCode, e o payload do Codex: não confirmados na doc pública. Ficam `nao-medido`.
- Doutrina da Seth: a constante `_DOUTRINA_FIXA` do gateway continua no código como cópia de regras. Não é o AGENTS.md, e o verificador marca isso como `disciplina`. Remover a cópia é outra proposta (ver decisões pendentes).
- Custo: a Seth passa a receber os 8.066 bytes de AGENTS.md em cada resposta (modo compacto). Em tokens, `nao-medido`.

## Passos do Humano, fora do repo

O agente não escreveu nada fora do repositório e não leu `~/.codex`, `~/.gemini`, `~/.config` nem o `.env`. Depois de assinado e aplicado:

1. Claude Code: nada a copiar; o repo já tem `.claude/settings.json`. Reabrir a sessão para recarregar os ganchos (`nao-medido` se a sessão aberta recarrega sozinha).
2. Codex: copiar os blocos de `config/cli/codex/config.toml.exemplo` para `~/.codex/config.toml`. Abrir o Codex e rodar `/hooks` para confiar no hook de Stop; sem isso ele não roda. Conferir se `~` é expandido na chave de `permissions`.
3. Gemini CLI: copiar a chave `hooks` de `config/cli/gemini/settings.json.exemplo` para `~/.gemini/settings.json`. O exemplo usa `$GEMINI_PROJECT_DIR`; se a variável não existir na versão instalada, trocar pelo caminho absoluto do repo. Atenção: a página da doc consultada diz que o Gemini CLI foi substituído pelo Antigravity CLI para contas gratuitas e Google One em 18/06/2026. Conferir qual CLI está instalada antes.
4. OpenCode: copiar a chave `permissions` de `config/cli/opencode/opencode.json.exemplo` para `~/.config/opencode/opencode.json` (ou para o `opencode.json` do projeto). A doc consultada é a V1 da página; conferir a sintaxe na versão instalada.
5. Assinar, depois do merge do PR de proposta: `bash scripts/aprovar.sh pacote-mecanico-12-11 "<motivo>"`, no checkout vivo, depois de `git pull`.
6. Depois de aplicado: `bash scripts/p8_verificar.sh pacote-mecanico-12-11`.

## Arquivos do pacote

- Alterados (20): `.agents/skills/agata-fluxo-equipe/SKILL.md` (seção 9, pacote mínimo); `.claude/agents/*.md` (10 agentes: `model: haiku`, `maxTurns`, pacote mínimo; Bash tirado de 5 agentes de leitura); `.claude/settings.json` (`UserPromptSubmit`, `Stop`, `permissions.deny`); `.github/workflows/sdd.yml` (passo do pacote e caminhos de gatilho); `AGENTS.md` (Regra 1 e linha de memória comum); `PROMPT_CARREGAMENTO.md` (linha de turno); `PROTOCOLOS.md` (contador mecânico); `REGRAS.md` (definição de turno); `redesign/router/auditoria_turno.py` (`--verificar --sessao`, divergência como aviso); `redesign/router/seth_gateway.py` (AGENTS.md na hidratação compacta); `scripts/ci_sdd_local.sh` (passos do pacote).
- Novos (11): `config/cli/codex/config.toml.exemplo`; `config/cli/gemini/settings.json.exemplo`; `config/cli/gemini/bloquear_env.py`; `config/cli/opencode/opencode.json.exemplo`; `redesign/router/spec/spec.md` e `acceptance.json` (52 critérios: 25 do turno e 27 deste pacote); `scripts/turno.py` (contador); `scripts/testar_turno.py` (41 testes); `scripts/auditoria_stop.py` (gancho de fim de turno, só avisa); `scripts/conselho_mecanismos.py` (verificador); `scripts/testar_mecanismos.py` (28 testes).

Agentes sem Bash (cinco, por leitura): `agata-inov-critico`, `agata-inov-pesquisa`, `agata-pesq-painel`, `agata-pesq-processo` e `agata-pesq-rea`. O `agata-pesq-rea` perdeu o `--help` de binário de terceiro, que a memória do Humano diz não ser leitura pura; o uso do REA fica como não medido nele. `agata-revisor` mantém Bash, porque roda testes e `git diff`; `agata-ci`, `agata-dev`, `agata-spec` e `agata-inov-arquiteto` mantêm Bash porque rodam CI ou escrevem.

## Conflitos da reaplicação

- Base nova: `origin/main` foi de `acdfbf2c` para `04bfe2e4` (PR #976) enquanto o pacote era montado. O conjunto foi reaplicado com `git apply -3` sobre `04bfe2e4`: medido, dois conflitos (`AGENTS.md` e `auditoria_turno.py`), resolvidos à mão e testados de novo.
- `AGENTS.md`, linha da memória comum: o main trocou Goose por OpenCode e acrescentou `--cliente <nome>` ao `--verificar`. A linha ficou com os dois: `--verificar --cliente <nome> [--sessao <id>] < arquivo`, com a nota de registro de metadado e a de divergência do `t=`.
- `redesign/router/auditoria_turno.py`: o main acrescentou `_args_verificar` e `_registrar_cli`. O `--sessao ID` é tirado da lista de argumentos antes desse parser, e `--verificar` com argumento inválido sai 2, como o teste do turno exige. O selftest ficou com `_casos_cli()` e com os casos de divergência.
- O `turno-mecanico-12-11` (proposta de outro worktree, sem PR e sem `APROVADO-`) entra inteiro neste pacote. O arquivo solto não deve ser assinado separadamente.
- Subprodutos de ciclos SDD gerados pelo CI local (`redesign/sdd_flow/spec/evidence.json`, `redesign/sdd_flow/spec/criterion-drift.md` e `redesign/nova_versao/spec/evidence.json`) não são código: o índice tem 31 arquivos de código e nenhum deles, conferido com `git diff --cached --name-only`.

## Testes medidos

Rodada final, sobre `origin/main` `04bfe2e4` com o pacote aplicado no worktree `agent-a99339b0acb0ffad1` (branch `proposta/pacote-mecanico-12-11`):

- `uv run --offline --with pytest bash scripts/ci_sdd_local.sh`: `CI LOCAL: TUDO OK`, 40 passos OK, saída 0. Inclui o gate de spec, o lint de skills e os cinco passos novos do pacote.
- `python3 scripts/testar_turno.py`: 41 testes OK.
- `python3 scripts/testar_mecanismos.py`: 28 testes OK (ponteiros, limite do Codex, override, verificador com saída 1, gancho Stop com aviso sem bloqueio, `.env` negado, subagentes, Seth, exemplos).
- `python3 scripts/turno.py --selftest` e `python3 redesign/router/auditoria_turno.py --selftest`: `SELFTEST OK`. Com `-I`, o selftest da auditoria continua falhando por `ModuleNotFoundError: detector_estado_sem_prova`, falha pré-existente (ver decisões pendentes).

Medidos antes da reaplicação sobre `origin/main` `acdfbf2c`, com o mesmo código (a reaplicação não mudou esses arquivos além dos dois conflitos resolvidos e retestados acima):

- `SETH_REPO=<repo> python3 redesign/router/seth_gateway.py --selftest`: `SELFTEST OK`.
- `python3 redesign/sdd_flow/acceptance_runner.py redesign/router/spec/acceptance.json`: 52 de 52 com `pass` (25 do turno e 27 do pacote).
- `python3 -I scripts/gate_spec_sync.py`: 13 componentes, router com 52 critérios no spec, 0 falha; 1 aviso, a dívida conhecida da alexandria, que já existia. O mesmo gate roda de novo no CI da rodada final.
- `python3 redesign/painel_operacional/qualidade_llm.py`: 21 skills, nenhum problema.
- `python3 scripts/conselho_mecanismos.py --verificar`: 27 controles; ok-mecanico 17; disciplina 5; FALHA 0; saída 0. O passo do verificador no CI da rodada final deu saída 0.
- Verificação de canon: as linhas de `AGENTS.md`, `REGRAS.md`, `PROTOCOLOS.md` e `PROMPT_CARREGAMENTO.md` que mudaram são só as deste pacote; nenhuma linha do bloco de âncora de SHA entra no diff.

## Não medido

- O disparo real dos ganchos (`Stop`, `UserPromptSubmit`) numa sessão aberta, e se o Claude Code recarrega `.claude/settings.json` com a sessão aberta.
- Codex, Gemini CLI e OpenCode rodando o pacote: só a doc pública foi lida, e nenhum binário foi executado. A ordem de execução do gancho do Codex e a confiança via `/hooks` não foram testadas.
- Se o `permissions.deny` impede a leitura do `.env` por subprocesso (`python3 -c "open(...)"`): a doc diz que não impede. Só sandbox impede.
- Custo em tokens de AGENTS.md por resposta da Seth: medido em bytes (8.066), não em tokens.
- O GitHub no headSha do PR: depois do push.
- `scripts/testar_perimetro.sh`: roda só no CI do GitHub (`perimetro.yml`).
- Revisão independente (`agata-revisor`, modo "contra a spec"): não feita nesta rodada.

## Decisões pendentes do Humano

1. Cópia da doutrina na Seth: `_DOUTRINA_FIXA` em `redesign/router/seth_gateway.py` continua duplicando regras do AGENTS.md. Remover a cópia (a Seth passaria a depender só do arquivo) é proposta própria, com teste de conversa real.
2. Gemini CLI ou Antigravity CLI (doc de 18/06/2026): qual CLI o Humano usa de fato.
3. Gancho de início de turno para tornar mecânica a leitura do canon: `SessionStart` do Claude Code (já existe, falta o conteúdo) e `BeforeAgent` do Gemini CLI.
4. Falha pré-existente sem dono: `python3 -I redesign/router/auditoria_turno.py --selftest` falha com `ModuleNotFoundError: detector_estado_sem_prova`. Já estava no pacote-12-11; dono a definir.
5. Os valores de `maxTurns` (25 a 80) e a remoção de Bash de cinco agentes são valores de partida, não medidos. Ajustar pelo uso.
6. O verificador confere a regra escrita para subagentes, não o que foi passado. Se o Humano quiser conferir o pacote enviado, é outra proposta.

## Reversão

- `git apply -R propostas/pacote-mecanico-12-11.diff` na árvore com o pacote reverte as 31 peças. Medido: `git apply -R --check` sobre a árvore de `origin/main` com o pacote aplicado: OK, saída 0.
- Fora do repo, o Humano remove o que copiou para `~/.codex/config.toml`, `~/.gemini/settings.json` e `~/.config/opencode/opencode.json`.
- O diretório de estado do contador é cache: o `turno.py` o cria no primeiro uso, e pode ser apagado sem perda.
- Registro (`MEMÓRIAS.md`, `ONDE_ESTAMOS.md`): correção é entrada nova, não edição.

## Apetite (R2)

Até 40 arquivos e 2 horas de agente. Medido: 31 arquivos de código; o agente trabalhou de 09:29 até o fechamento deste `.md`, cerca de 20 minutos, com as rodadas de CI incluídas.

## Lista de conferência de pronto (R3)

- [x] CI local `TUDO OK` (40 passos) sobre `04bfe2e4`.
- [x] Gate de spec sem falha; lint de skills sem problema; 52 de 52 critérios do roteador.
- [x] Diff aplica limpo sobre `origin/main` `04bfe2e4`: conferido com índice temporário.
- [x] Sem emoji nas linhas novas (conferido no diff).
- [x] Nenhuma leitura de `~/.config/agata/.env` nem de caminho fora do repo pelo agente.
- [ ] Run verde no GitHub no headSha do PR: depois do push.
- [ ] Revisão independente: não feita (decisão 6 acima).
- [x] Reversão medida (ver seção Reversão).
- [x] `auditoria_turno.py --verificar` sobre este `.md`: 1 achado, falso positivo. Cita caminhos novos do diff (`redesign/router/spec/`, `config/cli/`, `scripts/auditoria_stop.py`) que só existem depois da aplicação; o texto não afirma que existem na Máquina do registro.

## Assinatura

Depois do merge deste PR de proposta, o Humano roda:

```
bash scripts/aprovar.sh pacote-mecanico-12-11 "<motivo>"
```

Verificação depois da assinatura, no checkout vivo, com `git rev-parse HEAD` igual a `origin/main`:

```
bash scripts/p8_verificar.sh pacote-mecanico-12-11
```
