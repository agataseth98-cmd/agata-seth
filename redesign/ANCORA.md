# ÂNCORA — referência de reidratação do branch `redesign`

Atualizada à mão por quem commita (promoção a hook = mudança de espinha, pende do Humano —
H2 da AUDITORIA-01). Dá o **piso conhecido**: o HEAD do commit ANTERIOR a esta atualização.
A referência viva é sempre `git rev-parse origin/redesign` (ou o topo do `git log` do
branch no GitHub).

```
commit anterior (piso):   77c62d5      escrito em: 2026-09-03 11:45 -03 (relogio da maquina, chat 6 -- Fase 8: relay do conselho-remoto pronto (P8-01), inventario Hermes (P8-05), CANON-DELTA.md (P8-06); nada aplicado ao canon/producao; main 4aa90bd)
```

## Refs esperados (confira com estes)

| ref | valor | como conferir |
|---|---|---|
| `main` | `4aa90bd` | `git rev-parse --short main` |
| `pre-redesign` → commit | `4aa90bd` | `git rev-parse --short 'pre-redesign^{commit}'` (tag ANOTADA; o bare dá o objeto-tag `cea5aeb`) |
| `redesign` = `origin/redesign` | ≥ o piso acima | `git rev-parse --short redesign origin/redesign` — têm que ser iguais |

Se `main` ou `pre-redesign^{commit}` não baterem, ou `redesign` ≠ `origin/redesign`: **pare
e avise o Humano.**
