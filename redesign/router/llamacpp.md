# redesign/router/llamacpp.md — 2º backend local (worker MoE) — P3-03

**Não é canon.** Branch `redesign`, Fase 3. Fecha o aceite da Fase 3 (runtime duplo: Ollama
denso + llama.cpp MoE).

## O que subiu (2026-09-02, relógio da máquina ~10:57 -03)

- **Pacotes** (repo oficial `extra`/`cachyos-extra-v3`, assinados; `sudo pacman -S --needed
  llama-cpp ggml-cuda` — puxou `ggml` e `nccl` como dependência): `llama-cpp 0.3.0-1.1`
  (build 10621, commit `c1d0e7a004`) + `ggml-cuda 0.22.0-2.1`. `cuda 13.3.1` e
  `nvidia-utils 610.57.04` já estavam. `llama-server --list-devices` → `CUDA0: RTX 4060`.
- **Modelo:** `Qwen3-30B-A3B-Instruct-2507`, GGUF **Q4_K_M** (arquivo único, 17,3 GiB /
  18.550.716.416 B). Origem:
  `https://huggingface.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/resolve/main/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf`
  em `~/.cache/agata/models/` (subvolume `@cache`, **fora dos snapshots do snapper** — não
  repete o problema de disco do P3-02).
  `sha256 = 6c997b8af17debdfb01d890214400ccbab00db6acc0ba8da5de1cc906c4774d0`.
  MoE A3B: 30,5 B total / ~3,3 B ativos, 48 camadas, `n_ctx_train` 262144.
- **Serviço:** `~/.config/systemd/user/llamacpp-agata.service` (`Type=simple`,
  `Restart=on-failure`, `Nice=5`, **sem `enable`** — boot é Fase 7). `ExecStart`:
  ```
  /usr/sbin/llama-server -m %h/.cache/agata/models/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf \
    -ngl 999 --n-cpu-moe 36 --host 127.0.0.1 --port 20129 -c 8192 --alias qwen3-30b-a3b --no-webui
  ```
  Sobe healthy em ~6 s. Bind `127.0.0.1:20129`. `/v1/models` → id `qwen3-30b-a3b`.
- **OmniRoute:** provider `llamacpp-local` (`--provider-base-url http://127.0.0.1:20129/v1`,
  `--default-model qwen3-30b-a3b`, api-key placeholder `llamacpp-nokey`). Model-id de
  chamada: **`llamacpp-local/qwen3-30b-a3b`**. Combo `auto` refeita (ver abaixo).

## Varredura `--n-cpu-moe` (`llama-bench`, `-ngl 999 -p 128 -n 128 -r 3`)

`--n-cpu-moe N` = N camadas de experts na RAM (CPU), o resto (atenção + experts das 48−N
camadas) na GPU. N maior = menos VRAM, mais lento.

| N (cpu-moe) | pp128 tok/s | **tg128 tok/s** | VRAM pico (bench 128 ctx) | |
|---:|---:|---:|---:|---|
| 48 | 116,1 | 20,3 | 1,2 GB | tudo expert na CPU |
| 44 | 126,3 | 22,5 | 2,7 GB | |
| 40 | 138,1 | 25,7 | 4,1 GB | |
| **36** | **148,9** | **28,4** | **5,4 GB** | **escolhido** |
| 32 | 161,1 | 32,1 | 6,8 GB | cabe no bench, mas ver nota |
| 28 | — | — | — | **falha ao carregar (CUDA OOM)** — VRAM usável ≈ 7,83 GiB |
| 24 | — | — | — | OOM |
| 20 | — | — | — | OOM |

### Servidor real (não só bench) — `llama-server -c 8192`, geração de verdade

| N | VRAM idle após load | VRAM pico na geração | tg tok/s | folga (de ~7,83 GiB usáveis) |
|---:|---:|---:|---:|---:|
| 32 | 7623 MiB | 7637 MiB | 34,9 | **~197 MiB — apertado demais** |
| **36** | **6229 MiB** | **6243 MiB** | **31,4** | **~1590 MiB — confortável** |

## Decisão: `--n-cpu-moe 36`

