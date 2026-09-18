#!/usr/bin/env bash
# Extraido de scripts/perimetro.sh (item 10 do plano de mitigacao da
# auditoria do Marcos, MEMORIAS (437)) -- corte-e-cola, corpo identico ao
# de antes, nao e reescrita de logica.

# Mesmo padrão de propostas/APROVADO-<nome> (P-8): arquivo que o Humano
# cria pra autorizar, uso único, procurado em propostas/ e
# propostas/aplicadas/. Ecoa o caminho achado (não só 0/1) pro chamador
# poder citar qual marca disparou o ramo de permutação no aviso.
_p5_migracao_pendente() {
  local diretorio arq
  # PERIODO (Fase 4, MEMÓRIAS (357)): mecanismo RECORRENTE, ao contrário do
  # de (271) (uso único histórico) -- por isso pode continuar sendo achado
  # em propostas/aplicadas/ pra sempre sem risco: quem chama esta função
  # pra decidir o ramo PERIODO (`p5_append_only`) só olha pra marca DEPOIS
  # de o crescimento ordinário já ter falhado de verdade (quente/morno
  # encolheram), e mesmo assim quem prova que a migração é legítima é
  # `verificar_migracao_periodo.py` (byte a byte), não a marca sozinha.
  # Achado real, corrigido: uma versão anterior restringia a marca PERIODO
  # a só contar em propostas/ (pendente) -- resolvia o "nunca expira", mas
  # quebrava o padrão de sempre (marca commitada em aplicadas/ junto com o
  # resto) para o SEGUNDO corte de período. A ordem de decisão em
  # `p5_append_only` (ordinário primeiro) já resolve o "nunca expira" sem
  # precisar desta restrição.
  for diretorio in propostas propostas/aplicadas; do
    [ -d "$diretorio" ] || continue
    for arq in "$diretorio"/MIGRACAO-P5-*; do
      [ -e "$arq" ] && { echo "$arq"; return 0; }
    done
  done
  return 1
}


