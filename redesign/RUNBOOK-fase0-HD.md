# RUNBOOK — fechar a Fase 0 quando o HD `AgataBkup01` montar

Para a manhã de **2026-09-02, ~10:00 -03**. Executa na **Máquina (Predator)** — precisa do
HD físico, `sudo`, e dos arquivos locais. **Um cloud agent não roda isto.** A rotina
agendada só faz a verificação da manhã e deixa este runbook conferido.

Fecha: **P0-01 passos 3-4** (repo restic + 1º snapshot) e **P0-02 aceite de restore**.
Base: `redesign/tasks/P0-01-tag-e-backup.md`, `redesign/tasks/P0-02-fastmcp-ferramentas-maquina.md`.

Pré-checado em 2026-09-01 23:28 -03: `restic 0.19.1` instalado; as 4 fontes de backup
existem (`~/.hermes/config.yaml`, `~/agata/config/`, `~/.config/agata/`,
`~/agata/models/manifest.json`); HD ainda não montado.

**`~/.hermes/.env` NÃO entra no backup restic** (segredo; bundle cifrado é da Fase 7).

---

## 0. Reidratar (sempre)

```fish
cd $HOME/agata
git fetch origin --tags
git switch redesign
git pull --ff-only origin redesign
git status --porcelain            # tem que sair vazio
echo "main            = "(git rev-parse --short main)"            esperado 4aa90bd"
echo "pre-redesign    = "(git rev-parse --short 'pre-redesign^{commit}')"            esperado 4aa90bd"
echo "redesign        = "(git rev-parse --short redesign)
echo "origin/redesign = "(git rev-parse --short origin/redesign)"   (têm que ser iguais)"
```

Refs não batem ou árvore suja → **pare, avise o Humano.**

---

## 1. HD montado? (P0-01 passo 3)

```fish
lsblk -o NAME,LABEL,MOUNTPOINT,SIZE,FSTYPE | grep -i agatabkup
```

- **Aparece com MOUNTPOINT** → anote o ponto de montagem como `<MNT>` e siga.
- **Aparece sem MOUNTPOINT** → montar (ajuste o device):
  > ⚠️ **Monta um disco. Rode sozinho, confira o device com `lsblk` antes.**
  > ```fish
  > set DEV /dev/sdX1        # <- do lsblk acima
  > set MNT /run/media/orusoua/AgataBkup01
  > mkdir -p $MNT
  > sudo mount $DEV $MNT
  > mount | grep AgataBkup01
  > ```
- **Não aparece nada** → HD não conectado/reconhecido. Pare.

Confirme espaço livre: `df -h <MNT>` (o 1º snapshot é pequeno — configs + manifesto, < ~10 MB).

---

## 2. Repo restic + 1º snapshot (P0-01 passo 4)

```fish
cd $HOME/agata
set -x RESTIC_REPOSITORY <MNT>/restic-agata-local
set -x RESTIC_PASSWORD_FILE $HOME/.config/agata/restic.pass

mkdir -p $HOME/.config/agata
# gerar a senha do repo SE ainda não existir (fica só local, chmod 600, NUNCA no git)
test -f $RESTIC_PASSWORD_FILE
or begin
    openssl rand -base64 32 > $RESTIC_PASSWORD_FILE
    chmod 600 $RESTIC_PASSWORD_FILE
    echo "senha do repo restic criada em $RESTIC_PASSWORD_FILE -- GUARDE fora da máquina também"
end

restic init

restic backup \
    $HOME/.hermes/config.yaml \
    $HOME/agata/config \
    $HOME/.config/agata \
    $HOME/agata/models/manifest.json

restic snapshots
```

Colar de volta: a saída de `restic init`, a linha "Added to the repository ..." do
`backup`, e `restic snapshots`.
**Sucesso:** `restic snapshots` mostra **1** snapshot. Guarde `restic.pass` fora da
máquina (sem ela o backup não abre).

Conferência rápida da integridade:

```fish
restic check
restic ls latest | head -20
```

---

## 3. Aceite de restore num scratch (P0-02 — critério da Fase 0)

```fish
cd $HOME/agata
set SCRATCH (mktemp -d /tmp/agata-restore-XXXX)
restic restore latest --target $SCRATCH
echo "--- árvore restaurada ---"
find $SCRATCH -type f | sed "s#$SCRATCH/##" | sort

# comparar byte a byte com as fontes reais
for f in \
    .hermes/config.yaml \
    agata/models/manifest.json
    set orig $HOME/$f
    set rest $SCRATCH/root/$f            # ajuste o prefixo conforme o find acima mostrar
    if diff -q $orig $rest >/dev/null
        echo "OK   $f"
    else
        echo "DIFERE  $f  ($orig  vs  $rest)"
    end
end

# as pastas config/ e .config/agata/ -- comparar recursivamente
diff -rq $HOME/agata/config $SCRATCH/root/agata/config;    and echo "OK   agata/config/"
diff -rq $HOME/.config/agata $SCRATCH/root/.config/agata;  and echo "OK   .config/agata/"
```

Colar de volta: a lista de arquivos restaurados e as linhas `OK`/`DIFERE`.
**Sucesso (aceite P0-02):** todos os arquivos restauram e batem byte a byte com as fontes.
O prefixo dentro de `$SCRATCH` (`root/...` ou o caminho absoluto) varia com a versão do
restic — ajuste os caminhos de comparação pelo que o `find` mostrar.

Limpar o scratch:

```fish
rm -rf $SCRATCH
```

---

## 4. Registro (fim de sessão — CONTINUIDADE §7)

1. **Verificação S7 mínimo:** re-rodar o `restic snapshots` + o `diff -rq` do restore de
   estado limpo; anotar `PASS`/`FALHA` no LOG.
2. `redesign/STATUS.md`:
   - P0-01 → "Feito" (tirar de "Bloqueios"); anotar nº de snapshots e o `<MNT>`.
   - P0-02 aceite de restore → "Feito".
   - **Fase 0 → FECHADA.** "Próximo" passa a: aguardando o "vai" do Humano para a **Fase 1**
     (começa por `P1-00`, com revisão de plano de tier de risco antes).
   - Atualizar `ATUALIZADO`, a linha ÂNCORA, e `redesign/ANCORA.md`.
3. `redesign/LOG.md`: entrada nova (append-only) — o que rodou, saída-chave (snapshots,
   resultado do diff de restore), verificação S7 PASS/FALHA, `HEAD` no fim.
4. Commit + push:
   ```fish
   cd $HOME/agata
   git add -A redesign
   git commit -m "redesign: P0-01 passos 3-4 + P0-02 aceite de restore -- Fase 0 FECHADA"
   git push origin redesign
   git rev-parse --short HEAD
   ```
5. Copiar este resultado para `~/Área de trabalho/` se ajudar o Humano.

---

## Rollback (se algo der errado)

Não destrutivo:
```fish
set -e RESTIC_REPOSITORY RESTIC_PASSWORD_FILE
# a senha e o repo ficam onde estão; nada no git mudou ainda
```

Zerar o repo restic (só se explicitamente necessário):
> ⚠️ **DESTRUTIVO — apaga o repositório de backup. Rode sozinho, confirme o caminho.**
> ```fish
> rm -rf <MNT>/restic-agata-local
> ```
