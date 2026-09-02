# P7-00 — inventário + plano da Fase 7, e o que bloqueia

**Status:** ✅ **FEITO — 2026-09-02 ~19:26 (relógio da máquina).** Inventário +
rascunhos (`redesign/systemd/`) + P7-01/02/03 escritos. **Fase 7 NÃO roda autônoma
hoje:** (1) HD só amanhã (restic/timer/P-12/restore); (2) `sudo` (gamemode,
`OLLAMA_KEEP_ALIVE`); (3) P-12 e `cifrar_env.sh` são `scripts/*` → quarentena P-8
(decisão do Humano). Ver `LOG.md`.

**Objetivo:** fixar o que a Fase 7 entrega, o que dá para fazer hoje, e o que **bloqueia**
(HD, `sudo`, quarentena P-8).

**Pré-requisitos:** Fase 6 FECHADA.

Só leitura + doc.

---

## O que a Fase 7 entrega (ROADMAP)

`agata.target` puxando as units · hook Feral GameMode (`gamemode.ini` `[custom]
start=agata down` / `end=agata up`) · `ExecStop` que **drena** · `OLLAMA_KEEP_ALIVE=30s` ·
repo **restic** no HD + `agata-backup-artifacts.timer` · bundle de segredos cifrado
(`cifrar_env.sh`) · **controle P-12** no `perimetro.sh` (recurso no manifesto sem backup <
N dias = FALHA) · OpenTelemetry só coletor local.

**Aceite:** `agata down` libera a VRAM da 4060 no meio de uma sessão com o checkpoint
intacto · jogo por `gamemoderun` para o Agata e retoma ao fechar · P-12 vermelho com backup
velho, verde com fresco · restore completo do HD num scratch reproduz config + runtime.

## Inventário (2026-09-02)

| item | estado |
|---|---|
| `restic` | v0.19.1 instalado. **HD `AgataBkup01` NÃO montado** (só amanhã no trabalho). |
| `gamemode` (Feral) | **NÃO instalado** (`pacman -S gamemode` → sudo). Sem `~/.config/gamemode.ini`. |
| units `--user` do Agata | todas existem, todas `disabled` (Fase 7 as torna boot-persistentes). |
| `ollama.service` | unit **de sistema** (`/etc/systemd/system/`). Mudar env (`OLLAMA_KEEP_ALIVE`) = drop-in com `sudo`. |
| `agata` CLI | `redesign/grafo/cli.py` (P4-04) já tem `up`/`down` (com dreno do WAL) — base para o `agata.target`. |

## O que BLOQUEIA (por que a Fase 7 não roda autônoma hoje)

1. **HD** — restic repo, `agata-backup-artifacts.timer`, o "P-12 fica verde com backup
   fresco", e o aceite "restore do HD num scratch reproduz" — **tudo precisa do HD**. Só amanhã.
2. **`sudo`** — `pacman -S gamemode`; drop-in de `OLLAMA_KEEP_ALIVE` em `ollama.service`
   (system); talvez o coletor OTel. Pede o "vai".
3. **Quarentena P-8** — **`perimetro.sh` (P-12) e `cifrar_env.sh` são `scripts/*`** →
   mudança de comportamento, quarentena OBRIGATÓRIA: vai como `propostas/<nome>.diff` +
   `APROVADO-<nome>`, **nunca edição direta**. Decisão do Humano.

## O que dá para adiantar hoje (userspace, sem HD, sem P-8)

- `P7-01` — `agata.target` + as units com `WantedBy=agata.target`, `ExecStop` que chama
  `agata down` (dreno). Rascunho em `redesign/systemd/`. **Não** `enable` no boot ainda.
- `P7-02` — o rascunho do hook GameMode (`redesign/systemd/gamemode.ini.exemplo`) — texto,
  sem instalar o gamemode.
- Os `.diff` de P-12 e `cifrar_env.sh` **escritos em `propostas/`** (não aplicados) para o
  Humano revisar — é o mecanismo P-8, feito certo.

## Registro

- `STATUS.md`: P7-00 → "Feito"; a lista de bloqueios.
- `LOG.md`: inventário + o que adianta hoje + o que espera HD/sudo/P-8.
