# redesign/igpu/ — camada da iGPU Intel (Fase 2)

**Não é canon.** Branch `redesign`. Objetivo da Fase 2: tirar display + STT + embeddings da
RTX 4060 e pôr na iGPU Intel UHD.

## Estado (2026-09-02 ~12:00 -03, relógio da máquina)

| tarefa | estado |
|---|---|
| **P2-00** inventário | ✅ `INVENTARIO.md` |
| **P2-01** display na iGPU | ✅ `DISPLAY-PIN.md` — **já estava lá, sem mudança** |
| **P2-02** whisper STT na iGPU | ✅ `openvino-whisper.service` (`:20130`, `GPU.0`, RTF ~0.08) |
| **P2-03** embeddings na iGPU | ✅ `openvino-embeddings.service` (`:20134`, `GPU.0`, e5-small 384d) |
| **Fase 2** | ✅ **FECHADA** — 4060 em **1 W / 56 MB** com display+STT+embeddings todos na iGPU |

## Hardware (do `INVENTARIO.md`)

- **iGPU:** Intel UHD Graphics RPL-S `[8086:a78b]`, driver `i915`. Nós: `/dev/dri/card2`,
  `/dev/dri/renderD129`. OpenVINO a enumera como **`GPU.0`** (a 4060 é `GPU.1`; o CPU é `CPU`).
- **Runtime de compute:** `intel-compute-runtime` + `intel-graphics-compiler` +
  `intel-gpu-tools` instalados em P2-02 (repo `extra`, `sudo pacman`). `clinfo -l` agora
  lista `Intel(R) OpenCL Graphics -> Intel(R) UHD Graphics`.
- **Display:** painel `eDP-1` é conector da iGPU; a 4060 não tem trilha de vídeo para o eDP.
  Baseline 4060 em repouso: **~54 MiB / ~16 W / 0 % util**.

## `whisper_server.py` — STT na iGPU (P2-02)

- `openvino_genai.WhisperPipeline(model_dir, device="GPU.0")`. HTTP stdlib em `127.0.0.1:20130`.
- **`POST /transcribe`**: body `{"path": "..."}` **ou** bytes WAV crus → `{text, chunks,
  audio_s, proc_s, rtf, device, model}`. `GET /health` → 200.
- WAV lido por `wave` + reamostrado a 16 kHz mono por `librosa` se preciso. Long-form
  (>30 s): o `WhisperPipeline` chunka sozinho (`return_timestamps=True`).
- `--selftest <wav> [--device CPU|GPU.0] [--model DIR]` para medir RTF fora do serviço.

### Modelo: `OpenVINO/whisper-base-int8-ov` (IR pré-convertido)

**Desvio do arquivo-tarefa** (que dizia `distil-whisper/distil-small.en`), por 3 motivos:
1. **`optimum-cli export openvino` está quebrado** — `optimum` 2.3.0 tem um bug
   (`NormalizedConfig.__init__() got multiple values for argument 'allow_new'`) que atinge
   o export de Whisper, com `transformers` 5.5.4 **e** 4.57.6. IR pré-convertido do org
   `OpenVINO/` no HF pula o problema inteiro (traz `openvino_encoder/decoder_model.xml` +
   `openvino_tokenizer`/`detokenizer` prontos para o genai).
2. **Multilíngue** — o canon do Agata é PT-BR; `distil-small.en` é só inglês. `whisper-base`
   e `whisper-small` (org OpenVINO) são multilíngues.
3. `whisper-base` (74 M, 81 MB int8) é mais rápido que `distil-small` e sobra qualidade.

`whisper-small-int8-ov` (244 M, 245 MB) está baixado também — **upgrade drop-in** se a
qualidade do base não bastar (`OVW_MODEL_DIR` na unit, ou `--model`).

### RTF medido (`fala30s.wav`, 36 s, espeak-ng) — iGPU vs CPU

| modelo | `GPU.0` (iGPU) | `CPU` |
|---|---|---|
| **base**  | **RTF 0.082** (2.97 s) | RTF 0.022 (0.8 s) |
| small | RTF 0.212 (7.64 s) | RTF 0.057 (2.07 s) |

Todos **muito** abaixo de RTF 1 (tempo real). O **CPU é 3–4× mais rápido** que a iGPU para
esse tamanho de modelo — mas a escolha é **iGPU (`GPU.0`)** de propósito: é capacidade
ociosa (só move o display), STT é rajada (só quando alguém fala), e mantém o STT fora do
caminho crítico do CPU (o loop do grafo, git, scripts, o llama.cpp quando sobe). RTF 0.08
= ~8 % do tempo da iGPU. Se STT virar contínuo e a latência importar, `--device CPU` é a
alternativa registrada.