# --- P-5 -----------------------------------------------------------------
# "Registre e nunca apague" (REGRAS, Regra 4 -- linha vermelha). O
# controle mais forte do sistema. Compara os arquivos de camada quente/morna
# staged (o que vai virar o próximo commit) contra a versão do commit
# anterior (HEAD) -- não contra memória do executor.
#
# Desde MEMÓRIAS (271), 26/08/2026: MEMÓRIAS.md cresce pelo TOPO do corpo
# (logo após o marcador ENTRADAS-NOVAS). Desde "MEMÓRIAS por período"
# (Fase 4, MEMÓRIAS (357)): MEMORIAS-MORNO.md existe como segunda camada,
# mesma disciplina de crescimento por topo, e um chunk MEMORIAS-FRIO-*.md
# uma vez selado não é mais protegido por P-5 -- vira P-14
# (imutabilidade total, nunca mais escrita nenhuma, nem por sufixo).
#
# Ramos, nesta ordem de prioridade:
#   0. Marca de migração de PERÍODO presente (propostas*/MIGRACAO-P5-PERIODO-<nome>)
#      -- checagem de PERMUTAÇÃO entre CAMADAS via
#      scripts/verificar_migracao_periodo.py: união de quente+morno (HEAD)
#      == união de quente+morno+frio-novo (staged), byte-idêntico, só
#      realocado. Cada corte de período usa esta marca -- não é uso único
#      como o item 1 abaixo, é o mecanismo recorrente da Fase 4.
#   1. Marca de migração ANTIGA presente (MIGRACAO-P5-<nome>, sem
#      "PERIODO") -- checagem de PERMUTAÇÃO só de MEMÓRIAS.md via
#      scripts/verificar_migracao_memorias.py. Único uso esperado: a
#      migração de (271). Preservado por compatibilidade histórica.
#   2. Sem marca: roda o sufixo/prefixo normal (_p5_checar_sufixo, abaixo)
#      pra MEMÓRIAS.md E, se já existir no HEAD, pra MEMORIAS-MORNO.md --
#      as duas independentemente, as duas têm que passar.
_p5_checar_sufixo() {
  local caminho="$1" rotulo="$2"
  local tmp_antigo tmp_novo codigo
  tmp_antigo="$(mktemp)"
  tmp_novo="$(mktemp)"
  if ! git show "HEAD:$caminho" > "$tmp_antigo" 2>/dev/null; then
    # Arquivo não existia no HEAD (ex.: MEMORIAS-MORNO.md antes da
    # primeira migração de período) -- nada a proteger ainda, ele nasce
    # com o primeiro commit que o cria, fora do escopo deste controle.
    rm -f "$tmp_antigo" "$tmp_novo"
    return 0
  fi
  if ! git show ":$caminho" > "$tmp_novo" 2>/dev/null; then
    cat "$caminho" > "$tmp_novo" 2>/dev/null
  fi
  if grep -qF "$_P5_MARCADOR" "$tmp_antigo"; then
    python3 - "$tmp_antigo" "$tmp_novo" "$rotulo" <<'PYEOF'
import sys
MARCADOR = "<!-- ENTRADAS-NOVAS:AQUI".encode("utf-8")
rotulo = sys.argv[3]
with open(sys.argv[1], 'rb') as f:
    antigo = f.read()
with open(sys.argv[2], 'rb') as f:
    novo = f.read()
i_antigo = antigo.find(MARCADOR)
i_novo = novo.find(MARCADOR)
if i_antigo == -1:
    print(f"SUSPEITO (P-5): marcador ENTRADAS-NOVAS não achado no commit anterior de {rotulo} apesar do grep externo achar -- inconsistência, restaure antes de comitar.")
    sys.exit(1)
if i_novo == -1:
    print(f"SUSPEITO (P-5, nunca se apaga história): marcador ENTRADAS-NOVAS existia no commit anterior de {rotulo} e sumiu no staged -- não se apaga a âncora de append-only.")
    sys.exit(1)
fim_linha_antigo = antigo.find(b'\n', i_antigo) + 1
fim_linha_novo = novo.find(b'\n', i_novo) + 1
corpo_antigo = antigo[fim_linha_antigo:]
corpo_novo = novo[fim_linha_novo:]
if len(corpo_novo) < len(corpo_antigo):
    print(f"SUSPEITO (P-5, nunca se apaga história): corpo de {rotulo} ENCOLHEU -- {len(corpo_antigo)} bytes no commit anterior, {len(corpo_novo)} agora. Alguma entrada foi removida (ou precisa da marca de migração de período). Restaure antes de comitar.")
    sys.exit(1)
if not corpo_novo.endswith(corpo_antigo):
    print(f"SUSPEITO (P-5, nunca se apaga história): o conteúdo antigo de {rotulo} não é mais um SUFIXO do novo -- uma entrada já registrada foi alterada, ou a entrada nova não entrou logo após o marcador. Restaure antes de comitar.")
    sys.exit(1)
sys.exit(0)
PYEOF
    codigo=$?
  else
    python3 - "$tmp_antigo" "$tmp_novo" "$rotulo" <<'PYEOF'
import sys
rotulo = sys.argv[3]
with open(sys.argv[1], 'rb') as f:
    antigo = f.read()
with open(sys.argv[2], 'rb') as f:
    novo = f.read()
if len(novo) < len(antigo):
    print(f"SUSPEITO (P-5, nunca se apaga história): {rotulo} ENCOLHEU -- {len(antigo)} bytes no commit anterior, {len(novo)} agora. Alguma linha foi removida. Restaure antes de comitar.")
    sys.exit(1)
if novo[:len(antigo)] != antigo:
    for i, (a, b) in enumerate(zip(antigo, novo)):
        if a != b:
            print(f"SUSPEITO (P-5, nunca se apaga história): byte mudou no offset {i} de {rotulo} -- não é mais append-only. Um trecho antigo foi alterado. Restaure antes de comitar.")
            print(f"  antigo: ...{antigo[max(0,i-40):i+40]!r}...")
            print(f"  novo:   ...{novo[max(0,i-40):i+40]!r}...")
            break
    sys.exit(1)
sys.exit(0)
PYEOF
    codigo=$?
  fi
  rm -f "$tmp_antigo" "$tmp_novo"
  return "$codigo"
}


