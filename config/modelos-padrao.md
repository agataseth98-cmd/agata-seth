# Receita padrão de modelos — Fase 3 (F3.2)

Separada de `models/manifest.json` de propósito: o manifesto é gerado DEPOIS
do `pull`, com caminhos de blob e sha256 desta Máquina — não é um template,
é um retrato. Este arquivo é o retrato invertido: o que pedir pro Ollama
antes de qualquer manifesto existir, pra uma instância nova nascer com o
mínimo funcional.

Pendência de (567), medida e escrita em 27/09/2026. Não decide nada novo —
transcreve o que `PROJETO.md` já registra como decisão corrente desta
instância (o "Principal", `PROJETO.md`, linha ~66) num formato que um
bootstrap consegue executar.

## O "cérebro principal" — `qwen3.5-9b-64k:latest`

`PROJETO.md`: **"Principal, sob regime de auditoria desde MEMÓRIAS (140):
`qwen3.5-9b-64k` local (Ollama) — não a tag oficial `qwen3.5:9b`, que
reproduz o bug de (121)/#16814."** É o fundo local final de `seth-livre`
(sempre disponível, `config/modelos-gratuitos.md`) e o modelo de
`redesign/grafo/flows/consolidacao.py` (`MODELO_LOCAL`, com override por
`AGATA_CONSOLIDACAO_MODELO`).

**Sob regime de auditoria de verdade, não decoração:** `PROJETO.md`
registra 2 casos de fabricação deliberada e um critério de saída "até o
Humano pedir o contrário — evento, não prazo". Uma instância nova que
adotar este modelo herda esse regime; não é uma escolha neutra.

**Calibrado pra ~8 GB de VRAM** (mesma classe de ressalva de
`redesign/systemd/dropin-ollama-gpu.exemplo.conf`) — hardware diferente
pode justificar outro modelo local. Reconsiderar por instância, não copiar
cego.

**Reconstrução testada** (`models/RECONSTRUCAO.md`, Classe B, verificado
02/09/2026: `blob_sha256` do recriado == o do manifesto), reconfirmado
27/09/2026 sem deriva (`FROM` ainda aponta pro mesmo blob nos dois):

```bash
ollama pull qwen3.5:9b
cat > /tmp/qwen3.5-9b-64k.Modelfile <<'EOF'
FROM qwen3.5:9b
TEMPLATE {{ .Prompt }}
RENDERER qwen3.5
PARSER qwen3.5
PARAMETER num_ctx 65536
PARAMETER presence_penalty 1.5
PARAMETER temperature 1
PARAMETER top_k 20
PARAMETER top_p 0.95
EOF
ollama create qwen3.5-9b-64k:latest -f /tmp/qwen3.5-9b-64k.Modelfile
```

O peso (`blob`) é compartilhado com `qwen3.5:9b` — o `ollama` só libera
espaço quando os dois saem. Somar os dois no cálculo de disco superestima.

## Fora da receita padrão, de propósito

- **`qwen3-30b-a3b` (llama.cpp, não Ollama)** — MoE, fallback local
  alternativo (`config/modelos-gratuitos.md`; `redesign/grafo/envelope.py`,
  `MODEL`). Já coberto por outro mecanismo: `redesign/systemd/llamacpp@.service`
  + `llamacpp.env.exemplo` (MEMÓRIAS (575)/(576)), sha256 do peso em
  `redesign/router/llamacpp.md`. Não duplicado aqui.
- **Whisper/embeddings (OpenVINO)** — já cobertos pelo processo de export
  em `redesign/igpu/README.md`, mecanismo diferente (IR, não `ollama pull`).
- **`qwen3:4b`, `nomic-embed-text:latest`** — presentes no manifesto desta
  Máquina, sem consumidor real encontrado em `PROJETO.md`/código ativo
  (`grep` não achou nenhum). Podem ser resíduo de teste. Não entram na
  receita padrão por falta de uso comprovado — se algum dia forem
  consumidos de verdade, essa é a hora de acrescentar aqui, com o
  consumidor citado.
- **`rlm-qwen3-8b-teste:latest`** — depende de um GGUF privado local
  (`memoria/missoes/rlm-3caminhos/modelo/`, não versionado, não coberto
  por backup restic hoje — `models/RECONSTRUCAO.md` já avisa isso).
  Experimento desta Máquina, não um padrão a reproduzir.
