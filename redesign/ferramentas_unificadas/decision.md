# Decisões: ferramentas-unificadas-26-11

Escrito pelo especificador a partir do que o coordenador repassou. Não é resposta de entrevista do Humano. Se o Humano tiver respostas próprias, elas substituem D1–D6.

## Recebido do Humano (26/11/2026, via coordenador)
- H1. Todos os modelos, de qualquer origem, acessam as mesmas capacidades.
- H2. Skill de arranque carregada no início da sessão.
- H3. Tudo que um modelo pode usar fica disponível para os outros.
- H4. Fonte única de skills, memória e cache do Conselho para todos.

## Decidido pelo coordenador (o Humano pode reverter)
- D1. Propagação mista. Overlay `~/agata-local/ferramentas.yml`, fora do repo. Canônico `config/ferramentas/*.yml`, sob P-8. Sync lê canônico ∪ overlay, com overlay sobrepondo por nome. `promover.py` gera o diff para o canônico. Motivo: H3 sem fricção; H4 com fonte única.
- D2. Lote 1: Claude Code, Codex e OpenCode. Gemini CLI no lote 2.
- D3. Lote 1: MCP, skills (ponteiro) e subagentes. Hooks e slash commands no lote 2.
- D4. Skill `agata-arranque` em `.agents/skills/agata-arranque/SKILL.md`, por diff. Conteúdo: spec, seção 4.
- D5. Compatibilidade por merge, nunca overwrite.
- D6. Backup antes de escrever; `reverter.py <timestamp>`.

## Ajustes do especificador (precisam de aprovação)
- A1. MCP pelos comandos nativos (`claude mcp add -s user`, `codex mcp add`, `opencode mcp add`), não por edição de JSON ou TOML. Medido na ajuda. Motivo: `tomllib` só lê; os comandos preservam o que não nomeiam (D5). Não medido: `opencode mcp add` sem prompt.
- A2. Manifest `~/.local/share/agata/ferramentas/gerenciado.json`, com o que o sync criou. Sem ele não há remoção segura (D5). Estado novo.
- A3. Reversão pelo manifest. Arquivo inteiro só volta se o hash for o que o sync deixou. Motivo: Claude Code reescreve `~/.claude.json` na sessão.
- A4. Backups em `~/.local/share/agata/ferramentas/backup/<ts>/`, permissão 600, e não `~/.claude.json.bak-<ts>` na raiz da home (ajusta D6). Motivo: o arquivo tem o segredo de `github-pat`.

## Conflitos a decidir antes da implementação
- C1. D1 (overlay sem assinatura) contra AGENTS.md, "Assinatura por tipo de mudança": ferramenta é "sistema", com assinatura; "na dúvida, é sistema". Padrão desta spec: `instalar.py` pede o "sim" do Humano a cada instalação. Dispensar a assinatura exige diff em AGENTS.md (P-8), decisão do Humano.
- C2. D3 (hooks fora do lote 1) contra H2 e D4 (skill lida pelo SessionStart). Medido: SessionStart existe em `~/.claude/settings.json` e `~/.codex/hooks.json`; OpenCode não medido. Opções: incluir SessionStart de Claude e Codex no lote 1 (recomendado, por ser medido), ou aceitar a lacuna L1.

## Decisões do Conselho (26/11/2026 14:15, resolvem C1/C2 e ajustes)

Codex ocupado. Parecer pedido ao melhor modelo gratuito local (qwen3.5:9b via Ollama) + orquestração Claude Code. Anotado no cache_conselho em n=914, h=2de753168055.

