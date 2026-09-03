# P2-00 — inventário da iGPU + baseline da RTX 4060

**Objetivo:** saber, com medida, o que está na 4060 hoje (display? STT? nada?), qual é a
iGPU exata e se ela está utilizável para compute — antes de mover qualquer coisa.

**Status:** ✅ **FEITO — 2026-09-02 ~11:07 (relógio da máquina).** `redesign/igpu/INVENTARIO.md`
escrito. Achados: iGPU = Intel UHD RPL-S `[8086:a78b]` / `i915` / nó `renderD129`; **display
já está na iGPU** (painel `eDP-1` em `card2`; kwin usa 7 MiB na 4060) → P2-01 vira
verificação, não migração de risco; baseline 4060 em repouso = **~54 MiB / ~16 W / 0 %
util**; **nenhum STT existe** (P2-02 é greenfield); lacuna: iGPU sem `intel-compute-runtime`
(pré-req do plugin GPU do OpenVINO). Nada instalado (glxinfo/clinfo já estavam). S7: n/a
(só leitura).

**Pré-requisitos:** Fase 2 recebeu o "vai". (Ordem recomendada do ROADMAP: a Fase 2 pode
correr em paralelo com a Fase 3.)

**Arquivos que a tarefa toca:**
- `redesign/igpu/INVENTARIO.md` (novo) — a fotografia do estado atual
- `redesign/tasks/P2-00-*.md`

Nada de sistema muda neste passo. É só leitura.

---

## Contexto (PESQUISA C2, 01/09/2026)

A iGPU desta máquina foi descrita como **UHD (Raptor Lake), ~32 EU** — não Arc. CPU é
i7-13650HX (Raptor Lake-HX, mobile). Expectativa realista: distil-whisper int8 em tempo
real + **um** modelo de embedding pequeno. Nada além disso na iGPU. **Confirmar o modelo
real no passo 1** (a PESQUISA disse "Raptor Lake-S", o que não bate com HX — reconferir).

---

## Passos

### 1. Identificar a iGPU e o driver

```fish
lspci -nn | grep -Ei 'vga|display|3d'
ls -l /dev/dri/
cat /sys/class/drm/card*/device/uevent 2>/dev/null | grep -E 'DRIVER|PCI_ID'
# ferramentas Intel (instalar se faltar -- passo de leitura, mas instala util):
type -q intel_gpu_top; or sudo pacman -S --noconfirm intel-gpu-tools
timeout 3 intel_gpu_top -l 2>/dev/null | head
glxinfo -B 2>/dev/null | grep -Ei 'vendor|renderer|device'   # de mesa-utils
```
Colar de volta: tudo.
Objetivo: nome exato da iGPU, driver em uso (`i915` ou `xe`), `/dev/dri/renderD*` presente.

### 2. Onde o display está agora

```fish
echo "sessão: $XDG_SESSION_TYPE"
# Wayland/KDE:
kscreen-doctor -o 2>/dev/null
# qual GPU renderiza o compositor:
sudo cat /sys/kernel/debug/dri/*/clients 2>/dev/null
ps -o pid,comm,args -C kwin_wayland -C Xwayland 2>/dev/null
# a 4060 está segurando o display?
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv
nvidia-smi   # a lista de processos gráficos no rodapé
```
Colar de volta: tudo.
Objetivo: saber se `kwin_wayland`/`Xwayland`/`gnome-shell` aparecem na 4060 (`nvidia-smi`
rodapé) ou não; se o laptop tem MUX / está em modo híbrido.

### 3. Baseline da 4060 — o que ela carrega em repouso e sob uso normal

```fish
# repouso (sem jogo, sem inferência pesada):
nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used,power.draw --format=csv -l 1 -c 10
# processos:
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
fuser -v /dev/nvidia* 2>&1 | head -40
```
Colar de volta: as 10 amostras + a lista de processos.
Objetivo: número de referência — "a 4060 em repouso usa X MB / Y W por causa de
{display, ollama keep-alive, nada}". É contra isso que a Fase 2 vai comparar.

### 4. STT hoje — o Whisper/voz atual roda onde?

```fish
systemctl --user list-units '*whisper*' '*stt*' '*voice*' 2>/dev/null
grep -rEl 'whisper|faster-whisper|stt' ~/.hermes/ ~/.config/ 2>/dev/null | head
# se houver um serviço de voz, ver o device dele
```
Colar de volta: o que existir.
Objetivo: saber se já há STT e em qual device (provável: CPU ou 4060).

### 5. `INVENTARIO.md`

Escrever `redesign/igpu/INVENTARIO.md`: iGPU (modelo/driver/nós dri), display (onde
renderiza, MUX sim/não), baseline 4060 (MB/W em repouso + processos), STT atual. Com
data e comandos usados.

---

## Aceite

- `redesign/igpu/INVENTARIO.md` existe e responde: (a) modelo e driver da iGPU; (b) se o
  display está na 4060 ou na iGPU; (c) baseline numérico da 4060 em repouso; (d) onde o
  STT roda hoje.
- `/dev/dri/renderD128` (ou equivalente) existe e pertence à iGPU (não só à NVIDIA).
- Nada instalado além de `intel-gpu-tools` / `mesa-utils` (ferramentas de leitura).

## Verificação independente

- **Quem:** fallback afinado ou Humano.
- **O quê:** que o baseline da 4060 foi medido de verdade (10 amostras, não uma), e que a
  iGPU está exposta ao SO (nó `renderD*` + driver carregado), senão a Fase 2 inteira não
  encaixa.
- **Como:** reler `INVENTARIO.md` contra as saídas cruas coladas no LOG; `ls -l /dev/dri/by-path/`.
- **Resultado:** anotar no LOG.

## Rollback

Nada a desfazer (só leitura). Se instalou as ferramentas e quer tirar:
```fish
sudo pacman -Rns intel-gpu-tools mesa-utils
```

## Registro

- `STATUS.md`: P2-00 → "Feito"; anotar iGPU real e se o display já está nela.
- `LOG.md`: as saídas-chave (iGPU, baseline 4060, STT atual), o resultado da verificação
  independente, `HEAD` no fim.