- **31,4 tok/s** de geração — bem acima do aceite da Fase 3 (`≥ ~20 tok/s`).
- **~1,6 GB de folga de VRAM** na 4060 (8 GB), que também move o desktop. N=32 dava só
  ~200 MiB de folga com contexto de 8k — qualquer crescimento do KV cache ou o desktop
  pegando alguns MB → OOM. Os ~3 tok/s abertos mão compram margem real até a Fase 7 pôr o
  liga/desliga de VRAM (jogo vs. Agata).
- `-c 8192`: suficiente para o loop de governança. Rever se a Fase 5 (hidratação RLM)
  precisar de janela maior — a 16384 ainda cabe (~+0,4 GB de KV).
- **Offload real confirmado:** durante a geração `nvidia-smi` mostrou `utilization.gpu`
  oscilando 9–100 % com VRAM em 6243 MiB — não é 100 % CPU.

## Combo `auto` (priority) — antes → depois

- **antes:** `cerebras/gpt-oss-120b` → `groq/openai/gpt-oss-120b` → `gemini/gemini-2.5-flash`
  → `ollama-local/qwen3.5:9b`
- **depois:** `cerebras/gpt-oss-120b` → `groq/openai/gpt-oss-120b` → `gemini/gemini-2.5-flash`
  → **`llamacpp-local/qwen3-30b-a3b`** → `ollama-local/qwen3.5:9b`

**Por que tier 4 e não tier 2** (o arquivo-tarefa P3-03 sugeria #2): a tarefa foi escrita
antes das medições, supondo o MoE como opção rápida. Com o número real (31 tok/s, ~2 s ao
1º token) ele é um *bom fallback local*, não um competidor de latência com o
`gpt-oss-120b` na nuvem (~450 ms). Colocá-lo logo **acima** do denso 9B — subindo o tier
local de 9B para 30B-A3B — mantém `auto` otimizado para latência (nuvens rápidas primeiro)
e melhora o fallback local. Escolha pelo princípio-espelho (nós trocáveis, espinha mínima),
registrada no `LOG.md`. Reversível: `omniroute combo delete auto --yes` + recriar.

## Verificação (P3-03)

- `systemctl --user is-active llamacpp-agata.service` → `active`; `/health` → 200;
  `/v1/models` → `qwen3-30b-a3b`, `n_ctx 8192`. Bind `127.0.0.1:20129` (`ss -tlnp`).
- `llamacpp-local/qwen3-30b-a3b` roteia **direto** (`:20128`) e **pelo proxy sanitizador**
  (`:20127`) → `"ok"`, `system_fingerprint b10621-c1d0e7a004`.
- **Fallback para o MoE:** combo throwaway `[deepseek/deepseek-v4-flash (402) →
  llamacpp-local/qwen3-30b-a3b]` via `:20127` → resposta veio de `model: qwen3-30b-a3b`,
  fingerprint llama.cpp. Combo apagada depois.
- `omniroute cost` contabiliza `llamacpp-local` (linha própria, $0,0000).
- unit **não** `enable`d.

## Reconstrução

Público, hash fixado → **não precisa de snapshot restic** (ao contrário do
`rlm-qwen3-8b-teste`). Reconstrói com:
```fish
mkdir -p ~/.cache/agata/models; cd ~/.cache/agata/models
wget -c 'https://huggingface.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/resolve/main/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf'
test (sha256sum Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf | string split ' ')[1] = 6c997b8af17debdfb01d890214400ccbab00db6acc0ba8da5de1cc906c4774d0
```
Registrado em `models/manifest.json` (entry `name: qwen3-30b-a3b`, `backend: llama.cpp`).

## Rollback

```fish
systemctl --user stop llamacpp-agata.service
rm -f ~/.config/systemd/user/llamacpp-agata.service
systemctl --user daemon-reload
omniroute combo delete auto --yes
omniroute combo create auto --strategy priority --models "cerebras/gpt-oss-120b,groq/openai/gpt-oss-120b,gemini/gemini-2.5-flash,ollama-local/qwen3.5:9b"
# provider: deixar registrado ou remover pelo dashboard do omniroute
git checkout -- redesign/router/llamacpp.md models/manifest.json
```
> ⚠️ **Remove o GGUF do MoE (~17 GB) e os pacotes. Rode sozinho.**
> ```fish
> rm -f ~/.cache/agata/models/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf
> sudo pacman -Rns llama-cpp ggml-cuda
> ```
