#!/bin/sh
# Cifra ~/.config/agata/.env com GPG simétrico (AES256), verifica decifrando, e
# copia o resultado pro HD externo se estiver montado.
#
# A senha é pedida pelo prompt interativo do gpg (pinentry) — nunca por
# argumento de linha de comando. Argumento apareceria em `ps`/histórico de
# shell; prompt não. Confira este comentário bate com o comando abaixo
# antes de rodar: não há --passphrase em lugar nenhum deste script.
set -e

STAGING="$HOME/.agata-backup-staging"
mkdir -p "$STAGING"
OUT="$STAGING/env-$(date +%Y%m%d).gpg"
TESTDEC="$STAGING/.env.decrypt_test"

echo "=== Cifrando ~/.config/agata/.env (vai pedir a senha DUAS vezes, por prompt) ==="
gpg --symmetric --cipher-algo AES256 -o "$OUT" ~/.config/agata/.env

echo
echo "=== Verificando por decifração (vai pedir a senha DE NOVO) ==="
gpg -d -o "$TESTDEC" "$OUT"

if diff -q ~/.config/agata/.env "$TESTDEC" >/dev/null; then
  echo "OK — decifrou idêntico ao original."
else
  echo "FALHOU — o arquivo decifrado é diferente do original. NÃO confie neste .gpg."
  rm -f "$TESTDEC"
  exit 1
fi
rm -f "$TESTDEC"

echo
echo "Pronto: $OUT"
echo "sha256: $(sha256sum "$OUT" | cut -d' ' -f1)"

USB="/run/media/$USER/AgataBkup01"
if mountpoint -q "$USB" 2>/dev/null; then
  DEST="$USB/env-$(date +%Y%m%d).gpg"
  cp "$OUT" "$DEST"
  echo "Copiado pro HD: $DEST"

  # P7-03: o .gpg tambem entra DENTRO do repo restic, com tag -- assim o
  # `restic check` e o P-12 do perimetro.sh enxergam a cobertura. O `cp`
  # solto acima fica como redundancia (o `restic check` nao valida ele).
  RESTIC_REPO="${AGATA_RESTIC_REPO:-$USB/restic-agata-local}"
  RESTIC_PASS="$HOME/.config/agata/restic.pass"
  ENV_SHA="$(sha256sum "$OUT" | cut -d' ' -f1)"
  if [ -d "$RESTIC_REPO" ] && [ -f "$RESTIC_PASS" ]; then
    if RESTIC_PASSWORD_FILE="$RESTIC_PASS" restic -r "$RESTIC_REPO" cat config >/dev/null 2>&1; then
      RESTIC_PASSWORD_FILE="$RESTIC_PASS" restic -r "$RESTIC_REPO" backup \
        --tag agata-env --tag "$ENV_SHA" "$OUT"
      RESTIC_PASSWORD_FILE="$RESTIC_PASS" restic -r "$RESTIC_REPO" check --read-data-subset=1/50
      echo "restic: env cifrado no repo $RESTIC_REPO (tag agata-env / $ENV_SHA)."
    else
      echo "restic: repo $RESTIC_REPO inacessivel (senha? init?) -- so o .gpg solto foi pro HD."
    fi
  else
    echo "restic: repo $RESTIC_REPO ou $RESTIC_PASS ausente -- so o .gpg solto foi pro HD."
  fi
  echo "FALTA: registrar isto no MANIFESTO.txt da passada de backup (incluído, AES256 simétrico, data do conteúdo do .env)."
else
  echo "HD não montado — o .gpg ficou só em $OUT (mesmo disco do Predator, não é backup ainda)."
  echo "Plugue o HD e copie manualmente, ou peça pro executor rodar outra passada de backup."
fi

echo
echo "LEMBRETE (não automatizável): guarde a senha fora do Predator — gerenciador"
echo "sincronizado externo, ou papel guardado longe do HD. Senha só na cabeça ou"
echo "só nesta máquina é o mesmo ponto único de falha que o backup existe pra evitar."
