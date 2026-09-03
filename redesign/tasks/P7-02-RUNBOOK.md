# P7-02 — RUNBOOK de execução (quando o Humano acordar / der o "vai")

**Complemento operacional do `P7-02-gamemode-e-ollama-keepalive.md`.** Aqui estão os
blocos prontos pra colar, com as pré-checagens já feitas na Máquina em **2026-09-02 ~22:05
-03** (chat 5). Dois passos precisam de `sudo` e o passo B toca `ollama.service` (produção)
— por isso **nada disto foi rodado**; é decisão + mãos do Humano.

---

## Pré-checagens já feitas (não precisa refazer)

| item | estado medido em 02/09 ~22:05 |
|---|---|
| `gamemode` instalado? | **NÃO** (`pacman -Q gamemode` → não encontrado; sem `gamemoderun`/`gamemoded` no PATH) |
| `~/.config/gamemode.ini` existe? | **NÃO** — o exemplo `redesign/systemd/gamemode.ini.exemplo` já está correto (usa `systemctl --user stop/start agata.target`, não `cli.py`) |
| `ollama.service` | `/etc/systemd/system/ollama.service` + drop-in `override.conf` já existe com `OLLAMA_NUM_GPU=999`, `OLLAMA_KV_CACHE_TYPE=q4_0`, `CUDA_VISIBLE_DEVICES=0`, `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_HOST=127.0.0.1:11434` |
| `OLLAMA_KEEP_ALIVE` no serviço hoje | **ausente** (não está no `Environment` de `systemctl show ollama.service`) |
| `agata.target` | `enable`d p/ boot, S7 do fix de ordenação PASS (LOG 02/09 ~22:00) |

---

## Bloco A — instalar GameMode + hook (1 `sudo`, userspace no resto)

```fish
# A1. instala (repo 'extra' + multilib pro lib32)
sudo pacman -S gamemode lib32-gamemode

# A2. hook do Feral GameMode -- ao lançar jogo por gamemoderun:
#     start = stop agata.target (drena o WAL, para os 5 + libera a 4060)
#     end   = start agata.target (re-sobe os 5; o MoE NÃO volta sozinho)
cp ~/agata/redesign/systemd/gamemode.ini.exemplo ~/.config/gamemode.ini
```

**Verificação A:**
```fish
gamemoded -s                                   # 'gamemode is active' quando um jogo roda
gamemoderun glxgears                            # (ou um jogo real) numa aba; noutra:
systemctl --user is-active agata.target         # -> 'inactive' enquanto o jogo roda
nvidia-smi --query-gpu=memory.used --format=csv,noheader   # 4060 sem carga do Agata
# fechar o glxgears/jogo:
systemctl --user is-active agata.target         # -> 'active' de novo (os 5 sobem)
```
Aceite (ROADMAP): jogo por `gamemoderun` → Agata sai da 4060 sozinho e retoma ao fechar.

---

## Bloco B — `OLLAMA_KEEP_ALIVE=30s` (1 `sudo`, toca `ollama.service` = produção)

**Isto é `ollama.service` de produção.** É variável de ambiente (operação), não config de
modelo — o P7-02 e o ROADMAP colocam `OLLAMA_KEEP_ALIVE=30s` como entrega da Fase 7 —
mas a decisão de mexer no serviço de produção antes da Fase 8 é do Humano (P7-02 §3).

Método por arquivo (não abre editor, reprodutível):
```fish
sudo install -Dm644 /dev/stdin /etc/systemd/system/ollama.service.d/agata-keepalive.conf <<'EOF'
# P7-02 (Agata) -- solta a VRAM da 4060 rápido: modelo ocioso descarrega em ~30s.
[Service]
Environment=OLLAMA_KEEP_ALIVE=30s
EOF

sudo systemctl daemon-reload
sudo systemctl restart ollama.service
```

**Verificação B:**
```fish
systemctl show ollama.service -p Environment | tr ' ' '\n' | grep KEEP_ALIVE
#   -> OLLAMA_KEEP_ALIVE=30s
ollama run qwen3.5:9b "oi" >/dev/null       # carrega
ollama ps                                    # modelo listado, 'Until' ~30s
# esperar ~35s
ollama ps                                    # -> vazio (VRAM liberada)
```

---

## Rollback (completo)

```fish
rm -f ~/.config/gamemode.ini
sudo rm -f /etc/systemd/system/ollama.service.d/agata-keepalive.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama.service
sudo pacman -Rns gamemode lib32-gamemode
```
`sudo systemctl revert ollama.service` também tira o drop-in, mas só se não houver outros
drop-ins que você queira manter — aqui há o `override.conf`, então **prefira o `rm` do
arquivo específico** acima.

---

## Registro ao terminar

- `STATUS.md`: P7-02 → "Feito".
- `LOG.md`: saída do teste com `gamemoderun`, `ollama ps` esvaziando, `HEAD`.
- Se B foi feito: anotar que `ollama.service` (produção) foi tocado, com o quê e por quê,
  e que o `override.conf` original ficou intacto.

## Depois de P7-02

Falta só **P7-03** (HD `AgataBkup01` amanhã) pra fechar a Fase 7:
`redesign/fase7-hd/QUANDO-O-HD-VOLTAR.md` → `restic` dos GGUF/IR que faltam + `restic
check` + restore; régua do P-12 (`redesign/SILO-HUMANO.md` H-1, decisão do Humano) →
`APROVADO-p12-backup-verificavel` → os `.diff` de `redesign/propostas/` (ambos conferidos
02/09 ~22:05: `git apply --check` limpo contra o HEAD atual). Aí **Fase 8** (cutover +
merge p/ `main`), com "vai".
