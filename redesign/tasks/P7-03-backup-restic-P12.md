# P7-03 — repo restic no HD + timer + P-12 no perímetro + cifrar_env (PRECISA DO HD + P-8)

**Status:** ⏳ **BLOQUEADO** — precisa do HD `AgataBkup01` (só amanhã) **e** o P-12/`cifrar_env.sh`
são `scripts/*` → quarentena P-8 (vai como `propostas/<nome>.diff` + `APROVADO-`, nunca
edição direta; decisão do Humano).

**Objetivo:** todo recurso do `models/manifest.json` com backup restic verificável; o
`perimetro.sh` reprova (P-12) se um recurso está sem backup há > N dias;
`agata-backup-artifacts.timer` roda quando o HD monta (senão marcador pendente — padrão do
bundle); `~/.hermes/.env` num bundle cifrado (`cifrar_env.sh`).

**Pré-requisitos:** P7-00. HD montado. Fase 0 (repo restic `d0223c4…`) já existe.

## Passos
1. **HD montado:** `restic -r <HD>/restic-agata-local snapshot` dos GGUF/IR que ainda não
   têm (Qwen3-30B-A3B, whisper base/small, e5-small) + `restic check`.
2. **P-12 (P-8):** `propostas/p12-backup-verificavel.diff` — nova checagem em `perimetro.sh`:
   para cada recurso do `models/manifest.json` com `origem` não-pública (ou marcado
   `backup_obrigatorio`), confere `restic snapshots --tag <recurso>` com data < N dias;
   ausente/velho → SUSPEITO (P-12). N e a régua de "quais recursos" = decisão do Humano.
3. **`agata-backup-artifacts.timer`** — `systemd --user`, roda quando o HD monta (`ConditionPathIsMountPoint`),
   senão escreve marcador (como o `post-commit` do bundle já faz).
4. **`cifrar_env.sh` (P-8):** `propostas/cifrar-env.diff` — `age`/`gpg` do `~/.hermes/.env`
   para `<HD>/agata-env.age`, com a passphrase fora do git. Nunca imprime o `.env`.
5. **Aceite:** P-12 vermelho com backup velho, verde com fresco; `restic restore` completo
   num scratch reproduz config + estado de runtime.

## Rollback
Reverter os `.diff` de `propostas/` (não aplicados até `APROVADO-`); `systemctl --user
disable agata-backup-artifacts.timer`.

## Registro
`STATUS.md`: P7-03 → "Feito"; **Fase 7 FECHADA** (com P7-01/02/03). `LOG.md`: o `restic
check`, o teste de P-12 vermelho/verde, o restore, `HEAD`.
