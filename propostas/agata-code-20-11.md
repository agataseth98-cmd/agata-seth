# Proposta agata-code-20-11 — nasce o Agata Code e a Seth do painel passa a chamá-lo

Lote 2 das decisões do Humano por voz, 20/11/2026 (cache do Conselho): Agata Code é o agente que roda no OpenCode, frente de código, mesmas regras e portões; a Seth o chama de dentro da conversa, num sentido só; o Humano escolhe ver ou não o trabalho, como no Conselho.

**O quê:**
- `.opencode/agent/agata-code.md` (novo): agente do OpenCode 1.19.5 (formato conferido com `opencode agent list`), modelo agata/seth-livre. Segue AGENTS.md, lê e anota o cache com autor "Agata Code". Permissões: edita arquivos; lê tudo menos `.env` e `~/.config/agata`; sem web; bash negado por padrão, liberado só para git de leitura, ls/grep/rg/find/wc/head/tail, pytest e cache_conselho; negados git commit/push, sudo, rm -rf, curl, wget, `-exec`, `-delete`, `--output` e redirecionamento.
- `redesign/painel_operacional/ferramentas_seth.py`: ferramenta `agata_code` (só seth-livre). Roda `opencode run --agent agata-code` numa worktree NOVA e descartável de origin/main em `~/agata-arquivo/agata-code/<data-hora>/`, nunca no ~/agata vivo; ambiente mínimo; timeout 600 s; devolve resposta, `git diff --stat` e caminho; sem mudança, apaga a worktree; transcrição guardada. "Agata Code trabalhando…" a cada ~10 s (Regra 0).
- `prototipo.js`/`prototipo.css`: bloco "Trabalho do Agata Code", fechado por padrão.
- Spec e acceptance do painel (6 critérios); 12 testes novos com opencode falso.

**O que ele mudar fica na worktree descartável até o Humano decidir**; entra no sistema só pelo fluxo de proposta e assinatura.

**Medido:** 27 testes de ferramentas_seth; CI local TUDO OK (agente). Execução real só de leitura: 8,6 s, rota seth-codigo (nemotron-3.5-bolt), respeitou "não altere" (sem diff, worktree apagada), permissão barrou comando fora da lista. Qualidade: contou 1 arquivo .js onde há 5 — modelo gratuito fraco em contagem; é o que o lote 3 (divisão pelo placar) vai atacar.

**Riscos:** pytest roda código da worktree com os direitos do usuário (contenção Landlock é frente própria); o MCP global agata-maquina (só leitura) fica disponível ao agente; a conversa fica ocupada até 600 s; o bloco não entra na conversa salva; worktrees com mudança ficam em ~/agata-arquivo até o Humano mandar. **Reversão:** git revert e reiniciar o painel. **Modelo:** Sonnet 5.5 (código), Opus 5.5 (revisão; fechou -exec, -delete, --output e redirecionamento).
