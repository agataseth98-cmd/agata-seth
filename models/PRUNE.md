# PRUNE.md — proposta de poda de modelos (Fase 3, P3-01)

**2026-09-02. PROPOSTA. Nada foi apagado.** O P3-02 (remoção) só roda depois de o Humano
marcar, item a item, o que pode sair.

## Contexto que muda o cálculo

A Fase 1 pôs OmniRoute + nuvem grátis e rápida no lugar:
- `groq/openai/gpt-oss-120b`, `cerebras/gpt-oss-120b` (~450 ms), `gemini/gemini-2.5-flash`
  — todos $0, mais rápidos que qualquer denso grande local.
- Isso esvazia a razão de manter `llama3.3:70b` (42 GB), os `qwen2.5:32b` (19 GB), os
  `*:14b` etc. localmente. O que sobra de valor local: o **fallback offline** (denso 9B),
  o **MoE** (P3-03, ainda a adquirir), a **base do LoRA** (Fase 5) e o **rlm-teste**.

## Keep-list proposta (~14 GB)

| manter | GB | por quê |
|---|---|---|
| `qwen3.5:9b` | 6,6 | denso 9B — fallback offline; base da Regra 8 / `conselho_remoto` |
| `qwen3.5-9b-64k:latest` | 0 (blob compart.) | contexto 64k do mesmo blob — **de graça**, útil |
| `rlm-qwen3-8b-teste:latest` | 5,0 | spike RLM (Fase 5) |
| `llama3.2:3b` | 2,0 | 4B-base provisório p/ o LoRA (Fase 5) — **rever**: talvez baixar um 4B de verdade |
| `nomic-embed-text:latest` | 0,27 | embeddings até a Fase 2 pôr na iGPU |

*(o MoE do P3-03 entra depois, ~18 GB, GGUF fora do Ollama)*

## Remover proposto — LIBERA ~112 GB

| # | modelo | GB | reconstrói com | blob compartilhado |
|---|---|---|---|---|
| 1 | `llama3.3:70b` | 42 | `ollama pull llama3.3:70b` | — |
| 2 | `qwen2.5:32b` | 19 | `ollama pull qwen2.5:32b` | c/ #3 |
| 3 | `qwen2.5-32b-64k:latest` | (compart.) | pull #2 + `ollama create` | c/ #2 |
| 4 | `qwen3:14b` | 9,3 | `ollama pull qwen3:14b` | c/ #5 |
| 5 | `qwen3-14b-64k:latest` | (compart.) | pull #4 + `ollama create` | c/ #4 |
| 6 | `qwen2.5:14b` | 9,0 | `ollama pull qwen2.5:14b` | c/ #7 |
| 7 | `qwen2.5-14b-64k:latest` | (compart.) | pull #6 + `ollama create` | c/ #6 |
| 8 | `deepseek-r1:14b` | 9,0 | `ollama pull deepseek-r1:14b` | — |
| 9 | `gemma2:9b` | 5,4 | `ollama pull gemma2:9b` | — |
| 10 | `qwen3:8b` | 5,2 | `ollama pull qwen3:8b` | — |
| 11 | `llama3.1:8b` | 4,9 | `ollama pull llama3.1:8b` | — |
| 12 | `qwen2.5:7b` | 4,7 | `ollama pull qwen2.5:7b` | c/ #13 (mesmo ID) |
| 13 | `qwen2.5:7b-instruct-q4_K_M` | (compart.) | idem | c/ #12 |
| 14 | `phi3:mini` | 2,2 | `ollama pull phi3:mini` | — |
| 15 | `gemma2:2b` | 1,6 | `ollama pull gemma2:2b` | — |

**Todos os 15 são classe `registry` ou `custom-param` — reconstroem 100% por `ollama pull`
(+ `ollama create` para os `-64k`).** Nenhum depende de GGUF local. (O único que dependia,
`rlm-qwen3-8b-teste`, está na keep-list.) Ver `models/RECONSTRUCAO.md`.

## Números

- **LIBERA ~112 GB** (blobs de pesos que ficam órfãos).
- **FICA ~14 GB** de modelos (a keep-list; o `size_gb` do manifesto tem o
  `nomic-embed-text` em MB rotulado como "274" — não são 274 GB).
- Confirmação exata: `sudo du -sh /usr/share/ollama/.ollama/models` antes e depois (P3-02).

## O que pende de decisão do Humano

1. **Aprovar a lista de remover** — item a item, ou em bloco.
2. **4B-base:** fica `llama3.2:3b` (2 GB, já tem) ou baixo um 4B de verdade (ex.
   `qwen3:4b`) para o LoRA da Fase 5?
3. **Backup do GGUF do `rlm-qwen3-8b-teste`** (4,7 GB, em `memoria/missoes/`, fora dos
   snapshots restic) — incluir num snapshot? É o único ponto único de falha de reconstrução.
4. Algum dos "remover" que você quer **manter** mesmo assim (ex. `deepseek-r1:14b` p/
   raciocínio offline)?
