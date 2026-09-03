# P7-02 — hook "jogo liga/desliga o Agata" + OLLAMA_KEEP_ALIVE

**Status:** ⏳ **PARCIAL** — o hook (`agata-jogo`) está **FEITO e testado** (chat 6, 03/09);
falta o Humano fiar em Steam/Lutris/Heroic. `OLLAMA_KEEP_ALIVE` = 1 `sudo`, opcional agora.

**Objetivo:** lançar um jogo → `agata down` (libera a 4060) → ao fechar, `agata up`.

**Pré-requisitos:** P7-01 FEITO.

## Mudança de plano (chat 6, 03/09) — NÃO instalar Feral GameMode

Pesquisa + medição na Máquina:
- O **CachyOS já roda `ananicy-cpp`** (`systemctl is-active` = active), que faz **renice
  automático** por regra, inclusive de jogos.
- **Feral GameMode também faz renice** → os dois brigam pelo mesmo processo. A wiki do
  CachyOS **diz para não usar Feral GameMode** por isso.
- O caminho oficial do CachyOS é **`game-performance`** (do pacote `cachyos-settings`, já
  em `/usr/bin/game-performance`): põe o `power-profiles-daemon` em `performance` pelo
  tempo do jogo, **sem renice**, sem daemon novo.
- `gamemode` existe nos repos (`extra`, `cachyos-extra-v3`), mas instalá-lo = brigar com o
  `ananicy-cpp` e contrariar a orientação da distro.

**Decisão (princípio-espelho — nó determinístico que nós controlamos, sem pacote em
conflito):** o hook vira um **wrapper que nós versionamos**, `agata-jogo`, que compõe com o
`game-performance`. Zero `sudo`, zero pacote novo.

## O que ficou pronto

- **`redesign/systemd/agata-jogo`** (fonte versionada) → instalado em
  **`~/.local/bin/agata-jogo`** (`~/.local/bin` já está no PATH; `install -Dm755`, sem sudo).
- O que faz, em ordem: (1) `systemctl --user stop agata.target` (o `agata-drain` drena o
  WAL — nunca corta um commit; para os 5 + o MoE); (2) `ollama stop` de cada modelo
  carregado no Ollama de **produção** (:11434) — sem sudo, sem tocar o `ollama.service`, só
  descarrega da VRAM; (3) roda o jogo via `game-performance` (ou direto se ele sumir);
  (4) `trap ... EXIT` re-sobe `agata.target` **sempre** — inclusive se o jogo crashar ou
  levar Ctrl-C.

## Passos que faltam (Humano)

1. **Fiar o wrapper nos lançadores** (uma vez cada):
   | lançador | onde | valor |
   |---|---|---|
   | Steam | Propriedades do jogo → Opções de inicialização | `agata-jogo %command%` |
   | Lutris | Configurações → Opções de execução → "Command prefix" | `agata-jogo` |
   | Heroic | Settings → Advanced → "Wrapper command" | `agata-jogo` |
2. **(Opcional, 1 `sudo`) `OLLAMA_KEEP_ALIVE=30s` em `ollama.service`** — ver
   `P7-02-RUNBOOK.md` bloco B. Com o `agata-jogo` já fazendo `ollama stop` no start do jogo,
   isto deixou de ser necessário para o aceite; continua bom para o caso geral "Ollama
   ocioso não deve acampar na VRAM". Toca serviço de produção → mãos do Humano, sem pressa.

## Aceite
- Lançar um jogo pelo wrapper → os 5 serviços + o MoE saem da 4060, o Ollama de produção
  descarrega, e tudo retoma ao fechar o jogo (aceite do ROADMAP).
- **Verificado em 03/09 (chat 6):** `agata-jogo sh -c 'sleep 3'` → `agata.target` parou,
  `game-performance` lançou, e ao sair os 6 membros voltaram `active` (portas
  :20127/:20128/:20130/:20134/:27125 UP, whisper+embeddings `/health` 200, 4060 em 56 MiB).

## Rollback
`rm ~/.local/bin/agata-jogo`; tirar o wrapper das opções dos lançadores. (Se o bloco B foi
feito: `sudo rm /etc/systemd/system/ollama.service.d/agata-keepalive.conf` +
`daemon-reload` + `restart ollama` — o `override.conf` de produção fica intacto.)

## Registro
`STATUS.md`: P7-02 → hook FEITO, falta fiar nos lançadores (Humano) + `OLLAMA_KEEP_ALIVE`
opcional. `LOG.md`: a pesquisa (ananicy vs GameMode), o wrapper, o teste.
