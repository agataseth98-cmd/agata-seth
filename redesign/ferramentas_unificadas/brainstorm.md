# Brainstorm: ferramentas-unificadas-26-11

Exploração. Contrato em spec.md; decisões em decision.md.

## Usuários
- Humano: uma instalação aparece em todos os modelos [H3].
- Claude Code, Codex e OpenCode: medidos (binário e config existem).
- Gemini CLI: `~/.gemini/` residual, binário ausente. Não medido no runtime atual.

## Estado que muda
- Nativos: `~/.claude.json` (91 chaves; MCP de usuário: `github-pat`); `~/.codex/config.toml` (`mcp_servers.*`, plugins); `~/.config/opencode/opencode.jsonc` (2 linhas de comentário).
- Ponteiros: `~/.claude/skills/` (2 entradas); `~/.codex/skills/` (vazio).

## Memória comum por CLI
- Claude Code: SessionStart em `~/.claude/settings.json` (medido). Codex: `session_start` em `~/.codex/hooks.json` (medido). OpenCode: não medido.
- O cache continua em `redesign/router/cache_conselho.py`; muda só o ponto de entrada.

## Erros e concorrência
- Claude Code reescreve `~/.claude.json` na sessão; corrida não medida.
- Config inválida aborta antes da primeira escrita.
- Entrada de mesmo nome fora da fonte não é adotada sem marca.
- O backup copia o segredo de `github-pat`: permissão 600, fora do repo.

## Menor mecanismo
- JSON, TOML ou JSONC à mão: descartado.
- Comandos nativos de MCP: escolhido (reaproveitam o escritor de cada CLI).
- Ponteiro para `.agents/skills/`: escolhido; nada é copiado.
- Gerador de subagentes: só OpenCode, com formato medido (`.opencode/agent/agata-code.md`).

## Migração, observabilidade, reversão, sucesso
- Migração: dry-run, backup e escrita; nada removido na primeira rodada.
- Observabilidade: `sincronizar.py --dry-run` e `listar.py`, só com nomes e contagens.
- Reversão: spec.md, seção 6.
- Sucesso: aparece nos três CLIs; rodar de novo não muda nada; reverter não apaga o que a CLI gravou depois.
