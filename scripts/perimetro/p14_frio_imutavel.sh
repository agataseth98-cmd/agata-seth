#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.
#
# Reaberto em 25/09/2026 (memórias frias saindo da raiz para
# memoria/frio/, risco assumido por escrito pelo Humano -- ver a entrada
# de MEMÓRIAS que acompanha este commit) para distinguir RELOCAÇÃO
# legítima de EDIÇÃO disfarçada. Até aqui, qualquer path selado
# reaparecendo staged era SUSPEITO sem exceção (o teste
# "REGRESSAO (419): renomear chunk frio selado" existe exatamente pra
# isso). Essa dureza continua -- a exceção nova exige as DUAS provas
# juntas, nunca uma sozinha:
#   1. o SELOS.txt que vai entrar NESTE commit tem uma linha com o MESMO
#      hash de HEAD (imutável, não vem do commit em curso) num path
#      DIFERENTE do antigo;
#   2. o conteúdo REAL desse path novo, hasheado agora (nunca confiando
#      no texto do SELOS.txt como prova), bate com esse mesmo hash de
#      HEAD.
# Um ataque que edita o conteúdo e forja a linha do SELOS.txt pra
# "confirmar" a própria edição não passa: a prova 2 recalcula o hash do
# disco contra o valor de HEAD, que o commit em curso não controla.
# Sem as duas provas, cai no mesmo SUSPEITO de sempre -- nada relaxou.
p14_frio_imutavel() {
  [ -f SELOS.txt ] || return 0
  local ruim=0 arquivo staged tmp_saida selos_lista selos_lista_staged novo_path atual
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
  # Versão do SELOS.txt que vai entrar neste commit (índice); cai pro
  # disco se SELOS.txt não estiver staged -- mesmo bootstrap de sempre.
  selos_lista_staged="$(git show :SELOS.txt 2>/dev/null)" || selos_lista_staged=""
  [ -z "$selos_lista_staged" ] && selos_lista_staged="$(cat SELOS.txt 2>/dev/null)"
  while read -r hash_h arquivo _; do
    [ -z "$arquivo" ] && continue
    if echo "$staged" | grep -qxF "$arquivo"; then
      novo_path="$(echo "$selos_lista_staged" | awk -v h="$hash_h" -v velho="$arquivo" '$1==h && $2!=velho {print $2; exit}')"
      if [ -n "$novo_path" ]; then
        atual="$(sha256sum "$novo_path" 2>/dev/null | cut -d' ' -f1)"
        if [ "$atual" = "$hash_h" ]; then
          echo "INFO (P-14): '$arquivo' relocado para '$novo_path' -- hash de HEAD ($hash_h) confere no destino, conteúdo intacto. Tratado como mudança de local, não de história."
          continue
        fi
      fi
      echo "SUSPEITO (P-14): '$arquivo' está selado (SELOS.txt), já existia num commit anterior, e aparece staged neste commit -- chunk frio nunca recebe escrita depois de selado, e não achei destino de relocação com o mesmo hash de HEAD e conteúdo confere. O que fazer: 'git restore --staged $arquivo'; se o conteúdo mudou de verdade, o arquivo foi violado -- restaure também o conteúdo."
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

