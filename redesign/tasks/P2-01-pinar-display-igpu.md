# P2-01 — pinar o display na iGPU (tirar o compositor da RTX 4060)

**Objetivo:** o compositor (kwin_wayland / Xwayland) renderiza na **iGPU**, não na 4060 —
de forma explícita e persistente. Item do aceite da Fase 2: "`nvidia-smi` sem carga de
display na 4060".

**Pré-requisitos:** P2-00 FEITO (INVENTARIO diz onde o display está e se há MUX).

> **CLASSE DE RISCO ALTA (CONTINUIDADE §7): mexe na sessão gráfica.** Um erro aqui deixa a
> máquina sem display gráfico no próximo login. **Revisão de plano por 2º par de olhos
> antes.** Regras deste arquivo-tarefa:
> - Toda mudança é testada **numa sessão nova ao lado**, ou com um **caminho de reversão
>   pronto e testado antes de aplicar**.
> - Ter acesso a TTY (`Ctrl+Alt+F3`) e saber reverter por lá.
> - Nunca aplicar às cegas: se o INVENTARIO já mostrar o display na iGPU, esta tarefa
>   vira só "tornar explícito + verificar", sem troca de fato.

---

## Passos

### 0. Se o INVENTARIO já diz "display na iGPU"

Pular para o passo 3 (tornar explícito/persistente + verificar). Não há troca a fazer.

### 1. Caminho de reversão — preparar e testar ANTES

```fish
# guardar o estado atual
mkdir -p $HOME/redesign-igpu-backup
cp -a /etc/environment $HOME/redesign-igpu-backup/ 2>/dev/null; or true
cp -a ~/.config/plasma-workspace/env/ $HOME/redesign-igpu-backup/plasma-env 2>/dev/null; or true
cp -a ~/.config/kwinrc $HOME/redesign-igpu-backup/ 2>/dev/null; or true
# se houver xorg.conf.d / modeset:
sudo cp -a /etc/X11/xorg.conf.d/ $HOME/redesign-igpu-backup/xorg.conf.d 2>/dev/null; or true
ls -R $HOME/redesign-igpu-backup
```
Colar de volta: o `ls -R`.
**Escrever o comando de reversão exato** (restaurar esses arquivos + reboot) no LOG antes
de seguir.

### 2. Aplicar o pin (o método depende do INVENTARIO)

Casos possíveis (escolher pelo que o P2-00 achou):

- **Laptop com MUX / modo híbrido (mais comum com RTX 4060):** garantir modo "híbrido"
  (não "dGPU only") no firmware/`supergfxctl`/`envycontrol`, para o compositor poder usar
  a iGPU:
  ```fish
  type -q envycontrol; and envycontrol --query
  # se estiver em 'nvidia' (dGPU only), voltar para 'hybrid':
  # sudo envycontrol -s hybrid    # <- só depois da revisão de plano; reboot depois
  ```
- **PRIME render offload (compositor na iGPU, jogos na 4060 sob demanda):** garantir que o
  compositor não está com `__NV_PRIME_RENDER_OFFLOAD` / `DRI_PRIME` forçando a NVIDIA;
  deixar o KWin escolher a iGPU como GPU primária:
  ```fish
  # KDE Wayland: a GPU primária vem do 1º nó DRM; forçar via env do compositor se preciso:
  #   ~/.config/plasma-workspace/env/kwin-igpu.sh :  export KWIN_DRM_DEVICES=/dev/dri/by-path/pci-<BDF-da-iGPU>-card
  ```
- **Xorg:** `xorg.conf.d` com a iGPU como `Device` primário e a NVIDIA como secundária
  (`Option "PrimaryGPU" "no"` no `nvidia`).

Aplicar **uma** mudança, reiniciar a sessão gráfica (logout, ou reboot).

### 3. Tornar explícito e persistente

- Registrar num arquivo versionável qual foi a mudança (`redesign/igpu/DISPLAY-PIN.md`):
  o método, o arquivo tocado, o BDF da iGPU, o comando de reversão.

### 4. Verificar

```fish
echo "sessão: $XDG_SESSION_TYPE"
nvidia-smi   # rodapé de processos gráficos -- kwin_wayland/Xwayland NÃO devem aparecer
nvidia-smi --query-gpu=memory.used,power.draw --format=csv
sudo cat /sys/kernel/debug/dri/*/clients   # o compositor tem que estar no card da iGPU
timeout 3 intel_gpu_top -l 2>/dev/null | head   # a iGPU agora tem carga de render
```
Colar de volta: tudo.
Sucesso: `kwin_wayland`/`Xwayland` fora do `nvidia-smi`; `memory.used` da 4060 caiu para
perto de zero (menos o que Ollama/keep-alive segura); a iGPU mostra carga de render.

---

## Aceite

- `nvidia-smi` não lista o compositor (`kwin_wayland`, `Xwayland`, `gnome-shell`) nos
  processos gráficos.
- `memory.used` da 4060 em repouso ≤ o baseline do P2-00 **menos** a fração de display
  que o INVENTARIO atribuiu ao compositor (número no LOG).
- O pin está num arquivo (`redesign/igpu/DISPLAY-PIN.md`) com o comando de reversão.
- A sessão gráfica volta normal após reboot (testado).

## Verificação independente

- **Quem:** o Humano (é a máquina dele; o risco é sessão gráfica) + um fallback conferindo o diff.
- **O quê:** que a reversão foi testada **antes** de aplicar; que após um reboot completo
  o display sobe e o compositor está na iGPU.
- **Como:** reboot; `nvidia-smi` + `/sys/kernel/debug/dri/*/clients` de novo; confirmar
  que o `redesign-igpu-backup/` + o comando de reversão no LOG restauram o estado.
- **Resultado:** anotar no LOG.

## Rollback

> ⚠️ **Restaura a config de display. Rode sozinho; tenha um TTY (Ctrl+Alt+F3) à mão.**
> ```fish
> # restaurar os arquivos de $HOME/redesign-igpu-backup/ para os caminhos originais
> # (o comando exato foi escrito no LOG no passo 1)
> # se usou envycontrol: sudo envycontrol -s hybrid   (ou o modo anterior)
> sudo reboot
> ```

## Registro

- `STATUS.md`: P2-01 → "Feito"; anotar o método usado e o delta de MB/W na 4060.
- `LOG.md`: o comando de reversão (passo 1), o antes/depois de `nvidia-smi`, o resultado
  da verificação independente (incl. o reboot de teste), `HEAD` no fim.
