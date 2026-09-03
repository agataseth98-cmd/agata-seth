# P7-02 — RUNBOOK de execução

**Complemento operacional do `P7-02-gamemode-e-ollama-keepalive.md`.**

**Atualização chat 6 (03/09):** o Bloco A (instalar Feral GameMode) foi **descartado** — o
CachyOS roda `ananicy-cpp` e GameMode brigaria com ele (ver a task). O hook virou o wrapper
`agata-jogo` (`redesign/systemd/agata-jogo` → `~/.local/bin/agata-jogo`), **já instalado e
testado, sem `sudo`**. Sobrou só o Bloco B, e ele agora é **opcional**.

---

## Bloco A — (feito no chat 6, sem `sudo`, nada a colar)

Só para referência. O que rodou:
```fish
install -Dm755 ~/agata/redesign/systemd/agata-jogo ~/.local/bin/agata-jogo
```
Teste (PASS): `agata-jogo sh -c 'sleep 3'` parou o `agata.target`, lançou via
`game-performance`, e ao sair os 6 membros voltaram `active`.

**Falta (Humano, GUI, uma vez cada):** pôr `agata-jogo %command%` nas Opções de
inicialização do Steam; `agata-jogo` como "Command prefix" no Lutris; "Wrapper command" no
Heroic.

---

## Bloco B — `OLLAMA_KEEP_ALIVE=30s` (1 `sudo`, toca `ollama.service` = produção) — OPCIONAL

**Deixou de ser necessário para o aceite:** o `agata-jogo` já faz `ollama stop` de cada
modelo carregado no start do jogo. Este bloco continua útil para o caso geral (Ollama
ocioso fora de jogo também soltaria a VRAM em ~30s em vez dos 5min padrão). Sem pressa.

Pré-checagem (02/09 ~22:05, ainda vale em 03/09): `ollama.service` tem o drop-in
`override.conf` com `OLLAMA_NUM_GPU=999`, `OLLAMA_KV_CACHE_TYPE=q4_0`, `CUDA_VISIBLE_DEVICES=0`,
`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_HOST=127.0.0.1:11434` — **sem** `OLLAMA_KEEP_ALIVE`.

Método por arquivo (não abre editor, não toca o `override.conf` existente):
```fish
sudo install -Dm644 /dev/stdin /etc/systemd/system/ollama.service.d/agata-keepalive.conf <<'EOF'
# P7-02 (Agata) -- modelo ocioso descarrega da VRAM em ~30s (padrao e' 5min).
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
ollama run qwen3.5:9b "oi" >/dev/null ; ollama ps      # modelo listado, Until ~30s
# ~35s depois:
ollama ps                                              # -> vazio
```

**Rollback B:**
```fish
sudo rm -f /etc/systemd/system/ollama.service.d/agata-keepalive.conf
sudo systemctl daemon-reload ; sudo systemctl restart ollama.service
```
(Não use `systemctl revert` — tiraria também o `override.conf` de produção.)

---

## Registro ao terminar

- `STATUS.md`: P7-02 → hook FEITO; falta fiar nos lançadores (Humano); `OLLAMA_KEEP_ALIVE`
  opcional (feito/adiado).
- `LOG.md`: se o bloco B foi feito, anotar que `ollama.service` (produção) foi tocado, com
  o quê, e que o `override.conf` ficou intacto.

## Depois de P7-02

Falta de P7-03: `cifrar_env.sh` (Humano: `APROVADO-cifrar-env` + rodar, prompt GPG). Depois:
aplicar os 2 `.diff` de `redesign/propostas/` em `scripts/*` = **Fase 8** (cutover + merge
p/ `main`), com "vai".
