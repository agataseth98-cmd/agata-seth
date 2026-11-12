# Spec — Turno mecânico (contador de turno)

Spec mínima do turno dentro de `redesign/router/`. Origem: entrevista P1 do Humano em 12/11/2026, 09:15 (cache do Conselho, entrada (514)). Quatro decisões: (1) turno é a resposta do modelo que devolve o controle ao Humano; chamadas de ferramenta e subagentes dentro dela não contam; (2) contador mecânico na Máquina, por sessão, avançado por um gancho a cada mensagem do Humano, que entrega a linha pronta; o modelo só copia; (3) subagente herda o turno do pai, com `t=<n>.sub`; (4) divergência entre cabeçalho e contador é acusada pela auditoria e não bloqueia.

O código do contador fica em `scripts/turno.py` e os testes em `scripts/testar_turno.py`, por pedido da tarefa. Esta spec os cobre.

## Jornadas críticas

1. O Humano manda uma mensagem no Claude Code. O gancho avança o contador e a resposta abre com a linha que ele injetou: `agata · <modelo> · t=<n> (contador mecânico) · <hora>`.
2. Um subagente roda dentro do turno e escreve `t=<n>.sub`, sem avançar o contador.
3. A auditoria confere o `t=` do cabeçalho com o contador da sessão e acusa a divergência, sem bloquear.

## Contrato

- `scripts/turno.py proximo --sessao ID` avança o contador da sessão em 1, começando em 1, e imprime a linha pronta. `atual` e `sub` não avançam. `sub` imprime `t=<n>.sub`.
- O estado fica em `~/.cache/agata/turnos/<ID>.json` (ou em `$AGATA_TURNOS_DIR`), modo 0600, sob trava `flock` e com escrita atômica. O ID aceita letras, números, `.`, `_` e `-`, até 128 caracteres, começando por letra ou número.
- Arquivo corrompido: `proximo` recomeça em 1 com a marca `contador reiniciado`. `atual` e `sub` recusam com saída 1. Nada disso quebra o gancho.
- `scripts/turno.py hook` lê o JSON do gancho UserPromptSubmit: `session_id` do stdin (ou `CLAUDE_SESSION_ID`, como último recurso); modelo de `model` ou, na falta, do último `message.model` do `transcript_path`, ignorando `<synthetic>`. Devolve `additionalContext` com `Cabeçalho deste turno: …`. Na 1ª resposta da sessão, pede o bloco de prontidão e não injeta linha `t=`. Sem sessão, com entrada inválida ou com erro, sai 0 e não imprime nada.
- `redesign/router/auditoria_turno.py --verificar --sessao ID` compara o `t=` do cabeçalho com o contador da sessão. Divergência sai como `aviso (não bloqueia)`. O código de saída não muda por causa do aviso.
- O gateway da Seth (`redesign/router/seth_gateway.py`) já calcula `t=<n> (contador mecânico)` pela contagem de turnos da conversa, com o mesmo rótulo. Nada muda nele nesta proposta.
- Hora: formato regional com fuso e selo, `DD/MM/AAAA HH:MM -03 (relógio da Máquina)` (`PROTOCOLOS.md`, "Regra 1.1").

## Critérios de aceite

