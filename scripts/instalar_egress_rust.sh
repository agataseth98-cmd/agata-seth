#!/usr/bin/env bash
# Compila a camada Rust de egress e instala em ~/.local/bin (D6, 15/11/2026).
# Robustez (16/11/2026): a compilação roda com nice -n 15 e CARGO_BUILD_JOBS (padrão 2; sobrescreva pela variável).
# Pula a compilação se os binários de target/release já estão em dia (scripts/egress_em_dia.py). A instalação roda sempre.
# Depois: systemctl --user daemon-reload && systemctl --user restart navegador-mcp
set -euo pipefail
raiz="$(cd "$(dirname "$0")/.." && pwd)"
cd "$raiz/redesign/rust/egress"
if python3 -I "$raiz/scripts/egress_em_dia.py" "$(pwd)"; then
  echo "compilação pulada: binários em dia"
else
  CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}" nice -n 15 cargo build --release --locked
fi
mkdir -p "$HOME/.local/bin"
install -m 0755 target/release/egress "$HOME/.local/bin/agata-egress"
install -m 0755 target/release/egress-socks5 "$HOME/.local/bin/agata-egress-socks5"
echo "instalado: ~/.local/bin/agata-egress e ~/.local/bin/agata-egress-socks5"
