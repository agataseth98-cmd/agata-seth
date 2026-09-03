# redesign/igpu/DISPLAY-PIN.md — o display está na iGPU (P2-01)

**Não é canon.** Branch `redesign`, Fase 2. Medido **2026-09-02 ~11:12 -03** (relógio da
máquina), sessão Claude Code na Máquina.

## Conclusão: nada a mudar

O compositor **já renderiza na iGPU** e isso é **estrutural**, não configuração frágil:

- O painel interno `eDP-1` é um conector de **`card2`** (Intel `i915`, PCI `0000:00:02.0`).
- A RTX 4060 (`card1`, PCI `0000:01:00.0`) **não tem caminho de display para o painel** —
  os conectores dela (`card1-DP-1`, `card1-DP-2`, `card1-HDMI-A-1`) são para telas externas;
  o painel do laptop está fisicamente ligado à iGPU. É um laptop Optimus sem MUX para o eDP.
- Portanto o KWin **tem** que usar a iGPU para acender a tela. A 4060 é só alvo de PRIME
  render offload (`DRI_PRIME=1` / jogos), sob demanda.

P2-01 estava marcado **risco ALTO** (mexer na sessão gráfica). Com o P2-00, caiu para
**nenhuma mudança** — só documentar e verificar.

## Estado verificado (P2-00 + P2-01)

| item | valor |
|---|---|
| sessão | Wayland / KDE Plasma |
| output | 1× `eDP-1` (painel interno), 1920×1200@165, escala 1,5. Sem tela externa, sem MUX. |
| GPU do compositor | iGPU. `kwin_wayland` aparece no `nvidia-smi` com **7 MiB** (handle de modo híbrido p/ offload, não render de fato); `Xorg` 4 MiB. |
| renderer GL default | `Mesa Intel(R) Graphics (RPL-S)` (`glxinfo -B`). `DRI_PRIME=1` → `zink` sobre a 4060. |
| 4060 em repouso | **54 MiB / 8188 · ~16 W · 0 % util · 42–44 °C** (baseline P2-00) |
| KWin backend | log: `No backend specified, automatically choosing drm` — escolhe o nó DRM padrão (a iGPU, que é quem tem o painel) |

## O que NÃO existe (procurado, nada encontrado) — por isso nada força a 4060

- `~/.config/plasma-workspace/env/` — **não existe** (nenhum script de env do Plasma).
- `~/.config/environment.d/`, `/etc/environment`, `/etc/environment.d/` — nenhuma linha
  `PRIME` / `DRI_PRIME` / `__NV_PRIME_RENDER_OFFLOAD` / `KWIN_DRM_DEVICES` / `NVIDIA`.
- `/etc/X11/xorg.conf.d/` — só `00-keyboard.conf`. Sem `Device` / `PrimaryGPU`.
- `envycontrol` / `supergfxctl` / `optimus-manager` / `prime-select` — **nenhum instalado**.
- `~/.config/kwinrc` — sem seção de GPU.
- `/proc/cmdline` — sem flag de GPU (`nomodeset`, `nvidia-drm.modeset`, etc.).

## "Tornar explícito e persistente" — decisão: não adicionar env pin

O arquivo-tarefa sugeria opcionalmente um `KWIN_DRM_DEVICES=/dev/dri/by-path/pci-0000:00:02.0-card`.
**Não feito de propósito:** a garantia física (o painel é da iGPU; a 4060 não tem trilha de
display para o eDP) é mais forte que uma env var, e a env var poderia quebrar sozinha numa
mudança de path do `by-path`. Manter a espinha mínima (princípio-espelho). Se um dia uma
tela externa entrar na 4060 e o KWin migrar o primário, revisitar aqui.

## Verificação (aceite P2-01)

- `nvidia-smi` rodapé: compositor sem carga de render (kwin 7 MiB / Xorg 4 MiB = handles de
  modo híbrido, não render — a 4060 fica em 54 MiB / 0 % util). ✅ (interpretação do aceite:
  "sem carga de display", não "processo ausente da lista" — o handle de offload é benigno)
- `memory.used` da 4060 em repouso = **54 MiB**, já no piso; não havia fração de display a
  remover (o INVENTARIO não atribuiu render de compositor à 4060). ✅
- Reversão: **não aplicável** — nada foi mudado. `redesign-igpu-backup/` não foi criado
  (não havia o que restaurar).
- Reboot de teste: a sessão atual **já é** uma sessão pós-boot nesta exata config (o laptop
  vem rebootando neste estado; `uptime` > 1 dia antes desta sessão). Um reboot dedicado só
  confirmaria o status quo. **Pendente só se o Humano quiser a confirmação explícita** —
  então: `sudo reboot`, e depois reconferir `eDP-1` em `card2` + 4060 em ~54 MiB.

## Rollback

Nada a desfazer.
