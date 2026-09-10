#!/usr/bin/env bash
# scripts/testar_perimetro.sh -- suite de regressao DOS CONTROLES.
#
# POR QUE ISTO EXISTE (MEMORIAS (421)):
# Ate 09/09/2026 nada neste repositorio testava os controles. O resultado,
# medido: o P-7 ficou MORTO por 79 commits sem ninguem notar, e o P-8 e o
# P-11 eram cegos a renomeacao provavelmente desde que nasceram. Os quatro
# furos da (419) foram achados por auditoria manual -- se ninguem tivesse
# sentado pra procurar, continuariam abertos. Controle que ninguem testa
# nao e' controle, e' cerimonia.
#
# O QUE ESTA SUITE E': casos vermelho/verde contra um CLONE DESCARTAVEL do
# repositorio, nunca contra o repo real. Cada caso diz o que espera:
#   PEGA   -- o controle TEM que acusar (se nao acusar, ha um furo)
#   PASSA  -- o controle NAO pode acusar (se acusar, e' falso positivo)
# Falso positivo e' falha tanto quanto furo: controle que grita a toa e'
# desligado pelo operador, e ai nao protege mais nada.
#
# COMO RODAR:  bash scripts/testar_perimetro.sh          (tudo)
#              bash scripts/testar_perimetro.sh P-8      (so um controle)
#
# QUEM RODA SOZINHO: o P-16 (em perimetro.sh) dispara esta suite quando um
# arquivo de controle esta staged -- nao da' pra mudar os controles sem que
# os testes deles rodem. Custo zero nos commits que nao tocam controle.
#
# TESTA A ARVORE DE TRABALHO, nao o HEAD: o clone recebe uma copia de
# scripts/ e .githooks/ como estao no disco AGORA. E' o que voce esta prestes
# a commitar que e' exercitado.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILTRO="${1:-}"
export AGATA_TESTE_PERIMETRO=1   # impede o P-16 de recursar dentro do clone

OK=0; FALHOU=0; PULADO=0
falhas_detalhe=()

_cor() { [ -t 1 ] && printf '\033[%sm%s\033[0m' "$1" "$2" || printf '%s' "$2"; }

# ---------------------------------------------------------------- clone ----
CLONE=""
_montar_clone() {
  CLONE="$(mktemp -d -t agata-teste-perimetro.XXXXXX)"
  if ! git clone -q --no-hardlinks "$RAIZ" "$CLONE/repo" 2>/dev/null; then
    echo "ABORTADO: nao consegui clonar $RAIZ" >&2; exit 2
  fi
  # A arvore de trabalho manda: copia scripts/ e .githooks/ por cima do que
  # veio do HEAD, senao a suite testaria a versao ANTIGA dos controles --
  # exatamente o falso verde que ela existe pra impedir.
  cp -a "$RAIZ/scripts/." "$CLONE/repo/scripts/" 2>/dev/null || true
  cp -a "$RAIZ/.githooks/." "$CLONE/repo/.githooks/" 2>/dev/null || true
  ( cd "$CLONE/repo" && git -c user.email=teste@agata -c user.name=teste \
      commit -q --no-verify -am "base da suite: arvore de trabalho" 2>/dev/null ) || true
}
_limpar_clone() { [ -n "$CLONE" ] && rm -rf "$CLONE"; CLONE=""; }
trap _limpar_clone EXIT

_reset() { ( cd "$CLONE/repo" && git reset -q --hard HEAD && git clean -qfdx ) 2>/dev/null; }

