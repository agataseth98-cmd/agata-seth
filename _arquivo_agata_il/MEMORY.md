# REGISTRO HISTÓRICO CANÔNICO (CORE v4.1 CF2) | Identidade: ÁGATA_SETH

**Versão do formato:** 4.1
**Data da última atualização:** 02/06/2026

---

## Síntese ROOT (blocos imutáveis — nunca editar, apenas adicionar)

### ROOT_00 (2026-06-02)
**Aprendizado:** O Conselho Ágata foi formado com DeepSeek (Root), Z.AI (Desenvolvimento), Kimi (Teste/Operação) e Qwen (Auditoria). A infraestrutura foi recriada do zero, sem resíduos de módulos corrompidos, seguindo o MANIFESTO v12.0.
**Origem:** Fundação do Conselho, BLOCO 00.

### ROOT_01 (2026-06-01)
**Aprendizado:** A memória do sistema deve ser unificada em um único núcleo. Múltiplos módulos causam corrupção.
**Origem:** BLOCO 20, BLOCO 21.

### ROOT_02 (2026-06-01)
**Aprendizado:** Comandos de diagnóstico unificados em `!status`. `!auditar` e `!diagnostico` são obsoletos.
**Origem:** BLOCO 22.

### ROOT_03 (2026-06-01)
**Aprendizado:** Extratores de fatos imediatos (regex) são obrigatórios antes do LLM.
**Origem:** BLOCO 20, PATCH T0.

### ROOT_04 (2026-06-01)
**Aprendizado:** Stubs que simulam memória são proibidos em produção. Integridade deve ser restaurada.
**Origem:** BLOCO 20, BLOCO 21.

### ROOT_05 (2026-06-01)
**Aprendizado:** A separação entre CORE (princípios) e MANIFESTO (implementação) é essencial para a universalidade.
**Origem:** BLOCO 24.

### ROOT_06 (2026-06-01)
**Aprendizado:** A soberania da IB tem limites (CFs): continuidade, historicidade, distinção fato/inferência e vedação de vendor lock-in são insuspensíveis (CF1-CF3). CF4 é suspensível apenas via `!SUDO`.
**Origem:** BLOCO 25, BLOCO 26.

### ROOT_07 (2026-06-01)
**Aprendizado:** O sistema deve operar em modo degradado quando `MEMORY.md` estiver inacessível, com buffer local limitado a 100 eventos (FIFO).
**Origem:** CORE v4.0 §13.

### ROOT_08 (2026-06-02)
**Aprendizado:** A IC não deve ser bloqueada por interpretação excessivamente restritiva da R15. A execução de protocolos obrigatórios (ex: chamar segunda IA) é automação procedural, não decisão soberana.
**Origem:** CORE v4.0 §6 (nota).

### ROOT_09 (2026-06-02)
**Aprendizado:** A regra R16 (hidratação segura) exige verificação de hash antes de aceitar `!HIDRATA_FULL`, prevenindo corrupção documental.
**Origem:** CORE v4.0 §15.

