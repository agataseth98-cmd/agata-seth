#!/usr/bin/env bash
# Rodar da RAIZ do repo. Uso: bash scripts/selar.sh <arquivo> | --check
set -euo pipefail
SELOS="SELOS.txt"
if [ "${1:-}" = "--check" ]; then
    [ -f "$SELOS" ] || { echo "sem selos registrados ($SELOS ausente)"; exit 1; }
    falha=0
    while read -r hash arquivo data; do
        [ -z "$hash" ] && continue
        atual=$(sha256sum "$arquivo" 2>/dev/null | cut -d' ' -f1 || echo "ARQUIVO_AUSENTE")
        if [ "$atual" = "$hash" ]; then echo "OK      $arquivo (selado em $data)"
        else echo "VIOLADO $arquivo — selo $hash != atual $atual"; falha=1; fi
    done < "$SELOS"
    exit $falha
fi
if [ "${1:-}" = "--iniciar-cadeia" ]; then
    [ -f "$SELOS" ] || { echo "sem SELOS.txt"; exit 1; }
    [ -e SELOS.chain ] && { echo "SELOS.chain já existe; não reinicio a cadeia"; exit 1; }
    python3 - <<'PY'
import hashlib
c=""; out=[]
for l in open("SELOS.txt",encoding="utf-8"):
    l=l.rstrip("\n")
    if not l.strip(): continue
    c=hashlib.sha256((c+"\n"+l).encode("utf-8")).hexdigest(); out.append(c+"\n")
open("SELOS.chain","w",encoding="utf-8").write("".join(out))
print(f"cadeia iniciada: {len(out)} elo(s) em SELOS.chain")
PY
    exit 0
fi
[ -n "${1:-}" ] || { echo "uso: selar.sh <arquivo> | --check"; exit 1; }
[ -f "$1" ] || { echo "arquivo não existe: $1"; exit 1; }
hash=$(sha256sum "$1" | cut -d' ' -f1); data=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "$hash $1 $data" >> "$SELOS"
echo "selado: $1"; echo "sha256: $hash"
if [ -e SELOS.chain ]; then
    ant=$(tail -n1 SELOS.chain 2>/dev/null | awk '{print $1}')
    novo=$(printf '%s\n%s' "${ant}" "$(tail -n1 "$SELOS")" | python3 -c "import sys,hashlib;print(hashlib.sha256(sys.stdin.read().encode('utf-8')).hexdigest())")
    echo "$novo" >> SELOS.chain
    echo "cadeia: elo acrescentado em SELOS.chain"
else
    echo "cadeia ainda não iniciada: rode 'bash scripts/selar.sh --iniciar-cadeia' uma vez"
fi
tag="${1%.md}-final"; tag="${tag##*/}"
echo "próximos passos (manuais até automatizar e testar):"
echo "  1) git add SELOS.txt SELOS.chain $1 && git commit -m 'selo: $1'"
echo "  2) git tag $tag"
echo "  3) git push origin $tag"