- **4060 durante a inferência:** `nvidia-smi` mostra só `kwin_wayland` 7 MiB — **nenhum
  processo python**. STT saiu da 4060 (nunca esteve nela — não havia STT antes; agora tem,
  na iGPU).

### Serviço

`~/.config/systemd/user/openvino-whisper.service` — `Type=simple`, `Nice=5`,
`Restart=on-failure`, `Environment=OVW_DEVICE=GPU.0`, **sem `enable`** (boot é Fase 7).
Sobe healthy em ~6 s.

## venv

`redesign/igpu/.venv` (gitignorado, `redesign/**/.venv/`). OpenVINO 2026.3.1, openvino-genai
2026.3.1, optimum-intel 2.1.0, transformers 4.57.6 (fixado — o 5.5.4 não muda o bug do
export mas 4.57 é o alvo testado), torch 2.14 (puxou ~2 GB de libs CUDA à toa — venv
descartável). ~6.2 GB no total.

## `embeddings_server.py` — embeddings na iGPU (P2-03)

- Modelo **`intfloat/multilingual-e5-small`** (384 dim, PT-BR + multilíngue) — o export
  `optimum-cli export openvino --task feature-extraction --weight-format int8`
  **funcionou** (o bug do `optimum` 2.3.0 era só no `NormalizedConfig` de **Whisper**;
  XLM-RoBERTa exporta normal). IR int8 em `~/.cache/agata/openvino/embeddings/multilingual-e5-small-int8`.
- `optimum.intel.OVModelForFeatureExtraction.from_pretrained(dir, device="GPU.0")` +
  `AutoTokenizer`. mean-pooling mascarado + L2-normalize (receita e5).
- **`POST /embed`** (e `/v1/embeddings`) em **`127.0.0.1:20134`** — body
  `{"input": str|[str], "input_type": "query"|"passage"}` → **formato OpenAI embeddings**
  (`{object:"list", data:[{object:"embedding",index,embedding:[...]}], model, usage}`),
  sem adaptador no grafo. Prefixo `query: `/`passage: ` aplicado (não duplica se já vier).
  `GET /health` → `{dim:384}`.
- **Porta 20134** (não 20131): o OmniRoute ocupa `20127/20128/20131/20132`.
- `--selftest [--device CPU|GPU.0]`: 2 frases próximas + 1 distante → cossenos.
  Medido: `cos(próximas)=0.885` > `cos(distante)=0.791` na iGPU (idem no CPU — mesmo int8).
- **Zero vector DB** (invariante Fase 6): só devolve o vetor. `pip list` sem
  faiss/chroma/qdrant/weaviate/milvus/lancedb.
- Serviço: `~/.config/systemd/user/openvino-embeddings.service` (`GPU.0`, sem `enable`).

## Aceite conjunto da Fase 2 (P2-03 passo 5) — FECHADO

Com `openvino-whisper` + `openvino-embeddings` carregados **e** sob fogo cruzado (1
transcrição + 8 `POST /embed` simultâneos):

| 4060 | valor |
|---|---|
| potência | **1 W** (clock caiu p/ 405/210 MHz — idle profundo) |
| VRAM (`fb`) | **56 MB** (só o `kwin_wayland` 7 MiB + overhead do driver) |
| util (sm/mem/enc/dec) | 0 % |
| processos compute | **só `kwin_wayland`** — nenhum python/whisper/embeddings |

Whisper RTF durante a carga simultânea: **0.051**. Display + STT + embeddings **todos na
iGPU**; a 4060 fica livre para inferência (llama.cpp) e jogos.

> **iGPU vs CPU — a inferência roda mesmo na iGPU, não caiu p/ CPU em silêncio:** os RTF
> medidos são *diferentes* por device (whisper base iGPU 0.082 vs CPU 0.022; e5 idem),
> o que só acontece se forem caminhos de compute distintos. `device="GPU.0"` também
> falharia no load se a iGPU não estivesse disponível.

## Rollback

```fish
systemctl --user stop openvino-whisper.service openvino-embeddings.service
rm -f ~/.config/systemd/user/openvino-whisper.service ~/.config/systemd/user/openvino-embeddings.service
systemctl --user daemon-reload
git checkout -- redesign/igpu
```
> ⚠️ **Remove o venv (~6 GB) e os modelos IR. Rode sozinho.**
> ```fish
> rm -rf redesign/igpu/.venv ~/.cache/agata/openvino
> sudo pacman -Rns intel-gpu-tools intel-compute-runtime intel-graphics-compiler
> ```
