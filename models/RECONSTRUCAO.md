# RECONSTRUCAO.md — como reconstruir cada modelo a partir de `models/manifest.json`

Gate da Fase 3 (P3-00), 2026-09-02. **Nada foi apagado para produzir isto.**
Teste feito: `ollama create` de uma tag descartável + comparação de `blob_sha256` +
`ollama rm` da tag descartável (blob compartilhado não é tocado). `ollama list`: 20
modelos antes e depois.

## As 3 classes

### Classe A — `registry` (14 modelos) — reconstrói com `ollama pull`

`qwen3.5:9b`, `qwen3:14b`, `deepseek-r1:14b`, `llama3.3:70b`, `qwen2.5:32b`, `gemma2:9b`,
`qwen3:8b`, `phi3:mini`, `gemma2:2b`, `llama3.2:3b`, `llama3.1:8b`,
`qwen2.5:7b-instruct-q4_K_M`, `qwen2.5:14b`, `qwen2.5:7b`.

```
ollama pull <name>
```
Determinístico — é como esses modelos chegaram aqui. Precisa de rede. O `blob_sha256` do
manifesto é a régua de conferência pós-pull.

### Classe B — `custom-param` (4 modelos) — `ollama pull` da base + `ollama create`

| modelo | base (registry) | diferença |
|---|---|---|
| `qwen3.5-9b-64k` | `qwen3.5:9b` | `PARAMETER num_ctx 65536` |
| `qwen3-14b-64k` | `qwen3:14b` | `num_ctx 65536` |
| `qwen2.5-32b-64k` | `qwen2.5:32b` | `num_ctx 65536` (+ SYSTEM) |
| `qwen2.5-14b-64k` | `qwen2.5:14b` | `num_ctx 65536` (+ SYSTEM) |

**O blob de pesos é o MESMO da base** (confirmado: `qwen3.5-9b-64k` e `qwen3.5:9b`
compartilham `sha256-dec52a4456…`). Somar os `size_gb` desses no cálculo de disco
**superestima** — o `ollama` só libera o blob quando a base **e** o `-64k` saem.

```
ollama pull <base>
# pegar o Modelfile do manifesto, trocar a 1ª linha por:  FROM <base>
python3 -c "import json;print(next(m['modelfile'] for m in json.load(open('models/manifest.json'))['modelos'] if m['name']=='qwen3.5-9b-64k:latest'))" > /tmp/mf
sed -i 's#^FROM /.*#FROM qwen3.5:9b#' /tmp/mf
ollama create qwen3.5-9b-64k:latest -f /tmp/mf
```
**Testado 2026-09-02** para `qwen3.5-9b-64k`: `blob_sha256` do recriado ==
`sha256-dec52a4456…` == manifesto. ✅

### Classe C — GGUF próprio (2 modelos)

| modelo | fonte | reconstrução |
|---|---|---|
| `nomic-embed-text` | está na **library** do Ollama (o manifesto classifica "custom" por heurística de P0-01, mas é registry) | `ollama pull nomic-embed-text` |
| `rlm-qwen3-8b-teste` | **GGUF em `memoria/missoes/rlm-3caminhos/modelo/rlm-qwen3-8b-v0.1-q4_k_m.gguf`** (4,7 GB) | `ollama create rlm-qwen3-8b-teste:latest -f <Modelfile do manifesto, FROM = esse gguf>` |

**`rlm-qwen3-8b-teste` é o único que depende de um arquivo local não-registry.**
O `sha256` do GGUF (`c3b6bfbc3a9d36d6…`) **é idêntico** ao `blob_sha256` do modelo no
Ollama — o Ollama importou verbatim. Reconstrói bit a bit **enquanto esse GGUF existir**.

> ⚠️ **Ponto único de falha:** o GGUF `rlm-qwen3-8b-v0.1-q4_k_m.gguf` está em
> `memoria/missoes/` — **não** rastreado pelo git principal e **não** nos snapshots restic
> atuais (`61b986a3`/`a0aa676c`/`78bfad63` só pegam config). Se `rlm-qwen3-8b-teste`
> importa a longo prazo (spike RLM, Fase 5), incluir esse GGUF num snapshot restic.
> Decisão do Humano — é 4,7 GB.

## Resultado do gate P3-00

- 14/20 reconstroem por `ollama pull` (registry).
- 4/20 reconstroem por `pull` + `ollama create` (testado 1, sha256 bateu).
- 1/20 (`nomic-embed-text`) reconstrói por `ollama pull` (library).
- 1/20 (`rlm-qwen3-8b-teste`) reconstrói a partir de um GGUF local preservado — **o único
  a exigir cuidado de backup**.
- **Conclusão:** o manifesto + `ollama pull` + o GGUF do rlm reconstroem 100% dos modelos.
  Pode seguir para P3-01 (lista de prune). O GGUF do rlm entra como item de backup a decidir.