# Checagem de PERMUTAÇÃO entre camadas pra migração de período: união de
# {MEMÓRIAS.md, MEMORIAS-MORNO.md} no HEAD (as que existirem) tem que
# bater, byte a byte, com a união de {MEMÓRIAS.md, MEMORIAS-MORNO.md,
# todo MEMORIAS-FRIO-*.md ADICIONADO nesta commit} no staged. Chunk frio
# já existente no HEAD nunca entra aqui -- depois de selado é P-14, não
# P-5 (nunca deveria mudar de novo).
_p5_periodo_verificar() {
  local -a antes=() depois=()
  local f tmp staged_frio
  for f in "MEMÓRIAS.md" "MEMORIAS-MORNO.md"; do
    if git show "HEAD:$f" >/dev/null 2>&1; then
      tmp="$(mktemp)"; git show "HEAD:$f" > "$tmp"; antes+=("$tmp")
    fi
    if git show ":$f" >/dev/null 2>&1; then
      tmp="$(mktemp)"; git show ":$f" > "$tmp"; depois+=("$tmp")
    fi
  done
  staged_frio="$(git diff --cached --name-only --diff-filter=A -- 'MEMORIAS-FRIO-*.md' 2>/dev/null)"
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    tmp="$(mktemp)"; git show ":$f" > "$tmp"; depois+=("$tmp")
  done <<< "$staged_frio"

  if [ "${#antes[@]}" -eq 0 ]; then
    echo "SUSPEITO (P-5, período): marca de migração presente mas nenhum arquivo de quente/morno achado no HEAD -- nada a comparar, restaure antes de comitar."
    rm -f "${depois[@]}"
    return 1
  fi
  python3 "$_PERIMETRO_DIR/verificar_migracao_periodo.py" --antes "${antes[@]}" --depois "${depois[@]}"
  local codigo=$?
  rm -f "${antes[@]}" "${depois[@]}"
  return "$codigo"
}


