# P3-01 — decidir o que fica e o que sai (lista de prune, SEM apagar)

**Objetivo:** produzir `models/PRUNE.md` — a lista explícita de quais modelos manter e
quais remover, com tamanho real e justificativa. **Nenhuma remoção nesta tarefa.**

**Pré-requisitos:** P3-00 FEITO (reconstrutibilidade provada).

**Arquivos:** `models/PRUNE.md` (novo) · `redesign/tasks/P3-01-*.md`

---

## Keep-list de partida (ROADMAP, Fase 3)

| manter | qual | por quê |
|---|---|---|
| denso 9B (fallback local testado) | `qwen3.5:9b` | é o que a Regra 8 / `conselho_remoto` usam; base dos 64k |
| MoE | **a adquirir** — Qwen3-30B-A3B **ou** Qwen3.6-35B-A3B (GGUF p/ llama.cpp) | worker de julgamento local (P3-03) — **não roda bem no Ollama**, bug #10458 (PESQUISA C1) |
| 4B base (LoRA) | decidir — `llama3.2:3b` (2 GB) ou baixar um 4B real | matéria-prima do LoRA de formato Agata (Fase 5) |
| `rlm-qwen3-8b-teste` | manter | spike RLM (Fase 5) |
| embeddings | `nomic-embed-text` (274 MB) | até a Fase 2 pôr embeddings na iGPU; barato, deixar |

**Candidatos a remover** (tudo que não está acima). Hoje inclui: `llama3.3:70b` (42 GB),
`qwen2.5:32b` / `qwen2.5-32b-64k` (19 GB cada), `qwen3:14b` / `qwen3-14b-64k`,
`qwen2.5:14b` / `qwen2.5-14b-64k`, `deepseek-r1:14b`, `gemma2:9b`, `qwen3:8b`,
`llama3.1:8b`, `qwen2.5:7b` (+variantes), `phi3:mini`, `gemma2:2b`, `llama3.2:3b`
(se não for o 4B-base).

**Contexto que muda o cálculo:** com a Fase 1 pronta (OmniRoute + Groq/Cerebras/Gemini
grátis e rápidos), a maioria dos densos grandes locais perde razão de existir —
`gpt-oss-120b` na nuvem é mais rápido que `llama3.3:70b` local e custa $0. O prune pode
ser agressivo. Mas a decisão final é do Humano (destrutivo).

---

## Passos

### 1. Medir o tamanho REAL (blobs compartilhados)

```fish
cd $HOME/agata
du -sh /usr/share/ollama/.ollama/models
# tamanho por blob e quem referencia cada um:
python3 - <<'PY'
import subprocess, re, collections, os
blobs = "/usr/share/ollama/.ollama/models/blobs"
uso = collections.defaultdict(list)
for name in subprocess.check_output(["ollama","list"]).decode().splitlines()[1:]:
    n = name.split()[0]
    if not n: continue
    mf = subprocess.check_output(["ollama","show","--modelfile",n]).decode()
    for b in re.findall(r"blobs/(sha256-[0-9a-f]{64})", mf):
        uso[b].append(n)
for b, quem in sorted(uso.items(), key=lambda x:-os.path.getsize(f"{blobs}/{x[0]}") if os.path.exists(f"{blobs}/{x[0]}") else 0):
    p = f"{blobs}/{b}"
    gb = os.path.getsize(p)/1e9 if os.path.exists(p) else 0
    print(f"{gb:6.2f} GB  {b[:19]}…  <- {', '.join(quem)}")
PY
```
Colar de volta: o `du` e a tabela por blob.
Objetivo: saber, para cada blob, **qual conjunto de modelos precisa sair** para ele ser
liberado. Um blob só de `llama3.3:70b` → remover esse 1 modelo libera 42 GB. Um blob
compartilhado por 3 modelos → só libera se os 3 saírem.

### 2. Escrever `models/PRUNE.md`

Tabela final: `MANTER` / `REMOVER` por modelo, tamanho do(s) blob(s) exclusivo(s),
reconstrutível? (de P3-00), justificativa em 1 linha. Somatório do que o prune libera
(por blobs que ficam órfãos, não por soma de `size_gb`). Mais: a decisão do 4B-base e se
vai baixar um GGUF de MoE agora ou na P3-03.

### 3. Subir ao Humano

`PRUNE.md` é uma **proposta**. O P3-02 só roda depois do Humano marcar, item a item, o
que pode sair — é remoção destrutiva de dados.

---

## Aceite

- `models/PRUNE.md` existe, com toda linha classificada `MANTER`/`REMOVER`, tamanho de
  blob exclusivo, flag de reconstrutível, e o total liberável real.
- A keep-list cobre: 1 denso 9B, o `rlm-qwen3-8b-teste`, o 4B-base escolhido, o
  `nomic-embed-text`, e o plano do MoE.
- **Nada removido.** `ollama list` idêntico.

## Verificação independente

- **Quem:** Humano (é dado dele que vai sumir) + fallback conferindo a conta de GB.
- **O quê:** que o "total liberável" conta blobs órfãos, não soma de `size_gb`; que nenhum
  modelo da keep-list está marcado `REMOVER` por engano.
- **Como:** reconferir a tabela do passo 1 contra o `PRUNE.md`.
- **Resultado:** anotar no LOG.

## Rollback

Nada a desfazer. `git checkout -- models/PRUNE.md redesign/tasks/P3-01-*.md`.

## Registro

- `STATUS.md`: P3-01 → "Feito"; anotar o total liberável proposto e o que pende de decisão do Humano.
- `LOG.md`: a tabela por blob (resumo), o total, `HEAD` no fim.
