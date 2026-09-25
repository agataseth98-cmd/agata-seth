#!/usr/bin/env bash
# P-21 -- o nome do sistema não sai como marcador cru (Fase 2 do plano de
# replicabilidade, MEMÓRIAS (559); desenho do laboratório "Ensaio", 25/09/2026).
# AVISA, nunca falha -- doutrina P-6/P-9/P-18: higiene de texto, não segurança.
#
# Três checagens, cada uma com escopo fechado:
#  (i)   fonte lida crua por LLM que usa o marcador traz a regra de resolução
#        nas primeiras 40 linhas;
#  (ii)  saída GERADA não traz o marcador onde ele devia ter sido resolvido --
#        só nas partes resolvidas: vault regras/ e canon/, Partes 1-2 do índice,
#        posições faladas no .hidrata.md. História fica fora de propósito:
#        (558)/(559) citam o marcador e são verbatim para sempre (Regra 4);
#  (iii) linha nova de MEMÓRIAS (staged) que COMEÇA por uma posição falada --
#        modelo copiando a linha de turno sem resolver.
#
# O marcador é montado em pedaços: escrito inteiro, este arquivo seria uma fonte
# com marcador sem a regra no topo (mesma convenção de _vs_k, varredura_segredo.sh).
# Sem `grep -q` no fim de pipeline: com pipefail, grep saindo cedo dá SIGPIPE no
# produtor e o pipeline "falha" tendo casado. Sempre `grep -c ... || true`.

_p21_tok() { printf '%s%s%s' '{{' 'NOME_SISTEMA' '}}'; }

P21_REGRA='campo "Nome do sistema:"'
P21_FONTES=("REGRAS.md" "PROMPT_CARREGAMENTO.md" ".agents/skills/*/SKILL.md" ".claude/skills/*/SKILL.md")
P21_VAULT_RESOLVIDO=("memoria/obsidian/regras" "memoria/obsidian/canon")
P21_INDICE="memoria/missoes/agata-sistema/derivado/indice.md"
P21_HIDRATA=(".hidrata.md")

# Posições faladas, ancoradas no começo da linha. Casam só onde o marcador
# substitui o nome falado; citação no meio da linha ou entre crases não casa.
_p21_padroes() {
  local t; t="$(_p21_tok | sed 's/[{}]/\\&/g')"
  printf '%s\n' \
    "^[[:space:]]*${t}[[:space:]]+·" \
    "^# REGRAS\\.md — Sistema ${t}" \
    "^Você não é um assistente genérico.* sistema ${t}" \
    "^1\\. Sou Modelo do ${t}"
}

_p21_autoprova() {
  local t i ruim=0 n; t="$(_p21_tok)"
  local provas=(
    "$t · modelo · t=1 (contado no contexto)"
    "# REGRAS.md — Sistema $t"
    "Você não é um assistente genérico nesta conversa. Você é um MODELO do sistema $t."
    "1. Sou Modelo do $t, não assistente genérico?"
  )
  local padroes=(); mapfile -t padroes < <(_p21_padroes)
  if [ "${#provas[@]}" -ne "${#padroes[@]}" ]; then
    echo "AVISO (P-21): ${#padroes[@]} padrões e ${#provas[@]} provas -- alguém mudou um lado sem o outro. Por que importa: padrão sem prova pode estar cego sem ninguém saber. O que fazer: parear _p21_padroes e _p21_autoprova."
    return 1
  fi
  for i in "${!padroes[@]}"; do
    n=$(printf '%s\n' "${provas[$i]}" | grep -cE -- "${padroes[$i]}" 2>/dev/null || true)
    if [ "${n:-0}" -lt 1 ]; then
      echo "AVISO (P-21): o padrão '${padroes[$i]}' não casa a própria prova -- esta régua está cega. O que fazer: consertar o padrão antes de confiar no P-21."
      ruim=1
    fi
    # negativo: o marcador citado no meio da linha nunca pode casar
    n=$(printf 'a entrada discute %s sem resolver\n' "$t" | grep -cE -- "${padroes[$i]}" 2>/dev/null || true)
    if [ "${n:-0}" -gt 0 ]; then
      echo "AVISO (P-21): o padrão '${padroes[$i]}' casa citação no meio da linha -- ia acusar entrada que só discute o marcador. O que fazer: reancorar o padrão."
      ruim=1
    fi
  done
  return "$ruim"
}

