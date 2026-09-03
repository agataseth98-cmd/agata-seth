# P8-01 — fechar as pendências P-8 de `scripts/*`

**Status:** 🔶 **QUASE — 2026-09-03 ~09:50 (chat 6).** `p12-backup-verificavel.diff` e
`cifrar-env.diff` **aplicados no branch** + `perimetro.sh` 11 controles + P-12
vermelho/verde demonstrado. `conselho-remoto-omniroute.diff` **gerado**; falta B/C da
Cadeia + `APROVADO-conselho-remoto-omniroute`. **Bug achado e corrigido:** o caminho
`hd_ok=1` do P-12 estava quebrado (`restic | python3 - <<'PY'` — heredoc vencia o pipe,
`json.load(sys.stdin)` nunca via o JSON → P-12 sempre FALHOU com HD montado; a verificação
do chat 4 só exercitou `hd_ok=0`). Fix: python chama `restic` por `subprocess`.

**Objetivo:** os 3 `scripts/*` do redesenho entram em `main` pelo processo P-8 correto,
não por `--no-verify`. `perimetro.sh` passa a ter o P-12 funcionando.

**Pré-requisitos:** P8-00.

## Arquivos
- `scripts/perimetro.sh` ← `redesign/propostas/p12-backup-verificavel.diff` (+ `APROVADO-p12-backup-verificavel` ✅ já existe)
- `scripts/cifrar_env.sh` ← `redesign/propostas/cifrar-env.diff` (+ `APROVADO-cifrar-env` — **falta o Humano criar**)
- `scripts/conselho_remoto.py` ← novo `redesign/propostas/conselho-remoto-omniroute.diff` (a gerar) + `APROVADO-` ou Cadeia de auditoria

## Passos
1. **`conselho_remoto.py` — gerar o par P-8 retroativo.**
   ```fish
   git diff main:scripts/conselho_remoto.py redesign:scripts/conselho_remoto.py > redesign/propostas/conselho-remoto-omniroute.diff
   ```
   Cabeçalho no schema de `propostas/` (arquivo alvo, blob base, o que faz, verificado).
   O que muda: `enviar_omniroute()` → 1 POST no proxy `:20127` combo `conselho`; não lê mais
   chave; política preservada (privado, teto, 1 chamada, aborta-não-local, formato). Já
   testado com parecer real no branch (LOG 2026-09-02 ~08:45) — **mas** é `scripts/*` +
   toca rede → **Cadeia de auditoria em camadas** (A propôs+testou, B audita, C verifica na
   Máquina) antes do `APROVADO-`.
2. **Humano aprova `cifrar-env.diff`** → `touch redesign/propostas/APROVADO-cifrar-env`.
3. **Aplicar os 3 `.diff`** contra o HEAD de cada arquivo:
   ```fish
   for d in p12-backup-verificavel cifrar-env conselho-remoto-omniroute
     git apply --check redesign/propostas/$d.diff; and git apply redesign/propostas/$d.diff
   end
   ```
   (o P-8 do `perimetro.sh` exige: `.diff` aplicado ao HEAD reproduz **byte a byte** o
   staged; se `main` mudou esses arquivos desde as bases `70387a9`/`670dc6a`, rebasear o
   `.diff` antes.)
4. **`perimetro.sh` completo** — deve dar **11 controles**, P-12 incluído.

## Aceite
- `bash scripts/perimetro.sh` → `RESULTADO GERAL: OK`, 11 controles, `=== P-12 ===` presente.
- **P-12 vermelho/verde demonstrado:** com o HD montado e um artefato da lista FALHA sem
  snapshot fresco → `P-12` `FALHOU` e o commit trava; com tudo salvo → `OK`; com o HD fora
  → `PARCIAL` (nunca trava). (usa o `redesign/fase7-hd/semear_cache_p12.py` + um snapshot
  propositalmente velho num clone.)
- `git status` limpo fora do que a tarefa toca; os 3 pares `.diff`+`APROVADO-` presentes.

## Verificação independente
Camada C (Máquina): `.diff` aplicado ao HEAD == staged byte a byte (o que o P-8 exige);
`bash -n` nos 3; `perimetro.sh` roda os 11; nenhum `--passphrase`/chave em `conselho_remoto.py`
nem `cifrar_env.sh` (grep). Registrar o que cada camada acertou (Cadeia, item 5).

## Rollback
`git checkout -- scripts/perimetro.sh scripts/cifrar_env.sh scripts/conselho_remoto.py`;
remover os `.diff`/`APROVADO-` novos. Nada empurrado até P8-07.

## Registro
`STATUS.md`: P8-01 → Feito; P-12 ativo no `perimetro.sh`.
`LOG.md`: a cadeia de auditoria do `conselho_remoto.py` (achados de B, verificação de C),
o resultado do `perimetro.sh` 11-controles, a demo vermelho/verde do P-12.
