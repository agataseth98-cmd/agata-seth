#!/usr/bin/env bash
# Espera um serviço HTTP local responder (qualquer código HTTP conta como "de pé").
# Feito para `ExecCondition=` de unit oneshot: no boot, timer com Persistent=true
# dispara a recuperação antes de o serviço do qual depende subir (13/10/2026:
# pesquisa e consolidação terminaram 1 s antes do OmniRoute começar a subir).
# Saída 0 = pode rodar; 1 = o systemd PULA a unit (não é falha, nada é escrito).
#
# Uso: esperar_servico.sh <url> [segundos, padrão 120]
url="${1:?uso: esperar_servico.sh <url> [segundos]}"
limite="${2:-120}"
inicio=$SECONDS
while (( SECONDS - inicio < limite )); do
  curl -s -o /dev/null -m 2 "$url" && exit 0
  sleep 2
done
echo "esperar_servico: $url não respondeu em ${limite}s -- execução pulada, nada escrito"
exit 1
