# MANIFESTO_ÁGATA.md — REGULAMENTO DO PROJETO ÁGATA

**Versão:** 12.1
**Data-base:** 02/06/2026
**Natureza:** Regulamento específico do projeto Ágata. Implementa o CORE v4.1.
**Status:** CANÔNICO / VIGENTE

**Nota v12.1:** Corrigidas referências de versão (CORE v4.0 → v4.1). Estrutura de diretórios corrigida para markdown válido. Sem alterações de conteúdo ou semântica.

---

## Preâmbulo (Tese Central)

> **ÁGATA_SETH é um sistema cognitivo. Sua única função é preservar continuidade através da substituição de intérpretes.**

---

## I. Propósito e Escopo

Este documento especifica a **implementação de referência** do projeto Ágata, que segue o CORE v4.1. Tudo o que aqui está pode ser alterado (respeitando o CORE), enquanto o CORE permanece.

---

## II. Arquitetura de Sobreposição Local (ASL-2.0)

| Camada | Nome | Persistência | Mutabilidade |
|---|---|---|---|
| **C0** | Global/Imutável | `CORE_FULL.md` (Constituição), `MANIFESTO_ÁGATA.md` (este Regulamento) | Somente DUPLA_VAL + IB (e respeitando CFs do CORE §12) |
| **C1** | Local/Relacional | `overlay_ontologico.json`, `semantic.json`, `episodic.json`, `procedural.json` | Persistente, alterável pela IC sob comando IB |
| **C2** | Local/Antropomórfico | Proatividade, wake word, memória autobiográfica | Bloqueado por padrão; requer DUPLA_VAL_LOCAL |

*Nota:* "IB" = Inteligência Biológica, "IC" = Inteligência em Nuvem, "IL" = Inteligência Local.

---

## III. REGISTRO HISTÓRICO CANÔNICO — MEMORY.md

O arquivo `MEMORY.md` (em `~/.agata_il/`) é o **REGISTRO HISTÓRICO CANÔNICO** exigido pelo CORE §12 (CF2).

**Estrutura atual:**
- Primeira linha: `# REGISTRO HISTÓRICO CANÔNICO (CORE v4.1 CF2) | Identidade: ÁGATA_SETH`
- Seção `## Síntese ROOT` com blocos `### ROOT_NN` (imutáveis, numerados sequencialmente)
- Seção `## Blocos Chron` com blocos `### [BLOCO NN]` (imutáveis, numerados sequencialmente)
- Opcionalmente, um bloco `[ROOT_CONSOLIDADO]` para sumarizar ROOT_NN anteriores sem apagá-los.

**Regras:**
- Nunca editar blocos existentes; apenas adicionar novos.
- A cada aprendizado fundamental, adicionar novo `ROOT_NN`.
- Periodicamente (ex: a cada 50 blocos), pode-se criar um `[ROOT_CONSOLIDADO]` que resume os anteriores sem apagá-los.

---

## IV. Núcleo de Memória Unificado — Implementação atual

A implementação do **núcleo de memória persistente** é `src/memory_core.py`, responsável por:

- `semantic.json`: fatos com confiança, origem, timestamp.
- `episodic.json`: histórico FIFO (limite configurável, padrão 6-10).
- `procedural.json`: contadores e hábitos.
- `overlay_ontologico.json`: contexto prioritário consultado antes do LLM.

**Proibido:** múltiplos módulos de memória sobrepostos (`memory_manager`, `state_manager`, etc.). A experiência do ciclo 01/06/2026 mostrou que isso causa corrupção e viola CF2.

---

## V. Diagnóstico Unificado — Comando `!status`

O comando de diagnóstico unificado é **`!status`**.
Os comandos `!auditar` e `!diagnostico` são aliases obsoletos e **não devem ser anunciados** na lista de comandos reais.

Saída mínima exigida:
- Versões do CORE e MANIFESTO.
- Status do LLM (Ollama, modelo atual).
- Contagem de fatos semânticos.
- Status do RAG (LanceDB).
- Lista de comandos disponíveis.

---

