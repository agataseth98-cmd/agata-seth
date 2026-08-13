#!/bin/sh
# Bloco único de sudo, consolidado por pedido do Humano em MEMÓRIAS (126) --
# "uma passada só", porque o bug de login (PROCEDIMENTO_LOGIN.md) torna caro
# entrar e sair do terminal várias vezes. Cada item abaixo já foi checado
# sem privilégio nesta sessão; só a aplicação exige sudo.
set -e

echo "=== 1/4: Ollama -- restringe OLLAMA_HOST a 127.0.0.1 (hoje: 0.0.0.0, achado em (126)) ==="
echo "Resolve: Ollama escuta em todas as interfaces, sem autenticação própria."
sudo sed -i 's/OLLAMA_HOST=0.0.0.0:11434/OLLAMA_HOST=127.0.0.1:11434/' /etc/systemd/system/ollama.service.d/override.conf
sudo systemctl daemon-reload
sudo systemctl restart ollama.service
echo "Confere:"
systemctl show ollama.service -p Environment | tr ' ' '\n' | grep OLLAMA_HOST
ss -tlnp 2>/dev/null | grep 11434 || echo "(ss sem -p sem sudo -- confira a coluna de endereço acima)"

echo
echo "=== 2/4: confirma ao vivo se o DROP padrão do UFW está mesmo em vigor ==="
echo "Resolve: fecha a lacuna registrada em (126) -- regras vistas em disco, não ao vivo."
sudo nft list ruleset | head -80

echo
echo "=== 3/4: retenção do journal -- MaxRetentionSec=4week (hoje: só SystemMaxUse=1G) ==="
echo "Resolve: só 2 boots de história restavam mesmo com o teto de tamanho longe de bater."
sudo sed -i 's/^#MaxRetentionSec=.*/MaxRetentionSec=4week/' /etc/systemd/journald.conf
grep -q "^MaxRetentionSec=4week" /etc/systemd/journald.conf || echo "MaxRetentionSec=4week" | sudo tee -a /etc/systemd/journald.conf
sudo systemctl restart systemd-journald
echo "Confere:"
grep -E "^SystemMaxUse|^MaxRetentionSec" /etc/systemd/journald.conf
journalctl --disk-usage

echo
echo "=== 4/4: teclado USB (Hengchangtong, c0f4:0009) -- desabilita autosuspend ==="
echo "Resolve: paliativo pro bug de login -- o dispositivo falha resume em s2idle"
echo "(PM: failed to resume async: error -5) e perde/corrompe teclas durante a"
echo "digitação da senha. Não resolve a raiz (o que acorda a máquina 91x por"
echo "noite segue lacuna) -- só reduz o efeito colateral mais visível."
cat <<'UDEV' | sudo tee /etc/udev/rules.d/99-hct-keyboard-no-autosuspend.rules
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="c0f4", ATTR{idProduct}=="0009", TEST=="power/control", ATTR{power/control}="on"
UDEV
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "Confere (se o teclado estiver conectado agora):"
grep -l "c0f4" /sys/bus/usb/devices/*/idVendor 2>/dev/null | while read f; do d=$(dirname "$f"); echo "$d: $(cat "$d/power/control" 2>/dev/null)"; done

echo
echo "Feito. Os 4 itens pendentes de sudo resolvidos numa passada só."
