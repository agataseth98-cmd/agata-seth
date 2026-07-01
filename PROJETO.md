# PROJETO — Ágata (implementação atual)

Estado deste projeto, hoje. Trocável sem mexer nas REGRAS.

## O que é
Assistente pessoal do Orusoua, **local-first e grátis por padrão**, construída **sobre o Hermes Agent** (Nous Research) como motor. Ágata = Hermes + governança canônica (SOUL/REGRAS/PROJETO/DIÁRIO) + memória em formato aberto.

## Máquinas
- **Predator** (master — CachyOS, i7-13650HX, 40GB, RTX 4060 8GB): Hermes, Ollama, memória, git, Obsidian.
- **Orusoua** (réplica — Windows 11, sem GPU): Hermes em leitura/failover, sync.

## Motor: Hermes Agent
Cobre identidade (SOUL), memória (SQLite+FTS), skills auto-criadas, roteamento de provedores + fallback, sandbox de execução, voz e browser. Substitui todo o código bespoke antigo (nada de MCP server/roteador/OpenClaw caseiros).

## Cérebro (grátis-primeiro em teoria; pago por decisão explícita na prática)
- Principal: **`openai/gpt-4o-mini`** (pago — custo autorizado pelo Orusoua na Fase 2), via OpenRouter `https://openrouter.ai/api/v1`.
- Fallback: `openai/gpt-oss-120b:free` (OpenRouter) → **`llama3.1:8b`** local (Ollama `http://localhost:11434/v1`, `num_ctx 65536`).
- Motivo da troca: modelos locais e `:free` não fizeram tool-calling confiável nos testes da Fase 2 (detalhe da causa raiz no DIÁRIO).
- Auxiliares (classificação, tarefas leves): modelos pequenos locais (qwen2.5:7b, llama3.2:3b, gemma2:2b...).

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
0 base (em curso) · 1 identidade+memória · 2 cérebro/routing · 3 aprendizado · 4 voz · 5 mãos · 6 skills · 7 redundância · 8 mercado. Detalhe em `PLANO_AGATA_v1.3.md`.
