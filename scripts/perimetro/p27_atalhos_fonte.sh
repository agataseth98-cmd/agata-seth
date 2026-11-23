#!/usr/bin/env bash
# P-27 (23/11/2026): atalho instalado em ~/.local/bin igual à fonte versionada que ele declara.
# Motivo medido: em 23/11/2026 ~/.local/bin/fechar-agata estava diferente de redesign/systemd/seth-parar sem ninguém
# perceber. O atalho roda a cópia instalada, não a do repositório; uma correção versionada pode nunca chegar ao uso.
# Decisão do Humano, 18/11/2026: o sistema precisa se atualizar sozinho.
#
# Pares (instalado <- fonte): ~/.local/bin/agata <- redesign/systemd/seth
#                             ~/.local/bin/fechar-agata <- redesign/systemd/seth-parar
# A fonte de cada par é a que o próprio atalho declara na linha "# Fonte versionada: ..." (hoje ~/agata/redesign/systemd/...),
# e o nome dela tem de bater com o do par. Assim a conferência não depende da worktree em que o perímetro roda.
#
# AVISA, nunca falha (mesma doutrina de P-6/P-9): diferença, ausência ou cabeçalho faltando viram AVISO com o comando
# de reinstalar. Não copia nada sozinho; corrigir é decisão do Humano.
p27_atalhos_fonte() {
  local par nome fonte_nome inst decl fonte raiz padrao atencao=0 ok=""
  raiz="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  for par in "agata:seth" "fechar-agata:seth-parar"; do
    nome="${par%%:*}"
    fonte_nome="${par##*:}"
    inst="${HOME:-}/.local/bin/$nome"
    padrao="$raiz/redesign/systemd/$fonte_nome"
    if [ ! -f "$inst" ]; then
      atencao=1
      echo "AVISO (P-27): $inst não existe -- o atalho \"$nome\" não está instalado."
      echo "  Por que importa: sem o atalho instalado, o comando não faz o que o repositório manda."
      echo "  O que fazer: cp $padrao $inst && chmod +x $inst"
      continue
    fi
    decl="$(sed -n 's/^# Fonte versionada: *//p' "$inst" | head -n1 | tr -d '\r' | sed 's/[[:space:]]*$//')"
    if [ -z "$decl" ]; then
      atencao=1
      echo "AVISO (P-27): $inst não tem a linha \"# Fonte versionada: ...\" -- não dá para conferir contra a fonte."
      echo "  Por que importa: sem a fonte declarada, uma diferença fica invisível."
      echo "  O que fazer: cp $padrao $inst   (a cópia do repositório traz a linha)"
      continue
    fi
    case "$decl" in
      "~/"*) fonte="${HOME:-}/${decl#"~/"}" ;;
      *) fonte="$decl" ;;
    esac
    if [ "$(basename "$fonte")" != "$fonte_nome" ]; then
      atencao=1
      echo "AVISO (P-27): $inst declara como fonte $fonte, que não é $fonte_nome."
      echo "  Por que importa: o par do atalho não confere; a comparação sairia contra o arquivo errado."
      echo "  O que fazer: corrija a linha \"# Fonte versionada\" do atalho para redesign/systemd/$fonte_nome, ou reinstale: cp $padrao $inst"
      continue
    fi
    if [ ! -f "$fonte" ]; then
      atencao=1
      echo "AVISO (P-27): a fonte declarada por $inst não existe: $fonte"
      echo "  Por que importa: sem a fonte, não há como saber se o atalho está atualizado."
      echo "  O que fazer: confira o checkout do sistema; a fonte versionada é redesign/systemd/$fonte_nome."
      continue
    fi
    if cmp -s "$inst" "$fonte"; then
      ok="$ok $nome"
      continue
    fi
    atencao=1
    echo "AVISO (P-27): $inst difere da fonte versionada $fonte."
    echo "  Por que importa: o atalho roda a cópia instalada, não a do repositório; uma correção versionada pode nunca chegar ao uso."
    echo "  O que fazer: cp $fonte $inst"
  done
  if [ "$atencao" -eq 0 ]; then
    echo "OK (P-27): atalhos instalados iguais às fontes versionadas:$ok."
    return 0
  fi
  set -- $ok
  echo "P-27: $# de 2 atalho(s) iguais à fonte versionada; os demais têm AVISO acima."
  PERIMETRO_ESTADO="PARCIAL"
  return 0
}
