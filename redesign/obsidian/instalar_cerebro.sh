#!/usr/bin/env bash
# redesign/obsidian/instalar_cerebro.sh -- instala/atualiza o "cérebro" do vault
# (MEMÓRIAS (670)/(674)): dois plugins em versão FIXA e conferida --
#   Brain Atlas  (o cérebro anatômico, panorama; redesign/obsidian/brain-atlas.json)
#   New 3D Graph (grafo 3D navegável: girar, arrastar, zoom, WASD, rótulos legíveis;
#                 redesign/obsidian/grafo-3d.json)
# -- e os grupos de cor do grafo 2D, tudo na paleta da Agata (config/agata-identidade.json).
#
#   bash redesign/obsidian/instalar_cerebro.sh            # instala e configura
#   bash redesign/obsidian/instalar_cerebro.sh --conferir # só confere, não muda nada
#
# Segurança dos plugins (código de terceiros dentro do Obsidian):
#   - versão e sha256 fixos aqui; arquivo com hash diferente = aborta, nada instalado;
#   - atestação de origem do GitHub (`gh attestation verify`) onde o autor publica
#     (Brain Atlas sim; New 3D Graph não publica -- o sha256 fixo é a trava);
#   - chamada de rede no main.js: Brain Atlas, nenhuma; New 3D Graph, exatamente as
#     2 revisadas em (674) (carregador do motor de física local e uma opção de URL
#     da biblioteca 3d-force-graph que o plugin não usa). Número diferente = aborta.
# Depois: no Obsidian, Ctrl+R (recarregar) e Ctrl+P -> "Brain Atlas: Open".
set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
obs="$raiz/.obsidian"
# plugin -> "repo versão atestado redes_revisadas"
declare -A PLUGIN=(
  [brain-atlas]="colorpulse6/brain-atlas 0.2.2 sim 0"
  [new-3d-graph]="Apoo711/obsidian-3d-graph 2.8.1 nao 2"
)
declare -A SHA=(
  [brain-atlas/main.js]=9b137a59e6088ceab2af1d432da2abdfb1be0b37ee0007a087b793b11543de88
  [brain-atlas/manifest.json]=ef837563693ec9d742d872469bb01f6f50f9f86a9d3462a0596ca0a0923ee27a
  [brain-atlas/styles.css]=ab63af3bacb08a58159c9b0a91a7db3e16facad205eb94ff6b1b712b71908543
  [new-3d-graph/main.js]=5e4d995fd85592de320877bcd42c3c96c73cdcb6f437d34dffa45b415578ecfd
  [new-3d-graph/manifest.json]=599e47cfbc7210ba832d8810b628604a150d56e59e38fe083bf88866549b3ca7
  [new-3d-graph/styles.css]=ee541114387b5cbc3d691515209f6609ea15fa94b562d058e9cd6fb7af6c4f02
)

conferir() {
  local ok=0
  for chave in "${!SHA[@]}"; do
    if [ "$(sha256sum "$obs/plugins/$chave" 2>/dev/null | awk '{print $1}')" = "${SHA[$chave]}" ]; then
      echo "OK: $chave"
    else
      echo "FALTA/DIFERENTE: $obs/plugins/$chave"; ok=1
    fi
  done
  python3 - "$obs" <<'PY' || ok=1
import json, sys, os
obs = sys.argv[1]
cp = json.load(open(os.path.join(obs, "community-plugins.json")))
for pid in ("brain-atlas", "new-3d-graph"):
    print(f"OK: {pid} ligado" if pid in cp else f"FALTA: {pid} em community-plugins.json")
g = json.load(open(os.path.join(obs, "graph.json")))
n = sum(1 for c in g.get("colorGroups", []) if "brain_region" in c.get("query", ""))
print(f"OK: {n} grupos de cor por região no grafo" if n >= 6 else "FALTA: grupos de cor do grafo")
sys.exit(0 if all(p in cp for p in ("brain-atlas", "new-3d-graph")) and n >= 6 else 1)
PY
  return $ok
}

if [ "${1:-}" = "--conferir" ]; then
  conferir
  exit $?
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
# 1. baixa e confere TUDO antes de instalar qualquer coisa
for pid in "${!PLUGIN[@]}"; do
  read -r repo versao atestado redes <<<"${PLUGIN[$pid]}"
  mkdir -p "$tmp/$pid"
  for f in main.js manifest.json styles.css; do
    curl -fsSL -o "$tmp/$pid/$f" "https://github.com/$repo/releases/download/$versao/$f"
    got="$(sha256sum "$tmp/$pid/$f" | awk '{print $1}')"
    [ "$got" = "${SHA[$pid/$f]}" ] || { echo "ERRO: sha256 de $pid/$f não bate ($got) -- nada instalado." >&2; exit 1; }
    if [ "$atestado" = sim ] && command -v gh >/dev/null 2>&1; then
      gh attestation verify "$tmp/$pid/$f" -R "$repo" >/dev/null 2>&1 \
        || { echo "ERRO: atestação de origem de $pid/$f falhou -- nada instalado." >&2; exit 1; }
    fi
  done
  achadas="$( (grep -oE 'fetch\(|XMLHttpRequest|new WebSocket|requestUrl' "$tmp/$pid/main.js" || true) | wc -l)"
  [ "$achadas" -eq "$redes" ] || { echo "ERRO: $pid tem $achadas chamada(s) de rede, revisadas $redes -- nada instalado." >&2; exit 1; }
done
# 2. instala
for pid in "${!PLUGIN[@]}"; do
  mkdir -p "$obs/plugins/$pid"
  cp "$tmp/$pid/main.js" "$tmp/$pid/manifest.json" "$tmp/$pid/styles.css" "$obs/plugins/$pid/"
done

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

# 1b. New 3D Graph -- a configuração versionada vence; o resto que o Humano
# mudou na tela (forças, filtros) fica
g3 = ler(os.path.join(raiz, "redesign/obsidian/grafo-3d.json"), {})
g3.pop("_nota", None)
g3path = os.path.join(obs, "plugins/new-3d-graph/data.json")
gravar(g3path, {**ler(g3path, {}), **g3})

# 2. ligar os plugins
cpath = os.path.join(obs, "community-plugins.json")
cp = ler(cpath, [])
for pid in ("brain-atlas", "new-3d-graph"):
    if pid not in cp:
        cp.append(pid)
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
print(f"configurado: Brain Atlas, New 3D Graph ({len(g3.get('groups', []))} grupos), {len(grupos)} grupos de cor no grafo 2D")
PY
conferir
echo "Agora: reinicie o Obsidian (systemctl --user restart obsidian-app, ou Ctrl+P -> \"Recarregar app sem salvar\")."
echo "Panorama: Ctrl+P -> \"Brain Atlas: Open\".  Explorar: Ctrl+P -> \"New 3D Graph: Open 3d graph\"."
