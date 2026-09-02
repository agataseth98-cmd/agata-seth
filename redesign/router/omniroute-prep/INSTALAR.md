# P1-00 — INSTALADO ✅ (2026-09-02 ~00:02)

`omniroute@3.8.50` instalado em `~/.npm-global` (sem sudo), rodando como
`systemd --user omniroute.service`, bind `127.0.0.1:20128`, `health` = healthy, zero
provedor. Ver `redesign/tasks/P1-00-*.md`.

Este dir fica como referência de instalação/reinstalação. O que segue era o plano; foi
executado com um ajuste (o default de bind do OmniRoute é `0.0.0.0` — corrigido).

---

## Instalar (userspace, SEM sudo — prefix `~/.npm-global`)

No terminal, uma linha:

```
! npm install -g omniroute
```

(o `!` roda no chat e a saída volta pra sessão) — **ou** rode direto no fish e cole a
saída. `node v24` / `npm 12` já estão ok; `npm config get prefix` = `~/.npm-global`, então
não precisa de sudo.

Alternativa se quiser deixar a sessão autônoma nisso: adicionar em
`~/.claude/settings.json` a permissão `Bash(npm install -g omniroute)` (ou `Bash(npm:*)`).

## Depois disso — a sessão retoma sozinha

1. `redesign/router/omniroute-prep/verificar.sh` — checa binário, sobe em foreground,
   confere `:20128`, o bind `127.0.0.1`, e que nenhuma chave foi escrita.
2. `redesign/router/omniroute-prep/omniroute.service` — a unit `systemd --user` (copiar
   para `~/.config/systemd/user/`, `daemon-reload`, `start` — **sem** `enable`, boot é Fase 7).
3. Aceite de P1-00 (ver `redesign/tasks/P1-00-omniroute-instalar-subir.md`): `/v1/models`
   → 200; `is-active` → active; sem segredo em `~/.config/omniroute/`.

Nenhum provedor é configurado em P1-00 — o gateway sobe vazio. Chaves e provedores são
P1-01/P1-03, e as chaves são você editando o `.env`, nunca no chat.
