# ferramentas/

Caixa de ferramentas do Agata: skills e agentes de terceiros e próprios, organizados por tema e carregados sob demanda.

- `fontes/superpowers/`: obra/superpowers (MIT), 15 skills, commit em `COMMIT`.
- ECC (Everything Claude Code, MIT: 314 skills, 71 agentes, hooks desligados) saiu da caixa em 12/11/2026 e está em `extras/arquivo-ecc-12-11/`, fora do índice.
- `INDICE.md` e `indice.json`: gerados por `python3 -I ferramentas/ferramentas.py reindexar`.
- Entrada de uso: skill `agata-fluxo` (seção 2, tabela de escolha) e `python3 -I ferramentas/ferramentas.py tema <tema>`.

Nada aqui é instalado em `~/.claude/` nem em `~/.codex/`: a lista automática de skills continua pequena.
