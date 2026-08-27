> **ARQUIVADO 27/08/2026 (MEMÓRIAS (288)).** Documento de jul/2026, superado pelo canon atual (REGRAS.md / PROJETO.md / MEMÓRIAS.md / ONDE_ESTAMOS.md). Mantido por historicidade — não é fonte de estado. A decisão registrada aqui (Opção A) vive em PROJETO.md, "Ambiente Operacional" / "Serviços".

# DOSSIÊ — Coexistência Hermes ↔ Open WebUI (para auditoria do Conselho)

**Data:** 2026-07-03 · **Autor:** Claude Opus 4.8 · **Base:** síntese do DeepSeek (t=1) + auditoria do Claude
**Status:** PROPOSTA — aguarda auditoria do Conselho antes da implementação
**Decisão do Humano:** Opção A (frontend/backend), com a correção de voz abaixo.

---

## 1. Princípio (Opção A)
**Hermes é o cérebro (backend único). Open WebUI é a janela (frontend).**
Toda lógica de agente — memória, tools, execução, cron, MCP, identidade — fica no Hermes. O Open WebUI serve à interação humana. **Não se duplica função:** cada recurso mora numa casa só. Isso não desliga capacidades — distribui cada uma para quem a faz melhor.

Motivo (do próprio DIÁRIO): memória dupla foi o que corrompeu o sistema no início. Dois sistemas escrevendo em paralelo violam a regra "uma memória só". Ativar "tudo dos dois" não é aproveitar o melhor — é criar race conditions.

## 2. Divisão de responsabilidades

| Função | Casa | Por quê |
|---|---|---|
| Cérebro, memória, tools, execução, cron, MCP, identidade | **Hermes** | motor com estado; memória tem que ser única |
| Interface, chat visual, histórico visual, multi-usuário, feedback, exportação | **Open WebUI** | o Hermes não tem nada disso |
| **RAG de documentos estáticos** (manuais, PDFs, specs) | **Open WebUI** | o Hermes **não tem RAG** — ganho puro, sem sobreposição |
| **Voz (STT + TTS)** | **Open WebUI** | *ver §3 — correção* |
| Web search, image gen | **Hermes** (tools) | um executor só, sem busca duplicada |

## 3. Correção da voz (reverificada nesta auditoria)
O plano anterior (Fase 4) previa voz **no Hermes** (faster-whisper + Kokoro pf_dora). **A auditoria corrige: voz pertence ao Open WebUI (borda/cliente), não ao Hermes.** Três razões concretas:

1. **O microfone está no cliente.** Numa assistente web/multi-dispositivo, a voz tem que ser capturada onde o humano está (navegador do celular, do laptop) — não no microfone da Predator. O modo de voz do Hermes (CLI/Discord) captura o mic da própria Máquina, inútil remotamente.
2. **STT/TTS é I/O puro, não uma tool conflitante.** Converte áudio↔texto *antes* e *depois* da chamada ao Hermes. Não toca memória, não chama tools, não cria conflito de estado. Logo, não viola a regra "um executor, uma memória" da Opção A. É seguro na borda.
3. **A voz desejada (Kokoro `pf_dora`) funciona no Open WebUI.** O Open WebUI suporta TTS via Kokoro (contêiner Kokoro-FastAPI, endpoint compatível com OpenAI) e STT via Whisper local — ambos configuráveis, e o Kokoro roda em CPU (não disputa VRAM com o modelo). Mantém-se a voz que o projeto já queria (BLOCO 39), disponível em todo dispositivo que abrir o navegador.

**Pipeline resultante:** mic do navegador → STT Whisper (Open WebUI) → texto → Hermes api_server (Gemini/qwen, com tools/memória/SOUL) → texto → TTS Kokoro pf_dora (Open WebUI) → alto-falante do navegador.

**Dependência registrada:** o navegador só libera o microfone em `localhost` (http) ou via **HTTPS**. Voz no laptop local: funciona já. Voz do celular via Tailscale: exige HTTPS (Tailscale fornece cert). Ou seja, voz remota depende do passo Tailscale.

`lacuna:` confirmar que `pf_dora` está no conjunto de vozes do contêiner Kokoro-FastAPI (algumas builds vêm só com vozes em inglês). Se não vier, usar o bundle multilíngue do Kokoro-82M ou apontar pro modelo com as vozes pt.

## 4. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Memória dupla | Desabilitar "User Memory"/memory do Open WebUI. Só o Hermes lembra. |
| Tool-calling duplo | Desabilitar functions/tools nativas do Open WebUI. Ele só encaminha `tool_calls`; o Hermes executa. |
| System prompt sobrescrito | System prompt vazio no Open WebUI — a identidade vem do SOUL via Hermes. |
| Web search duplicada | Desabilitar web search do Open WebUI; busca só via tool do Hermes. |
| MCP duplo / race no git | MCP só no Hermes. Open WebUI nunca conecta MCP. |
| **RAG estoura o fallback** | RAG injeta documento no prompt. Já sem RAG o payload web é ~16.6k; com documento passa dos 32k nativos do qwen e entra em extrapolação. **RAG só é seguro nas sessões servidas pelo Gemini (janela grande). Se cair no qwen, limitar/desligar RAG.** |
| Estouro de VRAM | Kokoro TTS e Whisper STT em CPU; sem RAG local pesado (embeddings leves). GPU fica pro modelo. |
| Histórico dessincronizado | Fonte da verdade = Hermes. Open WebUI só exibe o que vem pela API. |

## 5. Plano de implementação (após auditoria)

**Já feito:** api_server ligado (auth, localhost); Open WebUI conectado ao Hermes; cwd corrigido (DIÁRIO chega via web).

**A fazer (config no Open WebUI — Admin Settings, maior parte manual no navegador):**
1. Desabilitar no Open WebUI: memory/User Facts, tools/functions nativas, web search, image gen, system prompts personalizados.
2. Manter no Open WebUI: chat, histórico visual, RAG (documentos estáticos), multi-usuário (se necessário).
3. **Voz:** subir contêiner Kokoro-FastAPI (CPU); em Admin → Audio, TTS = OpenAI-compatible apontando pro Kokoro, voz `pf_dora`; STT = Whisper local (small/base, CPU). Testar em `localhost` (http) primeiro.
4. **Trava de RAG:** documentar/forçar que sessões com RAG usem o Gemini; alerta se cair no qwen com documento grande.
5. Testar `carregar` + uma sessão com voz + uma com RAG, cada uma verificada na Máquina.

## 6. Pendências para o Conselho auditar
- A divisão da §2 está correta, ou algum recurso deveria trocar de casa?
- A correção da voz (Open WebUI, não Hermes) procede?
- A trava de RAG (só no Gemini) é suficiente, ou o RAG deveria ficar desligado até haver um cérebro de janela grande garantido?
- Algum risco da §4 sem mitigação adequada?
- Multi-usuário: entra agora ou só quando houver segundo usuário real?

---
**Recomendação do Claude:** aprovar a Opção A com a correção de voz. É a arquitetura que deixa **todos os recursos disponíveis** (nada fica de fora) sem duplicar memória ou execução — o "melhor de cada" de verdade, não "tudo dos dois ligado".
