# P2-02 — openvino-whisper.service (distil-whisper int8, chunked) na iGPU

**Objetivo:** STT roda na iGPU via OpenVINO, em tempo real, como serviço — tirando o
Whisper da 4060 (ou da CPU). Item do aceite da Fase 2: "Whisper transcreve em tempo real
na iGPU".

**Status:** ✅ **FEITO — 2026-09-02 ~12:00 (relógio da máquina).** `sudo pacman -S
intel-compute-runtime intel-graphics-compiler intel-gpu-tools` (a lacuna do P2-00 —
`clinfo -l` agora lista a iGPU). venv `redesign/igpu/.venv` (OpenVINO 2026.3.1 + genai +
optimum-intel + transformers 4.57.6 fixado). **Modelo: `OpenVINO/whisper-base-int8-ov`** (IR
pré-convertido, multilíngue — o `optimum-cli export` está quebrado no `optimum` 2.3.0, e o
canon é PT-BR, não `distil-small.en`). `whisper_server.py` (`:20130`, stdlib) +
`openvino-whisper.service` (`GPU.0`, sem `enable`). **RTF na iGPU = 0.082** (base) / 0.212
(small) — muito abaixo de 1. CPU é 3–4× mais rápido mas a iGPU é escolha deliberada
(capacidade ociosa, STT é rajada, fora do caminho crítico do CPU). `nvidia-smi` sem processo
python durante a inferência. `whisper-small-int8-ov` baixado como upgrade drop-in. Detalhes:
`redesign/igpu/README.md`.

**Pré-requisitos:** P2-00 FEITO (iGPU confirmada, `renderD*` presente). P2-01 recomendável
mas não bloqueante (o Whisper na iGPU independe de onde o display está).

**Arquivos que a tarefa toca:**
- venv isolado `redesign/igpu/.venv` (gitignorado — conferir `.gitignore` cobre
  `redesign/**/.venv/`; P0-00 já adicionou)
- modelo distil-whisper convertido para OpenVINO IR + int8 em `~/.cache/agata/openvino/whisper/`
  (fora do repo; entra no `models/manifest.json` na Fase 3)
- `redesign/igpu/whisper_server.py` (novo) — servidor de transcrição (HTTP local ou socket)
- `~/.config/systemd/user/openvino-whisper.service` (novo)
- `redesign/igpu/README.md` (novo)
- `redesign/tasks/P2-02-*.md`

---

## Contexto (PESQUISA + web 01/09/2026)

- OpenVINO estável 2026.1.0. `openvino.genai` tem Generate API para Whisper ASR.
- distil-whisper + NNCF int8; algoritmo **chunked long-form** ~9x mais rápido que sequential.
- iGPU Intel suportada (`device="GPU"` no OpenVINO). Numa UHD 32 EU a expectativa é
  **distil-small/medium** em tempo real — não o large. Confirmar qual tamanho fecha
  "tempo real" (RTF < 1) no passo 4.

---

## Passos

### 1. **INSTALA SOFTWARE** — venv + OpenVINO

> **Instala pacotes. Rode sozinho. Revisão de plano antes (classe: instala-pacote).**

```fish
cd $HOME/agata
python3 -m venv redesign/igpu/.venv
redesign/igpu/.venv/bin/pip install --upgrade pip
redesign/igpu/.venv/bin/pip install "openvino>=2026.1" "openvino-genai>=2026.1" \
  "optimum[openvino]" "transformers" "librosa" "soundfile"
redesign/igpu/.venv/bin/python -c "import openvino as ov; print(ov.__version__); print(ov.Core().available_devices)"
```
Colar de volta: a versão e `available_devices`.
Sucesso: a lista tem `GPU` (ou `GPU.0`) — a iGPU. Se só tiver `CPU`, parar: driver/compute
runtime da iGPU faltando (`intel-compute-runtime` / `intel-opencl`), resolver antes.

### 2. Converter distil-whisper para OpenVINO IR + int8

