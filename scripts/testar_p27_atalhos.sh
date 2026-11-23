#!/usr/bin/env bash
# Contraprovas offline do P-27 (23/11/2026): atalho instalado igual à fonte que ele declara.
# Usa um HOME FALSO em cada cenário; nunca lê nem escreve o ~/.local/bin real. Saída 0 = todos os casos passaram.
# O P-27 só avisa: em todo cenário a função devolve 0 (nunca falha o perímetro).
set -u
unset GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE GIT_PREFIX GIT_COMMON_DIR
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
# shellcheck source=/dev/null
source "$RAIZ/scripts/perimetro/p27_atalhos_fonte.sh"
falhas=0
caso() { if eval "$2"; then echo "PASS  $1"; else echo "FALHA $1"; falhas=$((falhas + 1)); fi; }

# repositório descartável só para o `git rev-parse --show-toplevel` da sugestão de cp
REPO="$TMP/repo"; mkdir -p "$REPO"; git init -q "$REPO"

# monta um HOME falso: fontes em ~/agata/redesign/systemd (como o cabeçalho declara) e os dois atalhos instalados
cenario() {  # $1 = nome do cenário
  H="$TMP/home-$1"
  mkdir -p "$H/.local/bin" "$H/agata/redesign/systemd"
  printf '#!/usr/bin/env bash\n# Fonte versionada: ~/agata/redesign/systemd/seth\necho ligar v1\n' > "$H/agata/redesign/systemd/seth"
  printf '#!/usr/bin/env bash\n# Fonte versionada: ~/agata/redesign/systemd/seth-parar\necho parar v1\n' > "$H/agata/redesign/systemd/seth-parar"
  cp "$H/agata/redesign/systemd/seth" "$H/.local/bin/agata"
  cp "$H/agata/redesign/systemd/seth-parar" "$H/.local/bin/fechar-agata"
}

# roda a função com o HOME do cenário; devolve a saída, o estado e o código de retorno
rodar() {  # $1 = HOME falso
  (
    export HOME="$1"
    cd "$REPO" || exit 9
    PERIMETRO_ESTADO=""
    p27_atalhos_fonte
    rc=$?
    echo "ESTADO=${PERIMETRO_ESTADO}"
    echo "RC=$rc"
  )
}

# 1. tudo igual: OK, sem aviso
cenario igual
saida="$(rodar "$TMP/home-igual")"
caso "iguais: sai OK (P-27) com os dois atalhos" 'printf "%s" "$saida" | grep -q "^OK (P-27): atalhos instalados iguais às fontes versionadas: agata fechar-agata\.$"'
caso "iguais: sem AVISO" '! printf "%s" "$saida" | grep -q "AVISO"'
caso "iguais: estado continua vazio (veredito OK)" 'printf "%s" "$saida" | grep -qx "ESTADO="'
caso "iguais: devolve 0" 'printf "%s" "$saida" | grep -qx "RC=0"'

# 2. fechar-agata diferente da fonte: AVISO com o cp da fonte, PARCIAL, nunca falha
cenario diferente
printf '#!/usr/bin/env bash\n# Fonte versionada: ~/agata/redesign/systemd/seth-parar\necho parar antiga\n' > "$TMP/home-diferente/.local/bin/fechar-agata"
saida="$(rodar "$TMP/home-diferente")"
caso "diferente: AVISO nomeia o atalho" 'printf "%s" "$saida" | grep -q "^AVISO (P-27): .*fechar-agata difere da fonte versionada .*seth-parar\.$"'
caso "diferente: o comando de reinstalar é o cp da fonte declarada" 'printf "%s" "$saida" | grep -q "^  O que fazer: cp .*/home-diferente/agata/redesign/systemd/seth-parar .*/home-diferente/.local/bin/fechar-agata$"'
caso "diferente: estado PARCIAL" 'printf "%s" "$saida" | grep -qx "ESTADO=PARCIAL"'
caso "diferente: devolve 0 (aviso, não falha)" 'printf "%s" "$saida" | grep -qx "RC=0"'
caso "diferente: o outro atalho continua conferido" 'printf "%s" "$saida" | grep -q "^P-27: 1 de 2 atalho(s) iguais"'

# 3. atalho ausente: AVISO, PARCIAL, nunca falha
cenario ausente
rm -f "$TMP/home-ausente/.local/bin/agata"
saida="$(rodar "$TMP/home-ausente")"
caso "ausente: AVISO diz que não existe" 'printf "%s" "$saida" | grep -q "^AVISO (P-27): .*/agata não existe"'
caso "ausente: sugere o cp e o chmod" 'printf "%s" "$saida" | grep -q "chmod +x"'
caso "ausente: PARCIAL e RC 0" 'printf "%s" "$saida" | grep -qx "ESTADO=PARCIAL" && printf "%s" "$saida" | grep -qx "RC=0"'

# 4. atalho sem a linha "Fonte versionada": AVISO, nunca falha
cenario semcabecalho
printf '#!/usr/bin/env bash\necho agata sem cabecalho\n' > "$TMP/home-semcabecalho/.local/bin/agata"
saida="$(rodar "$TMP/home-semcabecalho")"
caso "sem cabeçalho: AVISO diz que a linha falta" 'printf "%s" "$saida" | grep -q "não tem a linha \"# Fonte versionada"'
caso "sem cabeçalho: devolve 0" 'printf "%s" "$saida" | grep -qx "RC=0"'

# 5. cabeçalho aponta para a fonte de OUTRO nome: o par não confere, AVISO
cenario outronome
printf '#!/usr/bin/env bash\n# Fonte versionada: ~/agata/redesign/systemd/seth-parar\necho agata\n' > "$TMP/home-outronome/.local/bin/agata"
saida="$(rodar "$TMP/home-outronome")"
caso "outro nome: AVISO de par que não confere" 'printf "%s" "$saida" | grep -q "declara como fonte .*seth-parar, que não é seth\."'
caso "outro nome: devolve 0" 'printf "%s" "$saida" | grep -qx "RC=0"'

# 6. fonte declarada que não existe no disco: AVISO
cenario fontesumida
rm -f "$TMP/home-fontesumida/agata/redesign/systemd/seth-parar"
saida="$(rodar "$TMP/home-fontesumida")"
caso "fonte sumida: AVISO diz que a fonte não existe" 'printf "%s" "$saida" | grep -q "a fonte declarada por .*fechar-agata não existe"'
caso "fonte sumida: devolve 0" 'printf "%s" "$saida" | grep -qx "RC=0"'

[ "$falhas" -eq 0 ] && echo "P-27 atalhos: OK" || echo "P-27 atalhos: $falhas FALHA(S)"
exit "$falhas"