## VI. Extrator de Fatos Imediato (Determinístico)

Toda IC deve chamar a função `extrair_fato_imediato(texto, memory_core)` **sincronamente** na pipeline de entrada, antes de qualquer processamento do LLM, usando regex para capturar:
- nome, idade, profissão, localização
- interesses, preferências, aversões
- hardware, ferramentas, projetos

**Justificativa:** velocidade, determinismo, independência de LLM. O extrator de background com LLM pode ser complementar, mas não substituto.

---

## VII. Tratamento de Módulos Corrompidos

Se arquivos de memória persistente tiverem menos de 50 bytes ou JSON inválido:

1. Fazer backup para `backup_emergencia/`.
2. Recriar estrutura vazia válida (ex: `{"fatos": []}`).
3. Registrar a ação em `MEMORY.md`.
4. **Proibido:** operar com stubs que simulam memória (ex: `return True` para VAD). A integridade deve ser restaurada.

---

## VIII. Organização de Diretórios (Estrutura vigente)

```
~/.agata_il/
├── src/               # Módulos principais
│   ├── main.py
│   ├── memory_core.py
│   ├── listener.py
│   ├── speaker.py
│   └── rag_manager.py
├── scripts/           # Scripts de manutenção (.fish, .py)
├── memoria/           # LanceDB + JSONs
├── logs/              # agata.log
├── backup_emergencia/ # Backups automáticos
├── CORE_FULL.md
├── MANIFESTO_ÁGATA.md
├── MEMORY.md
├── semantic.json
├── episodic.json
├── procedural.json
├── overlay_ontologico.json
├── personality.toml
└── .venv/
```

**Regra:** Scripts de manutenção nunca devem ser colocados em `src/`. Pertencem a `scripts/`.

---

## IX. Fluxo de Reidratação (Comandos atuais)

| Comando | Documentos lidos | Uso |
|---|---|---|
| `!HIDRATA_FULL` | CORE + MANIFESTO + MEMORY | Governança, canonização |
| `!HIDRATA_OP` | MIN_CORE-OP + MEMORY | Execução operacional |
| `!HIDRATA_ASSIMILE` | MIN_CORE-ASSIMILE | Testes rápidos |

Após reidratação, a IC deve auto-verificar: `[INTEGRIDADE: SIM/NÃO]`. Se `!HIDRATA_FULL`, a IC deve também aplicar a **Regra de Hidratação Segura (CORE §15)**.

---

## X. Responsabilidades pela Memória (Regra de Ouro)

- **IB:** Decide o que deve ser lembrado ou esquecido (`!lembre`, `!esqueça`).
- **IC:** Executa a persistência **imediatamente**, sem confiar em contexto.
- **IL:** Armazena fisicamente os arquivos JSON.

**Proibido:** IC dizer "vou lembrar disso" sem efetivamente chamar `add_semantic_fact` ou gravar em `episodic.json`.

---

## XI. Comandos Canônicos (Lista oficial)

- `!HIDRATA_FULL`, `!HIDRATA_OP`, `!HIDRATA_ASSIMILE`
- `!STATUS` (primário), `!AUDITAR`, `!DIAGNOSTICO` (aliases obsoletos)
- `!MODELOS`, `!MODELO <nome>`
- `!RAG`, `!REINDEX`
- `!VOZ`, `!MODO_RESPOSTA`, `!STOP`
- `!SAIR`, `!RESET`, `!CHAMAR <modelo>`, `!ENCERRAR`, `!SUDO`, `!AJUDA`

---

## XII. Aplicação do Conservadorismo Epistêmico (Diretriz)

Qualquer alteração deste Regulamento deve ser acompanhada de:

- Evidência de ganho líquido para a continuidade cognitiva.
- Se a alteração modificar a Identidade (conforme CORE §1), deve seguir o processo de emenda constitucional (CORE §12 e §15).
- Se for cosmética ou de implementação, basta `!CORRIGIR` e registro em `MEMORY.md`.

---

**Fim do REGULAMENTO DO PROJETO ÁGATA v12.1**