# Escreve entrada nova NO LUGAR CERTO: topo do corpo, logo abaixo do marcador
# ENTRADAS-NOVAS (desde MEMORIAS (271)). Existe porque a primeira versao desta
# suite anexava no FIM do arquivo -- lugar errado -- e isso derrubava o
# crescimento ordinario do P-5, jogava a corrida no ramo de permutacao e fazia
# o P-7 pular. O teste "falhava" por defeito do fixture, nao do controle. Um
# fixture que nao imita o sistema de verdade produz vermelho falso, que custa
# tanta confianca quanto verde falso.
_nova_entrada() {
  python3 - "$1" <<'PY'
import io,sys
p="MEMÓRIAS.md"; s=io.open(p,encoding="utf-8").read()
i=s.index("<!-- ENTRADAS-NOVAS:AQUI"); fim=s.index("\n",i)+1
io.open(p,"w",encoding="utf-8").write(s[:fim]+"\n"+sys.argv[1].rstrip("\n")+"\n\n"+s[fim:].lstrip("\n"))
PY
}
# ... e no lugar ERRADO (fim fisico do arquivo), de proposito: e' o caminho
# que cai na permutacao. Usado so pelo caso de regressao que exige que a
# citacao continue sendo checada mesmo assim.
_entrada_no_fim() { printf '\n%s\n' "$1" >> "MEMÓRIAS.md"; }

# Quantos SUSPEITO/FALHA o controle $1 emitiu no estado atual do indice.
_acusacoes() {
  local ctrl="$1"
  ( cd "$CLONE/repo" && bash scripts/perimetro.sh 2>&1 ) \
    | sed -n "/^=== ${ctrl} ===/,/^=== /p" \
    | grep -cE "^(SUSPEITO|FALHA)" || true
}

# _caso <controle> <PEGA|PASSA> <nome> -- o setup vem no stdin, rodado no clone
_caso() {
  local ctrl="$1" espera="$2" nome="$3" setup n
  if [ -n "$FILTRO" ] && [ "$ctrl" != "$FILTRO" ]; then PULADO=$((PULADO+1)); return; fi
  setup="$(cat)"
  _reset
  if ! ( cd "$CLONE/repo" && eval "$setup" ) >/dev/null 2>&1; then
    FALHOU=$((FALHOU+1))
    falhas_detalhe+=("$ctrl/$nome: o SETUP falhou (o teste nao chegou a rodar)")
    printf '  %s %-7s %s\n' "$(_cor '1;31' 'ERRO ')" "$ctrl" "$nome"
    return
  fi
  n="$(_acusacoes "$ctrl")"
  local bom=0
  [ "$espera" = "PEGA"  ] && [ "$n" -ge 1 ] && bom=1
  [ "$espera" = "PASSA" ] && [ "$n" -eq 0 ] && bom=1
  if [ "$bom" = 1 ]; then
    OK=$((OK+1)); printf '  %s %-7s %s\n' "$(_cor '0;32' ' ok  ')" "$ctrl" "$nome"
  else
    FALHOU=$((FALHOU+1))
    falhas_detalhe+=("$ctrl/$nome: esperava $espera, obteve $n acusacao(oes)")
    printf '  %s %-7s %s  (esperava %s, obteve %s)\n' "$(_cor '1;31' 'FALHA')" "$ctrl" "$nome" "$espera" "$n"
  fi
}

# ---------------------------------------------------- cobertura declarada --
# Todo controle do perimetro tem de ter OU caso nesta suite OU um motivo
# ESCRITO aqui. Silencio nao e' opcao -- e' o P-16 que cobra.
#
# Por que isto existe: em 09/09/2026 a suite nasceu cobrindo 5 dos 16
# controles. Os outros 11 nao estavam "isentos" -- estavam ESQUECIDOS, e
# ninguem saberia dizer quais. A diferenca entre "nao da' pra testar" e
# "ninguem testou ainda" e' exatamente a diferenca entre P-7 dispensado e
# P-7 morto. Agora essa diferenca esta escrita, com nome e motivo.
#
# Regra pra quem mexer aqui: mover um controle desta lista PRA a suite e'
# sempre progresso. Acrescentar controle novo a esta lista exige motivo que
# alguem leia e concorde -- "e' dificil" nao e' motivo.
declare -A SEM_TESTE=(
  [P-2]="exige root para ler /etc/sudoers.d; a suite roda como usuario comum e nao vai pedir sudo pra testar"
  [P-3]="depende do estado do REMOTO (publicacao); um clone descartavel nao reproduz a condicao"
  [P-4]="depende de portas e processos VIVOS da Maquina; dentro do clone nao ha o que bindar"
  [P-6]="depende de marcador temporal e do HD de backup montado; nao reproduzivel offline"
  [P-9]="depende de unidades systemd vivas do usuario; o clone nao tem servicos"
  [P-10]="compara o vault derivado com HEAD; testa-lo exigiria gerar o vault inteiro no clone (minutos por caso)"
  [P-12]="exige o HD de backup montado e o repositorio restic; e' o mesmo motivo do PARCIAL que ele ja declara"
  [P-13]="relogio de 4 semanas; o caso depende de data e nao de estado do indice"
  [P-15]="depende do log de sucessos do Conselho Remoto, que so existe apos chamadas de rede reais"
  [P-16]="e' quem RODA esta suite; testa-lo aqui dentro recursa (a guarda AGATA_TESTE_PERIMETRO existe por isso)"
  [P-17]="conta series ENTRE corridas; um caso de indice nao expressa 'decima corrida seguida'"
)

