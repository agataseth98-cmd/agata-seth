# Mudanças de sistema — 10/09/2026 (para consolidar em MEMÓRIAS)

Nota de registro, **não** proposta estrutural (não mexe em `REGRAS.md` /
`PROJETO.md` / `scripts/*` / `.githooks/*` / `config/*`). Sessão de manutenção do
laptop Predator (Claude Sonnet 5, Claude Code). Pedido do Humano: "avise o
sistema Agata para atualizar depois essas alterações". Dobrar isto numa entrada
de MEMÓRIAS na próxima consolidação.

## 1. Atalhos da Seth — mudança de comportamento (fonte + instalado)

Ordem do Humano nesta sessão: *"deixe parar Seth parando tudo e reiniciar Seth
reiniciando tudo"*.

- **`seth-parar`** (`~/.local/bin/seth-parar` + `~/agata/redesign/systemd/seth-parar`):
  antes parava só as frentes e mantinha a espinha (`agata.target`) de pé. Agora
  também:
  - descarrega os modelos ativos do Ollama de produção (`ollama stop` por modelo,
    sem sudo, sem tocar o `ollama.service`);
  - `systemctl --user stop agata.target` no fim — o `agata-drain` continua
    drenando o WAL antes de derrubar os 5 serviços + o MoE `:20129`.
  - `notify-send` mudou de "frentes parados (espinha segue de pe)" para "parada
    por completo (frentes + espinha)".
- **`seth`** (`~/.local/bin/seth` + fonte): sem mudança funcional — já fazia
  `systemctl --user start agata.target` como primeiro passo. Só o cabeçalho foi
  atualizado para dizer que sobe a espinha inteira e é a contraparte de
  `seth-parar`. O MoE `:20129` continua sob demanda (decisão do README de
  `redesign/systemd/`).

Instalado == fonte versionada conferido (`diff -q`), `bash -n` PASS nos 3.
Git working tree do repo `agata`: `M redesign/systemd/{agata-jogo,seth,seth-parar}`
— **não commitado**, aguardando revisão do Humano.

## 2. `agata-jogo` — offload de GPU em MUX híbrido (fonte + instalado)

O MUX do BIOS voltou para **Optimus/híbrido** (as duas GPUs no `lspci`, painel
eDP-1 na iGPU Intel — confirmado nesta sessão). O `agata-jogo` chamava
`game-performance "$@"` direto, o que faria o jogo rodar na **iGPU Intel**.

Acrescentado: se `prime-run` existe **e** o `lspci` mostra Intel VGA **e** NVIDIA
VGA/3D, o wrapper injeta `prime-run` antes do comando do jogo (via array `_pr`).
Em "Discrete only" o bloco fica vazio e não muda nada. Fecha a lacuna entre o
`agata-jogo` (escrito quando o MUX era discrete-only, 03/09) e o estado atual.

Opção de inicialização recomendada na Steam agora:
`agata-jogo mangohud %command%` (o `prime-run` entra sozinho quando é híbrido).

## 3. Confirmação: Feral GameMode NÃO instalado (era decisão do projeto)

O Humano perguntou se o GameMode conflita com "o nativo do CachyOS". Confere com
o que `redesign/systemd/README.md` já registra (P7-02, chat 6): CachyOS roda
`ananicy-cpp` (renice automático) e a wiki manda **não** usar Feral GameMode;
caminho oficial é `game-performance` (pacote `cachyos-settings`, `/usr/sbin/`).
Nada foi instalado. `agata-jogo` já compõe com `game-performance`.

## 4. Mudanças fora do Agata (laptop) — só para contexto

Aplicadas nesta sessão, sem relação com o canon:

- **VRR** do painel eDP-1: `Never` → `Automatic` (`kscreen-doctor`).
- **KWin `AllowTearing`**: `false` → `true` (`~/.config/kwinrc`).
- Autostarts órfãos `picom` e `pasystray` (X11/PulseAudio, inúteis no KDE
  Wayland, falhavam todo login): `systemctl --user mask`.

Pendentes, precisam de `sudo` (na mão do Humano): desativar `predator-rgb.service`
(script `predator-rgb-boot.sh` não existe, falha todo boot); `blacklist spd5118`
+ remover o `predator-suspend-inhibit.service` para reativar o suspend; limpar
`/usr/lib/modules/7.0.10-1-cachyos` (órfão); `pacman -Rns linux-headers` (kernel
stock não instalado) + `pacdiff`; tirar `mem_sleep_default=s2idle` do GRUB.
