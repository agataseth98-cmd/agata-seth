# redesign/systemd/ — units da Fase 7 (P7-01)

Espelho do que está instalado em `~/.config/systemd/user/` (P7-01, 2026-09-02).
**`agata.target` está `enable`d para o boot** (`systemctl --user enable agata.target`,
"sim" do Humano 2026-09-02 ~21:00) — no login, `default.target` → `agata.target` →
puxa os 5 membros. `llamacpp-agata` **não** sobe no boot (PartOf sem WantedBy).
Só `agata.target` está em `default.target.wants/`; os membros só em `agata.target.wants/`.

## Arquivos

| arquivo aqui | instala em | o que faz |
|---|---|---|
| `agata.target` | `~/.config/systemd/user/agata.target` | alvo que agrupa os serviços. Sem `Requires`/`Wants` — os membros se ligam pelo `[Install] WantedBy=agata.target`. |
| `agata-drain.service` | `~/.config/systemd/user/agata-drain.service` | oneshot `RemainAfterExit`. `After=` os 5 serviços ⇒ no stop para **antes** deles ⇒ `ExecStop` roda `drenar.py` (espera o WAL, não corta), e só então o systemd derruba os serviços. **Não** chama `systemctl` (isso deadlocka contra a transação de stop — visto no teste). |
| `dropin-generico.conf` | `<unit>.service.d/agata.conf` em `omniroute-sanitizer`, `openvino-whisper`, `openvino-embeddings`, `obsidian-ro-proxy` | `[Unit] PartOf=agata.target` + `[Install] WantedBy=agata.target`. |
| `dropin-omniroute.conf` | `omniroute.service.d/agata.conf` | igual ao genérico + `[Service] SuccessExitStatus=143 SIGTERM` — `omniroute` é `Type=simple` e o `ExecStop=omniroute stop` mata o próprio main (sai 143); sem isto o stop normal fica `failed`. |
| `dropin-llamacpp.conf` | `llamacpp-agata.service.d/agata.conf` | **só** `PartOf=agata.target` (sem `WantedBy`): o MoE **para** com o `agata down` (libera a VRAM da 4060) mas **não sobe** junto — fica sob demanda (`agata up --moe`). |
| `agata-jogo` | `~/.local/bin/agata-jogo` (`install -Dm755`, **sem sudo**) | **P7-02 (chat 6).** Wrapper: `stop agata.target` (drena) + `ollama stop` dos modelos ativos → roda o jogo via `game-performance` (wrapper oficial do CachyOS) → `trap EXIT` re-sobe `agata.target`. **Substitui o Feral GameMode** — o CachyOS já roda `ananicy-cpp` (renice automático) e GameMode brigaria com ele. `gamemode.ini.exemplo` foi removido. |

## Instalado assim (P7-01, com "vai" do Humano 2026-09-02 ~20:30)

```
mkdir -p ~/.config/systemd/user/{omniroute,omniroute-sanitizer,openvino-whisper,openvino-embeddings,obsidian-ro-proxy,llamacpp-agata}.service.d
cp agata.target agata-drain.service ~/.config/systemd/user/
cp dropin-generico.conf   ~/.config/systemd/user/omniroute-sanitizer.service.d/agata.conf   # idem whisper, embeddings, ro-proxy
cp dropin-omniroute.conf  ~/.config/systemd/user/omniroute.service.d/agata.conf
cp dropin-llamacpp.conf   ~/.config/systemd/user/llamacpp-agata.service.d/agata.conf
systemctl --user daemon-reload
systemctl --user enable omniroute omniroute-sanitizer openvino-whisper openvino-embeddings obsidian-ro-proxy agata-drain   # popula agata.target.wants/
# remover os default.target.wants/<unit> que o enable também cria (não queremos boot):
rm ~/.config/systemd/user/default.target.wants/{omniroute,omniroute-sanitizer,openvino-whisper,openvino-embeddings,obsidian-ro-proxy}.service
systemctl --user daemon-reload
```

`agata-drain` foi `enable`d p/ `agata.target.wants/` (senão o target não puxa o dreno).
`agata.target` foi `enable`d p/ `default.target.wants/` (boot) — "sim" do Humano
2026-09-02 ~21:00. Rollback do boot: `systemctl --user disable agata.target`.

## Verificação P7-01 (S7, 2026-09-02 ~20:40) — PASS

- **`stop agata.target` com efeito pendente no WAL:** `agata-drain` segurou 26 s
  (`drenar.py`), logou `AVISO -- 1 efeito(s) ainda pendente(s) ... NAO cortados` com
  `thread=/node=/passo=/chave=`, saiu 0 (`Result=success`). Os 5 serviços só caíram
  **depois** do dreno. Nenhum membro `failed`.
- **`stop agata.target` com WAL limpo:** `dreno: WAL limpo` — teardown em 1 s, todos
  `Result=success`.
- **`start agata.target`:** os 5 voltam em ~6 s; portas `:20127 :20128 :20130 :20134
  :27124 :27125` UP.
- **VRAM da 4060:** `start llamacpp-agata` ⇒ 56 → 6229 MiB; `stop agata.target` ⇒
  MoE `inactive` (`success`) e 4060 volta a **54 MiB**. Checkpoint/WAL intactos
  (`drenar.py` não apaga nada).
- **Boot:** `default.target.wants/` sem nada do Agata; `agata.target is-enabled = disabled`.

## Rollback

```
systemctl --user disable agata.target agata-drain omniroute omniroute-sanitizer openvino-whisper openvino-embeddings obsidian-ro-proxy
rm ~/.config/systemd/user/agata.target ~/.config/systemd/user/agata-drain.service
rm ~/.config/systemd/user/{omniroute,omniroute-sanitizer,openvino-whisper,openvino-embeddings,obsidian-ro-proxy,llamacpp-agata}.service.d/agata.conf
systemctl --user daemon-reload
```
Os serviços seguem sobíveis um a um como antes.