# ------------------------------------------------------------------ casos --
_montar_clone
echo "suite de regressao dos controles -- clone descartavel, repo real intocado"
echo

# --- P-8: quarentena ------------------------------------------------------
# O caso "rename-pra-fora" e' o furo de (419): sem --no-renames o git mostra
# so o path NOVO, e mover um arquivo de comportamento pra fora dos padroes o
# tirava da quarentena sem APROVADO- nenhum.
_caso P-8 PEGA "editar arquivo de comportamento no lugar" <<'EOF'
echo "# sujo" >> redesign/router/sanitizar.py && git add redesign/router/sanitizar.py
EOF

_caso P-8 PEGA "REGRESSAO (419): renomear comportamento pra fora da quarentena" <<'EOF'
git mv redesign/router/sanitizar.py extras/sanitizar-fugitivo.py && git add -A
EOF

_caso P-8 PEGA "REGRESSAO (419): mover script de controle pra extras/" <<'EOF'
git mv scripts/checar_citacao.sh extras/checar_citacao.sh && git add -A
EOF

_caso P-8 PEGA "deletar arquivo de comportamento sem aprovacao" <<'EOF'
git rm -q redesign/router/sanitizar.py && git add -A
EOF

_caso P-8 PEGA "(419): SELOS.txt agora e' comportamento" <<'EOF'
echo "" >> SELOS.txt && git add SELOS.txt
EOF

_caso P-8 PEGA "(419): .gitignore agora e' comportamento" <<'EOF'
echo "# x" >> .gitignore && git add .gitignore
EOF

_caso P-8 PEGA "(419): redesign/obsidian/*.py agora e' comportamento" <<'EOF'
echo "# x" >> redesign/obsidian/ro_proxy.py && git add redesign/obsidian/ro_proxy.py
EOF

_caso P-8 PASSA "FALSO POSITIVO: renomear arquivo comum dentro de extras/" <<'EOF'
f=$(git ls-files 'extras/*.md' | head -1); git mv "$f" "${f%.md}-renomeado.md" && git add -A
EOF

_caso P-8 PASSA "FALSO POSITIVO: commit so em MEMORIAS.md" <<'EOF'
_nova_entrada "(9999) DIARIO — 01/01/2026 · teste." && git add "MEMÓRIAS.md"
EOF

# --- P-11: silos ----------------------------------------------------------
_caso P-11 PEGA "silo staged com nome de silo" <<'EOF'
printf 'modelo-alvo: seth\nMOD privado\n' > .hidrata-teste.md && git add -f .hidrata-teste.md
EOF

_caso P-11 PEGA "REGRESSAO (419): silo renomeado pra nome inocente" <<'EOF'
printf 'modelo-alvo: seth\nMOD privado\n' > .hidrata-teste.md && git add -f .hidrata-teste.md \
  && git mv .hidrata-teste.md notas-publicas.md
EOF

_caso P-11 PEGA "REGRESSAO (419): silo COPIADO (nunca teve nome de silo)" <<'EOF'
printf 'modelo-alvo: seth\nMOD privado\n' > notas-inocentes.md && git add notas-inocentes.md
EOF

