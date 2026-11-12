# Skills do Agata: índice para o Conselho

Para qualquer modelo que trabalhe no Agata (Claude, Codex, Gemini, OpenCode, Seth ou outro). Comece por `agata-fluxo`: a tabela de escolha dele aponta a skill certa. Cada skill tem um dono e um escopo.

Consolidado em 12/11/2026 (proposta `skills-consolidadas-12-11`): de 21 pastas para 10 skills do Agata. Os originais ficam em `extras/arquivo-skills-12-11/`.

## Skills próprias do Agata (`agata-*`)

| Skill | Use quando | Dono de fato |
|---|---|---|
| `agata-fluxo` | entrada de qualquer tarefa: medir o estado, conduta, escolha da skill, mudança no runtime da Máquina, afirmar com prova | Claude (doutrina) |
| `agata-aplicar-proposta` | criar, verificar, propor e aplicar uma proposta P-8 ou um lote (CI local, âncora, assinatura, registro) | Claude |
| `agata-equipe` | trabalhar em Equipe, qualquer membro do Conselho (papéis, canal MSG, vigia, fila, fallback, cota) | Claude |
| `agata-painel` | painel operacional (porta 20146): textos, cores, popups, medições | Claude |
| `agata-voz` | ler em voz alta, falar, conversa falada e debate; todo modelo que fala usa a voz do Agata | Claude |
| `agata-conversar-com-seth` | conversar com a Seth ou ler a conversa dela | Claude |
| `agata-relay-provedores` | adaptadores de chats web no RelayCouncil | Codex |
| `agata-time-inovacao` | propor melhoria nova com SDD (pesquisa, spec, revisão, decisão, drift); método elefante e peixinhos dourados | Claude |
| `agata-engenharia-reversa` | análise estática de app ou bundle com o REA (allowlist e regras de uso) | Claude |
| `agata-llm-fundamentos` | como a LLM falha e o mecanismo do Agata para cada falha; rodada de experimento com critério prévio | Claude |

## Skills de terceiros (cópias fixas, não editar aqui)
- `design-taste-frontend` (tasteskill v2, fonte: github.com/Leonxlnx/taste-skill): direção de arte e inspeção de páginas de frontend. Cópia fixa em `.agents/skills`; não editar aqui. Para o Claude Code carregá-la, crie o link local `ln -s ../../.agents/skills/design-taste-frontend .claude/skills/design-taste-frontend` (link não versionado: o P-8 não verifica symlink). Os scripts abrem um Chrome headless e `assets.mjs` acessa a rede; ver `propostas/design-taste-frontend-v2-20261031.md`.
- Em `.claude/skills/`: `defuddle`, `json-canvas`, `obsidian-bases`, `obsidian-cli`, `obsidian-markdown`. Cópias de terceiros; a fonte de atualização é externa.

## Regras de manutenção
1. Cada skill cita só caminhos que existem. Antes de salvar, confira com `python3 redesign/painel_operacional/qualidade_llm.py` (aviso "caminho citado inexistente").
2. Uma skill por assunto. Se um assunto já tem skill, acrescente à skill, não crie outra.
3. Formato universal: Markdown simples, frontmatter só com `name` e `description`, sem arquivo específico de um modelo (por exemplo, `agents/openai.yaml`).
4. Mudança em skill do repositório passa por proposta P-8 (é arquivo versionado).
5. Medido vai com comando e data. Sem medição, a frase começa com "não medido".
