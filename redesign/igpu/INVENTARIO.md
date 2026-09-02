# redesign/igpu/INVENTARIO.md — fotografia do estado (P2-00)

**Não é canon.** Branch `redesign`, Fase 2. Só leitura — nada de sistema mudou aqui.
Medido em **2026-09-02 ~11:07 -03** (relógio da máquina), sessão Claude Code na Máquina.

## Resumo (as 4 perguntas do aceite)

| # | pergunta | resposta |
|---|---|---|
| a | modelo e driver da iGPU | **Intel Raptor Lake-S UHD Graphics** `[8086:a78b]` rev 04, PCI `0000:00:02.0`, driver **`i915`**, Mesa 26.2.1. Nó de render: **`/dev/dri/renderD129`** (NÃO o 128 — a NVIDIA pegou o 128). |
| b | display está na 4060 ou na iGPU? | **Já está na iGPU.** O painel `eDP-1` está no conector de `card2` (i915). `kwin_wayland` usa **7 MiB** na 4060 (handle de modo híbrido, não render); o renderer GL default é `Mesa Intel(R) Graphics (RPL-S)`. → **P2-01 vira "tornar explícito + verificar", não migração de risco.** |
| c | baseline numérico da 4060 em repouso | **54 MiB / 8188** de VRAM · **~16–17 W** (média `nvidia-smi -q`: 16,75 W) · **GPU-util 0 %** (SM/mem/enc/dec/ofa todos 0) · 42–44 °C · 10 amostras `nvidia-smi dmon`, estável. Consumidores: `kwin_wayland` 7 MiB, `Xorg` 4 MiB, Brave com `/dev/nvidiactl` aberto. Nenhum compute. Ollama keep-alive **não** residente no momento. |
| d | onde o STT roda hoje | **Não existe STT.** Zero unit `*whisper*`/`*stt*`/`*voice*` (só `speech-dispatcher`, que é TTS de acessibilidade). Nada de `whisper`/`faster-whisper` em `~/.hermes/` nem `~/.config/`. → **P2-02 é greenfield**, não migra nada. |

## Detalhe

### iGPU e nós DRI

```
0000:00:02.0 VGA Intel Raptor Lake-S UHD Graphics [8086:a78b] (rev 04)   -> i915
0000:01:00.0 VGA NVIDIA AD107M [GeForce RTX 4060 Max-Q / Mobile] [10de:28e0]

/dev/dri/by-path/pci-0000:00:02.0-card   -> card2      (Intel i915)
/dev/dri/by-path/pci-0000:00:02.0-render -> renderD129 (Intel i915)   <- nó de compute da iGPU
/dev/dri/by-path/pci-0000:01:00.0-card   -> card1      (NVIDIA)
/dev/dri/by-path/pci-0000:01:00.0-render -> renderD128 (NVIDIA)
```

`renderD129` é `crw-rw-rw-` (render group, world-rw) — a iGPU **está exposta ao SO**.

A "-S" no nome não é erro: o i7-13650HX usa a die RPL-S com a UHD Graphics GT1 (`a78b`).
A dúvida da nota de PESQUISA ("HX não bate com -S") não procede — a PESQUISA estava certa.

### Display / compositor

- Sessão: **Wayland / KDE**. Único output: `eDP-1` (painel interno), 1920×1200@165 Hz, escala 1,5.
- `eDP-1` pendura em `card2` (i915). `kscreen-doctor -o`: 1 output, sem MUX, sem tela externa.
- `kwin_wayland` (pid 2842): 7 MiB na 4060. `Xwayland :1` ativo (rootless, para apps X11).
- `glxinfo -B`: renderer default = `Mesa Intel(R) Graphics (RPL-S)`. `DRI_PRIME=1` → `zink`
  sobre a `NVIDIA RTX 4060` (offload opt-in). **Modo híbrido: iGPU move o desktop, NVIDIA é
  offload sob demanda.**

### Baseline 4060 (`nvidia-smi dmon -s pucm -c 10`)

```
# gpu  pwr gtemp  sm  mem  enc  dec  ofa  mclk  pclk    fb  bar1
    0   16    43   0    0    0    0    0  8001  2250    54     3     (x10, estável)
```
(a 1ª amostra de `pwr` veio 590 W — artefato de leitura do dmon no 1º tick; `-q` confirma
16,75 W média / 17,08 W instantâneo.)

`nvidia-smi --query-compute-apps`: só `kwin_wayland` 7 MiB. Rodapé gráfico: `Xorg` 4 MiB +
`kwin_wayland` 7 MiB. `fuser /dev/nvidia*`: `brave` com `/dev/nvidiactl`.

> **Nota de ferramenta:** este driver (`NVIDIA-SMI 610.57.04`, CUDA UMD 13.3) **não aceita**
> `power.draw` nem `temperature.gpu` em `--query-gpu` (a query inteira falha se um deles
> entra na lista). Para potência/temperatura usar `nvidia-smi dmon` ou `nvidia-smi -q`.
> `memory.used`/`utilization.gpu` funcionam sozinhos.

## Lacunas achadas (entram como pré-requisito das próximas tarefas)

1. **iGPU sem runtime de compute.** `clinfo -l` só lista `NVIDIA CUDA` — não há plataforma
   Intel OpenCL/Level-Zero. O plugin GPU do OpenVINO precisa de **`intel-compute-runtime`**
   (Level Zero `libze_intel_gpu` + OpenCL). Instalar em P2-02 (sudo). `ggml-openvino` existe
   no repo (visto no P3-03) — não é necessário agora, mas é opção.
2. `libva-utils` ausente (`vainfo` não roda) — cosmético; instalar se precisar inspecionar VA-API.
3. `intel-gpu-tools` (`intel_gpu_top`) ausente — leitura de carga da iGPU; instalar em P2-02
   para medir RTF do Whisper na iGPU.

## Impacto no plano da Fase 2

- **P2-01 (pinar display na iGPU) — risco cai de ALTO para BAIXO.** O display já está na iGPU;
  a tarefa vira: (a) tornar explícito (garantir que nenhum `.desktop`/env force render na
  NVIDIA para o compositor), (b) verificar após um reboot de teste que `eDP-1` continua em
  `card2` e a 4060 fica em ~54 MiB. Reversão ainda preparada, mas o "salto no escuro" sumiu.
- **P2-02 (openvino-whisper) — greenfield.** Sem STT para desmontar. Pré-req: instalar
  `intel-compute-runtime` + `intel-gpu-tools`; venv `redesign/igpu/.venv` (gitignorado, conferido).
- **P2-03 (openvino-embeddings) — idem**, reusa o `intel-compute-runtime` do P2-02.
- **Alvo de comparação da Fase 2:** 4060 em repouso = **~54 MiB / ~16 W / 0 % util**. É contra
  esse número que "display + STT + embeddings fora da 4060" tem que se sustentar.

## Comandos usados

`lspci -nn` · `ls -l /dev/dri{,/by-path}` · `cat /sys/class/drm/card*/device/uevent` ·
`kscreen-doctor -o` · `ps -C kwin_wayland -C Xwayland` · `nvidia-smi` (default, `dmon`, `-q`,
`--query-compute-apps`) · `fuser -v /dev/nvidia*` · `glxinfo -B` (+ `DRI_PRIME=1`) ·
`clinfo -l` · `systemctl --user list-units/list-unit-files` · `grep -rEl whisper ~/.hermes ~/.config`.
