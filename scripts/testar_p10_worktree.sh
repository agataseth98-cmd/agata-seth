#!/usr/bin/env bash
# Contraprovas offline do P-10 em worktree vinculada (23/11/2026). Sem vault, a worktree não é "clone fresco":
# é SKIP isento (PERIMETRO_P17_ISENTO=1), que o P-17 não conta. No checkout principal, sem vault, continua
# SKIP comum (não isento). Com o vault presente na worktree, a conferência roda de verdade (não vira SKIP).
# Repositório descartável em $TMP. Saída 0 = todos os casos passaram.
set -u
unset GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE GIT_PREFIX GIT_COMMON_DIR GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_NAMESPACE
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
# shellcheck source=/dev/null
source "$RAIZ/scripts/perimetro/p10_vault_derivado.sh"
falhas=0
caso() { if eval "$2"; then echo "PASS  $1"; else echo "FALHA $1"; falhas=$((falhas + 1)); fi; }

PRINCIPAL="$TMP/principal"
VINCULADA="$TMP/vinculada"
git init -q "$PRINCIPAL"
git -C "$PRINCIPAL" -c user.name=teste -c user.email=teste@teste commit -q --allow-empty -m base
git -C "$PRINCIPAL" worktree add -q -b teste-p10-worktree "$VINCULADA" 2>/dev/null

# roda o P-10 dentro de um diretório, do jeito que o perímetro roda (na raiz do checkout)
rodar_p10() {  # $1 = diretório
  (
    cd "$1" || exit 9
    PERIMETRO_ESTADO=""; PERIMETRO_P17_ISENTO=0
    p10_vault_derivado
    rc=$?
    echo "ESTADO=$PERIMETRO_ESTADO ISENTO=$PERIMETRO_P17_ISENTO RC=$rc"
  )
}

# 1. checkout principal, sem vault: SKIP comum (clone fresco), não isento
saida="$(rodar_p10 "$PRINCIPAL")"
caso "principal sem vault: SKIP comum, não isento" 'printf "%s" "$saida" | grep -q "ESTADO=SKIP ISENTO=0 "'
caso "principal sem vault: mensagem de clone fresco, não de worktree" 'printf "%s" "$saida" | grep -q "ainda não existe" && ! printf "%s" "$saida" | grep -q "worktree vinculada"'

# 2. worktree vinculada, sem vault: SKIP isento, com a explicação
saida="$(rodar_p10 "$VINCULADA")"
caso "worktree sem vault: SKIP isento" 'printf "%s" "$saida" | grep -q "ESTADO=SKIP ISENTO=1 RC=0"'

# 3. worktree vinculada com vault presente: a conferência roda, não é SKIP isento
mkdir -p "$VINCULADA/memoria/obsidian"
saida="$(rodar_p10 "$VINCULADA")"
caso "worktree com vault: não vira SKIP isento" '! printf "%s" "$saida" | grep -q "ISENTO=1"'
caso "worktree com vault: a conferência de fato roda (não é SKIP)" '! printf "%s" "$saida" | grep -q "ESTADO=SKIP"'
rm -rf "$VINCULADA/memoria"

# 4. o detector: principal não é vinculada; worktree é
caso "detector: principal não é worktree vinculada" '! (cd "$PRINCIPAL" && _p10_worktree_vinculada)'
caso "detector: worktree é vinculada" '(cd "$VINCULADA" && _p10_worktree_vinculada)'

[ "$falhas" -eq 0 ] && echo "P-10 worktree: OK" || echo "P-10 worktree: $falhas FALHA(S)"
exit "$falhas"
