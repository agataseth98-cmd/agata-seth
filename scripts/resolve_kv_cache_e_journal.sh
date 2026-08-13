#!/bin/sh
set -e

echo "=== 1/2: OLLAMA_KV_CACHE_TYPE q8_0 -> q4_0 ==="
sudo sed -i 's/OLLAMA_KV_CACHE_TYPE=q8_0/OLLAMA_KV_CACHE_TYPE=q4_0/' /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama.service
echo "Confere:"
systemctl show ollama.service -p Environment | tr ' ' '\n' | grep KV_CACHE

echo
echo "=== 2/2: journald, aumenta retenção (SystemMaxUse) ==="
sudo sed -i 's/^#SystemMaxUse=.*/SystemMaxUse=1G/' /etc/systemd/journald.conf
grep -q "^SystemMaxUse=1G" /etc/systemd/journald.conf || echo "SystemMaxUse=1G" | sudo tee -a /etc/systemd/journald.conf
sudo systemctl restart systemd-journald
echo "Confere:"
grep "^SystemMaxUse" /etc/systemd/journald.conf
journalctl --disk-usage

echo
echo "Feito. Os dois itens de sudo da fila resolvidos."