p21_nome_sistema() {
  local t f d p n adic; t="$(_p21_tok)"
  _p21_autoprova || true

  # (i) fonte crua com marcador e sem regra de resolução no topo
  while IFS= read -r f; do
    if [ -z "$f" ] || [ ! -f "$f" ]; then continue; fi
    n=$(grep -cF -- "$t" "$f" 2>/dev/null || true)
    if [ "${n:-0}" -eq 0 ]; then continue; fi
    n=$(head -n 40 "$f" | grep -cF -- "$P21_REGRA" || true)
    if [ "${n:-0}" -eq 0 ]; then
      echo "AVISO (P-21): $f usa o marcador do nome do sistema, mas não traz a regra de resolução nas primeiras 40 linhas. Por que importa: quem lê o arquivo cru não sabe o que escrever no lugar e tende a copiar o marcador. O que fazer: copiar para o topo de $f a frase de REGRAS.md que cita o $P21_REGRA."
    fi
  done < <(git ls-files -- "${P21_FONTES[@]}" 2>/dev/null)

  # (ii-a) vault: só as pastas que o gerador resolve inteiras
  for d in "${P21_VAULT_RESOLVIDO[@]}"; do
    if [ ! -d "$d" ]; then continue; fi
    while IFS= read -r f; do
      if [ -z "$f" ]; then continue; fi
      echo "AVISO (P-21): $f (vault, parte resolvida) traz o marcador cru. Por que importa: a Seth e o Humano leem o vault como se fosse o texto final. O que fazer: python3 scripts/gerar_obsidian.py e conferir o campo 'Nome do sistema:' do PROJETO.md."
    done < <(grep -rlF -- "$t" "$d" 2>/dev/null || true)
  done

  # (ii-b) índice: só Partes 1-2 (a Parte 3 é história verbatim)
  if [ -f "$P21_INDICE" ]; then
    n=$(awk '/^## PARTE 1 /{p=1} /^## PARTE 3 /{p=0} p' "$P21_INDICE" | grep -cF -- "$t" || true)
    if [ "${n:-0}" -gt 0 ]; then
      echo "AVISO (P-21): $P21_INDICE tem $n linha(s) com o marcador cru nas Partes 1-2. Por que importa: o índice vai assim para o Drive e o NotebookLM. O que fazer: python3 scripts/gerar_indice_derivado.py (a versão que resolve o nome)."
    fi
  fi

  # (ii-c) .hidrata: só posições faladas
  local padroes=(); mapfile -t padroes < <(_p21_padroes)
  for f in "${P21_HIDRATA[@]}"; do
    if [ ! -f "$f" ]; then continue; fi
    for p in "${padroes[@]}"; do
      n=$(grep -cE -- "$p" "$f" 2>/dev/null || true)
      if [ "${n:-0}" -gt 0 ]; then
        echo "AVISO (P-21): $f tem $n linha(s) com o marcador numa posição falada. Por que importa: é o texto que a Seth recebe. O que fazer: conferir .githooks/gerar-hidratacao.sh e o campo 'Nome do sistema:' do PROJETO.md."
      fi
    done
  done

  # (iii) entrada nova de MEMÓRIAS começando por posição falada
  adic=$(git diff --cached -U0 -- "MEMÓRIAS.md" 2>/dev/null | sed -n 's/^+//p' | grep -v '^++ ' || true)
  if [ -n "$adic" ]; then
    for p in "${padroes[@]}"; do
      n=$(printf '%s\n' "$adic" | grep -cE -- "$p" || true)
      if [ "${n:-0}" -gt 0 ]; then
        echo "AVISO (P-21): entrada nova de MEMÓRIAS.md tem $n linha(s) começando com o marcador do nome numa posição falada. Por que importa: é modelo copiando a linha de turno sem resolver, e vira história (Regra 4). O que fazer: corrigir antes do commit, trocando o marcador pelo nome do campo 'Nome do sistema:'."
      fi
    done
  fi
  return 0
}