_caso P-11 PASSA "FALSO POSITIVO: MEMORIAS citando o formato modelo-alvo" <<'EOF'
_nova_entrada "(9999) DIARIO — 01/01/2026 · texto sobre o cabecalho modelo-alvo: usado em bloco MOD." && git add "MEMÓRIAS.md"
EOF

# --- P-5: append-only, a LINHA VERMELHA -----------------------------------
# P-5 guarda a Regra 4 ("Registre e nunca apague"), que as REGRAS declaram
# linha vermelha -- nem o Humano pede pra cruzar. Estava sem UM caso de
# teste ate 09/09/2026, e foi o proprio portao de cobertura do P-16 que
# cobrou, nesta mesma sessao. O controle mais grave do sistema era o menos
# exercitado.
_caso P-5 PASSA "FALSO POSITIVO: entrada nova no topo (crescimento ordinario)" <<'EOF'
_nova_entrada "(9999) DIARIO — 01/01/2026 · entrada legitima." && git add "MEMÓRIAS.md"
EOF

_caso P-5 PEGA "apagar uma linha de MEMORIAS" <<'EOF'
python3 - <<'PY2'
import io
p="MEMÓRIAS.md"; L=io.open(p,encoding="utf-8").read().split("\n")
del L[60]
io.open(p,"w",encoding="utf-8").write("\n".join(L))
PY2
git add "MEMÓRIAS.md"
EOF

# A 1a versao deste caso trocava o primeiro "DIÁRIO" do arquivo e dava
# VERMELHO FALSO: o primeiro fica no PREAMBULO (a legenda dos tipos de
# entrada), ACIMA do marcador ENTRADAS-NOVAS -- zona que o P-5 legitimamente
# nao policia. Fixture ruim acusa controle inocente, e foi a terceira vez
# nesta sessao. Por isso este caso ancora explicitamente ABAIXO do marcador.
_caso P-5 PEGA "editar entrada que ja existia (abaixo do marcador)" <<'EOF'
python3 - <<'PY2'
import io
p="MEMÓRIAS.md"; L=io.open(p,encoding="utf-8").read().split("\n")
i=next(k for k,l in enumerate(L) if "ENTRADAS-NOVAS:AQUI" in l)
alvo=next(k for k in range(i+1,len(L)) if len(L[k])>80)
L[alvo]=L[alvo].replace("a","@",3)
io.open(p,"w",encoding="utf-8").write("\n".join(L))
PY2
git add "MEMÓRIAS.md"
EOF

# --- P-7: citacao ---------------------------------------------------------
# O furo de (419): a marca de migracao em propostas/aplicadas/ (que nunca e'
# limpo, por desenho) deixava o P-7 em SKIP permanente. SKIP nao emite
# acusacao, entao o caso "citacao fabricada" cobre os dois de uma vez: se o
# P-7 voltar a pular, este teste falha.
_caso P-7 PEGA "REGRESSAO (419): citacao fabricada e' pega mesmo com marca de migracao presente" <<'EOF'
_nova_entrada "(9999) DIARIO — 01/01/2026 · teste citando (9876 - entrada que nunca existiu) de proposito."
git add "MEMÓRIAS.md"
EOF

# Furo achado pela PROPRIA suite em 09/09/2026, no primeiro dia dela: o
# conserto de (419) fez o P-7 pular sempre que o P-5 ia pela permutacao --
# mas permutacao COM entrada nova existe (entrada gravada no fim do arquivo
# derruba o crescimento ordinario e cai la). O commit trazia citacao nova e
# ninguem checava. Este caso e' a trava contra a volta disso.
_caso P-7 PEGA "REGRESSAO: citacao fabricada em entrada nova que caiu na PERMUTACAO" <<'EOF'
_entrada_no_fim "(9999) DIARIO — 01/01/2026 · teste citando (9876 - entrada que nunca existiu) de proposito."
git add "MEMÓRIAS.md"
EOF

