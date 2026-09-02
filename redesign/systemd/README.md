# redesign/systemd/ — units da Fase 7 (RASCUNHO, não instaladas no boot)

Rascunhos para o P7-01/P7-02. **Nada aqui é `enable`d no boot** — isso é decisão do
`agata up`/`agata.target` + o "vai" do Humano.

- `agata.target` — alvo que agrupa as units do Agata.
- `*.service.dropin` — drop-ins que ligam cada service ao `agata.target` + `ExecStop` que
  drena (`agata down`).
- `gamemode.ini.exemplo` — o hook `[custom]` do Feral GameMode (precisa `pacman -S gamemode`).

Instalação real = P7-01 (com "vai"): copiar para `~/.config/systemd/user/`, `daemon-reload`,
`systemctl --user enable agata.target` (aí sim boot).
