# P7-01 — agata.target + dreno no stop (userspace, sem HD)

**Status:** ⏳ rascunho em `redesign/systemd/` (não instalado). Pede o "vai" para copiar
para `~/.config/systemd/user/` e `enable`.

**Objetivo:** `agata.target` agrupa as units do Agata; `agata up`/`down` (P4-04) sobem/param
todas; `ExecStop` de cada service chama `agata down` (dreno do WAL — não corta no meio de um
efeito).

**Pré-requisitos:** P7-00. Fase 4 (`cli.py down` com dreno) FECHADA.

**Arquivos:** `redesign/systemd/agata.target`, `agata-dropin.conf` (rascunhos, feitos) ·
`~/.config/systemd/user/agata.target` + `<unit>.service.d/agata.conf` (na instalação) ·
`redesign/tasks/P7-01-*.md`.

## Passos (quando o Humano der o "vai")
1. `cp redesign/systemd/agata.target ~/.config/systemd/user/`.
2. Para cada unit (omniroute, sanitizer, whisper, embeddings, obsidian-ro-proxy):
   `mkdir -p ~/.config/systemd/user/<unit>.service.d/ && cp .../agata-dropin.conf .../agata.conf`.
3. `systemctl --user daemon-reload`. **Ainda sem `enable`** — testar `systemctl --user
   start/stop agata.target` e conferir que o `ExecStop` drenou (plantar um `intent` sem
   `done` no WAL, ver o stop esperar).
4. `agata down` no meio de uma sessão do grafo → VRAM da 4060 cai, checkpoint intacto
   (aceite do ROADMAP). Só então `enable` (boot).

## Aceite
- `systemctl --user start agata.target` sobe tudo; `stop` para tudo drenando.
- `agata down` com um efeito pendente no WAL → espera/avisa, não corta.
- unit `enable`d só depois do teste de dreno passar.

## Rollback
`systemctl --user disable agata.target; rm ~/.config/systemd/user/agata.target
~/.config/systemd/user/*.service.d/agata.conf; systemctl --user daemon-reload`.

## Registro
`STATUS.md`: P7-01 → "Feito". `LOG.md`: o teste de dreno, `HEAD`.
