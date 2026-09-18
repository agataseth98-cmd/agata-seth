#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

# --- P-14 -----------------------------------------------------------------
# "Depois de selado, imutável" (MEMÓRIAS por período, Fase 4, MEMÓRIAS
# (357)). Um chunk MEMORIAS-FRIO-*.md listado em SELOS.txt nunca mais
# recebe escrita nenhuma -- nem sequer voltar a aparecer staged. Diferente
# de P-5 (que permite crescer): aqui a garantia é imutabilidade TOTAL.
# FALHA-class, mesma severidade de P-8 -- violar um selo é o mesmo tipo de
# "história editada" que Regra 4 existe pra impedir, só que na camada fria.
p14_frio_imutavel() {
  [ -f SELOS.txt ] || return 0
  local ruim=0 arquivo staged tmp_saida selos_lista
  # A lista de selos vem de HEAD:SELOS.txt, não do disco. Se viesse do
  # disco, apagar a linha de um chunk e reescrever o chunk no MESMO commit
  # tiraria os dois do radar: o loop abaixo nunca veria o nome, e o
  # selar.sh --check (a outra perna) também não -- o chunk sumiria do
  # relatório em vez de aparecer como VIOLADO. Medido em 09/09/2026 numa
  # cópia em sandbox. Lendo de HEAD, remover a linha não desprotege
  # retroativamente o que já estava selado. (O outro lado do conserto:
  # SELOS.txt entrou na quarentena P-8, então mexer nele exige aprovação
  # assinada.) Sem HEAD ainda (primeiro commit) cai pro disco -- bootstrap,
  # mesma lógica de _p8_assinatura_ok.
  selos_lista="$(git show HEAD:SELOS.txt 2>/dev/null)" || selos_lista=""
  [ -z "$selos_lista" ] && selos_lista="$(cat SELOS.txt 2>/dev/null)"
  # Só é violação re-tocar um chunk que JÁ existia selado num commit
  # ANTERIOR -- na própria commit que cria e sela o chunk pela primeira vez
  # ele necessariamente aparece staged, e isso é normal (mesmo bootstrap de
  # P-8: aprovar e criar acontecem juntos).
  # Antes esse caso era excluído por `--diff-filter=M` (só MODIFICADO, nunca
  # ADICIONADO). O filtro saiu, e o caso continua excluído por um motivo
  # melhor: a lista agora vem de HEAD:SELOS.txt, e no commit que cria o
  # chunk o selo dele ainda NÃO está em HEAD -- o nome nem entra no loop.
  # Trocar o filtro pela origem-em-HEAD amplia a cobertura de graça: agora
  # DELEÇÃO e RENOMEAÇÃO de um chunk já selado também são pegas, e o
  # `--diff-filter=M` deixava as duas passarem.
  # --no-renames pelo mesmo motivo de P-8/P-11 (furo medido nesta data):
  # sem ele o lado antigo de um rename some da listagem. Aqui o
  # selar.sh --check ainda pegaria pelo hash, mas os três controles devem
  # enxergar o mesmo conjunto de paths -- controle que enxerga menos do que
  # devia é falha do controle (REGRAS, Princípios: Segurança).
  staged="$(git -c core.quotepath=false diff --cached --no-renames --name-only)"
  while read -r _ arquivo _; do
    [ -z "$arquivo" ] && continue
    if echo "$staged" | grep -qxF "$arquivo"; then
      echo "SUSPEITO (P-14): '$arquivo' está selado (SELOS.txt), já existia num commit anterior, e aparece staged neste commit -- chunk frio nunca recebe escrita depois de selado. O que fazer: 'git restore --staged $arquivo'; se o conteúdo mudou de verdade, o arquivo foi violado -- restaure também o conteúdo."
      ruim=1
    fi
  done <<< "$selos_lista"
  tmp_saida="$(mktemp)"
  if ! bash "$_PERIMETRO_DIR/selar.sh" --check > "$tmp_saida" 2>&1; then
    echo "SUSPEITO (P-14): 'scripts/selar.sh --check' reprovou -- ao menos um chunk frio foi alterado depois de selado:"
    sed 's/^/  /' "$tmp_saida"
    ruim=1
  fi
  rm -f "$tmp_saida"
  return "$ruim"
}

