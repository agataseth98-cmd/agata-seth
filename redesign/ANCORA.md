# ÂNCORA — referência de reidratação do branch `redesign`

Atualizada à mão por quem commita (promoção a hook = mudança de espinha, pende do Humano —
H2 da AUDITORIA-01). Dá o **piso conhecido**: o HEAD do commit ANTERIOR a esta atualização.
A referência viva é sempre `git rev-parse origin/redesign` (ou o topo do `git log` do
branch no GitHub).

```
commit anterior (piso):   23a840c      escrito em: 2026-09-03 08:50 -03 (relogio da maquina, chat 6 -- P7-01 reboot confirmado; regua P-12 aprovada + reafinada; falta cifrar_env + aplicar .diff na Fase 8)
```

## Refs esperados (confira com estes)

| ref | valor | como conferir |
|---|---|---|
| `main` | `4aa90bd` | `git rev-parse --short main` |
| `pre-redesign` → commit | `4aa90bd` | `git rev-parse --short 'pre-redesign^{commit}'` (tag ANOTADA; o bare dá o objeto-tag `cea5aeb`) |
| `redesign` = `origin/redesign` | ≥ o piso acima | `git rev-parse --short redesign origin/redesign` — têm que ser iguais |

Se `main` ou `pre-redesign^{commit}` não baterem, ou `redesign` ≠ `origin/redesign`: **pare
e avise o Humano.**
