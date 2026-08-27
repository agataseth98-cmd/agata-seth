> **ARQUIVADO 27/08/2026 (MEMÓRIAS (288)).** Snapshot de jul/2026, hoje **desatualizado em quase tudo** (dizia Gemini principal, qwen2.5-14b fallback, Hermes 0.17, "30 linhas do DIÁRIO", "6 regras", SOUL como identidade — nada disso vale). O estado atual está em PROJETO.md + ONDE_ESTAMOS.md + PROMPT_CARREGAMENTO.md. Mantido só por historicidade.

# ESTADO — Ágata Seth (snapshot para o Conselho)

**Data:** 2026-07-03 · **Autor:** Claude Opus 4.8 (condução da implementação com o Orusoua)
**Propósito:** dar a qualquer IC do Conselho o estado real do sistema em uma leitura, sem precisar percorrer o DIÁRIO inteiro. Fonte da verdade continua sendo a Máquina (`~/agata` na Predator) + o DIÁRIO.

---

## O que a Ágata é hoje
Assistente pessoal do Orusoua, construída **sobre o Hermes Agent 0.17.0** (Nous Research) como motor. Identidade, regras e história vivem em arquivos abertos; o modelo é intercambiável. Fases 0–3 concluídas. Operacional no terminal (TUI) e na web (Open WebUI, só localhost).

## Motor e cérebro
- **Motor:** Hermes Agent — identidade (SOUL), memória, tools, execução em sandbox, cron, fallback de provedores.
- **Cérebro principal:** `gemini-2.5-flash` (Google API direta, grátis). ~20 req/dia no free tier — esgota em dias de teste pesado, reseta diariamente.
- **Fallback:** `qwen2.5-14b-64k` local (Ollama, extrapolação de num_ctx pra 64k). Faz tool-calling. Lento (~5 min/tool via offload CPU). Grátis, privado, sem cota.
- **Último recurso:** `llama3.1:8b` local (responde texto, sem tool-calling). Fora da cadeia.
- **Barreira dura:** Hermes exige contexto ≥64k (constante hardcoded). Modelos <64k nativo não servem sem extrapolação/YaRN.

## Memória (uma só, formato aberto)
- `SOUL.md` (identidade), `REGRAS.md` (6 regras), `PROJETO.md` (estado), `DIÁRIO.md` (história append-only) — em `~/agata`, versionados em git, espelhados no Obsidian.
- Memória nativa do Hermes (`MEMORY.md`/`USER.md`) symlinkada em `~/agata/memoria/`.
- Hidratação: hook pre-commit gera `.hermes.md` (REGRAS + PROJETO + últimas 30 linhas do DIÁRIO) — injetado no system prompt. O modelo recebe o fim do DIÁRIO pronto, sem tool-call, sem alucinar.

## Interfaces
- **TUI:** `hermes` no terminal.
- **Web:** Open WebUI → `api_server` do Hermes (`/v1`, `127.0.0.1:8642`, com auth). Tools rodam no lado do Hermes; a web é a face.

## Skills e tools
- Skills: 12 ativas (obsidian, google-workspace, ocr, maps, computer-use, youtube, plan, systematic-debugging, github×4), 56 desabilitadas.
- Tools: 12 de 18 (payload ~12.6k tokens na TUI, ~16.6k via api_server).

## Segurança (linhas vermelhas)
- Segredos só em `~/.hermes/`, nunca no repo git. Duas chaves vazaram em terminal durante a montagem (config set ecoa valor; API key colada em chat) — as duas foram rotacionadas na hora.
- `api_server` executa terminal → nunca exposto na internet nem em `0.0.0.0` em rede não confiável. Acesso remoto só via VPN (Tailscale) + auth dupla. Hoje: só localhost.

## O que funciona (verificado na Máquina)
`carregar` (formato de prontidão, data correta), tool-calling (Gemini e qwen), memória injetada, git+GitHub sync, auto-atualização (ICs carregam canônicos via URL raw), Open WebUI ligado (localhost).

## O que falta / pendências
- Teste `carregar` pela web com o Gemini fora de cota (só faltou a cota voltar).
- Voz (Fase 4) — ver DOSSIE_COEXISTENCIA.md (decidido: no Open WebUI, não no Hermes).
- Tailscale + HTTPS para acesso remoto multi-dispositivo.
- Estratégia de coexistência Hermes ↔ Open WebUI — em auditoria (DOSSIE_COEXISTENCIA.md).

## Decisões travadas (não reabrir sem o Humano)
Hermes como motor · 6 regras · gemini-2.5-flash principal + qwen2.5-14b-64k fallback · memória única symlinkada · nomes Humano/Modelo/Máquina · REGRAS/PROJETO/DIÁRIO/SOUL canônicos · Open WebUI = frontend, Hermes = backend único (Opção A) · modelos locais <64k encerrados.

## Aprendizados de método (valem pra todo o Conselho)
1. **A Máquina é o árbitro.** Nenhum fato se afirma sem verificar no disco. Dois modelos já brigaram por cópias dessincronizadas do DIÁRIO — o `grep` decidiu.
2. **Não descartar por raciocínio, só por teste.** Projetar falha de um modelo em outro sem medir já custou caro.
3. **Injeção determinística > instruir o modelo.** Toda vez que dependemos do modelo "lembrar de ler", falhou; hook que injeta o conteúdo, funcionou.
4. **Documentação de LLM inventa nomes plausíveis** (qwen3.6, glm-4:9b não existem). Só o `pull` na Máquina prova.
5. **Regra 2 vale pro auditor.** Citar fonte sem mostrá-la é o mesmo vício de inventar.
