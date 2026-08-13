#!/bin/sh
# Restaura as 3 variáveis de ambiente do Ollama apagadas por um "sudo tee"
# (sem -a) que sobrescreveu /etc/systemd/system/ollama.service.d/override.conf
# depois que scripts/bloco_sudo_pendente.sh já tinha aplicado a mudança certa
# via sed -i (não destrutivo). Achado e cronologia em MEMÓRIAS (127).
#
# OLLAMA_HOST e OLLAMA_KV_CACHE_TYPE (os dois que sobreviveram) são
# preservados com os valores atuais -- este script não muda esses dois,
# só devolve os outros três.
set -e

echo "=== antes ==="
cat /etc/systemd/system/ollama.service.d/override.conf

sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<'EOF'
[Service]
Environment="OLLAMA_NUM_GPU=999"
Environment="OLLAMA_KV_CACHE_TYPE=q4_0"
Environment="CUDA_VISIBLE_DEVICES=0"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_HOST=127.0.0.1:11434"
EOF

sudo systemctl daemon-reload
sudo systemctl restart ollama.service

echo
echo "=== depois ==="
cat /etc/systemd/system/ollama.service.d/override.conf
echo
systemctl show ollama.service -p Environment