p5_append_only() {
  P5_RAMO="ordinario"
  P5_ENTRADAS_NOVAS=0
  if ! git rev-parse HEAD >/dev/null 2>&1; then
    return 0
  fi
  # Achado real ao testar (15/08/2026): `trap ... RETURN` dentro de uma
  # função não fica limitada a ela -- o bash não escopa isso por chamada.
  # Corrigido: limpeza explícita em cada saída, sem trap (vale pros
  # helpers acima também).
  #
  # (271), sem PERIODO no nome: branch histórico, prioridade sobre o resto,
  # comportamento intocado desde sempre -- reordenação de MEMÓRIAS.md não é
  # suficiente-crescimento, tem que ir direto pra permutação.
  local marca_migracao
  marca_migracao="$(_p5_migracao_pendente)" || true
  if [ -n "$marca_migracao" ] && [[ "$marca_migracao" != *PERIODO* ]]; then
    P5_RAMO="permutacao"
    echo "P-5: marca de migração '$marca_migracao' presente -- checagem de PERMUTAÇÃO (verificar_migracao_memorias.py), não de sufixo. Uso único, MEMÓRIAS (271)."
    local tmp_antigo tmp_novo codigo
    tmp_antigo="$(mktemp)"; tmp_novo="$(mktemp)"
    if ! git show HEAD:MEMÓRIAS.md > "$tmp_antigo" 2>/dev/null; then
      rm -f "$tmp_antigo" "$tmp_novo"; return 0
    fi
    if ! git show :MEMÓRIAS.md > "$tmp_novo" 2>/dev/null; then
      cat MEMÓRIAS.md > "$tmp_novo" 2>/dev/null
    fi
    if python3 "$_PERIMETRO_DIR/verificar_migracao_memorias.py" "$tmp_antigo" "$tmp_novo"; then
      codigo=0
    else
      codigo=1
    fi
    rm -f "$tmp_antigo" "$tmp_novo"
    return "$codigo"
  fi

  # PERIODO (Fase 4): ao contrário de (271), tenta o crescimento ORDINÁRIO
  # primeiro -- quente/morno crescendo normalmente (entrada nova) não
  # precisa de marca nenhuma, igual a todo commit de sempre. Só cai pra
  # permutação entre camadas se o crescimento ordinário genuinamente
  # falhar (encolheu de verdade -- migração real aconteceu). Achado
  # preparando o segundo corte de período: a versão anterior dava
  # prioridade à marca ANTES de tentar o ordinário, e uma marca antiga
  # esquecida em propostas/aplicadas/ forçava todo commit seguinte (mesmo
  # um sem migração nenhuma, só entrada nova) pela checagem de permutação
  # estrita, reprovando por "conteúdo novo". Nesta ordem, uma marca velha
  # nunca atrapalha um commit ordinário -- e quando a permutação É
  # necessária, o verificador (byte a byte) continua sendo a rede de
  # segurança real, não a marca.
  # Tentativa silenciosa primeiro -- saída só é impressa se for mesmo o
  # veredito final (senão, "ENCOLHEU" apareceria no log de um commit que
  # vai passar de qualquer jeito pela permutação, achado mais confuso que
  # útil de propósito).
  local saida_quente saida_morno cod_quente cod_morno
  saida_quente="$(_p5_checar_sufixo "MEMÓRIAS.md" "MEMÓRIAS.md (quente)" 2>&1)"; cod_quente=$?
  saida_morno="$(_p5_checar_sufixo "MEMORIAS-MORNO.md" "MEMORIAS-MORNO.md (morno)" 2>&1)"; cod_morno=$?
  if [ "$cod_quente" -eq 0 ] && [ "$cod_morno" -eq 0 ]; then
    return 0
  fi
  if [ -n "$marca_migracao" ]; then
    P5_RAMO="permutacao"
    echo "P-5: crescimento ordinário falhou (quente/morno encolheram) e marca '$marca_migracao' está presente -- checagem de PERMUTAÇÃO entre camadas (verificar_migracao_periodo.py), quente+morno+frio. MEMÓRIAS por período (Fase 4)."
    local saida_perm codigo_perm
    saida_perm="$(_p5_periodo_verificar 2>&1)"; codigo_perm=$?
    [ -n "$saida_perm" ] && echo "$saida_perm"
    # O verificador separa "entrada realocada byte-idêntica" de "entrada NOVA
    # genuína" e imprime a contagem das novas. Se veio entrada nova, este
    # commit TEM conteúdo inédito -- e o P-7 não pode pular alegando que não
    # há nada a citar. Medido em 09/09/2026: uma entrada gravada no lugar
    # errado (fim do arquivo, em vez do topo abaixo do marcador) derruba o
    # crescimento ordinário, cai aqui, passa como permutação legítima com
    # "+1 entrada nova genuína" -- e o P-7 pulava justo o commit que trazia
    # a citação nova. Achado pela suíte scripts/testar_perimetro.sh no
    # primeiro dia dela, contra um furo que o conserto do dia anterior
    # ((419)) tinha acabado de criar.
    if echo "$saida_perm" | grep -qE '[1-9][0-9]* entrada\(s\) nova\(s\) genuína\(s\)'; then
      P5_ENTRADAS_NOVAS=1
    fi
    return "$codigo_perm"
  fi
  [ -n "$saida_quente" ] && echo "$saida_quente"
  [ -n "$saida_morno" ] && echo "$saida_morno"
  local ruim=0
  [ "$cod_quente" -eq 0 ] || ruim=1
  [ "$cod_morno" -eq 0 ] || ruim=1
  return "$ruim"
}

