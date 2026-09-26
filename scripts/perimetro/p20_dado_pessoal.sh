#!/usr/bin/env bash
# P-20 -- dado pessoal em caminho de framework (plano de replicabilidade,
# MEMÓRIAS (560); desenhado pelo laboratório-nuvem "Ensaio", 25/09/2026).
# AVISA, nunca falha -- mesma doutrina de P-6/P-9/P-18/P-21: nenhum dos
# mecanismos de sanitização existentes (P-1, sanitizar.py, P-3) procura dado
# PESSOAL, só SEGREDO -- são classes diferentes (achado do laboratório,
# medido contra o repositório real: e-mail do Humano, IP/hostname do tailnet
# vazavam sem que nenhum controle enxergasse).
#
# Escopo desta fatia: só a direção de ENTRADA (commit), só linhas ADICIONADAS,
# só em caminho `framework|` do manifesto (config/caminhos-framework.txt) --
# um clone herda framework inteiro, nunca instância. A direção de SAÍDA
# (Fase 5, antes de exportar pro upstream) é a mesma função, chamada com
# --varrer <lista>; NÃO construída agora porque a ferramenta de merge
# seletivo da Fase 5 ainda não existe (nada para varrer antes de exportar).
#
# Lista de identificadores fora do repo, de propósito: no repositório PÚBLICO
# a lista seria o próprio vazamento. ~/.config/agata/identificadores-pessoais.txt
# (modo 600), formato "rotulo|regex ERE|prova" por linha -- a prova é o
# próprio dado real, sem problema porque o arquivo é privado. Testável via
# AGATA_P20_LISTA=<caminho> (só suíte/teste, nunca produção).
#
# Nunca reimprime o valor achado (achado do laboratório, L-3: o valor de um
# identificador saiu sem máscara numa transcrição antes). Só rótulo, arquivo
# e linha.

_p20_lista() {
  printf '%s' "${AGATA_P20_LISTA:-$HOME/.config/agata/identificadores-pessoais.txt}"
}

# Caminhos framework|, lidos do manifesto declarado -- nunca hardcoded aqui,
# senão duas fontes de verdade divergiriam (mesmo motivo do manifesto existir).
_p20_pathspecs_framework() {
  local manifesto="config/caminhos-framework.txt" linha classe caminho
  [ -f "$manifesto" ] || return 0
  while IFS='|' read -r classe caminho; do
    case "$classe" in \#*|"") continue ;; esac
    [ "$classe" = "framework" ] || continue
    printf '%s\n' "$caminho"
  done < "$manifesto"
}

# Carrega a lista em 3 arrays paralelos (rótulo/regex/prova). Retorna 1 se o
# arquivo não existe -- SKIP de propósito (aviso próprio, não erro de bash).
_p20_carregar() {
  local lista; lista="$(_p20_lista)"
  P20_ROTULOS=(); P20_REGEX=(); P20_PROVAS=()
  [ -f "$lista" ] || return 1
  local linha rotulo regex prova
  while IFS='|' read -r rotulo regex prova; do
    case "$rotulo" in \#*|"") continue ;; esac
    P20_ROTULOS+=("$rotulo"); P20_REGEX+=("$regex"); P20_PROVAS+=("$prova")
  done < "$lista"
  return 0
}

# Autoprova: cada regex tem que casar a própria prova, e só a própria --
# régua cega (não casa) é o mesmo perigo de P-1 (_autoprova_padroes):
# controle que "passa limpo" por não enxergar não é controle.
_p20_autoprova() {
  local i ruim=0 n
  for i in "${!P20_ROTULOS[@]}"; do
    n=$(printf '%s\n' "${P20_PROVAS[$i]}" | grep -cE -- "${P20_REGEX[$i]}" 2>/dev/null || true)
    if [ "${n:-0}" -lt 1 ]; then
      echo "AVISO (P-20): o identificador '${P20_ROTULOS[$i]}' tem regex que não casa a própria prova (ou está malformada) -- esta régua está cega e o dado passaria como limpo. O que fazer: corrigir a linha no arquivo de identificadores."
      ruim=1
    fi
  done
  return "$ruim"
}

_p20_permissao_ok() {
  local lista modo; lista="$(_p20_lista)"
  modo="$(stat -c '%a' "$lista" 2>/dev/null || stat -f '%Lp' "$lista" 2>/dev/null || true)"
  [ -n "$modo" ] || return 0
  if [ "$modo" != "600" ]; then
    echo "AVISO (P-20): a lista de identificadores tem permissão $modo, mais aberta que 600 -- outros usuários da Máquina leem o dado pessoal. O que fazer: chmod 600 $(_p20_lista)."
  fi
}

p20_dado_pessoal() {
  if ! _p20_carregar; then
    echo "AVISO (P-20): lista de identificadores ausente ($(_p20_lista)) -- o P-20 não tem o que procurar e não protege nada. O que fazer: criar o arquivo com modo 600, uma linha por identificador, no formato rotulo|regex|prova."
    return 0
  fi
  [ "${#P20_ROTULOS[@]}" -eq 0 ] && return 0
  _p20_autoprova || true
  _p20_permissao_ok || true

  local pathspecs=(); mapfile -t pathspecs < <(_p20_pathspecs_framework)
  [ "${#pathspecs[@]}" -eq 0 ] && return 0

  local arquivo diff_arquivo i linha_num conteudo
  while IFS= read -r arquivo; do
    [ -z "$arquivo" ] && continue
    diff_arquivo="$(git diff --cached -U0 -- "$arquivo" 2>/dev/null)"
    [ -z "$diff_arquivo" ] && continue
    for i in "${!P20_ROTULOS[@]}"; do
      # linhas ADICIONADAS (+, nunca +++ do cabeçalho), com o número de linha
      # real do lado novo -- grep -n aqui numera o DIFF, não o arquivo; por
      # isso usamos `git diff --cached -U0` com o próprio contexto de hunk
      # (mínimo, U0) e extraímos o número do cabeçalho @@ na mesma passada.
      while IFS= read -r bloco; do
        [ -z "$bloco" ] && continue
        linha_num="${bloco%%:*}"
        conteudo="${bloco#*:}"
        if printf '%s\n' "$conteudo" | grep -qE -- "${P20_REGEX[$i]}" 2>/dev/null; then
          echo "AVISO (P-20): $arquivo:$linha_num tem um identificador pessoal (${P20_ROTULOS[$i]}) num caminho que vai para os clones. Por que importa: o repositório é público e o framework é copiado para toda instância nova (plano de replicabilidade, Fase 5). O que fazer: trocar por um exemplo genérico, ou mover o trecho para PROJETO.md/MEMÓRIAS.md, que são instância e não vão."
        fi
      done < <(_p20_linhas_adicionadas_numeradas "$diff_arquivo")
    done
  done < <(git diff --cached --name-only -- "${pathspecs[@]}" 2>/dev/null)
  return 0
}

# Converte um diff -U0 de UM arquivo em "numero_da_linha_nova:conteudo", só
# das linhas adicionadas -- awk lê os cabeçalhos @@ -a,b +c,d @@ pra saber o
# número real da linha nova, sem depender de `git blame`/`grep -n` (que numera
# o próprio diff, não o arquivo).
_p20_linhas_adicionadas_numeradas() {
  awk '
    /^@@/ { match($0, /\+([0-9]+)/, m); n = m[1]; next }
    /^\+\+\+/ { next }
    /^\+/ { print n":"substr($0,2); n++; next }
  ' <<<"$1"
}