- [ ] proximo começa em 1 numa sessão nova e soma 1 a cada chamada
- [ ] sub não avança o contador e imprime t=<n>.sub; atual também não avança
- [ ] sessões diferentes têm contadores independentes
- [ ] id de sessão fora do formato é recusado e nada é gravado fora do diretório
- [ ] hora regional com fuso -03 e selo de origem
- [ ] chamadas em threads na mesma sessão não repetem nem pulam número
- [ ] chamadas em processos na mesma sessão não repetem nem pulam número
- [ ] arquivo corrompido recomeça em 1 com a marca contador reiniciado
- [ ] arquivo que não é arquivo não quebra o gancho
- [ ] atual sem turno sai 1 e id inválido sai 2
- [ ] o selftest do turno.py passa
- [ ] o gancho injeta Cabeçalho deste turno com a linha pronta a partir do 2º turno
- [ ] o gancho usa o session_id do stdin antes do CLAUDE_SESSION_ID
- [ ] entrada inválida ou sem sessão: o gancho sai 0, sem saída e sem escrever
- [ ] na 1ª resposta da sessão o gancho pede o bloco de prontidão, sem linha t=
- [ ] o modelo medido no transcrito entra no cabeçalho
- [ ] <synthetic> não entra no cabeçalho: vira modelo não verificado
- [ ] o modelo do payload tem prioridade sobre o transcrito
- [ ] a linha do gancho passa no verificador de cabeçalho
- [ ] a auditoria acusa t= divergente do contador como aviso, sem mudar o código de saída
- [ ] a auditoria compara t=<n>.sub pelo número
- [ ] sem --sessao, sem contador ou sem t= no cabeçalho, a auditoria não acusa
- [ ] o gateway da Seth usa o mesmo rótulo (contador mecânico)
- [ ] REGRAS, PROTOCOLOS e AGENTS apontam o contador mecânico e o t=<n>.sub
- [ ] .claude/settings.json registra o gancho UserPromptSubmit e preserva o SessionStart

## Pacote mecânico (12/11/2026): pontos de entrada, fim de turno, negação do .env, subagentes

Origem: decisões do Humano de 12/11/2026 (cache do Conselho): o que o Agata desenvolve vale para todos os modelos do Conselho por mecanismo da Máquina, não por instrução; todo modelo age segundo o mesmo sistema e as mesmas decisões; subagente recebe só o pacote mínimo. Código em `scripts/conselho_mecanismos.py`, `scripts/auditoria_stop.py` e `config/cli/`; testes em `scripts/testar_mecanismos.py`.

Pontos de entrada, por modelo: Claude Code lê `CLAUDE.md`, que importa `@AGENTS.md`. Codex e OpenCode leem `AGENTS.md` pelo próprio nome. Gemini CLI lê `GEMINI.md`, que importa `@AGENTS.md`. Seth recebe AGENTS.md na hidratação do gateway. Ponteiro não é cópia: CLAUDE.md e GEMINI.md têm no máximo 500 bytes.

Contrato do fim de turno: `scripts/auditoria_stop.py` é o gancho de Stop (Claude Code), AfterAgent (Gemini) ou Stop (Codex). Lê o texto da última resposta, roda `auditoria_turno.py --verificar` e só avisa, por `systemMessage`. Não bloqueia: sai 0 sempre.

Critérios de aceite (pacote mecânico)

- [ ] o CLAUDE.md importa @AGENTS.md
- [ ] o GEMINI.md importa @AGENTS.md
- [ ] ponteiro quebrado faz o verificador de mecanismos falhar
- [ ] ponteiro convertido em cópia (acima de 500 bytes) faz o verificador falhar
- [ ] AGENTS.md acima de 32 KiB faz o verificador falhar, pelo limite do Codex
- [ ] AGENTS.override.md na raiz faz o verificador falhar
- [ ] o verificador sai 1 quando há FALHA
- [ ] no repositório o verificador não tem FALHA
- [ ] o verificador imprime uma linha por controle e um resumo por estado
- [ ] a hidratação do gateway inclui AGENTS.md lido em tempo de execução
- [ ] sem AGENTS.md o gateway avisa lacuna e não quebra
- [ ] o settings registra o gancho Stop com auditoria_stop.py
- [ ] o gancho Stop avisa por systemMessage e nunca bloqueia
- [ ] resposta sem achado sai calada com 0
- [ ] entrada sem texto ou inválida sai 0 sem saída
- [ ] o gancho Stop lê prompt_response do Gemini
- [ ] o gancho Stop confere o t= com o contador da sessão e só avisa
- [ ] o settings nega Read de ~/.config/agata/.env
- [ ] o exemplo do Codex nega o .env pela chave permissions do config.toml
- [ ] o exemplo do OpenCode nega *.env pela sintaxe V2 de permissions
- [ ] o gancho do Gemini bloqueia a leitura do .env com exit 2
- [ ] todo agente em .claude/agents tem model haiku e maxTurns
- [ ] os agentes só de leitura não têm Bash
- [ ] nenhum agente desliga o CLAUDE.md (omitClaudeMd)
- [ ] todos os agentes têm o mesmo texto de pacote mínimo
- [ ] a skill de equipe tem a regra de pacote mínimo
- [ ] PROMPT_CARREGAMENTO aponta o contador de turno

