#!/usr/bin/env bash
# redesign/obsidian/instalar_cerebro.sh -- instala/atualiza o "cérebro" do vault
# (MEMÓRIAS (670)): o plugin Brain Atlas em versão FIXA e conferida, a
# configuração dele (redesign/obsidian/brain-atlas.json) e os grupos de cor do
# grafo 2D na paleta da Agata (config/agata-identidade.json).
#
#   bash redesign/obsidian/instalar_cerebro.sh            # instala e configura
#   bash redesign/obsidian/instalar_cerebro.sh --conferir # só confere, não muda nada
#
# Segurança do plugin (código de terceiros dentro do Obsidian):
#   - versão e sha256 fixos aqui; arquivo com hash diferente = aborta, nada instalado;
#   - atestação de origem do GitHub (`gh attestation verify`), quando o gh existe;
#   - o main.js não pode conter chamada de rede (fetch/XMLHttpRequest/WebSocket/requestUrl).
# Depois: no Obsidian, Ctrl+R (recarregar) e Ctrl+P -> "Brain Atlas: Open".
set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
obs="$raiz/.obsidian"
dest="$obs/plugins/brain-atlas"
VERSAO="0.2.2"
REPO_GH="colorpulse6/brain-atlas"
declare -A SHA=(
  [main.js]=9b137a59e6088ceab2af1d432da2abdfb1be0b37ee0007a087b793b11543de88
  [manifest.json]=ef837563693ec9d742d872469bb01f6f50f9f86a9d3462a0596ca0a0923ee27a
  [styles.css]=ab63af3bacb08a58159c9b0a91a7db3e16facad205eb94ff6b1b712b71908543
)

conferir() {
  local ok=0
  for f in "${!SHA[@]}"; do
    if [ "$(sha256sum "$dest/$f" 2>/dev/null | awk '{print $1}')" = "${SHA[$f]}" ]; then
      echo "OK: $f $VERSAO"
    else
      echo "FALTA/DIFERENTE: $dest/$f"; ok=1
    fi
  done
  python3 - "$obs" <<'PY' || ok=1
import json, sys, os
obs = sys.argv[1]
cp = json.load(open(os.path.join(obs, "community-plugins.json")))
print("OK: brain-atlas ligado" if "brain-atlas" in cp else "FALTA: brain-atlas em community-plugins.json")
g = json.load(open(os.path.join(obs, "graph.json")))
n = sum(1 for c in g.get("colorGroups", []) if "brain_region" in c.get("query", ""))
print(f"OK: {n} grupos de cor por região no grafo" if n >= 6 else "FALTA: grupos de cor do grafo")
sys.exit(0 if "brain-atlas" in cp and n >= 6 else 1)
PY
  return $ok
}

if [ "${1:-}" = "--conferir" ]; then
  conferir
  exit $?
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
for f in "${!SHA[@]}"; do
  curl -fsSL -o "$tmp/$f" "https://github.com/$REPO_GH/releases/download/$VERSAO/$f"
  got="$(sha256sum "$tmp/$f" | awk '{print $1}')"
  [ "$got" = "${SHA[$f]}" ] || { echo "ERRO: sha256 de $f não bate ($got) -- nada instalado." >&2; exit 1; }
  if command -v gh >/dev/null 2>&1; then
    gh attestation verify "$tmp/$f" -R "$REPO_GH" >/dev/null 2>&1 \
      || { echo "ERRO: atestação de origem de $f falhou -- nada instalado." >&2; exit 1; }
  fi
done
if grep -qE 'fetch\(|XMLHttpRequest|WebSocket|requestUrl' "$tmp/main.js"; then
  echo "ERRO: main.js contém chamada de rede -- nada instalado." >&2; exit 1
fi
mkdir -p "$dest"
cp "$tmp/main.js" "$tmp/manifest.json" "$tmp/styles.css" "$dest/"

python3 - "$raiz" <<'PY'
import json, os, sys
raiz = sys.argv[1]
obs = os.path.join(raiz, ".obsidian")

def ler(p, padrao):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao

def gravar(p, d):
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(p + ".tmp", p)

# 1. configuração do plugin -- preserva os neurônios fixados pelo Humano
cfg = ler(os.path.join(raiz, "redesign/obsidian/brain-atlas.json"), {})
cfg.pop("_nota", None)
dpath = os.path.join(obs, "plugins/brain-atlas/data.json")
atual = ler(dpath, {})
if atual.get("pinnedNodePositions"):
    cfg["pinnedNodePositions"] = atual["pinnedNodePositions"]
gravar(dpath, cfg)

# 2. ligar o plugin
cpath = os.path.join(obs, "community-plugins.json")
cp = ler(cpath, [])
if "brain-atlas" not in cp:
    cp.append("brain-atlas")
gravar(cpath, cp)

# 3. grafo 2D: um grupo de cor por região, na paleta da Agata
ident = ler(os.path.join(raiz, "config/agata-identidade.json"), {})
cores, reg = ident.get("escuro", {}), ident.get("regioes", {})
def rgb(h):
    return int(h.lstrip("#"), 16)
grupos = [{"query": f"[brain_region:{r}]", "color": {"a": 1, "rgb": rgb(cores[v["cor"]])}}
          for r, v in reg.items() if v.get("cor") in cores]
grupos.append({"query": "path:memoria/missoes", "color": {"a": 1, "rgb": rgb(cores.get("amber", "#e0a458"))}})
gpath = os.path.join(obs, "graph.json")
g = ler(gpath, {})
g.update({"colorGroups": grupos, "showArrow": True, "lineSizeMultiplier": 0.6,
          "nodeSizeMultiplier": 1.2, "textFadeMultiplier": -1, "showOrphans": True})
gravar(gpath, g)
print(f"configurado: Brain Atlas, {len(grupos)} grupos de cor no grafo")
PY
conferir
echo "Agora no Obsidian: Ctrl+R (recarregar), depois Ctrl+P -> \"Brain Atlas: Open\"."
