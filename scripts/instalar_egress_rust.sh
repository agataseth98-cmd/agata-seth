#!/usr/bin/env bash
# Compila a camada Rust de egress e instala em ~/.local/bin (D6, 15/11/2026).
# Depois: systemctl --user daemon-reload && systemctl --user restart navegador-mcp
set -euo pipefail
raiz="$(cd "$(dirname "$0")/.." && pwd)"
cd "$raiz/redesign/rust/egress"
cargo build --release --locked
mkdir -p "$HOME/.local/bin"
install -m 0755 target/release/egress "$HOME/.local/bin/agata-egress"
install -m 0755 target/release/egress-socks5 "$HOME/.local/bin/agata-egress-socks5"
echo "instalado: ~/.local/bin/agata-egress e ~/.local/bin/agata-egress-socks5"
