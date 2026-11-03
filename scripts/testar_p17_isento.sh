#!/usr/bin/env bash
# Contraprovas offline do isento do P-17 (03/11/2026): um SKIP de "não se aplica" do P-16 (sem controle
# staged, dentro da suíte, gênese) não conta na série do P-17; o SKIP comum continua contando.
# Sem rede nem systemd. Saída 0 = todos os casos passaram.
set -u
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
# shellcheck source=/dev/null
source "$RAIZ/scripts/perimetro.sh"
falhas=0
caso() { if eval "$2"; then echo "PASS  $1"; else echo "FALHA $1"; falhas=$((falhas + 1)); fi; }
veredito() { CONT_SKIP=0; CONT_OK=0; CONT_PARCIAL=0; CONT_FALHA=0; FALHOU=0; _perimetro_veredito "$1" >/dev/null; }

P17_SKIPS=""; PERIMETRO_CTRL="P-16"; PERIMETRO_ESTADO="SKIP"; PERIMETRO_P17_ISENTO=1; veredito 0
caso "SKIP isento (não se aplica) não entra na série do P-17" '[ -z "${P17_SKIPS// /}" ]'
caso "o isento vale para uma corrida só" '[ "$PERIMETRO_P17_ISENTO" = 0 ]'
PERIMETRO_CTRL="P-16"; PERIMETRO_ESTADO="SKIP"; veredito 0
caso "SKIP comum volta a contar" '[[ "$P17_SKIPS" == *"P-16 "* ]]'
P17_SKIPS=""; PERIMETRO_CTRL="P-7"; PERIMETRO_ESTADO="SKIP"; PERIMETRO_P17_ISENTO=1; veredito 0
caso "o isento é decidido por quem marca; o veredito só obedece" '[ -z "${P17_SKIPS// /}" ]'

# o P-16 marca o isento nos três SKIPs de "não se aplica"
cd "$TMP" && git init -q . && git -c user.name=t -c user.email=t@t commit -q --allow-empty -m base && echo x > a && git add a
unset AGATA_TESTE_PERIMETRO
PERIMETRO_P17_ISENTO=0; PERIMETRO_ESTADO=""; p16_testes_dos_controles >/dev/null 2>&1
caso "P-16 sem arquivo de controle staged: SKIP isento" '[ "$PERIMETRO_ESTADO" = SKIP ] && [ "$PERIMETRO_P17_ISENTO" = 1 ]'
PERIMETRO_P17_ISENTO=0; PERIMETRO_ESTADO=""; AGATA_TESTE_PERIMETRO=1 p16_testes_dos_controles >/dev/null 2>&1
caso "P-16 dentro da suíte (recursão): SKIP isento" '[ "$PERIMETRO_ESTADO" = SKIP ] && [ "$PERIMETRO_P17_ISENTO" = 1 ]'

[ "$falhas" -eq 0 ] && echo "P-17 isento: OK" || echo "P-17 isento: $falhas FALHA(S)"
exit "$falhas"
