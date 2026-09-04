# arquivo-redesign/

Documentos do redesenho do sistema (branch `redesign`, Fases 0-8, mergeado em
`main` em 03/09/2026 — MEMÓRIAS (310)/(311)) que já cumpriram seu papel e
viraram **história**, movidos pra cá em 04/09/2026 (MEMÓRIAS (319)/(320))
numa varredura pedida pelo Humano ("muitas notas soltas... tornar tudo
consiso e coerente"). Nada aqui é operacional — o que ainda é vivo continua
em `redesign/` (código-fonte das peças em produção: `router/`, `grafo/`,
`mcp/`, `librechat/`, `obsidian/`, `igpu/`, `systemd/`, `fase7-hd/`) e nos
documentos que seguem sendo referência ativa (`STATUS.md`, `LOG.md`,
`CONTINUIDADE.md`, `CLAUDE-NA-MAQUINA.md`, `ANCORA.md`, `ACESSO-GRADUADO.md`,
`ROADMAP.md`, `CANON-DELTA.md`, `OTIMIZACOES.md`, `SILO-HUMANO.md`,
`PESQUISA.md` — nenhum destes foi movido).

- `tasks/P0-*.md` … `P8-*.md` (42 arquivos) — especificação de cada tarefa
  das 9 fases do redesenho. Todas fechadas; o que aconteceu de fato está em
  `redesign/STATUS.md`/`LOG.md` e nas entradas de MEMÓRIAS que citam cada
  fase, não aqui.
- `REIDRATACAO-chat-{3,4,6}.md` — prompts de handoff pra continuar o
  redesenho numa sessão nova, escritos quando a janela de contexto de uma
  sessão anterior estourava. As sessões que eles reidratavam já terminaram.
- `AUDITORIA-01.md` — auditoria pontual de uma rodada específica da Fase 8.
  Achados já viraram correção aplicada (ver MEMÓRIAS) ou entraram no
  histórico de decisão.
- `CONSELHO-01-relay.md`, `CONSELHO-02-sync-fallbacks.md`,
  `CONSELHO-03-sync-fallbacks.md` — logs de consultas pontuais ao Conselho
  Remoto durante o redesenho. Resultado incorporado onde fez sentido.
- `RUNBOOK-fase0-HD.md` — runbook da Fase 0 (tag + backup inicial), fase
  fechada há muito.

Nenhum arquivo teve conteúdo alterado na mudança — só de lugar (`git mv`,
histórico preservado). Um comentário em `redesign/mcp/servidor.py` que
apontava pro caminho antigo de um dos `tasks/*.md` foi atualizado no mesmo
commit.
