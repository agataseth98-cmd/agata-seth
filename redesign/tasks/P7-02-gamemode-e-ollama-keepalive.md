# P7-02 — hook Feral GameMode + OLLAMA_KEEP_ALIVE (INSTALA + sudo)

**Status:** ⏳ **PENDE do "vai"** — `pacman -S gamemode` (sudo) + drop-in de env em
`ollama.service` (unit de sistema, sudo).

**Objetivo:** lançar jogo por `gamemoderun` → `agata down` (libera a 4060) → ao fechar,
`agata up`. `OLLAMA_KEEP_ALIVE=30s` para o Ollama soltar VRAM rápido.

**Pré-requisitos:** P7-01 FEITO.

## Passos
1. **INSTALA:** `sudo pacman -S gamemode lib32-gamemode`.
2. `cp redesign/systemd/gamemode.ini.exemplo ~/.config/gamemode.ini` (o `[custom]
   start=/end=` já aponta para o `cli.py down`/`up`).
3. **sudo:** `sudo systemctl edit ollama.service` → `[Service]\nEnvironment=OLLAMA_KEEP_ALIVE=30s`
   → `sudo systemctl restart ollama`. (OU `OLLAMA_KEEP_ALIVE` no `~/.ollama` se o serviço
   ler — conferir; o ollama de produção é intocado até a Fase 8, mas o env é operação, não
   config de modelo — decidir com o Humano.)
4. Teste: `gamemoderun glxgears` (ou um jogo) → `nvidia-smi` mostra a 4060 liberada pelo
   Agata; fechar → `agata up` re-sobe. `ollama ps` esvazia ~30 s após o último uso.

## Aceite
- Jogo por `gamemoderun` → Agata sai da 4060 sozinho e retoma ao fechar (aceite do ROADMAP).
- `OLLAMA_KEEP_ALIVE=30s` efetivo (`ollama ps` esvazia rápido).

## Rollback
`rm ~/.config/gamemode.ini`; `sudo systemctl revert ollama.service`; `sudo pacman -Rns gamemode`.

## Registro
`STATUS.md`: P7-02 → "Feito". `LOG.md`: o teste com `gamemoderun`, `HEAD`.