Não medido (neste pacote): o OpenCode tem evento de fim de turno com o texto da resposta (a doc pública consultada não confirma); o nome do campo do caminho em `tool_input` no Gemini; se o Codex expande `~` na chave de deny; se o Claude Code recarrega `.claude/settings.json` em sessão aberta; o custo em tokens do AGENTS.md na hidratação compacta da Seth (ordem de grandeza: 7,9 KB por turno, medido em bytes, não em tokens).

Pendência conhecida: `redesign/router/seth_gateway.py` mantém a constante `_DOUTRINA_FIXA` (cópia de regras). Remover a cópia é outra proposta; o verificador marca isso como disciplina.

## Desenho e alternativas

- Contador próprio em arquivo por sessão, em vez de contar mensagens no transcrito. O transcrito tem formato de cada CLI e pode ser compactado; o contador não depende disso.
- Gancho lê `session_id` do stdin, em vez de `$CLAUDE_SESSION_ID`. No binário do Claude Code local (2.1.322), `CLAUDE_SESSION_ID` aparece só como substituição de template de skill e comando; não há evidência de que o gancho o receba como variável. O nome `session_id` aparece entre os campos de entrada dos ganchos.
- Gateway não muda. Ele já conta os turnos da conversa com `auditoria_turno._turnos`, que agrupa por pedido do Humano. Contar `role=assistant` contaria também cada chamada de ferramenta, o que a decisão (1) exclui.
- Descartado: contar só no gateway da Seth e deixar Claude Code sem contador. Iria contra a decisão (2) de que o contador é da Máquina.

## Implementação e testes

- `scripts/turno.py`: contador, gancho e `--selftest`; biblioteca padrão apenas.
- `scripts/testar_turno.py`: unittest, 41 casos, com estado em diretório temporário. Roda com `python3 scripts/testar_turno.py` ou com pytest.
- `redesign/router/spec/acceptance.json`: cada critério aponta para um teste ou para o selftest.
- Verificação da auditoria: `redesign/router/auditoria_turno.py --selftest` ganha os casos de divergência.

## Migração e reversão

- Sem dados a migrar. Sessões anteriores à aplicação não têm contador; começam em 1 quando voltarem a receber mensagem.
- Reverter: tirar o bloco `UserPromptSubmit` de `.claude/settings.json`, restaurar as três linhas canônicas de `REGRAS.md`, `PROTOCOLOS.md` e `AGENTS.md`. `~/.cache/agata/turnos/` é cache, pode ser apagado.

## Riscos e dependências

- Não medido: se o Claude Code recarrega `.claude/settings.json` em sessões já abertas.
- Não medido: se o `UserPromptSubmit` dispara dentro de subagente. A spec assume que não, e que o orquestrador passa o `t` e o `<id>` no prompt do subagente.
- Não medido: se Codex, Gemini CLI e OpenCode leem `AGENTS.md` e seguem a instrução de chamar `proximo` no início de cada resposta. Sem gancho, o contador depende dessa disciplina do modelo.
- Não medido: conversa com turno só de ferramenta (sem texto) no gateway. `_turnos` ignora esse turno, e a contagem da Seth pode ficar uma unidade atrás.
- Não medido sob carga real: trava de 5 s entre processos. Os testes cobrem 30 processos e 8 threads.
- `redesign/router/` não está na lista de âncoras do `scripts/ci_sdd_local.sh`. Esta spec cobre só o turno; ancorar o roteador inteiro é outra proposta.

## Código

- `auditoria_turno.py` (verificação de divergência: `divergencia_turno` e `--verificar --sessao`)
