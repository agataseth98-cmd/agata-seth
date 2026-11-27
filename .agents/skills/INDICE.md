# Skills do Agata: índice para o Conselho

Para qualquer modelo que trabalhe no Agata (Claude, Codex, Gemini, OpenCode, Seth ou outro). Comece por `agata-fluxo`: a tabela de escolha dele aponta a skill certa. Cada skill tem um dono e um escopo.

Consolidado em 12/11/2026 (proposta `skills-consolidadas-12-11`). São 14 skills próprias (`agata-*`) e 6 de terceiros (20 pastas + este índice no diretório). Os originais ficam em `extras/arquivo-skills-12-11/`.

## Skills próprias do Agata (`agata-*`)

| Skill | Use quando | Dono de fato | Aberta a todos? |
|---|---|---|---|
| `agata-arranque` | início de qualquer sessão: cabeçalho, memória do Conselho, mapa do Humano, P-8 e problemas recorrentes | todos os modelos | sim |
| `agata-fluxo` | entrada de qualquer tarefa (guia Ma'at): medir o estado, conduta, escolha da skill, regras de lote, mudança no runtime da Máquina, afirmar com prova | agata-spec (dono); revisor agata-revisor (D4, 07/11/2026) | sim |
| `agata-aplicar-proposta` | criar, verificar, propor e aplicar uma proposta P-8 ou um lote (CI local, âncora, assinatura, registro) | Claude (mantém) | sim |
| `agata-adotar-skill` | adotar uma skill de terceiro comprovada no ledger (acima de 51%, ao menos 10 usos): reescrever em .agents/skills com licença e origem, por P-8 | Claude (mantém) | sim |
| `agata-equipe` | trabalhar em Equipe, qualquer membro do Conselho (papéis, canal MSG, vigia, fila, fallback, cota) | Claude (mantém) | sim |
| `agata-painel` | painel operacional (porta 20146): textos, cores, popups, medições | Claude (mantém) | sim |
| `agata-voz` | ler em voz alta, falar, conversa falada e debate; todo modelo que fala usa a voz do Agata | Claude (mantém) | sim |
| `agata-voz-cerebro` | conversa por voz com o modelo da CLI como cérebro (ouvido + voz + som de espera) | todos os modelos de CLI | sim |
| `agata-mapear-humano` | obrigatória: ao começar, ler o mapa do Humano no cache do Conselho; ao receber decisão ou correção dele, anotar com fonte (protocolo de inserção humana continuado, 18/11/2026) | todos os modelos | sim |
| `agata-conversar-com-seth` | conversar com a Seth ou ler a conversa dela | Claude (mantém) | sim |
| `agata-relay-provedores` | adaptadores de chats web no RelayCouncil | Codex (mantém) | sim |
| `agata-time-inovacao` | propor melhoria nova com SDD (pesquisa, spec, revisão, decisão, drift); método elefante e peixinhos dourados | Claude (mantém) | sim |
| `agata-engenharia-reversa` | análise estática de app ou bundle com o REA (allowlist e regras de uso) | Claude (mantém) | sim |
| `agata-llm-fundamentos` | como a LLM falha e o mecanismo do Agata para cada falha; rodada de experimento com critério prévio | Claude (mantém) | sim |

## Arranque rápido para modelos novos ou simples

Checklist operacional mínimo — os 4 comandos de CLI que todo modelo precisa em cada turno:

```bash
# 1. Cabeçalho de turno (sem hook automático)
python3 scripts/turno.py proximo --sessao <ID> --modelo <modelo>

# 2. Ler as últimas notas do Conselho
python3 redesign/router/cache_conselho.py ler --n 20

# 3. Anotar ao fechar trabalho relevante
python3 redesign/router/cache_conselho.py anotar --autor "<modelo>" --tipo fato "<texto>"

# 4. Auditar antes de entregar (mecânico: citação, P-n, caminhos)
python3 redesign/router/auditoria_turno.py --verificar --sessao <ID>
```

Para o fluxo completo: `.agents/skills/agata-fluxo/SKILL.md`. Para proposta P-8: `.agents/skills/agata-aplicar-proposta/SKILL.md`. Para o mapa do Humano (obrigatório): `.agents/skills/agata-mapear-humano/SKILL.md`.

## Skills de terceiros (cópias fixas, não editar aqui)
- `design-taste-frontend` (tasteskill v2, fonte: github.com/Leonxlnx/taste-skill): direção de arte e inspeção de páginas de frontend. Cópia fixa em `.agents/skills`; não editar aqui. Para o Claude Code carregá-la, crie o link local `ln -s ../../.agents/skills/design-taste-frontend .claude/skills/design-taste-frontend` (link não versionado: o P-8 não verifica symlink). Os scripts abrem um Chrome headless e `assets.mjs` acessa a rede; ver `propostas/design-taste-frontend-v2-20261031.md`.
- Em `.claude/skills/`: `defuddle`, `json-canvas`, `obsidian-bases`, `obsidian-cli`, `obsidian-markdown`. Cópias de terceiros; a fonte de atualização é externa.
- Atena/Reversa instalado para assimilação em worktree: `impeccable`, `reversa`, `reversa-add`, `reversa-agents-help`, `reversa-arbiter`, `reversa-archaeologist`, `reversa-architect`, `reversa-arquitetura-3d`, `reversa-audit`, `reversa-autonomous`, `reversa-brainstorm`, `reversa-challenger`, `reversa-clarify`, `reversa-code-express`, `reversa-coding`, `reversa-curator`, `reversa-data-master`, `reversa-debugger`, `reversa-debugger-debate`, `reversa-debugger-fix`, `reversa-debugger-graph`, `reversa-decouple`, `reversa-depth-inspection`, `reversa-design-system`, `reversa-designer`, `reversa-detective`, `reversa-docs`, `reversa-docs-analyst`, `reversa-docs-mapper`, `reversa-docs-publisher`, `reversa-docs-storyteller`, `reversa-drafter`, `reversa-especialista-d3`, `reversa-explorer`, `reversa-extract-soul`, `reversa-forward`, `reversa-forward-autonomous`, `reversa-framer`, `reversa-highcharts-visualizer`, `reversa-ideator`, `reversa-image-prompt-json`, `reversa-inspector`, `reversa-migrate`, `reversa-modularize`, `reversa-n8n`, `reversa-new`, `reversa-optimize`, `reversa-paradigm-advisor`, `reversa-plan`, `reversa-pre-spec`, `reversa-pricing`, `reversa-pricing-advisor`, `reversa-pricing-estimate`, `reversa-pricing-product`, `reversa-pricing-profile`, `reversa-pricing-research`, `reversa-pricing-size`, `reversa-principles`, `reversa-prune`, `reversa-quality`, `reversa-reconstructor`, `reversa-refactor`, `reversa-requirements`, `reversa-researcher`, `reversa-restructure`, `reversa-resume`, `reversa-reviewer`, `reversa-scout`, `reversa-screen-translator`, `reversa-selo-generativo`, `reversa-simplify`, `reversa-spec-sdd`, `reversa-standardize`, `reversa-strategist`, `reversa-sync`, `reversa-to-do`, `reversa-visor`, `reversa-writer`. Cópias de terceiros sob licença MIT/Apache conforme cada pacote; assimilação futura depende de revisão e P-8.

## Regras de manutenção
1. Cada skill cita só caminhos que existem. Antes de salvar, confira com `python3 redesign/painel_operacional/qualidade_llm.py` (aviso "caminho citado inexistente").
2. Uma skill por assunto. Se um assunto já tem skill, acrescente à skill, não crie outra.
3. Formato universal: Markdown simples, frontmatter só com `name` e `description`, sem arquivo específico de um modelo (por exemplo, um `openai.yaml` específico de um modelo).
4. Mudança em skill do repositório passa por proposta P-8 (é arquivo versionado).
5. Medido vai com comando e data. Sem medição, a frase começa com "não medido".
