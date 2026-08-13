#!/bin/sh
set -e

echo "=== retenção do journal: SystemMaxUse já é 1G (achado ativo em MEMÓRIAS (123)/(124)) ==="
echo "Isto adiciona um piso por TEMPO, que hoje não existe -- só o teto por tamanho."
echo "Sem MaxRetentionSec, journald pode rotacionar boots antigos mesmo com o teto de"
echo "tamanho longe de bater (achado: só 42M usados de 1G, e mesmo assim só 2 boots"
echo "de história restavam antes deste ajuste)."
echo

echo "=== MaxRetentionSec: 4week ==="
sudo sed -i 's/^#MaxRetentionSec=.*/MaxRetentionSec=4week/' /etc/systemd/journald.conf
grep -q "^MaxRetentionSec=4week" /etc/systemd/journald.conf || echo "MaxRetentionSec=4week" | sudo tee -a /etc/systemd/journald.conf
sudo systemctl restart systemd-journald

echo
echo "Confere:"
grep -E "^SystemMaxUse|^MaxRetentionSec" /etc/systemd/journald.conf
journalctl --disk-usage
journalctl --list-boots

echo
echo "Feito. Retenção por tempo somada à retenção por tamanho."
