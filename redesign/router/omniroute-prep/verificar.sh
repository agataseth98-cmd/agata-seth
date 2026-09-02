#!/usr/bin/env bash
# verificar.sh -- checagens de P1-00 depois de `npm install -g omniroute`.
# Não instala nada. Não configura provedor. Só verifica.
# Uso:  bash redesign/router/omniroute-prep/verificar.sh
set -uo pipefail

BIN="${OMNIROUTE_BIN:-$HOME/.npm-global/bin/omniroute}"
PORT="${OMNIROUTE_PORT:-20128}"
FALHAS=0
ok()  { echo "  OK   $*"; }
bad() { echo "  FALHA $*"; FALHAS=$((FALHAS+1)); }

echo "== 1. binário =="
if [ -x "$BIN" ]; then
  ok "$BIN"
  "$BIN" --version 2>&1 | head -1 || "$BIN" --help 2>&1 | head -3
else
  bad "não achei $BIN -- rode: type -p omniroute ; e ajuste OMNIROUTE_BIN"
  echo "resultado: $FALHAS falha(s). Pare aqui." ; exit 1
fi

echo "== 2. subir em foreground 8s e observar =="
( "$BIN" >/tmp/omniroute.boot 2>&1 & echo $! >/tmp/omniroute.pid )
sleep 8
PID="$(cat /tmp/omniroute.pid 2>/dev/null)"
echo "--- primeiras linhas do boot ---"; sed -n '1,25p' /tmp/omniroute.boot

echo "== 3. porta e bind =="
if ss -tlnp 2>/dev/null | grep -q ":${PORT}"; then
  LINHA="$(ss -tlnp 2>/dev/null | grep ":${PORT}")"
  echo "  $LINHA"
  echo "$LINHA" | grep -qE '127\.0\.0\.1|\[::1\]' && ok "bind local" || bad "NÃO está em 127.0.0.1 -- não deixar assim"
else
  bad "nada escutando em :${PORT}"
fi

echo "== 4. endpoints =="
code_root=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/" || echo 000)
code_models=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/v1/models" || echo 000)
echo "  /            -> $code_root"
echo "  /v1/models   -> $code_models"
[ "$code_models" = "200" ] && ok "/v1/models responde 200" || bad "/v1/models = $code_models (esperado 200)"

echo "== 5. nenhum segredo em disco =="
for d in "$HOME/.config/omniroute" "$HOME/.omniroute" "$HOME/.local/share/omniroute"; do
  [ -d "$d" ] || continue
  if grep -rIlE '(sk-[A-Za-z0-9]{20}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|ghp_[0-9A-Za-z]{36})' "$d" >/dev/null 2>&1; then
    bad "possível segredo em $d"
  else
    ok "sem padrão de chave em $d"
  fi
done

echo "== parar o processo de teste =="
[ -n "${PID:-}" ] && kill "$PID" 2>/dev/null && ok "processo $PID parado"

echo
if [ "$FALHAS" -eq 0 ]; then
  echo "VERIFICAR: OK -- pode instalar a unit systemd --user (omniroute.service) e seguir para P1-01."
else
  echo "VERIFICAR: $FALHAS falha(s) -- resolver antes de virar serviço."
fi
exit "$FALHAS"
