# Spec — Sincronia (fonte única, porquês, início de sessão)

Spec do componente `sincronia` (proposta `sincronia-12-11`). Origem: decisão do Humano de 12/11/2026, 10:00 (cache do Conselho, entrada (521)): atualizar o sistema para funcionar em sincronia, como um relógio; tudo deve ter um porquê; fonte única, sem cópias (começa removendo a cópia de regras `_DOUTRINA_FIXA` do gateway da Seth); gancho de início de sessão que torna mecânica a leitura do canon e do cache; maxTurns dos agentes pelo uso medido.

O texto próprio da Seth sai do código e vai para `PROTOCOLOS.md`, seção "Seth no gateway". O verificador de porquês fica em `scripts/porques.py`, com o registro em `config/porques.json`. O contexto de início de sessão fica em `scripts/sessao_contexto.py`, usado pelo Claude Code, pelo Gemini CLI e pelo Codex. Os testes ficam em `scripts/testar_sincronia.py`.

## Jornadas críticas

1. A Seth recebe a hidratação: o marcador, a seção "Seth no gateway" de `PROTOCOLOS.md`, o `AGENTS.md` inteiro e o estado. Nada vem de cópia no código.
2. Um modelo abre sessão no Claude Code: o gancho `SessionStart` injeta regras ativas, as últimas decisões do cache, os lotes abertos e o estado da Máquina, em texto curto.
3. Um bullet do `AGENTS.md` ou uma skill sem origem aparece como `SEM-PORQUE` na lista, para o Humano decidir. Na primeira versão é aviso.

## Contrato

- A constante `_DOUTRINA_FIXA` não existe em `redesign/router/seth_gateway.py`. A hidratação compacta inclui a seção `SETH-GATEWAY` de `PROTOCOLOS.md` e o `AGENTS.md`. Sem a seção, a hidratação diz `lacuna`, nunca cai em silêncio.
- O marcador `SETH:HIDRATADO` muda quando a seção ou o `AGENTS.md` mudam, para que conversas em andamento sejam hidratadas de novo depois do redeploy.
- `scripts/porques.py --verificar` lista uma linha por unidade (bullet "Sempre" do `AGENTS.md` e `SKILL.md` de `.agents/skills/`), com `OK` e a origem, ou `SEM-PORQUE`. Sai 0; com `--estrito`, sai 1 se houver `SEM-PORQUE`, referência que não confere ou registro órfão.
- Uma origem é válida se for `MEMÓRIAS (N)` com entrada existente em `MEMÓRIAS.md`, `MEMORIAS-MORNO.md` ou `memoria/frio/`, `Humano DD/MM/AAAA` com data válida, ou `cache (N)` na forma.
- `scripts/sessao_contexto.py --json` imprime `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ...}}` com no máximo 3500 caracteres e cinco seções.
- `scripts/sessao_claude_contexto.sh` é invólucro fino: não tem cópia de regras.
- Os exemplos `config/cli/gemini/settings.json.exemplo` e `config/cli/codex/config.toml.exemplo` têm `SessionStart` apontando para `scripts/sessao_contexto.py`, e mantêm o que já tinham.
- A rota pública (`seth-public`) lê a seção `SETH-PUBLICA` de `PROTOCOLOS.md`; sem ela, responde 503 (falha fechada), sem doutrina de reserva no código.
- Cada `.claude/agents/*.md` tem `maxTurns` numérico entre 10 e 300. O agente `agata-dev` tem pelo menos 232, o maior uso medido: os relatórios desta sessão citam de 19 a 232 tool_uses por execução, sem dizer o tipo do agente que chegou a 232.

## Critérios de aceite

- [ ] o gateway não tem _DOUTRINA_FIXA nem _DOUTRINA_PUBLICA e chama _doutrina_seth() e _doutrina_publica()
- [ ] a seção 'Seth no gateway' é lida de PROTOCOLOS.md sem os marcadores
- [ ] a hidratação traz a seção e o AGENTS.md, e o marcador de hidratação
- [ ] sem a seção, a hidratação diz lacuna e não cai em silêncio
- [ ] mudar a seção muda o marcador de hidratação
- [ ] PROTOCOLOS.md tem a seção 'Seth no gateway' marcada uma vez
- [ ] a seção 'Seth no gateway' diz que o gateway abre a resposta da Seth com o cabeçalho medido, e que ela não escreve cabeçalho
- [ ] a rota pública tem a doutrina em PROTOCOLOS.md (SETH-PUBLICA), sem cópia no gateway
- [ ] o verificador de mecanismos marca a fonte única como ok-mecanico
- [ ] o verificador de porquês passa no selftest
- [ ] o repositório tem 15 regras do AGENTS.md e uma unidade por SKILL.md
- [ ] regra sem origem não aparece como OK
- [ ] com --estrito, sem porquê sai 1; sem --estrito, sai 0
- [ ] as regras curtas listam os títulos das regras ativas
- [ ] o contexto de início de sessão passa no selftest offline
- [ ] as decisões do cache entram só quando são decisão, as últimas três
- [ ] os lotes abertos vêm da coluna de estado de ONDE_ESTAMOS
- [ ] o contexto tem cinco seções e cabe no limite de caracteres
- [ ] a saída tem o formato SessionStart com additionalContext
- [ ] o invólucro do Claude chama o conteúdo comum e não tem cópia de regras
- [ ] o .claude/settings.json tem SessionStart com o invólucro
- [ ] o exemplo do Gemini tem SessionStart e mantém AfterAgent
- [ ] o exemplo do Codex tem SessionStart e mantém Stop e a negação do .env
- [ ] cada agente em .claude/agents tem maxTurns entre 10 e 300
- [ ] o agente de desenvolvimento tem maxTurns de pelo menos 232 (maior uso medido)

## Não medido

- Disparo real do `SessionStart` numa sessão aberta do Claude Code, e a ordem em que roda com os outros ganchos.
- Gemini CLI e Codex rodando o gancho instalado. Só a doc pública foi lida; nenhum binário foi executado.
- Se a Seth, com o texto novo na hidratação, responde como antes. Só conversa real mede isso.
- Os limites de `maxTurns` por tipo de agente: não há medição por tipo no repositório. Só `agata-dev` mudou (80 para 300), porque o maior uso medido, 232, não cabe em 80 se for dele. Os demais ficam como estavam (25 a 40) até o coordenador passar a tabela de tool_uses por tipo.
