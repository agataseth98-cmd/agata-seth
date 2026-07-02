# PROJETO — Ágata (implementação atual)

Estado deste projeto, hoje. Trocável sem mexer nas REGRAS.

## O que é
Assistente pessoal do Orusoua, **local-first e grátis por padrão**, construída **sobre o Hermes Agent** (Nous Research) como motor. Ágata = Hermes + governança canônica (SOUL/REGRAS/PROJETO/DIÁRIO) + memória em formato aberto.

## Máquinas
- **Predator** (master — CachyOS, i7-13650HX, 40GB, RTX 4060 8GB): Hermes, Ollama, memória, git, Obsidian.
- **Orusoua** (réplica — Windows 11, sem GPU): Hermes em leitura/failover, sync.

## Motor: Hermes Agent
Cobre identidade (SOUL), memória (SQLite+FTS), skills auto-criadas, roteamento de provedores + fallback, sandbox de execução, voz e browser. Substitui todo o código bespoke antigo (nada de MCP server/roteador/OpenClaw caseiros).

## Cérebro (grátis a médio prazo)
- Principal: **gpt-4o-mini** via OpenRouter (pago, ~centavos/dia — único com tool-calling confiável hoje). Alvo: migrar pra modelo :free quando disponível.
- Fallback 1: **gpt-oss-120b:free** (OpenRouter, grátis, tool-calling).
- Fallback 2: **llama3.1:8b** local via Ollama (grátis, sem tool-calling — modo degradado).
- Skills builtin do Hermes: desabilitadas (68→0, prompt -42%).

## Memória (formato aberto)
- SOUL/REGRAS/PROJETO/DIÁRIO em Markdown, em `~/agata` (repo git + cofre Obsidian na mesma pasta).
- Fatos/hábitos: memória curada do Hermes + SQLite/FTS. Migrar os fatos reais do protótipo antigo (`_arquivo_agata_il/memoria/semantic.json`).
- Hidratação seletiva: injeta SOUL + resumo de estado + fatos recuperados, nunca o DIÁRIO inteiro.

## Segurança (linha vermelha)
Serviços em `127.0.0.1`; execução sempre em sandbox; scanning de injection + filtragem de credenciais (nativos do Hermes); produção só com aprovação do Orusoua.

## Interface
Hermes CLI/TUI; Open WebUI via adaptador API Server do Hermes (opcional).

## Diagnóstico
`hermes doctor` / `hermes status`. O comando de prontidão da Ágata é definido no SOUL.

## Fases
0 base ✅ · 1 identidade+memória ✅ · 2 cérebro/routing ✅ · 3 aprendizado ✅ · 4 voz (próxima) · 5 mãos · 6 skills · 7 redundância · 8 mercado. Detalhe em `PLANO_AGATA_v1.3.md`.