_caso P-7 PASSA "FALSO POSITIVO: citacao real com sintese coerente" <<'EOF'
_nova_entrada "(9999) DIARIO — 01/01/2026 · teste citando (417 - TES-001 e TES-002 aposentados por decisao do Humano)."
git add "MEMÓRIAS.md"
EOF

# --- P-14: chunk frio selado ---------------------------------------------
_caso P-14 PEGA "modificar chunk frio ja selado" <<'EOF'
a=$(awk 'NR==1{print $2}' SELOS.txt); printf '\nadulterado\n' >> "$a" && git add "$a"
EOF

_caso P-14 PEGA "REGRESSAO (419): renomear chunk frio selado" <<'EOF'
a=$(awk 'NR==1{print $2}' SELOS.txt); git mv "$a" "RENOMEADO-$a" && git add -A
EOF

_caso P-14 PEGA "REGRESSAO (419): apagar a linha do SELOS e reescrever o chunk" <<'EOF'
a=$(awk 'NR==1{print $2}' SELOS.txt)
grep -vF " $a " SELOS.txt > /tmp/selos.$$ && mv /tmp/selos.$$ SELOS.txt
printf '\nadulterado\n' >> "$a" && git add -A
EOF

# --- P-1: regua de segredo ------------------------------------------------
# (419): os padroes nao pegavam NENHUMA das chaves que este sistema usa.
#
# As chaves de teste sao MONTADAS EM PEDACOS, nunca escritas inteiras. Motivo
# concreto, achado ao commitar esta suite pela primeira vez: escrita inteira,
# a fixture casa os proprios padroes e o P-1 barra o commit do teste -- o
# varredor acusando o teste do varredor. A saida NAO e' abrir excecao no P-1
# (excecao no varredor de segredo e' exatamente o buraco que (419) fechou);
# e' nao deixar o literal existir no arquivo. Mesma convencao ja usada em
# redesign/router/sanitizar.py (_fx / _FIXTURES_CASA).
_k() { local IFS=""; printf '%s' "$*"; }

_A40="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
while IFS='|' read -r _nome _chave; do
  [ -z "$_nome" ] && continue
  _caso P-1 PEGA "chave $_nome nao pode passar" <<EOF
printf 'chave colada em prosa: $_chave\n' > vazamento.md && git add vazamento.md
EOF
done <<LISTA
anthropic|$(_k "sk" "-" "ant" "-api03-" "$_A40")
openrouter|$(_k "sk" "-" "or" "-v1-" "0000000000000000000000000000000000000000")
groq|$(_k "gs" "k" "_" "$_A40" "AAAAAAAA")
huggingface|$(_k "h" "f" "_" "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
github-pat|$(_k "git" "hub" "_pat_" "$_A40" "AAAAAAAAAAAAAAAAAAAA")
zhipu|$(_k "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" "." "bbbbbbbbbbbbbbbb")
openai (controle)|$(_k "sk" "-" "$_A40")
google (controle)|$(_k "AI" "za" "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
LISTA

_caso P-1 PASSA "FALSO POSITIVO: sha de commit e hash truncado" <<'EOF'
printf 'commit dc19621 sha256 8783d29d9f8d0158d71f91e7c6879c72 ok\n' > texto.md && git add texto.md
EOF

# --------------------------------------------------------------- veredito --
echo
if [ "$FALHOU" -eq 0 ]; then
  echo "$(_cor '0;32' "SUITE OK") -- $OK caso(s), 0 falha(s)${PULADO:+, $PULADO fora do filtro}"
  exit 0
fi
echo "$(_cor '1;31' "SUITE FALHOU") -- $OK ok, $FALHOU falha(s)"
printf '  - %s\n' "${falhas_detalhe[@]}"
echo
echo "Uma FALHA aqui significa uma de duas coisas, e as duas sao serias:"
echo "  'esperava PEGA'  -> um controle parou de proteger o que protegia (furo)."
echo "  'esperava PASSA' -> um controle passou a acusar o que e' legitimo"
echo "                      (falso positivo -- o operador desliga, e ai nao protege mais nada)."
exit 1
