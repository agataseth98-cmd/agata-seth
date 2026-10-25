#!/usr/bin/env bash
# Contraprovas offline do P-9 (24/10/2026): serviço parado ('inactive') avisa, oneshot não;
# modelo maior que a GPU usando o que cabe nela não avisa, o que cabe e está dividido avisa.
# Sem systemd nem Ollama de verdade: `systemctl`, `docker` e `nvidia-smi` falsos no PATH e um
# /api/ps falso servido por um python local. Saída 0 = todos os casos passaram.
set -u
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'kill "$PID_PS" 2>/dev/null; rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"
cat > "$TMP/bin/systemctl" <<'EOF'
#!/usr/bin/env bash
# estado por unidade: lido de $P9F_ESTADOS ("unidade=estado:tipo ...")
u=""; for a in "$@"; do case "$a" in *.service|*.timer) u="$a";; esac; done
for par in $P9F_ESTADOS; do
  nome="${par%%=*}"; resto="${par#*=}"; est="${resto%%:*}"; tipo="${resto#*:}"
  if [ "$nome" = "$u" ]; then
    case " $* " in *" is-active "*) echo "$est";; *" is-enabled "*) echo enabled;; *"Type"*) echo "$tipo";; esac
    exit 0
  fi
done
case " $* " in *" is-active "*) echo active;; *" is-enabled "*) echo enabled;; *"Type"*) echo simple;; esac
EOF
printf '#!/usr/bin/env bash\nexit 1\n' > "$TMP/bin/docker"
printf '#!/usr/bin/env bash\ncase " $* " in *memory.total*) echo 8188;; *) echo "1, llama-server, 7000 MiB";; esac\n' > "$TMP/bin/nvidia-smi"
chmod +x "$TMP/bin/"*
PORTA=$((20000 + RANDOM % 9000))
cat > "$TMP/ps.py" <<EOF
import http.server, json, os
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        corpo = open("$TMP/ps.json", "rb").read()
        self.send_response(200); self.end_headers(); self.wfile.write(corpo)
http.server.HTTPServer(("127.0.0.1", $PORTA), H).serve_forever()
EOF
echo '{"models": []}' > "$TMP/ps.json"
python3 "$TMP/ps.py" & PID_PS=$!
sleep 0.5
# shellcheck source=/dev/null
source "$RAIZ/scripts/perimetro/p09_servicos_declarados.sh"
P9_UNIDADES_SISTEMA=(); P9_CONTAINERS_DOCKER=()
P9_UNIDADES_USUARIO=("seth-gateway.service" "agata-manutencao.service")
export P9_OLLAMA_PS_URL="http://127.0.0.1:$PORTA/api/ps"
falhas=0
caso() { if eval "$2"; then echo "PASS  $1"; else echo "FALHA $1"; falhas=$((falhas + 1)); fi; }
rodar() { PATH="$TMP/bin:$PATH" p9_servicos_declarados 2>/dev/null; }

export P9F_ESTADOS="seth-gateway.service=inactive:simple agata-manutencao.service=inactive:oneshot"
out="$(rodar)"
caso "serviço simple parado ('inactive') avisa" '[[ "$out" == *"seth-gateway.service"* ]]'
caso "oneshot parado não avisa" '[[ "$out" != *"agata-manutencao.service"* ]]'
export P9F_ESTADOS="seth-gateway.service=active:simple agata-manutencao.service=inactive:oneshot"
caso "tudo no ar: nenhum aviso de unidade" '[[ "$(rodar)" != *"unidade de usuário"* ]]'

G=$((1024 * 1024 * 1024))
echo "{\"models\": [{\"name\": \"moe\", \"size\": $((198 * G / 10)), \"size_vram\": $((7 * G))}]}" > "$TMP/ps.json"
caso "modelo maior que a GPU usando o que cabe: não avisa" '[[ "$(rodar)" != *"GPU"* ]]'
echo "{\"models\": [{\"name\": \"moe\", \"size\": $((198 * G / 10)), \"size_vram\": $((2 * G))}]}" > "$TMP/ps.json"
caso "modelo maior que a GPU com pouca VRAM (intruso): avisa" '[[ "$(rodar)" == *"moe"* ]]'
echo "{\"models\": [{\"name\": \"9b\", \"size\": $((66 * G / 10)), \"size_vram\": $((3 * G))}]}" > "$TMP/ps.json"
caso "modelo que cabe na GPU e está dividido: avisa (como antes)" '[[ "$(rodar)" == *"9b"* ]]'
echo "{\"models\": [{\"name\": \"9b\", \"size\": $((66 * G / 10)), \"size_vram\": $((66 * G / 10))}]}" > "$TMP/ps.json"
caso "modelo inteiro na GPU: não avisa" '[[ "$(rodar)" != *"GPU"* ]]'

[ "$falhas" -eq 0 ] && echo "P-9: OK" || echo "P-9: $falhas FALHA(S)"
exit "$falhas"
