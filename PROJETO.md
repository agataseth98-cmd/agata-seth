# PROJETO — Ágata (implementação atual)

Estado deste projeto, hoje. Trocável sem mexer nas REGRAS.

## O que é
Assistente pessoal do Orusoua, **local-first e grátis por padrão**, construída **sobre o Hermes Agent** (Nous Research) como motor. Ágata = Hermes + governança canônica (SOUL/REGRAS/PROJETO/DIÁRIO) + memória em formato aberto.

**Propósito de uso:** acessível de múltiplos dispositivos e redes via interface web (Open WebUI), sobre acesso privado seguro (VPN Tailscale), **sem exposição à internet pública**. O terminal e o resto da TUI seguem disponíveis na própria Máquina.

## Máquinas
- **Predator** (master — CachyOS, i7-13650HX, 40GB, RTX 4060 8GB): Hermes, Ollama, memória, git, Obsidian, interface web.
- **Orusoua** (réplica — Windows 11, sem GPU): Hermes em leitura/failover, sync. *(planejado)*

## Motor: Hermes Agent
Cobre identidade (SOUL), memória (SQLite+FTS), skills auto-criadas, roteamento de provedores + fallback, sandbox de execução, voz e browser. Substitui todo o código bespoke antigo (nada de MCP server/roteador/OpenClaw caseiros).

## Cérebro (grátis)
- Principal: **gemini-2.5-flash** via Google API direta (grátis, rápido, tool-calling confiável).
- Fallback: **qwen2.5-14b-64k** local via Ollama (grátis, privado, sem cota; lento ~5min/tool via offload CPU; contexto 64k por extrapolação de num_ctx). Faz tool-calling — confirmado.
- Último recurso manual: **llama3.1:8b** local (responde texto, sem tool-calling). Fora da cadeia.
- Requisito do Hermes: contexto ≥64k (fixo, hardcoded). Modelos <64k nativo não servem.
- Skills: 12 ativas, 56 desabilitadas. Tools: 12 de 18 (payload ~12.6k tokens).

## Memória (formato aberto)
- SOUL/REGRAS/PROJETO/DIÁRIO em Markdown, em `~/agata` (repo git + cofre Obsidian na mesma pasta).
- Memória nativa do Hermes (`MEMORY.md`/`USER.md`) symlinkada em `~/agata/memoria/`.
- Hidratação: `.hermes.md` (gerado por hook) injeta REGRAS + PROJETO + últimas 30 linhas do DIÁRIO no system prompt — os dois cérebros leem as mesmas fontes.

## Interface
- **Hermes CLI/TUI** — na própria Máquina.
- **Open WebUI** — interface de chat no navegador, apontada pro `api_server` do Hermes (`/v1`, porta 8642). É a Ágata inteira (tools rodam no lado do Hermes), não um LLM pelado.

## Segurança (linhas vermelhas)
- Serviços em `127.0.0.1`; execução sempre em sandbox; scanning de injection + filtragem de credenciais (nativos do Hermes); produção só com aprovação do Orusoua.
- Segredos (chaves/tokens) **só** em `~/.hermes/.env`, nunca no repo git.
- **O `api_server` do Hermes executa comandos de terminal.** NUNCA expô-lo (nem o Open WebUI que o consome) na internet pública nem em `0.0.0.0` em rede não confiável. Acesso remoto **só** via VPN privada (Tailscale) + auth em duas camadas (chave do Hermes + login no Open WebUI). Sem exceção — é a única superfície do projeto que pode causar dano real.

## Diagnóstico
`hermes doctor` / `hermes status`. O comando de prontidão da Ágata é definido no SOUL.

## Fases
0 base ✅ · 1 identidade+memória ✅ · 2 cérebro/routing ✅ · 3 aprendizado ✅ · 4 voz (próxima) · 5 mãos · 6 skills · 7 redundância · 8 mercado. Detalhe em `PLANO_AGATA_v1.3.md`.