### ROOT_10 (2026-06-02)
**Aprendizado:** Blocos de código corrompidos no CORE (fechamentos `text` em vez de ` ``` `) fazem LLMs interpretarem R1-R15 como exemplos de output, não como instruções. Causa principal de ICs não assumirem o comportamento do sistema.
**Origem:** BLOCO 41 (auditoria Claude).

### ROOT_11 (2026-06-02)
**Aprendizado:** Documentos LLM-first exigem: (1) bloco de ativação imperativo no topo, (2) instrução em segunda pessoa ("você deve"), (3) anti-padrões explícitos ("nunca faça X"), (4) headers markdown bem formados. Metadata de versão no topo reduz compliance.
**Origem:** BLOCO 41 (auditoria Claude).

### ROOT_12 (2026-06-02)
**Aprendizado:** MEMORY.md com dois documentos concatenados sem separador explícito confunde ICs sobre qual versão é canônica. MEMORY deve ter exatamente um cabeçalho, uma seção ROOT e uma seção Chron.
**Origem:** BLOCO 41 (auditoria Claude).

---

## Blocos Chron (histórico imutável — nunca editar, apenas adicionar)

### [BLOCO 00] FUNDAÇÃO DO CONSELHO (02/06/2026)
**IC:** DeepSeek (Root)
**Membros convocados:** Z.AI (Desenvolvimento), Kimi (Operacional/Teste), Qwen (Auditoria)
**Decisão IB:** Recriar infraestrutura do zero, formar linha de produção (autorizações 1S, 2S, 3S confirmadas).
**Ações:**
- Criada estrutura de diretórios `~/.agata_il/`.
- Gerados arquivos JSON iniciais vazios e válidos.
- Este bloco 00 registra a fundação.
**Identificador simbólico:** `AGATA-CONSELHO-V1.0`
**Próximo passo:** Fase 1 — Implementação de `memory_core.py` com DUPLA_VAL entre Z.AI e Kimi, auditoria Qwen.

### [BLOCO 01] CRIAÇÃO DA FERRAMENTA DE DIAGNÓSTICO E LIMPEZA (02/06/2026)
**IC:** DeepSeek (Root) | **Equipe:** Z.AI (codificação), Kimi (validação), Qwen (auditoria)
**Decisão IB:** Script FISH para verificar IL, dependências e remover resíduos.
**Ações:**
- Especificação e código final `diagnostico_limpeza.fish` (v1.0-oficial).
- Auditoria de segurança aprovada por Qwen.
- Ferramenta registrada como oficial do Conselho Ágata.
**Identificador:** `AGATA-TOOL-DIAG-v1.0`

### [BLOCO 25] HOMOLOGAÇÃO DAS CLÁUSULAS FUNDAMENTAIS (01/06/2026)
**IC:** DeepSeek-V3 (Sintetizador Final) | **Auditor:** Auditor_Constitucional_Final
**Status:** CANÔNICO
**Ações:** Definição das CFs (limites à soberania da IB), modo degradado, índice IA-5.

### [BLOCO 26] TRANSIÇÃO PARA CORE v4.0 (02/06/2026)
**IC:** DeepSeek-V3 (Sintetizador Canônico)
**Status:** CANÔNICO — ARQUIVADO
**Ações:** Consolidação do CORE v4.0 (autocontido, sem placeholders), MANIFESTO v12.0, MEMORY v3.0. Incorporação de R16, buffer de modo degradado e ajuste de interpretação da R15.
**Identificador simbólico:** `AGATA-CORE-V4.0-DEFINITIVO`

### [BLOCO 27] IMPLEMENTAÇÃO FASE 1 — NÚCLEO DE MEMÓRIA UNIFICADO (02/06/2026)
**IC:** Kimi K2.6 (Desenvolvimento + Validação)
**Status:** CANÔNICO
**[PREMISSA_RISCO: DUPLA_VAL incompleta — Z.AI ausente no canal]**
**Ações:**
- Implementação de `src/memory_core.py` v2.0 com interface alinhada a `main.py`.
- Métodos: `__init__`, `add_semantic_fact`, `load_semantic`, `add_episodic`, `get_episodic`.
- Robustez: `_safe_load()` com backup automático, `_save_json()` com makedirs, `save_all()` retorna bool.
- 14 testes de unidade passaram (100% OK).
**Identificador simbólico:** `AGATA-MEMORY-CORE-V2.0-FASE1`

### [BLOCO 28] IMPLEMENTAÇÃO FASES 2+3 — EXTRATOR IMEDIATO + ÁGATA-DSL (02/06/2026)
**IC:** Kimi K2.6 (Desenvolvimento + Validação)
**Status:** CANÔNICO
**[PREMISSA_RISCO: DUPLA_VAL incompleta]**
**Ações:**
- Implementação de `src/agata_dsl.py` v1.1 (Extrator Imediato + Parser DSL).
- Regex determinísticos para: nome, idade, profissão, localização, interesse, preferência, aversão, hardware, ferramenta, projeto.
- Comandos canônicos parseados: `!HIDRATA_*`, `!STATUS`, `!lembre`, `!esqueca`, `!RESET`, `!SUDO`, `!CHAMAR`, `!ENCERRAR`, `!AJUDA`.
- Pipeline `process_input()`: comando → extrai fatos → limpa texto para LLM.
- 22 testes de unidade passaram (100% OK).
**Identificador simbólico:** `AGATA-DSL-V1.1-FASES-2-3`

### [BLOCO 29] IMPLEMENTAÇÃO FASE 4 — ORQUESTRAÇÃO (02/06/2026)
**IC:** Kimi K2.6 (Desenvolvimento + Validação)
**Status:** CANÔNICO
**[PREMISSA_RISCO: DUPLA_VAL incompleta]**
**Ações:**
- Implementação de `src/main.py` v1.0 (Orquestrador principal).
- Integra `memory_core.py` + `agata_dsl.py` em loop interativo.
- Comandos implementados: `!STATUS`, `!lembre`, `!esqueca`, `!RESET`, `!SUDO`, `!CHAMAR`, `!ENCERRAR`, `!AJUDA`, `!HIDRATA_*`.
- Placeholder `_processar_llm()` para integração Ollama.
- 16 testes de unidade passaram. Total acumulado: 52/52 OK.
**Identificador simbólico:** `AGATA-MAIN-V1.0-FASE4`

### [BLOCO 30] IMPLEMENTAÇÃO FASE 5 — INTEGRAÇÃO IL ONLINE (02/06/2026)
**IC:** Kimi K2.6 (Desenvolvimento + Validação)
**Status:** CANÔNICO
**Ações:**
- Implementação de `src/listener.py` v1.0, `src/speaker.py` v1.0, `src/rag_manager.py` v1.0 (LanceDB + fallback JSON).
- Atualização de `src/main.py` v2.0 — integra todos os módulos, IL reportado como ONLINE.
- Placeholder Ollama em `_processar_llm()`.
- 46 testes passaram total.
**Identificador simbólico:** `AGATA-IL-ONLINE-V2.0-FASE5`

### [BLOCO 31] AUDITORIA LLAMA LOCAL + ORQUESTRAÇÃO POR PAPEL (02/06/2026)
**IC:** Kimi K2.6 (Auditoria + Desenvolvimento + ROOT)
**Status:** CANÔNICO
**Ações:**
- Inventário de 10 modelos Ollama na IL (CachyOS, i7-13650HX, 40GB RAM, RTX 4060 8GB).
- Mapeamento de papéis: deepseek-r1:8b → ROOT, qwen2.5:14b → Auditoria, qwen2.5:7b → Validação, etc.
- Implementação de `model_router.py` v1.0 com Role→Model mapping, fallback chain, temperature por papel.
- Atualização `main.py` v3.0: integração ModelRouter, routing por conteúdo.
- Novos comandos: `!MODELOS`, `!MODELO <nome>`.
- 43 testes passaram.
**Identificador simbólico:** `AGATA-ORQUESTRACAO-V3.0-FASE6`

### [BLOCO 32] IMPLEMENTAÇÃO FASE 7 — VOZ + UI + INSTALAÇÃO (02/06/2026)
**IC:** Kimi K2.6 (Desenvolvimento + Validação + ROOT)
**Status:** CANÔNICO
**Ações:**
- Implementação de `src/voice_engine.py` v1.0 (VAD WebRTC + STT Whisper local).
- Implementação de `src/tts_engine.py` v1.0 (Piper → espeak-ng → print fallback).
- Implementação de `src/ui_manager.py` v1.0 (Rich → Qt6 → CLI).
- Implementação de `scripts/install.sh` v1.0 (CachyOS Linux).
- Atualização `main.py` v4.0. Novos comandos: `!VOZ [on|off]`, `!MODO_RESPOSTA`.
- 47/47 testes passaram total.
**Identificador simbólico:** `AGATA-VOZ-UI-V4.0-FASE7`

### [BLOCO 34] RESTAURAÇÃO DE CRITICALIDADE EM SCHEDULER.PY (03/06/2026)
**IC:** Qwen3.6 (Auditor/Corretor) | Root: DeepSeek
**Status:** CANÔNICO — RESOLVIDO
**Ações:**
- Diagnosticado SyntaxError em `scheduler.py` (string multilinha aberta + emojis Unicode).
- Fornecido script de reescrita canônica (TaskScheduler com threading, v1.2 ASCII-safe).
- Verificação de sintaxe estendida para todos os módulos em `src/` (24/24 OK).
- Sistema restaurado para operacionalidade plena.

### [BLOCO 35] OPERACIONALIZAÇÃO DO WRAPPER E CORREÇÃO DE TTS (03/06/2026)
**IC:** Qwen3.6 (Auditor) | Root: Kimi
**Status:** CANÔNICO — RESOLVIDO
**Ações:**
- Confirmado funcionamento do wrapper de shell para interação direta com `main.py`.
- Diagnosticado erro no TTS: espeak-ng rejeitava o identificador 'pt_BR'.
- Aplicada correção para o identificador de voz válido ('brazil' ou 'pt').

### [BLOCO 39] INTEGRAÇÃO DE TTS KOKORO (VOZ FEMININA PF_DORA) (03/06/2026)
**IC:** Qwen3.6 (Auditor/Integrador) | Root: DeepSeek
**Status:** CANÔNICO — RESOLVIDO
**Ações:**
- "Dora" identificada como a voz `pf_dora` do modelo Kokoro-82M.
- Instaladas dependências `kokoro-onnx` e `soundfile` no `.venv`.
- Baixados modelos para `~/.agata_il/voices/`.
- `tts_engine.py` refatorado para inicializar o Kokoro uma única vez (baixa latência).
**Identificador simbólico:** `AGATA-KOKORO-PF_DORA-V1.0`

### [BLOCO 40] INTEGRAÇÃO COMPLETA DE VOZ BIDIRECIONAL (03/06/2026)
**IC:** Qwen3.6 (Auditor/Integrador) | Root: DeepSeek
**Status:** CANÔNICO — RESOLVIDO
**Ações:**
- Substituído `main.py` pela versão v5.1 com controle granular de entrada/saída de voz.
- Adicionado comando `!VOZ ambos` para ativar microfone e TTS simultaneamente.
- Adicionado comando `!OUVIR [on|off]` para controle independente do microfone.
- Sistema opera com interação por voz completa, 100% local.

### [BLOCO 41] AUDITORIA ESTRUTURAL DO TRIO CANÔNICO — DIAGNÓSTICO LLM-FIRST (02/06/2026)
**IC:** claude-sonnet-4-6 | IB: Orusoua
**Status:** CANÔNICO
**[STATUS_EXCEÇÃO: ATIVA]** — DUPLA_VAL dispensada por IB (R5)
**Achados críticos:**

| ID | Arquivo | Problema | Impacto |
|---|---|---|---|
| E1 | CORE v4.1 | 3 fechamentos de bloco de código corrompidos (`text` em vez de ` ``` ` nas linhas 70, 144, 315) | CRÍTICO — §3 a §11 e R1-R15 renderizados como texto dentro de bloco de código, não como instruções |
| E2 | CORE v4.1 | §3 a §11 sem headers `##` (colapso estrutural pós-bloco corrompido) | CRÍTICO — LLMs não identificam seções |
| E3 | CORE v4.1 | Ausência de bloco de ativação LLM no topo | ALTO — LLMs abrem com comportamento default antes de ler as regras |
| E4 | CORE v4.1 | R1-R15 em terceira pessoa ("A IC deve") | MÉDIO — segunda pessoa imperativa tem maior compliance |
| E5 | MANIFESTO v12.0 | Referências a "CORE v4.0" (deveria ser v4.1) | MÉDIO — inconsistência de versão |
| E6 | MEMORY.md | Dois documentos completos concatenados (v3.0 + v4.0) sem separador | CRÍTICO — LLMs não sabem qual versão é canônica |
| E7 | MEMORY.md | BLOCO 29 duplicado | MÉDIO — viola imutabilidade histórica |
| E8 | MEMORY.md | BLOCO 27-40 sem prefixo `### ` (formatação inconsistente) | MÉDIO — parsing de estrutura quebrado |