```fish
cd $HOME/agata
set -x HF_HUB_ENABLE_HF_TRANSFER 1
redesign/igpu/.venv/bin/optimum-cli export openvino \
  --model distil-whisper/distil-small.en \
  --weight-format int8 \
  ~/.cache/agata/openvino/whisper/distil-small.en-int8
# (repetir com distil-medium.en se small não bastar em qualidade)
ls -lh ~/.cache/agata/openvino/whisper/distil-small.en-int8
```
Colar de volta: o `ls`.
Sucesso: os arquivos `openvino_*.xml/.bin` do encoder e decoder existem.

### 3. `whisper_server.py`

Escrever `redesign/igpu/whisper_server.py`:
- carrega o modelo com `openvino_genai.WhisperPipeline(model_dir, device="GPU")`.
- expõe `POST /transcribe` (HTTP em `127.0.0.1:20130`, ou socket UNIX) que recebe áudio
  (wav/pcm) e devolve `{text, segments, rtf}` onde `rtf` = tempo_de_processo / duração_do_áudio.
- usa o modo **chunked** (long-form) para áudio > 30 s.
- `--selftest <arquivo.wav>`: transcreve e imprime `{text, rtf}`.

### 4. Teste — tempo real na iGPU

```fish
cd $HOME/agata
# um wav de ~30s de fala (gravar ou usar amostra); medir RTF
redesign/igpu/.venv/bin/python redesign/igpu/whisper_server.py --selftest /tmp/fala30s.wav
# durante, em outro terminal:
timeout 8 intel_gpu_top -l | head
nvidia-smi --query-compute-apps=pid,process_name --format=csv   # whisper NÃO deve aparecer
```
Colar de volta: o `{text, rtf}`, a carga da iGPU, o `nvidia-smi`.
Sucesso: `rtf < 1` (transcreve mais rápido que o áudio) com carga na **iGPU** e **nada** na 4060.

### 5. systemd --user

```fish
printf '%s\n' \
  '[Unit]' 'Description=OpenVINO Whisper STT na iGPU (Agata, Fase 2)' 'After=default.target' \
  '' '[Service]' \
  'ExecStart=%h/agata/redesign/igpu/.venv/bin/python %h/agata/redesign/igpu/whisper_server.py' \
  'Restart=on-failure' 'Nice=5' \
  '' '[Install]' 'WantedBy=default.target' \
  > $HOME/.config/systemd/user/openvino-whisper.service
systemctl --user daemon-reload
systemctl --user start openvino-whisper.service
systemctl --user status openvino-whisper.service --no-pager
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:20130/health   # se existir
```
**Não** `enable` ainda (boot é Fase 7).

---

## Aceite

- `whisper_server.py --selftest <wav de ~30s>` → transcrição correta, `rtf < 1`.
- Durante a transcrição: `intel_gpu_top` mostra carga; `nvidia-smi` **não** lista o
  processo Whisper.
- `systemctl --user is-active openvino-whisper.service` → `active`.
- `redesign/igpu/.venv` não aparece em `git status`.

## Verificação independente

- **Quem:** fallback afinado ou Humano.
- **O quê:** que a inferência roda mesmo na iGPU (não caiu para CPU silenciosamente) e que
  o RTF < 1 se sustenta em 3 áudios diferentes, não um só.
- **Como:** rodar o `--selftest` com `device="CPU"` forçado e comparar o RTF (tem que ser
  claramente pior); `OV_GPU_...` logs ou `intel_gpu_top` durante.
- **Resultado:** anotar no LOG.

## Rollback

Não destrutivo:
```fish
systemctl --user stop openvino-whisper.service
rm -f $HOME/.config/systemd/user/openvino-whisper.service
systemctl --user daemon-reload
git checkout -- redesign/igpu
```
> ⚠️ **Remove o venv e o modelo convertido (~1–2 GB). Rode sozinho.**
> ```fish
> rm -rf redesign/igpu/.venv ~/.cache/agata/openvino/whisper
> ```

## Registro

- `STATUS.md`: P2-02 → "Feito"; anotar o modelo (small/medium) e o RTF medido.
- `LOG.md`: o `{text, rtf}`, a comparação iGPU vs CPU, o `nvidia-smi` durante, o resultado
  da verificação independente, `HEAD` no fim.
