# Decreto: caixa de ferramentas do Agata (30/10/2026)

Pedido do Humano: trazer as skills e os agentes do ECC (Everything Claude Code) e as skills do superpowers para dentro do repositório, unidos às skills do Agata, por tema e carregados só quando a tarefa pedir.

O que entra:
- `ferramentas/fontes/ecc/`: 314 skills, 71 agentes (commit b38be6a, licença MIT) e os hooks em `hooks-inativos/` (desligados).
- `ferramentas/fontes/superpowers/`: 15 skills (commit bb92a77, licença MIT).
- `ferramentas/ferramentas.py`, `INDICE.md`, `indice.json`: índice por 11 temas; só leitura.
- Skill `agata-ferramentas` (porta de entrada) e uma linha em `.agents/skills/INDICE.md`.
- Teste: índice em dia, quarentena, commit e licença presentes, nenhum arquivo executável.

Alteração sobre o original (decisão do Humano, 30/10): 11 valores de exemplo (senhas de mentira) trocados por `<exemplo>` para passar no detector de segredos; lista em `ferramentas/fontes/ALTERACOES.md`. O resto é idêntico ao commit da fonte.

Riscos apontados e decisões:
- Hooks do ECC gravam atividade em disco e podem capturar segredos: entram desligados; ligar exige novo Decreto.
- Tema `quarentena` (16 peças: aprendizado automático, memória paralela, laços autônomos): só leitura, em choque com "o Humano decide".
- Nada é instalado em `~/.claude/` nem em `~/.codex/`: a lista automática de skills não cresce.
- Sobreposição (TDD, revisão, depuração entre ECC e superpowers): vale a skill `agata-*` quando houver.
- 140 peças ficaram no tema genérico `negocios-e-nichos`; refinar depois.

Não verificado: o corpo das skills e o código dos hooks linha a linha.

Aplicação, depois da assinatura: `bash scripts/aprovar.sh ferramentas-caixa-20261030 "aprovo: caixa de ferramentas"`.