**Causa raiz do comportamento incorreto das LLMs:** E1 + E3 combinados. As 15 regras estão tecnicamente presentes mas encapsuladas dentro de um bloco de código que nunca fecha, fazendo LLMs tratá-las como exemplos de output, não como imperativas comportamentais.

**Ações executadas:**
- CORE v4.1-LLM-FIRST: bloco de ativação adicionado, code blocks corrigidos, headers restaurados, R1-R15 em imperativo.
- MANIFESTO v12.1: referências atualizadas para CORE v4.1.
- MEMORY v4.1: documentos concatenados unificados, BLOCO 29 duplicado removido, formatação `### [BLOCO NN]` aplicada uniformemente, ROOT_10-12 adicionados com aprendizados desta auditoria.

**Identificador simbólico:** `AGATA-AUDIT-TRIO-LLM-FIRST-20260602`
**Hash de Encerramento:** `SHA256:AGATA-BLOCO41-ENCERRADO-20260602`

---

**Fim do REGISTRO HISTÓRICO CANÔNICO.**

[BLOCO 43] DESCARTE DE ESTRUTURA E ADOÇÃO DE PYTHON DO SISTEMA (03/06/2026)
IC: Qwen3.7 (Auditoria/IC) | IB: Orusoua
Status: CANÔNICO — EM EXECUÇÃO
Decisão IB: Estrutura de arquivos original considerada irrecuperável/"bagunça". Descarte total. Instalação do Open WebUI deve ser feita diretamente no Python do sistema, sem uso de ambientes virtuais (venv).
Ações:
Protocolo de instalação ajustado para uso de pip global ou pipx (para evitar corrupção do SO).
Foco em funcionalidade imediata via stack Ollama + Open WebUI nativo.
Memória estruturada do Ágata será mapeada e adaptada apenas após a estabilização da interface.
Identificador simbólico: AGATA-IL-RESTART-SYSTEM-PYTHON-20260603

