#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

# --- P-4 -----------------------------------------------------------------
# "O api_server executa terminal: nunca expor sem contenção" e "Ollama
# restrito a 127.0.0.1" (PROJETO, Segurança). Transforma a auditoria
# pontual de S-2 (181) em checagem recorrente -- escopo fechado aos
# serviços do Agata (hermes*, ollama), não hardening de toda superfície
# de rede da máquina (isso já foi olhado uma vez em S-2 e ficou fora
# deste perímetro por decisão de escopo).
p4_bind() {
  local saida="${1:-}"
  [ -z "$saida" ] && saida="$(ss -tulpn 2>/dev/null)"
  # Reescrito -- item 9 do plano de mitigação da auditoria do Marcos
  # (MEMÓRIAS (437)/(440)). A regex "hermes|ollama" contra a linha inteira
  # nunca cobriu a arquitetura pós-redesenho: o processo real aparece em
  # `ss` como "python" (seth-gateway, seth-escriba, discord-mcp, etc.), não
  # pelo nome do script -- P-4 nunca teria pego um desses bindando fora de
  # loopback. Agora lê config/portas-agata.txt (manifesto declarativo:
  # porta|nome|bind_esperado) e confere CADA porta declarada por NÚMERO,
  # contra o bind real -- funciona não importa o nome do processo. Serviço
  # novo sem entrada no manifesto simplesmente não é coberto -- registrado
  # no comentário do próprio manifesto, não escondido.
  local manifesto="config/portas-agata.txt"
  if [ ! -f "$manifesto" ]; then
    echo "SUSPEITO (P-4): $manifesto ausente -- sem manifesto, sem checagem de bind possível."
    return 1
  fi
  # Achado real ao testar (16/08/2026, MEMÓRIAS (193)): sem root, `ss -p`
  # só atribui processo a sockets do PRÓPRIO uid -- a linha continua tendo
  # endereço e porta mesmo sem o nome do processo, então isto não invalida
  # a checagem por porta acima; mantido porque um processo de OUTRO uid
  # (ex. ollama.service, systemd system) pode ficar com o texto do
  # processo oculto, e não dá pra provar que a porta observada é mesmo a
  # esperada sem esse texto.
  if [ "$(id -u)" -ne 0 ]; then
    PERIMETRO_ESTADO="PARCIAL"
    # MEMÓRIAS (202): PARCIAL sozinho não dizia por quê nem o que fazer --
    # os outros vereditos explicam antes do veredito, este não explicava.
    echo "PARCIAL: rodando sem privilégio de administrador, não enxergo todos os processos -- não é falha, é o controle enxergando menos do que deveria. Para ver completo: rode de novo com sudo."
  fi
  local ruim=0
  local porta nome bind_esperado linha_ss endereco
  while IFS='|' read -r porta nome bind_esperado; do
    case "$porta" in ''|'#'*) continue ;; esac
    while IFS= read -r linha_ss; do
      [ -z "$linha_ss" ] && continue
      endereco="$(echo "$linha_ss" | awk '{print $5}')"
      # bind_esperado pode ser LISTA separada por vírgula (MEMÓRIAS (539)): o relé
      # do B8 (librechat-ponte-host) escuta as MESMAS portas em 172.29.7.1, o
      # gateway da bridge do LibreChat. Cada endereço aceito é declarado porta a
      # porta no manifesto -- nunca curinga.
      local ok=0 aceito
      case "$endereco" in \[::1\]:*) ok=1 ;; esac
      for aceito in ${bind_esperado//,/ }; do
        case "$endereco" in "$aceito":*) ok=1 ;; esac
      done
      if [ "$ok" = 0 ]; then
          echo "SUSPEITO (P-4): '$nome' (porta $porta, manifesto $manifesto) bindado em '$endereco', esperado '$bind_esperado' -- $linha_ss"
          ruim=1
      fi
    done <<< "$(echo "$saida" | awk -v p=":$porta\$" '$5 ~ p {print}')"
  done < "$manifesto"
  return "$ruim"
}