- **R1 (C1).** Overlay sem assinatura = **(a) overlay + confirmação interativa do Humano em cada install**. `instalar.py` pede "sim" no terminal antes de gravar. Dispensar a confirmação exige diff em AGENTS.md num lote futuro.
- **R2 (C2).** SessionStart entra no lote 1 em **Claude e Codex** (medidos). OpenCode fica como L1 (lacuna documentada, lote 2).
- **R3 (ajustes A1-A4).** Aprovados. MCP via `claude/codex/opencode mcp add`. Manifest `~/.local/share/agata/ferramentas/gerenciado.json`. Reversão por manifest com hash guard. Backups em `~/.local/share/agata/ferramentas/backup/<ts>/` permissão 600.
- **R4 (/usage item 1).** claude-in-chrome. **A decisão original (B) não funciona:** documentação oficial (`code.claude.com/docs/en/permissions`, confirmada por teste externo Classmethod) diz que **deny sempre vence allow**; deny global bloqueia inclusive dentro do allow de projeto. Ressalva descoberta pelo `agata-dev` e confirmada pelo orquestrador via WebSearch. **Opções para o Humano decidir na assinatura:**
  - **E (recomendada)** — `permissions.ask` em `~/.claude/settings.json` (user, global) + `permissions.allow` em `~/agata/.claude/settings.json` (projeto). Fora de agata o Claude pergunta a cada chamada; dentro de agata passa sem perguntar.
  - **C** — desinstalar/desativar a extensão Chrome "Claude Code Browser". Elimina o custo em toda sessão; perde a capacidade.
  - **B (original, não funciona)** — mantida só como registro. Se o Humano preferir, o par de arquivos fica como está mas sem efeito prático.
  
  O lote 1 entrega: (a) o script `aplicar_denylist_browser.py` (funciona para E trocando `deny` por `ask` ou para C numa variante que remova o plugin), (b) o `allow` já aplicado em `.claude/settings.json` do projeto. A edição em `~/.claude/settings.json` user-level fica **para o Humano aplicar manualmente** depois de escolher entre E/C (o script dá o comando pronto).
- **R5 (/usage item 2).** haiku-5-5 mantém `effortLevel: xhigh`. Qualidade de revisor/arquiteto/dev medida nesta sessão justifica o custo.

## Escopo do lote 2 (declarado agora, não implementado)

Diretriz do Humano 26/11 14:10: "todos os modelos na Predator usando a pasta do sistema agata devem ter todos os seus arquivos no mesmo lugar refletindo alterações mútuas". Parcialmente atendida pelo lote 1 (fonte única de MCP, skills ponteiro, hook SessionStart, skill agata-arranque). Resta no lote 2:

- **L2-A.** Symlinks dos CLIs para pastas canônicas: `~/.codex/skills → ~/agata/.agents/skills/` (ou flag de config apontando); OpenCode idem.
- **L2-B.** Gerador de `~/.codex/rules/default.rules` a partir de `AGENTS.md` (fonte única de regras).
- **L2-C.** Migração de `~/.claude/hooks/herdr-agent-state.sh` para `~/agata/scripts/hooks/` + symlink.
- **L2-D.** Migração de `~/.codex/automations/` para `~/agata/.codex/automations/` + symlink.
- **L2-E.** OpenCode: SessionStart equivalente (não medido), skill de arranque, mcp add sem prompt.
- **L2-F.** Gemini CLI: binário ausente da PATH, retorna quando reinstalado.
- **L2-G.** Subagentes neutros em `.agents/perfis/`, gerador por CLI.
- **L2-H.** Slash commands onde a CLI suporta.

## Escopo da escrita
- Só documentos, nesta pasta. Fonte única e skill não foram criadas: entram pelo diff.
- `REGRAS.md`, `PROTOCOLOS.md`, `MEMÓRIAS.md` e `PROJETO.md` não foram tocados.

## Lacunas e riscos (declarados no lote 1, não implementados)
Achados da revisão independente que não entram neste lote. Lote 2 trata.
- **L7. Cobertura do AC-13 restrita.** A varredura de segredo cobre valor de env em overlay, canônico, manifest, log e saída do sync. Não varre `comando`, `motivo` e `descricao` como texto livre, nem `args` além da heurística de padrões (`token=`, `ghp_`, `sk-` etc.). Um segredo colado em um desses campos passa. Lote 2: varredura desses campos e recusa de valor colado em texto.
- **L8. Retenção de backups.** `<base>/backup/<ts>/` guarda cópia 600 dos arquivos nativos, com valores de env. Não há limite de quantidade nem de idade, e cada rodada com escrita cria uma pasta. Lote 2: política de retenção, com o que sair indo para `~/agata-arquivo/` por mv (nunca rm).
- **L9. Manifest sem caminho de backup e sem guarda de hash na adoção.** O manifest guarda hash e ts, mas não o caminho do backup (o registro fica em `backup/<ts>/sincronia.json`). A guarda de hash cobre entrada já gerenciada (`alterado_depois`). A adoção com `adotar: true` substitui o nativo sem conferir hash: quem lê e escreve (corrida com a CLI aberta, L5) não confere se o valor mudou entre as duas operações. Lote 2: caminho do backup no manifest e conferência de hash também na adoção.