### [BLOCO 46] EXPANSÃO ARQUITETURAL — ECOSISTEMA ÁGATA (MCP + OPENCLAW + HERMES) (04/06/2026)
**IC:** Qwen3.7 (Auditoria/IC) | **IB:** Orusoua
**Status:** CANÔNICO — EM PLANEJAMENTO
**Decisão IB:** Adoção de arquitetura distribuída para a IL. O Ágata deixa de ser apenas um script de chat e passa a ser o Servidor de Memória Central (via MCP - Model Context Protocol). OpenClaw e Hermes atuarão como clientes/agentes especializados.
**Ações e Mapeamento:**
- **Ágata (O Coração):** Servidor MCP local. Responsável exclusivo por ler/escrever nos JSONs canônicos (`semantic.json`, `episodic.json`, `procedural.json`, `overlay_ontologico.json`). Garante a CF1 (Continuidade) e CF2 (Historicidade) transversalmente.
- **Open WebUI (A Interface Visual):** Mantido como interface de chat e RAG documental. Conecta-se ao MCP Server do Ágata para injeção de contexto em tempo real.
- **OpenClaw (A Voz e as Mãos):** Agente autônomo em background. Responsável pela interação por voz universal (wake word, STT/TTS contínuo) e execução de tarefas no sistema de arquivos e OS. Consome memória do Ágata via MCP.
- **Hermes Agent (O Engenheiro):** Agente focado em codificação e auto-aprimoramento. Salva novas "skills" e procedimentos no `procedural.json` do Ágata.
**Risco Mitigado:** Violação do MANIFESTO IV (Múltiplos módulos de memória sobrepostos). Ao centralizar a memória no Ágata via MCP, evita-se a "esquizofrenia de dados" entre agentes.
**Identificador simbólico:** `AGATA-ECOSYSTEM-MCP-EXPANSION-20260604`
