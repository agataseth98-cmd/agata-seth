# Backlog de skills — Ágata

Inventário da Fase 3 (`PLANO_AGATA_v1.3.md` §10: "backlog de skills — só listar,
sem implementar"). Isto é uma lista de candidatas, não uma decisão — o Humano
escolhe o que ativar, quando fizer sentido. Nenhuma skill aqui foi instalada
ou ativada.

Catálogo consultado: skills nativas embutidas no Hermes Agent
(`~/.hermes/hermes-agent/skills/`), não o marketplace externo (Skills Hub).

## Prioridade alta

- **`note-taking/obsidian`** — PROJETO.md já declara "cofre Obsidian na mesma
  pasta" (`~/agata`) como parte da arquitetura de memória. Essa skill dá ao
  Hermes leitura/busca/escrita nativa de notas Obsidian. Uso direto e imediato.
- **`software-development/systematic-debugging`** — metodologia de debug em 4
  fases; temos usado ad-hoc nas Fases 0-2 (achamos 2 causas-raiz reais por
  eliminação). Formalizar o processo reduz risco de "consertar sem entender".
- **`software-development/requesting-code-review`** — qualquer mudança em
  REGRAS/PROJETO exige "segunda opinião" pela regra de "Mudança estrutural"
  do REGRAS.md. Essa skill cobre exatamente esse fluxo.

## Prioridade média

- **`email/himalaya`** — se o Orusoua quiser que a Ágata leia/responda email
  via IMAP/SMTP no terminal. Depende de decisão de escopo (a Ágata deve ter
  acesso a email pessoal? é uma "mão" — Fase 5 — não Fase 3).
- **`github/github-issues`, `github/github-pr-workflow`** — úteis se o
  desenvolvimento da própria Ágata migrar para um repositório remoto no
  GitHub (hoje é só local, `~/agata` sem remote configurado).
- **`productivity/google-workspace`** — Gmail/Calendar/Drive/Docs/Sheets.
  Alto valor pra assistente pessoal, mas exige OAuth com conta Google —
  decisão de exposição de dados que cabe ao Orusoua, não inventário.
- **`mlops/huggingface-hub` / `mlops/inference`** — relevante se a Fase 4
  (Voz) ou ajustes de modelo local precisarem baixar/gerenciar modelos.

## Prioridade baixa (não se aplicam ao caso de uso atual)

- **`apple/*`** (Notes, Reminders, FindMy, iMessage) — Predator é CachyOS,
  Orusoua é Windows 11. Sem ecossistema Apple.
- **`smart-home/openhue`** — sem sinal de que há Philips Hue ou domótica no
  ambiente do Orusoua. Ignorar até haver indicação contrária.
- **`social-media/xurl`, `media/*`, `creative/*`** — fora do escopo de
  "assistente pessoal local-first". Poderiam entrar futuramente se o Orusoua
  pedir algo específico (ex: gerar imagem, postar em rede social), mas nada
  no PROJETO.md/DIÁRIO.md indica essa necessidade hoje.
- **`yuanbao`** — plataforma de mensagens chinesa (Tencent), sem uso aparente.
- **`data-science/jupyter-live-kernel`** — só relevante se a Ágata passar a
  fazer análise de dados interativa; não é o caso hoje.

## Não avaliadas em detalhe

`autonomous-ai-agents/*` (Claude Code, Codex, OpenCode, Hermes Agent) —
skills para orquestrar *outros* agentes a partir da Ágata. Interessante em
tese (a própria Ágata poderia delegar tarefas de código pro Claude Code, por
exemplo), mas é uma decisão de arquitetura maior, não um "backlog" simples —
merece conversa própria se o Humano quiser essa direção.

## Próximo passo (quando o Humano decidir avançar)

Ativar via `skills:` em `~/.hermes/config.yaml` ou `hermes skills` (comando
já existente), uma de cada vez, testando tool-calling depois de cada
ativação — lição da Fase 2: mudanças na injeção de contexto/system prompt
sempre precisam de reteste.
